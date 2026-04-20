from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from mge.mge_embed_manager import (
    build_mge_awards_embed,
    build_mge_leadership_embed,
    build_mge_main_embed,
    build_mge_signup_embed,
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
        "Status": "signup_open",
        "RulesText": "rules text",
    }


# ---------------------------------------------------------------------------
# build_mge_main_embed — title includes 🏆 prefix and variant
# ---------------------------------------------------------------------------


def test_controlled_embed_render():
    embed = build_mge_main_embed(_event("controlled"), ["GovA", "GovB"])
    assert embed.title == "🏆 MGE Infantry - Infantry"
    # The existing source adds a Mode field
    assert any(f.name == "Mode" for f in embed.fields)


def test_open_embed_render():
    embed = build_mge_main_embed(_event("open"), ["GovA"])
    assert any(f.name == "Mode" and f.value == "open" for f in embed.fields)


def test_public_list_governor_name_only():
    embed = build_mge_main_embed(_event("controlled"), ["GovA"])
    # Field is "Signups (Public)" in the unchanged source
    public = next(f.value for f in embed.fields if f.name == "Signups (Public)")
    assert "GovA" in public
    assert "<@" not in public


# ---------------------------------------------------------------------------
# build_mge_signup_embed — lifecycle_state parameter
# The lifecycle_state kwarg is optional; the base embed colour is 0x2ECC71.
# ---------------------------------------------------------------------------


def test_signup_embed_open_state():
    event = _event("controlled")
    event["SignupCloseUtc"] = datetime.now(UTC) + timedelta(hours=1)
    embed = build_mge_signup_embed(
        event_row=event, public_signup_names=["GovA"], lifecycle_state="open"
    )
    # Colour is the base green used by build_mge_signup_embed: 0x2ECC71
    assert embed.color.value == 0x2ECC71
    # Title includes variant
    assert embed.title == "🏆 MGE Infantry - Infantry"
    # Status field is present
    assert any(f.name == "Status" for f in embed.fields)


def test_signup_embed_closed_state():
    event = _event("controlled")
    embed = build_mge_signup_embed(
        event_row=event, public_signup_names=["GovA"], lifecycle_state="closed"
    )
    # Closed lifecycle sets colour to amber: 0xFFA500
    assert embed.color.value == 0xFFA500
    assert any(f.name == "Status" for f in embed.fields)


def test_signup_embed_finished_state():
    event = _event("controlled")
    embed = build_mge_signup_embed(
        event_row=event, public_signup_names=[], lifecycle_state="finished"
    )
    # finished lifecycle sets colour to grey: 0x95A5A6
    assert embed.color.value == 0x95A5A6
    assert any(f.name == "Status" for f in embed.fields)


# ---------------------------------------------------------------------------
# build_mge_awards_embed — existing sanitisation (source unchanged)
# ---------------------------------------------------------------------------


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


def test_build_mge_awards_embed_bolds_governor_and_italicises_commander() -> None:
    embed = build_mge_awards_embed(
        event_row={"EventName": "E1", "VariantName": "Infantry", "EventId": 1},
        awarded_rows=[
            {
                "AwardedRank": 1,
                "DiscordUserId": 12345,
                "GovernorNameSnapshot": "GovOne",
                "RequestedCommanderName": "Mathias",
                "TargetScore": 13_500_000,
            }
        ],
        waitlist_rows=[],
        publish_version=2,
        published_utc=datetime.now(UTC),
    )

    awarded_field = next(f for f in embed.fields if f.name.startswith("Awarded ("))
    # Governor name must be bold
    assert "**GovOne**" in awarded_field.value
    # Commander name must be italic
    assert "*Mathias*" in awarded_field.value
    # Target shown without extra bold wrapper
    assert "Target: 13.5M" in awarded_field.value


# ---------------------------------------------------------------------------
# build_publish_change_summary_lines — existing source (unchanged)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# resolve_public_signup_channel_id
# Source reads MGE_SIGNUP_CHANNEL_ID from bot_config at import time; the
# name IS bound at module level so monkeypatching it works.
# Source always returns source="signup_channel" — not "MGE_SIGNUP_CHANNEL_ID".
# ---------------------------------------------------------------------------


def test_resolve_public_signup_channel_id_returns_structured_result(monkeypatch):
    monkeypatch.setattr("mge.mge_embed_manager.MGE_SIGNUP_CHANNEL_ID", "456")

    channel_id, raw_value, source = resolve_public_signup_channel_id()

    assert channel_id == 456
    assert raw_value == "456"
    assert source == "signup_channel"


def test_resolve_public_signup_channel_id_uses_signup_channel(monkeypatch):
    monkeypatch.setattr("mge.mge_embed_manager.MGE_SIGNUP_CHANNEL_ID", "789")

    channel_id, raw_value, source = resolve_public_signup_channel_id()

    assert channel_id == 789
    assert raw_value == "789"
    assert source == "signup_channel"


def test_resolve_public_signup_channel_id_returns_zero_when_signup_invalid(monkeypatch):
    monkeypatch.setattr("mge.mge_embed_manager.MGE_SIGNUP_CHANNEL_ID", "not-a-number")

    channel_id, raw_value, source = resolve_public_signup_channel_id()

    assert channel_id == 0
    assert raw_value == "not-a-number"
    assert source == "signup_channel"


# ---------------------------------------------------------------------------
# build_mge_leadership_embed — existing source (unchanged)
# Source uses guidance_lines / display_chunks / "Summary" field name.
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# refresh_mge_boards — returns dict[str, bool] in the existing source
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Part 6 — New tests: awards embed formatting and reminders cap injection
# ---------------------------------------------------------------------------


def test_awards_embed_rows_no_raw_mention() -> None:
    """Awarded embed rows must NOT contain raw <@USER_ID> Discord mentions."""
    embed = build_mge_awards_embed(
        event_row={"EventName": "E", "VariantName": "Infantry", "EventId": 1},
        awarded_rows=[
            {
                "AwardedRank": 4,
                "DiscordUserId": 987654321,
                "GovernorNameSnapshot": "SomeGov",
                "RequestedCommanderName": "SomeCmdr",
                "TargetScore": 7_000_000,
            }
        ],
        waitlist_rows=[],
        publish_version=1,
        published_utc=datetime.now(UTC),
    )
    combined = "\n".join(f.value for f in embed.fields)
    assert "<@987654321>" not in combined, "Raw Discord mention must not appear in embed rows"


def test_awards_embed_rows_governor_is_bold() -> None:
    """GovernorNameSnapshot must be wrapped in ** in the awarded field."""
    embed = build_mge_awards_embed(
        event_row={"EventName": "E", "VariantName": "Infantry", "EventId": 1},
        awarded_rows=[
            {
                "AwardedRank": 5,
                "DiscordUserId": 111,
                "GovernorNameSnapshot": "ChrislosGov",
                "RequestedCommanderName": "DavidIV",
                "TargetScore": 8_000_000,
            }
        ],
        waitlist_rows=[],
        publish_version=1,
        published_utc=datetime.now(UTC),
    )
    awarded_field = next(f for f in embed.fields if f.name.startswith("Awarded ("))
    assert "**ChrislosGov**" in awarded_field.value


def test_awards_embed_rows_commander_is_italic() -> None:
    """RequestedCommanderName must be wrapped in * in the awarded field."""
    embed = build_mge_awards_embed(
        event_row={"EventName": "E", "VariantName": "Infantry", "EventId": 1},
        awarded_rows=[
            {
                "AwardedRank": 5,
                "DiscordUserId": 222,
                "GovernorNameSnapshot": "SomeGov",
                "RequestedCommanderName": "DavidIV",
                "TargetScore": 8_000_000,
            }
        ],
        waitlist_rows=[],
        publish_version=1,
        published_utc=datetime.now(UTC),
    )
    awarded_field = next(f for f in embed.fields if f.name.startswith("Awarded ("))
    assert "*DavidIV*" in awarded_field.value


def test_reminders_embed_bold_cap_uses_event_field() -> None:
    """The points cap bold uses event_row PointCapMillions, not regex on text."""
    from mge.mge_embed_manager import build_mge_award_reminders_embed

    event_row = {
        "EventName": "CappedEvent",
        "VariantName": "Infantry",
        "RuleMode": "fixed",
        "PointCapMillions": 8,
    }
    embed = build_mge_award_reminders_embed(
        event_row=event_row,
        reminders_text="# Rules\nDo your best.",
        published_utc=datetime.now(UTC),
    )
    combined = "\n".join(f.value for f in embed.fields)
    assert "**8 million**" in combined, "Cap must appear bold using event-derived value"


def test_reminders_embed_no_cap_field_when_no_event_cap() -> None:
    """If PointCapMillions is absent, no points-cap field is injected."""
    from mge.mge_embed_manager import build_mge_award_reminders_embed

    event_row = {
        "EventName": "NoCap",
        "VariantName": "Infantry",
        "RuleMode": "fixed",
    }
    embed = build_mge_award_reminders_embed(
        event_row=event_row,
        reminders_text="# Rules\nDo your best.",
        published_utc=datetime.now(UTC),
    )
    field_names = [f.name for f in embed.fields]
    assert "⚠️ Points Cap" not in field_names

