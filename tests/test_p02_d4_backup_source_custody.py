"""A test bridge preserves history without authorizing partial D4 installation."""

import hashlib
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from tests.updater_source_assertions import before_d4_backup_route_hash


def test_backup_successor_bridge_rejects_source_drift(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    assert before_d4_backup_route_hash(root, "log_backup.py") == (
        "bd6a99fbd5eab29ac31528fe2e137b0e1dc1d411ff336b19ec380efeb04dac50"
    )
    original = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda self: original(self) + b"\n# drift\n")
    with pytest.raises(AssertionError):
        before_d4_backup_route_hash(root, "log_backup.py")


def test_partial_backup_patch_requires_combined_release(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    after = (root / "log_backup.py").read_bytes().replace(b"\r\n", b"\n")
    # Use the same hash-bound inert source fixture convention as historical
    # updater tests. The real final combined jump remains D4c/d qualification.
    before = b"inert exact pre-D4 backup fixture"
    original = updater.sha256
    monkeypatch.setattr(
        updater,
        "sha256",
        lambda raw: (
            "bd6a99fbd5eab29ac31528fe2e137b0e1dc1d411ff336b19ec380efeb04dac50"
            if raw == before
            else original(raw)
        ),
    )
    read = lambda revision, path: before if revision == "before" else after
    with pytest.raises(ValueError):
        updater.check_source_only(
            {"log_backup.py"}, read_blob=read, before="before", target="after"
        )


def test_all_88_historical_entries_remain_unchanged():
    entries = updater.reviewed_transitions()
    assert len(entries) == 89
    assert hashlib.sha256(json.dumps(entries[:88], sort_keys=True).encode()).hexdigest() == (
        "44ea1d790395c62940fa38ce4aa63684a71310933658a247411477ae57af025a"
    )
    assert entries[87]["id"] == "p02_d3_cleanup_custody_v1"
    assert entries[88]["id"] == updater.D4_CONTRACT_TRANSITION
