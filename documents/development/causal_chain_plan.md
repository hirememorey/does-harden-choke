# Causal Chain Plan — Contraction → Team ORtg → Wins

**Date:** June 2026  
**Status:** Step 0 **complete**; Steps 1–4 **not started**  
**Blocks:** The practical claim that failure mode predicts team outcomes (`open_questions.md` §A)

---

## Research question

Does a star's **contraction** in floor games causally hurt their team — lower offensive rating and lower win probability — relative to the same player's non-floor games and relative to **forcers** who preserve volume?

Pass 1 established *that* players contract differently. This extension tests whether contraction *matters* for team success at the game level.

### Hypotheses

| ID | Claim | Test |
|----|-------|------|
| **CC1** | Floor games have lower team ORtg than the same player's non-floor games | Within-player paired comparison; regression with player FE |
| **CC2** | Floor games have lower win rate than non-floor games | Logistic `win ~ is_floor + controls` |
| **CC3** | Contraction mechanism amplifies CC1/CC2 | Interaction: floor × low FGA retention (Screen E / retention baselines) |
| **CC4** | Effect persists after score-margin control | Add `plus_minus`, `opponent_defrtg`, `is_playoff`, `minutes` |

**Falsification:** If floor games show no team ORtg or win-rate penalty after controls, the taxonomy is descriptive only — not actionable for scouting.

---

## Prerequisites

Before starting Step 1, regenerate locally:

```bash
make venv
make scrape              # player logs — if not already present
make validate-scrape
make features            # → analysis_table.csv
make scrape-team-logs    # ~50 min full cohort; uses --resume
make validate-team-logs  # must exit 0
```

Step 0 validation gates (June 2026 run):

| Gate | Criterion | Result |
|------|-----------|--------|
| League ORtg sanity | Recent-season mean ORtg 108–118 | **PASS** (2022–25: 114.7–116.4) |
| Join coverage | ≥95% player `(game_id, team_id)` in team logs | **PASS** (100% on 17,024 rows) |
| ORtg reconstruction | API `off_rating` vs `100×pts/poss` within ±1.0 on ≥90% | **PASS** (100%, mean \|delta\| = 0.02) |

---

## Step 0 — Team game logs (DONE)

**Goal:** Attach team-level `OFF_RATING`, `POSS`, `WL`, and box score to every player-game row in the cohort.

### Scripts

| Script | Output | Notes |
|--------|--------|-------|
| `src/scrape_team_logs.py` | `data/raw/team_game_logs.csv` | 372 team-season keys from player CSVs; Base + Advanced merge |
| `src/validate_team_logs.py` | stdout gates | Run after every scrape |

### Makefile

```bash
make scrape-team-logs      # --resume: checkpoint every 10 keys, skip completed
make validate-team-logs
make smoke-team-logs       # 5 team-seasons in 2023-24 only (dev)
```

### Implementation notes

1. **Keys:** `collect_team_season_keys()` dedupes `(team_id, season, is_playoff)` from all `{player_slug}_rs.csv` and `_po.csv` under `data/raw/`.
2. **API:** `nba_client.get_team_game_logs(team_id, season, season_type, measure_type)` — `measure_type` added June 2026 (was hardcoded `"Base"`).
3. **game_id normalization:** Both player and team logs use `normalize_game_id()` (10-digit zero-padded, e.g. `20900012` → `0020900012`). **Required** for join — without it, join coverage was ~2%.
4. **Resume:** `--resume` reads existing CSV, skips completed keys, checkpoints every 10 fetches (~50 min full run).
5. **Scale:** ~19,700 team-game rows, ~16,900 unique games for the 18-player cohort.

### Key columns in `team_game_logs.csv`

| Column | Source | Use in causal chain |
|--------|--------|---------------------|
| `game_id`, `team_id` | API | Join keys |
| `off_rating` | Advanced | **Primary outcome (CC1)** |
| `def_rating` | Advanced | Opponent context / sensitivity |
| `poss` | Advanced | ORtg validation; pace control |
| `pts`, `fga`, `fgm`, `oreb`, `tov`, `fta` | Base | Formula ORtg fallback |
| `wl` | Base | **Win indicator (CC2)** |
| `plus_minus` | Base | Score-margin proxy (CC4) |
| `season`, `is_playoff` | derived | Fixed effects |
| `opponent`, `matchup` | parsed | Audit |

---

## Step 1 — Join player floor flags to team outcomes (NEXT)

**Goal:** One analysis-ready table: player floor flag + team ORtg + win per game.

### Proposed script

`src/join_causal_table.py` (not yet written)

### Logic

```python
# Pseudocode
players = pd.read_csv("data/processed/analysis_table.csv")
teams = pd.read_csv("data/raw/team_game_logs.csv")

players["game_id"] = players["game_id"].apply(normalize_game_id)
teams["game_id"] = teams["game_id"].apply(normalize_game_id)

merged = players.merge(
    teams,
    on=["game_id", "team_id"],
    how="inner",
    suffixes=("", "_team"),
)

# Attach mechanism labels from screen_e_results.csv (optional left join on player)
merged.to_csv("data/processed/causal_analysis_table.csv")
```

### Join keys

- `(game_id, team_id)` — player row is always from the team they played for that game.
- Expect **~17,000 rows** (same as join validation count); inner join drops player-games missing team logs (should be 0 after Step 0).

### Columns to carry forward

From `analysis_table.csv`: `player_name`, `is_floor_primary`, `game_score`, `minutes`, `is_playoff`, `opponent_defrtg`, `series_game_num`, `is_elimination`, `plus_minus` (player).

From `team_game_logs.csv`: `off_rating`, `def_rating`, `poss`, `wl`, `pts` (team).

Derived:
- `team_win` = `wl == "W"`
- `player_floor` = `is_floor_primary`

### Validation gate (Step 1)

| Check | Pass criterion |
|-------|----------------|
| Row count | ≥99% of `analysis_table` rows with valid `team_id` |
| No duplicate keys | One row per `(game_id, player_name)` |
| ORtg non-null | ≥95% `off_rating` populated |
| Spot check | Harden 2017 G6: floor game, team ORtg and WL match basketball-reference / memory |

### Makefile target (to add)

```makefile
join-causal:
	$(PYTHON) src/join_causal_table.py
```

---

## Step 2 — Descriptive causal comparisons

**Goal:** Answer CC1 and CC2 descriptively before regression.

### Proposed script

`src/causal_chain_screen.py` (not yet written)

### Analyses

1. **Within-player floor vs non-floor**
   - Per player: mean `off_rating` | floor vs non-floor; mean `team_win` rate
   - Paired structure: same player, different game types

2. **Mechanism split**
   - Merge `screen_e_results.csv` `mechanism` (shrinker/forcer/mixed)
   - Or use continuous `vol_share` / FGA retention from `retention_baselines.csv`
   - Compare floor-game team ORtg penalty: contractors vs forcers

3. **Harden vs Durant contrast**
   - Lead case: Harden floor games → team ORtg delta vs Durant floor games

### Output

`data/processed/causal_chain_results.csv` — per-player floor vs non-floor team ORtg and win rate.

---

## Step 3 — Regression with controls (CC4)

**Goal:** Estimate floor-game penalty net of game context.

### Model sketches

**Team ORtg (CC1):**
```
off_rating ~ is_floor_primary + plus_minus + opponent_defrtg + is_playoff
             + C(player_name) + C(season)
```
Cluster SE at player level. Alternative: within-player demeaned specification.

**Win probability (CC2):**
```
team_win ~ is_floor_primary + plus_minus + opponent_defrtg + is_playoff
           + C(player_name) + C(season)
```

**Mechanism interaction (CC3):**
```
off_rating ~ is_floor * contractor_indicator + controls + FE
```
Where `contractor_indicator` comes from Screen E (`vol_share > 0.55`) or low FGA retention.

### Confounds acknowledged

| Confound | Mitigation |
|----------|------------|
| Blowouts | `plus_minus`; sensitivity: exclude \|PM\| > 15 |
| Coach benches star in floor games | Minutes drop conflates player + coach; Pass 2 decontamination later |
| Opponent quality | `opponent_defrtg` (season-level; coarse) |
| Playoff intensity | `is_playoff` FE |
| Star not playing whole game | Control `minutes`; sensitivity: `minutes >= 25` |

---

## Step 4 — Report and bridge to paper

1. Update `findings.md` with causal chain section.
2. Add figure: floor vs non-floor team ORtg by mechanism class.
3. One paragraph: "Screen E showed contraction; causal chain [does/does not] show it costs wins."

---

## Implementation sequence

| Step | Module | Depends on | Status |
|------|--------|------------|--------|
| 0 | `scrape_team_logs.py`, `validate_team_logs.py` | Player raw CSVs | **Done** |
| 1 | `join_causal_table.py` | Step 0 + `analysis_table.csv` | **Next** |
| 2 | `causal_chain_screen.py` | Step 1 + `screen_e_results.csv` | Pending |
| 3 | `causal_chain_models.py` (or notebook) | Step 1 | Pending |
| 4 | `findings.md` update | Steps 2–3 | Pending |

**No step may skip validation gates.** Step 0 gate is `make validate-team-logs` exit 0.

---

## File index

| Path | Role |
|------|------|
| `documents/development/causal_chain_plan.md` | This document |
| `src/scrape_team_logs.py` | Step 0 fetch |
| `src/validate_team_logs.py` | Step 0 validation |
| `src/join_causal_table.py` | Step 1 (to write) |
| `src/causal_chain_screen.py` | Step 2 (to write) |
| `data/raw/team_game_logs.csv` | Step 0 output (gitignored) |
| `data/processed/analysis_table.csv` | Player games + floor flags |
| `data/processed/causal_analysis_table.csv` | Step 1 output (to write) |
| `data/processed/screen_e_results.csv` | Mechanism labels for CC3 |

---

## Decision log

| Date | Decision |
|------|----------|
| Jun 2026 | Causal chain prioritized over Pass 2 at scale |
| Jun 2026 | Step 0: team `teamgamelogs` API (Base + Advanced), not box-score reconstruction alone |
| Jun 2026 | `game_id` must be normalized to 10 digits before any player↔team join |
| Jun 2026 | Step 0 complete — 19,717 rows, 100% join coverage, validation OK |
