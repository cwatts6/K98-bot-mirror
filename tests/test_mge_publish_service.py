from __future__ import annotations

from types import SimpleNamespace

import pytest

from mge import mge_embed_manager, mge_publish_service


def _ready_payload():
    return {
        "total_signups": 1,
        "roster_count": 1,
        "waitlist_count": 0,
        "rejected_count": 0,
        "publish_ready": True,
        "publish_status_text": "Ready to publish.",
        "publish_block_reason_codes": [],
        "missing_roster_target_count": 0,
    }


def test_generate_targets_from_rank1_uses_current_roster_and_clears_non_roster(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mge_publish_service,
        "get_ordered_leadership_rows",
        lambda event_id: {
            "roster_rows": [
                {"AwardId": 1, "ComputedAwardedRank": 1},
                {"AwardId": 2, "ComputedAwardedRank": 2},
            ],
            "waitlist_rows": [{"AwardId": 3}],
            "rejected_rows": [{"AwardId": 4}],
            "unassigned_rows": [{"AwardId": 5}],
        },
    )
    captured = {}

    def _apply(**kwargs):
        captured.update(kwargs)
        return 2

    monkeypatch.setattr(mge_publish_service.mge_publish_dal, "apply_generated_targets", _apply)

    res = mge_publish_service.generate_targets_from_rank1(
        event_id=99, rank1_target_millions=8, actor_discord_id=123
    )
    assert res.success is True
    assert captured["roster_targets"][1]["target_score"] == 8_000_000
    assert captured["roster_targets"][2]["target_score"] == 7_500_000
    assert captured["clear_award_ids"] == [3, 4, 5]


def test_generate_targets_wipes_previous_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mge_publish_service,
        "get_ordered_leadership_rows",
        lambda event_id: {
            "roster_rows": [
                {"AwardId": 55, "ComputedAwardedRank": 1, "TargetScore": 999_999_999},
            ],
            "waitlist_rows": [],
            "rejected_rows": [],
            "unassigned_rows": [],
        },
    )
    captured = {}
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "apply_generated_targets",
        lambda **kwargs: captured.update(kwargs) or 1,
    )

    res = mge_publish_service.generate_targets_from_rank1(
        event_id=9, rank1_target_millions=6, actor_discord_id=777
    )

    assert res.success is True
    assert captured["roster_targets"][55]["target_score"] == 6_000_000


def test_generate_targets_from_rank1_uses_half_million_rank_ladder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mge_publish_service,
        "get_ordered_leadership_rows",
        lambda event_id: {
            "roster_rows": [
                {"AwardId": 101, "ComputedAwardedRank": 1},
                {"AwardId": 102, "ComputedAwardedRank": 2},
                {"AwardId": 103, "ComputedAwardedRank": 3},
                {"AwardId": 104, "ComputedAwardedRank": 4},
            ],
            "waitlist_rows": [],
            "rejected_rows": [],
            "unassigned_rows": [],
        },
    )
    captured = {}
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "apply_generated_targets",
        lambda **kwargs: captured.update(kwargs) or 4,
    )

    res = mge_publish_service.generate_targets_from_rank1(
        event_id=50, rank1_target_millions=12, actor_discord_id=321
    )

    assert res.success is True
    assert captured["roster_targets"][101]["target_score"] == 12_000_000
    assert captured["roster_targets"][102]["target_score"] == 11_500_000
    assert captured["roster_targets"][103]["target_score"] == 11_000_000
    assert captured["roster_targets"][104]["target_score"] == 10_500_000


def test_generate_targets_accepts_half_million_rank1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rank 1 target of 13.5 (millions) must be accepted and produce correct scores."""
    monkeypatch.setattr(
        mge_publish_service,
        "get_ordered_leadership_rows",
        lambda event_id: {
            "roster_rows": [
                {"AwardId": 201, "ComputedAwardedRank": 1},
                {"AwardId": 202, "ComputedAwardedRank": 2},
            ],
            "waitlist_rows": [],
            "rejected_rows": [],
            "unassigned_rows": [],
        },
    )
    captured = {}
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "apply_generated_targets",
        lambda **kwargs: captured.update(kwargs) or 2,
    )

    res = mge_publish_service.generate_targets_from_rank1(
        event_id=60, rank1_target_millions=13.5, actor_discord_id=1
    )

    assert res.success is True
    assert captured["roster_targets"][201]["target_score"] == 13_500_000
    assert captured["roster_targets"][202]["target_score"] == 13_000_000


def test_generate_targets_rejects_non_half_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-.5-aligned values like 13.3 must be rejected."""
    res = mge_publish_service.generate_targets_from_rank1(
        event_id=61, rank1_target_millions=13.3, actor_discord_id=1
    )
    assert res.success is False


def test_manual_override_persists_only_for_awarded_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_award_target_row",
        lambda award_id: {"AwardId": award_id, "AwardStatus": "awarded"},
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "apply_manual_target_override",
        lambda **kwargs: True,
    )
    res = mge_publish_service.override_target_score(
        award_id=77, target_score=5_500_000, actor_discord_id=555
    )
    assert res.success is True

    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_award_target_row",
        lambda award_id: {"AwardId": award_id, "AwardStatus": "waitlist"},
    )
    res = mge_publish_service.override_target_score(
        award_id=88, target_score=5_500_000, actor_discord_id=555
    )
    assert res.success is False
    assert "current roster" in res.message.lower()


@pytest.mark.asyncio
async def test_publish_increments_version_and_refreshes_all_boards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_calls = []
    monkeypatch.setattr(mge_publish_service, "MGE_AWARD_CHANNEL_ID", "999")
    monkeypatch.setattr(
        mge_publish_service, "evaluate_publish_readiness", lambda event_id: _ready_payload()
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_event_publish_context",
        lambda event_id: {
            "EventId": event_id,
            "EventName": "E1",
            "VariantName": "Infantry",
            "PublishVersion": 0,
        },
    )
    monkeypatch.setattr(
        mge_publish_service,
        "_build_publish_sets",
        lambda event_id: (
            [{"AwardId": 1, "FinalAwardedRank": 1, "TargetScore": 8_000_000}],
            [],
            [],
        ),
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "apply_publish_atomic", lambda **kwargs: 1
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "fetch_published_snapshot", lambda *args, **kwargs: []
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_awards_with_signup_user",
        lambda event_id: [
            {
                "AwardId": 1,
                "AwardStatus": "awarded",
                "AwardedRank": 1,
                "GovernorNameSnapshot": "Gov1",
                "RequestedCommanderName": "Cmd1",
                "TargetScore": 8_000_000,
            }
        ],
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "update_award_embed_ids", lambda **kwargs: True
    )

    async def _refresh(**kwargs):
        refresh_calls.append(kwargs)

    monkeypatch.setattr(mge_publish_service, "refresh_mge_boards", _refresh)

    class _Msg:
        id = 123

    class _Channel:
        id = 999

        async def send(self, **kwargs):
            return _Msg()

    bot = SimpleNamespace(get_channel=lambda x: _Channel(), fetch_channel=lambda x: _Channel())
    res = await mge_publish_service.publish_event_awards(bot=bot, event_id=1, actor_discord_id=2)
    assert res.success is True
    assert res.publish_version == 1
    assert refresh_calls[0]["refresh_awards"] is True


@pytest.mark.asyncio
async def test_publish_blocked_when_readiness_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mge_publish_service,
        "evaluate_publish_readiness",
        lambda event_id: {
            "publish_ready": False,
            "publish_status_text": "Publish blocked: Every rostered signup must have a target value.",
            "publish_block_reason_codes": ["missing_roster_targets"],
        },
    )

    bot = SimpleNamespace(get_channel=lambda _x: None, fetch_channel=lambda _x: None)
    res = await mge_publish_service.publish_event_awards(bot=bot, event_id=1, actor_discord_id=2)

    assert res.success is False
    assert "publish blocked" in res.message.lower()


@pytest.mark.asyncio
async def test_publish_excludes_unassigned_rows_from_final_publish_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mge_publish_service, "MGE_AWARD_CHANNEL_ID", "654")
    monkeypatch.setattr(
        mge_publish_service, "evaluate_publish_readiness", lambda event_id: _ready_payload()
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_event_publish_context",
        lambda event_id: {
            "EventId": event_id,
            "EventName": "E1",
            "VariantName": "Infantry",
            "PublishVersion": 0,
        },
    )
    monkeypatch.setattr(
        mge_publish_service,
        "_build_publish_sets",
        lambda event_id: (
            [{"AwardId": 10, "FinalAwardedRank": 1, "TargetScore": 8_000_000}],
            [{"AwardId": 20, "FinalWaitlistOrder": 1, "TargetScore": None}],
            [20, 30],
        ),
    )
    captured = {}

    def _apply_publish_atomic(**kwargs):
        captured.update(kwargs)
        return 4

    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "apply_publish_atomic",
        _apply_publish_atomic,
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_awards_with_signup_user",
        lambda event_id: [
            {
                "AwardId": 10,
                "AwardStatus": "awarded",
                "AwardedRank": 1,
                "GovernorNameSnapshot": "Gov1",
                "RequestedCommanderName": "Cmd1",
                "TargetScore": 8_000_000,
            },
            {
                "AwardId": 20,
                "AwardStatus": "waitlist",
                "WaitlistOrder": 1,
                "GovernorNameSnapshot": "Gov2",
                "RequestedCommanderName": "Cmd2",
                "TargetScore": None,
            },
        ],
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "fetch_published_snapshot", lambda *args, **kwargs: []
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "update_award_embed_ids", lambda **kwargs: True
    )

    monkeypatch.setattr(mge_publish_service, "refresh_mge_boards", lambda **kwargs: None)

    class _Msg:
        id = 321

    class _Channel:
        id = 654

        async def send(self, **kwargs):
            return _Msg()

    bot = SimpleNamespace(get_channel=lambda x: _Channel(), fetch_channel=lambda x: _Channel())
    res = await mge_publish_service.publish_event_awards(bot=bot, event_id=5, actor_discord_id=9)

    assert res.success is True
    assert [row["AwardId"] for row in captured["publish_rows"]] == [10]
    assert captured["clear_rank_award_ids"] == [20, 30]


@pytest.mark.asyncio
async def test_publish_sends_reminders_once_and_marks_sent(monkeypatch: pytest.MonkeyPatch) -> None:
    sent_payloads = []
    marked = {}
    monkeypatch.setattr(mge_publish_service, "MGE_AWARD_CHANNEL_ID", "999")
    monkeypatch.setattr(
        mge_publish_service, "evaluate_publish_readiness", lambda event_id: _ready_payload()
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_event_publish_context",
        lambda event_id: {
            "EventId": event_id,
            "EventName": "E2",
            "VariantName": "Infantry",
            "RuleMode": "fixed",
            "PublishVersion": 0,
            "AwardRemindersText": None,
            "AwardRemindersSentUtc": None,
        },
    )
    monkeypatch.setattr(
        mge_publish_service,
        "_build_publish_sets",
        lambda event_id: (
            [{"AwardId": 1, "FinalAwardedRank": 1, "TargetScore": 8_000_000}],
            [],
            [],
        ),
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "apply_publish_atomic", lambda **kwargs: 1
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "fetch_published_snapshot", lambda *args, **kwargs: []
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_awards_with_signup_user",
        lambda event_id: [
            {
                "AwardId": 1,
                "AwardStatus": "awarded",
                "AwardedRank": 1,
                "GovernorNameSnapshot": "Gov1",
                "RequestedCommanderName": "Cmd1",
                "TargetScore": 8_000_000,
            }
        ],
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "update_award_embed_ids", lambda **kwargs: True
    )
    monkeypatch.setattr(mge_publish_service, "refresh_mge_boards", lambda **kwargs: None)
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "update_event_award_reminders_text",
        lambda **kwargs: True,
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "mark_award_reminders_sent",
        lambda **kwargs: marked.update(kwargs) or True,
    )

    class _Msg:
        id = 777

    class _Channel:
        id = 999

        async def send(self, **kwargs):
            sent_payloads.append(kwargs)
            return _Msg()

    bot = SimpleNamespace(get_channel=lambda x: _Channel(), fetch_channel=lambda x: _Channel())

    res = await mge_publish_service.publish_event_awards(
        bot=bot,
        event_id=2,
        actor_discord_id=42,
        reminders_text_override="event-specific reminders",
    )

    assert res.success is True
    assert res.reminders_embed_status == "sent"
    assert res.reminders_embed_sent is True
    assert len(sent_payloads) == 2
    assert sent_payloads[1]["content"] == "@everyone"
    assert marked["event_id"] == 2


@pytest.mark.asyncio
async def test_republish_skips_reminders_when_already_sent(monkeypatch: pytest.MonkeyPatch) -> None:
    sent_payloads = []
    mark_called = {"value": False}
    monkeypatch.setattr(mge_publish_service, "MGE_AWARD_CHANNEL_ID", "999")
    monkeypatch.setattr(
        mge_publish_service, "evaluate_publish_readiness", lambda event_id: _ready_payload()
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_event_publish_context",
        lambda event_id: {
            "EventId": event_id,
            "EventName": "E3",
            "VariantName": "Cavalry",
            "RuleMode": "open",
            "PublishVersion": 1,
            "AwardRemindersText": "already persisted",
            "AwardRemindersSentUtc": "2026-01-01T00:00:00",
        },
    )
    monkeypatch.setattr(
        mge_publish_service,
        "_build_publish_sets",
        lambda event_id: (
            [{"AwardId": 1, "FinalAwardedRank": 1, "TargetScore": 8_000_000}],
            [],
            [],
        ),
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "apply_publish_atomic", lambda **kwargs: 2
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "fetch_published_snapshot", lambda *args, **kwargs: []
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_awards_with_signup_user",
        lambda event_id: [
            {
                "AwardId": 1,
                "AwardStatus": "awarded",
                "AwardedRank": 1,
                "GovernorNameSnapshot": "Gov1",
                "RequestedCommanderName": "Cmd1",
                "TargetScore": 8_000_000,
            }
        ],
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "update_award_embed_ids", lambda **kwargs: True
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "mark_award_reminders_sent",
        lambda **kwargs: mark_called.update(value=True) or True,
    )
    monkeypatch.setattr(mge_publish_service, "refresh_mge_boards", lambda **kwargs: None)

    class _Msg:
        id = 888

    class _Channel:
        id = 999

        async def send(self, **kwargs):
            sent_payloads.append(kwargs)
            return _Msg()

    bot = SimpleNamespace(get_channel=lambda x: _Channel(), fetch_channel=lambda x: _Channel())
    res = await mge_publish_service.publish_event_awards(bot=bot, event_id=3, actor_discord_id=9)

    assert res.success is True
    assert res.reminders_embed_status == "already_sent"
    assert len(sent_payloads) == 1
    assert mark_called["value"] is False


@pytest.mark.asyncio
async def test_publish_reminders_persist_failure_skips_second_embed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_payloads = []
    monkeypatch.setattr(mge_publish_service, "MGE_AWARD_CHANNEL_ID", "999")
    monkeypatch.setattr(
        mge_publish_service, "evaluate_publish_readiness", lambda event_id: _ready_payload()
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_event_publish_context",
        lambda event_id: {
            "EventId": event_id,
            "EventName": "E4",
            "VariantName": "Infantry",
            "RuleMode": "fixed",
            "PublishVersion": 0,
            "AwardRemindersText": None,
            "AwardRemindersSentUtc": None,
        },
    )
    monkeypatch.setattr(
        mge_publish_service,
        "_build_publish_sets",
        lambda event_id: (
            [{"AwardId": 1, "FinalAwardedRank": 1, "TargetScore": 8_000_000}],
            [],
            [],
        ),
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "apply_publish_atomic", lambda **kwargs: 1
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "fetch_published_snapshot", lambda *args, **kwargs: []
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_awards_with_signup_user",
        lambda event_id: [
            {
                "AwardId": 1,
                "AwardStatus": "awarded",
                "AwardedRank": 1,
                "GovernorNameSnapshot": "Gov1",
                "RequestedCommanderName": "Cmd1",
                "TargetScore": 8_000_000,
            }
        ],
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "update_award_embed_ids", lambda **kwargs: True
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "update_event_award_reminders_text",
        lambda **kwargs: False,
    )
    monkeypatch.setattr(mge_publish_service, "refresh_mge_boards", lambda **kwargs: None)

    class _Msg:
        id = 1001

    class _Channel:
        id = 999

        async def send(self, **kwargs):
            sent_payloads.append(kwargs)
            return _Msg()

    bot = SimpleNamespace(get_channel=lambda x: _Channel(), fetch_channel=lambda x: _Channel())
    res = await mge_publish_service.publish_event_awards(
        bot=bot,
        event_id=4,
        actor_discord_id=9,
        reminders_text_override="custom text",
    )

    assert res.success is True
    assert res.reminders_embed_status == "persist_failed"
    assert len(sent_payloads) == 1


@pytest.mark.asyncio
async def test_publish_reminders_mark_sent_failure_reports_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_payloads = []
    monkeypatch.setattr(mge_publish_service, "MGE_AWARD_CHANNEL_ID", "999")
    monkeypatch.setattr(
        mge_publish_service, "evaluate_publish_readiness", lambda event_id: _ready_payload()
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_event_publish_context",
        lambda event_id: {
            "EventId": event_id,
            "EventName": "E5",
            "VariantName": "Infantry",
            "RuleMode": "fixed",
            "PublishVersion": 0,
            "AwardRemindersText": None,
            "AwardRemindersSentUtc": None,
        },
    )
    monkeypatch.setattr(
        mge_publish_service,
        "_build_publish_sets",
        lambda event_id: (
            [{"AwardId": 1, "FinalAwardedRank": 1, "TargetScore": 8_000_000}],
            [],
            [],
        ),
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "apply_publish_atomic", lambda **kwargs: 1
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "fetch_published_snapshot", lambda *args, **kwargs: []
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_awards_with_signup_user",
        lambda event_id: [
            {
                "AwardId": 1,
                "AwardStatus": "awarded",
                "AwardedRank": 1,
                "GovernorNameSnapshot": "Gov1",
                "RequestedCommanderName": "Cmd1",
                "TargetScore": 8_000_000,
            }
        ],
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "update_award_embed_ids", lambda **kwargs: True
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "update_event_award_reminders_text",
        lambda **kwargs: True,
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "mark_award_reminders_sent",
        lambda **kwargs: False,
    )
    monkeypatch.setattr(mge_publish_service, "refresh_mge_boards", lambda **kwargs: None)

    class _Msg:
        id = 1002

    class _Channel:
        id = 999

        async def send(self, **kwargs):
            sent_payloads.append(kwargs)
            return _Msg()

    bot = SimpleNamespace(get_channel=lambda x: _Channel(), fetch_channel=lambda x: _Channel())
    res = await mge_publish_service.publish_event_awards(
        bot=bot,
        event_id=5,
        actor_discord_id=9,
        reminders_text_override="custom text",
    )

    assert res.success is True
    assert res.reminders_embed_status == "mark_failed"
    assert res.reminders_embed_sent is True
    assert len(sent_payloads) == 2


@pytest.mark.asyncio
async def test_unpublish_preserves_state_and_refreshes(monkeypatch: pytest.MonkeyPatch) -> None:
    refresh_calls = []
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_event_publish_context",
        lambda event_id: {
            "EventId": event_id,
            "Status": "published",
            "PublishVersion": 2,
        },
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "apply_unpublish_atomic",
        lambda **kwargs: {
            "embed_channel_id": 0,
            "embed_message_id": 0,
            "restore_status": "signup_closed",
        },
    )

    async def _refresh(**kwargs):
        refresh_calls.append(kwargs)

    monkeypatch.setattr(mge_publish_service, "refresh_mge_boards", _refresh)

    bot = SimpleNamespace(get_channel=lambda _x: None, fetch_channel=lambda _x: None)
    res = await mge_publish_service.unpublish_event_awards(bot=bot, event_id=1, actor_discord_id=2)

    assert res.success is True
    assert refresh_calls[0]["refresh_awards"] is True
    assert "rolled back" in res.message.lower()


def test_republish_generates_change_summary() -> None:
    """
    Verify build_publish_change_summary_lines detects rank change, target change,
    and added rows. Commander-name tracking was removed in the new implementation;
    we test only what the new function guarantees.
    """
    old_rows = [
        {
            "AwardId": 1,
            "GovernorNameSnapshot": "A",
            "AwardedRank": 1,
            "FinalAwardedRank": 1,
            "TargetScore": 8_000_000,
        },
    ]
    new_rows = [
        {
            "AwardId": 1,
            "GovernorNameSnapshot": "A",
            "AwardedRank": 2,
            "FinalAwardedRank": 2,
            "TargetScore": 7_500_000,
        },
        {
            "AwardId": 2,
            "GovernorNameSnapshot": "B",
            "AwardedRank": 1,
            "FinalAwardedRank": 1,
            "TargetScore": 8_000_000,
        },
    ]
    lines = mge_embed_manager.build_publish_change_summary_lines(old_rows, new_rows)
    assert any("Added" in x for x in lines)
    assert any("Rank changed" in x for x in lines)
    assert any("Target changed" in x for x in lines)
    # Commander changed is no longer tracked — do not assert it


# ---------------------------------------------------------------------------
# Part 6 — New tests: DM failure, award_mail_dm_sent flag
# ---------------------------------------------------------------------------


def _base_publish_monkeypatches(monkeypatch: pytest.MonkeyPatch, channel_id: str = "999") -> None:
    """Apply the standard publish-flow monkeypatches shared by DM tests."""
    monkeypatch.setattr(mge_publish_service, "MGE_AWARD_CHANNEL_ID", channel_id)
    monkeypatch.setattr(
        mge_publish_service, "evaluate_publish_readiness", lambda event_id: _ready_payload()
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_event_publish_context",
        lambda event_id: {
            "EventId": event_id,
            "EventName": "DMTest",
            "VariantName": "Infantry",
            "PublishVersion": 0,
        },
    )
    monkeypatch.setattr(
        mge_publish_service,
        "_build_publish_sets",
        lambda event_id: (
            [{"AwardId": 1, "FinalAwardedRank": 1, "TargetScore": 8_000_000}],
            [],
            [],
        ),
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "apply_publish_atomic", lambda **kwargs: 1
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "fetch_published_snapshot", lambda *a, **kw: []
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_awards_with_signup_user",
        lambda event_id: [
            {
                "AwardId": 1,
                "AwardStatus": "awarded",
                "AwardedRank": 1,
                "DiscordUserId": 111222333,
                "GovernorNameSnapshot": "GovDM",
                "RequestedCommanderName": "CmdX",
                "TargetScore": 8_000_000,
            }
        ],
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal, "update_award_embed_ids", lambda **kwargs: True
    )
    monkeypatch.setattr(mge_publish_service, "refresh_mge_boards", lambda **kwargs: None)


@pytest.mark.asyncio
async def test_dm_failure_does_not_block_publish(monkeypatch: pytest.MonkeyPatch) -> None:
    """DM send failure must NOT set publish result success to False."""
    _base_publish_monkeypatches(monkeypatch)
    monkeypatch.setattr(mge_publish_service, "MGE_MAIL_DM_USER_IDS", [888999])

    class _FakeUser:
        async def send(self, text, **kwargs):
            raise RuntimeError("DM send failed deliberately")

    async def _fetch_user(uid):
        return _FakeUser()

    class _Msg:
        id = 555

    class _Channel:
        id = 999

        async def send(self, **kwargs):
            return _Msg()

    bot = SimpleNamespace(
        get_channel=lambda x: _Channel(),
        fetch_channel=lambda x: _Channel(),
        fetch_user=_fetch_user,
    )

    res = await mge_publish_service.publish_event_awards(bot=bot, event_id=10, actor_discord_id=2)

    assert res.success is True, f"Publish must succeed despite DM failure, got: {res.message}"
    assert res.award_mail_dm_sent is False
    assert res.award_mail_dm_status == "all_failed:1"


@pytest.mark.asyncio
async def test_dm_sent_flag_true_when_dm_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    """award_mail_dm_sent is True when DM is sent successfully to a single recipient."""
    _base_publish_monkeypatches(monkeypatch)
    monkeypatch.setattr(mge_publish_service, "MGE_MAIL_DM_USER_IDS", [888999])

    class _FakeUser:
        async def send(self, text, **kwargs):
            pass  # success

    async def _fetch_user(uid):
        return _FakeUser()

    class _Msg:
        id = 556

    class _Channel:
        id = 999

        async def send(self, **kwargs):
            return _Msg()

    bot = SimpleNamespace(
        get_channel=lambda x: _Channel(),
        fetch_channel=lambda x: _Channel(),
        fetch_user=_fetch_user,
    )

    res = await mge_publish_service.publish_event_awards(bot=bot, event_id=11, actor_discord_id=2)

    assert res.success is True
    assert res.award_mail_dm_sent is True
    assert res.award_mail_dm_status == "sent:1"


@pytest.mark.asyncio
async def test_dm_sent_to_multiple_recipients(monkeypatch: pytest.MonkeyPatch) -> None:
    """award_mail_dm_sent is True and status reflects count when two recipients are configured."""
    _base_publish_monkeypatches(monkeypatch)
    monkeypatch.setattr(mge_publish_service, "MGE_MAIL_DM_USER_IDS", [111111, 222222])

    class _FakeUser:
        async def send(self, text, **kwargs):
            pass  # success

    async def _fetch_user(uid):
        return _FakeUser()

    class _Msg:
        id = 558

    class _Channel:
        id = 999

        async def send(self, **kwargs):
            return _Msg()

    bot = SimpleNamespace(
        get_channel=lambda x: _Channel(),
        fetch_channel=lambda x: _Channel(),
        fetch_user=_fetch_user,
    )

    res = await mge_publish_service.publish_event_awards(bot=bot, event_id=13, actor_discord_id=2)

    assert res.success is True
    assert res.award_mail_dm_sent is True
    assert res.award_mail_dm_status == "sent:2"


@pytest.mark.asyncio
async def test_dm_partial_failure_still_marks_sent(monkeypatch: pytest.MonkeyPatch) -> None:
    """When one of two recipients fails, award_mail_dm_sent is True with partial status."""
    _base_publish_monkeypatches(monkeypatch)
    monkeypatch.setattr(mge_publish_service, "MGE_MAIL_DM_USER_IDS", [111111, 222222])

    call_count = {"n": 0}

    class _FakeUser:
        def __init__(self, fail: bool):
            self._fail = fail

        async def send(self, text, allowed_mentions=None):
            assert allowed_mentions is not None
            assert allowed_mentions.everyone is False
            assert allowed_mentions.users is False
            assert allowed_mentions.roles is False
            if self._fail:
                raise RuntimeError("deliberate failure")

    async def _fetch_user(uid):
        call_count["n"] += 1
        return _FakeUser(fail=(call_count["n"] == 1))

    class _Msg:
        id = 559

    class _Channel:
        id = 999

        async def send(self, **kwargs):
            return _Msg()

    bot = SimpleNamespace(
        get_channel=lambda x: _Channel(),
        fetch_channel=lambda x: _Channel(),
        fetch_user=_fetch_user,
    )

    res = await mge_publish_service.publish_event_awards(bot=bot, event_id=14, actor_discord_id=2)

    assert res.success is True
    assert res.award_mail_dm_sent is True
    assert res.award_mail_dm_status == "partial:1_ok_1_failed"


@pytest.mark.asyncio
async def test_dm_skipped_when_no_recipient_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """When MGE_MAIL_DM_USER_IDS is empty, DM is skipped and publish still succeeds."""
    _base_publish_monkeypatches(monkeypatch)
    monkeypatch.setattr(mge_publish_service, "MGE_MAIL_DM_USER_IDS", [])

    class _Msg:
        id = 557

    class _Channel:
        id = 999

        async def send(self, **kwargs):
            return _Msg()

    bot = SimpleNamespace(
        get_channel=lambda x: _Channel(),
        fetch_channel=lambda x: _Channel(),
    )

    res = await mge_publish_service.publish_event_awards(bot=bot, event_id=12, actor_discord_id=2)

    assert res.success is True
    assert res.award_mail_dm_sent is False
    assert res.award_mail_dm_status == "skipped_no_recipient"


def test_dm_body_sanitizes_governor_names(monkeypatch: pytest.MonkeyPatch) -> None:
    from mge.mge_publish_service import _build_award_mail_text

    ctx = {"RuleMode": "fixed", "PointCapMillions": 8}
    rows = [
        {
            "GovernorNameSnapshot": "*Bad_Name* <@123>",
            "AwardedRank": 1,
            "TargetScore": 14_000_000,
        }
    ]

    text = _build_award_mail_text(ctx, rows)

    assert "<@123>" not in text
    assert "*" not in text
    assert "_" not in text


@pytest.mark.asyncio
async def test_dm_body_contains_all_awarded_governors(monkeypatch: pytest.MonkeyPatch) -> None:
    """The DM body must list all awarded governors with their targets."""
    from mge.mge_publish_service import _build_award_mail_text

    ctx = {
        "EventName": "Test MGE",
        "RuleMode": "fixed",
        "PointCapMillions": 8,
    }
    rows = [
        {"GovernorNameSnapshot": "Chrislos", "AwardedRank": 1, "TargetScore": 14_000_000},
        {"GovernorNameSnapshot": "义Viper义", "AwardedRank": 2, "TargetScore": 13_500_000},
    ]
    text = _build_award_mail_text(ctx, rows)

    assert "Chrislos - Target: 14.0M" in text
    assert "义Viper义 - Target: 13.5M" in text
    assert "8m points" in text
    assert "Leadership" in text
    # Must NOT contain commander names (not present in rows used here)
    # Must be plain text (no bold/italic Discord markdown)
    assert "**" not in text
    assert "*" not in text
    assert "<@" not in text
