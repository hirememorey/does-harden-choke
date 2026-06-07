# Open Questions — Resolve Before Proceeding

**Date:** June 2026  
**Context:** Pass 1 complete, Pass 2 possession parser validated, cold-start spike analysis run on Harden and Kobe. The pipeline works. The research direction needs sharpening before scaling.

---

## 1. What is the actual thesis — player-specific or structural?

Pass 1 found that Harden's floor games are "disengagement events" (everything contracts). The spike work showed he sometimes forces instead. Is the claim about **James Harden specifically**, or about a **class of offensive structure** (heliocentric creators) that produces catastrophic variance as a systemic feature?

If it's Harden-specific, it's a blog post. If it's structural — "heliocentric offensive systems produce a distinct failure mode under adversity that scalable systems do not" — it's a Sloan paper.

**Decision needed:** Which claim are we making?

---

## 2. What is the novel contribution?

"Stars play worse in the playoffs" is known. "Harden chokes" is a media narrative. Neither is a research finding. The Pass 1 insight that survived — that Harden's floor games are **contraction events** (volume collapse) rather than **inefficiency events** (volume-preserved, efficiency collapse) — is genuinely novel. But it needs a sharper frame:

- Is the finding that **the type of failure mode predicts something downstream** (series outcome, team offensive rating, future performance)?
- Is it that **offensive structure determines failure mode**, not individual psychology?
- Is it that **the public "choke" narrative systematically misdiagnoses what's actually happening**?

**Decision needed:** A one-sentence claim that a Sloan reviewer reads and thinks "I need to see the evidence for that."

---

## 3. What is the unit of analysis and does the sample support it?

Pass 1 operated at the **game level** and found borderline statistical significance (*p* = 0.067 on the floor-rate shift, underpowered group comparison at *p* = 0.18). The spike work operates at the **possession level** but has N=2 per player — pure anecdote.

Before writing more code, estimate: across 9 star players and ~50–170 playoff games each, **how many Cold Start events will fire?** If Event A (1-for-5 in Q1/Q2) fires in ~15–20% of playoff games, that's roughly 10–30 events per player, or 100–250 across the cohort. That's enough for within-player profiles and cross-player comparison. If it fires in 5% of games, we're underpowered and need to loosen the trigger or combine event types.

This is an arithmetic question answerable from the existing box score CSVs without touching the PBP pipeline at all.

**Decision needed:** Estimate cold-start event frequency from existing data. If underpowered, adjust the trigger threshold or combine event types before building the pipeline.

---

## 4. What is the counterfactual?

"Harden's usage drops after a cold start" — compared to what? The spike script compares post-event to pre-event within the same game. But that conflates the adversity response with game-state effects (score margin, pace, opponent adjustment). The design spec's baseline matching (pass2_design_spec.md §3) exists for this reason, but it's heavy machinery.

The simpler question: do we need **within-game baselines** (same game, pre-event possessions in similar score margin), or is **cross-game comparison** sufficient (same player's non-cold-start games as the control)? Within-game is cleaner identification but smaller samples. Cross-game is noisier but statistically powerful.

**Decision needed:** Choose the baseline strategy before building the matching infrastructure.

---

## 5. Is Pass 2 (possession-grain) actually necessary, or can Pass 1 (game-grain) answer the question with better methodology?

The spike work produced vivid case studies. But the core finding — that Harden's floor games are contraction events — was already visible at the game level in Pass 1. The possession grain adds **mechanism** (what happens in the 8 possessions after a cold start), but mechanism is only valuable if the **top-level claim** is established first.

If the game-level claim is borderline (*p* = 0.067), adding possession-level color doesn't rescue it. It might be more productive to **strengthen the game-level analysis** first — add opponent adjustment, expand the player sample, tighten the floor-game definition — and use the possession-grain spike as illustrative evidence rather than the primary identification strategy.

**Decision needed:** Decide whether Pass 2 is the primary analysis or a supporting illustration. If supporting, invest in strengthening Pass 1 first.
