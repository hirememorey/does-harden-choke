"""Causal chain Step 2 — Descriptive analysis of mechanism → team outcomes.

Produces tables and figures for the causal chain. No regressions — that's Step 3.
Focus: what does the data look like before modeling?
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = config.PROCESSED_DIR
FIGURES_DIR = config.FIGURES_DIR


def save_fig(fig: plt.Figure, name: str) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        path = FIGURES_DIR / f"{name}.{ext}"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        logger.info("Wrote %s", path)


def validation_gates(floor: pd.DataFrame) -> None:
    """VG1/VG2: floor games have lower team ORtg and win rate than non-floor."""
    df = pd.read_csv(OUTPUT_DIR / "causal_analysis_table.csv")
    fl = df[df["is_floor_primary"] == True]
    nfl = df[df["is_floor_primary"] == False]

    ortg_fl = fl["team_off_rating"].mean()
    ortg_nfl = nfl["team_off_rating"].mean()
    win_fl = fl["team_win"].mean()
    win_nfl = nfl["team_win"].mean()

    print("=== Validation Gates (sanity checks, not findings) ===")
    print(f"  VG1 — Team ORtg: floor={ortg_fl:.1f}, non-floor={ortg_nfl:.1f}, Δ={ortg_fl - ortg_nfl:+.1f}")
    print(f"  VG2 — Win rate:  floor={win_fl:.3f}, non-floor={win_nfl:.3f}, Δ={win_fl - win_nfl:+.3f}")
    assert ortg_fl < ortg_nfl, "VG1 failed: floor games don't have lower team ORtg"
    assert win_fl < win_nfl, "VG2 failed: floor games don't have lower win rate"
    print("  Both passed. Do not present as findings.\n")


def per_player_floor_summary(floor: pd.DataFrame) -> pd.DataFrame:
    """2b. Per-player mechanism-conditional team ORtg in floor games."""
    rows = []
    for player, grp in floor.groupby("player_name"):
        n_floor = len(grp)
        mean_ortg = grp["team_off_rating"].mean()
        mean_fga_ret = grp["fga_retention"].mean()
        mean_gs = grp["game_score"].mean()
        win_rate = grp["team_win"].mean()
        mechanism = grp["mechanism"].dropna().iloc[0] if grp["mechanism"].notna().any() else "unknown"

        # Split by above/below-median fga_retention (within-player)
        if n_floor >= 15:
            med = grp["fga_retention"].median()
            high_ret = grp[grp["fga_retention"] >= med]
            low_ret = grp[grp["fga_retention"] < med]
            ortg_high = high_ret["team_off_rating"].mean() if len(high_ret) > 0 else np.nan
            ortg_low = low_ret["team_off_rating"].mean() if len(low_ret) > 0 else np.nan
        else:
            ortg_high = np.nan
            ortg_low = np.nan

        rows.append({
            "player_name": player,
            "mechanism": mechanism,
            "n_floor": n_floor,
            "mean_team_ortg": mean_ortg,
            "mean_fga_retention": mean_fga_ret,
            "mean_game_score": mean_gs,
            "win_rate": win_rate,
            "ortg_high_retention": ortg_high,
            "ortg_low_retention": ortg_low,
        })

    summary = pd.DataFrame(rows).sort_values("mean_team_ortg")
    summary.to_csv(OUTPUT_DIR / "mechanism_descriptives.csv", index=False)
    logger.info("Wrote mechanism_descriptives.csv (%d players)", len(summary))

    print("=== Per-Player Floor-Game Summary (sorted by team ORtg) ===")
    print(summary[["player_name", "mechanism", "n_floor", "mean_team_ortg", "mean_fga_retention", "win_rate"]].to_string(index=False))
    print()
    return summary


def mechanism_group_summary(floor: pd.DataFrame) -> None:
    """2b. Mechanism groups: contractor vs forcer vs mixed team ORtg."""
    grp = floor.groupby("mechanism").agg(
        n=("game_id", "count"),
        mean_ortg=("team_off_rating", "mean"),
        sem_ortg=("team_off_rating", lambda x: x.std() / np.sqrt(len(x))),
        mean_fga_ret=("fga_retention", "mean"),
        mean_gs=("game_score", "mean"),
        win_rate=("team_win", "mean"),
    ).sort_values("mean_ortg")

    print("=== Floor Games by Mechanism Group ===")
    print(grp.to_string())
    print()


def within_player_retention_split(floor: pd.DataFrame) -> None:
    """2b. Within-player: Harden, Durant, Curry floor-game ORtg by retention quartile."""
    for player in ["James Harden", "Kevin Durant", "Stephen Curry", "Russell Westbrook", "LeBron James"]:
        pf = floor[floor["player_name"] == player].copy()
        if len(pf) < 15:
            continue
        pf["ret_quartile"] = pd.qcut(pf["fga_retention"], 4, labels=["Q1(low)", "Q2", "Q3", "Q4(high)"])
        q = pf.groupby("ret_quartile", observed=True).agg(
            n=("game_id", "count"),
            mean_ortg=("team_off_rating", "mean"),
            mean_fga_ret=("fga_retention", "mean"),
            mean_gs=("game_score", "mean"),
            win_rate=("team_win", "mean"),
        )
        print(f"=== {player} — Floor Games by FGA Retention Quartile ===")
        print(q.to_string())
        print()


def scatter_fga_retention_vs_ortg(floor: pd.DataFrame) -> None:
    """Figure 1: Scatter of per-game fga_retention vs team_off_rating in floor games."""
    fig, ax = plt.subplots(figsize=(10, 7))

    highlight = {"James Harden": config.GROUP_A_COLOR, "Kevin Durant": config.GROUP_B_COLOR}
    other_color = "#aaaaaa"

    for player, grp in floor.groupby("player_name"):
        if player in highlight:
            color = highlight[player]
            ax.scatter(grp["fga_retention"], grp["team_off_rating"], alpha=0.6, s=30, color=color, label=player, zorder=3)
        else:
            ax.scatter(grp["fga_retention"], grp["team_off_rating"], alpha=0.15, s=12, color=other_color, zorder=1)

    # Overall regression line
    valid = floor.dropna(subset=["fga_retention", "team_off_rating"])
    z = np.polyfit(valid["fga_retention"], valid["team_off_rating"], 1)
    x_line = np.linspace(valid["fga_retention"].min(), valid["fga_retention"].max(), 100)
    ax.plot(x_line, np.polyval(z, x_line), color="black", linewidth=1.5, linestyle="--", alpha=0.7, label=f"OLS (slope={z[0]:.1f})")

    ax.axhline(110, color="green", linewidth=0.8, alpha=0.3, linestyle=":")
    ax.axvline(1.0, color="gray", linewidth=0.8, alpha=0.3, linestyle=":")
    ax.text(1.02, ax.get_ylim()[1] * 0.95, "Normal volume", fontsize=8, color="gray")

    ax.set_xlabel("FGA Retention (floor-game FGA/36 ÷ baseline FGA/36)")
    ax.set_ylabel("Team Offensive Rating")
    ax.set_title("Floor Games: FGA Retention vs Team ORtg\n(lower retention = more contraction)")
    ax.legend(loc="upper right")
    save_fig(fig, "causal_scatter_fga_retention_vs_ortg")
    plt.close(fig)


def bar_mechanism_team_ortg(floor: pd.DataFrame) -> None:
    """Figure 2: Bar chart of mean team ORtg by mechanism group with CI."""
    mechs = floor.groupby("mechanism").agg(
        n=("game_id", "count"),
        mean_ortg=("team_off_rating", "mean"),
        sem=("team_off_rating", lambda x: x.std() / np.sqrt(len(x))),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = {"shrinker": "#d62728", "forcer": "#1f77b4", "mixed": "#ff7f0e"}
    bar_colors = [colors.get(m, "#888888") for m in mechs["mechanism"]]

    bars = ax.bar(mechs["mechanism"], mechs["mean_ortg"], yerr=1.96 * mechs["sem"], color=bar_colors, capsize=5, alpha=0.85)
    for bar, n in zip(bars, mechs["n"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, f"n={n}", ha="center", fontsize=10)

    ax.set_ylabel("Mean Team ORtg")
    ax.set_title("Floor Games: Team ORtg by Failure Mechanism\n(with 95% CI)")
    ax.set_ylim(90, 115)
    save_fig(fig, "causal_bar_mechanism_ortg")
    plt.close(fig)


def harden_retention_quartile_bar(floor: pd.DataFrame) -> None:
    """Figure 3: Harden floor-game team ORtg by fga_retention quartile."""
    harden = floor[floor["player_name"] == "James Harden"].copy()
    if len(harden) < 15:
        return
    harden["ret_quartile"] = pd.qcut(harden["fga_retention"], 4, labels=["Q1\n(hardest\ncontraction)", "Q2", "Q3", "Q4\n(most\nforcing)"])
    q = harden.groupby("ret_quartile", observed=True).agg(
        mean_ortg=("team_off_rating", "mean"),
        sem=("team_off_rating", lambda x: x.std() / np.sqrt(len(x))),
        n=("game_id", "count"),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(q["ret_quartile"], q["mean_ortg"], yerr=1.96 * q["sem"], color=config.GROUP_A_COLOR, capsize=5, alpha=0.85)
    for bar, n in zip(bars, q["n"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, f"n={n}", ha="center", fontsize=10)

    ax.set_ylabel("Mean Team ORtg")
    ax.set_title("Harden Floor Games: Team ORtg by FGA Retention Quartile\n(controlling for game_score in regression)")
    ax.set_ylim(90, 115)
    save_fig(fig, "causal_harden_retention_quartile")
    plt.close(fig)


def matched_pairs(floor: pd.DataFrame) -> None:
    """2c. Harden vs Durant matched comparison on game_score and opponent quality."""
    full = pd.read_csv(OUTPUT_DIR / "causal_analysis_table.csv")
    harden_fl = floor[floor["player_name"] == "James Harden"].copy()
    durant_fl = floor[floor["player_name"] == "Kevin Durant"].copy()

    matches = []
    used_durant = set()
    for _, h in harden_fl.iterrows():
        candidates = durant_fl[~durant_fl.index.isin(used_durant)]
        if candidates.empty:
            break
        gs_diff = (candidates["game_score"] - h["game_score"]).abs()
        elim_match = (candidates["is_elimination"] == h["is_elimination"]).astype(int)
        score = gs_diff - elim_match * 2
        best_idx = score.idxmin()
        if gs_diff[best_idx] <= 3.0:
            d = candidates.loc[best_idx]
            used_durant.add(best_idx)
            matches.append({
                "harden_game_score": h["game_score"],
                "durant_game_score": d["game_score"],
                "harden_fga_retention": h["fga_retention"],
                "durant_fga_retention": d["fga_retention"],
                "harden_team_ortg": h["team_off_rating"],
                "durant_team_ortg": d["team_off_rating"],
                "harden_fga": h["fga"],
                "durant_fga": d["fga"],
                "harden_pts": h["pts"],
                "durant_pts": d["pts"],
                "harden_win": h["team_win"],
                "durant_win": d["team_win"],
                "gs_diff": gs_diff[best_idx],
            })

    if not matches:
        print("No matched pairs found.")
        return

    mf = pd.DataFrame(matches)
    mf.to_csv(OUTPUT_DIR / "matched_pairs_harden_durant.csv", index=False)

    print(f"=== Matched Pairs: Harden vs Durant Floor Games (game_score ±3) ===")
    print(f"  Pairs found: {len(mf)}")
    print(f"  Harden mean team ORtg: {mf['harden_team_ortg'].mean():.1f}")
    print(f"  Durant mean team ORtg: {mf['durant_team_ortg'].mean():.1f}")
    print(f"  Δ (Harden - Durant):    {mf['harden_team_ortg'].mean() - mf['durant_team_ortg'].mean():+.1f}")
    print(f"  Harden mean fga_ret:   {mf['harden_fga_retention'].mean():.3f}")
    print(f"  Durant mean fga_ret:   {mf['durant_fga_retention'].mean():.3f}")

    t, p = stats.ttest_rel(mf["harden_team_ortg"], mf["durant_team_ortg"])
    print(f"  Paired t-test: t={t:.2f}, p={p:.4f}")
    print()


def teammate_efficiency_proxy(floor: pd.DataFrame) -> None:
    """2d. Teammate efficiency under contraction vs forcing."""
    floor = floor.copy()
    floor["teammate_pts_proxy"] = floor["team_pts"] - floor["pts"]
    floor["teammate_poss_proxy"] = floor["team_poss"] - (floor["fga"] + floor["tov"] + 0.44 * floor["fta"]).clip(lower=0)
    floor["teammate_ortg_proxy"] = np.where(
        floor["teammate_poss_proxy"] > 0,
        100 * floor["teammate_pts_proxy"] / floor["teammate_poss_proxy"],
        np.nan,
    )

    low_ret = floor[floor["fga_retention"] < floor["fga_retention"].median()]
    high_ret = floor[floor["fga_retention"] >= floor["fga_retention"].median()]

    print("=== Teammate Efficiency Proxy (floor games only) ===")
    print(f"  Low retention (contraction):  teammate ORtg proxy = {low_ret['teammate_ortg_proxy'].mean():.1f} (n={len(low_ret)})")
    print(f"  High retention (forcing):      teammate ORtg proxy = {high_ret['teammate_ortg_proxy'].mean():.1f} (n={len(high_ret)})")
    print(f"  Δ: {low_ret['teammate_ortg_proxy'].mean() - high_ret['teammate_ortg_proxy'].mean():+.1f}")
    print(f"  (Rough proxy — team ORtg is not cleanly decomposable from box scores)")
    print()


def main() -> None:
    df = pd.read_csv(OUTPUT_DIR / "causal_analysis_table.csv")
    floor = df[df["is_floor_primary"] == True].dropna(subset=["fga_retention", "team_off_rating", "game_score"])
    logger.info("Loaded %d floor games for descriptive analysis", len(floor))

    print("\n" + "=" * 70)
    print("CAUSAL CHAIN STEP 2 — DESCRIPTIVE ANALYSIS")
    print("=" * 70 + "\n")

    validation_gates(floor)
    per_player_floor_summary(floor)
    mechanism_group_summary(floor)
    within_player_retention_split(floor)
    matched_pairs(floor)
    teammate_efficiency_proxy(floor)

    scatter_fga_retention_vs_ortg(floor)
    bar_mechanism_team_ortg(floor)
    harden_retention_quartile_bar(floor)

    print("=== Figures saved to output/figures/ ===")
    print("  causal_scatter_fga_retention_vs_ortg.png")
    print("  causal_bar_mechanism_ortg.png")
    print("  causal_harden_retention_quartile.png")


if __name__ == "__main__":
    main()
