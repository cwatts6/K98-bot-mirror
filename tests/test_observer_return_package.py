"""Exact-source return pair checks. No database, process or deployment execution."""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import zipfile

import pytest

from scripts.prepare_p02_observer_return import (
    AMENDED,
    MIGRATION_ID,
    PROFILE_SHA256,
    RETURN_ID,
    REUPGRADE_ID,
    build,
    prepare,
)


@pytest.fixture
def source():
    archive = os.environ.get("K98_OBSERVER_BASELINE_ARCHIVE")
    sql = os.environ.get("K98_OBSERVER_SQL_SOURCE")
    if not archive or not sql:
        pytest.skip("Explicit retained baseline and SQL candidate required; no native connection")
    return Path(archive), Path(sql)


def embedded_modules(raw):
    return [
        value.replace("''", "'")
        for value in re.findall(r"EXEC sys\.sp_executesql N'((?:''|[^'])*)';", raw.decode())
    ]


def test_return_restores_exact_historical_procedure_text_and_keeps_identity(source):
    archive, sql = source
    files, receipt = build(archive, sql)
    with zipfile.ZipFile(archive) as z:
        rows = list(map(json.loads, z.read("run-01/observations.jsonl").splitlines()))
    old = next(r["observation"] for r in rows if r["stage"] == "application_sql_contract")
    expected = {
        r["ModuleDefinition"] for r in old["metadata"]["objects"] if r["ObjectName"] in AMENDED
    }
    modules = embedded_modules(files[RETURN_ID + ".sql"])
    assert len(modules) == 3
    assert {"CREATE   " + m[len("CREATE OR ALTER ") :] for m in modules} == expected
    assert receipt["preserved_objects"] == [
        "dbo.P02ObservationGeneration",
        "dbo.usp_P02BeginCatalogueMutation",
        "dbo.usp_P02EndCatalogueMutation",
        "dbo.usp_P02ReadObservationBoundary",
    ]
    for identifier in (RETURN_ID, REUPGRADE_ID):
        raw = files[identifier + ".sql"].decode()
        assert not re.search(r"(?i)\b(?:ALTER|DROP|CREATE)\s+SEQUENCE\b", raw)
        assert not re.search(
            r"(?i)\b(?:INSERT|UPDATE|DELETE|MERGE)\s+(?:INTO\s+)?dbo\.(?:SchemaMigrationHistory|DeploymentRunHistory)\b",
            raw,
        )
        assert "no-business return window" in raw
        assert "@LockTimeout=0" in raw
        assert "ActiveOutputOperationID IS NOT NULL" in raw
    assert not receipt["deployable"] and not receipt["native_qualified"]


def test_pair_uses_fresh_receipts_and_exact_inverse_checks(source):
    files, _ = build(*source)
    profiles = {i: json.loads(files[i + ".release.json"]) for i in (RETURN_ID, REUPGRADE_ID)}
    assert profiles[RETURN_ID]["requires"] == [
        dict(migration_id=MIGRATION_ID, sha256=PROFILE_SHA256, status="Applied")
    ]
    assert profiles[REUPGRADE_ID]["requires"][-1] == dict(
        migration_id=RETURN_ID,
        sha256=hashlib.sha256(files[RETURN_ID + ".release.json"]).hexdigest(),
        status="Applied",
    )
    assert files[RETURN_ID + ".after.sql"] == files[REUPGRADE_ID + ".before.sql"]
    assert files[RETURN_ID + ".before.sql"] == files[REUPGRADE_ID + ".after.sql"]
    original = source[1] / "migrations" / (MIGRATION_ID + ".after.sql")
    assert files[REUPGRADE_ID + ".after.sql"] == original.read_bytes()
    for profile in profiles.values():
        for item in (profile["script"], *profile["checks"].values()):
            assert hashlib.sha256(files[item["file"]]).hexdigest() == item["sha256"]


def test_reupgrade_restores_only_reviewed_amendments_and_hooks(source):
    files, _ = build(*source)
    modules = embedded_modules(files[REUPGRADE_ID + ".sql"])
    assert len(modules) == 7
    assert sum(bool(re.match(r"^(?:ALTER|CREATE OR ALTER) PROCEDURE\b", m)) for m in modules) == 3
    assert sum("CREATE OR ALTER TRIGGER" in m for m in modules) == 4
    assert all("CREATE OR ALTER PROCEDURE dbo.usp_P02" not in m for m in modules)
    text = files[REUPGRADE_ID + ".sql"].decode()
    assert len(re.findall(r"(?m)^GRANT EXECUTE ON OBJECT::", text)) == 3
    assert len(re.findall(r"(?m)^DENY ALTER ON OBJECT::", text)) == 3
    returned = files[RETURN_ID + ".sql"].decode()
    assert len(re.findall(r"(?m)^REVOKE (?:EXECUTE|ALTER) ON OBJECT::", returned)) == 6


def test_replaced_baseline_is_not_used_as_a_new_expectation(source, tmp_path):
    archive = tmp_path / "baseline.zip"
    archive.write_bytes(source[0].read_bytes() + b"changed")
    with pytest.raises(ValueError, match="Exact retained predecessor archive"):
        build(archive, source[1])


@pytest.mark.parametrize("damage", ["profile", "after_check", "source"])
def test_changed_source_or_profile_is_refused(source, tmp_path, damage):
    archive, sql = source
    root = tmp_path / "sql"
    profile_path = Path("migrations") / (MIGRATION_ID + ".release.json")
    profile = json.loads((sql / profile_path).read_bytes())
    paths = [profile_path]
    paths += [
        Path("migrations") / item["file"]
        for item in (profile["script"], *profile["checks"].values())
    ]
    paths += [Path(p) for p in profile["source_files"]]
    for path in paths:
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(sql / path, root / path)
    target = {
        "profile": profile_path,
        "after_check": Path("migrations") / profile["checks"]["after"]["file"],
        "source": Path(next(iter(profile["source_files"]))),
    }[damage]
    with (root / target).open("ab") as stream:
        stream.write(b"\n-- changed")
    with pytest.raises(ValueError, match=r"differs|required"):
        build(archive, root)


def test_preparation_never_replaces_an_existing_directory(source, tmp_path):
    output = tmp_path / "retained"
    prepare(*source, output)
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    with pytest.raises(FileExistsError):
        prepare(*source, output)
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}
