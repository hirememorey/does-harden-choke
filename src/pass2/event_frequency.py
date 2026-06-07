"""Event frequency estimator for Pass 2 adversity events.

Computes how often Event A (Cold Start: 1-for-5 or worse in Q1-Q2) fires
for star players across their playoff careers. Uses PBP data where available,
and a game-level box-score proxy for the full sample.

Output: Estimated event counts per player, projected total across cohort.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

STAR_PLAYER_IDS = {
    v["nba_id"]: name for name, v in config.ALL_PLAYERS.items()
}


def detect_cold_starts_in_game(possessions: pd.DataFrame, player_id: int) -> list[dict]:
    cumulative_fga = 0
    cumulative_fgm = 0
    events = []

    for idx, row in possessions.iterrows():
        if int(row["period"]) > 2:
            break
        if row["is_garbage_time"]:
            continue

        on_court = (
            player_id in _parse_players(row.get("players_on_court", "[]"))
            or row.get("terminal_player_id") == player_id
            or row.get("assist_player_id") == player_id
        )
        if not on_court:
            continue

        terminal_pid = row.get("terminal_player_id")
        event_type = row.get("terminal_event_type", "")

        if terminal_pid == player_id:
            if event_type == "fga_make":
                cumulative_fga += 1
                cumulative_fgm += 1
            elif event_type == "fga_miss":
                cumulative_fga += 1

        if cumulative_fga >= 5 and cumulative_fgm <= 1:
            events.append({
                "possession_idx": idx,
                "period": int(row["period"]),
                "clock": row.get("start_clock", ""),
                "cumulative_fgm": cumulative_fgm,
                "cumulative_fga": cumulative_fga,
            })
            break

    return events


def _parse_players(val) -> list[int]:
    if isinstance(val, list):
        return val
    if isinstance(val, str) and val.startswith("["):
        try:
            return json.loads(val.replace("'", '"'))
        except (json.JSONDecodeError, ValueError):
            return []
    return []


def scan_pbp_games(p2_dir: Path | None = None) -> pd.DataFrame:
    p2_dir = p2_dir or config.PROCESSED_PASS2_DIR
    rows = []

    for csv_file in sorted(p2_dir.glob("possessions_*.csv")):
        gid = csv_file.stem.replace("possessions_", "")
        df = pd.read_csv(csv_file)
        df["players_on_court"] = df["players_on_court"].apply(_parse_players)

        q12 = df[df["period"].isin([1, 2])]
        fga_events = q12[q12["terminal_event_type"].isin(["fga_make", "fga_miss"])]
        player_ids_in_game = set(fga_events["terminal_player_id"].dropna().astype(int))

        for pid in player_ids_in_game:
            name = STAR_PLAYER_IDS.get(pid, f"player_{pid}")
            is_star = pid in STAR_PLAYER_IDS

            events = detect_cold_starts_in_game(df, pid)

            fga_in_q12 = len(fga_events[fga_events["terminal_player_id"] == pid])
            fg_made = len(fga_events[(fga_events["terminal_player_id"] == pid) & (fga_events["terminal_event_type"] == "fga_make")])

            rows.append({
                "game_id": gid,
                "player_id": pid,
                "player_name": name,
                "is_star": is_star,
                "q12_fga": fga_in_q12,
                "q12_fgm": fg_made,
                "event_a_fired": len(events) > 0,
                "event_count": len(events),
            })

    return pd.DataFrame(rows)


def box_score_cold_start_proxy(po_dir: Path | None = None) -> pd.DataFrame:
    po_dir = po_dir or config.RAW_DIR
    rows = []

    for name, info in config.ALL_PLAYERS.items():
        slug = config.player_slug(name)
        po_path = po_dir / f"{slug}_po.csv"
        if not po_path.exists():
            logger.warning("No playoff CSV for %s", name)
            continue

        df = pd.read_csv(po_path, low_memory=False)
        if df.empty:
            continue

        n_games = len(df)
        n_high_fga_low_pct = len(df[(df["fga"] >= 10) & (df["fg_pct"] <= 0.25)])
        n_very_cold = len(df[(df["fga"] >= 8) & (df["fg_pct"] <= 0.20)])
        n_catastrophic = len(df[(df["fga"] >= 6) & (df["fg_pct"] <= 0.167)])

        rows.append({
            "player": name,
            "player_group": config.PLAYER_GROUP.get(name, ""),
            "nba_id": info["nba_id"],
            "po_games": n_games,
            "high_fga_low_pct_games": n_high_fga_low_pct,
            "high_fga_low_pct_rate": n_high_fga_low_pct / n_games if n_games else 0,
            "very_cold_games": n_very_cold,
            "very_cold_rate": n_very_cold / n_games if n_games else 0,
            "catastrophic_games": n_catastrophic,
            "catastrophic_rate": n_catastrophic / n_games if n_games else 0,
        })

    return pd.DataFrame(rows)


def estimate_event_counts(proxy_df: pd.DataFrame, pbp_rate: float) -> pd.DataFrame:
    proxy_df = proxy_df.copy()

    proxy_df["estimated_event_a_rate"] = pbp_rate
    proxy_df["estimated_event_a_count"] = (proxy_df["po_games"] * pbp_rate).round(0).astype(int)

    proxy_df["very_cold_adjusted_rate"] = proxy_df["very_cold_rate"] * 0.75
    proxy_df["very_cold_adjusted_count"] = (proxy_df["po_games"] * proxy_df["very_cold_adjusted_rate"]).round(0).astype(int)

    proxy_df["best_estimate_rate"] = proxy_df[["estimated_event_a_rate", "very_cold_adjusted_rate"]].mean(axis=1)
    proxy_df["best_estimate_count"] = (proxy_df["po_games"] * proxy_df["best_estimate_rate"]).round(0).astype(int)

    return proxy_df


def main() -> None:
    print("=" * 70)
    print("EVENT FREQUENCY ESTIMATOR — Pass 2 Cold Start Events")
    print("=" * 70)

    # Phase 1: PBP-based event detection on available games
    print("\n--- Phase 1: PBP-based Cold Start Detection ---\n")
    pbp_results = scan_pbp_games()

    pbp_cold_start_rate = 0.15

    if not pbp_results.empty:
        total_games = pbp_results["game_id"].nunique()
        total_player_games = len(pbp_results)
        cold_starts = pbp_results[pbp_results["event_a_fired"]]
        rate_overall = len(cold_starts) / total_player_games if total_player_games else 0

        print(f"Scanned {total_games} games, {total_player_games} player-games with Q1-Q2 FGA")
        print(f"Event A (Cold Start) fired: {len(cold_starts)} / {total_player_games} = {rate_overall:.1%}\n")

        star_results = pbp_results[pbp_results["is_star"]]
        if not star_results.empty:
            print("Star players in PBP sample:")
            for _, row in star_results.iterrows():
                print(f"  {row['player_name']}: {row['q12_fgm']}-for-{row['q12_fga']} in Q1-Q2, Event A = {row['event_a_fired']}")

        all_high_usage = pbp_results[pbp_results["q12_fga"] >= 5]
        high_usage_rate = all_high_usage["event_a_fired"].mean() if len(all_high_usage) > 0 else 0
        n_eligible = len(all_high_usage)

        print(f"\nPlayers with Q1-Q2 FGA >= 5 (Event A eligible): {n_eligible}")
        print(f"  Event A rate among eligible: {high_usage_rate:.1%}")

        if high_usage_rate > 0:
            pbp_cold_start_rate = high_usage_rate
    else:
        print("No PBP possession files found. Using default rate estimate.")

    # Phase 2: Box-score proxy
    print("\n--- Phase 2: Game-Level Box Score Proxy ---\n")
    proxy_df = box_score_cold_start_proxy()

    print("Game-level cold-start proxies (full playoff sample):\n")
    print(f"{'Player':<22} {'Group':<4} {'PO G':>5} {'Cold10/25%':>10} {'VeryCold8/20%':>14} {'Cata6/17%':>10}")
    print("-" * 70)
    for _, row in proxy_df.sort_values("very_cold_rate", ascending=False).iterrows():
        print(f"{row['player']:<22} {row['player_group']:<4} {row['po_games']:>5} "
              f"{row['high_fga_low_pct_games']:>3} ({row['high_fga_low_pct_rate']:.0%})    "
              f"{row['very_cold_games']:>3} ({row['very_cold_rate']:.0%})       "
              f"{row['catastrophic_games']:>3} ({row['catastrophic_rate']:.0%})")

    # Phase 3: Projected event counts
    print("\n--- Phase 3: Projected Event A Counts ---\n")

    eligible_fraction = 0.70
    effective_rate = pbp_cold_start_rate * eligible_fraction

    print(f"Assumptions:")
    print(f"  PBP cold-start rate (among Q1-Q2 FGA >= 5): {pbp_cold_start_rate:.1%}")
    print(f"  Fraction of star playoff games with Q1-Q2 FGA >= 5: ~{eligible_fraction:.0%}")
    print(f"  Effective Event A rate per playoff game: {effective_rate:.1%}")
    print()

    estimates = estimate_event_counts(proxy_df, effective_rate)

    print(f"{'Player':<22} {'Group':<4} {'PO G':>5} {'Est. Events':>11} {'Box-Score Adj':>14}")
    print("-" * 60)
    total_est = 0
    total_box = 0
    for _, row in estimates.sort_values("best_estimate_count", ascending=False).iterrows():
        print(f"{row['player']:<22} {row['player_group']:<4} {row['po_games']:>5} "
              f"{row['estimated_event_a_count']:>7}      "
              f"{row['best_estimate_count']:>7}")
        total_est += row["estimated_event_a_count"]
        total_box += row["best_estimate_count"]

    print("-" * 60)
    print(f"{'TOTAL':<22} {'':4} {estimates['po_games'].sum():>5} {total_est:>7}      {total_box:>7}")

    # Event B estimate
    print("\n--- Event B (Consecutive Empty Trips) Estimate ---\n")
    event_b_rate_approx = effective_rate * 0.6
    print(f"Event B is more common than Event A (any quarter, not just Q1-Q2).")
    print(f"Estimated Event B rate: ~{event_b_rate_approx:.1%} (1.5x Event A rate)")
    event_b_total = int(estimates["po_games"].sum() * event_b_rate_approx)
    print(f"Estimated total Event B events across cohort: ~{event_b_total}")
    print(f"Combined Events A + B: ~{total_box + event_b_total}")

    # Power assessment
    print("\n--- Statistical Power Assessment ---\n")
    for _, row in estimates.iterrows():
        n = row["best_estimate_count"]
        if n >= 20:
            verdict = "WELL-POWERED (within-player profiles + cross-player comparison)"
        elif n >= 10:
            verdict = "ADEQUATE (within-player profiles possible, noisy cross-player)"
        elif n >= 5:
            verdict = "MARGINAL (pooled analysis only)"
        else:
            verdict = "UNDERPOWERED (need to combine event types or expand sample)"
        print(f"  {row['player']:<22} ~{n:>3} events  {verdict}")

    estimates.to_csv(config.PROCESSED_DIR / "event_frequency_estimates.csv", index=False)
    print(f"\nSaved to {config.PROCESSED_DIR / 'event_frequency_estimates.csv'}")


if __name__ == "__main__":
    main()
