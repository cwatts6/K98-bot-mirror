"""The native continuation owns one connection and never dispatches business SQL."""

import pytest

from scripts.prove_p02_observer_binding import APPLICATION_CONTEXT_SQL, prove
from scripts.verify_k98_running_release import ObservationConnections
from services.catalogue_observation_dal import BOUNDARY_SQL
from tests.test_observation_installation_binding import approved, boundary


class NativeConnection:
    autocommit = True

    def __init__(self, *, fail_read=False, fail_close=False):
        self.commands = []
        self.closes = 0
        self.fail_read, self.fail_close = fail_read, fail_close

    def cursor(self):
        connection = self

        class Cursor:
            def execute(self, statement):
                assert statement in {"SET LOCK_TIMEOUT 0", APPLICATION_CONTEXT_SQL, BOUNDARY_SQL}
                connection.commands.append(statement)
                if statement == BOUNDARY_SQL and connection.fail_read:
                    raise RuntimeError("FIRST_READ_FAILURE")
                self.result = iter([boundary(), None]) if statement == BOUNDARY_SQL else iter([])

            def fetchone(self):
                return next(self.result)

            def nextset(self):
                return False

            def close(self):
                pass

        return Cursor()

    def close(self):
        self.closes += 1
        if self.fail_close:
            raise RuntimeError("CLOSE_FAILURE")


def test_binding_continuation_dispatches_two_reads_and_preserves_first_success():
    native = NativeConnection()
    owner = ObservationConnections(lambda: native)
    records = {}
    facts = prove(owner, approved(), 2, lambda name, value: records.setdefault(name, value))
    assert facts["replacement_identity_refused"] and facts["cleanup"] == "acknowledged"
    assert set(records) == {"progress.json", "catalogue-cost-result.json"}
    assert native.commands == [
        "SET LOCK_TIMEOUT 0",
        APPLICATION_CONTEXT_SQL,
        BOUNDARY_SQL,
        BOUNDARY_SQL,
    ]
    assert native.closes == 1


@pytest.mark.parametrize("close_fails", [False, True])
def test_failed_first_read_does_not_retry_or_lose_owner_failure(close_fails):
    native = NativeConnection(fail_read=True, fail_close=close_fails)
    owner = ObservationConnections(lambda: native)
    with pytest.raises(RuntimeError):
        prove(
            owner, approved(), 2, lambda *_: pytest.fail("Success evidence written after failure")
        )
    assert native.commands.count(BOUNDARY_SQL) == 1
    assert native.closes == 1
    assert owner.first_failure["operation"] == "execute"
    assert owner.evidence()["connections"] == [
        dict(closed=not close_fails, close_failed=close_fails)
    ]
