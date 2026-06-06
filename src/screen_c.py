"""Screen C: peer comparison and Group A vs B tests."""

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


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 2 or len(b) < 2:
        return np.nan
    pooled = np.sqrt(((a.std(ddof=1) ** 2 + b.std(ddof=1) ** 2)) / 2)
    return (a.mean() - b.mean()) / pooled if pooled else np.nan


def main() -> None:
    path = config.PROCESSED_DIR / "screen_a_results.csv"
    if not path.exists():
        raise FileNotFoundError(f"Run screen_a first: {path}")
    a = pd.read_csv(path)

    a["rank_floor_increase"] = a["floor_rate_increase"].rank(ascending=False, method="min")
    a["rank_variance_shift"] = a["variance_shift_ratio"].rank(ascending=False, method="min")

    harden_row = a[a["player"] == "James Harden"]
    if not harden_row.empty:
        pct = 100 * (1 - (harden_row["rank_floor_increase"].iloc[0] - 1) / (len(a) - 1))
        a.loc[a["player"] == "James Harden", "harden_percentile"] = pct

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    a.to_csv(config.PROCESSED_DIR / "screen_c_results.csv", index=False)

    ga = a[a["player_group"] == "A"]
    gb = a[a["player_group"] == "B"]

    u_floor, p_floor = stats.mannwhitneyu(
        ga["floor_rate_increase"],
        gb["floor_rate_increase"],
        alternative="two-sided",
    )
    u_var, p_var = stats.mannwhitneyu(
        ga["variance_shift_ratio"].dropna(),
        gb["variance_shift_ratio"].dropna(),
        alternative="two-sided",
    )

    group_cmp = pd.DataFrame(
        [
            {
                "metric": "floor_rate_increase",
                "group_a_mean": ga["floor_rate_increase"].mean(),
                "group_b_mean": gb["floor_rate_increase"].mean(),
                "mannwhitney_u": u_floor,
                "pvalue": p_floor,
                "cohens_d": cohens_d(
                    ga["floor_rate_increase"].values, gb["floor_rate_increase"].values
                ),
            },
            {
                "metric": "variance_shift_ratio",
                "group_a_mean": ga["variance_shift_ratio"].mean(),
                "group_b_mean": gb["variance_shift_ratio"].mean(),
                "mannwhitney_u": u_var,
                "pvalue": p_var,
                "cohens_d": cohens_d(
                    ga["variance_shift_ratio"].dropna().values,
                    gb["variance_shift_ratio"].dropna().values,
                ),
            },
        ]
    )
    group_cmp.to_csv(config.PROCESSED_DIR / "screen_c_group_comparison.csv", index=False)

    print("\n=== Screen C: Peer comparison ===")
    print(a.sort_values("rank_floor_increase")[["player", "player_group", "floor_rate_increase", "rank_floor_increase"]].to_string(index=False))
    if not harden_row.empty:
        print(
            f"\nHarden rank (floor increase): {int(harden_row['rank_floor_increase'].iloc[0])}/{len(a)}"
        )
    print("\nGroup A vs B:")
    print(group_cmp.to_string(index=False))


if __name__ == "__main__":
    main()
