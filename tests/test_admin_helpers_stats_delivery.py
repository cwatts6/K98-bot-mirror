from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import admin_helpers as helpers
from stats_alerts.delivery_outcomes import DeliveryAttempt, DeliveryResult


@pytest.mark.asyncio
@pytest.mark.parametrize("export", [True, False, None, "pending"])
async def test_processing_gate_and_truthful_delivery_log(monkeypatch, caplog, export):
    result = DeliveryResult(
        (
            DeliveryAttempt("ks", outcome="sent", message_id=123),
            DeliveryAttempt("fighting", outcome="unknown", reason="TimeoutError"),
        ),
        "audit-correlation",
        "fighting",
    )
    refresh = AsyncMock(return_value=result)
    monkeypatch.setattr(helpers, "send_stats_update_embed", refresh)
    monkeypatch.setattr(helpers, "append_csv_line", AsyncMock())
    monkeypatch.setattr(helpers, "send_embed", AsyncMock())
    monkeypatch.setattr(helpers, "is_currently_kvk", lambda: True)
    channel = SimpleNamespace(id=90)
    with caplog.at_level("INFO"):
        await helpers.log_processing_result(
            bot=SimpleNamespace(get_channel=lambda _: channel),
            notify_channel_id=90,
            user="operator",
            message=None,
            filename="fixture",
            rank="1",
            seed="A",
            success_excel=True,
            success_archive=True,
            success_sql=True,
            success_export=export,
            success_proc_import=True,
            combined_log="",
            start_time=datetime.now(UTC),
            summary_log_path="unused",
        )
    assert refresh.await_count == int(export is True)
    assert "Stats update embed sent successfully" not in caplog.text
    if export is True:
        assert "outcome=unknown" in caplog.text and "message=123" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("sql_success", [True, False])
async def test_pending_export_is_truthful_in_logs_and_notifications(monkeypatch, sql_success):
    append, send, stats = AsyncMock(), AsyncMock(), AsyncMock()
    monkeypatch.setattr(helpers, "append_csv_line", append)
    monkeypatch.setattr(helpers, "send_embed", send)
    monkeypatch.setattr(helpers, "send_stats_update_embed", stats)
    await helpers.log_processing_result(
        bot=SimpleNamespace(get_channel=lambda _: object()),
        notify_channel_id=90,
        user="operator",
        message=None,
        filename="fixture",
        rank="1",
        seed="A",
        success_excel=True,
        success_archive=True,
        success_sql=sql_success,
        success_export="pending",
        success_proc_import=True,
        combined_log="queued exact-job",
        start_time=datetime.now(UTC),
        summary_log_path="summary-fixture",
    )
    summary = next(c.args[1] for c in append.call_args_list if c.args[0] == "summary-fixture")
    assert summary[8] == "pending"
    assert sum(c.args[0] == helpers.FAILED_LOG for c in append.call_args_list) == int(
        not sql_success
    )
    assert send.call_args.args[2]["Export Status"] == "pending"
    if sql_success:
        assert "Awaiting Export" in send.call_args.args[1]
    stats.assert_not_awaited()
