"""Keep-all fighting preview receipts, independent of production admission and Phase 2H."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
from uuid import uuid4

from filelock import FileLock
import psutil

from stats_alerts import guard
from stats_alerts.diagnostic_sessions import (
    _TOKEN,
    MAX_SESSIONS,
    MAX_STATE_BYTES,
    _contained,
    _read,
    _write,
)
from stats_alerts.dispatch_reservations import DispatchGuarded, DispatchUnavailable, _owner_alive
from utils import utcnow

_PHASES = {"preparing", "sending", "editing", "accepted", "committed", "failed", "unavailable"}
_UNRESOLVED = {"sending", "editing", "accepted"}


def _positive(value):
    return type(value) is int and value > 0


@dataclass
class PreviewSession:
    repository: PreviewRepository
    path: Path
    manifest: dict

    @property
    def token(self):
        return self.manifest["session"]

    def snapshot(self) -> dict:
        """Strict read-only inspection: never acquire/create locks, repair or recover."""
        for name in ("session.json", "publication.json", "session.lck"):
            _contained(self.repository.root, self.path / name)
        if _read(self.path / "session.json") != self.manifest:
            raise DispatchUnavailable("Preview identity changed")
        data = _read(self.path / "publication.json")
        if (
            set(data) != {"version", "message_id", "generation", "operations"}
            or type(data["version"]) is not int
            or data["version"] != 1
            or type(data["generation"]) is not int
            or data["generation"] < 0
            or not isinstance(data["operations"], list)
            or len(data["operations"]) != data["generation"]
            or (data["message_id"] is not None and not _positive(data["message_id"]))
        ):
            raise DispatchUnavailable("Invalid preview publication state")
        committed_id = None
        for generation, row in enumerate(data["operations"], 1):
            if (
                not isinstance(row, dict)
                or row.get("generation") != generation
                or type(row.get("generation")) is not int
                or not isinstance(row.get("token"), str)
                or not _TOKEN.fullmatch(row["token"])
                or row.get("phase") not in _PHASES
                or row.get("mode") not in {"send", "edit"}
                or not isinstance(row.get("digest"), str)
                or len(row["digest"]) not in {0, 64}
            ):
                raise DispatchUnavailable("Invalid preview operation")
            for key in ("started_at", "updated_at"):
                stamp = datetime.fromisoformat(row[key])
                if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
                    raise DispatchUnavailable("Invalid preview UTC timestamp")
            receipt = row.get("receipt")
            if receipt is not None and not _positive(receipt):
                raise DispatchUnavailable("Invalid preview receipt")
            if row["phase"] in {"accepted", "committed"} and receipt is None:
                raise DispatchUnavailable("Missing preview receipt")
            if row["phase"] == "committed":
                if committed_id is not None and receipt != committed_id:
                    raise DispatchUnavailable("Preview identity replacement is forbidden")
                committed_id = receipt
        if committed_id != data["message_id"]:
            raise DispatchUnavailable("Preview receipt/projection mismatch")
        return data

    def _save(self, data):
        if (
            len(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"))
            > MAX_STATE_BYTES - 4096
        ):
            raise DispatchUnavailable("Preview history full; retain evidence")
        _write(self.path / "publication.json", data)

    def _lock(self):
        _contained(self.repository.root, self.path / "session.lck")
        return FileLock(str(self.path / "session.lck"), timeout=5)

    def begin(self, operation: str):
        with self.repository.lock(), self._lock():
            data = self.snapshot()
            lease = self.repository.root / "operation.json"
            if lease.exists():
                previous = _read(lease)
                if previous.get("active") is not False:
                    if previous.get("active") is not True or _owner_alive(previous) is not False:
                        raise DispatchGuarded("Preview operation busy or owner unknown")
            if data["operations"]:
                previous = data["operations"][-1]
                if previous["phase"] in _UNRESOLVED:
                    if previous["phase"] != "accepted":
                        raise DispatchGuarded("Uncertain publication; do not resend")
                    # Positive durable receipt recovery never publishes.
                    previous["phase"] = "committed"
                    data["message_id"] = previous["receipt"]
                elif previous["phase"] == "preparing":
                    previous["phase"] = "failed"
            data["generation"] += 1
            now = utcnow().isoformat()
            data["operations"].append(
                dict(
                    token=operation,
                    generation=data["generation"],
                    phase="preparing",
                    mode="edit" if data["message_id"] else "send",
                    receipt=None,
                    digest="",
                    started_at=now,
                    updated_at=now,
                )
            )
            # Preflight history capacity before taking durable ownership.
            if (
                len(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"))
                > MAX_STATE_BYTES - 8192
            ):
                raise DispatchUnavailable("Preview history full; retain evidence")
            _write(
                lease,
                dict(
                    active=True,
                    operation=operation,
                    session=self.token,
                    owner_pid=os.getpid(),
                    owner_created=psutil.Process().create_time(),
                ),
            )
            self._save(data)

    def transition(self, operation: str, phase: str, *, receipt=None, digest=None):
        with self.repository.lock(), self._lock():
            lease = _read(self.repository.root / "operation.json")
            if (
                lease.get("operation") != operation
                or lease.get("session") != self.token
                or lease.get("active") is not True
            ):
                raise DispatchUnavailable("Preview operation ownership changed")
            data = self.snapshot()
            row = data["operations"][-1]
            allowed = {
                "preparing": {"sending", "editing", "failed", "unavailable"},
                "sending": {"accepted"},
                "editing": {"accepted"},
                "accepted": {"committed"},
            }
            if row["token"] != operation or phase not in allowed.get(row["phase"], set()):
                raise DispatchUnavailable("Invalid preview transition")
            if phase in {"sending", "editing"} and phase != (
                "editing" if data["message_id"] else "sending"
            ):
                raise DispatchUnavailable("Preview publication mode changed")
            if phase == "accepted":
                if not _positive(receipt) or (data["message_id"] and receipt != data["message_id"]):
                    raise DispatchUnavailable("Invalid preview publication receipt")
                row["receipt"] = receipt
            if phase == "committed":
                data["message_id"] = row["receipt"]
            row.update(phase=phase, updated_at=utcnow().isoformat())
            if digest is not None:
                row["digest"] = digest
            self._save(data)

    def finish(self, operation: str):
        with self.repository.lock():
            path = self.repository.root / "operation.json"
            data = _read(path)
            if data.get("operation") != operation or data.get("session") != self.token:
                raise DispatchUnavailable("Preview operation ownership changed")
            data.update(active=False, finished_at=utcnow().isoformat())
            _write(path, data)


class PreviewRepository:
    def __init__(self, root: Path | None = None):
        self.root = (
            root if root is not None else Path(guard.LOG_PATH).parent / "kvk_embed_diagnostics"
        ).absolute()

    def lock(self):
        for name in ("sessions.lck", "operation.json"):
            _contained(self.root, self.root / name)
        return FileLock(str(self.root / "sessions.lck"), timeout=5)

    def open(self, guild_id: int, channel_id: int, owner_id: int, token=None, *, kvk_no=None):
        if not all(_positive(value) for value in (guild_id, channel_id, owner_id)):
            raise ValueError("Invalid preview identity")
        if token is not None and (not isinstance(token, str) or not _TOKEN.fullmatch(token)):
            raise ValueError("Use the issued preview session token")
        if kvk_no is not None and (not _positive(kvk_no) or kvk_no > 2147483647):
            raise ValueError("KVK number must be a positive SQL integer")
        if token is None:
            _contained(self.root, self.root)
            self.root.mkdir(parents=True, exist_ok=True)
            with self.lock():
                if sum(1 for _ in self.root.glob("*/*/*")) >= MAX_SESSIONS:
                    raise DispatchUnavailable("Preview capacity reached; retain evidence")
                token = uuid4().hex
                path = self.root / str(guild_id) / str(channel_id) / token
                _contained(self.root, path)
                path.mkdir(parents=True, exist_ok=False)
                _write(
                    path / "publication.json",
                    dict(version=1, message_id=None, generation=0, operations=[]),
                )
                (path / "session.lck").touch(exist_ok=False)
                _write(
                    path / "session.json",
                    dict(
                        version=2 if kvk_no is not None else 1,
                        kind="fighting_preview",
                        session=token,
                        guild_id=guild_id,
                        channel_id=channel_id,
                        owner_id=owner_id,
                        created_at=utcnow().isoformat(),
                        **({"kvk_no": kvk_no} if kvk_no is not None else {}),
                    ),
                )
        path = self.root / str(guild_id) / str(channel_id) / token
        _contained(self.root, path / "session.json")
        manifest = _read(path / "session.json")
        version = manifest.get("version")
        if type(version) is not int or version not in {1, 2}:
            raise DispatchUnavailable("Unsupported preview session version")
        selected = manifest.get("kvk_no")
        if version == 2:
            if not _positive(selected) or selected > 2147483647:
                raise DispatchUnavailable("Invalid saved KVK selection")
            if kvk_no is not None and kvk_no != selected:
                raise DispatchUnavailable("Session KVK cannot change; use its saved selection")
        elif "kvk_no" in manifest or kvk_no is not None:
            raise DispatchUnavailable(
                "Current-KVK session cannot be retargeted; create a new session"
            )
        expected = dict(
            version=version,
            kind="fighting_preview",
            session=token,
            guild_id=guild_id,
            channel_id=channel_id,
            owner_id=owner_id,
        )
        if any(
            type(manifest.get(k)) is not type(v) or manifest[k] != v for k, v in expected.items()
        ):
            raise DispatchUnavailable("Preview owner/destination mismatch")
        stamp = datetime.fromisoformat(manifest["created_at"])
        if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
            raise DispatchUnavailable("Invalid preview creation time")
        session = PreviewSession(self, path, manifest)
        session.snapshot()
        return session
