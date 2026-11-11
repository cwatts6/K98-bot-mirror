"""D4 census distinguishes source candidates from installed evidence."""

import subprocess

import pytest

from scripts import p02_d4_inventory as inventory


def test_missing_definition_is_not_retirement_or_invented_definition():
    result = inventory.source_census(
        {"caller.py": b"query = 'EXEC dbo.UPDATE_ALL'\n"},
        {"sql_schema/dbo.KingdomScanData4.Table.sql": b"DEFAULT NEXT VALUE FOR dbo.KS4_UNO_SEQ"},
    )
    rows = {r["name"]: r for r in result["objects"]}
    assert rows["KS4_UNO_SEQ"]["source_status"] == "missing"
    assert rows["KS4_UNO_SEQ"]["references"][0]["lines"] == [1]
    assert rows["UPDATE_ALL"]["installed_use"] == "unknown"
    assert rows["TEST"]["references"] == []
    assert rows["TEST"]["disposition"] == "qualify_or_explicit_retirement"


def test_comment_and_dynamic_matches_are_candidates_without_source_disclosure():
    result = inventory.source_census(
        {"caller.py": b"# UPDATE_ALL\nquery = 'EXEC [dbo].[update_all2]'\n"},
        {
            "sql_schema/dbo.UPDATE_ALL.StoredProcedure.sql": b"CREATE PROCEDURE dbo.UPDATE_ALL AS SELECT 1"
        },
    )
    rows = {r["name"]: r for r in result["objects"]}
    assert rows["UPDATE_ALL"]["definitions"] == ["sql_schema/dbo.UPDATE_ALL.StoredProcedure.sql"]
    assert len(rows["UPDATE_ALL"]["references"]) == 2
    assert len(rows["UPDATE_ALL2"]["references"]) == 1
    ref = rows["UPDATE_ALL2"]["references"][0]
    assert ref["lines"] == [2]
    assert len(ref["sha256"]) == 64
    assert ref["classification"] == "lexical_candidate_requires_review"
    assert "text" not in ref


def test_only_git_tracked_sources_are_read(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    (tmp_path / "caller.py").write_text("# UPDATE_ALL")
    (tmp_path / "private.py").write_text("raise Exception('must not import')")
    subprocess.run(["git", "-C", str(tmp_path), "add", "caller.py"], check=True)
    assert inventory.tracked_sources(tmp_path, ".py") == {"caller.py": b"# UPDATE_ALL"}


def test_source_byte_bound_is_enforced_before_loading(tmp_path, monkeypatch):
    monkeypatch.setattr(inventory.subprocess, "check_output", lambda *a, **k: b"large.py\0")
    monkeypatch.setattr(inventory, "MAX_FILE_BYTES", 3)
    (tmp_path / "large.py").write_bytes(b"abcd")
    with pytest.raises(ValueError, match="file bound"):
        inventory.tracked_sources(tmp_path, ".py")


def test_missing_tracked_source_is_not_silently_dropped(tmp_path, monkeypatch):
    monkeypatch.setattr(inventory.subprocess, "check_output", lambda *a, **k: b"missing.py\0")
    with pytest.raises(ValueError, match="missing"):
        inventory.tracked_sources(tmp_path, ".py")


def test_total_byte_bound_is_enforced(tmp_path, monkeypatch):
    monkeypatch.setattr(inventory.subprocess, "check_output", lambda *a, **k: b"a.py\0b.py\0")
    monkeypatch.setattr(inventory, "MAX_TOTAL_BYTES", 3)
    (tmp_path / "a.py").write_bytes(b"ab")
    (tmp_path / "b.py").write_bytes(b"cd")
    with pytest.raises(ValueError, match="total byte bound"):
        inventory.tracked_sources(tmp_path, ".py")


def test_git_path_cannot_escape_repository(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    (tmp_path / "outside.py").write_bytes(b"private")
    monkeypatch.setattr(inventory.subprocess, "check_output", lambda *a, **k: b"../outside.py\0")
    with pytest.raises(ValueError, match="escapes"):
        inventory.tracked_sources(root, ".py")


def test_manifest_changes_for_unreferenced_source():
    before = inventory.source_census({"unrelated.py": b"pass"}, {})
    after = inventory.source_census({"unrelated.py": b"changed"}, {})
    assert (
        before["source_inventory"]["bot"]["manifest_sha256"]
        != after["source_inventory"]["bot"]["manifest_sha256"]
    )
