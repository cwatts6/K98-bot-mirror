"""Bounded, keep-all diagnostic sessions. No Discord or production-state writes."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from uuid import uuid4

from filelock import FileLock
import psutil

from file_utils import atomic_json_write, atomic_write_csv
from stats_alerts import guard
from stats_alerts.dispatch_reservations import DispatchUnavailable, ReservationStore, _owner_alive
from stats_alerts.state import MessageStateStore
from utils import utcnow

MAX_SESSIONS = 20
MAX_STATE_BYTES = 1_048_576
_TOKEN = re.compile(r"[0-9a-f]{32}\Z")


def _read(path: Path) -> dict:
    if path.stat().st_size > MAX_STATE_BYTES:
        raise DispatchUnavailable("Diagnostic state exceeds its limit; preserve for recovery")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise DispatchUnavailable("Invalid diagnostic state")
    return data


def _write(path: Path, data: dict) -> None:
    atomic_json_write(str(path), data, ensure_ascii=False, sort_keys=True, default=None)


def _contained(root: Path, path: Path) -> None:
    """Reject symlinks/junctions as well as lexical escapes in the trusted namespace."""
    if not path.is_relative_to(root):
        raise DispatchUnavailable("Invalid diagnostic path")
    for part in (root, *path.relative_to(root).parents, path):
        candidate = part if part.is_absolute() else root / part
        if candidate.is_symlink() or (candidate.exists() and candidate.resolve() != candidate):
            raise DispatchUnavailable("Redirected diagnostic path is not allowed")


@dataclass
class DiagnosticSession:
    repository: SessionRepository
    path: Path
    manifest: dict
    store: ReservationStore

    @property
    def token(self) -> str:
        return self.manifest["session"]

    def validate(self) -> None:
        root = self.repository.root
        _contained(root, self.path)
        for name in (
            "session.json",
            "alerts.csv",
            "alerts.csv.dispatch.json",
            "message.json",
            "alerts.csv.dispatch.lck",
            "message.json.lck",
        ):
            _contained(root, self.path / name)
            if not name.endswith(".lck") and not (self.path / name).is_file():
                raise DispatchUnavailable("Incomplete diagnostic session; preserve for recovery")
            if not name.endswith(".lck") and (self.path / name).stat().st_size > MAX_STATE_BYTES:
                raise DispatchUnavailable(
                    "Diagnostic state exceeds its limit; preserve for recovery"
                )
        current = _read(self.path / "session.json")
        if current != self.manifest:
            raise DispatchUnavailable("Diagnostic session identity changed")
        self.store.message_state.load_state()
        journal = self.store._read()
        if any(
            row["channel_id"] != self.manifest["channel_id"] or row["kind"] != "prekvk_daily"
            for row in journal["attempts"].values()
        ):
            raise DispatchUnavailable("Diagnostic journal destination/kind mismatch")
        # Unlike the legacy reader, diagnostics must not migrate malformed CSV to empty.
        import csv

        csv_path = self.path / "alerts.csv"
        if csv_path.stat().st_size > MAX_STATE_BYTES:
            raise DispatchUnavailable("Diagnostic CSV exceeds its limit")
        with csv_path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.reader(stream))
        if not rows or rows[0] != guard.HEADER:
            raise DispatchUnavailable("Invalid diagnostic CSV")
        from datetime import date, time

        for row in rows[1:]:
            if len(row) != 3 or row[2] != "prekvk_daily":
                raise DispatchUnavailable("Invalid diagnostic success row")
            date.fromisoformat(row[0])
            time.fromisoformat(row[1])

    def begin(self) -> str:
        """Durable root-wide admission. No filesystem lock survives this call."""
        with self.repository.lock():
            self.validate()
            if self.store.path.stat().st_size > MAX_STATE_BYTES:
                raise DispatchUnavailable("Diagnostic journal is full")
            lease_path = self.repository.root / "operation.json"
            if lease_path.exists():
                previous = _read(lease_path)
                if previous.get("active") is not False:
                    if previous.get("active") is not True or _owner_alive(previous) is not False:
                        raise DispatchUnavailable("Diagnostic operation busy or owner unknown")
            operation = uuid4().hex
            _write(
                lease_path,
                {
                    "active": True,
                    "operation": operation,
                    "session": self.token,
                    "owner_pid": os.getpid(),
                    "owner_created": psutil.Process().create_time(),
                    "started_at": utcnow().isoformat(),
                },
            )
            return operation

    def finish(self, operation: str) -> None:
        with self.repository.lock():
            path = self.repository.root / "operation.json"
            data = _read(path)
            if data.get("operation") != operation or data.get("session") != self.token:
                raise DispatchUnavailable("Diagnostic operation owner mismatch")
            data.update(active=False, finished_at=utcnow().isoformat())
            _write(path, data)

    def snapshot(self) -> dict:
        """Read-only observation: never reserve, repair, recover, migrate or create locks."""
        self.validate()
        paths = [
            self.path / name for name in ("alerts.csv.dispatch.json", "alerts.csv", "message.json")
        ]
        before = [path.read_bytes() for path in paths]
        data = self.store._read()
        reference = self.store.message_state.load_state().get("prekvk_msg_id")
        after = [path.read_bytes() for path in paths]
        if before != after:
            raise DispatchUnavailable("Diagnostic state changed during observation; inspect again")
        import csv
        import io

        rows = list(csv.reader(io.StringIO(after[1].decode("utf-8"))))[1:]
        attempts = list(data["attempts"].values())
        latest = max(attempts, key=lambda row: row["reserved_at"], default=None)
        pending = any(row["phase"] not in {"committed", "released"} for row in attempts)
        day = utcnow().date().isoformat()
        guarded = (
            pending
            or any(row[0] == day for row in rows)
            or any(
                row["phase"] == "committed" and row["accepted_at"][:10] == day for row in attempts
            )
        )
        return {
            "session": self.token,
            "guild_id": self.manifest["guild_id"],
            "channel_id": self.manifest["channel_id"],
            "message_id": reference,
            "attempt": latest,
            "rows": rows,
            "guarded": guarded,
            "generation": data["message_generation"],
            "pending": pending,
        }


class SessionRepository:
    def __init__(self, root: Path | None = None):
        # Root injection is internal/test-only; command inputs never select paths.
        self.root = (
            root
            if root is not None
            else Path(guard.LOG_PATH).parent / "prekvk_dispatch_diagnostics"
        ).absolute()

    def lock(self) -> FileLock:
        _contained(self.root, self.root / "sessions.lck")
        _contained(self.root, self.root / "operation.json")
        return FileLock(str(self.root / "sessions.lck"), timeout=5)

    def open(
        self, guild_id: int, channel_id: int, owner_id: int, token: str | None = None
    ) -> DiagnosticSession:
        if any(type(value) is not int or value <= 0 for value in (guild_id, channel_id, owner_id)):
            raise ValueError("Invalid diagnostic identity")
        if token is not None and not _TOKEN.fullmatch(token):
            raise ValueError("Session must be the issued 32-character token")
        if token is not None:
            return self._open_existing(guild_id, channel_id, owner_id, token)
        _contained(self.root, self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        with self.lock():
            # Count incomplete sessions too: corruption never grants another allocation.
            if sum(1 for _ in self.root.glob("*/*/*")) >= MAX_SESSIONS:
                raise DispatchUnavailable("Diagnostic session capacity reached; retain evidence")
            token = uuid4().hex
            path = self.root / str(guild_id) / str(channel_id) / token
            _contained(self.root, path)
            path.mkdir(parents=True, exist_ok=False)
            atomic_write_csv(str(path / "alerts.csv"), guard.HEADER, [])
            _write(path / "message.json", {})
            _write(
                path / "alerts.csv.dispatch.json",
                {"version": 1, "message_generation": 0, "attempts": {}},
            )
            for name in ("alerts.csv.dispatch.lck", "message.json.lck"):
                (path / name).touch(exist_ok=False)
            _write(
                path / "session.json",
                {
                    "version": 1,
                    "session": token,
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "owner_id": owner_id,
                    "created_at": utcnow().isoformat(),
                },
            )
        return self._open_existing(guild_id, channel_id, owner_id, token)

    def _open_existing(
        self, guild_id: int, channel_id: int, owner_id: int, token: str
    ) -> DiagnosticSession:
        path = self.root / str(guild_id) / str(channel_id) / token
        _contained(self.root, path / "session.json")
        manifest = _read(path / "session.json")
        expected = {
            "version": 1,
            "session": token,
            "guild_id": guild_id,
            "channel_id": channel_id,
            "owner_id": owner_id,
        }
        if any(
            type(manifest.get(k)) is not type(v) or manifest[k] != v for k, v in expected.items()
        ):
            raise DispatchUnavailable("Diagnostic session owner/destination mismatch")
        from datetime import datetime

        created = datetime.fromisoformat(manifest["created_at"])
        if created.utcoffset() is None or created.utcoffset().total_seconds() != 0:
            raise DispatchUnavailable("Invalid diagnostic creation time")
        store = ReservationStore(
            str(path / "alerts.csv"), message_state=MessageStateStore(path / "message.json")
        )
        session = DiagnosticSession(self, path, manifest, store)
        session.validate()
        return session
