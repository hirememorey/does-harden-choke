# Does Harden Choke? — Findings

**Date:** June 2026 (Pass 1: March 2026; extensions: June 2026; FTA deep-dive: June 17 2026)  
**Project:** `does-harden-choke`  
**Status:** Pass 1 complete (Screens A–E) + extensions (opponent adjustment, RS retention baselines, event frequency). Trigger taxonomy retired (Phase A). Architecture model failed (Phase B/C). FTA shift analysis (Phase E) produced the project's strongest finding. Pass 2 parser validated; possession analysis at spike scale (~69 games).

**Cohort:** 31 players, ~31,000 games in `analysis_table.csv`

---

## Executive Summary

The original hypothesis asked whether James Harden's playoff reputation reflects a **variance shift** that **compounds late in series** because opponents adapt to heliocentric offense — and whether that pattern distinguishes Group A from Group B.

**Verdict (updated June 17 2026):** The adaptation story is dead (H2 rejected). The aggregate "playoffs cause more floor games" story is dead after opponent adjustment. The trigger taxonomy was retired after failing split-sample validation (Phase A). The architecture model failed (Phases B/C). What survived and strengthened:

### The actual finding: FTA shift as the primary risk signal

**Players whose free throw attempts per 36 minutes drop from regular season to playoffs have significantly more floor games (r = −0.528, p = 0.002, bootstrap 95% CI [−0.72, −0.28]).** This is the project's strongest statistical result by a wide margin.

The mechanism is a single-action collapse: FGA and FTA co-collapse in playoff floor games (r = +0.428, p = 0.016) because for foul-dependent scorers, the drive-and-draw-contact IS the scoring action. When the rim is walled off or the calls don't come, both the shot attempt and the foul disappear simultaneously. There is no secondary mode to absorb the load. Shot chart data confirms: losing restricted area access predicts losing free throw attempts (RA shift → FTA shift: r = +0.521, p = 0.003).

This is NOT the "playoff whistle" narrative. The cohort-wide FTA shift is essentially zero (15/31 players *increase* FTA rate). The finding is player-specific: some players consistently gain FTAs in the playoffs (LeBron +0.4/36, Dirk +1.7/36, Brunson +1.3/36), others consistently lose them (Harden −1.1/36, Embiid −1.2/36, Fox −1.8/36). The question is *why*.

### The predictive gap

The FTA shift is moderately stable across career halves (split-half r = +0.451, p = 0.016; sign concordance 79%). Harden consistently loses FTAs; LeBron consistently gains them; Dirk consistently gains them. But it is NOT stable enough to predict future floor rates: first-half FTA shift → second-half PO floor rate is r = −0.164, p = 0.403.

The missing variable is **foul type** — what kind of contact generates the free throws. Players whose FTAs come from genuine rim-finishing contact (LeBron driving through defenders) likely maintain or increase FTAs under playoff physicality. Players whose FTAs come from perimeter foul-drawing (rip-throughs, pump-fake-and-jump-into, marginal whistle-seeking) likely lose FTAs as refs tighten and defenders adjust. This distinction is not measurable from box scores or play-by-play — it requires video classification of shooting fouls. See `documents/development/foul_type_video_plan.md`.

### How we got here (resolved background)

The project began by asking *how* stars fail in the playoffs — do they **contract** (stop shooting) or **force** (keep shooting inefficiently)? The key finding was negative: mechanism and frequency are independent. Butler contracts like Harden but barely floors in the playoffs. The mechanism taxonomy is resolved context, not a primary axis.

The trigger taxonomy (Screen F) then asked *when* floor games happen by examining floor rates across opponent quality. This was retired after failing split-sample validation (Phase A, June 14 2026 — 31% concordance across career halves).

The architecture prediction model (Phases B/C) asked whether RS scoring architecture predicts PO floor risk. The box-score model (R² = 0.128) and shot-chart model (mode independence range 0.315–0.340, no variance) both failed.

The FTA shift analysis (Phase E, June 17 2026) asked why some players lose free throws in the playoffs and others don't, producing the project's strongest finding.

### Summary of key findings

1. **FTA per-36 shift is the strongest predictor of PO floor-game rate** — r = −0.528, p = 0.002 (career level, n=31). Combined with FGA shift: R² = 0.40.
2. **FGA and FTA co-collapse in floor games** — r = +0.428, p = 0.016. Foul-dependent scoring fails as a single action.
3. **RA shift → FTA shift → floor games** — losing restricted area access costs free throws (r = +0.521, p = 0.003), and losing free throws predicts floor games.
4. **FTA dependency is significant at the game level** — multilevel model (n=3,269 games): β = −0.024, p = 0.019, controlling for opponent quality. It operates as a base-rate risk factor (interaction with opponent quality is null, p = 0.226).
5. **Contraction is a stable career trait** — RS FGA retention predicts PO FGA retention (r = 0.72). But trait stability of mechanism does not predict frequency.
6. **The cohort-wide playoff floor effect is explained by opponent quality** — p = 0.83 after adjustment.
7. **The "playoff whistle" is not universal** — 15/31 increase FTA rate; cohort mean shift −0.05.
8. **The predictive gap remains open** — FTA shift is moderately stable (split-half r = 0.45) but does not predict future floor rates (H1 → H2: r = −0.16, p = 0.40). The missing variable is foul type.

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

### Players (31 total)

**Original Pass 1 cohort (11)** — see Screen A–D tables below for per-player stats.

**June 2026 expansion (7):** DeMar DeRozan, John Wall, Chris Paul, LeBron James, Kobe Bryant, Paul George, Shai Gilgeous-Alexander. Added to test contractor/forcer taxonomy, opponent-independent vs. scheme-dependent contraction, and minutes-contamination edge cases (Kobe).

**June 2026 Butler addition (1):** Jimmy Butler. Added to stress-test the taxonomy — perceived elite playoff riser vs. DeRozan (perceived playoff shrinker). Reveals mechanism–frequency independence and a new "situational contractor" archetype.

**June 2026 fourth wave (4):** De'Aaron Fox (disengagement trigger), Tobias Harris (standard/shrinker), Kyrie Irving (standard/forcer), Donovan Mitchell (bimodal/mixed). Added to extend trigger taxonomy to rim-pressure guards, secondary scorers, clutch-narrative guards, and bimodal riser/shrinker patterns. See [`butler_derozan_case_study.md`](butler_derozan_case_study.md).

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
| Jimmy Butler | A | 907 | 130 |
| Stephen Curry | B | 1,026 | 155 |
| Klay Thompson | B | 865 | 158 |
| Ray Allen | B | 1,300 | 171 |
| Richard Hamilton | B | 921 | 130 |
| Kevin Durant | B | 1,123 | 170 |
| Kobe Bryant | B | 1,346 | 220 |
| Paul George | B | 793 | 114 |

**June 2026 fourth wave (4):**

| Player | Group | RS games | PO games |
|--------|-------|----------|----------|
| De'Aaron Fox | A | 603 | 28 |
| Tobias Harris | B | 1,033 | 81 |
| Kyrie Irving | B | 779 | 96 |
| Donovan Mitchell | B | 609 | 81 |

*Sample changes from original plan:* Kyrie Irving and Khris Middleton removed; Damian Lillard and Kevin Durant added (March 2026). Seven additional players added (June 2026). Jimmy Butler added (June 2026).

**Total games in analysis table:** ~31,000 (29,000+ with opponent DEF_RATING joined)

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

### Note on Screen E's role

Screen E is **resolved background**. It answered the question "how do stars fail?" (contraction vs. forcing) and revealed that mechanism is a stable career trait (r = 0.72) but independent of failure frequency. This finding was the critical pivot point: if *how* you fail doesn't predict *how often*, then something else determines frequency — which led to the trigger taxonomy (Screen F). New readers should understand Screen E as settled context that motivated Screen F, not as the project's primary contribution.

---

## Screen F — Trigger Classification (Primary Axis)

**Question:** *Why* do floor games happen? Under what conditions does a star's bad game get triggered?

This is the project's primary contribution. The contractor/forcer mechanism taxonomy (Screen E) showed that failure mechanism and failure frequency are independent — Butler contracts like Harden but barely floors. So the differentiator isn't *how* a star fails but *when*. Screen F classifies the **trigger conditions** that produce floor games by examining floor-game rates across opponent defensive quality terciles.

### Trigger types

| Type | Definition | Scouting implication |
|------|-----------|---------------------|
| **Opponent-independent** | Floors vs weak and strong D alike | Unpredictable — can't scheme it away or build a system to prevent it |
| **Scheme-dependent** | Floors only vs elite D | Gameplan-able — structure offense to avoid the scheme that triggers failure |
| **Disengagement** | Floors vs weak D, rises vs strong D | System-dependent — keep the star engaged; bad games come from coasting, not pressure |
| **Bimodal** | Floors vs both ends, not average | Two different triggers operating |
| **Standard** | No distinctive pattern | Mild gradient, no actionable trigger signal |

### Full trigger classification (31 players)

| Player | Trigger | PO floor % | Δ floor | Weak D | Avg D | Strong D | Gradient |
|--------|---------|-----------|---------|--------|-------|----------|----------|
| **James Harden** | opponent-independent | 22.3% | +7.5% | 32% | 14% | 20% | +0.12 |
| **Joel Embiid** | opponent-independent | 27.3% | +12.2% | 39% | 19% | 25% | +0.14 |
| **Paul George** | opponent-independent | 15.2% | +0.2% | 27% | 6% | 17% | +0.10 |
| **Klay Thompson** | opponent-independent | 15.2% | +0.2% | 22% | 11% | 13% | +0.09 |
| Russell Westbrook | scheme-dependent | 19.4% | +4.4% | 11% | 19% | 30% | −0.19 |
| Trae Young | scheme-dependent | 25.9% | +10.9% | 8% | 36% | 50% | −0.42 |
| Ben Simmons | scheme-dependent | 17.9% | +2.8% | 6% | 8% | 50% | −0.44 |
| **De'Aaron Fox** | disengagement | 17.9% | +2.8% | 30% | 15% | 0% | +0.30 |
| Shai Gilgeous-Alexander | disengagement | 14.8% | −0.3% | 35% | 8% | 0% | +0.35 |
| Jimmy Butler | disengagement | 10.8% | −4.2% | 19% | 10% | 2% | +0.16 |
| Giannis Antetokounmpo | disengagement | 10.7% | −4.0% | 19% | 8% | 4% | +0.16 |
| Ray Allen | disengagement | 28.1% | +13.2% | 35% | 31% | 18% | +0.17 |
| Tyrese Haliburton | disengagement | 7.9% | −7.1% | 21% | 0% | 0% | +0.21 |
| **Donovan Mitchell** | bimodal | 16.0% | +1.1% | 21% | 7% | 20% | +0.01 |
| DeRozan | bimodal | 15.9% | +0.8% | 21% | 5% | 21% | 0.00 |
| Iverson | bimodal | 16.4% | +1.4% | 20% | 9% | 21% | −0.01 |
| Wall | bimodal | 10.8% | −4.2% | 21% | 0% | 9% | +0.12 |
| Curry | bimodal | 7.4% | −7.6% | 12% | 2% | 9% | +0.03 |
| Luka Doncic | bimodal | 14.5% | −0.5% | 17% | 5% | 24% | −0.07 |
| **Dirk Nowitzki** | standard | **7.1%** | **−7.8%** | 8% | 4% | 10% | −0.02 |
| **Kyrie Irving** | standard | 18.8% | +3.7% | 14% | 20% | 23% | −0.08 |
| **Tobias Harris** | standard | 11.1% | −3.2% | 3% | 20% | 12% | −0.09 |
| Kevin Durant | standard | 13.3% | −1.7% | 16% | 16% | 7% | +0.09 |
| LeBron James | standard | 12.0% | −3.1% | 14% | 13% | 9% | +0.06 |
| Kobe Bryant | standard | 11.6% | −3.4% | 10% | 16% | 8% | +0.02 |
| CP3 | standard | 17.4% | +2.5% | 11% | 16% | 26% | −0.15 |
| Lillard | standard | 23.5% | +8.5% | 24% | 19% | 29% | −0.05 |
| Nikola Jokic | standard | 4.0% | −11.1% | 8% | 0% | 3% | +0.05 |
| Jalen Brunson | standard | 4.7% | −10.3% | 3% | 10% | 0% | +0.03 |
| Jayson Tatum | standard | 11.8% | −3.2% | 16% | 10% | 8% | +0.08 |
| Richard Hamilton | standard | 10.9% | −4.1% | 10% | 12% | 11% | 0.00 |

### The Dirk Nowitzki test case

Dirk had one of the most visible "choker to champion" narrative flips in NBA history. Pre-2011: labeled soft, couldn't win the big one, 2006 Finals collapse, 2007 first-round upset. Post-2011: playoff legend, carried the Mavs through the gauntlet, beat LeBron's Heat.

The data do not support the narrative flip:

| Metric | RS | Playoffs |
|--------|-----|----------|
| Floor-game rate | 15.0% | **7.1%** |
| Trigger | — | **standard** |
| Mechanism | — | **forcer** (vol_share 27%) |
| FGA retention | 89% RS | **94% PO** |
| PO floor rate vs weak D | — | 8% |
| PO floor rate vs strong D | — | 10% |

Dirk **improves** in the playoffs by every metric available. His floor rate drops nearly 8pp. His FGA retention goes UP — he shoots more aggressively in PO floor games than RS floor games. His trigger profile is `standard` — no distinctive opponent pattern, nothing to scheme against or build around.

The 2011 championship wasn't Dirk "finally showing up." It was the year the team around him was good enough to win when Dirk did what Dirk always did. This is the **KAT pattern**: the system changed, not the player. But unlike KAT (whose floor weaknesses are hidden by team defense), Dirk's floor weaknesses were never the problem — the surrounding roster was.

**Key contrast with Harden:** Dirk's "choker" reputation was a pure narrative artifact — the data show a player who gets *better* in the playoffs. Harden's reputation has a real empirical basis (opponent-independent 22% floor rate, +7.5pp increase) but is *misdiagnosed* — it's not psychology, it's a structural trigger pattern with no identifiable condition to remove.

---

## Fourth-Wave Case Studies (June 2026)

### De'Aaron Fox — Disengagement extends to rim-pressure guards

Fox classified `disengagement` (gradient +0.30): 30% floor rate vs weak D, 0% vs strong D. This extends the disengagement archetype beyond SGA and Butler to speed-dependent creators whose engagement is stakes-dependent. Fox's adjusted floor-rate increase (+7.0pp) ties Harden for the cohort's largest — but via the opposite trigger. Harden is unpredictable (floors vs everyone); Fox is manageable (floors only vs weak D). The same +7pp number means completely different things structurally.

### Tobias Harris — The inverse meme

Harris classified `standard` trigger, `shrinker` mechanism (vol_share 59%). His PO floor rate is only 11.1% (−3.2pp from RS) — he rarely floors. But when he does, the contraction is catastrophic: FGA retention drops from 92% RS to 64% PO (−28pp shift, the largest in the cohort). With ≥25 min filter, FTA retention drops from 53% RS to 11% PO (−41pp). The "Tobias Harris" meme exists because floor games are *visible* when they happen (catastrophic withdrawal), not because they happen often. This is the inverse of Harden: Harden floors often (+7.5pp) but moderately; Harris floors rarely (−3.2pp) but severely.

### Kyrie Irving — The clutch god is a sampling artifact

Kyrie classified `standard` trigger (gradient −0.08), `forcer` mechanism (vol_share 31%). His PO floor rate is 18.8% (+3.7pp raw, +2.4pp adj) — he floors more in the playoffs, not less. The `standard` trigger means no opponent condition predicts his floor games: 14% vs weak D, 20% vs average, 23% vs strong D. The `forcer` mechanism means he keeps shooting through slumps (FGA retention 91% PO) — the shots just don't fall (FG% −16.3pp, 3PT% −18.0pp in floor games).

The "clutch god" narrative is a highlight-reel sampling artifact. The 2016 Game 7 shot and the 2017 conference finals are real — but they're drawn from the same distribution that produces 4-of-18 against Milwaukee and 6-of-19 in the 2024 Finals. Kyrie isn't clutch; he's **random at a high base rate**, and people remember the peaks because they happened to land in the biggest moments.

### Donovan Mitchell — Two triggers, one player

Mitchell classified `bimodal` trigger (gradient +0.01), `mixed` mechanism (vol_share 41%). The bimodal classification: 21% floor rate vs weak D, 7% vs average, 20% vs strong D. Two different triggers:

1. **Against weak defenses (disengagement):** He coasts. The 2022 Dallas Game 5 (4-of-15, 0-for-7 from 3, 9 points with the series on the line) is the archetype.
2. **Against strong defenses (scheme-suppressed):** Elite switching takes away his driving lanes; he keeps launching contested pull-ups. The 2019 Houston series (3 floor games in 5 games) is the archetype.

His 2025-26 Cleveland runs exposed the bimodal trigger in full: vs Toronto (weak-average D), he disengaged for five consecutive games after Games 1-2 (FTA dropped from 7 to 0); vs Detroit (weaker D), he was engaged and peaked at 43 points in Game 4; vs New York (ECF, strong D), he forced inefficiently — 27 PPG on mediocre shooting while the team was destroyed (−66 +/− across four games).

The bimodal trigger means two different coaching interventions depending on opponent quality — keep him engaged vs weak D, scheme easier looks vs strong D. No single strategy addresses both.

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

**June 2026 extensions reframed the project** without changing the raw Screen A–D results: opponent adjustment explains the cohort-wide playoff effect (but Harden retains +7.1pp adjusted increase); RS retention baselines show contraction is a stable trait; trigger taxonomy (Screen F) replaces failure-mode taxonomy as the primary axis. Pass 2 proceeds as supporting evidence — see [`open_questions.md`](open_questions.md) §5.

What survives is a **reframed finding**:

> The critical differentiator among star players in the playoffs is not what happens when they have a bad game (contraction vs. forcing) but *why* bad games happen. Floor-game trigger type — opponent-independent (Harden, PG), scheme-dependent (SGA), or disengagement-dependent (Butler) — determines whether playoff risk is unpredictable, gameplan-able, or system-manageable. Two players can share the same failure mechanism with completely different frequency patterns (Harden contracts and floors often; Butler contracts and barely floors), because the trigger is different. The public “choke” narrative misdiagnoses trigger conditions as clutch psychology.

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
| Situational contractor | Butler | Contracts by mechanism (vol 68%) but floor rate −4.2pp; inverted opponent pattern (floors vs weak D, rises vs strong D) |
| Forcer | Durant, Curry, Iverson | FGA retention >90%; efficiency collapse |
| Bimodal forcer | DeRozan | Mixed/forcer (vol 42%) + rim abandonment; floors vs weak AND strong D; "choker" reputation is Toronto-specific |
| **Bimodal mixed** | **Donovan Mitchell** | Mixed (vol 41%) + rim abandonment in floor games; floors vs weak D (disengagement) AND strong D (scheme-suppressed); two triggers require two interventions |
| Inverse contractor | Westbrook, CP3 | Floor *more* vs weak D (disengagement when not forced) |
| **Forcer (standard trigger)** | **Kyrie Irving** | FGA retention 91% PO; keeps shooting through slumps; efficiency collapses; standard trigger = no opponent condition predicts floors; "clutch god" is sampling artifact |
| **Shrinker (standard trigger, rare floor)** | **Tobias Harris** | Vol 59% (shrinker); FGA retention drops −28pp RS→PO; FTA retention with ≥25 min drops −41pp; but floor rate only 11.1% — catastrophic contraction when it happens, but it rarely happens |

**Key finding (Butler + DeRozan):** Mechanism and frequency are independent dimensions. Butler has Harden's mechanism (contraction) with the opposite frequency pattern (floor rate decreases). DeRozan has PG's rim-abandonment symptom without the FGA collapse. The public narrative confuses mechanism with frequency — calling Butler a "playoff riser" and DeRozan a "choker" misdiagnoses both. See [`butler_derozan_case_study.md`](butler_derozan_case_study.md) for full analysis.

---

## Limitations

1. ~~**No opponent adjustment**~~ — **Done.** Cohort effect explained; Harden-specific pattern persists.
2. **Peer sample still modest** — 31 players; PG (17 PO floor games), SGA (8), Fox (5), Harris (9) underpowered for structural claims.
3. **Game Score is offense-only** — Does not capture defensive variability. Cannot distinguish disengagement from scheme suppression from random variance within a game. See Gap 4 in [`CRITICAL_GAPS.md`](CRITICAL_GAPS.md).
4. **Season-level opponent DEF_RATING** — No game-level or series-level scheme adjustment.
5. **Age and team context** — Not controlled (partially mitigated by player + season FE in causal chain).
6. **Minutes contamination** — Partially addressed (≥25 min filter); possession-level decontamination still needed.
7. **Causal chain not yet run** — Does failure mechanism predict team ORtg? Revised plan uses continuous `fga_retention` on floor games with player FE and `game_score` control; tests H1/H2/H3 symmetrically. See [`causal_chain_plan.md`](causal_chain_plan.md).
8. **Reverse causality in mechanism** — Does contraction *cause* bad team offense, or does bad team offense *cause* contraction? Game-level data cannot resolve this. Pass 2 temporal ordering (does usage drop follow personal cold start or team collapse?) is the strongest available mitigation.
9. **Leverage score is constructed** — Not WP-based.
10. **Trigger taxonomy is descriptive, not predictive** — No split-sample validation; no evidence trigger types are stable across career halves. See Gap 1 in [`CRITICAL_GAPS.md`](CRITICAL_GAPS.md).
11. **Classification thresholds are overfit by construction** — Hard-coded `classify_trigger()` thresholds tuned on this cohort; bimodal category especially fragile given sample sizes; no null model showing the taxonomy finds more structure than chance. See Gap 3 in [`CRITICAL_GAPS.md`](CRITICAL_GAPS.md).
12. **No causal identification** — Correlations between opponent quality and floor rates are narrated as "triggers" but could reflect team-quality confounds. See Gap 2 in [`CRITICAL_GAPS.md`](CRITICAL_GAPS.md).
13. **Narrative confidence outruns evidence** — "Harden's bad games are a coin flip" is stated from a gradient of +0.12 with p=0.124. Statistical support does not warrant the confidence of the prose.

---

## Pipeline Notes (March 2026)

The initial scrape had critical bugs (wrong NBA player IDs mapping Kyrie → Jokić, Klay → Draymond, Ray Allen → Lorenzen Wright; API 500 crash after ~65 minutes). These were fixed:

- Player IDs corrected; Unicode normalization for Dončić name verification
- Per-player scrape isolation with cooldown on failure
- Stale raw/processed data purged and full pipeline re-run
- Final Pass 1 sample (March 2026): 11 players, 11,683 games, all screens A–E passing
- June 2026 expansion: 18 players, ~20,000 games; extensions added (`screen_a_adj.py`, `rs_retention_baseline.py`, `event_frequency.py`)
- June 2026 fourth wave: 31 players, ~31,000 games; Fox, Harris, Kyrie Irving, Mitchell added; critical structural gaps documented

---

## Suggested Next Steps

### Priority order (June 17 2026, revised)

1. **Foul-type video classification** — The missing variable that could close the predictive loop. Classify shooting fouls by type (rim-finishing contact, perimeter foul-drawing, rip-through, transition) using NBA.com video review data. If foul type predicts FTA shift direction, the full chain becomes: RS foul-type composition → predicted FTA shift → predicted PO floor risk. See [`foul_type_video_plan.md`](foul_type_video_plan.md).
2. **Causal chain — FTA shift → team outcomes** — Reframe the causal chain around continuous FTA shift (not trigger type or mechanism). Among floor games, does the FTA shift predict team ORtg after controlling for individual performance? Infrastructure exists (`join_causal_table.py`); regressions need re-specification.
3. **Expand cohort for FTA shift stability** — The split-half stability test (r = 0.45) uses 28 players. Adding 10–15 more stars with sufficient PO samples could tighten the CI and test whether the trait is truly stable enough for projection.
4. **Game-level FTA shift model** — The current game-level multilevel model uses season-level RS FTA dependency as the cross-level predictor. A within-season model using per-game FTA shift (game-level PO FTA/36 minus RS season FTA/36) could test whether the FTA shift signal is game-specific or player-specific.

### If writing up now

The honest paper is not "Harden chokes in the clutch." It is:

**"Playoff floor-game risk is predicted by what happens to a player's free throw attempts, not by psychology or clutch pressure. Players whose FTA per 36 drops from regular season to playoffs have significantly more floor games (r = −0.53, p = 0.002), driven by a single-action collapse: foul-dependent scoring (drive + contact + whistle) fails as a unit when rim access is denied. The FTA shift is moderately stable across career halves (r = 0.45) but not stable enough to predict future floor rates, because the missing variable — what *type* of contact generates the free throws — is not observable in box-score data."**

The descriptive contributions are publishable: FTA-FGA co-collapse as a mechanism, the "playoff whistle" debunking, contraction stability, and four honestly reported negative predictive results (trigger taxonomy, architecture model, shot-chart independence, RS opponent-gradient). The predictive claim requires foul-type classification to close.

---

## Output Files

| File | Description |
|------|-------------|
| `data/processed/analysis_table.csv` | Full game-level table (~31k rows) |
| `data/processed/screen_a_results.csv` | Variance shift per player |
| `data/processed/screen_a_adj_results.csv` | Opponent-adjusted floor rates |
| `data/processed/retention_baselines.csv` | RS vs PO FGA/FTA/min retention |
| `data/processed/screen_b_results.csv` | Within-series floor rates |
| `data/processed/screen_c_results.csv` | Peer rankings |
| `data/processed/screen_d_results.csv` | Leverage concentration |
| `data/processed/screen_e_results.csv` | Floor-game mechanism profiles |
| `data/processed/event_frequency_estimates.csv` | Pass 2 Event A/B projections |
| `data/processed/architecture_career_table.csv` | Career-average architecture + PO floor rate |
| `data/processed/architecture_season_table.csv` | Season-level architecture + PO outcomes |
| `data/processed/shot_chart_architecture.csv` | Per-player-season shot-chart features |
| `data/processed/fta_collapse_profiles.csv` | FGA/FTA co-collapse profiles per player |
| `data/processed/rq_game_level.csv` | Game-level Resilience Quotient |
| `output/figures/fta_dependency_deepdive.{png,svg}` | FTA shift analysis figures (4-panel) |
| `documents/development/DEVELOPER.md` | Onboarding — setup, pipeline, what's done vs. open |
| `documents/development/pass1_plan.md` | Original research design |
| `documents/development/open_questions.md` | Resolved decisions + remaining gaps |
| `documents/development/causal_chain_plan.md` | Causal chain Steps 0–4 (Step 0 complete) |
| `documents/development/foul_type_video_plan.md` | Video-based foul-type classification plan |

---

## One-Paragraph Summary

The strongest predictor of playoff floor-game risk is what happens to a player's free throw attempts: players whose FTA per 36 drops from regular season to playoffs have significantly more floor games (r = −0.53, p = 0.002, n = 31). The mechanism is a single-action collapse — FGA and FTA co-collapse (r = +0.43, p = 0.016) because foul-dependent scoring (drive + contact + whistle) fails as a unit when rim access is denied (RA shift → FTA shift: r = +0.52, p = 0.003). This is NOT the "playoff whistle" narrative — the cohort-wide FTA shift is zero (15/31 increase), but individual variation is large and moderately stable across career halves (split-half r = 0.45, sign concordance 79%): Harden consistently loses 1.1 FTA/36, LeBron consistently gains 0.4, Dirk gains 1.7. The FTA shift is significant at the game level controlling for opponent quality (multilevel β = −0.024, p = 0.019) and operates as a base-rate risk factor (interaction null, p = 0.226). However, the trait is not stable enough to predict future floor rates (H1 → H2 floor rate: r = −0.16, p = 0.40), because the missing variable — what *type* of contact generates the free throws — is not in the data. The predictive question requires foul-type video classification to determine whether the fouls a player draws are from rim-finishing contact (which increases under playoff physicality) or perimeter foul-seeking (which evaporates).

---

## Phase A: Trigger Taxonomy Validation (June 14, 2026) — TAXONOMY RETIRED

### Summary

The 5-bucket trigger taxonomy (Screen F) failed split-sample validation and is retired as the primary axis. The project pivots to an architecture-prediction framing.

### Results

| Test | Method | Result | Verdict |
|------|--------|--------|---------|
| A1: Threshold sensitivity | Parameterized `classify_trigger()` across gradient/bimodal/weak-floor grids | 4/31 (13%) swing under ±0.03 | **PASS** |
| A2: Null model | 1000 permutations of `is_floor_primary` within each player's PO games | Bimodal p=0.072; gradient signal p=0.009 | **MIXED** |
| A3: Bayesian classification | Beta posteriors on tercile floor rates | 25/31 concordance; 13/31 (42%) uncertain | **CAUTION** |
| A4: Split-sample | Split careers by median date, re-classify each half independently | **8/26 (31%) concordance; 6/26 (23%) gradient direction stability** | **FAIL** |
| A5: Bootstrap CIs | 1000 resamples per tercile per player | 26/31 (84%) weak-strong CI overlap | **WARNING** |

### Key player results (A4)

| Player | Full career | 1st half | 2nd half | Stable? |
|--------|------------|----------|----------|---------|
| James Harden | opponent-independent | opponent-independent | scheme-dependent | No |
| Joel Embiid | opponent-independent | standard | disengagement | No |
| SGA | disengagement | disengagement | disengagement | **Yes** |
| Jimmy Butler | disengagement | opponent-independent | standard | No |
| Dirk Nowitzki | standard | standard | standard | **Yes** |
| LeBron James | standard | standard | standard | **Yes** |

### What this means

1. **The categorical 5-bucket taxonomy is not a stable player trait.** Labels change across career halves for 69% of eligible players.
2. **Even the continuous gradient flips sign for 77% of players.** The opponent-sensitivity signal is real at the full-career level but not stable within career halves.
3. **The fundamental problem is statistical power.** Splitting ~130 PO games into halves → ~65 per half → ~22 per tercile → ~3 floor games per tercile per half. Sampling error overwhelms the signal.
4. **What survives:** Contraction as a stable trait (r = 0.72). Opponent adjustment killing the aggregate effect. The mechanism taxonomy (Screen E). Individual player profiles at the full-career level.

### The "playoff whistle" finding

Separately confirmed: the cohort does NOT show a systematic FTA decline in the playoffs. 15/31 players increase FTA/36; 16/31 decrease. Cohort mean shift: −0.05 FTA/36 (effectively zero). Among high-FTA stars (RS FTA/36 ≥ 7): Harden −13.3%, Luka −12.6%, Butler −10.9%, Embiid −10.5%, but also SGA +2.7%, Giannis +3.6%, LeBron +5.3%, Durant +5.7%. The blanket "playoff whistle" narrative is not supported.

### Project pivot: architecture prediction

The trigger taxonomy was a productive dead end. The project's new primary question:

> **Can you predict a star's playoff floor-game risk from their regular-season scoring architecture?**

Key variables: FGA retention (stable trait), FTA dependency, scoring-mode concentration, rim-abandonment index. See `DEVELOPER.md` for the build spec.

### Scripts

| Script | Phase A test |
|--------|-------------|
| `src/trigger_sensitivity.py` | A1 (sensitivity), A2 (null model), A3 (Bayesian), A5 (bootstrap) |
| `src/validate_trigger_stability.py` | A4 (split-sample) |

### Output files

| File | Description |
|------|-------------|
| `data/processed/trigger_sensitivity.csv` | Classification per threshold combination |
| `data/processed/trigger_null_model.csv` | Null model results (1000 permutations) |
| `data/processed/trigger_bayesian.csv` | Bayesian posterior probabilities |
| `data/processed/trigger_bootstrap_cis.csv` | Bootstrap 95% CIs per tercile |
| `data/processed/trigger_split_sample.csv` | Split-sample concordance table |

---

## Phase B: Box-Score Architecture Model (June 14, 2026) — FAILED (R² = 0.128)

### Summary

The box-score architecture model tested whether RS scoring architecture (FGA retention, FTA dependency, HHI scoring concentration, % points from FT) predicts PO floor-game rate. Career-level R² = 0.128. Below the pre-registered 0.25 bar. Player-season pooled R² = 0.010. The model does not clear any reasonable threshold for predictive contribution.

### Results

**Career-level bivariate correlations with PO floor rate (n=31):**

| Variable | r | p | Interpretation |
|---|---|---|---|
| RS FTA/FGA ratio | **+0.303** | **0.098** | Foul-dependent scorers floor more — only marginal signal |
| % points from FT | **+0.313** | **0.086** | Same signal via different measure |
| RS floor rate | -0.258 | 0.162 | Higher RS floor rate weakly predicts lower PO floor rate (regression to mean) |
| HHI scoring (3-mode) | -0.182 | 0.328 | Null — concentration doesn't predict vulnerability |
| RS FGA retention | -0.056 | 0.763 | Null — the stable trait does NOT predict frequency |
| RS FTA retention | -0.003 | 0.988 | Null |

**Career-level multivariate OLS (n=31):** R² = 0.128, Adj R² = -0.006. No individual predictor significant at p < 0.05.

**Player-season pooled (n=225):** R² = 0.010. Architecture variables have no within-cohort predictive power at the season level.

### Why box-score HHI fails

Harden has the **lowest** HHI in the cohort (0.341 — most diversified) yet the **5th-highest** PO floor rate (21.5%). The 3-mode decomposition (2PM / 3PM / FT point shares) treats Harden as a balanced scorer across three modes. But two of his modes — rim attacks (2PM from drives) and foul drawing (FT from the same drives) — are mechanically the same action. When the whistle tightens, both collapse simultaneously. A 3-mode scorer with 2 correlated modes behaves like a 1-mode scorer under stress.

The HHI measures *spread*, not *independence*. The thesis requires per-shot zone data to decompose FGA into independent scoring modes and measure whether they collapse together or separately.

### What survives

1. **FTA dependency is the only architecture signal.** r = +0.30, p = 0.098 — marginal but directionally consistent with the Harden thesis. The higher the foul-drawing rate relative to FGA, the more vulnerable the player is to playoff floor games.
2. **FGA retention is a stable trait that does NOT predict frequency.** This is itself a finding: *how* a player contracts (vol_share) is consistent RS-to-PO (r = 0.72), but it does not predict *how often* floor games occur. Mechanism and frequency remain independent at the architecture level.

### Next step: shot chart data

The `shotchartdetail` API endpoint provides per-shot `ACTION_TYPE` and `SHOT_ZONE_BASIC`, enabling a 5-mode HHI (RA, Paint, Mid, 3PT, FT) and mode-independence metrics. See shot chart integration plan for implementation spec.

### Scripts

| Script | Phase B component |
|--------|-------------------|
| `src/architecture_model.py` | Full pipeline: season architecture, PO outcomes, career + season regressions, figures |

### Output files

| File | Description |
|------|-------------|
| `data/processed/architecture_career_table.csv` | Career-average architecture + PO floor rate per player |
| `data/processed/architecture_season_table.csv` | Season-level architecture + PO outcomes (n=225) |
| `output/figures/architecture_career_scatter.{png,svg}` | FTA dependency and HHI vs PO floor rate |
| `output/figures/architecture_correlation_heatmap.{png,svg}` | Variable correlation matrix |

---

## Phase C: Shot-Chart Architecture Model (June 15, 2026) — FAILED (mode_independence_score has no discriminative power)

### Summary

The shot-chart architecture model extended the box-score model with per-shot zone data from `shotchartdetail`. The key new variable — `mode_independence_score` (average absolute pairwise correlation of per-game mode shares across 4 FGA zones) — was designed to capture whether a player's scoring modes collapse together or independently. The metric has **no discriminative power**: the range across 31 players is 0.315–0.340. All players appear equally mode-independent. The combined box-score + shot-chart model does not meaningfully improve on the box-score alone (R² = 0.128).

### Why mode_independence_score failed

The metric computes average absolute pairwise Pearson correlation of per-game zone shares (share_ra, share_paint, share_mid, share_three) across all RS games for a player-season. The problem is structural: per-game zone shares are compositional (they sum to 1.0 for FGA zones), so when one zone share goes up, others mechanically go down. This induces negative correlations between all zone pairs, compressing the average absolute correlation into a narrow band. The metric cannot distinguish Harden's correlated rim+FT collapse from Durant's balanced absorption because the compositional constraint dominates the signal.

### Mode-collapse profiles: the descriptive salvage

While the predictive model failed, the per-mode floor-game collapse profiles (computed in `shot_chart_features.py`) are the most diagnostically interesting output:

| Player | RA collapse | 3PT collapse | FT collapse | Interpretation |
|--------|------------|-------------|------------|---------------|
| **James Harden** | −0.024 | **−0.109** | **+0.113** | 3PT share drops 11pp; FT share *rises* 11pp — FT can't compensate for 3PT failure |
| **Kevin Durant** | +0.001 | −0.026 | +0.025 | Balanced minor shifts — no mode dominates, no catastrophic collapse |
| **Joel Embiid** | **−0.057** | −0.012 | **+0.064** | Rim attacks dry up; FT share rises as compensation fails |
| **Stephen Curry** | +0.051 | **−0.078** | +0.005 | 3PT collapse with mild RA absorption — limited secondary mode |
| **Klay Thompson** | +0.054 | **−0.137** | +0.029 | Pure 3PT shooter — when threes fail, nothing absorbs |
| **Paul George** | **+0.066** | −0.042 | −0.016 | RA share *increases* in floor games — he drives more but inefficiently |
| **Trae Young** | +0.026 | **−0.122** | +0.047 | 3PT collapse with FT absorption attempt |

**Key finding:** FT share *increases* in floor games for foul-dependent players (Harden +11pp, Embiid +6pp). This contradicts the "playoff whistle stops their fouls" narrative. The FT mode doesn't collapse — it *can't compensate*. When the 3PT mode fails, these players lean on foul drawing, but the fouls alone cannot carry the offense.

### Output files

| File | Description |
|------|-------------|
| `data/processed/shot_chart_architecture.csv` | Per-player-season shot-chart features |
| `data/processed/shot_chart_career_table.csv` | Career averages + PO floor rate |
| `data/processed/architecture_combined_career_table.csv` | Combined box+shot-chart career table |

---

## Phase D: RS Opponent-Independence → PO Floor Rate (June 15, 2026) — MARGINAL, FRAGILE

### Question

Do players who floor equally against strong and weak opponents during the regular season have a higher frequency of floor games in the playoffs than those whose floor games are opponent-dependent?

This reframes the retired trigger taxonomy (Screen F) as a predictive question: the RS opponent-gradient is an observable regular-season statistic that could, in principle, predict playoff risk.

### Method

For each player, compute the RS opponent-gradient: `floor_rate_vs_weak_D − floor_rate_vs_strong_D` using league-wide opponent DEF_RATING terciles. Absolute gradient measures opponent-dependence (high = floors only against certain opponent types; low = floors regardless of opponent). Then test whether RS |gradient| predicts PO floor-game rate at the career level (n=30).

### Results

**Career-level correlation (n=30):**

| Test | r | p | Direction |
|------|---|---|-----------|
| RS |gradient| → PO floor rate | **−0.315** | **0.090** | Opponent-independent RS floorers have marginally higher PO floor rates |
| RS gradient (signed) → PO floor rate | −0.201 | 0.287 | No directional signal |

**Bootstrap (10,000 resamples):** Mean r = −0.302, 95% CI = [−0.607, +0.090]. The CI crosses zero.

**Binary split (flat |gradient| < 0.10 vs steep):**

| Group | n | Mean PO floor rate |
|-------|---|--------------------|
| Flat RS (|grad| < 0.10) | 8 | 15.6% |
| Steep RS (|grad| ≥ 0.10) | 22 | 14.9% |
| Difference | — | +0.7pp, p = 0.80 |

**Sensitivity (leave-one/two-out):**

| Exclusion | r | p |
|-----------|---|---|
| Full sample (n=30) | −0.315 | 0.090 |
| Without Jokic + Giannis (n=28) | −0.120 | 0.544 |
| Without Embiid (n=29) | −0.407 | 0.028 |
| Without Ray Allen (n=29) | −0.304 | 0.109 |

**Player-season level (n=97):** Simpson's paradox — correlation *flips positive* (r = +0.222, p = 0.029) when aggregated at season level instead of career level. With player FE, the effect disappears (p = 0.15). Season-level PO floor rates are estimated from 3–15 games and are too noisy to be reliable.

### Interpretation

The direction is consistent with the hypothesis: players whose RS floor games are opponent-independent (flat gradient across weak/strong defenses) have marginally higher PO floor rates. But the evidence is weak and fragile:

1. The continuous correlation (r = −0.315, p = 0.09) is marginal.
2. The binary split shows essentially no difference (0.7pp).
3. The signal is driven by two leverage points: Jokic (huge coaster gradient, 4% PO floor) and Giannis (huge coaster gradient, 10% PO floor). Removing them kills the result.
4. The bootstrap 95% CI includes zero.
5. The season-level reversal (Simpson's paradox) suggests the career-level aggregation is doing heavy lifting and may be overfitting to the specific composition of this cohort.

**The honest answer to the question "do RS opponent-independent floorers have higher PO floor rates?" is: directionally yes, but we cannot confirm it with this sample. The pattern is suggestive and theory-consistent but underpowered and leverage-dependent.**

### Per-player RS opponent gradient table

| Player | RS floor (weak D) | RS floor (strong D) | RS gradient | |RS gradient| | PO floor rate |
|--------|-------------------|---------------------|-------------|-------------|---------------|
| Trae Young | 14.3% | 12.8% | +0.015 | 0.015 | 25.9% |
| Klay Thompson | 17.3% | 14.9% | +0.024 | 0.024 | 15.2% |
| John Wall | 18.5% | 22.1% | −0.036 | 0.036 | 10.8% |
| LeBron James | 19.1% | 13.9% | +0.051 | 0.051 | 11.6% |
| Allen Iverson | 15.3% | 21.4% | −0.061 | 0.061 | 16.9% |
| Kevin Durant | 18.1% | 11.8% | +0.063 | 0.063 | 12.9% |
| Kobe Bryant | 15.8% | 7.7% | +0.081 | 0.081 | 12.7% |
| Russell Westbrook | 12.1% | 21.4% | −0.093 | 0.093 | 18.5% |
| Ray Allen | 15.7% | 4.5% | +0.112 | 0.112 | 28.7% |
| Stephen Curry | 20.7% | 9.1% | +0.116 | 0.116 | 8.4% |
| Kyrie Irving | 21.6% | 8.6% | +0.130 | 0.130 | 18.5% |
| **James Harden** | **20.9%** | **7.8%** | **+0.131** | **0.131** | **21.5%** |
| Paul George | 22.6% | 9.2% | +0.134 | 0.134 | 15.2% |
| Dirk Nowitzki | 13.5% | 26.9% | −0.135 | 0.135 | 6.9% |
| Chris Paul | 10.2% | 24.2% | −0.140 | 0.140 | 17.4% |
| Damian Lillard | 23.3% | 8.9% | +0.143 | 0.143 | 23.5% |
| Ben Simmons | 5.3% | 21.5% | −0.162 | 0.162 | 17.9% |
| DeMar DeRozan | 24.9% | 7.2% | +0.176 | 0.176 | 15.9% |
| Tobias Harris | 26.3% | 8.4% | +0.179 | 0.179 | 11.1% |
| Richard Hamilton | 19.5% | 0.0% | +0.195 | 0.195 | 10.0% |
| Jalen Brunson | 29.4% | 9.4% | +0.200 | 0.200 | 4.7% |
| Shai Gilgeous-Alexander | 29.4% | 9.0% | +0.204 | 0.204 | 14.8% |
| Luka Doncic | 33.3% | 12.4% | +0.210 | 0.210 | 14.5% |
| De'Aaron Fox | 30.6% | 8.1% | +0.225 | 0.225 | 17.9% |
| Donovan Mitchell | 33.3% | 10.2% | +0.231 | 0.231 | 16.0% |
| Joel Embiid | 33.3% | 10.0% | +0.234 | 0.234 | 27.3% |
| Jimmy Butler | 29.0% | 4.0% | +0.250 | 0.250 | 10.8% |
| Jayson Tatum | 35.9% | 8.4% | +0.275 | 0.275 | 11.8% |
| Giannis Antetokounmpo | 37.7% | 1.7% | +0.361 | 0.361 | 10.7% |
| Nikola Jokic | 44.2% | 4.5% | +0.398 | 0.398 | 4.0% |

Positive gradient = coasts vs weak D (floors more against weak defenses). Negative gradient = scheme-suppressed (floors more against strong defenses).

---

## Phase E: FTA Shift Deep-Dive (June 17, 2026) — PROJECT'S STRONGEST FINDING

### Summary

The FTA per-36 shift (PO minus RS) is the strongest predictor of playoff floor-game rate the project has found. r = −0.528, p = 0.002, bootstrap 95% CI [−0.722, −0.279] (excludes zero). Players who lose free throw attempts in the playoffs have significantly more floor games. Combined with FGA shift in a two-predictor model: R² = 0.396.

### How this finding emerged

The starting question was whether FTA dependency (RS FTA/FGA ratio) could be made into an airtight risk factor. The deep-dive revealed:

1. **FTA dependency itself is marginal at career level** — r = +0.303, p = 0.098 (season-averaged); r = +0.232, p = 0.209 (career-summed). Bootstrap CI crosses zero. Embiid is a leverage point (removing him drops r from +0.30 to +0.11).
2. **FTA dependency IS significant at the game level** — multilevel model (n = 3,269 PO games, 31 players): β = −0.024, p = 0.019. The game-level model uses 100x the observations and handles the multilevel structure properly.
3. **But the real signal is the FTA shift** — not how many FTAs you attempt, but whether that number goes up or down in the playoffs. This variable (r = −0.528) is 2x stronger than RS FTA dependency (r = +0.303) and passes every robustness check.

### Results

**Career-level: FTA per-36 shift → PO floor rate (n=31)**

| Test | r | p |
|------|---|---|
| Pearson | −0.528 | 0.002 |
| Spearman | −0.473 | 0.007 |
| Bootstrap 95% CI | [−0.722, −0.279] | Excludes zero |
| Leave-one-out max influence | 0.051 (Brunson) | No single player dominates |
| Controlling for RS FTA dependency | β = −0.040, p = 0.005 | Survives; RS FTA dependency goes null (p = 0.53) |

**Combined model (FTA shift + FGA shift → PO floor rate):**

| Variable | β | p |
|----------|---|---|
| FTA per-36 shift | −0.036 | 0.005 |
| FGA per-36 shift | −0.015 | 0.027 |
| R² = 0.396 | | |

**FTA shift by player (sorted, PO minus RS FTA per 36):**

| Player | FTA shift | PO floor rate |
|--------|-----------|---------------|
| De'Aaron Fox | −1.8 | 17.9% |
| Joel Embiid | −1.2 | 27.3% |
| Luka Doncic | −1.1 | 14.5% |
| James Harden | −1.1 | 21.5% |
| Jimmy Butler | −0.8 | 10.8% |
| Allen Iverson | −0.7 | 16.9% |
| ... | ... | ... |
| LeBron James | +0.4 | 11.6% |
| Jalen Brunson | +1.3 | 4.7% |
| Dirk Nowitzki | +1.7 | 6.9% |

### Mechanism: single-action collapse

**FGA-FTA co-collapse:** r = +0.428, p = 0.016. When a player's FGA drops in floor games, FTA drops too. This supports the thesis that for foul-dependent scorers, driving and foul-drawing are the same action. When the rim is walled off, both the shot attempt and the foul disappear simultaneously.

**RA shift → FTA shift:** r = +0.521, p = 0.003. Players who lose restricted area shot share in the playoffs also lose free throw attempts. Losing rim access costs FTAs.

**Drive shift → FTA shift:** r = +0.518, p = 0.003. Same story via action type: players who attempt fewer driving actions in PO also lose FTAs.

**FTA dependency → FTA collapse magnitude:** r = −0.347, p = 0.056. Borderline — more FTA-dependent players have larger FTA drops in floor games, but does not clear p < 0.05.

### Multilevel model: FTA dependency at game level

Game-level linear probability model (n = 3,269 PO games, 31 players), is_floor as DV:

| Model | FTA dep β | p | Opp quality β | p | Interaction β | p |
|-------|-----------|---|---------------|---|---------------|---|
| Opponent only | — | — | −0.023 | 0.001 | — | — |
| Main effects | −0.024 | 0.019 | −0.026 | 0.001 | — | — |
| Interaction | −0.024 | 0.025 | −0.025 | 0.001 | −0.009 | 0.226 |

ICC (player) = 0.022 — only 2% of floor-game variance is between-player. Floor games are overwhelmingly a game-level phenomenon, not a player-level trait.

The interaction is null: FTA dependency is a **base-rate risk factor**, not modulated by opponent quality. FTA-dependent players don't floor more specifically against elite defenses — they floor more in general.

### Split-half stability: is FTA shift a career trait?

**Split-half correlation (n=28 players with 4+ PO seasons):** r = +0.451, p = 0.016. **Sign concordance: 79% (22/28 same direction in both halves).**

Consistently negative (lose FTAs): Harden (−0.30, −1.79), Embiid (−0.21, −2.49), Butler (−1.18, −1.14), Iverson (−1.01, −1.57), DeRozan (−1.42, −1.29).

Consistently positive (gain FTAs): LeBron (+0.22, +0.21), Dirk (+0.52, +1.12), Paul George (+0.98, +0.44), Brunson (+0.96, +0.85), Mitchell (+1.18, +0.34).

Sign flippers (6/28, 21%): Giannis (+0.05, −1.88), Tatum (+1.60, −0.57), Durant (−0.41, +0.65), Kyrie (+0.27, −0.59), Simmons (−0.67, +0.52), Westbrook (+0.09, −0.22).

### The predictive test: FAILS

**H1 FTA shift → H2 PO floor rate:** r = −0.164, p = 0.403. Bootstrap CI [−0.434, +0.125] (crosses zero).

The trait is stable enough to replicate *itself* across career halves (r = 0.45), but not stable enough to predict future floor-game rates (r = −0.16). The FTA shift explains floor games within the same time period (retrospectively) but does not carry predictive power across time.

### Why the predictive test fails — the missing variable

RS FTA dependency → FTA shift is only r = −0.254, p = 0.168. Being FTA-dependent in the regular season does NOT reliably predict losing FTAs in the playoffs. Butler (0.538 RS FTA/FGA) loses 0.8 FTA/36. Giannis (0.525) gains 0.3. The RS RA share → RA shift is null (r = 0.03, p = 0.86). Knowing where a player shoots in the RS doesn't predict whether he'll lose rim access in playoffs.

The missing variable is **foul type**: what kind of contact action generates the free throws. The hypothesis is that players whose FTAs come from rim-finishing contact (LeBron, Giannis) maintain or increase FTAs under playoff physicality, while players whose FTAs come from perimeter foul-drawing (Harden, Embiid) lose FTAs as refs tighten and defenders adjust. This is not measurable from box scores or PBP data — it requires video classification. See [`foul_type_video_plan.md`](foul_type_video_plan.md).

### Scripts

| Script | Component |
|--------|-----------|
| `src/fta_dependency_deepdive.py` | Full pipeline: threshold analysis, mode-collapse bridge, multilevel model, robustness |

### Output files

| File | Description |
|------|-------------|
| `data/processed/fta_collapse_profiles.csv` | Per-player FGA/FTA collapse in PO floor games |
| `output/figures/fta_dependency_deepdive.{png,svg}` | 4-panel figure: scatter + bootstrap + co-collapse + FTA share |
