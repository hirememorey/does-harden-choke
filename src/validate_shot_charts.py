"""Validate shot chart data coverage and integrity.

Checks:
  1. Row count >= 95% of total FGA in analysis_table.csv
  2. No duplicate (game_id, game_event_id, player_id) keys
  3. Per-player-season coverage: flag any with <80% FGA match rate
  4. Spot-check Harden 2018-19 PO step-back 3s
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def validate_shot_charts() -> None:
    shots_path = config.RAW_DIR / "shot_charts.csv"
    analysis_path = config.PROCESSED_DIR / "analysis_table.csv"

    if not shots_path.exists():
        raise FileNotFoundError(f"Run 'make scrape-shot-charts' first: {shots_path}")
    if not analysis_path.exists():
        raise FileNotFoundError(f"Run 'make features' first: {analysis_path}")

    shots = pd.read_csv(shots_path, low_memory=False)
    analysis = pd.read_csv(analysis_path, low_memory=False)

    print("=" * 70)
    print("SHOT CHART VALIDATION")
    print("=" * 70)
    print(f"\nShot chart rows: {len(shots):,}")
    print(f"Unique players: {shots['player_name'].nunique()}")
    print(f"Unique games: {shots['game_id'].nunique() if 'game_id' in shots.columns else 'N/A'}")

    # Check 1: Duplicate keys
    if all(c in shots.columns for c in ("game_id", "game_event_id", "player_id")):
        dupes = shots.duplicated(subset=["game_id", "game_event_id", "player_id"]).sum()
        print(f"\nDuplicate (game_id, game_event_id, player_id): {dupes}")
        if dupes > 0:
            logger.warning("Found %d duplicate shot rows", dupes)
    else:
        print("\nCould not check duplicates — missing key columns")

    # Check 2: FGA coverage vs analysis_table
    analysis["is_playoff"] = analysis["is_playoff"].astype(bool)
    shots["is_playoff"] = shots["is_playoff"].astype(bool)

    fga_analysis = analysis.groupby(["player_name", "season", "is_playoff"])["fga"].sum().reset_index()
    fga_analysis.columns = ["player_name", "season", "is_playoff", "fga_analysis"]

    shot_type_col = "shot_type" if "shot_type" in shots.columns else None
    if shot_type_col:
        fga_shots = (
            shots
            .groupby(["player_name", "season", "is_playoff"])
            .size()
            .reset_index(name="fga_shots")
        )
    else:
        fga_shots = (
            shots
            .groupby(["player_name", "season", "is_playoff"])
            .size()
            .reset_index(name="fga_shots")
        )

    coverage = fga_analysis.merge(fga_shots, on=["player_name", "season", "is_playoff"], how="left")
    coverage["fga_shots"] = coverage["fga_shots"].fillna(0).astype(int)
    coverage["coverage_pct"] = coverage["fga_shots"] / coverage["fga_analysis"].clip(lower=1) * 100

    total_fga_analysis = coverage["fga_analysis"].sum()
    total_fga_shots = coverage["fga_shots"].sum()
    overall_coverage = total_fga_shots / max(total_fga_analysis, 1) * 100

    print(f"\nOverall FGA coverage: {total_fga_shots:,} / {total_fga_analysis:,} = {overall_coverage:.1f}%")

    # Per-player-season coverage
    low_coverage = coverage[coverage["coverage_pct"] < 80]
    if len(low_coverage) > 0:
        print(f"\nPlayer-seasons with <80% FGA coverage: {len(low_coverage)}")
        for _, row in low_coverage.iterrows():
            stype = "PO" if row["is_playoff"] else "RS"
            print(
                f"  {row['player_name']} {row['season']} {stype}: "
                f"{row['fga_shots']}/{row['fga_analysis']} ({row['coverage_pct']:.0f}%)"
            )
    else:
        print("\nAll player-seasons have >=80% FGA coverage")

    # Check 3: Spot-check Harden 2018-19 PO
    harden_po_19 = shots[
        (shots["player_name"] == "James Harden")
        & (shots["season"] == "2018-19")
        & (shots["is_playoff"])
    ]
    if len(harden_po_19) > 0:
        action_col = "action_type" if "action_type" in harden_po_19.columns else None
        zone_col = "shot_zone_basic" if "shot_zone_basic" in harden_po_19.columns else None
        print(f"\nHarden 2018-19 PO shots: {len(harden_po_19)}")
        if action_col:
            step_backs = harden_po_19[harden_po_19[action_col].str.contains("Step Back", case=False, na=False)]
            print(f"  Step-back shots: {len(step_backs)}")
        if zone_col:
            print(f"  Zone distribution:")
            for zone, count in harden_po_19[zone_col].value_counts().items():
                print(f"    {zone}: {count}")
    else:
        print("\nNo Harden 2018-19 PO shots found (may not have been scraped yet)")

    # Required columns check
    required = {"game_id", "player_id", "player_name", "season", "is_playoff", "shot_zone_basic"}
    available = set(shots.columns)
    missing = required - available
    if missing:
        print(f"\nMissing required columns: {missing}")
    else:
        print(f"\nAll required columns present: {required}")

    # Summary
    print("\n" + "=" * 70)
    if overall_coverage >= 95 and len(low_coverage) == 0 and not missing:
        print("VALIDATION PASSED")
    elif overall_coverage >= 90:
        print("VALIDATION PASSED WITH WARNINGS — check low-coverage player-seasons")
    else:
        print("VALIDATION FAILED — coverage below 90%")
    print("=" * 70)


if __name__ == "__main__":
    validate_shot_charts()
