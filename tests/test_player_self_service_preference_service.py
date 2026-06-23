from __future__ import annotations

import asyncio
import logging

import pytest

from inventory.models import InventoryReportVisibility
from inventory.reporting_service import InventoryVisibilityPreferenceWrite
from player_self_service import preference_service


@pytest.mark.asyncio
async def test_save_inventory_visibility_uses_existing_visibility_writer() -> None:
    calls = []

    async def writer(user_id, visibility):
        calls.append((user_id, visibility))
        return InventoryVisibilityPreferenceWrite(
            ok=True,
            visibility=InventoryReportVisibility.PUBLIC,
        )

    result = await preference_service.save_inventory_visibility(
        42,
        InventoryReportVisibility.PUBLIC,
        writer=writer,
    )

    assert result.ok is True
    assert result.inventory_visibility == "public"
    assert result.message == "Inventory report visibility saved as public."
    assert calls == [(42, InventoryReportVisibility.PUBLIC)]


@pytest.mark.asyncio
async def test_save_inventory_visibility_reports_failed_write() -> None:
    async def writer(_user_id, _visibility):
        return InventoryVisibilityPreferenceWrite(ok=False)

    result = await preference_service.save_inventory_visibility(
        42,
        InventoryReportVisibility.PUBLIC,
        writer=writer,
    )

    assert result.ok is False
    assert result.inventory_visibility is None
    assert "previous setting is unchanged" in result.message


@pytest.mark.asyncio
async def test_save_private_visibility_does_not_treat_private_failure_as_success() -> None:
    async def writer(_user_id, _visibility):
        return InventoryVisibilityPreferenceWrite(ok=False)

    result = await preference_service.save_inventory_visibility(
        42,
        InventoryReportVisibility.ONLY_ME,
        writer=writer,
    )

    assert result.ok is False
    assert "previous setting is unchanged" in result.message


@pytest.mark.asyncio
async def test_save_inventory_visibility_reports_writer_failure(caplog) -> None:
    async def writer(_user_id, _visibility):
        raise RuntimeError("db down")

    caplog.set_level(logging.ERROR)

    result = await preference_service.save_inventory_visibility(
        42,
        InventoryReportVisibility.PUBLIC,
        writer=writer,
    )

    assert result.ok is False
    assert result.inventory_visibility is None
    assert "could not be saved" in result.message
    assert "player_self_service_inventory_visibility_save_failed user_id=42" in caplog.text


@pytest.mark.asyncio
async def test_save_inventory_visibility_propagates_cancellation() -> None:
    async def writer(_user_id, _visibility):
        raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        await preference_service.save_inventory_visibility(
            42,
            InventoryReportVisibility.PUBLIC,
            writer=writer,
        )
