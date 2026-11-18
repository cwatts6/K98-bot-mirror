"""D5b offline contract challenges. Failures are evidence, not native permission.

Run only this packet with --noconftest and plugin autoload disabled. Every SQL
handle is a finite in-memory double; no driver or application factory is used.
"""

from copy import deepcopy
import importlib
import socket
from types import SimpleNamespace

import pytest

KINDS = ("import", "configuration", "player_report", "kvk_output", "final_stats", "post_import")
CLAIM = "11111111-1111-4111-8111-111111111111"
QUIET = (0, "NoLock", "NoLock", "NoLock", "NoLock", "NoLock")


def rows():
    return [
        dict(
            Kind=k,
            DueGeneration=0,
            CompletedGeneration=0,
            ClaimedGeneration=None,
            ClaimID=None,
            State="complete",
            FirstErrorNumber=None,
            LastErrorNumber=None,
        )
        for k in KINDS
    ]


@pytest.fixture
def api(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("D5b offline packet attempted an external connection")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    dal = importlib.import_module("services.maintenance_dal")
    service = importlib.import_module("services.maintenance_service")
    backup = importlib.import_module("services.maintenance_backup_dal")
    custody = importlib.import_module("core.sql_connection_custody")
    monkeypatch.setattr(custody, "_holds", {})
    # Never enter the backup dispatch/import path, even for positive demand.
    backup_calls = []

    def requested(cursor):
        backup_calls.append(cursor)
        return dict(
            State="requested",
            DueGeneration=1,
            RequestedGeneration=1,
            ClaimedGeneration=1,
            ClaimID=CLAIM,
        )

    monkeypatch.setattr(backup, "run", requested)
    return SimpleNamespace(dal=dal, service=service, custody=custody, backup_calls=backup_calls)


class Wire:
    """Finite result sets, with independently injectable reply/cleanup failures."""

    autocommit = False
    timeout = None

    def __init__(self, api, sets):
        self.api = api
        self.sets = deepcopy(sets)
        self.index = 0
        self.events = []
        self.mode = "initial"
        self.initial = QUIET
        self.late_error = None
        self.release_error = None
        self.close_error = None

    @property
    def description(self):
        fields = self.api.dal.FIELDS if self.mode == "work" else ()
        return tuple((x,) for x in fields)

    def cursor(self):
        return self

    def execute(self, statement, request=None):
        if statement == self.api.dal.SESSION_STATE:
            self.mode = "initial"
        elif statement == self.api.dal.RELEASE_SESSION:
            self.mode = "release"
            self.events.append("release")
            if self.release_error:
                raise self.release_error
        else:
            assert statement == "EXEC dbo.usp_update_stats @RequestID=?"
            assert request == CLAIM
            self.mode = "work"
            self.events.append("entered")

    def fetchone(self):
        return self.initial if self.mode == "initial" else QUIET

    def fetchmany(self, size):
        assert size == 7 and self.mode == "work"
        batch = self.sets[self.index][:size]
        del self.sets[self.index][:size]
        return [tuple(row[f] for f in self.api.dal.FIELDS) for row in batch]

    def nextset(self):
        if self.mode != "work":
            return False
        if self.late_error:
            raise self.late_error
        self.index += 1
        return self.index < len(self.sets)

    def close(self):
        self.events.append("close")
        if self.close_error:
            raise self.close_error


def invoke(api, data, path):
    packet = dict(request_id=CLAIM, maintenance=deepcopy(data))
    if path == "dal":
        wire = Wire(api, [data])
        return api.dal.run_maintenance(lambda: wire, request_id=CLAIM)
    if path == "result":
        return api.service.result(packet)
    return api.service.evidence((True, packet))


@pytest.mark.parametrize("path", ["dal", "result", "evidence"])
@pytest.mark.parametrize("missing", [*KINDS, "all", "all_but_post_import"])
def test_incomplete_six_kind_contract_is_rejected(api, path, missing):
    data = rows()
    if missing == "all":
        data = []
    elif missing == "all_but_post_import":
        data = data[-1:]
    else:
        data = [r for r in data if r["Kind"] != missing]
    with pytest.raises(ValueError):
        invoke(api, data, path)


@pytest.mark.parametrize(
    "damage",
    [
        "duplicate",
        "foreign",
        "state",
        "negative_due",
        "done_above_due",
        "false_complete",
        "bad_uuid",
        "claim_zero",
        "claim_negative",
        "claim_above_due",
        "claim_text",
        "claim_overflow",
    ],
)
def test_malformed_receipts_rejected_with_physical_cleanup(api, damage):
    data = rows()
    row = data[0]
    if damage == "duplicate":
        data.append(deepcopy(row))
    elif damage == "foreign":
        row["Kind"] = "foreign"
    elif damage == "state":
        row["State"] = "success"
    elif damage == "negative_due":
        row["DueGeneration"] = -1
    elif damage == "done_above_due":
        row["CompletedGeneration"] = 1
    elif damage == "false_complete":
        row["DueGeneration"] = 1
    elif damage == "bad_uuid":
        row["ClaimID"] = "invalid"
    else:
        row.update(DueGeneration=1, CompletedGeneration=1, ClaimID=CLAIM)
        row["ClaimedGeneration"] = {
            "claim_zero": 0,
            "claim_negative": -1,
            "claim_above_due": 2,
            "claim_text": "1",
            "claim_overflow": 2**63,
        }[damage]
    wire = Wire(api, [data])
    try:
        with pytest.raises(ValueError):
            api.dal.run_maintenance(lambda: wire, request_id=CLAIM)
    finally:
        assert wire.events[-3:] == ["release", "close", "close"]
        assert api.custody.custody_snapshot()["admission"] == "open"


@pytest.mark.parametrize("state", ["complete", "pending", "running", "failed", "unknown"])
def test_complete_and_outstanding_full_sets(api, state):
    data = rows()
    data[0].update(
        DueGeneration=1,
        CompletedGeneration=int(state == "complete"),
        ClaimedGeneration=1,
        ClaimID=CLAIM,
        State=state,
    )
    wire = Wire(api, [data[:3], data[3:]])
    packet = api.dal.run_maintenance(lambda: wire, request_id=CLAIM)
    assert len(packet["maintenance"]) == 6
    result = api.service.result(packet)
    assert result[0] is (state == "complete")
    assert api.service.evidence(result)[1] is (state == "complete")
    assert wire.events[-3:] == ["release", "close", "close"]


def test_duplicate_across_result_sets_rejected(api):
    wire = Wire(api, [rows()[:3], rows()[3:] + rows()[:1]])
    with pytest.raises(ValueError):
        api.dal.run_maintenance(lambda: wire, request_id=CLAIM)
    assert wire.events[-3:] == ["release", "close", "close"]


@pytest.mark.parametrize("backup_state", [None, "pending", "requested", "unconfirmed"])
def test_final_stats_demand_needs_backup_evidence(api, backup_state):
    data = rows()
    data[4].update(DueGeneration=1, CompletedGeneration=1, ClaimedGeneration=1, ClaimID=CLAIM)
    wire = Wire(api, [data])
    packet = api.dal.run_maintenance(lambda: wire, request_id=CLAIM)
    assert api.backup_calls == [wire]
    if backup_state is None:
        del packet["backup_request"]
    elif backup_state == "pending":
        packet["backup_request"].update(State="pending", RequestedGeneration=0)
    elif backup_state == "unconfirmed":
        packet["backup_request"]["dispatch_cleanup"] = "unconfirmed"
    assert api.service.result(packet)[0] is (backup_state == "requested")
    assert api.service.evidence((True, packet))[1] is (backup_state == "requested")


def test_original_failure_survives_cleanup_failure(api):
    wire = Wire(api, [rows()])
    original = RuntimeError("controlled late reply failure")
    wire.late_error = original
    wire.close_error = OSError("controlled cleanup failure")
    with pytest.raises(RuntimeError) as error:
        api.dal.run_maintenance(lambda: wire, request_id=CLAIM)
    assert error.value is original
    assert "SQL cursor_close failed: OSError" in original.__notes__
    assert api.custody.connection_retained(wire)


@pytest.mark.parametrize("unknown", ["foreign_initial", "release_lost"])
def test_unknown_owner_not_released_or_reused(api, unknown):
    wire = Wire(api, [rows()])
    if unknown == "foreign_initial":
        wire.initial = (0, "Exclusive", *QUIET[2:])
    else:
        wire.release_error = OSError("controlled release failure")
    with pytest.raises((api.custody.SqlCleanupUnknown, OSError)):
        api.dal.run_maintenance(lambda: wire, request_id=CLAIM)
    assert "close" not in wire.events
    if unknown == "foreign_initial":
        assert "release" not in wire.events and "entered" not in wire.events
    assert api.custody.connection_retained(wire)
    with pytest.raises(api.custody.SqlCleanupUnknown):
        api.dal.run_maintenance(lambda: pytest.fail("closed admission invoked factory"))
