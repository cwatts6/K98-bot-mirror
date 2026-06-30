from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


@pytest.mark.asyncio
async def test_claim_governor_session_acquires(monkeypatch):
    from services import governor_session_lock_service as svc

    captured = {}

    def fake_acquire_lock(**kwargs):
        captured.update(kwargs)
        return True, {
            "HolderDiscordUserID": kwargs["user_id"],
            "ExpiresAtUTC": kwargs["expires_at_utc"],
        }

    monkeypatch.setattr(svc.governor_session_lock_dal, "acquire_lock", fake_acquire_lock)

    now = datetime(2026, 5, 12, 12, 0, tzinfo=UTC)
    result = await svc.claim_governor_session("123", 42, now_utc=now)

    assert result.acquired is True
    assert result.holder_user_id == 42
    assert captured["expires_at_utc"] == now + svc.DEFAULT_TTL


@pytest.mark.asyncio
async def test_claim_governor_session_blocks_contention(monkeypatch):
    from services import governor_session_lock_service as svc

    expires = datetime(2026, 5, 12, 12, 10, tzinfo=UTC)

    def fake_acquire_lock(**kwargs):
        return False, {"HolderDiscordUserID": 99, "ExpiresAtUTC": expires}

    monkeypatch.setattr(svc.governor_session_lock_dal, "acquire_lock", fake_acquire_lock)

    result = await svc.claim_governor_session("123", 42)

    assert result.acquired is False
    assert result.holder_user_id == 99
    assert result.expires_at_utc == expires
    assert "currently being edited" in result.message


@pytest.mark.asyncio
async def test_refresh_release_and_cleanup_delegate_to_dal(monkeypatch):
    from services import governor_session_lock_service as svc

    calls = []

    def fake_refresh_lock(**kwargs):
        calls.append(("refresh", kwargs))
        return True

    def fake_release_lock(**kwargs):
        calls.append(("release", kwargs))
        return True

    def fake_cleanup_expired(**kwargs):
        calls.append(("cleanup", kwargs))
        return 3

    monkeypatch.setattr(svc.governor_session_lock_dal, "refresh_lock", fake_refresh_lock)
    monkeypatch.setattr(svc.governor_session_lock_dal, "release_lock", fake_release_lock)
    monkeypatch.setattr(svc.governor_session_lock_dal, "cleanup_expired", fake_cleanup_expired)

    now = datetime(2026, 5, 12, 12, 0)
    assert await svc.refresh_governor_session("123", 42, ttl=timedelta(minutes=5), now_utc=now)
    assert await svc.release_governor_session("123", 42)
    assert await svc.cleanup_expired_governor_sessions(now_utc=now) == 3

    assert calls[0][1]["expires_at_utc"].tzinfo is UTC
    assert calls[1][1]["user_id"] == 42
    assert calls[2][1]["now_utc"].tzinfo is UTC
