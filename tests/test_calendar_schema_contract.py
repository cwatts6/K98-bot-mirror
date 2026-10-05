from __future__ import annotations

from pathlib import Path


def test_calendar_schema_sql_exists_and_contains_required_objects():
    p = Path("sql/calendar_schema.sql")
    assert p.exists(), "Expected sql/calendar_schema.sql to exist"

    text = p.read_text(encoding="utf-8")

    required_fragments = [
        "CREATE TABLE dbo.EventRecurringRules",
        "CREATE TABLE dbo.EventOneOffEvents",
        "CREATE TABLE dbo.EventOverrides",
        "CREATE TABLE dbo.EventInstances",
        "CREATE TABLE dbo.EventSyncLog",
        "IX_EventInstances_StartUTC",
        "IX_EventInstances_EventType",
        "IX_EventInstances_SourceID",
        "VARBINARY(32)",
    ]
    for frag in required_fragments:
        assert frag in text, f"Missing fragment: {frag}"
