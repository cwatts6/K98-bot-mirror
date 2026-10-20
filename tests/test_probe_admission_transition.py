"""A probe fix must not authorize a partial or unrelated protected upgrade."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def test_probe_admission_transition_matches_complete_runtime_patch():
    bundle = next(
        t for t in updater.reviewed_transitions() if t["id"] == "probe_stream_admission_v1"
    )
    assert {m["path"] for m in bundle["members"]} == updater.PROBE_ADMISSION_TRANSITION_PATHS
    root = Path(__file__).resolve().parents[1]
    for member in bundle["members"]:
        assert (
            updater.sha256((root / member["path"]).read_bytes().replace(b"\r\n", b"\n"))
            == member["after_sha256"]
        )
        assert member["before_sha256"] != member["after_sha256"]


@pytest.mark.parametrize("damage", ["missing", "extra", "renamed"])
def test_probe_transition_refuses_incomplete_or_unreviewed_bundle(tmp_path, monkeypatch, damage):
    bundle = deepcopy(
        next(t for t in updater.reviewed_transitions() if t["id"] == "probe_stream_admission_v1")
    )
    if damage == "missing":
        bundle["members"].pop()
    elif damage == "extra":
        bundle["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    else:
        bundle["id"] = "foreign_admission_v1"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[bundle]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
