"""Strict, identity-checked persistence for the existing generic view tracker."""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from file_utils import acquire_lock, atomic_write_json
from services.legacy_export_snapshot_service import drain_thread

EDIT_RECEIPT = "_restoration_edit"
MAX_TRACKER_BYTES = 8 * 1024 * 1024


def fingerprint(entry: Any) -> str:
    payload = (
        {k: v for k, v in entry.items() if k != EDIT_RECEIPT} if isinstance(entry, dict) else entry
    )
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


@contextmanager
def tracker_lock(path, *, timeout, poll):
    """Release the legacy lock even when the protected operation raises."""
    lock = acquire_lock(path, timeout=timeout, poll=poll)
    lock.__enter__()
    try:
        yield
    finally:
        # acquire_lock's generator releases on normal exit, not on a thrown body error.
        lock.__exit__(None, None, None)


class TrackedViewStore:
    def __init__(self, path, lock_path, *, timeout=5.0, poll=0.05):
        self.path = Path(path)
        self.lock_path = lock_path
        self.timeout = timeout
        self.poll = poll

    def read(self) -> dict[str, Any]:
        try:
            with self.path.open("rb") as stream:
                data = stream.read(MAX_TRACKER_BYTES + 1)
        except FileNotFoundError:
            return {}
        if len(data) > MAX_TRACKER_BYTES:
            raise ValueError("tracker exceeds restoration size limit")
        raw = json.loads(data)
        if not isinstance(raw, dict):
            raise ValueError("tracker root must be an object")
        return raw

    async def snapshot(self) -> dict[str, Any]:
        return await drain_thread(self.read)

    @asynccontextmanager
    async def locked(self):
        lock = tracker_lock(self.lock_path, timeout=self.timeout, poll=self.poll)
        acquired = False

        def enter():
            nonlocal acquired
            lock.__enter__()
            acquired = True

        try:
            await drain_thread(enter)
            yield
        finally:
            if acquired:
                await drain_thread(lock.__exit__, None, None, None)

    @staticmethod
    def matches(data, key, expected) -> bool:
        return key in data and fingerprint(data[key]) == fingerprint(expected)

    async def write(self, data):
        """Caller holds locked(); once entered, drain the actual atomic writer."""
        await drain_thread(atomic_write_json, self.path, data)

    async def prune(self, key, expected) -> Literal["pruned", "superseded", "outcome_unconfirmed"]:
        async with self.locked():
            data = await self.snapshot()
            if not self.matches(data, key, expected):
                return "superseded"
            current = data[key]
            receipt = current.get(EDIT_RECEIPT) if isinstance(current, dict) else None
            if receipt is not None and (
                not isinstance(receipt, dict) or receipt.get("state") != "acknowledged"
            ):
                return "outcome_unconfirmed"
            del data[key]
            await self.write(data)
            return "pruned"


def preserve_edit_receipt(previous, replacement):
    """A same-message producer save cannot erase an uncertain remote edit."""
    result = dict(replacement)
    result.pop(EDIT_RECEIPT, None)
    if isinstance(previous, dict) and EDIT_RECEIPT in previous:
        # Keep uncertainty across payload updates to the same physical message too.
        if all(str(previous.get(k)) == str(result.get(k)) for k in ("channel_id", "message_id")):
            result[EDIT_RECEIPT] = deepcopy(previous[EDIT_RECEIPT])
    return result
