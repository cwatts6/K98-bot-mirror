"""Stage cancellation, registration and receipt truthfulness boundaries."""

import asyncio
from contextlib import contextmanager
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest

from services import processing_pipeline_receipts as receipts
from services.producer_recovery_intent import atomic_producer_intent, current_intent


@pytest.mark.asyncio
async def test_cancelled_waiter_retains_guard_until_worker_and_receipt_finish(monkeypatch):
    started, release = asyncio.Event(), asyncio.Event()
    operation, run_id = str(uuid4()), str(uuid4())
    history = []

    @contextmanager
    def guard(_):
        history.append("guard_acquired")
        try:
            yield
        finally:
            history.append("guard_released")

    dal = SimpleNamespace(
        guard=guard,
        start=lambda *a, **k: operation,
        observe=lambda *a, **k: history.append("receipt"),
    )
    monkeypatch.setattr(receipts, "result_evidence", lambda *a: ({"outcome": "verified"}, True))

    @atomic_producer_intent("configuration_import")
    def producer():
        assert current_intent()["operation"] == operation

    async def worker():
        producer()
        started.set()
        await release.wait()
        history.append("worker_finished")

    token = receipts._pipeline.set((dal, run_id))
    try:
        pending = asyncio.create_task(receipts.stage("configuration", worker))
        await started.wait()
        pending.cancel()
        await asyncio.sleep(0)
        assert not pending.done()
        assert history == ["guard_acquired"]
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await pending
        assert history == ["guard_acquired", "worker_finished", "receipt", "guard_released"]
        assert receipts.producer_operation() is None
    finally:
        receipts._pipeline.reset(token)


@pytest.mark.asyncio
async def test_registration_ack_loss_never_starts_business_work(monkeypatch):
    calls = []
    runtime = object()
    monkeypatch.setattr(receipts, "pipeline_runtime", lambda: runtime)

    def create(*args, **kwargs):
        calls.append("run_committed")
        raise TimeoutError("registration reply lost")

    monkeypatch.setattr(receipts, "PipelineReceiptDAL", lambda _: SimpleNamespace(create=create))

    @receipts.record_pipeline
    async def pipeline(*args, **kwargs):
        calls.append("import_started")

    with pytest.raises(TimeoutError):
        await pipeline(1, seed="A", filename="input.xlsx", channel_id=1)
    assert calls == ["run_committed"]


def test_released_reservation_and_boolean_success_cannot_certify_import():
    dal = SimpleNamespace(preparation=lambda _: None)
    proof, complete = receipts.result_evidence(dal, "import", str(uuid4()), True)
    assert not complete
    assert proof["outcome"] == "request_not_recorded"


def test_generic_cache_wrapper_return_is_not_a_cache_receipt():
    proof, complete = receipts.result_evidence(None, "player_cache", str(uuid4()), None)
    assert not complete
    assert proof["outcome"] == "cache_unconfirmed"


@pytest.mark.asyncio
async def test_lost_observation_ack_is_preserved_not_replayed(monkeypatch):
    calls = []
    operation = str(uuid4())

    @contextmanager
    def guard(_):
        yield

    def observe(*args, **kwargs):
        calls.append("receipt_attempt")
        raise TimeoutError("receipt acknowledgement unknown")

    dal = SimpleNamespace(guard=guard, start=lambda *a, **k: operation, observe=observe)
    monkeypatch.setattr(receipts, "result_evidence", lambda *a: ({"outcome": "verified"}, True))
    token = receipts._pipeline.set((dal, str(uuid4())))
    try:
        with pytest.raises(TimeoutError):
            await receipts.stage("configuration", lambda: calls.append("business_call"))
        assert calls.count("business_call") == 1
    finally:
        receipts._pipeline.reset(token)


@pytest.mark.parametrize(
    "disposition,allowed",
    [("configuration_only_v1", False), (None, False), ("pipeline_export_v1", True)],
)
def test_pipeline_cannot_export_a_sql_only_configuration_successor(
    monkeypatch, disposition, allowed
):
    from services.processing_pipeline_receipt_dal import STAGES
    from services.processing_pipeline_recovery import ProcessingPipelineRecovery

    child = dict(
        PreparationID=str(uuid4()),
        State="captured",
        RequestJson=json.dumps({"request": {"producer": {"export_disposition": disposition}}}),
    )
    state = dict(
        stages={
            name: dict(
                State="not_started" if name == "export" else "observed",
                OperationID=str(uuid4()),
                EvidenceJson=None,
            )
            for name in STAGES
        },
        children={"import": None, "player_cache": None, "configuration": child},
        reads={"configuration": None},
        run={"InputsJson": "{}"},
    )
    adapter = ProcessingPipelineRecovery(SimpleNamespace(token=lambda _: "a" * 64))
    monkeypatch.setattr(adapter, "_state", lambda _: state)
    evidence, _, complete = adapter.inspect(str(uuid4()))
    assert not complete
    assert ("continue_stage" in evidence["actions"]) is allowed
