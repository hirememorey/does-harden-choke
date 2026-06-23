# Developer Onboarding

**Last updated:** June 23, 2026 (LLM video grader built with Vertex AI support; `foul_type_llm_grader.py` supports Gemini, OpenAI, Anthropic, and Vertex providers)

This guide gets a new contributor from clone to running analyses to understanding what is settled vs. open. Read this first, then [`findings.md`](findings.md) for results and [`open_questions.md`](open_questions.md) for what's next.

---

## What this project is

**Great players, bad games: what does the failure look like mechanically, and can you predict it from regular-season architecture?**

A quantitative study of playoff failure modes across 31 HOF-caliber NBA players (~31,000 games). The project started as "does Harden choke?" and has evolved through three phases:

1. **Mechanism taxonomy (Screens A–E, settled):** Classified how stars fail in bad games — contraction (stop shooting) vs forcing (keep shooting inefficiently). Key finding: contraction is a stable career trait (r = 0.72) independent of failure frequency.

2. **Trigger taxonomy (Screen F, retired):** Attempted to classify *when* floor games happen based on opponent-quality terciles. Produced a 5-bucket classification (opponent-independent, scheme-dependent, disengagement, bimodal, standard). **Failed Phase A validation** (June 2026): 31% split-sample concordance, 23% gradient stability. The taxonomy is not a stable trait. Retired as primary axis; gradient signal (continuous) retained as descriptive measure.

3. **Architecture prediction (dead) → Foul-type video classification (current):** The predictive path forward is foul discretion — classifying shooting fouls by whether the contact is always-called or marginally-called. This requires video review. Tool spec complete; manual classifier and LLM grader both built. See [`foul_type_classifier_plan.md`](foul_type_classifier_plan.md).

### Current thesis

> A star's regular-season scoring architecture — how many independent modes they have, how dependent they are on getting to the line, and how their volume contracts in bad games — predicts their playoff floor-game vulnerability better than any opponent-based trigger classification.

**Update (June 15, 2026):** The predictive claim above has been tested and failed. Shot-chart mode independence has no discriminative power. RS opponent-independence marginally predicts PO floor rate (r = −0.32, p = 0.09) but the signal is fragile. The honest contribution is **descriptive**, not predictive. See Section I of `open_questions.md` for the full assessment and open questions.

**Update (June 17, 2026):** The FTA shift deep-dive (Phase E) produced the project's strongest finding (r = −0.53, p = 0.002). The predictive loop doesn't close because FTA shift is retrospective. The path forward is **foul-type video classification** — classifying shooting fouls by discretion (always-called vs marginally-called vs sought) to see if RS foul-discretion composition predicts FTA shift direction. Tool spec is in [`foul_type_classifier_plan.md`](foul_type_classifier_plan.md). The `videoeventsasset` API is verified working.

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
│   ├── foul_type_scraper.py        # PBP filter + video URL fetcher → manifest JSON
│   ├── foul_type_classifier.py     # Manifest JSON → classification HTML tool
│   ├── foul_type_llm_grader.py     # Multimodal LLM video grading (Gemini/OpenAI/Anthropic/Vertex)
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
| **Box-score architecture model failed (R² = 0.128)** | Below 0.25 bar; HHI-3 can't capture mode interdependence | `architecture_model.py` |
| FTA dependency is only architecture signal | r = +0.30, p = 0.098 vs PO floor rate (marginal) | `architecture_model.py` |
| FGA retention does not predict frequency | r = -0.06, p = 0.76 — stable trait that doesn't predict when floors happen | `architecture_model.py` |
| **Shot-chart mode_independence_score is dead metric** | Range 0.315–0.340 across 31 players; no discriminative power | `shot_chart_features.py` |
| **Mode-collapse profiles are descriptively diagnostic** | Harden: 3PT share −11pp, FT share +11pp in floor games — FT can't compensate | `shot_chart_features.py` |
| **RS opponent-independence marginally predicts PO floor rate** | r = −0.315, p = 0.09; fragile (remove Jokic/Giannis → r = −0.12) | Ad-hoc analysis (June 15) |
| **Binary split (flat vs steep RS gradient) is null** | +0.7pp PO floor rate difference, p = 0.80 | Ad-hoc analysis (June 15) |

---

## What to build next

### Foul-type video classification tool (priority 1)

The project's path to a predictive contribution. See [`foul_type_classifier_plan.md`](foul_type_classifier_plan.md) for the full spec.

**Built (June 17, 2026):**
1. `src/foul_type_scraper.py` — Filters PBP for shooting fouls drawn by a target player, fetches video URLs via `videoeventsasset` API, builds a clip manifest JSON
2. `src/foul_type_classifier.py` — Generates a self-contained HTML classification tool from a manifest JSON

**Alpha test ready:** Harden (20 clips, 5 RS games 2019-20) and Giannis (16 clips, 5 RS games 2023-24). Run `make foul-type-serve` and open the classifier HTML files. If `sought%` is dramatically different between Harden and Giannis → proceed to full sample. If similar → kill the foul-type hypothesis.

**Run the alpha test:**
```bash
make foul-type-alpha     # scrape + classify for both players
make foul-type-serve     # start local server
# Open http://localhost:8080/foul_type_classifier_james_harden.html
# Open http://localhost:8080/foul_type_classifier_giannis_antetokounmpo.html
```

### LLM video grader (built June 23, 2026)

Automated timing classification (BEFORE/DURING/AFTER) of shooting fouls from video clips using multimodal LLMs. Supplements the manual classifier by grading the timing axis automatically.

**Script:** `src/foul_type_llm_grader.py`

**Providers:**

| Provider | Model | Auth | Video handling |
|----------|-------|------|---------------|
| **Vertex AI** (recommended) | `gemini-2.5-flash` | gcloud ADC (no API key) | Native video upload via GCS |
| Gemini | `gemini-2.5-flash` | `GEMINI_API_KEY` env var | Native video upload |
| OpenAI | `gpt-5.4-mini` | `OPENAI_API_KEY` env var | Frame extraction (3fps, 15 frames) |
| Anthropic | `claude-sonnet-4-6` | `ANTHROPIC_API_KEY` env var | Frame extraction (2fps, 10 frames) |

**Vertex AI setup (no API key needed):**
1. Install [gcloud CLI](https://cloud.google.com/sdk/docs/install)
2. Run `gcloud auth application-default login`
3. Set project: `gcloud config set project <PROJECT_ID>`
4. The grader uses a GCS bucket (`project-3984c931-3755-423f-966-foul-type-grader-tmp`) with 1-day auto-delete for temporary video uploads

**Run the LLM grader:**
```bash
# Vertex AI (recommended — no API key needed)
make foul-type-vertex-harden           # Harden RS
make foul-type-vertex-validate-harden  # validate against manual ground truth

# Gemini API (requires GEMINI_API_KEY)
make foul-type-llm-harden

# OpenAI / Anthropic (requires respective API keys)
PYTHONPATH=. .venv/bin/python src/foul_type_llm_grader.py --player "James Harden" --provider "openai" --model "gpt-5.4-mini"
PYTHONPATH=. .venv/bin/python src/foul_type_llm_grader.py --player "James Harden" --provider "anthropic" --model "claude-sonnet-4-6"
```

**Output:** `data/processed/foul_type_llm_results_{player_slug}.json` — per-clip timing predictions with confidence and reasoning, plus validation analytics against manual ground truth when available.

**Key technical notes:**
- The LLM grader currently classifies only the **timing** axis (BEFORE/DURING/AFTER). Mechanism, body part, severity, and location still require the manual classifier HTML tool.
- Gemini/Vertex use native video upload (best temporal precision). OpenAI and Anthropic use extracted frames (lower temporal resolution).
- `--validate-only` restricts grading to clips with manual ground truth in `foul_type_classifications.csv` for accuracy benchmarking.
- `--limit N` caps grading to the first N clips (useful for cost control and testing).

**Key technical notes:**
- `videoeventsasset` API (NOT `videodetailsasset`, which returns 500) returns direct MP4 URLs
- Use 960x540 resolution (`murl` field) — good enough for arm/body distinction
- PBP `actionNumber` (NOT `actionId`) maps to `GameEventID` in the video API (verified across multiple games)
- Three-axis classification: mechanism (what you see) + discretion (why the whistle blew) + location (where it happened)
- Classifier HTML must be served via `http://localhost` (not `file://`) because NBA CDN has no CORS headers

### Decision point: descriptive or predictive?

This project has tested four predictive hypotheses and failed to clear a reasonable bar on any of them:

| Phase | Hypothesis | Result |
|-------|-----------|--------|
| A | Trigger taxonomy is a stable trait | KILLED (31% split-sample concordance) |
| B | Box-score architecture predicts PO floor rate | KILLED (R² = 0.128) |
| C | Shot-chart mode independence predicts PO floor rate | KILLED (metric has no variance) |
| D | RS opponent-independence predicts PO floor rate | MARGINAL (r = −0.32, p = 0.09, fragile) |

The next developer should decide whether to:
- **(A) Pursue the marginal signal** — try to extract more from the RS opponent-independence finding with better methods (multilevel models, different DVs, expanded cohort)
- **(B) Accept the descriptive contribution** — write up what we have (contraction stability, mechanism–frequency independence, opponent adjustment, mode-collapse profiles, "playoff whistle" debunking) as a descriptive study
- **(C) Pivot to a new question** — e.g., "when stars floor, what breaks?" (mode-collapse profiles as primary), or coasting as a qualitative framework

### Option A: Pursue the marginal signal

| Step | What | Why |
|------|------|-----|
| 1 | Game-level multilevel model: `is_floor ~ rs_gradient + opponent_defrtg + (1|player)` on PO games | Uses full ~8000 PO games instead of 30 career averages; handles player-level uncertainty better |
| 2 | Try different DVs: PO FGA retention shift, PO mean Game Score, PO Game Score variance | PO floor rate is noisy (30–300 PO games); more stable DVs might show clearer signal |
| 3 | Expand cohort below HOF tier to ~60–80 players | Would need r ≈ −0.32 to clear p < 0.01 at n = 80; marginal but feasible if signal is real |

### Option B: Descriptive contribution (recommended if Option A fails)

| Step | What | Why |
|------|------|-----|
| 1 | Formalize mode-collapse profiles as the primary contribution | Per-mode collapse tables (Harden: 3PT −11pp / FT +11pp; Klay: 3PT −14pp / nothing absorbs; Embiid: RA −6pp / FT +6pp) are coaching-actionable and descriptively novel |
| 2 | Write up the "FT can't compensate" finding | Foul-dependent players (Harden, Embiid) lean on FT in floor games but FT alone can't carry offense — this contradicts the "playoff whistle" narrative for these players specifically |
| 3 | Document the negative predictive results honestly | Four failed hypotheses are themselves a contribution — the field should know that RS observables don't predict PO floor-game risk at usable precision |

### Option C: New questions

| Question | Approach | Data needed |
|----------|----------|-------------|
| What breaks when stars floor? | Mode-collapse profiles as primary axis; qualitative case studies | Already computed in `shot_chart_architecture.csv` |
| Can coasting be de-risked by team composition? | Case studies: Jokic (coaster, championship), Giannis (coaster, championship), Butler (coaster, Finals runs) | Existing data + team-level context |
| Is floor-game variance itself a trait? | Cross-player comparison of Game Score variance in RS vs PO | Existing `analysis_table.csv` |

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
| Shot chart integration plan | `inbox/2026-06-14/shot-chart-integration-plan.md` (work-log repo) |
| Trigger taxonomy gaps (historical) | `CRITICAL_GAPS.md` |
| Causal chain implementation | `causal_chain_plan.md` |
| Foul-type video classification (scoping) | `foul_type_video_plan.md` |
| Foul-type classifier tool (build spec) | `foul_type_classifier_plan.md` |
| Original Pass 1 design | `pass1_plan.md` |
