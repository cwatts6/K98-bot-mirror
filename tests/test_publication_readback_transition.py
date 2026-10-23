"""Read batching needs one complete exact protected source transition."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from tests.updater_source_assertions import historical_runtime_hash


def bundle():
    return next(
        t for t in updater.reviewed_transitions() if t["id"] == "publication_readback_batches_v1"
    )


def test_batch_transition_has_exact_sources_and_predecessor():
    item = bundle()
    assert {m["path"] for m in item["members"]} == updater.PUBLICATION_READBACK_BATCH_PATHS
    root = Path(__file__).resolve().parents[1]
    for member in item["members"]:
        prior = {
            "services/export_execution_dal.py": "d01ea9d09d7318621c45e57c15ef1ffcb6ec744f4f9d67a5cea0fc4fc8a68a06",
            "services/export_reconciliation_service.py": "eabdd107a0ad22642e2757c4c2ec2b999d377fc7131ded1215bdbe27240e9319",
            "kvk/services/new_source_workbook_transport.py": "7ffc87e1616923b141c51ce8a603f7676c6f88dde00b69f1a623828d13ed194a",
        }
        assert prior[member["path"]] == member["before_sha256"]
        assert historical_runtime_hash(root, member["path"]) == member["after_sha256"]


@pytest.mark.parametrize("damage", ["missing", "extra", "duplicate", "renamed", "invalid_hash"])
def test_partial_or_foreign_batch_transition_is_rejected(tmp_path, monkeypatch, damage):
    item = deepcopy(bundle())
    if damage == "missing":
        item["members"].pop()
    elif damage == "extra":
        item["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    elif damage == "duplicate":
        item["members"].append(item["members"][0])
    elif damage == "renamed":
        item["id"] = "unreviewed_readback"
    else:
        item["members"][0]["after_sha256"] = "invalid"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[item]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
