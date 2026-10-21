"""Authority timing setup requires both exact runtime members."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


@pytest.mark.parametrize("transition", ["publication_timing_v1", "guided_rollover_timing_v1"])
def test_publication_timing_pins_complete_runtime(transition):
    item = next(t for t in updater.reviewed_transitions() if t["id"] == transition)
    expected = updater.PUBLICATION_TIMING_PATHS
    if transition == "guided_rollover_timing_v1":
        expected = expected | updater.ROLLOVER_GUIDED_PATHS
    assert {m["path"] for m in item["members"]} == expected
    root = Path(__file__).resolve().parents[1]
    for member in item["members"]:
        source = root / member["path"]
        if member["path"] == "services/rollover_replacement_authority.py" and not source.exists():
            continue  # Private source is pinned and checked in the private repository.
        expected = member["after_sha256"]
        for successor in updater.reviewed_transitions():
            if successor["id"] not in {
                "configuration_intent_replay_v1",
                "publication_detail_v1",
                "publication_readback_batches_v1",
                "evidence_backup_collection_v1",
                "configuration_pipeline_continuation_v1",
            }:
                continue
            for update in successor["members"]:
                if update["path"] == member["path"]:
                    assert update["before_sha256"] == expected
                    expected = update["after_sha256"]
        assert updater.sha256(source.read_bytes().replace(b"\r\n", b"\n")) == expected
        assert member["before_sha256"] and member["before_sha256"] != member["after_sha256"]


@pytest.mark.parametrize("change", ["missing", "extra", "renamed"])
@pytest.mark.parametrize("transition", ["publication_timing_v1", "guided_rollover_timing_v1"])
def test_publication_timing_rejects_incomplete_or_foreign_transition(
    tmp_path, monkeypatch, change, transition
):
    item = deepcopy(next(t for t in updater.reviewed_transitions() if t["id"] == transition))
    if change == "missing":
        item["members"].pop()
    elif change == "extra":
        item["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    else:
        item["id"] = "unreviewed_timing"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[item]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()


def test_combined_transition_preserves_both_exact_endpoints():
    transitions = {
        t["id"]: {m["path"]: m for m in t["members"]} for t in updater.reviewed_transitions()
    }
    first = transitions["guided_rollover_v1"]
    second = transitions["publication_timing_v1"]
    combined = transitions["guided_rollover_timing_v1"]
    for path, member in combined.items():
        assert member["before_sha256"] == (first.get(path) or second[path])["before_sha256"]
        assert member["after_sha256"] == (second.get(path) or first[path])["after_sha256"]
        if path in first and path in second:
            assert first[path]["after_sha256"] == second[path]["before_sha256"]
