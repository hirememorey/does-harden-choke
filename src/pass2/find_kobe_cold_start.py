"""Dynamic Search: Find a qualifying Cold Start game for Kobe Bryant and run spike analysis.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import config
from src.nba_client import create_client, normalize_game_id
from src.pass2.ingest_pbp import fetch_game_pbp
from src.pass2.possessions import build_and_save
from src.pass2.cold_start_spike import run_spike_analysis

def main():
    client = create_client()
    
    # Load Kobe's playoff games
    kobe_po_path = config.DATA_DIR / "raw" / "kobe_bryant_po.csv"
    if not kobe_po_path.exists():
        print("Error: Kobe playoff CSV not found.")
        return
        
    df_kobe = pd.read_csv(kobe_po_path)
    
    # Sort by worst shooting percentage / worst game scores (excluding injury games)
    bad_games = df_kobe[(df_kobe["min"] > 30) & (df_kobe["fga"] >= 12)].sort_values("fg_pct")
    
    print(f"Searching Kobe's {len(bad_games)} playoff games for a qualifying Q1-Q2 Cold Start...")
    
    found_games = 0
    for _, row in bad_games.iterrows():
        game_id = normalize_game_id(row["game_id"])
        
        # 1. Ingest PBP
        try:
            fetch_game_pbp(client, game_id)
        except Exception as e:
            # Skip if older game doesn't have PBP available
            continue
            
        # 2. Build possessions
        try:
            build_and_save(game_id)
        except Exception as e:
            continue
            
        # 3. Check for Cold Start
        poss_path = config.PROCESSED_PASS2_DIR / f"possessions_{game_id}.csv"
        df_poss = pd.read_csv(poss_path)
        df_poss["players_on_court"] = df_poss["players_on_court"].apply(
            lambda x: json.loads(x.replace("'", '"')) if isinstance(x, str) and x.startswith("[") else []
        )
        
        cumulative_fga = 0
        cumulative_fgm = 0
        event_idx = None
        
        for idx, r in df_poss.iterrows():
            if int(r["period"]) > 2:
                break
            if 977 not in r["players_on_court"]:
                continue
                
            if r["terminal_player_id"] == 977:
                if r["terminal_event_type"] == "fga_make":
                    cumulative_fga += 1
                    cumulative_fgm += 1
                elif r["terminal_event_type"] == "fga_miss":
                    cumulative_fga += 1
                    
            if cumulative_fga >= 5 and cumulative_fgm <= 1:
                event_idx = idx
                break
                
        if event_idx is not None:
            print(f"\n>>> SUCCESS! Found qualifying Cold Start game for Kobe Bryant: Game {game_id} vs {row['opponent']} on {row['game_date']}")
            print(f"    FG in first half: {row['fgm']}-for-{row['fga']}, Game Score: {row['game_score']:.1f}")
            run_spike_analysis(game_id, "Kobe Bryant", 977)
            found_games += 1
            if found_games >= 2:  # Find top 2
                break

if __name__ == "__main__":
    main()
