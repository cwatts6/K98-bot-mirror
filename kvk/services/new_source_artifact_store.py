"""Private, bounded original storage; no application configuration or default root."""

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import tempfile


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    sha256: str
    byte_count: int
    storage_key: str


class ArtifactStore:
    """The operator supplies a private root outside Git, writable only by the service.

    Failed writes retain their generated temporary file as orphan evidence. Source filenames
    never participate in paths. There is no original/history cleanup operation.
    """

    def __init__(self, root: Path, *, max_bytes: int = 20 * 1024 * 1024):
        root = Path(root)
        if not root.is_absolute() or not 0 < max_bytes <= 20 * 1024 * 1024:
            raise ValueError("Require an absolute private root and bounded artifact size.")
        self.root = root.resolve()
        self.max_bytes = max_bytes
        if any((parent / ".git").exists() for parent in (self.root, *self.root.parents)):
            raise ValueError("Original artifacts must be outside Git.")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, digest: str) -> Path:
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("Invalid artifact hash.")
        path = self.root / (digest + ".xlsx")
        if path.is_symlink() or path.resolve().parent != self.root:
            raise ValueError("Artifact path escapes its private root.")
        return path

    def read(self, artifact: StoredArtifact) -> bytes:
        path = self._path(artifact.sha256)
        if artifact.storage_key != path.name:
            raise ValueError("Artifact key/hash mismatch.")
        with path.open("rb") as stream:
            content = stream.read(self.max_bytes + 1)
        if (
            not 0 < len(content) <= self.max_bytes
            or len(content) != artifact.byte_count
            or hashlib.sha256(content).hexdigest() != artifact.sha256
        ):
            raise ValueError("Original artifact failed integrity verification.")
        return content

    def persist_artifact(self, content: bytes) -> StoredArtifact:
        if not isinstance(content, bytes) or not 0 < len(content) <= self.max_bytes:
            raise ValueError("Original artifact exceeds the accepted size boundary.")
        digest = hashlib.sha256(content).hexdigest()
        path = self._path(digest)
        artifact = StoredArtifact(digest, len(content), path.name)
        if path.exists():
            self.read(artifact)
            return artifact
        descriptor, temporary = tempfile.mkstemp(prefix=".source-", dir=self.root)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        # Concurrent writers for this hash have identical verified bytes. An existing
        # different original is an integrity conflict, never permission to repair it.
        if path.exists():
            self.read(artifact)
            os.unlink(temporary)
        else:
            self._path(digest)
            os.replace(temporary, path)
        self.read(artifact)
        return artifact
