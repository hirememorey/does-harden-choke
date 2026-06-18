"""Scrape per-shot data from shotchartdetail for all cohort player-seasons.

Output: data/raw/shot_charts.csv  (~430K rows, gitignored)
Runtime: ~18 min full cohort with --resume support
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from src.nba_client import NBAStatsClient, result_set_to_records
from src.scrape import normalize_columns

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

SHOT_CHARTS_PATH = config.RAW_DIR / "shot_charts.csv"


def collect_shot_chart_keys() -> pd.DataFrame:
    """Unique (player_id, season, is_playoff) tuples from analysis_table."""
    path = config.PROCESSED_DIR / "analysis_table.csv"
    if not path.exists():
        raise FileNotFoundError(f"Run 'make features' first: {path}")

    df = pd.read_csv(path, low_memory=False, usecols=["player_name", "season", "is_playoff"])
    df["is_playoff"] = df["is_playoff"].astype(bool)

    id_map = {name: info["nba_id"] for name, info in config.ALL_PLAYERS.items()}
    df["player_id"] = df["player_name"].map(id_map)
    df = df.dropna(subset=["player_id"])
    df["player_id"] = df["player_id"].astype(int)

    keys = (
        df[["player_id", "player_name", "season", "is_playoff"]]
        .drop_duplicates()
        .sort_values(["player_id", "season", "is_playoff"])
        .reset_index(drop=True)
    )
    return keys


def fetch_shot_chart(
    client: NBAStatsClient,
    player_id: int,
    season: str,
    season_type: str,
) -> pd.DataFrame:
    """Fetch shotchartdetail for one (player, season, season_type) combo."""
    resp = client._make_request(
        "shotchartdetail",
        {
            "PlayerID": str(player_id),
            "Season": season,
            "SeasonType": season_type,
            "PlayerPosition": "",
            "ContextMeasure": "FGA",
            "LastNGames": "0",
            "LeagueID": "00",
            "Month": "0",
            "OpponentTeamID": "0",
            "Period": "0",
            "DateFrom": "",
            "DateTo": "",
            "GameSegment": "",
            "Location": "",
            "Outcome": "",
            "SeasonSegment": "",
            "VsConference": "",
            "VsDivision": "",
            "RookieYear": "",
            "GameId": "",
            "Position": "",
            "Division": "",
            "PORound": "0",
            "MeasureType": "Base",
            "PerMode": "Totals",
            "PlusMinus": "N",
            "PaceAdjust": "N",
            "Rank": "N",
            "CumShotRange": "N",
            "ShotClockRange": "",
            "StarterBench": "",
            "TwoWay": "0",
            "TeamID": "0",
            "GameSegment": "",
            "Conference": "",
        },
    )

    rows = result_set_to_records(resp, result_set_index=0)
    if not rows:
        return pd.DataFrame()

    df = normalize_columns(pd.DataFrame(rows))
    return df


def _completed_keys(df: pd.DataFrame) -> set[tuple[int, str, bool]]:
    if df.empty:
        return set()
    req = {"player_id", "season", "is_playoff"}
    if not req.issubset(df.columns):
        return set()
    subset = df[list(req)].dropna(subset=["player_id", "season"])
    return {
        (int(r.player_id), str(r.season), bool(r.is_playoff))
        for r in subset.itertuples(index=False)
    }


def _finalize_shot_charts(frames: list[pd.DataFrame]) -> pd.DataFrame:
    combined = pd.concat(frames, ignore_index=True)
    dedupe_cols = [c for c in ("game_id", "game_event_id", "player_id") if c in combined.columns]
    if dedupe_cols:
        combined = combined.drop_duplicates(subset=dedupe_cols, keep="first")
    sort_cols = [c for c in ("player_id", "season", "game_id") if c in combined.columns]
    if sort_cols:
        combined = combined.sort_values(sort_cols).reset_index(drop=True)
    return combined


def scrape_shot_charts(
    keys: pd.DataFrame | None = None,
    output_path: Path = SHOT_CHARTS_PATH,
    force: bool = False,
    resume: bool = False,
) -> pd.DataFrame:
    """Fetch shot chart data for all cohort player-seasons."""
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not force and not resume:
        logger.info("Using cached %s", output_path)
        return pd.read_csv(output_path, low_memory=False)

    keys = keys if keys is not None else collect_shot_chart_keys()
    client = NBAStatsClient()

    existing_frames: list[pd.DataFrame] = []
    done: set[tuple[int, str, bool]] = set()
    if resume and output_path.exists():
        existing = pd.read_csv(output_path, low_memory=False)
        if not existing.empty:
            existing_frames.append(existing)
            done = _completed_keys(existing)
            logger.info("Resuming — %d player-season keys already in %s", len(done), output_path.name)

    failed: list[str] = []
    pending = sum(
        1
        for _, row in keys.iterrows()
        if (int(row["player_id"]), str(row["season"]), bool(row["is_playoff"])) not in done
    )

    if pending == 0 and existing_frames:
        combined = _finalize_shot_charts(existing_frames)
        combined.to_csv(output_path, index=False)
        logger.info("Nothing to fetch; %s up to date (%d rows)", output_path, len(combined))
        return combined

    logger.info("%d player-season keys to fetch", pending)

    new_frames: list[pd.DataFrame] = []
    checkpoint_every = 20
    fetched_since_save = 0

    for _, row in tqdm(keys.iterrows(), total=len(keys), desc="Shot chart fetches"):
        player_id = int(row["player_id"])
        player_name = str(row["player_name"])
        season = str(row["season"])
        is_playoff = bool(row["is_playoff"])
        key = (player_id, season, is_playoff)

        if key in done:
            continue

        season_type = "Playoffs" if is_playoff else "Regular Season"

        try:
            df = fetch_shot_chart(client, player_id, season, season_type)
        except Exception as exc:
            failed.append(f"{player_name} {season} {season_type}: {exc}")
            continue

        if df.empty:
            continue

        df["player_name"] = player_name
        df["season"] = season
        df["is_playoff"] = is_playoff

        new_frames.append(df)
        done.add(key)
        fetched_since_save += 1

        if fetched_since_save >= checkpoint_every:
            combined = _finalize_shot_charts(existing_frames + new_frames)
            combined.to_csv(output_path, index=False)
            logger.info(
                "Checkpoint: %d rows (%d player-seasons)",
                len(combined),
                len(done),
            )
            fetched_since_save = 0

    all_frames = existing_frames + new_frames
    if not all_frames:
        logger.warning("No shot chart data fetched; %d failures: %s", len(failed), failed[:10])
        return pd.DataFrame()

    combined = _finalize_shot_charts(all_frames)
    combined.to_csv(output_path, index=False)
    logger.info(
        "Wrote %s (%d rows, %d unique games)",
        output_path,
        len(combined),
        combined["game_id"].nunique() if "game_id" in combined.columns else 0,
    )

    if failed:
        logger.warning("%d fetches failed: %s", len(failed), failed[:10])

    return combined


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape shot chart data from shotchartdetail")
    parser.add_argument("--force", action="store_true", help="Re-fetch even if CSV exists")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continue from existing shot_charts.csv, skipping completed keys",
    )
    args = parser.parse_args()
    scrape_shot_charts(force=args.force, resume=args.resume)


if __name__ == "__main__":
    main()
