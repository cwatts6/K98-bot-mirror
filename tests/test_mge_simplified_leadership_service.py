from __future__ import annotations

import os
import sys
import types

sys.modules.setdefault("aiofiles", types.ModuleType("aiofiles"))
os.environ.setdefault("OUR_KINGDOM", "0")
if "dotenv" not in sys.modules:
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv

import pytest

from mge import mge_simplified_leadership_service as svc
from mge.mge_constants import DEFAULT_TARGET_DECREMENT_SCORE


def test_board_payload_includes_summary_guidance_and_rows(monkeypatch):
    monkeypatch.setattr(
        svc,
        "get_ordered_leadership_rows",
        lambda event_id: {
            "roster_rows": [
                {
                    "SignupId": 1,
                    "GovernorNameSnapshot": "Alpha",
                    "RequestPriority": "High",
                    "LatestKVKRank": 2,
                    "LatestT4T5Kills": 1_500_000,
                    "LatestPercentOfKillTarget": 0.8,
                    "TargetScore": 8_000_000,
                    "SimplifiedStatus": "roster",
                    "ComputedAwardedRank": 1,
                }
            ],
            "waitlist_rows": [],
            "unassigned_rows": [],
            "rejected_rows": [],
            "counts": {
                "total_signups": 1,
                "roster_count": 1,
                "waitlist_count": 0,
                "rejected_count": 0,
            },
        },
    )
    monkeypatch.setattr(
        svc,
        "evaluate_publish_readiness",
        lambda event_id: {"publish_ready": True, "publish_status_text": "Ready to publish."},
    )

    payload = svc.get_leadership_board_payload(10)

    assert payload["counts"]["total_signups"] == 1
    assert payload["guidance_lines"][0].startswith("Step 1:")
    assert "Alpha" in payload["display_lines"][0]
    assert "High" in payload["display_lines"][0]
    # _fmt_short_number renders 1_500_000 as "1.5M" via fmt_short
    assert "1.5M" in payload["display_lines"][0]
    # roster_count=1 → can_move_to_waitlist = (1 > 15) = False
    assert payload["actions"]["can_move_to_waitlist"] is False
    assert payload["actions"]["can_move_to_roster"] is False


def test_button_state_logic_for_waitlist_and_roster(monkeypatch):
    # First scenario: roster_count=16, waitlist_count=1
    monkeypatch.setattr(
        svc,
        "get_ordered_leadership_rows",
        lambda event_id: {
            "roster_rows": [],
            "waitlist_rows": [],
            "unassigned_rows": [],
            "rejected_rows": [],
            "counts": {
                "total_signups": 20,
                "roster_count": 16,
                "waitlist_count": 1,
                "rejected_count": 0,
            },
        },
    )
    monkeypatch.setattr(
        svc,
        "evaluate_publish_readiness",
        lambda event_id: {"publish_ready": False, "publish_status_text": "Blocked"},
    )
    payload = svc.get_leadership_board_payload(20)
    assert payload["actions"]["can_move_to_waitlist"] is True
    # roster_count=16 >= 15 → can_move_to_roster = False; use can_promote_with_swap instead
    assert payload["actions"]["can_move_to_roster"] is False
    assert payload["actions"]["can_promote_with_swap"] is True

    # Second scenario: roster_count=14, waitlist_count=1
    monkeypatch.setattr(
        svc,
        "get_ordered_leadership_rows",
        lambda event_id: {
            "roster_rows": [],
            "waitlist_rows": [],
            "unassigned_rows": [],
            "rejected_rows": [],
            "counts": {
                "total_signups": 15,
                "roster_count": 14,
                "waitlist_count": 1,
                "rejected_count": 0,
            },
        },
    )
    payload = svc.get_leadership_board_payload(21)
    # roster_count=14 → can_move_to_waitlist = (14 > 15) = False
    assert payload["actions"]["can_move_to_waitlist"] is False
    assert payload["actions"]["can_move_to_roster"] is True
    assert payload["actions"]["can_reject_signup"] is True


def test_reset_active_ranks_clears_manual_overrides_for_active_only(monkeypatch):
    updates = []
    audits = []
    monkeypatch.setattr(
        svc,
        "get_ordered_leadership_rows",
        lambda event_id: {
            "roster_rows": [
                {
                    "AwardId": 11,
                    "GovernorId": 101,
                    "AwardedRank": 5,
                    "ComputedAwardedRank": 1,
                    "AwardStatus": "awarded",
                    "AwardStatusRaw": "awarded",
                    "ManualOrderOverride": True,
                    "TargetScore": 8_000_000,
                }
            ],
            "waitlist_rows": [
                {
                    "AwardId": 12,
                    "GovernorId": 102,
                    "WaitlistOrder": 4,
                    "ComputedWaitlistOrder": 1,
                    "AwardStatus": "waitlist",
                    "ManualOrderOverride": True,
                    "TargetScore": None,
                }
            ],
            "rejected_rows": [
                {
                    "AwardId": 13,
                    "GovernorId": 103,
                    "AwardStatus": "rejected",
                    "ManualOrderOverride": True,
                }
            ],
        },
    )
    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.mge_roster_dal.update_award",
        lambda **kwargs: updates.append(kwargs) or True,
    )
    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.mge_roster_dal.insert_award_audit",
        lambda **kwargs: audits.append(kwargs) or True,
    )

    result = svc.reset_active_ranks(event_id=8, actor_discord_id=9001)

    assert result.success is True
    assert len(updates) == 2
    assert all(item["manual_order_override"] is False for item in updates)
    assert [item["award_id"] for item in updates] == [11, 12]
    assert len(audits) == 0


def test_board_payload_exposes_swap_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        svc,
        "get_ordered_leadership_rows",
        lambda event_id: {
            "roster_rows": [{"AwardId": 1}],
            "waitlist_rows": [{"AwardId": 2}],
            "unassigned_rows": [],
            "rejected_rows": [],
            "counts": {
                "total_signups": 2,
                "roster_count": 15,
                "waitlist_count": 1,
                "rejected_count": 0,
            },
        },
    )
    monkeypatch.setattr(
        svc,
        "evaluate_publish_readiness",
        lambda event_id: {"publish_ready": False, "publish_status_text": "Blocked"},
    )

    payload = svc.get_leadership_board_payload(9)
    actions = payload["actions"]

    assert actions["roster_full"] is True
    assert actions["can_promote_with_swap"] is True


def test_move_waitlist_to_roster_with_demote_appends_to_waitlist_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.get_ordered_leadership_rows",
        lambda event_id: {
            "roster_rows": [
                {
                    "AwardId": 101,
                    "GovernorId": 1,
                    "AwardedRank": 1,
                    "ComputedAwardedRank": 1,
                    "AwardStatus": "awarded",
                },
                {
                    "AwardId": 102,
                    "GovernorId": 2,
                    "AwardedRank": 2,
                    "ComputedAwardedRank": 2,
                    "AwardStatus": "awarded",
                },
            ]
            + [
                {
                    "AwardId": 200 + i,
                    "GovernorId": 200 + i,
                    "AwardedRank": i,
                    "ComputedAwardedRank": i,
                    "AwardStatus": "awarded",
                }
                for i in range(3, 16)
            ],
            "waitlist_rows": [
                {"AwardId": 301, "GovernorId": 30, "WaitlistOrder": 1, "AwardStatus": "waitlist"},
                {"AwardId": 302, "GovernorId": 31, "WaitlistOrder": 2, "AwardStatus": "waitlist"},
            ],
        },
    )

    calls: list[dict] = []
    audits: list[dict] = []

    def _update_award(**kwargs):
        calls.append(dict(kwargs))
        return True

    def _insert_audit(**kwargs):
        audits.append(dict(kwargs))
        return True

    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.mge_roster_dal.update_award", _update_award
    )
    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.mge_roster_dal.insert_award_audit", _insert_audit
    )

    result = svc.move_waitlist_to_roster_with_optional_demote(
        event_id=77,
        promote_award_id=302,
        demote_award_id=102,
        actor_discord_id=999,
        notes="swap test",
    )

    assert result.success is True
    assert len(calls) == 2

    demote_call = next(c for c in calls if c["award_id"] == 102)
    promote_call = next(c for c in calls if c["award_id"] == 302)

    assert demote_call["award_status"] == "waitlist"
    assert demote_call["waitlist_order"] == 2
    assert promote_call["award_status"] == "awarded"
    assert promote_call["awarded_rank"] == 2
    assert len(audits) == 2


def test_move_waitlist_to_roster_requires_demote_when_roster_full(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.get_ordered_leadership_rows",
        lambda event_id: {
            "roster_rows": [{"AwardId": i} for i in range(1, 16)],
            "waitlist_rows": [{"AwardId": 99}],
        },
    )

    result = svc.move_waitlist_to_roster_with_optional_demote(
        event_id=77,
        promote_award_id=99,
        demote_award_id=None,
        actor_discord_id=999,
    )
    assert result.success is False
    assert "Roster is full" in result.message


# ---------------------------------------------------------------------------
# Part 6 — New tests: auto-regen after rank change
# ---------------------------------------------------------------------------


def _make_dataset_with_targets():
    return {
        "roster_rows": [
            {
                "AwardId": 11,
                "GovernorId": 1,
                "AwardedRank": 1,
                "ComputedAwardedRank": 1,
                "AwardStatus": "awarded",
                "AwardStatusRaw": "awarded",
                "TargetScore": 8_000_000,
            },
            {
                "AwardId": 12,
                "GovernorId": 2,
                "AwardedRank": 2,
                "ComputedAwardedRank": 2,
                "AwardStatus": "awarded",
                "AwardStatusRaw": "awarded",
                "TargetScore": 7_500_000,
            },
        ],
        "waitlist_rows": [],
        "unassigned_rows": [],
        "rejected_rows": [],
        "counts": {
            "total_signups": 2,
            "roster_count": 2,
            "waitlist_count": 0,
            "rejected_count": 0,
        },
    }


def test_rank_change_triggers_regen_when_targets_exist(monkeypatch: pytest.MonkeyPatch) -> None:
    """After a successful promote/demote swap, _maybe_regenerate_targets is called."""
    regen_calls = []

    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.get_ordered_leadership_rows",
        lambda event_id: _make_dataset_with_targets(),
    )
    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.mge_roster_dal.update_award",
        lambda **kwargs: True,
    )
    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.mge_roster_dal.insert_award_audit",
        lambda **kwargs: True,
    )

    def _fake_apply_targets(**kwargs):
        regen_calls.append(kwargs)
        return 2

    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.mge_publish_dal.apply_generated_targets",
        _fake_apply_targets,
    )

    # Full roster (15), promote waitlist, demote roster
    big_roster = [
        {
            "AwardId": 100 + i,
            "GovernorId": 100 + i,
            "AwardedRank": i,
            "ComputedAwardedRank": i,
            "AwardStatus": "awarded",
            "TargetScore": 8_000_000 - (i - 1) * 500_000,
        }
        for i in range(1, 16)
    ]
    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.get_ordered_leadership_rows",
        lambda event_id: {
            "roster_rows": big_roster,
            "waitlist_rows": [
                {
                    "AwardId": 201,
                    "GovernorId": 50,
                    "WaitlistOrder": 1,
                    "AwardStatus": "waitlist",
                }
            ],
            "unassigned_rows": [],
            "rejected_rows": [],
        },
    )

    result = svc.move_waitlist_to_roster_with_optional_demote(
        event_id=88,
        promote_award_id=201,
        demote_award_id=115,
        actor_discord_id=9001,
    )
    assert result.success is True
    assert len(regen_calls) >= 1, "Target regen should have been called"


def test_rank_change_no_targets_regen_not_triggered(monkeypatch: pytest.MonkeyPatch) -> None:
    """When no targets exist, _maybe_regenerate_targets does NOT call apply_generated_targets."""
    regen_calls = []

    dataset_no_targets = {
        "roster_rows": [
            {
                "AwardId": 11,
                "GovernorId": 1,
                "AwardedRank": 1,
                "ComputedAwardedRank": 1,
                "AwardStatus": "awarded",
                "AwardStatusRaw": "awarded",
                "TargetScore": None,  # no target
            },
        ],
        "waitlist_rows": [
            {"AwardId": 21, "GovernorId": 2, "WaitlistOrder": 1, "AwardStatus": "waitlist"}
        ],
        "unassigned_rows": [],
        "rejected_rows": [],
        "counts": {"total_signups": 2, "roster_count": 1, "waitlist_count": 1, "rejected_count": 0},
    }
    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.get_ordered_leadership_rows",
        lambda event_id: dataset_no_targets,
    )
    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.mge_roster_dal.update_award",
        lambda **kwargs: True,
    )
    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.mge_roster_dal.insert_award_audit",
        lambda **kwargs: True,
    )
    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.mge_publish_dal.apply_generated_targets",
        lambda **kwargs: regen_calls.append(kwargs) or 1,
    )

    from mge import mge_roster_service as roster_svc

    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.mge_roster_service.promote_waitlist_to_roster",
        lambda **kwargs: roster_svc.RosterResult(True, "Promoted."),
    )

    result = svc.move_waitlist_to_roster_with_optional_demote(
        event_id=99,
        promote_award_id=21,
        demote_award_id=None,
        actor_discord_id=9001,
    )
    assert result.success is True
    assert len(regen_calls) == 0, "Regen must NOT be called when no targets exist"


def test_regen_failure_does_not_block_rank_update(monkeypatch: pytest.MonkeyPatch) -> None:
    """Target regen failure must NOT fail the rank change result."""
    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.get_ordered_leadership_rows",
        lambda event_id: _make_dataset_with_targets(),
    )
    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.mge_roster_dal.update_award",
        lambda **kwargs: True,
    )
    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.mge_roster_dal.insert_award_audit",
        lambda **kwargs: True,
    )

    def _regen_raises(**kwargs):
        raise RuntimeError("DB exploded")

    monkeypatch.setattr(
        "mge.mge_simplified_leadership_service.mge_publish_dal.apply_generated_targets",
        _regen_raises,
    )

    result = svc.reset_active_ranks(event_id=55, actor_discord_id=9002)
    assert result.success is True, "Rank reset must succeed even when regen raises"


def test_target_decrement_constant_shared() -> None:
    """Shared target decrement constant should remain at the expected value."""
    assert DEFAULT_TARGET_DECREMENT_SCORE == 500_000
