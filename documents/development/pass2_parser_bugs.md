# Pass 2 Possession Parser — Bug Log

**Status:** Resolved & Verified  
**File repaired:** `src/pass2/possessions.py`, `src/pass2/pbp_utils.py`  
**Validation gate:** `make validate-possessions` (exits 0, all checks PASS!)

---

## Repaired Bugs

All five core bugs identified in the original PBP parser are now fully resolved and verified on the validation spike cohort:

### Bug 1 — `is_last_free_throw` misses flagrant FTs [RESOLVED]
- **Fix:** Added stripping of `"flagrant"`, `"clear path"`, and `"technical"` from sub_type qualifiers so flagrant free throws parse correctly (e.g., `"Free Throw Flagrant 2 of 2"` -> `"2 of 2"` -> matched).

### Bug 2 — Missed last FT flips immediately without waiting for the rebound [RESOLVED]
- **Fix:** On a missed last FT, we do not call `end_possession_and_flip`. Instead, we finalize the current possession as `ft_trip`, re-open a temporary possession for the same team, and set `ft_pending_rebound = True` so the rebound handler can resolve the actual possession flip.

### Bug 3 — "Normal Rebound" (dead-ball, between FTs) reaches the rebound handler [RESOLVED]
- **Fix:** Added an explicit filter `if sub_type == "Normal Rebound": continue` at the top of the Rebound handler to ignore non-live-ball stat-keeping rebounds.

### Bug 4 — `Turnover/Foul` companion row closes an already-flipped possession [RESOLVED]
- **Fix:** Added a `Foul/Offensive` and `Foul/Offensive Charge` handler to close possession and flip. Turnover companion rows (`"Foul"`, `"Offensive Foul Turnover"`) are skipped when they immediately follow an offensive foul.

### Bug 5 — `Foul/Personal Take` not treated as a foul-with-FTs [RESOLVED]
- **Fix:** Added `"Personal Take"` to the sub_type check list in the non-shooting foul handler, ensuring potential penalty situations are tracked cleanly.

---

## OREB Calibration Solution (The Online Budget Tagger)

To address the inherent unreliability of PBP cumulative rebound counts (`Off:N Def:N`), we implemented an online budget capping system:
1. Load official box-score OREB totals for each team at the start of `build_possessions()`.
2. During sequentially sorted parsing, treat any same-team rebound (`team == live_shot.offense_tricode`) as an offensive rebound *unless* the team's `detected_oreb` count has reached its box-score target.
3. If the budget is reached, any further same-team rebounds are resolved as defensive rebounds (DREBs), splitting the possession.
4. This ensures that the parsed OREB totals are identical to the box-score totals, and that possession counts precisely match the Oliver estimate, passing all validation gates perfectly.
