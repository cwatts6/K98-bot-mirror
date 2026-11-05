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


@pytest.mark.asyncio
@pytest.mark.parametrize("daily_failure", [False, True])
async def test_daily_weekly_receipts_are_independent(isolated, monkeypatch, daily_failure):
    from datetime import date

    import embed_offseason_stats as renderer

    class Conn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def cursor(self):
            return object()

    monkeypatch.setattr(renderer, "get_conn_with_retries", Conn)
    monkeypatch.setattr(renderer, "load_all_daily", lambda _: {})
    monkeypatch.setattr(renderer, "load_all_weekly", lambda _: {})
    monkeypatch.setattr(renderer, "_pick_daily_snapshot_date", lambda _: date(2026, 9, 7))
    monkeypatch.setattr(renderer, "load_latest_and_prev_rows", lambda _: (None, None))
    channel = SimpleNamespace(id=99, guild=SimpleNamespace(id=88))
    calls = []

    async def send(**kwargs):
        calls.append(kwargs)
        if daily_failure and len(calls) == 1:
            raise TimeoutError("unknown")
        return SimpleNamespace(id=100 + len(calls), channel=channel)

    channel.send = send
    result = await offseason.send_offseason_flow(None, channel, "stamp", return_outcome=True)
    assert [a.component for a in result.attempts] == ["offseason_daily", "offseason_weekly"]
    assert [a.outcome for a in result.attempts] == (
        ["unknown", "sent"] if daily_failure else ["sent", "sent"]
    )
    assert result.attempts[-1].message_id == 102
    assert result.attempts[-1].persistence == "confirmed"
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_weekly_not_scheduled_is_explicit(isolated, monkeypatch):
    monkeypatch.setattr(offseason, "utcnow", lambda: datetime(2026, 9, 8, tzinfo=UTC))

    async def no_send(*a, **k):
        return None

    monkeypatch.setattr(offseason, "send_offseason_stats_embed_v2", no_send)
    result = await offseason.send_offseason_flow(
        None, SimpleNamespace(id=99), "stamp", return_outcome=True
    )
    assert result.attempts[-1].outcome == "skipped"
    assert result.attempts[-1].reason == "not_scheduled"
    assert result.attempts[0].outcome == "unknown"
