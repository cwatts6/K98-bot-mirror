"""Verified redundancy and explicit restoration inside the protected evidence root.

Replicas protect against individual missing/corrupt files, not loss of the disk
or DPAPI identity. Restoration cannot manufacture a provider result or receipt.
"""

import hashlib
import os
from uuid import UUID, uuid4

from kvk.dal.new_source_import_dal import SourceConflict


class EvidenceCopies:
    def __init__(self, private_store):
        self.private = private_store
        self.store = private_store._store

    @staticmethod
    def keys(reference):
        key = UUID(str(reference)).hex
        return key, "replica_" + key

    def _read(self, key, expected_hash):
        with self.store._path(key).open("rb") as source:
            encrypted = source.read(self.store.max_bytes + 1)
        if not 0 < len(encrypted) <= self.store.max_bytes:
            raise ValueError("Evidence exceeds the encrypted bound.")
        data = self.private._unprotect(encrypted)
        if hashlib.sha256(data).digest() != expected_hash:
            raise ValueError("Evidence content differs from its saved commitment.")
        return encrypted

    def inspect(self, reference, expected_hash):
        if not isinstance(expected_hash, bytes) or len(expected_hash) != 32:
            raise ValueError("Exact evidence hash required.")
        result = {}
        for label, key in zip(("primary", "replica"), self.keys(reference), strict=True):
            try:
                encrypted = self._read(key, expected_hash)
                result[label] = dict(
                    state="verified", cipher_sha256=hashlib.sha256(encrypted).hexdigest()
                )
            except FileNotFoundError:
                result[label] = dict(state="missing")
            except Exception:
                # Includes DPAPI/ACL failures. No path, key material or data leaves
                # the authority; unavailable copies never count as verified.
                result[label] = dict(state="unavailable")
        return result

    def _replace(self, key, encrypted):
        destination = self.store._path(key)
        temporary = "restore_" + uuid4().hex
        self._write(temporary, encrypted)
        if destination.exists():
            # Preserve even oversized damaged files without loading them. Both
            # paths are opaque names checked inside the same protected root.
            os.rename(destination, self.store._path("damaged_" + uuid4().hex))
        os.replace(self.store._path(temporary), self.store._path(key))

    def _write(self, key, data):
        with self.store._path(key).open("xb") as target:
            target.write(data)
            target.flush()
            os.fsync(target.fileno())

    def repair(self, reference, expected_hash):
        keys = self.keys(reference)
        copies = self.inspect(reference, expected_hash)
        source = next(
            (
                key
                for label, key in zip(("primary", "replica"), keys, strict=True)
                if copies[label]["state"] == "verified"
            ),
            None,
        )
        if source is None:
            raise SourceConflict("No surviving copy verifies against the original evidence hash.")
        encrypted = self._read(source, expected_hash)
        for label, key in zip(("primary", "replica"), keys, strict=True):
            if copies[label]["state"] != "verified":
                self._replace(key, encrypted)
        result = self.inspect(reference, expected_hash)
        if any(copy["state"] != "verified" for copy in result.values()):
            raise SourceConflict(
                "Restored evidence did not pass independent readback verification."
            )
        return result

    def retain_replica(self, receipt):
        self.repair(receipt.key, bytes.fromhex(receipt.sha256))
