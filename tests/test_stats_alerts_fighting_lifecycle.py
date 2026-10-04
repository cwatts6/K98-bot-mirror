from __future__ import annotations

from types import SimpleNamespace

import pytest

import file_utils
from stats_alerts import interface


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("fighting_open", "expected_route"),
    [(False, "prekvk"), (True, "kvk")],
)
async def test_stats_alert_route_changes_only_at_fighting_open(
    monkeypatch,
    fighting_open: bool,
    expected_route: str,
) -> None:
    calls: list[str] = []
    clears: list[bool] = []

    async def run_blocking(_func, **_kwargs):
        return fighting_open

    async def send_summary(*_args, **_kwargs):
        return None

    async def send_prekvk(*_args, **_kwargs):
        calls.append("prekvk")
        return "sent"

    async def send_kvk(*_args, **_kwargs):
        calls.append("kvk")

    monkeypatch.setattr(file_utils, "run_blocking_in_thread", run_blocking)
    monkeypatch.setattr(interface, "ks_mod", send_summary)
    monkeypatch.setattr(interface.prekvk_mod, "send_prekvk_embed", send_prekvk)
    monkeypatch.setattr(interface.kvk_mod, "send_kvk_embed", send_kvk)

    async def clear_message():
        clears.append(True)
        return True

    monkeypatch.setattr(interface, "clear_prekvk_message", clear_message)

    bot = SimpleNamespace(get_channel=lambda _channel_id: object())

    await interface.send_stats_update_embed(
        bot,
        "2026-08-27 16:00 UTC",
        is_kvk=True,
        is_test=True,
    )

    assert calls == [expected_route]
    assert clears == ([True] if fighting_open else [])


@pytest.mark.asyncio
async def test_interface_does_not_duplicate_prekvk_daily_claim(monkeypatch) -> None:
    calls: list[str] = []

    async def run_blocking(_func, **_kwargs):
        return False

    async def send_summary(*_args, **_kwargs):
        return None

    async def send_prekvk(*_args, **_kwargs):
        calls.append("prekvk")
        return "sent"

    monkeypatch.setattr(file_utils, "run_blocking_in_thread", run_blocking)
    monkeypatch.setattr(interface, "ks_mod", send_summary)
    monkeypatch.setattr(interface.prekvk_mod, "send_prekvk_embed", send_prekvk)
    monkeypatch.setattr(
        interface,
        "claim_send",
        lambda *_args, **_kwargs: pytest.fail("the interface must not own the prekvk_daily claim"),
    )

    bot = SimpleNamespace(get_channel=lambda _channel_id: object())

    await interface.send_stats_update_embed(
        bot,
        "2026-08-27 16:00 UTC",
        is_kvk=True,
        is_test=False,
    )

    assert calls == ["prekvk"]


@pytest.mark.asyncio
@pytest.mark.parametrize("source_state", ["new_disabled", "new_complete", "legacy_empty"])
async def test_ordinary_source_dispatch_preserves_daily_claim_owner(monkeypatch, source_state):
    from unittest.mock import AsyncMock

    from stats_alerts.embeds import kvk
    from tests.test_kvk_public_routing import RoutingStore

    store = RoutingStore()
    store.install(monkeypatch)
    disabled = source_state == "new_disabled"
    store.routing["Enabled"] = not disabled
    if source_state == "legacy_empty":
        from kvk.dal import kvk_reporting_dal

        store.choice["SourceKey"] = "legacy_full_data"

        def empty_legacy_rows(kvk_no, our_kingdom, *, read):
            assert kvk_no == 16 and read.availability == "legacy"
            return {}

        monkeypatch.setattr(kvk_reporting_dal, "fetch_allkingdom_reporting_rows", empty_legacy_rows)
        monkeypatch.setattr(kvk, "get_latest_honor_top", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        kvk,
        "get_latest_kvk_metadata_sql",
        lambda: dict(kvk_no=16, kvk_name="Season", start_date=1, end_date=2),
    )
    channel = SimpleNamespace(id=20, guild=SimpleNamespace(id=10))
    channel.send = AsyncMock(return_value=SimpleNamespace(id=100, channel=channel))
    monkeypatch.setattr(interface, "is_kvk_fighting_open", lambda: True)
    monkeypatch.setattr(interface, "clear_prekvk_message", AsyncMock())
    monkeypatch.setattr(interface, "ks_mod", AsyncMock())
    monkeypatch.setattr(interface, "sent_today_any", lambda _: False)
    monkeypatch.setattr(interface, "read_counts_for", lambda *args: 0)
    claims = []
    monkeypatch.setattr(
        interface, "claim_send", lambda *args, **kw: claims.append((args, kw)) or True
    )
    result = await interface.send_stats_update_embed(
        SimpleNamespace(get_channel=lambda _: channel), "test", True
    )
    assert channel.send.await_count == (0 if disabled else 1)
    assert len(claims) == (0 if disabled else 1)
    assert result.attempts[-1].outcome == ("skipped" if disabled else "sent")
    if not disabled:
        assert claims == [(("kvk",), {"max_per_day": 3})]
    if source_state == "legacy_empty":
        assert result.attempts[-1].data == "empty_or_unavailable"
        assert len(channel.send.call_args.kwargs["embeds"]) == 2
        assert channel.send.call_args.kwargs["content"] == "@everyone"
