# Foul-Type Video Classifier — Implementation Plan

**Date:** June 17, 2026
**Status:** Ready to build
**Predecessor:** `foul_type_video_plan.md` (scoping document)

## Problem Statement

The project's strongest finding is that FTA shift (PO − RS) predicts playoff floor-game rate (r = −0.53, p = 0.002), but FTA shift is retrospective — you can't observe it before the playoffs. The predictive test fails (H1 shift → H2 floor rate: r = −0.16, p = 0.40).

The missing variable is **foul discretion**: whether a player's shooting fouls come from contact that refs always call (through-body finish, arm-on-contest) or contact that refs can choose not to call (arm hooks, rip-throughs, pump-fake jump-intos). This distinction is invisible in PBP data and can only be observed on video.

This document specifies the tool for a human reviewer to watch video clips of shooting fouls and classify them by type and location.

---

## Foul-Type Taxonomy (v2)

Revised from the original taxonomy in `foul_type_video_plan.md`. The critical change: categories are now organized by **observable contact mechanism** (what you see on video), with a separate **discretion** tag for the judgment axis.

### Contact mechanism (what happened — tag the mechanism you see)

| Code | Label | Description | Visual cue |
|------|-------|-------------|------------|
| **DRV-BODY** | Drive through-body | Driver goes through defender's torso/chest while attempting to finish at the rim | Defender's body is in the path; driver goes through or over them |
| **DRV-ARM** | Drive arm hook/lock | Driver hooks, traps, or locks defender's arm during a drive | Driver's arm wraps around or pins defender's arm; often on step-through or gather |
| **DRV-INIT** | Drive initiated contact | Driver initiates body contact (shoulder, hip) without a clear finishing angle | Driver veers into defender rather than toward the basket |
| **JMP-CONTEST** | Jumper arm/hand contest | Defender hits shooter's arm or hand on a genuine contest | Defender reaches in and makes contact with shooter's arm during release |
| **JMP-LANDING** | Jumper landing space | Defender closes out and lands under the shooter's landing zone | Shooter lands on defender's foot or legs; closeout too tight |
| **JMP-PUMP** | Jumper pump-fake jump-into | Shooter pump-fakes, defender leaves feet, shooter jumps into them | Shooter deliberately initiates upward contact with airborne defender |
| **JMP-RIP** | Jumper rip-through | Shooter swings ball through defender's extended arm | Defender has arm extended across body; shooter rips ball through the arm |
| **POST-REACH** | Post reach-in | Defender reaches or hacks on a post-up | Post player backing down; defender reaches across and hits arm/body |
| **REB** | Putback/rebound foul | Foul during offensive rebound or putback attempt | Scramble under the basket; over-the-back or arm grab |
| **OFFBALL** | Off-ball foul | Grab, hold, screen foul away from the ball | Player doesn't have the ball; defender grabs/holds on cut or screen |
| **TAKE** | Take foul | Intentional foul to stop play; no shot attempt | Transition or end-of-clock; wrap-up or push before shot |
| **AMB** | Ambiguous | Cannot determine from available angle | — |

### Discretion (why the whistle blew — tag your judgment)

| Code | Label | Description |
|------|-------|-------------|
| **ALWAYS** | Always called | Contact is obvious and unavoidable — genuine contest, body-to-body on finish |
| **MARGINAL** | Marginally called | Contact is real but could go either way — arm hook where defender reached, lean-in on drive |
| **SOUGHT** | Offense sought the foul | Player's primary intent was drawing contact, not scoring — pump-fake jump-in, rip-through, arm trap |

### Location (where the action happened)

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
│  [Video Player — 960x540]          │  Context Panel  │
│                                     │  Player: Harden │
│  Autoplays on load                 │  vs LAC G3      │
│  Loop until classified              │  Q2 8:12        │
│                                     │  54-51          │
│                                     │  S.FOUL         │
├─────────────────────────────────────┤                 │
│  [Classification Panel]            │                 │
│                                     │                 │
│  Mechanism:                         │                 │
│  [1] DRV-BODY  [2] DRV-ARM         │  Progress:      │
│  [3] DRV-INIT  [4] JMP-CONTEST     │  3/47           │
│  [5] JMP-LANDING [6] JMP-PUMP      │                 │
│  [7] JMP-RIP   [8] POST-REACH      │  Previous:      │
│  [9] REB       [0] OFFBALL         │  DRV-BODY       │
│  [Q] TAKE      [W] AMB             │  ALWAYS / RA    │
│                                     │                 │
│  Discretion:                        │                 │
│  [A] ALWAYS  [S] MARGINAL  [D] SOUGHT │              │
│                                     │                 │
│  Location:                           │                 │
│  [Z] RA  [X] PAINT  [C] MID  [V] PERIM │            │
│                                     │                 │
│  [N] Next  [P] Prev  [E] Export CSV │                 │
└──────────────────────────────────────────────────────┘
```

### Keyboard bindings

| Key | Action |
|-----|--------|
| `1` | DRV-BODY |
| `2` | DRV-ARM |
| `3` | DRV-INIT |
| `4` | JMP-CONTEST |
| `5` | JMP-LANDING |
| `6` | JMP-PUMP |
| `7` | JMP-RIP |
| `8` | POST-REACH |
| `9` | REB |
| `0` | OFFBALL |
| `Q` | TAKE |
| `W` | AMB |
| `A` | ALWAYS (discretion) |
| `S` | MARGINAL (discretion) |
| `D` | SOUGHT (discretion) |
| `Z` | RA (location) |
| `X` | PAINT (location) |
| `C` | MID (location) |
| `V` | PERIM (location) |
| `N` | Next clip |
| `P` | Previous clip |
| `E` | Export CSV |
| `R` | Replay video |
| `Backspace` | Clear current classification |

### Workflow

1. Page loads → first clip autoplays
2. Reviewer watches clip (typically 5-15 seconds)
3. Press mechanism key → mechanism highlighted, video pauses
4. Press discretion key → discretion set
5. Press location key → location set
6. All three set → auto-advance to next clip after 0.5s confirmation flash
7. If unsure, press `W` (AMB) for mechanism → still requires discretion + location
8. At any time: `P` to go back and re-classify, `E` to export

### Data model (localStorage)

```json
{
  "classifications": {
    "0042300164_13": {
      "mechanism": "DRV-ARM",
      "discretion": "SOUGHT",
      "location": "RA",
      "timestamp": "2026-06-17T20:15:00Z"
    }
  },
  "currentClipIndex": 3,
  "playerSlug": "james_harden"
}
```

### CSV export format

```csv
game_id,event_id,player_name,period,clock,description,opponent,score,mechanism,discretion,location,timestamp
0042300164,13,James Harden,1,PT11M43S,Nurkic S.FOUL (P1.T1),LAC,0-2,DRV-ARM,SOUGHT,RA,2026-06-17T20:15:00Z
```

---

## Sample Design for Alpha Test

### Minimum viable test: 2 players × 5 RS games each

| Player | Why | Expected profile |
|--------|-----|------------------|
| **Harden** | Highest FTA shift in cohort (−3.3/36); known for arm hooks, rip-throughs, pump-fake jump-intos | High SOUGHT%, high DRV-ARM, high JMP-PUMP/RIP |
| **Giannis** | Large FTA shift (−4.5/36) but from through-body contact — genuine rim finishes | High DRV-BODY, high ALWAYS, low SOUGHT |

**Prediction:** If foul discretion explains FTA shift, Harden's SOUGHT% should be dramatically higher than Giannis's, and Giannis's ALWAYS% should be dramatically higher than Harden's. If they're similar, foul type is not the missing variable.

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
| `src/foul_type_scraper.py` | PBP filter + video URL fetcher → manifest JSON | To build |
| `src/foul_type_classifier.py` | Manifest JSON → classification HTML tool | To build |
| `data/processed/foul_type_manifest_*.json` | Per-player clip manifests | Generated by scraper |
| `output/foul_type_classifier_*.html` | Per-player classification tools | Generated by classifier |
| `data/processed/foul_type_classifications.csv` | All classifications (after export) | Human-generated |
| `data/processed/foul_type_player_profiles.csv` | Per-player foul-type composition | After full sample |

---

## Key Technical Decisions

1. **Video is streamed, not downloaded.** The HTML loads MP4s directly from `videos.nba.com` CDN. No local storage of video files. Requires internet connection during classification.

2. **960x540 resolution.** Good enough to distinguish arm hooks from body contact. 1280x720 is overkill for classification and would slow loading. 320x180 is too small to see arm-level detail.

3. **Self-contained HTML.** No build step, no npm, no server. The reviewer opens a file in Chrome and starts classifying. The manifest data is embedded in the HTML as a JSON blob.

4. **localStorage for state.** Classifications persist across page refreshes. The export button writes to CSV file via the browser's download mechanism. No server round-trips.

5. **Three-axis classification (mechanism + discretion + location).** Mechanism is what you see. Discretion is your judgment on whether the foul was sought. Location is where it happened. The alpha test is whether `sought%` differs between Harden and Giannis.

6. **`actionId` → `GameEventID` mapping.** The PBP `actionId` field maps directly to the `GameEventID` parameter in the `videoeventsasset` API. Verified on the Nurkic S.FOUL example (actionId=3, GameEventID=13 — note: GameEventID is the `actionNumber` field, not `actionId`; verify this mapping during scraper build).

---

## Risks

| Risk | Probability | Mitigation |
|------|-------------|------------|
| `videoeventsasset` requires authentication or breaks | Low — verified working June 17, 2026 with standard headers | Fall back to nba.com/stats/events page (manual browser navigation) |
| Video URLs expire | Low — CDN URLs appear stable (cache headers show 31536000s TTL) | Re-scrape if URLs expire; manifest stores all metadata for re-generation |
| `actionId`/`actionNumber` mapping is inconsistent | Medium | Verify on 3-4 games before building full scraper; log mismatches |
| Harden and Giannis have similar foul-type profiles | Medium | This is the kill criterion — honest null result, foul type is not the variable |
| Classification takes >30 seconds per clip | Low with keyboard-driven UI | Practice round of 5 clips; adjust UI if flow feels slow |
