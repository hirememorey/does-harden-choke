# Critical Gaps — RESOLVED (June 14, 2026)

**Date:** June 2026 | **Resolved:** June 14, 2026
**Status:** **Phase A testing complete. The trigger taxonomy failed split-sample validation (Gap 1) and is retired as the primary axis.** The project has pivoted to an architecture-prediction framing. This document is preserved for historical reference. See `DEVELOPER.md` for current next steps.

**Phase A Results Summary:**
- Gap 3 (threshold sensitivity): PASS — 13% swing rate, core labels stable
- Gap 1 (split-sample): **FAIL — 31% concordance, 23% gradient stability**
- Gap 4 (composite metric): Mooted by Gap 1 failure
- Gap 2 (causal identification): Mooted by Gap 1 failure

The trigger taxonomy (Screen F) is a descriptive finding that did not survive validation. These four structural problems were identified and the first two were tested. Gap 1 failure killed the taxonomy as a predictive tool. Each gap is preserved below as a self-contained brief for reference.

---

## Gap 1: The Taxonomy Is Descriptive, Not Predictive

### Problem

Screen F classified 31 players into trigger buckets after observing all their playoff data. We have no evidence these types are stable — whether a player classified `opponent-independent` on their full career would get the same label on the first half. Without split-sample validation, the taxonomy is a categorization of observed data, not a finding about player behavior.

### What Sloan will ask

"Can you predict a player's trigger type before it manifests? If I give you a player's first 50 playoff games, can you tell me their trigger classification, and does it hold on games 51+?"

### What to build

**Script:** `src/validate_trigger_stability.py`

**Method:**
1. For each player with ≥40 playoff games (Harden, LeBron, Kobe, CP3, Ray Allen, Westbrook, Durant, Curry, Klay, Butler, Dirk, Tatum, Mitchell, Giannis, Jokic — ~15 players), split career into first half and second half by game date.
2. Run `screen_f.py`'s `compute_trigger_profile()` and `classify_trigger()` on each half independently.
3. Report: does the trigger type match across halves? Build a concordance table.
4. Compute confidence intervals on tercile floor rates via bootstrap (resample games within each tercile, recompute floor rate 1000x, report 95% CI). Flag players whose tercile CIs overlap — they may be misclassified.
5. Run a null model: generate synthetic floor-game assignments by randomly permuting `is_floor_primary` within each player's playoff games (preserving overall floor rate), then run the full Screen F pipeline. How many players end up in "bimodal" by chance? How many show gradient ≥ 0.15? This tells you whether the taxonomy finds more structure than random noise.

**Success criteria:**
- ≥70% of players with ≥40 PO games retain trigger classification across halves
- Null model produces fewer bimodal/opponent-independent classifications than the real data (p < 0.05)
- Tercile floor-rate CIs for classified players do not cross zero gradient (for scheme-dependent/disengagement) or do not overlap between weak and strong (for opponent-independent/bimodal)

**Failure mode:** If trigger types are unstable across halves or the null model produces similar structure, the taxonomy is overfit to this cohort and not a generalizable finding. The paper would need to be reframed as "exploratory observation" rather than "discovery."

---

## Gap 2: No Causal Identification

### Problem

The thesis is about *triggers* — what causes floor games. But we have zero causal evidence. We observe correlations between opponent quality terciles and floor rates, then narrate them as triggers. The confound is massive: elite defenses tend to belong to elite teams, which tend to have elite offenses, which means the player's team is also scoring less, which means fewer assists, worse +/-, etc. We cannot distinguish "elite defense causes Mitchell to floor" from "elite teams create conditions where everyone on the other team looks bad."

### What Sloan will ask

"You're calling these 'triggers' but you have no instrument. What makes this causal and not just correlation with opponent quality — which itself correlates with team quality, roster construction, coaching, and a dozen other things?"

### What to build

This requires two complementary approaches:

**A. Game-level causal chain (extends existing `causal_chain_plan.md`):**

The existing causal chain plan (Steps 1-4) tests whether trigger type predicts team outcomes *controlling for* individual performance. This addresses a different question (do floor games *matter*) but the same pipeline is needed. The key addition for causal identification:

1. **Opponent quality controls at game level**, not season level. Currently we use season-average DEF_RATING. This must be replaced with or supplemented by game-level opponent defensive metrics (available from `teamgamelogs` Advanced endpoint: opponent's season DEF_RATING is a start, but game-level defensive rating would be better). This is the single most important data improvement for the causal claim.

2. **Team quality fixed effects.** Add team-season FE to the causal chain regressions. This absorbs all stable team-level confounds (roster quality, coaching, system). The identifying variation becomes within-team-season: across games in the same season by the same team, does trigger type still predict outcomes?

3. **Instrument attempt.** The strongest available instrument is opponent defensive *scheme type* (switch-heavy vs. drop vs. blitz), which affects different players differently. This is hard to get from public data but could be proxied by opponent steal rate (switch teams generate more steals) or opponent block rate (drop teams generate more blocks). Not a clean instrument, but directionally useful.

**B. Possession-level temporal ordering (Pass 2):**

This is the strongest available causal argument in observational data. If we can show that:
- Event A fires (star goes cold) → star's usage drops → team ORtg changes

...rather than:
- Team offense collapses → star reduces usage

...then reverse causality is less plausible. The existing Pass 2 infrastructure (`src/pass2/`) is built for this. It needs to be scaled from 3 validation games to the full event set (~273 projected).

**Priority order:** Run A first (it uses existing game-level data). B is essential for the paper but is engineering-scale work.

---

## Gap 3: Classification Thresholds Are Overfit by Construction

### Problem

`screen_f.py`'s `classify_trigger()` uses hard-coded thresholds that were tuned to produce the current taxonomy on this cohort:
- `gradient <= -0.15` for scheme-dependent
- `gradient >= 0.15` for disengagement
- `weak_floor > max(po_floor + 0.05, 0.20)` and `strong_floor > 0.10` for opponent-independent
- `weak_floor > avg_floor + 0.05 and strong_floor > avg_floor + 0.05` for bimodal

Change those thresholds and players move between buckets. The bimodal category is especially fragile — with 27-81 playoff games per player and tercile splits giving 9-27 games per bucket, the confidence intervals on those floor rates are ±15-20pp. Five of 31 players landing in "bimodal" is roughly what you'd expect from noise.

### What Sloan will ask

"How sensitive are your classifications to threshold choice? What happens if you use gradient >= 0.10 instead of 0.15? Show me a sensitivity analysis."

### What to build

**Script:** `src/trigger_sensitivity.py`

**Method:**
1. Parameterize the `classify_trigger()` thresholds. Create a config dict with all current thresholds as defaults.
2. Run Screen F with threshold variations:
   - Gradient thresholds: 0.10, 0.12, 0.15, 0.18, 0.20
   - Weak-floor elevation: 0.15, 0.20, 0.25
   - Bimodal elevation over average: 0.03, 0.05, 0.08
3. For each parameter combination, report:
   - How many players change classification
   - Which specific players are "swing" players (change classification under small threshold perturbations)
   - Whether the five trigger types still emerge as natural clusters or merge/collapse
4. Plot: heatmap of player (y) vs. gradient threshold (x), colored by trigger type. This is the key figure for showing which players are robustly classified and which are threshold-dependent.
5. Bayesian alternative: instead of hard thresholds, model each player's floor rate in each tercile as a draw from a Beta distribution. Compute posterior probability of each trigger type. Report posterior probabilities rather than point classifications. Players with <70% posterior probability of any single trigger type are "uncertain" — this replaces the hard classification with a probabilistic one.

**Success criteria:**
- ≥80% of players retain classification under ±0.03 threshold perturbation
- Bimodal category is not an artifact of the specific 0.05pp elevation threshold
- Bayesian posterior analysis shows the same five clusters emerge naturally

**Failure mode:** If small threshold changes reclassify many players, the taxonomy is an artifact of the specific numbers chosen. The paper would need to present probabilistic classifications rather than hard labels.

---

## Gap 4: Game Score Is the Wrong Metric for the Question

### Problem

Game Score is offense-only, designed as a box-score summary, not a performance diagnostic. It cannot distinguish "bad because shots didn't fall" from "bad because the player checked out" from "bad because the scheme took away their role" — which is exactly the distinction the trigger taxonomy claims to make. A player who plays elite defense but scores below their 15th percentile is classified as having a floor game. The Mitchell Toronto case study exposed this directly: Games 5-7 weren't "floor games" but they were clearly a floor series. The threshold misses sustained mediocrity that kills teams.

### What Sloan will ask

"You're building a trigger taxonomy on a metric that can't detect the phenomenon you're studying. Game Score doesn't capture defense, engagement, or role execution. Why should we trust floor-game classifications derived from it?"

### What to build

**A. Composite floor-game metric:**

**Script:** `src/composite_floor_metric.py`

Define a new metric that captures multiple dimensions of floor-game behavior:

```
floor_index = weighted combination of:
  1. Game Score (offensive production) — weight ~0.4
  2. FTA/FGA ratio relative to RS baseline (engagement proxy) — weight ~0.2
  3. Usage rate drop relative to RS baseline (role execution) — weight ~0.2
  4. Plus/minus relative to RS baseline (team impact) — weight ~0.2
```

The weights should be determined by PCA on the normalized components, not hand-tuned. Run PCA on the four components across all RS games, use the first principal component as the composite metric. Re-derive floor-game thresholds on this composite.

**B. Series-level floor detection:**

**Script:** `src/series_floor_detector.py`

Instead of classifying individual games, detect floor *series* — a sustained multi-game stretch where the player is below their RS baseline. Definition:

- A series is a "floor series" if the player's mean floor_index across all games in the series is below their RS 15th-percentile mean.
- Report both game-level and series-level floor rates. If they diverge (a player has few floor games but many floor series, or vice versa), that's a finding.

**C. Re-run the full Screen A/F pipeline on the composite metric:**

After defining the composite metric, re-run `features.py` (with the new metric as an alternative floor threshold), `screen_a.py`, `screen_e.py`, `screen_f.py`. Do the trigger classifications change? Do players move between buckets? This is the robustness check that matters.

**Success criteria:**
- Trigger classifications are largely robust to the floor-game metric choice (≥80% concordance between Game Score and composite metric)
- Series-level floor detection captures the Mitchell Toronto-type pattern that game-level misses
- The composite metric's PCA weights are not dominated by a single component (if Game Score explains 95% of variance in the first PC, the composite adds nothing)

**Failure mode:** If the composite metric produces meaningfully different trigger classifications, the current taxonomy is metric-dependent. The paper would need to report both and discuss the differences.

---

## Priority Order

| Priority | Gap | Estimated effort | Dependency |
|----------|-----|-----------------|------------|
| **1** | Gap 3 (Threshold sensitivity) | 1-2 days | None — uses existing data |
| **2** | Gap 1 (Split-sample validation) | 2-3 days | None — uses existing data |
| **3** | Gap 4 (Composite metric) | 3-5 days | Requires metric design + re-pipeline |
| **4** | Gap 2 (Causal identification) | 5-10 days | Requires game-level opponent data + scaling Pass 2 |

Gaps 3 and 1 can be done immediately with existing data and should be done first — if the taxonomy doesn't survive sensitivity analysis or split-sample validation, the other gaps are moot. Gap 4 is important but is a larger engineering effort. Gap 2 is essential for the paper but is the longest pole.

---

## What the Null Result Looks Like

If all four gaps fail to produce supportive evidence:
- The taxonomy is an overfit description of this specific cohort
- The paper contribution is the opponent adjustment finding (aggregate playoff effect is explained by opponent quality) plus the trait-stability finding (contraction is a stable RS→PO trait)
- The trigger taxonomy would be presented as "exploratory observation requiring validation" — still potentially publishable at a lower-tier venue, but not Sloan

If Gaps 1 and 3 pass but 2 and 4 fail:
- The taxonomy is real (stable and robust to threshold choice) but not actionable (no causal evidence, wrong metric)
- The paper is a descriptive contribution: "here's a pattern that exists, we don't yet know if it matters"
- This is the most likely publishable outcome if work stops here

If all four pass:
- The taxonomy is stable, robust, and causally meaningful
- Sloan submission is viable
