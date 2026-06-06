"""Pass 1 — Pillar 1: Failure Mode Stability Test.

Question: Is a player's failure mode (shrinker/forcer/mixed) a stable
career trait that replicates from RS to playoffs, or is it a playoff-specific
artifact?

Method: Compute Screen E's vol_share on RS floor games, then correlate
with the playoff vol_share already computed. If RS vol_share predicts
playoff vol_share, failure mode is a trait — not a playoff artifact.

Output:
  - data/processed/pillar1_rs_profiles.csv
  - data/processed/pillar1_stability.csv
  - console report with Pearson r and p-value
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def compute_vol_share(fl: pd.DataFrame, nfl: pd.DataFrame) -> dict:
    """Compute volume-share decomposition for a set of floor vs non-floor games."""
    def per36(col, sub):
        mins = sub["minutes"].mean()
        return sub[col].mean() / mins * 36 if mins > 0 else np.nan

    fga_36_fl = per36("fga", fl)
    fga_36_nfl = per36("fga", nfl)
    fta_36_fl = per36("fta", fl)
    fta_36_nfl = per36("fta", nfl)
    fg3a_36_fl = per36("fg3a", fl)
    fg3a_36_nfl = per36("fg3a", nfl)
    tov_36_fl = per36("tov", fl)
    tov_36_nfl = per36("tov", nfl)
    ast_36_fl = per36("ast", fl)
    ast_36_nfl = per36("ast", nfl)
    pts_36_fl = per36("pts", fl)
    pts_36_nfl = per36("pts", nfl)

    fg_pct_fl = fl["fgm"].sum() / fl["fga"].sum() if fl["fga"].sum() > 0 else np.nan
    fg_pct_nfl = nfl["fgm"].sum() / nfl["fga"].sum() if nfl["fga"].sum() > 0 else np.nan
    fg3_pct_fl = fl["fg3m"].sum() / fl["fg3a"].sum() if fl["fg3a"].sum() > 0 else np.nan
    fg3_pct_nfl = nfl["fg3m"].sum() / nfl["fg3a"].sum() if nfl["fg3a"].sum() > 0 else np.nan

    fta_fga_fl = fl["fta"].sum() / fl["fga"].sum() if fl["fga"].sum() > 0 else np.nan
    fta_fga_nfl = nfl["fta"].sum() / nfl["fga"].sum() if nfl["fga"].sum() > 0 else np.nan

    fg3a_fga_fl = fl["fg3a"].sum() / fl["fga"].sum() if fl["fga"].sum() > 0 else np.nan
    fg3a_fga_nfl = nfl["fg3a"].sum() / nfl["fga"].sum() if nfl["fga"].sum() > 0 else np.nan

    ast_tov_fl = fl["ast"].sum() / fl["tov"].sum() if fl["tov"].sum() > 0 else np.nan
    ast_tov_nfl = nfl["ast"].sum() / nfl["tov"].sum() if nfl["tov"].sum() > 0 else np.nan

    pts_36_drop = pts_36_nfl - pts_36_fl
    possessions_lost = (fga_36_nfl - fga_36_fl) + 0.44 * (fta_36_nfl - fta_36_fl)
    pts_per_poss = (
        pts_36_nfl / (fga_36_nfl + 0.44 * fta_36_nfl)
        if (fga_36_nfl + 0.44 * fta_36_nfl) > 0
        else 1.1
    )
    vol_component = possessions_lost * pts_per_poss
    vol_share = min(1.0, vol_component / pts_36_drop) if pts_36_drop > 0 else np.nan

    return {
        "vol_share": vol_share,
        "eff_share": 1.0 - vol_share if vol_share is not None and not np.isnan(vol_share) else np.nan,
        "n_floor": len(fl),
        "n_nonfloor": len(nfl),
        "min_floor": fl["minutes"].mean(),
        "min_nonfloor": nfl["minutes"].mean(),
        "min_delta": fl["minutes"].mean() - nfl["minutes"].mean(),
        "fga_36_delta": fga_36_fl - fga_36_nfl,
        "fta_36_delta": fta_36_fl - fta_36_nfl,
        "fg3a_36_delta": fg3a_36_fl - fg3a_36_nfl,
        "tov_36_delta": tov_36_fl - tov_36_nfl,
        "ast_36_delta": ast_36_fl - ast_36_nfl,
        "pts_36_delta": pts_36_fl - pts_36_nfl,
        "fg_pct_delta": (fg_pct_fl or 0) - (fg_pct_nfl or 0),
        "fta_fga_delta": (fta_fga_fl or 0) - (fta_fga_nfl or 0),
        "fg3a_fga_delta": (fg3a_fga_fl or 0) - (fg3a_fga_nfl or 0),
        "ast_tov_delta": (ast_tov_fl or 0) - (ast_tov_nfl or 0),
        "pts_36_floor": pts_36_fl,
        "pts_36_nonfloor": pts_36_nfl,
        "r_min_gs": pd.concat([fl, nfl], ignore_index=True)["minutes"].corr(
            pd.concat([fl, nfl], ignore_index=True)["game_score"]
        ) if len(fl) > 2 and len(nfl) > 2 else np.nan,
    }


def classify_mechanism(vol_share: float) -> str:
    if pd.isna(vol_share):
        return "unknown"
    if vol_share > 0.55:
        return "shrinker"
    if vol_share < 0.35:
        return "forcer"
    return "mixed"


def run_pillar1(df: pd.DataFrame) -> None:
    rs = df[~df["is_playoff"]].copy()

    rs_rows = []
    for player, grp in rs.groupby("player_name"):
        valid = grp.dropna(subset=["game_score", "minutes"])
        if len(valid) < 50:
            continue

        fl = valid[valid["is_floor_primary"]]
        nfl = valid[~valid["is_floor_primary"]]
        if len(fl) < 10:
            logger.warning("%s has only %d RS floor games — results noisy", player, len(fl))
            continue

        metrics = compute_vol_share(fl, nfl)
        metrics["player"] = player
        metrics["player_group"] = config.PLAYER_GROUP.get(player, "")
        metrics["context"] = "RS"
        metrics["mechanism"] = classify_mechanism(metrics["vol_share"])
        rs_rows.append(metrics)

    rs_profiles = pd.DataFrame(rs_rows)

    po_profiles = pd.read_csv(config.PROCESSED_DIR / "screen_e_results.csv")
    po_profiles = po_profiles.rename(columns={"vol_share": "po_vol_share", "mechanism": "po_mechanism"})
    po_profiles["context"] = "PO"

    # Merge on player
    po_subset = po_profiles[["player", "player_group", "po_vol_share", "po_mechanism", "po_n_games", "n_floor"]].copy()
    po_subset = po_subset.rename(columns={"n_floor": "po_n_floor"})

    merged = rs_profiles.merge(po_subset, on=["player", "player_group"], how="inner")

    rs_profiles.to_csv(config.PROCESSED_DIR / "pillar1_rs_profiles.csv", index=False)

    # === Correlation test ===
    valid = merged.dropna(subset=["vol_share", "po_vol_share"])
    n = len(valid)

    print("\n" + "=" * 70)
    print("PILLAR 1: FAILURE MODE STABILITY TEST")
    print("=" * 70)
    print(f"\nPlayers with both RS and PO profiles: {n}")

    print("\n--- RS vs Playoff: vol_share comparison ---\n")
    print(merged[[
        "player", "player_group",
        "vol_share", "mechanism",
        "po_vol_share", "po_mechanism",
        "n_floor", "po_n_floor",
    ]].to_string(index=False))

    if n >= 4:
        r, p = stats.pearsonr(valid["vol_share"], valid["po_vol_share"])
        r_spearman, p_spearman = stats.spearmanr(valid["vol_share"], valid["po_vol_share"])

        print(f"\n--- Stability correlation ---\n")
        print(f"  Pearson  r = {r:.3f}  p = {p:.4f}")
        print(f"  Spearman ρ = {r_spearman:.3f}  p = {p_spearman:.4f}")
        print(f"  n = {n}")

        # Mechanism concordance
        concordant = (valid["mechanism"] == valid["po_mechanism"]).sum()
        print(f"\n  Mechanism concordance: {concordant}/{n} ({concordant/n:.0%})")

        # One-directional test: is the correlation positive?
        # If failure mode is a trait, RS should predict PO directionally
        if p < 0.05:
            print(f"\n  *** SIGNIFICANT at α = 0.05 — failure mode is a stable trait ***")
        elif p < 0.10:
            print(f"\n  ** BORDERLINE (p < 0.10) — suggestive of stability **")
        else:
            print(f"\n  Not significant at α = 0.10")

        # Sensitivity: drop players with <10 PO floor games
        ample = valid[valid["po_n_floor"] >= 10]
        if len(ample) >= 4 and len(ample) < n:
            r_amp, p_amp = stats.pearsonr(ample["vol_share"], ample["po_vol_share"])
            print(f"\n--- Sensitivity: players with ≥10 PO floor games ({len(ample)}/{n}) ---")
            print(f"  Pearson  r = {r_amp:.3f}  p = {p_amp:.4f}")

        # Paired differences: does vol_share systematically shift RS → PO?
        diff = valid["po_vol_share"] - valid["vol_share"]
        t_diff, p_diff = stats.ttest_1samp(diff, 0)
        print(f"\n--- Paired shift: PO vol_share − RS vol_share ---")
        print(f"  Mean shift = {diff.mean():+.3f}")
        print(f"  t = {t_diff:.3f}  p = {p_diff:.4f}")
        if p_diff < 0.05:
            direction = "HIGHER" if diff.mean() > 0 else "LOWER"
            print(f"  Playoff vol_share is systematically {direction} than RS")
        else:
            print(f"  No systematic shift between RS and PO vol_share")

    # Full detail table
    detail = merged[[
        "player", "player_group",
        "vol_share", "eff_share", "mechanism",
        "po_vol_share", "po_mechanism",
        "min_delta", "fga_36_delta", "fta_36_delta", "ast_36_delta",
        "n_floor", "po_n_floor",
    ]].copy()
    detail = detail.sort_values("vol_share", ascending=False)
    print(f"\n--- Full RS profile detail ---\n")
    print(detail.to_string(index=False))

    # Save merged stability results
    stability = merged.copy()
    if n >= 4:
        r_val, p_val = stats.pearsonr(valid["vol_share"], valid["po_vol_share"])
        stability.attrs["pearson_r"] = r_val
        stability.attrs["pearson_p"] = p_val
    stability.to_csv(config.PROCESSED_DIR / "pillar1_stability.csv", index=False)
    logger.info("Saved pillar1_stability.csv and pillar1_rs_profiles.csv")


def main() -> None:
    df = pd.read_csv(config.PROCESSED_DIR / "analysis_table.csv", low_memory=False)
    run_pillar1(df)


if __name__ == "__main__":
    main()
