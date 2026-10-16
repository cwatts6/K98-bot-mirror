"""Source-derived finite forms; no runtime receipt, database or provider reads."""

import hashlib
import json
import os
from pathlib import Path
import re

import pytest

from services.export_execution_dal import legacy_definition_hash, validate_legacy_permission_source
from services.export_runtime_composition import verify_legacy_installation_contract
from services.export_sql_direct_permissions import FILE_VISIBILITY_MODULE_HASHES
from tests.test_export_runtime_composition import legacy_permission_fixture

SQL_ROOT = Path(os.environ.get("K98_SQL_SOURCE_ROOT", "C:/K98-bot-SQL-Server"))
CALLER_FORMS = {
    "dbo.sp_Prep_ExcelExportTable",
    "dbo.sp_Prep_ExcelOutputTable",
    "dbo.sp_Prep_TargetTable",
    "dbo.sp_RefreshInactiveGovernors",
}
TYPE_FORMS = CALLER_FORMS | {"dbo.sp_Create_Excel_For_Kvk_Indexes"}
END_FORMS = {"dbo.fn_NormalizeGovernorNameKey", "dbo.usp_RecordKvkFinalReportCompletion"}


def source_definition(raw):
    text = raw.decode("utf-8-sig").replace("\r\n", "\n")
    starts = list(re.finditer(r"^(?:ALTER|CREATE OR ALTER)\s+(?:PROCEDURE|FUNCTION)\b", text, re.M))
    assert len(starts) == 1
    source = re.sub(r"(?im)^GO\s*\Z", "", text[starts[0].start() :]).strip(" \t\r\n")
    return re.sub(r"^(?:ALTER|CREATE OR ALTER)\b", "CREATE", source)


def historical_source_bytes(module, raw, outcome_source):
    """Check the exact forward image before undoing only reviewed amendments.

    Python counterpart of the SQL repo's Test-ExportLegacyModulePermissionContracts.ps1
    and StatsImportOutcome.Source.ps1, keeping pytest independent of PowerShell/Git.
    Neither historical manifests nor runtime allowlists are rewritten.
    """
    name = module["name"]
    if name == "dbo.UPDATE_ALL2":
        validate_legacy_permission_source(outcome_source)
        current = next(m for m in outcome_source["modules"] if m["name"] == name)
        assert hashlib.sha256(raw).hexdigest() == current["source_sha256"], "Outcome source drift"
        assert (
            legacy_definition_hash(source_definition(raw)) == current["definition_sha256"]
        ), "Outcome definition drift"
        text = raw.decode("utf-8").replace("\r\n", "\n")
        text = text.replace(
            "@CompletedFileName [nvarchar](260),\n    @ExportPreparationID uniqueidentifier = NULL",
            "@CompletedFileName [nvarchar](260)",
        )
        for indent, suffix in (("    ", "\n"), ("        ", "")):
            text = re.sub(
                rf"(?ms)^{indent}IF @ExportPreparationID IS NOT NULL\n{indent}BEGIN\n"
                rf".*?^{indent}END;\n{suffix}",
                "",
                text,
            )
        text = text.replace(
            "        DECLARE @S11CompletionCounters TABLE (LastRunCounter int NOT NULL);\n", ""
        ).replace(
            "        OUTPUT inserted.LastRunCounter INTO @S11CompletionCounters (LastRunCounter)\n",
            "",
        )
        text = text.replace(
            "FROM dbo.SP_TaskStatus WITH (UPDLOCK,HOLDLOCK)", "FROM dbo.SP_TaskStatus"
        )
        assert "@ExportPreparationID" not in text and "StatsImportExecution" not in text
        raw = text.replace("\n", "\r\n").encode("utf-8")
    elif name == "dbo.sp_TARGETS_MASTER":
        validate_legacy_permission_source(outcome_source)
        current = next(m for m in outcome_source["modules"] if m["name"] == name)
        text = raw.decode("utf-8").replace("\r\n", "\n")
        assert (
            hashlib.sha256(text.encode()).hexdigest() == current["source_sha256"]
        ), "Atomic configuration source drift"
        assert (
            legacy_definition_hash(source_definition(raw)) == current["definition_sha256"]
        ), "Atomic configuration definition drift"
        text = text.replace(
            "    @RepublishReason [nvarchar](400) = NULL,\n    @ExportPreparationID uniqueidentifier = NULL",
            "    @RepublishReason [nvarchar](400) = NULL",
        ).replace("IF @ExportPreparationID IS NULL AND @@TRANCOUNT <> 0", "IF @@TRANCOUNT <> 0")
        text = re.sub(
            r"(?ms)^    -- Only the typed configuration producer.*?(?=^    DECLARE @RequestedKVK int = @KVK;)",
            "",
            text,
        )
        text = text.replace(
            "        IF @ExportPreparationID IS NOT NULL AND (@@TRANCOUNT <> 1 OR XACT_STATE() <> 1)\n            THROW 52626, 'Atomic configuration publication lost its caller transaction.', 1;\n",
            "",
        )
        assert "@ExportPreparationID" not in text
        raw = text.replace("\n", "\r\n").encode()
    elif name in FILE_VISIBILITY_MODULE_HASHES:
        assert (
            legacy_definition_hash(source_definition(raw)) == FILE_VISIBILITY_MODULE_HASHES[name]
        ), "File visibility definition drift"
        text = re.sub(
            r"SET (@\w+) = COALESCE\(\(SELECT file_exists FROM sys\.dm_os_file_exists\((@\w+)\)\), 0\);",
            r"EXEC master.dbo.xp_fileexist \2, \1 OUTPUT;",
            raw.decode("utf-8").replace("\r\n", "\n"),
        )
        raw = text.replace("\n", "\r\n").encode("utf-8")
    assert hashlib.sha256(raw).hexdigest() == module["source_sha256"], "Historical source drift"
    return raw


@pytest.fixture
def permission_sources():
    if not SQL_ROOT.is_dir():
        pytest.skip("Separate authoritative SQL checkout required")
    historical = json.loads(
        (SQL_ROOT / "deploy/export_legacy_module_permission_manifest.json").read_bytes()
    )
    outcome = json.loads((SQL_ROOT / "deploy/export_stats_import_outcome_source.json").read_bytes())
    validate_legacy_permission_source(historical)
    validate_legacy_permission_source(outcome)
    return historical, outcome


def tokens(text):
    """Comparison aid only; preserve strings, quoted identifiers and operators."""
    result = []
    i = 0
    while i < len(text):
        if text[i].isspace():
            i += 1
        elif text.startswith("--", i):
            end = text.find("\n", i)
            i = len(text) if end < 0 else end + 1
        elif text.startswith("/*", i):
            depth = 1
            i += 2
            while depth:
                assert i < len(text)
                if text.startswith("/*", i):
                    depth += 1
                    i += 2
                elif text.startswith("*/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
        elif text[i] in "'\"[":
            start = i
            close = "]" if text[i] == "[" else text[i]
            i += 1
            while True:
                assert i < len(text)
                if text[i] == close:
                    i += 1
                    if i < len(text) and text[i] == close:
                        i += 1
                    else:
                        break
                else:
                    i += 1
            result.append(text[start:i])
        else:
            match = re.match(r"[\w@$#]+|<>|!=|>=|<=|!<|!>|\+=|-=|\*=|/=|%=|&=|\^=|\|=|.", text[i:])
            assert match
            result.append(match[0])
            i += len(match[0])
    return result


def equivalent_tokens(name, text):
    if name not in TYPE_FORMS | END_FORMS:
        return tokens(text)
    header, body = text.split("\nAS\n", 1)
    if name in CALLER_FORMS:
        header = header.replace("\nWITH EXECUTE AS CALLER", "")
    header_tokens = tokens(header)
    if name in TYPE_FORMS:
        header_tokens = [
            (
                t.strip("[]").lower()
                if t.lower() in {"int", "[int]", "nvarchar", "[nvarchar]", "sysname", "[sysname]"}
                else t
            )
            for t in header_tokens
        ]
    body_tokens = tokens(body)
    if name in END_FORMS and body_tokens[-1] == ";":
        assert body_tokens[-2] == "END"
        body_tokens.pop()
    return header_tokens, body_tokens


def test_all_finite_forms_are_reconstructed_from_authoritative_source(permission_sources):
    manifest, outcome = permission_sources
    forms_bytes = (SQL_ROOT / manifest["compatibility_forms"]).read_bytes()
    assert hashlib.sha256(forms_bytes).hexdigest() == manifest["compatibility_forms_sha256"]
    forms = json.loads(forms_bytes)["forms"]
    assert len(forms) == len({f["module"] for f in forms}) == 27
    modules = {m["name"]: m for m in manifest["modules"]}
    assert len(modules) == 38
    # Check all 38 historical byte pins, including amended modules without a recipe.
    sources = {
        name: source_definition(
            historical_source_bytes(module, (SQL_ROOT / module["path"]).read_bytes(), outcome)
        )
        for name, module in modules.items()
    }
    for name, module in modules.items():
        assert legacy_definition_hash(sources[name]) == module["definition_sha256"]
    for form in forms:
        module = modules[form["module"]]
        source = sources[module["name"]]
        assert (
            legacy_definition_hash(source)
            == module["definition_sha256"]
            == form["source_definition_sha256"]
        )
        lines = source.splitlines(keepends=True)
        for edit in reversed(form["edits"]):
            start = edit["start"]
            assert lines[start : start + len(edit["before"])] == edit["before"]
            lines[start : start + len(edit["before"])] = edit["after"]
        variant = "".join(lines)
        assert equivalent_tokens(module["name"], source) == equivalent_tokens(
            module["name"], variant
        )
        assert [legacy_definition_hash(variant)] == module["compatible_definition_sha256"]
        if module["name"] in CALLER_FORMS:
            assert module["execute_as"] is None
        for path in (
            "migrations/20260924_002_export_legacy_module_permissions.sql",
            "migrations/rollback/20260924_002_export_legacy_module_permissions_rollback.sql",
            "validation/kvk_source/s11_export_legacy_module_permissions.sql",
        ):
            assert f"(N'{module['name']}',0x{legacy_definition_hash(variant)})" in (
                SQL_ROOT / path
            ).read_text(encoding="utf-8-sig")


@pytest.mark.parametrize(
    "name", ["dbo.UPDATE_ALL2", "dbo.sp_TARGETS_MASTER", *FILE_VISIBILITY_MODULE_HASHES]
)
def test_amendment_reconstruction_rejects_changed_forward_image(permission_sources, name):
    manifest, outcome = permission_sources
    module = next(m for m in manifest["modules"] if m["name"] == name)
    raw = (SQL_ROOT / module["path"]).read_bytes()
    # Damage the added code itself, which inversion would otherwise remove.
    before, after = (
        (b"State='completed',", b"State='partial',")
        if name == "dbo.UPDATE_ALL2"
        else (b"SELECT file_exists FROM", b"SELECT file_is_a_directory FROM")
    )
    if name == "dbo.sp_TARGETS_MASTER":
        before, after = b"THROW 52625", b"PRINT 52625"
    assert before in raw
    with pytest.raises(
        AssertionError,
        match=r"Outcome source drift|File visibility definition drift|Atomic configuration source drift",
    ):
        historical_source_bytes(module, raw.replace(before, after, 1), outcome)


def test_amendment_reconstruction_rejects_resealed_outcome_manifest(permission_sources):
    from copy import deepcopy

    from kvk.dal.new_source_import_dal import SourceConflict

    manifest, outcome = permission_sources
    module = next(m for m in manifest["modules"] if m["name"] == "dbo.UPDATE_ALL2")
    raw = (
        (SQL_ROOT / module["path"]).read_bytes().replace(b"State='completed',", b"State='partial',")
    )
    changed = deepcopy(outcome)
    current = next(m for m in changed["modules"] if m["name"] == module["name"])
    current["source_sha256"] = hashlib.sha256(raw).hexdigest()
    current["definition_sha256"] = legacy_definition_hash(source_definition(raw))
    with pytest.raises(SourceConflict, match="Exact reviewed legacy SQL source manifest required"):
        historical_source_bytes(module, raw, changed)


@pytest.mark.parametrize(
    "name", ["dbo.UPDATE_ALL2", "dbo.sp_TARGETS_MASTER", *FILE_VISIBILITY_MODULE_HASHES]
)
def test_amendment_reconstruction_preserves_exact_historical_byte_pin(permission_sources, name):
    manifest, outcome = permission_sources
    module = next(m for m in manifest["modules"] if m["name"] == name)
    raw = (SQL_ROOT / module["path"]).read_bytes()
    with pytest.raises(AssertionError, match="Historical source drift"):
        historical_source_bytes(module | {"source_sha256": "0" * 64}, raw, outcome)


def compatibility_fixture(monkeypatch):
    from kvk.dal.new_source_import_dal import digest
    import services.export_execution_dal as dal

    observed, approved = legacy_permission_fixture(monkeypatch)
    variant = "CREATE   PROCEDURE dbo.UPDATE_ALL2 AS SELECT 1;"
    approved["source"]["modules"][0]["compatible_definition_sha256"] = [
        legacy_definition_hash(variant)
    ]
    monkeypatch.setattr(dal, "LEGACY_PERMISSION_SOURCE_HASH", digest(approved["source"]).hex())
    observed["modules"][0]["ModuleDefinition"] = variant
    approved["metadata_hash"] = digest(observed).hex()
    return observed, approved


def test_exact_compatible_form_passes_with_all_existing_permission_checks(monkeypatch):
    observed, approved = compatibility_fixture(monkeypatch)
    verify_legacy_installation_contract(observed, approved)


@pytest.mark.parametrize(
    "replacement",
    [
        "CREATE   PROCEDURE dbo.UPDATE_ALL2 AS SELECT 3;",
        "CREATE   PROCEDURE dbo.UPDATE_ALL2 AS SELECT '1';",
        "CREATE    PROCEDURE dbo.UPDATE_ALL2 AS SELECT 1;",
        "CREATE   PROCEDURE dbo.child AS SELECT 1;",
    ],
)
def test_compatible_form_does_not_accept_new_body_or_unlisted_format(monkeypatch, replacement):
    from kvk.dal.new_source_import_dal import SourceConflict

    observed, approved = compatibility_fixture(monkeypatch)
    observed["modules"][0]["ModuleDefinition"] = replacement
    with pytest.raises(SourceConflict):
        verify_legacy_installation_contract(observed, approved)


@pytest.mark.parametrize(
    "field,value",
    [("OwnerName", "other"), ("ExecuteAsPrincipal", -2), ("AnsiNulls", 0), ("QuotedIdentifier", 0)],
)
def test_compatible_form_preserves_module_metadata_refusal(monkeypatch, field, value):
    from kvk.dal.new_source_import_dal import SourceConflict

    observed, approved = compatibility_fixture(monkeypatch)
    observed["modules"][0][field] = value
    with pytest.raises(SourceConflict):
        verify_legacy_installation_contract(observed, approved)


def test_compatible_form_preserves_exact_signature_refusal(monkeypatch):
    from kvk.dal.new_source_import_dal import SourceConflict

    observed, approved = compatibility_fixture(monkeypatch)
    observed["signatures"][0]["SignatureHash"] = "f" * 64
    with pytest.raises(SourceConflict):
        verify_legacy_installation_contract(observed, approved)


@pytest.mark.skipif(not SQL_ROOT.is_dir(), reason="Separate authoritative SQL checkout required")
def test_historical_conduct_layout_keeps_stats_candidate_projection_aligned():
    table = (SQL_ROOT / "sql_schema/dbo.STATS_FOR_UPLOAD.Table.sql").read_text(encoding="utf-8-sig")
    columns = re.findall(r"^\s*\[([^\]]+)\]\s+\[", table, re.M)
    assert len(columns) == 62 and columns[18] == "Conduct"
    historical = (SQL_ROOT / "migrations/20260615_001_add_conduct_reporting_field.sql").read_text(
        encoding="utf-8-sig"
    )
    assert "ALTER TABLE dbo.STATS_FOR_UPLOAD" in historical
    assert "ALTER TABLE dbo.STATS_FOR_UPLOAD ADD [Conduct] decimal(5,2) NULL;" in historical
    appended = [c for c in columns if c != "Conduct"] + ["Conduct"]
    assert appended[61] == "Conduct" and set(appended) == set(columns)
    # Candidate inherits the actual table order. Its population uses named
    # columns, then the unchanged same-shape candidate is copied to its parent.
    procedure = (SQL_ROOT / "sql_schema/dbo.SP_Stats_for_Upload.StoredProcedure.sql").read_text(
        encoding="utf-8-sig"
    )
    assert re.search(
        r"SELECT TOP \(0\) \*\s+INTO #StatsForUploadCandidate\s+FROM dbo.STATS_FOR_UPLOAD",
        procedure,
    )
    assert re.search(r"INSERT INTO #StatsForUploadCandidate\s*\(", procedure)
    assert re.search(
        r"INSERT INTO dbo.STATS_FOR_UPLOAD\s+SELECT \*\s+FROM #StatsForUploadCandidate", procedure
    )
