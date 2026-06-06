"""Screen A: variance shift test (floor rate vs mean decline)."""

from __future__ import annotations

import argparse
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


def run_screen(df: pd.DataFrame, floor_col: str = "is_floor_primary") -> pd.DataFrame:
    rows = []
    for player, grp in df.groupby("player_name"):
        rs = grp[~grp["is_playoff"]]
        po = grp[grp["is_playoff"]]
        if rs.empty or po.empty:
            continue

        rs_floor = rs[floor_col].mean()
        po_floor = po[floor_col].mean()
        rs_mean = rs["game_score"].mean()
        po_mean = po["game_score"].mean()

        floor_rate_ratio = po_floor / rs_floor if rs_floor > 0 else np.nan
        mean_ratio = po_mean / rs_mean if rs_mean != 0 else np.nan
        variance_shift_ratio = (
            floor_rate_ratio / mean_ratio if mean_ratio and not np.isnan(mean_ratio) else np.nan
        )

        table = pd.crosstab(grp["is_playoff"], grp[floor_col])
        try:
            if (table.values < 5).any():
                _, p_chi = stats.fisher_exact(table.values)
                chi2_stat = np.nan
            else:
                chi2_stat, p_chi, _, _ = stats.chi2_contingency(table.values)
        except Exception:
            chi2_stat, p_chi = np.nan, np.nan

        tstat, p_ttest = stats.ttest_ind(
            rs["game_score"].dropna(),
            po["game_score"].dropna(),
            equal_var=False,
        )

        rows.append(
            {
                "player": player,
                "player_group": config.PLAYER_GROUP.get(player, ""),
                "rs_n_games": len(rs),
                "po_n_games": len(po),
                "rs_floor_rate": rs_floor,
                "po_floor_rate": po_floor,
                "floor_rate_increase": po_floor - rs_floor,
                "floor_rate_ratio": floor_rate_ratio,
                "rs_mean_gs": rs_mean,
                "po_mean_gs": po_mean,
                "mean_decline": rs_mean - po_mean,
                "mean_ratio": mean_ratio,
                "variance_shift_ratio": variance_shift_ratio,
                "chi2_stat": chi2_stat,
                "chi2_pvalue": p_chi,
                "ttest_stat": tstat,
                "ttest_pvalue": p_ttest,
            }
        )
    return pd.DataFrame(rows)


def print_summary(results: pd.DataFrame) -> None:
    sig = results[
        (results["variance_shift_ratio"] > 1) & (results["chi2_pvalue"] < 0.05)
    ]
    print("\n=== Screen A: Variance shift (primary threshold) ===")
    if sig.empty:
        print("No players with variance_shift_ratio > 1 and chi2 p < 0.05")
    else:
        print(sig.sort_values("variance_shift_ratio", ascending=False).to_string(index=False))

    harden = results[results["player"] == "James Harden"]
    if not harden.empty:
        h = harden.iloc[0]
        print(
            f"\nHarden: floor_rate {h['rs_floor_rate']:.1%} RS -> {h['po_floor_rate']:.1%} PO, "
            f"variance_shift_ratio={h['variance_shift_ratio']:.2f}, "
            f"chi2 p={h['chi2_pvalue']:.4f}"
        )


def main() -> None:
    path = config.PROCESSED_DIR / "analysis_table.csv"
    if not path.exists():
        raise FileNotFoundError(f"Run features first: {path}")
    df = pd.read_csv(path)
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    primary = run_screen(df, "is_floor_primary")
    primary.to_csv(config.PROCESSED_DIR / "screen_a_results.csv", index=False)
    secondary = run_screen(df, "is_floor_secondary")
    secondary.to_csv(config.PROCESSED_DIR / "screen_a_results_secondary.csv", index=False)
    print_summary(primary)


if __name__ == "__main__":
    main()
