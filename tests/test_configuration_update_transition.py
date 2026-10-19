"""The installed tool accepts only the complete named configuration-only transition."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def test_configuration_transition_pins_every_runtime_member():
    bundle = next(
        t for t in updater.reviewed_transitions() if t["id"] == "configuration_only_completion_v1"
    )
    assert {m["path"] for m in bundle["members"]} == updater.CONFIGURATION_ONLY_TRANSITION_PATHS
    root = Path(__file__).resolve().parents[1]
    for member in bundle["members"]:
        assert (
            updater.sha256((root / member["path"]).read_bytes().replace(b"\r\n", b"\n"))
            == member["after_sha256"]
        )
        assert member["before_sha256"] != member["after_sha256"]


@pytest.mark.parametrize("damage", ["missing", "extra", "renamed"])
def test_configuration_transition_cannot_authorize_a_partial_or_foreign_bundle(
    tmp_path, monkeypatch, damage
):
    bundle = deepcopy(
        next(
            t
            for t in updater.reviewed_transitions()
            if t["id"] == "configuration_only_completion_v1"
        )
    )
    if damage == "missing":
        bundle["members"].pop()
    elif damage == "extra":
        bundle["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    else:
        bundle["id"] = "foreign_completion_v1"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[bundle]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
