from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import logging
from pathlib import Path
from typing import Any

from constants import DATA_DIR
from file_utils import acquire_lock, atomic_write_json, read_json_safe

logger = logging.getLogger(__name__)

TEAM_STATE_SCHEMA_VERSION = 1
DEFAULT_TEAM_STATE_PATH = Path(DATA_DIR) / "ark_team_state.json"


def _utcnow_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_int_list(values: list[Any] | None) -> list[int]:
    out: list[int] = []
    for v in values or []:
        try:
            out.append(int(v))
        except Exception:
            continue
    return out


@dataclass
class ArkTeamAssignment:
    match_id: int
    roster_player_ids: list[int] = field(default_factory=list)
    team1_player_ids: list[int] = field(default_factory=list)
    team2_player_ids: list[int] = field(default_factory=list)
    created_by_discord_id: int | None = None
    updated_by_discord_id: int | None = None
    published_header_message_id: int | None = None
    published_team1_message_id: int | None = None
    published_team2_message_id: int | None = None
    published_at_utc: str | None = None
    status: str = "draft"  # draft|published
    updated_at_utc: str | None = None

    def normalize(self) -> None:
        # Keep only roster IDs in teams, unique, deterministic order by roster order
        roster = [int(x) for x in self.roster_player_ids]
        roster_set = set(roster)

        seen: set[int] = set()
        t1: list[int] = []
        for gid in self.team1_player_ids:
            gid = int(gid)
            if gid in roster_set and gid not in seen:
                t1.append(gid)
                seen.add(gid)

        t2: list[int] = []
        for gid in self.team2_player_ids:
            gid = int(gid)
            if gid in roster_set and gid not in seen:
                t2.append(gid)
                seen.add(gid)

        self.team1_player_ids = t1
        self.team2_player_ids = t2
        self.roster_player_ids = roster
        self.status = "published" if self.status == "published" else "draft"

    def unassigned_player_ids(self) -> list[int]:
        assigned = set(self.team1_player_ids) | set(self.team2_player_ids)
        return [gid for gid in self.roster_player_ids if gid not in assigned]


@dataclass
class ArkTeamStateStore:
    path: Path = field(default_factory=lambda: DEFAULT_TEAM_STATE_PATH)
    schema_version: int = TEAM_STATE_SCHEMA_VERSION
    assignments: dict[int, ArkTeamAssignment] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None = None) -> ArkTeamStateStore:
        resolved = path or DEFAULT_TEAM_STATE_PATH
        data = read_json_safe(str(resolved), default={}) or {}
        raw_assignments = (data or {}).get("assignments") or {}
        store = cls(path=resolved, schema_version=int((data or {}).get("schema_version") or 1))

        for match_id_str, payload in raw_assignments.items():
            try:
                match_id = int(match_id_str)
            except Exception:
                continue
            try:
                a = ArkTeamAssignment(
                    match_id=match_id,
                    roster_player_ids=_safe_int_list(payload.get("roster_player_ids")),
                    team1_player_ids=_safe_int_list(payload.get("team1_player_ids")),
                    team2_player_ids=_safe_int_list(payload.get("team2_player_ids")),
                    created_by_discord_id=payload.get("created_by_discord_id"),
                    updated_by_discord_id=payload.get("updated_by_discord_id"),
                    published_header_message_id=payload.get("published_header_message_id"),
                    published_team1_message_id=payload.get("published_team1_message_id"),
                    published_team2_message_id=payload.get("published_team2_message_id"),
                    published_at_utc=payload.get("published_at_utc"),
                    status=str(payload.get("status") or "draft"),
                    updated_at_utc=payload.get("updated_at_utc"),
                )
                a.normalize()
                store.assignments[match_id] = a
            except Exception:
                logger.exception(
                    "[ARK_TEAM_STATE] failed to parse assignment match_id=%s", match_id
                )

        return store

    def save(self) -> None:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "assignments": {
                str(mid): asdict(assignment) for mid, assignment in (self.assignments or {}).items()
            },
        }
        lock_path = str(self.path) + ".lock"
        with acquire_lock(lock_path, timeout=5.0):
            atomic_write_json(str(self.path), payload, ensure_parent_dir=True)

    def get_or_create(
        self,
        *,
        match_id: int,
        roster_player_ids: list[int],
        actor_discord_id: int | None,
    ) -> ArkTeamAssignment:
        existing = self.assignments.get(int(match_id))
        if existing:
            existing.roster_player_ids = [int(x) for x in roster_player_ids]
            existing.updated_by_discord_id = actor_discord_id
            existing.updated_at_utc = _utcnow_iso()
            existing.normalize()
            return existing

        created = ArkTeamAssignment(
            match_id=int(match_id),
            roster_player_ids=[int(x) for x in roster_player_ids],
            created_by_discord_id=actor_discord_id,
            updated_by_discord_id=actor_discord_id,
            updated_at_utc=_utcnow_iso(),
            status="draft",
        )
        created.normalize()
        self.assignments[int(match_id)] = created
        return created

    def reset(self, *, match_id: int, actor_discord_id: int | None) -> ArkTeamAssignment | None:
        a = self.assignments.get(int(match_id))
        if not a:
            return None
        a.team1_player_ids = []
        a.team2_player_ids = []
        a.status = "draft"
        a.updated_by_discord_id = actor_discord_id
        a.updated_at_utc = _utcnow_iso()
        return a
