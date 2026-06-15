"""A4: Split-Sample Trigger Validation.

Split each player's career in half by game date, run Screen F independently
on each half, and test whether trigger classifications are stable.

The concordance test: if a player classified "opponent-independent" on their
full career, do they get the same label on the first half and second half
independently? If trigger types are stable, they should. If they're career-phase
artifacts, they won't.

Method:
  1. For each player with >= 40 playoff games, split PO games by median date.
  2. Run compute_trigger_profile() on each half independently.
     RS baselines use the full RS career (floor-game percentile is career-level).
  3. Classify trigger on each half using the same classify_trigger_param().
  4. Build concordance table: full-career label vs first-half vs second-half.
  5. For players with < 40 PO games, flag as underpowered.

Success criteria:
  - >= 70% of players with >= 40 PO games retain trigger classification across halves
  - The core classifications (Harden, Embiid, SGA, Butler, Trae) are stable

Output:
  data/processed/trigger_split_sample.csv
  Console report
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

from screen_f import compute_trigger_profile, _def_col
from trigger_sensitivity import classify_trigger_param

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MIN_PO_GAMES_FULL = 40
MIN_PO_GAMES_HALF = 15


def run_split_sample(df: pd.DataFrame) -> pd.DataFrame:
    col = _def_col(df)
    po = df[df["is_playoff"] & df[col].notna()].copy()

    if "game_date" not in po.columns:
        raise ValueError("analysis_table must have game_date column for split-sample")

    po["game_date"] = pd.to_datetime(po["game_date"])

    players = sorted(po["player_name"].unique())
    rows = []

    for player in players:
        po_sub = po[po["player_name"] == player].sort_values("game_date")
        rs_sub = df[(df["player_name"] == player) & ~df["is_playoff"]]

        n_po = len(po_sub)

        full_profile = compute_trigger_profile(po_sub, rs_sub, col, min_games=10)
        full_trigger = classify_trigger_param(full_profile) if full_profile else "unknown"

        if n_po < MIN_PO_GAMES_FULL:
            rows.append({
                "player": player,
                "n_po": n_po,
                "full_trigger": full_trigger,
                "first_half_trigger": "underpowered",
                "second_half_trigger": "underpowered",
                "concordant": np.nan,
                "eligible": False,
                "n_first": np.nan,
                "n_second": np.nan,
                "first_weak": np.nan,
                "first_strong": np.nan,
                "first_gradient": np.nan,
                "second_weak": np.nan,
                "second_strong": np.nan,
                "second_gradient": np.nan,
                "full_weak": full_profile.get("weak_floor", np.nan) if full_profile else np.nan,
                "full_strong": full_profile.get("strong_floor", np.nan) if full_profile else np.nan,
                "full_gradient": full_profile.get("gradient", np.nan) if full_profile else np.nan,
            })
            continue

        median_date = po_sub["game_date"].quantile(0.5)
        first_half = po_sub[po_sub["game_date"] <= median_date]
        second_half = po_sub[po_sub["game_date"] > median_date]

        if len(first_half) < MIN_PO_GAMES_HALF or len(second_half) < MIN_PO_GAMES_HALF:
            first_profile = compute_trigger_profile(first_half, rs_sub, col, min_games=8) if len(first_half) >= 8 else None
            second_profile = compute_trigger_profile(second_half, rs_sub, col, min_games=8) if len(second_half) >= 8 else None
            first_trigger = classify_trigger_param(first_profile) if first_profile else "underpowered"
            second_trigger = classify_trigger_param(second_profile) if second_profile else "underpowered"
        else:
            first_profile = compute_trigger_profile(first_half, rs_sub, col, min_games=10)
            second_profile = compute_trigger_profile(second_half, rs_sub, col, min_games=10)
            first_trigger = classify_trigger_param(first_profile) if first_profile else "unknown"
            second_trigger = classify_trigger_param(second_profile) if second_profile else "unknown"

        concordant = first_trigger == second_trigger

        rows.append({
            "player": player,
            "n_po": n_po,
            "n_first": len(first_half),
            "n_second": len(second_half),
            "full_trigger": full_trigger,
            "first_half_trigger": first_trigger,
            "second_half_trigger": second_trigger,
            "concordant": concordant,
            "eligible": True,
            "first_weak": first_profile.get("weak_floor", np.nan) if first_profile else np.nan,
            "first_strong": first_profile.get("strong_floor", np.nan) if first_profile else np.nan,
            "first_gradient": first_profile.get("gradient", np.nan) if first_profile else np.nan,
            "first_avg": first_profile.get("avg_floor", np.nan) if first_profile else np.nan,
            "second_weak": second_profile.get("weak_floor", np.nan) if second_profile else np.nan,
            "second_strong": second_profile.get("strong_floor", np.nan) if second_profile else np.nan,
            "second_gradient": second_profile.get("gradient", np.nan) if second_profile else np.nan,
            "second_avg": second_profile.get("avg_floor", np.nan) if second_profile else np.nan,
            "full_weak": full_profile.get("weak_floor", np.nan) if full_profile else np.nan,
            "full_strong": full_profile.get("strong_floor", np.nan) if full_profile else np.nan,
            "full_gradient": full_profile.get("gradient", np.nan) if full_profile else np.nan,
        })

    results = pd.DataFrame(rows)
    results.to_csv(config.PROCESSED_DIR / "trigger_split_sample.csv", index=False)
    return results


def print_split_sample_report(results: pd.DataFrame) -> None:
    print("\n" + "=" * 100)
    print("A4: SPLIT-SAMPLE TRIGGER VALIDATION")
    print("=" * 100)
    print()
    print("  Split each player's playoff career in half by median game date.")
    print("  Run Screen F independently on each half. Test concordance.")
    print()

    eligible = results[results["eligible"] == True]
    underpowered = results[results["eligible"] == False]

    print(f"  Eligible (>= {MIN_PO_GAMES_FULL} PO games): {len(eligible)}")
    print(f"  Underpowered: {len(underpowered)}")
    print()

    print(f"  {'Player':<28} {'N':>4} {'Full':>18} {'1st half':>18} {'2nd half':>18} {'Conc':>5} {'1st W/A/S':>14} {'2nd W/A/S':>14}")
    print(f"  {'-'*28} {'-':>4} {'-'*18} {'-'*18} {'-'*18} {'-'*5} {'-'*14} {'-'*14}")

    n_concordant = 0
    n_eligible = 0
    for _, r in eligible.iterrows():
        n_eligible += 1
        if r["concordant"]:
            n_concordant += 1

        def was(fmt_str, w, a, s):
            parts = []
            parts.append(f"{w:.0%}" if not np.isnan(w) else "-")
            parts.append(f"{a:.0%}" if not np.isnan(a) else "-")
            parts.append(f"{s:.0%}" if not np.isnan(s) else "-")
            return "/".join(parts)

        first_was = was("", r["first_weak"], r["first_avg"], r["first_strong"])
        second_was = was("", r["second_weak"], r["second_avg"], r["second_strong"])
        conc = "Y" if r["concordant"] else " "
        print(f"  {r['player']:<28} {int(r['n_po']):>4} {r['full_trigger']:>18} "
              f"{r['first_half_trigger']:>18} {r['second_half_trigger']:>18} {conc:>5} "
              f"{first_was:>14} {second_was:>14}")

    print()
    if len(underpowered) > 0:
        print("  Underpowered players (< 40 PO games):")
        for _, r in underpowered.iterrows():
            print(f"    {r['player']:<28} {int(r['n_po']):>4} {r['full_trigger']:>18}")
        print()

    if n_eligible > 0:
        concordance_rate = n_concordant / n_eligible
        print(f"  CONCORDANCE: {n_concordant}/{n_eligible} ({concordance_rate*100:.0f}%)")

        if concordance_rate >= 0.70:
            print("  PASS: >= 70% of eligible players retain trigger across halves.")
        else:
            print("  FAIL: < 70% concordance. Trigger types may be career-phase artifacts.")

    print()
    print("  === GRADIENT STABILITY (continuous, not categorical) ===")
    print()
    print(f"  {'Player':<28} {'Full grad':>10} {'1st grad':>10} {'2nd grad':>10} {'Direction':>12}")
    print(f"  {'-'*28} {'-'*10} {'-'*10} {'-'*10} {'-'*12}")

    same_direction = 0
    opposite_direction = 0
    for _, r in eligible.iterrows():
        fg = r["full_gradient"]
        g1 = r["first_gradient"]
        g2 = r["second_gradient"]
        if np.isnan(fg) or np.isnan(g1) or np.isnan(g2):
            continue
        dir_match = (g1 > 0 and g2 > 0) or (g1 < 0 and g2 < 0)
        direction = "same" if dir_match else "OPPOSITE"
        if dir_match:
            same_direction += 1
        else:
            opposite_direction += 1
        print(f"  {r['player']:<28} {fg:>+10.3f} {g1:>+10.3f} {g2:>+10.3f} {direction:>12}")

    total_grad = same_direction + opposite_direction
    if total_grad > 0:
        print(f"\n  Gradient direction stability: {same_direction}/{total_grad} ({same_direction/total_grad*100:.0f}%)")

    print()
    print("  === FULL vs HALF-LABEL CONCORDANCE ===")
    print()
    for trigger_type in ["opponent-independent", "scheme-dependent", "disengagement", "bimodal", "standard"]:
        full_matches = eligible[eligible["full_trigger"] == trigger_type]
        if len(full_matches) == 0:
            continue
        first_match = (full_matches["first_half_trigger"] == trigger_type).sum()
        second_match = (full_matches["second_half_trigger"] == trigger_type).sum()
        both_match = ((full_matches["first_half_trigger"] == trigger_type) & (full_matches["second_half_trigger"] == trigger_type)).sum()
        print(f"  {trigger_type:<22} Full={len(full_matches)}  1st={first_match}  2nd={second_match}  Both={both_match}")

    print()
    print("  === KEY PLAYERS ===")
    print()
    key_players = ["James Harden", "Joel Embiid", "Shai Gilgeous-Alexander",
                   "Jimmy Butler", "Trae Young", "Ben Simmons",
                   "Paul George", "Klay Thompson", "Dirk Nowitzki",
                   "Russell Westbrook", "Ray Allen", "DeMar DeRozan"]
    for kp in key_players:
        row = eligible[eligible["player"] == kp]
        if len(row) == 0:
            row = underpowered[underpowered["player"] == kp]
        if len(row) == 0:
            continue
        r = row.iloc[0]
        if r.get("eligible", False):
            conc = "STABLE" if r["concordant"] else "SHIFTS"
            print(f"  {r['player']:<28} {r['full_trigger']:>18} -> {r['first_half_trigger']:>18} / {r['second_half_trigger']:>18}  {conc}")
        else:
            print(f"  {r['player']:<28} {r['full_trigger']:>18}  (underpowered: {int(r['n_po'])} PO games)")


def main() -> None:
    path = config.PROCESSED_DIR / "analysis_table.csv"
    if not path.exists():
        raise FileNotFoundError(f"Run features first: {path}")

    df = pd.read_csv(path, low_memory=False)
    df["is_playoff"] = df["is_playoff"].astype(bool)
    df["is_floor_primary"] = df["is_floor_primary"].astype(bool)

    if "game_date" not in df.columns:
        raw_frames = []
        for name in config.ALL_PLAYERS:
            slug = config.player_slug(name)
            for suffix in ("rs", "po"):
                p = config.RAW_DIR / f"{slug}_{suffix}.csv"
                if p.exists():
                    raw_frames.append(p)
        logger.info("Checking raw data for game_date...")
        from features import load_all_raw
        raw = load_all_raw()
        if "game_date" in raw.columns:
            raw_date_map = raw[["player_name", "game_id", "game_date"]].drop_duplicates(subset=["player_name", "game_id"])
            df = df.merge(raw_date_map, on=["player_name", "game_id"], how="left", suffixes=("", "_raw"))
            if "game_date_raw" in df.columns:
                df["game_date"] = df["game_date_raw"]
            logger.info("Joined game_date from raw data")
        else:
            logger.warning("No game_date in raw data; using season as proxy")
            df["game_date"] = df["season"]

    results = run_split_sample(df)
    print_split_sample_report(results)
    logger.info("A4 complete")


if __name__ == "__main__":
    main()
