from __future__ import annotations

import os
from pathlib import Path
import re

import pytest

K98_SQL_REPO_ENV = os.environ.get("K98_SQL_REPO")
SQL_REPO = Path(K98_SQL_REPO_ENV) if K98_SQL_REPO_ENV else Path(r"C:\K98-bot-SQL-Server")
SQL_SCHEMA = SQL_REPO / "sql_schema"


def _running_in_ci() -> bool:
    return any(
        os.environ.get(name)
        for name in ("CI", "GITHUB_ACTIONS", "BUILD_BUILDID", "TF_BUILD")
    )


def _sql_file(name: str) -> str:
    path = SQL_SCHEMA / name
    if not path.exists():
        if _running_in_ci():
            if not K98_SQL_REPO_ENV:
                pytest.fail(
                    "K98_SQL_REPO must be set in CI so SQL contract tests run against "
                    f"the external SQL repository; missing expected file: {path}"
                )
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
        assert "COL_LENGTH" in sql
        assert "WITH VALUES" in sql


def test_recompute_uses_documented_full_data_v2_source_precedence() -> None:
    sql = _compact(_sql_file("KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql"))

    expected_source_expressions = [
        "COALESCE(r.kill_points_diff, r.points_difference, r.max_kill_points - r.min_kill_points, 0)",
        "COALESCE(r.healed_troops, r.max_units_healed_diff, r.max_units_healed - r.min_units_healed, 0)",
        "COALESCE(r.max_contribute_diff, r.max_max_contribute - r.min_max_contribute, 0)",
        "COALESCE(r.cur_contribute_diff, r.max_cur_contribute - r.min_cur_contribute, 0)",
    ]

    for expression in expected_source_expressions:
        assert _compact(expression) in sql


def test_recompute_populates_contribution_outputs_and_rollups() -> None:
    sql = _compact(_sql_file("KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql"))

    required_tokens = [
        "max_contribute_gain, cur_contribute_gain",
        "ISNULL(E.max_contrib_e,0)- ISNULL(S.max_contrib_s,0) AS max_contribute_gain",
        "ISNULL(E.cur_contrib_e,0)- ISNULL(S.cur_contrib_s,0) AS cur_contribute_gain",
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

    tabs = Path("gsheet_module.py").read_text(encoding="utf-8")
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
        "GO",
    ]

    for token in required_tokens:
        assert token in script
