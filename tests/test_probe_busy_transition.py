"""Probe scheduling and held-read recovery ship together under exact pins."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from tests.updater_source_assertions import historical_runtime_hash


def test_probe_busy_transition_pins_complete_runtime():
    item = next(t for t in updater.reviewed_transitions() if t["id"] == "probe_busy_recovery_v1")
    assert {m["path"] for m in item["members"]} == updater.PROBE_BUSY_TRANSITION_PATHS
    root = Path(__file__).resolve().parents[1]
    for member in item["members"]:
        expected = member["after_sha256"]
        for successor in updater.reviewed_transitions():
            if successor["id"] not in {
                "guided_rollover_v1",
                "publication_timing_v1",
                "configuration_intent_replay_v1",
                "publication_detail_v1",
                "publication_readback_batches_v1",
                "evidence_backup_collection_v1",
                "configuration_pipeline_continuation_v1",
                "configuration_read_request_v1",
            }:
                continue
            for changed in successor["members"]:
                if changed["path"] == member["path"]:
                    assert changed["before_sha256"] == expected
                    expected = changed["after_sha256"]
        assert historical_runtime_hash(root, member["path"]) == expected


@pytest.mark.parametrize("change", ["missing", "extra", "renamed"])
def test_probe_busy_transition_refuses_partial_or_unreviewed_bundle(tmp_path, monkeypatch, change):
    item = deepcopy(
        next(t for t in updater.reviewed_transitions() if t["id"] == "probe_busy_recovery_v1")
    )
    if change == "missing":
        item["members"].pop()
    elif change == "extra":
        item["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    else:
        item["id"] = "unreviewed_probe_busy"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[item]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
