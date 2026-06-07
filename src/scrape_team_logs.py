"""Causal chain Step 0 — fetch team game logs (Base + Advanced) for cohort games."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from src.nba_client import NBAStatsClient, normalize_game_id, result_set_to_records
from src.scrape import normalize_columns, parse_matchup, records_to_df

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

TEAM_LOGS_PATH = config.RAW_DIR / "team_game_logs.csv"


def collect_team_season_keys(player_csvs: list[Path] | None = None) -> pd.DataFrame:
    """Unique (team_id, season, is_playoff) tuples from player raw CSVs."""
    paths = player_csvs or []
    if not paths:
        for name in config.ALL_PLAYERS:
            slug = config.player_slug(name)
            for suffix in ("_rs", "_po"):
                p = config.RAW_DIR / f"{slug}{suffix}.csv"
                if p.exists():
                    paths.append(p)

    if not paths:
        raise FileNotFoundError("No player CSVs found under data/raw/")

    frames = []
    usecols = {"team_id", "season", "is_playoff", "game_id"}
    for path in paths:
        df = pd.read_csv(path, usecols=lambda c: c in usecols)
        frames.append(df)

    all_games = pd.concat(frames, ignore_index=True)
    keys = (
        all_games.dropna(subset=["team_id", "season"])
        .drop_duplicates(subset=["team_id", "season", "is_playoff"])
        .astype({"team_id": int, "is_playoff": bool})
        .sort_values(["team_id", "season", "is_playoff"])
        .reset_index(drop=True)
    )
    return keys


def fetch_merged_team_logs(
    client: NBAStatsClient,
    team_id: int,
    season: str,
    season_type: str,
) -> pd.DataFrame:
    """Fetch Base + Advanced team game logs and merge on game_id."""
    base = result_set_to_records(
        client.get_team_game_logs(team_id, season, season_type, "Base")
    )
    if not base:
        return pd.DataFrame()

    df_base = records_to_df(base)
    try:
        adv = result_set_to_records(
            client.get_team_game_logs(team_id, season, season_type, "Advanced")
        )
    except Exception as exc:
        logger.warning(
            "Advanced team logs failed for team %s %s %s: %s (Base only)",
            team_id,
            season,
            season_type,
            exc,
        )
        return df_base

    if not adv:
        return df_base

    df_adv = records_to_df(adv)
    merge_keys = [
        c for c in ("game_id", "team_id", "season") if c in df_base.columns and c in df_adv.columns
    ]
    if not merge_keys:
        merge_keys = ["game_id"] if "game_id" in df_base.columns else []
    if not merge_keys:
        return df_base

    adv_only = [c for c in df_adv.columns if c not in df_base.columns and c not in merge_keys]
    # Avoid duplicate wl/matchup columns with different suffixes from Advanced payload.
    adv_only = [c for c in adv_only if c not in {"wl", "matchup", "game_date", "team", "team_name"}]
    return df_base.merge(df_adv[merge_keys + adv_only], on=merge_keys, how="left")


def enrich_team_logs(df: pd.DataFrame, season: str, is_playoff: bool) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    if "season" not in out.columns:
        out["season"] = season
    out["is_playoff"] = is_playoff

    if "matchup" in out.columns:
        parsed = out["matchup"].apply(parse_matchup)
        out["team"] = parsed.apply(lambda x: x[0])
        out["opponent"] = parsed.apply(lambda x: x[1])
        out["home_away"] = parsed.apply(lambda x: x[2])

    if "game_date" in out.columns:
        out["game_date"] = pd.to_datetime(out["game_date"])

    # Normalize team_id to int for joins.
    if "team_id" in out.columns:
        out["team_id"] = pd.to_numeric(out["team_id"], errors="coerce").astype("Int64")

    if "game_id" in out.columns:
        out["game_id"] = out["game_id"].apply(normalize_game_id)

    return out


def _completed_keys(df: pd.DataFrame) -> set[tuple[int, str, bool]]:
    if df.empty:
        return set()
    req = {"team_id", "season", "is_playoff"}
    if not req.issubset(df.columns):
        return set()
    subset = df[list(req)].dropna(subset=["team_id", "season"])
    return {
        (int(r.team_id), str(r.season), bool(r.is_playoff))
        for r in subset.itertuples(index=False)
    }


def _finalize_team_logs(frames: list[pd.DataFrame]) -> pd.DataFrame:
    combined = pd.concat(frames, ignore_index=True)
    dedupe_cols = [c for c in ("game_id", "team_id") if c in combined.columns]
    combined = combined.drop_duplicates(subset=dedupe_cols, keep="first")
    sort_cols = [c for c in ("season", "game_date", "team_id") if c in combined.columns]
    return combined.sort_values(sort_cols).reset_index(drop=True)


def scrape_team_logs(
    keys: pd.DataFrame | None = None,
    output_path: Path = TEAM_LOGS_PATH,
    force: bool = False,
    resume: bool = False,
) -> pd.DataFrame:
    """Fetch team game logs for all team-season keys in the cohort."""
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not force and not resume:
        logger.info("Using cached %s", output_path)
        return pd.read_csv(output_path, parse_dates=["game_date"], low_memory=False)

    keys = keys if keys is not None else collect_team_season_keys()
    client = NBAStatsClient()

    existing_frames: list[pd.DataFrame] = []
    done: set[tuple[int, str, bool]] = set()
    if resume and output_path.exists():
        existing = pd.read_csv(output_path, low_memory=False)
        if not existing.empty:
            existing_frames.append(existing)
            done = _completed_keys(existing)
            logger.info("Resuming — %d team-season keys already in %s", len(done), output_path.name)

    failed: list[str] = []
    pending = 0
    for _, row in keys.iterrows():
        key = (int(row["team_id"]), str(row["season"]), bool(row["is_playoff"]))
        if key in done:
            continue
        pending += 1

    if pending == 0 and existing_frames:
        combined = _finalize_team_logs(existing_frames)
        combined.to_csv(output_path, index=False)
        logger.info("Nothing to fetch; %s up to date (%d rows)", output_path, len(combined))
        return combined

    new_frames: list[pd.DataFrame] = []
    checkpoint_every = 10
    fetched_since_save = 0

    for _, row in tqdm(keys.iterrows(), total=len(keys), desc="Team-season fetches"):
        team_id = int(row["team_id"])
        season = str(row["season"])
        is_playoff = bool(row["is_playoff"])
        key = (team_id, season, is_playoff)
        if key in done:
            continue

        season_type = "Playoffs" if is_playoff else "Regular Season"

        try:
            df = fetch_merged_team_logs(client, team_id, season, season_type)
        except Exception as exc:
            failed.append(f"{team_id} {season} {season_type}: {exc}")
            continue

        if df.empty:
            failed.append(f"{team_id} {season} {season_type}: empty response")
            continue

        enriched = enrich_team_logs(df, season, is_playoff)
        new_frames.append(enriched)
        done.add(key)
        fetched_since_save += 1

        if fetched_since_save >= checkpoint_every:
            combined = _finalize_team_logs(existing_frames + new_frames)
            combined.to_csv(output_path, index=False)
            logger.info("Checkpoint: %d rows (%d unique games)", len(combined), combined["game_id"].nunique())
            fetched_since_save = 0

    all_frames = existing_frames + new_frames
    if not all_frames:
        raise RuntimeError("No team game logs fetched")

    combined = _finalize_team_logs(all_frames)
    combined.to_csv(output_path, index=False)
    logger.info("Wrote %s (%d rows, %d unique games)", output_path, len(combined), combined["game_id"].nunique())

    if failed:
        logger.warning("%d team-season fetches failed: %s", len(failed), failed[:10])

    return combined


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape team game logs (Base + Advanced)")
    parser.add_argument("--force", action="store_true", help="Re-fetch even if CSV exists")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continue from existing team_game_logs.csv, skipping completed keys",
    )
    args = parser.parse_args()
    scrape_team_logs(force=args.force, resume=args.resume)


if __name__ == "__main__":
    main()
