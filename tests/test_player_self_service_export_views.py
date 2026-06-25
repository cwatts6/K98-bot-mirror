from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from inventory.models import InventoryExportFile, InventoryExportFormat, InventoryReportView
from services.stats_export_service import StatsExportFile, StatsExportOutcome
from ui.views import player_self_service_export_views as export_views


class _Response:
    def __init__(self) -> None:
        self.deferred = []
        self._done = False

    async def defer(self, **kwargs):
        self.deferred.append(kwargs)
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
    def __init__(self) -> None:
        self.user = SimpleNamespace(id=42, display_name="Tester")
        self.response = _Response()
        self.followup = _Followup()


class _FakeDiscordFile:
    def __init__(self, path, *, filename):
        self.path = path
        self.filename = filename


@pytest.mark.asyncio
async def test_stats_export_adapter_uses_service_private_send_and_cleanup(monkeypatch) -> None:
    calls = []
    cleaned = []
    telemetry = []
    export_file = StatsExportFile(
        file_path="stats.xlsx",
        temp_dir="tmp",
        filename="stats.xlsx",
        format_name="Excel",
        format_emoji="",
        description="Excel export",
        instructions="Open the file.",
        governor_ids=[111],
        row_count=3,
        days=90,
        telemetry={"event": "my_stats_export"},
    )

    async def fake_build(**kwargs):
        calls.append(kwargs)
        return StatsExportOutcome(status="ok", export_file=export_file)

    monkeypatch.setattr(export_views.discord, "File", _FakeDiscordFile)
    monkeypatch.setattr(
        export_views.stats_export_service, "build_personal_stats_export", fake_build
    )
    monkeypatch.setattr(
        export_views.stats_export_service,
        "cleanup_export_file",
        lambda item: cleaned.append(item),
    )
    monkeypatch.setattr(export_views, "emit_telemetry_event", lambda item: telemetry.append(item))
    interaction = _Interaction()

    await export_views.send_stats_export(
        interaction,
        display_name="Fallback",
        requested_format="CSV",
    )

    assert interaction.response.deferred == [{"ephemeral": True}]
    assert calls == [
        {
            "discord_user_id": 42,
            "display_name": "Tester",
            "requested_format": "CSV",
            "days": 90,
        }
    ]
    assert interaction.followup.sent[0][1]["ephemeral"] is True
    assert interaction.followup.sent[0][1]["file"].filename == "stats.xlsx"
    assert telemetry == [{"event": "my_stats_export"}]
    assert cleaned == [export_file]


@pytest.mark.asyncio
async def test_stats_export_adapter_reports_service_unavailable(monkeypatch) -> None:
    async def fake_build(**_kwargs):
        return StatsExportOutcome(status="no_accounts", message="Register first.")

    monkeypatch.setattr(
        export_views.stats_export_service, "build_personal_stats_export", fake_build
    )
    interaction = _Interaction()

    await export_views.send_stats_export(
        interaction,
        display_name="Tester",
        requested_format="Excel",
    )

    assert interaction.followup.sent[0][0] == ("Stats export unavailable: Register first.",)
    assert interaction.followup.sent[0][1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_inventory_export_adapter_uses_default_private_scope_and_cleanup(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls = []
    cleaned = []
    export_file = InventoryExportFile(
        path=tmp_path / "inventory.xlsx",
        filename="inventory.xlsx",
        format=InventoryExportFormat.EXCEL,
        row_count=5,
        governor_ids=(111, 222),
    )

    async def fake_build(**kwargs):
        calls.append(kwargs)
        return export_file

    monkeypatch.setattr(export_views.discord, "File", _FakeDiscordFile)
    monkeypatch.setattr(
        export_views.inventory_export_service,
        "build_inventory_export_file",
        fake_build,
    )
    monkeypatch.setattr(
        export_views.inventory_export_service,
        "cleanup_export_file",
        lambda item: cleaned.append(item),
    )
    interaction = _Interaction()

    await export_views.send_inventory_export(
        interaction,
        display_name="Fallback",
        export_format=InventoryExportFormat.CSV,
    )

    assert calls[0]["discord_user_id"] == 42
    assert calls[0]["username"] == "Tester"
    assert calls[0]["export_format"] == InventoryExportFormat.CSV
    assert calls[0]["view"] == InventoryReportView.ALL
    assert calls[0]["governor_id"] is None
    assert calls[0]["is_admin"] is False
    assert interaction.followup.sent[0][0] == (
        "Inventory export ready. `5` raw approved row(s), `2` governor(s).",
    )
    assert interaction.followup.sent[0][1]["file"].filename == "inventory.xlsx"
    assert cleaned == [export_file]
