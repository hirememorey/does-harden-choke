"""Screen E: Floor-Game Profile Decomposition.

Question: What *kind* of bad games does Harden have, and how do they differ
from other players' bad games?

Three mechanisms:
  1. Shrinking: Volume collapse (fewer shots, fewer FTA, lower usage)
  2. Forcing: Same or more shots, much worse efficiency
  3. Disengagement: Fewer minutes that can't be explained by game state alone

Key metrics per player:
  - Volume share: what % of the scoring drop in floor games is explained
    by fewer shot attempts (vs worse efficiency)
  - Minutes drop: how much less does the player play in floor games
  - Min-GS correlation: does the coach ride the hot hand / bench the cold?
  - FTA/FGA ratio shift: does the player's attack profile change?
  - Assist drop: does playmaking collapse alongside scoring?
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


def run_screen(df: pd.DataFrame) -> None:
    po = df[df["is_playoff"]].copy()

    rows = []
    for player, grp in po.groupby("player_name"):
        valid = grp.dropna(subset=["game_score", "minutes"])
        if len(valid) < 10:
            continue

        fl = valid[valid["is_floor_primary"]]
        nfl = valid[~valid["is_floor_primary"]]
        if len(fl) < 3:
            continue

        # Minutes-game_score correlation
        r_min_gs = valid["minutes"].corr(valid["game_score"])

        # Per-36 rates
        def per36(col, sub):
            mins = sub["minutes"].mean()
            return sub[col].mean() / mins * 36 if mins > 0 else np.nan

        # Volume metrics (per-36)
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

        # Efficiency metrics
        fg_pct_fl = fl["fgm"].sum() / fl["fga"].sum() if fl["fga"].sum() > 0 else np.nan
        fg_pct_nfl = nfl["fgm"].sum() / nfl["fga"].sum() if nfl["fga"].sum() > 0 else np.nan
        fg3_pct_fl = fl["fg3m"].sum() / fl["fg3a"].sum() if fl["fg3a"].sum() > 0 else np.nan
        fg3_pct_nfl = nfl["fg3m"].sum() / nfl["fg3a"].sum() if nfl["fg3a"].sum() > 0 else np.nan

        # FTA/FGA ratio shift — attack profile
        fta_fga_fl = fl["fta"].sum() / fl["fga"].sum() if fl["fga"].sum() > 0 else np.nan
        fta_fga_nfl = nfl["fta"].sum() / nfl["fga"].sum() if nfl["fga"].sum() > 0 else np.nan

        # Volume share: rough decomposition
        pts_36_drop = pts_36_nfl - pts_36_fl
        possessions_lost = (fga_36_nfl - fga_36_fl) + 0.44 * (fta_36_nfl - fta_36_fl)
        pts_per_poss = pts_36_nfl / (fga_36_nfl + 0.44 * fta_36_nfl) if (fga_36_nfl + 0.44 * fta_36_nfl) > 0 else 1.1
        vol_component = possessions_lost * pts_per_poss
        vol_share = min(1.0, vol_component / pts_36_drop) if pts_36_drop > 0 else np.nan

        # Assist-to-turnover shift
        ast_tov_fl = fl["ast"].sum() / fl["tov"].sum() if fl["tov"].sum() > 0 else np.nan
        ast_tov_nfl = nfl["ast"].sum() / nfl["tov"].sum() if nfl["tov"].sum() > 0 else np.nan

        # 3-point reliance shift: does fg3a/fga change in floor games?
        fg3a_fga_fl = fl["fg3a"].sum() / fl["fga"].sum() if fl["fga"].sum() > 0 else np.nan
        fg3a_fga_nfl = nfl["fg3a"].sum() / nfl["fga"].sum() if nfl["fga"].sum() > 0 else np.nan

        rows.append({
            "player": player,
            "player_group": config.PLAYER_GROUP.get(player, ""),
            "po_n_games": len(valid),
            "n_floor": len(fl),
            "min_nonfloor": nfl["minutes"].mean(),
            "min_floor": fl["minutes"].mean(),
            "min_delta": fl["minutes"].mean() - nfl["minutes"].mean(),
            "r_min_gs": r_min_gs,
            "fga_36_delta": fga_36_fl - fga_36_nfl,
            "fta_36_delta": fta_36_fl - fta_36_nfl,
            "fg3a_36_delta": fg3a_36_fl - fg3a_36_nfl,
            "tov_36_delta": tov_36_fl - tov_36_nfl,
            "ast_36_delta": ast_36_fl - ast_36_nfl,
            "pts_36_delta": pts_36_fl - pts_36_nfl,
            "fg_pct_delta": (fg_pct_fl or 0) - (fg_pct_nfl or 0),
            "fg3_pct_delta": (fg3_pct_fl or 0) - (fg3_pct_nfl or 0),
            "fta_fga_delta": (fta_fga_fl or 0) - (fta_fga_nfl or 0),
            "fg3a_fga_delta": (fg3a_fga_fl or 0) - (fg3a_fga_nfl or 0),
            "ast_tov_delta": (ast_tov_fl or 0) - (ast_tov_nfl or 0),
            "vol_share": vol_share,
            "eff_share": 1.0 - vol_share if vol_share is not None and not np.isnan(vol_share) else np.nan,
        })

    results = pd.DataFrame(rows)

    # Classify mechanism
    def classify(row):
        if pd.isna(row["vol_share"]):
            return "unknown"
        if row["vol_share"] > 0.55:
            return "shrinker"
        if row["vol_share"] < 0.35:
            return "forcer"
        return "mixed"

    results["mechanism"] = results.apply(classify, axis=1)

    results.to_csv(config.PROCESSED_DIR / "screen_e_results.csv", index=False)

    print("\n=== Screen E: Floor-Game Profile Decomposition ===\n")
    print("Mechanism classification: shrinker (>55% volume-driven) | forcer (<35%) | mixed\n")

    sorted_by_vol = results.sort_values("vol_share", ascending=False)
    print(sorted_by_vol[[
        "player", "player_group", "mechanism",
        "vol_share", "eff_share",
        "min_delta", "r_min_gs",
        "fga_36_delta", "fta_36_delta",
    ]].to_string(index=False))

    print("\n--- Attack profile shift in floor games ---\n")
    print("FTA/FGA delta: negative = stops attacking rim in bad games")
    print("FG3A/FGA delta: positive = shifts toward 3s in bad games\n")
    print(results.sort_values("fta_fga_delta")[[
        "player", "player_group",
        "fta_fga_delta", "fg3a_fga_delta",
        "fg_pct_delta", "fg3_pct_delta",
        "ast_36_delta", "tov_36_delta",
    ]].to_string(index=False))

    # Harden detail
    harden = results[results["player"] == "James Harden"]
    if not harden.empty:
        h = harden.iloc[0]
        print(f"\n--- Harden Profile ---")
        print(f"  Mechanism: {h['mechanism']}")
        print(f"  Volume share of scoring drop: {h['vol_share']:.0%}")
        print(f"  Efficiency share: {h['eff_share']:.0%}")
        print(f"  Minutes drop in floor games:  {h['min_delta']:+.1f}")
        print(f"  Minutes-GameScore correlation: {h['r_min_gs']:.3f}")
        print(f"  FGA/36 drop:  {h['fga_36_delta']:+.1f}")
        print(f"  FTA/36 drop:  {h['fta_36_delta']:+.1f}")
        print(f"  FG3A/36 drop: {h['fg3a_36_delta']:+.1f}")
        print(f"  AST/36 drop:  {h['ast_36_delta']:+.1f}")
        print(f"  TOV/36 delta: {h['tov_36_delta']:+.1f}")
        print(f"  FTA/FGA ratio shift: {h['fta_fga_delta']:+.3f}")
        print(f"  FG3A/FGA ratio shift: {h['fg3a_fga_delta']:+.3f}")
        print(f"  FG% delta:    {h['fg_pct_delta']:+.3f}")
        print(f"  FG3% delta:   {h['fg3_pct_delta']:+.3f}")

    # Group comparison on key metrics
    print(f"\n--- Group A vs B mechanism comparison ---\n")
    for metric in ["vol_share", "min_delta", "r_min_gs", "fta_fga_delta", "fg3a_fga_delta"]:
        ga = results[results["player_group"] == "A"][metric].dropna()
        gb = results[results["player_group"] == "B"][metric].dropna()
        if len(ga) >= 2 and len(gb) >= 2:
            u, p = stats.mannwhitneyu(ga, gb, alternative="two-sided")
            print(f"  {metric:<20} A={ga.mean():+.3f}  B={gb.mean():+.3f}  p={p:.3f}")

    # The disengagement test: minutes drop adjusted for game margin
    # If minutes drop is just blowout effect, plus_minus should explain it
    print(f"\n--- Minutes drop: blowout vs disengagement ---\n")
    for player, grp in po.groupby("player_name"):
        valid = grp.dropna(subset=["game_score", "minutes", "plus_minus"])
        if len(valid) < 20:
            continue
        fl = valid[valid["is_floor_primary"]]
        nfl = valid[~valid["is_floor_primary"]]
        if len(fl) < 3:
            continue

        # Regress minutes on game_score and plus_minus
        # If game_score coefficient is still significant after controlling for margin,
        # the coach is responding to individual performance, not just game state
        from statsmodels.api import OLS
        X = valid[["game_score", "plus_minus"]].copy()
        X = X.dropna()
        y = valid.loc[X.index, "minutes"]
        X = (X - X.mean()) / X.std()
        X_const = OLS(y, sm_add_const(X)).fit()

        gs_coef = X_const.params.get("game_score", np.nan)
        gs_pval = X_const.pvalues.get("game_score", np.nan)
        pm_coef = X_const.params.get("plus_minus", np.nan)

        fl_min = fl["minutes"].mean()
        nfl_min = nfl["minutes"].mean()
        fl_pm = fl["plus_minus"].mean()
        nfl_pm = nfl["plus_minus"].mean()

        print(f"  {player:<20} min drop={fl_min-nfl_min:+.1f}  +/- drop={fl_pm-nfl_pm:+.1f}  GS coef={gs_coef:+.2f}(p={gs_pval:.3f})")

def sm_add_const(X):
    import statsmodels.api as sm
    return sm.add_constant(X)


def main() -> None:
    df = pd.read_csv(config.PROCESSED_DIR / "analysis_table.csv", low_memory=False)
    run_screen(df)


if __name__ == "__main__":
    main()
