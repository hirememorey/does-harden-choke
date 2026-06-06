"""Validation gates for the possession parser (pass2_design_spec §6.1)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import config
from src.nba_client import create_client, normalize_game_id, result_set_to_records
from src.pass2.possessions import build_possessions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

POSSESSION_TOLERANCE = 3
USG_TOLERANCE_PP = 3.0


def parse_minutes(min_str: str) -> float:
    if not min_str or min_str == "None":
        return 0.0
    if ":" in str(min_str):
        mins, secs = str(min_str).split(":")
        return float(mins) + float(secs) / 60.0
    return float(min_str)


def estimated_team_possessions(team_row: dict) -> float:
    return (
        float(team_row["FGA"])
        + 0.44 * float(team_row["FTA"])
        + float(team_row["TO"])
        - float(team_row["OREB"])
    )


def _played(row: dict) -> bool:
    return bool(row.get("MIN")) and row.get("FGA") is not None


def box_score_usg(player_row: dict, team_rows: list[dict]) -> float:
    team = player_row["TEAM_ABBREVIATION"]
    team_players = [r for r in team_rows if r["TEAM_ABBREVIATION"] == team and _played(r)]
    team_mp = sum(parse_minutes(r["MIN"]) for r in team_players)
    player_mp = parse_minutes(player_row["MIN"])
    if player_mp <= 0 or team_mp <= 0:
        return float("nan")
    team_denom = sum(
        float(r["FGA"]) + 0.44 * float(r["FTA"]) + float(r["TO"]) for r in team_players
    )
    if team_denom <= 0:
        return float("nan")
    player_usage = (
        float(player_row["FGA"])
        + 0.44 * float(player_row["FTA"])
        + float(player_row["TO"])
    )
    return 100.0 * player_usage * (team_mp / 5.0) / (player_mp * team_denom)


def reconstructed_usg(
    player_id: int,
    possessions: pd.DataFrame,
    team_abbr: str,
    player_mp: float,
    team_mp: float,
    team_usage_denom: float,
) -> float:
    if player_mp <= 0 or team_usage_denom <= 0:
        return float("nan")
    play = possessions[possessions["terminal_event_type"] != "period_end"]
    team_poss = play[play["offensive_team"] == team_abbr]
    player_rows = play[play["terminal_player_id"] == player_id]
    usage_events = 0.0
    for _, row in player_rows.iterrows():
        if row["terminal_event_type"] in ("fga_make", "fga_miss", "tov"):
            usage_events += 1.0
        elif row["terminal_event_type"] == "ft_trip":
            usage_events += 1.0
    return 100.0 * usage_events * (team_mp / 5.0) / (player_mp * len(team_poss))


def terminal_team_mismatch_rate(
    possessions: pd.DataFrame,
    player_team: dict[int, str],
) -> float:
    play = possessions[
        possessions["terminal_event_type"].isin(["fga_make", "fga_miss", "tov", "ft_trip"])
    ]
    mismatches = 0
    checked = 0
    for _, row in play.iterrows():
        if pd.isna(row["terminal_player_id"]):
            continue
        player_id = int(row["terminal_player_id"])
        true_team = player_team.get(player_id)
        if not true_team:
            continue
        checked += 1
        if true_team != row["offensive_team"]:
            mismatches += 1
    return mismatches / checked if checked else 0.0


def build_player_team_map(game_id: str) -> dict[int, str]:
    from src.nba_client import playbyplay_actions
    from src.pass2.pbp_utils import sort_actions
    from src.pass2.possessions import load_pbp_payload

    actions = sort_actions(playbyplay_actions(load_pbp_payload(game_id)))
    player_team: dict[int, str] = {}
    for action in actions:
        player_id = int(action.get("personId") or 0)
        team = action.get("teamTricode") or ""
        if player_id and team:
            player_team[player_id] = team
    return player_team


def validate_game(
    game_id: str,
    *,
    focus_player_id: int | None = None,
    focus_player_name: str | None = None,
    rebuild: bool = False,
) -> dict:
    game_id = normalize_game_id(game_id)
    if rebuild:
        possessions = build_possessions(game_id)
    else:
        path = config.PROCESSED_PASS2_DIR / f"possessions_{game_id}.csv"
        if not path.exists():
            possessions = build_possessions(game_id)
        else:
            possessions = pd.read_csv(path)
            possessions["players_on_court"] = possessions["players_on_court"].apply(
                lambda x: json.loads(x.replace("'", '"')) if isinstance(x, str) and x.startswith("[") else []
            )

    client = create_client()
    box = client._make_request(
        "boxscoretraditionalv2",
        {
            "GameID": game_id,
            "StartPeriod": 0,
            "EndPeriod": 10,
            "RangeType": 0,
            "StartRange": 0,
            "EndRange": 0,
        },
    )
    team_rows = result_set_to_records(box, 1)
    player_rows = result_set_to_records(box, 0)
    play = possessions[possessions["terminal_event_type"] != "period_end"]

    possession_checks = []
    for team_row in team_rows:
        abbr = team_row["TEAM_ABBREVIATION"]
        expected = estimated_team_possessions(team_row)
        actual = int(play[play["offensive_team"] == abbr].shape[0])
        delta = actual - expected
        possession_checks.append(
            {
                "team": abbr,
                "expected": round(expected, 1),
                "actual": actual,
                "delta": round(delta, 1),
                "pass": abs(delta) <= POSSESSION_TOLERANCE,
            }
        )

    usg_check = None
    if focus_player_id:
        player_row = next((r for r in player_rows if int(r["PLAYER_ID"]) == focus_player_id), None)
        if player_row:
            team = player_row["TEAM_ABBREVIATION"]
            team_players = [r for r in player_rows if r["TEAM_ABBREVIATION"] == team and _played(r)]
            team_mp = sum(parse_minutes(r["MIN"]) for r in team_players)
            team_denom = sum(
                float(r["FGA"]) + 0.44 * float(r["FTA"]) + float(r["TO"]) for r in team_players
            )
            box_usg = box_score_usg(player_row, player_rows)
            recon_usg = reconstructed_usg(
                focus_player_id,
                possessions,
                team,
                parse_minutes(player_row["MIN"]),
                team_mp,
                team_denom,
            )
            usg_check = {
                "player": focus_player_name or player_row["PLAYER_NAME"],
                "box_usg": round(box_usg, 1),
                "reconstructed_usg": round(recon_usg, 1),
                "delta_pp": round(recon_usg - box_usg, 1),
                "pass": abs(recon_usg - box_usg) <= USG_TOLERANCE_PP,
            }

    player_team = build_player_team_map(game_id)
    mismatch_rate = terminal_team_mismatch_rate(possessions, player_team)

    return {
        "game_id": game_id,
        "total_possessions": int(len(play)),
        "possession_checks": possession_checks,
        "possession_pass": all(c["pass"] for c in possession_checks),
        "usg_check": usg_check,
        "terminal_mismatch_rate": round(mismatch_rate, 3),
        "terminal_mismatch_pass": mismatch_rate < 0.05,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate possession parser output.")
    parser.add_argument("--validation", action="store_true")
    parser.add_argument("--game-id", action="append", dest="game_ids")
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    if args.validation or not args.game_ids:
        with open(config.PASS2_VALIDATION_GAMES) as f:
            games = json.load(f)["games"]
    else:
        games = [{"game_id": gid} for gid in args.game_ids]

    all_pass = True
    for game in games:
        result = validate_game(
            game["game_id"],
            focus_player_id=game.get("focus_player_id"),
            focus_player_name=game.get("focus_player"),
            rebuild=args.rebuild,
        )
        logger.info("Validation %s", result["game_id"])
        for check in result["possession_checks"]:
            logger.info(
                "  %s possessions expected=%s actual=%s delta=%s pass=%s",
                check["team"],
                check["expected"],
                check["actual"],
                check["delta"],
                check["pass"],
            )
        if result["usg_check"]:
            u = result["usg_check"]
            logger.info(
                "  USG %s box=%s recon=%s delta=%s pass=%s",
                u["player"],
                u["box_usg"],
                u["reconstructed_usg"],
                u["delta_pp"],
                u["pass"],
            )
        logger.info(
            "  terminal mismatch rate=%.1f%% pass=%s",
            100 * result["terminal_mismatch_rate"],
            result["terminal_mismatch_pass"],
        )
        game_pass = (
            result["possession_pass"]
            and result["terminal_mismatch_pass"]
            and (result["usg_check"] is None or result["usg_check"]["pass"])
        )
        logger.info("  GAME PASS=%s", game_pass)
        all_pass = all_pass and game_pass

    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
