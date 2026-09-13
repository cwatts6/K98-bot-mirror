import asyncio
import json
import threading
from unittest.mock import AsyncMock

import pytest

from stats_alerts import kvk_diagnostic_sessions as sessions
from stats_alerts.dispatch_reservations import DispatchUnavailable
from stats_alerts.kvk_diagnostics import PreviewPayload, PreviewRunner


def opened(tmp_path):
    repo = sessions.PreviewRepository(tmp_path / "preview")
    return repo, repo.open(10, 20, 30)


def test_ownership_capacity_corruption_and_independent_sessions(tmp_path, monkeypatch):
    repo, session = opened(tmp_path)
    for ids in [(10, 20, 31), (11, 20, 30), (10, 21, 30)]:
        with pytest.raises((DispatchUnavailable, FileNotFoundError)):
            repo.open(*ids, session.token)
    for token in ["../x", "A" * 32, "", True]:
        with pytest.raises(ValueError):
            repo.open(10, 20, 30, token)
    other = repo.open(10, 20, 30)
    assert other.path != session.path
    monkeypatch.setattr(sessions, "MAX_SESSIONS", 2)
    with pytest.raises(DispatchUnavailable):
        repo.open(10, 20, 30)
    assert repo.open(10, 20, 30, session.token).token == session.token
    (session.path / "publication.json").write_text("{}")
    with pytest.raises(DispatchUnavailable):
        session.snapshot()


def test_accepted_receipt_recovery_and_uncertain_guard(tmp_path):
    repo, session = opened(tmp_path)
    session.begin("a" * 32)
    session.transition("a" * 32, "sending", digest="d" * 64)
    session.transition("a" * 32, "accepted", receipt=100)
    session.finish("a" * 32)
    reopened = repo.open(10, 20, 30, session.token)
    reopened.begin("b" * 32)
    assert reopened.snapshot()["message_id"] == 100
    assert reopened.snapshot()["operations"][0]["phase"] == "committed"
    reopened.transition("b" * 32, "editing")
    reopened.finish("b" * 32)
    with pytest.raises(DispatchUnavailable):
        reopened.begin("c" * 32)


@pytest.mark.asyncio
@pytest.mark.parametrize("when", ["build", "network"])
async def test_shutdown_cancellation_preserves_uncertainty(tmp_path, when):
    repo = sessions.PreviewRepository(tmp_path / "preview")
    runner = PreviewRunner()
    started = asyncio.Event()

    async def build():
        if when == "build":
            started.set()
            await asyncio.Future()
        return PreviewPayload(None, True, "", "a" * 64)

    async def publish(preview, message_id, before_send):
        await before_send()
        started.set()
        await asyncio.Future()

    task = asyncio.create_task(
        runner.execute(
            guild_id=10,
            channel_id=20,
            owner_id=30,
            token=None,
            action="run",
            repository=repo,
            build=build,
            publish=publish,
        )
    )
    await asyncio.wait_for(started.wait(), 5)
    await runner.shutdown()
    assert task.cancelled() and runner.active is None and runner.stopping
    publication = next(repo.root.rglob("publication.json"))
    phase = json.loads(publication.read_text())["operations"][-1]["phase"]
    assert phase == ("failed" if when == "build" else "sending")
    assert json.loads((repo.root / "operation.json").read_text())["active"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("failure_phase", ["accepted", "committed"])
async def test_positive_receipt_disk_failure_is_uncertain(tmp_path, monkeypatch, failure_phase):
    repo = sessions.PreviewRepository(tmp_path / "preview")
    original = sessions.PreviewSession.transition

    def fail(self, operation, phase, **kwargs):
        if phase == failure_phase:
            raise OSError("disk")
        return original(self, operation, phase, **kwargs)

    monkeypatch.setattr(sessions.PreviewSession, "transition", fail)

    async def publish(preview, message_id, before_send):
        await before_send()
        return 100

    result = await PreviewRunner().execute(
        guild_id=10,
        channel_id=20,
        owner_id=30,
        token=None,
        action="run",
        repository=repo,
        build=AsyncMock(return_value=PreviewPayload(None, True, "", "a" * 64)),
        publish=publish,
    )
    assert result.outcome == "uncertain" and result.receipt == 100
    phase = repo.open(10, 20, 30, result.session).snapshot()["operations"][-1]["phase"]
    assert phase == ("sending" if failure_phase == "accepted" else "accepted")
    assert result.snapshot["operations"][-1]["phase"] == phase


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["build", "send", "edit", "finish"])
async def test_failure_result_contains_final_saved_snapshot(tmp_path, monkeypatch, failure):
    repo, session = opened(tmp_path)
    if failure == "edit":
        session.begin("a" * 32)
        session.transition("a" * 32, "sending")
        session.transition("a" * 32, "accepted", receipt=100)
        session.transition("a" * 32, "committed")
        session.finish("a" * 32)

    async def build():
        if failure == "build":
            raise RuntimeError("renderer failed")
        return PreviewPayload(None, True, "", "a" * 64)

    async def publish(preview, message_id, before_send):
        await before_send()
        if failure in {"send", "edit"}:
            raise OSError("publication uncertain")
        return 100

    if failure == "finish":

        def fail_finish(self, operation):
            raise OSError("lease finalization failed")

        monkeypatch.setattr(sessions.PreviewSession, "finish", fail_finish)

    runner = PreviewRunner()
    result = await runner.execute(
        guild_id=10,
        channel_id=20,
        owner_id=30,
        token=session.token,
        action="run",
        repository=repo,
        build=build,
        publish=publish,
    )
    assert result.outcome == ("failed" if failure == "build" else "uncertain")
    assert result.snapshot == session.snapshot()
    row = result.snapshot["operations"][-1]
    assert (
        row["phase"]
        == {"build": "failed", "send": "sending", "edit": "editing", "finish": "committed"}[failure]
    )
    assert row["token"] and row["updated_at"]
    assert runner.active is None


@pytest.mark.asyncio
async def test_failure_snapshot_read_is_best_effort(tmp_path, monkeypatch):
    repo, session = opened(tmp_path)

    def unreadable(self):
        raise OSError("state unavailable")

    async def build():
        monkeypatch.setattr(sessions.PreviewSession, "snapshot", unreadable)
        raise RuntimeError("renderer failed")

    runner = PreviewRunner()
    publish = AsyncMock()
    result = await runner.execute(
        guild_id=10,
        channel_id=20,
        owner_id=30,
        token=session.token,
        action="run",
        repository=repo,
        build=build,
        publish=publish,
    )
    assert result.outcome == "failed" and result.snapshot is None
    assert "saved state could not be read" in result.detail
    publish.assert_not_awaited()
    assert runner.active is None


@pytest.mark.asyncio
async def test_cancelled_file_offload_enters_once_and_drains(tmp_path, monkeypatch):
    repo = sessions.PreviewRepository(tmp_path / "preview")
    entered, release = threading.Event(), threading.Event()
    original = sessions.PreviewSession.transition
    calls = []

    def blocked(self, operation, phase, **kwargs):
        calls.append(phase)
        if phase == "sending":
            entered.set()
            assert release.wait(5)
        return original(self, operation, phase, **kwargs)

    monkeypatch.setattr(sessions.PreviewSession, "transition", blocked)
    publish_calls = []

    async def publish(preview, message_id, before_send):
        await before_send()
        publish_calls.append(1)
        return 100

    runner = PreviewRunner()
    task = asyncio.create_task(
        runner.execute(
            guild_id=10,
            channel_id=20,
            owner_id=30,
            token=None,
            action="run",
            repository=repo,
            build=AsyncMock(return_value=PreviewPayload(None, True, "", "a" * 64)),
            publish=publish,
        )
    )
    try:
        assert await asyncio.to_thread(entered.wait, 5)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert calls.count("sending") == 1 and not publish_calls
    assert runner.active is None
    publication = next(repo.root.rglob("publication.json"))
    assert json.loads(publication.read_text())["operations"][-1]["phase"] == "sending"


def test_root_admission_unknown_owner_and_capacity_preflight(tmp_path, monkeypatch):
    repo, first = opened(tmp_path)
    second = repo.open(10, 20, 30)
    first.begin("a" * 32)
    with pytest.raises(DispatchUnavailable):
        second.begin("b" * 32)
    monkeypatch.setattr(sessions, "_owner_alive", lambda _: None)
    with pytest.raises(DispatchUnavailable):
        second.begin("b" * 32)
    first.finish("a" * 32)
    monkeypatch.setattr(sessions, "MAX_STATE_BYTES", 8192)
    with pytest.raises(DispatchUnavailable):
        second.begin("b" * 32)
    assert second.snapshot()["operations"] == []


@pytest.mark.parametrize(
    "field,value", [("version", True), ("generation", True), ("message_id", True)]
)
def test_strict_publication_types(tmp_path, field, value):
    repo, session = opened(tmp_path)
    path = session.path / "publication.json"
    data = json.loads(path.read_text())
    data[field] = value
    path.write_text(json.dumps(data))
    with pytest.raises(DispatchUnavailable):
        repo.open(10, 20, 30, session.token)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "action,token", [("status", None), ("legacy", None), ("run", "../foreign")]
)
async def test_invalid_selector_does_not_allocate(tmp_path, action, token):
    repo = sessions.PreviewRepository(tmp_path / "preview")
    with pytest.raises(ValueError):
        await PreviewRunner().execute(
            guild_id=10,
            channel_id=20,
            owner_id=30,
            token=token,
            action=action,
            repository=repo,
            build=AsyncMock(),
            publish=AsyncMock(),
        )
    assert not repo.root.exists()
