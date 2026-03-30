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
    assert captured["roster_targets"][2]["target_score"] == 7_000_000
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
