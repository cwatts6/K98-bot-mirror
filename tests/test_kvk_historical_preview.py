import json
from unittest.mock import AsyncMock, Mock

import pytest

from stats_alerts.dispatch_reservations import DispatchUnavailable
from stats_alerts.embeds import kvk
from stats_alerts.kvk_diagnostic_sessions import PreviewRepository
from stats_alerts.kvk_diagnostics import PreviewPayload, PreviewRunner


@pytest.mark.asyncio
@pytest.mark.parametrize("metadata", ["valid", "missing", "wrong_season", "error"])
async def test_exact_season_renderer_never_falls_back_or_mixes_honor(monkeypatch, metadata):
    selected = Mock(
        return_value=dict(kvk_no=15, kvk_name="Old season", start_date=None, end_date=None)
    )
    if metadata == "missing":
        selected.return_value = None
    elif metadata == "wrong_season":
        selected.return_value["kvk_no"] = 16
    elif metadata == "error":
        selected.side_effect = OSError("metadata unavailable")
    latest = Mock(side_effect=AssertionError("latest metadata used"))
    sheets = Mock(side_effect=AssertionError("Sheets fallback used"))
    blocks = Mock(return_value=dict(players_by_kills=[dict(name="Historic player", kills_gain=1)]))
    honor = AsyncMock(side_effect=AssertionError("latest-season honor used"))
    monkeypatch.setattr(kvk, "get_kvk_metadata_sql", selected)
    monkeypatch.setattr(kvk, "get_latest_kvk_metadata_sql", latest)
    monkeypatch.setattr(kvk, "get_latest_kvk_metadata", sheets)
    monkeypatch.setattr(kvk, "load_allkingdom_blocks", blocks)
    monkeypatch.setattr(kvk, "get_latest_honor_top", honor)
    result = await kvk.build_kvk_preview("test", kvk_no=15)
    selected.assert_called_once_with(15)
    latest.assert_not_called()
    sheets.assert_not_called()
    honor.assert_not_awaited()
    assert result.available == (metadata == "valid")
    if metadata == "valid":
        blocks.assert_called_once_with(15)
        assert "KVK 15" in result.payload[0].title
        assert "Honor omitted" in result.detail
    else:
        blocks.assert_not_called()


def snapshot_files(root):
    return {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}


@pytest.mark.asyncio
async def test_selected_session_reopens_status_and_edits_same_season(tmp_path):
    repo = PreviewRepository(tmp_path / "preview")
    build = AsyncMock(return_value=PreviewPayload([], True, "historical", "a" * 64))
    message_ids = []

    async def publish(preview, message_id, before_send):
        message_ids.append(message_id)
        await before_send()
        return 100

    kwargs = dict(
        guild_id=10, channel_id=20, owner_id=30, repository=repo, build=build, publish=publish
    )
    first = await PreviewRunner().execute(**kwargs, token=None, action="run", kvk_no=15)
    assert first.outcome == "sent" and "Selected KVK 15" in first.detail
    session = repo.open(10, 20, 30, first.session)
    assert session.manifest["version"] == 2 and session.manifest["kvk_no"] == 15
    before = snapshot_files(repo.root)
    status = await PreviewRunner().execute(**kwargs, token=first.session, action="status")
    assert "Selected KVK 15" in status.detail
    assert snapshot_files(repo.root) == before
    second = await PreviewRunner().execute(**kwargs, token=first.session, action="run")
    assert second.outcome == "edited" and second.receipt == 100
    assert message_ids == [None, 100]
    assert all(call.kwargs == {"kvk_no": 15} for call in build.await_args_list)
    before = snapshot_files(repo.root)
    for action in ("run", "status"):
        with pytest.raises(DispatchUnavailable, match="KVK cannot change"):
            await PreviewRunner().execute(**kwargs, token=first.session, action=action, kvk_no=16)
    assert snapshot_files(repo.root) == before
    assert len(message_ids) == 2


def test_legacy_current_session_preserved_and_cannot_be_retargeted(tmp_path):
    repo = PreviewRepository(tmp_path / "preview")
    session = repo.open(10, 20, 30)
    before = snapshot_files(repo.root)
    assert repo.open(10, 20, 30, session.token).manifest["version"] == 1
    with pytest.raises(DispatchUnavailable, match="cannot be retargeted"):
        repo.open(10, 20, 30, session.token, kvk_no=15)
    assert snapshot_files(repo.root) == before


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "15", 2147483648])
def test_invalid_selection_never_allocates(tmp_path, value):
    repo = PreviewRepository(tmp_path / "preview")
    with pytest.raises(ValueError):
        repo.open(10, 20, 30, kvk_no=value)
    assert not repo.root.exists()


@pytest.mark.parametrize("value", [None, True, "15", 0, 2147483648])
def test_invalid_saved_selection_fails_closed(tmp_path, value):
    repo = PreviewRepository(tmp_path / "preview")
    session = repo.open(10, 20, 30, kvk_no=15)
    manifest = dict(session.manifest, kvk_no=value)
    (session.path / "session.json").write_text(json.dumps(manifest))
    before = snapshot_files(repo.root)
    with pytest.raises(DispatchUnavailable, match="Invalid saved KVK"):
        repo.open(10, 20, 30, session.token)
    assert snapshot_files(repo.root) == before


def test_selected_session_retains_owner_boundary(tmp_path):
    repo = PreviewRepository(tmp_path / "preview")
    session = repo.open(10, 20, 30, kvk_no=15)
    with pytest.raises(DispatchUnavailable, match="owner/destination mismatch"):
        repo.open(10, 20, 31, session.token, kvk_no=15)
