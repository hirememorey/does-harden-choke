"""Resilience Quotient (RQ) as DV in a game-level multilevel model.

Borrowed from resilience-basketball's Dual-Grade system:
    RQ = (PO Volume / RS Volume) × (PO Efficiency / RS Efficiency)

Where:
    Volume = FGA/36 (shot attempt rate — captures engagement / abdication)
    Efficiency = TS% (true shooting — captures shot quality / forcing)

RQ is computed per *game* (PO games only, with RS season baseline as denominator).
This gives ~3389 game-level observations instead of 31 career averages.

Level 1 (game): RQ ~ opponent_defrtg + is_elimination + series_game_num + (1|player)
Level 2 (player): RS architecture variables as cross-level predictors

RS architecture IVs (all observable before playoffs):
    rs_fta_fga_ratio      FTA dependency — foul-drawing reliance
    rs_fga_retention      Volume retention in RS floor games (stable trait r=0.72)
    rs_fta_retention      FTA-specific collapse signal (rim abandonment)
    hhi_scoring           Concentration across scoring modes
    pct_pts_ft            Share of scoring from free throws
    rs_floor_rate         Base rate of RS floor games (~15% by construction)
    rs_opponent_gradient  Floor-rate gradient across opponent quality terciles

Success: significant cross-level effects or R²_conditional > 0.25
Kill: no cross-level effects and R²_conditional < 0.15
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

MIN_RS_GAMES_SEASON = 20
MIN_PO_GAMES_SEASON = 5
MIN_MINUTES_GAME = 10


def load_data() -> pd.DataFrame:
    path = config.PROCESSED_DIR / "analysis_table.csv"
    if not path.exists():
        raise FileNotFoundError(f"Run 'make features' first: {path}")
    df = pd.read_csv(path, low_memory=False)
    df["is_playoff"] = df["is_playoff"].astype(bool)
    df["is_floor_primary"] = df["is_floor_primary"].astype(bool)
    return df


def compute_rs_season_baselines(df: pd.DataFrame) -> pd.DataFrame:
    rs = df[~df["is_playoff"] & (df["minutes"] > 0)].copy()

    rows = []
    for (player, season), grp in rs.groupby(["player_name", "season"]):
        if len(grp) < MIN_RS_GAMES_SEASON:
            continue

        fga_per36 = (grp["fga"] / grp["minutes"] * 36).mean()
        fta_per36 = (grp["fta"] / grp["minutes"] * 36).mean()
        pts_per36 = (grp["pts"] / grp["minutes"] * 36).mean()

        total_fga = grp["fga"].sum()
        total_fta = grp["fta"].sum()
        total_pts = grp["pts"].sum()

        ts_mean = grp["ts_pct"].mean()
        usg_mean = grp["usg_pct"].mean()

        fl = grp[grp["is_floor_primary"] == True]
        nfl = grp[grp["is_floor_primary"] == False]

        fga_ret = np.nan
        fta_ret = np.nan
        if len(fl) >= 3 and len(nfl) >= 10:
            nfl_fga = (nfl["fga"] / nfl["minutes"] * 36).mean()
            fl_fga = (fl["fga"] / fl["minutes"] * 36).mean()
            nfl_fta = (nfl["fta"] / nfl["minutes"] * 36).mean()
            fl_fta = (fl["fta"] / fl["minutes"] * 36).mean()
            fga_ret = fl_fga / max(nfl_fga, 0.01)
            fta_ret = fl_fta / max(nfl_fta, 0.01) if nfl_fta > 0.5 else np.nan

        fta_fga_ratio = total_fta / max(total_fga, 1)

        pts_2pm = 2 * (grp["fgm"] - grp["fg3m"]).sum()
        pts_3pm = 3 * grp["fg3m"].sum()
        pts_ft = grp["ftm"].sum()
        total_pts_check = pts_2pm + pts_3pm + pts_ft
        if total_pts_check <= 0:
            continue
        pct_pts_2pm = pts_2pm / total_pts_check
        pct_pts_3pm = pts_3pm / total_pts_check
        pct_pts_ft = pts_ft / total_pts_check
        hhi = pct_pts_2pm**2 + pct_pts_3pm**2 + pct_pts_ft**2

        opponent_grad = np.nan
        if "opponent_defrtg" in grp.columns:
            valid = grp.dropna(subset=["opponent_defrtg"])
            if len(valid) >= 10:
                weak = valid[valid["opponent_defrtg"] >= valid["opponent_defrtg"].quantile(0.667)]
                strong = valid[valid["opponent_defrtg"] <= valid["opponent_defrtg"].quantile(0.333)]
                if len(weak) >= 3 and len(strong) >= 3:
                    weak_floor = weak["is_floor_primary"].mean()
                    strong_floor = strong["is_floor_primary"].mean()
                    opponent_grad = weak_floor - strong_floor

        rows.append({
            "player_name": player,
            "season": season,
            "rs_fga_per36": fga_per36,
            "rs_fta_per36": fta_per36,
            "rs_pts_per36": pts_per36,
            "rs_ts_pct": ts_mean,
            "rs_usg_pct": usg_mean,
            "rs_n_games": len(grp),
            "rs_fga_retention": fga_ret,
            "rs_fta_retention": fta_ret,
            "rs_fta_fga_ratio": fta_fga_ratio,
            "hhi_scoring": hhi,
            "pct_pts_ft": pct_pts_ft,
            "rs_floor_rate": len(fl) / len(grp),
            "rs_opponent_gradient": opponent_grad,
        })

    return pd.DataFrame(rows)


def compute_game_level_rq(po_games: pd.DataFrame, rs_baselines: pd.DataFrame) -> pd.DataFrame:
    po = po_games[po_games["minutes"] >= MIN_MINUTES_GAME].copy()

    po["po_fga_per36"] = po["fga"] / po["minutes"] * 36
    po["po_pts_per36"] = po["pts"] / po["minutes"] * 36

    merged = po.merge(
        rs_baselines,
        on=["player_name", "season"],
        how="inner",
    )

    merged["volume_ratio"] = merged["po_fga_per36"] / merged["rs_fga_per36"].clip(lower=1.0)
    merged["efficiency_ratio"] = merged["ts_pct"] / merged["rs_ts_pct"].clip(lower=0.3)

    merged["rq"] = merged["volume_ratio"] * merged["efficiency_ratio"]

    merged["log_rq"] = np.log(merged["rq"].clip(lower=0.01))

    merged["is_floor"] = merged["is_floor_primary"].astype(int)

    return merged


def run_descriptive_stats(df: pd.DataFrame) -> None:
    print("=" * 70)
    print("RQ MULTILEVEL MODEL — DESCRIPTIVE STATISTICS")
    print("=" * 70)

    print(f"\nGame-level observations: {len(df)}")
    print(f"Players: {df['player_name'].nunique()}")
    print(f"Player-seasons: {df.groupby(['player_name', 'season']).ngroups}")

    print(f"\nRQ distribution:")
    print(f"  Mean:  {df['rq'].mean():.3f}")
    print(f"  Median: {df['rq'].median():.3f}")
    print(f"  SD:    {df['rq'].std():.3f}")
    print(f"  Min:   {df['rq'].min():.3f}")
    print(f"  Max:   {df['rq'].max():.3f}")
    print(f"  Skew:  {df['rq'].skew():.3f}")

    floor_rq = df[df["is_floor"] == 1]["rq"]
    nonfloor_rq = df[df["is_floor"] == 0]["rq"]
    print(f"\nRQ by floor status:")
    print(f"  Non-floor games: mean={nonfloor_rq.mean():.3f}, median={nonfloor_rq.median():.3f} (n={len(nonfloor_rq)})")
    print(f"  Floor games:      mean={floor_rq.mean():.3f}, median={floor_rq.median():.3f} (n={len(floor_rq)})")
    t, p = stats.ttest_ind(nonfloor_rq, floor_rq)
    d = (nonfloor_rq.mean() - floor_rq.mean()) / np.sqrt((nonfloor_rq.std()**2 + floor_rq.std()**2) / 2)
    print(f"  t={t:.2f}, p={p:.4f}, d={d:.2f}")

    print(f"\nRQ by player (selected):")
    for name in ["James Harden", "Kevin Durant", "Stephen Curry", "Jimmy Butler",
                  "Nikola Jokic", "Paul George", "Luka Doncic", "Ben Simmons",
                  "DeMar DeRozan", "Dirk Nowitzki", "Joel Embiid", "Shai Gilgeous-Alexander"]:
        sub = df[df["player_name"] == name]
        if len(sub) >= 5:
            fl = sub[sub["is_floor"] == 1]
            print(f"  {name:30s}: RQ={sub['rq'].mean():.3f} "
                  f"(floor={fl['rq'].mean():.3f}, n={len(fl)}) "
                  f"non-floor={sub[sub['is_floor']==0]['rq'].mean():.3f}, n={len(sub)}")


def run_bivariate(df: pd.DataFrame) -> None:
    print("\n" + "=" * 70)
    print("BIVARIATE: RS ARCHITECTURE vs. MEAN RQ (player-season level)")
    print("=" * 70)

    ps = df.groupby(["player_name", "season"]).agg(
        mean_rq=("rq", "mean"),
        rs_fta_fga_ratio=("rs_fta_fga_ratio", "first"),
        rs_fga_retention=("rs_fga_retention", "first"),
        rs_fta_retention=("rs_fta_retention", "first"),
        hhi_scoring=("hhi_scoring", "first"),
        pct_pts_ft=("pct_pts_ft", "first"),
        rs_floor_rate=("rs_floor_rate", "first"),
        rs_opponent_gradient=("rs_opponent_gradient", "first"),
        rs_usg_pct=("rs_usg_pct", "first"),
    ).reset_index()

    iv_cols = [
        "rs_fta_fga_ratio", "rs_fga_retention", "rs_fta_retention",
        "hhi_scoring", "pct_pts_ft", "rs_floor_rate",
        "rs_opponent_gradient", "rs_usg_pct",
    ]

    print(f"\nPlayer-seasons: {len(ps)}")
    print(f"\n{'Variable':30s} {'r':>8s} {'p':>10s} {'n':>6s}")
    print("-" * 58)
    for col in iv_cols:
        valid = ps.dropna(subset=[col, "mean_rq"])
        if len(valid) < 10:
            continue
        r, p = stats.pearsonr(valid[col], valid["mean_rq"])
        print(f"  {col:28s} {r:+.3f}  {p:.4f}  {len(valid)}")

    print("\n" + "=" * 70)
    print("BIVARIATE: RS ARCHITECTURE vs. CAREER-LEVEL RQ (n=31)")
    print("=" * 70)

    career = df.groupby("player_name").agg(
        career_rq=("rq", "mean"),
        rs_fta_fga_ratio=("rs_fta_fga_ratio", "mean"),
        rs_fga_retention=("rs_fga_retention", "mean"),
        rs_fta_retention=("rs_fta_retention", "mean"),
        hhi_scoring=("hhi_scoring", "mean"),
        pct_pts_ft=("pct_pts_ft", "mean"),
        rs_floor_rate=("rs_floor_rate", "mean"),
        rs_opponent_gradient=("rs_opponent_gradient", "mean"),
        rs_usg_pct=("rs_usg_pct", "mean"),
    ).reset_index()

    print(f"\nPlayers: {len(career)}")
    print(f"\n{'Variable':30s} {'r':>8s} {'p':>10s} {'n':>6s}")
    print("-" * 58)
    for col in iv_cols:
        valid = career.dropna(subset=[col, "career_rq"])
        if len(valid) < 10:
            continue
        r, p = stats.pearsonr(valid[col], valid["career_rq"])
        print(f"  {col:28s} {r:+.3f}  {p:.4f}  {len(valid)}")


def run_multilevel_models(df: pd.DataFrame) -> dict:
    results = {}

    print("\n" + "=" * 70)
    print("MODEL 1: NULL MODEL — RQ ~ (1|player)")
    print("=" * 70)

    m1 = smf.mixedlm("log_rq ~ 1", df, groups=df["player_name"], re_formula="1")
    m1_fit = m1.fit(reml=True)
    print(m1_fit.summary().tables[1].to_string())
    icc = m1_fit.cov_re.iloc[0, 0] / (m1_fit.cov_re.iloc[0, 0] + m1_fit.scale)
    print(f"\n  ICC (player): {icc:.3f}")
    print(f"  Player-level variance: {m1_fit.cov_re.iloc[0, 0]:.4f}")
    print(f"  Residual variance:     {m1_fit.scale:.4f}")
    results["null"] = m1_fit

    print("\n" + "=" * 70)
    print("MODEL 2: GAME-LEVEL PREDICTORS — log(RQ) ~ opponent + leverage + (1|player)")
    print("=" * 70)

    model2_cols = ["log_rq", "player_name", "opponent_defrtg", "series_game_num",
                   "is_elimination", "is_floor", "home_away"]
    m2_data = df.dropna(subset=["opponent_defrtg", "series_game_num"]).copy()
    m2_data["is_elimination"] = m2_data["is_elimination"].fillna(False).astype(bool).astype(int)
    m2_data["series_game_num"] = pd.to_numeric(m2_data["series_game_num"], errors="coerce")

    m2_data["is_home"] = (m2_data["home_away"].str.upper() == "HOME").astype(int)

    m2 = smf.mixedlm(
        "log_rq ~ opponent_defrtg + series_game_num + is_elimination + is_home",
        m2_data,
        groups=m2_data["player_name"],
        re_formula="1",
    )
    try:
        m2_fit = m2.fit(reml=True)
    except np.linalg.LinAlgError:
        logger.warning("Model 2 singular with series_game_num — falling back to simpler formula")
        m2 = smf.mixedlm(
            "log_rq ~ opponent_defrtg + is_elimination + is_home",
            m2_data,
            groups=m2_data["player_name"],
            re_formula="1",
        )
        m2_fit = m2.fit(reml=True)
    print(m2_fit.summary().tables[1].to_string())
    print(f"\n  AIC: {m2_fit.aic:.1f} (null: {m1_fit.aic:.1f})")
    results["game_level"] = m2_fit

    print("\n" + "=" * 70)
    print("MODEL 3: FULL MODEL — log(RQ) ~ game-level + RS architecture + (1|player)")
    print("  Cross-level: RS architecture as player-level moderators")
    print("=" * 70)

    m3_data = m2_data.copy()

    arch_cols = ["rs_fta_fga_ratio", "rs_fga_retention", "hhi_scoring",
                 "pct_pts_ft", "rs_opponent_gradient"]
    m3_data = m3_data.dropna(subset=arch_cols)

    print(f"\n  Observations: {len(m3_data)}")
    print(f"  Players: {m3_data['player_name'].nunique()}")

    m3 = smf.mixedlm(
        "log_rq ~ opponent_defrtg + is_elimination + is_home + "
        "rs_fta_fga_ratio + rs_fga_retention + hhi_scoring + pct_pts_ft + rs_opponent_gradient",
        m3_data,
        groups=m3_data["player_name"],
        re_formula="1",
    )
    m3_fit = m3.fit(reml=True)
    print(m3_fit.summary().tables[1].to_string())

    r2_cond = 1 - m3_fit.scale / m1_fit.scale
    print(f"\n  Pseudo R² (conditional vs null): {r2_cond:.3f}")
    print(f"  AIC: {m3_fit.aic:.1f}")
    results["full"] = m3_fit

    print("\n" + "=" * 70)
    print("MODEL 4: INTERACTION — RS architecture × opponent quality")
    print("  Does FTA dependency amplify the opponent effect on RQ?")
    print("=" * 70)

    m4 = smf.mixedlm(
        "log_rq ~ opponent_defrtg * rs_fta_fga_ratio + "
        "opponent_defrtg * rs_opponent_gradient + "
        "is_elimination + is_home + "
        "rs_fga_retention + hhi_scoring + pct_pts_ft",
        m3_data,
        groups=m3_data["player_name"],
        re_formula="1",
    )
    m4_fit = m4.fit(reml=True)
    print(m4_fit.summary().tables[1].to_string())
    print(f"\n  AIC: {m4_fit.aic:.1f} (full: {m3_fit.aic:.1f})")
    results["interaction"] = m4_fit

    return results


def run_floor_game_model(df: pd.DataFrame) -> None:
    print("\n" + "=" * 70)
    print("MODEL 5: FLOOR GAME PREDICTION — is_floor ~ RQ + architecture + (1|player)")
    print("  Logistic multilevel: does RS architecture predict floor-game likelihood,")
    print("  and does RQ mediate the relationship?")
    print("=" * 70)

    m5_data = df.dropna(subset=["opponent_defrtg", "rs_fta_fga_ratio",
                                 "rs_fga_retention", "hhi_scoring"]).copy()
    m5_data["is_elimination"] = m5_data["is_elimination"].fillna(False).astype(bool).astype(int)
    m5_data["is_home"] = (m5_data["home_away"].str.upper() == "HOME").astype(int)

    print(f"\n  Observations: {len(m5_data)}")
    print(f"  Floor games: {m5_data['is_floor'].sum()}")
    print(f"  Non-floor: {(m5_data['is_floor'] == 0).sum()}")

    m5_null = smf.mixedlm(
        "is_floor ~ 1",
        m5_data,
        groups=m5_data["player_name"],
        re_formula="1",
    )
    m5_null_fit = m5_null.fit(reml=True)

    m5_arch = smf.mixedlm(
        "is_floor ~ opponent_defrtg + is_elimination + is_home + "
        "rs_fta_fga_ratio + rs_fga_retention + hhi_scoring + pct_pts_ft + rs_opponent_gradient",
        m5_data,
        groups=m5_data["player_name"],
        re_formula="1",
    )
    m5_arch_fit = m5_arch.fit(reml=True)

    print("\n  --- Null model (intercept only) ---")
    print(m5_null_fit.summary().tables[1].to_string())

    print("\n  --- Architecture model ---")
    print(m5_arch_fit.summary().tables[1].to_string())

    print(f"\n  Null AIC: {m5_null_fit.aic:.1f}")
    print(f"  Architecture AIC: {m5_arch_fit.aic:.1f}")
    delta_aic = m5_null_fit.aic - m5_arch_fit.aic
    print(f"  ΔAIC: {delta_aic:.1f} ({'arch better' if delta_aic > 0 else 'null better'})")


def run_rq_vs_floor_rate(df: pd.DataFrame) -> None:
    print("\n" + "=" * 70)
    print("MODEL 6: RQ vs PO FLOOR RATE — career level")
    print("  Does career-mean RQ predict career PO floor rate?")
    print("  (Direct comparison with failed architecture model R²=0.128)")
    print("=" * 70)

    career = df.groupby("player_name").agg(
        career_rq=("rq", "mean"),
        career_rq_sd=("rq", "std"),
        n_po_games=("game_id", "count"),
        n_floor=("is_floor", "sum"),
    ).reset_index()
    career["po_floor_rate"] = career["n_floor"] / career["n_po_games"]

    valid = career.dropna(subset=["career_rq", "po_floor_rate"])
    r, p = stats.pearsonr(valid["career_rq"], valid["po_floor_rate"])
    print(f"\n  Career RQ → PO floor rate: r={r:+.3f}, p={p:.4f} (n={len(valid)})")
    print(f"  (Previous best: FTA/FGA ratio r=+0.303, p=0.098)")

    m = smf.ols("po_floor_rate ~ career_rq", data=valid).fit()
    print(f"\n  OLS: R²={m.rsquared:.3f}")
    print(f"  (Previous architecture model: R²=0.128)")

    if m.rsquared > 0.128:
        print(f"\n  RQ outperforms the architecture model by {m.rsquared - 0.128:.3f} R²")
    else:
        print(f"\n  RQ does NOT outperform the architecture model (ΔR²={m.rsquared - 0.128:+.3f})")

    print(f"\n  Career RQ by player (sorted):")
    for _, row in career.sort_values("career_rq").iterrows():
        print(f"    {row['player_name']:30s}: RQ={row['career_rq']:.3f} "
              f"(floor rate={row['po_floor_rate']:.1%}, n={row['n_po_games']})")


def produce_figures(df: pd.DataFrame) -> None:
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(16, 14))

    ax = axes[0, 0]
    for _, row in df.iterrows():
        color = config.GROUP_A_COLOR if row["player_name"] in config.GROUP_A else config.GROUP_B_COLOR
        alpha = 0.3 if row["is_floor"] else 0.6
        ax.scatter(row["rq"], row["game_score"], s=15, color=color, alpha=alpha)
    ax.set_xlabel("Resilience Quotient (RQ)")
    ax.set_ylabel("Game Score")
    ax.set_title("RQ vs Game Score (all PO games)\nRed=Group A, Blue=Group B, Faint=Floor games")
    ax.axhline(df["rs_p15_gs"].mean(), color="gray", linestyle=":", alpha=0.4)

    ax = axes[0, 1]
    career = df.groupby("player_name").agg(
        career_rq=("rq", "mean"),
        po_floor_rate=("is_floor", "mean"),
    ).reset_index()
    for _, row in career.iterrows():
        color = config.GROUP_A_COLOR if row["player_name"] in config.GROUP_A else config.GROUP_B_COLOR
        ax.scatter(row["career_rq"], row["po_floor_rate"], s=60,
                   color=color, alpha=0.7, edgecolors="black", linewidth=0.5)
        ax.annotate(row["player_name"].split()[-1], (row["career_rq"], row["po_floor_rate"]),
                    fontsize=6, alpha=0.8, xytext=(4, 4), textcoords="offset points")
    valid = career.dropna(subset=["career_rq", "po_floor_rate"])
    if len(valid) >= 5:
        r, p = stats.pearsonr(valid["career_rq"], valid["po_floor_rate"])
        ax.set_title(f"Career RQ → PO Floor Rate\nr={r:.3f}, p={p:.4f}")
    ax.set_xlabel("Career Mean RQ")
    ax.set_ylabel("PO Floor-Game Rate")
    ax.axhline(0.15, color="gray", linestyle=":", alpha=0.4)

    ax = axes[1, 0]
    floor = df[df["is_floor"] == 1]
    nonfloor = df[df["is_floor"] == 0]
    ax.hist(nonfloor["rq"], bins=50, alpha=0.6, color=config.GROUP_B_COLOR, label="Non-floor", density=True)
    ax.hist(floor["rq"], bins=30, alpha=0.6, color=config.GROUP_A_COLOR, label="Floor", density=True)
    ax.set_xlabel("RQ")
    ax.set_ylabel("Density")
    ax.set_title("RQ Distribution: Floor vs Non-Floor Games")
    ax.legend()
    ax.axvline(1.0, color="gray", linestyle=":", alpha=0.4, label="RQ=1.0 (no change)")

    ax = axes[1, 1]
    ps = df.groupby(["player_name", "season"]).agg(
        mean_rq=("rq", "mean"),
        rs_fta_fga_ratio=("rs_fta_fga_ratio", "first"),
    ).reset_index()
    valid_ps = ps.dropna(subset=["rs_fta_fga_ratio", "mean_rq"])
    if len(valid_ps) >= 5:
        r, p = stats.pearsonr(valid_ps["rs_fta_fga_ratio"], valid_ps["mean_rq"])
        for name in valid_ps["player_name"].unique():
            sub = valid_ps[valid_ps["player_name"] == name]
            color = config.GROUP_A_COLOR if name in config.GROUP_A else config.GROUP_B_COLOR
            ax.scatter(sub["rs_fta_fga_ratio"], sub["mean_rq"], s=20, color=color, alpha=0.6)
        ax.set_title(f"RS FTA Dependency → Mean RQ (per season)\nr={r:.3f}, p={p:.4f}")
    ax.set_xlabel("RS FTA/FGA Ratio (FTA Dependency)")
    ax.set_ylabel("Mean RQ (Season)")

    for ext in ("png", "svg"):
        fig.savefig(config.FIGURES_DIR / f"rq_multilevel_analysis.{ext}", dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote rq_multilevel_analysis")


def main() -> None:
    df = load_data()
    logger.info("Loaded %d games (%d PO)", len(df), df["is_playoff"].sum())

    rs_baselines = compute_rs_season_baselines(df)
    logger.info("RS baselines: %d player-seasons", len(rs_baselines))

    po_games = df[df["is_playoff"]].copy()
    game_df = compute_game_level_rq(po_games, rs_baselines)
    logger.info("Game-level RQ: %d observations", len(game_df))

    game_df.to_csv(config.PROCESSED_DIR / "rq_game_level.csv", index=False)
    logger.info("Wrote rq_game_level.csv")

    run_descriptive_stats(game_df)
    run_bivariate(game_df)
    model_results = run_multilevel_models(game_df)
    run_floor_game_model(game_df)
    run_rq_vs_floor_rate(game_df)
    produce_figures(game_df)

    print("\n" + "=" * 70)
    print("RQ MULTILEVEL MODEL — VERDICT")
    print("=" * 70)

    m3 = model_results.get("full")
    m1 = model_results.get("null")
    if m3 is not None and m1 is not None:
        r2_cond = 1 - m3.scale / m1.scale
        print(f"\n  Pseudo R² (full vs null): {r2_cond:.3f}")
        print(f"  Full model AIC: {m3.aic:.1f}" if not np.isnan(m3.aic) else f"  Full model AIC: N/A")
        print(f"  Null model AIC: {m1.aic:.1f}" if not np.isnan(m1.aic) else f"  Null model AIC: N/A")

        sig_effects = []
        for var in m3.params.index:
            if var == "Intercept" or var == "Group Var":
                continue
            pval = m3.pvalues.get(var, 1.0)
            if pval < 0.05:
                coef = m3.params[var]
                sig_effects.append(f"{var}: β={coef:+.4f}, p={pval:.4f}")

        if sig_effects:
            print(f"\n  Significant cross-level effects (p < 0.05):")
            for e in sig_effects:
                print(f"    {e}")
        else:
            print(f"\n  No significant cross-level effects at p < 0.05")

        if r2_cond >= 0.25:
            print(f"\n  PASS — RQ multilevel model clears R² > 0.25 bar")
            print(f"  The predictive framing works with RQ as DV instead of PO floor rate")
        elif r2_cond >= 0.15:
            print(f"\n  MARGINAL — RQ model shows some signal (R² = {r2_cond:.3f})")
            print(f"  Better than career-level architecture model (R²=0.128) but not decisive")
        else:
            print(f"\n  FAIL — RQ model does not clear R² > 0.15 bar")
            print(f"  Project contribution remains descriptive")

    logger.info("RQ multilevel model complete")


if __name__ == "__main__":
    main()
