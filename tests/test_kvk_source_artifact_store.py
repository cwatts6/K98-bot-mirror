import hashlib

import pytest

from kvk.services.new_source_artifact_store import ArtifactStore, StoredArtifact


def test_round_trip_replay_and_content_address(tmp_path):
    store = ArtifactStore(tmp_path / "private")
    artifact = store.persist_artifact(b"synthetic original")
    assert artifact.storage_key == hashlib.sha256(b"synthetic original").hexdigest() + ".xlsx"
    assert store.persist_artifact(b"synthetic original") == artifact
    assert store.read(artifact) == b"synthetic original"
    assert len(list(store.root.iterdir())) == 1


def test_bounds_hash_conflict_and_no_git_root(tmp_path):
    store = ArtifactStore(tmp_path / "private", max_bytes=4)
    for content in (b"", b"12345"):
        with pytest.raises(ValueError):
            store.persist_artifact(content)
    artifact = store.persist_artifact(b"1234")
    (store.root / artifact.storage_key).write_bytes(b"4321")
    with pytest.raises(ValueError, match="integrity"):
        store.persist_artifact(b"1234")
    with pytest.raises(ValueError):
        store.read(StoredArtifact("../escape", 1, "../escape.xlsx"))
    (tmp_path / ".git").mkdir()
    with pytest.raises(ValueError, match="outside Git"):
        ArtifactStore(tmp_path / "repository")
