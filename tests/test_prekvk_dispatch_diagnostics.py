from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
import json
from types import SimpleNamespace

import pytest

from stats_alerts import guard, state
from stats_alerts.diagnostic_sessions import SessionRepository
from stats_alerts.diagnostics import DiagnosticRunner, validate_destination
from stats_alerts.dispatch_reservations import DispatchUnavailable
from stats_alerts.embeds import prekvk


@pytest.fixture
def harness(tmp_path, monkeypatch):
    production = tmp_path / "production"
    production.mkdir()
    for name in (
        "alerts.csv",
        "alerts.csv.dispatch.json",
        "message.json",
        "alerts.csv.dispatch.lck",
        "message.json.lck",
    ):
        (production / name).write_bytes(b"production sentinel\n")
    monkeypatch.setattr(guard, "LOG_PATH", str(production / "alerts.csv"))
    monkeypatch.setattr(state, "STATE_PATH", str(production / "message.json"))
    monkeypatch.setattr(state, "_STATE_LOCK_PATH", str(production / "message.json.lck"))
    baseline = {p.name: p.read_bytes() for p in production.iterdir()}
    monkeypatch.setattr(prekvk, "get_latest_kvk_metadata_sql", lambda: None)
    monkeypatch.setattr(prekvk, "get_all_upcoming_events", lambda: [])

    async def honor(_n):
        return []

    monkeypatch.setattr(prekvk, "get_latest_honor_top", honor)
    repo = SessionRepository(tmp_path / "diagnostics")
    yield repo
    assert {p.name: p.read_bytes() for p in production.iterdir()} == baseline


class Channel:
    id = 20

    def __init__(self):
        self.sent = []
        self.edits = []
        self.messages = {}
        self.send_error = None
        self.edit_error = None

    async def send(self, **kwargs):
        self.sent.append(kwargs)
        if self.send_error:
            raise self.send_error
        message_id = 100 + len(self.sent)

        async def edit(**payload):
            self.edits.append(payload)
            if self.edit_error:
                raise self.edit_error

        message = SimpleNamespace(
            id=message_id,
            created_at=datetime.now(UTC),
            author=SimpleNamespace(id=30),
            channel=self,
            edit=edit,
        )
        self.messages[message_id] = message
        return message

    async def fetch_message(self, message_id):
        return self.messages[message_id]


def publisher(channel):
    async def publish(session, receipt):
        return await prekvk.send_prekvk_embed(
            SimpleNamespace(user=SimpleNamespace(id=30)),
            channel,
            "diagnostic",
            diagnostic_store=session.store,
            diagnostic_check_destination=lambda: None,
            diagnostic_view_factory=lambda events: None,
            on_diagnostic_receipt=lambda mid: setattr(receipt, "message_id", mid),
        )

    return publish


async def run(repo, channel, *, token=None, action="run", runner=None, publish=None):
    return await (runner or DiagnosticRunner()).execute(
        guild_id=10,
        channel_id=20,
        owner_id=30,
        token=token,
        action=action,
        repository=repo,
        publish=publish or publisher(channel),
    )


@pytest.mark.asyncio
async def test_real_send_edit_readonly_status_and_restart(harness):
    channel = Channel()
    first = await run(harness, channel)
    assert first.outcome == "sent"
    assert first.receipt == 101
    assert first.snapshot["attempt"]["phase"] == "committed"
    assert first.snapshot["rows"][0][2] == "prekvk_daily"
    session = harness.open(10, 20, 30, first.session)
    before = {str(p): p.read_bytes() for p in harness.root.rglob("*") if p.is_file()}
    status = await run(harness, channel, token=first.session, action="status")
    assert status.snapshot["guarded"] is True
    assert {str(p): p.read_bytes() for p in harness.root.rglob("*") if p.is_file()} == before
    reopened = SessionRepository(harness.root)
    edited = await run(reopened, channel, token=first.session)
    assert edited.outcome == "edited"
    assert len(channel.sent) == len(channel.edits) == 1
    for payload in channel.sent + channel.edits:
        assert payload["allowed_mentions"].to_dict() == {"parse": []}
        assert payload.get("content") is None
    # Separate real-store guard proof, without deleting a message or sending again.
    assert session.store.reserve("prekvk_daily", 20) is None
    assert len(channel.sent) == 1


@pytest.mark.asyncio
async def test_distinct_sessions_and_uncertain_send(harness):
    channel = Channel()
    first = await run(harness, channel)
    second = await run(harness, channel)
    assert first.session != second.session
    assert len(channel.sent) == 2
    channel.send_error = TimeoutError("unknown delivery")
    unknown = await run(harness, channel)
    assert unknown.outcome == "uncertain"
    assert unknown.snapshot["attempt"]["phase"] == "uncertain"
    repeat = await run(harness, channel, token=unknown.session)
    assert repeat.outcome == "guarded"
    assert len(channel.sent) == 3


@pytest.mark.asyncio
async def test_positive_receipt_projection_failure_reopens_without_send(harness, monkeypatch):
    session = harness.open(10, 20, 30)
    original = state.MessageStateStore.update_prekvk_message

    def fail(*args, **kwargs):
        raise OSError("projection unavailable")

    monkeypatch.setattr(state.MessageStateStore, "update_prekvk_message", fail)
    channel = Channel()
    result = await run(harness, channel, token=session.token)
    assert result.outcome == "uncertain" and result.receipt == 101
    assert result.snapshot["attempt"]["phase"] == "accepted"
    monkeypatch.setattr(state.MessageStateStore, "update_prekvk_message", original)
    recovered = await run(SessionRepository(harness.root), channel, token=session.token)
    assert recovered.outcome == "edited"
    assert recovered.snapshot["attempt"]["phase"] == "committed"
    assert len(channel.sent) == 1


@pytest.mark.asyncio
async def test_stale_clear_is_isolated_and_guarded(harness):
    channel = Channel()
    first = await run(harness, channel)
    channel.messages[101].created_at -= timedelta(days=1)
    repeat = await run(harness, channel, token=first.session)
    assert repeat.outcome == "guarded"
    assert repeat.snapshot["message_id"] is None
    assert repeat.snapshot["generation"] == 1
    assert len(channel.sent) == 1


@pytest.mark.asyncio
async def test_ambiguous_edit_never_falls_through_to_send(harness):
    channel = Channel()
    first = await run(harness, channel)
    channel.edit_error = TimeoutError("edit uncertain")
    result = await run(harness, channel, token=first.session)
    assert result.outcome == "uncertain"
    assert len(channel.sent) == 1
    assert harness.open(10, 20, 30, first.session).snapshot()["message_id"] == 101


@pytest.mark.parametrize(
    "name,payload",
    [
        ("message.json", "broken"),
        ("alerts.csv.dispatch.json", "{}"),
        ("alerts.csv", "invalid"),
        ("session.json", "{}"),
    ],
)
@pytest.mark.asyncio
async def test_corruption_fails_closed_without_repair(harness, name, payload):
    session = harness.open(10, 20, 30)
    target = session.path / name
    target.write_text(payload)
    channel = Channel()
    with pytest.raises((ValueError, KeyError, DispatchUnavailable)):
        await run(harness, channel, token=session.token)
    assert channel.sent == []
    assert target.read_text() == payload


@pytest.mark.parametrize("token", ["../escape", "A" * 32, "a" * 33, "C:\\state", "", "a/b"])
def test_token_cannot_select_path(harness, token):
    with pytest.raises(ValueError):
        harness.open(10, 20, 30, token)
    assert not harness.root.exists()


def test_owner_destination_and_missing_session_rejected(harness):
    session = harness.open(10, 20, 30)
    for guild, channel, owner in [(10, 20, 31), (11, 20, 30), (10, 21, 30)]:
        with pytest.raises((DispatchUnavailable, FileNotFoundError)):
            harness.open(guild, channel, owner, session.token)
    with pytest.raises(FileNotFoundError):
        harness.open(10, 20, 30, "a" * 32)


def test_capacity_counts_incomplete_sessions(harness, monkeypatch):
    from stats_alerts import diagnostic_sessions

    monkeypatch.setattr(diagnostic_sessions, "MAX_SESSIONS", 1)
    session = harness.open(10, 20, 30)
    (session.path / "session.json").unlink()
    with pytest.raises(DispatchUnavailable):
        harness.open(10, 20, 30)


@pytest.mark.parametrize(
    "change",
    [
        {"guild_id": 11},
        {"channel_guild_id": 11},
        {"channel_id": 99},
        {"is_text": False},
        {"requester_can_send": False},
        {"bot_can_publish": False},
    ],
)
def test_destination_boundary(change):
    values = dict(
        guild_id=10,
        expected_guild_id=10,
        channel_guild_id=10,
        channel_id=20,
        forbidden_channels={99},
        is_text=True,
        requester_can_send=True,
        bot_can_publish=True,
    )
    validate_destination(**values)
    values.update(change)
    with pytest.raises(ValueError):
        validate_destination(**values)


@pytest.mark.asyncio
async def test_session_lease_contention_and_unknown_owner(harness, monkeypatch):
    from stats_alerts import diagnostic_sessions

    one = harness.open(10, 20, 30)
    two = harness.open(10, 20, 30)
    operation = one.begin()
    for owner_state in (True, None):
        monkeypatch.setattr(diagnostic_sessions, "_owner_alive", lambda row: owner_state)
        with pytest.raises(DispatchUnavailable):
            two.begin()
    one.finish(operation)
    two.finish(two.begin())


@pytest.mark.asyncio
async def test_cancellation_during_real_send_retains_uncertainty(harness):
    entered = asyncio.Event()
    channel = Channel()

    async def send(**kwargs):
        entered.set()
        await asyncio.Event().wait()

    channel.send = send
    session = harness.open(10, 20, 30)
    task = asyncio.create_task(run(harness, channel, token=session.token))
    await asyncio.wait_for(entered.wait(), timeout=5)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    reopened = harness.open(10, 20, 30, session.token)
    assert reopened.snapshot()["attempt"]["phase"] == "uncertain"
    assert json.loads((harness.root / "operation.json").read_text())["active"] is False


def test_recovery_and_rollover_use_real_protocol(harness):
    session = harness.open(10, 20, 30)
    store = session.store
    token = store.reserve("prekvk_daily", 20)
    store.owner_alive = lambda row: False
    store.recover()
    assert store._read()["attempts"][token]["phase"] == "released"
    token = store.reserve("prekvk_daily", 20)
    store.start(token)
    store.recover()
    assert store._read()["attempts"][token]["phase"] == "uncertain"
    store.clock = lambda: datetime.now(UTC) + timedelta(days=1)
    assert store.reserve("prekvk_daily", 20) is None


@pytest.mark.asyncio
async def test_finalization_failure_never_reports_clean_success(harness, monkeypatch):
    from stats_alerts.diagnostic_sessions import DiagnosticSession

    def fail(*args):
        raise OSError("lease write failed")

    monkeypatch.setattr(DiagnosticSession, "finish", fail)
    result = await run(harness, Channel())
    assert result.outcome == "uncertain"
    assert result.receipt == 101
    assert "finalization failed" in result.detail


@pytest.mark.asyncio
async def test_status_without_lock_files_is_read_only(harness, monkeypatch):
    from filelock import BaseFileLock

    session = harness.open(10, 20, 30)
    for path in harness.root.rglob("*.lck"):
        path.unlink()
    before = {str(p): p.read_bytes() for p in harness.root.rglob("*") if p.is_file()}

    def reject_lock(*args, **kwargs):
        pytest.fail("Read-only status must not acquire a filesystem lock")

    monkeypatch.setattr(BaseFileLock, "acquire", reject_lock)
    result = await run(harness, Channel(), token=session.token, action="status")
    assert result.snapshot["message_id"] is None
    assert not list(harness.root.rglob("*.lck"))
    assert {str(p): p.read_bytes() for p in harness.root.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize(
    "missing", ["session.json", "alerts.csv", "alerts.csv.dispatch.json", "message.json"]
)
def test_missing_durable_session_file_fails_closed(harness, missing):
    session = harness.open(10, 20, 30)
    (session.path / missing).unlink()
    with pytest.raises(DispatchUnavailable, match="Incomplete diagnostic session"):
        session.validate()
