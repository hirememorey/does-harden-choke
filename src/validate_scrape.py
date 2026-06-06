"""Pass 1 — Validate scraped player CSVs against config and NBA Stats API samples.

See documents/development/findings.md for Pass 1 pipeline context.
"""

from __future__ import annotations

import argparse
import logging
import sys
import unicodedata
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from src.nba_client import NBAStatsClient, result_set_to_records

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _normalize_name(name: str) -> str:
    folded = unicodedata.normalize("NFKD", str(name))
    return "".join(c.lower() for c in folded if c.isalnum())


def validate_csv_identity(name: str, df: pd.DataFrame) -> list[str]:
    """Check nba_id and player_name in file match config."""
    issues: list[str] = []
    expected_id = config.ALL_PLAYERS[name]["nba_id"]
    if "nba_id" not in df.columns:
        issues.append("missing nba_id column")
        return issues
    ids = df["nba_id"].dropna().unique()
    if len(ids) != 1 or int(ids[0]) != expected_id:
        issues.append(f"nba_id mismatch: file={ids.tolist()} expected={expected_id}")
    if "player_name" in df.columns:
        names = df["player_name"].dropna().unique()
        if len(names) != 1 or _normalize_name(names[0]) != _normalize_name(name):
            issues.append(f"player_name mismatch: file={names.tolist()} expected={name}")
    return issues


def api_game_count(
    client: NBAStatsClient,
    nba_id: int,
    season: str,
    season_type: str,
) -> int:
    resp = client.get_player_game_logs(nba_id, season, season_type, "Base")
    return len(result_set_to_records(resp))


def validate_player(
    client: NBAStatsClient,
    name: str,
    check_seasons: list[str] | None = None,
) -> dict:
    slug = config.player_slug(name)
    rs_path = config.RAW_DIR / f"{slug}_rs.csv"
    po_path = config.RAW_DIR / f"{slug}_po.csv"
    meta = config.ALL_PLAYERS[name]
    nba_id = meta["nba_id"]
    result: dict = {"name": name, "issues": [], "checks": []}

    resp = client.get_common_player_info(nba_id)
    api_name = result_set_to_records(resp)[0].get("DISPLAY_FIRST_LAST", "")
    if _normalize_name(api_name) != _normalize_name(name):
        result["issues"].append(f"API id {nba_id} resolves to {api_name!r}")

    if not rs_path.exists() and not po_path.exists():
        result["issues"].append("no CSV files")
        return result

    debut = int(result_set_to_records(resp)[0].get("FROM_YEAR", 1996))
    seasons = check_seasons or [
        config.year_to_season(debut),
        "2023-24",
    ]

    for path, stype in [(rs_path, "Regular Season"), (po_path, "Playoffs")]:
        if not path.exists():
            result["issues"].append(f"missing {path.name}")
            continue
        df = pd.read_csv(path)
        result["issues"].extend(validate_csv_identity(name, df))
        result[f"{path.stem}_rows"] = len(df)

        if "season" not in df.columns:
            continue
        for season in seasons:
            if config.season_to_year(season) < debut:
                continue
            csv_n = len(df[df["season"] == season])
            try:
                api_n = api_game_count(client, nba_id, season, stype)
            except Exception as exc:
                result["issues"].append(f"API error {season} {stype}: {exc}")
                continue
            ok = csv_n == api_n
            result["checks"].append(
                {
                    "file": path.name,
                    "season": season,
                    "csv": csv_n,
                    "api": api_n,
                    "ok": ok,
                }
            )
            if not ok:
                result["issues"].append(
                    f"{path.name} {season}: csv={csv_n} api={api_n}"
                )

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate scraped player data")
    parser.add_argument("--players", nargs="*", help="Player names (default: all with CSVs)")
    args = parser.parse_args()

    client = NBAStatsClient(min_interval=0.8)
    if args.players:
        players = args.players
    else:
        players = []
        for name in config.ALL_PLAYERS:
            slug = config.player_slug(name)
            if (config.RAW_DIR / f"{slug}_rs.csv").exists() or (
                config.RAW_DIR / f"{slug}_po.csv"
            ).exists():
                players.append(name)

    all_ok = True
    for name in players:
        r = validate_player(client, name)
        status = "OK" if not r["issues"] else "FAIL"
        if r["issues"]:
            all_ok = False
        logger.info(
            "%s [%s] RS=%s PO=%s issues=%s",
            name,
            status,
            r.get(f"{config.player_slug(name)}_rs_rows", "?"),
            r.get(f"{config.player_slug(name)}_po_rows", "?"),
            r["issues"] or "none",
        )
        for c in r.get("checks", []):
            mark = "✓" if c["ok"] else "✗"
            logger.info(
                "  %s %s %s: csv=%d api=%d",
                mark,
                c["file"],
                c["season"],
                c["csv"],
                c["api"],
            )

    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
