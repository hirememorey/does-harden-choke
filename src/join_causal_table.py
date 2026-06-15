"""Causal chain Step 1 — join player analysis table to team game logs, compute per-game mechanism variables."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from src.nba_client import normalize_game_id

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_PATH = config.PROCESSED_DIR / "causal_analysis_table.csv"


def load_and_normalize() -> tuple[pd.DataFrame, pd.DataFrame]:
    players = pd.read_csv(config.PROCESSED_DIR / "analysis_table.csv")
    teams = pd.read_csv(config.RAW_DIR / "team_game_logs.csv")

    players["game_id"] = players["game_id"].apply(normalize_game_id)
    teams["game_id"] = teams["game_id"].apply(normalize_game_id)

    players["team_id"] = players["team_id"].astype(str)
    teams["team_id"] = teams["team_id"].astype(str)

    return players, teams


def join_player_team(players: pd.DataFrame, teams: pd.DataFrame) -> pd.DataFrame:
    team_cols = [
        "game_id",
        "team_id",
        "off_rating",
        "def_rating",
        "poss",
        "wl",
        "pts",
        "plus_minus",
        "is_playoff",
    ]
    team_subset = teams[team_cols].copy()
    team_subset = team_subset.rename(columns={
        "off_rating": "team_off_rating",
        "def_rating": "team_def_rating",
        "poss": "team_poss",
        "pts": "team_pts",
        "plus_minus": "team_plus_minus",
    })

    merged = players.merge(
        team_subset,
        on=["game_id", "team_id", "is_playoff"],
        how="inner",
        suffixes=("", "_team"),
    )

    logger.info(
        "Join: %d player-games → %d matched (%.1f%%)",
        len(players),
        len(merged),
        100 * len(merged) / len(players) if len(players) else 0,
    )
    return merged


def compute_per_game_retention(df: pd.DataFrame) -> pd.DataFrame:
    non_floor = df[df["is_floor_primary"] == False].copy()

    non_floor["fga_per36"] = non_floor["fga"] / non_floor["minutes"] * 36
    non_floor["fta_per36"] = non_floor["fta"] / non_floor["minutes"] * 36
    non_floor["ast_per36"] = non_floor["ast"] / non_floor["minutes"] * 36

    baselines = non_floor.groupby("player_name").agg(
        baseline_fga_per36=("fga_per36", "mean"),
        baseline_fta_per36=("fta_per36", "mean"),
        baseline_ast_per36=("ast_per36", "mean"),
    ).reset_index()

    df = df.merge(baselines, on="player_name", how="left")

    df["fga_per36"] = np.where(df["minutes"] > 0, df["fga"] / df["minutes"] * 36, np.nan)
    df["fta_per36"] = np.where(df["minutes"] > 0, df["fta"] / df["minutes"] * 36, np.nan)
    df["ast_per36"] = np.where(df["minutes"] > 0, df["ast"] / df["minutes"] * 36, np.nan)

    df["fga_retention"] = np.where(
        (df["baseline_fga_per36"] > 0) & (df["minutes"] > 0),
        df["fga_per36"] / df["baseline_fga_per36"],
        np.nan,
    )
    df["fta_retention"] = np.where(
        (df["baseline_fta_per36"] > 0) & (df["minutes"] > 0),
        df["fta_per36"] / df["baseline_fta_per36"],
        np.nan,
    )
    df["ast_retention"] = np.where(
        (df["baseline_ast_per36"] > 0) & (df["minutes"] > 0),
        df["ast_per36"] / df["baseline_ast_per36"],
        np.nan,
    )

    return df


def attach_mechanism_labels(df: pd.DataFrame) -> pd.DataFrame:
    screen_e_path = config.PROCESSED_DIR / "screen_e_results.csv"
    if not screen_e_path.exists():
        logger.warning("screen_e_results.csv not found — skipping mechanism labels")
        return df

    screen_e = pd.read_csv(screen_e_path)
    label_cols = ["player", "mechanism", "vol_share"]
    available = [c for c in label_cols if c in screen_e.columns]
    if "player" not in available:
        return df

    labels = screen_e[available].rename(columns={"player": "player_name"})
    df = df.merge(labels, on="player_name", how="left", suffixes=("", "_e"))
    return df


def add_team_win(df: pd.DataFrame) -> pd.DataFrame:
    df["team_win"] = (df["wl"] == "W").astype(int)
    return df


def validate(df: pd.DataFrame, original_n: int) -> None:
    row_pct = len(df) / original_n if original_n else 0
    logger.info("Validation — rows: %d (%.1f%% of original)", len(df), 100 * row_pct)

    dup_keys = df.duplicated(subset=["game_id", "player_name"]).sum()
    logger.info("Duplicate (game_id, player_name): %d", dup_keys)
    assert dup_keys == 0, f"Duplicate keys found: {dup_keys}"

    ortg_null = df["team_off_rating"].isna().sum()
    ortg_pct = 1 - ortg_null / len(df) if len(df) else 0
    logger.info("team_off_rating non-null: %.1f%%", 100 * ortg_pct)
    assert ortg_pct >= 0.95, f"team_off_rating coverage {ortg_pct:.1%} < 95%"

    floor = df[df["is_floor_primary"] == True]
    floor_fga_ret = floor["fga_retention"]
    finite_pct = floor_fga_ret.notna().mean() if len(floor_fga_ret) else 0
    logger.info(
        "Floor games: %d total, fga_retention finite: %.1f%%",
        len(floor),
        100 * finite_pct,
    )
    inf_count = np.isinf(floor_fga_ret.dropna()).sum() if len(floor_fga_ret.dropna()) else 0
    logger.info("fga_retention inf count in floor games: %d", inf_count)

    # Spot check: Harden 2017 G6 vs SAS
    harden_2017_g6 = df[
        (df["player_name"] == "James Harden")
        & (df["season"] == "2016-17")
        & (df["is_playoff"] == True)
        & (df["is_floor_primary"] == True)
    ]
    if len(harden_2017_g6) > 0:
        sample = harden_2017_g6.iloc[0]
        logger.info(
            "Spot check — Harden PO floor game: game_score=%.1f, fga_retention=%.2f, team_ORtg=%.1f, WL=%s",
            sample["game_score"],
            sample.get("fga_retention", np.nan),
            sample.get("team_off_rating", np.nan),
            sample.get("wl", "?"),
        )
    else:
        logger.info("Spot check: no Harden PO floor games in 2016-17 found (may be different season ID)")


def select_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    player_cols = [
        "player_name", "is_floor_primary", "game_score", "minutes",
        "fga", "fta", "ast", "tov", "pts", "is_playoff",
        "opponent", "home_away", "player_group",
        "def_rating_y", "series_game_num", "is_elimination",
        "plus_minus", "game_id", "team_id", "season", "game_date",
        "is_injury_flagged",
    ]

    team_cols = [
        "team_off_rating", "team_def_rating", "team_poss", "team_pts",
        "team_plus_minus", "team_win",
    ]

    derived_cols = [
        "fga_per36", "fta_per36", "ast_per36",
        "baseline_fga_per36", "baseline_fta_per36", "baseline_ast_per36",
        "fga_retention", "fta_retention", "ast_retention",
    ]

    mechanism_cols = ["mechanism", "vol_share"]

    available_player = [c for c in player_cols if c in df.columns]
    available_team = [c for c in team_cols if c in df.columns]
    available_derived = [c for c in derived_cols if c in df.columns]
    available_mechanism = [c for c in mechanism_cols if c in df.columns]

    all_cols = available_player + available_team + available_derived + available_mechanism
    return df[all_cols]


def main() -> None:
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    players, teams = load_and_normalize()
    original_n = len(players)

    merged = join_player_team(players, teams)
    merged = compute_per_game_retention(merged)
    merged = attach_mechanism_labels(merged)
    merged = add_team_win(merged)

    validate(merged, original_n)

    output = select_output_columns(merged)
    output.to_csv(OUTPUT_PATH, index=False)
    logger.info("Wrote %d rows to %s", len(output), OUTPUT_PATH)


if __name__ == "__main__":
    main()
