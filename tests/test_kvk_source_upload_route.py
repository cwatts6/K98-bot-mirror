from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from tests.test_kvk_source_admin import ACCESS
from upload_routes.kvk_source_route import KvkSourceRouteDeps, handle_kvk_source_upload


def message():
    member = SimpleNamespace(id=11, roles=[SimpleNamespace(id=40)], bot=False)
    return SimpleNamespace(
        id=100,
        content="16",
        author=member,
        guild=SimpleNamespace(id=20, fetch_member=AsyncMock(return_value=member)),
        channel=SimpleNamespace(id=30, send=AsyncMock()),
        attachments=[
            SimpleNamespace(
                id=200, filename="bad.xlsx", size=3, read=AsyncMock(return_value=b"bad")
            )
        ],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["disabled", "other_channel", "no_attachment"])
async def test_unmatched_route_has_no_side_effects(case):
    msg = message()
    access = ACCESS
    if case == "disabled":
        access = replace(access, enabled=False)
    if case == "other_channel":
        msg.channel.id = 99
    if case == "no_attachment":
        msg.attachments = []
    factory = Mock(side_effect=AssertionError("must not initialize"))
    assert await handle_kvk_source_upload(msg, KvkSourceRouteDeps(access, factory)) is False
    factory.assert_not_called()
    msg.guild.fetch_member.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case", ["collision", "guild", "role", "two_files", "xls", "csv", "oversize", "zero", "bot"]
)
async def test_recognized_invalid_source_never_falls_through_or_downloads(case):
    msg = message()
    access = ACCESS
    if case == "collision":
        access = replace(access, collision_channels=frozenset({30}))
    if case == "guild":
        msg.guild.id = 99
    if case == "role":
        msg.author.roles = []
    if case == "two_files":
        msg.attachments *= 2
    if case in ("xls", "csv"):
        msg.attachments[0].filename = "bad." + case
    if case == "oversize":
        msg.attachments[0].size = 20 * 1024 * 1024 + 1
    if case == "zero":
        msg.attachments[0].size = 0
    if case == "bot":
        msg.author.bot = True
    factory = Mock()
    assert await handle_kvk_source_upload(msg, KvkSourceRouteDeps(access, factory)) is True
    factory.assert_not_called()
    msg.attachments[0].read.assert_not_called()
    assert msg.channel.send.call_args.kwargs["allowed_mentions"].to_dict() == {"parse": []}


@pytest.mark.asyncio
async def test_role_loss_during_download_rejects_before_persistence():
    msg = message()
    msg.guild.fetch_member.side_effect = [msg.author, SimpleNamespace(id=11, roles=[])]
    factory = Mock()
    assert await handle_kvk_source_upload(msg, KvkSourceRouteDeps(ACCESS, factory))
    factory.assert_not_called()


@pytest.mark.asyncio
async def test_false_advertised_size_and_download_failure_are_consumed():
    for content in (b"x" * (20 * 1024 * 1024 + 1), RuntimeError("private field and token")):
        msg = message()
        if isinstance(content, Exception):
            msg.attachments[0].read.side_effect = content
        else:
            msg.attachments[0].read.return_value = content
        factory = Mock()
        assert await handle_kvk_source_upload(msg, KvkSourceRouteDeps(ACCESS, factory))
        factory.assert_not_called()
        assert "private field" not in str(msg.channel.send.call_args)


@pytest.mark.asyncio
async def test_success_creates_one_owner_view_off_event_loop(monkeypatch):
    import ui.views.kvk_source_import_view as views

    msg = message()
    row = {"AttemptID": "receipt"}
    service = SimpleNamespace(
        stage_upload=Mock(return_value=row), summary=lambda row: "Receipt only"
    )
    view = Mock(return_value="view")
    monkeypatch.setattr(views, "KvkSourceImportView", view)
    offload = AsyncMock(side_effect=lambda fn, *args, **kwargs: fn(*args, **kwargs))
    assert await handle_kvk_source_upload(msg, KvkSourceRouteDeps(ACCESS, lambda: service, offload))
    assert offload.await_count == 2
    assert service.stage_upload.call_args.kwargs["season"] == 16
    view.assert_called_once_with(service, row)
    assert msg.channel.send.call_args.kwargs["view"] == "view"
