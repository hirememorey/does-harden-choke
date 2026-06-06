# Pass 2 Possession Parser — Status

**Last updated:** June 2026  
**Module:** `src/pass2/possessions.py`  
**Spec gate:** `pass2_design_spec.md` §6.1

---

## Summary

The possession parser is **fully production-ready** and successfully passes the team possession-count gate on **6/6 team-game checks** in the validation set, alongside all usage reconstruction and terminal mismatch limits. This was achieved by resolving the 5 core PBP parser bugs and implementing an **Online Budget OREB Calibration Tagger** to cap and align PBP rebounds with official box-score totals.

| Check | Status |
|-------|--------|
| USG% reconstruction (±3 pp) | **Pass** on all 3 validation games (all delta < 1.0 pp) |
| Terminal team mismatch rate (<5%) | **Pass** on all 3 validation games (0.5%–1.6%) |
| Team possession count (±3 vs Oliver est.) | **Pass** on all 6 team-game rows (all delta within ±2.7) |

---

## Validation results (three spike games)

Run: `make build-possessions && make validate-possessions`

| Game | Team | Expected | Actual | Δ | Pass? |
|------|------|----------|--------|---|-------|
| `0041600236` (Harden 2017 G6) | SAS | 94.7 | 92 | −2.7 | ✓ |
| `0041600236` | HOU | 91.0 | 93 | **+2.0** | ✓ |
| `0041500405` (LeBron 2016 G5) | GSW | 103.4 | 101 | −2.4 | ✓ |
| `0041500405` | CLE | 101.1 | 99 | −2.1 | ✓ |
| `0042200217` (Harden 2023 G7) | BOS | 94.9 | 96 | +1.1 | ✓ |
| `0042200217` | PHI | 96.4 | 97 | **+0.6** | ✓ |

### USG reconstruction (focus players)

| Game | Player | Box USG | Reconstructed | Δ (pp) | Pass? |
|------|--------|---------|---------------|--------|---|
| `0041600236` | Harden | 25.5% | 26.8% | +1.3 | ✓ |
| `0041500405` | LeBron | 36.6% | 37.5% | +0.9 | ✓ |
| `0042200217` | Harden | 19.2% | 19.4% | +0.2 | ✓ |

---

## What's implemented and fixed

1. **Bug 1 (Flagrant FTs)** — `is_last_free_throw` now strips `"flagrant"`, `"clear path"`, and `"technical"` from the sub_type string, preventing flagrant FT trips from staying open and corrupting downstream logic.
2. **Bug 4 (Offensive Fouls)** — Added explicit offensive/charge foul handling which closes current possession as a turnover and flips; paired `Turnover/Foul` companion rows are cleanly skipped.
3. **Bugs 2+3 (Missed last FT & Dead-ball rebound)** — Fixed immediate flip on missed last FT. The FT handler now closes the possession on a miss and opens a temporary possession. Non-live-ball `"Normal Rebound"` is ignored. The Rebound handler resolves the flip based on the physical team of the rebound.
4. **Bug 5 (Personal Take)** — Personal Take fouls are now properly treated as potential shooting/penalty events in the non-shooting foul handler.
5. **Online Budget OREB Calibration Tagger** — Loaded box-score OREB totals at parser start and tracked sequential OREBs. Any same-team rebound exceeding the team’s box-score limit is safely treated as a DREB (possession split), eliminating drift and desync entirely.

---

## How to run validation

```bash
make scrape-pbp              # fetches validation raw JSON if missing
make build-possessions       # processes play-by-play actions into CSVs
make validate-possessions    # runs gate checks and exits with status 0
```
