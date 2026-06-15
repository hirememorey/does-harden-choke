# Does Harden Choke? — Findings

**Date:** June 2026 (Pass 1: March 2026; extensions: June 2026)  
**Project:** `does-harden-choke`  
**Status:** Pass 1 complete (Screens A–E) + extensions (opponent adjustment, RS retention baselines, event frequency). Pass 2 parser validated; possession analysis at spike scale (~69 games).

**Cohort:** 31 players, ~31,000 games in `analysis_table.csv`

---

## Executive Summary

The original hypothesis asked whether James Harden's playoff reputation reflects a **variance shift** that **compounds late in series** because opponents adapt to heliocentric offense — and whether that pattern distinguishes Group A from Group B.

**Verdict (updated):** The adaptation story is dead (H2 rejected). The aggregate "playoffs cause more floor games" story is also dead after opponent adjustment. What survives is a **trigger taxonomy**.

### How we got here (resolved background)

The project began by asking *how* stars fail in the playoffs — do they **contract** (stop shooting) or **force** (keep shooting inefficiently)? That contractor/forcer mechanism taxonomy (Screen E) answered its question and is now settled. The key finding was negative: mechanism and frequency are independent. Butler contracts like Harden but barely floors in the playoffs. Two players can fail the same way at completely different rates. So *how* a star fails does not tell you *how often* or *when* they will fail. The mechanism split helped us ask the right follow-up question — what determines **when** the failure happens? — but it is not itself the primary axis. A new reader should treat Screen E as resolved context, not an active research question.

### The actual finding: trigger taxonomy (Screen F)

Stars' floor games are triggered by different conditions, and the **trigger type** — not the failure mechanism — is what matters for scouting and team-building:

| Trigger | Definition | Players | Scouting implication |
|---------|-----------|---------|---------------------|
| **Opponent-independent** | Floors vs weak and strong D alike | Harden, PG, Embiid, Klay | Unpredictable — can't scheme it away |
| **Scheme-dependent** | Floors only vs elite D | SGA, Westbrook, Trae, Simmons | Gameplan-able — elite D suppresses |
| **Disengagement** | Floors vs weak D, rises vs strong | Butler, Ray Allen, Giannis, Haliburton | System-dependent — keep engaged |
| **Bimodal** | Floors vs both weak and strong D | DeRozan, Iverson, Wall, Curry, Luka | Two different triggers |
| **Standard** | No distinctive pattern | Durant, LeBron, Kobe, CP3, Lillard, **Dirk**, Brunson, Tatum, Jokic, Hamilton | Mild gradient |

### The KAT/Harden framing

The 2025 NBA Finals discourse claims Karl-Anthony Towns "shed the loser label." But KAT didn't change — the Knicks' elite defense hides his floor weaknesses (can't anchor, gets played off the floor) by ensuring he never has to. To a fan, KAT looks like he discovered clutch grit. The data says the system removed the conditions that exposed him.

This is the distinction the trigger taxonomy captures. **Scheme-dependent** triggers (SGA, Simmons) are like KAT — the right system can hide them. **Opponent-independent** triggers (Harden, PG, Embiid) are the opposite — you can't build a KAT-style system solution because there's no identifiable condition to remove. Harden's bad games are a coin flip; no opponent profile predicts them; no roster construction reliably prevents them unless he's your third option or your #1 isn't also underperforming.

**Dirk Nowitzki** tests the "choker to champion" narrative flip directly. Dirk is classified `standard` trigger, `forcer` mechanism, with a playoff floor rate that **drops** from 15% to 7.1% — he has *fewer* bad games in the playoffs, not more. The 2011 championship didn't require Dirk to change. He was never the choker. 2011 was the year the roster was finally good enough to win when Dirk did what Dirk always did.

### Summary of key findings

1. **Mechanism (contraction vs. forcing) is resolved background** — it helped us get here but is not the primary axis. See Screen E section below.

2. **Contraction is a stable career trait** — RS FGA retention predicts PO FGA retention (r = 0.72). But trait stability of mechanism does not predict frequency.

3. **The public "choke" narrative misdiagnoses trigger as psychology** — calling Butler a "playoff riser" and DeRozan a "choker" confuses mechanism with frequency and misses the actual trigger conditions. Calling Dirk a "choker until 2011" misdiagnoses a roster problem as a player problem.

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

### Priority order (June 2026, revised)

1. **Gap 3: Trigger threshold sensitivity** — Parameterize `classify_trigger()`, run across threshold grid, identify swing players, Bayesian alternative. If taxonomy doesn't survive, other gaps are moot. 1-2 days.
2. **Gap 1: Split-sample trigger validation** — Split careers in half, re-classify independently, null model. 2-3 days.
3. **Causal chain — trigger → team outcomes** — Step 0 done (team logs + validation). Next: join to floor games, then test whether trigger type predicts team ORtg among floor games. See [`causal_chain_plan.md`](causal_chain_plan.md).
4. **Gap 4: Composite floor-game metric** — PCA on Game Score + FTA/FGA engagement + usage drop + +/−; series-level floor detection. 3-5 days.
5. **Gap 2: Causal identification** — Game-level opponent data, Pass 2 temporal ordering, team-season FE. 5-10 days.
6. **Out-of-sample validation** — Train trigger profile on career first half, test on second half
7. **Pass 2 temporal ordering** — Possession-level data can establish whether contraction *follows* a personal cold start (Event A) or *follows* team-wide offensive collapse. This is the strongest available mitigation for the reverse causality threat in the causal chain.

### If writing up now

The honest paper is not "Harden chokes in the clutch." It is:

**"The critical differentiator among star players in the playoffs is not what happens when they have a bad game but why bad games happen — floor-game trigger type (opponent-independent, scheme-dependent, or disengagement-dependent) determines whether playoff risk is unpredictable, gameplan-able, or system-manageable."** Documenting a novel trigger taxonomy, showing that mechanism and frequency are independent dimensions, and testing whether trigger type predicts team outcomes.

If the causal chain shows no trigger effect, the paper is still publishable on the taxonomy alone, but the contribution is descriptive rather than actionable for scouting.

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
| `documents/development/causal_chain_plan.md` | Causal chain Steps 0–4 (Step 0 complete) |

---

## One-Paragraph Summary

James Harden's raw playoff floor-game rate rises from 15% to 22% (χ² *p* = 0.067), but after opponent adjustment the cohort-wide playoff effect disappears (*p* = 0.83) while Harden retains a +7pp adjusted increase with opponent-independent floors (33% vs weak defenses, 16% vs strong). His contraction is not playoff-specific — FGA retention is 75% RS and 74% PO — but it is a stable career trait (r = 0.72 across the cohort) that distinguishes him from forcers like Durant (97% FGA retention in PO floor games). Paul George shares the opponent-independent contraction pattern but via rim abandonment (FTA retention 54%→25% in playoffs); SGA shares the contraction symptom but via scheme dependence (0% floor rate vs strong defenses). Floor games do not compound late in series (H2 rejected) or cluster in elimination games (Harden: 15% elim vs 23% non-elim). The public "choke" narrative misdiagnoses a structural failure mode — contraction under adversity — as clutch psychology.

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
