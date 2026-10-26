import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest

from core.private_status_response import PrivateStatusResponse
from services.gsheets_health_service import HealthProbe


def interaction():
    return SimpleNamespace(
        response=SimpleNamespace(is_done=lambda: False, defer=AsyncMock()),
        edit_original_response=AsyncMock(),
        followup=SimpleNamespace(send=AsyncMock()),
    )


@pytest.mark.asyncio
async def test_failed_ack_never_edits_or_falls_back():
    ctx = interaction()
    ctx.response.defer.side_effect = RuntimeError("secret")
    response = PrivateStatusResponse(ctx)
    assert not await response.acknowledge()
    assert await response.complete(content="status") == "not_acknowledged"
    ctx.edit_original_response.assert_not_awaited()
    ctx.followup.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_unknown_webhook_records_code_without_private_tokens(caplog):
    ctx = interaction()
    ctx.edit_original_response.side_effect = discord.NotFound(
        SimpleNamespace(status=404, reason="Not Found"), {"code": 10015, "message": "secret-token"}
    )
    response = PrivateStatusResponse(ctx)
    assert await response.acknowledge()
    assert await response.complete(content="status") == "unconfirmed"
    ctx.response.defer.assert_awaited_once_with(ephemeral=True)
    ctx.followup.send.assert_not_awaited()
    assert "10015" in caplog.text and "secret-token" not in caplog.text


@pytest.mark.asyncio
async def test_probe_deadline_retains_original_and_shutdown_drains():
    started, release = asyncio.Event(), asyncio.Event()
    calls = []

    async def run():
        calls.append(1)
        started.set()
        await release.wait()
        return True, "SQL connected"

    probe = HealthProbe(label="SQL")
    observer = asyncio.create_task(probe.observe(run, timeout=0.01))
    await started.wait()
    assert (await observer)[0] is None
    assert (await probe.observe(run, timeout=0.01))[0] is None
    shutdown = asyncio.create_task(probe.shutdown())
    await asyncio.sleep(0)
    assert not shutdown.done() and calls == [1]
    release.set()
    await shutdown
    assert (await probe.observe(run, timeout=1))[0] is None
