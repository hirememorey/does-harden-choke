"""Spike Analysis: Cold-start response comparison for Harden vs Kobe.

Directly tests the 'shrinker' (contraction) vs 'forcer' (disengagement vs disefficiency)
hypotheses at the possession grain without needing the full cohorts pipeline.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import config


def run_spike_analysis(game_id: str, player_name: str, player_id: int):
    path = config.PROCESSED_PASS2_DIR / f"possessions_{game_id}.csv"
    if not path.exists():
        print(f"Error: Possessions file not found for game {game_id}")
        return

    df = pd.read_csv(path)
    df["players_on_court"] = df["players_on_court"].apply(
        lambda x: json.loads(x.replace("'", '"')) if isinstance(x, str) and x.startswith("[") else []
    )

    # Track sequential player stats to find the Cold Start event
    cumulative_fga = 0
    cumulative_fgm = 0
    event_idx = None

    for idx, row in df.iterrows():
        # Only evaluate first half (Q1, Q2)
        if int(row["period"]) > 2:
            break

        # Check if player was active / on the court
        on_court = (player_id in row["players_on_court"]) or (row["terminal_player_id"] == player_id) or (row["assist_player_id"] == player_id)
        if not on_court:
            continue

        # Update stats
        terminal_pid = row["terminal_player_id"]
        event_type = row["terminal_event_type"]

        if terminal_pid == player_id:
            if event_type == "fga_make":
                cumulative_fga += 1
                cumulative_fgm += 1
            elif event_type == "fga_miss":
                cumulative_fga += 1

        # Check Event A (Cold Start) threshold: >= 5 FGA and <= 1 FGM
        if cumulative_fga >= 5 and cumulative_fgm <= 1:
            event_idx = idx
            break

    if event_idx is None:
        print(f"No Cold Start event triggered for {player_name} in game {game_id}.")
        return

    print(f"\n==================================================")
    print(f"COLD START EVENT TRIGGERED FOR {player_name} ({game_id})")
    print(f"  Triggered at possession: {event_idx} (Q{df.loc[event_idx, 'period']} {df.loc[event_idx, 'start_clock']})")
    print(f"  Cumulative stats at trigger: {cumulative_fgm}-for-{cumulative_fga} FG")

    # 1. Baseline Pool: Pre-event possessions with player active
    baseline_poss = df.iloc[:event_idx]
    baseline_active = baseline_poss[baseline_poss.apply(lambda r: (player_id in r["players_on_court"]) or (r["terminal_player_id"] == player_id) or (r["assist_player_id"] == player_id), axis=1)]

    # 2. Response Window: Next 8 active possessions with player active, excluding garbage time
    response_active_rows = []
    for idx, row in df.iloc[event_idx + 1 :].iterrows():
        if len(response_active_rows) >= 8:
            break
        # Exclude garbage time
        if row["is_garbage_time"]:
            continue
        # Player must be active
        if (player_id in row["players_on_court"]) or (row["terminal_player_id"] == player_id) or (row["assist_player_id"] == player_id):
            response_active_rows.append(row)

    response_active = pd.DataFrame(response_active_rows)

    print(f"  Baseline possessions (pre-event, on-court): {len(baseline_active)}")
    print(f"  Response possessions (post-event, on-court): {len(response_active)}")

    # Compute metrics
    def compute_metrics(subs_df: pd.DataFrame, label: str) -> dict:
        if len(subs_df) == 0:
            return {}
        # Find player team
        team_row = subs_df.iloc[0]
        # In possessions table, we have offensive_team.
        # But we want to measure player metrics relative to player's team possessions
        player_team = "LAL" if "kobe" in player_name.lower() else ("HOU" if "00416" in game_id else "PHI")
        if game_id == "0042200217":
            player_team = "PHI"
        
        team_poss = subs_df[subs_df["offensive_team"] == player_team]
        player_terminations = subs_df[subs_df["terminal_player_id"] == player_id]

        fga = len(player_terminations[player_terminations["terminal_event_type"].isin(["fga_make", "fga_miss"])])
        ast = len(player_terminations[player_terminations["terminal_event_type"] == "ast"])  # wait, assists are in col assist_player_id
        # Let's count assists where player is assist_player_id
        ast = len(subs_df[subs_df["assist_player_id"] == player_id])
        tov = len(player_terminations[player_terminations["terminal_event_type"] == "tov"])
        ft_trips = len(player_terminations[player_terminations["terminal_event_type"] == "ft_trip"])

        # Approximated Usage Events = FGA + 0.44*FTA(trips) + TOV
        usage_events = fga + ft_trips + tov
        team_poss_count = max(1, len(team_poss))

        return {
            "poss_count": len(subs_df),
            "team_poss_count": team_poss_count,
            "usage_rate": usage_events / team_poss_count,
            "shot_rate": fga / team_poss_count,
            "assist_rate": ast / team_poss_count,
            "turnover_rate": tov / team_poss_count,
            "fga": fga,
            "ast": ast,
            "tov": tov,
            "ft_trips": ft_trips,
        }

    b_m = compute_metrics(baseline_active, "Baseline")
    r_m = compute_metrics(response_active, "Response")

    if not b_m or not r_m:
        print("Error: Underpowered sample for metrics.")
        return

    # Print Comparison Table
    print(f"\n  Metric               | Baseline  | Response  | Delta (Response - Baseline)")
    print(f"  ---------------------|-----------|-----------|----------------------------")
    for m_key, m_name in [
        ("usage_rate", "Usage Approximate   "),
        ("shot_rate", "Shots / Team Poss   "),
        ("assist_rate", "Assists / Team Poss "),
        ("turnover_rate", "Turnovers / Team Pos"),
    ]:
        b_val = b_m[m_key]
        r_val = r_m[m_key]
        delta = r_val - b_val
        print(f"  {m_name} | {b_val:9.3f} | {r_val:9.3f} | {delta:+11.3f}")

    print(f"\n  Raw Counts in Window:")
    print(f"    Baseline:  FGA={b_m['fga']}, AST={b_m['ast']}, TOV={b_m['tov']}, FT_Trips={b_m['ft_trips']}")
    print(f"    Response:  FGA={r_m['fga']}, AST={r_m['ast']}, TOV={r_m['tov']}, FT_Trips={r_m['ft_trips']}")


if __name__ == "__main__":
    # James Harden 2023 Game 7 (started cold vs Boston)
    run_spike_analysis("0042200217", "James Harden", 201935)
    
    # Kobe Bryant 2009 Game 3 vs Utah (started cold, forced)
    run_spike_analysis("0040800143", "Kobe Bryant", 977)
    
    # Kobe Bryant 2001 Game 1 vs Philadelphia (started cold, redistributed)
    run_spike_analysis("0040000083", "Kobe Bryant", 977)
    
    # James Harden 2017 Game 6 (iconic collapse vs SAS - disengaged, didn't shoot enough)
    run_spike_analysis("0041600236", "James Harden", 201935)
    run_spike_analysis("0041600236", "James Harden", 201935)
