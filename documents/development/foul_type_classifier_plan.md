# Foul-Type Video Classifier — Implementation Plan

**Date:** June 17, 2026 (taxonomy revised June 18, 2026; LLM grader added June 23, 2026)
**Status:** Manual classifier + LLM grader built
**Predecessor:** `foul_type_video_plan.md` (scoping document)

## Problem Statement

The project's strongest finding is that FTA shift (PO − RS) predicts playoff floor-game rate (r = −0.53, p = 0.002), but FTA shift is retrospective — you can't observe it before the playoffs. The predictive test fails (H1 shift → H2 floor rate: r = −0.16, p = 0.40).

The missing variable is **how fouls occur**: whether a player's shooting fouls come from high-force body contact on genuine finishes (hard to avoid, refs always call) versus light arm contact on foul-seeking moves (refs have real discretion). This distinction is invisible in PBP data and can only be observed on video.

This document specifies the tool for a human reviewer to watch video clips of shooting fouls and classify them by mechanism, body part, timing, severity, and location.

---

## Foul-Type Taxonomy (v3)

Revised June 18, 2026 from v2. Key changes:
- **Discretion removed.** ALWAYS/MARGINAL/SOUGHT asked for a meta-judgment about referee behavior — an opinion on top of an observation, and impossible for an LLM to replicate. Replaced by **Severity**, which is grounded in observable physics (force and trajectory change).
- **Mechanism decoupled from body part.** Old codes like DRV-BODY and DRV-ARM conflated *how* the foul happened with *where* contact landed. These are now independent axes.
- **Timing added as drive sub-tag.** Only shown when mechanism is a drive type (DRV-FINISH, DRV-INIT, ARM-HOOK); irrelevant for jumper fouls.

### Mechanism (how did the foul happen)

| Code | Label | Description | Visual cue |
|------|-------|-------------|------------|
| **DRV-FINISH** | Drive finish | Driver going toward the basket; defender is in the path on a genuine finish attempt | Clear finishing angle; driver's trajectory is toward the rim |
| **DRV-INIT** | Drive initiate | Driver veers into or creates contact with defender without a clear finishing angle | Driver's path deviates toward defender rather than the basket |
| **ARM-HOOK** | Arm hook / lock | Driver hooks, traps, or locks defender's arm during a drive | Driver's arm wraps around or pins defender's arm; often on step-through or gather |
| **CONTEST** | Jumper contest | Defender hits shooter's arm or hand while contesting a shot | Defender reaches in during release; genuine contest attempt |
| **LANDING** | Landing space | Defender closes out and is under the shooter's landing zone | Shooter lands on defender's foot or legs; closeout too tight |
| **PUMP-JUMP** | Pump-fake jump-in | Shooter pump-fakes, defender leaves feet, shooter jumps into them | Shooter deliberately initiates upward contact with airborne defender |
| **RIP-THRU** | Rip-through | Shooter swings ball through defender's extended arm | Defender has arm extended across body; shooter rips through it |
| **POST** | Post contact | Contact on a post-up — defender reaches or hacks | Post player backing down; defender reaches across and makes contact |
| **PUTBACK** | Putback / rebound | Foul during offensive rebound or putback attempt | Scramble under the basket; over-the-back or arm grab |
| **OFFBALL** | Off-ball | Grab, hold, or screen foul away from the ball | Player doesn't have the ball; defender grabs/holds on cut or screen |
| **TAKE** | Take foul | Intentional foul to stop play; no shot attempt | Transition or end-of-clock; wrap-up or push before shot |
| **AMB** | Ambiguous | Cannot determine from available angle | — |

### Body Part (where contact landed)

| Code | Label | Description |
|------|-------|-------------|
| **HEAD** | Head | Contact to the head or face |
| **ARM** | Arm / Hand | Contact to the arm, forearm, wrist, or hand |
| **CHEST** | Chest / Body | Contact to the torso, chest, or midsection |
| **SHOULDER** | Shoulder | Contact to the shoulder |
| **LOWER** | Lower Body | Contact to the hip, thigh, leg, or foot |

### Timing (drive sub-tag — only applies when mechanism is DRV-FINISH, DRV-INIT, or ARM-HOOK)

| Code | Label | Description |
|------|-------|-------------|
| **BEFORE** | Before shot (gather) | Contact happens during the gather/dribble-gather, before the shooting motion begins |
| **DURING** | During shot motion | Contact happens simultaneous with the upward shooting motion |
| **AFTER** | Post-release | Contact happens after the ball leaves the shooter's hand |

### Severity (how forceful was the contact)

Anchor to observable physics — how much did the contact alter the shooter's body trajectory, not whether a ref should have called it.

| Code | Label | Description |
|------|-------|-------------|
| **STRONG** | Strong | High-force collision; shooter's body trajectory visibly displaced or altered |
| **MEDIUM** | Medium | Clear contact with meaningful force; shot motion affected but not body displacement |
| **MARGINAL** | Marginal | Light or incidental contact; minimal effect on the shooter's motion |

An optional one-sentence note field is available in the classifier for tricky severity calls. These notes are exported to CSV and serve as few-shot examples for future LLM grading.

### Location (where on the court)

| Code | Label | Description |
|------|-------|-------------|
| **RA** | Restricted area | Within the restricted area arc |
| **PAINT** | Paint | In the paint, outside restricted area |
| **MID** | Mid-range | Inside the arc, outside the paint |
| **PERIM** | Perimeter | Beyond the 3-point line |

---

## Data Sources

### Video clips: `videoeventsasset` API

**Verified working (June 17, 2026).** The endpoint returns direct MP4 URLs for any play event:

```
GET https://stats.nba.com/stats/videoeventsasset?GameEventID={eid}&GameID={gid}
```

Response structure:
```json
{
  "resultSets": {
    "Meta": {
      "videoUrls": [{
        "uuid": "b5d018c2-473c-ceba-7be1-8582c9a239dc",
        "sdur": 6950,
        "surl": "https://videos.nba.com/.../320x180.mp4",
        "murl": "https://videos.nba.com/.../960x540.mp4",
        "lurl": "https://videos.nba.com/.../1280x720.mp4",
        "mth":  "https://videos.nba.com/.../960x540.jpg"
      }]
    }
  }
}
```

Three resolutions available (320x180, 960x540, 1280x720). Use 960x540 for classification (good enough for arm/body distinction, smaller download than 720p).

### Foul events: PBP data (already cached)

Each game's PBP is cached in `data/raw/pbp/{game_id}.json`. Shooting fouls are:
- `actionType == "Foul"` and `subType == "Shooting"` — the foul event
- The shooter is the person drawing the foul (opposite of `personId` on the foul event — look for the preceding shot attempt or the free-throw taker)

### Game/event mapping: `playbyplayv3` (already cached)

Game IDs and event IDs come from the existing PBP cache. The `actionId` field in PBP maps to `GameEventID` in the video API.

---

## Architecture

### Two-script design

```
src/foul_type_scraper.py   # Step 1: Fetch video URLs + build clip manifest
src/foul_type_classifier.py # Step 2: Generate classification HTML tool
```

Plus one output file:

```
data/processed/foul_type_classifications.csv  # Human-generated classifications
```

### Step 1: `foul_type_scraper.py`

**Input:** Player name (from `config.py`), season, season type, number of games (optional — default all)

**Process:**
1. Load player's game logs from cache (`playergamelogs`)
2. For each game, load PBP from cache (`data/raw/pbp/{game_id}.json`)
3. Filter to S.FOUL events where the target player drew the foul:
   - `actionType == "Foul"` and `subType == "Shooting"`
   - The player is the fouled party (not the committer): identify from the subsequent free-throw events or from the `personId` field on the preceding shot attempt
4. For each qualifying foul event, call `videoeventsasset` with the game ID and event ID
5. Extract the 960x540 MP4 URL (`murl`), thumbnail URL (`mth`), and duration (`mdur`)
6. Build a clip manifest: game_id, event_id, period, clock, description, opponent, score, video_url, thumbnail_url, duration

**Output:** `data/processed/foul_type_manifest_{player_slug}.json`

**Rate limiting:** Use existing `nba_client.py` infrastructure (1.2s min interval + jitter). ~6-8 shooting fouls per game for star players → ~30-40 API calls per 5-game sample.

**Caching:** Cache video API responses in the existing `data/cache/` directory with 30-day TTL (same as season data). Video URLs are stable.

### Step 2: `foul_type_classifier.py`

**Input:** A manifest JSON from Step 1

**Output:** A single self-contained HTML file: `output/foul_type_classifier_{player_slug}.html`

**Design principles:**
- Zero dependencies — opens in any browser, no server
- Keyboard-driven — target <5 seconds per clip
- All state in localStorage — survive page refresh
- Export to CSV at any time

---

## HTML Classifier Specification

### Layout

```
┌──────────────────────────────────────────────────────┐
│  [Video Player]                     │  Context Panel  │
│                                     │  Opponent: LAC  │
│  Autoplays on load, loops           │  Q2  8:12       │
│                              [↺ Replay]  S.FOUL       │
├─────────────────────────────────────┤                 │
│  [Classification Panel]             │  Progress:      │
│                                     │  3 / 47         │
│  Mechanism:                         │  ████░░░░░░     │
│  [Drive finish]  [Drive initiate]   │                 │
│  [Arm hook/lock] [Jumper contest]   │  Recent:        │
│  [Landing space] [Pump-fake jump-in]│  Clip 3         │
│  [Rip-through]   [Post contact]     │  DRV-FINISH     │
│  [Putback/reb]   [Off-ball]         │  CHEST STRONG   │
│  [Take foul]     [Ambiguous]        │  RA             │
│                                     │                 │
│  Body Part:                         │                 │
│  [Head] [Arm/Hand] [Chest/Body]     │                 │
│  [Shoulder] [Lower Body]            │                 │
│                                     │                 │
│  Timing:  ← only for drive mechs    │                 │
│  [Before (gather)] [During] [After] │                 │
│                                     │                 │
│  Severity:                          │                 │
│  [Strong]  [Medium]  [Marginal]     │                 │
│  [____________________________]     │                 │
│   optional one-sentence note        │                 │
│                                     │                 │
│  Location:                          │                 │
│  [Restricted Area] [Paint]          │                 │
│  [Mid-range]       [Perimeter]      │                 │
│                                     │                 │
│  [← Prev]  [Next →]  [Export CSV]  [Clear]           │
└──────────────────────────────────────────────────────┘
```

### Interface

Click-based UI — all classification is done by clicking buttons. No keyboard shortcuts. The Timing section is hidden by default and appears only when a drive mechanism (DRV-FINISH, DRV-INIT, ARM-HOOK) is selected.

### Workflow

1. Page loads → first clip autoplays and loops
2. Click mechanism button
3. Click body part button
4. If a drive mechanism was selected, the Timing section appears → click a timing button
5. Click severity button
6. Optionally type a one-sentence note in the severity note field for tricky calls
7. Click location button
8. All required fields complete → 0.5s green flash, auto-advance to next clip
9. Click **← Prev** / **Next →** to navigate manually at any time
10. Click **Clear** to reset the current clip's classification
11. Click **Export CSV** to download all completed classifications

### Completion rules

A clip is considered classified when all required fields are set:
- Mechanism, Body Part, Severity, Location always required
- Timing required only when mechanism is DRV-FINISH, DRV-INIT, or ARM-HOOK
- Severity note is always optional (never blocks auto-advance)

### Data model (localStorage key: `ftc_v3_{player_slug}`)

```json
{
  "idx": 3,
  "cls": {
    "0042300164_13": {
      "mech":   "DRV-FINISH",
      "body":   "CHEST",
      "timing": "DURING",
      "sev":    "STRONG",
      "note":   "Full-speed collision, Nurkic slid back 2 feet",
      "loc":    "RA",
      "ts":     "2026-06-18T18:15:00Z"
    }
  }
}
```

Note: the `v3` prefix in the key means data from the v2 classifier is not loaded automatically.

### CSV export format

```csv
game_id,event_id,period,clock,description,opponent,mechanism,body_part,timing,severity,severity_note,location,timestamp
0042300164,13,1,PT11M43S,"Nurkic S.FOUL (P1.T1)",LAC,DRV-FINISH,CHEST,DURING,STRONG,"Full-speed collision, Nurkic slid back 2 feet",RA,2026-06-18T18:15:00Z
```

The `timing` column is empty for non-drive mechanisms. The `severity_note` column is empty when no note was entered.

---

## Sample Design for Alpha Test

### Minimum viable test: 2 players × 5 RS games each

| Player | Why | Expected profile |
|--------|-----|------------------|
| **Harden** | Highest FTA shift in cohort (−3.3/36); known for arm hooks, rip-throughs, pump-fake jump-intos | High ARM-HOOK/RIP-THRU/PUMP-JUMP, high MARGINAL severity, high ARM body part |
| **Giannis** | Large FTA shift (−4.5/36) but from through-body contact — genuine rim finishes | High DRV-FINISH, high STRONG severity, high CHEST body part |

**Prediction:** If foul type explains FTA shift, Harden should show high MARGINAL severity + foul-seeking mechanisms (ARM-HOOK, RIP-THRU, PUMP-JUMP), while Giannis should show high STRONG severity + DRV-FINISH + CHEST/BODY contact. If severity and mechanism distributions are similar between the two, foul type is not the missing variable.

**Games:** Select 5 recent RS games per player from 2023-24 or 2024-25 seasons (video availability is best for recent games).

**Expected clips:** ~6-8 shooting fouls per game × 5 games × 2 players = ~60-80 clips
**Time:** ~25 minutes of classification at 20 seconds/clip

### If alpha test passes: full sample

Expand to the 10-12 players with the strongest FTA shift signals (both positive and negative). See `foul_type_video_plan.md` Phase 2 for the full sample design.

---

## Implementation Steps

### 1. Build `foul_type_scraper.py` (~1 hour)

- Extend `nba_client.py` with a `get_video_events(game_id, event_id)` method
- Filter PBP for shooting fouls drawn by target player
- Build and cache clip manifest
- Handle missing video (some events return empty videoUrls)

### 2. Build `foul_type_classifier.py` (~1.5 hours)

- Generate self-contained HTML from manifest JSON
- Embed clip URLs (loaded from NBA CDN at runtime — no local download needed)
- Implement keyboard bindings, localStorage persistence, CSV export
- Include instructions panel visible on first load

### 2b. Build `foul_type_llm_grader.py` (built June 23, 2026)

Automated timing classification (BEFORE/DURING/AFTER) using multimodal LLMs. Supplements the manual classifier by grading the timing axis automatically.

**Providers:** Gemini (native video, recommended), OpenAI (GPT-5.4-mini, frame-based), Anthropic (Claude Sonnet 4.6, frame-based), **Vertex AI** (gcloud ADC, no API key needed — uses GCS for video upload).

**Usage:**
```bash
# Vertex AI (no API key needed)
PYTHONPATH=. python src/foul_type_llm_grader.py --player "James Harden" --provider "vertex" --model "gemini-2.5-flash"

# Gemini API
PYTHONPATH=. python src/foul_type_llm_grader.py --player "James Harden" --provider "gemini" --model "gemini-2.5-flash"

# Validate against manual ground truth
PYTHONPATH=. python src/foul_type_llm_grader.py --player "James Harden" --provider "vertex" --model "gemini-2.5-flash" --validate-only
```

**Scope:** Currently grades only the timing axis (BEFORE/DURING/AFTER). Mechanism, body part, severity, and location still require the manual classifier HTML tool. Extending the LLM grader to additional axes is straightforward — add fields to the system prompt and response schema.

**Vertex AI setup:** Uses gcloud Application Default Credentials for authentication. Videos are uploaded to a GCS bucket (`project-3984c931-3755-423f-966-foul-type-grader-tmp`) with 1-day lifecycle auto-delete. No API key environment variable required.

### 3. Alpha test (~30 minutes)

- Run scraper for Harden + Giannis (5 RS games each)
- Generate classifier HTML
- Classify all clips
- Export CSV and compute SOUGHT%, ALWAYS%, mechanism distribution

### 4. Analyze (~30 minutes)

- Compare foul-type profiles between Harden and Giannis
- If profiles are dramatically different → proceed to full sample
- If profiles are similar → kill the foul-type hypothesis

---

## File Manifest

| File | Description | Status |
|------|-------------|--------|
| `src/foul_type_scraper.py` | PBP filter + video URL fetcher → manifest JSON | **Done** |
| `src/foul_type_classifier.py` | Manifest JSON → classification HTML tool | **Done** |
| `src/foul_type_llm_grader.py` | Multimodal LLM video grading (Gemini/OpenAI/Anthropic/Vertex) | **Done** |
| `data/processed/foul_type_manifest_*.json` | Per-player clip manifests | **Generated** (Harden: 20, Giannis: 16) |
| `output/foul_type_classifier_*.html` | Per-player classification tools | **Generated** |
| `data/processed/foul_type_classifications.csv` | All classifications (after export) | Human-generated |
| `data/processed/foul_type_player_profiles.csv` | Per-player foul-type composition | After full sample |

---

## Key Technical Decisions

1. **Video is streamed, not downloaded.** The HTML loads MP4s directly from `videos.nba.com` CDN. No local storage of video files. Requires internet connection during classification.

2. **960x540 resolution.** Good enough to distinguish arm hooks from body contact. 1280x720 is overkill for classification and would slow loading. 320x180 is too small to see arm-level detail.

3. **HTML served via localhost.** No build step, no npm. Run `make foul-type-serve` (or `python -m http.server 8080 --directory output`) and open in Chrome. The manifest data is embedded in the HTML as a JSON blob. A local HTTP server is required because NBA CDN videos have no CORS headers — `file://` won't load them.

4. **localStorage for state.** Classifications persist across page refreshes. The export button writes to CSV file via the browser's download mechanism. No server round-trips.

5. **Five-axis classification (mechanism + body part + timing + severity + location).** All axes describe observable facts — what happened, where contact landed, when, how hard, and from where on the court. Severity is the most judgment-dependent axis but is grounded in physics (force/trajectory change), not referee behavior. The optional severity note captures reasoning on ambiguous calls and doubles as future few-shot examples for LLM grading. Timing is a conditional sub-tag shown only for drive mechanisms.

6. **`actionNumber` → `GameEventID` mapping.** The PBP `actionNumber` field (NOT `actionId`) maps to the `GameEventID` parameter in the `videoeventsasset` API. Verified across multiple games — `actionId` returns empty video URLs. The scraper uses `actionNumber` exclusively.

---

## Risks

| Risk | Probability | Mitigation |
|------|-------------|------------|
| `videoeventsasset` requires authentication or breaks | Low — verified working June 17, 2026 with standard headers | Fall back to nba.com/stats/events page (manual browser navigation) |
| Video URLs expire | Low — CDN URLs appear stable (cache headers show 31536000s TTL) | Re-scrape if URLs expire; manifest stores all metadata for re-generation |
| `actionNumber` mapping breaks on older games | Low — verified working back to 2014-15 season | Use `videoAvailable` flag on PBP actions as pre-check |
| Harden and Giannis have similar foul-type profiles | Medium | This is the kill criterion — honest null result, foul type is not the variable |
| Classification takes >30 seconds per clip | Low with keyboard-driven UI | Practice round of 5 clips; adjust UI if flow feels slow |
