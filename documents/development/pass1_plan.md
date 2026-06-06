# Does Harden Choke?

## Research Question

**Is James Harden's playoff problem better described as a repeated-opponent increase in downside variance — especially floor-game frequency late in series — than as a uniform decline in average performance?**

This generalizes beyond Harden to a broader question: do heliocentric offensive engines experience a playoff-specific increase in catastrophic game frequency that cannot be explained by opponent quality alone?

---

## Hypothesis Structure

### H1 (load-bearing): Variance shift, not mean shift

Playoff floor-game frequency increases more than average performance declines for heliocentric creators. The distribution doesn't just shift left — its left tail gets fatter.

### H2 (dependent on H1): Within-series adaptation

The floor-game effect compounds as a series goes on and opponents accumulate tape. Games 5-7 should show materially higher floor-game rates than games 1-2.

### Falsification criterion

If floor-game rate in playoffs is statistically indistinguishable from regular season after adjusting for opponent quality, the line is dead.

---

## Pass 1: 48-Hour Feasibility Test

**Goal:** Answer three yes/no questions with public data.

1. Is there a clear floor-game signal for Harden in the playoffs?
2. Does it grow in later series games?
3. Is Harden an outlier versus peers?

If no to #1, stop. If yes to #1 but no to #2, still a paper — just about playoff conditions, not adaptation. If yes to both, proceed to Pass 2.

---

## Implementation Plan (Pass 1 Only)

### Phase 0: Project Scaffolding

**Directory structure:**

```
does-harden-choke/
├── documents/development/pass1_plan.md   # this document
├── Makefile                 # pipeline orchestration
├── requirements.txt         # dependencies
├── .gitignore               # exclude data/, __pycache__, .env
├── config.py                # player lists, IDs, parameters
├── data/
│   ├── raw/                 # scraped game logs
│   └── processed/           # derived analysis tables
├── src/
│   ├── __init__.py
│   ├── nba_client.py        # HTTP client (adapted from resilience-basketball)
│   ├── scrape.py            # data collection
│   ├── features.py          # compute residuals, floor-game flags
│   ├── screen_a.py          # variance shift test
│   ├── screen_b.py          # within-series gradient test
│   ├── screen_c.py          # peer comparison
│   └── visualize.py         # distribution plots, series decay charts
├── notebooks/
│   └── exploration.ipynb
└── output/
    └── figures/
```

**`requirements.txt`:**

```
pandas>=1.3.0
requests>=2.26.0
numpy>=1.21.0
scipy>=1.7.0
statsmodels>=0.14.0
matplotlib>=3.4.0
seaborn>=0.11.0
tqdm>=4.60.0
tenacity>=8.0.0
lxml>=4.6.0
beautifulsoup4>=4.9.0
basketball-reference-scraper>=2.0.0
```

**`.gitignore`:**

```
data/raw/
data/processed/
data/cache/
output/
__pycache__/
*.pyc
.env
*.db
```

**`config.py` — Player lists and parameters:**

```python
# Group A — Heliocentric creators (high usage, high self-creation, foul-dependent)
GROUP_A = {
    "James Harden":      {"nba_id": 201935,  "bbref_id": "hardeja01"},
    "Russell Westbrook": {"nba_id": 201566,  "bbref_id": "westbru01"},
    "Luka Doncic":       {"nba_id": 1629029, "bbref_id": "doncilu01"},
    "Trae Young":        {"nba_id": 1629027, "bbref_id": "younga01"},
    "Allen Iverson":     {"nba_id": 947,     "bbref_id": "iversal01"},
    "Kyrie Irving":      {"nba_id": 203999,  "bbref_id": "irvinky01"},
}

# Group B — Scalable stars (lower self-creation burden, more off-ball)
GROUP_B = {
    "Stephen Curry":     {"nba_id": 201939,  "bbref_id": "curryst01"},
    "Klay Thompson":     {"nba_id": 203110,  "bbref_id": "thompkl01"},
    "Ray Allen":         {"nba_id": 953,     "bbref_id": "allenra02"},
    "Richard Hamilton":  {"nba_id": 977,     "bbref_id": "hamilri01"},
    "Khris Middleton":   {"nba_id": 203496,  "bbref_id": "middlkh01"},
}

ALL_PLAYERS = {**GROUP_A, **GROUP_B}

# Analysis parameters
FLOOR_GAME_PERCENTILE = 15
FLOOR_GAME_SD_CUTOFF = 1.5
MIN_RS_GAMES = 50
SEASONS = list(range(1996, 2025))  # 1996-97 through 2024-25

# Color scheme
GROUP_A_COLOR = "#d62728"
GROUP_B_COLOR = "#1f77b4"
RS_COLOR = "#7f7f7f"
```

Note: `nba_id` values should be verified at scrape time via the `commonplayerinfo` endpoint or the `regular_season_{season}.csv` files from the `resilience-basketball` project. If any ID is wrong, the scrape will fail cleanly (0 results returned). The `bbref_id` values are needed only if the NBA Stats API fallback to Basketball Reference is required (expected for pre-1996-97 seasons).

**`Makefile`:**

```makefile
.PHONY: scrape features screen-a screen-b screen-c visualize all clean

scrape:
	python src/scrape.py

features:
	python src/features.py

screen-a:
	python src/screen_a.py

screen-b:
	python src/screen_b.py

screen-c:
	python src/screen_c.py

visualize:
	python src/visualize.py

all: scrape features screen-a screen-b screen-c visualize

clean:
	rm -rf data/processed/ output/figures/
```

---

### Phase 1: Data Collection

**Source: NBA Stats API (primary), Basketball Reference (fallback for pre-1996-97)**

The `resilience-basketball` project at `https://github.com/hirememorey/resilience-basketball` contains a production-grade `NBAStatsClient` that handles rate limiting, caching, retries, and browser-mimicking headers. Copy and adapt it into `src/nba_client.py`, stripping to only the methods needed for this project.

#### 1.1: HTTP Client (`src/nba_client.py`)

Adapt from `resilience-basketball/src/nba_data/api/nba_stats_client.py`. Keep:

- **Rate limiting:** Minimum interval between requests (default 1.2s) + random jitter (0.2-0.8s)
- **Caching:** File-based JSON cache in `data/cache/`, MD5-keyed, configurable expiration (30 days for season-level data, 7 days for game logs)
- **Retry logic:** `urllib3.Retry` with exponential backoff on 429/5xx (10 retries, backoff factor 2)
- **Browser-mimicking headers:** Chrome User-Agent, `Origin: https://www.nba.com`, `Referer: https://www.nba.com/`, `x-nba-stats-origin: stats`, `x-nba-stats-token: true`
- **Session management:** Single `requests.Session` with mounted retry adapter

Methods to implement:

- `get_player_game_logs(player_id, season, season_type="Regular Season"|"Playoffs", measure_type="Base"|"Advanced")` — calls `playergamelogs` endpoint
- `get_team_game_logs(team_id, season, season_type="Playoffs")` — calls `teamgamelogs` endpoint
- `get_common_player_info(player_id)` — calls `commonplayerinfo` endpoint (for name verification)
- `get_league_team_stats(season, season_type="Regular Season", measure_type="Advanced")` — calls `leaguedashteamstats` for opponent defensive ratings

Helper functions:

- `result_set_to_records(response, result_set_name)` — Converts NBA Stats API `resultSets` arrays into list-of-dicts (copy from resilience-basketball)

#### 1.2: Series Game Number Inference (`src/scrape.py` — critical section)

**The Problem:** The NBA Stats API's `playergamelogs` endpoint has no series identifier or game number. If you try to infer series structure from individual player game logs, you get the wrong answer when a player misses a game (e.g., Harden misses Game 3 of a series → his Game 4 row gets mislabeled as Game 3, shifting all subsequent labels).

**The Solution: Derive series structure from team game logs, not player game logs.**

Algorithm:

1. **Fetch team playoff game logs** via `teamgamelogs` endpoint for every team that made the playoffs in each season.
2. **Group by season + opponent** (parsed from `MATCHUP` string, e.g., "vs. LAL" or "@ LAL") — this defines a series.
3. **Sort by `GAME_DATE`** within each series group.
4. **Assign sequential game number** (1 through N, max 7).
5. **Track cumulative W/L** within each series to determine elimination game status:
   - A game is an elimination game if the player's team has 3 losses (facing elimination) OR the opponent has 3 losses (opponent facing elimination).
6. **Handle edge case: same opponent in different rounds.** If there's a >7-day gap between consecutive games vs the same opponent, split into separate series. (Same opponent met twice in one playoff year is rare but possible if reseeding occurs.)
7. **Store as `data/raw/team_series_map.csv`** with columns: `season, team_abbrev, opponent_abbrev, game_date, series_game_num, is_elimination, team_wins_so_far, opponent_wins_so_far`.

8. **Join player game logs to the team series map** on (team, date, opponent). This gives each player game row its correct `series_game_num` and `is_elimination` flag, regardless of whether the player appeared in every game. If Harden misses Game 3, the team row still exists as Game 3 — Harden just has no row for it, and his Game 4 row joins correctly to `series_game_num=4`.

This approach is computed once per team-season and shared across all players on that team — more efficient and more correct than per-player inference.

#### 1.3: Main Scrape Flow (`src/scrape.py`)

**Step 1: Resolve player IDs**

For each player in `config.ALL_PLAYERS`:
- Call `get_common_player_info(nba_id)` to verify the ID is correct and get the player's active seasons
- If the ID returns no results, log an error and flag for manual resolution
- Store the player's team history (which team they were on each season)

**Step 2: Fetch team playoff game logs and build series map**

For each season in `config.SEASONS`:
- Fetch all team playoff game logs via `teamgamelogs`
- Run the series inference algorithm (Section 1.2)
- Save to `data/raw/team_series_map.csv`

**Step 3: Fetch player game logs**

For each player in `config.ALL_PLAYERS`:
- For each season the player was active:
  - Fetch RS game logs (Base): `get_player_game_logs(player_id, season, "Regular Season", "Base")`
  - Fetch RS game logs (Advanced): `get_player_game_logs(player_id, season, "Regular Season", "Advanced")`
  - Merge Base + Advanced on `(PLAYER_ID, GAME_ID)` → single row per game with all stats
  - Fetch Playoff game logs (Base): `get_player_game_logs(player_id, season, "Playoffs", "Base")`
  - Fetch Playoff game logs (Advanced): `get_player_game_logs(player_id, season, "Playoffs", "Advanced")`
  - Merge Base + Advanced on `(PLAYER_ID, GAME_ID)`
- Save to `data/raw/{player_slug}_rs.csv` and `data/raw/{player_slug}_po.csv`
- Save incrementally (every 10 players) to avoid total loss on interruption

**Step 4: Compute derived fields**

For each player's game log CSV:

- `game_score`: Computed from box score components using the formula:
  ```
  Game Score = PTS + 0.4*FGM + 0.7*OREB + 0.3*DREB + STL + 0.7*AST + 0.7*BLK
               - 0.7*FGA - 0.4*(FTA-FTM) - 0.4*PF - TOV
  ```
  Note: The `playergamelogs` endpoint returns OREB and DREB separately in the Advanced measure type, or they may need to be sourced from the Base endpoint. Verify at scrape time. If only total REB is available, approximate OREB as `0.25 * REB` and DREB as `0.75 * REB` (league-average split).

- `opponent`: Parsed from `MATCHUP` string. "vs. LAL" → opponent is LAL (home game). "@ LAL" → opponent is LAL (away game).

- `home_away`: "vs." → "home", "@" → "away"

- `usage_rate_approx`: `(FGA + 0.44*FTA + TOV) / team_possessions`. If team possessions are not available at game level, use the Basketball Reference approximation:
  ```
  team_possessions ~ 0.5 * ((FGA + 0.4*FTA - 1.07*(OREB/(OREB+OPP_DREB)) * (FGA-FGM) + TOV) / (MP / (team_MP/5)))
  ```
  For Pass 1, a simpler approximation is acceptable. If team possession data is unavailable, use the player's FGA+0.44*FTA+TOV as a raw creation volume metric instead.

- `rest_days`: Days between consecutive games. Compute from `GAME_DATE`. At the start of each playoff series (Series Game 1), set rest_days to the gap from the last game of any type (RS or prior series). If no prior game exists, rest_days = NaN.

**Step 5: Join series context to player logs**

For each player's playoff CSV:
- Join to `data/raw/team_series_map.csv` on (team, date, opponent)
- This adds: `series_game_num`, `is_elimination`, `team_wins_so_far`, `opponent_wins_so_far`
- Left join — if a player's game doesn't match (e.g., team ID mismatch), log a warning

**Step 6: Opponent defensive ratings**

- Fetch season-level team defensive ratings via `leaguedashteamstats` endpoint (measure_type="Advanced", metric="DEF_RATING")
- Or reuse the `defensive_context_{season}.csv` files from `resilience-basketball` if they cover the right seasons (2015-16 through 2023-24)
- For seasons not covered by resilience-basketball (pre-2015), fetch fresh from the API
- Save as `data/raw/opponent_defrtg.csv` with columns: `season, team_abbrev, def_rating`
- Join to each player's game log on (season, opponent)

**Step 7: Basketball Reference fallback**

If the NBA Stats API returns no data for a player-season (expected for Allen Iverson pre-1996-97, Ray Allen pre-1996-97):
- Try `basketball_reference_scraper` package's `player.get_game_logs()` method
- If that fails, manual scrape with `requests` + `beautifulsoup4` from BBRef gamelog pages
- BBRef URL pattern: `https://www.basketball-reference.com/players/{first_letter}/{bbref_id}/gamelog/{year}/`
- **Rate limiting for BBRef:** 3-second delay between requests + random jitter (±1s). BBRef blocks aggressive scraping. Add exponential backoff on 429/503.
- BBRef game logs include pre-computed Game Score, which can be used directly or validated against the formula
- Parse the HTML table: `Game Score` column, `Series` column (only present in playoff tables — indicates which playoff round), `GmSc` column
- For BBRef playoff data, series game number must still be inferred using the team-series approach (Section 1.2), as BBRef only indicates the round, not the game within the round

**Step 8: Data validation**

- Row count audit: compare fetched game count against known career totals (hardcode expected ranges for sanity check)
- Null/missing value audit per column
- Range checks: minutes 0-63 (OT), TS% 0-1.5, FTA >= 0, Game Score reasonable range (-10 to 50)
- Flag games where minutes <= 15 as potentially injury-affected (don't exclude, but mark with `is_injury_flagged = True`)
- Verify floor-game rate in RS is approximately 15% after feature engineering (by construction — sanity check)
- Log warnings for any anomalous values (e.g., 0 minutes played → DNP, should be excluded)

**Output files from Phase 1:**

- `data/raw/{player_slug}_rs.csv` — regular season game logs with all columns
- `data/raw/{player_slug}_po.csv` — playoff game logs with all columns + series_game_num, is_elimination, rest_days
- `data/raw/team_series_map.csv` — team-level series structure
- `data/raw/opponent_defrtg.csv` — season-level opponent defensive ratings

**Column schema for player game log CSVs:**

| Column | Source | Notes |
|---|---|---|
| `player_name` | config | Display name |
| `player_group` | config | "A" or "B" |
| `nba_id` | config | NBA Stats API player ID |
| `season` | API | e.g., "2023-24" |
| `game_id` | API | NBA game ID |
| `game_date` | API | Date of game |
| `is_playoff` | derived | True/False |
| `matchup` | API | e.g., "HOU vs. LAL" or "HOU @ LAL" |
| `opponent` | derived | 3-letter abbreviation parsed from MATCHUP |
| `home_away` | derived | "home" or "away" |
| `minutes` | API | Minutes played |
| `game_score` | derived | Computed from formula |
| `bpm` | API (Advanced) | Box Plus/Minus |
| `pts` | API | Points |
| `fgm` | API | Field goals made |
| `fga` | API | Field goals attempted |
| `fg_pct` | API | Field goal percentage |
| `fg3m` | API | 3-pointers made |
| `fg3a` | API | 3-pointers attempted |
| `fg3_pct` | API | 3-point percentage |
| `ftm` | API | Free throws made |
| `fta` | API | Free throws attempted |
| `ft_pct` | API | Free throw percentage |
| `oreb` | API | Offensive rebounds |
| `dreb` | API | Defensive rebounds |
| `reb` | API | Total rebounds |
| `ast` | API | Assists |
| `stl` | API | Steals |
| `blk` | API | Blocks |
| `tov` | API | Turnovers |
| `pf` | API | Personal fouls |
| `plus_minus` | API | Plus/minus |
| `ts_pct` | API (Advanced) | True shooting percentage |
| `usg_pct` | API (Advanced) | Usage percentage |
| `ast_pct` | API (Advanced) | Assist percentage |
| `usage_rate_approx` | derived | Approximation if USG% not available |
| `series_game_num` | team_series_map join | 1-7, playoffs only |
| `is_elimination` | team_series_map join | True/False, playoffs only |
| `team_wins_so_far` | team_series_map join | Playoff series wins, playoffs only |
| `opponent_wins_so_far` | team_series_map join | Playoff series opponent wins, playoffs only |
| `rest_days` | derived | Days since previous game |
| `opponent_defrtg` | opponent_defrtg join | Season-level opponent defensive rating |
| `is_injury_flagged` | derived | True if minutes <= 15 |

---

### Phase 2: Feature Engineering (`src/features.py`)

**Input:** All `data/raw/{player_slug}_rs.csv` and `data/raw/{player_slug}_po.csv` files.

**Step 1: Filter and clean**

- Exclude rows where `minutes == 0` (DNP — did not play)
- Keep `is_injury_flagged` rows in the dataset but preserve the flag for downstream sensitivity analysis
- Normalize column names to lowercase snake_case if not already done in scrape

**Step 2: Compute player baselines from regular season only**

For each player, compute from RS game logs only (never include playoff games in baseline):

| Stat | Description |
|---|---|
| `rs_mean_gs` | Mean Game Score |
| `rs_sd_gs` | Standard deviation of Game Score |
| `rs_p15_gs` | 15th percentile of Game Score |
| `rs_p85_gs` | 85th percentile of Game Score |
| `rs_median_gs` | Median Game Score |
| `rs_mean_bpm` | Mean BPM (if available) |
| `rs_sd_bpm` | SD of BPM |
| `rs_n_games` | Number of RS games used |

- Require `rs_n_games >= MIN_RS_GAMES` (50). If a player falls short, log a warning and exclude from peer comparison (but still include in Harden-specific analysis if applicable).
- Save as `data/processed/player_baselines.csv` (one row per player).

**Step 3: Classify floor games**

For every game (RS and playoff), join player baselines and compute:

```python
is_floor_primary   = game_score < rs_p15_gs
is_floor_secondary = game_score < (rs_mean_gs - FLOOR_GAME_SD_CUTOFF * rs_sd_gs)
residual_primary   = game_score - rs_p15_gs
residual_secondary = game_score - (rs_mean_gs - FLOOR_GAME_SD_CUTOFF * rs_sd_gs)
```

- Primary threshold (15th percentile) is the main analysis metric.
- Secondary threshold (mean − 1.5 SD) is a robustness check.
- Floor-game flags are always computed against RS baselines, even for playoff games. This is intentional: we are asking "how often does this player produce a game that would be in the bottom 15% of their regular-season distribution?"

Save intermediate output as `data/processed/floor_games.csv` (all games with floor flags and residuals).

**Step 4: Build analysis table**

Concatenate all players' RS + playoff game logs into one flat table:

- Add `player_group`: "A" or "B" from config
- Add `is_playoff`: boolean
- Join all baseline columns from `player_baselines.csv`
- Join all floor-game columns

Output: `data/processed/analysis_table.csv`

**Step 5: Data quality checks**

- Assert RS floor-game rate ≈ 15% per player (by construction of percentile threshold). Log if any player deviates by >3 percentage points.
- Verify Game Score distribution is right-skewed (mean > median) for each player.
- Report playoff game counts per player per season — flag any player with < 10 total playoff games as underpowered for within-series analysis.
- Print summary stats: total games, RS games, playoff games, floor-game rates by player and season type.

**Output files from Phase 2:**

- `data/processed/player_baselines.csv`
- `data/processed/floor_games.csv`
- `data/processed/analysis_table.csv`

---

### Phase 3: Analysis — Three Screens

All screens read from `data/processed/analysis_table.csv`. Each screen writes a results CSV to `data/processed/` and prints a human-readable summary to stdout.

#### 3.1: Screen A — Variance Shift Test (`src/screen_a.py`)

**Question:** Does the playoff distribution shift via increased floor-game frequency more than via mean decline?

**Per player:**

1. Build 2×2 contingency table: (floor vs non-floor) × (RS vs playoff)
2. Run chi-squared test of independence. If any expected cell count < 5, use Fisher's exact test instead.
3. Compute floor-game rates: `rs_floor_rate`, `po_floor_rate`, `floor_rate_ratio = po_floor_rate / rs_floor_rate`
4. Run Welch's t-test on mean Game Score (RS vs playoff). Also compute `mean_ratio = po_mean_gs / rs_mean_gs`.
5. Compute **variance shift ratio**:
   ```
   variance_shift_ratio = floor_rate_ratio / mean_ratio
   ```
   If `variance_shift_ratio > 1`, the floor-game rate increase outpaces the mean decline — variance shift dominates.

**Output:** `data/processed/screen_a_results.csv`

| Column | Description |
|---|---|
| `player` | Player name |
| `player_group` | A or B |
| `rs_n_games` | RS game count |
| `po_n_games` | Playoff game count |
| `rs_floor_rate` | RS floor-game rate (primary) |
| `po_floor_rate` | Playoff floor-game rate (primary) |
| `floor_rate_increase` | po_floor_rate − rs_floor_rate |
| `floor_rate_ratio` | po / rs |
| `rs_mean_gs` | RS mean Game Score |
| `po_mean_gs` | Playoff mean Game Score |
| `mean_decline` | rs_mean_gs − po_mean_gs |
| `mean_ratio` | po / rs |
| `variance_shift_ratio` | floor_rate_ratio / mean_ratio |
| `chi2_stat` | Chi-squared statistic |
| `chi2_pvalue` | p-value |
| `ttest_stat` | Welch's t-test statistic |
| `ttest_pvalue` | p-value |

**Also run secondary threshold analysis** (mean − 1.5 SD) and save as `data/processed/screen_a_results_secondary.csv`.

**Print summary:** List players where `variance_shift_ratio > 1` and `chi2_pvalue < 0.05`. Highlight Harden's position.

#### 3.2: Screen B — Within-Series Gradient Test (`src/screen_b.py`)

**Question:** Does floor-game frequency increase as a series progresses (H2)?

**Requires:** `series_game_num` from team series map join (playoff games only).

**Analysis steps:**

1. Filter to playoff games where `series_game_num` is not null.
2. Create series game buckets:
   - `early`: games 1–2
   - `mid`: games 3–4
   - `late`: games 5–7
3. Per player: compute floor-game rate per bucket.
4. Aggregate: compute floor-game rate per bucket for Group A and Group B separately.
5. **Trend test:** Cochran-Armitage test for trend across buckets (early → mid → late). Alternative: logistic regression `is_floor_primary ~ series_game_bucket` with bucket as ordinal (1, 2, 3).
6. **Harden-specific:** Compute exact floor-game rate by `series_game_num` (1 through 7) with binomial confidence intervals (Wilson score interval).
7. **Sensitivity:** Re-run excluding `is_injury_flagged` games to check if injury-driven absences affect the gradient.

**Output:** `data/processed/screen_b_results.csv`

| Column | Description |
|---|---|
| `player` | Player name (or "Group A", "Group B" for aggregates) |
| `series_bucket` | early / mid / late |
| `n_games` | Games in bucket |
| `floor_rate` | Floor-game rate |
| `ci_lower` | 95% CI lower bound |
| `ci_upper` | 95% CI upper bound |

Also save `data/processed/screen_b_harden_by_game.csv` with exact game-by-game (1–7) rates for Harden.

**Print summary:** Does floor-game rate increase monotonically from early → late? Is Harden's late-series rate an outlier?

#### 3.3: Screen C — Peer Comparison (`src/screen_c.py`)

**Question:** Is Harden an outlier among heliocentric creators (Group A) vs scalable stars (Group B)?

**Analysis steps:**

1. Load Screen A results for all 12 players.
2. Rank all players by `floor_rate_increase` (playoff − RS).
3. Compute Harden's percentile rank within the 12-player sample.
4. Compare Group A vs Group B distributions of `floor_rate_increase`:
   - Mann-Whitney U test (non-parametric, small sample)
   - Cohen's d effect size
5. Compare Group A vs Group B on `variance_shift_ratio`.
6. Identify whether Harden is the largest outlier in Group A or merely above average.

**Output:** `data/processed/screen_c_results.csv`

| Column | Description |
|---|---|
| `player` | Player name |
| `player_group` | A or B |
| `floor_rate_increase` | From Screen A |
| `variance_shift_ratio` | From Screen A |
| `rank_floor_increase` | Rank 1–12 |
| `rank_variance_shift` | Rank 1–12 |
| `harden_percentile` | Harden's percentile (only on Harden's row) |

Also save `data/processed/screen_c_group_comparison.csv` with Group A vs Group B test results.

**Print summary:** Harden's rank, Group A vs B comparison p-values, effect sizes.

---

### Phase 4: Visualization (`src/visualize.py`)

All plots saved to `output/figures/` as both PNG (150 dpi) and SVG.

**Style constants (from config):**
- Group A: `#d62728` (red)
- Group B: `#1f77b4` (blue)
- RS: `#7f7f7f` (gray)
- Playoff: use group color
- Harden: highlighted with star marker or bold label

**Plot 1: Distribution comparison** (`dist_comparison_{player_slug}.png`)

- Overlaid KDEs of Game Score: RS (gray) vs playoff (group color)
- Vertical dashed line at player's RS 15th percentile threshold
- Shaded region below threshold = floor-game zone
- Generate for all 12 players; Harden version is the featured plot

**Plot 2: Floor-game rate bar chart** (`floor_rate_comparison.png`)

- Grouped bar chart: RS vs playoff floor-game rate
- X-axis: all 12 players, sorted by floor_rate_increase descending
- Color: Group A (red) / Group B (blue)
- Harden highlighted with star or annotation
- Error bars: binomial 95% CI (Wilson)

**Plot 3: Within-series decay** (`series_decay.png`)

- Line chart: floor-game rate by series game number (1–7)
- Harden as primary line with CI shading
- Group A aggregate and Group B aggregate as dashed comparison lines
- X-axis: series game number; Y-axis: floor-game rate

**Plot 4: Peer scatter** (`peer_scatter.png`)

- X-axis: mean Game Score decline (RS → playoff)
- Y-axis: floor-game rate increase (RS → playoff)
- Each player = labeled dot, color-coded by group
- Harden highlighted
- Quadrant reference lines at (0, 0)
- Quadrant labels: "Mean decline only", "Variance shift only", "Both", "Neither"

**Plot 5: Variance shift decomposition** (`variance_decomposition.png`)

- For each player: stacked or grouped bar showing RS vs playoff mean Game Score alongside RS vs playoff floor-game rate
- Makes the "mean shift vs tail fattening" contrast visually obvious
- Sort by variance_shift_ratio descending

---

### Phase 5: Exploration Notebook (`notebooks/exploration.ipynb`)

**Purpose:** Narrative walkthrough of all three screens with inline visualizations. This becomes the first draft of the results section.

**Structure:**

1. **Setup cell:** Import pandas, load `analysis_table.csv`, `screen_a/b/c_results.csv`
2. **Data overview:** Game counts, date ranges, RS vs playoff sample sizes per player
3. **Screen A walkthrough:** Load results, display table, render distribution comparison plots for Harden + 2–3 peers
4. **Screen B walkthrough:** Series decay plot, Harden game-by-game table, Group A vs B bucket comparison
5. **Screen C walkthrough:** Peer scatter, ranking table, Group A vs B statistical test results
6. **Decision matrix:**

   | H1 (variance shift) | H2 (series gradient) | Conclusion |
   |---|---|---|
   | Confirmed | Confirmed | Proceed to Pass 2 |
   | Confirmed | Rejected | Paper about playoff variance, not adaptation |
   | Rejected | — | Line is dead |

7. **Confounds section:** Acknowledge limitations (see below) without controlling for them in Pass 1.

---

### Implementation Order

| Step | File | Depends on | Est. effort |
|---|---|---|---|
| 1 | `config.py` | — | Small |
| 2 | `src/nba_client.py` | config.py | Medium |
| 3 | `src/scrape.py` | nba_client.py, config.py | Large |
| 4 | `src/features.py` | scrape.py output | Medium |
| 5 | `src/screen_a.py` | features.py output | Medium |
| 6 | `src/screen_b.py` | features.py output | Medium |
| 7 | `src/screen_c.py` | screen_a.py output | Medium |
| 8 | `src/visualize.py` | all screen outputs | Medium |
| 9 | `notebooks/exploration.ipynb` | all outputs | Small |
| 10 | `Makefile` | all src files | Small |

**Recommended build sequence for a new implementer:**

1. Scaffold project (Phase 0) — config, Makefile, requirements, directory structure
2. Build and test `nba_client.py` in isolation — verify one player-season fetch works
3. Build team series map first (Section 1.2) — this is the critical correctness dependency; test against a known series (e.g., HOU vs GSW 2018)
4. Scrape all player logs
5. Feature engineering → verify RS floor rate ≈ 15%
6. Run screens A, B, C in order
7. Generate visualizations
8. Populate notebook

---

### Existing Code to Reuse

**Primary source: `resilience-basketball`** (`https://github.com/hirememorey/resilience-basketball`)

| File | What to copy/adapt |
|---|---|
| `src/nba_data/api/nba_stats_client.py` | HTTP client, rate limiting, caching, retries |
| `src/nba_data/api/helpers.py` | `result_set_to_records()` and response parsing |
| `scripts/collect_rs_game_logs.py` | Pattern for bulk RS game log collection |
| `scripts/collect_playoff_logs.py` | Pattern for bulk playoff game log collection |
| `data/defensive_context_{season}.csv` | Opponent defensive ratings (2015-16 through 2023-24) |

**Secondary source: `cranky-scott-foster`** (`https://github.com/hirememorey/cranky-scott-foster`)

| File | What to copy/adapt |
|---|---|
| Scraping patterns | Rate limiting, retry, caching conventions (if BBRef fallback needed) |

**Do not import these repos as packages.** Copy the relevant modules into this project to keep it self-contained.

**`basketball_reference_scraper` package:** Available on PyPI (v2.0.0, updated March 2024). Use only as fallback for pre-1996-97 seasons where the NBA Stats API has no data. Not the primary data path.

---

### Confounds (Acknowledged in Pass 1, Not Controlled)

These should be documented in the notebook but are out of scope for Pass 1:

1. **Series length ↔ opponent quality.** Games 5–7 only exist against good teams. A higher late-series floor rate may partially reflect opponent strength, not adaptation.
2. **Injury.** Games flagged with `is_injury_flagged` (minutes ≤ 15) may distort floor-game rates. Screen B includes a sensitivity run excluding these.
3. **Age/decline.** No age adjustment. Older playoff seasons for Iverson/Harden may reflect career decline, not playoff-specific effects.
4. **Team quality colinearity.** Heliocentric creators may have weaker supporting casts in some playoff years. Not adjusted.
5. **Rest days.** Included as a column but not controlled for. Back-to-backs and short rest may drive floor games independently of series position.
6. **Opponent defensive rating is season-level.** Joining season-average DEF_RATING to individual games ignores that a team's defense may improve over a series. Pass 2 could use game-level or series-level opponent metrics.

---

### Pass 1 Success Criteria

| Screen | Pass condition |
|---|---|
| Screen A | Harden `variance_shift_ratio > 1` and `chi2_pvalue < 0.05` |
| Screen B | Monotonic increase in floor-game rate from early → late series games for Harden; trend test p < 0.10 |
| Screen C | Harden in top 3 of `floor_rate_increase` among all 12 players; Group A mean > Group B mean on floor-rate-increase |

If Screen A fails for Harden, stop. The research question is answered (in the negative).

If Screen A passes but Screen B fails, there is still a paper — about playoff variance conditions generally, not within-series adaptation.

If all three pass, proceed to Pass 2 (controlled regression, opponent-adjusted models, usage/FGA decomposition).
