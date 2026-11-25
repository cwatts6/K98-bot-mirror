"""Opt-in engine tests using uniquely named global temporary tables only.

No database or persistent object is created, altered or dropped. The owner
connection keeps these disposable tempdb tables alive until the fixture ends.
"""

from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import re
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit
from services.recovery_dal import RecoveryDAL

pytestmark = pytest.mark.skipif(
    os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1",
    reason="Requires explicit local temporary-table SQL test opt-in",
)


@pytest.fixture
def store():
    import pyodbc

    names = {
        f"dbo.Recovery{kind}": f"##K98Recovery_{uuid4().hex}_{kind}"
        for kind in ("Incident", "Action", "InputDraft")
    }

    def rewrite(sql):
        for source, target in names.items():
            sql = sql.replace(source, target)
        return sql

    # Fixed local development endpoint, integrated auth; never environment-derived production.
    connection_string = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\\K98DEV;DATABASE=master;Trusted_Connection=yes;TrustServerCertificate=yes"
    owner = pyodbc.connect(connection_string, autocommit=True, timeout=5)
    schema = Path(os.environ["K98_RECOVERY_SQL_SCHEMA"])
    for kind in ("Incident", "Action", "InputDraft"):
        sql = (schema / f"dbo.Recovery{kind}.Table.sql").read_text(encoding="utf-8-sig")
        # SQL Server does not enforce FKs for temporary tables. Persistent FK is
        # covered by source validation; all other table constraints run here.
        sql = re.sub(
            r"^\s*CONSTRAINT FK_Recovery(?:Action|InputDraft)_Incident[^\n]*\n",
            "",
            sql,
            flags=re.M,
        )
        sql = re.sub(r"CONSTRAINT (\w+)", lambda m: "CONSTRAINT " + m[1] + "_" + uuid4().hex, sql)
        owner.execute(rewrite(sql))

    class Cursor:
        def __init__(self, inner):
            self.inner = inner

        def execute(self, sql, *args):
            self.inner.execute(rewrite(sql), *args)
            return self

        def __getattr__(self, name):
            return getattr(self.inner, name)

    class Connection:
        def __init__(self):
            self.inner = pyodbc.connect(connection_string, autocommit=False, timeout=5)
            self.inner.timeout = 5

        def cursor(self):
            return Cursor(self.inner.cursor())

        def __getattr__(self, name):
            return getattr(self.inner, name)

    dal = RecoveryDAL(Connection, account="test-account", storage_owner="test-disk", guild_id=2)
    try:
        yield dal
    finally:
        owner.close()  # SQL Server removes only these session-owned temp objects.


def test_large_export_incident_preserves_all_guided_links_and_failure_diagnostic(store):
    evidence = dict(
        title="Replacement",
        explanation="Review the supplied output roles",
        actions={},
        targets=[f"old-{i:04}-" + "x" * 100 for i in range(1024)],
    )
    row = store.observe("export_job", str(uuid4()), evidence, "a" * 64)
    assert row["evidence"] == evidence
    store.check_failed(row["IncidentID"], "SourceConflict")
    restored = store.get(row["IncidentID"])["evidence"]
    assert restored["targets"] == evidence["targets"]
    assert restored["check_unavailable"] == "SourceConflict"
    with pytest.raises(ValueError, match="bound"):
        store.observe("stats_import", str(uuid4()), evidence, "b" * 64)
    with pytest.raises(ValueError, match="bound"):
        store.observe("export_job", str(uuid4()), dict(evidence, padding="x" * 1048576), "c" * 64)


def incident(store):
    return store.observe("stats_import", str(uuid4()), {"actions": {}}, "a" * 64)


def test_latest_publication_action_is_scoped_and_report_retains_terminal_failure(store):
    evidence = {"actions": {"verify_publication": {}}}
    row = store.observe("export_job", str(uuid4()), evidence, "a" * 64, resolved=True)
    first, _ = store.claim(
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "verify_publication",
        "discord:1",
        "fixture",
    )
    store.finish(row["IncidentID"], first, "verified", {"verification": "verified"})
    row = store.observe("export_job", row["SourceID"], evidence, "b" * 64, resolved=True)
    second, _ = store.claim(
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "verify_publication",
        "discord:1",
        "fixture",
    )
    store.finish(row["IncidentID"], second, "not_applied", {"verification": "not_applied"})
    latest = store.latest_publication_action(row["IncidentID"])
    assert str(latest["ActionID"]).lower() == second
    assert latest["State"] == "not_applied"
    page = store.report_page()
    assert page["rows"][0]["publication_check"]["outcome"] == "not_verified"
    foreign = RecoveryDAL(store.connect, account="foreign", storage_owner="disk", guild_id=2)
    with pytest.raises(SourceConflict, match="scope"):
        foreign.latest_publication_action(row["IncidentID"])
    assert not foreign.report_page()["rows"]


@pytest.mark.parametrize("outcome", ["not_applied", "unknown", "verified"])
def test_only_verified_nonapplication_opens_one_fresh_admin_decision(store, outcome):
    row = incident(store)
    action, acquired = store.claim(
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "verify_publication",
        "discord:1",
        "Check original outcome",
    )
    assert acquired
    store.finish(row["IncidentID"], action, outcome, {"verification": outcome})
    current = store.get(row["IncidentID"])
    assert current["Revision"] == row["Revision"] + (outcome == "not_applied")
    assert current["EvidenceHash"] == row["EvidenceHash"]
    if outcome == "not_applied":
        store.finish(row["IncidentID"], action, outcome, {"verification": outcome})
        assert store.get(row["IncidentID"])["Revision"] == current["Revision"]
    assert not store.claim(
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "verify_publication",
        "discord:1",
        "Old confirmation",
    )[1]
    _, new = store.claim(
        current["IncidentID"],
        current["Revision"],
        current["EvidenceHash"],
        "isolate_targets",
        "discord:1",
        "Reviewed separate disposition",
    )
    assert new is (outcome == "not_applied")


def test_bounded_check_diagnostic_survives_restart_without_revision_churn(store):
    row = incident(store)
    detail = dict(
        error_type="ValueError",
        stage="incident:stats_import",
        frames=[dict(file="adapter.py", line=42, function="inspect")],
        observed_utc="first",
    )
    store.check_failed(row["IncidentID"], detail)
    restarted = RecoveryDAL(
        store.connect, account="test-account", storage_owner="test-disk", guild_id=2
    )
    failed = restarted.get(row["IncidentID"])
    assert failed["evidence"]["check_diagnostic"] == detail
    restarted.check_failed(row["IncidentID"], dict(detail, observed_utc="later"))
    assert restarted.get(row["IncidentID"])["Revision"] == failed["Revision"]
    restarted.observe(row["SourceKind"], row["SourceID"], {"actions": {}}, "a" * 64)
    assert "check_diagnostic" not in restarted.get(row["IncidentID"])["evidence"]


def test_incident_pages_are_chronological_with_ties_and_resolved_cursor(store):
    from kvk.dal.new_source_import_dal import transaction

    created = [incident(store) for _ in range(47)]
    with transaction(store.connect) as cursor:
        for index, row in enumerate(reversed(created)):
            cursor.execute(
                "UPDATE dbo.RecoveryIncident SET FirstSeenUTC=DATEADD(second,?,CAST('20261001' AS datetime2)) WHERE IncidentID=?",
                index // 3,
                row["IncidentID"],
            )
    first = store.list_open(limit=20)
    boundary = first[-1]
    store.observe(
        boundary["SourceKind"], boundary["SourceID"], {"actions": {}}, "a" * 64, resolved=True
    )
    second = store.list_open(after=boundary["IncidentID"], limit=20)
    third = store.list_open(after=second[-1]["IncidentID"], limit=20)
    all_rows = first + second + third
    assert len(all_rows) == len({r["IncidentID"] for r in all_rows}) == 47
    dates = [r["FirstSeenUTC"] for r in all_rows]
    assert dates == sorted(dates)
    foreign = RecoveryDAL(store.connect, account="foreign", storage_owner="disk", guild_id=2)
    with pytest.raises(SourceConflict):
        foreign.list_open(after=boundary["IncidentID"])
    with pytest.raises(SourceConflict):
        store.list_open(after=str(uuid4()))


def test_scoped_discovery_revision_and_alert_roundtrip(store):
    row = incident(store)
    same = store.observe(row["SourceKind"], row["SourceID"], {"actions": {}}, "a" * 64)
    assert same["Revision"] == 1
    changed = store.observe(row["SourceKind"], row["SourceID"], {"actions": {}}, "b" * 64)
    assert changed["Revision"] == 2
    # Individual incident delivery has been replaced by the scoped overview.
    assert store.alerts_due() == []
    store.alert_sent(row["IncidentID"], 2, 3, 4)
    assert store.get(row["IncidentID"])["AlertMessageID"] == 4
    assert store.alerts_due() == []
    assert len(store.list_open()) == 1
    other = RecoveryDAL(store.connect, account="different", storage_owner="test-disk", guild_id=2)
    with pytest.raises(SourceConflict):
        other.get(row["IncidentID"])
    assert other.list_open() == []


def test_check_failure_is_persisted_and_cleared_only_by_successful_observation(store):
    row = incident(store)
    store.check_failed(row["IncidentID"], "TimeoutError")
    failed = store.get(row["IncidentID"])
    assert failed["evidence"]["check_unavailable"] == "TimeoutError"
    assert failed["LastSeenUTC"] == row["LastSeenUTC"]
    assert failed["Revision"] == 2
    assert store.has_failed_checks()
    assert [r["IncidentID"] for r in store.list_open(failed_checks_only=True)] == [
        row["IncidentID"]
    ]
    assert store.list_open(after=row["IncidentID"], failed_checks_only=True) == []
    other = RecoveryDAL(store.connect, account="other", storage_owner="test-disk", guild_id=2)
    assert not other.has_failed_checks()
    assert other.list_open(failed_checks_only=True) == []
    with pytest.raises(SourceConflict):
        other.list_open(after=row["IncidentID"], failed_checks_only=True)
    store.check_failed(row["IncidentID"], "TimeoutError")
    assert store.get(row["IncidentID"])["Revision"] == 2
    fresh = store.observe(row["SourceKind"], row["SourceID"], {"actions": {}}, "a" * 64)
    assert "check_unavailable" not in fresh["evidence"]
    assert fresh["Revision"] == 3
    assert not store.has_failed_checks()
    assert store.list_open(failed_checks_only=True) == []


def test_alert_lease_and_paired_identity_constraint(store):
    import pyodbc

    row = incident(store)
    assert store.claim_alert(row["IncidentID"]) is True
    assert store.claim_alert(row["IncidentID"]) is False
    store.alert_sent(row["IncidentID"], 1, 3, 4)
    connection = store.connect()
    try:
        with pytest.raises(pyodbc.IntegrityError):
            connection.cursor().execute(
                "UPDATE dbo.RecoveryIncident SET AlertChannelID=NULL WHERE IncidentID=?",
                row["IncidentID"],
            )
        connection.rollback()
    finally:
        connection.close()


def test_concurrent_claims_dispatch_once_and_survive_new_dal(store):
    row = incident(store)

    def claim(_):
        return store.claim(
            row["IncidentID"],
            row["Revision"],
            row["EvidenceHash"],
            "release_failure",
            "discord:1",
            "confirmed",
        )

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(claim, range(4)))
    assert sum(acquired for _, acquired in results) == 1
    assert len({key for key, _ in results}) == 1
    restarted = RecoveryDAL(
        store.connect, account="test-account", storage_owner="test-disk", guild_id=2
    )
    action = restarted.pending_actions(row["IncidentID"])[0]
    store.finish(row["IncidentID"], action["ActionID"], "verified", {"verified": True})
    assert restarted.pending_actions(row["IncidentID"]) == []
    assert claim(0)[1] is False


def test_stale_and_cross_scope_claims_cannot_dispatch(store):
    row = incident(store)
    with pytest.raises(SourceConflict):
        store.claim(row["IncidentID"], 2, "b" * 64, "release_failure", "discord:1", "confirmed")
    other = RecoveryDAL(
        store.connect, account="test-account", storage_owner="test-disk", guild_id=999
    )
    with pytest.raises(SourceConflict):
        other.claim(row["IncidentID"], 1, "a" * 64, "release_failure", "discord:1", "confirmed")


@pytest.mark.parametrize(
    "kind,action,offered,allowed",
    [
        ("export_job", "verify_publication", True, True),
        ("export_job", "verify_publication", False, False),
        ("export_job", "retry_absent", True, False),
        ("stats_import", "verify_publication", True, False),
    ],
)
def test_only_explicit_publication_check_can_claim_resolved_incident(
    store, kind, action, offered, allowed
):
    row = store.observe(
        kind,
        str(uuid4()),
        {"actions": {action: {}} if offered else {}},
        "a" * 64,
        resolved=True,
    )

    def claim():
        return store.claim(
            row["IncidentID"],
            row["Revision"],
            row["EvidenceHash"],
            action,
            "discord:1",
            "Check current output",
        )

    if allowed:
        assert claim()[1]
        assert store.get(row["IncidentID"])["State"] == "open"
        assert not claim()[1]
    else:
        with pytest.raises(SourceConflict):
            claim()


def test_unknown_action_blocks_new_revision_dispatch(store):
    row = incident(store)
    key, acquired = store.claim(
        row["IncidentID"], 1, "a" * 64, "release_failure", "discord:1", "confirmed"
    )
    assert acquired
    store.finish(row["IncidentID"], key, "unknown", {"error_type": "TimeoutError"})
    store.observe(row["SourceKind"], row["SourceID"], {"actions": {}}, "b" * 64)
    assert store.claim(
        row["IncidentID"], 2, "b" * 64, "release_failure", "discord:1", "confirmed"
    ) == (key, False)


def test_commit_ack_loss_retains_single_durable_action(store):
    row = incident(store)
    real_connect = store.connect

    class LostAck:
        def __init__(self):
            self.inner = real_connect()

        def commit(self):
            self.inner.commit()
            raise OSError("lost commit acknowledgement")

        def __getattr__(self, name):
            return getattr(self.inner, name)

    store.connect = LostAck
    with pytest.raises(UncertainCommit):
        store.claim(row["IncidentID"], 1, "a" * 64, "release_failure", "discord:1", "confirmed")
    store.connect = real_connect
    assert len(store.pending_actions(row["IncidentID"])) == 1
    assert (
        store.claim(row["IncidentID"], 1, "a" * 64, "release_failure", "discord:1", "confirmed")[1]
        is False
    )
