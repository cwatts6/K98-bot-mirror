"""Fault injection around the actual DAL transaction boundary (no live SQL).

The cursor fixture supplies SQL-shaped results, while the production writer,
mutation/audit statements, commit classification and resource cleanup execute.
Native SQL locking/plan qualification remains a separate integration gate.
"""

from copy import deepcopy
from datetime import UTC, datetime, timedelta
import json

import pytest

from core.operation_outcome import MutationOutcome as O
from mge.dal import mge_signup_mutation_dal as dal


class Connection:
    autocommit = False

    def __init__(self, *, fail=None, rollback_fails=False):
        self.fail = fail
        self.rollback_fails = rollback_fails
        self.event = dict(
            EventId=42,
            EventMode="controlled",
            Status="signup_open",
            SignupCloseUtc=datetime.now(UTC) + timedelta(hours=1),
            VariantName="Infantry",
        )
        self.persisted = {
            "signup": dict(SignupId=99, EventId=42, GovernorId=100, IsActive=True, CurrentHeads=12),
            "audits": [],
            "award": dict(
                AwardId=77,
                EventId=42,
                GovernorId=100,
                AwardedRank=1,
                AwardStatus="awarded",
                TargetScore=100,
            ),
        }
        self.working = deepcopy(self.persisted)
        self.calls = []
        self.cur = Cursor(self)

    def cursor(self):
        return self.cur

    def commit(self):
        self.calls.append("commit")
        self.persisted = deepcopy(self.working)
        if self.fail == "commit_ack":
            raise OSError("lost acknowledgement")

    def rollback(self):
        self.calls.append("rollback")
        if self.rollback_fails:
            raise OSError("rollback unavailable")
        self.working = deepcopy(self.persisted)

    def close(self):
        self.calls.append("close")


class Cursor:
    def __init__(self, conn):
        self.conn = conn
        self.rowcount = 1
        self.description = []
        self.row = None

    def result(self, values):
        self.description = [(key,) for key in values] if values else []
        self.row = tuple(values.values()) if values else None

    def execute(self, sql, params=()):
        sql = " ".join(sql.split())
        self.conn.calls.append(sql)
        if self.conn.fail and self.conn.fail in sql:
            raise OSError("injected statement failure")
        state = self.conn.working
        if sql.startswith("SELECT e.EventId"):
            self.result(self.conn.event)
        elif sql.startswith("SELECT EventMode"):
            self.result({"EventMode": self.conn.event["EventMode"]})
        elif "FROM dbo.MGE_SignupAudit" in sql:
            self.result(
                next(
                    (
                        r
                        for r in state["audits"]
                        if json.loads(r["DetailsJson"])["operation_id"] == params[2]
                    ),
                    None,
                )
            )
        elif "FROM dbo.MGE_Signups" in sql:
            self.result(state["signup"])
        elif "INSERT INTO dbo.MGE_Signups" in sql:
            state["signup"] = dict(
                SignupId=99, EventId=params[0], GovernorId=params[1], IsActive=True
            )
            self.result({"SignupId": 99})
        elif sql.startswith("UPDATE dbo.MGE_Signups SET IsActive"):
            state["signup"]["IsActive"] = False
        elif sql.startswith("UPDATE dbo.MGE_Signups"):
            state["signup"]["CurrentHeads"] = params[4]
        elif "FROM dbo.MGE_Awards" in sql and sql.startswith("SELECT"):
            self.result(state["award"])
        elif sql.startswith("DELETE FROM dbo.MGE_Awards"):
            state["award"] = None
        elif sql.startswith("INSERT INTO dbo.MGE_SignupAudit"):
            state["audits"].append(
                dict(
                    SignupId=params[0],
                    GovernorId=params[2],
                    ActionType=params[3],
                    DetailsJson=params[5],
                )
            )
        elif sql.startswith("INSERT INTO dbo.MGE_AwardAudit"):
            state["award_audit"] = params
        else:
            raise AssertionError(sql)

    def fetchone(self):
        return self.row

    def close(self):
        self.conn.calls.append("cursor_close")


def invoke(monkeypatch, conn, **overrides):
    monkeypatch.setattr(dal, "get_conn_with_retries", lambda: conn)
    values = dict(
        action="withdraw",
        event_id=42,
        governor_id=100,
        actor_discord_id=1,
        is_admin=False,
        signup_id=99,
        operation_id="fixture-1",
        validate_event=lambda event, now: "locked" if event["Status"] == "published" else None,
    )
    values.update(overrides)
    return dal.mutate_signup(**values)


def test_withdraw_commit_includes_required_audits_and_cleanup(monkeypatch):
    conn = Connection()
    result = invoke(monkeypatch, conn)
    assert result.outcome == O.COMMITTED
    assert not conn.persisted["signup"]["IsActive"]
    assert conn.persisted["award"] is None
    assert len(conn.persisted["audits"]) == 1
    assert conn.persisted["award_audit"][3] == "withdraw_cleanup"
    assert conn.calls[-3:] == ["commit", "cursor_close", "close"]
    assert "MGE_Events e WITH (UPDLOCK, HOLDLOCK)" in conn.calls[0]


@pytest.mark.parametrize(
    "fail",
    [
        "UPDATE dbo.MGE_Signups",
        "DELETE FROM dbo.MGE_Awards",
        "INSERT INTO dbo.MGE_AwardAudit",
        "INSERT INTO dbo.MGE_SignupAudit",
    ],
)
def test_failure_at_each_required_write_rolls_everything_back(monkeypatch, fail):
    conn = Connection(fail=fail)
    original = deepcopy(conn.persisted)
    result = invoke(monkeypatch, conn)
    assert result.outcome == O.ROLLED_BACK
    assert conn.persisted == conn.working == original
    assert "commit" not in conn.calls
    assert conn.calls[-3:] == ["rollback", "cursor_close", "close"]


def test_lost_commit_ack_is_unknown_even_when_rollback_returns(monkeypatch):
    conn = Connection(fail="commit_ack")
    result = invoke(monkeypatch, conn)
    assert result.outcome == O.UNKNOWN
    assert not conn.persisted["signup"]["IsActive"]
    assert conn.calls.count("commit") == 1
    # A later exact same operation is positively reconciled, never replayed.
    conn.fail = None
    prior_writes = len([s for s in conn.calls if s.startswith(("UPDATE", "DELETE", "INSERT"))])
    repeated = invoke(monkeypatch, conn)
    assert repeated.outcome == O.COMMITTED and repeated.reason == "reconciled"
    assert (
        len([s for s in conn.calls if s.startswith(("UPDATE", "DELETE", "INSERT"))]) == prior_writes
    )


def test_rollback_failure_retains_unknown(monkeypatch):
    conn = Connection(fail="INSERT INTO dbo.MGE_SignupAudit", rollback_fails=True)
    assert invoke(monkeypatch, conn).outcome == O.UNKNOWN


@pytest.mark.parametrize(
    "change", ["wrong_event", "wrong_governor", "inactive", "published", "stale"]
)
def test_authority_changes_reject_before_write(monkeypatch, change):
    conn = Connection()
    args = {}
    if change == "wrong_event":
        conn.working["signup"]["EventId"] = 43
    elif change == "wrong_governor":
        conn.working["signup"]["GovernorId"] = 101
    elif change == "inactive":
        conn.working["signup"]["IsActive"] = False
    elif change == "published":
        conn.event["Status"] = "published"
    else:
        args["expected_signup"] = {"CurrentHeads": 11}
    result = invoke(monkeypatch, conn, **args)
    assert result.outcome == O.ROLLED_BACK
    assert not any(s.startswith(("UPDATE", "INSERT", "DELETE")) for s in conn.calls)


def test_same_receipt_identity_cannot_be_reused_for_different_input(monkeypatch):
    conn = Connection()
    assert invoke(monkeypatch, conn).outcome == O.COMMITTED
    result = invoke(monkeypatch, conn, governor_id=101)
    assert result.outcome == O.ROLLED_BACK
    assert "identity" in result.reason


def test_connection_failure_proves_non_entry(monkeypatch):
    def unavailable():
        raise OSError("not connected")

    monkeypatch.setattr(dal, "get_conn_with_retries", unavailable)
    result = dal.mutate_signup(
        action="withdraw",
        event_id=42,
        governor_id=100,
        actor_discord_id=1,
        is_admin=False,
        signup_id=99,
        validate_event=lambda *_: None,
    )
    assert result.outcome == O.NOT_ENTERED


@pytest.mark.parametrize("action", ["create", "edit"])
@pytest.mark.parametrize("audit_fails", [False, True])
def test_signup_and_required_audit_share_commit_for_create_and_edit(
    monkeypatch, action, audit_fails
):
    conn = Connection(fail="INSERT INTO dbo.MGE_SignupAudit" if audit_fails else None)
    original = deepcopy(conn.persisted)
    values = dict(
        request_priority="high",
        preferred_rank_band="1-5",
        requested_commander_id=1,
        requested_commander_name="Fixture",
        current_heads=25,
        kingdom_role=None,
        gear_text=None,
        armament_text=None,
    )
    if action == "create":
        values.update(governor_name_snapshot="Fixture", discord_user_id=1)
    result = invoke(monkeypatch, conn, action=action, values=values)
    if audit_fails:
        assert result.outcome == O.ROLLED_BACK
        assert conn.persisted == original
        assert "commit" not in conn.calls
    else:
        assert result.outcome == O.COMMITTED
        assert conn.calls.count("commit") == 1
        assert len(conn.persisted["audits"]) == 1
        details = json.loads(conn.persisted["audits"][0]["DetailsJson"])
        assert details["before"] == (original["signup"] if action == "edit" else None)
