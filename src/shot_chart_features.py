"""Shot chart architecture features — mode concentration, independence, and collapse profiles.

Reads: data/raw/shot_charts.csv + data/processed/analysis_table.csv
Writes: data/processed/shot_chart_architecture.csv

Key new variables per player-season:
  hhi_5                    — Herfindahl across 5 modes (RA, Paint, Mid, 3PT, FT)
  mode_independence_score  — avg absolute pairwise correlation of per-game mode shares
  n_tertiary_modes         — modes contributing >=15% of scoring
  floor_mode_collapse_*    — per-mode share shift in floor vs non-floor RS games
"""

from __future__ import annotations

import logging
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MIN_RS_GAMES = 30
TERTIARY_THRESHOLD = 0.15

MODE_ZONE_MAP = {
    "Restricted Area": "ra",
    "In The Paint (Non-RA)": "paint",
    "Mid-Range": "mid",
    "Above the Break 3": "three",
    "Left Corner 3": "three",
    "Right Corner 3": "three",
    "Backcourt": "other",
    "Corner 3": "three",
}

MODES = ["ra", "paint", "mid", "three", "ft"]


def classify_zone(zone: str) -> str:
    if pd.isna(zone):
        return "other"
    return MODE_ZONE_MAP.get(zone.strip(), "other")


def _per_game_mode_shares(
    player_season_shots: pd.DataFrame,
) -> pd.DataFrame:
    """Per-game FGA share by zone mode for a single player-season.

    Returns one row per game with columns share_ra, share_paint, share_mid, share_three.
    """
    zone_modes = ["ra", "paint", "mid", "three"]
    game_counts = (
        player_season_shots
        .groupby("game_id")["zone_mode"]
        .value_counts()
        .unstack(fill_value=0)
    )
    for m in zone_modes:
        if m not in game_counts.columns:
            game_counts[m] = 0
    game_totals = game_counts[zone_modes].sum(axis=1)
    for m in zone_modes:
        game_counts[f"share_{m}"] = game_counts[m] / game_totals.replace(0, np.nan)
    return game_counts[[c for c in game_counts.columns if c.startswith("share_")]]


def compute_mode_independence(
    player_season_shots: pd.DataFrame,
) -> float:
    """Average absolute pairwise Pearson correlation of per-game mode shares.

    High = modes move together (vulnerable). Low = modes move independently (resilient).
    """
    shares = _per_game_mode_shares(player_season_shots)
    share_cols = [c for c in shares.columns if c.startswith("share_")]
    if len(share_cols) < 2 or len(shares) < MIN_RS_GAMES:
        return np.nan

    valid = shares[share_cols].dropna()
    if len(valid) < MIN_RS_GAMES:
        return np.nan

    corrs = []
    for c1, c2 in combinations(share_cols, 2):
        mask = valid[[c1, c2]].notna().all(axis=1)
        if mask.sum() < 15:
            continue
        r = valid.loc[mask, c1].corr(valid.loc[mask, c2])
        if not np.isnan(r):
            corrs.append(abs(r))

    return float(np.mean(corrs)) if corrs else np.nan


def compute_season_architecture(
    shots: pd.DataFrame, analysis: pd.DataFrame,
) -> pd.DataFrame:
    """Compute shot-chart architecture variables per player-season."""
    shots = shots.copy()
    shots["zone_mode"] = shots["shot_zone_basic"].apply(classify_zone)

    shots["shot_points"] = 0.0
    made_col = "shot_made_flag" if "shot_made_flag" in shots.columns else None
    if made_col is not None:
        made_mask = shots[made_col] == 1
        if "shot_type" in shots.columns:
            is_three = shots["shot_type"].str.contains("3PT", case=False, na=False)
            shots.loc[made_mask & is_three, "shot_points"] = 3.0
            shots.loc[made_mask & ~is_three, "shot_points"] = 2.0
        else:
            shots.loc[made_mask, "shot_points"] = 2.0

    # Merge floor-game flags from analysis_table
    if "game_id" in analysis.columns and "game_id" in shots.columns:
        floor_lookup = analysis[["game_id", "player_name", "is_floor_primary"]].drop_duplicates()
        shots = shots.merge(floor_lookup, on=["game_id", "player_name"], how="left")
        shots["is_floor_primary"] = shots["is_floor_primary"].fillna(False).astype(bool)
    else:
        shots["is_floor_primary"] = False

    # FTA data from analysis_table for the FT mode
    fta_by_game = (
        analysis[analysis["minutes"] > 0]
        .groupby(["player_name", "season", "game_id"])
        .agg(fta=("fta", "sum"), ftm=("ftm", "sum"), fga=("fga", "sum"))
        .reset_index()
    )
    fta_by_game["ft_points"] = fta_by_game["ftm"]

    rows = []
    rs = shots[~shots["is_playoff"]]

    for (player, season), grp in rs.groupby(["player_name", "season"]):
        zone_pts = grp.groupby("zone_mode")["shot_points"].sum()
        ft_pts_row = fta_by_game[
            (fta_by_game["player_name"] == player) & (fta_by_game["season"] == season)
        ]
        ft_points = ft_pts_row["ft_points"].sum() if len(ft_pts_row) > 0 else 0.0

        total_pts = zone_pts.sum() + ft_points
        if total_pts == 0:
            continue

        shares = {}
        for m in MODES:
            if m == "ft":
                shares[m] = ft_points / total_pts
            else:
                shares[m] = zone_pts.get(m, 0.0) / total_pts

        hhi_5 = sum(s ** 2 for s in shares.values())

        n_tertiary = sum(1 for s in shares.values() if s >= TERTIARY_THRESHOLD)

        mode_indep = compute_mode_independence(grp)

        # Floor-game mode collapse
        floor_shots = grp[grp["is_floor_primary"]]
        nonfloor_shots = grp[~grp["is_floor_primary"]]

        floor_zone_pts = floor_shots.groupby("zone_mode")["shot_points"].sum()
        nonfloor_zone_pts = nonfloor_shots.groupby("zone_mode")["shot_points"].sum()

        floor_ft = ft_pts_row.merge(
            analysis[
                (analysis["player_name"] == player)
                & (analysis["season"] == season)
                & (analysis["is_floor_primary"] == True)
            ][["game_id"]].drop_duplicates(),
            on="game_id",
            how="inner",
        ) if len(floor_shots) > 0 else pd.DataFrame()
        nonfloor_ft = ft_pts_row.merge(
            analysis[
                (analysis["player_name"] == player)
                & (analysis["season"] == season)
                & (analysis["is_floor_primary"] == False)
            ][["game_id"]].drop_duplicates(),
            on="game_id",
            how="inner",
        ) if len(nonfloor_shots) > 0 else pd.DataFrame()

        floor_total = floor_zone_pts.sum() + (floor_ft["ft_points"].sum() if len(floor_ft) > 0 else 0)
        nonfloor_total = nonfloor_zone_pts.sum() + (nonfloor_ft["ft_points"].sum() if len(nonfloor_ft) > 0 else 0)

        collapse = {}
        for m in MODES:
            if m == "ft":
                fl_share = (floor_ft["ft_points"].sum() / floor_total) if floor_total > 0 else np.nan
                nfl_share = (nonfloor_ft["ft_points"].sum() / nonfloor_total) if nonfloor_total > 0 else np.nan
            else:
                fl_share = (floor_zone_pts.get(m, 0) / floor_total) if floor_total > 0 else np.nan
                nfl_share = (nonfloor_zone_pts.get(m, 0) / nonfloor_total) if nonfloor_total > 0 else np.nan
            collapse[m] = fl_share - nfl_share if not (np.isnan(fl_share) or np.isnan(nfl_share)) else np.nan

        rows.append({
            "player_name": player,
            "season": season,
            "n_rs_shots": len(grp),
            "share_ra": shares["ra"],
            "share_paint": shares["paint"],
            "share_mid": shares["mid"],
            "share_three": shares["three"],
            "share_ft": shares["ft"],
            "hhi_5": hhi_5,
            "mode_independence_score": mode_indep,
            "n_tertiary_modes": n_tertiary,
            "floor_mode_collapse_ra": collapse["ra"],
            "floor_mode_collapse_paint": collapse["paint"],
            "floor_mode_collapse_mid": collapse["mid"],
            "floor_mode_collapse_three": collapse["three"],
            "floor_mode_collapse_ft": collapse["ft"],
        })

    return pd.DataFrame(rows)


def main() -> None:
    shots_path = config.RAW_DIR / "shot_charts.csv"
    analysis_path = config.PROCESSED_DIR / "analysis_table.csv"

    if not shots_path.exists():
        raise FileNotFoundError(f"Run 'make scrape-shot-charts' first: {shots_path}")
    if not analysis_path.exists():
        raise FileNotFoundError(f"Run 'make features' first: {analysis_path}")

    shots = pd.read_csv(shots_path, low_memory=False)
    analysis = pd.read_csv(analysis_path, low_memory=False)
    analysis["is_playoff"] = analysis["is_playoff"].astype(bool)
    analysis["is_floor_primary"] = analysis["is_floor_primary"].astype(bool)

    logger.info("Loaded %d shot chart rows, %d analysis rows", len(shots), len(analysis))

    arch = compute_season_architecture(shots, analysis)
    logger.info("Computed architecture for %d player-seasons", len(arch))

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = config.PROCESSED_DIR / "shot_chart_architecture.csv"
    arch.to_csv(out_path, index=False)
    logger.info("Wrote %s", out_path)

    # Print summary
    print("\n" + "=" * 70)
    print("SHOT CHART ARCHITECTURE SUMMARY")
    print("=" * 70)
    print(f"Player-seasons: {len(arch)}")
    print(f"\nHHI-5: mean={arch['hhi_5'].mean():.3f}, std={arch['hhi_5'].std():.3f}")
    print(f"Mode independence: mean={arch['mode_independence_score'].mean():.3f}")
    print(f"Tertiary modes: mean={arch['n_tertiary_modes'].mean():.1f}")

    # Harden vs Durant contrast
    for name in ["James Harden", "Kevin Durant"]:
        row = arch[arch["player_name"] == name]
        if len(row) > 0:
            avg = row.iloc[0] if len(row) == 1 else row.mean(numeric_only=True)
            print(f"\n{name}:")
            print(f"  HHI-5: {avg.get('hhi_5', np.nan):.3f}")
            print(f"  Mode independence: {avg.get('mode_independence_score', np.nan):.3f}")
            print(f"  Tertiary modes: {avg.get('n_tertiary_modes', np.nan):.0f}")
            for m in ["ra", "paint", "mid", "three", "ft"]:
                print(f"  share_{m}: {avg.get(f'share_{m}', np.nan):.3f}")


if __name__ == "__main__":
    main()
