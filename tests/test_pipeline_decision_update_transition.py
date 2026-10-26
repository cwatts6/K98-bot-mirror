from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from tests.updater_source_assertions import before_coordination_lifecycle_hash


def pipeline_transition():
    return next(
        item
        for item in updater.reviewed_transitions()
        if item["id"] == "pipeline_decision_bound_v1"
    )


def test_pipeline_transition_pins_reviewed_runtime_file():
    transition = pipeline_transition()
    root = Path(__file__).resolve().parents[1]
    assert {m["path"] for m in transition["members"]} == updater.PIPELINE_DECISION_BOUND_PATHS
    for member in transition["members"]:
        assert before_coordination_lifecycle_hash(root, member["path"]) == member["after_sha256"]
        assert member["before_sha256"] != member["after_sha256"]


@pytest.mark.parametrize("defect", ["missing", "extra", "foreign"])
def test_pipeline_transition_rejects_incomplete_or_foreign_members(monkeypatch, defect):
    item = deepcopy(pipeline_transition())
    if defect == "missing":
        item["members"].pop()
    elif defect == "extra":
        item["members"].append(dict(item["members"][0], path="services/export_unreviewed.py"))
    else:
        item["members"][0]["path"] = "services/unreviewed.py"
    raw = json.dumps(dict(version=1, transitions=[item])).encode()
    monkeypatch.setattr(Path, "read_bytes", lambda self: raw)
    with pytest.raises(
        ValueError,
        match=r"Complete fixed pipeline-decision|Unique export protocol|Unique bounded transition",
    ):
        updater.reviewed_transitions()


@pytest.mark.parametrize("changed", [None, "before", "after"])
def test_pipeline_transition_requires_both_exact_images(monkeypatch, changed):
    item = deepcopy(pipeline_transition())
    blobs = {}
    for member in item["members"]:
        for revision, field in (("before", "before_sha256"), ("after", "after_sha256")):
            raw = (revision + member["path"]).encode()
            blobs[revision, member["path"]] = raw
            member[field] = updater.sha256(raw)
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: [item])
    path = item["members"][0]["path"]
    if changed:
        blobs[changed, item["members"][0]["path"]] += b"unreviewed"
        with pytest.raises(ValueError, match="not installed/reviewed"):
            updater.check_protocol_transition(path, lambda *key: blobs.get(key), "before", "after")
    else:
        assert (
            updater.check_protocol_transition(path, lambda *key: blobs.get(key), "before", "after")
            == updater.PIPELINE_DECISION_BOUND_PATHS
        )
