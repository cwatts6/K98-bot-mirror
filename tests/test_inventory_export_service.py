import csv
from datetime import UTC, datetime

import pytest

from inventory import export_service
from inventory.models import InventoryExportFormat, InventoryReportView, RegisteredGovernor

pytestmark = pytest.mark.asyncio


async def test_resolve_export_governor_ids_defaults_to_registered(monkeypatch):
    async def _governors(user_id):
        assert user_id == 42
        return [RegisteredGovernor(111, "Gov 1", "Main"), RegisteredGovernor(222, "Gov 2", "Alt")]

    monkeypatch.setattr(export_service, "get_registered_governors_for_user", _governors)

    governor_ids = await export_service.resolve_export_governor_ids(
        discord_user_id=42,
        governor_id=None,
    )

    assert governor_ids == [111, 222]


async def test_build_inventory_export_file_writes_csv_and_cleans_up(monkeypatch):
    async def _governors(_user_id):
        return [RegisteredGovernor(111, "Gov", "Main")]

    def _resources(governor_ids, *, lookback_days):
        assert governor_ids == [111]
        assert lookback_days == 30
        return [
            {
                "ImportBatchID": 1,
                "GovernorID": 111,
                "DiscordUserID": 42,
                "FlowType": "upload_first",
                "ApprovedAtUtc": datetime.now(UTC),
                "ScanUtc": datetime.now(UTC),
                "ResourceType": "food",
                "FromItemsValue": 100,
                "TotalResourcesValue": 200,
            }
        ]

    monkeypatch.setattr(export_service, "get_registered_governors_for_user", _governors)
    monkeypatch.setattr(
        export_service.inventory_export_dal,
        "fetch_resource_export_rows",
        _resources,
    )

    export_file = await export_service.build_inventory_export_file(
        discord_user_id=42,
        username="Tester",
        export_format=InventoryExportFormat.CSV,
        view=InventoryReportView.RESOURCES,
        lookback_days=30,
    )

    try:
        with export_file.path.open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert rows[0]["RecordKind"] == "resource"
        assert rows[0]["TotalResourcesValue"] == "200"
        assert export_file.row_count == 1
    finally:
        parent = export_file.path.parent
        export_service.cleanup_export_file(export_file)
    assert not export_file.path.exists()
    assert not parent.exists()


async def test_build_inventory_export_file_writes_xlsx_smoke(monkeypatch):
    """Smoke test: xlsx branch calls _write_xlsx and produces a file."""

    async def _governors(_user_id):
        return [RegisteredGovernor(111, "Gov", "Main")]

    def _resources(governor_ids, *, lookback_days):
        return [
            {
                "ImportBatchID": 1,
                "GovernorID": 111,
                "DiscordUserID": 42,
                "FlowType": "upload_first",
                "ApprovedAtUtc": datetime.now(UTC),
                "ScanUtc": datetime.now(UTC),
                "ResourceType": "food",
                "FromItemsValue": 100,
                "TotalResourcesValue": 200,
            }
        ]

    xlsx_write_calls: list[tuple] = []

    def _fake_write_xlsx(rows, path):
        xlsx_write_calls.append((rows, path))
        path.touch()

    monkeypatch.setattr(export_service, "get_registered_governors_for_user", _governors)
    monkeypatch.setattr(
        export_service.inventory_export_dal,
        "fetch_resource_export_rows",
        _resources,
    )
    monkeypatch.setattr(export_service, "_write_xlsx", _fake_write_xlsx)

    export_file = await export_service.build_inventory_export_file(
        discord_user_id=42,
        username="Tester",
        export_format=InventoryExportFormat.EXCEL,
        view=InventoryReportView.RESOURCES,
        lookback_days=30,
    )

    try:
        assert export_file.path.suffix == ".xlsx"
        assert export_file.path.exists()
        assert export_file.row_count == 1
        assert len(xlsx_write_calls) == 1
        rows_written, path_written = xlsx_write_calls[0]
        assert len(rows_written) == 1
        assert path_written == export_file.path
    finally:
        export_service.cleanup_export_file(export_file)


async def test_build_inventory_export_file_rejects_no_records(monkeypatch):
    async def _governors(_user_id):
        return [RegisteredGovernor(111, "Gov", "Main")]

    monkeypatch.setattr(export_service, "get_registered_governors_for_user", _governors)
    monkeypatch.setattr(
        export_service.inventory_export_dal,
        "fetch_resource_export_rows",
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr(
        export_service.inventory_export_dal,
        "fetch_speedup_export_rows",
        lambda *_args, **_kwargs: [],
    )

    with pytest.raises(ValueError, match="No approved inventory records"):
        await export_service.build_inventory_export_file(
            discord_user_id=42,
            username="Tester",
            export_format=InventoryExportFormat.CSV,
            view=InventoryReportView.ALL,
        )
