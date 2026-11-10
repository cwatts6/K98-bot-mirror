"""Single-host durable notification evidence; never owns SQL or provider work."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time
from uuid import UUID

from filelock import FileLock

from file_utils import atomic_json_write


class NotificationHeld(RuntimeError):
    """Evidence does not authorize another Discord operation."""


def run_identity(value):
    return str(UUID(str(value)))


class NotificationStore:
    def __init__(self, path):
        self.path = Path(path)

    def _read(self):
        if not self.path.exists():
            return {"schema": 1, "runs": {}}
        if self.path.stat().st_size > 4 * 1024 * 1024:
            raise NotificationHeld(
                "Notification journal exceeds its size limit; retain and inspect it."
            )
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if (
            not isinstance(data, dict)
            or data.get("schema") != 1
            or not isinstance(data.get("runs"), dict)
        ):
            raise NotificationHeld(
                "Notification journal is invalid; retain and restore verified evidence."
            )
        return data

    def _locked(self, change):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(str(self.path) + ".lck", timeout=5):
            data = self._read()
            result = change(data)
            atomic_json_write(str(self.path), data)
            return deepcopy(result)

    def all(self):
        with FileLock(str(self.path) + ".lck", timeout=5):
            return deepcopy(list(self._read()["runs"].values()))

    def get(self, run_id):
        key = run_identity(run_id)
        with FileLock(str(self.path) + ".lck", timeout=5):
            return deepcopy(self._read()["runs"][key])

    def create(self, run_id, **context):
        key = run_identity(run_id)

        def change(data):
            if key in data["runs"]:
                raise NotificationHeld("Run identity already registered.")
            finished = sorted(
                (r for r in data["runs"].values() if r.get("closed")),
                key=lambda r: r["created"],
            )
            for row in finished[:-127]:
                del data["runs"][row["run_id"]]
            if len(data["runs"]) >= 256:
                raise NotificationHeld(
                    "Journal is full; inspect unresolved runs before accepting more notifications."
                )
            row = dict(
                context,
                run_id=key,
                created=time.time(),
                version=1,
                stats="pending",
                sheets="pending",
                components={},
                stats_tries=0,
            )
            data["runs"][key] = row
            return row

        return self._locked(change)

    def update(self, run_id, change):
        key = run_identity(run_id)

        def mutate(data):
            row = data["runs"][key]
            change(row)
            row["version"] += 1
            return row

        return self._locked(mutate)

    def patch(self, run_id, **changes):
        def change(row):
            patch = dict(changes)
            if row.get("sheets") in {"confirmed", "failed", "cancelled"}:
                # A late pipeline handoff cannot replace authoritative job evidence.
                patch.pop("sheets", None)
                if patch.get("handoff"):
                    patch.pop("completed_at", None)
                    patch.pop("duration_seconds", None)
            if (
                row.get("sheets") == "uncertain"
                and patch.get("sheets") == "uncertain"
                and patch.get("handoff")
                and row.get("completed_at") is not None
            ):
                # Preserve first observation timing, while still allowing later
                # authoritative confirmation/failure to advance an uncertain job.
                patch.pop("completed_at", None)
                patch.pop("duration_seconds", None)
            if row.get("sheets") in {"confirmed", "failed", "uncertain", "cancelled"} and patch.get(
                "sheets"
            ) in {"pending", "waiting", "ready", "running"}:
                patch.pop("sheets")
            row.update(patch)

        return self.update(run_id, change)

    def enter(
        self, run_id, component, *, channel_id, operation="send", message_id=None, route=None
    ):
        def change(row):
            if row.get("closed"):
                raise NotificationHeld("Administrator closed this notification watch.")
            existing = row["components"].get(component, {})
            if existing.get("state") in {"sending", "acknowledged", "held", "skipped"}:
                raise NotificationHeld(
                    "Component already sent, skipped or ambiguous; no automatic resend."
                )
            if route and row.get("stats_route", route) != route:
                raise NotificationHeld(
                    "Stats routing changed; inspect this run instead of publishing stale data."
                )
            if route:
                row["stats_route"] = route
            row["components"][component] = dict(
                state="sending",
                channel_id=channel_id,
                operation=operation,
                message_id=message_id,
                entered=time.time(),
            )

        return self.update(run_id, change)

    def acknowledge(self, run_id, component, *, message_id, channel_id):
        def change(row):
            item = row["components"][component]
            if item["state"] != "sending" or item["channel_id"] != channel_id:
                raise NotificationHeld("Discord receipt differs from the registered destination.")
            if type(message_id) is not int or message_id <= 0:
                raise NotificationHeld("Discord returned no exact message receipt.")
            item.update(state="acknowledged", message_id=message_id, acknowledged=time.time())

        return self.update(run_id, change)

    @staticmethod
    def token(row):
        return hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()

    def resolve(self, run_id, *, action, token, reason, actor, component=None, channel_id=None):
        if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 512:
            raise ValueError("An audit reason of 1–512 characters is required.")
        if not isinstance(actor, str) or not 1 <= len(actor) <= 128:
            raise ValueError("A bounded local administrator identity is required.")

        def change(row):
            if self.token(row) != token:
                raise NotificationHeld("Run changed since preview; inspect and preview again.")
            if action == "close":
                # Administrative acknowledgment ends only this notification watch.
                # A crash before export correlation may leave no terminal fact;
                # do not invent one or force an application replay to close it.
                row["closed"] = True
            else:
                item = row["components"].get(component)
                if not item:
                    raise NotificationHeld("Exact recorded notification component required.")
                if action == "retry":
                    if item["state"] != "failed" or not component.startswith(
                        ("sheets_", "summary_")
                    ):
                        raise NotificationHeld(
                            "Only a proven unsent status notification can retry; ambiguous sends cannot."
                        )
                    if channel_id is not None:
                        if type(channel_id) is not int or channel_id <= 0:
                            raise ValueError("A positive destination channel ID is required.")
                        if not component.startswith("sheets_"):
                            raise NotificationHeld(
                                "Only the unsent Sheets destination can be corrected here."
                            )
                        row["sheets_channel_id"] = channel_id
                    item.update(state="failed", tries=0)
                elif action == "dismiss":
                    if item["state"] not in {"sending", "held", "failed"}:
                        raise NotificationHeld("Only an unresolved notification can be dismissed.")
                    item.update(state="skipped", reason="admin_dismissed")
                else:
                    raise ValueError("Unsupported resolution action.")
                row["closed"] = False
            row["last_admin_resolution"] = dict(
                action=action,
                component=component,
                actor=actor,
                reason=reason.strip(),
                at=time.time(),
            )

        return self.update(run_id, change)


def notification_store():
    from constants import DATA_DIR

    return NotificationStore(Path(DATA_DIR) / "processing_outcomes.json")
