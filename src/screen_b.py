"""Screen B: within-series floor-game gradient."""

from __future__ import annotations

import argparse
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

BUCKETS = {"early": (1, 2), "mid": (3, 4), "late": (5, 7)}
BUCKET_ORDINAL = {"early": 1, "mid": 2, "late": 3}


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return np.nan, np.nan
    p = successes / n
    denom = 1 + z**2 / n
    centre = p + z**2 / (2 * n)
    margin = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    lower = (centre - margin) / denom
    upper = (centre + margin) / denom
    return lower, upper


def assign_bucket(game_num: float) -> str | None:
    if pd.isna(game_num):
        return None
    g = int(game_num)
    for name, (lo, hi) in BUCKETS.items():
        if lo <= g <= hi:
            return name
    return None


def floor_rate_table(po: pd.DataFrame, group_col: str | None = None) -> pd.DataFrame:
    rows = []
    groups = po.groupby(group_col) if group_col else [(None, po)]
    for key, grp in groups:
        label = key if key is not None else grp["player_name"].iloc[0] if len(grp) else "?"
        for bucket in ("early", "mid", "late"):
            sub = grp[grp["series_bucket"] == bucket]
            n = len(sub)
            k = sub["is_floor_primary"].sum() if n else 0
            lo, hi = wilson_ci(int(k), n)
            rows.append(
                {
                    "player": label,
                    "series_bucket": bucket,
                    "n_games": n,
                    "floor_rate": k / n if n else np.nan,
                    "ci_lower": lo,
                    "ci_upper": hi,
                }
            )
    return pd.DataFrame(rows)


def trend_test(po: pd.DataFrame) -> tuple[float, float]:
    """Logistic regression: floor ~ ordinal bucket."""
    df = po.dropna(subset=["series_bucket"]).copy()
    if df.empty:
        return np.nan, np.nan
    df["bucket_ord"] = df["series_bucket"].map(BUCKET_ORDINAL)
    y = df["is_floor_primary"].astype(int)
    X = sm.add_constant(df["bucket_ord"])
    try:
        model = sm.Logit(y, X).fit(disp=0)
        return float(model.params["bucket_ord"]), float(model.pvalues["bucket_ord"])
    except Exception:
        return np.nan, np.nan


def harden_by_game(po: pd.DataFrame) -> pd.DataFrame:
    h = po[po["player_name"] == "James Harden"].copy()
    rows = []
    for g in range(1, 8):
        sub = h[h["series_game_num"] == g]
        n = len(sub)
        k = sub["is_floor_primary"].sum() if n else 0
        lo, hi = wilson_ci(int(k), n)
        rows.append(
            {
                "series_game_num": g,
                "n_games": n,
                "floor_rate": k / n if n else np.nan,
                "ci_lower": lo,
                "ci_upper": hi,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    path = config.PROCESSED_DIR / "analysis_table.csv"
    df = pd.read_csv(path)
    po = df[df["is_playoff"]].copy()
    po = po[po["series_game_num"].notna()]
    po["series_bucket"] = po["series_game_num"].apply(assign_bucket)
    po = po[po["series_bucket"].notna()]

    results = []
    for player, grp in po.groupby("player_name"):
        for bucket in ("early", "mid", "late"):
            sub = grp[grp["series_bucket"] == bucket]
            n = len(sub)
            k = sub["is_floor_primary"].sum() if n else 0
            lo, hi = wilson_ci(int(k), n)
            results.append(
                {
                    "player": player,
                    "player_group": config.PLAYER_GROUP.get(player, ""),
                    "series_bucket": bucket,
                    "n_games": n,
                    "floor_rate": k / n if n else np.nan,
                    "ci_lower": lo,
                    "ci_upper": hi,
                }
            )

    for group_label, names in (("Group A", list(config.GROUP_A)), ("Group B", list(config.GROUP_B))):
        gpo = po[po["player_name"].isin(names)]
        for bucket in ("early", "mid", "late"):
            sub = gpo[gpo["series_bucket"] == bucket]
            n = len(sub)
            k = sub["is_floor_primary"].sum() if n else 0
            lo, hi = wilson_ci(int(k), n)
            results.append(
                {
                    "player": group_label,
                    "player_group": group_label[-1],
                    "series_bucket": bucket,
                    "n_games": n,
                    "floor_rate": k / n if n else np.nan,
                    "ci_lower": lo,
                    "ci_upper": hi,
                }
            )

    out = pd.DataFrame(results)
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(config.PROCESSED_DIR / "screen_b_results.csv", index=False)

    harden_tbl = harden_by_game(po)
    harden_tbl.to_csv(config.PROCESSED_DIR / "screen_b_harden_by_game.csv", index=False)

    coef, pval = trend_test(po[po["player_name"] == "James Harden"])
    coef_all, pval_all = trend_test(po)

    print("\n=== Screen B: Within-series gradient ===")
    print(out[out["player"].isin(["James Harden", "Group A", "Group B"])].to_string(index=False))
    print(f"\nHarden trend (logit ordinal bucket): coef={coef:.3f}, p={pval:.4f}")
    print(f"All players trend: coef={coef_all:.3f}, p={pval_all:.4f}")

    # sensitivity: exclude injury-flagged
    if "is_injury_flagged" in po.columns:
        po_clean = po[~po["is_injury_flagged"]]
        c2, p2 = trend_test(po_clean[po_clean["player_name"] == "James Harden"])
        print(f"Harden trend (excl injury-flagged): coef={c2:.3f}, p={p2:.4f}")


if __name__ == "__main__":
    main()
