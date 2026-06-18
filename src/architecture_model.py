"""Architecture-prediction model — can RS scoring architecture predict PO floor-game risk?

The trigger taxonomy failed split-sample validation (June 14 2026).  The project
pivots to a predictive, architecture-first frame:

    Given only regular-season box scores, how well can we predict which stars
    will have elevated playoff floor-game rates?

Box-score IVs (all RS-only, observable before playoffs):
    rs_fga_retention      FGA volume drop in RS floor games (stable trait r=0.72)
    rs_fta_retention      FTA-specific collapse in RS floor games (rim-abandonment)
    rs_fta_fga_ratio      FTA dependency — how reliant on getting to the line
    hhi_scoring           Herfindahl index across 2PM / 3PM / FT point shares
    pct_pts_ft            Share of scoring from free throws (foul-drawing pillar)
    rs_floor_rate         Base rate of RS floor games (~15% by construction)

Shot-chart IVs (from shotchartdetail, added June 14 2026):
    hhi_5                 Herfindahl across 5 modes (RA, Paint, Mid, 3PT, FT)
    mode_independence_score  avg absolute pairwise correlation of per-game mode shares
    n_tertiary_modes      modes contributing >=15% of scoring

Dependent variables:
    po_floor_rate         Playoff floor-game rate (player-season or career)
    po_floor_severity     Mean game_score in PO floor games (how bad the bad games are)

Two levels:
    Career-level      n=31 players — career-average RS architecture → career PO floor rate
    Player-season     n~260 — season-specific RS architecture → season-specific PO floor rate

Success: R² > 0.25 (career) or partial effects interpretable (player-season)
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = config.PROCESSED_DIR
FIGURES_DIR = config.FIGURES_DIR
MIN_RS_NONFLOOR = 10
MIN_RS_FLOOR = 3
MIN_PO_GAMES = 5


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def compute_season_architecture(df: pd.DataFrame) -> pd.DataFrame:
    """Compute RS scoring architecture per player-season."""
    rs = df[~df["is_playoff"]].copy()
    rs = rs[rs["minutes"] > 0].copy()

    # Per-game scoring mode decomposition
    rs["pts_2pm"] = 2 * (rs["fgm"] - rs["fg3m"])
    rs["pts_3pm"] = 3 * rs["fg3m"]
    rs["pts_ft"] = rs["ftm"]

    # Per-36 rates
    rs["fga_per36"] = rs["fga"] / rs["minutes"] * 36
    rs["fta_per36"] = rs["fta"] / rs["minutes"] * 36
    rs["fg3a_per36"] = rs["fg3a"] / rs["minutes"] * 36

    rows = []
    for (player, season), grp in rs.groupby(["player_name", "season"]):
        fl = grp[grp["is_floor_primary"] == True]
        nfl = grp[grp["is_floor_primary"] == False]
        if len(nfl) < MIN_RS_NONFLOOR or len(fl) < MIN_RS_FLOOR:
            continue

        total_pts = grp["pts"].sum()
        if total_pts == 0:
            continue

        # Scoring shares
        pct_2pm = grp["pts_2pm"].sum() / total_pts
        pct_3pm = grp["pts_3pm"].sum() / total_pts
        pct_ft = grp["pts_ft"].sum() / total_pts

        # HHI concentration
        hhi = pct_2pm ** 2 + pct_3pm ** 2 + pct_ft ** 2

        # FTA dependency
        total_fga = grp["fga"].sum()
        total_fta = grp["fta"].sum()
        fta_fga_ratio = total_fta / max(total_fga, 1)

        # Retention in RS floor games
        nfl_fga = nfl["fga_per36"].mean()
        nfl_fta = nfl["fta_per36"].mean()
        fl_fga = fl["fga_per36"].mean()
        fl_fta = fl["fta_per36"].mean()

        fga_ret = fl_fga / max(nfl_fga, 0.01)
        fta_ret = fl_fta / max(nfl_fta, 0.01) if nfl_fta > 0.5 else np.nan

        rows.append({
            "player_name": player,
            "season": season,
            "n_rs_games": len(grp),
            "n_rs_floor": len(fl),
            "rs_floor_rate": len(fl) / len(grp),
            "rs_fga_retention": fga_ret,
            "rs_fta_retention": fta_ret,
            "rs_fta_fga_ratio": fta_fga_ratio,
            "hhi_scoring": hhi,
            "pct_pts_2pm": pct_2pm,
            "pct_pts_3pm": pct_3pm,
            "pct_pts_ft": pct_ft,
            "rs_rim_abandon_index": fga_ret - fta_ret if not np.isnan(fta_ret) else np.nan,
        })

    return pd.DataFrame(rows)


def compute_season_po_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    """Compute PO floor-game outcomes per player-season."""
    po = df[df["is_playoff"]].copy()

    rows = []
    for (player, season), grp in po.groupby(["player_name", "season"]):
        if len(grp) < MIN_PO_GAMES:
            continue
        fl = grp[grp["is_floor_primary"] == True]
        rows.append({
            "player_name": player,
            "season": season,
            "n_po_games": len(grp),
            "n_po_floor": len(fl),
            "po_floor_rate": len(fl) / len(grp),
            "po_floor_severity": fl["game_score"].mean() if len(fl) > 0 else np.nan,
            "po_mean_gs": grp["game_score"].mean(),
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Regression and analysis
# ---------------------------------------------------------------------------

def career_level_regression(arch: pd.DataFrame, po: pd.DataFrame) -> dict:
    """Cross-player career-level regression (n=31)."""
    career_arch = arch.groupby("player_name").agg(
        rs_fga_retention=("rs_fga_retention", "mean"),
        rs_fta_retention=("rs_fta_retention", "mean"),
        rs_fta_fga_ratio=("rs_fta_fga_ratio", "mean"),
        hhi_scoring=("hhi_scoring", "mean"),
        pct_pts_ft=("pct_pts_ft", "mean"),
        rs_floor_rate=("rs_floor_rate", "mean"),
        rs_rim_abandon_index=("rs_rim_abandon_index", "mean"),
        n_seasons=("season", "count"),
    ).reset_index()

    career_po = po.groupby("player_name").agg(
        po_floor_rate=("po_floor_rate", lambda x: po.loc[x.index, "n_po_floor"].sum() / po.loc[x.index, "n_po_games"].sum()),
        n_po_total=("n_po_games", "sum"),
        n_po_floor=("n_po_floor", "sum"),
    ).reset_index()

    merged = career_arch.merge(career_po, on="player_name", how="inner")
    merged.to_csv(OUTPUT_DIR / "architecture_career_table.csv", index=False)

    print("=" * 70)
    print("CAREER-LEVEL ARCHITECTURE → PO FLOOR RATE (n=%d)" % len(merged))
    print("=" * 70)

    # Bivariate correlations
    print("\n--- Bivariate correlations with PO floor rate ---")
    iv_cols = [
        "rs_fga_retention", "rs_fta_retention", "rs_fta_fga_ratio",
        "hhi_scoring", "pct_pts_ft", "rs_floor_rate",
    ]
    corr_rows = []
    for col in iv_cols:
        valid = merged.dropna(subset=[col, "po_floor_rate"])
        if len(valid) < 5:
            continue
        r, p = stats.pearsonr(valid[col], valid["po_floor_rate"])
        print(f"  {col:25s}: r={r:+.3f}, p={p:.4f} (n={len(valid)})")
        corr_rows.append({"variable": col, "r": r, "p": p, "n": len(valid)})

    # Multivariate: kitchen-sink
    valid_mv = merged.dropna(subset=iv_cols + ["po_floor_rate"])
    print(f"\n--- Multivariate OLS (n={len(valid_mv)}) ---")
    if len(valid_mv) >= 10:
        formula = "po_floor_rate ~ rs_fga_retention + rs_fta_fga_ratio + hhi_scoring + pct_pts_ft"
        m = smf.ols(formula, data=valid_mv).fit()
        print(m.summary2().tables[1].to_string())
        print(f"\n  R² = {m.rsquared:.3f}, Adj R² = {m.rsquared_adj:.3f}")

        # Parsimonious: just FGA retention + FTA dependency
        formula2 = "po_floor_rate ~ rs_fga_retention + rs_fta_fga_ratio"
        m2 = smf.ols(formula2, data=valid_mv).fit()
        print(f"\n--- Parsimonious (FGA retention + FTA ratio, n={len(valid_mv)}) ---")
        print(m2.summary2().tables[1].to_string())
        print(f"\n  R² = {m2.rsquared:.3f}, Adj R² = {m2.rsquared_adj:.3f}")
    else:
        m = None
        m2 = None
        print("  Not enough valid observations for multivariate regression")

    return {
        "merged": merged,
        "model_full": m,
        "model_parsim": m2,
        "corr_rows": corr_rows,
    }


def season_level_regression(arch: pd.DataFrame, po: pd.DataFrame) -> dict:
    """Player-season level regression with player FE (n~260)."""
    merged = arch.merge(po, on=["player_name", "season"], how="inner")
    merged.to_csv(OUTPUT_DIR / "architecture_season_table.csv", index=False)

    print("\n" + "=" * 70)
    print("PLAYER-SEASON ARCHITECTURE → PO FLOOR RATE (n=%d)" % len(merged))
    print("=" * 70)

    # Remove players with only 1 season (can't estimate FE)
    season_counts = merged.groupby("player_name").size()
    multi_season = season_counts[season_counts >= 2].index
    subset = merged[merged["player_name"].isin(multi_season)].copy()
    print(f"  Players with >=2 PO seasons: {len(multi_season)}")
    print(f"  Player-seasons in regression: {len(subset)}")

    if len(subset) < 20:
        print("  Not enough observations for player-season regression")
        return {"merged": merged}

    # Without player FE (pooled)
    formula_pooled = (
        "po_floor_rate ~ rs_fga_retention + rs_fta_fga_ratio + hhi_scoring + pct_pts_ft"
    )
    m_pooled = smf.ols(formula_pooled, data=subset).fit(cov_type="HC1")
    print(f"\n--- Pooled OLS (no player FE, n={len(subset)}) ---")
    print(m_pooled.summary2().tables[1].to_string())
    print(f"\n  R² = {m_pooled.rsquared:.3f}")

    # With player FE
    formula_fe = (
        "po_floor_rate ~ rs_fga_retention + rs_fta_fga_ratio + hhi_scoring + pct_pts_ft"
        " + C(player_name)"
    )
    m_fe = smf.ols(formula_fe, data=subset).fit()
    # Print only the architecture coefficients
    arch_terms = ["rs_fga_retention", "rs_fta_fga_ratio", "hhi_scoring", "pct_pts_ft"]
    print(f"\n--- With player FE (n={len(subset)}) ---")
    for t in arch_terms:
        if t in m_fe.params.index:
            print(f"  {t:25s}: β={m_fe.params[t]:+.4f}, p={m_fe.pvalues[t]:.4f}")
    print(f"\n  R² = {m_fe.rsquared:.3f} (includes FE)")

    return {
        "merged": merged,
        "model_pooled": m_pooled,
        "model_fe": m_fe,
    }


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Shot-chart architecture regression
# ---------------------------------------------------------------------------

def load_shot_chart_architecture() -> pd.DataFrame | None:
    path = config.PROCESSED_DIR / "shot_chart_architecture.csv"
    if not path.exists():
        return None
    return pd.read_csv(path, low_memory=False)


def shot_chart_career_regression(
    sc_arch: pd.DataFrame, po: pd.DataFrame,
) -> dict:
    """Career-level regression with shot-chart IVs (hhi_5, mode_independence, n_tertiary)."""
    career_sc = sc_arch.groupby("player_name").agg(
        hhi_5=("hhi_5", "mean"),
        mode_independence_score=("mode_independence_score", "mean"),
        n_tertiary_modes=("n_tertiary_modes", "mean"),
        share_ra=("share_ra", "mean"),
        share_paint=("share_paint", "mean"),
        share_mid=("share_mid", "mean"),
        share_three=("share_three", "mean"),
        share_ft=("share_ft", "mean"),
        floor_mode_collapse_ra=("floor_mode_collapse_ra", "mean"),
        floor_mode_collapse_three=("floor_mode_collapse_three", "mean"),
        floor_mode_collapse_ft=("floor_mode_collapse_ft", "mean"),
    ).reset_index()

    career_po = po.groupby("player_name").agg(
        po_floor_rate=("po_floor_rate", lambda x: po.loc[x.index, "n_po_floor"].sum() / po.loc[x.index, "n_po_games"].sum()),
        n_po_total=("n_po_games", "sum"),
        n_po_floor=("n_po_floor", "sum"),
    ).reset_index()

    merged = career_sc.merge(career_po, on="player_name", how="inner")
    merged.to_csv(OUTPUT_DIR / "shot_chart_career_table.csv", index=False)

    print("\n" + "=" * 70)
    print("SHOT-CHART CAREER-LEVEL → PO FLOOR RATE (n=%d)" % len(merged))
    print("=" * 70)

    sc_iv_cols = ["hhi_5", "mode_independence_score", "n_tertiary_modes", "share_ft"]
    corr_rows = []
    print("\n--- Bivariate correlations with PO floor rate ---")
    for col in sc_iv_cols:
        valid = merged.dropna(subset=[col, "po_floor_rate"])
        if len(valid) < 5:
            continue
        r, p = stats.pearsonr(valid[col], valid["po_floor_rate"])
        print(f"  {col:30s}: r={r:+.3f}, p={p:.4f} (n={len(valid)})")
        corr_rows.append({"variable": col, "r": r, "p": p, "n": len(valid)})

    valid_mv = merged.dropna(subset=sc_iv_cols + ["po_floor_rate"])
    print(f"\n--- Multivariate OLS (n={len(valid_mv)}) ---")
    m = None
    m_indep = None
    if len(valid_mv) >= 10:
        formula_full = "po_floor_rate ~ hhi_5 + mode_independence_score + n_tertiary_modes + share_ft"
        m = smf.ols(formula_full, data=valid_mv).fit()
        print(m.summary2().tables[1].to_string())
        print(f"\n  R² = {m.rsquared:.3f}, Adj R² = {m.rsquared_adj:.3f}")

        formula_indep = "po_floor_rate ~ mode_independence_score + share_ft"
        m_indep = smf.ols(formula_indep, data=valid_mv).fit()
        print(f"\n--- Parsimonious (mode independence + FTA share, n={len(valid_mv)}) ---")
        print(m_indep.summary2().tables[1].to_string())
        print(f"\n  R² = {m_indep.rsquared:.3f}, Adj R² = {m_indep.rsquared_adj:.3f}")
    else:
        print("  Not enough valid observations for multivariate regression")

    # Floor-game mode collapse table
    print("\n--- Floor-game mode collapse (selected players) ---")
    for name in ["James Harden", "Kevin Durant", "Stephen Curry", "Paul George"]:
        row = merged[merged["player_name"] == name]
        if len(row) > 0:
            r = row.iloc[0]
            print(f"  {name}: RA collapse={r.get('floor_mode_collapse_ra', np.nan):+.3f}, "
                  f"3PT collapse={r.get('floor_mode_collapse_three', np.nan):+.3f}, "
                  f"FT collapse={r.get('floor_mode_collapse_ft', np.nan):+.3f}")

    return {
        "merged": merged,
        "model_full": m,
        "model_parsim": m_indep,
        "corr_rows": corr_rows,
    }


def combined_career_regression(
    box_arch: pd.DataFrame, sc_arch: pd.DataFrame, po: pd.DataFrame,
) -> dict:
    """Career-level regression combining box-score + shot-chart IVs."""
    career_box = box_arch.groupby("player_name").agg(
        rs_fga_retention=("rs_fga_retention", "mean"),
        rs_fta_fga_ratio=("rs_fta_fga_ratio", "mean"),
        hhi_scoring=("hhi_scoring", "mean"),
        pct_pts_ft=("pct_pts_ft", "mean"),
    ).reset_index()

    career_sc = sc_arch.groupby("player_name").agg(
        hhi_5=("hhi_5", "mean"),
        mode_independence_score=("mode_independence_score", "mean"),
        n_tertiary_modes=("n_tertiary_modes", "mean"),
    ).reset_index()

    career_po = po.groupby("player_name").agg(
        po_floor_rate=("po_floor_rate", lambda x: po.loc[x.index, "n_po_floor"].sum() / po.loc[x.index, "n_po_games"].sum()),
        n_po_total=("n_po_games", "sum"),
    ).reset_index()

    merged = career_box.merge(career_sc, on="player_name", how="inner")
    merged = merged.merge(career_po, on="player_name", how="inner")
    merged.to_csv(OUTPUT_DIR / "architecture_combined_career_table.csv", index=False)

    print("\n" + "=" * 70)
    print("COMBINED BOX+SHOT-CHART CAREER-LEVEL → PO FLOOR RATE (n=%d)" % len(merged))
    print("=" * 70)

    combined_ivs = ["rs_fta_fga_ratio", "hhi_5", "mode_independence_score", "n_tertiary_modes"]
    valid_mv = merged.dropna(subset=combined_ivs + ["po_floor_rate"])

    if len(valid_mv) >= 10:
        formula = "po_floor_rate ~ rs_fta_fga_ratio + hhi_5 + mode_independence_score + n_tertiary_modes"
        m = smf.ols(formula, data=valid_mv).fit()
        print(f"\n--- Combined OLS (n={len(valid_mv)}) ---")
        print(m.summary2().tables[1].to_string())
        print(f"\n  R² = {m.rsquared:.3f}, Adj R² = {m.rsquared_adj:.3f}")
    else:
        m = None
        print("  Not enough observations for combined regression")

    return {"merged": merged, "model_combined": m}


def plot_shot_chart_scatter(merged: pd.DataFrame) -> None:
    """Key figure: mode independence score vs PO floor rate."""
    if "mode_independence_score" not in merged.columns:
        return

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    ax = axes[0]
    for _, row in merged.iterrows():
        if pd.isna(row.get("mode_independence_score")) or pd.isna(row.get("po_floor_rate")):
            continue
        color = config.GROUP_A_COLOR if row["player_name"] in config.GROUP_A else config.GROUP_B_COLOR
        ax.scatter(
            row["mode_independence_score"], row["po_floor_rate"],
            s=max(row.get("n_po_total", 20), 20),
            color=color, alpha=0.7, edgecolors="black", linewidth=0.5,
        )
        ax.annotate(
            row["player_name"].split()[-1],
            (row["mode_independence_score"], row["po_floor_rate"]),
            fontsize=7, alpha=0.8, xytext=(4, 4), textcoords="offset points",
        )
    valid = merged.dropna(subset=["mode_independence_score", "po_floor_rate"])
    if len(valid) >= 5:
        r, p = stats.pearsonr(valid["mode_independence_score"], valid["po_floor_rate"])
        ax.set_title(f"Mode Independence → PO Floor Risk\nr={r:.3f}, p={p:.4f}")
    else:
        ax.set_title("Mode Independence → PO Floor Risk")
    ax.set_xlabel("Mode Independence Score (high = correlated modes)")
    ax.set_ylabel("Playoff Floor-Game Rate")
    ax.axhline(0.15, color="gray", linestyle=":", alpha=0.4)

    ax = axes[1]
    for _, row in merged.iterrows():
        if pd.isna(row.get("hhi_5")) or pd.isna(row.get("po_floor_rate")):
            continue
        color = config.GROUP_A_COLOR if row["player_name"] in config.GROUP_A else config.GROUP_B_COLOR
        ax.scatter(
            row["hhi_5"], row["po_floor_rate"],
            s=max(row.get("n_po_total", 20), 20),
            color=color, alpha=0.7, edgecolors="black", linewidth=0.5,
        )
        ax.annotate(
            row["player_name"].split()[-1],
            (row["hhi_5"], row["po_floor_rate"]),
            fontsize=7, alpha=0.8, xytext=(4, 4), textcoords="offset points",
        )
    valid2 = merged.dropna(subset=["hhi_5", "po_floor_rate"])
    if len(valid2) >= 5:
        r2, p2 = stats.pearsonr(valid2["hhi_5"], valid2["po_floor_rate"])
        ax.set_title(f"HHI-5 (5-Mode) → PO Floor Risk\nr={r2:.3f}, p={p2:.4f}")
    else:
        ax.set_title("HHI-5 (5-Mode) → PO Floor Risk")
    ax.set_xlabel("Scoring Mode Concentration (HHI-5)")
    ax.set_ylabel("Playoff Floor-Game Rate")
    ax.axhline(0.15, color="gray", linestyle=":", alpha=0.4)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        path = FIGURES_DIR / f"shot_chart_career_scatter.{ext}"
        fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote shot_chart_career_scatter")


def plot_career_scatter(merged: pd.DataFrame) -> None:
    """Key figure: RS FTA/FGA ratio vs PO floor rate, sized by n_po_total."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Left: FTA/FGA ratio vs PO floor rate
    ax = axes[0]
    for _, row in merged.iterrows():
        color = config.GROUP_A_COLOR if row["player_name"] in config.GROUP_A else config.GROUP_B_COLOR
        ax.scatter(
            row["rs_fta_fga_ratio"], row["po_floor_rate"],
            s=max(row.get("n_po_total", 20), 20),
            color=color, alpha=0.7, edgecolors="black", linewidth=0.5,
        )
        ax.annotate(
            row["player_name"].split()[-1],
            (row["rs_fta_fga_ratio"], row["po_floor_rate"]),
            fontsize=7, alpha=0.8,
            xytext=(4, 4), textcoords="offset points",
        )
    r, p = stats.pearsonr(merged["rs_fta_fga_ratio"], merged["po_floor_rate"])
    ax.set_xlabel("RS FTA/FGA Ratio (FTA Dependency)")
    ax.set_ylabel("Playoff Floor-Game Rate")
    ax.set_title(f"FTA Dependency → PO Floor Risk\nr={r:.3f}, p={p:.4f}")
    ax.axhline(0.15, color="gray", linestyle=":", alpha=0.4, label="RS baseline (~15%)")
    ax.legend(fontsize=8)

    # Right: HHI vs PO floor rate
    ax = axes[1]
    for _, row in merged.iterrows():
        color = config.GROUP_A_COLOR if row["player_name"] in config.GROUP_A else config.GROUP_B_COLOR
        ax.scatter(
            row["hhi_scoring"], row["po_floor_rate"],
            s=max(row.get("n_po_total", 20), 20),
            color=color, alpha=0.7, edgecolors="black", linewidth=0.5,
        )
        ax.annotate(
            row["player_name"].split()[-1],
            (row["hhi_scoring"], row["po_floor_rate"]),
            fontsize=7, alpha=0.8,
            xytext=(4, 4), textcoords="offset points",
        )
    r2, p2 = stats.pearsonr(merged["hhi_scoring"], merged["po_floor_rate"])
    ax.set_xlabel("Scoring Mode Concentration (HHI)")
    ax.set_ylabel("Playoff Floor-Game Rate")
    ax.set_title(f"Scoring Concentration → PO Floor Risk\nr={r2:.3f}, p={p2:.4f}")
    ax.axhline(0.15, color="gray", linestyle=":", alpha=0.4)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        path = FIGURES_DIR / f"architecture_career_scatter.{ext}"
        fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote architecture_career_scatter")


def plot_architecture_heatmap(merged: pd.DataFrame) -> None:
    """Correlation heatmap of architecture variables + PO floor rate."""
    cols = [
        "rs_fga_retention", "rs_fta_fga_ratio", "hhi_scoring",
        "pct_pts_ft", "rs_floor_rate", "po_floor_rate",
    ]
    available = [c for c in cols if c in merged.columns]
    corr = merged[available].corr()

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax, vmin=-1, vmax=1)
    ax.set_title("Architecture Variables: Correlation Matrix")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(FIGURES_DIR / f"architecture_correlation_heatmap.{ext}", dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote architecture_correlation_heatmap")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    path = config.PROCESSED_DIR / "analysis_table.csv"
    if not path.exists():
        raise FileNotFoundError(f"Run 'make features' first: {path}")

    df = pd.read_csv(path, low_memory=False)
    df["is_playoff"] = df["is_playoff"].astype(bool)
    df["is_floor_primary"] = df["is_floor_primary"].astype(bool)

    logger.info("Computing RS scoring architecture per player-season...")
    arch = compute_season_architecture(df)
    logger.info("Architecture table: %d player-seasons", len(arch))

    logger.info("Computing PO floor-game outcomes per player-season...")
    po = compute_season_po_outcomes(df)
    logger.info("PO outcomes table: %d player-seasons", len(po))

    # Box-score architecture (original)
    career_result = career_level_regression(arch, po)
    season_result = season_level_regression(arch, po)

    # Figures
    plot_career_scatter(career_result["merged"])
    plot_architecture_heatmap(career_result["merged"])

    # Shot-chart architecture (if available)
    sc_arch = load_shot_chart_architecture()
    sc_career_result = None
    combined_result = None

    if sc_arch is not None:
        logger.info("Shot-chart architecture: %d player-seasons", len(sc_arch))
        sc_career_result = shot_chart_career_regression(sc_arch, po)
        combined_result = combined_career_regression(arch, sc_arch, po)
        plot_shot_chart_scatter(sc_career_result["merged"])
    else:
        logger.info("No shot-chart architecture found — run 'make shot-chart-features' first")

    # Summary
    print("\n" + "=" * 70)
    print("ARCHITECTURE MODEL — KILL DECISION")
    print("=" * 70)
    m = career_result.get("model_full")
    if m is not None:
        r2 = m.rsquared
        print(f"\n  Box-score career-level R² = {r2:.3f}")
    else:
        print("\n  Box-score model could not be fit")

    if sc_career_result is not None:
        m_sc = sc_career_result.get("model_full")
        if m_sc is not None:
            r2_sc = m_sc.rsquared
            print(f"  Shot-chart career-level R² = {r2_sc:.3f}")
        else:
            print("  Shot-chart model could not be fit")

    if combined_result is not None:
        m_comb = combined_result.get("model_combined")
        if m_comb is not None:
            r2_comb = m_comb.rsquared
            print(f"  Combined box+shot-chart R² = {r2_comb:.3f}")
            if r2_comb >= 0.25:
                print("\n  PASS — Combined architecture predicts PO floor-game risk (R² >= 0.25)")
                print("  The project has a predictive contribution beyond description.")
            else:
                print("\n  FAIL — Combined architecture does not clear the R² > 0.25 bar")
                print("  Contribution is descriptive: trait stability + opponent adjustment + narrative debunking")
                print("  Shot-chart mode-collapse profiles are still publishable as descriptive finding.")

    mp = career_result.get("model_parsim")
    if mp is not None:
        print(f"\n  Box-score parsimonious (FGA retention + FTA ratio) R² = {mp.rsquared:.3f}")

    if sc_career_result is not None:
        mp_sc = sc_career_result.get("model_parsim")
        if mp_sc is not None:
            print(f"  Shot-chart parsimonious (mode independence + FTA share) R² = {mp_sc.rsquared:.3f}")

    logger.info("Architecture model complete")


if __name__ == "__main__":
    main()
