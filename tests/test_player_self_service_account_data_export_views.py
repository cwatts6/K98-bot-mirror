from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from player_self_service.account_data_export_contract import (
    AccountDataExportFile,
    AccountDataExportMetadata,
    AccountDataExportOutcome,
    AccountDataOutputKind,
)
from ui.views import player_self_service_account_data_export_views as views


class _Response:
    def __init__(self) -> None:
        self.sent = []
        self.deferred = []
        self.edited = []
        self._done = False

    async def send_message(self, *args, **kwargs):
        self.sent.append((args, kwargs))
        self._done = True

    async def defer(self, **kwargs):
        self.deferred.append(kwargs)
        self._done = True

    async def edit_message(self, **kwargs):
        self.edited.append(kwargs)
        self._done = True

    def is_done(self):
        return self._done


class _Followup:
    def __init__(self) -> None:
        self.sent = []

    async def send(self, *args, **kwargs):
        self.sent.append((args, kwargs))
        return SimpleNamespace(id=123)


class _Interaction:
    def __init__(self, user_id: int = 42) -> None:
        self.user = SimpleNamespace(id=user_id, display_name="Tester")
        self.response = _Response()
        self.followup = _Followup()
        self.data = {}
        self.original_edits = []

    async def edit_original_response(self, **kwargs):
        self.original_edits.append(kwargs)


class _FakeDiscordFile:
    instances: ClassVar[list[_FakeDiscordFile]] = []

    def __init__(self, path, *, filename):
        self.path = path
        self.filename = filename
        self.closed = False
        self.instances.append(self)

    def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_private_defer_logs_ordinary_failure_and_preserves_cancellation(caplog) -> None:
    failed = _Interaction()

    async def fail_defer(**_kwargs):
        raise RuntimeError("transient Discord defer failure")

    failed.response.defer = fail_defer
    with caplog.at_level(logging.DEBUG, logger=views.__name__):
        await views._defer_private(failed)

    assert "account_data_export_defer_failed" in caplog.text

    cancelled = _Interaction()

    async def cancel_defer(**_kwargs):
        raise asyncio.CancelledError

    cancelled.response.defer = cancel_defer
    with pytest.raises(asyncio.CancelledError):
        await views._defer_private(cancelled)


def _export_file(tmp_path: Path) -> AccountDataExportFile:
    path = tmp_path / "stats_Tester_20260716_093000.xlsx"
    path.write_bytes(b"xlsx")
    metadata = AccountDataExportMetadata(
        output_kind=AccountDataOutputKind.FULL_WORKBOOK,
        generated_at_utc=datetime(2026, 7, 16, 9, 30, tzinfo=UTC),
        authorised_governor_count=2,
        snapshot_row_count=2,
        history_row_count=180,
        requested_days=90,
        window_start=date(2026, 4, 18),
        window_end=date(2026, 7, 16),
        written_start=date(2026, 4, 18),
        written_end=date(2026, 7, 16),
        stats_freshness=date(2026, 7, 16),
        governor_scan_freshness=datetime(2026, 7, 16, 8, tzinfo=UTC),
        inventory_oldest=datetime(2026, 7, 15, 8, tzinfo=UTC),
        inventory_latest=datetime(2026, 7, 16, 8, tzinfo=UTC),
        inventory_reporting_count=2,
        inventory_expected_count=2,
    )
    return AccountDataExportFile(
        file_path=path,
        temp_dir=tmp_path,
        filename=path.name,
        metadata=metadata,
    )


@pytest.mark.asyncio
async def test_options_default_to_one_workbook_choice_and_ninety_days() -> None:
    view = views.AccountDataOptionsView(author_id=42, display_name="Tester")

    assert view.selected_kind is AccountDataOutputKind.FULL_WORKBOOK
    assert view.selected_days == 90
    labels = [option.label for option in view.kind_select.options]
    assert labels == [
        "Full workbook (.xlsx)",
        "Current account snapshot (.csv)",
        "Raw stats history (.csv)",
    ]
    assert all("Google Sheets" not in label for label in labels[1:])
    assert "Google Sheets compatible" in view.kind_select.options[0].description
    assert view.timeout == 300
    assert "expires after 5 minutes" in views._options_copy(view)


@pytest.mark.asyncio
async def test_select_callbacks_sync_rendered_defaults_and_allow_reselection() -> None:
    view = views.AccountDataOptionsView(author_id=42, display_name="Tester")

    view.kind_select._selected_values = [AccountDataOutputKind.RAW_HISTORY.value]
    raw_interaction = _Interaction()
    view.kind_select._interaction = raw_interaction
    await view.kind_select.callback(raw_interaction)

    assert view.selected_kind is AccountDataOutputKind.RAW_HISTORY
    assert [option.value for option in view.kind_select.options if option.default] == [
        AccountDataOutputKind.RAW_HISTORY.value
    ]
    assert "Output: **Raw stats history (.csv)**" in raw_interaction.response.edited[0]["content"]

    view.kind_select._selected_values = [AccountDataOutputKind.FULL_WORKBOOK.value]
    workbook_interaction = _Interaction()
    view.kind_select._interaction = workbook_interaction
    await view.kind_select.callback(workbook_interaction)

    assert view.selected_kind is AccountDataOutputKind.FULL_WORKBOOK
    assert [option.value for option in view.kind_select.options if option.default] == [
        AccountDataOutputKind.FULL_WORKBOOK.value
    ]

    view.days_select._selected_values = ["360"]
    days_interaction = _Interaction()
    view.days_select._interaction = days_interaction
    await view.days_select.callback(days_interaction)
    assert view.selected_days == 360
    assert [option.value for option in view.days_select.options if option.default] == ["360"]

    view.days_select._selected_values = ["90"]
    default_days_interaction = _Interaction()
    view.days_select._interaction = default_days_interaction
    await view.days_select.callback(default_days_interaction)
    assert view.selected_days == 90
    assert [option.value for option in view.days_select.options if option.default] == ["90"]


@pytest.mark.asyncio
async def test_snapshot_selection_disables_history_days() -> None:
    view = views.AccountDataOptionsView(author_id=42, display_name="Tester")
    view.selected_kind = AccountDataOutputKind.CURRENT_SNAPSHOT
    interaction = _Interaction()

    await view._edit_window(interaction)

    assert view.days_select.disabled is True
    assert "History: **Not applicable**" in interaction.response.edited[0]["content"]

    view.selected_kind = AccountDataOutputKind.RAW_HISTORY
    raw_interaction = _Interaction()
    await view._edit_window(raw_interaction)
    assert view.days_select.disabled is False


@pytest.mark.asyncio
async def test_timeout_disables_window_and_edits_via_original_response_fallback() -> None:
    view = views.AccountDataOptionsView(author_id=42, display_name="Tester")
    interaction = _Interaction()
    view.set_timeout_target(interaction)
    view._busy = True

    await view.on_timeout()

    assert view._expired is True
    assert view._busy is False
    assert all(child.disabled for child in view.children)
    assert interaction.original_edits == [{"content": view.expired_message, "view": view}]


@pytest.mark.asyncio
async def test_delivery_is_private_closes_file_and_cleans_temp(monkeypatch, tmp_path) -> None:
    export_file = _export_file(tmp_path)
    cleaned = []
    telemetry = []

    async def fake_build(**kwargs):
        assert kwargs["discord_user_id"] == 42
        assert kwargs["requested_kind"] is AccountDataOutputKind.FULL_WORKBOOK
        assert kwargs["requested_days"] == 90
        return AccountDataExportOutcome(status="ok", export_file=export_file)

    monkeypatch.setattr(views.account_data_export_service, "build_account_data_export", fake_build)
    monkeypatch.setattr(
        views.account_data_export_service,
        "cleanup_export_file",
        lambda item: cleaned.append(item),
    )
    monkeypatch.setattr(views.discord, "File", _FakeDiscordFile)
    monkeypatch.setattr(views, "emit_telemetry_event", lambda item: telemetry.append(item))
    interaction = _Interaction()

    succeeded = await views.send_account_data_export(
        interaction,
        display_name="Fallback",
        output_kind=AccountDataOutputKind.FULL_WORKBOOK,
        days=90,
    )

    assert succeeded is True
    assert interaction.response.deferred == [{"ephemeral": True}]
    assert interaction.followup.sent[0][1]["ephemeral"] is True
    assert interaction.followup.sent[0][1]["file"].filename == export_file.filename
    assert _FakeDiscordFile.instances[-1].closed is True
    assert cleaned == [export_file]
    assert telemetry[0]["event"] == "account_data_export"


@pytest.mark.asyncio
async def test_author_expired_busy_and_terminal_interactions_fail_privately() -> None:
    foreign_view = views.AccountDataOptionsView(author_id=42, display_name="Tester")
    foreign = _Interaction(user_id=99)
    assert await foreign_view.interaction_check(foreign) is False
    assert "not for you" in foreign.response.sent[0][0][0]

    expired_view = views.AccountDataOptionsView(author_id=42, display_name="Tester")
    await expired_view.on_timeout()
    expired = _Interaction()
    assert await expired_view.interaction_check(expired) is False
    assert "expired" in expired.response.sent[0][0][0]

    busy_view = views.AccountDataOptionsView(author_id=42, display_name="Tester")
    busy_view._busy = True
    busy = _Interaction()
    assert await busy_view.interaction_check(busy) is False
    assert "already being prepared" in busy.response.sent[0][0][0]

    terminal_view = views.AccountDataOptionsView(author_id=42, display_name="Tester")
    terminal_view._terminal = True
    terminal = _Interaction()
    assert await terminal_view.interaction_check(terminal) is False
    assert "already complete" in terminal.response.sent[0][0][0]


@pytest.mark.asyncio
async def test_download_uses_selected_kind_and_days_then_terminally_disables(monkeypatch) -> None:
    calls = []

    async def fake_send(interaction, *, display_name, output_kind, days):
        calls.append((interaction.user.id, display_name, output_kind, days))
        return True

    monkeypatch.setattr(views, "send_account_data_export", fake_send)
    view = views.AccountDataOptionsView(author_id=42, display_name="Tester")
    view.selected_kind = AccountDataOutputKind.RAW_HISTORY
    view.selected_days = 360
    interaction = _Interaction()
    button = next(child for child in view.children if child.custom_id == "me:account-data:download")

    await button.callback(interaction)

    assert calls == [(42, "Tester", AccountDataOutputKind.RAW_HISTORY, 360)]
    assert view._terminal is True
    assert all(child.disabled for child in view.children)
