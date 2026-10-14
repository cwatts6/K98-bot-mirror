"""Immutable membership and source pins for each fighting-window output."""

from dataclasses import asdict, dataclass
import hashlib
import json


@dataclass(frozen=True)
class FightMember:
    period_id: str
    name: str
    order: int
    start_scan: int | None
    end_scan: int | None
    status: str
    publication_id: str | None = None
    selection_version: int | None = None
    calculation_version: str | None = None
    config_id: str | None = None
    roster_id: str | None = None
    revisions: tuple = ()


@dataclass(frozen=True)
class FightCheckpoint:
    period_id: str
    name: str
    members: tuple[FightMember, ...]
    sheet_keys: tuple[str, ...]
    version: str = "fighting_checkpoint_v1"

    @property
    def canonical(self):
        return json.dumps(asdict(self), sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    @property
    def key(self):
        return hashlib.sha256(self.canonical.encode()).hexdigest()
