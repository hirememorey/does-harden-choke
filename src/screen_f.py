"""Screen F: Floor-Game Trigger Classification.

Primary contribution of the project. Classifies each player's floor-game
trigger pattern — WHY floor games happen, not WHAT happens when they do.

The contractor/forcer mechanism taxonomy (Screen E) answered its question
but is not the primary axis. Mechanism (contraction vs forcing) and
frequency (how often floor games occur) are independent — Butler contracts
like Harden but almost never floors in the playoffs. The differentiator
is the TRIGGER: what conditions produce floor games.

Trigger types:
  1. Opponent-independent  — floors vs weak and strong D alike (Harden)
  2. Scheme-dependent      — floors only vs elite D (SGA, Trae)
  3. Disengagement          — floors vs weak D, rises vs strong D (Butler, Wall)
  4. Bimodal                — floors vs both weak and strong D, not average (DeRozan)
  5. Standard               — mild opponent gradient, no distinctive pattern

Classification uses:
  - Gradient: weak_floor - strong_floor (tertile split)
  - OLS: is_floor ~ opponent_defrtg (coefficient and p-value)
  - Bimodal check: both weak and strong tertiles elevated vs average
  - Floor-rate delta: PO - RS (context for frequency axis)

Output:
  - data/processed/screen_f_results.csv
  - Console report
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _def_col(df: pd.DataFrame) -> str:
    if "opponent_defrtg" in df.columns and df["opponent_defrtg"].notna().sum() > 0:
        return "opponent_defrtg"
    return "def_rating_y"


def compute_trigger_profile(
    po_sub: pd.DataFrame,
    rs_sub: pd.DataFrame,
    col: str,
    min_games: int = 10,
) -> dict | None:
    if len(po_sub) < min_games:
        return None

    rs_floor = rs_sub["is_floor_primary"].mean() if len(rs_sub) > 0 else np.nan
    po_floor = po_sub["is_floor_primary"].mean()

    q33 = po_sub[col].quantile(0.33)
    q67 = po_sub[col].quantile(0.67)
    weak = po_sub[po_sub[col] <= q33]
    avg = po_sub[(po_sub[col] > q33) & (po_sub[col] <= q67)]
    strong = po_sub[po_sub[col] > q67]

    weak_floor = weak["is_floor_primary"].mean() if len(weak) >= 3 else np.nan
    avg_floor = avg["is_floor_primary"].mean() if len(avg) >= 3 else np.nan
    strong_floor = strong["is_floor_primary"].mean() if len(strong) >= 3 else np.nan

    if not np.isnan(weak_floor) and not np.isnan(strong_floor):
        gradient = weak_floor - strong_floor
    else:
        gradient = np.nan

    weak_n = len(weak)
    strong_n = len(strong)
    weak_mean_def = weak[col].mean() if len(weak) > 0 else np.nan
    strong_mean_def = strong[col].mean() if len(strong) > 0 else np.nan

    def_coef = np.nan
    def_pval = 1.0
    def_r2 = np.nan
    if len(po_sub) >= 20:
        X = sm.add_constant(po_sub[[col]].astype(float))
        y = po_sub["is_floor_primary"].astype(float)
        ols = sm.OLS(y, X).fit()
        def_coef = ols.params.get(col, np.nan)
        def_pval = ols.pvalues.get(col, 1.0)
        def_r2 = ols.rsquared

    is_bimodal = False
    if not np.isnan(weak_floor) and not np.isnan(avg_floor) and not np.isnan(strong_floor):
        if weak_floor > avg_floor and strong_floor > avg_floor:
            is_bimodal = True

    return {
        "n_po": len(po_sub),
        "n_rs": len(rs_sub),
        "rs_floor_rate": rs_floor,
        "po_floor_rate": po_floor,
        "delta_floor": po_floor - rs_floor if not np.isnan(rs_floor) else np.nan,
        "weak_floor": weak_floor,
        "avg_floor": avg_floor,
        "strong_floor": strong_floor,
        "gradient": gradient,
        "weak_n": weak_n,
        "strong_n": strong_n,
        "weak_mean_def": weak_mean_def,
        "strong_mean_def": strong_mean_def,
        "def_coef": def_coef,
        "def_pval": def_pval,
        "def_r2": def_r2,
        "is_bimodal": is_bimodal,
    }


def classify_trigger(profile: dict) -> str:
    if profile is None:
        return "unknown"

    gradient = profile.get("gradient", np.nan)
    def_coef = profile.get("def_coef", np.nan)
    def_pval = profile.get("def_pval", 1.0)
    is_bimodal = profile.get("is_bimodal", False)
    weak_floor = profile.get("weak_floor", np.nan)
    strong_floor = profile.get("strong_floor", np.nan)
    avg_floor = profile.get("avg_floor", np.nan)
    po_floor = profile.get("po_floor_rate", np.nan)
    delta_floor = profile.get("delta_floor", np.nan)

    if np.isnan(gradient):
        return "unknown"

    # 1. Scheme-dependent: gradient strongly negative (floors vs strong D),
    #    OLS significant or near-significant with positive def_coef
    if gradient <= -0.15 and (def_pval < 0.10 or (not np.isnan(def_coef) and def_coef > 0.01)):
        return "scheme-dependent"

    # 2. Disengagement: gradient strongly positive (floors vs weak D, not strong),
    #    strong_floor materially lower than weak_floor, or strong_floor near-zero
    if gradient >= 0.15:
        if not np.isnan(strong_floor) and strong_floor < po_floor * 0.5:
            return "disengagement"
        if not np.isnan(weak_floor) and not np.isnan(strong_floor) and weak_floor - strong_floor > 0.15:
            return "disengagement"

    # 3. Opponent-independent: weak_floor materially elevated (floors even against weak D).
    #    The defining feature: you can't scheme away the trigger because bad teams trigger it too.
    #    Require weak_floor well above overall AND strong_floor also not suppressed.
    if not np.isnan(weak_floor) and not np.isnan(strong_floor):
        weak_elevated = weak_floor > max(po_floor + 0.05, 0.20) if not np.isnan(po_floor) else False
        strong_present = strong_floor > 0.10
        if weak_elevated and strong_present:
            return "opponent-independent"

    # 4. Bimodal: genuinely U-shaped — both weak and strong elevated, average materially lower
    #    Require weak and strong both > average by at least 5pp
    if is_bimodal and not np.isnan(avg_floor) and not np.isnan(weak_floor) and not np.isnan(strong_floor):
        if weak_floor > avg_floor + 0.05 and strong_floor > avg_floor + 0.05:
            return "bimodal"

    # 5. Disengagement (soft): positive gradient, weak_floor elevated, but strong_floor
    #    not as extreme as the hard check
    if gradient > 0.10 and not np.isnan(weak_floor) and weak_floor > strong_floor + 0.05:
        return "disengagement"

    # Default
    return "standard"


def run_screen(df: pd.DataFrame) -> pd.DataFrame:
    col = _def_col(df)
    po = df[df["is_playoff"] & df[col].notna()].copy()

    rows = []
    for player in sorted(po["player_name"].unique()):
        po_sub = po[po["player_name"] == player]
        rs_sub = df[(df["player_name"] == player) & ~df["is_playoff"]]

        profile = compute_trigger_profile(po_sub, rs_sub, col)
        if profile is None:
            continue

        trigger = classify_trigger(profile)
        profile["player"] = player
        profile["player_group"] = config.PLAYER_GROUP.get(player, "")
        profile["trigger"] = trigger
        rows.append(profile)

    results = pd.DataFrame(rows)
    results.to_csv(config.PROCESSED_DIR / "screen_f_results.csv", index=False)
    return results


def print_report(results: pd.DataFrame) -> None:
    print("\n" + "=" * 100)
    print("SCREEN F: FLOOR-GAME TRIGGER CLASSIFICATION")
    print("=" * 100)
    print()
    print("Primary axis: WHY floor games happen, not WHAT happens when they do.")
    print("Mechanism (contraction/forcing) is secondary — two players can share")
    print("the same mechanism with completely different trigger profiles.")
    print()

    trigger_order = [
        "opponent-independent",
        "scheme-dependent",
        "disengagement",
        "bimodal",
        "standard",
        "unknown",
    ]
    trigger_desc = {
        "opponent-independent": "Floors vs weak and strong D alike — unpredictable, not gameplan-able",
        "scheme-dependent": "Floors only vs elite D — gameplan-able, elite D suppresses",
        "disengagement": "Floors vs weak D, rises to challenge — system-dependent, keep engaged",
        "bimodal": "Floors vs both weak and strong D, not average — two different triggers",
        "standard": "Mild opponent gradient, no distinctive pattern",
        "unknown": "Insufficient data",
    }

    for trigger_type in trigger_order:
        subset = results[results["trigger"] == trigger_type]
        if subset.empty:
            continue

        print(f"--- {trigger_type.upper()} ---")
        print(f"  {trigger_desc[trigger_type]}")
        print()
        print(f"  {'Player':<25} {'PO':>4} {'RS→PO':>8} {'Weak':>6} {'Avg':>6} {'Strong':>6} {'Grad':>6} {'def_p':>6}")
        print(f"  {'-'*25} {'----':>4} {'------':>8} {'----':>6} {'---':>6} {'------':>6} {'----':>6} {'----':>6}")
        for _, r in subset.iterrows():
            delta = f"{r['delta_floor']:+.1%}" if not np.isnan(r['delta_floor']) else "—"
            weak = f"{r['weak_floor']:.0%}" if not np.isnan(r['weak_floor']) else "—"
            avg = f"{r['avg_floor']:.0%}" if not np.isnan(r['avg_floor']) else "—"
            strong = f"{r['strong_floor']:.0%}" if not np.isnan(r['strong_floor']) else "—"
            grad = f"{r['gradient']:+.2f}" if not np.isnan(r['gradient']) else "—"
            dp = f"{r['def_pval']:.3f}" if not np.isnan(r['def_pval']) else "—"
            print(f"  {r['player']:<25} {r['n_po']:>4} {delta:>8} {weak:>6} {avg:>6} {strong:>6} {grad:>6} {dp:>6}")
        print()

    # Summary table
    print("=== TRIGGER SUMMARY ===")
    print()
    summary = results.groupby("trigger").agg(
        n_players=("player", "count"),
        mean_delta=("delta_floor", "mean"),
        mean_gradient=("gradient", "mean"),
    ).reindex(trigger_order).dropna(how="all")

    for trigger_type, row in summary.iterrows():
        if pd.isna(row["n_players"]):
            continue
        players_list = results[results["trigger"] == trigger_type]["player"].tolist()
        print(f"  {trigger_type:<22} {int(row['n_players'])} players  "
              f"mean Δ={row['mean_delta']:+.1%}  mean grad={row['mean_gradient']:+.2f}  "
              f"[{', '.join(players_list)}]")
    print()

    # Key contrast
    print("=== KEY CONTRAST: SAME MECHANISM, DIFFERENT TRIGGER ===")
    print()
    butler = results[results["player"] == "Jimmy Butler"]
    harden = results[results["player"] == "James Harden"]
    if not butler.empty and not harden.empty:
        b, h = butler.iloc[0], harden.iloc[0]
        print(f"  Both contract in floor games. But:")
        print(f"  Harden: {h['trigger']} — weak={h['weak_floor']:.0%}, strong={h['strong_floor']:.0%}, Δ floor={h['delta_floor']:+.1%}")
        print(f"  Butler: {b['trigger']} — weak={b['weak_floor']:.0%}, strong={b['strong_floor']:.0%}, Δ floor={b['delta_floor']:+.1%}")
        print()
        print(f"  Same mechanism. Opposite frequency. Opposite scouting advice.")


def main() -> None:
    path = config.PROCESSED_DIR / "analysis_table.csv"
    if not path.exists():
        raise FileNotFoundError(f"Run features first: {path}")

    df = pd.read_csv(path, low_memory=False)
    df["is_playoff"] = df["is_playoff"].astype(bool)
    df["is_floor_primary"] = df["is_floor_primary"].astype(bool)

    results = run_screen(df)
    print_report(results)

    out = config.PROCESSED_DIR / "screen_f_results.csv"
    print(f"Saved: {out}")
    logger.info("Done")


if __name__ == "__main__":
    main()
