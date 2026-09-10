from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest

from stats_alerts import guard, state
from stats_alerts.embeds import kvk
from stats_alerts.kvk_diagnostic_sessions import PreviewRepository
from stats_alerts.kvk_diagnostics import PreviewPayload, PreviewRunner


@pytest.fixture
def preview_data(monkeypatch):
    monkeypatch.setattr(
        kvk,
        "get_latest_kvk_metadata_sql",
        lambda: dict(
            kvk_no=16,
            kvk_name="Season",
            start_date=datetime(2026, 1, 1, tzinfo=UTC),
            end_date=datetime(2026, 2, 1, tzinfo=UTC),
        ),
    )
    monkeypatch.setattr(
        kvk,
        "load_allkingdom_blocks",
        lambda _: dict(players_by_kills=[dict(name="Alice", kills_gain=1)]),
    )
    monkeypatch.setattr(kvk, "get_latest_honor_top", AsyncMock(return_value=[]))


class Channel:
    id = 20

    def __init__(self):
        self.sent = []
        self.edits = []
        self.message = None
        self.error = None

    async def send(self, **payload):
        self.sent.append(payload)
        if self.error:
            raise self.error
        self.message = SimpleNamespace(
            id=100, author=SimpleNamespace(id=30), channel=self, edit=self.edit
        )
        return self.message

    async def edit(self, **payload):
        self.edits.append(payload)
        if self.error:
            raise self.error

    async def fetch_message(self, message_id):
        if self.message is None:
            raise LookupError("missing")
        return self.message


async def run(
    repo, channel, *, token=None, action="run", runner=None, check=lambda: None, build=None
):
    async def publish(preview, message_id, before_send):
        return await kvk.publish_kvk_preview(
            SimpleNamespace(user=SimpleNamespace(id=30)),
            channel,
            preview,
            message_id,
            before_send,
            check,
        )

    return await (runner or PreviewRunner()).execute(
        guild_id=10,
        channel_id=20,
        owner_id=30,
        token=token,
        action=action,
        repository=repo,
        build=build or (lambda: kvk.build_kvk_preview("test")),
        publish=publish,
    )


@pytest.mark.asyncio
async def test_send_edit_restart_status_and_production_isolation(
    tmp_path, monkeypatch, preview_data
):
    production = tmp_path / "production"
    production.mkdir()
    for name in (
        "alerts.csv",
        "alerts.csv.dispatch.json",
        "message.json",
        "phase2h.json",
        "active_reminders.json",
    ):
        (production / name).write_text("production sentinel")
    monkeypatch.setattr(guard, "LOG_PATH", str(production / "alerts.csv"))
    monkeypatch.setattr(state, "STATE_PATH", str(production / "message.json"))
    baseline = {p.name: p.read_bytes() for p in production.iterdir()}
    repo = PreviewRepository(tmp_path / "preview")
    channel = Channel()
    sent = await run(repo, channel)
    assert sent.outcome == "sent" and sent.receipt == 100
    before = {str(p): p.read_bytes() for p in repo.root.rglob("*") if p.is_file()}
    status = await run(
        repo,
        channel,
        token=sent.session,
        action="status",
        build=AsyncMock(side_effect=AssertionError("status built")),
    )
    assert status.snapshot["operations"][-1]["phase"] == "committed"
    assert before == {str(p): p.read_bytes() for p in repo.root.rglob("*") if p.is_file()}
    reopened = await run(PreviewRepository(repo.root), channel, token=sent.session)
    assert reopened.outcome == "edited" and reopened.receipt == 100
    assert len(channel.sent) == len(channel.edits) == 1
    for payload in channel.sent + channel.edits:
        assert len(payload["embeds"]) == 2
        assert payload["allowed_mentions"].to_dict() == {"parse": []}
    assert baseline == {p.name: p.read_bytes() for p in production.iterdir()}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure", ["send", "edit", "missing", "foreign", "wrong_id", "destination"]
)
async def test_never_replace_on_error(tmp_path, preview_data, failure):
    repo, channel = PreviewRepository(tmp_path / "preview"), Channel()
    if failure == "send":
        channel.error = RuntimeError("ambiguous")
        result = await run(repo, channel)
        assert result.outcome == "uncertain"
    else:
        first = await run(repo, channel)
        if failure == "edit":
            channel.error = RuntimeError("ambiguous")
        elif failure == "missing":
            channel.message = None
        elif failure == "foreign":
            channel.message.author.id = 999
        elif failure == "wrong_id":
            channel.message.id = 999
        check = (
            (lambda: (_ for _ in ()).throw(ValueError("revoked")))
            if failure == "destination"
            else lambda: None
        )
        result = await run(repo, channel, token=first.session, check=check)
        assert result.outcome == ("uncertain" if failure == "edit" else "failed")
    count = len(channel.sent)
    if failure in {"send", "edit"}:
        again = await run(repo, channel, token=result.session)
        assert again.outcome == "guarded"
    assert len(channel.sent) == count == 1


@pytest.mark.asyncio
async def test_unavailable_and_grouped_overflow_never_send(tmp_path, preview_data, monkeypatch):
    repo, channel = PreviewRepository(tmp_path / "preview"), Channel()
    monkeypatch.setattr(kvk, "load_allkingdom_blocks", lambda _: {})
    result = await run(repo, channel)
    assert result.outcome == "unavailable" and not channel.sent

    async def huge():
        return PreviewPayload(
            [discord.Embed(description="x" * 4000), discord.Embed(description="x" * 4000)],
            True,
            "",
            "a" * 64,
        )

    result = await run(repo, channel, token=result.session, build=huge)
    assert result.outcome == "failed" and not channel.sent


@pytest.mark.asyncio
@pytest.mark.parametrize("is_test", [True, False])
async def test_legacy_production_payload_and_return_preserved(preview_data, is_test):
    channel = Channel()
    expected = await kvk.build_kvk_preview("same")
    assert await kvk.send_kvk_embed(None, channel, "same", is_test=is_test) is None
    sent = channel.sent[0]
    assert [e.to_dict() for e in sent["embeds"]] == [e.to_dict() for e in expected.payload]
    assert sent["content"] == (None if is_test else "@everyone")
    assert (
        sent["allowed_mentions"].to_dict()
        == discord.AllowedMentions(everyone=not is_test).to_dict()
    )
    channel.error = RuntimeError("legacy swallow")
    assert await kvk.send_kvk_embed(None, channel, "same", is_test=is_test) is None


def test_source_session_v3_pins_selection_and_keeps_legacy_readable(tmp_path):
    from kvk.schemas.new_source_schema import SOURCE_KEY
    from stats_alerts.dispatch_reservations import DispatchUnavailable
    from tests.test_kvk_source_reporting import PERIOD, PUBLICATION

    repo = PreviewRepository(tmp_path / "sessions")
    selection = dict(source_key=SOURCE_KEY, period_id=PERIOD, publication_id=PUBLICATION)
    old = repo.open(1, 2, 3, kvk_no=16)
    session = repo.open(1, 2, 3, kvk_no=16, source_selection=selection)
    assert session.manifest["version"] == 3
    assert repo.open(1, 2, 3, session.token).manifest == session.manifest
    assert repo.open(1, 2, 3, old.token).manifest == old.manifest
    with pytest.raises(DispatchUnavailable, match="cannot change"):
        repo.open(1, 2, 3, session.token, source_selection=dict(selection, publication_id=PERIOD))
    with pytest.raises(DispatchUnavailable, match="Legacy"):
        repo.open(1, 2, 3, old.token, source_selection=selection)
    with pytest.raises(DispatchUnavailable, match="owner"):
        repo.open(1, 2, 4, session.token)


@pytest.mark.asyncio
async def test_source_runner_reuses_saved_selection_on_restart(tmp_path):
    from kvk.schemas.new_source_schema import SOURCE_KEY
    from tests.test_kvk_source_reporting import PERIOD, PUBLICATION

    repo = PreviewRepository(tmp_path / "sessions")
    selection = dict(source_key=SOURCE_KEY, period_id=PERIOD, publication_id=PUBLICATION)
    session = repo.open(1, 2, 3, kvk_no=16, source_selection=selection)
    build = AsyncMock(return_value=PreviewPayload([], False, "publication changed", ""))
    publish = AsyncMock(side_effect=AssertionError("No external delivery"))
    result = await PreviewRunner().execute(
        guild_id=1,
        channel_id=2,
        owner_id=3,
        token=session.token,
        action="run",
        build=build,
        publish=publish,
        repository=PreviewRepository(repo.root),
    )
    build.assert_awaited_once_with(kvk_no=16, source_selection=selection)
    publish.assert_not_awaited()
    assert result.outcome == "unavailable"


@pytest.mark.asyncio
async def test_explicit_source_preview_bypasses_legacy_reads(monkeypatch):
    from unittest.mock import Mock

    from kvk.schemas.new_source_schema import SOURCE_KEY
    from stats_alerts import allkingdoms
    from tests.test_kvk_source_reporting import PERIOD, PUBLICATION, load_synthetic

    report, _, _, _ = load_synthetic(monkeypatch)
    load = Mock(return_value=report)
    monkeypatch.setattr(allkingdoms, "load_allkingdom_report_v2", load)
    monkeypatch.setattr(
        kvk, "get_latest_kvk_metadata_sql", Mock(side_effect=AssertionError("legacy"))
    )
    preview = await kvk.build_kvk_preview(
        "not scan time",
        kvk_no=16,
        source_selection=dict(source_key=SOURCE_KEY, period_id=PERIOD, publication_id=PUBLICATION),
        connect=Mock(),
    )
    assert preview.available
    load.assert_called_once()
    assert "not scan time" not in str(preview.payload[0].to_dict())
