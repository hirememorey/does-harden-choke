"""Causal chain Step 0 — validate team ORtg from scraped team game logs."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from src.nba_client import normalize_game_id
from src.scrape_team_logs import TEAM_LOGS_PATH, collect_team_season_keys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ORTG_TOLERANCE = 1.0


def estimate_possessions(row: pd.Series, opp_dreb: float | None = None) -> float | None:
    """Dean Oliver team possessions estimate from box score."""
    fga = row.get("fga")
    fgm = row.get("fgm")
    oreb = row.get("oreb")
    tov = row.get("tov")
    fta = row.get("fta")

    if any(pd.isna(v) for v in (fga, fgm, oreb, tov, fta)):
        return None

    if opp_dreb is None or pd.isna(opp_dreb) or (oreb + opp_dreb) == 0:
        oreb_factor = 0.0
    else:
        oreb_factor = oreb / (oreb + opp_dreb)

    return float(fga - oreb_factor * (fga - fgm) + tov + 0.44 * fta)


def compute_ortg_from_box(row: pd.Series, opp_dreb: float | None = None) -> float | None:
    pts = row.get("pts")
    poss = row.get("poss")
    if pd.notna(poss) and poss > 0 and pd.notna(pts):
        return 100.0 * float(pts) / float(poss)

    est = estimate_possessions(row, opp_dreb=opp_dreb)
    if est is None or est <= 0 or pd.isna(pts):
        return None
    return 100.0 * float(pts) / est


def join_opponent_dreb(df: pd.DataFrame) -> pd.DataFrame:
    """Attach opponent DREB for possession formula validation."""
    if df.empty or "game_id" not in df.columns or "team_id" not in df.columns:
        return df

    opp = df[["game_id", "team_id", "dreb"]].rename(
        columns={"team_id": "opp_team_id", "dreb": "opp_dreb"}
    )
    out = df.merge(
        opp,
        left_on=["game_id", "opponent_team_id"] if "opponent_team_id" in df.columns else ["game_id"],
        right_on=["game_id", "opp_team_id"] if "opponent_team_id" in df.columns else ["game_id"],
        how="left",
    )
    return out


def validate_ortg(
    team_logs: pd.DataFrame,
    sample_n: int = 10,
    seed: int = 42,
) -> dict:
    """Compare API off_rating to formula-derived ORtg and API poss."""
    df = team_logs.copy()

    required = {"game_id", "pts", "off_rating"}
    missing = required - set(df.columns)
    if missing:
        return {"ok": False, "error": f"missing columns: {sorted(missing)}"}

    # Build opponent DREB lookup via game_id + opponent abbrev if team_id join unavailable.
    if "opponent" in df.columns:
        opp_map = df.set_index(["game_id", "team"])["dreb"].to_dict()
        df["opp_dreb"] = df.apply(
            lambda r: opp_map.get((r["game_id"], r.get("opponent"))), axis=1
        )
    else:
        df["opp_dreb"] = np.nan

    df["ortg_from_poss"] = df.apply(
        lambda r: compute_ortg_from_box(r, opp_dreb=r.get("opp_dreb")), axis=1
    )
    df["ortg_from_formula"] = df.apply(
        lambda r: compute_ortg_from_box(
            r,
            opp_dreb=r.get("opp_dreb"),
        )
        if pd.isna(r.get("poss"))
        else np.nan,
        axis=1,
    )

    valid = df.dropna(subset=["off_rating", "ortg_from_poss"]).copy()
    if valid.empty:
        return {"ok": False, "error": "no rows with comparable ORtg"}

    valid["ortg_delta"] = valid["ortg_from_poss"] - valid["off_rating"]
    valid["abs_delta"] = valid["ortg_delta"].abs()

    rng = np.random.default_rng(seed)
    sample_idx = rng.choice(valid.index, size=min(sample_n, len(valid)), replace=False)
    sample = valid.loc[sample_idx].sort_values("abs_delta", ascending=False)

    within_tol = (valid["abs_delta"] <= ORTG_TOLERANCE).mean()
    sample_within = (sample["abs_delta"] <= ORTG_TOLERANCE).mean()

    result = {
        "ok": bool(within_tol >= 0.9),
        "rows_compared": int(len(valid)),
        "pct_within_tolerance": float(within_tol),
        "mean_abs_delta": float(valid["abs_delta"].mean()),
        "max_abs_delta": float(valid["abs_delta"].max()),
        "tolerance": ORTG_TOLERANCE,
        "sample": sample[
            [
                c
                for c in [
                    "game_id",
                    "season",
                    "team",
                    "opponent",
                    "pts",
                    "poss",
                    "off_rating",
                    "ortg_from_poss",
                    "ortg_delta",
                ]
                if c in sample.columns
            ]
        ].to_dict("records"),
        "sample_pct_within_tolerance": float(sample_within),
    }
    return result


def validate_join_coverage(team_logs: pd.DataFrame, sample_n: int = 10) -> dict:
    """Check team logs join rate to player cohort game_ids."""
    keys = collect_team_season_keys()
    player_frames = []
    usecols = {"game_id", "team_id", "season", "is_playoff"}
    for name in config.ALL_PLAYERS:
        slug = config.player_slug(name)
        for suffix in ("_rs", "_po"):
            p = config.RAW_DIR / f"{slug}{suffix}.csv"
            if p.exists():
                player_frames.append(pd.read_csv(p, usecols=lambda c: c in usecols))

    players = pd.concat(player_frames, ignore_index=True)
    players["game_id"] = players["game_id"].apply(normalize_game_id)
    player_games = players.drop_duplicates(subset=["game_id", "team_id"])

    team_logs = team_logs.copy()
    team_logs["game_id"] = team_logs["game_id"].apply(normalize_game_id)

    merged = player_games.merge(
        team_logs,
        on=["game_id", "team_id"],
        how="left",
        indicator=True,
        suffixes=("", "_team"),
    )
    join_rate = (merged["_merge"] == "both").mean()

    missing = merged[merged["_merge"] == "left_only"].head(sample_n)
    return {
        "ok": bool(join_rate >= 0.95),
        "player_game_rows": int(len(player_games)),
        "join_rate": float(join_rate),
        "missing_sample": missing[["game_id", "team_id", "season", "is_playoff"]].to_dict("records"),
    }


def validate_league_ortg(team_logs: pd.DataFrame) -> dict:
    """Sanity check: recent-season mean ORtg should be near league average."""
    if "season" not in team_logs.columns or "off_rating" not in team_logs.columns:
        return {"ok": False, "error": "missing season/off_rating"}

    recent = team_logs[team_logs["season"].isin(["2022-23", "2023-24", "2024-25"])]
    if recent.empty:
        return {"ok": False, "error": "no recent seasons"}

    means = recent.groupby("season")["off_rating"].mean().round(1)
    ok = bool(((means >= 108) & (means <= 118)).all())
    return {"ok": ok, "recent_mean_off_rating_by_season": means.to_dict()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate team game logs")
    parser.add_argument("--path", type=Path, default=TEAM_LOGS_PATH)
    parser.add_argument("--sample", type=int, default=10)
    args = parser.parse_args()

    if not args.path.exists():
        logger.error("Missing %s — run scrape_team_logs.py first", args.path)
        sys.exit(1)

    df = pd.read_csv(args.path, low_memory=False)
    logger.info("Loaded %d team-game rows (%d unique games)", len(df), df["game_id"].nunique())

    league = validate_league_ortg(df)
    logger.info("League ORtg sanity: %s", league)

    join = validate_join_coverage(df, sample_n=args.sample)
    logger.info(
        "Join coverage: %.1f%% (%d player-game rows)",
        100 * join["join_rate"],
        join["player_game_rows"],
    )
    if join["missing_sample"]:
        logger.warning("Missing join sample: %s", join["missing_sample"][:3])

    ortg = validate_ortg(df, sample_n=args.sample)
    if ortg.get("error"):
        logger.error("ORtg validation error: %s", ortg["error"])
        sys.exit(1)

    logger.info(
        "ORtg check: %.1f%% within ±%.1f (mean |delta|=%.2f, max=%.2f)",
        100 * ortg["pct_within_tolerance"],
        ortg["tolerance"],
        ortg["mean_abs_delta"],
        ortg["max_abs_delta"],
    )

    for row in ortg["sample"]:
        logger.info(
            "  %s %s vs %s: API=%.1f formula=%.1f delta=%+.1f",
            row.get("game_id"),
            row.get("team"),
            row.get("opponent"),
            row.get("off_rating"),
            row.get("ortg_from_poss"),
            row.get("ortg_delta"),
        )

    all_ok = league.get("ok", False) and join.get("ok", False) and ortg.get("ok", False)
    if not all_ok:
        logger.error("Validation FAILED")
        sys.exit(1)
    logger.info("Validation OK")


if __name__ == "__main__":
    main()
