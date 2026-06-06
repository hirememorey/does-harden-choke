# Pass 2 Possession Parser — Status

**Last updated:** June 2026  
**Module:** `src/pass2/possessions.py`  
**Spec gate:** `pass2_design_spec.md` §6.1

---

## Summary

The possession parser is **functional for downstream spike work** on terminal-actor logic (USG reconstruction passes), but **fails the team possession-count gate** on 3/6 team-game checks in the validation set.

| Check | Status |
|-------|--------|
| USG% reconstruction (±3 pp) | **Pass** on all 3 validation games |
| Terminal team mismatch rate (<5%) | **Pass** (0.0%–3.7%) |
| Team possession count (±3 vs Oliver est.) | **Fail** on 3 of 6 team-rows |

---

## Validation results (three spike games)

Run: `make build-possessions && make validate-possessions`

| Game | Team | Expected | Actual | Δ | Pass? |
|------|------|----------|--------|---|-------|
| `0041600236` (Harden 2017 G6) | SAS | 94.7 | 92 | −2.7 | ✓ |
| `0041600236` | HOU | 91.0 | 97 | **+6.0** | ✗ |
| `0041500405` (LeBron 2016 G5) | GSW | 103.4 | 101 | −2.4 | ✓ |
| `0041500405` | CLE | 101.1 | 98 | −3.1 | ✗ (borderline) |
| `0042200217` (Harden 2023 G7) | BOS | 94.9 | 92 | −2.9 | ✓ |
| `0042200217` | PHI | 96.4 | 92 | **−4.4** | ✗ |

### USG reconstruction (focus players)

| Game | Player | Box USG | Reconstructed | Δ (pp) |
|------|--------|---------|---------------|--------|
| `0041600236` | Harden | 25.5% | 25.7% | +0.2 |
| `0041500405` | LeBron | 36.6% | 36.8% | +0.2 |
| `0042200217` | Harden | 19.2% | 20.5% | +1.2 |

---

## What's passing

1. **Terminal-actor assignment** — Usage reconstructs within 0.2–1.2 pp of box score USG. Wrong-team terminal rate is <4% across validation games.
2. **Jump-ball / tip resolution** — Fixed cross-team `resolve_player_id` bug (Mills was matching on HOU roster).
3. **Team rebound tricode** — Empty `teamTricode` on team rebounds now resolves via `teamId` / `personId` → team map.
4. **Offensive rebound continuity** — `live_shot` state persists through OREBs instead of clearing on offensive boards.

---

## What's failing

**Team possession totals** drift asymmetrically: HOU +6 in 2017 G6, PHI −4.4 in 2023 G7. Total game possessions are close (~188–193 vs ~186 expected), but the **split between teams** is off by ~5 possessions in the worst cases.

---

## Hypotheses (ranked)

1. **FT-trip / made-shot boundary** — And-1 detection (`has_immediate_free_throw`) may merge or split possessions incorrectly; missed last-FT + defensive rebound sequences may double-flip offense.
2. **Loose-ball fouls mid-possession** — Fouls that don't end the possession but precede a steal/turnover (e.g. Q1 6:50 in `0041600236`) may leave offense state misaligned.
3. **Shooting foul without prior rebound** — Miss → shooting foul → FT trip should be one possession; if `live_shot` clears early, an extra possession may appear.
4. **Residual cross-team terminals** — 7 possessions in 2017 G6 still have terminal player on opposite team from `offensive_team` (down from 14 pre-fix).

---

## PBP sequences to inspect

### Game `0041600236` — Q1 6:50 (loose-ball foul + steal)

```
6:50 SAS  MISS Green 3PT
6:50      Rebound Spurs Rebound   ← teamTricode empty; personId = SAS team id
6:50 HOU  Beverley L.B.FOUL
6:43 HOU  Ariza STEAL
6:43 SAS  Gasol TOV
6:40 HOU  Beverley MAKE
```

Parser historically opened a `nan` offense row on the team rebound before fixes. Re-check possession assignment through this sequence.

### Game `0041600236` — possession 140 (Harden ft_trip on SAS offense)

Terminal: Harden (`201935`) on `offensive_team = SAS`. Indicates offense flip error after prior possession ended.

### Game `0041600236` — Q2 1:59 (OREB then def reb)

```
2:01 HOU MISS Anderson
2:00 HOU MISS Anderson tip
2:00 HOU OREB Anderson
1:59 SAS REB Ginobili          ← should end HOU possession, open SAS
1:43 SAS MAKE Aldridge         ← was briefly attributed to HOU offense pre-OREB fix
```

### Game `0041600236` — Q2 5:55 (missed FTs)

Harden 0-for-2 at the line — Event B "empty FT trip" not yet modeled in parser; may affect count if FT sequence splits wrong.

---

## How to reproduce

```bash
make scrape-pbp              # if data/raw/pbp/ missing
make build-possessions
make validate-possessions      # exits 1 while count gate fails
```

Single game:

```bash
.venv/bin/python src/pass2/possessions.py --game-id 0041600236
.venv/bin/python src/pass2/validate_possessions.py --game-id 0041600236
```

Outputs: `data/processed/pass2/possessions_{game_id}.csv`

---

## Acceptance criteria (§6.1)

Before scaling PBP scrape to full playoff cohort:

- [ ] Both teams within **±3 possessions** of Oliver estimate per game
- [x] USG% reconstruction within **±3 pp** for focus players
- [x] Terminal mismatch rate **< 5%**
- [ ] Spot-check 10 possessions manually in 3 games (≥9/10 match) — not yet done
- [ ] Substitution accuracy **< 5%** error — not yet measured

---

## Next steps (after count gate passes)

1. Adversity event detector (`src/pass2/adversity_events.py`)
2. Response windows + baseline matching
3. Full playoff cohort PBP scrape
