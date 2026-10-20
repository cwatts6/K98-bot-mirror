from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


@pytest.mark.parametrize(
    "transition,paths",
    [
        ("publication_result_v1", updater.PUBLICATION_RESULT_PATHS),
        ("publication_result_handoff_v1", updater.PUBLICATION_RESULT_HANDOFF_PATHS),
    ],
)
def test_result_transition_pins_all_runtime_members(transition, paths):
    item = next(t for t in updater.reviewed_transitions() if t["id"] == transition)
    assert {m["path"] for m in item["members"]} == paths
    root = Path(__file__).resolve().parents[1]
    for member in item["members"]:
        assert (
            updater.sha256((root / member["path"]).read_bytes().replace(b"\r\n", b"\n"))
            == member["after_sha256"]
        )
        assert member["before_sha256"] != member["after_sha256"]


@pytest.mark.parametrize("change", ["missing", "extra", "renamed"])
@pytest.mark.parametrize("transition", ["publication_result_v1", "publication_result_handoff_v1"])
def test_result_transition_refuses_partial_or_foreign_bundle(
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
        item["id"] = "unreviewed_result"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[item]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
