# Open Questions — Status

**Date:** June 2026  
**Context:** Pass 1 complete and extended. Five pre-scaling questions from March 2026 are **resolved below**. Remaining gaps are listed at the end.

Evidence lives in [`findings.md`](findings.md). Onboarding: [`DEVELOPER.md`](DEVELOPER.md). Scripts: `src/screen_a_adj.py`, `src/rs_retention_baseline.py`, `src/pass2/event_frequency.py`.

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

### A. Causal chain to team outcomes

Does contraction → team ORtg drop → lost games? Need score-margin control at time of contraction, not just game-level floor flag.

### B. Minutes decontamination at possession level

Separate "player stops attacking" from "coach benches player." Kobe reclassification showed game-level metrics conflate these. Pass 2 possession data is the right resolution.

### C. Out-of-sample validation

Train contraction profile on career first half; test floor-rate and retention stability on second half. PG (17 PO floor games) and SGA (8) need larger samples before structural claims.

### D. Series-level defensive data

Season-average DEF_RATING is coarse. SGA's opponent-driven pattern may reflect series-specific schemes invisible in season averages.

### E. Pass 2 at scale

Run same-game pre-event baseline matching on full event set (~273 events). Parser validated; scaling is engineering, not research design.

### F. Expand cohort

Embiid, Butler, Mitchell, Booker — test whether PG/Harden opponent-independent contractor category replicates.

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
