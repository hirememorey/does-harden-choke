"""Screen D: Leverage Concentration Test.

Question: Do Harden's floor games cluster in high-leverage moments more than
his non-floor games — and is this pattern an outlier relative to peers?

Leverage score (continuous, 0-1):
  Combines series position and elimination pressure into a single metric.

  Base leverage from series game number:
    Games 1-2: 0.15
    Games 3-4: 0.35
    Games 5:   0.55
    Games 6:   0.70
    Games 7:   0.90

  Elimination pressure modifier:
    If either team has 3 wins (facing elimination): +0.10
    If BOTH teams have 3 wins (Game 7): already captured at 0.90

  The modifier makes elimination games within a series more leveraged
  than non-elimination games at the same series position.
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

BASE_LEVERAGE = {1: 0.15, 2: 0.15, 3: 0.35, 4: 0.35, 5: 0.55, 6: 0.70, 7: 0.90}


def compute_leverage(row: pd.Series) -> float:
    game_num = row.get("series_game_num")
    if pd.isna(game_num):
        return np.nan
    game_num = int(game_num)
    base = BASE_LEVERAGE.get(game_num, 0.35)
    if row.get("is_elimination") and game_num < 7:
        base += 0.10
    return base


def leverage_tier(score: float) -> str:
    if pd.isna(score):
        return "unknown"
    if score < 0.30:
        return "low"
    if score < 0.55:
        return "medium"
    return "high"


def run_screen(df: pd.DataFrame) -> None:
    po = df[df["is_playoff"]].copy()
    po["leverage"] = po.apply(compute_leverage, axis=1)
    po["leverage_tier"] = po["leverage"].apply(leverage_tier)

    rows = []
    for player, grp in po.groupby("player_name"):
        valid = grp.dropna(subset=["leverage", "is_floor_primary"])
        if len(valid) < 10:
            logger.warning("Skipping %s: only %d playoff games with leverage data", player, len(valid))
            continue
        floor = valid[valid["is_floor_primary"]]
        non_floor = valid[~valid["is_floor_primary"]]

        mean_lev_floor = floor["leverage"].mean() if len(floor) > 0 else np.nan
        mean_lev_nonfloor = non_floor["leverage"].mean() if len(non_floor) > 0 else np.nan
        leverage_concentration = mean_lev_floor - mean_lev_nonfloor

        tier_rates = {}
        for tier in ("low", "medium", "high"):
            tier_games = valid[valid["leverage_tier"] == tier]
            tier_rates[f"{tier}_n"] = len(tier_games)
            tier_rates[f"{tier}_floor_rate"] = (
                tier_games["is_floor_primary"].mean() if len(tier_games) > 0 else np.nan
            )

        logit_coef = np.nan
        logit_pvalue = np.nan
        if len(valid) > 20 and valid["leverage"].std() > 0:
            try:
                X = valid[["leverage"]].copy()
                X["leverage"] = (X["leverage"] - X["leverage"].mean()) / X["leverage"].std()
                X = sm.add_constant(X)
                y = valid["is_floor_primary"].astype(int)
                model = sm.Logit(y, X).fit(disp=0)
                logit_coef = model.params["leverage"]
                logit_pvalue = model.pvalues["leverage"]
            except Exception as exc:
                logger.warning("Logit failed for %s: %s", player, exc)

        rows.append({
            "player": player,
            "player_group": config.PLAYER_GROUP.get(player, ""),
            "po_n_games": len(valid),
            "n_floor_games": len(floor),
            "mean_leverage_floor": mean_lev_floor,
            "mean_leverage_nonfloor": mean_lev_nonfloor,
            "leverage_concentration": leverage_concentration,
            "logit_coef": logit_coef,
            "logit_pvalue": logit_pvalue,
            **tier_rates,
        })

    results = pd.DataFrame(rows).sort_values("leverage_concentration", ascending=False)
    results["rank"] = range(1, len(results) + 1)
    results.to_csv(config.PROCESSED_DIR / "screen_d_results.csv", index=False)

    print("\n=== Screen D: Leverage Concentration ===\n")
    print("leverage_concentration = mean(leverage of floor games) - mean(leverage of non-floor games)")
    print("Positive = floor games cluster in higher-leverage moments\n")
    print(results[[
        "player", "player_group", "po_n_games", "n_floor_games",
        "mean_leverage_floor", "mean_leverage_nonfloor",
        "leverage_concentration", "rank",
    ]].to_string(index=False))

    print("\n--- Floor-game rate by leverage tier ---\n")
    tier_cols = [
        "player", "player_group",
        "low_n", "low_floor_rate",
        "medium_n", "medium_floor_rate",
        "high_n", "high_floor_rate",
    ]
    print(results[tier_cols].to_string(index=False))

    harden = results[results["player"] == "James Harden"]
    if not harden.empty:
        h = harden.iloc[0]
        print(f"\n--- Harden detail ---")
        print(f"  Mean leverage of floor games:     {h['mean_leverage_floor']:.3f}")
        print(f"  Mean leverage of non-floor games: {h['mean_leverage_nonfloor']:.3f}")
        print(f"  Leverage concentration (delta):   {h['leverage_concentration']:+.3f}")
        print(f"  Rank: {int(h['rank'])}/{len(results)}")
        if not np.isnan(h.get("logit_coef", np.nan)):
            print(f"  Logit(coef): {h['logit_coef']:.3f}, p={h['logit_pvalue']:.4f}")

    ga = results[results["player_group"] == "A"]["leverage_concentration"]
    gb = results[results["player_group"] == "B"]["leverage_concentration"]
    if len(ga) >= 2 and len(gb) >= 2:
        u, p = stats.mannwhitneyu(ga, gb, alternative="greater")
        pooled_sd = np.sqrt((ga.std() ** 2 + gb.std() ** 2) / 2)
        d = (ga.mean() - gb.mean()) / pooled_sd if pooled_sd > 0 else np.nan
        print(f"\n--- Group A vs B (leverage concentration) ---")
        print(f"  Group A mean: {ga.mean():+.3f}")
        print(f"  Group B mean: {gb.mean():+.3f}")
        print(f"  Mann-Whitney U={u:.0f}, p={p:.4f}")
        print(f"  Cohen's d={d:.3f}")

    # Harden game-by-game detail: floor games sorted by leverage
    harden_po = po[po["player_name"] == "James Harden"].copy()
    harden_floor = harden_po[harden_po["is_floor_primary"]].sort_values("leverage", ascending=False)
    if not harden_floor.empty:
        print(f"\n--- Harden floor games (top 10 by leverage) ---")
        detail_cols = ["season", "matchup", "series_game_num", "is_elimination",
                        "leverage", "leverage_tier", "game_score", "pts", "fga"]
        avail = [c for c in detail_cols if c in harden_floor.columns]
        print(harden_floor[avail].head(10).to_string(index=False))

    # Supplementary: catastrophic depth test
    # When Harden has a floor game, HOW BAD is it relative to his baseline,
    # and does the depth of the floor correlate with leverage?
    print(f"\n--- Floor depth vs leverage (residual correlation) ---")
    depth_rows = []
    for player, grp in po.groupby("player_name"):
        floor_games = grp[grp["is_floor_primary"]].dropna(subset=["leverage", "residual_primary"])
        if len(floor_games) < 5:
            continue
        r, p = stats.pearsonr(floor_games["leverage"], floor_games["residual_primary"])
        depth_rows.append({
            "player": player,
            "player_group": config.PLAYER_GROUP.get(player, ""),
            "n_floor_games": len(floor_games),
            "corr_leverage_residual": r,
            "corr_pvalue": p,
        })
    depth_df = pd.DataFrame(depth_rows).sort_values("corr_leverage_residual")
    depth_df.to_csv(config.PROCESSED_DIR / "screen_d_depth.csv", index=False)
    print(depth_df.to_string(index=False))


def main() -> None:
    df = pd.read_csv(config.PROCESSED_DIR / "analysis_table.csv", low_memory=False)
    run_screen(df)


if __name__ == "__main__":
    main()
