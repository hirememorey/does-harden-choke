# Pass 2 Design Spec: Adversity Events + Baseline Matching

**Status:** Draft — frozen before first line of code
**Date:** June 2026
**Depends on:** `pass2_research_design.md`, `findings.md` (Pass 1 results)

---

## 0. Purpose

This document specifies the identification strategy for Pass 2. It answers three questions:

1. **What counts as an adversity event?** (observable, repeatable triggers)
2. **What do we compare it to?** (baseline matching logic)
3. **How do we measure the response?** (elasticity computation)

Everything else in the pipeline (PBP ingestion, possession segmentation, clustering) serves these three decisions. If they are wrong, the pipeline produces precise nonsense.

---

## 1. Adversity Event Definitions

### 1.1 Design principles

An adversity event must be:
- **Observable from PBP data** — no subjective judgment required
- **Repeatable** — the same trigger produces the same event flag regardless of who runs the script
- **Player-specific** — the event reflects something that happened to *this player*, not the team generally
- **Pre-response** — the event must precede the response window (no lookahead)

An adversity event must **not** be:
- A description of the player's *response* (that's what we're measuring)
- So common it's meaningless (every missed shot) or so rare it's underpowered (0-for-10 in a half)

### 1.2 MVP events (implement first)

#### Event A: Cold Start

| Field | Value |
|-------|-------|
| **Trigger** | Player has attempted >= 5 FGA and made <= 1 FG (i.e., shooting 1-for-5 or worse) |
| **Scope** | First half only (Q1-Q2) |
| **Emit at** | The possession immediately after the qualifying miss |
| **Minimum FGA** | 5 (prevents 0-for-1 or 1-for-3 noise) |
| **Rationale** | The pass2_research_design.md "MVP Event." Captures the archetype-relevant scenario: a player starts cold, then faces a choice about what to do next. Directly analogous to Screen E's game-level floor games but at within-game grain. |

**Why first-half only?** First-half cold starts give a long response window (rest of the game) and avoid conflating with end-of-game blowout dynamics. Second-half cold starts often occur in garbage time or with limited remaining possessions — the response window is too short.

**Why 1-for-5, not 0-for-5?** A single made basket in 5+ attempts still represents clear adversity — the player's efficiency is catastrophic. Restricting to 0-for-N loses too many events. Sensitivity analysis will test 0-for-5 and 2-for-8 thresholds.

#### Event B: Consecutive Empty Trips

| Field | Value |
|-------|-------|
| **Trigger** | Player has 2 consecutive possessions ending in a missed FGA, a turnover, or a missed FT trip (0-of-2 or worse) — with no made basket, assist, or drawn foul in between |
| **Scope** | Any quarter |
| **Emit at** | The possession immediately after the second empty trip |
| **Minimum** | Both possessions must belong to the target player as terminal actor |
| **Rationale** | Captures within-game "nothing is working" moments. More granular than Cold Start — can happen mid-game after a hot opening. Mirrors the pass2_research_design.md "2 consecutive scoring attempts ending empty." |

**What counts as "the player's possession"?** A possession where the player is the **terminal actor**: took the FGA, drew the shooting foul that led to FTs, or committed the turnover. Assists don't count as "empty" for this purpose (assist = productive outcome even if the shooter missed). Offensive rebounds by the player reset the consecutive counter only if the player scores on the putback — otherwise the trip is still "empty."

#### Event C: Turnover -> Miss Sequence

| Field | Value |
|-------|-------|
| **Trigger** | Player commits a turnover, then on the *next possession where they are the terminal actor*, misses a FGA or misses FTs |
| **Scope** | Any quarter |
| **Emit at** | The possession after the miss |
| **Rationale** | The pass2_research_design.md "turnover followed by a miss." Captures a compounding mistake sequence — turnover then forced shot. More specific than Event B; isolates a particular failure pattern. |

**Edge case:** If the player commits a turnover and doesn't touch the ball for 3+ team possessions, the event should not fire — the turnover and miss are too disconnected. Require that the miss possession occurs within 4 team possessions of the turnover.

### 1.3 Granular events (implement after MVP)

These require tracking data or richer PBP parsing. Do not implement until the MVP pipeline is validated.

| Event | Trigger | Data required |
|-------|---------|---------------|
| **Rim rejection** | Player misses an at-rim attempt without drawing FTs | PBP shot-type or shot-distance fields |
| **Foul denial** | Player drives and misses without FTs (foul not called) | Tracking: drive events + contact detection |
| **Scored-upon run** | Player's direct defender scores 3+ consecutive baskets | Tracking: matchup data |
| **First-half TS% floor** | Player's first-half TS% < 0.300 with >= 8 FTA-equivalent | PBP + computed TS% |

### 1.4 Events we deliberately exclude

| Excluded | Why |
|----------|-----|
| Team-level adversity (opponent run, score deficit) | Not player-specific; confounds team context with individual adversity |
| Bench/substitution as adversity trigger | That's a *response*, not a trigger — belongs in Bucket 4 |
| Any event in garbage time | Response window would be contaminated by blowout behavior |
| "Felt cold" / "looked frustrated" | Not observable from data |

### 1.5 Event deduplication within a game

A single game can produce multiple adversity events. Rules:

1. **Minimum gap:** After an event fires, no new event can fire for the next **4 team possessions**. This prevents cascading events from a single bad stretch.
2. **Maximum events per game:** Cap at **2**. If a player is still triggering events after 2, the game is already a floor game — the marginal event adds no information.
3. **Event priority:** If two event types would fire on the same possession (e.g., both Event A and Event B qualify), emit **Event A** (Cold Start) — it's the more conservative trigger. Log the overlap for audit.
4. **Recovery reset:** If the player records a productive possession (made FG, assist on made FG, or drawn shooting foul) between events, the consecutive counters reset.

### 1.6 Sample scope for MVP

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Season range | 2013-14 through 2024-25 | Tracking era + reliable PBP format |
| Game type | Playoffs only | Higher stakes, more adversity events per game, fewer garbage-time possessions |
| Players | Harden, Durant, Curry, Westbrook, Lillard, Luka, Booker, Tatum, Trae | pass2_research_design.md Section 5; all have >= 50 playoff games in this range |
| Kobe | Qualitative archetype only | Insufficient tracking-era playoff sample |

**RS expansion** (post-MVP): Add regular-season games for statistical power. Requires garbage-time filter to be stricter (more blowouts in RS). Expected to triple the event sample.
## 2. Response Window

### 2.1 Primary definition

**The next 8 team possessions after the adversity event, while the target player is on the court, excluding garbage time.**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Window length | 8 team possessions | ~4 minutes of game time at average pace. Long enough to observe behavioral response; short enough to maintain causal proximity to the event. |
| Player must be on court | Yes | Off-court possessions tell us nothing about the player's response. |
| Exclude garbage time | Yes | See Section 2.3 |
| Stop at game end | Yes | If < 8 qualifying possessions remain, the window is partial. |

### 2.2 Partial windows

If the player is subbed out mid-window or the game ends:

- **Complete window:** Player is on court for all 8 possessions. Primary analysis sample.
- **Partial window (sub-out):** Player leaves before 8 possessions. Record the partial window + flag `is_partial = True`. Include in sensitivity analysis only — the sub-out itself may be part of the response (Bucket 4).
- **Partial window (game end):** Game ends before 8 possessions. Record partial + flag. Include in primary analysis if >= 5 possessions observed; exclude otherwise.

**Minimum window size for inclusion: 5 possessions.** Below this, per-window metrics are too noisy to be informative.

### 2.3 Garbage time definition

A possession is garbage time if **any** of:

| Rule | Condition | Source |
|------|-----------|--------|
| Q4 blowout | Q4 and absolute margin >= 20 | Score from PBP |
| Q3 blowout | Q3 and absolute margin >= 30 | Score from PBP |
| Win probability | WP < 0.05 or > 0.95 (if available) | Computed or external |

For the MVP (playoffs only), Q4 margin >= 20 is sufficient — playoff blowouts of 20+ are rare and usually genuine. The Q3 rule and WP rule are for the RS expansion where blowouts are common.

**Garbage-time possessions are excluded from both the response window and the baseline pool.** They do not exist for the purpose of this study.

---

## 3. Baseline Matching

This is the identification core. Without a valid baseline, "elasticity" measures game state, not adversity response.

### 3.1 The identification problem

We want: `elasticity = behavior_after_adversity - behavior_in_normal_conditions`

The naive baseline is the player's season averages. This is wrong because:

1. **Game script confound:** After a cold start (Event A), the team is likely losing. Behavior in "losing by 8 in Q2" is systematically different from "season-average behavior" regardless of adversity.
2. **Pace confound:** A losing team plays faster -> more possessions -> different usage rates.
3. **Opponent confound:** Playoff opponents are better than average -> lower baseline efficiency.
4. **Clock confound:** Late-clock possessions are structurally different from early-clock possessions.

We need a baseline that holds game-state constant and varies **only** whether the player has experienced adversity.

### 3.2 Baseline definition: Same-game, pre-event pool

For each adversity event, the baseline is constructed from **possessions in the same game, before the event, with the target player on the court, in a comparable game state.**

| Match dimension | Strata | Rationale |
|-----------------|--------|-----------|
| **Game** | Exact same game | Controls for opponent, game plan, rest days, venue |
| **Period** | Same quarter (+-1 if event is in Q2) | Controls for coaching rotation patterns |
| **Score margin bucket** | Within 5 / 6-10 / 11-15 / 16+ | Controls for game script without over-stratifying |
| **Pre-event only** | Possessions before the adversity event fired | Ensures baseline behavior is not contaminated by the player's post-adversity response |

**Why same-game, not cross-game?** Cross-game baselines (e.g., "same player vs. same opponent in a different game") introduce between-game variance that swamps the within-game signal. The adversity response we're measuring operates on a possession-to-possession timescale — the comparison should too.

**Why pre-event only?** If we used post-event possessions as baseline, we'd be comparing "behavior after adversity" to "behavior after adversity + some recovery," which underestimates the adversity effect. If we used all non-response-window possessions, we'd contaminate the baseline with the player's response to the adversity event (which may persist beyond the 8-possession window).

### 3.3 Minimum baseline size

Require >= 8 qualifying baseline possessions per event. If the pre-event pool is too small (e.g., event fires in Q1 with few prior possessions), the event is still recorded but flagged `baseline_underpowered = True`. These events enter a sensitivity analysis only — they do not appear in primary results.

### 3.4 Baseline metrics

For each baseline pool, compute the same four buckets as the response window:

| Bucket | Baseline metric | Computed from |
|--------|----------------|---------------|
| 1. Possession ownership | Mean terminal-event share, mean usage rate, mean late-clock share | PBP |
| 2. Attack persistence | Mean drives/touch, mean rim-attack rate, mean FT-generation rate, mean pull-up 3 rate | Tracking (or PBP proxies) |
| 3. Redistribution | Mean assists per possession, mean teammate usage, mean potential assists | PBP + tracking |
| 4. Coach trust | Mean stint length (possessions until next sub), mean minutes remaining in game | PBP substitution events |

### 3.5 What the baseline does NOT control for

| Uncontrolled factor | Why it's acceptable | Mitigation |
|---------------------|--------------------|------------|
| Within-game fatigue | Event A fires in Q1-Q2; fatigue is minimal at that point | Sensitivity: exclude events after Q2 |
| Opponent tactical adjustment (within game) | This IS part of the adversity — opponent sees the player struggling and defends differently | Not a confound — it's the mechanism |
| Player's own momentum (hot hand / cold hand) | The whole point of the study | Placebo test (Section 6.3) |
| Random variance in small samples | 8-possession windows are noisy | Aggregate to player-level profiles across many events |

### 3.6 Alternative baseline designs (for sensitivity analysis)

| Alternative | How it works | When to use |
|-------------|--------------|-------------|
| **Cross-game matched** | Same player, same opponent, same quarter, similar margin — different game | Primary baseline fails (too few pre-event possessions) |
| **Season-stratified** | Same player, same quarter, same margin bucket, across the season | Maximizes sample size; loses game-specific control |
| **Random-possession baseline** | Same game, random non-adversity timestamp, 8 possessions | Placebo arm — should produce near-zero elasticity |
## 4. Elasticity Computation

### 4.1 Event-level elasticity

For each adversity event `e` and each metric `m`:

```
delta_m_e = response_m_e - baseline_m_e
```

where:
- `response_m_e` = mean of metric `m` across the 8-possession response window
- `baseline_m_e` = mean of metric `m` across the matched baseline pool

**Standardized elasticity** (primary metric):

```
elasticity_m_e = delta_m_e / sd_player_m
```

where `sd_player_m` is the **within-game standard deviation** of metric `m` for this player, computed from all non-garbage-time possessions in the same game. This puts all metrics on a comparable scale and adjusts for game-specific variance.

If within-game SD is unstable (too few possessions), fall back to the player's **playoff-level SD** of per-game metric `m`.

### 4.2 Player-level elasticity profile

Aggregate across all events for a player:

| Field | Definition |
|-------|------------|
| `mean_elasticity_m` | Mean of `elasticity_m_e` across all events for this player |
| `median_elasticity_m` | Median (robust to outlier events) |
| `n_events` | Total adversity events observed |
| `n_complete_windows` | Events with complete (non-partial) 8-possession windows |
| `pct_negative_m` | Fraction of events where `elasticity_m_e < 0` (direction-specific) |

### 4.3 The identification discriminator: Redistribution vs. Contraction

This is the core diagnostic from the pass2_research_design.md. It must be computed as an **explicit feature**, not left to clustering alone.

**Redistribution index:**

```
redistribution_index = mean_elasticity_assists - mean_elasticity_usage
```

- **Positive** = assists preserved while usage drops -> redistributive adjustment
- **Negative** = both assists and usage drop -> contractive collapse
- **Near-zero** = assists and usage move together -> forcing or mixed

**Classification rule (for labeling, not hard assignment):**

| Condition | Label |
|-----------|-------|
| `elasticity_usage >= -0.3` AND `elasticity_efficiency < -0.5` | **Forcing** — preserves volume, efficiency collapses |
| `elasticity_usage < -0.5` AND `redistribution_index < -0.3` | **Contractive** — volume and creation both collapse |
| `elasticity_usage < -0.5` AND `redistribution_index > +0.3` | **Redistributive** — volume drops, creation preserved |
| All other combinations | **Mixed** — no clean archetype; defer to clustering |

Threshold values (-0.3, -0.5, +0.3) are initial guesses. They should be validated against known cases:

- **Harden** (Pass 1 Screen E: vol_share = 0.52, mixed/shrinker) -> should classify as Contractive or mixed-leaning-contractive
- **Durant** (Pass 1 Screen E: vol_share = 0.25, forcer) -> should classify as Forcing
- **Chris Paul** (not in Pass 1, but the pass2_research_design.md archetype) -> should classify as Redistributive

If these three don't separate cleanly, the thresholds need adjustment before clustering.

### 4.4 Bridge to Pass 1

For each player, compare:

| Pass 2 metric | Pass 1 analog | Expected relationship |
|---------------|---------------|----------------------|
| `mean_elasticity_usage` | Screen E `vol_share` | Negative elasticity_usage <-> high vol_share (both measure volume contraction) |
| `mean_elasticity_assists` | Screen E `ast_36_delta` | Same sign (assist drop in both) |
| `redistribution_index` | No direct analog | New to Pass 2; tests the identification trap |
| `mean_elasticity_minutes` | Screen E `min_delta` | Same sign (minutes contraction) |

If Pass 2 elasticity directions are **inconsistent** with Pass 1 game-level profiles, the within-game event study is measuring something different from the game-level pattern. That's a finding, not a bug — but it must be reported explicitly.
## 5. Data Dictionary

### 5.1 `possessions` table

One row per possession per game.

| Column | Type | Source | Notes |
|--------|------|--------|-------|
| `game_id` | str | PBP | NBA game ID |
| `season` | str | config | e.g., "2023-24" |
| `is_playoff` | bool | config | |
| `possession_idx` | int | derived | Sequential index within game (0-based) |
| `period` | int | PBP | Quarter (1-4, 5+ for OT) |
| `start_clock` | str | PBP | e.g., "11:22" |
| `end_clock` | str | PBP | |
| `offensive_team` | str | PBP | 3-letter abbreviation |
| `defensive_team` | str | PBP | |
| `score_margin` | int | PBP | Offensive team's margin at possession start |
| `terminal_player_id` | int | PBP | Player who ended the possession (FGA, TOV, shooting foul drawn) |
| `terminal_event_type` | str | derived | "fga_miss", "fga_make", "tov", "shooting_foul_drawn", "ft_trip" |
| `is_garbage_time` | bool | derived | Per Section 2.3 |
| `players_on_court` | list[int] | PBP subs | All 10 player IDs on court during this possession |
| `shot_distance` | float | PBP | In feet, if available |
| `shot_zone` | str | PBP | "rim", "midrange", "3pt" (if available) |
| `is_fast_break` | bool | PBP | If available |
| `assist_player_id` | int | PBP | Player who assisted (if any) |
| `seconds_remaining` | int | derived | Seconds remaining in period (for late-clock classification) |

### 5.2 `adversity_events` table

One row per detected adversity event.

| Column | Type | Notes |
|--------|------|-------|
| `event_id` | str | `{game_id}_{player_id}_{possession_idx}` |
| `game_id` | str | |
| `player_id` | int | |
| `player_name` | str | |
| `season` | str | |
| `is_playoff` | bool | |
| `event_type` | str | "cold_start", "consecutive_empty", "tov_then_miss" |
| `possession_idx` | int | Possession index where event fires |
| `period` | int | |
| `game_clock` | str | Clock when event fires |
| `cumulative_fga` | int | Player's FGA to this point in the game |
| `cumulative_fgm` | int | Player's FGM to this point |
| `cumulative_tov` | int | Player's TOV to this point |
| `score_margin` | int | Player's team margin at event time |
| `is_garbage_time` | bool | |
| `baseline_n_possessions` | int | Number of qualifying baseline possessions |
| `baseline_underpowered` | bool | True if baseline_n_possessions < 8 |
| `is_first_event_in_game` | bool | |
| `event_sequence` | int | 1 or 2 (max 2 per game per Section 1.5) |

### 5.3 `response_windows` table

One row per event with metric columns.

| Column | Type | Notes |
|--------|------|-------|
| `event_id` | str | FK to adversity_events |
| `window_length` | int | Qualifying possessions observed (5-8) |
| `is_partial` | bool | |
| `partial_reason` | str | "sub_out", "game_end", or null |
| `terminal_event_share` | float | Bucket 1: player-ended possessions / team possessions |
| `usage_rate_window` | float | Bucket 1: (FGA + 0.44*FTA + TOV) / team possessions |
| `late_clock_share` | float | Bucket 1: share of terminal events with <= 5s on clock |
| `rim_attack_rate` | float | Bucket 2: rim FGA / total FGA (PBP proxy for drives/touch) |
| `ft_generation_rate` | float | Bucket 2: FT trips / total possessions as terminal actor |
| `pullup_3_rate` | float | Bucket 2: pull-up 3 FGA / total FGA (tracking only) |
| `assist_rate` | float | Bucket 3: assists / team possessions while on court |
| `teammate_usage_delta` | float | Bucket 3: teammate usage in window - teammate usage in baseline |
| `potential_assist_rate` | float | Bucket 3: tracking only |
| `possessions_until_sub` | int | Bucket 4: how many possessions until player is subbed out |
| `minutes_remaining` | float | Bucket 4: game minutes remaining after event |

### 5.4 `baseline_pools` table

Same schema as `response_windows`, computed for the matched baseline possessions per event.

| Column | Type | Notes |
|--------|------|-------|
| `event_id` | str | FK to adversity_events |
| `baseline_n_possessions` | int | |
| `baseline_margin_bucket` | str | "within_5", "6_to_10", etc. |
| `baseline_period` | int | |
| (all metric columns from response_windows) | | Same metrics, computed from baseline possessions |

### 5.5 `elasticity` table

One row per event per metric, or pivoted to one row per event.

| Column | Type | Notes |
|--------|------|-------|
| `event_id` | str | FK to adversity_events |
| `metric` | str | e.g., "terminal_event_share", "usage_rate_window" |
| `response_value` | float | |
| `baseline_value` | float | |
| `delta` | float | response - baseline |
| `within_game_sd` | float | Player's within-game SD for this metric |
| `elasticity` | float | delta / within_game_sd |
| `sd_source` | str | "within_game" or "playoff_level" (fallback) |

### 5.6 `player_profiles` table

One row per player.

| Column | Type | Notes |
|--------|------|-------|
| `player_id` | int | |
| `player_name` | str | |
| `n_events` | int | |
| `n_complete_windows` | int | |
| `mean_elasticity_usage` | float | |
| `mean_elasticity_efficiency` | float | |
| `mean_elasticity_assists` | float | |
| `mean_elasticity_minutes` | float | |
| `mean_elasticity_rim_attack` | float | |
| `redistribution_index` | float | mean_elasticity_assists - mean_elasticity_usage |
| `pct_contractive_events` | float | Fraction of events where usage elasticity < -0.5 AND redistribution_index < -0.3 |
| `archetype_label` | str | "forcing", "contractive", "redistributive", "mixed" |
| `cluster_id` | int | From clustering (post-hoc) |
## 6. Validation Plan

### 6.1 Possession parser validation

Before any event detection runs, validate the possession builder:

| Check | Method | Pass criterion |
|-------|--------|-----------------|
| Possession count | Compare team possession count to published game pace * (minutes/48) | Within +-3 possessions |
| Usage reconstruction | Reconstruct USG% from terminal events; compare to box score | Within +-3 percentage points |
| Known-game spot check | Manual review of 10 possessions in 3 known games | >= 9 of 10 match expected |
| Substitution accuracy | Reconstruct on-court lineups from sub events; compare to known lineups | Error rate < 5% of possessions |

**Validation games (initial set):**

| Game | Why |
|------|-----|
| HOU vs SAS, 2017-05-11 (Game 6) | Harden 2-11 FG, 10 pts — iconic floor game. Event A should fire. |
| GSW vs CLE, 2016-06-13 (Game 5) | LeBron 41 pts — no adversity event should fire (unless he started cold). |
| BOS vs PHI, 2023-05-14 (Game 7) | Harden 3-11 FG, 9 pts — Event A should fire. |
| Any 2024 playoff game with tracking | Validate tracking <-> PBP consistency. |

### 6.2 Event detection validation

| Check | Method |
|-------|--------|
| Event A fires on known cold starts | Harden 2017 G6 starts 2-11 -> should trigger by ~FGA 5 |
| Event A does NOT fire on hot starts | Curry 30-pt first half -> should not trigger |
| Event B fires on consecutive empty trips | Harden misses -> turnover -> should trigger |
| Deduplication works | Same game doesn't produce 5+ events |
| Garbage-time exclusion works | Q4 blowout possessions excluded from event detection |

### 6.3 Placebo test (critical)

**Design:** For each player-game in the sample, select **2 random non-adversity timestamps** (possessions where no event fires) and construct the same 8-possession response window + baseline.

**Expected result:** Placebo elasticity should be centered near 0 for all metrics. If it's not, the baseline matching is flawed or the metric computation is biased.

**Implementation:** Run the full pipeline on placebo "events" before analyzing real events. If placebo elasticity for any metric has |mean| > 0.2, investigate and fix before proceeding.

### 6.4 Screen E concordance check

For each player, compare Pass 2 `archetype_label` to Pass 1 Screen E `mechanism`:

| Pass 2 label | Pass 1 mechanism (renamed) | Expected concordance |
|--------------|---------------------------|---------------------|
| Forcing | Forcer | High |
| Contractive | Shrinker / mixed (high vol_share) | High for shrinker; mixed may split |
| Redistributive | No direct analog | New finding |
| Mixed | Mixed | Low — by definition ambiguous |

**Vocabulary mapping (Pass 1 -> Pass 2):**

| Pass 1 term | Pass 2 term | Rationale |
|-------------|-------------|-----------|
| shrinker | contractive | Behavioral, not evaluative |
| forcer | forcing | Consistent tense |
| mixed | mixed | Retained — genuinely ambiguous |
| quits / disappears | contracts / relinquishes possessions | Behavioral, not moral |
| killer instinct | assumes authorship | Behavioral, not evaluative |
| chokes | contracts under adversity | Behavioral, not moral |

---

## 7. Edge Cases and Decision Log

### 7.1 Edge cases resolved

| Case | Decision | Rationale |
|------|----------|-----------|
| Player enters game already in adversity (cold bench player) | Include if thresholds met — the event is still a valid adversity trigger | The trigger is about the player's performance, not the team's |
| Multiple adversity types fire simultaneously | Emit highest-priority event (A > B > C); log overlap | Prevents double-counting the same bad stretch |
| Adversity event in OT | Include — OT is high-leverage, not garbage time | OT possessions are competitive by definition |
| Player fouls out mid-window | Treat as sub-out (partial window) | Bucket 4 captures the fouling-out as a response |
| Technical foul / ejection after adversity | Exclude the ejection possession from the window; flag as partial | Ejection is a distinct event, not a behavioral response to adversity |
| Delayed-event games (e.g., COVID suspension) | Use game_id, not calendar date, for joins | Same rule as Pass 1 |

### 7.2 Open decisions (resolve before implementation)

| Decision | Options | Default |
|----------|---------|---------|
| Should Event A trigger on 1-for-5 or require 0-for-5? | 1-for-5 (more events) vs 0-for-5 (cleaner signal) | 1-for-5 for MVP; test 0-for-5 in sensitivity |
| Should baseline match on exact quarter or allow +-1? | Exact (cleaner) vs +-1 (more baseline possessions) | +-1 for Event A in Q2 (Q1 baseline too small otherwise); exact for Events B/C |
| Minimum possessions for a valid baseline | 6 vs 8 vs 10 | 8 for primary; 6 for sensitivity |
| Should tracking-only metrics (Bucket 2) gate event detection? | No — PBP events trigger regardless; tracking enriches the response window | No gating |
| Cluster k for archetype detection | k=3 (theory-driven) vs data-driven | k=3 primary; test k=2 and k=4 in sensitivity |

---

## 8. Implementation Sequence (Spec-Driven)

The spec is now frozen. Implementation order:

| Step | Module | Depends on | Validation gate |
|------|--------|------------|-----------------|
| 1 | PBP ingestion (`src/pass2/ingest_pbp.py`) | Game IDs from Pass 1 | Fetch 3 known games; spot-check event types |
| 2 | Possession builder (`src/pass2/possessions.py`) | Ingested PBP | Validation games (Section 6.1); possession count within +-3 |
| 3 | Garbage-time tagger (`src/pass2/garbage_time.py`) | Possessions | Known blowout games correctly flagged |
| 4 | Adversity event detector (`src/pass2/adversity_events.py`) | Possessions + garbage flags | Harden 2017 G6 triggers Event A; hot games don't trigger |
| 5 | Response window extractor (`src/pass2/response_windows.py`) | Events + possessions | 8-possession windows correctly sliced; partials flagged |
| 6 | Metric computation (`src/pass2/metrics.py`) | Windows + baseline pools | USG% reconstruction within +-3pp of box score |
| 7 | Baseline matching (`src/pass2/baselines.py`) | Events + possessions | Baseline pool >= 8 possessions for >80% of events |
| 8 | Elasticity computation (`src/pass2/elasticity.py`) | Metrics + baselines | Placebo test mean elasticity < 0.2 for all metrics |
| 9 | Player profiles + archetype labeling (`src/pass2/profiles.py`) | Elasticity | Harden -> Contractive; Durant -> Forcing |
| 10 | Clustering + visualization (`src/pass2/cluster.py`) | Profiles | k=3 recovers 3 interpretable archetypes |

**No step may begin until the previous step's validation gate passes.** The possession builder (Step 2) is the critical-path correctness dependency — if it drifts, everything downstream is compromised.

---

## 9. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| NBA tracking endpoints unreliable or restricted | High | Bucket 2/3 metrics degraded | PBP-only MVP first; tracking is enrichment, not gate |
| Possession parser produces wrong terminal-actor assignments | Medium | All downstream metrics wrong | Validation games + USG% reconstruction check |
| Pre-event baseline pool too small for Q1 events | Medium | Many events flagged `baseline_underpowered` | Allow +-1 quarter matching for Event A; cross-game fallback |
| Garbage-time filter too aggressive (playoffs) | Low | Excludes competitive possessions | Q4 >= 20 is conservative for playoffs; relax to >= 25 if too many excluded |
| Clustering doesn't recover 3 archetypes | Medium | Results harder to interpret | Fall back to 2-cluster (forcing vs contracting); report continuous redistribution index |
| PBP format changes across seasons | Medium | Parser breaks on older games | Version-detect PBP format; test on 2013-14 and 2024-25 endpoints separately |

---

## 10. Definition of Done

Pass 2 is "implemented" when:

1. **Event-level elasticity table** exists for the star cohort with all four buckets (or documented PBP-only substitutes for tracking-dependent metrics)
2. **Harden vs Durant vs CP3-style contrast** is visible on the redistribution vs contraction axis — the doc's core identification trap
3. **Clustering** recovers three interpretable archetypes without using player names as inputs
4. **Placebo test passes**: mean |elasticity| < 0.2 across all metrics for random-event baselines
5. **Sensitivity memo** documents: MVP vs granular events, 6 vs 8 possessions, playoffs-only vs pooled
6. **Bridge paragraph** to Pass 1: "Screen E showed game-level contraction; Pass 2 [shows/does not show] it begins N possessions after in-game adversity"
