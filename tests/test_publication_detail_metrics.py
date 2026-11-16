from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from services import export_publication_metrics as metrics
from services.export_request_budget import RequestBudget


def records(logger):
    return {call.args[1]: call.args[2:] for call in logger.info.call_args_list}


def test_aggregate_is_bounded_redacted_and_inactive_outside_probe(monkeypatch):
    clock = iter([0, 2, 4, 7])
    monkeypatch.setattr(metrics, "monotonic", lambda: next(clock))
    logger = Mock()
    with metrics.measure_publication_step("provider_child"):
        pass
    with metrics.publication_details(logger):
        with metrics.measure_publication_step("private target and credentials"):
            pass
        with metrics.measure_publication_step("provider_child"):
            pass
        with pytest.raises(ValueError):
            with metrics.measure_publication_step("provider_child"):
                raise ValueError("private spreadsheet content")
    assert records(logger) == {"provider_child": (2, 1, 5000)}
    assert "private" not in str(logger.mock_calls)
    assert metrics._active.get() is None


def test_nested_scopes_and_other_threads_do_not_share_counts():
    outer, inner = Mock(), Mock()
    with metrics.publication_details(outer):
        with metrics.measure_publication_step("request_lookup"):
            pass
        with metrics.publication_details(inner):
            with metrics.measure_publication_step("provider_child"):
                pass
        with ThreadPoolExecutor(max_workers=1) as executor:
            assert executor.submit(lambda: metrics._active.get()).result() is None
        with metrics.measure_publication_step("request_lookup"):
            pass
    assert set(records(outer)) == {"request_lookup"}
    assert records(outer)["request_lookup"][0] == 2
    assert set(records(inner)) == {"provider_child"}


@pytest.mark.parametrize("failure", ["clock", "logger"])
def test_diagnostic_failure_does_not_change_business_outcome(monkeypatch, failure):
    logger = Mock()
    if failure == "clock":
        monkeypatch.setattr(metrics, "monotonic", Mock(side_effect=OSError("private")))
    else:
        logger.info.side_effect = OSError("private")
    with pytest.raises(ValueError, match="original"):
        with metrics.publication_details(logger):
            with metrics.measure_publication_step("provider_child"):
                raise ValueError("original")
    assert metrics._active.get() is None


@pytest.mark.parametrize("failure", [None, "enter", "body", "close", "suppressed"])
def test_probe_preserves_context_arguments_and_never_retries(failure):
    calls = []
    original = ValueError("original")

    class Manager:
        def __enter__(self):
            calls.append("enter")
            if failure == "enter":
                raise original
            return self

        def __exit__(self, kind, value, trace):
            calls.append(("close", kind, value))
            if failure == "close":
                raise original
            return failure == "suppressed"

    manager = Manager()
    streams = SimpleNamespace(probe=Mock(return_value=manager))
    logger = Mock()

    def run():
        with metrics.publication_details(logger), metrics.measured_probe(streams, {}) as opened:
            assert opened is manager
            if failure in {"body", "suppressed"}:
                raise original

    if failure in {"enter", "body", "close"}:
        with pytest.raises(ValueError) as caught:
            run()
        assert caught.value is original
    else:
        run()
    streams.probe.assert_called_once_with({})
    assert len(calls) == (1 if failure == "enter" else 2)
    if failure in {"body", "suppressed"}:
        assert calls[-1] == ("close", ValueError, original)
    assert metrics._active.get() is None


def test_budget_distinguishes_durable_reservations_from_waits(monkeypatch):
    now = [0]
    monkeypatch.setattr(metrics, "monotonic", lambda: now[0])
    dal = Mock()

    def reserve(*args):
        now[0] += 2
        return {"WaitSeconds": 3, "ReservedUTC": "reserved"}

    def refresh(*args):
        now[0] += 1
        return {"WaitSeconds": 0, "ReservedUTC": "reserved"}

    dal.reserve_request.side_effect = reserve
    dal.refresh_reservation.side_effect = refresh
    budget = RequestBudget(
        dal, "private account", sleep=lambda seconds: now.__setitem__(0, now[0] + seconds)
    )
    logger = Mock()
    with metrics.publication_details(logger), metrics.measure_publication_step("request_budget"):
        budget()
    assert records(logger) == {
        "budget_sql": (2, 0, 3000),
        "budget_wait": (1, 0, 3000),
        "request_budget": (1, 0, 6000),
    }
    dal.reserve_request.assert_called_once_with("private account")
    dal.refresh_reservation.assert_called_once_with("private account", "reserved")
