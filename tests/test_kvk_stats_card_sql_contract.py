from __future__ import annotations

import os
from pathlib import Path
import re

import pytest

SQL_REPO = Path(os.environ.get("K98_SQL_REPO", r"C:\K98-bot-SQL-Server"))
SQL_SCHEMA = SQL_REPO / "sql_schema"


def _normalise_sql(sql: str) -> str:
    sql = sql.lower().replace("[", "").replace("]", "")
    sql = re.sub(r"\bn'", "'", sql)
    return re.sub(r"\s+", " ", sql).strip()


def _read_sql_file(name: str) -> str:
    path = SQL_SCHEMA / name
    if not path.exists():
        if "K98_SQL_REPO" in os.environ:
            pytest.fail(f"SQL repo file not available: {path}")
        pytest.skip(f"SQL repo file not available: {path}")
    return path.read_text(encoding="utf-8-sig")


def test_overall_kvk_rank_view_contract():
    sql = _normalise_sql(_read_sql_file("KVK.vw_Player_Overall_KVK_Rank.View.sql"))

    assert re.search(r"\bcreate\s+or\s+alter\s+view\s+kvk\.vw_player_overall_kvk_rank\b", sql)
    assert re.search(r"\bfrom\s+kvk\.kvk_player_windowed\s+(?:as\s+)?p\b", sql)
    assert re.search(r"\bwhere\s+p\.windowname\s*=\s*'full'", sql)
    assert re.search(
        r"\brow_number\(\)\s+over\s*\([^)]*partition\s+by\s+p\.kvk_no\s*,\s*p\.windowname",
        sql,
    )
    assert re.search(
        r"\border\s+by\s+p\.kp_gain_recalc\s+desc\s*,\s*p\.governor_id\s+asc",
        sql,
    )
    assert re.search(r"\bas\s+overall_kvk_rank\b", sql)
    assert re.search(r"\bas\s+overall_kvk_total_governors\b", sql)
    assert re.search(r"\bas\s+overall_kvk_top_percent\b", sql)
