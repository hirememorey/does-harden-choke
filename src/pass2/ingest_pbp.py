"""Pass 2 Step 1: fetch and cache play-by-play JSON for validation games."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import config
from src.nba_client import NBAStatsClient, create_client, normalize_game_id, playbyplay_actions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def load_validation_games(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or config.PASS2_VALIDATION_GAMES
    with open(path) as f:
        payload = json.load(f)
    return payload["games"]


def pbp_output_path(game_id: str, raw_dir: Path | None = None) -> Path:
    raw_dir = raw_dir or config.RAW_PBP_DIR
    return raw_dir / f"{normalize_game_id(game_id)}.json"


def fetch_game_pbp(
    client: NBAStatsClient,
    game_id: str | int,
    *,
    force: bool = False,
    raw_dir: Path | None = None,
) -> dict[str, Any]:
    gid = normalize_game_id(game_id)
    out_path = pbp_output_path(gid, raw_dir=raw_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and not force:
        logger.info("Cache hit (file): %s", out_path.name)
        with open(out_path) as f:
            return json.load(f)

    logger.info("Fetching play-by-play for %s", gid)
    payload = client.get_play_by_play(gid)
    actions = playbyplay_actions(payload)
    if not actions:
        raise RuntimeError(f"No play-by-play actions returned for game {gid}")

    with open(out_path, "w") as f:
        json.dump(payload, f)

    return payload


def summarize_game(payload: dict[str, Any], meta: dict[str, Any] | None = None) -> dict[str, Any]:
    game = payload.get("game") or {}
    actions = playbyplay_actions(payload)
    periods = sorted({a.get("period") for a in actions if a.get("period")})
    player_ids = sorted({a.get("personId") for a in actions if a.get("personId")})
    summary = {
        "game_id": game.get("gameId") or meta.get("game_id") if meta else None,
        "action_count": len(actions),
        "periods": ",".join(str(p) for p in periods),
        "distinct_player_ids": len(player_ids),
        "video_available": game.get("videoAvailable"),
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    if meta:
        summary.update(
            {
                "label": meta.get("label"),
                "date": meta.get("date"),
                "matchup": meta.get("matchup"),
                "focus_player": meta.get("focus_player"),
                "focus_player_id": meta.get("focus_player_id"),
            }
        )
    return summary


def ingest_games(
    games: list[dict[str, Any]],
    *,
    client: NBAStatsClient | None = None,
    force: bool = False,
) -> pd.DataFrame:
    client = client or create_client()
    config.RAW_PBP_DIR.mkdir(parents=True, exist_ok=True)
    config.PROCESSED_PASS2_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for game in games:
        gid = normalize_game_id(game["game_id"])
        payload = fetch_game_pbp(client, gid, force=force)
        row = summarize_game(payload, meta=game)
        rows.append(row)
        logger.info(
            "%s (%s): %s actions across periods [%s]",
            game.get("label", gid),
            gid,
            row["action_count"],
            row["periods"],
        )

    manifest = pd.DataFrame(rows)
    manifest_path = config.PROCESSED_PASS2_DIR / "pbp_manifest.csv"
    manifest.to_csv(manifest_path, index=False)
    logger.info("Wrote manifest: %s", manifest_path)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch and cache NBA play-by-play JSON.")
    parser.add_argument(
        "--validation",
        action="store_true",
        help="Fetch the 3 hand-checked validation games from pass2_validation_games.json.",
    )
    parser.add_argument(
        "--game-id",
        action="append",
        dest="game_ids",
        help="Explicit game ID(s) to fetch (repeatable).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-fetch even if cached JSON exists on disk.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.validation:
        games = load_validation_games()
    elif args.game_ids:
        games = [{"label": gid, "game_id": normalize_game_id(gid)} for gid in args.game_ids]
    else:
        games = load_validation_games()
        logger.info("No flags passed; defaulting to validation spike games.")

    manifest = ingest_games(games, force=args.force)
    print(manifest.to_string(index=False))


if __name__ == "__main__":
    main()
