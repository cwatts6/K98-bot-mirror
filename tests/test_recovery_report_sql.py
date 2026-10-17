"""Scoped report paging against authoritative session-local SQL tables."""

from uuid import uuid4

import pytest

from services.recovery_dal import RecoveryDAL
from tests import test_export_target_containment_sql as fixture
from tests.test_export_target_containment_sql import (
    contained_job as contained_job,
    pytestmark as pytestmark,
)


@pytest.fixture(autouse=True)
def report_tables(monkeypatch):
    monkeypatch.setattr(
        fixture, "TABLES", (*fixture.TABLES, "dbo.RecoveryIncident", "dbo.RecoveryAction")
    )


def test_all_states_scope_and_sql_guid_order_are_complete_and_read_only(contained_job):
    f = contained_job
    store = RecoveryDAL(f.connect, account="test-account", storage_owner="disk", guild_id=2)
    foreign = RecoveryDAL(f.connect, account="other-account", storage_owner="disk", guild_id=2)
    evidence = dict(title="Test", explanation="Fixture", outcome="held", actions={})
    identifiers = set()
    for index in range(105):
        row = store.observe(
            "stats_import", str(uuid4()), evidence, "a" * 64, resolved=bool(index % 2)
        )
        identifiers.add(row["IncidentID"])
    outside = foreign.observe("stats_import", str(uuid4()), evidence, "a" * 64)
    before = f.sql.execute(
        "SELECT IncidentID,Revision,LastSeenUTC FROM #RecoveryIncident ORDER BY IncidentID"
    ).fetchall()
    first = store.report_page()
    assert first["total"] == 105 and first["more"] and len(first["rows"]) == 100
    second = store.report_page(after=first["rows"][-1]["IncidentID"], through=first["through"])
    assert second["total"] == 105 and not second["more"] and len(second["rows"]) == 5
    result = first["rows"] + second["rows"]
    assert {r["IncidentID"] for r in result} == identifiers
    assert outside["IncidentID"] not in identifiers
    assert {r["State"] for r in result} == {"open", "resolved"}
    after = f.sql.execute(
        "SELECT IncidentID,Revision,LastSeenUTC FROM #RecoveryIncident ORDER BY IncidentID"
    ).fetchall()
    assert list(map(tuple, before)) == list(map(tuple, after))


def test_new_incidents_do_not_change_existing_report_membership(contained_job):
    f = contained_job
    store = RecoveryDAL(f.connect, account="test-account", storage_owner="disk", guild_id=2)
    first = store.report_page()
    evidence = dict(title="Test", explanation="Fixture", outcome="held", actions={})
    row = store.observe("stats_import", str(uuid4()), evidence, "a" * 64)
    f.sql.execute(
        "UPDATE #RecoveryIncident SET FirstSeenUTC=DATEADD(second,1,?) WHERE IncidentID=?",
        first["through"],
        row["IncidentID"],
    )
    f.sql.commit()
    assert store.report_page(through=first["through"])["total"] == 0
