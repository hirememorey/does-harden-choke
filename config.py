"""Player lists, season range, and analysis parameters."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_PBP_DIR = RAW_DIR / "pbp"
PROCESSED_DIR = DATA_DIR / "processed"
PROCESSED_PASS2_DIR = PROCESSED_DIR / "pass2"
CACHE_DIR = DATA_DIR / "cache"
# Tracked fixture (not under raw/ or processed/); see .gitignore negation
PASS2_VALIDATION_GAMES = DATA_DIR / "pass2_validation_games.json"
OUTPUT_DIR = PROJECT_ROOT / "output"
FIGURES_DIR = OUTPUT_DIR / "figures"

# Group A — Heliocentric creators (high usage, high self-creation, foul-dependent)
GROUP_A = {
    "James Harden": {"nba_id": 201935, "bbref_id": "hardeja01"},
    "Russell Westbrook": {"nba_id": 201566, "bbref_id": "westbru01"},
    "Luka Doncic": {"nba_id": 1629029, "bbref_id": "doncilu01"},
    "Trae Young": {"nba_id": 1629027, "bbref_id": "younga01"},
    "Allen Iverson": {"nba_id": 947, "bbref_id": "iversal01"},
    "Damian Lillard": {"nba_id": 203081, "bbref_id": "lillada01"},
    # Expansion — shrinker candidates + heliocentric contrast cases
    "DeMar DeRozan": {"nba_id": 201942, "bbref_id": "derozde01"},
    "John Wall": {"nba_id": 202322, "bbref_id": "walljo01"},
    "Chris Paul": {"nba_id": 101108, "bbref_id": "paulch01"},
    "LeBron James": {"nba_id": 2544, "bbref_id": "jamesle01"},
    # FTA-dependent contractor contrast (scheme-dependent vs Harden/PG)
    "Shai Gilgeous-Alexander": {"nba_id": 1628983, "bbref_id": "gilgesh01"},
    # Playoff riser contrast — perceived elite playoff performer; situational contractor
    "Jimmy Butler": {"nba_id": 202710, "bbref_id": "butleji01"},
    # Expansion — big/off-ball heliocentric engines + playmaking creators
    "Joel Embiid": {"nba_id": 203954, "bbref_id": "embiijo01"},
    "Ben Simmons": {"nba_id": 1627732, "bbref_id": "simmobe01"},
    "Jalen Brunson": {"nba_id": 1628973, "bbref_id": "brunsja01"},
    "Tyrese Haliburton": {"nba_id": 1630169, "bbref_id": "halibty01"},
    "Giannis Antetokounmpo": {"nba_id": 203507, "bbref_id": "antigia01"},
    "Nikola Jokic": {"nba_id": 203999, "bbref_id": "jokicni01"},
    # "Choker" to champion — testing whether narrative flip reflects trigger change or system change
    "Dirk Nowitzki": {"nba_id": 1717, "bbref_id": "nowitdi01"},
    # Speed-dependent heliocentric creator — rim pressure + playmaking guard
    "De'Aaron Fox": {"nba_id": 1628368, "bbref_id": "foxde01"},
}

# Group B — Scalable stars (lower self-creation burden, more off-ball)
GROUP_B = {
    "Stephen Curry": {"nba_id": 201939, "bbref_id": "curryst01"},
    "Klay Thompson": {"nba_id": 202691, "bbref_id": "thompkl01"},
    "Ray Allen": {"nba_id": 951, "bbref_id": "allenra02"},
    "Richard Hamilton": {"nba_id": 1888, "bbref_id": "hamilri01"},
    "Kevin Durant": {"nba_id": 201142, "bbref_id": "duranke01"},
    # Expansion — forcer archetypes + scalable wing shrinker candidate
    "Kobe Bryant": {"nba_id": 977, "bbref_id": "bryanko01"},
    "Paul George": {"nba_id": 202331, "bbref_id": "georgpa01"},
    # Expansion — scalable wing creator
    "Jayson Tatum": {"nba_id": 1628369, "bbref_id": "tatumja01"},
    # Secondary scorer — scheme-dependent floor hypothesis
    "Tobias Harris": {"nba_id": 202699, "bbref_id": "harrito02"},
    # Clutch god narrative vs. data — most polarizing playoff guard of his generation
    "Kyrie Irving": {"nba_id": 202681, "bbref_id": "irvinky01"},
    # Bimodal riser/shrinker hypothesis — spectacular peaks and invisible valleys
    "Donovan Mitchell": {"nba_id": 1628378, "bbref_id": "mitchdo01"},
}

ALL_PLAYERS = {**GROUP_A, **GROUP_B}

PLAYER_GROUP = {name: "A" for name in GROUP_A}
PLAYER_GROUP.update({name: "B" for name in GROUP_B})

# Analysis parameters
FLOOR_GAME_PERCENTILE = 15
FLOOR_GAME_SD_CUTOFF = 1.5
MIN_RS_GAMES = 50
SEASON_START_YEARS = list(range(1996, 2026))  # 1996-97 through 2025-26
SERIES_GAP_DAYS = 7

# Color scheme
GROUP_A_COLOR = "#d62728"
GROUP_B_COLOR = "#1f77b4"
RS_COLOR = "#7f7f7f"


def year_to_season(start_year: int) -> str:
    """Convert start year (e.g. 2023) to NBA season string (e.g. 2023-24)."""
    return f"{start_year}-{(start_year + 1) % 100:02d}"


def season_to_year(season: str) -> int:
    """Convert season string (e.g. 2023-24) to start year."""
    return int(season.split("-")[0])


def player_slug(name: str) -> str:
    return name.lower().replace(" ", "_").replace("'", "")


def all_seasons() -> list[str]:
    return [year_to_season(y) for y in SEASON_START_YEARS]
