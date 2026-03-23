from __future__ import annotations

from datetime import UTC, datetime

import pytest

from mge.mge_embed_manager import (
    build_mge_awards_embed,
    build_mge_leadership_embed,
    build_mge_main_embed,
    build_publish_change_summary_lines,
    refresh_mge_boards,
    resolve_public_signup_channel_id,
)


def _event(mode: str = "controlled"):
    now = datetime.now(UTC)
    return {
        "EventName": "MGE Infantry",
        "VariantName": "Infantry",
        "StartUtc": now,
        "EndUtc": now,
        "SignupCloseUtc": now,
        "EventMode": mode,
        "RulesText": "rules text",
    }


def test_controlled_embed_render():
    embed = build_mge_main_embed(_event("controlled"), ["GovA", "GovB"])
    assert embed.title == "MGE Infantry"
    assert any(f.name == "Mode" and f.value == "controlled" for f in embed.fields)


def test_open_embed_render():
    embed = build_mge_main_embed(_event("open"), ["GovA"])
    assert any(f.name == "Mode" and f.value == "open" for f in embed.fields)


def test_public_list_governor_name_only():
    embed = build_mge_main_embed(_event("controlled"), ["GovA"])
    public = next(f.value for f in embed.fields if f.name == "Signups (Public)")
    assert "GovA" in public
    assert "<@" not in public


def test_build_mge_awards_embed_sanitizes_user_text_fields() -> None:
    embed = build_mge_awards_embed(
        event_row={"EventName": "E1", "VariantName": "Infantry", "EventId": 1},
        awarded_rows=[
            {
                "AwardedRank": 1,
                "DiscordUserId": 12345,
                "GovernorNameSnapshot": "<@999999>",
                "RequestedCommanderName": "<@&888888>",
                "TargetScore": 8_000_000,
            }
        ],
        waitlist_rows=[
            {
                "WaitlistOrder": 1,
                "GovernorNameSnapshot": "<@everyone>",
                "RequestedCommanderName": "<@777777>",
                "TargetScore": 7_000_000,
            }
        ],
        publish_version=2,
        published_utc=datetime.now(UTC),
    )

    combined = "\n".join(f.value for f in embed.fields)
    assert "‹@999999›" in combined
    assert "‹@&888888›" in combined
    assert "‹@everyone›" in combined
    assert "‹@777777›" in combined
    assert "<@999999>" not in combined
    assert "<@&888888>" not in combined
    assert "<@everyone>" not in combined


def test_publish_change_summary_lines_sanitizes_angle_brackets() -> None:
    old_rows = [
        {
            "AwardId": 1,
            "GovernorNameSnapshot": "<@123>",
            "AwardStatus": "awarded",
            "AwardedRank": 1,
            "TargetScore": 8_000_000,
            "RequestedCommanderName": "<@&456>",
        }
    ]
    new_rows = [
        {
            "AwardId": 1,
            "GovernorNameSnapshot": "<@123>",
            "AwardStatus": "awarded",
            "AwardedRank": 2,
            "TargetScore": 7_000_000,
            "RequestedCommanderName": "<@&789>",
        }
    ]

    lines = build_publish_change_summary_lines(old_rows, new_rows)
    payload = "\n".join(lines)

    assert "‹@123›" in payload
    assert "‹@&456›" in payload or "‹@&789›" in payload
    assert "<@123>" not in payload
    assert "<@&456>" not in payload
    assert "<@&789>" not in payload


def test_resolve_public_signup_channel_id_returns_structured_result(monkeypatch):
    monkeypatch.setattr("mge.mge_embed_manager.MGE_SIMPLIFIED_FLOW_ENABLED", True)
    monkeypatch.setattr("mge.mge_embed_manager.MGE_DATA_CHANNEL_ID", "123")
    monkeypatch.setattr("mge.mge_embed_manager.MGE_SIGNUP_CHANNEL_ID", "456")

    channel_id, raw_value, source = resolve_public_signup_channel_id()

    assert channel_id == 456
    assert raw_value == "456"
    assert source == "signup_channel"


def test_resolve_public_signup_channel_id_uses_signup_channel_even_if_data_is_valid(monkeypatch):
    monkeypatch.setattr("mge.mge_embed_manager.MGE_SIMPLIFIED_FLOW_ENABLED", False)
    monkeypatch.setattr("mge.mge_embed_manager.MGE_DATA_CHANNEL_ID", "123")
    monkeypatch.setattr("mge.mge_embed_manager.MGE_SIGNUP_CHANNEL_ID", "789")

    channel_id, raw_value, source = resolve_public_signup_channel_id()

    assert channel_id == 789
    assert raw_value == "789"
    assert source == "signup_channel"


def test_resolve_public_signup_channel_id_returns_zero_when_signup_invalid(monkeypatch):
    monkeypatch.setattr("mge.mge_embed_manager.MGE_SIMPLIFIED_FLOW_ENABLED", True)
    monkeypatch.setattr("mge.mge_embed_manager.MGE_DATA_CHANNEL_ID", "999")
    monkeypatch.setattr("mge.mge_embed_manager.MGE_SIGNUP_CHANNEL_ID", "not-a-number")

    channel_id, raw_value, source = resolve_public_signup_channel_id()

    assert channel_id == 0
    assert raw_value == "not-a-number"
    assert source == "signup_channel"


def test_build_mge_leadership_embed_contains_summary_and_guidance():
    embed = build_mge_leadership_embed(
        event_row={
            "EventName": "Leadership MGE",
            "VariantName": "Leadership",
            "EventMode": "controlled",
        },
        board_payload={
            "counts": {
                "total_signups": 18,
                "roster_count": 15,
                "waitlist_count": 2,
                "rejected_count": 1,
            },
            "publish": {"publish_status_text": "Ready to publish."},
            "guidance_lines": [
                "Step 1: Review order and reduce roster to 15 if needed",
                "Step 2: Generate targets",
                "Step 3: Publish awards",
            ],
            "display_chunks": [
                "#1 • Alpha • High • KVK Rank 1 • Kills 2,000,000 • Target% 80% • MGE 8,000,000"
            ],
        },
    )

    summary = next(field.value for field in embed.fields if field.name == "Summary")
    assert "18" in summary
    assert "15" in summary
    assert "2" in summary
    assert "1" in summary
    assert "Step 1:" in embed.description
    assert "Step 2:" in embed.description
    assert "Step 3:" in embed.description


@pytest.mark.asyncio
async def test_refresh_mge_boards_uses_rollout_and_leadership_sync(monkeypatch):
    calls = {"public": None, "leadership": None, "awards": None}

    monkeypatch.setattr(
        "mge.mge_embed_manager.resolve_public_signup_channel_id",
        lambda: (321, "321", "signup_channel"),
    )

    async def _public(**kwargs):
        calls["public"] = kwargs
        return True

    async def _leadership(**kwargs):
        calls["leadership"] = kwargs
        return True

    monkeypatch.setattr("mge.mge_embed_manager.sync_event_signup_embed", _public)
    monkeypatch.setattr("mge.mge_embed_manager.sync_event_leadership_embed", _leadership)

    async def _awards(**kwargs):
        calls["awards"] = kwargs
        return True

    monkeypatch.setattr("mge.mge_embed_manager.sync_event_awards_embed", _awards)

    result = await refresh_mge_boards(
        bot=object(), event_id=55, refresh_public=True, refresh_leadership=True, refresh_awards=True
    )

    assert result == {"public": True, "leadership": True, "awards": True}
    assert calls["public"]["signup_channel_id"] == 321
    assert calls["leadership"]["event_id"] == 55
    assert calls["awards"]["event_id"] == 55
