"""Only the reviewed issuer source is authorized by this installed transition."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def issuer_bundle():
    return next(t for t in updater.reviewed_transitions() if t["id"] == "drained_issuer_exit_v1")


def test_drained_issuer_transition_pins_exact_current_source():
    bundle = issuer_bundle()
    assert {m["path"] for m in bundle["members"]} == updater.DRAINED_ISSUER_TRANSITION_PATHS
    member = bundle["members"][0]
    raw = (Path(__file__).resolve().parents[1] / member["path"]).read_bytes()
    assert updater.sha256(raw.replace(b"\r\n", b"\n")) == member["after_sha256"]
    assert member["before_sha256"] and member["before_sha256"] != member["after_sha256"]


def test_unreviewed_issuer_bytes_remain_refused():
    with pytest.raises(ValueError):
        updater.check_source_only(
            ["scripts/run_export_startup_issuer.py"],
            read_blob=lambda commit, path: b"unreviewed issuer",
            before="a" * 40,
            target="b" * 40,
        )


@pytest.mark.parametrize("damage", ["missing", "extra", "renamed", "other_script"])
def test_issuer_transition_cannot_authorize_foreign_or_partial_source(
    tmp_path, monkeypatch, damage
):
    bundle = deepcopy(issuer_bundle())
    if damage == "missing":
        bundle["members"].clear()
    elif damage == "extra":
        bundle["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    elif damage == "renamed":
        bundle["id"] = "other_issuer"
    else:
        bundle["members"][0]["path"] = "scripts/run_export_authority.py"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[bundle]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
