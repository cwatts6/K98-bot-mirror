"""Local event-delivery receipts. Existing SQL/export authority is unrelated.

An entered operation is never retried implicitly, even after restart. This is an
evidence journal, not a queue. Unknown and acknowledged receipts are not aged out.
"""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import time

from filelock import FileLock

from file_utils import atomic_json_write

MAX_JOURNAL_BYTES = 8 * 1024 * 1024
SETTLEMENT_RESERVE_BYTES = 256


class DeliveryHeld(RuntimeError):
    """Retained evidence does not authorize dispatch."""


def delivery_key(*parts):
    return hashlib.sha256(json.dumps(parts, separators=(",", ":")).encode()).hexdigest()


class EventDeliveryStore:
    def __init__(self, path):
        self.path = Path(path)

    def _read(self):
        if not self.path.exists():
            return {"schema": 1, "operations": {}}
        if self.path.stat().st_size > MAX_JOURNAL_BYTES:
            raise DeliveryHeld("Event delivery journal is full; retain and inspect evidence.")
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema") != 1:
            raise DeliveryHeld("Invalid event delivery journal.")
        rows = data.get("operations")
        if not isinstance(rows, dict) or any(
            not isinstance(row, dict)
            or row.get("state") not in {"entered", "acknowledged", "not_found", "refused"}
            for row in rows.values()
        ):
            raise DeliveryHeld("Invalid event delivery receipts.")
        return data

    def _access(self, operation, *, write=False):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(str(self.path) + ".lck", timeout=5):
            data = self._read()
            result = operation(data["operations"])
            if write:
                # Match atomic_json_write's exact formatting and text-mode
                # newline encoding. Reserve space for every entered settlement.
                serialized = json.dumps(data, indent=2, ensure_ascii=False, default=None)
                size = len(serialized.replace("\n", os.linesep).encode("utf-8"))
                reserve = (
                    sum(row["state"] == "entered" for row in data["operations"].values())
                    * SETTLEMENT_RESERVE_BYTES
                )
                if size + reserve > MAX_JOURNAL_BYTES:
                    raise DeliveryHeld("Event delivery journal is full.")
                atomic_json_write(str(self.path), data, default=None)
            return deepcopy(result)

    def get(self, key):
        return self._access(lambda rows: rows.get(key))

    def rows(self):
        return self._access(lambda rows: list(rows.values()))

    def begin(
        self,
        key,
        *,
        kind,
        target,
        event=None,
        window=None,
        message_id=None,
        event_data=None,
        generation=None,
    ):
        def mutate(rows):
            if key in rows:
                return False
            rows[key] = dict(
                key=key,
                kind=kind,
                target=str(target),
                event=event,
                window=window,
                state="entered",
                entered_at=time.time(),
            )
            if message_id is not None:
                rows[key]["message_id"] = int(message_id)
            if event_data is not None:
                rows[key]["event_data"] = deepcopy(event_data)
            if generation is not None:
                rows[key]["generation"] = int(generation)
            return True

        return self._access(mutate, write=True)

    def finish(self, key, state, *, message_id=None, channel_id=None):
        if state not in {"acknowledged", "not_found", "refused"}:
            raise ValueError("Invalid terminal delivery state")

        def mutate(rows):
            row = rows[key]
            if row["state"] != "entered":
                raise DeliveryHeld("Delivery receipt already settled.")
            row.update(state=state, completed_at=time.time())
            if message_id is not None:
                row["message_id"] = int(message_id)
            if channel_id is not None:
                row["channel_id"] = int(channel_id)
            return row

        return self._access(mutate, write=True)
