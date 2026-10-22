"""Probe scheduling and held-read recovery ship together under exact pins."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def test_report_cache_transition_pins_complete_runtime():
    item = next(
        t for t in updater.reviewed_transitions() if t["id"] == "fresh_report_cache_diagnostics_v1"
    )
    assert {m["path"] for m in item["members"]} == updater.REPORT_CACHE_TRANSITION_PATHS
    root = Path(__file__).resolve().parents[1]
    handoff = next(
        t for t in updater.reviewed_transitions() if t["id"] == "report_cache_handoff_v1"
    )
    successors = {m["path"]: m for m in handoff["members"]}
    result = next(t for t in updater.reviewed_transitions() if t["id"] == "publication_result_v1")
    result_members = {m["path"]: m for m in result["members"]}
    for member in item["members"]:
        expected = member["after_sha256"]
        if member["path"] in successors:
            successor = successors[member["path"]]
            assert successor["before_sha256"] == expected
            expected = successor["after_sha256"]
        if member["path"] in result_members:
            successor = result_members[member["path"]]
            assert successor["before_sha256"] == expected
            expected = successor["after_sha256"]
        for transition in updater.reviewed_transitions():
            if transition["id"] in {
                "guided_rollover_v1",
                "publication_timing_v1",
                "configuration_intent_replay_v1",
                "publication_detail_v1",
                "publication_readback_batches_v1",
                "evidence_backup_collection_v1",
                "configuration_pipeline_continuation_v1",
            }:
                for successor in transition["members"]:
                    if successor["path"] == member["path"]:
                        assert successor["before_sha256"] == expected
                        expected = successor["after_sha256"]
        assert (
            updater.sha256((root / member["path"]).read_bytes().replace(b"\r\n", b"\n")) == expected
        )


@pytest.mark.parametrize("change", ["missing", "extra", "renamed"])
def test_report_cache_transition_refuses_partial_or_unreviewed_bundle(
    tmp_path, monkeypatch, change
):
    item = deepcopy(
        next(
            t
            for t in updater.reviewed_transitions()
            if t["id"] == "fresh_report_cache_diagnostics_v1"
        )
    )
    if change == "missing":
        item["members"].pop()
    elif change == "extra":
        item["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    else:
        item["id"] = "unreviewed_report_cache"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[item]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()


def test_handoff_transition_pins_complete_runtime():
    item = next(t for t in updater.reviewed_transitions() if t["id"] == "report_cache_handoff_v1")
    assert {m["path"] for m in item["members"]} == updater.REPORT_CACHE_HANDOFF_PATHS
    root = Path(__file__).resolve().parents[1]
    result = next(t for t in updater.reviewed_transitions() if t["id"] == "publication_result_v1")
    successors = {m["path"]: m for m in result["members"]}
    for member in item["members"]:
        expected = member["after_sha256"]
        if member["path"] in successors:
            assert successors[member["path"]]["before_sha256"] == expected
            expected = successors[member["path"]]["after_sha256"]
        for transition in updater.reviewed_transitions():
            if transition["id"] in {
                "guided_rollover_v1",
                "publication_timing_v1",
                "configuration_intent_replay_v1",
                "publication_detail_v1",
                "publication_readback_batches_v1",
                "evidence_backup_collection_v1",
                "configuration_pipeline_continuation_v1",
            }:
                for successor in transition["members"]:
                    if successor["path"] == member["path"]:
                        assert successor["before_sha256"] == expected
                        expected = successor["after_sha256"]
        assert (
            updater.sha256((root / member["path"]).read_bytes().replace(b"\r\n", b"\n")) == expected
        )


@pytest.mark.parametrize("change", ["missing", "extra", "renamed"])
def test_handoff_refuses_partial_or_foreign_bundle(tmp_path, monkeypatch, change):
    item = deepcopy(
        next(t for t in updater.reviewed_transitions() if t["id"] == "report_cache_handoff_v1")
    )
    if change == "missing":
        item["members"].pop()
    elif change == "extra":
        item["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    else:
        item["id"] = "unreviewed_handoff"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[item]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
