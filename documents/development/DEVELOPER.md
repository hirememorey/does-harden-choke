# Developer Onboarding

**Last updated:** June 14, 2026 (thesis pivot — trigger taxonomy retired after Phase A validation failure; architecture-prediction framing adopted)

This guide gets a new contributor from clone to running analyses to understanding what is settled vs. open. Read this first, then [`findings.md`](findings.md) for results and [`open_questions.md`](open_questions.md) for what's next.

---

## What this project is

**Great players, bad games: what does the failure look like mechanically, and can you predict it from regular-season architecture?**

A quantitative study of playoff failure modes across 31 HOF-caliber NBA players (~31,000 games). The project started as "does Harden choke?" and has evolved through three phases:

1. **Mechanism taxonomy (Screens A–E, settled):** Classified how stars fail in bad games — contraction (stop shooting) vs forcing (keep shooting inefficiently). Key finding: contraction is a stable career trait (r = 0.72) independent of failure frequency.

2. **Trigger taxonomy (Screen F, retired):** Attempted to classify *when* floor games happen based on opponent-quality terciles. Produced a 5-bucket classification (opponent-independent, scheme-dependent, disengagement, bimodal, standard). **Failed Phase A validation** (June 2026): 31% split-sample concordance, 23% gradient stability. The taxonomy is not a stable trait. Retired as primary axis; gradient signal (continuous) retained as descriptive measure.

3. **Architecture prediction (current, in progress):** Can you predict a star's playoff floor-game risk from their regular-season scoring architecture? This is where a new developer should focus.

### Current thesis

> A star's regular-season scoring architecture — how many independent modes they have, how dependent they are on getting to the line, and how their volume contracts in bad games — predicts their playoff floor-game vulnerability better than any opponent-based trigger classification.

### Key variables for the architecture model

| Variable | What it measures | Where it lives |
|---|---|---|
| **FGA retention** (RS floor games) | How much volume drops in bad games — stable trait (r = 0.72) | `retention_baselines.csv` |
| **FTA dependency** (RS FTA/FGA ratio) | How reliant the player is on getting to the line | Computable from `analysis_table.csv` |
| **Scoring mode concentration** | How many independent ways the player can score | Not yet computed — this is the next build |
| **Rim abandonment index** | Whether bad games show FTA-specific collapse (PG) or total contraction (Harden) | `retention_baselines.csv` (compare FGA vs FTA retention) |
| **FTA shift RS→PO** | Whether the player draws more or fewer fouls in the playoffs | Computable from `analysis_table.csv` — NOT a universal "whistle" effect |

### What's NOT the thesis (retired hypotheses)

- ~~"Playoffs systematically suppress free throws"~~ — 15/31 players increase FTA rate in playoffs; cohort mean shift is −0.05. LeBron, Dirk, PG, Mitchell all draw more.
- ~~"Trigger type (opponent-independent vs scheme-dependent) is a stable player trait"~~ — Failed split-sample validation. 31% concordance across career halves.
- ~~"Floor games compound late in series as opponents adapt"~~ — H2 rejected. Flat early/mid/late gradient.
- ~~"Bad games cluster in big moments"~~ — Harden's elimination-game floor rate (15%) is lower than non-elimination (23%).

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
│   ├── screen_a.py … screen_f.py   # Pass 1 screens (E settled, F retired)
│   ├── screen_a_adj.py       # Opponent-adjusted floor rates
│   ├── rs_retention_baseline.py    # RS vs PO retention baselines
│   ├── trigger_sensitivity.py      # Phase A validation (A1/A2/A3/A5)
│   ├── validate_trigger_stability.py # Phase A validation (A4 split-sample)
│   ├── scrape_team_logs.py   # Causal chain Step 0 — team ORtg
│   ├── validate_team_logs.py
│   ├── join_causal_table.py  # Causal chain Step 1 (written, needs revision)
│   ├── mechanism_descriptives.py   # Causal chain Step 2 (stub)
│   ├── visualize.py
│   └── pass2/                # Possession-level analysis (partial)
├── data/
│   ├── raw/                  # gitignored
│   ├── processed/            # gitignored
│   └── pass2_validation_games.json   # tracked fixture
├── documents/development/    # Research context (tracked)
└── output/figures/           # gitignored
```

---

## Setup

Requires Python 3.11+ (tested on 3.13).

```bash
make venv
source .venv/bin/activate
```

Data under `data/` is gitignored except `data/pass2_validation_games.json`. After clone you must scrape.

---

## Full pipeline

### 1. Scrape and validate

```bash
make scrape              # ~60 min for full 31-player cohort
make validate-scrape
```

Smoke test: `make smoke-scrape` (Harden 2023-24 only).

### 2. Features and screens

```bash
make features            # → analysis_table.csv
make screen-a            # variance shift (raw)
make screen-a-adj        # opponent-adjusted floor rates
make retention           # RS vs PO retention baselines
make screen-e            # mechanism taxonomy (settled background)
make screen-f            # trigger taxonomy (retired — reference only)
make trigger-sensitivity # Phase A validation results
```

### 3. Causal chain (Step 0 complete)

```bash
make scrape-team-logs    # ~50 min; --resume supported
make validate-team-logs
```

---

## Cohort (31 players)

Defined in `config.py`. Groups A/B are legacy — not analytically load-bearing.

| Group | Players |
|-------|---------|
| A (heliocentric) | Harden, Westbrook, Luka, Trae, Iverson, Lillard, DeRozan, Wall, CP3, LeBron, SGA, Butler, Embiid, Simmons, Brunson, Haliburton, Giannis, Jokic, Dirk, Fox |
| B (scalable/wing) | Curry, Klay, Ray Allen, Hamilton, Durant, Kobe, PG, Tatum, Harris, Kyrie, Mitchell |

### Adding a player

1. Add to `GROUP_A` or `GROUP_B` in `config.py` with `nba_id` and `bbref_id`
2. `python src/scrape.py --players "Player Name"`
3. `make features` then re-run screens

---

## Key definitions

| Term | Definition |
|------|------------|
| **Floor game** | Game Score below player's RS 15th percentile (`is_floor_primary`) |
| **FGA retention** | (FGA/36 in floor games) / (FGA/36 in non-floor games) — measures volume contraction |
| **FTA retention** | Same for free throw attempts — measures rim-attack contraction |
| **Contractor** | Volume collapses in floor games (low FGA/FTA retention) |
| **Forcer** | Volume preserved, efficiency collapses (high FGA retention) |
| **Scoring architecture** | The set of independent scoring modes a player uses (rim attacks, midrange, threes, foul drawing) |
| **Rim abandonment** | FTA-specific collapse while FGA stays stable — PG archetype |

---

## What we know (settled findings)

| Finding | Evidence | Script |
|---------|----------|--------|
| Contraction is a stable career trait | RS FGA retention predicts PO (r = 0.72) | `rs_retention_baseline.py` |
| Cohort playoff effect explained by opponent quality | `is_playoff` OR ≈ 0.98, p ≈ 0.80 | `screen_a_adj.py` |
| Harden retains +7pp adjusted floor-rate increase | Opponent-independent at full-career level | `screen_a_adj.py` |
| H2 (late-series adaptation) rejected | Flat gradient | `screen_b.py` |
| Mechanism and frequency are independent | Butler contracts like Harden, barely floors | `screen_e.py` + `screen_f.py` |
| Dirk was never a choker | PO floor rate 7.1% (vs 15% RS) | `screen_f.py` |
| "Playoff whistle" is not a universal effect | 15/31 increase FTA; cohort mean shift −0.05 | Analysis table |
| **Trigger taxonomy failed split-sample** | 31% concordance, 23% gradient stability | `validate_trigger_stability.py` |
| Threshold sensitivity OK (13% swing) | Core labels stable under perturbation | `trigger_sensitivity.py` |
| Null model: gradient signal is real | Extreme gradients exceed chance (p = 0.009) | `trigger_sensitivity.py` |
| Bayesian: 42% of players uncertain | Hard labels premature for many players | `trigger_sensitivity.py` |
| Bootstrap: 84% tercile CI overlap | Tercile-level floor rates not statistically distinguishable | `trigger_sensitivity.py` |

---

## What to build next (priority order)

### 1. Architecture-prediction model (HIGH — the new primary axis)

**Goal:** Predict playoff floor-game rate and severity from regular-season architecture.

**Script:** `src/architecture_model.py` (not yet written)

**Variables to compute for each player-season:**
- RS FGA retention (already in retention baselines)
- RS FTA/FGA ratio (FTA dependency)
- RS FTA retention (rim-abandonment indicator)
- Scoring mode concentration: what % of points come from the top-1 / top-2 scoring modes (rim, midrange, three, FT)
- RS floor-game rate (the base rate)

**Test:** Does RS architecture predict PO floor-game rate (cross-player regression) and PO floor-game severity (within-player, conditional on flooring)?

**Success criteria:** An RS-only model that predicts PO floor-game rate with R² > 0.25 across the 31-player cohort.

**Failure mode:** If RS architecture has no predictive power, the project's publishable contribution is the descriptive findings (mechanism taxonomy, trait stability, opponent adjustment, narrative debunking).

### 2. Rim abandonment vs full contraction → team outcomes

**Goal:** Test whether PG-style rim abandonment and Harden-style full contraction produce different team consequences.

**Script:** Extend `join_causal_table.py` and `mechanism_descriptives.py`

**Method:** Among floor games, does the type of contraction (FTA-specific vs total volume) predict team ORtg, controlling for individual game score? This is a narrower, more testable version of the original causal chain.

### 3. Defense as second axis

**Goal:** Add defensive vulnerability alongside offensive architecture for a two-axis risk profile.

**Variables:** On-off defensive rating, matchup-dependent exposure, defensive floor-game equivalent (if definable).

**Why:** KAT's playoff narrative flip is a defensive story, not an offensive one. Harden's is offensive. A complete risk model needs both axes.

### 4. Causal chain Steps 1–4 (architecture-framed)

Revise the causal chain plan from trigger-type → team outcomes to architecture-type → team outcomes. The data infrastructure (Step 0) is complete; the join and regression specs need updating.

---

## Phase A results (June 2026) — why the trigger taxonomy was retired

Full results in `data/processed/trigger_sensitivity.csv`, `trigger_null_model.csv`, `trigger_bayesian.csv`, `trigger_bootstrap_cis.csv`, `trigger_split_sample.csv`.

| Test | Result | Pass/Fail |
|------|--------|-----------|
| A1: Threshold sensitivity | 4/31 (13%) swing under ±0.03 | PASS |
| A2: Null model | Bimodal p=0.072; gradient signal p=0.009 | MIXED |
| A3: Bayesian | 13/31 (42%) uncertain | CAUTION |
| A4: Split-sample | **8/26 (31%) concordance** | **FAIL** |
| A5: Bootstrap CIs | 26/31 (84%) overlap | WARNING |

**The kill shot was A4.** Even Harden's gradient flips sign across career halves (+0.12 → −0.16). Zero of the 4 opponent-independent players retain their label across both halves. The tercile-level analysis is fundamentally underpowered for split-sample validation.

**What survives:** The gradient signal exists (p=0.009). Contraction is a stable trait (r=0.72). Opponent adjustment kills the aggregate effect. These are standalone findings that don't require the taxonomy.

---

## Data policy

- Do **not** commit `data/raw/`, `data/processed/`, `data/cache/`, or `output/`.
- Exception: `data/pass2_validation_games.json` is tracked.
- Regenerate locally via Makefile targets.

---

## Document index

| Read when | Document |
|-----------|----------|
| Onboarding / running code | This file + `README.md` |
| Full results | `findings.md` |
| What's decided vs. open | `open_questions.md` |
| Trigger taxonomy gaps (historical) | `CRITICAL_GAPS.md` |
| Causal chain implementation | `causal_chain_plan.md` |
| Original Pass 1 design | `pass1_plan.md` |
