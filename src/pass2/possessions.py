"""Build possession-level table from cached playbyplayv3 JSON."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import config
from src.nba_client import (
    NBAStatsClient,
    create_client,
    normalize_game_id,
    playbyplay_actions,
    result_set_to_records,
)
from src.pass2.garbage_time import is_garbage_time
from src.pass2.lineups import LineupTracker
from src.pass2.pbp_utils import (
    has_immediate_free_throw,
    has_upcoming_free_throw,
    is_last_free_throw,
    iso_clock_to_seconds,
    parse_assist_player_id,
    parse_score_from_action,
    parse_tip_recipient,
    rebound_is_offensive,
    resolve_team_tricode,
    seconds_to_clock,
    shot_zone,
    sort_actions,
    team_margin_for_offense,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class OpenPossession:
    period: int
    start_clock: str
    start_seconds: int
    offense_tricode: str
    score_home: int
    score_away: int
    players_on_court: list[int]


@dataclass
class LiveShotAttempt:
    shooter_id: int
    offense_tricode: str
    shot_distance: float | None
    shot_zone: str | None


def load_pbp_payload(game_id: str, raw_dir: Path | None = None) -> dict[str, Any]:
    raw_dir = raw_dir or config.RAW_PBP_DIR
    path = raw_dir / f"{normalize_game_id(game_id)}.json"
    with open(path) as f:
        return json.load(f)


def infer_team_metadata(actions: list[dict[str, Any]]) -> tuple[dict[int, str], int, dict[str, bool]]:
    team_ids: dict[int, str] = {}
    home_team_id = 0
    home_flags: dict[str, bool] = {}
    for action in actions:
        team_id = int(action.get("teamId") or 0)
        tricode = action.get("teamTricode") or ""
        if team_id and tricode:
            team_ids[team_id] = tricode
        location = action.get("location") or ""
        if tricode and location == "h":
            home_flags[tricode] = True
            home_team_id = team_id
        elif tricode and location == "v":
            home_flags[tricode] = False
    if not home_team_id:
        raise ValueError("Could not infer home team from play-by-play actions")
    return team_ids, home_team_id, home_flags


def fetch_starters(client: NBAStatsClient, game_id: str) -> dict[str, list[int]]:
    resp = client._make_request(
        "boxscoretraditionalv2",
        {
            "GameID": normalize_game_id(game_id),
            "StartPeriod": 0,
            "EndPeriod": 10,
            "RangeType": 0,
            "StartRange": 0,
            "EndRange": 0,
        },
    )
    players = result_set_to_records(resp, 0)
    starters: dict[str, list[int]] = {}
    for row in players:
        if row.get("START_POSITION"):
            starters.setdefault(row["TEAM_ABBREVIATION"], []).append(int(row["PLAYER_ID"]))
    return starters


def build_name_maps(actions: list[dict[str, Any]]) -> dict[str, int]:
    name_to_id: dict[str, int] = {}
    for action in actions:
        player_id = int(action.get("personId") or 0)
        name = action.get("playerName") or ""
        if player_id and name:
            name_to_id[name] = player_id
    return name_to_id


def close_possession(
    open_possession: OpenPossession,
    *,
    possession_idx: int,
    game_id: str,
    season: str | None,
    is_playoff: bool,
    lineups: LineupTracker,
    terminal_player_id: int | None,
    terminal_event_type: str,
    end_clock: str,
    end_seconds: int,
    assist_player_id: int | None = None,
    shot_distance: float | None = None,
    zone: str | None = None,
) -> dict[str, Any]:
    offense = open_possession.offense_tricode
    defense = lineups.away_tricode if offense == lineups.home_tricode else lineups.home_tricode
    margin = team_margin_for_offense(
        open_possession.score_home,
        open_possession.score_away,
        lineups.offense_is_home(offense),
    )
    abs_margin = abs(margin)
    return {
        "game_id": normalize_game_id(game_id),
        "season": season,
        "is_playoff": is_playoff,
        "possession_idx": possession_idx,
        "period": open_possession.period,
        "start_clock": open_possession.start_clock,
        "end_clock": end_clock,
        "offensive_team": offense,
        "defensive_team": defense,
        "score_margin": margin,
        "terminal_player_id": terminal_player_id,
        "terminal_event_type": terminal_event_type,
        "is_garbage_time": is_garbage_time(open_possession.period, abs_margin, is_playoff=is_playoff),
        "players_on_court": open_possession.players_on_court,
        "shot_distance": shot_distance,
        "shot_zone": zone,
        "assist_player_id": assist_player_id,
        "seconds_remaining": end_seconds,
    }


def build_possessions(
    game_id: str,
    *,
    payload: dict[str, Any] | None = None,
    season: str | None = None,
    is_playoff: bool = True,
    starters: dict[str, list[int]] | None = None,
    client: NBAStatsClient | None = None,
) -> pd.DataFrame:
    payload = payload or load_pbp_payload(game_id)
    actions = sort_actions(playbyplay_actions(payload))
    if not actions:
        raise ValueError(f"No actions found for game {game_id}")

    team_ids, home_team_id, _ = infer_team_metadata(actions)
    client = client or create_client()
    starters = starters or fetch_starters(client, game_id)
    name_to_id = build_name_maps(actions)
    player_names = {pid: name for name, pid in name_to_id.items()}
    lineups = LineupTracker.from_starters(starters, team_ids, home_team_id, player_names)

    possessions: list[dict[str, Any]] = []
    possession_idx = 0

    home_score = 0
    away_score = 0
    open_possession: OpenPossession | None = None
    live_shot: LiveShotAttempt | None = None
    ft_active = False
    ft_shooter_id: int | None = None
    offense_tricode: str | None = None

    def update_score(action: dict[str, Any]) -> None:
        nonlocal home_score, away_score
        parsed = parse_score_from_action(action)
        if parsed is not None:
            home_score, away_score = parsed

    def other_team(tricode: str) -> str:
        return lineups.away_tricode if tricode == lineups.home_tricode else lineups.home_tricode

    def open_new_possession(period: int, clock: str, offense: str) -> None:
        nonlocal open_possession, offense_tricode, live_shot, ft_active, ft_shooter_id
        offense_tricode = offense
        open_possession = OpenPossession(
            period=period,
            start_clock=seconds_to_clock(iso_clock_to_seconds(clock)),
            start_seconds=iso_clock_to_seconds(clock),
            offense_tricode=offense,
            score_home=home_score,
            score_away=away_score,
            players_on_court=lineups.players_on_court(),
        )
        live_shot = None
        ft_active = False
        ft_shooter_id = None

    def finalize_possession(
        terminal_player_id: int | None,
        terminal_event_type: str,
        clock: str,
        *,
        assist_player_id: int | None = None,
        shot_distance: float | None = None,
        zone: str | None = None,
    ) -> None:
        nonlocal possession_idx, open_possession, live_shot, ft_active, ft_shooter_id
        if open_possession is None:
            return
        possessions.append(
            close_possession(
                open_possession,
                possession_idx=possession_idx,
                game_id=game_id,
                season=season,
                is_playoff=is_playoff,
                lineups=lineups,
                terminal_player_id=terminal_player_id,
                terminal_event_type=terminal_event_type,
                end_clock=seconds_to_clock(iso_clock_to_seconds(clock)),
                end_seconds=iso_clock_to_seconds(clock),
                assist_player_id=assist_player_id,
                shot_distance=shot_distance,
                zone=zone,
            )
        )
        possession_idx += 1
        open_possession = None
        live_shot = None
        ft_active = False
        ft_shooter_id = None

    def end_possession_and_flip(
        offense: str,
        terminal_player_id: int | None,
        terminal_event_type: str,
        clock: str,
        period: int,
        **kwargs: Any,
    ) -> None:
        finalize_possession(
            terminal_player_id,
            terminal_event_type,
            clock,
            **kwargs,
        )
        open_new_possession(period, clock, other_team(offense))

    for idx, action in enumerate(actions):
        action_type = action.get("actionType") or ""
        sub_type = action.get("subType") or ""
        period = int(action.get("period") or 0)
        clock = action.get("clock") or ""
        team = resolve_team_tricode(
            action,
            team_ids,
            home_tricode=lineups.home_tricode,
            away_tricode=lineups.away_tricode,
        )
        player_id = int(action.get("personId") or 0)
        if player_id in team_ids:
            player_id = 0
        description = action.get("description") or ""

        if player_id and action.get("playerName"):
            lineups.register_player_name(player_id, action.get("playerName") or "")

        if action_type == "period":
            if sub_type == "end" and open_possession is not None:
                finalize_possession(
                    terminal_player_id=None,
                    terminal_event_type="period_end",
                    clock=clock,
                )
            continue

        if action_type == "Substitution":
            lineups.apply_substitution(action)
            continue

        if action_type in ("Timeout",):
            continue

        if action_type == "":
            continue

        update_score(action)

        if action_type == "Jump Ball":
            tip_name = parse_tip_recipient(description)
            tip_team = None
            if tip_name:
                for tricode in (lineups.home_tricode, lineups.away_tricode):
                    if lineups.resolve_player_id(tip_name, tricode):
                        tip_team = tricode
                        break
            if tip_team is None:
                tip_team = team
            open_new_possession(period, clock, tip_team)
            continue

        if open_possession is None:
            if team:
                open_new_possession(period, clock, team)
            else:
                continue

        if action_type == "Made Shot":
            live_shot = None
            assist_id = parse_assist_player_id(description, name_to_id)
            zone_value = shot_zone(action)
            distance = action.get("shotDistance")
            distance_value = float(distance) if distance not in (None, "") else None
            if has_immediate_free_throw(
                actions,
                idx,
                shooter_id=player_id,
                team_tricode=team,
            ):
                ft_active = True
                ft_shooter_id = player_id
                continue
            end_possession_and_flip(
                team,
                player_id,
                "fga_make",
                clock,
                period,
                assist_player_id=assist_id,
                shot_distance=distance_value,
                zone=zone_value,
            )
            continue

        if action_type == "Missed Shot":
            live_shot = LiveShotAttempt(
                shooter_id=player_id,
                offense_tricode=team,
                shot_distance=float(action.get("shotDistance"))
                if action.get("shotDistance") not in (None, "")
                else None,
                shot_zone=shot_zone(action),
            )
            continue

        if action_type == "Rebound" and live_shot is not None:
            offensive = rebound_is_offensive(description)
            if offensive is None:
                offensive = team == live_shot.offense_tricode
            if offensive:
                continue
            finalize_possession(
                terminal_player_id=live_shot.shooter_id,
                terminal_event_type="fga_miss",
                clock=clock,
                shot_distance=live_shot.shot_distance,
                zone=live_shot.shot_zone,
            )
            open_new_possession(period, clock, team)
            continue

        if action_type == "Turnover":
            if live_shot is not None:
                live_shot = None
            end_possession_and_flip(team, player_id, "tov", clock, period)
            continue

        if action_type == "Foul" and "Shooting" in sub_type:
            ft_active = True
            ft_shooter_id = live_shot.shooter_id if live_shot else None
            continue

        if action_type == "Foul" and not ft_active and sub_type in ("Personal", "Loose Ball"):
            if has_upcoming_free_throw(actions, idx, team_tricode=team):
                ft_active = True
                ft_shooter_id = None
            continue

        if action_type == "Free Throw":
            if open_possession is None and team:
                open_new_possession(period, clock, team)
            if ft_shooter_id is None and player_id:
                ft_shooter_id = player_id
            if live_shot and ft_shooter_id is None:
                ft_shooter_id = live_shot.shooter_id
            if not ft_active:
                ft_active = True
                ft_shooter_id = player_id
            if is_last_free_throw(sub_type):
                offense = open_possession.offense_tricode if open_possession else team
                terminal_id = ft_shooter_id or live_shot.shooter_id if live_shot else ft_shooter_id
                end_possession_and_flip(
                    offense,
                    terminal_id,
                    "ft_trip",
                    clock,
                    period,
                )
            continue

        if action_type == "Violation" and "Goaltend" in description:
            # Scoring play is captured by the paired made-shot action.
            continue

    if not possessions:
        raise ValueError(f"No possessions parsed for game {game_id}")

    df = pd.DataFrame(possessions)
    return df


def build_and_save(
    game_id: str,
    *,
    season: str | None = None,
    is_playoff: bool = True,
    output_dir: Path | None = None,
) -> pd.DataFrame:
    output_dir = output_dir or config.PROCESSED_PASS2_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    df = build_possessions(game_id, season=season, is_playoff=is_playoff)
    out_path = output_dir / f"possessions_{normalize_game_id(game_id)}.csv"
    df.to_csv(out_path, index=False)
    logger.info("Wrote %s rows to %s", len(df), out_path)
    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build possessions from cached PBP JSON.")
    parser.add_argument("--validation", action="store_true", help="Process validation games.")
    parser.add_argument("--game-id", action="append", dest="game_ids")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.validation or not args.game_ids:
        with open(config.PASS2_VALIDATION_GAMES) as f:
            games = json.load(f)["games"]
        for game in games:
            build_and_save(
                game["game_id"],
                season=game.get("season"),
                is_playoff=True,
            )
    else:
        for game_id in args.game_ids:
            build_and_save(game_id)


if __name__ == "__main__":
    main()
