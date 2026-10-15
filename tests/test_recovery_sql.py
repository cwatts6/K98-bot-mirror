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
        for kind in ("Incident", "Action")
    }

    def rewrite(sql):
        for source, target in names.items():
            sql = sql.replace(source, target)
        return sql

    # Fixed local development endpoint, integrated auth; never environment-derived production.
    connection_string = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\\K98DEV;DATABASE=master;Trusted_Connection=yes;TrustServerCertificate=yes"
    owner = pyodbc.connect(connection_string, autocommit=True, timeout=5)
    schema = Path(os.environ["K98_RECOVERY_SQL_SCHEMA"])
    for kind in ("Incident", "Action"):
        sql = (schema / f"dbo.Recovery{kind}.Table.sql").read_text(encoding="utf-8-sig")
        # SQL Server does not enforce FKs for temporary tables. Persistent FK is
        # covered by source validation; all other table constraints run here.
        sql = re.sub(r"^\s*CONSTRAINT FK_RecoveryAction_Incident[^\n]*\n", "", sql, flags=re.M)
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


def incident(store):
    return store.observe("stats_import", str(uuid4()), {"actions": {}}, "a" * 64)


def test_scoped_discovery_revision_and_alert_roundtrip(store):
    row = incident(store)
    same = store.observe(row["SourceKind"], row["SourceID"], {"actions": {}}, "a" * 64)
    assert same["Revision"] == 1
    changed = store.observe(row["SourceKind"], row["SourceID"], {"actions": {}}, "b" * 64)
    assert changed["Revision"] == 2
    assert store.alerts_due() == [row["IncidentID"]]
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
    store.check_failed(row["IncidentID"], "TimeoutError")
    assert store.get(row["IncidentID"])["Revision"] == 2
    fresh = store.observe(row["SourceKind"], row["SourceID"], {"actions": {}}, "a" * 64)
    assert "check_unavailable" not in fresh["evidence"]
    assert fresh["Revision"] == 3


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
