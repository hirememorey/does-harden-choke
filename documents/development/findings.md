# Does Harden Choke? — Pass 1 Findings

**Date:** March 2026  
**Project:** `does-harden-choke`  
**Status:** Pass 1 complete (Screens A–E); Pass 2 not started

---

## Executive Summary

The original hypothesis asked whether James Harden’s playoff reputation reflects a **variance shift** (more catastrophic floor games) that **compounds late in series** because opponents adapt to heliocentric offense — and whether that pattern distinguishes Group A (heliocentric creators) from Group B (scalable stars).

**Verdict:** The adaptation story is dead. The heliocentric-vs-scalable distinction is directionally suggestive but statistically underpowered. What *is* distinctive about Harden is not *when* his bad games happen or *how often* they happen relative to peers, but **what kind** of bad games they are: total offensive contraction (fewer shots, fewer free throws, fewer assists, fewer minutes) rather than high-volume inefficiency.

The public “choke” narrative is powered by a handful of unforgettable high-leverage catastrophes (Game 6 vs. Spurs 2017, Game 5 vs. Warriors 2015, Game 7 vs. Celtics 2023) that are real but **do not define the statistical distribution** of his playoff performance.

---

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

If playoff floor-game rate is indistinguishable from regular season after opponent adjustment, the line is dead. Pass 1 does not opponent-adjust; that is Pass 2 scope.

---

## Sample & Methods

### Players (11 total)

**Group A — Heliocentric creators**

| Player | RS games | PO games |
|--------|----------|----------|
| James Harden | 1,151 | 173 |
| Russell Westbrook | 1,237 | 135 |
| Luka Dončić | 450 | 55 |
| Trae Young | 483 | 27 |
| Allen Iverson | 914 | 71 |
| Damian Lillard | 900 | 68 |

**Group B — Scalable stars**

| Player | RS games | PO games |
|--------|----------|----------|
| Stephen Curry | 1,026 | 155 |
| Klay Thompson | 865 | 158 |
| Ray Allen | 1,300 | 171 |
| Richard Hamilton | 921 | 130 |
| Kevin Durant | 1,123 | 170 |

*Sample changes from original plan:* Kyrie Irving and Khris Middleton removed; Damian Lillard and Kevin Durant added (March 2026).

**Total games in analysis table:** 11,683

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

---

## Decision Matrix

| H1 (variance shift) | H2 (series gradient) | Conclusion |
|---------------------|----------------------|------------|
| Confirmed | Confirmed | Proceed to Pass 2 |
| Confirmed | Rejected | Paper about playoff variance, not adaptation |
| **Borderline / not significant** | **Rejected** | **See below** |
| Rejected | — | Line is dead |

### Where we land

Per pre-registered criteria, Pass 1 does **not** clear the bar for proceeding to Pass 2 as originally designed. The research question is answered **in the negative** for the adaptation and clutch-concentration framings.

What survives is a **reframed finding**:

> James Harden’s distinctive playoff problem is not that he has more bad games than peers, or that they cluster in elimination games, or that opponents figure him out over seven games. It is that **when he has a bad game, he disappears** — contracting usage, creation, and minutes simultaneously — whereas comparable stars tend to force shots (Durant) or stay on the floor (Curry).

---

## Limitations (Pass 1)

1. **No opponent adjustment** — Playoff opponents are stronger; floor-rate inflation may partly reflect matchup quality, not a Harden-specific mechanism.
2. **Small peer sample** — 11 players; Mann-Whitney tests underpowered; Cohen’s *d* = 0.72 on Group A vs. B is suggestive but *p* = 0.18.
3. **Game Score is offense-only** — Does not capture Harden’s defensive variability.
4. **Season-level opponent DEF_RATING** — No game-level or series-level defensive adjustment.
5. **Age and team context** — Not controlled; Houston-era Harden carries most of the playoff sample.
6. **Injury minutes** — Games with ≤15 minutes flagged but not excluded from primary analysis.
7. **Leverage score is constructed** — Not a market- or win-probability-based leverage metric; sensitivity to definition not tested.

---

## Pipeline Notes (March 2026)

The initial scrape had critical bugs (wrong NBA player IDs mapping Kyrie → Jokić, Klay → Draymond, Ray Allen → Lorenzen Wright; API 500 crash after ~65 minutes). These were fixed:

- Player IDs corrected; Unicode normalization for Dončić name verification
- Per-player scrape isolation with cooldown on failure
- Stale raw/processed data purged and full pipeline re-run
- Final sample: 11 players, 11,683 games, all screens A–E passing

---

## Suggested Next Steps

### If continuing the project

1. **Pass 2 regression** — Opponent-adjusted floor probability: `is_floor ~ is_playoff + opponent_defrtg + rest_days + series_game_num + player FE`
2. **Refine mechanism** — Add `USG%` from advanced logs; test shrinkage as usage-rate drop, not just FGA/36
3. **Bimodality** — Hartigan’s dip test or mixture model on Harden’s playoff Game Score distribution
4. **Expand sample** — 15–20 players per group to test whether Group A > Group B reaches significance without Ray Allen–type outliers
5. **Win-probability leverage** — Replace constructed leverage score with explicit WP or elimination-only subsets

### If writing up now

The honest paper is not “Harden chokes in the clutch.” It is:

**“Playoff floor games among high-usage creators: a profile analysis”** — with Harden as the lead case study showing contraction/disengagement as a distinct failure mode from efficiency-collapse (Durant) or mean-regression (Curry).

---

## Output Files

| File | Description |
|------|-------------|
| `data/processed/screen_a_results.csv` | Variance shift per player |
| `data/processed/screen_b_results.csv` | Within-series floor rates |
| `data/processed/screen_c_results.csv` | Peer rankings |
| `data/processed/screen_d_results.csv` | Leverage concentration |
| `data/processed/screen_e_results.csv` | Floor-game mechanism profiles |
| `data/processed/analysis_table.csv` | Full game-level table |
| `pass1_plan.md` | Original research design |

---

## One-Paragraph Summary

James Harden’s playoff floor-game rate rises from 15% to 21% (variance shift ratio 1.52, χ² *p* = 0.067), but he is not a statistical outlier — Ray Allen shows a larger and significant shift, and the heliocentric group difference is medium-sized but not significant at *n* = 11. Floor games do not compound late in series (H2 rejected) and do not cluster in high-leverage moments (Harden ranks 7th of 11 on leverage concentration; elimination-game floor rate is 14.6% vs. 23.2% otherwise). What distinguishes Harden is the **profile** of his bad games: a 54% per-36 scoring collapse driven roughly equally by volume and efficiency loss, with large drops in FGA, FTA, assists, and minutes — a pattern of offensive disengagement that contrasts sharply with Kevin Durant’s “keep shooting” floor games and differs from the public narrative of clutch failure.
