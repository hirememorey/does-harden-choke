# Does Harden Choke? — Findings

**Date:** June 2026 (Pass 1: March 2026; extensions: June 2026)  
**Project:** `does-harden-choke`  
**Status:** Pass 1 complete (Screens A–E) + extensions (opponent adjustment, RS retention baselines, event frequency). Pass 2 parser validated; possession analysis at spike scale (~69 games).

**Cohort:** 18 players, ~20,000 games in `analysis_table.csv`

---

## Executive Summary

The original hypothesis asked whether James Harden's playoff reputation reflects a **variance shift** that **compounds late in series** because opponents adapt to heliocentric offense — and whether that pattern distinguishes Group A from Group B.

**Verdict (updated):** The adaptation story is dead (H2 rejected). The aggregate "playoffs cause more floor games" story is also dead after opponent adjustment. What survives is a **failure-mode taxonomy**:

1. **Contraction** (volume collapses) vs. **forcing** (volume preserved, efficiency collapses) — a novel game-level distinction (Screen E).
2. **Contraction is a stable career trait** — RS FGA retention predicts PO FGA retention (r = 0.72). Harden's RS≈PO shift is −0pp on FGA retention; playoff contraction is not new behavior.
3. **Three contractor subtypes** cut across Group A/B:
   - **Trait contractor (Harden):** opponent-independent floors; elevated adj. floor rate (+7pp)
   - **Rim-abandoning contractor (PG):** stable volume, catastrophic PO FTA collapse (−29pp)
   - **Scheme-dependent contractor (SGA):** hardest PO contraction, entirely opponent-driven
4. **Forcers** (Durant, Curry) keep shooting through bad nights.

The honest Harden claim: **he contracts the same way in all bad games (RS or PO), has more floor games in the playoffs (partly opponent-driven), and those floors happen against weak defenses too — making them unpredictable.** The public "choke" narrative misdiagnoses mechanism (contraction, not clutch failure) and overweights memorable catastrophes that don't define the distribution.

See [`open_questions.md`](open_questions.md) for resolved research decisions and remaining gaps.

## Research Question

> Is James Harden’s playoff problem better described as a repeated-opponent increase in **downside variance** — especially floor-game frequency late in series — than as a uniform decline in average performance?

Generalized: Do heliocentric offensive engines experience a playoff-specific increase in catastrophic game frequency that cannot be explained by opponent quality alone?

### Hypotheses

| ID | Claim | Pass 1 criterion |
|----|-------|------------------|
| **H1** | Playoff floor-game frequency rises more than mean Game Score falls (variance shift, not mean shift) | Harden `variance_shift_ratio > 1` and χ² *p* < 0.05 |
| **H2** | Floor-game rate increases within series as opponents accumulate tape (Games 5–7 > Games 1–2) | Monotonic early → late gradient; trend *p* < 0.10 |
| **H3** | Harden is an outlier among heliocentric creators vs. scalable stars | Top 3 in floor-rate increase; Group A mean > Group B |

### Falsification

If playoff floor-game rate is indistinguishable from regular season after opponent adjustment, the line is dead. **Opponent adjustment has been run** (see Post-Pass-1 Extensions below): the cohort-wide playoff effect disappears, but Harden's opponent-independent contraction pattern persists.

---

## Sample & Methods

### Players (18 total)

**Original Pass 1 cohort (11)** — see Screen A–D tables below for per-player stats.

**June 2026 expansion (7):** DeMar DeRozan, John Wall, Chris Paul, LeBron James, Kobe Bryant, Paul George, Shai Gilgeous-Alexander. Added to test contractor/forcer taxonomy, opponent-independent vs. scheme-dependent contraction, and minutes-contamination edge cases (Kobe).

| Player | Group | RS games | PO games |
|--------|-------|----------|----------|
| James Harden | A | 1,151 | 173 |
| Russell Westbrook | A | 1,237 | 135 |
| Luka Dončić | A | 450 | 55 |
| Trae Young | A | 483 | 27 |
| Allen Iverson | A | 914 | 71 |
| Damian Lillard | A | 900 | 68 |
| DeMar DeRozan | A | 1,078 | 63 |
| John Wall | A | 647 | 37 |
| Chris Paul | A | 1,274 | 149 |
| LeBron James | A | 1,562 | 282 |
| Shai Gilgeous-Alexander | A | 462 | 46 |
| Stephen Curry | B | 1,026 | 155 |
| Klay Thompson | B | 865 | 158 |
| Ray Allen | B | 1,300 | 171 |
| Richard Hamilton | B | 921 | 130 |
| Kevin Durant | B | 1,123 | 170 |
| Kobe Bryant | B | 1,346 | 220 |
| Paul George | B | 793 | 114 |

*Sample changes from original plan:* Kyrie Irving and Khris Middleton removed; Damian Lillard and Kevin Durant added (March 2026). Seven additional players added (June 2026).

**Total games in analysis table:** ~20,000 (18,746 with opponent DEF_RATING joined)

### Floor-game definition

A **floor game** is any game with Game Score below the player’s **regular-season 15th percentile** (`is_floor_primary`). By construction, each player’s RS floor rate ≈ 15%. Playoff games are evaluated against RS baselines only.

**Game Score formula:**

```
PTS + 0.4×FGM + 0.7×OREB + 0.3×DREB + STL + 0.7×AST + 0.7×BLK
  − 0.7×FGA − 0.4×(FTA−FTM) − 0.4×PF − TOV
```

### Data source

NBA Stats API (`playergamelogs`), seasons 1996–97 through 2024–25. Series game numbers derived from **team** playoff logs (not player logs) to handle missed games correctly. See `pass1_plan.md` for full pipeline.

---

## Screen A — Variance Shift (H1)

**Question:** Does the playoff distribution shift via increased floor-game frequency more than via mean decline?

### Harden

| Metric | RS | Playoffs |
|--------|-----|----------|
| Floor-game rate | 15.0% | 20.8% |
| Mean Game Score | 19.36 | 17.59 |
| Floor-rate increase | — | **+5.8 pp** |
| Variance shift ratio | — | **1.52** |
| χ² *p*-value | — | **0.067** |
| Welch *t*-test (mean GS) | — | *p* = 0.023 |

**Interpretation:** Directionally consistent with H1 — floor games rise faster than mean output falls (`variance_shift_ratio` = 1.52). But the contingency test misses conventional significance (*p* = 0.067). Mean Game Score decline is statistically significant; floor-rate increase is borderline.

### Full peer table (sorted by floor-rate increase)

| Player | Group | RS floor % | PO floor % | Δ floor | Var. shift ratio | χ² *p* |
|--------|-------|------------|------------|---------|------------------|--------|
| Ray Allen | B | 14.9% | 28.7% | +13.7 | 2.25 | <0.001 |
| Trae Young | A | 15.1% | 25.9% | +10.8 | 1.86 | 0.22 |
| Damian Lillard | A | 15.0% | 23.5% | +8.5 | 1.68 | 0.09 |
| **James Harden** | **A** | **15.0%** | **20.8%** | **+5.8** | **1.52** | **0.067** |
| Russell Westbrook | A | 15.0% | 19.3% | +4.3 | 1.32 | 0.23 |
| Allen Iverson | A | 15.0% | 16.9% | +1.9 | 1.10 | 0.79 |
| Klay Thompson | B | 15.0% | 16.5% | +1.4 | 1.14 | 0.74 |
| Kevin Durant | B | 15.0% | 14.1% | −0.9 | 0.91 | 0.84 |
| Luka Dončić | A | 15.1% | 14.5% | −0.6 | 0.94 | 1.00 |
| Richard Hamilton | B | 15.0% | 10.0% | −5.0 | 0.59 | 0.17 |
| Stephen Curry | B | 14.9% | 8.4% | −6.5 | 0.54 | 0.04 |

**Harden ranks 4th of 11** in floor-rate increase (needed top 3 for Pass 1). Ray Allen — a Group B off-ball shooter — shows the strongest and only highly significant variance shift in the sample, which undercuts the heliocentric-vulnerability framing.

**H1 verdict:** Borderline fail on pre-registered criteria. Descriptive signal present; not significant at α = 0.05.

---

## Screen B — Within-Series Gradient (H2)

**Question:** Does floor-game frequency compound as a series progresses?

### Harden by series bucket

| Bucket | Games | Floor rate | 95% CI |
|--------|-------|------------|--------|
| Early (1–2) | 61 | 21.3% | 12.9–33.1% |
| Mid (3–4) | 60 | 18.3% | 10.6–29.9% |
| Late (5–7) | 52 | 23.1% | 13.7–36.1% |

**Not monotonic** (early → mid → late). No evidence of compounding adaptation.

### Harden by exact series game number

| Game # | *n* | Floor rate |
|--------|-----|------------|
| 1 | 31 | 19.4% |
| 2 | 30 | 23.3% |
| 3 | 30 | 13.3% |
| 4 | 30 | 23.3% |
| 5 | 29 | **31.0%** |
| 6 | 16 | 12.5% |
| 7 | 7 | 14.3% |

Game 5 is elevated but the pattern is noisy; Games 6–7 do not show a sustained late-series spike.

### Group aggregates (playoff only)

| Bucket | Group A floor % | Group B floor % |
|--------|-----------------|-----------------|
| Early | 20.3% | 15.1% |
| Mid | 18.7% | 15.0% |
| Late | 20.7% | 18.2% |

Both groups are flat across buckets. Group A runs ~5 pp higher throughout, not accelerating late.

**H2 verdict:** Rejected. The within-series adaptation mechanism has no support.

---

## Screen C — Peer Comparison (H3)

| Metric | Group A mean | Group B mean | Mann-Whitney *p* | Cohen’s *d* |
|--------|--------------|--------------|-------------------|-------------|
| Floor-rate increase | +5.1 pp | +0.5 pp | 0.18 | 0.72 (medium) |
| Variance shift ratio | 1.40 | 1.09 | 0.25 | 0.58 |

Group A shows a larger floor-rate increase on average, with medium effect size, but **n = 6 vs. 5** is too small for significance. Harden’s percentile rank on floor-rate increase: **70th** (4th of 11).

**H3 verdict:** Partial. Directionally consistent with Group A > Group B; not statistically significant; Harden not in top 3.

---

## Screen D — Leverage Concentration

**Question:** Do Harden’s floor games cluster in high-leverage moments (elimination games, late series games) more than his non-floor games — and more than peers?

### Leverage score (0–1)

| Series game | Base leverage |
|-------------|---------------|
| 1–2 | 0.15 |
| 3–4 | 0.35 |
| 5 | 0.55 |
| 6 | 0.70 |
| 7 | 0.90 |
| +0.10 if elimination game (either team at 3 wins) | |

**Leverage concentration** = mean(leverage | floor game) − mean(leverage | non-floor game). Positive = bad games cluster in big moments.

### Results (ranked)

| Rank | Player | Group | Leverage conc. | Logit *p* |
|------|--------|-------|----------------|-----------|
| 1 | Klay Thompson | B | +0.104 | 0.040 |
| 2 | Trae Young | A | +0.085 | 0.429 |
| 3 | Russell Westbrook | A | +0.082 | 0.121 |
| … | … | … | … | … |
| **7** | **James Harden** | **A** | **−0.015** | **0.728** |
| 11 | Damian Lillard | A | −0.163 | 0.013 |

**Harden ranks 7th of 11** — his floor games skew slightly *lower* leverage than his non-floor games. The “clutch choke” framing is not supported statistically.

### Harden floor rate by leverage tier

| Tier | Games | Floor rate |
|------|-------|------------|
| Low | 61 | 21.3% |
| Medium | 60 | 18.3% |
| High | 52 | 23.1% |

Roughly flat across tiers.

### Elimination vs. non-elimination (binary)

| Context | Harden floor rate |
|---------|-------------------|
| Elimination games | **14.6%** |
| Non-elimination | **23.2%** |

Harden’s floor-game rate is **lower** in elimination games — the opposite of the choke narrative.

### Iconic catastrophes vs. the distribution

Harden’s highest-leverage floor games are real and memorable:

| Date | Matchup | Game # | Elim? | Leverage | PTS | FGA | GmSc |
|------|---------|--------|-------|----------|-----|-----|------|
| 2023-05-14 | PHI @ BOS | 7 | Yes | 0.90 | 9 | 11 | 6.9 |
| 2017-05-11 | HOU vs. SAS | 6 | Yes | 0.80 | 10 | 11 | 1.4 |
| 2015-05-27 | HOU @ GSW | 5 | Yes | 0.65 | 14 | 11 | 1.0 |
| 2024-05-01 | LAC vs. DAL | 5 | No | 0.55 | 7 | 12 | 1.9 |

These games anchor the narrative. They do not, however, pull the overall leverage concentration positive — most of Harden’s 36 playoff floor games occur in ordinary contexts.

**Leverage verdict:** Rejected. Bad games are not disproportionately “big games” for Harden relative to peers.

---

## Screen E — Floor-Game Profile (Mechanism)

**Question:** What *kind* of bad games does Harden have, and how does that differ from similar superstars?

### Mechanism taxonomy

| Type | Definition | Floor-game behavior |
|------|------------|---------------------|
| **Shrinker** | >55% of scoring drop from volume collapse | Fewer FGA, FTA; stops attacking |
| **Forcer** | <35% volume share | Keeps shooting; efficiency collapses |
| **Mixed** | 35–55% | Both volume and efficiency contribute |

Volume share = share of per-36 scoring drop explained by lost shot attempts and free throws (vs. efficiency on remaining attempts).

### Playoff floor-game profiles

| Player | Group | Mechanism | Vol. share | Min Δ | FGA/36 Δ | FTA/36 Δ | AST/36 Δ |
|--------|-------|-----------|------------|-------|----------|----------|----------|
| James Harden | A | mixed | 52% | −7.0 | −4.3 | −3.2 | −2.0 |
| Kevin Durant | B | forcer | 25% | −3.1 | −0.6 | −2.6 | −1.3 |
| Stephen Curry | B | mixed | 45% | −2.0 | −3.3 | −2.9 | −0.7 |
| Russell Westbrook | A | mixed | 41% | −9.7 | −3.2 | −3.3 | −2.0 |
| Ray Allen | B | mixed | 51% | −8.7 | −3.7 | −1.3 | −1.2 |
| Klay Thompson | B | forcer | 32% | −0.6 | −2.4 | −1.0 | −0.8 |

### Harden vs. Durant — the key contrast

When Harden has a playoff floor game:

- **Scoring:** −13.4 pts/36 (−54% vs. his non-floor playoff rate)
- **Volume:** FGA/36 −4.3, FTA/36 −3.2, AST/36 −2.0
- **Minutes:** −7.0 per game
- **Attack profile:** FTA/FGA ratio drops (−0.095) — stops getting to the line relative to shot volume
- **Turnovers:** slightly up (+0.7/36) despite lower usage

When Durant has a playoff floor game:

- **Scoring:** −8.7 pts/36 (−32% vs. non-floor rate)
- **Volume:** FGA/36 −0.6 — **keeps shooting** at nearly the same rate
- **Minutes:** −3.1
- **Classification:** forcer (efficiency collapse, not volume collapse)

When Curry has a playoff floor game:

- Minutes drop only −2.0 — staff keeps him on the floor through bad nights
- Volume share 45% (mixed), closer to Harden than Durant

### What this means

Harden’s bad playoff games are **disengagement events**, not clutch failures:

1. He does not force through inefficiency the way Durant does.
2. He does not stay on the floor through slumps the way Curry does.
3. When his shot isn’t falling, **everything contracts at once** — shots, free throws, assists, minutes. The offensive role shrinks holistically.

This is consistent with watching the iconic games: Game 6 vs. Spurs (10 pts, 2–11 FG), Game 5 vs. Warriors (14 pts, 2–11 FG), Game 7 vs. Celtics (9 pts, 3–11 FG) are low-volume catastrophes, not 30-point inefficient nights.

The foul-whistle hypothesis (playoff officiating devalues his rim attacks) was considered but deprioritized based on game film — the data show FTA collapse alongside FGA collapse, which is consistent with **not attacking** rather than attacking without whistles.

### Kobe reclassification (June 2026)

Original Screen E labeled Kobe "shrinker" (vol_share 62%, min Δ −16.6). **This was wrong.** Half his floor games were blowout benchings (median 13.6 minutes). With ≥25-minute floor games: FGA retention 75% PO, FTA retention 52%. He keeps shooting jump shots that don't fall — **forcer with rim abandonment**, not contractor. Do not cite Kobe alongside Harden/PG as a contraction archetype without the minutes filter.

---

## Decision Matrix

| H1 (variance shift) | H2 (series gradient) | Conclusion |
|---------------------|----------------------|------------|
| Confirmed | Confirmed | Proceed to Pass 2 |
| Confirmed | Rejected | Paper about playoff variance, not adaptation |
| **Borderline / not significant** | **Rejected** | **See below** |
| Rejected | — | Line is dead |

### Where we land (updated June 2026)

Per **pre-registered** criteria (H1 χ² *p* < 0.05, H2 monotonic gradient, H3 top-3 floor-rate increase), Pass 1 does not clear the bar for the original adaptation/variance-shift thesis. H2 and leverage concentration are rejected outright.

**June 2026 extensions reframed the project** without changing the raw Screen A–D results: opponent adjustment explains the cohort-wide playoff effect (but Harden retains +7.1pp adjusted increase); RS retention baselines show contraction is a stable trait; failure-mode taxonomy replaces heliocentric/scalable partition. Pass 2 proceeds as supporting evidence — see [`open_questions.md`](open_questions.md) §5.

What survives is a **reframed finding**:

> James Harden’s distinctive playoff problem is not that opponents figure him out over seven games, or that his bad games cluster in elimination games. It is that **he contracts the same way in all bad games (RS or PO), has more floor games in the playoffs (partly opponent-driven), and those floors happen against weak defenses too** — whereas comparable stars tend to force shots (Durant) or contract only when elite defenses take away their driving lanes (SGA).

---

## Post-Pass-1 Extensions (June 2026)

### Opponent-adjusted floor rates (`screen_a_adj.py`)

Logistic regression: `is_floor ~ is_playoff + def_rating + player FE` on 18,746 games with opponent DEF_RATING (93% coverage).

| Coefficient | Result |
|-------------|--------|
| `is_playoff` | OR = 0.98, *p* = 0.83 — **no residual playoff effect** |
| `def_rating` | OR = 0.95 per point, *p* < 10⁻²⁴ — stronger defenses *reduce* floor-game odds |

**Harden deep dive:** floors vs weak (33%), average (16%), strong (16%) defenses. OLS `is_floor ~ def_rating`: coef = −0.014, *p* = 0.066, R² = 0.02. **Opponent quality does not explain Harden's floors** — he floors against weak defenses at the same rate as strong ones.

**Adjusted floor-rate increases (top 4):** Trae Young +12.3pp, Lillard +8.2pp, Harden +7.1pp, Ray Allen +7.0pp.

### RS retention baselines (`rs_retention_baseline.py`)

FGA retention = (FGA/36 in floor games) / (FGA/36 in non-floor games). Same for FTA and minutes.

**Harden (stable trait):**

| Metric | RS | Playoffs | Shift |
|--------|-----|----------|-------|
| FGA retention | 75% | 74% | −0pp |
| FTA retention | 57% | 60% | +3pp |

**Paul George (rim abandonment in playoffs):**

| Metric | RS | Playoffs | Shift |
|--------|-----|----------|-------|
| FGA retention | 76% | 72% | −4pp |
| FTA retention | 54% | 25% | **−29pp** |

**SGA (scheme-dependent, small n):**

| Metric | RS | Playoffs | Shift |
|--------|-----|----------|-------|
| FGA retention | 72% | 53% | −19pp |
| Floor rate vs weak/strong D | 39% / 0% | — | opponent-driven (*p* = 0.001) |

**Trait stability:** RS FGA retention → PO FGA retention: Pearson r = 0.72, *p* = 0.0008 (n = 18). No cohort-wide PO intensification (mean shift −3.2pp, *p* = 0.08).

**Kobe reclassification:** Original Screen E labeled Kobe "shrinker" (vol_share 62%, min Δ −16.6). With ≥25-minute floor games: FGA retention 80% PO, FTA retention 52%. He keeps shooting jump shots that don't fall — **forcer with rim abandonment**, not contractor. Minute collapse was blowout benching (median 13.6 min in floor games).

### Event frequency (`pass2/event_frequency.py`)

69-game PBP sample; Event A = ≤1 FGM on ≥5 Q1–Q2 FGA.

| Metric | Value |
|--------|-------|
| Event A rate (eligible) | 14.5% |
| Projected Event A (cohort) | ~138 |
| Combined Events A + B | ~273 |
| Harden projected Event A | ~14 (adequate) |
| SGA, Luka, Trae | ~2–3 (underpowered) |

**Decision:** Pass 2 feasible as supporting illustration for top 5–6 stars; not primary identification strategy.

### Contractor / forcer taxonomy (refined)

| Archetype | Players | Key signature |
|-----------|---------|---------------|
| Trait contractor | Harden | RS≈PO contraction; opponent-independent floors |
| Rim-abandoning contractor | Paul George | Stable FGA; PO FTA collapse −29pp |
| Scheme-dependent contractor | SGA | Hardest PO contraction; 0% floor vs strong D |
| Forcer | Durant, Curry, Iverson | FGA retention >90%; efficiency collapse |
| Inverse contractor | Westbrook, CP3 | Floor *more* vs weak D (disengagement when not forced) |

**Rejected:** "FTA dependency → contraction" as simple rule. SGA has highest FTA dependency and contracts hardest — but entirely opponent-driven.

---

## Limitations

1. ~~**No opponent adjustment**~~ — **Done.** Cohort effect explained; Harden-specific pattern persists.
2. **Peer sample still modest** — 18 players; PG (17 PO floor games), SGA (8) underpowered for structural claims.
3. **Game Score is offense-only** — Does not capture defensive variability.
4. **Season-level opponent DEF_RATING** — No game-level or series-level scheme adjustment.
5. **Age and team context** — Not controlled.
6. **Minutes contamination** — Partially addressed (≥25 min filter); possession-level decontamination still needed.
7. **No causal chain** — Contraction → team ORtg → wins untested.
8. **Leverage score is constructed** — Not WP-based.

---

## Pipeline Notes (March 2026)

The initial scrape had critical bugs (wrong NBA player IDs mapping Kyrie → Jokić, Klay → Draymond, Ray Allen → Lorenzen Wright; API 500 crash after ~65 minutes). These were fixed:

- Player IDs corrected; Unicode normalization for Dončić name verification
- Per-player scrape isolation with cooldown on failure
- Stale raw/processed data purged and full pipeline re-run
- Final Pass 1 sample (March 2026): 11 players, 11,683 games, all screens A–E passing
- June 2026 expansion: 18 players, ~20,000 games; extensions added (`screen_a_adj.py`, `rs_retention_baseline.py`, `event_frequency.py`)

---

## Suggested Next Steps

### Priority order (June 2026)

1. **Causal chain** — In contraction games, team ORtg and win rate vs. non-contraction games; control for score margin
2. **Pass 2 at scale** — Same-game pre-event baselines on ~273 combined cold-start events
3. **Out-of-sample validation** — Train profile on career first half, test on second half
4. **Expand cohort** — Embiid, Butler, Mitchell to test PG/Harden category robustness
5. **Minutes decontamination** — Possession-level "on-floor contraction" vs. benching

### If writing up now

The honest paper is not "Harden chokes in the clutch." It is:

**"Failure modes under adversity: contraction vs. forcing among NBA stars"** — documenting a novel taxonomy, showing contraction is a stable trait, and distinguishing opponent-independent contractors (Harden, PG) from scheme-dependent ones (SGA) and forcers (Durant, Curry).

---

## Output Files

| File | Description |
|------|-------------|
| `data/processed/analysis_table.csv` | Full game-level table (~20k rows) |
| `data/processed/screen_a_results.csv` | Variance shift per player |
| `data/processed/screen_a_adj_results.csv` | Opponent-adjusted floor rates |
| `data/processed/retention_baselines.csv` | RS vs PO FGA/FTA/min retention |
| `data/processed/screen_b_results.csv` | Within-series floor rates |
| `data/processed/screen_c_results.csv` | Peer rankings |
| `data/processed/screen_d_results.csv` | Leverage concentration |
| `data/processed/screen_e_results.csv` | Floor-game mechanism profiles |
| `data/processed/event_frequency_estimates.csv` | Pass 2 Event A/B projections |
| `documents/development/DEVELOPER.md` | Onboarding — setup, pipeline, what's done vs. open |
| `documents/development/pass1_plan.md` | Original research design |
| `documents/development/open_questions.md` | Resolved decisions + remaining gaps |

---

## One-Paragraph Summary

James Harden's raw playoff floor-game rate rises from 15% to 22% (χ² *p* = 0.067), but after opponent adjustment the cohort-wide playoff effect disappears (*p* = 0.83) while Harden retains a +7pp adjusted increase with opponent-independent floors (33% vs weak defenses, 16% vs strong). His contraction is not playoff-specific — FGA retention is 75% RS and 74% PO — but it is a stable career trait (r = 0.72 across the cohort) that distinguishes him from forcers like Durant (97% FGA retention in PO floor games). Paul George shares the opponent-independent contraction pattern but via rim abandonment (FTA retention 54%→25% in playoffs); SGA shares the contraction symptom but via scheme dependence (0% floor rate vs strong defenses). Floor games do not compound late in series (H2 rejected) or cluster in elimination games (Harden: 15% elim vs 23% non-elim). The public "choke" narrative misdiagnoses a structural failure mode — contraction under adversity — as clutch psychology.
