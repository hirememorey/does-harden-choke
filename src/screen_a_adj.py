"""Screen A (Opponent-Adjusted): variance shift test with opponent quality control.

Extends Screen A by:
1. Stratifying floor-game rates by opponent defensive quality
2. Running logistic regression: is_floor ~ is_playoff + def_rating + player FE
3. Computing opponent-adjusted floor-rate differences

The raw Pass 1 finding was Harden floor-rate increase p = 0.067.
This screen asks: does that hold after controlling for the fact
that playoff opponents are systematically better defensively?
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def opponent_quality_stratification(df: pd.DataFrame) -> None:
    po = df[df["is_playoff"] & df["def_rating_y"].notna()].copy()

    def_rating_bins = pd.qcut(po["def_rating_y"], q=3, labels=["weak", "average", "strong"])
    po["opp_quality"] = def_rating_bins

    print("\n=== Opponent Quality Stratification ===\n")
    print("Floor-game rate by opponent quality tier (playoffs only):\n")
    print(f"{'Player':<22} {'Weak':>8} {'Average':>8} {'Strong':>8} {'Overall':>8}")
    print("-" * 60)

    for player in sorted(po["player_name"].unique()):
        sub = po[po["player_name"] == player]
        if len(sub) < 10:
            continue
        rates = {}
        for tier in ["weak", "average", "strong"]:
            tier_games = sub[sub["opp_quality"] == tier]
            if len(tier_games) >= 3:
                rates[tier] = f"{tier_games['is_floor_primary'].mean():.0%} (n={len(tier_games)})"
            else:
                rates[tier] = "—"
        overall = f"{sub['is_floor_primary'].mean():.0%} (n={len(sub)})"
        print(f"{player:<22} {rates.get('weak', '—'):>8} {rates.get('average', '—'):>8} {rates.get('strong', '—'):>8} {overall:>8}")

    print("\nGroup aggregates:")
    for group_label in ["A", "B"]:
        grp = po[po["player_group"] == group_label]
        if grp.empty:
            continue
        rates = {}
        for tier in ["weak", "average", "strong"]:
            tier_games = grp[grp["opp_quality"] == tier]
            if len(tier_games) >= 3:
                rates[tier] = f"{tier_games['is_floor_primary'].mean():.0%} (n={len(tier_games)})"
            else:
                rates[tier] = "—"
        overall = f"{grp['is_floor_primary'].mean():.0%} (n={len(grp)})"
        print(f"  Group {group_label}:        {rates.get('weak', '—'):>8} {rates.get('average', '—'):>8} {rates.get('strong', '—'):>8} {overall:>8}")


def logistic_regression_adjusted(df: pd.DataFrame) -> pd.DataFrame:
    po = df[df["is_playoff"] & df["def_rating_y"].notna()].copy()
    rs = df[~df["is_playoff"] & df["def_rating_y"].notna()].copy()

    combined = pd.concat([po, rs], ignore_index=True)
    combined = combined[combined["def_rating_y"].notna()].copy()

    # Center def_rating for interpretability
    def_mean = combined["def_rating_y"].mean()
    combined["def_rating_centered"] = combined["def_rating_y"] - def_mean

    combined["is_playoff_num"] = combined["is_playoff"].astype(float)

    player_dummies = pd.get_dummies(combined["player_name"], prefix="player", drop_first=True, dtype=float)
    combined = pd.concat([combined, player_dummies], axis=1)
    feature_cols = ["is_playoff_num", "def_rating_centered"] + list(player_dummies.columns)
    X = combined[feature_cols].astype(float)
    X = sm.add_constant(X)
    y = combined["is_floor_primary"].astype(float)

    model = sm.Logit(y, X).fit(disp=0, maxiter=200, method="lbfgs")

    print("\n=== Logistic Regression: is_floor ~ is_playoff + def_rating + player FE ===\n")
    print(model.summary2().tables[1].to_string())

    playoff_coef = model.params.get("is_playoff_num", np.nan)
    playoff_pval = model.pvalues.get("is_playoff_num", np.nan)
    playoff_odds = np.exp(playoff_coef) if not np.isnan(playoff_coef) else np.nan
    def_coef = model.params.get("def_rating_centered", np.nan)
    def_pval = model.pvalues.get("def_rating_centered", np.nan)
    def_odds = np.exp(def_coef) if not np.isnan(def_coef) else np.nan

    print(f"\nKey coefficients:")
    print(f"  is_playoff:     coef={playoff_coef:+.4f}  p={playoff_pval:.4f}  OR={playoff_odds:.3f}")
    print(f"  def_rating:     coef={def_coef:+.4f}  p={def_pval:.4f}  OR={def_odds:.3f}")

    if playoff_pval < 0.05:
        print("\n  → Playoff floor-game increase is SIGNIFICANT after opponent adjustment.")
    elif playoff_pval < 0.10:
        print("\n  → Playoff floor-game increase is BORDERLINE after opponent adjustment (p < 0.10).")
    else:
        print("\n  → Playoff floor-game increase is NOT significant after opponent adjustment.")

    if def_pval < 0.05:
        print(f"  → Opponent defensive quality IS a significant predictor (each +1 DEF_RTNG point increases floor-game odds by {(def_odds-1)*100:.1f}%).")
    else:
        print(f"  → Opponent defensive quality is NOT a significant predictor of floor games.")

    # Per-player adjusted rates
    print("\n=== Per-Player Opponent-Adjusted Floor Rates ===\n")
    rows = []
    for player in sorted(po["player_name"].unique()):
        sub_po = po[po["player_name"] == player]
        sub_rs = rs[rs["player_name"] == player]
        if sub_po.empty:
            continue

        po_floor_raw = sub_po["is_floor_primary"].mean()
        po_def_mean = sub_po["def_rating_y"].mean()
        rs_floor_raw = sub_rs["is_floor_primary"].mean() if not sub_rs.empty else np.nan

        avg_def = combined["def_rating_y"].mean()
        n_po = len(sub_po)
        delta_raw = po_floor_raw - rs_floor_raw if not np.isnan(rs_floor_raw) else np.nan

        # Simple adjustment: what would the playoff floor rate be if opponents
        # had league-average defense instead of actual playoff defense?
        # Use the logistic model coefficient to back out the opponent effect
        def_delta = po_def_mean - avg_def
        opponent_effect = def_delta * def_coef if not np.isnan(def_coef) else 0
        po_floor_adjusted_logit = np.log(po_floor_raw / (1 - po_floor_raw)) if 0 < po_floor_raw < 1 else 0
        po_floor_adjusted_logit -= opponent_effect
        po_floor_adjusted = 1 / (1 + np.exp(-po_floor_adjusted_logit))

        delta_adjusted = po_floor_adjusted - rs_floor_raw if not np.isnan(rs_floor_raw) else np.nan

        rows.append({
            "player": player,
            "player_group": config.PLAYER_GROUP.get(player, ""),
            "n_po": n_po,
            "po_avg_defrtg": round(po_def_mean, 1),
            "rs_floor_rate": rs_floor_raw,
            "po_floor_rate_raw": po_floor_raw,
            "po_floor_rate_adj": po_floor_adjusted,
            "delta_raw": delta_raw,
            "delta_adjusted": delta_adjusted,
            "opponent_adjustment_pp": (po_floor_raw - po_floor_adjusted) * 100,
        })

    results = pd.DataFrame(rows)
    results = results.sort_values("delta_adjusted", ascending=False)

    print(f"{'Player':<22} {'Grp':>3} {'PO':>4} {'Avg Def':>7} {'RS Floor':>8} {'PO Raw':>8} {'PO Adj':>8} {'Δ Raw':>7} {'Δ Adj':>7} {'Opp Δpp':>7}")
    print("-" * 92)
    for _, row in results.iterrows():
        print(f"{row['player']:<22} {row['player_group']:>3} {row['n_po']:>4} {row['po_avg_defrtg']:>7.1f} "
              f"{row['rs_floor_rate']:>8.1%} {row['po_floor_rate_raw']:>8.1%} {row['po_floor_rate_adj']:>8.1%} "
              f"{row['delta_raw']:>+7.1%} {row['delta_adjusted']:>+7.1%} {row['opponent_adjustment_pp']:>+7.1f}")

    results.to_csv(config.PROCESSED_DIR / "screen_a_adj_results.csv", index=False)
    print(f"\nSaved to {config.PROCESSED_DIR / 'screen_a_adj_results.csv'}")

    return results


def harden_deep_dive(df: pd.DataFrame) -> None:
    po = df[df["is_playoff"] & df["def_rating_y"].notna()].copy()
    harden_po = po[po["player_name"] == "James Harden"]

    if harden_po.empty:
        return

    print("\n=== Harden Deep Dive: Opponent Quality vs Floor Games ===\n")

    def_rating_bins = pd.qcut(harden_po["def_rating_y"], q=3, labels=["weak", "average", "strong"])
    harden_po_copy = harden_po.copy()
    harden_po_copy["opp_quality"] = def_rating_bins

    for tier in ["weak", "average", "strong"]:
        tier_games = harden_po_copy[harden_po_copy["opp_quality"] == tier]
        if tier_games.empty:
            continue
        floor_count = tier_games["is_floor_primary"].sum()
        floor_rate = tier_games["is_floor_primary"].mean()
        avg_def = tier_games["def_rating_y"].mean()
        print(f"  vs {tier:>7} defense ({avg_def:.1f} avg): {floor_count}/{len(tier_games)} floor games ({floor_rate:.0%})")

    rs = df[~df["is_playoff"] & (df["player_name"] == "James Harden")]
    rs_floor = rs["is_floor_primary"].mean()
    print(f"\n  Regular-season floor rate: {rs_floor:.1%}")
    print(f"  Playoff floor rate (raw):   {harden_po['is_floor_primary'].mean():.1%}")

    # Average opponent defense faced in playoffs
    po_def = harden_po["def_rating_y"].mean()
    print(f"  Average opponent DEF_RATING in playoffs: {po_def:.1f}")
    print(f"  League average DEF_RATING:               {df['def_rating_y'].mean():.1f}")

    # How much does opponent quality explain?
    # Simple OLS: is_floor ~ def_rating in playoffs only
    from statsmodels.api import OLS
    X = sm.add_constant(harden_po[["def_rating_y"]].astype(float))
    y = harden_po["is_floor_primary"].astype(float)
    ols_model = OLS(y, X).fit()
    print(f"\n  Harden OLS (playoffs only): is_floor ~ def_rating")
    print(f"    def_rating coef: {ols_model.params.get('def_rating_y', np.nan):+.4f} (p={ols_model.pvalues.get('def_rating_y', 1):.4f})")
    print(f"    R² = {ols_model.rsquared:.3f}")

    if ols_model.pvalues.get("def_rating_y", 1) < 0.05:
        print("    → Opponent quality SIGNIFICANTLY predicts Harden's floor games")
    else:
        print("    → Opponent quality does NOT significantly predict Harden's floor games")
        print("    → The playoff floor-rate increase is NOT explained by opponent quality")


def main() -> None:
    path = config.PROCESSED_DIR / "analysis_table.csv"
    if not path.exists():
        raise FileNotFoundError(f"Run features first: {path}")

    df = pd.read_csv(path, low_memory=False)

    # Convert is_playoff to bool if needed
    df["is_playoff"] = df["is_playoff"].astype(bool)
    df["is_floor_primary"] = df["is_floor_primary"].astype(bool)

    n_with_def = df["def_rating_y"].notna().sum()
    n_total = len(df)
    print(f"Analysis table: {n_total} rows, {n_with_def} with opponent DEF_RATING ({n_with_def/n_total:.0%} coverage)")

    opponent_quality_stratification(df)
    logistic_regression_adjusted(df)
    harden_deep_dive(df)


if __name__ == "__main__":
    main()
