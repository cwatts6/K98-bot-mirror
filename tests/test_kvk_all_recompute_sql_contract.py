from __future__ import annotations

import os
from pathlib import Path
import re

import pytest

K98_SQL_REPO_ENV = os.environ.get("K98_SQL_REPO")
SQL_REPO = Path(K98_SQL_REPO_ENV) if K98_SQL_REPO_ENV else Path(r"C:\K98-bot-SQL-Server")
SQL_SCHEMA = SQL_REPO / "sql_schema"
# Phase 10 recompute switched configured-window KP gain to endpoint delta logic and
# introduced this alias in both canonical and deployment-script definitions.
PHASE_10_RECOMPUTE_SENTINEL = "r.max_kill_points AS kp_endpoint_s"


def _running_in_ci() -> bool:
    return any(
        os.environ.get(name) for name in ("CI", "GITHUB_ACTIONS", "BUILD_BUILDID", "TF_BUILD")
    )


def _sql_file(name: str) -> str:
    path = SQL_SCHEMA / name
    if not path.exists():
        if not K98_SQL_REPO_ENV:
            pytest.skip(
                "SQL contract tests require the external SQL repository; "
                f"set K98_SQL_REPO to enable them. Missing expected file: {path}"
            )
        if _running_in_ci():
            pytest.fail(f"SQL repo file not available in CI: {path}")
        pytest.skip(f"SQL repo file not available: {path}")
    return path.read_text(encoding="utf-8")


def _compact(sql: str) -> str:
    """Collapse whitespace and normalise spacing around SQL operators/punctuation.

    * Collapses all whitespace runs to a single space.
    * Strips spaces around ``-``, ``+``, and ``,`` (arithmetic operators / argument
      separators), so ``a - b`` and ``a-b`` are treated identically.
    * Strips the space *after* ``(`` and *before* ``)`` so that
      ``COALESCE( x, y )`` normalises to ``COALESCE(x,y)`` while
      ``func(…) AS alias`` is unaffected (space after ``)`` is preserved).
    * ``*`` is intentionally excluded so that ``SELECT *`` detection still works.
    """
    sql = re.sub(r"\s+", " ", sql)
    sql = re.sub(r" *([-+,]) *", r"\1", sql)
    sql = re.sub(r"\( *", "(", sql)
    sql = re.sub(r" *\)", ")", sql)
    return sql.strip()


def _phase10_recompute_sql_contract_source() -> str:
    canonical = _compact(_sql_file("KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql"))
    # Canonical SQL repo may lag deployment scripts; fall back to the PR deployment
    # script when this Phase 10 endpoint-source token is absent.
    if PHASE_10_RECOMPUTE_SENTINEL in canonical:
        return canonical
    sql_repo_script = SQL_SCHEMA / "kvk_all_phase10_recompute_correctness.sql"
    if sql_repo_script.exists():
        return _compact(sql_repo_script.read_text(encoding="utf-8-sig"))
    return _compact(
        Path("sql/kvk_all_phase10_recompute_correctness.sql").read_text(encoding="utf-8-sig")
    )


def test_phase4_metric_source_rules_are_documented() -> None:
    doc = Path("docs/KVK_ALL Schema Modernisation - Phase 4 Metric Source Rules.md")
    text = doc.read_text(encoding="utf-8")

    required_tokens = [
        "`kill_points_diff` is the Full Data v2 semantic source",
        "`points_difference` is retained as the legacy compatibility field",
        "`healed_troops` is the Full Data v2 semantic source",
        "`max_units_healed_diff` is retained as the legacy compatibility field",
        "`max_contribute_gain`",
        "`cur_contribute_gain`",
        "They are not added to Discord reporting display, Google Sheets tab names, or export result-set ordering",
    ]

    for token in required_tokens:
        assert token in text


def test_phase10_metric_source_correction_is_documented() -> None:
    doc = Path("docs/KVK_ALL Schema Modernisation - Phase 10 Metric Source Correction.md")
    text = doc.read_text(encoding="utf-8")

    required_tokens = [
        "configured windows such as Pass 4 use cumulative\nendpoint deltas",
        "`End.max_kill_points - Start.max_kill_points`",
        "Legacy diff fields remain fallback inputs",
        "Zero diff fields are not authoritative for Full Data v2 configured windows",
        "`Full` output rows represent baseline-to-latest values",
        "Older 22-column Full Data workbooks do not contain raw endpoint families",
    ]

    for token in required_tokens:
        assert token in text


def test_windowed_tables_add_contribution_columns_additively() -> None:
    table_files = [
        "KVK.KVK_Player_Windowed.Table.sql",
        "KVK.KVK_Kingdom_Windowed.Table.sql",
        "KVK.KVK_Camp_Windowed.Table.sql",
    ]

    for file_name in table_files:
        sql = _sql_file(file_name)
        assert "[max_contribute_gain] [bigint] NOT NULL" in sql
        assert "[cur_contribute_gain] [bigint] NOT NULL" in sql


def test_recompute_uses_documented_full_data_v2_source_precedence() -> None:
    sql = _phase10_recompute_sql_contract_source()

    expected_source_expressions = [
        "r.max_kill_points AS kp_endpoint_s",
        "r.max_kill_points AS kp_endpoint_e",
        "COALESCE(r.kill_points_diff, r.points_difference, 0) AS kp_legacy_s",
        "COALESCE(r.kill_points_diff, r.points_difference, 0) AS kp_legacy_e",
        "r.max_units_healed AS heals_endpoint_s",
        "r.max_units_healed AS heals_endpoint_e",
        "COALESCE(r.healed_troops, r.max_units_healed_diff, 0) AS heals_legacy_s",
        "COALESCE(r.healed_troops, r.max_units_healed_diff, 0) AS heals_legacy_e",
        "CASE WHEN E.kp_endpoint_e IS NOT NULL AND S.kp_endpoint_s IS NOT NULL THEN E.kp_endpoint_e - S.kp_endpoint_s ELSE ISNULL(E.kp_legacy_e,0) - ISNULL(S.kp_legacy_s,0) END AS kp_gain",
        "CASE WHEN E.max_contrib_endpoint_e IS NOT NULL AND S.max_contrib_endpoint_s IS NOT NULL THEN E.max_contrib_endpoint_e - S.max_contrib_endpoint_s ELSE ISNULL(E.max_contrib_legacy_e,0) - ISNULL(S.max_contrib_legacy_s,0) END AS max_contribute_gain",
    ]

    for expression in expected_source_expressions:
        assert _compact(expression) in sql


def test_recompute_full_row_uses_baseline_to_latest_endpoint_delta() -> None:
    sql = _phase10_recompute_sql_contract_source()

    required_tokens = [
        "SELECT governor_id,baseline_scan_id,starting_power",
        "AND r.ScanID = B.baseline_scan_id",
        "CASE WHEN E.max_kill_points IS NOT NULL AND S.max_kill_points IS NOT NULL THEN E.max_kill_points-S.max_kill_points ELSE E.legacy_kp END AS kp",
        "CASE WHEN E.max_kills_iv IS NOT NULL AND S.max_kills_iv IS NOT NULL THEN E.max_kills_iv-S.max_kills_iv ELSE E.legacy_t4 END AS t4",
        "CASE WHEN E.max_kills_v IS NOT NULL AND S.max_kills_v IS NOT NULL THEN E.max_kills_v-S.max_kills_v ELSE E.legacy_t5 END AS t5",
        "CASE WHEN E.max_dead IS NOT NULL AND S.max_dead IS NOT NULL THEN E.max_dead-S.max_dead ELSE E.legacy_deads END AS deads",
        "CASE WHEN E.max_units_healed IS NOT NULL AND S.max_units_healed IS NOT NULL THEN E.max_units_healed-S.max_units_healed ELSE E.legacy_heals END AS heals",
    ]

    for token in required_tokens:
        assert _compact(token) in sql


def test_phase10_prod_sql_script_contains_recompute_correctness_fix() -> None:
    script = Path("sql/kvk_all_phase10_recompute_correctness.sql").read_text(encoding="utf-8-sig")
    compact = _compact(script)

    required_tokens = [
        "KVK_ALL Schema Modernisation - Phase 10 Recompute Correctness",
        "ALTER PROCEDURE [KVK].[sp_KVK_Recompute_Windows]",
        "AND w.StartScanID <= @MaxScanID",
        "r.max_kill_points AS kp_endpoint_s",
        "COALESCE(r.kill_points_diff, r.points_difference, 0) AS kp_legacy_s",
        "THEN E.kp_endpoint_e - S.kp_endpoint_s",
        "ELSE E.legacy_kp END AS kp",
        "max_contribute_gain",
        "cur_contribute_gain",
        "GO",
    ]

    for token in required_tokens:
        assert _compact(token) in compact


def test_recompute_populates_contribution_outputs_and_rollups() -> None:
    sql = _phase10_recompute_sql_contract_source()

    required_tokens = [
        "max_contribute_gain, cur_contribute_gain",
        "THEN E.max_contrib_endpoint_e-S.max_contrib_endpoint_s",
        "ELSE ISNULL(E.max_contrib_legacy_e,0)-ISNULL(S.max_contrib_legacy_s,0) END AS max_contribute_gain",
        "THEN E.cur_contrib_endpoint_e-S.cur_contrib_endpoint_s",
        "ELSE ISNULL(E.cur_contrib_legacy_e,0)-ISNULL(S.cur_contrib_legacy_s,0) END AS cur_contribute_gain",
        "SUM(p.max_contribute_gain) AS max_contribute_gain",
        "SUM(p.cur_contribute_gain) AS cur_contribute_gain",
        "K.max_contribute_gain, K.cur_contribute_gain",
        "C.max_contribute_gain, C.cur_contribute_gain",
    ]

    for token in required_tokens:
        assert _compact(token) in sql


def test_export_contract_keeps_ten_result_sets_and_no_full_select_star() -> None:
    sql = _sql_file("KVK.sp_KVK_Get_Exports.StoredProcedure.sql")
    compact = _compact(sql)

    for section in range(1, 11):
        assert f"-- {section})" in sql
    assert "-- 11)" not in sql
    assert "SELECT * FROM KVK.KVK_Player_Windowed" not in compact
    assert "SELECT * FROM KVK.KVK_Kingdom_Windowed" not in compact
    assert "SELECT * FROM KVK.KVK_Camp_Windowed" not in compact
    assert compact.count("max_contribute_gain,cur_contribute_gain") >= 6

    tabs = Path("gsheet_module.py").read_text(encoding="utf-8") + Path(
        "kvk/services/kvk_export_service.py"
    ).read_text(encoding="utf-8")
    for tab in (
        "KVK_Scan_Log",
        "KVK_Windows",
        "KVK_DKP_Weights",
        "KVK_Player_Windowed",
        "KVK_Kingdom_Windowed",
        "KVK_Camp_Windowed",
        "KVK_Player_Full",
        "KVK_Kingdom_Full",
        "KVK_Camp_Full",
        "KVK_Ingest_Negatives",
    ):
        assert f'"{tab}"' in tabs


def test_phase4_prod_sql_script_contains_all_changed_sql_objects() -> None:
    script = Path("sql/kvk_all_phase4_recompute_modernisation.sql").read_text(encoding="utf-8-sig")

    required_tokens = [
        "KVK_ALL Schema Modernisation - Phase 4 Recompute Modernisation",
        "KVK.KVK_Player_Windowed.Table.sql",
        "KVK.KVK_Kingdom_Windowed.Table.sql",
        "KVK.KVK_Camp_Windowed.Table.sql",
        "KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql",
        "KVK.sp_KVK_Get_Exports.StoredProcedure.sql",
        "ALTER PROCEDURE [KVK].[sp_KVK_Recompute_Windows]",
        "ALTER PROCEDURE [KVK].[sp_KVK_Get_Exports]",
        "max_contribute_gain",
        "cur_contribute_gain",
        "COL_LENGTH('KVK.KVK_Player_Windowed', 'max_contribute_gain')",
        "COL_LENGTH('KVK.KVK_Kingdom_Windowed', 'max_contribute_gain')",
        "COL_LENGTH('KVK.KVK_Camp_Windowed', 'max_contribute_gain')",
        "WITH VALUES",
        "GO",
    ]

    for token in required_tokens:
        assert token in script


def test_phase5_prod_sql_script_contains_export_contract_changes() -> None:
    script = Path("sql/kvk_all_phase5_export_contract_decoupling.sql").read_text(
        encoding="utf-8-sig"
    )

    required_tokens = [
        "KVK_ALL Schema Modernisation - Phase 5 Export Contract Decoupling",
        "ALTER PROCEDURE [KVK].[sp_KVK_Get_Exports]",
        "max_contribute_gain",
        "cur_contribute_gain",
        "-- 10) Negative Corrections",
        "GO",
    ]

    for token in required_tokens:
        assert token in script


def test_phase8_sql_repo_contains_diagnostic_and_cleanup_contract() -> None:
    stage_sql = _sql_file("KVK.KVK_AllPlayers_Stage.Table.sql")
    diagnostics_sql = _sql_file("KVK.KVK_Ingest_Diagnostics.Table.sql")
    cleanup_sql = _sql_file("KVK.sp_KVK_Ingest_Cleanup.StoredProcedure.sql")

    assert "[staged_at_utc] [datetime2](0) NOT NULL" in stage_sql
    assert "DF_KVK_AllPlayers_Stage_StagedAtUTC" in stage_sql
    assert "IX_KVK_AllPlayers_Stage_StagedAt" in stage_sql
    assert "INCLUDE([IngestToken])" in stage_sql

    for token in (
        "CREATE TABLE [KVK].[KVK_Ingest_Diagnostics]",
        "[DiagnosticStatus] [varchar](20)",
        "[DiagnosticType] [nvarchar](64)",
        "[IngestToken] [uniqueidentifier] NULL",
        "[SchemaVersion] [nvarchar](64)",
        "[SourceSheetName] [nvarchar](128)",
        "[SourceColumnHash] [char](64)",
        "[ContextJson] [nvarchar](max)",
        "CK_KVK_IngestDiag_Status",
        "IX_KVK_IngestDiag_Status_Created",
        "IX_KVK_IngestDiag_Token",
        "IX_KVK_IngestDiag_Created",
    ):
        assert token in diagnostics_sql

    compact_cleanup = _compact(cleanup_sql)
    for token in (
        "ALTER PROCEDURE [KVK].[sp_KVK_Ingest_Cleanup]",
        "@StageRetentionHours [int] = 24",
        "@DiagnosticRetentionDays [int] = 90",
        "@NegativeRetentionDays [int] = 365",
        "@DryRun [bit] = 1",
        "THROW 51010, 'Stage retention must be at least 1 hour.', 1",
        "WHERE staged_at_utc < @StageCutoff",
        "WHERE CreatedUTC < @DiagnosticCutoff",
        "WHERE recorded_at_utc < @NegativeCutoff",
        "DiagnosticStatus, DiagnosticType, ErrorText, ContextJson",
        "StaleStageRows",
        "StaleDiagnosticRows",
        "StaleNegativeRows",
    ):
        assert _compact(token) in compact_cleanup


def test_phase8_prod_sql_script_contains_retention_objects_and_policy() -> None:
    script = Path("sql/kvk_all_phase8_ingest_retention.sql").read_text(encoding="utf-8-sig")
    compact = _compact(script)

    required_tokens = [
        "KVK_ALL Schema Modernisation - Phase 8 Ingest Diagnostics & Retention",
        "IF OBJECT_ID(N'[KVK].[KVK_AllPlayers_Stage]', N'U') IS NULL",
        "COL_LENGTH('KVK.KVK_AllPlayers_Stage', 'staged_at_utc')",
        "CREATE TABLE [KVK].[KVK_Ingest_Diagnostics]",
        "CK_KVK_IngestDiag_Status",
        "IX_KVK_IngestDiag_Status_Created",
        "IX_KVK_IngestDiag_Token",
        "IX_KVK_IngestDiag_Created",
        "ALTER PROCEDURE [KVK].[sp_KVK_Ingest_Cleanup]",
        "@StageRetentionHours [int] = 24",
        "@DiagnosticRetentionDays [int] = 90",
        "@NegativeRetentionDays [int] = 365",
        "@DryRun [bit] = 1",
        "WHERE staged_at_utc < @StageCutoff",
        "WHERE CreatedUTC < @DiagnosticCutoff",
        "WHERE recorded_at_utc < @NegativeCutoff",
        "GO",
    ]

    for token in required_tokens:
        assert _compact(token) in compact
