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


def test_pending_actions_are_loaded_with_the_scoped_page_without_mutation(contained_job):
    f = contained_job
    store = RecoveryDAL(f.connect, account="test-account", storage_owner="disk", guild_id=2)
    foreign = RecoveryDAL(f.connect, account="other-account", storage_owner="disk", guild_id=2)
    evidence = dict(title="Test", explanation="Fixture", outcome="held", actions={})
    expected = {}
    for owner, state in (
        (store, "dispatched"),
        (store, "unknown"),
        (store, "verified"),
        (foreign, "unknown"),
    ):
        row = owner.observe("stats_import", str(uuid4()), evidence, "a" * 64)
        action, acquired = owner.claim(
            row["IncidentID"], 1, "a" * 64, "release_failure", "discord:1", "fixture"
        )
        assert acquired
        if state != "dispatched":
            owner.finish(row["IncidentID"], action, state, {"fixture": True})
        if owner is store:
            expected[row["IncidentID"]] = (
                dict(state=state, kind="release_failure") if state != "verified" else None
            )
    before = list(
        map(tuple, f.sql.execute("SELECT * FROM #RecoveryAction ORDER BY ActionID").fetchall())
    )
    page = store.report_page()
    assert {r["IncidentID"]: r["pending_action"] for r in page["rows"]} == expected
    after = list(
        map(tuple, f.sql.execute("SELECT * FROM #RecoveryAction ORDER BY ActionID").fetchall())
    )
    assert after == before


@pytest.mark.parametrize("fraction", ["1234000", "1236000"])
def test_report_cutoff_matches_incident_timestamp_precision(contained_job, monkeypatch, fraction):
    f = contained_job
    store = RecoveryDAL(f.connect, account="test-account", storage_owner="disk", guild_id=2)
    evidence = dict(title="Test", explanation="Fixture", outcome="held", actions={})
    row = store.observe("stats_import", str(uuid4()), evidence, "a" * 64)
    instant = "2026-10-17T12:00:00." + fraction
    f.sql.execute(
        "UPDATE #RecoveryIncident SET FirstSeenUTC=CONVERT(datetime2(7),?) WHERE IncidentID=?",
        instant,
        row["IncidentID"],
    )
    f.sql.commit()
    original = fixture.local_sql
    monkeypatch.setattr(
        fixture,
        "local_sql",
        lambda sql: original(sql).replace(
            "SYSUTCDATETIME()", "CONVERT(datetime2(7),'" + instant + "')"
        ),
    )
    page = store.report_page()
    assert page["total"] == 1
    assert [item["IncidentID"] for item in page["rows"]] == [row["IncidentID"]]
    assert page["through"] == page["rows"][0]["FirstSeenUTC"]
