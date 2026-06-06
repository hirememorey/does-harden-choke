"""Feature engineering: baselines, floor-game flags, analysis table."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_all_raw() -> pd.DataFrame:
    frames = []
    for name in config.ALL_PLAYERS:
        slug = config.player_slug(name)
        for suffix, is_po in (("rs", False), ("po", True)):
            path = config.RAW_DIR / f"{slug}_{suffix}.csv"
            if not path.exists():
                logger.warning("Missing %s", path)
                continue
            df = pd.read_csv(path, parse_dates=["game_date"])
            df["is_playoff"] = is_po
            frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No raw CSVs in {config.RAW_DIR}")
    return pd.concat(frames, ignore_index=True)


def compute_baselines(rs_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for player, grp in rs_df.groupby("player_name"):
        gs = grp["game_score"].dropna()
        n = len(gs)
        row = {
            "player_name": player,
            "player_group": config.PLAYER_GROUP.get(player, ""),
            "rs_n_games": n,
            "rs_mean_gs": gs.mean(),
            "rs_sd_gs": gs.std(),
            "rs_p15_gs": gs.quantile(config.FLOOR_GAME_PERCENTILE / 100),
            "rs_p85_gs": gs.quantile(0.85),
            "rs_median_gs": gs.median(),
        }
        if "bpm" in grp.columns:
            bpm = grp["bpm"].dropna()
            row["rs_mean_bpm"] = bpm.mean()
            row["rs_sd_bpm"] = bpm.std()
        rows.append(row)
    baselines = pd.DataFrame(rows)
    short = baselines[baselines["rs_n_games"] < config.MIN_RS_GAMES]
    for _, r in short.iterrows():
        logger.warning(
            "%s has only %d RS games (min %d)",
            r["player_name"],
            r["rs_n_games"],
            config.MIN_RS_GAMES,
        )
    return baselines


def add_floor_flags(df: pd.DataFrame, baselines: pd.DataFrame) -> pd.DataFrame:
    merged = df.merge(baselines, on="player_name", how="left", suffixes=("", "_bl"))
    cutoff_secondary = merged["rs_mean_gs"] - config.FLOOR_GAME_SD_CUTOFF * merged["rs_sd_gs"]
    merged["is_floor_primary"] = merged["game_score"] < merged["rs_p15_gs"]
    merged["is_floor_secondary"] = merged["game_score"] < cutoff_secondary
    merged["residual_primary"] = merged["game_score"] - merged["rs_p15_gs"]
    merged["residual_secondary"] = merged["game_score"] - cutoff_secondary
    return merged


def quality_checks(df: pd.DataFrame) -> None:
    for player, grp in df[~df["is_playoff"]].groupby("player_name"):
        rate = grp["is_floor_primary"].mean()
        if abs(rate - 0.15) > 0.03:
            logger.warning(
                "%s RS floor rate %.1f%% (expected ~15%%)", player, 100 * rate
            )
        mean_gs = grp["game_score"].mean()
        med = grp["game_score"].median()
        if mean_gs <= med:
            logger.warning("%s RS distribution not right-skewed", player)

    po_counts = df[df["is_playoff"]].groupby("player_name").size()
    for player, n in po_counts.items():
        if n < 10:
            logger.warning("%s has only %d playoff games", player, n)

    logger.info(
        "Totals: %d games (%d RS, %d PO)",
        len(df),
        (~df["is_playoff"]).sum(),
        df["is_playoff"].sum(),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = load_all_raw()
    df = df[df["minutes"].fillna(0) > 0]

    rs = df[~df["is_playoff"]]
    baselines = compute_baselines(rs)
    baselines.to_csv(config.PROCESSED_DIR / "player_baselines.csv", index=False)

    flagged = add_floor_flags(df, baselines)
    flagged.to_csv(config.PROCESSED_DIR / "floor_games.csv", index=False)
    flagged.to_csv(config.PROCESSED_DIR / "analysis_table.csv", index=False)

    quality_checks(flagged)
    logger.info("Wrote processed tables to %s", config.PROCESSED_DIR)


if __name__ == "__main__":
    main()
