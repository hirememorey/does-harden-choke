"""Shared helpers for parsing NBA playbyplayv3 actions."""

from __future__ import annotations

import re
from typing import Any, Iterable

ISO_CLOCK_RE = re.compile(
    r"^PT(?:(?P<minutes>\d+)M)?(?P<seconds>\d+(?:\.\d+)?)S$"
)
ASSIST_RE = re.compile(r"\((?P<name>[^()]+?)\s+\d+\s+AST\)")
SUB_RE = re.compile(
    r"SUB:\s*(?P<in_player>.+?)\s+FOR\s+(?P<out_player>.+?)$",
    re.IGNORECASE,
)
TIP_RE = re.compile(r"Tip to\s+(.+)$", re.IGNORECASE)


def iso_clock_to_seconds(clock: str | None) -> int:
    """Convert ISO 8601 duration clock (PT11M38.00S) to seconds remaining."""
    if not clock:
        return 0
    match = ISO_CLOCK_RE.match(clock)
    if not match:
        return 0
    minutes = int(match.group("minutes") or 0)
    seconds = float(match.group("seconds"))
    return int(round(minutes * 60 + seconds))


def seconds_to_clock(seconds: int) -> str:
    seconds = max(0, int(seconds))
    minutes, secs = divmod(seconds, 60)
    return f"{minutes}:{secs:02d}"


def sort_actions(actions: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Chronological order within a game."""

    def key(action: dict[str, Any]) -> tuple:
        action_type = action.get("actionType") or ""
        # Process primary events before empty companion rows (steal/block).
        primary_rank = 1 if action_type else 0
        return (
            int(action.get("period") or 0),
            -iso_clock_to_seconds(action.get("clock")),
            int(action.get("actionNumber") or 0),
            primary_rank,
        )

    return sorted(actions, key=key)


def is_scoring_action(action: dict[str, Any]) -> bool:
    action_type = action.get("actionType") or ""
    if action_type == "Made Shot":
        return True
    if action_type == "Free Throw" and "PTS" in (action.get("description") or ""):
        return True
    return False


def parse_score_from_action(action: dict[str, Any]) -> tuple[int, int] | None:
    home = action.get("scoreHome")
    away = action.get("scoreAway")
    if home in ("", None) or away in ("", None):
        return None
    try:
        return int(home), int(away)
    except (TypeError, ValueError):
        return None


def parse_assist_player_id(
    description: str,
    name_to_id: dict[str, int],
) -> int | None:
    match = ASSIST_RE.search(description or "")
    if not match:
        return None
    raw = match.group("name").strip()
    # Descriptions use last names or abbreviated names.
    for name, player_id in name_to_id.items():
        if raw.lower() in name.lower() or name.lower().startswith(raw.lower()):
            return player_id
    return None


def parse_substitution(description: str) -> tuple[str, str] | None:
    match = SUB_RE.search(description or "")
    if not match:
        return None
    return match.group("in_player").strip(), match.group("out_player").strip()


def parse_tip_recipient(description: str) -> str | None:
    match = TIP_RE.search(description or "")
    if not match:
        return None
    return match.group(1).strip()


def rebound_is_offensive(description: str) -> bool | None:
    match = re.search(r"Off:(\d+)\s+Def:(\d+)", description or "")
    if not match:
        return None
    off, def_ = int(match.group(1)), int(match.group(2))
    if off > def_:
        return True
    if def_ > off:
        return False
    return None


def is_last_free_throw(sub_type: str | None) -> bool:
    sub = (sub_type or "").lower().replace("free throw", "").strip()
    if " of " not in sub:
        return False
    num, den = [part.strip() for part in sub.split(" of ", 1)]
    return num == den


def has_immediate_free_throw(
    actions: list[dict[str, Any]],
    index: int,
    *,
    shooter_id: int,
    team_tricode: str,
) -> bool:
    """Detect and-1 / shooting-foul sequences where FTs follow immediately."""
    for action in actions[index + 1 : index + 6]:
        action_type = action.get("actionType") or ""
        if action_type == "Free Throw":
            return (
                action.get("teamTricode") == team_tricode
                and int(action.get("personId") or 0) == shooter_id
            )
        if action_type in ("Made Shot", "Missed Shot", "Turnover", "Rebound", "Jump Ball"):
            return False
    return False


def has_upcoming_free_throw(
    actions: list[dict[str, Any]],
    index: int,
    *,
    team_tricode: str | None = None,
) -> bool:
    for action in actions[index + 1 : index + 6]:
        action_type = action.get("actionType") or ""
        if action_type == "Free Throw":
            if team_tricode is None:
                return True
            return action.get("teamTricode") == team_tricode
        if action_type in ("Made Shot", "Missed Shot", "Turnover", "Rebound", "Jump Ball"):
            return False
    return False


def shot_zone(action: dict[str, Any]) -> str | None:
    distance = action.get("shotDistance")
    sub_type = (action.get("subType") or "").lower()
    description = (action.get("description") or "").lower()
    if "3pt" in description or "3-pt" in description:
        return "3pt"
    if distance is None:
        return None
    try:
        dist = float(distance)
    except (TypeError, ValueError):
        return None
    if dist <= 4:
        return "rim"
    if dist >= 22:
        return "3pt"
    return "midrange"


def resolve_team_tricode(
    action: dict[str, Any],
    team_tricodes: dict[int, str],
    *,
    home_tricode: str,
    away_tricode: str,
) -> str:
    tricode = action.get("teamTricode") or ""
    if tricode:
        return tricode
    team_id = int(action.get("teamId") or 0)
    if team_id in team_tricodes:
        return team_tricodes[team_id]
    person_id = int(action.get("personId") or 0)
    if person_id in team_tricodes:
        return team_tricodes[person_id]
    location = action.get("location") or ""
    if location == "h":
        return home_tricode
    if location == "v":
        return away_tricode
    return ""


def team_margin_for_offense(
    home_score: int,
    away_score: int,
    offense_is_home: bool,
) -> int:
    if offense_is_home:
        return home_score - away_score
    return away_score - home_score
