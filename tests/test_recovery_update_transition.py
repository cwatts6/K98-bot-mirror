from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def receipt_transition():
    return next(
        item
        for item in updater.reviewed_transitions()
        if item["id"] == "recovery_receipt_roundtrip_v1"
    )


def test_receipt_transition_pins_both_reviewed_runtime_files():
    transition = receipt_transition()
    root = Path(__file__).resolve().parents[1]
    assert {m["path"] for m in transition["members"]} == updater.RECOVERY_RECEIPT_ROUNDTRIP_PATHS
    for member in transition["members"]:
        assert (
            updater.sha256((root / member["path"]).read_bytes().replace(b"\r\n", b"\n"))
            == member["after_sha256"]
        )
        assert member["before_sha256"] != member["after_sha256"]


@pytest.mark.parametrize("defect", ["missing", "extra", "foreign"])
def test_receipt_transition_rejects_incomplete_or_foreign_members(monkeypatch, defect):
    item = deepcopy(receipt_transition())
    if defect == "missing":
        item["members"].pop()
    elif defect == "extra":
        item["members"].append(dict(item["members"][0], path="services/export_unreviewed.py"))
    else:
        item["members"][0]["path"] = "services/unreviewed.py"
    raw = json.dumps(dict(version=1, transitions=[item])).encode()
    monkeypatch.setattr(Path, "read_bytes", lambda self: raw)
    with pytest.raises(ValueError, match=r"Complete fixed recovery-receipt|Unique export protocol"):
        updater.reviewed_transitions()


@pytest.mark.parametrize("changed", [None, "before", "after"])
def test_receipt_transition_requires_both_exact_images(monkeypatch, changed):
    item = deepcopy(receipt_transition())
    blobs = {}
    for member in item["members"]:
        for revision, field in (("before", "before_sha256"), ("after", "after_sha256")):
            raw = (revision + member["path"]).encode()
            blobs[revision, member["path"]] = raw
            member[field] = updater.sha256(raw)
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: [item])
    path = item["members"][0]["path"]
    if changed:
        blobs[changed, item["members"][1]["path"]] += b"unreviewed"
        with pytest.raises(ValueError, match="not installed/reviewed"):
            updater.check_protocol_transition(path, lambda *key: blobs.get(key), "before", "after")
    else:
        assert (
            updater.check_protocol_transition(path, lambda *key: blobs.get(key), "before", "after")
            == updater.RECOVERY_RECEIPT_ROUNDTRIP_PATHS
        )
