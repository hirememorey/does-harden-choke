# Open Questions — Status

**Date:** June 2026 | **Last updated:** June 14, 2026 (trigger taxonomy retired; architecture-prediction pivot)
**Context:** Pass 1 complete and extended. Trigger taxonomy (Screen F) completed Phase A validation and **failed split-sample** — retired as primary axis. Project pivoting to architecture-prediction framing. Five pre-scaling questions from March 2026 are resolved below. Critical gaps resolved by Phase A testing. New next steps at the end.

Evidence lives in [`findings.md`](findings.md). Onboarding: [`DEVELOPER.md`](DEVELOPER.md). Phase A scripts: `src/trigger_sensitivity.py`, `src/validate_trigger_stability.py`.

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

## H. New next steps — Architecture prediction (June 14, 2026)

The project's new primary question: **Can you predict a star's playoff floor-game risk from their regular-season scoring architecture?**

### H1. Architecture-prediction model (HIGH PRIORITY)

**Script:** `src/architecture_model.py` (not yet written)

Compute per player-season:
- RS FGA retention in floor games (already computed)
- RS FTA/FGA ratio (FTA dependency)
- RS FTA retention in floor games (rim-abandonment indicator)
- Scoring mode concentration (% of points from top-1/top-2 modes)
- RS floor-game rate (base rate)

**Test:** Cross-player regression — do RS architecture variables predict PO floor-game rate and severity?

**Success:** R² > 0.25 across 31 players. Partial effects interpretable.

**Failure:** If RS architecture has no predictive power, the project's contribution is descriptive only (mechanism taxonomy, trait stability, opponent adjustment, narrative debunking).

### H2. Rim abandonment vs full contraction → team outcomes

Among floor games, does contraction type (FTA-specific vs total volume) predict team ORtg controlling for individual game score? This is a narrower, testable version of the causal chain.

### H3. Defense as second axis

KAT's story is defensive vulnerability hidden by system — a different axis from Harden's offensive contraction. A complete risk model needs both. Integration of on-off defensive metrics alongside offensive architecture.

### H4. "Playoff whistle" as player-specific, not universal

The cohort shows no systematic FTA decline. But individual variation is large (Harden −13%, Dirk +31%). Test whether player-specific RS→PO FTA shift predicts floor-game rate as an architecture variable.

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
