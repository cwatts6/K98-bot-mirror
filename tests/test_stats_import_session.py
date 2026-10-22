"""Import execution borrows its existing guard, never a second SQL session."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services import legacy_export_snapshot_service as snapshot
from services.stats_import_outcome_service import execution_connection


@pytest.fixture
def admitted(monkeypatch):
    connection = Mock(autocommit=True, timeout=15)
    runtime = object()
    owner = SimpleNamespace(connection=connection, runtime=runtime, kind="scan_data", closed=False)
    monkeypatch.setattr(snapshot, "current_owner", lambda: owner)
    monkeypatch.setattr(snapshot, "require_runtime", lambda: runtime)
    return owner


@pytest.mark.parametrize("fails", [False, True])
def test_borrow_preserves_custody_and_restores_timeout(admitted, fails):
    factory = Mock(side_effect=AssertionError("must not open a separate session"))
    failure = RuntimeError("report transaction failed")
    try:
        with execution_connection(factory, timeout_seconds=600) as connection:
            assert connection is admitted.connection
            assert connection.timeout == 595
            if fails:
                raise failure
    except RuntimeError as error:
        assert fails and error is failure
    assert admitted.connection.timeout == 15
    admitted.connection.close.assert_not_called()
    admitted.connection.commit.assert_not_called()
    admitted.connection.rollback.assert_not_called()
    factory.assert_not_called()


@pytest.mark.parametrize("mutation", ["closed", "kind", "transaction", "runtime"])
def test_invalid_writer_cannot_borrow_session(admitted, mutation):
    if mutation == "closed":
        admitted.closed = True
    elif mutation == "kind":
        admitted.kind = "all_kvk"
    elif mutation == "transaction":
        admitted.connection.autocommit = False
    else:
        admitted.runtime = object()
    with pytest.raises(SourceConflict):
        with execution_connection(Mock(), timeout_seconds=600):
            pytest.fail("invalid owner entered SQL")


def test_runtime_without_admission_cannot_open_replacement_connection(monkeypatch):
    monkeypatch.setattr(snapshot, "current_owner", lambda: None)
    factory = Mock()
    with snapshot.use_runtime(object()), pytest.raises(SourceConflict, match="admitted"):
        with execution_connection(factory, timeout_seconds=600):
            pytest.fail("unadmitted execution")
    factory.assert_not_called()
