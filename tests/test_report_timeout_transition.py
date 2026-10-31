from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from tests.updater_source_assertions import before_contention_hash


def test_timeout_transition_requires_complete_exact_companion_bundle(monkeypatch):
    transition = next(
        t for t in updater.reviewed_transitions() if t["id"] == "report_timeout_monitor_v1"
    )
    root = Path(__file__).resolve().parents[1]
    blobs = {}
    fixture = deepcopy(transition)
    for member in fixture["members"]:
        path = member["path"]
        after = (root / path).read_bytes().replace(b"\r\n", b"\n")
        assert before_contention_hash(root, path) == member["after_sha256"]
        # The following transition exercise uses synthetic before/after images.
        member["after_sha256"] = updater.sha256(after)
        blobs[("before", path)] = b"fixture predecessor\n"
        blobs[("after", path)] = after
        member["before_sha256"] = updater.sha256(blobs[("before", path)])
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: [fixture])
    read = lambda rev, name: blobs.get((rev, name))
    path = "services/recovery_runtime.py"
    assert updater.check_protocol_transition(path, read, "before", "after") == set(
        updater.REPORT_TIMEOUT_MONITOR_PATHS
    )
    companion = ("after", "services/stats_report_continuation_dal.py")
    blobs[companion] += b"# unreviewed change\n"
    with pytest.raises(ValueError, match="not installed/reviewed"):
        updater.check_protocol_transition(path, read, "before", "after")
    del blobs[companion]
    with pytest.raises(ValueError, match="not installed/reviewed"):
        updater.check_protocol_transition(path, read, "before", "after")


def test_timeout_registry_refuses_incomplete_fixed_members(monkeypatch):
    registry = json.loads(
        Path(updater.__file__).with_name("k98_update_transitions.json").read_bytes()
    )
    transition = next(t for t in registry["transitions"] if t["id"] == "report_timeout_monitor_v1")
    transition["members"].pop()
    monkeypatch.setattr(Path, "read_bytes", lambda _: json.dumps(registry).encode())
    with pytest.raises(ValueError, match="Complete fixed reporting-timeout/monitor"):
        updater.reviewed_transitions()
