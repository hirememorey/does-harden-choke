# Foul-Type Video Classification Plan

**Date:** June 17, 2026
**Context:** The FTA shift (PO − RS FTA per 36) is the project's strongest predictor of playoff floor-game rate (r = −0.53, p = 0.002), but it is a retrospective variable — you can't observe it before the playoffs. The predictive test fails (H1 shift → H2 floor rate: r = −0.16, p = 0.40). The missing variable is **foul discretion**: whether a player's shooting fouls come from contact that refs always call (through-body finish, arm-on-contest) or contact that refs can choose not to call (arm hooks, rip-throughs, pump-fake jump-intos). If foul-discretion composition predicts FTA shift direction, the full chain closes: RS foul-discretion composition → predicted FTA shift → predicted PO floor risk.

**The hypothesis (revised):** The critical axis is **discretion**, not location. A Harden arm-trap on a drive and a LeBron through-contact on a drive are the same PBP event ("Driving Layup + S.FOUL") but have completely different foul discretion. Players whose FTAs come from always-called contact (genuine finishing contact, clean arm contests) maintain FTAs under playoff conditions. Players whose FTAs come from marginally-called contact (arm hooks, rip-throughs, pump-fake jump-intos, initiated body contact) lose FTAs as refs tighten and defenders become more disciplined.

**Implementation plan:** See [`foul_type_classifier_plan.md`](foul_type_classifier_plan.md) for the full build spec of the video classification tool.

**PBP proxy killed (June 17):** Option C from the original plan (PBP-derived heuristic using shot subtype + location) is dead. Shot subtype cannot disambiguate foul discretion — and-1s on the perimeter blow up the assumption that rim-adjacent shots = genuine contact. Drive-rate is similarly confounded (Harden drives plenty but traps arms). The only viable alpha test is manual video classification.

---

## Why PBP Text Is Insufficient

The NBA PBP data has:
- `actionType: Foul`, `subType: Shooting` — tells you it's a shooting foul, nothing more
- The preceding shot attempt has `subType` (e.g., "Driving Layup Shot", "Jump Shot") and `shotDistance`, `xLegacy`, `yLegacy`

You can infer that Iverson drew a shooting foul after a driving layup from the restricted area, but you CANNOT distinguish:
- **Incidental contact during a genuine finish** (LeBron powering through a contest at the rim)
- **Contact-seeking on a drive** (Harden hooking an arm or initiating body contact to draw the call)
- **Rip-through from the mid-range** (Embiid using the ball to draw an arm across a defender's reach)
- **Pump-fake-and-lean-in** (drawing a foul by jumping into a defender who left his feet)
- **Off-ball grab on a screen action** (coming off a pin-down, defender grabs the shooter's arm)

These actions look identical in PBP text ("S.FOUL") and may even occur in the same shot zone (restricted area). The distinction lives entirely in the physical nature of the contact, which is only visible on video.

Additionally, some players (Embiid) execute rip-throughs from the mid-range — the PBP would show a mid-range shooting foul, which looks the same as a contested mid-range jumper that drew a foul through arm contact. The court location alone cannot disambiguate.

**Why shot subtype + drive-rate proxies are also dead:** And-1s happen on the perimeter and at the mid-range (e.g., Embiid rip-through and-1 from 15 feet), destroying the assumption that rim-adjacent shots = genuine contact. Drive-rate is similarly confounded — Harden drives plenty but traps defenders' arms on those drives. A drive can produce genuine finishing contact (LeBron) or contact-seeking (Harden), and PBP cannot distinguish them. The only observable proxy for discretion is the video itself.

---

## Proposed Foul-Type Taxonomy

| Type | Code | Description | Expected PO behavior |
|------|------|-------------|---------------------|
| **Rim-finishing contact** | RFC | Fouled during a genuine scoring attempt at the rim — body contact, arm slap while finishing layup/dunk | **Maintain/increase** — playoff physicality creates more contact |
| **Perimeter foul-seeking** | PFS | Initiated contact on a perimeter action — pump-fake-and-lean, rip-through, off-arm hook | **Decrease** — refs tighten on marginal calls, defenders more disciplined |
| **Transition foul** | TRN | Take foul, intentional foul to stop fast break | **Increase** — more deliberate fouling in playoffs |
| **Off-ball / screen foul** | OBS | Fouled away from the ball — grab on a screen, holding on a cut | **Neutral/decrease** |
| **And-1 contact** | A1C | Fouled during a made field goal (subset of RFC typically) | **Maintain** — genuine scoring contact |
| **Ambiguous** | AMB | Cannot determine from available angle or too close to call | N/A |

The critical axis is **RFC vs PFS**. The other categories exist for completeness but the hypothesis is tested by the ratio of rim-finishing to perimeter-seeking fouls.

---

## Data Sources for Video

### Option 1: NBA.com Video Events API

The NBA Stats API has a `videoeventsasset` or `videodetailsasset` endpoint that returns video clip URLs for specific game events. For modern games (roughly 2015-16 onward), each foul event has an associated video clip.

**Access pattern:**
```
GET https://stats.nba.com/stats/videodetailsasset
  ?ContextMeasure=FTA
  &GameID={game_id}
  &PlayerID={player_id}
  &Season={season}
  &SeasonType=Playoffs
```

This returns JSON with video URLs (typically `videos.nba.com` CDN links) for each FTA event in the game. Each clip is 5–15 seconds showing the foul action.

**Known constraints:**
- Requires proper `Referer` and `User-Agent` headers
- Rate-limited; may require the same cooldown strategy as the existing `nba_client.py`
- Video availability varies by season — pre-2012 games may have no clips
- The API may return different video views (broadcast, baseline, etc.)

**Status:** Not yet tested in this project. The `nba_client.py` infrastructure can be extended to handle this endpoint.

### Option 2: NBA.com L2M Reports

The NBA publishes Last Two Minute (L2M) reports for close games that include referee assessments of calls (Correct Call, Incorrect Call, Incorrect Non-Call). These reports describe the foul action in text but only cover the final 2 minutes of games within 5 points.

**Limitation:** Tiny sample — only close games, only last 2 minutes. Useful for validation but not for building the full taxonomy.

### Option 3: Manual Video Review via NBA.com

Each game on NBA.com has a play-by-play page with embedded video clips for each event. A human reviewer can click through foul events and classify them. This is the most reliable method but the most labor-intensive.

**URL pattern:**
```
https://www.nba.com/game/{game_slug}/play-by-play
```

### Option 4: Computer Vision / LLM Classification

Feed the video clips to a multimodal model (GPT-4V, Gemini Pro Vision, Claude with vision) and ask it to classify the foul type. This could dramatically reduce the manual labor.

**Feasibility concerns:**
- Basketball foul classification requires domain expertise that current vision models may lack
- The distinction between "driving through contact" and "initiating contact" is subtle
- Video clip quality and angle matter — baseline angle may obscure arm hooks
- Need to validate against a human-coded ground truth

---

## Recommended Approach

### Phase 1: Scoping Spike (1–2 days)

**Goal:** Determine whether the NBA video API is accessible and whether LLM classification is feasible.

1. **Test the video API** — Extend `nba_client.py` to call the `videodetailsasset` endpoint for one modern game (e.g., Harden 2023 playoff game). Determine: Does it return video URLs? What format? Can they be downloaded?

2. **Manual classification pilot** — Pick one game for Harden and one for LeBron from the same playoff year. Watch each shooting foul (typically 5–10 per game for these players). Classify using the taxonomy above. Time the effort.

3. **LLM classification pilot** — If video URLs are obtainable, feed 10 clips to a multimodal model with the taxonomy definitions. Compare to your manual classifications.

**Kill criterion:** If the video API is inaccessible and manual review takes >5 minutes per foul, the full classification is not feasible at scale within a reasonable timeline.

### Phase 2: Sample Design (1 day)

**If Phase 1 succeeds,** design the classification sample:

**Minimum viable sample:** For the predictive test, we need per-player foul-type composition from regular-season games, then test whether that predicts FTA shift direction. This requires:

- **Players:** Focus on the 10–12 players with the strongest FTA shift signal (both positive and negative): Harden, Embiid, Fox, Butler, Iverson, LeBron, Dirk, Brunson, Paul George, Tatum, Mitchell, Simmons.
- **Games per player:** 10–15 RS games × 2 (RS + PO) per player. Random sample within each season-type.
- **Fouls per game:** ~5–8 shooting fouls drawn per game for star players.
- **Total clips:** ~12 players × 25 games × 6 fouls = ~1,800 clips.

At 30 seconds per clip (watch + classify), that's ~15 hours of coding. At 1 minute per clip (conservative), ~30 hours.

**If using LLM classification:** 1,800 API calls with video input. Cost depends on model — likely $50–200 at current vision API rates.

### Phase 3: Classification (3–7 days)

Execute the classification. Options:

**Option A: Full manual (30 hours)**
- Code each foul with the taxonomy
- Record: game_id, event_id, player_name, foul_type, confidence (high/medium/low), notes
- Inter-rater reliability check: have a second coder classify 100 clips (~5%)

**Option B: LLM-assisted with human validation (10–15 hours)**
- LLM classifies all 1,800 clips
- Human reviews: all clips where LLM confidence is low (~30%?), plus a random 10% for validation
- Compute LLM-human agreement rate; if >85%, accept LLM classifications for high-confidence clips

**Option C: Hybrid proxy — PBP-derived heuristic with targeted video validation**
- Use PBP data to create a *coarse* classification:
  - **Probable RFC:** Shooting foul where the preceding shot attempt was a layup/dunk/driving action from ≤5 feet AND the shot was made (and-1) or the shot description contains "Driving"
  - **Probable PFS:** Shooting foul where no preceding shot attempt is recorded in the same action sequence, OR the preceding action was a jump shot from >15 feet
  - **Ambiguous:** Everything else
- Video-validate 200 clips across the three categories to measure accuracy of the heuristic
- If the heuristic is >75% accurate on RFC vs PFS, use it at scale (covers all ~31,000 games in the dataset)

**Recommendation: Start with Option C.** The PBP heuristic can be built immediately from existing data and covers the full dataset. Video validation on 200 clips (~3 hours of coding) determines whether the heuristic is good enough. If it is, you avoid the need for large-scale video classification entirely. If it isn't, you've identified the failure modes and can target video review to the ambiguous cases.

### Phase 4: Analysis (1–2 days)

With per-player foul-type composition:

1. **RS foul-type composition → FTA shift direction** — The key test. Does the share of RFC vs PFS fouls in the regular season predict whether FTAs go up or down in the playoffs?

2. **RS foul-type composition → PO floor rate** — The full chain. If foul type predicts FTA shift, and FTA shift predicts floor rate, does foul type predict floor rate directly?

3. **Foul-type shift RS → PO** — Do some players' foul-type compositions change in the playoffs? (e.g., does Harden draw fewer PFS fouls but maintain RFC fouls, or do both decline?)

4. **Split-half validation** — If the sample is large enough, test whether first-half foul-type composition predicts second-half FTA shift.

**Success criterion:** RS foul-type ratio (RFC / total shooting fouls) predicts FTA shift direction at r > 0.35 and p < 0.05. This would close the predictive loop and make the finding actionable for scouting.

---

## Risk Assessment

| Risk | Probability | Mitigation |
|------|-------------|------------|
| NBA video API is rate-limited or blocked | Medium | Use existing `nba_client.py` rate-limiting; fall back to manual review via web browser |
| LLM classification accuracy is insufficient | Medium | Option C (PBP heuristic) doesn't require video; validate with targeted manual review |
| PBP heuristic is too noisy (>25% error) | Medium | Upgrade to Option A/B for the reduced sample (12 players × 25 games) |
| Foul-type composition doesn't predict FTA shift | Medium | This would be an honest null result — foul type is not the missing variable, and the predictive gap remains open |
| The hypothesis is wrong (FTA shift is driven by team context, not foul type) | Medium | Test team context as a competing predictor; if team-quality variables explain FTA shift better than foul type, pivot to the team-context explanation |
| Video availability is limited for older players (Iverson, Dirk, Ray Allen) | High | Focus on 2012+ seasons for video; use PBP heuristic for older seasons |

---

## Timeline

| Phase | Days | Dependency |
|-------|------|------------|
| Phase 1: Scoping spike | 1–2 | None |
| Phase 2: Sample design | 1 | Phase 1 |
| Phase 3: Classification (Option C) | 2–3 | Phase 2 |
| Phase 4: Analysis | 1–2 | Phase 3 |
| **Total (Option C path)** | **5–8 days** | |
| Phase 3 alt: Full manual classification | 7–10 | Phase 2 |
| **Total (manual path)** | **10–15 days** | |

---

## Files

| File | Description |
|------|-------------|
| `src/foul_type_heuristic.py` | (to build) PBP-based coarse foul-type classification |
| `src/foul_type_analysis.py` | (to build) Foul-type composition → FTA shift → floor rate chain |
| `data/processed/foul_type_classifications.csv` | (to produce) Per-event foul-type labels |
| `data/processed/foul_type_player_profiles.csv` | (to produce) Per-player RS/PO foul-type composition |
