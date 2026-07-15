from __future__ import annotations

import asyncio
import logging

import pytest

from inventory.models import InventoryReportVisibility
from inventory.reporting_service import (
    InventoryVisibilityPreferenceRead,
    InventoryVisibilityPreferenceWrite,
)
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
    assert result.message.startswith("Inventory report visibility could not be saved.")
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
    assert result.message.startswith("Inventory report visibility could not be saved.")
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
    assert result.message.startswith("Inventory report visibility could not be saved.")
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


@pytest.mark.asyncio
async def test_confirm_visibility_rereads_expected_state_before_write() -> None:
    calls = []

    async def reader(user_id):
        calls.append(("read", user_id))
        return InventoryVisibilityPreferenceRead(
            ok=True,
            visibility=InventoryReportVisibility.ONLY_ME,
        )

    async def writer(user_id, visibility):
        calls.append(("write", user_id, visibility))
        return InventoryVisibilityPreferenceWrite(ok=True, visibility=visibility)

    result = await preference_service.confirm_inventory_visibility_change(
        42,
        expected_visibility=InventoryReportVisibility.ONLY_ME,
        target_visibility=InventoryReportVisibility.PUBLIC,
        reader=reader,
        writer=writer,
    )

    assert result.ok is True
    assert calls == [
        ("read", 42),
        ("write", 42, InventoryReportVisibility.PUBLIC),
    ]


@pytest.mark.asyncio
async def test_confirm_visibility_rejects_stale_state_without_write() -> None:
    writes = []

    async def reader(_user_id):
        return InventoryVisibilityPreferenceRead(
            ok=True,
            visibility=InventoryReportVisibility.PUBLIC,
        )

    async def writer(*args):
        writes.append(args)
        return InventoryVisibilityPreferenceWrite(ok=True)

    result = await preference_service.confirm_inventory_visibility_change(
        42,
        expected_visibility=InventoryReportVisibility.ONLY_ME,
        target_visibility=InventoryReportVisibility.PUBLIC,
        reader=reader,
        writer=writer,
    )

    assert result.ok is False
    assert result.stale is True
    assert "changed after this confirmation opened" in result.message
    assert writes == []


@pytest.mark.asyncio
async def test_confirm_visibility_treats_missing_row_as_private_default() -> None:
    async def reader(_user_id):
        return InventoryVisibilityPreferenceRead(ok=True, visibility=None)

    async def writer(_user_id, visibility):
        return InventoryVisibilityPreferenceWrite(ok=True, visibility=visibility)

    result = await preference_service.confirm_inventory_visibility_change(
        42,
        expected_visibility=InventoryReportVisibility.ONLY_ME,
        target_visibility=InventoryReportVisibility.PUBLIC,
        reader=reader,
        writer=writer,
    )

    assert result.ok is True


@pytest.mark.asyncio
async def test_confirm_visibility_propagates_cancellation() -> None:
    async def reader(_user_id):
        raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        await preference_service.confirm_inventory_visibility_change(
            42,
            expected_visibility=InventoryReportVisibility.ONLY_ME,
            target_visibility=InventoryReportVisibility.PUBLIC,
            reader=reader,
        )
