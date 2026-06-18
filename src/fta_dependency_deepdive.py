"""FTA Dependency Deep-Dive — making the one confirmed risk factor airtight.

FTA dependency (RS FTA/FGA ratio → PO floor-game rate) is the only predictor
that cleared significance (r=+0.30, p=0.028). This script deepens that finding:

Part 1 — Threshold Analysis
    Is the relationship linear, or is there a danger zone?
    Piecewise regression, LOWESS, and bootstrap CIs to identify
    whether a cliff exists at some FTA/FGA ratio.

Part 2 — Mode-Collapse Bridge
    FTA dependency → what breaks → floor game (two-step mechanism).
    High-FTA players' floor games show a specific mode-collapse signature:
    FGA and FTA collapse simultaneously because they're the same action.
    Formally test whether FTA dependency predicts the *type* of collapse.

Part 3 — Multilevel Model (game-level)
    is_floor ~ opponent_defrtg + rs_fta_fga_ratio + interaction + (1|player)
    ~3400 game-level observations instead of 31 career averages.
    The interaction tests: are FTA-dependent players more sensitive to
    opponent quality, or do they floor regardless?

Part 4 — Bootstrap robustness on the career-level correlation.
"""

from __future__ import annotations

import logging
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

FIGURES_DIR = config.FIGURES_DIR
OUTPUT_DIR = config.PROCESSED_DIR

MIN_RS_NONFLOOR = 10
MIN_RS_FLOOR = 3
MIN_PO_GAMES = 5
MIN_RS_GAMES_SEASON = 20
MIN_PO_GAMES_SEASON = 5
MIN_MINUTES = 10

N_BOOTSTRAP = 5000


# ---------------------------------------------------------------------------
# Data loading — reuse the architecture model's feature engineering
# ---------------------------------------------------------------------------

def load_analysis_table() -> pd.DataFrame:
    path = config.PROCESSED_DIR / "analysis_table.csv"
    if not path.exists():
        raise FileNotFoundError(f"Run 'make features' first: {path}")
    df = pd.read_csv(path, low_memory=False)
    df["is_playoff"] = df["is_playoff"].astype(bool)
    df["is_floor_primary"] = df["is_floor_primary"].astype(bool)
    return df


def build_career_table(df: pd.DataFrame) -> pd.DataFrame:
    """Career-level: RS FTA dependency + PO floor rate per player."""
    rs = df[~df["is_playoff"] & (df["minutes"] > 0)].copy()
    po = df[df["is_playoff"] & (df["minutes"] > 0)].copy()

    rows = []
    for player in df["player_name"].unique():
        rs_p = rs[rs["player_name"] == player]
        po_p = po[po["player_name"] == player]

        if len(po_p) < MIN_PO_GAMES:
            continue

        total_fga = rs_p["fga"].sum()
        total_fta = rs_p["fta"].sum()
        if total_fga == 0:
            continue

        fta_fga_ratio = total_fta / total_fga

        # Points decomposition for pct_pts_ft
        pts_ft = rs_p["ftm"].sum()
        pts_total = rs_p["pts"].sum()
        pct_pts_ft = pts_ft / max(pts_total, 1)

        # PO floor rate
        po_floor = po_p["is_floor_primary"].sum()
        po_floor_rate = po_floor / len(po_p)

        # RS FGA/FTA per-36 for mechanism detail
        rs_fga_per36 = (rs_p["fga"] / rs_p["minutes"] * 36).mean()
        rs_fta_per36 = (rs_p["fta"] / rs_p["minutes"] * 36).mean()

        rows.append({
            "player_name": player,
            "rs_fta_fga_ratio": fta_fga_ratio,
            "pct_pts_ft": pct_pts_ft,
            "po_floor_rate": po_floor_rate,
            "n_po_games": len(po_p),
            "n_po_floor": int(po_floor),
            "n_rs_games": len(rs_p),
            "rs_fga_per36": rs_fga_per36,
            "rs_fta_per36": rs_fta_per36,
        })

    return pd.DataFrame(rows)


def build_game_level_table(df: pd.DataFrame) -> pd.DataFrame:
    """Game-level PO observations with player-season RS FTA dependency."""
    rs = df[~df["is_playoff"] & (df["minutes"] > 0)].copy()
    po = df[df["is_playoff"] & (df["minutes"] >= MIN_MINUTES)].copy()

    # Compute RS FTA/FGA ratio per player-season
    rs_season = []
    for (player, season), grp in rs.groupby(["player_name", "season"]):
        if len(grp) < MIN_RS_GAMES_SEASON:
            continue
        total_fga = grp["fga"].sum()
        total_fta = grp["fta"].sum()
        if total_fga == 0:
            continue
        rs_season.append({
            "player_name": player,
            "season": season,
            "rs_fta_fga_ratio": total_fta / total_fga,
            "rs_fga_per36": (grp["fga"] / grp["minutes"] * 36).mean(),
            "rs_fta_per36": (grp["fta"] / grp["minutes"] * 36).mean(),
            "rs_n_games": len(grp),
        })
    rs_df = pd.DataFrame(rs_season)

    # Merge RS features onto PO games
    merged = po.merge(rs_df, on=["player_name", "season"], how="inner")

    # Per-game FGA/FTA per 36 for mechanism analysis
    merged["po_fga_per36"] = merged["fga"] / merged["minutes"] * 36
    merged["po_fta_per36"] = merged["fta"] / merged["minutes"] * 36

    merged["is_floor"] = merged["is_floor_primary"].astype(int)

    return merged


# ---------------------------------------------------------------------------
# Part 1 — Threshold Analysis
# ---------------------------------------------------------------------------

def run_threshold_analysis(career: pd.DataFrame) -> dict:
    """Test whether FTA dependency → PO floor rate has a cliff or is linear."""
    print("\n" + "=" * 70)
    print("PART 1: THRESHOLD ANALYSIS — Is there a danger zone?")
    print("=" * 70)

    x = career["rs_fta_fga_ratio"].values
    y = career["po_floor_rate"].values
    n = len(career)

    # 1a. Linear baseline
    r, p = stats.pearsonr(x, y)
    print(f"\n  Linear: r={r:+.3f}, p={p:.4f} (n={n})")
    slope, intercept, _, _, se = stats.linregress(x, y)
    print(f"  Slope: {slope:+.4f} (+/- {se:.4f})")
    print(f"  Interpretation: each +0.10 FTA/FGA → +{slope * 0.10:.1%} PO floor rate")

    # 1b. Bootstrap CI on the correlation
    boot_rs = []
    rng = np.random.default_rng(42)
    for _ in range(N_BOOTSTRAP):
        idx = rng.choice(n, size=n, replace=True)
        br, _ = stats.pearsonr(x[idx], y[idx])
        boot_rs.append(br)
    boot_rs = np.array(boot_rs)
    ci_lo, ci_hi = np.percentile(boot_rs, [2.5, 97.5])
    print(f"\n  Bootstrap 95% CI on r: [{ci_lo:+.3f}, {ci_hi:+.3f}]")
    print(f"  {'Excludes zero — robust' if ci_lo > 0 else 'Includes zero — fragile'}")

    # 1c. LOWESS to visualize nonlinearity
    lowess_result = sm.nonparametric.lowess(y, x, frac=0.6, return_sorted=True)

    # 1d. Piecewise regression — test candidate breakpoints
    print("\n  --- Piecewise regression: testing breakpoints ---")
    # Test breakpoints at each player's FTA/FGA ratio (excluding extremes)
    sorted_x = np.sort(x)
    candidates = sorted_x[3:-3]  # avoid edge breakpoints with <3 obs per side

    best_bp = None
    best_aic = np.inf
    best_result = None

    for bp in candidates:
        # Create piecewise terms: linear below bp, different slope above
        x_below = np.minimum(x, bp) - bp
        x_above = np.maximum(x - bp, 0)
        X_pw = np.column_stack([np.ones(n), x_below, x_above])
        try:
            model = sm.OLS(y, X_pw).fit()
            if model.aic < best_aic:
                best_aic = model.aic
                best_bp = bp
                best_result = model
        except Exception:
            continue

    # Compare with linear AIC
    X_lin = np.column_stack([np.ones(n), x])
    linear_model = sm.OLS(y, X_lin).fit()
    linear_aic = linear_model.aic

    print(f"\n  Linear AIC: {linear_aic:.1f}")
    print(f"  Best piecewise AIC: {best_aic:.1f} (breakpoint at FTA/FGA = {best_bp:.3f})")
    delta_aic = linear_aic - best_aic
    print(f"  ΔAIC: {delta_aic:.1f} ({'piecewise better' if delta_aic > 2 else 'no improvement'})")

    if best_result is not None and best_bp is not None:
        below_slope = best_result.params[1]
        above_slope = best_result.params[1] + best_result.params[2]
        print(f"\n  Slope below {best_bp:.3f}: {below_slope:+.4f}")
        print(f"  Slope above {best_bp:.3f}: {above_slope:+.4f}")
        if above_slope > below_slope * 2 and delta_aic > 2:
            print(f"  ** CLIFF DETECTED: slope more than doubles above breakpoint **")
        else:
            print(f"  No convincing cliff — relationship is approximately linear")

    # 1e. Tercile analysis — simple diagnostic
    career_sorted = career.sort_values("rs_fta_fga_ratio")
    n_tercile = n // 3
    low = career_sorted.iloc[:n_tercile]
    mid = career_sorted.iloc[n_tercile:2 * n_tercile]
    high = career_sorted.iloc[2 * n_tercile:]

    print(f"\n  --- Tercile analysis ---")
    print(f"  Low FTA dep  (FTA/FGA ≤ {low['rs_fta_fga_ratio'].max():.3f}): "
          f"PO floor = {low['po_floor_rate'].mean():.1%} (n={len(low)})")
    print(f"  Mid FTA dep  (FTA/FGA ≤ {mid['rs_fta_fga_ratio'].max():.3f}): "
          f"PO floor = {mid['po_floor_rate'].mean():.1%} (n={len(mid)})")
    print(f"  High FTA dep (FTA/FGA > {mid['rs_fta_fga_ratio'].max():.3f}): "
          f"PO floor = {high['po_floor_rate'].mean():.1%} (n={len(high)})")

    t_stat, t_p = stats.ttest_ind(
        high["po_floor_rate"], low["po_floor_rate"], equal_var=False,
    )
    d = (high["po_floor_rate"].mean() - low["po_floor_rate"].mean()) / np.sqrt(
        (high["po_floor_rate"].std() ** 2 + low["po_floor_rate"].std() ** 2) / 2
    )
    print(f"  High vs Low: t={t_stat:.2f}, p={t_p:.4f}, d={d:.2f}")

    # 1f. Player-level scatter data for figure
    print(f"\n  --- Player scatter (sorted by FTA dependency) ---")
    for _, row in career.sort_values("rs_fta_fga_ratio", ascending=False).iterrows():
        flag = " ***" if row["rs_fta_fga_ratio"] > (best_bp or 0.40) else ""
        print(f"    {row['player_name']:30s}: FTA/FGA={row['rs_fta_fga_ratio']:.3f}, "
              f"PO floor={row['po_floor_rate']:.1%} ({row['n_po_floor']}/{row['n_po_games']}){flag}")

    return {
        "r": r, "p": p,
        "boot_ci": (ci_lo, ci_hi),
        "lowess": lowess_result,
        "best_breakpoint": best_bp,
        "delta_aic": delta_aic,
        "linear_model": linear_model,
        "piecewise_model": best_result,
        "slope": slope,
        "terciles": {"low": low, "mid": mid, "high": high},
    }


# ---------------------------------------------------------------------------
# Part 2 — Mode-Collapse Bridge
# ---------------------------------------------------------------------------

def run_mode_collapse_bridge(df: pd.DataFrame, career: pd.DataFrame) -> dict:
    """Test the two-step mechanism: FTA dependency → collapse signature → floor game."""
    print("\n" + "=" * 70)
    print("PART 2: MODE-COLLAPSE BRIDGE")
    print("  Does FTA dependency predict *how* a player's offense collapses?")
    print("=" * 70)

    # Load shot-chart collapse profiles if available
    sc_path = config.PROCESSED_DIR / "shot_chart_architecture.csv"
    has_shot_chart = sc_path.exists()

    if has_shot_chart:
        sc = pd.read_csv(sc_path, low_memory=False)
        sc_career = sc.groupby("player_name").agg(
            floor_mode_collapse_ra=("floor_mode_collapse_ra", "mean"),
            floor_mode_collapse_three=("floor_mode_collapse_three", "mean"),
            floor_mode_collapse_ft=("floor_mode_collapse_ft", "mean"),
            floor_mode_collapse_mid=("floor_mode_collapse_mid", "mean"),
            floor_mode_collapse_paint=("floor_mode_collapse_paint", "mean"),
        ).reset_index()
        merged = career.merge(sc_career, on="player_name", how="inner")
    else:
        merged = None
        print("\n  No shot-chart architecture data — using box-score collapse only")

    # 2a. Box-score mode collapse: FGA and FTA co-movement in floor games
    print("\n  --- Box-score: FGA/FTA co-collapse in floor games ---")
    rs = df[~df["is_playoff"] & (df["minutes"] > 0)].copy()
    po = df[df["is_playoff"] & (df["minutes"] > 0)].copy()

    collapse_rows = []
    for player in career["player_name"]:
        po_p = po[po["player_name"] == player]
        rs_p = rs[rs["player_name"] == player]

        if len(po_p) < MIN_PO_GAMES:
            continue

        # RS baselines (non-floor per-36)
        rs_nfl = rs_p[~rs_p["is_floor_primary"]]
        if len(rs_nfl) < MIN_RS_NONFLOOR:
            continue

        rs_fga_baseline = (rs_nfl["fga"] / rs_nfl["minutes"] * 36).mean()
        rs_fta_baseline = (rs_nfl["fta"] / rs_nfl["minutes"] * 36).mean()

        # PO floor games vs non-floor
        po_floor = po_p[po_p["is_floor_primary"]]
        po_nonfloor = po_p[~po_p["is_floor_primary"]]

        if len(po_floor) < 2:
            continue

        po_fl_fga = (po_floor["fga"] / po_floor["minutes"] * 36).mean()
        po_fl_fta = (po_floor["fta"] / po_floor["minutes"] * 36).mean()
        po_nfl_fga = (po_nonfloor["fga"] / po_nonfloor["minutes"] * 36).mean()
        po_nfl_fta = (po_nonfloor["fta"] / po_nonfloor["minutes"] * 36).mean()

        # Collapse = floor vs non-floor shift (in PO)
        fga_collapse = po_fl_fga - po_nfl_fga  # negative = contraction
        fta_collapse = po_fl_fta - po_nfl_fta  # negative = FTA lost

        # Also compute the proportion of total scoring drop from FTA loss
        po_fl_pts = (po_floor["pts"] / po_floor["minutes"] * 36).mean()
        po_nfl_pts = (po_nonfloor["pts"] / po_nonfloor["minutes"] * 36).mean()
        total_pts_drop = po_fl_pts - po_nfl_pts  # should be negative
        fta_pts_drop = fta_collapse  # FTA ≈ 0.44 * FTA attempted points
        # More precisely: lost FTA → lost FTM at the player's FT%
        ft_pct = rs_p["ftm"].sum() / max(rs_p["fta"].sum(), 1)
        fta_pts_contribution = fta_collapse * ft_pct
        fta_share_of_drop = fta_pts_contribution / min(total_pts_drop, -0.01) if total_pts_drop < -0.5 else np.nan

        fta_fga = career[career["player_name"] == player]["rs_fta_fga_ratio"].values[0]

        collapse_rows.append({
            "player_name": player,
            "rs_fta_fga_ratio": fta_fga,
            "po_fga_collapse": fga_collapse,
            "po_fta_collapse": fta_collapse,
            "po_pts_collapse": total_pts_drop,
            "fta_share_of_pts_drop": fta_share_of_drop,
            "po_fl_fga_per36": po_fl_fga,
            "po_fl_fta_per36": po_fl_fta,
            "po_nfl_fga_per36": po_nfl_fga,
            "po_nfl_fta_per36": po_nfl_fta,
            "rs_fga_baseline": rs_fga_baseline,
            "rs_fta_baseline": rs_fta_baseline,
            "ft_pct": ft_pct,
            "n_po_floor": len(po_floor),
        })

    collapse_df = pd.DataFrame(collapse_rows)

    # 2b. FGA-FTA co-collapse correlation
    print(f"\n  Players with PO collapse data: {len(collapse_df)}")

    if len(collapse_df) >= 10:
        # Do FGA and FTA collapse together?
        r_co, p_co = stats.pearsonr(collapse_df["po_fga_collapse"], collapse_df["po_fta_collapse"])
        print(f"\n  FGA-FTA co-collapse: r={r_co:+.3f}, p={p_co:.4f}")
        print(f"  (positive = when FGA drops, FTA drops too — same action)")

        # Does FTA dependency predict the magnitude of FTA collapse?
        r_dep, p_dep = stats.pearsonr(collapse_df["rs_fta_fga_ratio"], collapse_df["po_fta_collapse"])
        print(f"\n  FTA dependency → FTA collapse magnitude: r={r_dep:+.3f}, p={p_dep:.4f}")
        print(f"  (negative = more FTA-dependent → bigger FTA loss in floor games)")

        # Does FTA dependency predict what share of the scoring drop comes from FTA loss?
        valid_share = collapse_df.dropna(subset=["fta_share_of_pts_drop"])
        if len(valid_share) >= 8:
            r_share, p_share = stats.pearsonr(
                valid_share["rs_fta_fga_ratio"], valid_share["fta_share_of_pts_drop"],
            )
            print(f"\n  FTA dependency → FTA share of scoring drop: r={r_share:+.3f}, p={p_share:.4f}")
            print(f"  (positive = more FTA-dependent → higher proportion of damage from FTA loss)")

    # 2c. Shot-chart bridge (if available)
    sc_results = {}
    if merged is not None and len(merged) >= 10:
        print(f"\n  --- Shot-chart: FTA dependency → mode-collapse signature ---")
        for mode in ["ra", "three", "ft"]:
            col = f"floor_mode_collapse_{mode}"
            valid = merged.dropna(subset=[col, "rs_fta_fga_ratio"])
            if len(valid) >= 8:
                r_m, p_m = stats.pearsonr(valid["rs_fta_fga_ratio"], valid[col])
                print(f"  FTA dep → {mode:5s} collapse: r={r_m:+.3f}, p={p_m:.4f} (n={len(valid)})")
                sc_results[mode] = {"r": r_m, "p": p_m}

    # 2d. Print collapse profiles sorted by FTA dependency
    print(f"\n  --- Collapse profiles (sorted by FTA dependency) ---")
    print(f"  {'Player':30s} {'FTA/FGA':>8s} {'FGA drop':>9s} {'FTA drop':>9s} {'Pts drop':>9s} {'FTA% of drop':>12s}")
    print(f"  {'-'*30} {'-'*8} {'-'*9} {'-'*9} {'-'*9} {'-'*12}")
    for _, row in collapse_df.sort_values("rs_fta_fga_ratio", ascending=False).iterrows():
        fta_share_str = f"{row['fta_share_of_pts_drop']:.0%}" if not np.isnan(row.get("fta_share_of_pts_drop", np.nan)) else "N/A"
        print(f"  {row['player_name']:30s} {row['rs_fta_fga_ratio']:8.3f} "
              f"{row['po_fga_collapse']:+9.1f} {row['po_fta_collapse']:+9.1f} "
              f"{row['po_pts_collapse']:+9.1f} {fta_share_str:>12s}")

    collapse_df.to_csv(OUTPUT_DIR / "fta_collapse_profiles.csv", index=False)
    logger.info("Wrote fta_collapse_profiles.csv")

    return {
        "collapse_df": collapse_df,
        "sc_results": sc_results,
    }


# ---------------------------------------------------------------------------
# Part 3 — Multilevel Model
# ---------------------------------------------------------------------------

def run_multilevel_model(game_df: pd.DataFrame) -> dict:
    """Game-level: is_floor ~ opponent + FTA dependency + interaction + (1|player)."""
    print("\n" + "=" * 70)
    print("PART 3: MULTILEVEL MODEL — FTA dependency at game level")
    print("  is_floor ~ opponent_defrtg + rs_fta_fga_ratio + interaction + (1|player)")
    print("=" * 70)

    # Prepare data
    mdata = game_df.dropna(subset=["opponent_defrtg", "rs_fta_fga_ratio"]).copy()

    # Standardize IVs for interpretable interaction
    mdata["opp_defrtg_z"] = (mdata["opponent_defrtg"] - mdata["opponent_defrtg"].mean()) / mdata["opponent_defrtg"].std()
    mdata["fta_dep_z"] = (mdata["rs_fta_fga_ratio"] - mdata["rs_fta_fga_ratio"].mean()) / mdata["rs_fta_fga_ratio"].std()

    print(f"\n  Observations: {len(mdata)}")
    print(f"  Players: {mdata['player_name'].nunique()}")
    print(f"  Floor games: {mdata['is_floor'].sum()} ({mdata['is_floor'].mean():.1%})")

    results = {}

    # Model 1: Null
    print(f"\n  --- Model 1: Null (intercept + random player) ---")
    m1 = smf.mixedlm("is_floor ~ 1", mdata, groups=mdata["player_name"], re_formula="1")
    m1_fit = m1.fit(reml=True)
    icc = m1_fit.cov_re.iloc[0, 0] / (m1_fit.cov_re.iloc[0, 0] + m1_fit.scale)
    print(f"  ICC (player): {icc:.3f}")
    print(f"  Interpretation: {icc:.0%} of floor-game variance is between-player")
    results["null"] = m1_fit

    # Model 2: Opponent only
    print(f"\n  --- Model 2: Opponent quality only ---")
    m2 = smf.mixedlm(
        "is_floor ~ opp_defrtg_z", mdata,
        groups=mdata["player_name"], re_formula="1",
    )
    m2_fit = m2.fit(reml=True)
    print(m2_fit.summary().tables[1].to_string())
    results["opp_only"] = m2_fit

    # Model 3: FTA dependency (cross-level) — the key test
    print(f"\n  --- Model 3: FTA dependency (cross-level predictor) ---")
    m3 = smf.mixedlm(
        "is_floor ~ opp_defrtg_z + fta_dep_z", mdata,
        groups=mdata["player_name"], re_formula="1",
    )
    m3_fit = m3.fit(reml=True)
    print(m3_fit.summary().tables[1].to_string())

    fta_coef = m3_fit.params.get("fta_dep_z", np.nan)
    fta_p = m3_fit.pvalues.get("fta_dep_z", np.nan)
    print(f"\n  FTA dependency effect: β={fta_coef:+.4f}, p={fta_p:.4f}")
    print(f"  Interpretation: +1 SD in FTA dependency → +{fta_coef:.4f} floor probability")
    results["fta_main"] = m3_fit

    # Model 4: Interaction — does FTA dependency amplify opponent effect?
    print(f"\n  --- Model 4: Interaction (FTA dep × opponent quality) ---")
    m4 = smf.mixedlm(
        "is_floor ~ opp_defrtg_z * fta_dep_z", mdata,
        groups=mdata["player_name"], re_formula="1",
    )
    m4_fit = m4.fit(reml=True)
    print(m4_fit.summary().tables[1].to_string())

    ix_coef = m4_fit.params.get("opp_defrtg_z:fta_dep_z", np.nan)
    ix_p = m4_fit.pvalues.get("opp_defrtg_z:fta_dep_z", np.nan)
    print(f"\n  Interaction effect: β={ix_coef:+.4f}, p={ix_p:.4f}")
    if not np.isnan(ix_p):
        if ix_p < 0.05:
            if ix_coef < 0:
                print(f"  ** SIGNIFICANT: FTA-dependent players are MORE sensitive to opponent quality **")
                print(f"     (Their floor risk increases more against elite defenses)")
            else:
                print(f"  ** SIGNIFICANT: FTA-dependent players are LESS sensitive to opponent quality **")
                print(f"     (They floor regardless — base-rate risk, not matchup risk)")
        else:
            print(f"  Interaction is null — FTA dependency is a base-rate risk factor,")
            print(f"  not modulated by opponent quality")
    results["interaction"] = m4_fit

    # Model comparison
    print(f"\n  --- Model comparison ---")
    for name, fit in results.items():
        aic_val = fit.aic if hasattr(fit, 'aic') and not np.isnan(fit.aic) else "N/A"
        print(f"  {name:15s}: AIC={aic_val}")

    # Pseudo R² (proportional reduction in residual variance)
    r2_m3 = 1 - m3_fit.scale / m1_fit.scale
    r2_m4 = 1 - m4_fit.scale / m1_fit.scale
    print(f"\n  Pseudo R² (vs null):")
    print(f"    Model 3 (main effects): {r2_m3:.4f}")
    print(f"    Model 4 (interaction):  {r2_m4:.4f}")

    return results


# ---------------------------------------------------------------------------
# Part 4 — Robustness: alternative FTA dependency measures
# ---------------------------------------------------------------------------

def run_robustness(career: pd.DataFrame) -> None:
    """Test alternative operationalizations of FTA dependency."""
    print("\n" + "=" * 70)
    print("PART 4: ROBUSTNESS — Alternative FTA dependency measures")
    print("=" * 70)

    # Already have FTA/FGA ratio. Also test:
    # - pct_pts_ft (share of scoring from free throws)
    # - rs_fta_per36 (absolute FTA volume)

    measures = [
        ("rs_fta_fga_ratio", "FTA/FGA ratio"),
        ("pct_pts_ft", "% pts from FT"),
        ("rs_fta_per36", "FTA per 36 min"),
    ]

    print(f"\n  {'Measure':25s} {'r':>8s} {'p':>10s} {'boot 95% CI':>20s}")
    print(f"  {'-'*25} {'-'*8} {'-'*10} {'-'*20}")

    rng = np.random.default_rng(42)
    n = len(career)

    for col, label in measures:
        valid = career.dropna(subset=[col, "po_floor_rate"])
        if len(valid) < 10:
            print(f"  {label:25s}  insufficient data")
            continue

        x = valid[col].values
        y = valid["po_floor_rate"].values
        r, p = stats.pearsonr(x, y)

        boot_rs = []
        for _ in range(N_BOOTSTRAP):
            idx = rng.choice(len(valid), size=len(valid), replace=True)
            br, _ = stats.pearsonr(x[idx], y[idx])
            boot_rs.append(br)
        ci_lo, ci_hi = np.percentile(boot_rs, [2.5, 97.5])

        robust = "robust" if ci_lo > 0 else "fragile"
        print(f"  {label:25s} {r:+.3f}  {p:10.4f}  [{ci_lo:+.3f}, {ci_hi:+.3f}] ({robust})")

    # Rank-order correlation (Spearman) as nonparametric check
    print(f"\n  --- Spearman (rank-order, nonparametric) ---")
    for col, label in measures:
        valid = career.dropna(subset=[col, "po_floor_rate"])
        if len(valid) < 10:
            continue
        rho, p = stats.spearmanr(valid[col], valid["po_floor_rate"])
        print(f"  {label:25s}: ρ={rho:+.3f}, p={p:.4f}")

    # Leave-one-out sensitivity — which players are leverage points?
    print(f"\n  --- Leave-one-out influence (FTA/FGA ratio) ---")
    full_r, _ = stats.pearsonr(career["rs_fta_fga_ratio"], career["po_floor_rate"])
    loo_results = []
    for i, row in career.iterrows():
        subset = career.drop(i)
        r_loo, _ = stats.pearsonr(subset["rs_fta_fga_ratio"], subset["po_floor_rate"])
        delta = full_r - r_loo
        loo_results.append({"player_name": row["player_name"], "r_without": r_loo, "influence": delta})

    loo_df = pd.DataFrame(loo_results).sort_values("influence", ascending=False)
    print(f"\n  Full r = {full_r:+.3f}")
    print(f"  {'Player':30s} {'r without':>10s} {'influence':>10s}")
    print(f"  {'-'*30} {'-'*10} {'-'*10}")
    for _, row in loo_df.iterrows():
        flag = " **" if abs(row["influence"]) > 0.03 else ""
        print(f"  {row['player_name']:30s} {row['r_without']:+10.3f} {row['influence']:+10.3f}{flag}")

    max_influence = loo_df["influence"].abs().max()
    max_player = loo_df.loc[loo_df["influence"].abs().idxmax(), "player_name"]
    print(f"\n  Most influential: {max_player} (Δr = {max_influence:+.3f})")
    if max_influence > 0.05:
        print(f"  WARNING: result depends heavily on {max_player}")
    else:
        print(f"  No single player dominates — finding is not leverage-dependent")


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def produce_figures(career: pd.DataFrame, threshold_results: dict, collapse_results: dict) -> None:
    """Generate the key figures for the FTA dependency deep-dive."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(18, 16))

    # Panel 1: FTA dependency → PO floor rate with LOWESS
    ax = axes[0, 0]
    for _, row in career.iterrows():
        color = config.GROUP_A_COLOR if row["player_name"] in config.GROUP_A else config.GROUP_B_COLOR
        ax.scatter(
            row["rs_fta_fga_ratio"], row["po_floor_rate"],
            s=max(row["n_po_games"], 20),
            color=color, alpha=0.7, edgecolors="black", linewidth=0.5,
        )
        ax.annotate(
            row["player_name"].split()[-1],
            (row["rs_fta_fga_ratio"], row["po_floor_rate"]),
            fontsize=6, alpha=0.8, xytext=(4, 4), textcoords="offset points",
        )

    # LOWESS line
    lowess = threshold_results["lowess"]
    ax.plot(lowess[:, 0], lowess[:, 1], color="black", linewidth=2, label="LOWESS")

    # Linear fit
    x_line = np.linspace(career["rs_fta_fga_ratio"].min(), career["rs_fta_fga_ratio"].max(), 100)
    lm = threshold_results["linear_model"]
    y_line = lm.params[0] + lm.params[1] * x_line
    ax.plot(x_line, y_line, color="gray", linewidth=1, linestyle="--", label="Linear fit")

    # Breakpoint if detected
    bp = threshold_results.get("best_breakpoint")
    if bp and threshold_results["delta_aic"] > 2:
        ax.axvline(bp, color="red", linestyle=":", alpha=0.7, label=f"Breakpoint ({bp:.3f})")

    ax.axhline(0.15, color="gray", linestyle=":", alpha=0.3)
    r = threshold_results["r"]
    p = threshold_results["p"]
    ci = threshold_results["boot_ci"]
    ax.set_xlabel("RS FTA/FGA Ratio (FTA Dependency)")
    ax.set_ylabel("Playoff Floor-Game Rate")
    ax.set_title(f"FTA Dependency → PO Floor Risk\nr={r:+.3f}, p={p:.4f} | 95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]")
    ax.legend(fontsize=8, loc="upper left")

    # Panel 2: Bootstrap distribution of r
    ax = axes[0, 1]
    rng = np.random.default_rng(42)
    boot_rs = []
    x_vals = career["rs_fta_fga_ratio"].values
    y_vals = career["po_floor_rate"].values
    n = len(career)
    for _ in range(N_BOOTSTRAP):
        idx = rng.choice(n, size=n, replace=True)
        br, _ = stats.pearsonr(x_vals[idx], y_vals[idx])
        boot_rs.append(br)
    ax.hist(boot_rs, bins=50, color=config.GROUP_A_COLOR, alpha=0.7, edgecolor="black", linewidth=0.3)
    ax.axvline(0, color="black", linewidth=1.5)
    ax.axvline(r, color="blue", linewidth=2, label=f"Observed r={r:+.3f}")
    ax.axvline(ci[0], color="red", linestyle="--", label=f"95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]")
    ax.axvline(ci[1], color="red", linestyle="--")
    pct_above_zero = np.mean(np.array(boot_rs) > 0) * 100
    ax.set_xlabel("Bootstrap r (FTA/FGA → PO floor rate)")
    ax.set_ylabel("Count")
    ax.set_title(f"Bootstrap Distribution (n={N_BOOTSTRAP})\n{pct_above_zero:.1f}% of bootstraps > 0")
    ax.legend(fontsize=8)

    # Panel 3: FGA-FTA co-collapse
    ax = axes[1, 0]
    collapse_df = collapse_results["collapse_df"]
    for _, row in collapse_df.iterrows():
        color = config.GROUP_A_COLOR if row["player_name"] in config.GROUP_A else config.GROUP_B_COLOR
        ax.scatter(
            row["po_fga_collapse"], row["po_fta_collapse"],
            s=max(row.get("n_po_floor", 3) * 8, 20),
            color=color, alpha=0.7, edgecolors="black", linewidth=0.5,
        )
        ax.annotate(
            row["player_name"].split()[-1],
            (row["po_fga_collapse"], row["po_fta_collapse"]),
            fontsize=6, alpha=0.7, xytext=(3, 3), textcoords="offset points",
        )
    if len(collapse_df) >= 5:
        r_co, p_co = stats.pearsonr(collapse_df["po_fga_collapse"], collapse_df["po_fta_collapse"])
        ax.set_title(f"FGA-FTA Co-Collapse in PO Floor Games\nr={r_co:+.3f}, p={p_co:.4f}")
    ax.set_xlabel("FGA Collapse (floor - non-floor, per 36)")
    ax.set_ylabel("FTA Collapse (floor - non-floor, per 36)")
    ax.axhline(0, color="gray", linewidth=0.5, alpha=0.5)
    ax.axvline(0, color="gray", linewidth=0.5, alpha=0.5)

    # Panel 4: FTA dependency → FTA share of scoring drop
    ax = axes[1, 1]
    valid_share = collapse_df.dropna(subset=["fta_share_of_pts_drop"])
    if len(valid_share) >= 5:
        for _, row in valid_share.iterrows():
            color = config.GROUP_A_COLOR if row["player_name"] in config.GROUP_A else config.GROUP_B_COLOR
            ax.scatter(
                row["rs_fta_fga_ratio"], row["fta_share_of_pts_drop"],
                s=max(row.get("n_po_floor", 3) * 8, 20),
                color=color, alpha=0.7, edgecolors="black", linewidth=0.5,
            )
            ax.annotate(
                row["player_name"].split()[-1],
                (row["rs_fta_fga_ratio"], row["fta_share_of_pts_drop"]),
                fontsize=6, alpha=0.7, xytext=(3, 3), textcoords="offset points",
            )
        r_s, p_s = stats.pearsonr(valid_share["rs_fta_fga_ratio"], valid_share["fta_share_of_pts_drop"])
        ax.set_title(f"FTA Dependency → FTA Share of Scoring Collapse\nr={r_s:+.3f}, p={p_s:.4f}")
    ax.set_xlabel("RS FTA/FGA Ratio (FTA Dependency)")
    ax.set_ylabel("FTA Share of Pts/36 Drop in Floor Games")
    ax.axhline(0, color="gray", linewidth=0.5, alpha=0.5)

    plt.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(FIGURES_DIR / f"fta_dependency_deepdive.{ext}", dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote fta_dependency_deepdive figures")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 70)
    print("FTA DEPENDENCY DEEP-DIVE")
    print("Making the one confirmed risk factor airtight")
    print("=" * 70)

    df = load_analysis_table()
    logger.info("Loaded %d games (%d PO)", len(df), df["is_playoff"].sum())

    career = build_career_table(df)
    logger.info("Career table: %d players", len(career))

    game_df = build_game_level_table(df)
    logger.info("Game-level table: %d PO observations", len(game_df))

    # Part 1: Threshold
    threshold_results = run_threshold_analysis(career)

    # Part 2: Mode-collapse bridge
    collapse_results = run_mode_collapse_bridge(df, career)

    # Part 3: Multilevel model
    multilevel_results = run_multilevel_model(game_df)

    # Part 4: Robustness
    run_robustness(career)

    # Figures
    produce_figures(career, threshold_results, collapse_results)

    # Summary
    print("\n" + "=" * 70)
    print("FTA DEPENDENCY DEEP-DIVE — VERDICT")
    print("=" * 70)

    r = threshold_results["r"]
    p = threshold_results["p"]
    ci = threshold_results["boot_ci"]
    print(f"\n  Career-level: r={r:+.3f}, p={p:.4f}")
    print(f"  Bootstrap 95% CI: [{ci[0]:+.3f}, {ci[1]:+.3f}]")

    m3 = multilevel_results.get("fta_main")
    if m3 is not None:
        fta_p = m3.pvalues.get("fta_dep_z", np.nan)
        fta_b = m3.params.get("fta_dep_z", np.nan)
        print(f"\n  Game-level multilevel: β={fta_b:+.4f}, p={fta_p:.4f}")

    m4 = multilevel_results.get("interaction")
    if m4 is not None:
        ix_p = m4.pvalues.get("opp_defrtg_z:fta_dep_z", np.nan)
        ix_b = m4.params.get("opp_defrtg_z:fta_dep_z", np.nan)
        print(f"  Interaction (FTA dep × opponent): β={ix_b:+.4f}, p={ix_p:.4f}")

    delta_aic = threshold_results["delta_aic"]
    bp = threshold_results["best_breakpoint"]
    if delta_aic > 2:
        print(f"\n  Threshold: cliff at FTA/FGA = {bp:.3f} (ΔAIC = {delta_aic:.1f})")
    else:
        print(f"\n  No threshold — relationship is approximately linear")

    print(f"\n  Output files:")
    print(f"    data/processed/fta_collapse_profiles.csv")
    print(f"    output/figures/fta_dependency_deepdive.{{png,svg}}")

    logger.info("FTA dependency deep-dive complete")


if __name__ == "__main__":
    main()
