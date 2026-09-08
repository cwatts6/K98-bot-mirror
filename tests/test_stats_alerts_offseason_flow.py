from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from stats_alerts import dispatch_reservations as dispatch, guard, state
from stats_alerts.embeds import offseason


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(guard, "LOG_PATH", str(tmp_path / "log.csv"))
    monkeypatch.setattr(state, "STATE_PATH", str(tmp_path / "state.json"))
    monkeypatch.setattr(state, "_STATE_LOCK_PATH", str(tmp_path / "state.lck"))
    monkeypatch.setattr(offseason, "utcnow", lambda: datetime(2026, 9, 7, tzinfo=UTC))


@pytest.mark.asyncio
@pytest.mark.parametrize("is_test", [False, True])
async def test_daily_weekly_order_mentions_and_test_bypass(isolated, monkeypatch, is_test):
    calls = []

    async def send(bot, **kwargs):
        calls.append(kwargs)
        if "before_send" in kwargs:
            await kwargs["before_send"]()
        return SimpleNamespace(id=123 + len(calls))

    monkeypatch.setattr(offseason, "send_offseason_stats_embed_v2", send)
    await offseason.send_offseason_flow(object(), SimpleNamespace(id=99), "audit", is_test=is_test)
    assert [call["is_weekly"] for call in calls] == [False, True]
    assert [call["mention_everyone"] for call in calls] == [not is_test, False]
    assert all(call["include_kingdom_summary"] for call in calls)
    assert len(list(guard.iter_log_rows())) == (0 if is_test else 2)
    assert dispatch.ReservationStore().path.exists() is not is_test


@pytest.mark.asyncio
async def test_active_prekvk_blocks_both_offseason_periods(isolated, monkeypatch):
    dispatch.ReservationStore().reserve("prekvk_daily", 99)

    async def fail(*args, **kwargs):
        pytest.fail("must not send")

    monkeypatch.setattr(offseason, "send_offseason_stats_embed_v2", fail)
    await offseason.send_offseason_flow(object(), SimpleNamespace(id=99), "audit")
    assert list(guard.iter_log_rows()) == []


@pytest.mark.asyncio
async def test_no_message_releases_reservation_without_claim(isolated, monkeypatch):
    async def no_send(*args, **kwargs):
        return None

    monkeypatch.setattr(offseason, "send_offseason_stats_embed_v2", no_send)
    await offseason.send_offseason_flow(object(), SimpleNamespace(id=99), "audit")
    assert list(guard.iter_log_rows()) == []
    assert all(
        row["phase"] == "released"
        for row in dispatch.ReservationStore()._read()["attempts"].values()
    )


@pytest.mark.asyncio
async def test_transport_failure_keeps_uncertain_and_preserves_summary_suppression(
    isolated, monkeypatch
):
    assert guard.claim_send("kingdom_summary_daily")
    monkeypatch.setattr(offseason, "utcnow", lambda: datetime(2026, 9, 8, tzinfo=UTC))

    async def send(bot, **kwargs):
        assert kwargs["include_kingdom_summary"] is False
        await kwargs["before_send"]()
        raise TimeoutError("outcome unknown")

    monkeypatch.setattr(offseason, "send_offseason_stats_embed_v2", send)
    await offseason.send_offseason_flow(object(), SimpleNamespace(id=99), "audit")
    row = next(iter(dispatch.ReservationStore()._read()["attempts"].values()))
    assert row["phase"] == "uncertain"
    assert not guard.sent_today("offseason_daily")
