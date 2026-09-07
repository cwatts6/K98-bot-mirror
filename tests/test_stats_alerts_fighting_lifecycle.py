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
    monkeypatch.setattr(interface, "load_state", lambda: {})
    monkeypatch.setattr(interface, "save_state", lambda _state: None)

    bot = SimpleNamespace(get_channel=lambda _channel_id: object())

    await interface.send_stats_update_embed(
        bot,
        "2026-08-27 16:00 UTC",
        is_kvk=True,
        is_test=True,
    )

    assert calls == [expected_route]


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
