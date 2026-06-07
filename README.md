# does-harden-choke

Research project asking whether star players **contract**, **force**, or **redistribute** under playoff adversity — measured first at the game level (Pass 1), then at the possession level (Pass 2).

**Status (June 2026):** Pass 1 complete and extended (18 players, opponent adjustment, RS retention baselines). **Causal chain Step 0 complete** — team ORtg logs scraped and validated; Step 1 (join to player floor games) is next ([`causal_chain_plan.md`](documents/development/causal_chain_plan.md)). Pass 2 possession parser validated on fixture games; full Pass 2 pipeline not yet scaled.

**Start here:** [`documents/development/DEVELOPER.md`](documents/development/DEVELOPER.md) to onboard and run the pipeline. [`documents/development/findings.md`](documents/development/findings.md) for what we learned. [`documents/development/open_questions.md`](documents/development/open_questions.md) for resolved decisions and remaining gaps.

## Documents

| Document | Covers |
|----------|--------|
| [`documents/development/DEVELOPER.md`](documents/development/DEVELOPER.md) | **Onboarding** — setup, pipeline, cohort, what's done vs. open |
| [`documents/development/findings.md`](documents/development/findings.md) | Full results — Pass 1 screens A–E plus post-Pass-1 extensions |
| [`documents/development/open_questions.md`](documents/development/open_questions.md) | Five pre-scaling questions — **resolved** with pointers to evidence |
| [`documents/development/pass1_plan.md`](documents/development/pass1_plan.md) | Pass 1 research design and pipeline spec |
| [`documents/development/pass2_research_design.md`](documents/development/pass2_research_design.md) | Pass 2 conceptual framing |
| [`documents/development/pass2_design_spec.md`](documents/development/pass2_design_spec.md) | Pass 2 technical spec (events, baselines, validation gates) |
| [`documents/development/pass2_possession_parser_status.md`](documents/development/pass2_possession_parser_status.md) | Parser validation status and how to reproduce |
| [`documents/development/causal_chain_plan.md`](documents/development/causal_chain_plan.md) | **Causal chain** — Step 0 done; Steps 1–4 spec for contraction → ORtg → wins |

Root level is **runtime** (Makefile, `config.py`, `src/`). `documents/development/` is **research context**.

## Cohort (18 players)

Defined in `config.py`. Original 11-player sample expanded with DeRozan, Wall, CP3, LeBron, Kobe, Paul George, and Shai Gilgeous-Alexander.

- **Group A** (11): heliocentric creators — Harden, Westbrook, Luka, Trae, Iverson, Lillard, DeRozan, Wall, CP3, LeBron, SGA
- **Group B** (7): scalable / wing stars — Curry, Klay, Ray Allen, Hamilton, Durant, Kobe, PG

## Setup

Requires Python 3.11+ (tested on 3.13).

```bash
make venv
source .venv/bin/activate
```

## Pass 1 pipeline

```bash
make scrape              # → data/raw/*.csv  (NBA Stats API; ~30 min full cohort)
make validate-scrape
make features            # → data/processed/analysis_table.csv
make screen-a            # floor-game rates (raw)
make screen-b            # within-series gradient
make screen-c            # group comparisons
make visualize           # → output/figures/
```

**Post-Pass-1 extensions:**

```bash
make screen-a-adj        # opponent-adjusted floor rates → screen_a_adj_results.csv
make retention           # RS vs PO retention baselines → retention_baselines.csv
make screen-e            # mechanism taxonomy (contractor/forcer/mixed)
```

Or `make all` after scrape (screens A–C + visualize). Smoke test: `make smoke-scrape` (Harden 2023-24 only).

## Causal chain pipeline (Step 0 complete)

```bash
make scrape-team-logs      # → data/raw/team_game_logs.csv (~50 min; resumes if interrupted)
make validate-team-logs    # join coverage + ORtg sanity gates
```

Step 1 (`join_causal_table.py`) not yet implemented — see [`causal_chain_plan.md`](documents/development/causal_chain_plan.md).

## Pass 2 pipeline (partial)

```bash
make scrape-pbp              # 3 validation games → data/raw/pbp/
make build-possessions       # → data/processed/pass2/possessions_*.csv
make validate-possessions    # §6.1 validation gates
```

**Spike / estimation scripts:**

```bash
make event-frequency                    # Event A/B frequency from PBP sample → event_frequency_estimates.csv
python src/pass2/cold_start_spike.py    # Harden vs Kobe case studies on validation games
```

To fetch additional PBP for a star player:

```bash
python src/pass2/ingest_pbp.py --game-id <GAME_ID>
python src/pass2/possessions.py --game-id <GAME_ID>   # then build_and_save via possessions module
```

Validation fixture (tracked in git): `data/pass2_validation_games.json`

## Current thesis (one sentence)

> Under adversity, a star's offensive structure determines their failure mode (contraction vs. forcing); contraction is a stable career trait, and whether it is opponent-independent (Harden, PG) or scheme-dependent (SGA) distinguishes players the public narrative lumps together as "playoff chokers."

## What to do next

See **Remaining work** in [`open_questions.md`](documents/development/open_questions.md). Priority order:

1. **Causal chain Step 1** — join floor games to team ORtg; then test contraction → wins ([`causal_chain_plan.md`](documents/development/causal_chain_plan.md))
2. **Pass 2 at scale** — same-game pre-event baselines on ~270 combined cold-start events
3. **Out-of-sample validation** — train profile on first half of career, test on second half
4. **Expand cohort** — Embiid, Butler, Mitchell for contractor/forcer taxonomy robustness

## Data policy

Everything under `data/` is gitignored **except** `data/pass2_validation_games.json`. Regenerate bulk data with the Makefile targets above; do not commit CSVs, cache, or PBP JSON.

## Output files (generated, not in git)

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
| `data/processed/causal_analysis_table.csv` | `join_causal_table.py` *(planned)* |
