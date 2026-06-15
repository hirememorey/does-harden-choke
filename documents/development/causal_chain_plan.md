# Causal Chain Plan — Does Floor-Game Mechanism Predict Team Outcomes?

**Date:** June 2026 (revised from mechanism-framing to trigger-framing; **trigger framing retired June 14, 2026**)
**Status:** Step 0 **complete**; Steps 1–4 **not started**; needs revision for architecture-prediction framing
**Blocks:** The practical claim that scoring architecture predicts team outcomes (`open_questions.md` §H)

> **NOTE (June 14, 2026):** The trigger taxonomy (Screen F) failed Phase A split-sample validation (31% concordance) and is retired as the primary axis. This document's trigger-type hypotheses (H1: opponent-independent floors are worse; H2: disengagement floors are less damaging) are no longer viable as stated. The data infrastructure (Step 0) and the per-game `fga_retention` / `fta_retention` secondary analysis remain valid. The next developer should revise Steps 1–4 to test **architecture variables** (FGA retention, FTA dependency, scoring-mode concentration, rim-abandonment index) rather than trigger-type categories. See `DEVELOPER.md` §H and `open_questions.md` §H for the revised framing.

---

## Revision history

The original version of this document (June 2026) framed the causal chain around failure mechanism (contraction vs. forcing) predicting team outcomes.

**First revision** (June 2026): CC1/CC2 demoted to validation gates; primary analysis restricted to floor games; continuous `fga_retention` replaces binary mechanism indicator.

**Second revision** (June 2026): Pivoted from mechanism to trigger as primary axis. The contractor/forcer taxonomy (Screen E) answered its question but is not the headline. Butler and DeRozan showed that mechanism (contraction vs. forcing) and frequency (how often floor games occur) are independent — two players can share the same mechanism with opposite frequency patterns. The differentiator is the *trigger*: what conditions produce floor games. Screen F classifies players into trigger types (opponent-independent, scheme-dependent, disengagement, bimodal, standard). The causal chain now tests whether trigger type predicts team outcomes. The per-game `fga_retention` regressions are retained as a secondary analysis.

**Problem with mechanism-first framing:** Asking "does contraction vs. forcing predict team ORtg?" is interesting but secondary. A GM doesn't care *what* happens in Harden's bad games — they care *whether* those bad games will happen and *when*. Trigger type answers that directly. An opponent-independent trigger means risk is unpredictable; a disengagement trigger means it's manageable with the right system.

**Revised framing:** The primary question is whether trigger type predicts team outcomes. Do opponent-independent floor games hurt teams more than scheme-dependent ones? Does disengagement-triggered contraction have different team consequences than opponent-independent contraction?

---

## Research question (revised)

> Among floor games by high-usage stars, does the trigger type — opponent-independent, scheme-dependent, disengagement-dependent, bimodal, or standard — predict team offensive outcomes, after controlling for individual performance quality?

Screen F established *why* players floor differently. This extension tests whether those trigger differences *matter* for team success — and how much.

### Why trigger type matters more than mechanism

If trigger type predicts team outcomes net of individual performance quality:
- Front offices can price playoff risk based on *predictability* of floor games, not just frequency — an opponent-independent trigger (Harden) is ungameable risk; a disengagement trigger (Butler) is system-manageable
- Coaching staffs can design interventions matched to trigger type — keep a disengagement player involved vs. scheme against a scheme-dependent one
- The "choker" narrative is reframed: the problem isn't what happens in bad games, it's whether you can prevent the bad games from happening

If trigger type does NOT predict team outcomes:
- The taxonomy is descriptively interesting but not actionable for scouting
- The paper contribution is the taxonomy itself (Screen F) plus trait stability (retention baselines)

---

## Hypotheses

### Validation gates (sanity checks, not primary findings)

| ID | Claim | Test | Expected |
|----|-------|------|----------|
| **VG1** | Floor games have lower team ORtg than the same player's non-floor games | Within-player mean comparison | Trivially true; confirms pipeline |
| **VG2** | Floor games have lower win rate | Same | Trivially true |

Run these in Step 2 as two-line checks. If either fails, something is broken in the data join. Do not present as findings.

### Primary hypotheses (trigger type → team outcomes)

| ID | Claim | Prediction |
|----|-------|------------|
| **H1: Opponent-independent floors are worse** | When a star floors regardless of opponent quality, the team has no counter — you can't scheme around an unpredictable trigger, and contraction leaves the offense anchorless | Opponent-independent trigger players show lower team ORtg in floor games than other trigger types, controlling for individual performance |
| **H2: Disengagement floors are less damaging** | When a star floors due to disengagement, the system can compensate — other players step up, and the trigger is manageable with coaching | Disengagement trigger players show higher team ORtg in floor games than opponent-independent players |
| **H3: No difference by trigger type** | Team outcome is determined by individual performance quality, not trigger pattern | Trigger type has no predictive power after controlling for `game_score` |

**Prior expectation:** H1 (opponent-independent is worse) based on the disengagement/contraction mechanism and the observation that Butler's Miami system suppresses floors entirely. But H2 is plausible — if contraction is rational redistribution, the trigger type may not matter for team outcomes.

### Secondary analysis (mechanism → team outcomes, within floor games)

The per-game `fga_retention` regressions from the prior framing are retained as secondary. Among floor games, does the degree of contraction (continuous FGA retention) predict team ORtg? This tests whether *what happens* in a floor game matters net of *why it happened*. Same H1/H2/H3 structure as before but with `fga_retention` as the IV.

### Falsification

If trigger type has no predictive power for team ORtg after controlling for `game_score` and player fixed effects (H3 confirmed), the taxonomy is descriptive only. The paper is still publishable on the trigger taxonomy (Screen F) plus trait stability but cannot make scouting claims about predictability of risk.

---

## Key design decisions

### 1. Restrict primary analysis to floor games

The unit of analysis is **floor games by high-usage stars** (`is_floor_primary == 1`). We are not comparing floor games to non-floor games (that's a validation gate). We are comparing *types* of floor games to each other.

### 2. Use continuous mechanism, not binary

The key independent variable is **continuous `fga_retention`** (FGA/36 in this floor game ÷ player's non-floor FGA/36 baseline), not a binary contractor/forcer label. This is critical for two reasons:

- **Within-player variation:** A binary `mechanism_contractor` label is a *player-level* trait. Including it alongside player fixed effects makes it collinear — the fixed effects absorb it. But continuous per-game `fga_retention` varies *within* players across floor games. Harden doesn't contract identically every time. Some floor games are 2-for-11 with 24 minutes; others are 5-for-16 with 33 minutes. That within-player variation is the identifying variation.

- **Statistical power:** Continuous treatment has more power than binary classification, and avoids arbitrary threshold choices (the 55% vol_share cutoff in Screen E).

### 3. Control for individual performance quality

The regression must control for `game_score` (or an equivalent individual performance measure). Without this control, `fga_retention` will be confounded with "how bad was the floor game" — a player who takes only 5 shots in a terrible game has low retention AND low game score. We need to ask: *holding badness constant, does mechanism matter?*

### 4. Player fixed effects for cross-player comparison

Include `C(player_name)` fixed effects. This controls for all stable player characteristics (skill, role, average teammate quality, system). The identifying variation becomes within-player: across Player X's floor games, does the degree of contraction predict team ORtg?

**Note on cross-player mechanism comparison:** A secondary descriptive analysis (Step 2) can compare Harden floor-game team ORtg to Durant floor-game team ORtg. But this is heavily confounded (different teams, systems, eras) and should be presented as illustrative, not causal.

---

## Endogeneity threats and mitigations

### Threat 1: Selection into mechanism

Why does Harden contract and Durant force? Possible confounds:
- Harden faces better defensive schemes targeting him (so he contracts)
- Durant has worse teammates (so he has to force because no one else can)
- Harden plays in better offensive systems (easier to defer)

**Mitigation:** Player fixed effects control for stable player-level confounds. Within-player variation (Harden contracts *more* in some floor games than others) is less likely to be driven by these factors. Control for `opponent_defrtg` and `is_elimination` to absorb game-level defensive context.

### Threat 2: Reverse causality

Does contraction cause bad team offense, or does bad team offense cause the star to contract? If teammates are cold, Harden may see no good passing options and reduce volume — making contraction a *response to* team collapse, not a *cause of* it.

**Mitigation (game level):** Limited. Controlling for game score partially addresses this (it captures the player's individual performance independent of teammates). But game-level data cannot establish temporal ordering.

**Mitigation (Pass 2):** This is Pass 2's strongest contribution to the causal chain. Possession-level data can establish temporal ordering: does the star's usage drop *follow* a personal cold start (Event A) or *follow* team-wide offensive collapse? If Event A fires (star goes 1-for-5), and *then* the star's usage drops, and *then* team ORtg changes, the reverse causality story is harder to sustain. Pass 2 provides the temporal chain that game-level regressions cannot.

### Threat 3: Definition circularity

Floor games are defined by Game Score, which includes FGA. If a player takes fewer shots, Game Score mechanically drops, which *creates* floor games. So contraction partly *causes* floor-game classification, not just behavior within floor games.

**Mitigation:** FGA enters Game Score with a negative coefficient (−0.7 × FGA), meaning *more* shots actually *lower* Game Score, all else equal. So taking fewer shots does not mechanically lower Game Score — missing more shots does. The circularity concern is therefore limited: FGA retention measures volume independent of the makes/misses that define floor-game status.

### Transparent acknowledgment (for the paper)

> We cannot claim strict causality due to selection and reverse causality concerns. The within-player fixed-effects design isolates variation in mechanism across a player's floor games, which is more plausibly exogenous than cross-player comparisons. Possession-level temporal analysis (Pass 2) provides supplementary evidence on causal direction by establishing that contraction follows personal cold starts rather than preceding them.

---

## Prerequisites

Unchanged from the original plan. Before starting Step 1, regenerate locally:

```bash
make venv
make scrape              # player logs — if not already present
make validate-scrape
make features            # → analysis_table.csv
make scrape-team-logs    # ~50 min full cohort; uses --resume
make validate-team-logs  # must exit 0
```

Step 0 validation gates (June 2026 run):

| Gate | Criterion | Result |
|------|-----------|--------|
| League ORtg sanity | Recent-season mean ORtg 108–118 | **PASS** (2022–25: 114.7–116.4) |
| Join coverage | ≥95% player `(game_id, team_id)` in team logs | **PASS** (100% on 17,024 rows) |
| ORtg reconstruction | API `off_rating` vs `100×pts/poss` within ±1.0 on ≥90% | **PASS** (100%, mean \|delta\| = 0.02) |

---

## Step 0 — Team game logs (DONE)

Unchanged. See original plan for details on `scrape_team_logs.py` and `validate_team_logs.py`.

**Key columns in `team_game_logs.csv`:**

| Column | Source | Use |
|--------|--------|-----|
| `game_id`, `team_id` | API | Join keys |
| `off_rating` | Advanced | **Primary dependent variable** |
| `def_rating` | Advanced | Opponent context control |
| `poss` | Advanced | ORtg validation; pace control |
| `wl` | Base | Win indicator (secondary DV) |
| `plus_minus` | Base | Blowout sensitivity filter |
| `season`, `is_playoff` | derived | Fixed effects |

---

## Step 1 — Join and compute per-game mechanism variables (NEXT)

**Goal:** One analysis-ready table with player floor flags, per-game mechanism metrics, and team outcomes.

### Proposed script

`src/join_causal_table.py` (not yet written)

### Logic

```python
players = pd.read_csv("data/processed/analysis_table.csv")
teams = pd.read_csv("data/raw/team_game_logs.csv")

players["game_id"] = players["game_id"].apply(normalize_game_id)
teams["game_id"] = teams["game_id"].apply(normalize_game_id)

merged = players.merge(
    teams,
    on=["game_id", "team_id"],
    how="inner",
    suffixes=("", "_team"),
)

# Compute per-game FGA retention relative to player's non-floor baseline
baselines = (
    merged[merged["is_floor_primary"] == False]
    .groupby("player_name")
    .agg(
        baseline_fga_per36=("fga", lambda x: (x / merged.loc[x.index, "minutes"] * 36).mean()),
        baseline_fta_per36=("fta", lambda x: (x / merged.loc[x.index, "minutes"] * 36).mean()),
        baseline_ast_per36=("ast", lambda x: (x / merged.loc[x.index, "minutes"] * 36).mean()),
    )
)
merged = merged.merge(baselines, on="player_name", how="left")

# Per-game retention: how much of normal volume did the player maintain?
merged["fga_per36"] = merged["fga"] / merged["minutes"] * 36
merged["fga_retention"] = merged["fga_per36"] / merged["baseline_fga_per36"]
merged["fta_per36"] = merged["fta"] / merged["minutes"] * 36
merged["fta_retention"] = merged["fta_per36"] / merged["baseline_fta_per36"]

# Attach Screen E mechanism labels (for descriptive splits)
screen_e = pd.read_csv("data/processed/screen_e_results.csv")
merged = merged.merge(
    screen_e[["player_name", "mechanism", "vol_share"]],
    on="player_name",
    how="left",
    suffixes=("", "_e"),
)

merged["team_win"] = (merged["wl"] == "W").astype(int)

merged.to_csv("data/processed/causal_analysis_table.csv", index=False)
```

### Columns to carry forward

From `analysis_table.csv`: `player_name`, `is_floor_primary`, `game_score`, `minutes`, `fga`, `fta`, `ast`, `is_playoff`, `opponent_defrtg`, `series_game_num`, `is_elimination`, `plus_minus` (player).

From `team_game_logs.csv`: `off_rating`, `def_rating`, `poss`, `wl`, `pts` (team).

Derived:
- `fga_per36` — FGA per 36 minutes in this game
- `fga_retention` — this game's FGA/36 ÷ player's non-floor mean FGA/36
- `fta_retention` — same for FTA
- `baseline_fga_per36`, `baseline_fta_per36` — player baselines from non-floor games
- `team_win` — `wl == "W"`

### Important: per-game vs. player-level retention

The `fga_retention` and `fta_retention` in `retention_baselines.csv` (from `rs_retention_baseline.py`) are **player-level averages**: mean floor-game FGA/36 ÷ mean non-floor FGA/36. For the regression, we need **per-game** retention: this specific floor game's FGA/36 ÷ the player's non-floor baseline. This captures within-player variation that the player-level average masks.

### Validation gate (Step 1)

| Check | Pass criterion |
|-------|----------------|
| Row count | ≥99% of `analysis_table` rows with valid `team_id` |
| No duplicate keys | One row per `(game_id, player_name)` |
| ORtg non-null | ≥95% `off_rating` populated |
| fga_retention finite | No inf/NaN for floor games with minutes > 0 |
| Spot check | Harden 2017 G6: floor game, low fga_retention, team ORtg and WL match memory |

### Makefile target (to add)

```makefile
join-causal:
	$(PYTHON) src/join_causal_table.py
```

---

## Step 2 — Descriptive analysis

**Goal:** Show the patterns before regression. Build intuition for what the data looks like.

### Proposed script

`src/mechanism_descriptives.py` (not yet written)

### 2a. Validation gates (VG1, VG2)

Per-player: mean team `off_rating` in floor vs. non-floor games; mean `team_win` rate. Confirm floor games are worse on both. Two-line table, not a finding. If any player shows *higher* team ORtg in floor games, investigate the data join.

### 2b. Mechanism-conditional team ORtg in floor games (primary descriptive)

Among floor games only:

| Analysis | What to show |
|----------|-------------|
| Scatter | Per-game `fga_retention` (x) vs. `off_rating` (y), colored by player. Is there a visible slope? |
| Player means | Mean team ORtg in Harden floor games vs. Durant floor games vs. Curry floor games. Raw comparison (confounded, but vivid). |
| Mechanism groups | Mean team ORtg in contractor floor games vs. forcer floor games (using Screen E labels). Report with caveat about cross-player confounding. |
| Within-player | For Harden specifically: split his floor games by above/below-median `fga_retention`. Does team ORtg differ? Same for other players with ≥15 floor games. |

### 2c. Matched comparison (Harden vs. Durant)

Find Harden floor games and Durant floor games matched on:
- `game_score` (within ±3 points)
- `opponent_defrtg` (within ±2 points)
- `is_elimination` (exact match)

Compare team `off_rating` in matched pairs. Report sample size — it will be small, but the comparison is intuitive for a Sloan audience. Present as illustrative, not causal.

### 2d. Teammate efficiency under contraction vs. forcing

For each floor game, compute `teammate_off_rating_proxy`:

```python
team_pts = merged["pts_team"]
player_pts = merged["pts"]  # player's own points
# Very rough: (team_pts - player_pts) as share of team possessions not used by player
```

If contractive floor games show *higher* teammate scoring efficiency, that supports H2 (contraction is rational redistribution). If lower, that supports H1 (contraction leaves the offense anchorless).

This is a rough proxy — team ORtg is not decomposable into player and non-player contributions cleanly from box scores. But the directional signal is informative.

### Output

`data/processed/mechanism_descriptives.csv` — per-player floor-game mechanism metrics with team outcomes.

Figures: scatter of fga_retention vs. team ORtg; bar chart of mechanism-group team ORtg.

---

## Step 3 — Regression models

**Goal:** Estimate the marginal effect of failure mechanism on team outcomes, controlling for individual performance quality and game context.

### Proposed script

`src/mechanism_models.py` (not yet written)

### Model 1: Primary specification (team ORtg)

```python
import statsmodels.formula.api as smf

floor_games = data[data['is_floor_primary'] == 1]

model1 = smf.ols('''
    off_rating ~
        fga_retention +
        game_score +
        opponent_defrtg +
        is_playoff +
        minutes +
        C(player_name) +
        C(season)
''', data=floor_games).fit(cov_type='cluster', cov_kwds={'groups': floor_games['player_name']})
```

**Interpretation:** The coefficient on `fga_retention` is the key estimate.
- **Positive** → higher retention (forcing) predicts *better* team ORtg → contraction is worse (H1)
- **Negative** → higher retention (forcing) predicts *worse* team ORtg → forcing is worse (H2)
- **Not significant** → mechanism doesn't matter (H3)

### Model 2: Win probability

```python
model2 = smf.logit('''
    team_win ~
        fga_retention +
        game_score +
        opponent_defrtg +
        is_playoff +
        minutes +
        C(player_name) +
        C(season)
''', data=floor_games).fit(cov_type='cluster', cov_kwds={'groups': floor_games['player_name']})
```

### Model 3: FTA retention as alternative mechanism measure

```python
model3 = smf.ols('''
    off_rating ~
        fta_retention +
        game_score +
        opponent_defrtg +
        is_playoff +
        minutes +
        C(player_name) +
        C(season)
''', data=floor_games).fit(cov_type='cluster', cov_kwds={'groups': floor_games['player_name']})
```

FTA retention captures a different facet of contraction — specifically relevant for the PG rim-abandonment archetype.

### Model 4: Descriptive cross-player mechanism (no player FE)

```python
model4 = smf.ols('''
    off_rating ~
        mechanism_contractor +
        game_score +
        opponent_defrtg +
        is_playoff +
        minutes +
        C(season)
''', data=floor_games).fit(cov_type='HC1')
```

Where `mechanism_contractor` is a binary indicator from Screen E labels. This model does NOT include player fixed effects, so it captures cross-player mechanism differences. It is **descriptive only** — the coefficient is confounded by team quality, system, era, and everything else that differs between contractors and forcers. Report with heavy caveats. Its role is to provide the vivid "contractor floor games vs. forcer floor games" comparison for narrative purposes.

### Robustness checks

| Check | Specification change |
|-------|---------------------|
| Close games only | Exclude games where \|`plus_minus`\| > 15 |
| Minutes floor | Restrict to `minutes >= 25` (removes blowout benchings per Kobe lesson) |
| Playoff only | Restrict to `is_playoff == 1` |
| Exclude injury-flagged | Drop `minutes <= 15` games |
| Within-series | Add series FE (`C(series_id)`) where available |
| Continuous game score | Replace `game_score` with TS% as individual performance control |
| Harden-only | Run within-player on Harden's ~36 PO floor games alone (underpowered but vivid) |

### Confounds acknowledged

| Confound | Mitigation |
|----------|------------|
| Cross-player system/teammate quality | Player FE in primary spec; cross-player comparison is descriptive only |
| Individual performance severity | `game_score` control; sensitivity with TS% |
| Blowout benchings inflate contraction | Minutes control; ≥25 min sensitivity; Kobe lesson applied |
| Opponent quality | `opponent_defrtg` (season-level; coarse) |
| Reverse causality (team collapse → star contracts) | Acknowledged; partially addressed by `game_score` control; fully addressed only by Pass 2 temporal ordering |
| Small sample within player | Clustered SE at player level; report effective sample sizes |

---

## Step 4 — Report and bridge to paper

### 4a. Update `findings.md`

Add a new section: **"Causal Chain: Does Failure Mechanism Predict Team Outcomes?"**

Structure based on what the results show:

**If H1 (contraction is worse):**
> Stars who contract in floor games produce significantly worse team offense than stars who force through inefficiency, even after controlling for individual performance quality. This suggests contraction is not a neutral failure mode — it actively damages team outcomes beyond the star's own scoring collapse. Coaching interventions that keep contracted stars involved (force-feeding, set plays) may mitigate playoff risk.

**If H2 (forcing is worse):**
> Stars who force through floor games produce significantly worse team offense than stars who contract, after controls. Contraction may be a rational, team-first adaptation: by reducing volume, the contracted star cedes possessions to teammates who can use them more efficiently. The "choker" narrative is not just mechanistically wrong — it may describe a strategically *correct* response to personal adversity.

**If H3 (no difference):**
> After controlling for individual performance quality, failure mechanism does not predict team offensive outcomes. The taxonomy (contraction vs. forcing) is descriptively valid and captures real behavioral differences, but those differences do not produce measurably different team consequences at the game level. The paper contribution is the taxonomy itself, not a scouting recommendation.

### 4b. Figures to produce

1. Scatter: per-game `fga_retention` vs. team `off_rating` in floor games, with regression line, faceted or colored by player
2. Bar chart: mean team ORtg in contractor vs. forcer vs. mixed floor games (with CI error bars)
3. Within-player: Harden floor-game team ORtg by fga_retention quartile
4. Matched pairs: Harden vs. Durant floor games, team ORtg side-by-side (if sample permits)

### 4c. Bridge to Pass 2

Regardless of H1/H2/H3 outcome, note:

> Game-level analysis cannot establish causal direction between mechanism and team outcomes. Pass 2 possession-level data provides temporal ordering: if Event A fires (personal cold start) and usage drops *follow* rather than *precede* team offensive collapse, reverse causality is less plausible. This temporal evidence is the strongest available causal argument in observational data.

---

## Implementation sequence (revised)

| Step | Module | Depends on | Status | Description |
|------|--------|------------|--------|-------------|
| 0 | `scrape_team_logs.py`, `validate_team_logs.py` | Player raw CSVs | **Done** | Team ORtg, POSS, WL |
| 1 | `join_causal_table.py` | Step 0 + `analysis_table.csv` + `screen_e_results.csv` | **Next** | Join + per-game retention |
| 2 | `mechanism_descriptives.py` | Step 1 | Pending | Descriptive tables and figures |
| 3 | `mechanism_models.py` | Step 1 | Pending | Regressions (H1/H2/H3) |
| 4 | `findings.md` update | Steps 2–3 | Pending | Interpret and report |

**No step may skip validation gates.** Step 0 gate is `make validate-team-logs` exit 0. Step 1 gate is the join validation table above.

---

## File index

| Path | Role |
|------|------|
| `documents/development/causal_chain_plan.md` | This document |
| `src/scrape_team_logs.py` | Step 0 fetch |
| `src/validate_team_logs.py` | Step 0 validation |
| `src/join_causal_table.py` | Step 1 — join + per-game retention (to write) |
| `src/mechanism_descriptives.py` | Step 2 — descriptive analysis (to write) |
| `src/mechanism_models.py` | Step 3 — regressions (to write) |
| `data/raw/team_game_logs.csv` | Step 0 output (gitignored) |
| `data/processed/analysis_table.csv` | Player games + floor flags |
| `data/processed/causal_analysis_table.csv` | Step 1 output (to write) |
| `data/processed/screen_e_results.csv` | Mechanism labels for descriptive splits |
| `data/processed/retention_baselines.csv` | Player-level retention (reference, not primary IV) |
| `data/processed/mechanism_descriptives.csv` | Step 2 output (to write) |

---

## Decision log

| Date | Decision |
|------|----------|
| Jun 2026 | Causal chain prioritized over Pass 2 at scale |
| Jun 2026 | Step 0: team `teamgamelogs` API (Base + Advanced), not box-score reconstruction alone |
| Jun 2026 | `game_id` must be normalized to 10 digits before any player↔team join |
| Jun 2026 | Step 0 complete — 19,717 rows, 100% join coverage, validation OK |
| Jun 2026 | **Revised:** CC1/CC2 demoted to validation gates; primary analysis restricted to floor games; continuous `fga_retention` replaces binary mechanism indicator; player FE + `game_score` control isolate within-player mechanism variation |
| Jun 2026 | **Revised:** Test H1 (contraction worse), H2 (forcing worse), H3 (no difference) symmetrically — do not assume contraction is harmful |
| Jun 2026 | **Revised:** Pass 2 temporal ordering identified as strongest available mitigation for reverse causality |
| Jun 2026 | **Revised:** Pivoted from mechanism to trigger as primary axis; Screen F trigger classification replaces Screen E mechanism labels as headline; per-game `fga_retention` retained as secondary analysis |
