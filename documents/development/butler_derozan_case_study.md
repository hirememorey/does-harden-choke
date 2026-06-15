# Butler & DeRozan Case Studies: Stress-Testing the Failure-Mode Taxonomy

**Date:** June 2026  
**Context:** Butler added to cohort (19 players, ~22k games). DeRozan already in cohort but under-profiled. Both selected as strategic contrasts: Butler (perceived elite playoff riser) and DeRozan (perceived classic playoff shrinker) stress-test whether the taxonomy captures real structure or artifacts of the original sample.

**One-sentence finding:** Butler and DeRozan reveal that the critical question isn't *what happens* in a floor game (contraction vs. forcing) but *why floor games happen* (trigger type). Butler's trigger is disengagement (floors vs weak D, rises vs strong); DeRozan's trigger is bimodal (floors at both ends of opponent spectrum). Together they force a pivot from mechanism to trigger as the project's primary axis.

---

## Executive Summary

The existing contractor/forcer taxonomy was built on players whose floor-game **frequency** increases in the playoffs. Butler and DeRozan invert that expectation — and reveal that the more fundamental axis is **trigger type** (why floor games happen), not mechanism (what happens in them):

| Player | Public narrative | Actual floor-rate shift | Actual mechanism | Verdict |
|--------|-----------------|------------------------|------------------|---------|
| Jimmy Butler | Elite playoff riser | **−4.2pp** (15% → 11%) | Shrinker (vol_share 68%) | Mechanism is contraction; frequency is inverted |
| DeMar DeRozan | Classic playoff choker | **+0.8pp** (15% → 16%) | Mixed/forcer (vol_share 42%) | Narrative is Toronto-specific; not a contractor |

The taxonomy needs an upgrade: **mechanism** (what happens in a floor game) and **frequency** (how often floor games occur) are independent dimensions. A player can have Harden's mechanism (contraction) without Harden's problem (elevated floor rate).

---

## 1. Jimmy Butler

### Sample

| Context | Games | Mean GS | Floor rate |
|---------|-------|---------|------------|
| Regular season | 907 | 16.63 | 15.0% |
| Playoffs | 130 | 18.08 | 10.8% |
| — Miami playoffs | 64 | 21.6 | 3.1% |
| — Chicago playoffs | 38 | 13.3 | 26.3% |
| — Philadelphia playoffs | 12 | 17.1 | 8.3% |
| — GSW playoffs | 11 | 17.6 | 9.1% |

Butler's playoff floor rate **decreases** by 4.2pp — one of the largest declines in the cohort (only Curry −7.4pp, Hamilton −5.1pp, Wall −4.1pp are larger). This is the opposite of a "choker."

But the **mechanism** in those rare floor games is pure contraction:

### Mechanism (Screen E)

| Metric | Floor games | Non-floor games | Delta |
|--------|-------------|-----------------|-------|
| FGA/36 | 9.5 | 15.2 | −5.7 |
| FTA/36 | 2.3 | 6.9 | **−4.7** |
| PTS/36 | 8.0 | 21.1 | −13.2 |
| AST/36 | 1.7 | 4.7 | −3.0 |
| Minutes | 27.0 | 39.1 | −12.0 |
| FTA/FGA | 0.240 | 0.457 | **−0.217** |

Butler is classified **shrinker** (vol_share 68%) — the second-highest in the cohort behind SGA (77%). When he floors, he stops attacking the rim completely. His FTA/FGA drops from 0.457 to 0.240 — the largest rim-abandonment signal in the dataset (PG is −0.262, but PG's absolute FTA/FGA non-floor is lower at 0.355).

### Retention baselines (floor ≥25 min)

| Metric | RS | Playoffs | Shift |
|--------|-----|----------|-------|
| FGA retention | 75% | 64% | −11pp |
| FTA retention | 33% | 30% | −3pp |

Butler's PO FGA retention (64%) is the **3rd lowest** in the cohort (SGA 63%, Wall 74%). His FTA retention (30%) is the **2nd lowest** (PG 23%). By mechanism alone, Butler looks like a harder contractor than Harden.

### The paradox: mechanism says contractor, frequency says riser

Butler's opponent stratification reveals the resolution:

| Opponent quality | Floor rate | n |
|-----------------|------------|---|
| Weak defense | **19%** | 48 |
| Average defense | 10% | 54 |
| Strong defense | **2%** | 41 |

This is the **inverse** of Harden's pattern. Harden floors against weak defenses (33%) and less against strong ones (16%). Butler floors against weak defenses (19%) and almost never against strong ones (2%). The direction is flipped.

**Interpretation:** Butler is a **situational contractor** — his contraction is triggered by *disengagement*, not by opponent pressure. Against elite defenses, he locks in. Against weak defenses, he coasts — and coasting is when contraction happens. The mechanism (stop attacking, FTA collapse, minutes drop) is the same as Harden's, but the trigger is inverted.

### Team-context dependence

Butler's Miami playoff performance (3.1% floor rate, 21.6 mean GS) is one of the most dominant playoff profiles in the entire cohort. His Chicago playoff performance (26.3% floor rate, 13.3 mean GS) is one of the worst. No other player in the cohort shows this level of team-context variation.

This suggests Butler's contraction is **system-dependent** in a different way than SGA. SGA contracts when opponents take away his driving lanes (scheme-dependent). Butler contracts when the *system doesn't demand him* — when the offensive architecture doesn't force engagement. Miami's system (Himmy Buckets, full creator autonomy) forces engagement. Chicago's system (more structured, less on-ball creation burden) allows coasting.

### Elimination games

| Context | Floor rate | Mean GS |
|---------|------------|---------|
| Elimination | 8% | 17.6 |
| Non-elimination | 12% | 18.3 |

No leverage concentration. Floor rate slightly lower in elimination games.

### Classification

**Situational contractor** — contracts by mechanism (vol_share 68%, FTA ret 30%) but not by frequency (floor rate −4.2pp). Contraction triggered by disengagement/context, not opponent pressure. Inverse opponent pattern distinguishes from all existing archetypes.

---

## 2. DeMar DeRozan

### Sample

| Context | Games | Mean GS | Floor rate |
|---------|-------|---------|------------|
| Regular season | 1,264 | 15.31 | 15.0% |
| Playoffs | 63 | 13.64 | 15.9% |
| — Toronto playoffs | 51 | 13.0 | 19.6% |
| — San Antonio playoffs | 7 | 17.5 | 0.0% |
| — Chicago playoffs | 5 | 14.3 | 0.0% |

DeRozan's overall playoff floor-rate increase is **+0.8pp** — essentially flat. The "playoff choker" narrative is not supported at the career level. The entire reputation is driven by 51 Toronto playoff games where his floor rate was 19.6%.

### Mechanism (Screen E)

| Metric | Floor games | Non-floor games | Delta |
|--------|-------------|-----------------|-------|
| FGA/36 | 14.9 | 18.5 | −3.6 |
| FTA/36 | 4.0 | 6.9 | −2.9 |
| PTS/36 | 10.5 | 22.6 | −12.0 |
| AST/36 | 2.0 | 3.8 | −1.8 |
| TOV/36 | 3.2 | 2.0 | +1.1 |
| Minutes | 33.1 | 38.4 | −5.3 |
| FTA/FGA | 0.270 | 0.372 | −0.102 |
| FG% | 0.248 | 0.440 | **−0.192** |

DeRozan is classified **mixed** (vol_share 42%). His scoring drop is 58% efficiency-driven — he keeps shooting but the shots don't fall. The FG% drop (−0.192) is the **worst in the cohort** alongside Klay Thompson (−0.192).

Key distinction from contractors: DeRozan's FGA retention is 81% — he keeps shooting. His FTA retention is 59% — he loses some free throws but not catastrophically (PG is 23%). This is not contraction; this is **inefficient forcing with rim abandonment**.

### Retention baselines (floor ≥25 min)

| Metric | RS | Playoffs | Shift |
|--------|-----|----------|-------|
| FGA retention | 81% | 81% | −0pp |
| FTA retention | 47% | 59% | +12pp |

FGA retention is **stable** (RS ≈ PO, 81% → 81%). FTA retention actually **increases** in the playoffs — the opposite of PG's −34pp collapse. DeRozan's failure mode is not playoff-specific; it's the same mechanism in RS and PO.

### Opponent stratification

| Opponent quality | Floor rate | n |
|-----------------|------------|---|
| Weak defense | **21%** | 24 |
| Average defense | 5% | 20 |
| Strong defense | **21%** | 19 |

**Bimodal.** DeRozan floors against both weak and strong defenses, but not average ones. This is an unusual pattern — neither opponent-independent (like Harden) nor scheme-dependent (like SGA).

The weak-defense floors suggest disengagement (similar to Butler and Westbrook's "inverse contractor" pattern). The strong-defense floors suggest he can be schemed out of rhythm. Average defenses don't trigger either failure mode.

### Series game breakdown

| Game # | n | Floor rate | Mean GS |
|--------|---|------------|---------|
| 1 | 11 | 18% | 10.2 |
| 2 | 11 | 18% | 14.6 |
| 3 | 11 | 18% | 15.0 |
| 4 | 11 | 27% | 12.2 |
| 5 | 8 | 0% | 16.6 |
| 6 | 7 | 14% | 14.0 |
| 7 | 4 | 0% | 14.0 |

No late-series compounding (H2 already rejected for full cohort). Game 4 is the weakest game; Games 5–7 recover.

### Elimination games

| Context | Floor rate | Mean GS |
|---------|------------|---------|
| Elimination | 13% | 13.0 |
| Non-elimination | 17% | 13.8 |

Slightly lower floor rate in elimination games — no clutch concentration.

### Classification

**Bimodal forcer with rim abandonment** — keeps shooting (FGA ret 81%) but efficiency collapses catastrophically (FG% −0.192). FTA/FGA drops (−0.102) indicating partial rim abandonment without the wholesale contraction of Harden/PG. The "playoff choker" reputation is Toronto-specific (19.6% floor rate) and opponent-bimodal, not a stable career trait. Outside Toronto, his playoff floor rate is 0% (12 games, small sample).

---

## 3. Taxonomy Upgrade

### Current taxonomy (4 archetypes)

| Archetype | Players | Key signature |
|-----------|---------|---------------|
| Trait contractor | Harden | RS≈PO contraction; opponent-independent floors |
| Rim-abandoning contractor | PG | Stable FGA; PO FTA collapse −29pp |
| Scheme-dependent contractor | SGA | Hardest PO contraction; entirely opponent-driven |
| Forcer | Durant, Curry, LeBron, Iverson | FGA retention >90%; efficiency collapse |

### Revised taxonomy (6 archetypes)

| Archetype | Players | Mechanism | Frequency trigger | Opponent pattern |
|-----------|---------|-----------|-------------------|------------------|
| Trait contractor | Harden | Contraction (vol 51%) | Stable, elevated | Independent |
| Rim-abandoning contractor | PG | Contraction via FTA | Elevated vs weak D | Semi-dependent |
| Scheme-dependent contractor | SGA | Contraction (vol 77%) | Opponent-driven | Fully dependent |
| **Situational contractor** | **Butler** | Contraction (vol 68%) | Disengagement/context | **Inverted** (floors vs weak D) |
| Forcer | Durant, Curry, LeBron, Iverson | Efficiency collapse | Stable or decreased | Independent |
| **Bimodal forcer** | **DeRozan** | Mixed (vol 42%) + rim abandonment | Context-dependent | **Bimodal** (weak + strong) |

### Key distinction: mechanism vs. frequency are independent

The original taxonomy conflated *what happens in a floor game* (mechanism) with *how often floor games occur* (frequency). Butler demonstrates these are independent:

- **Mechanism** = contraction (shrinker, vol_share 68%, FTA ret 30%)
- **Frequency** = decreased (floor rate −4.2pp, Miami 3.1%)

Harden has the same mechanism but inverted frequency:
- **Mechanism** = contraction (mixed, vol_share 51%, FTA ret 69%)
- **Frequency** = increased (floor rate +6.6pp, opponent-independent)

The practical implication: scouting reports that say "Butler contracts in bad games" are mechanistically correct but strategically misleading. The right question isn't "what happens when Butler has a bad game?" but "under what conditions does Butler have bad games?" — and the answer is "when he's not challenged," not "when the opponent is elite."

### Opponent-pattern taxonomy

The opponent stratification now shows four distinct patterns:

| Pattern | Players | Weak D floor | Strong D floor | Interpretation |
|---------|---------|-------------|----------------|----------------|
| **Independent** | Harden | 33% | 16% | Floors regardless; weak D doesn't help |
| **Dependent** | SGA | 35% | 0% | Scheme takes away driving lanes |
| **Inverted** | Butler | 19% | 2% | Rises to challenge; coasts otherwise |
| **Bimodal** | DeRozan | 21% | 21% | Disengages vs weak OR gets schemed vs strong |
| Standard | Durant | 16% | 7% | Normal opponent gradient |

---

## 4. Implications

### For the project thesis

The original thesis: "a star's offensive structure determines their failure mode." Butler and DeRozan show this is secondary. The primary axis is **trigger type** — *why* floor games happen, not *what* happens when they do. Offensive structure predicts mechanism (Butler contracts, DeRozan forces) but not frequency or trigger pattern. The scouting-relevant question is "under what conditions does this player floor?" not "what does this player do in a bad game?"

**Revised one-sentence thesis:**

> The critical differentiator among star players in the playoffs is not what happens when they have a bad game but *why* bad games happen — floor-game trigger type (opponent-independent, scheme-dependent, disengagement-dependent) determines whether playoff risk is unpredictable, gameplan-able, or system-manageable; the public narrative misdiagnoses trigger conditions as clutch psychology.

### For the causal chain

Butler's team-context variation (Miami 3% vs Chicago 26%) is the strongest natural experiment in the cohort for testing whether system moderates the mechanism → team outcome relationship. If the causal chain shows that contraction in floor games predicts lower team ORtg (H1), Butler's Miami games (where contraction almost never happens) should show higher team ORtg than his Chicago games (where contraction is frequent). This is a within-player, cross-system test.

### For scouting

The practical payoff of separating mechanism from frequency:

1. **Butler-type players** are *safer* than their mechanism suggests. Yes, when they floor, they contract hard. But the conditions that trigger contraction (disengagement, weak opponent, low-stakes) are predictable and manageable. A coach who keeps Butler engaged won't see the contraction.

2. **DeRozan-type players** are *riskier* than their frequency suggests. His floor rate is only +0.8pp — but his mechanism (efficiency collapse with rim abandonment, FG% −0.192) is devastating when it activates. The trigger is bimodal (both weak and strong D), making it harder to game-plan around.

3. **Harden-type players** are the *hardest* to manage. Same mechanism as Butler, but opponent-independent frequency. You can't scheme away the trigger because there isn't one — the floors are unpredictable.

---

## 5. Data Tables

### Butler vs DeRozan vs taxonomy archetypes (floor ≥25 min)

| Player | Archetype | PO games | RS floor | PO floor | Δ floor | FGA ret PO | FTA ret PO | Floor vs weak | Floor vs strong |
|--------|-----------|----------|----------|----------|---------|------------|------------|--------------|----------------|
| Jimmy Butler | Situational contractor | 130 | 15% | 11% | −4.2% | 64% | 30% | 19% | 2% |
| DeMar DeRozan | Bimodal forcer | 63 | 15% | 16% | +0.8% | 81% | 59% | 21% | 21% |
| James Harden | Trait contractor | 191 | 15% | 21% | +6.6% | 78% | 69% | 33% | 20% |
| Paul George | Rim-abandoning | 125 | 15% | 15% | +0.2% | 72% | 23% | 27% | 17% |
| SGA | Scheme-dependent | 61 | 15% | 15% | −0.3% | 63% | 36% | 35% | 0% |
| Kevin Durant | Forcer | 171 | 15% | 13% | −2.1% | 98% | 69% | 16% | 7% |
| LeBron James | Forcer | 302 | 15% | 12% | −3.5% | 93% | 63% | 14% | 9% |

### Butler team-specific playoff breakdown

| Team | PO games | Floor rate | Mean GS |
|------|----------|------------|---------|
| MIA | 64 | 3.1% | 21.6 |
| GSW | 11 | 9.1% | 17.6 |
| PHI | 12 | 8.3% | 17.1 |
| MIN | 5 | 0.0% | 13.0 |
| CHI | 38 | 26.3% | 13.3 |

### DeRozan team-specific playoff breakdown

| Team | PO games | Floor rate | Mean GS |
|------|----------|------------|---------|
| TOR | 51 | 19.6% | 13.0 |
| SAS | 7 | 0.0% | 17.5 |
| CHI | 5 | 0.0% | 14.3 |

---

## 6. Open Questions

1. **Butler's inverted opponent pattern: robust or artifact?** 2% vs strong D (1/41 games) is a very small count. Need more seasons or a Bayesian approach to estimate the true rate. The direction is consistent with his team-context variation (engagement-driven), but the magnitude may be inflated by sampling.

2. **DeRozan's bimodal pattern: same mechanism, different triggers?** The weak-D floors and strong-D floors might be different failure modes (disengagement vs. scheme) with the same observable outcome (bad game). Possession-level data (Pass 2) could distinguish these.

3. **Mechanism–frequency independence: how general?** Butler is one data point. Are there other situational contractors in the cohort? Westbrook's "inverse contractor" pattern (floors more vs weak D) hints at the same disengagement mechanism. But Westbrook's frequency still increases in the playoffs (+4.3pp) while Butler's decreases (−4.2pp).

4. **System moderates mechanism → outcome?** Butler's Miami/Chicago split is the cohort's best natural experiment for the causal chain. If Step 1 joins team ORtg, test whether Butler's Miami floor games (rare but still present) have the same team-ORtg impact as his Chicago floor games (frequent).
