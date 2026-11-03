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


from mge import mge_roster_service


def test_add_to_roster_success(monkeypatch):
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.fetch_signup_snapshot",
        lambda signup_id, event_id: {
            "SignupId": signup_id,
            "EventId": event_id,
            "GovernorId": 1001,
            "GovernorNameSnapshot": "Gov A",
            "RequestedCommanderId": 1,
            "RequestedCommanderName": "Commander A",
            "IsActive": 1,
        },
    )
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.fetch_event_awards",
        lambda event_id: [],
    )
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.insert_award",
        lambda **kwargs: 999,
    )
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.insert_award_audit",
        lambda **kwargs: True,
    )

    res = mge_roster_service.add_signup_to_roster(event_id=10, signup_id=200, actor_discord_id=300)
    assert res.success
    assert res.award_id == 999


def test_move_rank_up_down(monkeypatch):
    row = {
        "AwardId": 7,
        "EventId": 10,
        "GovernorId": 1001,
        "AwardedRank": 5,
        "AwardStatus": "awarded",
        "InternalNotes": None,
        "TargetScore": None,
    }

    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.fetch_award_by_id", lambda aid: dict(row)
    )
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.apply_set_rank_atomic",
        lambda **kwargs: {"ok": True, "award_id": kwargs["award_id"], "event_id": 10},
    )

    up = mge_roster_service.move_rank_up(award_id=7, actor_discord_id=9)
    down = mge_roster_service.move_rank_down(award_id=7, actor_discord_id=9)

    assert up.success
    assert down.success


def test_duplicate_governor_blocked(monkeypatch):
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.fetch_signup_snapshot",
        lambda signup_id, event_id: {
            "SignupId": signup_id,
            "EventId": event_id,
            "GovernorId": 1001,
            "GovernorNameSnapshot": "Gov A",
            "RequestedCommanderId": 1,
            "RequestedCommanderName": "Commander A",
            "IsActive": 1,
        },
    )
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.fetch_event_awards",
        lambda event_id: [
            {"AwardId": 1, "GovernorId": 1001, "AwardStatus": "awarded", "AwardedRank": 1}
        ],
    )
    res = mge_roster_service.add_signup_to_roster(event_id=1, signup_id=2, actor_discord_id=3)
    assert not res.success


def test_max_15_enforced(monkeypatch):
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.fetch_signup_snapshot",
        lambda signup_id, event_id: {
            "SignupId": signup_id,
            "EventId": event_id,
            "GovernorId": 9999,
            "GovernorNameSnapshot": "Gov B",
            "RequestedCommanderId": 2,
            "RequestedCommanderName": "Commander B",
            "IsActive": 1,
        },
    )
    full_awarded = [
        {"AwardId": i, "GovernorId": i, "AwardStatus": "awarded", "AwardedRank": i}
        for i in range(1, 16)
    ]
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.fetch_event_awards", lambda event_id: full_awarded
    )
    res = mge_roster_service.add_signup_to_roster(event_id=1, signup_id=2, actor_discord_id=3)
    assert not res.success


def test_waitlist_placement(monkeypatch):
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.fetch_award_by_id",
        lambda aid: {
            "AwardId": aid,
            "EventId": 9,
            "GovernorId": 200,
            "AwardedRank": 3,
            "AwardStatus": "awarded",
            "InternalNotes": None,
            "TargetScore": None,
        },
    )
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.fetch_event_awards", lambda event_id: []
    )
    monkeypatch.setattr("mge.mge_roster_service.mge_roster_dal.update_award", lambda **kwargs: True)
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.insert_award_audit", lambda **kwargs: True
    )

    res = mge_roster_service.move_to_waitlist(award_id=11, actor_discord_id=22)
    assert res.success


def test_set_waitlist_order_marks_manual_override(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.fetch_award_by_id",
        lambda aid: {
            "AwardId": aid,
            "EventId": 9,
            "GovernorId": 200,
            "AwardStatus": "waitlist",
            "WaitlistOrder": 1,
            "InternalNotes": None,
            "TargetScore": None,
            "ManualOrderOverride": 0,
        },
    )

    def _update(**kwargs):
        captured.update(kwargs)
        return True

    monkeypatch.setattr("mge.mge_roster_service.mge_roster_dal.update_award", _update)

    res = mge_roster_service.set_waitlist_order(award_id=11, waitlist_order=2, actor_discord_id=22)

    assert res.success
    assert captured["manual_order_override"] is True


def test_reject_signup_persists_award_side_row_when_missing(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.fetch_signup_snapshot",
        lambda signup_id, event_id: {
            "SignupId": signup_id,
            "EventId": event_id,
            "GovernorId": 5001,
            "GovernorNameSnapshot": "Gov Reject",
            "RequestedCommanderId": 2,
            "RequestedCommanderName": "Cmdr",
            "IsActive": 1,
        },
    )
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.fetch_award_by_event_signup",
        lambda event_id, signup_id: None,
    )
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.insert_award",
        lambda **kwargs: captured.update(kwargs) or 444,
    )
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.insert_award_audit",
        lambda **kwargs: True,
    )

    res = mge_roster_service.reject_signup(
        event_id=9,
        signup_id=90,
        actor_discord_id=11,
        reason="not eligible",
    )

    assert res.success is True
    assert captured["award_status"] == "rejected"
    assert captured["manual_order_override"] is False
