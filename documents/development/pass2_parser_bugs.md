# Pass 2 Possession Parser — Bug Log

**Status:** Under active repair  
**File under repair:** `src/pass2/possessions.py`  
**Validation gate:** `make validate-possessions` (exits 1 while any check fails)  
**Baseline:** The initial commit is the revert point. All work here is uncommitted.

---

## Current validation results (baseline, post-revert)

```
0041600236  SAS  expected=94.7  actual=92   delta=-2.7  PASS
0041600236  HOU  expected=91.0  actual=97   delta=+6.0  FAIL ← primary target
0041500405  GSW  expected=103.4 actual=101  delta=-2.4  PASS
0041500405  CLE  expected=101.1 actual=98   delta=-3.1  FAIL ← borderline
0042200217  BOS  expected=94.9  actual=92   delta=-2.9  PASS
0042200217  PHI  expected=96.4  actual=92   delta=-4.4  FAIL
```

USG reconstruction and terminal mismatch rate pass on all three games. The problem is exclusively possession-count drift, concentrated in the HOU/PHI sides.

---

## How the parser works (read this first)

`build_possessions()` in `src/pass2/possessions.py` is a single-pass state machine over sorted PBP actions. It tracks:

| Variable | Type | Meaning |
|---|---|---|
| `open_possession` | `OpenPossession \| None` | The currently-open possession. `None` between periods or before tip-off. |
| `live_shot` | `LiveShotAttempt \| None` | Set on `Missed Shot`; cleared when the rebound resolves the possession. `None` at all other times. |
| `ft_active` | `bool` | `True` while a free-throw trip is in progress. |
| `ft_shooter_id` | `int \| None` | Player ID of the FT shooter. |

A possession is **opened** by `open_new_possession()` and **closed + written** by `finalize_possession()`. Both reset `live_shot`, `ft_active`, and `ft_shooter_id` to their null states.

`end_possession_and_flip(offense, ...)` is the standard terminal: it finalizes the current possession and immediately opens a new one for `other_team(offense)`.

**Critical invariant:** After any call to `finalize_possession()`, `open_possession` is `None`. If you then set `ft_active = True` without also setting `open_possession`, the next rebound handler will silently drop the rebound because it checks `open_possession is not None and ft_active`.

---

## PBP data facts you must know before touching the parser

### 1. Rebound sub_types

There are exactly two values in the validation set:

| `subType` | Meaning | When it appears |
|---|---|---|
| `"Unknown"` | A player rebound with standard Off/Def stat counts | Any player rebound |
| `"Normal Rebound"` | A **dead-ball** team rebound between free throws | Always has empty `teamTricode` and `personId` = team ID |

"Normal Rebound" events occur mid-FT-trip when FT 1 of 2 is missed. They are informational (keeping team rebound stats accurate) and must be **ignored** by the parser. They are NOT live-ball rebounds.

### 2. The "Off:N Def:N" pattern in rebound descriptions

`rebound_is_offensive()` in `pbp_utils.py` parses this pattern to determine whether a rebound is offensive or defensive. **This is unreliable and should not be the primary determination method.**

The Off/Def numbers are the rebounding team's cumulative per-quarter stats for offensive and defensive rebounds. They are updated to include the current rebound, so in theory Off > Def means OREB and Def > Off means DREB. In practice this is unreliable for two reasons:

- **Off == Def** returns `None` (ambiguous), falling back to `team == live_shot.offense_tricode`.
- The cumulative nature means the counts can be misleading near the start of quarters.

**The correct primary method** for determining OREB vs DREB is `team == live_shot.offense_tricode`. If the rebounding team is the same as the team that took the shot, it is an offensive rebound. Use `rebound_is_offensive()` only as a secondary check when `live_shot` is not available.

### 3. Paired event types — actions that must be skipped

Some PBP events are companion rows that exist solely to update stats for an event already handled by a preceding action. Processing them as independent events creates phantom possession changes.

| Event | `actionType` | `subType` | What precedes it | Correct handling |
|---|---|---|---|---|
| Foul turnover | `Turnover` | `"Foul"` | An `Offensive` or `Offensive Charge` foul | **Skip.** The offensive foul closes the possession. |
| Offensive foul turnover | `Turnover` | `"Offensive Foul Turnover"` | Same offensive foul | **Skip** — same reason. |

In the validation set, `Turnover/Foul` and `Turnover/Offensive Foul Turnover` always immediately follow a `Foul/Offensive` or `Foul/Offensive Charge`. Do not process them.

### 4. Free throw sub_types and `is_last_free_throw()`

The current `is_last_free_throw()` implementation strips `"free throw"` from the sub_type and checks whether the N-of-M values match. **This breaks for flagrant FTs** because the sub_type is `"Free Throw Flagrant 2 of 2"`, which after stripping becomes `"flagrant 2 of 2"`, and `"2" != "flagrant 2"`.

All FT sub_types in the validation set:

```
Free Throw 1 of 1           → is_last=True   ✓
Free Throw 1 of 2           → is_last=False  ✓
Free Throw 1 of 3           → is_last=False  ✓
Free Throw 2 of 2           → is_last=True   ✓
Free Throw 2 of 3           → is_last=False  ✓
Free Throw 3 of 3           → is_last=True   ✓
Free Throw Flagrant 1 of 2  → is_last=False  WRONG (should be False — ok here)
Free Throw Flagrant 2 of 2  → is_last=False  WRONG (should be True)
Free Throw Flagrant 1 of 3  → is_last=False  WRONG (should be False — ok here)
Free Throw Flagrant 2 of 3  → is_last=False  WRONG (should be False — ok here)
Free Throw Flagrant 3 of 3  → is_last=False  WRONG (should be True)
```

Fix: strip `"flagrant"`, `"clear path"`, and `"technical"` from the sub_type string before the N-of-M comparison.

### 5. Foul sub_types the parser does not handle

The parser handles `Shooting`, `Shooting Block`, `Personal`, `Loose Ball`, `Offensive`, `Offensive Charge`. The following sub_types exist in the validation set but fall through unhandled:

| `subType` | Effect on possession | Correct handling |
|---|---|---|
| `"Double Technical"` | No possession change; both teams get a technical FT each (cancelled out). Ball stays with team that had it. | `continue` (ignore) |
| `"Personal Block"` | Defensive foul; results in FTs or side-out. Currently falls through, but `ft_active` gets set by the paired `Shooting Block` sub_type handler if applicable. | `continue` if no FTs; covered by `has_upcoming_free_throw` if FTs follow |
| `"Personal Take"` | Intentional foul; always results in FTs for the fouled team. Not caught by the `sub_type in ("Personal", "Loose Ball")` guard. | Treat the same as `"Personal"`: check `has_upcoming_free_throw` |
| `"Flagrant Type 1"` | Results in FTs + possession retention. The FT trip ends the possession, but the fouled team retains the ball after FTs rather than the other team getting it. | Complex — out of scope until MVP gate passes |

### 6. Violated possessions (Kicked Ball, Delay of Game)

| `subType` | Effect | Correct handling |
|---|---|---|
| `"Kicked Ball"` | The team that kicked the ball (defense, usually) loses the ball; offense retains. It is a **stoppage, not a possession change**. | `continue` (ignore). The offense does not change. |
| `"Delay Of Game"` | Warning; no possession change. | `continue` |
| `"Defensive Goaltending"` | Scoring play; handled by the paired `Made Shot` action. | Already handled with `continue`. |

### 7. Missed last FT + rebound — the possession flip problem

This is the primary source of the HOU +6 drift. The sequence is:

```
Harden FT 2 of 2  MISS
  → is_last_free_throw = True
  → end_possession_and_flip("HOU", Harden, "ft_trip")   ← flips to SAS immediately
Gasol  REBOUND (Off:1 Def:1)                             ← live_shot is None; ignored
Harden SHOOTING FOUL (HOU fouls Green)                   ← ft_active still False
Green  FT 1 of 2  (made)                                 ← open_possession is SAS, correct
Green  FT 2 of 2  MISS
  → end_possession_and_flip("SAS", Green, "ft_trip")     ← flips to HOU
Aldridge REBOUND (Off:1 Def:4)                           ← SAS OREB, but live_shot is None; ignored
```

The root problem: the parser flips to the other team on the last FT regardless of whether the FT was made or missed. When the FT is missed and the rebounding team is the offense (OREB), the flip was wrong and nothing corrects it.

**Required fix:** On a missed last FT, do not call `end_possession_and_flip`. Instead:
1. Call `finalize_possession()` to close the row.
2. Re-open a temporary possession for the FT-shooting team (they might get the OREB).
3. Set `ft_active = True` and `live_shot = None` so the next rebound resolves the flip.
4. In the rebound handler, when `live_shot is None and ft_active is True`, use `team == open_possession.offense_tricode` to determine OREB vs DREB, then open the new possession for the correct team.

The dead-ball "Normal Rebound" between FT 1 and FT 2 must be filtered before reaching this logic (see §1 above).

A made FT is detectable from the description: `"PTS"` appears in the description of a made FT and is absent from a missed FT (`"MISS ..."` prefix).

---

## Confirmed bugs (prioritized)

### Bug 1 — `is_last_free_throw` misses flagrant FTs **[HIGH]**

**File:** `src/pass2/pbp_utils.py`, `is_last_free_throw()`  
**Effect:** Flagrant FT trips are never closed. The `ft_active` flag stays True indefinitely, corrupting downstream possession logic.  
**Fix:** Strip `"flagrant"`, `"clear path"`, `"technical"` from the sub_type string before the N-of-M comparison.  
**Validation:** `is_last_free_throw("Free Throw Flagrant 2 of 2")` must return `True`.

---

### Bug 2 — Missed last FT flips immediately without waiting for the rebound **[HIGH]**

**File:** `src/pass2/possessions.py`, Free Throw handler, line ~419  
**Effect:** When the last FT is missed, `end_possession_and_flip` gives the ball to the wrong team before the rebound resolves it. Any subsequent offensive rebound is dropped (no `live_shot` to trigger the rebound handler).  
**Symptoms:** Consecutive same-team possessions on `ft_trip` → next possession. The worst case in the validation set is the HOU +6 drift in `0041600236`.  
**Fix:** Detect made vs missed from the description. On a miss, finalize the possession but re-open for the FT-shooting team with `ft_active = True`. Let the rebound handler resolve the flip.  
**Validation:** Q2 5:55 in `0041600236` — Harden misses FT 2 of 2 → SAS Gasol rebound → SAS gets the ball. Parser must produce one HOU FT possession then immediately one SAS possession.

---

### Bug 3 — "Normal Rebound" (dead-ball, between FTs) reaches the rebound handler **[MEDIUM]**

**File:** `src/pass2/possessions.py`, Rebound handler  
**Effect:** Dependent on Bug 2. If the missed-FT flip is fixed correctly (re-open possession with `ft_active = True`), the dead-ball "Normal Rebound" between FT 1 and FT 2 must be filtered before it incorrectly triggers possession logic.  
**Occurrences in `0041600236`:** Actions 36, 165, 188 (all have `subType == "Normal Rebound"` and `teamTricode == ""`).  
**Fix:** At the top of the Rebound handler, `if "Normal" in sub_type: continue`.

---

### Bug 4 — `Turnover/Foul` companion row closes an already-flipped possession **[MEDIUM]**

**File:** `src/pass2/possessions.py`, Turnover handler  
**Effect:** After the offensive foul handler correctly flips the possession, the immediately-following `Turnover/Foul` row triggers the Turnover handler again, closing the new possession for the wrong team and flipping it back. Net result: +1 phantom possession for the turnover-committing team, -1 for the other.  
**Occurrences in `0041600236`:** Q2 3:13 (Mills), Q2 2:08 (Aldridge).  
**Fix:** `if sub_type in ("Foul", "Offensive Foul Turnover"): continue` at the top of the Turnover handler.  
**Validation:** Q2 3:13 in `0041600236` — Mills OFF.Foul followed by Mills Foul Turnover. Only one possession change must occur.

---

### Bug 5 — `Foul/Personal Take` not treated as a foul-with-FTs **[LOW]**

**File:** `src/pass2/possessions.py`, Foul handler  
**Effect:** `"Personal Take"` sub_type falls through the `sub_type in ("Personal", "Loose Ball")` guard and is silently dropped. In most cases the FTs that follow are recovered via the FT handler's `if not ft_active: ft_active = True` branch, so the damage is limited. But `ft_shooter_id` will be `None` until the FT action sets it.  
**Occurrences in `0041600236`:** Q4 6:18, Q4 3:15 (Harden), Q4 2:33 (Murray).  
**Fix:** Add `"Personal Take"` to the `sub_type in (...)` set in the non-shooting foul handler.

---

## Recommended fix sequence

Fix one bug at a time. After each fix, run `make validate-possessions` and confirm the delta moves in the right direction for all three games before proceeding.

```
1. Bug 1  → fix is_last_free_throw for flagrant FTs
2. Bug 4  → skip Turnover/Foul companion rows
3. Bugs 2+3 together → missed-last-FT + dead-ball rebound (these must be done atomically)
4. Bug 5  → Personal Take
```

Do not bundle fixes. A fix that improves one game and regresses another means the fix logic is wrong — revert and understand why before trying again.

---

## Diagnostic script

To inspect the parser's state at any moment, run the single-game possessions builder and inspect the CSV:

```bash
.venv/bin/python src/pass2/possessions.py --game-id 0041600236
.venv/bin/python src/pass2/validate_possessions.py --game-id 0041600236 --rebuild
```

To find consecutive same-team possessions (should be zero in a correct parser):

```python
import pandas as pd
df = pd.read_csv("data/processed/pass2/possessions_0041600236.csv")
play = df[df["terminal_event_type"] != "period_end"]
prev = None
for _, row in play.iterrows():
    if prev is not None and row["offensive_team"] == prev["offensive_team"]:
        print(f'CONSECUTIVE poss {prev["possession_idx"]} -> {row["possession_idx"]} ({row["offensive_team"]})')
    prev = row
```

To find cross-team terminal mismatches:

```python
import pandas as pd, sys
sys.path.insert(0, ".")
from src.pass2.validate_possessions import build_player_team_map
df = pd.read_csv("data/processed/pass2/possessions_0041600236.csv")
play = df[df["terminal_event_type"] != "period_end"]
player_team = build_player_team_map("0041600236")
for _, row in play.iterrows():
    pid = row["terminal_player_id"]
    if pd.isna(pid): continue
    true = player_team.get(int(pid))
    if true and true != row["offensive_team"]:
        print(f'Poss {row["possession_idx"]}: off={row["offensive_team"]} but terminal is {true}')
```

To dump raw PBP for a specific time window:

```python
import sys; sys.path.insert(0, ".")
from src.pass2.possessions import load_pbp_payload
from src.nba_client import playbyplay_actions
from src.pass2.pbp_utils import sort_actions, iso_clock_to_seconds

payload = load_pbp_payload("0041600236")
actions = sort_actions(playbyplay_actions(payload))
for i, a in enumerate(actions):
    period = int(a.get("period") or 0)
    secs = iso_clock_to_seconds(a.get("clock",""))
    if period == 2 and 5*60 <= secs <= 6*60:
        atype = a.get("actionType","")
        sub = a.get("subType","") or ""
        team = a.get("teamTricode","")
        desc = (a.get("description") or "")[:80]
        mins, s = divmod(secs, 60)
        print(f"{i:4d} Q{period} {mins}:{s:02d} {team:4s} {atype:15s} [{sub}] | {desc}")
```

---

## What was tried and failed

A prior attempt applied fixes in the following order, bundling multiple changes per iteration:

1. Added `rebound_is_offensive` + team fallback logic for missed-FT rebounds
2. Added offensive foul handler (`Foul/Offensive`)
3. Added kicked ball handler
4. Changed rebound direction to use `team == live_shot.offense_tricode` exclusively (dropped `rebound_is_offensive`)

The last change fixed `0041600236` (HOU within tolerance) but broke `0041500405` and `0042200217` because it dropped all OREB continuity — every rebound was treated as a defensive rebound, causing possessions to close when the offense got their own rebound.

The specific failure: the `"Off:N Def:N"` numbers in rebound descriptions are per-team cumulative stats that correctly distinguish OREBs from DREBs when `live_shot` is available, but the attempt to use them as a fallback when `live_shot is None` is unreliable. The right approach is `team == live_shot.offense_tricode` when `live_shot` is not None, and explicit possession re-opening logic for the missed-last-FT case (Bug 2) rather than rebound-direction inference.

**Bottom line:** Fix the five bugs above in order. Do not change the rebound direction logic for the `live_shot is not None` case — it is correct.
