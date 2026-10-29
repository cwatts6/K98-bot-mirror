"""Admission tests are offline; none qualify native SQL or Windows custody."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def profile():
    return dict(
        version=1,
        profile="mge_finalisation_v1",
        migration_id="20261029_001_mge_board_finalisation",
        database_collation="Latin1_General_CI_AS",
        tempdb_collation="SQL_Latin1_General_CP1_CI_AS",
        compatibility_level=160,
        requires=[],
    )


def description(p):
    return dict(
        version=1,
        profile=p["profile"],
        bot_predecessors=["a" * 40],
        sql_commit="b" * 40,
        migrations=[dict(id=p["migration_id"], sha256=updater.sha256(json.dumps(p).encode()))],
    )


def test_exact_registry_pins_all_runtime_members_including_results_import():
    item = next(t for t in updater.reviewed_transitions() if t["id"] == "p1_mge_finalisation_v1")
    assert {m["path"] for m in item["members"]} == updater.MGE_FINALISATION_PATHS
    assert "mge/dal/mge_results_dal.py" in updater.MGE_FINALISATION_PATHS
    for member in item["members"]:
        raw = (Path(__file__).resolve().parents[1] / member["path"]).read_bytes()
        assert updater.sha256(raw.replace(b"\r\n", b"\n")) == member["after_sha256"]


@pytest.mark.parametrize("path", sorted(updater.MGE_FINALISATION_PATHS))
@pytest.mark.parametrize("revision", ["before", "after"])
def test_each_bundle_peer_is_authenticated(monkeypatch, path, revision):
    item = deepcopy(
        next(t for t in updater.reviewed_transitions() if t["id"] == "p1_mge_finalisation_v1")
    )
    blobs = {}
    for member in item["members"]:
        for rev in ("before", "after"):
            raw = None if member[rev + "_sha256"] is None else (rev + member["path"]).encode()
            blobs[rev, member["path"]] = raw
            member[rev + "_sha256"] = updater.sha256(raw) if raw is not None else None
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: [item])
    updater.check_protocol_transition(
        "mge/mge_finalisation.py", lambda *k: blobs.get(k), "before", "after"
    )
    blobs[revision, path] = b"unreviewed"
    with pytest.raises(ValueError, match="not installed/reviewed"):
        updater.check_protocol_transition(
            "mge/mge_finalisation.py", lambda *k: blobs.get(k), "before", "after"
        )


@pytest.mark.parametrize(
    "defect", ["extra", "type", "compatibility", "collation", "requires", "duplicate"]
)
def test_no_arbitrary_profile_or_coercion(defect):
    p = profile()
    if defect == "extra":
        p["sql"] = "SELECT 1"
    if defect == "type":
        p["version"] = True
    if defect == "compatibility":
        p["compatibility_level"] = "160"
    if defect == "collation":
        p["database_collation"] = "x; SELECT 1"
    if defect == "requires":
        p["requires"] = {}
    if defect == "duplicate":
        p["requires"] = [
            dict(migration_id="20261001_001_example", sha256="c" * 64, status="Applied")
        ] * 2
    with pytest.raises(ValueError):
        updater.validate_mge_profile(p, p["migration_id"])


def test_exact_payload_and_protected_family():
    p = profile()
    d = description(p)
    files = {
        "deploy/" + name: name.encode()
        for name in (
            "Deploy-SqlMigration.ps1",
            "SqlDeploy.ModuleRelease.ps1",
            "SqlDeploy.TableRelease.ps1",
            "SqlDeploy.MgeFinalisation.ps1",
        )
    }
    files["migrations/" + p["migration_id"] + ".release.json"] = json.dumps(p).encode()
    binding, payload = updater.combined_payload(d, files.get)
    from scripts.build_mge_release_description import describe

    assert describe(d["sql_commit"], d["bot_predecessors"], files.get) == d
    assert len(payload) == 5
    assert binding["profiles"][0]["sha256"] == d["migrations"][0]["sha256"]
    with pytest.raises(ValueError, match="protected MGE"):
        updater.combined_payload(d, files.get, protected_objects=["dbo.MGE_Events"])
    for path in list(files):
        damaged = dict(files)
        damaged.pop(path)
        with pytest.raises(ValueError):
            updater.combined_payload(d, damaged.get)


@pytest.mark.parametrize(
    "mode", ["missing", "unchanged", "old_profile", "wrong_predecessor", "valid"]
)
def test_initial_adoption_cannot_be_source_only(mode):
    p = profile()
    d = description(p)
    if mode == "old_profile":
        d["profile"] = "additive_tables_v1"
    if mode == "wrong_predecessor":
        d["bot_predecessors"] = ["c" * 40]
    raw = json.dumps(d).encode()
    blobs = {("b" * 40, "mge/mge_finalisation.py"): b"new"}
    if mode != "missing":
        blobs["b" * 40, updater.RELEASE_DESCRIPTION] = raw
    if mode == "unchanged":
        blobs["a" * 40, updater.RELEASE_DESCRIPTION] = raw
    call = lambda: updater.check_mge_release_binding(
        "a" * 40, "b" * 40, ["mge/mge_finalisation.py"], lambda *k: blobs.get(k)
    )
    if mode == "valid":
        call()
    else:
        with pytest.raises(ValueError):
            call()
