"""Immutable, bounded spool bytes with explicit private storage ownership."""

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
from uuid import uuid4


@dataclass(frozen=True)
class SnapshotReceipt:
    key: str
    byte_count: int
    sha256: str
    storage_owner: str


class ExportSnapshotStore:
    def __init__(self, root, storage_owner, *, max_bytes=256 * 1024 * 1024):
        path = Path(root)
        if not path.is_absolute() or path.is_symlink():
            raise ValueError("An absolute registered private spool root is required.")
        self.root = path.resolve()
        if not self.root.is_dir() or any(
            (p / ".git").exists() for p in (self.root, *self.root.parents)
        ):
            raise ValueError("Provision a private spool directory outside Git first.")
        if not re.fullmatch(r"[A-Za-z0-9_.@:-]{1,128}", storage_owner):
            raise ValueError("Invalid storage owner.")
        if type(max_bytes) is not int or not 1 <= max_bytes <= 2**31 - 1:
            raise ValueError("Invalid spool byte bound.")
        self.storage_owner, self.max_bytes = storage_owner, max_bytes

    def _path(self, key):
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", key):
            raise ValueError("Invalid opaque spool key.")
        path = self.root / key
        if path.is_symlink() or path.resolve().parent != self.root:
            raise ValueError("Spool escapes its registered root.")
        return path

    def put(self, data):
        if not isinstance(data, bytes) or not 0 < len(data) <= self.max_bytes:
            raise ValueError("Spool exceeds its configured bound.")
        key = uuid4().hex
        # Exclusive creation never replaces an existing generation. Register in SQL
        # only after close/fsync and readback; incomplete/orphan bytes are retained.
        with self._path(key).open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        receipt = SnapshotReceipt(
            key, len(data), hashlib.sha256(data).hexdigest(), self.storage_owner
        )
        self.read(receipt)
        return receipt

    def read(self, receipt):
        if receipt.storage_owner != self.storage_owner:
            raise ValueError("Spool belongs to another storage owner.")
        if not 0 < receipt.byte_count <= self.max_bytes:
            raise ValueError("Invalid retained spool length.")
        with self._path(receipt.key).open("rb") as stream:
            data = stream.read(receipt.byte_count + 1)
        if len(data) != receipt.byte_count or hashlib.sha256(data).hexdigest() != receipt.sha256:
            raise ValueError("Retained spool is missing, incomplete or corrupt.")
        return data
