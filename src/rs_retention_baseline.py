"""RS retention baselines: floor-game volume retention in RS vs playoffs.

Computes FGA, FTA, minutes, and points retention (floor / non-floor ratios)
for each player in regular season and playoffs. Answers whether contraction
in bad games is a stable trait or playoff-specific.

Output:
  - data/processed/retention_baselines.csv
  - console report with RS vs PO comparison
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
from pillar1_stability import compute_vol_share

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MIN_RS_GAMES = 50
MIN_RS_FLOOR = 10
MIN_PO_GAMES = 10
MIN_PO_FLOOR = 3
FLOOR_MIN_FILTER = 25  # minutes — excludes blowout benchings from floor pool


def per36(col: str, sub: pd.DataFrame) -> float:
    mins = sub["minutes"].mean()
    return sub[col].mean() / mins * 36 if mins > 0 else np.nan


def compute_retention(fl: pd.DataFrame, nfl: pd.DataFrame) -> dict:
    """Retention ratios: floor rate / non-floor rate (1.0 = no change)."""
    fga_36_fl = per36("fga", fl)
    fga_36_nfl = per36("fga", nfl)
    fta_36_fl = per36("fta", fl)
    fta_36_nfl = per36("fta", nfl)
    pts_36_fl = per36("pts", fl)
    pts_36_nfl = per36("pts", nfl)
    ast_36_fl = per36("ast", fl)
    ast_36_nfl = per36("ast", nfl)

    min_fl = fl["minutes"].mean()
    min_nfl = nfl["minutes"].mean()

    fg_pct_fl = fl["fgm"].sum() / fl["fga"].sum() if fl["fga"].sum() > 0 else np.nan
    fg_pct_nfl = nfl["fgm"].sum() / nfl["fga"].sum() if nfl["fga"].sum() > 0 else np.nan
    fta_fga_fl = fl["fta"].sum() / fl["fga"].sum() if fl["fga"].sum() > 0 else np.nan
    fta_fga_nfl = nfl["fta"].sum() / nfl["fga"].sum() if nfl["fga"].sum() > 0 else np.nan

    def ratio(num: float, den: float) -> float:
        return num / den if den and den > 0 and not np.isnan(num) else np.nan

    return {
        "n_floor": len(fl),
        "n_nonfloor": len(nfl),
        "fga_retention": ratio(fga_36_fl, fga_36_nfl),
        "fta_retention": ratio(fta_36_fl, fta_36_nfl),
        "pts_retention": ratio(pts_36_fl, pts_36_nfl),
        "ast_retention": ratio(ast_36_fl, ast_36_nfl),
        "min_retention": ratio(min_fl, min_nfl),
        "fg_pct_floor": fg_pct_fl,
        "fg_pct_nonfloor": fg_pct_nfl,
        "fta_fga_floor": fta_fga_fl,
        "fta_fga_nonfloor": fta_fga_nfl,
        "fta_fga_retention": ratio(fta_fga_fl, fta_fga_nfl),
        "fga_36_floor": fga_36_fl,
        "fga_36_nonfloor": fga_36_nfl,
        "fta_36_floor": fta_36_fl,
        "fta_36_nonfloor": fta_36_nfl,
        "min_floor": min_fl,
        "min_nonfloor": min_nfl,
    }


def player_retention(
    grp: pd.DataFrame,
    *,
    is_playoff: bool,
    floor_min: float | None = None,
) -> dict | None:
    valid = grp.dropna(subset=["game_score", "minutes"])
    min_games = MIN_PO_GAMES if is_playoff else MIN_RS_GAMES
    min_floor = MIN_PO_FLOOR if is_playoff else MIN_RS_FLOOR
    if len(valid) < min_games:
        return None

    fl = valid[valid["is_floor_primary"]]
    if floor_min is not None:
        fl = fl[fl["minutes"] >= floor_min]
    nfl = valid[~valid["is_floor_primary"]]
    if len(fl) < min_floor:
        return None

    retention = compute_retention(fl, nfl)
    vol = compute_vol_share(fl, nfl)
    retention["vol_share"] = vol["vol_share"]
    retention["min_delta"] = vol["min_delta"]
    retention["fta_fga_delta"] = vol["fta_fga_delta"]
    return retention


def run_retention_baselines(df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for player, grp in df.groupby("player_name"):
        player_group = config.PLAYER_GROUP.get(player, "")
        for is_playoff, context in ((False, "RS"), (True, "PO")):
            sub = grp[grp["is_playoff"] == is_playoff]
            for floor_min, variant in ((None, "all"), (FLOOR_MIN_FILTER, "floor_min25")):
                metrics = player_retention(sub, is_playoff=is_playoff, floor_min=floor_min)
                if metrics is None:
                    continue
                rows.append({
                    "player": player,
                    "player_group": player_group,
                    "context": context,
                    "variant": variant,
                    **metrics,
                })

    return pd.DataFrame(rows)


def print_report(wide: pd.DataFrame) -> None:
    print("\n" + "=" * 90)
    print("RS RETENTION BASELINES: floor / non-floor ratios (1.0 = no change)")
    print("=" * 90)

    cols = [
        "player", "player_group",
        "rs_fga_retention", "po_fga_retention", "fga_retention_shift",
        "rs_fta_retention", "po_fta_retention", "fta_retention_shift",
        "rs_min_retention", "po_min_retention",
        "rs_vol_share", "po_vol_share",
        "rs_n_floor", "po_n_floor",
    ]

    print("\n--- All floor games ---\n")
    all_games = wide[wide["variant"] == "all"].copy()
    all_games = all_games.sort_values("fga_retention_shift")
    print(all_games[cols].to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    print("\n--- Floor games with ≥25 minutes (benching excluded) ---\n")
    min25 = wide[wide["variant"] == "floor_min25"].copy()
    min25 = min25.sort_values("fga_retention_shift")
    print(min25[cols].to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    # Key players
    print("\n--- Harden & Paul George: RS vs PO detail ---\n")
    for name in ["James Harden", "Paul George"]:
        for variant_label, variant in [("all games", "all"), ("floor ≥25 min", "floor_min25")]:
            sub = wide[(wide["player"] == name) & (wide["variant"] == variant)]
            if sub.empty:
                continue
            r = sub.iloc[0]
            print(f"  {name} ({variant_label}):")
            print(f"    FGA retention:  RS {r['rs_fga_retention']:.0%}  →  PO {r['po_fga_retention']:.0%}  (shift {r['fga_retention_shift']:+.0%})")
            print(f"    FTA retention:  RS {r['rs_fta_retention']:.0%}  →  PO {r['po_fta_retention']:.0%}  (shift {r['fta_retention_shift']:+.0%})")
            print(f"    Min retention:  RS {r['rs_min_retention']:.0%}  →  PO {r['po_min_retention']:.0%}")
            print(f"    vol_share:      RS {r['rs_vol_share']:.0%}  →  PO {r['po_vol_share']:.0%}")
            print()

    # Stability test: does RS FGA retention predict PO FGA retention?
    valid = all_games.dropna(subset=["rs_fga_retention", "po_fga_retention"])
    n = len(valid)
    if n >= 4:
        r, p = stats.pearsonr(valid["rs_fga_retention"], valid["po_fga_retention"])
        print(f"--- Stability: RS FGA retention → PO FGA retention ---")
        print(f"  Pearson r = {r:.3f}  p = {p:.4f}  n = {n}")

        shift = valid["fga_retention_shift"].dropna()
        t, p_shift = stats.ttest_1samp(shift, 0)
        print(f"\n--- Paired shift: PO FGA retention − RS FGA retention ---")
        print(f"  Mean shift = {shift.mean():+.3f}  t = {t:.3f}  p = {p_shift:.4f}")
        if p_shift < 0.05:
            direction = "MORE contraction" if shift.mean() < 0 else "LESS contraction"
            print(f"  Playoffs show systematically {direction} than RS")
        else:
            print(f"  No systematic RS → PO shift in FGA retention")

    # Players who contract MORE in playoffs than RS
    more_po = all_games[all_games["fga_retention_shift"] < -0.05].sort_values("fga_retention_shift")
    if not more_po.empty:
        print("\n--- Players with ≥5pp MORE contraction in playoffs vs RS ---\n")
        for _, r in more_po.iterrows():
            print(f"  {r['player']:<22} RS {r['rs_fga_retention']:.0%} → PO {r['po_fga_retention']:.0%}  (shift {r['fga_retention_shift']:+.0%})")

    # Players whose contraction is stable (within 5pp)
    stable = all_games[all_games["fga_retention_shift"].abs() <= 0.05].sort_values("player")
    if not stable.empty:
        print("\n--- Players with STABLE contraction (RS ≈ PO, within 5pp) ---\n")
        for _, r in stable.iterrows():
            print(f"  {r['player']:<22} RS {r['rs_fga_retention']:.0%} → PO {r['po_fga_retention']:.0%}  (shift {r['fga_retention_shift']:+.0%})")


def pivot_wide(long: pd.DataFrame) -> pd.DataFrame:
    """One row per player per variant with RS and PO columns side by side."""
    metrics = [
        "fga_retention", "fta_retention", "pts_retention", "ast_retention",
        "min_retention", "vol_share", "fta_fga_retention",
        "fg_pct_floor", "fta_fga_floor", "n_floor",
    ]
    rows = []
    for (player, variant), sub in long.groupby(["player", "variant"]):
        row = {
            "player": player,
            "player_group": sub["player_group"].iloc[0],
            "variant": variant,
        }
        for ctx in ("RS", "PO"):
            ctx_row = sub[sub["context"] == ctx]
            if ctx_row.empty:
                for m in metrics:
                    row[f"{ctx.lower()}_{m}"] = np.nan
                continue
            r = ctx_row.iloc[0]
            for m in metrics:
                row[f"{ctx.lower()}_{m}"] = r[m]
        row["fga_retention_shift"] = row.get("po_fga_retention", np.nan) - row.get("rs_fga_retention", np.nan)
        row["fta_retention_shift"] = row.get("po_fta_retention", np.nan) - row.get("rs_fta_retention", np.nan)
        row["vol_share_shift"] = row.get("po_vol_share", np.nan) - row.get("rs_vol_share", np.nan)
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    path = config.PROCESSED_DIR / "analysis_table.csv"
    if not path.exists():
        raise FileNotFoundError(f"Run features first: {path}")

    df = pd.read_csv(path, low_memory=False)
    df["is_playoff"] = df["is_playoff"].astype(bool)
    df["is_floor_primary"] = df["is_floor_primary"].astype(bool)

    long = run_retention_baselines(df)
    long.to_csv(config.PROCESSED_DIR / "retention_baselines_long.csv", index=False)

    wide = pivot_wide(long)
    wide.to_csv(config.PROCESSED_DIR / "retention_baselines.csv", index=False)

    print_report(wide)
    print(f"\nSaved: {config.PROCESSED_DIR / 'retention_baselines.csv'}")
    logger.info("Done")


if __name__ == "__main__":
    main()
