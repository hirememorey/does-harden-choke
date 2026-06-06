"""On-court lineup reconstruction from substitutions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.pass2.pbp_utils import parse_substitution


@dataclass
class LineupTracker:
    team_tricodes: dict[int, str]
    home_team_id: int
    away_team_id: int
    home_tricode: str
    away_tricode: str
    on_court: dict[str, set[int]] = field(default_factory=dict)
    player_names: dict[int, str] = field(default_factory=dict)
    last_name_index: dict[str, set[int]] = field(default_factory=dict)

    @classmethod
    def from_starters(
        cls,
        starters_by_team: dict[str, list[int]],
        team_tricodes: dict[int, str],
        home_team_id: int,
        player_names: dict[int, str] | None = None,
    ) -> "LineupTracker":
        home_tricode = team_tricodes[home_team_id]
        away_team_id = next(tid for tid, tri in team_tricodes.items() if tid != home_team_id)
        away_tricode = team_tricodes[away_team_id]
        tracker = cls(
            team_tricodes=team_tricodes,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            home_tricode=home_tricode,
            away_tricode=away_tricode,
            on_court={
                home_tricode: set(starters_by_team.get(home_tricode, [])),
                away_tricode: set(starters_by_team.get(away_tricode, [])),
            },
            player_names=dict(player_names or {}),
        )
        tracker._rebuild_name_index()
        return tracker

    def _rebuild_name_index(self) -> None:
        self.last_name_index.clear()
        for player_id, name in self.player_names.items():
            token = name.split()[-1].lower()
            self.last_name_index.setdefault(token, set()).add(player_id)

    def register_player_name(self, player_id: int, name: str) -> None:
        if not player_id or not name:
            return
        self.player_names[player_id] = name
        token = name.split()[-1].lower()
        self.last_name_index.setdefault(token, set()).add(player_id)

    def resolve_player_id(self, label: str, team_tricode: str) -> int | None:
        label = label.strip()
        if not label:
            return None
        on_court = self.on_court.get(team_tricode, set())
        if not on_court:
            return None

        candidates = {
            pid
            for pid in on_court
            if label.lower() in self.player_names.get(pid, "").lower()
        }
        if len(candidates) == 1:
            return next(iter(candidates))

        token = label.split()[-1].lower()
        overlap = self.last_name_index.get(token, set()) & on_court
        if len(overlap) == 1:
            return next(iter(overlap))

        if "." in label:
            initials, last = label.split(".", 1)
            last = last.strip().lower()
            dotted = {
                pid
                for pid in on_court
                if self.player_names.get(pid, "").split()[-1].lower() == last
                and self.player_names.get(pid, "").lower().startswith(initials.lower())
            }
            if len(dotted) == 1:
                return next(iter(dotted))

        return None

    def apply_substitution(self, action: dict[str, Any]) -> None:
        parsed = parse_substitution(action.get("description") or "")
        if not parsed:
            return
        in_label, out_label = parsed
        team = action.get("teamTricode") or ""
        if not team:
            return
        in_id = self.resolve_player_id(in_label, team)
        out_id = self.resolve_player_id(out_label, team)
        lineup = self.on_court.setdefault(team, set())
        if out_id:
            lineup.discard(out_id)
        if in_id:
            lineup.add(in_id)
        if action.get("personId"):
            self.register_player_name(int(action["personId"]), action.get("playerName") or "")

    def players_on_court(self) -> list[int]:
        return sorted(self.on_court.get(self.home_tricode, set()) | self.on_court.get(self.away_tricode, set()))

    def offense_is_home(self, offense_tricode: str) -> bool:
        return offense_tricode == self.home_tricode
