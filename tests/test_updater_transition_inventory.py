"""Changed-path admission must retain authenticated unchanged dependencies."""

from copy import deepcopy
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from scripts.validate_k98_update_compatibility import classify

BEFORE, AFTER = "a" * 40, "b" * 40


def bundle_fixture(monkeypatch, *, crlf=False):
    item = deepcopy(next(t for t in updater.reviewed_transitions() if t["id"] == "p1_mge_a1b_v1"))
    blobs = {}
    for member in item["members"]:
        unchanged = member["before_sha256"] == member["after_sha256"]
        for revision, field in ((BEFORE, "before_sha256"), (AFTER, "after_sha256")):
            raw = None
            if member[field] is not None:
                identity = "unchanged" if unchanged else revision
                raw = f"# {identity}:{member['path']}\n".encode()
            member[field] = updater.sha256(raw) if raw is not None else None
            blobs[revision, member["path"]] = (
                raw.replace(b"\n", b"\r\n") if crlf and raw is not None else raw
            )
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: [item])
    monkeypatch.setattr(updater, "coordinated_policy", lambda: None)
    paths = sorted(m["path"] for m in item["members"])
    changed = [p for p in paths if blobs[BEFORE, p] != blobs[AFTER, p]]
    previous = {
        "AutomaticStartupPolicy.json": {
            "source_hashes": {
                p: updater.sha256(blobs[BEFORE, p]) for p in paths if blobs[BEFORE, p] is not None
            }
        }
    }
    files = {Path(p).name: "c" * 64 for p in updater.TOOL_SOURCE_PATHS}
    files["EmptyGitConfig.txt"] = updater.sha256(b"")
    import hashlib

    from scripts.verify_k98_update_pair import build_contract_archive

    files["contract_verifier.zip"] = hashlib.sha256(
        build_contract_archive(Path(__file__).resolve().parents[1])
    ).hexdigest()
    installed = {"version": 1, "files": files}
    return blobs, paths, changed, previous, installed


@pytest.mark.parametrize("crlf", [False, True])
def test_real_a1b_changed_shape_prepares_with_unchanged_dependencies(monkeypatch, crlf):
    blobs, paths, changed, previous, installed = bundle_fixture(monkeypatch, crlf=crlf)
    assert len(paths) == 41 and len(changed) == 36
    read = lambda revision, path: blobs.get((revision, path))
    result = classify(BEFORE, AFTER, changed, read, installed)
    assert result["classification"] == "ROUTINE_COMPATIBLE", result
    plan, payload = updater.source_plan(previous, BEFORE, AFTER, changed, read)
    assert {m["path"] for m in plan["source_members"]} == set(changed)
    assert set(payload) == set(changed)
    for path in paths:
        assert plan["new_pins"][path] == updater.sha256(blobs[AFTER, path])


def test_omitted_changed_member_is_refused_by_classifier_and_preparation(monkeypatch):
    blobs, _, changed, previous, installed = bundle_fixture(monkeypatch)
    changed.remove("mge/mge_embed_manager.py")
    read = lambda revision, path: blobs.get((revision, path))
    result = classify(BEFORE, AFTER, changed, read, installed)
    assert result["classification"] == "COORDINATED_RELEASE_REQUIRED"
    assert any("Incomplete reviewed protocol transition inventory" in s for s in result["blockers"])
    with pytest.raises(ValueError, match="Incomplete reviewed protocol transition inventory"):
        updater.source_plan(previous, BEFORE, AFTER, changed, read)


@pytest.mark.parametrize("revision", [BEFORE, AFTER])
@pytest.mark.parametrize("damage", ["missing", "altered"])
def test_unchanged_dependency_still_requires_exact_authenticated_bytes(
    monkeypatch, revision, damage
):
    blobs, _, changed, previous, installed = bundle_fixture(monkeypatch)
    blobs[revision, "core/owned_work.py"] = None if damage == "missing" else b"unreviewed"
    read = lambda revision, path: blobs.get((revision, path))
    assert (
        classify(BEFORE, AFTER, changed, read, installed)["classification"]
        == "COORDINATED_RELEASE_REQUIRED"
    )
    with pytest.raises(ValueError, match="not installed/reviewed"):
        updater.source_plan(previous, BEFORE, AFTER, changed, read)


def test_omitted_newline_only_change_is_not_treated_as_unchanged(monkeypatch):
    blobs, _, changed, previous, installed = bundle_fixture(monkeypatch)
    path = "core/owned_work.py"
    blobs[AFTER, path] = blobs[AFTER, path].replace(b"\n", b"\r\n")
    read = lambda revision, path: blobs.get((revision, path))
    result = classify(BEFORE, AFTER, changed, read, installed)
    assert result["classification"] == "COORDINATED_RELEASE_REQUIRED"
    with pytest.raises(ValueError, match="Incomplete reviewed protocol transition inventory"):
        updater.source_plan(previous, BEFORE, AFTER, changed, read)


def test_unchanged_dependency_cannot_be_invented_as_a_changed_path(monkeypatch):
    blobs, _, changed, previous, installed = bundle_fixture(monkeypatch)
    changed.append("core/owned_work.py")
    read = lambda revision, path: blobs.get((revision, path))
    assert (
        classify(BEFORE, AFTER, changed, read, installed)["classification"]
        == "COORDINATED_RELEASE_REQUIRED"
    )
    with pytest.raises(ValueError, match="Changed-path inventory differs"):
        updater.source_plan(previous, BEFORE, AFTER, changed, read)
