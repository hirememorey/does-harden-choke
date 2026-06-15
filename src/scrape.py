"""Data collection: player game logs, team series map, opponent ratings."""

from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from src.nba_client import NBAStatsClient, result_set_to_records

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

MATCHUP_RE = re.compile(r"^(\w+)\s+(vs\.|@)\s+(\w+)$")


def parse_matchup(matchup: str) -> tuple[str, str, str]:
    """Return (team_abbrev, opponent_abbrev, home_away)."""
    m = MATCHUP_RE.match(str(matchup).strip())
    if not m:
        return "", "", ""
    team, loc, opp = m.group(1), m.group(2), m.group(3)
    home_away = "home" if loc == "vs." else "away"
    return team, opp, home_away


def compute_game_score(row: pd.Series) -> float:
    """John Hollinger Game Score from box score."""
    oreb = row.get("oreb")
    dreb = row.get("dreb")
    reb = row.get("reb", 0) or 0
    if pd.isna(oreb) or pd.isna(dreb):
        oreb = 0.25 * reb
        dreb = 0.75 * reb
    fta = row.get("fta", 0) or 0
    ftm = row.get("ftm", 0) or 0
    return (
        (row.get("pts", 0) or 0)
        + 0.4 * (row.get("fgm", 0) or 0)
        + 0.7 * oreb
        + 0.3 * dreb
        + (row.get("stl", 0) or 0)
        + 0.7 * (row.get("ast", 0) or 0)
        + 0.7 * (row.get("blk", 0) or 0)
        - 0.7 * (row.get("fga", 0) or 0)
        - 0.4 * (fta - ftm)
        - 0.4 * (row.get("pf", 0) or 0)
        - (row.get("tov", 0) or 0)
    )


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase snake_case column names."""
    df = df.copy()
    df.columns = [
        c.lower().replace("%", "_pct").replace("+/-", "plus_minus")
        for c in df.columns
    ]
    # common API aliases
    renames = {
        "season_year": "season",
        "team_abbreviation": "team",
        "game_date": "game_date",
    }
    df = df.rename(columns={k: v for k, v in renames.items() if k in df.columns})
    return df


def records_to_df(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    return normalize_columns(pd.DataFrame(records))


def get_player_debut_start_year(client: NBAStatsClient, nba_id: int) -> int:
    """First NBA season start year from commonplayerinfo FROM_YEAR."""
    resp = client.get_common_player_info(nba_id)
    records = result_set_to_records(resp)
    if not records:
        return config.SEASON_START_YEARS[0]
    from_year = records[0].get("FROM_YEAR")
    if from_year is None:
        return config.SEASON_START_YEARS[0]
    return int(from_year)


def seasons_for_player(all_seasons: list[str], debut_start_year: int) -> list[str]:
    """Drop seasons before the player's NBA debut."""
    return [s for s in all_seasons if config.season_to_year(s) >= debut_start_year]


def fetch_merged_player_logs(
    client: NBAStatsClient,
    player_id: int,
    season: str,
    season_type: str,
) -> pd.DataFrame:
    """Fetch Base + Advanced player game logs and merge."""
    base = result_set_to_records(
        client.get_player_game_logs(player_id, season, season_type, "Base")
    )
    if not base:
        return pd.DataFrame()
    df_base = records_to_df(base)
    try:
        adv = result_set_to_records(
            client.get_player_game_logs(player_id, season, season_type, "Advanced")
        )
    except Exception as exc:
        logger.warning(
            "Advanced logs failed for player %s %s %s: %s (using Base only)",
            player_id,
            season,
            season_type,
            exc,
        )
        return df_base
    if not adv:
        return df_base
    df_adv = records_to_df(adv)
    merge_keys = [c for c in ("game_id", "player_id", "season") if c in df_base.columns and c in df_adv.columns]
    if not merge_keys:
        merge_keys = ["game_id"] if "game_id" in df_base.columns else []
    if not merge_keys:
        return df_base
    extra = [c for c in df_adv.columns if c not in df_base.columns and c not in merge_keys]
    return df_base.merge(df_adv[merge_keys + extra], on=merge_keys, how="left")


def fetch_merged_player_logs_safe(
    client: NBAStatsClient,
    player_id: int,
    season: str,
    season_type: str,
) -> pd.DataFrame | None:
    """
    Per-season fetch with error isolation.
    Returns None if the season could not be fetched after retries.
    """
    try:
        return fetch_merged_player_logs(client, player_id, season, season_type)
    except Exception as exc:
        logger.error(
            "Skipping %s %s for player %s after retries: %s",
            season,
            season_type,
            player_id,
            exc,
        )
        return None


def build_team_series_map(playoff_games: pd.DataFrame) -> pd.DataFrame:
    """
    Infer series game numbers from team playoff game logs.
    Splits series when gap > SERIES_GAP_DAYS vs same opponent.
    """
    if playoff_games.empty:
        return pd.DataFrame()

    df = playoff_games.copy()
    df["game_date"] = pd.to_datetime(df["game_date"])
    rows = []

    for (season, team), grp in df.groupby(["season", "team"]):
        grp = grp.sort_values("game_date")
        # group consecutive games vs same opponent with gap logic
        series_id = 0
        prev_opp = None
        prev_date = None
        game_nums: list[int] = []
        team_wins: list[int] = []
        opp_wins: list[int] = []
        wins_running = 0
        opp_wins_running = 0

        for _, row in grp.iterrows():
            opp = row["opponent"]
            dt = row["game_date"]
            if prev_opp is None or opp != prev_opp:
                series_id += 1
                game_num = 1
                wins_running = 0
                opp_wins_running = 0
            elif prev_date is not None and (dt - prev_date).days > config.SERIES_GAP_DAYS:
                series_id += 1
                game_num = 1
                wins_running = 0
                opp_wins_running = 0
            else:
                game_num += 1

            # Elimination status uses series score before this game.
            is_elim = (wins_running == 3) or (opp_wins_running == 3)
            game_nums.append(game_num)
            team_wins.append(wins_running)
            opp_wins.append(opp_wins_running)

            wl = str(row.get("wl", row.get("w", ""))).upper()
            if wl == "W":
                wins_running += 1
            elif wl == "L":
                opp_wins_running += 1

            prev_opp = opp
            prev_date = dt

        out = grp.copy()
        out["series_game_num"] = game_nums
        out["team_wins_so_far"] = team_wins
        out["opponent_wins_so_far"] = opp_wins
        out["is_elimination"] = [
            (tw == 3) or (ow == 3) for tw, ow in zip(team_wins, opp_wins)
        ]
        rows.append(out)

    result = pd.concat(rows, ignore_index=True)
    keep = [
        "season",
        "team",
        "opponent",
        "game_date",
        "series_game_num",
        "is_elimination",
        "team_wins_so_far",
        "opponent_wins_so_far",
    ]
    return result[[c for c in keep if c in result.columns]]


def fetch_playoff_games_for_season(client: NBAStatsClient, season: str) -> pd.DataFrame:
    records = result_set_to_records(
        client.get_league_game_finder(season, "Playoffs", "T")
    )
    df = records_to_df(records)
    if df.empty:
        return df
    parsed = df["matchup"].apply(parse_matchup)
    df["team"] = parsed.apply(lambda x: x[0])
    df["opponent"] = parsed.apply(lambda x: x[1])
    df["home_away"] = parsed.apply(lambda x: x[2])
    if "season" not in df.columns and "season_id" in df.columns:
        df["season"] = season
    elif "season" not in df.columns:
        df["season"] = season
    df["game_date"] = pd.to_datetime(df["game_date"])
    return df


def enrich_player_logs(df: pd.DataFrame, player_name: str) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    parsed = df["matchup"].apply(parse_matchup)
    df["team"] = parsed.apply(lambda x: x[0])
    df["opponent"] = parsed.apply(lambda x: x[1])
    df["home_away"] = parsed.apply(lambda x: x[2])
    df["player_name"] = player_name
    df["player_group"] = config.PLAYER_GROUP[player_name]
    df["nba_id"] = config.ALL_PLAYERS[player_name]["nba_id"]
    df["game_date"] = pd.to_datetime(df["game_date"])

    col_map = {
        "min": "minutes",
        "pts": "pts",
        "fgm": "fgm",
        "fga": "fga",
        "fg_pct": "fg_pct",
        "fg3m": "fg3m",
        "fg3a": "fg3a",
        "fg3_pct": "fg3_pct",
        "ftm": "ftm",
        "fta": "fta",
        "ft_pct": "ft_pct",
        "oreb": "oreb",
        "dreb": "dreb",
        "reb": "reb",
        "ast": "ast",
        "stl": "stl",
        "blk": "blk",
        "tov": "tov",
        "pf": "pf",
        "plus_minus": "plus_minus",
        "ts_pct": "ts_pct",
        "usg_pct": "usg_pct",
        "ast_pct": "ast_pct",
        "bpm": "bpm",
    }
    for src, dst in col_map.items():
        if src in df.columns and dst not in df.columns:
            df[dst] = df[src]

    if "minutes" in df.columns:
        df["minutes"] = pd.to_numeric(
            df["minutes"].astype(str).str.replace(":", "."), errors="coerce"
        )

    df["game_score"] = df.apply(compute_game_score, axis=1)
    df["is_injury_flagged"] = df["minutes"].fillna(0) <= 15
    df = df[df["minutes"].fillna(0) > 0]

    df = df.sort_values("game_date")
    df["rest_days"] = df["game_date"].diff().dt.days
    if "fga" in df.columns and "fta" in df.columns and "tov" in df.columns:
        df["usage_rate_approx"] = df["fga"] + 0.44 * df["fta"].fillna(0) + df["tov"].fillna(0)
    return df


SERIES_CONTEXT_COLS = (
    "series_game_num",
    "is_elimination",
    "team_wins_so_far",
    "opponent_wins_so_far",
)


def join_series_context(po_df: pd.DataFrame, series_map: pd.DataFrame) -> pd.DataFrame:
    if po_df.empty or series_map.empty:
        return po_df
    out = po_df.copy()
    # Drop prior join artifacts before re-merging (incremental rescrape safety).
    drop_cols = [c for c in out.columns if c in SERIES_CONTEXT_COLS or c.endswith("_series")]
    if drop_cols:
        out = out.drop(columns=drop_cols)
    sm = series_map.copy()
    sm["game_date"] = pd.to_datetime(sm["game_date"])
    out["game_date"] = pd.to_datetime(out["game_date"])
    join_cols = ["season", "team", "opponent", "game_date"]
    return out.merge(
        sm.drop_duplicates(subset=join_cols),
        on=join_cols,
        how="left",
    )


def build_team_name_abbrev_map(client: NBAStatsClient, season: str) -> dict[str, str]:
    """Map full team names to 3-letter abbrevs via leaguegamefinder."""
    records = result_set_to_records(
        client.get_league_game_finder(season, "Regular Season", "T")
    )
    mapping: dict[str, str] = {}
    for row in records:
        name = row.get("TEAM_NAME")
        abbrev = row.get("TEAM_ABBREVIATION")
        if name and abbrev:
            mapping[str(name)] = str(abbrev)
    return mapping


def fetch_opponent_defrtg(client: NBAStatsClient, seasons: list[str]) -> pd.DataFrame:
    name_to_abbrev = build_team_name_abbrev_map(client, seasons[-1])
    frames = []
    for season in tqdm(seasons, desc="Opponent DEF_RATING"):
        resp = client.get_league_team_stats(season, "Regular Season", "Advanced")
        records = result_set_to_records(resp)
        if not records:
            continue
        df = records_to_df(records)
        def_col = "def_rating" if "def_rating" in df.columns else None
        if def_col is None:
            for c in df.columns:
                if "def" in c.lower() and "rating" in c.lower() and "rank" not in c.lower():
                    def_col = c
                    break
        if def_col is None:
            logger.warning("No DEF_RATING column for %s", season)
            continue
        if "team_name" in df.columns:
            df["team_abbrev"] = df["team_name"].map(name_to_abbrev)
        elif "team_abbreviation" in df.columns:
            df["team_abbrev"] = df["team_abbreviation"]
        elif "team" in df.columns:
            df["team_abbrev"] = df["team"]
        else:
            logger.warning("No team column for %s", season)
            continue
        frames.append(df[["team_abbrev", def_col]].assign(season=season).rename(columns={def_col: "def_rating"}))
    if not frames:
        return pd.DataFrame(columns=["season", "team_abbrev", "def_rating"])
    return pd.concat(frames, ignore_index=True)


def join_defrtg(df: pd.DataFrame, defrtg: pd.DataFrame) -> pd.DataFrame:
    if df.empty or defrtg.empty:
        out = df.copy()
        if "opponent_defrtg" not in out.columns:
            out["opponent_defrtg"] = pd.NA
        return out
    out = df.copy()
    if "opponent_defrtg" in out.columns:
        out = out.drop(columns=["opponent_defrtg"])
    # Player advanced logs also carry def_rating; rename opponent side before merge.
    opp = defrtg.rename(
        columns={"team_abbrev": "opponent", "def_rating": "opponent_defrtg"}
    )
    return out.merge(
        opp[["season", "opponent", "opponent_defrtg"]],
        on=["season", "opponent"],
        how="left",
    )


def _normalize_player_name(name: str) -> str:
    """Lowercase ASCII alphanumeric only, for loose name matching.

    Uses NFKD normalization to decompose accented characters (Dončić -> Doncic)
    then strips combining marks so the comparison works across Unicode variants.
    """
    import unicodedata

    decomposed = unicodedata.normalize("NFKD", str(name))
    return "".join(c.lower() for c in decomposed if c.isascii() and c.isalnum())


def verify_player_id(client: NBAStatsClient, name: str, nba_id: int) -> bool:
    resp = client.get_common_player_info(nba_id)
    records = result_set_to_records(resp)
    if not records:
        logger.error("No commonplayerinfo for %s (id=%s)", name, nba_id)
        return False
    api_name = records[0].get("DISPLAY_FIRST_LAST") or records[0].get("PLAYER_NAME", "")
    norm_config = _normalize_player_name(name)
    norm_api = _normalize_player_name(api_name)
    if norm_config != norm_api and norm_config not in norm_api and norm_api not in norm_config:
        logger.error(
            "Player ID mismatch: config %s (id=%s) resolves to API name %s",
            name,
            nba_id,
            api_name,
        )
        return False
    logger.info("Verified %s (id=%s)", name, nba_id)
    return True


def _seasons_in_file(path: Path) -> set[str]:
    if not path.exists():
        return set()
    df = pd.read_csv(path, usecols=["season"])
    return set(df["season"].astype(str).unique())


def _merge_player_logs(existing: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    if existing.empty:
        return new
    if new.empty:
        return existing
    combined = pd.concat([existing, new], ignore_index=True)
    if "game_id" in combined.columns:
        combined = combined.drop_duplicates(subset=["game_id"], keep="last")
    return combined.sort_values("game_date")


def _scrape_player(
    client: NBAStatsClient,
    name: str,
    seasons: list[str],
    series_map: pd.DataFrame,
    defrtg: pd.DataFrame,
    incremental: bool = False,
) -> None:
    meta = config.ALL_PLAYERS[name]
    nba_id = meta["nba_id"]
    slug = config.player_slug(name)
    rs_path = config.RAW_DIR / f"{slug}_rs.csv"
    po_path = config.RAW_DIR / f"{slug}_po.csv"

    if rs_path.exists() and po_path.exists() and not incremental:
        logger.info("Skipping %s (cached)", name)
        return

    if not verify_player_id(client, name, nba_id):
        return

    debut_year = get_player_debut_start_year(client, nba_id)
    player_seasons = seasons_for_player(seasons, debut_year)
    if incremental:
        cached_rs = _seasons_in_file(rs_path)
        cached_po = _seasons_in_file(po_path)
        player_seasons = [
            s for s in player_seasons if s not in cached_rs or s not in cached_po
        ]
        if not player_seasons:
            logger.info("Skipping %s (all seasons cached)", name)
            return

    logger.info(
        "%s: debut %s — fetching %d/%d seasons",
        name,
        config.year_to_season(debut_year),
        len(player_seasons),
        len(seasons),
    )

    rs_frames, po_frames = [], []
    failed: list[str] = []
    for season in tqdm(player_seasons, desc=f"{name} seasons", leave=False):
        if not incremental or season not in _seasons_in_file(rs_path):
            rs = fetch_merged_player_logs_safe(
                client, nba_id, season, "Regular Season"
            )
            if rs is None:
                failed.append(f"{season} RS")
            elif not rs.empty:
                rs["is_playoff"] = False
                rs_frames.append(rs)
        if not incremental or season not in _seasons_in_file(po_path):
            po = fetch_merged_player_logs_safe(client, nba_id, season, "Playoffs")
            if po is None:
                failed.append(f"{season} PO")
            elif not po.empty:
                po["is_playoff"] = True
                po_frames.append(po)

    if failed:
        logger.warning("%s: %d season fetches failed: %s", name, len(failed), failed[:8])

    if rs_frames or (incremental and rs_path.exists()):
        new_rs = enrich_player_logs(pd.concat(rs_frames, ignore_index=True), name) if rs_frames else pd.DataFrame()
        if incremental and rs_path.exists():
            existing_rs = pd.read_csv(rs_path, parse_dates=["game_date"])
            rs_df = _merge_player_logs(existing_rs, new_rs)
        else:
            rs_df = new_rs
        rs_df = join_defrtg(rs_df, defrtg)
        rs_df.to_csv(rs_path, index=False)
        logger.info("%s RS: %d games", name, len(rs_df))

    if po_frames or (incremental and po_path.exists()):
        new_po = enrich_player_logs(pd.concat(po_frames, ignore_index=True), name) if po_frames else pd.DataFrame()
        if incremental and po_path.exists():
            existing_po = pd.read_csv(po_path, parse_dates=["game_date"])
            po_df = _merge_player_logs(existing_po, new_po)
        else:
            po_df = new_po
        po_df = join_series_context(po_df, series_map)
        po_df = join_defrtg(po_df, defrtg)
        po_df.to_csv(po_path, index=False)
        logger.info("%s PO: %d games", name, len(po_df))


def _append_opponent_defrtg(
    client: NBAStatsClient,
    defrtg_path: Path,
    seasons: list[str],
) -> pd.DataFrame:
    existing = pd.read_csv(defrtg_path) if defrtg_path.exists() else pd.DataFrame()
    cached = set(existing["season"].astype(str).unique()) if not existing.empty else set()
    missing = [s for s in seasons if s not in cached]
    if not missing:
        return existing
    new = fetch_opponent_defrtg(client, missing)
    combined = pd.concat([existing, new], ignore_index=True) if not existing.empty else new
    combined = combined.drop_duplicates(subset=["season", "team_abbrev"], keep="last")
    combined.to_csv(defrtg_path, index=False)
    logger.info("Wrote %s (%d rows, +%d seasons)", defrtg_path, len(combined), len(missing))
    return combined


def _append_series_map(
    client: NBAStatsClient,
    series_path: Path,
    seasons: list[str],
) -> pd.DataFrame:
    existing = pd.read_csv(series_path, parse_dates=["game_date"]) if series_path.exists() else pd.DataFrame()
    cached = set(existing["season"].astype(str).unique()) if not existing.empty else set()
    missing = [s for s in seasons if s not in cached]
    if not missing:
        return existing
    new_rows = []
    for season in tqdm(missing, desc="Playoff games (series map)"):
        po = fetch_playoff_games_for_season(client, season)
        if not po.empty:
            new_rows.append(build_team_series_map(po))
    if not new_rows and existing.empty:
        return pd.DataFrame()
    combined = pd.concat([existing] + new_rows, ignore_index=True) if new_rows else existing
    combined = combined.drop_duplicates(
        subset=["season", "team", "opponent", "game_date"], keep="last"
    )
    combined.to_csv(series_path, index=False)
    logger.info("Wrote %s (%d rows, +%d seasons)", series_path, len(combined), len(missing))
    return combined


def scrape_all(
    players: list[str] | None = None,
    seasons: list[str] | None = None,
    skip_series: bool = False,
    rebuild_shared: bool = False,
    incremental: bool = False,
) -> None:
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    client = NBAStatsClient()
    players = players or list(config.ALL_PLAYERS.keys())
    seasons = seasons or config.all_seasons()

    series_path = config.RAW_DIR / "team_series_map.csv"
    if rebuild_shared and series_path.exists():
        series_path.unlink()
    if not skip_series:
        if incremental or not series_path.exists():
            if incremental and series_path.exists():
                series_map = _append_series_map(client, series_path, seasons)
            else:
                all_po = []
                for season in tqdm(seasons, desc="Playoff games (series map)"):
                    po = fetch_playoff_games_for_season(client, season)
                    if not po.empty:
                        all_po.append(po)
                if all_po:
                    combined = pd.concat(all_po, ignore_index=True)
                    series_map = build_team_series_map(combined)
                    series_map.to_csv(series_path, index=False)
                    logger.info("Wrote %s (%d rows)", series_path, len(series_map))
                else:
                    series_map = pd.DataFrame()
        elif series_path.exists():
            series_map = pd.read_csv(series_path, parse_dates=["game_date"])
        else:
            series_map = pd.DataFrame()
    elif series_path.exists():
        series_map = pd.read_csv(series_path, parse_dates=["game_date"])
    else:
        series_map = pd.DataFrame()

    defrtg_path = config.RAW_DIR / "opponent_defrtg.csv"
    if rebuild_shared and defrtg_path.exists():
        defrtg_path.unlink()
    if incremental and defrtg_path.exists():
        defrtg = _append_opponent_defrtg(client, defrtg_path, seasons)
    elif not defrtg_path.exists():
        defrtg = fetch_opponent_defrtg(client, seasons)
        defrtg.to_csv(defrtg_path, index=False)
        logger.info("Wrote %s", defrtg_path)
    else:
        defrtg = pd.read_csv(defrtg_path)

    for i, name in enumerate(tqdm(players, desc="Players")):
        try:
            _scrape_player(client, name, seasons, series_map, defrtg, incremental=incremental)
        except Exception as exc:
            logger.error("FATAL for %s: %s — continuing to next player", name, exc)
            time.sleep(30)
        if (i + 1) % 3 == 0:
            logger.info("Checkpoint after %d players", i + 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape NBA game logs")
    parser.add_argument("--players", nargs="*", help="Subset of player names")
    parser.add_argument("--seasons", nargs="*", help="Subset of seasons e.g. 2023-24")
    parser.add_argument("--series-only", action="store_true", help="Only rebuild series map")
    parser.add_argument("--skip-series", action="store_true")
    parser.add_argument(
        "--rebuild-shared",
        action="store_true",
        help="Rebuild team_series_map.csv and opponent_defrtg.csv",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Fetch only seasons missing from cached CSVs and append shared tables",
    )
    args = parser.parse_args()

    if args.series_only:
        config.RAW_DIR.mkdir(parents=True, exist_ok=True)
        client = NBAStatsClient()
        seasons = args.seasons or config.all_seasons()
        all_po = []
        for season in tqdm(seasons, desc="Playoff games"):
            po = fetch_playoff_games_for_season(client, season)
            if not po.empty:
                all_po.append(po)
        combined = pd.concat(all_po, ignore_index=True)
        build_team_series_map(combined).to_csv(
            config.RAW_DIR / "team_series_map.csv", index=False
        )
        return

    scrape_all(
        args.players,
        args.seasons,
        args.skip_series,
        args.rebuild_shared,
        args.incremental,
    )


if __name__ == "__main__":
    main()
