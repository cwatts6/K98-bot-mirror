"""New boundary decisions, using the SQL procedure's exact native row shape."""

from copy import deepcopy
from datetime import datetime
import json

import pytest

from services import catalogue_observation_dal as dal


def expected():
    return {
        name: f"CREATE {'TRIGGER' if name.startswith('tr_') else 'PROCEDURE'} {name} AS SELECT 1;"
        for name in dal.MODULES
    }


@pytest.mark.parametrize("kind", ["PROCEDURE", "TRIGGER"])
@pytest.mark.parametrize("header", ["CREATE   ", "ALTER\t", "CREATE\tOR\nALTER  "])
def test_module_header_forms_preserve_complete_body(kind, header):
    body = "dbo.Example AS SELECT 'literal'; -- comment\n\t\n"
    assert dal.canonical_module(header + kind + "\t" + body) == kind + " " + body
    assert (
        dal.canonical_module(header + kind + " " + body.replace("\n", "\r\n")) == kind + " " + body
    )


@pytest.mark.parametrize("changed", ["dbo.Other", "AS SELECT 2;", "-- other", "\n", " "])
def test_module_comparison_does_not_trim_or_hide_body_changes(changed):
    original = "CREATE PROCEDURE dbo.Example AS SELECT 1; -- comment\n"
    assert dal.canonical_module(original) != dal.canonical_module(original + changed)


def token(generation=2, absent=1):
    health = [
        dict(
            name=name,
            definition=body,
            uses_ansi_nulls=True,
            uses_quoted_identifier=True,
            execute_as_principal_id=None,
            is_disabled=False if name.startswith("tr_") else None,
            is_not_for_replication=False if name.startswith("tr_") else None,
        )
        for name, body in expected().items()
    ]
    stamp = datetime(2026, 11, 19)
    return [
        "lab",
        "fixture",
        7,
        "dbo",
        "lab-user",
        51,
        0,
        0,
        2,
        generation,
        absent,
        generation,
        100,
        stamp,
        stamp,
        100,
        stamp,
        stamp,
        json.dumps(health),
    ]


class Cursor:
    def __init__(self, *boundaries):
        self.boundaries = iter(boundaries)
        self.commands = []

    def execute(self, sql):
        self.commands.append(sql)
        self.result = iter([next(self.boundaries), None])

    def fetchone(self):
        return next(self.result)

    def nextset(self):
        return False


def test_stable_candidate_and_between_batch_check():
    cursor = Cursor(token(), token(), token())

    def collect(checkpoint):
        checkpoint()
        return {"complete": "metadata"}

    result = dal.observe_catalogue(cursor, expected(), collect)
    assert result.value == {"complete": "metadata"}
    assert result.guard == "catalogue_generation_v1"
    assert cursor.commands == [dal.BOUNDARY_SQL] * 3


@pytest.mark.parametrize(
    "row,reason", [(token(absent=0), "active_writer"), (token(3), "generation_changed")]
)
def test_overlap_discards_candidate_without_retry(row, reason):
    cursor = Cursor(token(), row)
    with pytest.raises(dal.ObservationDeferred, match=reason):
        dal.observe_catalogue(cursor, expected(), lambda _: "must be discarded")
    assert len(cursor.commands) == 2


def test_active_writer_does_not_dispatch_full_scan():
    cursor = Cursor(token(absent=0))
    with pytest.raises(dal.ObservationDeferred):
        dal.observe_catalogue(cursor, expected(), lambda _: pytest.fail("full scan started"))


@pytest.mark.parametrize(
    "field,value",
    [(9, True), (10, True), (11, None), (6, 2), (7, -1), (8, 5), (12, None), (15, 101), (5, 0)],
)
def test_native_contract_corruption_is_not_busy(field, value):
    row = token()
    row[field] = value
    with pytest.raises(dal.ObservationContractError):
        dal.read_boundary(Cursor(row), expected())


@pytest.mark.parametrize(
    "corruption", ["disabled", "body", "missing", "duplicate", "execute_as", "replication"]
)
def test_health_refuses_disabled_changed_missing_or_ambiguous_protocol(corruption):
    row = token()
    health = json.loads(row[-1])
    trigger = next(x for x in health if x["name"].startswith("tr_"))
    if corruption == "disabled":
        trigger["is_disabled"] = True
    elif corruption == "body":
        trigger["definition"] += " -- unreviewed"
    elif corruption == "missing":
        health.pop()
    elif corruption == "duplicate":
        health[-1] = deepcopy(health[0])
    elif corruption == "execute_as":
        trigger["execute_as_principal_id"] = -2
    else:
        trigger["is_not_for_replication"] = True
    row[-1] = json.dumps(health)
    with pytest.raises(dal.ObservationContractError):
        dal.read_boundary(Cursor(row), expected())


def test_first_metadata_error_propagates_without_hidden_cleanup_or_retry():
    original = RuntimeError("first SQL error")
    cursor = Cursor(token())

    def collect(_):
        raise original

    with pytest.raises(RuntimeError) as caught:
        dal.observe_catalogue(cursor, expected(), collect)
    assert caught.value is original
    assert len(cursor.commands) == 1


def test_changed_borrowed_session_is_never_reused():
    row = token()
    row[5] += 1
    with pytest.raises(dal.ObservationContractError, match="identity changed"):
        dal.observe_catalogue(Cursor(token(), row), expected(), lambda _: None)


def test_late_boundary_failure_is_not_discarded(monkeypatch):
    cursor = Cursor(token())
    failure = RuntimeError("late boundary failure")

    def finish():
        raise failure

    monkeypatch.setattr(cursor, "nextset", finish)
    with pytest.raises(RuntimeError) as caught:
        dal.read_boundary(cursor, expected())
    assert caught.value is failure


@pytest.mark.parametrize("count,state", [(0, 0), (0, 1), (1, 1)])
def test_native_autocommit_statement_state_does_not_equal_user_nesting(count, state):
    row = token()
    row[6:8] = [count, state]
    result = dal.read_boundary(Cursor(row), expected())
    assert result.identity[6:8] == (count, state)


def test_transaction_count_one_with_no_active_state_is_inconsistent():
    row = token()
    row[6:8] = [1, 0]
    with pytest.raises(dal.ObservationContractError):
        dal.read_boundary(Cursor(row), expected())
