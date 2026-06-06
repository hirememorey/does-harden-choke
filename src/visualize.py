"""Generate Pass 1 figures."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

sns.set_theme(style="whitegrid")


def save_fig(fig: plt.Figure, name: str) -> None:
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        path = config.FIGURES_DIR / f"{name}.{ext}"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        logger.info("Wrote %s", path)


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return np.nan, np.nan
    p = successes / n
    denom = 1 + z**2 / n
    centre = p + z**2 / (2 * n)
    margin = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return (centre - margin) / denom, (centre + margin) / denom


def plot_distribution(player: str, df: pd.DataFrame, baselines: pd.DataFrame) -> None:
    slug = config.player_slug(player)
    grp = df[df["player_name"] == player]
    if grp.empty:
        return
    bl = baselines[baselines["player_name"] == player].iloc[0]
    p15 = bl["rs_p15_gs"]
    color = config.GROUP_A_COLOR if config.PLAYER_GROUP.get(player) == "A" else config.GROUP_B_COLOR

    fig, ax = plt.subplots(figsize=(8, 5))
    rs = grp[~grp["is_playoff"]]["game_score"].dropna()
    po = grp[grp["is_playoff"]]["game_score"].dropna()
    if len(rs) > 5:
        sns.kdeplot(rs, ax=ax, color=config.RS_COLOR, label="Regular season", linewidth=2)
    if len(po) > 3:
        sns.kdeplot(po, ax=ax, color=color, label="Playoffs", linewidth=2)
    ax.axvline(p15, color="black", linestyle="--", label="RS 15th pct")
    ax.axvspan(ax.get_xlim()[0], p15, alpha=0.15, color="gray")
    ax.set_title(f"{player}: Game Score distribution")
    ax.set_xlabel("Game Score")
    ax.legend()
    save_fig(fig, f"dist_comparison_{slug}")
    plt.close(fig)


def plot_floor_rate_bars(screen_a: pd.DataFrame) -> None:
    df = screen_a.sort_values("floor_rate_increase", ascending=False).copy()
    x = np.arange(len(df))
    width = 0.35
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = [config.GROUP_A_COLOR if g == "A" else config.GROUP_B_COLOR for g in df["player_group"]]
    ax.bar(x - width / 2, df["rs_floor_rate"], width, label="RS", color=config.RS_COLOR)
    ax.bar(x + width / 2, df["po_floor_rate"], width, label="Playoffs", color=colors)
    ax.set_xticks(x)
    ax.set_xticklabels(df["player"], rotation=45, ha="right")
    for i, row in df.iterrows():
        if row["player"] == "James Harden":
            ax.annotate("*", (list(df["player"]).index(row["player"]), row["po_floor_rate"] + 0.02))
    ax.set_ylabel("Floor-game rate")
    ax.set_title("Floor-game rate: RS vs Playoffs")
    ax.legend()
    save_fig(fig, "floor_rate_comparison")
    plt.close(fig)


def plot_series_decay(analysis: pd.DataFrame) -> None:
    po = analysis[analysis["is_playoff"] & analysis["series_game_num"].notna()].copy()
    fig, ax = plt.subplots(figsize=(8, 5))

    def line_for(label: str, mask) -> None:
        sub = po[mask]
        xs, ys, yerr_lo, yerr_hi = [], [], [], []
        for g in range(1, 8):
            gsub = sub[sub["series_game_num"] == g]
            n = len(gsub)
            if n == 0:
                continue
            k = gsub["is_floor_primary"].sum()
            lo, hi = wilson_ci(int(k), n)
            xs.append(g)
            ys.append(k / n)
            yerr_lo.append(k / n - lo)
            yerr_hi.append(hi - k / n)
        if xs:
            ax.errorbar(xs, ys, yerr=[yerr_lo, yerr_hi], marker="o", label=label, capsize=3)

    line_for("James Harden", po["player_name"] == "James Harden")
    line_for("Group A", po["player_name"].isin(config.GROUP_A))
    line_for("Group B", po["player_name"].isin(config.GROUP_B))
    ax.set_xlabel("Series game number")
    ax.set_ylabel("Floor-game rate")
    ax.set_title("Floor-game rate by series game")
    ax.legend()
    save_fig(fig, "series_decay")
    plt.close(fig)


def plot_peer_scatter(screen_a: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 8))
    for _, row in screen_a.iterrows():
        color = config.GROUP_A_COLOR if row["player_group"] == "A" else config.GROUP_B_COLOR
        ax.scatter(row["mean_decline"], row["floor_rate_increase"], c=color, s=80)
        weight = "bold" if row["player"] == "James Harden" else "normal"
        ax.annotate(row["player"], (row["mean_decline"], row["floor_rate_increase"]), fontsize=8, fontweight=weight)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.axvline(0, color="gray", linewidth=0.8)
    ax.set_xlabel("Mean Game Score decline (RS − PO)")
    ax.set_ylabel("Floor-game rate increase (PO − RS)")
    ax.set_title("Peer scatter: mean shift vs tail fattening")
    save_fig(fig, "peer_scatter")
    plt.close(fig)


def plot_variance_decomposition(screen_a: pd.DataFrame) -> None:
    df = screen_a.sort_values("variance_shift_ratio", ascending=False)
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(df))
    ax.bar(x - 0.2, df["rs_mean_gs"], 0.4, label="RS mean GS", color=config.RS_COLOR)
    ax.bar(x + 0.2, df["po_mean_gs"], 0.4, label="PO mean GS", color="#aaaaaa")
    ax2 = ax.twinx()
    ax2.plot(x, df["po_floor_rate"] - df["rs_floor_rate"], "r-o", label="Floor rate Δ")
    ax.set_xticks(x)
    ax.set_xticklabels(df["player"], rotation=45, ha="right")
    ax.set_ylabel("Mean Game Score")
    ax2.set_ylabel("Floor rate increase")
    ax.set_title("Mean shift vs floor-rate increase")
    fig.legend(loc="upper right")
    save_fig(fig, "variance_decomposition")
    plt.close(fig)


def main() -> None:
    analysis_path = config.PROCESSED_DIR / "analysis_table.csv"
    screen_a_path = config.PROCESSED_DIR / "screen_a_results.csv"
    baselines_path = config.PROCESSED_DIR / "player_baselines.csv"

    if not analysis_path.exists():
        raise FileNotFoundError(f"Missing {analysis_path} — run features first")

    df = pd.read_csv(analysis_path)
    baselines = pd.read_csv(baselines_path) if baselines_path.exists() else pd.DataFrame()
    screen_a = pd.read_csv(screen_a_path) if screen_a_path.exists() else pd.DataFrame()

    for name in config.ALL_PLAYERS:
        plot_distribution(name, df, baselines)

    if not screen_a.empty:
        plot_floor_rate_bars(screen_a)
        plot_peer_scatter(screen_a)
        plot_variance_decomposition(screen_a)

    plot_series_decay(df)
    logger.info("Figures written to %s", config.FIGURES_DIR)


if __name__ == "__main__":
    main()
