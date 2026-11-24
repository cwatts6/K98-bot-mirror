"""Combined dispatch must not skip rows, checkpoints, failures or owner limits."""

from copy import deepcopy

import pytest

from services.catalogue_observation_batch_dal import CatalogueBatchCursor
from services.catalogue_observation_dal import (
    BOUNDARY_SQL,
    ObservationContractError,
    ObservationDeferred,
    observe_catalogue,
    read_boundary,
)
from tests.test_catalogue_observation import expected, token


class ResultCursor:
    def __init__(self, *results):
        self.dispatches = iter(results)
        self.commands = []
        self.connection = object()
        self.description = [("value",)]

    def execute(self, *args):
        self.commands.append(args)
        self.sets = iter(deepcopy(next(self.dispatches)))
        self.result = iter(next(self.sets))
        return self

    def fetchone(self):
        return next(self.result, None)

    def fetchall(self):
        return list(self.result)

    def nextset(self):
        result = next(self.sets, None)
        if result is None:
            return False
        self.result = iter(result)
        return True


def test_query_and_bound_values_unchanged_and_all_checkpoints_still_checked():
    raw = ResultCursor([[token()]], [[(1,), (2,)], [token()]], [[token()]])
    cursor = CatalogueBatchCursor(raw)

    def collect(checkpoint):
        cursor.execute("SELECT ? -- preserve the full query", "bound value")
        result = cursor.fetchall()
        checkpoint()
        return result

    result = observe_catalogue(cursor, expected(), collect)
    assert result.value == [(1,), (2,)]
    assert cursor.connection is raw.connection
    assert raw.commands == [
        (BOUNDARY_SQL,),
        ("SELECT ? -- preserve the full query\n;" + BOUNDARY_SQL, "bound value"),
        (BOUNDARY_SQL,),
    ]


@pytest.mark.parametrize(
    "changed,reason", [(token(3), "generation_changed"), (token(absent=0), "active_writer")]
)
def test_changed_tail_stops_before_next_metadata_dispatch(changed, reason):
    raw = ResultCursor([[token()]], [[(1,)], [changed]])
    cursor = CatalogueBatchCursor(raw)

    def collect(checkpoint):
        cursor.execute("SELECT 1")
        cursor.fetchall()
        checkpoint()
        pytest.fail("No later batch may run after a changed boundary")

    with pytest.raises(ObservationDeferred, match=reason):
        observe_catalogue(cursor, expected(), collect)
    assert len(raw.commands) == 2


def test_unread_rows_are_refused_instead_of_discarded_by_nextset():
    raw = ResultCursor([[(1,), (2,)], [token()]])
    cursor = CatalogueBatchCursor(raw)
    cursor.execute("SELECT 1 UNION ALL SELECT 2")
    assert cursor.fetchone() == (1,)
    with pytest.raises(ObservationContractError, match="remain unread"):
        read_boundary(cursor, expected())
    with pytest.raises(ObservationContractError, match="not completed"):
        cursor.execute("SELECT 3")
    assert len(raw.commands) == 1


@pytest.mark.parametrize("rows", [[], [(1,)]])
def test_empty_and_single_row_reads_reach_boundary_without_losing_rows(rows):
    raw = ResultCursor([rows, [token()]])
    cursor = CatalogueBatchCursor(raw)
    cursor.execute("SELECT 1")
    assert cursor.fetchone() == (rows[0] if rows else None)
    assert read_boundary(cursor, expected()).generation == 2
    assert len(raw.commands) == 1


@pytest.mark.parametrize(
    "sets,message",
    [
        ([[(1,)]], "missing its boundary"),
        ([[(1,)], []], "Exactly one complete"),
        ([[(1,)], [token(), token()]], "Exactly one complete"),
        ([[(1,)], [token()], [(99,)]], "Unexpected additional"),
    ],
)
def test_missing_duplicate_and_extra_results_never_become_a_proof(sets, message):
    raw = ResultCursor(sets)
    cursor = CatalogueBatchCursor(raw)
    cursor.execute("SELECT 1")
    cursor.fetchall()
    with pytest.raises(ObservationContractError, match=message):
        read_boundary(cursor, expected())
    assert len(raw.commands) == 1


@pytest.mark.parametrize("operation", ["execute", "fetchall", "fetchone", "nextset"])
def test_driver_failure_propagates_and_poisoned_batch_cannot_be_replayed(monkeypatch, operation):
    raw = ResultCursor([[(1,)], [token()]])
    cursor = CatalogueBatchCursor(raw)
    failure = RuntimeError("first driver error")

    def fail(*_):
        raise failure

    if operation != "execute":
        cursor.execute("SELECT 1")
    if operation == "nextset":
        cursor.fetchall()
    monkeypatch.setattr(raw, operation, fail)
    with pytest.raises(RuntimeError) as caught:
        if operation == "execute":
            cursor.execute("SELECT 1")
        elif operation == "fetchall":
            cursor.fetchall()
        else:
            read_boundary(cursor, expected())
    assert caught.value is failure
    with pytest.raises(ObservationContractError, match="not completed"):
        cursor.execute("SELECT 1")


def test_owner_dispatch_and_fetch_budget_remain_in_control():
    from types import SimpleNamespace

    from scripts.verify_k98_running_release import (
        Cursor as BudgetCursor,
        ObservationConnections,
        VerificationBudgetExceeded,
    )

    now = [0]
    owner = ObservationConnections(lambda: None, clock=lambda: now[0])
    raw = ResultCursor([[(1,)], [token()]])
    cursor = CatalogueBatchCursor(BudgetCursor(SimpleNamespace(budget=owner), raw))
    owner.statements = 255
    cursor.execute("SELECT 1")
    assert cursor.fetchall() == [(1,)]
    read_boundary(cursor, expected())  # Tail uses the already-admitted dispatch.
    assert owner.statements == 256 and len(raw.commands) == 1
    with pytest.raises(VerificationBudgetExceeded):
        cursor.execute("SELECT 2")
    assert len(raw.commands) == 1

    raw = ResultCursor([[(1,)], [token()]])
    owner = ObservationConnections(lambda: None, clock=lambda: now[0])
    cursor = CatalogueBatchCursor(BudgetCursor(SimpleNamespace(budget=owner), raw))
    cursor.execute("SELECT 1")
    cursor.fetchall()
    now[0] = 45
    with pytest.raises(VerificationBudgetExceeded):
        read_boundary(cursor, expected())
    assert len(raw.commands) == 1 and owner.first_failure["operation"] == "fetch_budget"
