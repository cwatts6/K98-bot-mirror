from __future__ import annotations

import os
from pathlib import Path
import re

import pytest


SQL_REPO = Path(os.environ.get("K98_SQL_REPO", r"C:\K98-bot-SQL-Server"))
SQL_SCHEMA = SQL_REPO / "sql_schema"


def _normalise_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", sql).strip().lower()


def _read_sql_file(name: str) -> str:
    path = SQL_SCHEMA / name
    if not path.exists():
        if "K98_SQL_REPO" in os.environ:
            pytest.fail(f"SQL repo file not available: {path}")
        pytest.skip(f"SQL repo file not available: {path}")
    return path.read_text(encoding="utf-8-sig")


def test_overall_kvk_rank_view_contract():
    sql = _normalise_sql(_read_sql_file("KVK.vw_Player_Overall_KVK_Rank.View.sql"))

    assert "create or alter view [kvk].[vw_player_overall_kvk_rank]" in sql
    assert "from kvk.kvk_player_windowed as p" in sql
    assert "where p.windowname = n'full'" in sql
    assert "row_number() over" in sql
    assert "partition by p.kvk_no, p.windowname" in sql
    assert "order by p.kp_gain_recalc desc, p.governor_id asc" in sql
    assert "as overall_kvk_rank" in sql
    assert "as overall_kvk_total_governors" in sql
    assert "as overall_kvk_percentile" in sql
