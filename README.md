# does-harden-choke

**Great players, bad games: what does the failure look like mechanically, and can you predict it from regular-season architecture?**

## What this project is

A quantitative study of playoff failure modes across 31 HOF-caliber NBA players (~31,000 games). The original question was "does Harden choke?" The answer turned out to be more interesting than yes or no.

### What we found (settled)

1. **Contraction is a stable career trait** (r = 0.72). How a player's volume drops in bad games is consistent RS-to-PO. Harden contracts the same way in January as in May.

2. **The cohort-wide "playoff effect" is explained by opponent quality.** After adjustment, there is no systematic increase in floor games in the playoffs (p = 0.83). But individual players (Harden +7pp, Embiid +14pp) retain elevated rates after adjustment.

3. **Mechanism (contraction vs forcing) and frequency (how often bad games occur) are independent.** Butler contracts like Harden but barely floors. Two players can fail the same way at completely different rates.

4. **The "playoff whistle" narrative is mostly a myth** in this cohort. 15/31 players increase FTA/36 in the playoffs; 16/31 decrease. Cohort mean shift: −0.05. LeBron, Dirk, Brunson, Mitchell, Paul George all draw MORE free throws. Harden's −13% decline is real but not rare — Luka, Embiid, Butler show comparable drops.

5. **Harden's floor games are not clutch-concentrated.** His elimination-game floor rate (15%) is *lower* than non-elimination (23%). Bad games don't cluster in big moments. The "choke" narrative is a misdiagnosis.

6. **Dirk was never a choker.** PO floor rate 7.1% (vs 15% RS). FGA retention 94%. The 2011 championship didn't require Dirk to change — the team around him improved.

### What we tried and killed (honest negative results)

- **H2 (within-series adaptation):** Rejected. Floor games don't compound as a series progresses.
- **Leverage concentration:** Rejected. Bad games don't cluster in high-leverage moments.
- **The 5-bucket trigger taxonomy** (opponent-independent / scheme-dependent / disengagement / bimodal / standard): **Failed split-sample validation.** Phase A testing (June 2026) showed 31% concordance across career halves, 23% gradient stability. The categorical labels are not stable traits. The taxonomy is retired as a primary axis; the gradient signal (continuous opponent-sensitivity) survives as a descriptive measure.

### The current thesis (June 2026 pivot)

The trigger taxonomy was a productive dead end — it produced the right questions but the wrong vessel. The project now pivots to a predictive, architecture-first frame:

> **Can you predict a star's playoff floor-game risk from their regular-season scoring architecture?**

The key variables are:
- **Scoring mode count:** How many independent ways can this player score? Harden has two pillars (foul baiting + step-back threes); when both collapse, he has no tertiary mode. Durant has three (midrange + driving + threes). Players with fewer modes are more vulnerable.
- **FGA retention as stable trait:** RS floor-game volume retention predicts PO floor-game volume retention (r = 0.72). This is measurable before the playoffs start.
- **Rim abandonment vs full contraction:** PG keeps shooting but stops getting to the line (FTA retention 54%→25%). Harden contracts everything at once. Different failure architectures, different team consequences.
- **Defense as a second axis:** KAT's defensive vulnerability (can't anchor, gets played off the floor) is hidden by the Knicks' elite defense. Offensive architecture and defensive floor are two independent risk dimensions.

### The KAT/Dirk question

The 2025 NBA Finals discourse argues KAT "shed the loser label." But KAT didn't fundamentally change — the Knicks' elite defense hides his floor weaknesses. Harden is the opposite case: you can't build a system solution for a failure mode you can't predict. Dirk proves the narrative flip is almost always a system change, not a player change.

**Status (June 2026):** Pass 1 complete and extended. Trigger taxonomy Phase A validation complete (taxonomy retired). Box-score architecture model failed (R² = 0.128). Shot-chart mode_independence_score has no discriminative power (range 0.315–0.340). RS opponent-independence marginally predicts PO floor rate (r = −0.32, p = 0.09) but signal is fragile. FTA shift deep-dive (Phase E, June 17) produced the project's strongest finding: FTA per-36 shift → PO floor rate r = −0.53, p = 0.002. Predictive test fails (r = −0.16) because FTA shift is retrospective. **The path to a predictive contribution is foul-type video classification** — see `foul_type_classifier_plan.md`. The `videoeventsasset` API is verified working.

**Start here:** [`documents/development/DEVELOPER.md`](documents/development/DEVELOPER.md) to onboard and run the pipeline. [`documents/development/findings.md`](documents/development/findings.md) for full results. [`documents/development/open_questions.md`](documents/development/open_questions.md) for what's decided and what's next.

## Documents

| Document | Covers |
|----------|--------|
| [`DEVELOPER.md`](documents/development/DEVELOPER.md) | **Onboarding** — setup, pipeline, cohort, what's done vs. open |
| [`findings.md`](documents/development/findings.md) | Full results — Pass 1 screens A–E, extensions, trigger taxonomy (retired), Phase A validation |
| [`open_questions.md`](documents/development/open_questions.md) | Resolved decisions, architecture-prediction next steps |
| [`foul_type_classifier_plan.md`](documents/development/foul_type_classifier_plan.md) | **Foul-type classifier tool** — build spec for video classification |
| [`foul_type_video_plan.md`](documents/development/foul_type_video_plan.md) | Foul-type scoping document — why video, taxonomy, data sources |
| [`CRITICAL_GAPS.md`](documents/development/CRITICAL_GAPS.md) | Trigger taxonomy gaps — **resolved by Phase A testing (taxonomy failed)** |
| [`causal_chain_plan.md`](documents/development/causal_chain_plan.md) | Causal chain Steps 0–4 (Step 0 complete); needs revision for architecture framing |

Root level is **runtime** (Makefile, `config.py`, `src/`). `documents/development/` is **research context**.

## Cohort (31 players)

Defined in `config.py`. Groups A/B are legacy structure — not analytically load-bearing.

- **Group A** (20): Harden, Westbrook, Luka, Trae, Iverson, Lillard, DeRozan, Wall, CP3, LeBron, SGA, Butler, Embiid, Simmons, Brunson, Haliburton, Giannis, Jokic, Dirk, Fox
- **Group B** (11): Curry, Klay, Ray Allen, Hamilton, Durant, Kobe, PG, Tatum, Harris, Kyrie, Mitchell

## Setup

Requires Python 3.11+ (tested on 3.13).

```bash
make venv
source .venv/bin/activate
```

## Pipeline

```bash
make scrape              # → data/raw/*.csv  (NBA Stats API; ~60 min full cohort)
make validate-scrape
make features            # → data/processed/analysis_table.csv
make screen-a            # floor-game rates (raw)
make screen-b            # within-series gradient
make screen-c            # group comparisons
make screen-e            # mechanism taxonomy (resolved background)
make screen-f            # trigger taxonomy (retired — run for reference only)
make screen-a-adj        # opponent-adjusted floor rates
make retention           # RS vs PO retention baselines
make visualize           # → output/figures/
make trigger-sensitivity # Phase A validation (sensitivity + null model + Bayesian + bootstrap)
```

Causal chain (Step 0 complete, Steps 1–3 runnable):
```bash
make scrape-team-logs    # → data/raw/team_game_logs.csv (~50 min)
make validate-team-logs
make causal-chain        # join + descriptives + regressions (pre-pivot framing)
```

Architecture prediction (box-score version done, shot charts next):
```bash
make architecture-model  # box-score architecture → PO floor rate (R²=0.128 — FAIL)
# NOT YET IMPLEMENTED:
# make scrape-shot-charts  # → data/raw/shot_charts.csv (~18 min)
# make validate-shot-charts
# make shot-chart-features # → data/processed/shot_chart_architecture.csv
```

Or `make all` after scrape (screens A–C + visualize).

## What to do next

The project has found a strong descriptive predictor (FTA shift, r = −0.53) but the predictive loop doesn't close because FTA shift is retrospective. The path forward is **foul-type video classification** — classifying shooting fouls by discretion (always-called vs marginally-called vs sought) to test whether RS foul-discretion composition predicts FTA shift direction.

See [`foul_type_classifier_plan.md`](documents/development/foul_type_classifier_plan.md) for the full build spec. Alpha test: Harden vs Giannis, ~80 clips.

If foul-type classification also fails, the project's honest contribution is descriptive:
1. FTA-FGA co-collapse mechanism
2. Contraction stability (r = 0.72)
3. "Playoff whistle" debunking (15/31 increase FTA)
4. Mode-collapse profiles
5. Five honestly reported negative predictive results

## Data policy

Everything under `data/` is gitignored **except** `data/pass2_validation_games.json`. Regenerate with Makefile targets; do not commit CSVs.
