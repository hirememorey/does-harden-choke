# Developer Onboarding

**Last updated:** June 2026

This guide gets a new contributor from clone → running analyses → understanding what is settled vs. open. Read this first, then [`findings.md`](findings.md) for results and [`open_questions.md`](open_questions.md) for decision status.

---

## What this project is

Research project testing whether James Harden's playoff reputation reflects a real variance shift — and, more generally, whether star players **contract**, **force**, or **redistribute** under adversity.

- **Pass 1 (game level):** Complete. Screens A–E plus June 2026 extensions (opponent adjustment, RS retention baselines, refined mechanism taxonomy).
- **Causal chain (game level):** Step 0 complete — team game logs scraped and validated (`scrape_team_logs.py`). Step 1 (join to `analysis_table.csv`) is next. See [`causal_chain_plan.md`](causal_chain_plan.md).
- **Pass 2 (possession level):** Parser validated on fixture games; event frequency estimated; full pipeline not scaled to all ~270 cold-start events.

**Current thesis (one sentence):**

> Under adversity, a star's offensive structure determines their failure mode (contraction vs. forcing); contraction is a stable career trait, and whether it is opponent-independent (Harden, PG) or scheme-dependent (SGA) distinguishes players the public narrative lumps together as "playoff chokers."

---

## Repo layout

```
does-harden-choke/
├── config.py                 # Cohort, paths, analysis parameters
├── Makefile                  # Pipeline targets
├── requirements.txt
├── src/
│   ├── scrape.py             # NBA Stats API → data/raw/*.csv
│   ├── features.py           # Raw CSVs → analysis_table.csv
│   ├── screen_a.py … screen_e.py   # Pass 1 screens
│   ├── screen_a_adj.py       # Opponent-adjusted floor rates (extension)
│   ├── rs_retention_baseline.py    # RS vs PO retention baselines (extension)
│   ├── scrape_team_logs.py   # Causal chain Step 0 — team ORtg / POSS
│   ├── validate_team_logs.py # Causal chain Step 0 validation gates
│   ├── visualize.py
│   └── pass2/
│       ├── ingest_pbp.py     # Fetch play-by-play JSON
│       ├── possessions.py    # PBP → possession CSVs
│       ├── validate_possessions.py
│       ├── event_frequency.py    # Event A/B frequency estimates
│       └── cold_start_spike.py   # Harden vs Kobe case studies
├── data/
│   ├── raw/                  # gitignored — game logs, PBP JSON
│   ├── processed/            # gitignored — analysis outputs
│   └── pass2_validation_games.json   # tracked fixture (3 games)
├── documents/development/    # Research context (tracked)
│   ├── findings.md           # Full results — start here for science
│   ├── open_questions.md     # Resolved decisions + remaining gaps
│   ├── DEVELOPER.md          # This file
│   ├── pass1_plan.md         # Original Pass 1 spec
│   └── pass2_*.md            # Pass 2 design + parser status
└── output/figures/           # gitignored — charts from visualize.py
```

**Runtime vs. research:** Root + `src/` is executable code. `documents/development/` is narrative and design — update it when findings or decisions change.

---

## Setup

Requires Python 3.11+ (tested on 3.13).

```bash
make venv
source .venv/bin/activate
```

Data under `data/` is gitignored except `data/pass2_validation_games.json`. After clone you must scrape or obtain raw CSVs locally.

---

## Full pipeline (recommended order)

### 1. Scrape and validate

```bash
make scrape              # ~30 min for full 18-player cohort
make validate-scrape
```

Smoke test (Harden 2023-24 only):

```bash
make smoke-scrape
```

### 2. Pass 1 core

```bash
make features            # → data/processed/analysis_table.csv
make screen-a            # variance shift (raw)
make screen-b            # within-series gradient (H2)
make screen-c            # group comparisons (H3)
make screen-e            # mechanism taxonomy
make visualize           # → output/figures/
```

Screen D (leverage concentration) has no Makefile target — run `python src/screen_d.py` if needed.

### 3. Pass 1 extensions (June 2026)

```bash
make screen-a-adj        # opponent-adjusted floor rates
make retention           # RS vs PO FGA/FTA/min retention baselines
```

### 4. Causal chain — Step 0 (June 2026, complete)

Requires player raw CSVs from step 1. Fetches team-level `OFF_RATING`, `POSS`, `WL` for every cohort game.

```bash
make scrape-team-logs    # ~50 min; --resume checkpoints every 10 team-seasons
make validate-team-logs  # must pass before Step 1
```

Smoke test (5 team-seasons in 2023-24):

```bash
make smoke-team-logs
```

**Next:** implement Step 1 per [`causal_chain_plan.md`](causal_chain_plan.md) — join `team_game_logs.csv` to `analysis_table.csv` on `(game_id, team_id)` with normalized game IDs.

### 5. Pass 2 (partial)

```bash
make scrape-pbp          # 3 validation games
make build-possessions
make validate-possessions
make event-frequency     # Event A/B projections from PBP sample
```

Spike scripts:

```bash
python src/pass2/cold_start_spike.py
```

To fetch additional PBP for a specific game:

```bash
python src/pass2/ingest_pbp.py --game-id <GAME_ID>
python -c "from src.pass2.possessions import build_and_save; build_and_save('<GAME_ID>')"
```

---

## Cohort (18 players)

Defined in `config.py`. Original 11-player Pass 1 sample expanded with DeRozan, Wall, CP3, LeBron, Kobe, Paul George, and Shai Gilgeous-Alexander.

| Group | Label | Players |
|-------|-------|---------|
| A | Heliocentric creators | Harden, Westbrook, Luka, Trae, Iverson, Lillard, DeRozan, Wall, CP3, LeBron, SGA |
| B | Scalable / wing stars | Curry, Klay, Ray Allen, Hamilton, Durant, Kobe, PG |

### Adding a player

1. Add entry to `GROUP_A` or `GROUP_B` in `config.py` with `nba_id` and `bbref_id`.
2. `make scrape` (or `python src/scrape.py --players "Player Name"`).
3. `make features` then re-run screens and extensions.
4. Update `findings.md` if results change materially.

---

## Key definitions

| Term | Definition |
|------|------------|
| **Floor game** | Game Score below player's RS 15th percentile (`is_floor_primary`) |
| **FGA retention** | (FGA/36 in floor games) / (FGA/36 in non-floor games) |
| **FTA retention** | Same for free throw attempts |
| **Contractor** | Volume collapses in floor games (low FGA/FTA retention) |
| **Forcer** | Volume preserved, efficiency collapses (high FGA retention) |
| **Event A** | ≤1 FGM on ≥5 Q1–Q2 FGA (Pass 2 cold-start trigger) |
| **Event B** | Consecutive empty offensive trips (Pass 2 supplement) |

---

## What we know (June 2026)

| Finding | Evidence |
|---------|----------|
| H2 (late-series adaptation) rejected | `screen_b.py` — flat early/mid/late gradient |
| Aggregate playoff floor-rate increase explained by opponent quality | `screen_a_adj.py` — `is_playoff` OR ≈ 0.98, *p* ≈ 0.80 |
| Harden floors are opponent-independent | 33% vs weak D, 16% vs strong D; def_coef *p* ≈ 0.07 |
| Contraction is a stable trait | Harden RS≈PO FGA retention (75%→74%); cohort r = 0.72 |
| Failure-mode taxonomy is novel | Screen E + retention baselines — contractors vs forcers |
| PG shares Harden's opponent-independent pattern | Different mechanism: PO FTA collapse (−33pp) |
| SGA is scheme-dependent contractor | 0% floor vs strong D; def_coef *p* = 0.001 |
| Kobe was misclassified as shrinker | Blowout benching inflated minute drop; ≥25 min → forcer |
| Pass 2 event frequency adequate for top stars | ~138 Event A projected; ~273 Events A+B combined |

See [`findings.md`](findings.md) for full tables and interpretation.

---

## What we do NOT know yet

These block a "who to avoid in the playoffs" scouting claim:

1. **Causal chain Step 1+** — join floor flags to team ORtg; test contraction → wins ([`causal_chain_plan.md`](causal_chain_plan.md))
2. **Minutes decontamination at possession level** — on-floor contraction vs. benching
3. **Out-of-sample validation** — train profile on career first half, test second half
4. **Pass 2 at scale** — same-game pre-event baselines on full event set
5. **Series-level defensive data** — season-average DEF_RATING is coarse
6. **Small-sample players** — SGA (8 PO floor games), PG (17) need more data

Full list: [`open_questions.md` § Remaining work](open_questions.md).

---

## Generated output files

| File | Script |
|------|--------|
| `data/processed/analysis_table.csv` | `features.py` |
| `data/processed/screen_a_results.csv` | `screen_a.py` |
| `data/processed/screen_a_adj_results.csv` | `screen_a_adj.py` |
| `data/processed/retention_baselines.csv` | `rs_retention_baseline.py` |
| `data/processed/screen_e_results.csv` | `screen_e.py` |
| `data/processed/event_frequency_estimates.csv` | `pass2/event_frequency.py` |
| `data/processed/pass2/possessions_*.csv` | `pass2/possessions.py` |
| `data/raw/team_game_logs.csv` | `scrape_team_logs.py` |
| `data/processed/causal_analysis_table.csv` | `join_causal_table.py` *(not yet written)* |

---

## Suggested next tasks (priority order)

1. **Causal chain Step 1** — `join_causal_table.py`: merge `analysis_table.csv` + `team_game_logs.csv`
2. **Pass 2 at scale** — run pre-event baseline matching on ~273 events
3. **Out-of-sample validation** — split career halves
4. **Expand cohort** — Embiid, Butler, Mitchell
5. **Exclude 3–5 possessions before Event A** from baseline pool (per `pass2_design_spec.md`)

---

## Data policy

- Do **not** commit `data/raw/`, `data/processed/`, `data/cache/`, or `output/`.
- Exception: `data/pass2_validation_games.json` is tracked for reproducible parser validation.
- Regenerate locally via Makefile targets.

---

## Document index

| Read when… | Document |
|------------|----------|
| Onboarding / running code | This file + `README.md` |
| What we learned | `findings.md` |
| What's decided vs. open | `open_questions.md` |
| Original Pass 1 design | `pass1_plan.md` |
| Pass 2 event definitions | `pass2_design_spec.md` |
| Parser validation | `pass2_possession_parser_status.md` |
| Causal chain implementation | `causal_chain_plan.md` |
