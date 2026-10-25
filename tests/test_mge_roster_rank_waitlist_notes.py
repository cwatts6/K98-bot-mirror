from __future__ import annotations

from mge import mge_roster_service


def test_set_rank_uses_atomic_dal(monkeypatch):
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.apply_set_rank_atomic",
        lambda **kwargs: {"ok": True, "award_id": 10, "event_id": 1},
    )
    res = mge_roster_service.set_rank(award_id=10, new_rank=4, actor_discord_id=99)
    assert res.success


def test_set_rank_collision_from_waitlist_rejected(monkeypatch):
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.apply_set_rank_atomic",
        lambda **kwargs: {"error": "rank_collision_without_current_rank"},
    )
    res = mge_roster_service.set_rank(award_id=10, new_rank=4, actor_discord_id=99)
    assert not res.success


def test_set_waitlist_order(monkeypatch):
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.fetch_award_by_id",
        lambda aid: {
            "AwardId": aid,
            "EventId": 1,
            "GovernorId": 2,
            "AwardStatus": "waitlist",
            "InternalNotes": None,
        },
    )
    monkeypatch.setattr("mge.mge_roster_service.mge_roster_dal.update_award", lambda **kwargs: True)
    res = mge_roster_service.set_waitlist_order(award_id=10, waitlist_order=2, actor_discord_id=99)
    assert res.success


def test_update_notes(monkeypatch):
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.fetch_award_by_id",
        lambda aid: {
            "AwardId": aid,
            "AwardStatus": "awarded",
            "AwardedRank": 1,
            "WaitlistOrder": None,
        },
    )
    monkeypatch.setattr("mge.mge_roster_service.mge_roster_dal.update_award", lambda **kwargs: True)
    res = mge_roster_service.update_internal_notes(award_id=10, notes="x", actor_discord_id=99)
    assert res.success
