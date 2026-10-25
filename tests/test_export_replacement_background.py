import threading
from types import SimpleNamespace
from unittest.mock import Mock

from services.export_execution_authority import ExportExecutionAuthority
from services.export_replacement_verification import ReplacementVerificationPlan
from services.export_replacement_verification_service import ReplacementVerificationService
from tests.test_export_replacement_verification import value


def test_slow_verification_returns_control_and_drain_owns_its_thread(monkeypatch):
    root = ExportExecutionAuthority(
        dal=Mock(), store=Mock(), host=Mock(), budget_factory=Mock(), session_id="test"
    )
    service = ReplacementVerificationService(dal=Mock(), authority=root, proposals=Mock())
    plan = ReplacementVerificationPlan(value())
    key = plan.value()["plan_id"]
    entered, release = threading.Event(), threading.Event()
    worker = SimpleNamespace(drain=Mock(return_value=True))
    starts = []

    def admit(*args, **kwargs):
        if starts:
            return None
        starts.append(key)
        root._replacement_readers[key] = worker
        return worker, {}

    def run(*args):
        entered.set()
        assert release.wait(3)

    monkeypatch.setattr(service, "_admit", admit)
    monkeypatch.setattr(service, "_run_owned", run)
    monkeypatch.setattr(service, "inspect", lambda _: dict(state="checking"))
    try:
        assert service.start(plan, actor="recovery:" + key, reason="Check")["state"] == "checking"
        assert entered.wait(2)
        assert root._lock.acquire(timeout=0.2)
        root._lock.release()
        service.start(plan, actor="recovery:" + key, reason="Check")
        assert len(starts) == 1 and len(root._replacement_threads) == 1
        root.stop()
    finally:
        release.set()
        assert root.drain()
    worker.drain.assert_called_once()
    assert not root._replacement_threads[key].is_alive()


def test_unverified_replacement_child_prevents_clean_authority_drain():
    root = ExportExecutionAuthority(
        dal=Mock(), store=Mock(), host=Mock(), budget_factory=Mock(), session_id="test"
    )
    root._replacement_readers["unfinished"] = SimpleNamespace(drain=Mock(return_value=False))
    assert not root.drain()
