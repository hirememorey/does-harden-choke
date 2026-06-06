# does-harden-choke

Research project asking whether star players **contract**, **force**, or **redistribute** under playoff adversity — measured first at the game level (Pass 1), then at the possession level (Pass 2).

**Status:** Pass 1 complete. Pass 2 possession parser implemented; possession-count validation gate still open (see below).

## Documents

| Document | Covers |
|----------|--------|
| [`documents/development/findings.md`](documents/development/findings.md) | Pass 1 results — start here for what we learned |
| [`documents/development/pass1_plan.md`](documents/development/pass1_plan.md) | Pass 1 research design and pipeline spec |
| [`documents/development/pass2_research_design.md`](documents/development/pass2_research_design.md) | Pass 2 conceptual framing |
| [`documents/development/pass2_design_spec.md`](documents/development/pass2_design_spec.md) | Pass 2 technical spec (events, baselines, validation gates) |
| [`documents/development/pass2_possession_parser_status.md`](documents/development/pass2_possession_parser_status.md) | Open parser bug + how to reproduce validation |

Root level is **runtime** (Makefile, config, `src/`). `documents/development/` is **research context**.

## Setup

Requires Python 3.11+ (tested on 3.13).

```bash
make venv
source .venv/bin/activate
```

## Pass 1 pipeline (complete)

```bash
make scrape              # → data/raw/*.csv
make validate-scrape
make features            # → data/processed/analysis_table.csv
make screen-a            # floor-game rates
make screen-b            # shrinker vs forcer
make screen-c            # group comparisons
make visualize           # → output/figures/
```

Or `make all` after scrape. Smoke test: `make smoke-scrape` (Harden 2023-24 only).

## Pass 2 pipeline (in progress)

```bash
make scrape-pbp              # 3 validation games → data/raw/pbp/
make build-possessions       # → data/processed/pass2/possessions_*.csv
make validate-possessions    # §6.1 validation gates
```

Validation fixture (tracked in git): `data/pass2_validation_games.json`

## Open task for Pass 2

Possession counts drift ±3–6 per team vs the Oliver estimate on validation games. USG reconstruction and terminal-mismatch checks pass. See [`pass2_possession_parser_status.md`](documents/development/pass2_possession_parser_status.md) and §6.1 of [`pass2_design_spec.md`](documents/development/pass2_design_spec.md).

## Data policy

Everything under `data/` is gitignored **except** `data/pass2_validation_games.json`. Regenerate bulk data with the Makefile targets above; do not commit CSVs, cache, or PBP JSON.
