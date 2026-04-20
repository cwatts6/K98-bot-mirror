from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from mge import mge_dm_followup


class _Attachment:
    def __init__(self, *, url: str, filename: str, content_type: str | None, size: int | None):
        self.url = url
        self.filename = filename
        self.content_type = content_type
        self.size = size


def test_validate_and_get_image_accepts_content_type_image() -> None:
    att = _Attachment(
        url="https://cdn.discordapp.com/x.png",
        filename="x.png",
        content_type="image/png",
        size=123,
    )
    got = mge_dm_followup.validate_and_get_image([att])  # type: ignore[arg-type]
    assert got is att


def test_validate_and_get_image_rejects_non_image() -> None:
    att = _Attachment(
        url="https://cdn.discordapp.com/x.txt",
        filename="x.txt",
        content_type="text/plain",
        size=22,
    )
    got = mge_dm_followup.validate_and_get_image([att])  # type: ignore[arg-type]
    assert got is None


def test_save_gear_attachment_persists_and_audits(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}

    def _update(**kwargs):
        calls["update"] = kwargs
        return True

    def _audit(**kwargs):
        calls["audit"] = kwargs
        return True

    monkeypatch.setattr(mge_dm_followup.mge_signup_dal, "update_signup_gear_attachment", _update)
    monkeypatch.setattr(mge_dm_followup.mge_signup_dal, "insert_signup_audit", _audit)

    att = _Attachment(
        url="https://cdn.discordapp.com/gear.png",
        filename="gear.png",
        content_type="image/png",
        size=555,
    )
    result = mge_dm_followup.save_attachment_for_signup(
        signup_id=10,
        event_id=20,
        governor_id=30,
        actor_discord_id=40,
        kind="gear",
        attachment=att,  # type: ignore[arg-type]
        now_utc=datetime.now(UTC),
    )
    assert result.success is True
    assert "Gear attachment saved." == result.message
    assert calls["update"] is not None
    audit = calls["audit"]
    assert isinstance(audit, dict)
    details = audit["details"]
    assert isinstance(details, dict)
    assert details["content_type"] == "image/png"
    assert details["size"] == 555


def test_save_armament_attachment_persists_and_audits(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}

    def _update(**kwargs):
        calls["update"] = kwargs
        return True

    def _audit(**kwargs):
        calls["audit"] = kwargs
        return True

    monkeypatch.setattr(
        mge_dm_followup.mge_signup_dal, "update_signup_armament_attachment", _update
    )
    monkeypatch.setattr(mge_dm_followup.mge_signup_dal, "insert_signup_audit", _audit)

    att = _Attachment(
        url="https://cdn.discordapp.com/arm.png",
        filename="arm.png",
        content_type="image/jpeg",
        size=888,
    )
    result = mge_dm_followup.save_attachment_for_signup(
        signup_id=11,
        event_id=21,
        governor_id=31,
        actor_discord_id=41,
        kind="armament",
        attachment=att,  # type: ignore[arg-type]
        now_utc=datetime.now(UTC),
    )
    assert result.success is True
    assert result.message == "Armament attachment saved."
    audit = calls["audit"]
    assert isinstance(audit, dict)
    details = audit["details"]
    assert isinstance(details, dict)
    assert details["content_type"] == "image/jpeg"
    assert details["size"] == 888


@pytest.mark.asyncio
async def test_open_dm_followup_closed_dm(monkeypatch: pytest.MonkeyPatch) -> None:
    class _User:
        id = 123
        dm_channel = None

        async def create_dm(self):
            raise RuntimeError("DM blocked")

    ok, msg = await mge_dm_followup.open_dm_followup(
        user=_User(),  # type: ignore[arg-type]
        event_id=1,
        signup_id=2,
        event_name="MGE Infantry",
    )
    assert ok is False
    assert "couldn't dm you" in msg.lower()


def test_latest_upload_wins_by_repeated_save(monkeypatch: pytest.MonkeyPatch) -> None:
    updates: list[dict[str, object]] = []

    def _update(**kwargs):
        updates.append(kwargs)
        return True

    monkeypatch.setattr(mge_dm_followup.mge_signup_dal, "update_signup_gear_attachment", _update)
    monkeypatch.setattr(mge_dm_followup.mge_signup_dal, "insert_signup_audit", lambda **_: True)

    a1 = _Attachment(
        url="https://cdn.discordapp.com/old.png",
        filename="old.png",
        content_type="image/png",
        size=10,
    )
    a2 = _Attachment(
        url="https://cdn.discordapp.com/new.png",
        filename="new.png",
        content_type="image/png",
        size=20,
    )
    mge_dm_followup.save_attachment_for_signup(
        signup_id=1,
        event_id=2,
        governor_id=3,
        actor_discord_id=4,
        kind="gear",
        attachment=a1,  # type: ignore[arg-type]
    )
    mge_dm_followup.save_attachment_for_signup(
        signup_id=1,
        event_id=2,
        governor_id=3,
        actor_discord_id=4,
        kind="gear",
        attachment=a2,  # type: ignore[arg-type]
    )

    assert len(updates) == 2
    assert updates[-1]["gear_attachment_url"] == "https://cdn.discordapp.com/new.png"


@pytest.mark.asyncio
async def test_route_dm_message_returns_false_without_attachments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mge_dm_followup.register_dm_session(
        actor_discord_id=123,
        signup_id=1,
        event_id=2,
        view=SimpleNamespace(handle_dm_message=None),  # type: ignore[arg-type]
    )

    sent: list[str] = []

    class _Channel:
        async def send(self, text: str) -> None:
            sent.append(text)

    msg = SimpleNamespace(
        author=SimpleNamespace(id=123, bot=False),
        guild=None,
        attachments=[],
        channel=_Channel(),
    )

    handled = await mge_dm_followup.route_dm_message(msg)  # type: ignore[arg-type]
    assert handled is False
    assert sent == []


@pytest.mark.asyncio
async def test_route_dm_message_handles_when_session_and_attachment() -> None:
    class _View:
        async def handle_dm_message(self, message) -> str:
            return "ok saved"

    mge_dm_followup.register_dm_session(
        actor_discord_id=555,
        signup_id=10,
        event_id=20,
        view=_View(),  # type: ignore[arg-type]
    )

    sent: list[str] = []

    class _Channel:
        async def send(self, text: str) -> None:
            sent.append(text)

    msg = SimpleNamespace(
        author=SimpleNamespace(id=555, bot=False),
        guild=None,
        attachments=[object()],
        channel=_Channel(),
    )

    handled = await mge_dm_followup.route_dm_message(msg)  # type: ignore[arg-type]
    assert handled is True
    assert sent[-1] == "ok saved"


@pytest.mark.asyncio
async def test_route_dm_message_handler_exception_returns_true_and_sends_error() -> None:
    class _View:
        async def handle_dm_message(self, message) -> str:
            raise RuntimeError("boom")

    mge_dm_followup.register_dm_session(
        actor_discord_id=777,
        signup_id=10,
        event_id=20,
        view=_View(),  # type: ignore[arg-type]
    )

    sent: list[str] = []

    class _Channel:
        async def send(self, text: str) -> None:
            sent.append(text)

    msg = SimpleNamespace(
        author=SimpleNamespace(id=777, bot=False),
        guild=None,
        attachments=[object()],
        channel=_Channel(),
    )

    handled = await mge_dm_followup.route_dm_message(msg)  # type: ignore[arg-type]
    assert handled is True
    assert "failed to process attachment" in sent[-1].lower()
