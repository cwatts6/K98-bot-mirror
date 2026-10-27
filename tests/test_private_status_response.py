import asyncio
from datetime import UTC, datetime, timedelta
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
async def test_ack_failure_retains_codes_and_missing_age_reason_without_payload(caplog):
    ctx = interaction()
    ctx.response.defer.side_effect = discord.NotFound(
        SimpleNamespace(status=404, reason="Not Found"), {"code": 10062, "message": "secret-token"}
    )
    caplog.set_level("INFO")
    assert not await PrivateStatusResponse(ctx).acknowledge()
    assert "10062" in caplog.text and "status=404" in caplog.text
    assert "creation_time_unavailable" in caplog.text
    assert "secret-token" not in caplog.text


def test_real_pycord_interaction_creation_time_and_context():
    raw = object.__new__(discord.Interaction)
    raw.id = discord.utils.time_snowflake(datetime.now(UTC) - timedelta(seconds=10))
    for ctx in (raw, SimpleNamespace(interaction=raw)):
        age, source = PrivateStatusResponse(ctx).age_observation()
        assert 9 <= age <= 12
        # Supported Pycord revisions expose either the property or only the ID.
        assert source in {"created_at", "interaction_id"}


def test_aware_created_at_is_preferred_over_snowflake():
    now = datetime.now(UTC)
    ctx = interaction()
    ctx.created_at = now - timedelta(seconds=10)
    ctx.id = discord.utils.time_snowflake(now - timedelta(minutes=10))
    age, source = PrivateStatusResponse(ctx).age_observation()
    assert 9 <= age <= 12
    assert source == "created_at"


def test_missing_created_property_uses_local_snowflake_without_logging_identity():
    ctx = interaction()
    ctx.id = discord.utils.time_snowflake(datetime.now(UTC) - timedelta(seconds=10))
    age, source = PrivateStatusResponse(ctx).age_observation()
    assert 9 <= age <= 12
    assert source == "interaction_id"


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
