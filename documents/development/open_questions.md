# Open Questions — Status

**Date:** June 2026 | **Last updated:** June 23, 2026 (LLM video grader rewritten with four prompt modes; event-ordering sequence prompt achieves 71% binary accuracy / 50% 3-way accuracy on Harden validation set — up from 40% / 0% with original 13-field prompt)
**Context:** Pass 1 complete and extended. Trigger taxonomy retired (Phase A). Architecture model failed (Phases B/C). FTA shift analysis (Phase E, June 17) produced r = −0.528, p = 0.002 — the project's strongest predictor. Split-half stability moderate (r = 0.45) but predictive test fails (H1 → H2 floor rate: r = −0.16). Missing variable identified: foul type (requires video classification). Five pre-scaling questions from March 2026 are resolved below.

Evidence lives in [`findings.md`](findings.md). Onboarding: [`DEVELOPER.md`](DEVELOPER.md). FTA deep-dive: `src/fta_dependency_deepdive.py`. Video plan: [`foul_type_video_plan.md`](foul_type_video_plan.md).

---

## 1. Player-specific or structural?

**Status: RESOLVED — hybrid claim**

**Decision:** Neither pure Harden case study nor pure Group A/B structural claim. The honest frame is a **failure-mode taxonomy** with structural predictors that cut across the original groups.

| Finding | Implication |
|---------|-------------|
| Group A vs B floor-rate difference not significant (*p* = 0.18, *d* = 0.72) | Heliocentric/scalable partition is a weak proxy for mechanism |
| Ray Allen (Group B) had largest raw floor-rate increase | Original structural partition fails |
| Three contractor subtypes identified | Structure matters, but via FTA dependency + opponent independence, not heliocentrism |

**Three contractor archetypes:**

| Archetype | Players | Signature |
|-----------|---------|-----------|
| **Trait contractor** | Harden | Stable RS≈PO contraction; floors opponent-independent; elevated adj. floor rate (+7pp) |
| **Rim-abandoning contractor** | Paul George | Stable FGA retention; catastrophic PO FTA collapse (54%→25%); floors opponent-independent |
| **Scheme-dependent contractor** | SGA | Hardest PO contraction (72%→53% FGA retention, n=8); floors entirely opponent-driven (*p* = 0.001) |

**Forcers** (Durant, Curry, Iverson) preserve volume; efficiency collapses.

**Paper tier:** Structural taxonomy with Harden as lead case — not Sloan-level "heliocentric systems fail" claim.

---

## 2. What is the novel contribution?

**Status: RESOLVED**

**One-sentence claim:**

> Under playoff adversity, a star's offensive structure — not psychology — determines whether they contract, force, or redistribute; contraction events are the failure mode the public misreads as "choking," and whether contraction is opponent-independent distinguishes unpredictable playoff risk (Harden, PG) from gameplan-able scheme vulnerability (SGA).

**What is novel (confirmed by data):**

1. **Failure-mode taxonomy** — contraction vs. forcing vs. mixed at game level (Screen E)
2. **Contraction is a stable trait** — RS FGA retention predicts PO FGA retention (r = 0.72, *p* < 0.001)
3. **Opponent adjustment kills aggregate playoff effect** — but Harden/PG floors persist against weak defenses
4. **Public narrative misdiagnosis** — Harden's floors are not clutch-concentrated (Screen D); elimination-game floor rate *lower* than non-elimination

**What is NOT yet novel (needs more work):**

- "Failure mode predicts series outcome" — causal chain untested
- "FTA dependency → contraction" as simple rule — SGA refutes it (highest FTA dependency, scheme-dependent)

---

## 3. Sample size — event frequency sufficient?

**Status: RESOLVED — adequate for top stars, marginal for others**

**Method:** `src/pass2/event_frequency.py` — Event A (≤1 FGM on ≥5 Q1–Q2 FGA) detected on 69-game PBP sample; projected to full cohort via box-score cross-check.

| Metric | Value |
|--------|-------|
| Event A rate (eligible players, PBP) | 14.5% |
| Event A rate (stars, effective) | ~10% per playoff game |
| Projected Event A (18-player cohort) | ~138 |
| Projected Events A + B combined | ~273 |

**Per-player power (Event A projections):**

| Tier | Players | Events |
|------|---------|--------|
| Adequate (≥10) | Harden (~14), LeBron (~16), Kobe (~12), Westbrook (~11), Ray Allen (~11), Klay (~10) | Within-player profiles feasible |
| Marginal (5–9) | Durant, Curry, CP3, PG, Iverson, Lillard, Hamilton (~8 each) | Pooled analysis only |
| Underpowered (<5) | Luka, Trae, Wall, DeRozan, SGA (~2–4) | Combine event types or expand RS sample |

**Decision:** Proceed with Pass 2 as **supporting illustration**, not primary identification. Event B (consecutive empty trips) supplements Event A for underpowered players.

---

## 4. Within-game vs. cross-game baselines?

**Status: RESOLVED — same-game pre-event primary**

**Decision:** Same-game, pre-event possession pool as primary baseline (per `pass2_design_spec.md` §3). Cross-game baseline as sensitivity check only.

**Rationale:**

- Cross-game baseline confounds adversity response with between-game variance
- Event A typically fires after 15–25 team possessions → 8+ baseline possessions available
- `baseline_underpowered` flag handles edge cases

**Open refinement (not yet implemented):** Exclude 3–5 possessions immediately preceding the event trigger from baseline pool — those possessions are part of the cold stretch, not neutral pre-event behavior.

---

## 5. Is Pass 2 necessary?

**Status: RESOLVED — supporting, not primary**

**Decision:** Pass 1 (strengthened) is the primary analysis. Pass 2 is vivid mechanism evidence.

**What Pass 1 now answers (after extensions):**

| Extension | Script | Key result |
|-----------|--------|------------|
| Opponent adjustment | `screen_a_adj.py` | Cohort playoff effect disappears (*p* = 0.83); Harden floors not opponent-explained |
| RS retention baselines | `rs_retention_baseline.py` | Harden RS≈PO contraction (−0pp FGA shift); trait not playoff invention |
| Mechanism taxonomy | `screen_e.py` | Contraction vs forcing distinguished; Kobe misclassified (minutes contamination) |
| Event frequency | `event_frequency.py` | ~273 combined events — enough for case studies |

**Pass 2 adds:** possession-level behavioral sequence after cold start (usage drop timing, redistribution collapse). Valuable for mechanism color; does not rescue borderline *p* = 0.067 on raw floor-rate shift (which opponent adjustment reframes anyway).

---

## Remaining work (not yet answered)

These block the "who to avoid in the playoffs" practical claim:

### A. Causal chain to team outcomes (revised framing)

**Step 0 complete (June 2026).** Team game logs with `OFF_RATING`, `POSS`, `WL` fetched for all cohort games; validation passed (100% join coverage, ORtg sanity OK). See [`causal_chain_plan.md`](causal_chain_plan.md).

**Framing revised (June 2026).** The original CC1–CC4 hypotheses ("floor games have lower team ORtg") were demoted to validation gates — they are mechanically obvious and not a contribution. The revised question is:

> Among floor games, does failure mechanism (contraction vs. forcing, measured continuously via per-game FGA retention) predict team ORtg, after controlling for individual performance quality?

Three hypotheses tested symmetrically:
- **H1 (contraction is worse):** Lower FGA retention → lower team ORtg. Contracted star leaves offense anchorless.
- **H2 (forcing is worse):** Lower FGA retention → *higher* team ORtg. Contraction redistributes possessions to competent teammates.
- **H3 (no difference):** Mechanism has no predictive power after controlling for `game_score`. Taxonomy is descriptive only.

Key design decisions:
- Primary sample restricted to floor games (`is_floor_primary == 1`)
- Continuous `fga_retention` per game (not binary contractor/forcer label)
- Player FE + `game_score` control to isolate within-player mechanism variation
- Reverse causality acknowledged; Pass 2 temporal ordering is the strongest available mitigation

**Still open:** Step 1 (join + per-game retention computation), Step 2 (descriptive analysis), Step 3 (regressions).

### B. Minutes decontamination at possession level

Separate "player stops attacking" from "coach benches player." Kobe reclassification showed game-level metrics conflate these. Pass 2 possession data is the right resolution.

### C. Out-of-sample validation

Train contraction profile on career first half; test floor-rate and retention stability on second half. PG (17 PO floor games) and SGA (8) need larger samples before structural claims.

### D. Series-level defensive data

Season-average DEF_RATING is coarse. SGA's opponent-driven pattern may reflect series-specific schemes invisible in season averages.

### E. Pass 2 at scale

Run same-game pre-event baseline matching on full event set (~273 events). Parser validated; scaling is engineering, not research design.

### F. Expand cohort

Embiid (done), Mitchell (done), Booker — test whether PG/Harden opponent-independent contractor category replicates. Butler (done) — revealed situational contractor archetype and mechanism–frequency independence. See [`butler_derozan_case_study.md`](butler_derozan_case_study.md).

Recent additions (June 2026, fourth wave):

| Player | Trigger | Mechanism | Why added |
|--------|---------|-----------|-----------|
| De'Aaron Fox | disengagement | mixed (36% vol) | Speed-dependent heliocentric — test whether rim-pressure guards share SGA's disengagement pattern (yes) |
| Tobias Harris | standard | shrinker (59% vol) | Secondary scorer — test scheme-dependent hypothesis (missed; his floor rate is low but contraction is catastrophic when it happens) |
| Kyrie Irving | standard | forcer (31% vol) | Clutch god narrative vs. data — test whether reputation matches trigger (no; standard trigger, forcer mechanism = sampling artifact) |
| Donovan Mitchell | bimodal | mixed (41% vol) | Bimodal riser/shrinker — test whether ceiling and floor have opposite triggers (yes; disengagement vs weak D, scheme-suppressed vs strong D) |

**Key findings from fourth wave:**

- Fox confirms the disengagement archetype extends to rim-pressure guards (not just SGA)
- Harris is the inverse of the meme: rare floors but catastrophic contraction when they happen (PO FGA retention −28pp from RS)
- Kyrie Irving's "clutch god" reputation is a highlight-reel sampling artifact — his trigger is `standard` (no opponent condition predicts floor games) and his mechanism is `forcer` (keeps shooting, efficiency collapses)
- Mitchell's bimodal trigger is the most important finding: two different triggers (disengagement vs weak D, scheme-suppressed vs strong D) require two different coaching interventions depending on opponent quality
- Mitchell's 2025-26 Cleveland runs exposed a limitation of game-level floor detection: his Toronto Games 5-7 weren't floor games by the 15th-percentile threshold but were clearly a floor series. Game Score misses sustained mediocrity.

### G. Critical structural gaps — RESOLVED (June 14, 2026)

Phase A validation executed. Gaps 3 and 1 were tested; Gap 1 failed, killing the taxonomy. Gaps 2 and 4 mooted. See [`CRITICAL_GAPS.md`](CRITICAL_GAPS.md) for full preserved briefs.

| Gap | Tested? | Result |
|-----|---------|--------|
| **3. Thresholds overfit** | Yes (A1 sensitivity, A2 null model) | **PASS** — 13% swing; gradient signal p=0.009 |
| **1. Not predictive** | Yes (A4 split-sample) | **FAIL** — 31% concordance, 23% gradient stability |
| **4. Wrong metric** | Mooted | Gap 1 failure kills taxonomy; metric reform won't save it |
| **2. No causal ID** | Mooted | Taxonomy not stable enough for causal claims |

**Verdict:** The trigger taxonomy is a descriptive finding that does not replicate across career halves. The project pivots to architecture prediction.

---

## H. Architecture prediction — Phase B results (June 14, 2026)

### H1. Box-score architecture model — FAILED (R² = 0.128)

**Script:** `src/architecture_model.py` (written and run)

**What was tested:** Career-level cross-player regression (n=31) — RS FGA retention, RS FTA/FGA ratio, HHI scoring concentration (3-mode: 2PM/3PM/FT), pct points from FT → PO floor-game rate.

**Results:**

| Variable | r vs PO floor rate | p |
|---|---|---|
| RS FTA/FGA ratio | +0.303 | 0.098 |
| % points from FT | +0.313 | 0.086 |
| RS floor rate | -0.258 | 0.162 |
| HHI scoring (3-mode) | -0.182 | 0.328 |
| RS FGA retention | -0.056 | 0.763 |
| RS FTA retention | -0.003 | 0.988 |

Full model R² = 0.128. Parsimonious (FGA retention + FTA ratio) R² = 0.095. Player-season pooled R² = 0.010.

**Why it failed:** The 3-mode HHI (2PM/3PM/FT point shares) cannot capture scoring-mode interdependence. Harden has the *lowest* HHI in the cohort (most diversified) but the highest floor rate — because his rim attacks and foul drawing are the same action. When one collapses, both collapse. HHI measures spread, not independence.

**What survives:** FTA dependency is the only marginal signal (r = +0.30, p = 0.098). Foul-dependent scorers floor more in the playoffs. FGA retention — the project's most robust finding (r = 0.72 RS→PO) — does NOT predict floor-game frequency. How you contract is stable; it doesn't predict how often.

**Output:** `data/processed/architecture_career_table.csv`, `architecture_season_table.csv`, `output/figures/architecture_career_scatter.{png,svg}`, `architecture_correlation_heatmap.{png,svg}`

### H2. Shot chart mode independence — NEXT BUILD

The box-score model's failure is a measurement problem, not a thesis problem. The thesis (mode interdependence drives floor-game vulnerability) requires per-shot zone data from `shotchartdetail` to compute:

- **HHI-5** — Herfindahl across 5 modes (Restricted Area, Paint, Mid-Range, 3PT, FT)
- **Mode independence score** — average pairwise correlation of mode shares across games
- **Tertiary mode count** — modes contributing ≥15% of scoring
- **Floor-game mode collapse** — which modes drop in floor games vs non-floor games

**Full plan:** `inbox/2026-06-14/shot-chart-integration-plan.md` (work-log repo). API endpoint verified working. ~18 min scrape for full cohort.

**Success criterion:** R² > 0.25 career-level with shot-chart variables.

**Kill:** If shot-chart architecture also fails, the project's contribution is descriptive only.

### H3. Defense as second axis

KAT's story is defensive vulnerability hidden by system — a different axis from Harden's offensive contraction. A complete risk model needs both. Integration of on-off defensive metrics alongside offensive architecture. Lower priority than H2.

### H4. "Playoff whistle" as player-specific, not universal

The cohort shows no systematic FTA decline. But individual variation is large (Harden −13%, Dirk +31%). This is subsumed by H2 — player-specific FTA shift is computable from existing box scores and is already an IV in `architecture_model.py`.

### H5. RS opponent-independence → PO floor rate (June 15, 2026) — MARGINAL, FRAGILE

**Question:** Do players who floor equally against strong and weak opponents in the RS have higher PO floor-game rates?

**Rationale:** If RS floor games are opponent-independent (flat gradient across opponent quality terciles), that suggests the player's bad games are unhideable — no system or scheme can prevent them. Opponent-dependent RS floorers (coasters who only floor vs weak D, or scheme-suppressed players who only floor vs strong D) have a lever: their floor games are conditional and potentially manageable in the playoffs.

**Method:** Compute RS opponent-gradient per player (floor_rate_vs_weak_D − floor_rate_vs_strong_D using league-wide DEF_RATING terciles). Test whether |gradient| (opponent-independence) predicts PO floor rate at career level (n=30).

**Results:**

| Test | Result |
|------|--------|
| Career-level r (n=30) | r = −0.315, p = 0.090 |
| Bootstrap 95% CI | [−0.607, +0.090] (crosses zero) |
| Binary split (flat vs steep) | +0.7pp difference, p = 0.80 |
| Without Jokic + Giannis | r = −0.120, p = 0.544 |
| Season-level (n=97) | Simpson's paradox: r = +0.222, opposite direction |

**Verdict:** Direction consistent with hypothesis but underpowered and fragile. The continuous correlation is marginal (p=0.09). The binary split is null. Removing two leverage points (Jokic, Giannis) kills the signal. Cannot confirm or reject the hypothesis.

**Status:** Open. Needs either a larger cohort or a different analytical approach (see next steps below).

### H6. Shot-chart mode_independence_score — DEAD METRIC (June 15, 2026)

**Finding:** The `mode_independence_score` computed from `shotchartdetail` data has a range of 0.315–0.340 across 31 players. All players appear equally mode-independent. The metric has no discriminative power and cannot predict PO floor rates.

**Why it failed:** Per-game zone shares are compositional (sum to 1.0 for FGA zones). When one zone share goes up, others mechanically go down, inducing negative correlations between all zone pairs. This compresses the average absolute correlation into a narrow band regardless of a player's actual scoring architecture.

**What survives from shot charts:** The mode-collapse profiles (per-mode share shift in floor vs non-floor games) are diagnostically valuable descriptively — they show *what breaks* when a player floors — even though they cannot predict *whether* a player will floor.

---

## I. Where the project stands (June 17, 2026)

### What we know (robust)

1. **FTA per-36 shift is the strongest predictor of PO floor-game rate** — r = −0.528, p = 0.002. Players who lose FTAs in playoffs floor more. Bootstrap CI excludes zero. No single player dominates (LOO max influence = 0.051).
2. **FGA and FTA co-collapse in floor games** — r = +0.428, p = 0.016. Foul-dependent scoring fails as a single action.
3. **Losing rim access costs FTAs** — RA shift → FTA shift: r = +0.521, p = 0.003. Drive shift → FTA shift: r = +0.518, p = 0.003.
4. **Combined FTA + FGA shift model explains 40% of career-level variance** — R² = 0.396, both predictors significant.
5. **FTA dependency is significant at game level** — multilevel (n=3,269): β = −0.024, p = 0.019. Base-rate risk factor (interaction with opponent quality null, p = 0.226).
6. **FTA shift is moderately stable across career halves** — split-half r = +0.451, p = 0.016. Sign concordance 79%.
7. **Contraction is a stable career trait** (r = 0.72 RS→PO FGA retention). But trait stability does not predict frequency.
8. **The cohort-wide playoff floor effect is explained by opponent quality** (p = 0.83 after adjustment).
9. **The "playoff whistle" is not universal** — 15/31 increase FTA rate; cohort mean shift −0.05. Individual variation is the signal.
10. **ICC for floor games is nearly zero (0.022)** — only 2% of floor-game variance is between-player. Floor games are overwhelmingly a game-level phenomenon.

### What we tried and killed

| Hypothesis | Method | Result | Status |
|---|---|---|---|
| Trigger taxonomy is a stable trait | Split-sample validation (Phase A) | 31% concordance | **KILLED** |
| Box-score architecture predicts PO floor rate | Career-level OLS (Phase B) | R² = 0.128 | **KILLED** |
| Shot-chart mode independence predicts PO floor rate | Career-level OLS (Phase C) | metric range 0.315–0.340, no variance | **KILLED** |
| RS opponent-independence predicts PO floor rate | Correlation + binary split (Phase D) | r = −0.315, p = 0.09; fragile | **KILLED** (Jokic/Giannis dependent) |
| RS floor rate predicts PO floor rate | Correlation | r = −0.02, p = 0.91 | **NULL** |
| RS FTA dependency predicts PO floor rate (career) | Correlation | r = +0.303, p = 0.098; Embiid dependent | **MARGINAL** |
| H1 FTA shift predicts H2 PO floor rate | Predictive split | r = −0.164, p = 0.403 | **NULL** |

### The honest assessment

The project has found a strong *descriptive* predictor (FTA shift, r = −0.53) but has not closed the *predictive* loop. The FTA shift is retrospective — you can't observe it before the playoffs happen. The trait is moderately stable (r = 0.45 split-half) but not stable enough to project forward.

The missing variable is **foul discretion**: whether a player's shooting fouls come from contact that refs always call (through-body finish, clean arm contest) or contact that refs can choose not to call (arm hooks, rip-throughs, pump-fake jump-intos). This is not measurable from box scores or PBP text — it requires video classification of shooting fouls. The PBP proxy (Option C in the original plan) is dead — shot subtype and drive-rate cannot disambiguate foul discretion (Harden drives plenty but traps arms; and-1s happen on the perimeter). See [`foul_type_video_plan.md`](foul_type_video_plan.md) and [`foul_type_classifier_plan.md`](foul_type_classifier_plan.md).

The descriptive contributions are real and publishable: FTA-FGA co-collapse mechanism, the "playoff whistle" debunking, contraction stability, mode-collapse profiles, and five honestly reported negative predictive results. The predictive claim — "can you identify which stars will lose their FTAs in advance?" — requires the foul-type classification to answer.

### What the next phase requires

1. **Foul-type video classification** — Classify shooting fouls by type using NBA.com video review data. If RS foul-type composition predicts FTA shift direction, the full chain closes: RS foul-type → predicted FTA shift → predicted PO floor risk. This is the only path to a predictive contribution. See [`foul_type_video_plan.md`](foul_type_video_plan.md).

2. **Causal chain re-specification** — The causal chain infrastructure exists but tests the wrong hypothesis (trigger type → team outcomes). Reframe around continuous FTA shift: does FTA shift predict team ORtg in floor games?

3. **Cohort expansion for stability** — 28 players in split-half test. More players would tighten the stability estimate and potentially move the predictive test from r = −0.16 to something meaningful — or confirm it's genuinely null.

---

## Decision log

| Date | Decision |
|------|----------|
| Mar 2026 | Pass 1 complete; adaptation hypothesis (H2) rejected |
| Mar 2026 | Five open questions drafted before scaling |
| Jun 2026 | Opponent adjustment run; aggregate playoff effect explained by matchup quality |
| Jun 2026 | RS retention baselines run; contraction is stable trait |
| Jun 2026 | Event frequency computed; Pass 2 feasible as illustration |
| Jun 2026 | SGA added; three-way contractor split confirmed |
| Jun 2026 | Kobe reclassified (forcer with rim abandonment, not shrinker) |
| Jun 2026 | Thesis reframed: failure-mode taxonomy + opponent independence |
| Jun 2026 | `DEVELOPER.md` added; documentation sweep for handoff |
| Jun 2026 | Causal chain Step 0: `scrape_team_logs.py` + `validate_team_logs.py`; 19,717 team-game rows; 100% join coverage |
| Jun 2026 | `causal_chain_plan.md` added; Step 1 (`join_causal_table.py`) is next |
| Jun 2026 | Causal chain revised: CC1/CC2 demoted to validation gates; primary analysis uses continuous `fga_retention` on floor games with player FE; H1/H2/H3 tested symmetrically |
| Jun 2026 | Butler added (19 players, ~22k games); situational contractor archetype identified; mechanism–frequency independence established; `screen_a_adj.py` updated to use `opponent_defrtg` column |
| Jun 2026 | Screen F (trigger classification) written; project pivoted from mechanism to trigger as primary axis; all thesis statements updated; causal chain reframed around trigger → outcomes |
| Jun 2026 | Fourth cohort wave: Fox (disengagement), Harris (standard/shrinker), Kyrie Irving (standard/forcer), Mitchell (bimodal/mixed) — 31 players total |
| Jun 2026 | Kyrie Irving: "clutch god" narrative is sampling artifact — standard trigger, forcer mechanism, no opponent condition predicts floor games |
| Jun 2026 | Donovan Mitchell: bimodal trigger confirmed — disengagement vs weak D, scheme-suppressed vs strong D; two triggers require two interventions |
| Jun 2026 | Tobias Harris: inverse of the meme — rare floors (11.1%) but catastrophic contraction (−28pp FGA retention from RS) |
| Jun 2026 | De'Aaron Fox: disengagement trigger confirmed — 30% floor rate vs weak D, 0% vs strong D; extends disengagement archetype to rim-pressure guards |
| Jun 2026 | Mitchell Toronto case study exposed Game Score limitation: Games 5-7 weren't floor games but were clearly a floor series; sustained mediocrity invisible to game-level threshold |
| Jun 2026 | Four critical structural gaps identified and documented in `CRITICAL_GAPS.md`: (1) not predictive, (2) no causal ID, (3) thresholds overfit, (4) wrong metric |
| Jun 2026 | Gap priority order established: threshold sensitivity (3) → split-sample validation (1) → composite metric (4) → causal identification (2) |
| Jun 14, 2026 | Phase A executed: `trigger_sensitivity.py` (A1/A2/A3/A5) and `validate_trigger_stability.py` (A4) |
| Jun 14, 2026 | A1 (threshold sensitivity): PASS — 13% swing, core labels stable across threshold grid |
| Jun 14, 2026 | A2 (null model): MIXED — bimodal p=0.072 (not significant), gradient signal p=0.009 (significant) |
| Jun 14, 2026 | A3 (Bayesian): CAUTION — 42% uncertain; hard labels premature for many players |
| Jun 14, 2026 | A4 (split-sample): **FAIL** — 31% concordance, 23% gradient stability; taxonomy is not a stable trait |
| Jun 14, 2026 | A5 (bootstrap CIs): WARNING — 84% weak-strong tercile CI overlap |
| Jun 14, 2026 | **Trigger taxonomy (Screen F) retired as primary axis** — failed split-sample validation |
| Jun 14, 2026 | "Playoff whistle" narrative confirmed as mostly myth — 15/31 increase FTA rate in playoffs; cohort mean shift −0.05 |
| Jun 14, 2026 | **Project pivots to architecture-prediction framing** — can RS scoring architecture predict PO floor-game risk? |
| Jun 14, 2026 | Causal chain plan needs revision from trigger-type → architecture-type framing |
| Jun 14, 2026 | `architecture_model.py` written and run — box-score model R² = 0.128, **FAIL** (below 0.25 bar) |
| Jun 14, 2026 | FTA dependency is only signal (r=+0.30, p=0.098); FGA retention (r=-0.06) and HHI-3 (r=-0.18) are null |
| Jun 14, 2026 | Diagnosis: 3-mode box-score HHI cannot capture mode interdependence; Harden is most "diversified" but most vulnerable |
| Jun 14, 2026 | `shotchartdetail` API tested — returns per-shot ACTION_TYPE, SHOT_ZONE_BASIC, GAME_ID. Verified working. |
| Jun 14, 2026 | Shot chart integration plan written: `inbox/2026-06-14/shot-chart-integration-plan.md` |
| Jun 14, 2026 | **Next build: `scrape_shot_charts.py` → `shot_chart_features.py` → extend `architecture_model.py`** |
| Jun 14, 2026 | Causal chain Steps 1-3 also run (pre-pivot framing) — infrastructure reusable but regressions test wrong hypothesis |
| Jun 14, 2026 | `join_causal_table.py` updated: adds player_gradient, rim_abandonment_index, rs_fta_shift; 21,894 joined rows |
| Jun 15, 2026 | Shot-chart architecture model run (Phase C) — `mode_independence_score` has no discriminative power (range 0.315–0.340); combined model does not improve on box-score R² = 0.128 |
| Jun 15, 2026 | Mode-collapse profiles computed: Harden's FT share *rises* 11pp in floor games (FT can't compensate for 3PT failure); contradicts "playoff whistle" narrative for Harden specifically |
| Jun 15, 2026 | RS opponent-independence → PO floor rate tested (Phase D): r = −0.315, p = 0.09 at career level; direction consistent with hypothesis but fragile (removing Jokic/Giannis kills signal) |
| Jun 15, 2026 | Binary split (flat vs steep RS gradient): +0.7pp PO floor rate difference, p = 0.80 — null |
| Jun 15, 2026 | Season-level Simpson's paradox: r = +0.222 at season level (opposite direction from career level) |
| Jun 15, 2026 | **Honest assessment: no RS-observable predictor clears a reasonable bar for predictive contribution.** FTA dependency (r=+0.30) and RS opponent-independence (r=−0.32) are marginal directional signals only. |
| Jun 15, 2026 | **Project's contribution is descriptive, not predictive.** See Section I for open questions for next developer. |
| Jun 17, 2026 | **FTA shift deep-dive (Phase E):** FTA per-36 shift (PO−RS) → PO floor rate: r=−0.528, p=0.002, bootstrap CI [−0.72, −0.28] — project's strongest finding |
| Jun 17, 2026 | FGA-FTA co-collapse confirmed: r=+0.428, p=0.016 — single-action collapse mechanism |
| Jun 17, 2026 | RA shift → FTA shift: r=+0.521, p=0.003 — losing rim access costs free throws |
| Jun 17, 2026 | Combined FTA+FGA shift model: R²=0.396 — explains 40% of career-level floor-rate variance |
| Jun 17, 2026 | Game-level multilevel model: FTA dependency β=−0.024, p=0.019 (n=3,269 games). Interaction with opponent quality null (p=0.226) — base-rate risk factor |
| Jun 17, 2026 | ICC for floor games = 0.022 — only 2% of variance is between-player; floor games are overwhelmingly game-level |
| Jun 17, 2026 | FTA shift split-half stability: r=+0.451, p=0.016; sign concordance 79% — moderately stable trait |
| Jun 17, 2026 | **Predictive test FAILS:** H1 FTA shift → H2 PO floor rate: r=−0.164, p=0.403 |
| Jun 17, 2026 | RS FTA dependency → FTA shift: r=−0.254, p=0.168 — being FTA-dependent does NOT predict losing FTAs in PO |
| Jun 17, 2026 | **Missing variable identified: foul type.** Players whose FTAs come from rim-finishing contact likely maintain FTAs (LeBron, Dirk); players whose FTAs come from perimeter foul-drawing likely lose them (Harden, Embiid). Requires video classification. |
| Jun 17, 2026 | `fta_dependency_deepdive.py` written; `fta_collapse_profiles.csv` and 4-panel figure produced |
| Jun 17, 2026 | **Project pivots to foul-type video classification as the path to predictive contribution.** See `foul_type_video_plan.md` |
| Jun 17, 2026 | **PBP proxy (Option C) killed.** Shot subtype + location cannot disambiguate foul discretion — and-1s on the perimeter, Harden arm-traps on drives. Drive-rate is similarly confounded. |
| Jun 17, 2026 | **Foul-type taxonomy revised to v2 (discretion axis).** Categories organized by observable contact mechanism (DRV-BODY, DRV-ARM, JMP-PUMP, etc.) + separate discretion tag (ALWAYS/MARGINAL/SOUGHT) + location. Alpha test is whether `sought%` differs between Harden and Giannis. See `foul_type_classifier_plan.md` |
| Jun 17, 2026 | **`videoeventsasset` API verified working.** Returns direct 960x540 MP4 URLs for any play event. `videodetailsasset` (wrong endpoint) returns 500. |
| Jun 17, 2026 | **Foul-type classifier tool spec complete.** `foul_type_classifier_plan.md` — keyboard-driven HTML classification tool. Two Python scripts: scraper (manifest) + classifier (HTML). Alpha test: Harden vs Giannis, 5 RS games each, ~80 clips. |
| Jun 23, 2026 | **LLM video grader built** (`src/foul_type_llm_grader.py`). Automated timing classification (BEFORE/DURING/AFTER) using multimodal LLMs. Supports Gemini, OpenAI, Anthropic, and Vertex AI (gcloud ADC, no API key needed). Vertex provider uses GCS bucket with 1-day auto-delete for temporary video uploads. |
| Jun 23, 2026 | **Makefile targets added** for all LLM grader providers: `foul-type-llm-*` (Gemini), `foul-type-vertex-*` (Vertex AI). |
| Jun 23, 2026 | **LLM grader prompt engineering:** Original 13-field observation prompt produced degenerate output (all 20 clips → DURING, 40% binary accuracy). Root causes: (1) `thinkingBudget: 0` disabled reasoning, (2) 13-field schema with cross-reference rules caused cognitive overload, (3) freeze-frame state classification ("is the ball on the release path?") is harder than temporal event ordering. |
| Jun 23, 2026 | **Three new prompt modes added:** 3-field observation (collapsed schema: who_initiated, ball_state_at_contact, arm_geometry), direct-timing (model outputs BEFORE/DURING/AFTER directly), event-ordering sequence (model identifies observable events and their temporal order). Legacy 13-field retained via `--legacy-prompt`. |
| Jun 23, 2026 | **Few-shot support added** (`--few-shot`): uploads 2-3 labeled video clips from ground truth as examples in the prompt. Gemini/Vertex only (requires native video upload). |
| Jun 23, 2026 | **`thinkingBudget: 0` removed** from Vertex AI — Gemini 3.5 Flash is a reasoning model; zero budget forced pattern-matching. `maxOutputTokens` raised from 512 → 8192 to accommodate thinking + JSON output. |
| Jun 23, 2026 | **Validation results (Harden, 20 clips, Vertex AI gemini-3.5-flash):** Legacy 13-field: 40% binary, 0% 3-way (degenerate output). 3-field observation: 50% binary, 25% 3-way. Event-ordering sequence: **71% binary, 50% 3-way**. Sequence prompt dramatically improved BEFORE detection (0/11 → 7/11) by replacing freeze-frame state classification with temporal event ordering. Remaining errors are genuine BEFORE/DURING boundary calls where arm-extend timing is ambiguous. |
