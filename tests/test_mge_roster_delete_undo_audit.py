from __future__ import annotations

from datetime import UTC, datetime, timedelta

from mge import mge_roster_service


def test_remove_hard_delete_stores_undo(monkeypatch):
    snap = {
        "AwardId": 11,
        "EventId": 55,
        "SignupId": 101,
        "GovernorId": 202,
        "GovernorNameSnapshot": "GovX",
        "RequestedCommanderId": 7,
        "RequestedCommanderName": "CmdX",
        "AwardedRank": 3,
        "AwardStatus": "awarded",
        "WaitlistOrder": None,
        "InternalNotes": "note",
    }
    monkeypatch.setattr(
        "mge.mge_roster_service.mge_roster_dal.delete_award_with_audit_atomic",
        lambda **kwargs: snap,
    )
    res = mge_roster_service.remove_award_hard_delete(
        award_id=11,
        actor_discord_id=999,
        event_id=55,
        session_key=(55, 999),
    )
    assert res.success


def test_undo_readd(monkeypatch):
    mge_roster_service._UNDO_BUFFER[(55, 999)] = mge_roster_service.UndoEntry(
        snapshot={
            "SignupId": 101,
            "GovernorId": 202,
            "GovernorNameSnapshot": "GovX",
            "RequestedCommanderId": 7,
            "RequestedCommanderName": "CmdX",
            "AwardedRank": 3,
            "AwardStatus": "awarded",
            "WaitlistOrder": None,
            "InternalNotes": "note",
        },
        created_at=datetime.now(UTC),
    )

    monkeypatch.setattr(
        "mge.mge_roster_service._ensure_no_duplicate_governor", lambda event_id, governor_id: True
    )
    monkeypatch.setattr("mge.mge_roster_service.mge_roster_dal.insert_award", lambda **kwargs: 77)

    res = mge_roster_service.undo_last_removal_in_session(event_id=55, actor_discord_id=999)
    assert res.success
    assert (55, 999) not in mge_roster_service._UNDO_BUFFER


def test_prune_undo_buffer_ttl():
    key = (99, 88)
    mge_roster_service._UNDO_BUFFER[key] = mge_roster_service.UndoEntry(
        snapshot={"SignupId": 1, "GovernorId": 1},
        created_at=datetime.now(UTC) - timedelta(hours=1),
    )
    mge_roster_service.prune_undo_buffer()
    assert key not in mge_roster_service._UNDO_BUFFER


def test_undo_failure_duplicate_restores_entry_if_absent(monkeypatch):
    key = (55, 999)
    original = mge_roster_service.UndoEntry(
        snapshot={"SignupId": 101, "GovernorId": 202},
        created_at=mge_roster_service._now_utc(),
    )
    with mge_roster_service._UNDO_LOCK:
        mge_roster_service._UNDO_BUFFER[key] = original

    monkeypatch.setattr(
        "mge.mge_roster_service._ensure_no_duplicate_governor", lambda *a, **k: False
    )

    res = mge_roster_service.undo_last_removal_in_session(event_id=55, actor_discord_id=999)
    assert not res.success
    with mge_roster_service._UNDO_LOCK:
        assert key in mge_roster_service._UNDO_BUFFER


def test_undo_failure_does_not_overwrite_newer_entry(monkeypatch):
    key = (55, 999)
    old_entry = mge_roster_service.UndoEntry(
        snapshot={"SignupId": 101, "GovernorId": 202},
        created_at=mge_roster_service._now_utc(),
    )
    newer_entry = mge_roster_service.UndoEntry(
        snapshot={"SignupId": 303, "GovernorId": 404},
        created_at=mge_roster_service._now_utc(),
    )

    with mge_roster_service._UNDO_LOCK:
        mge_roster_service._UNDO_BUFFER[key] = old_entry

    monkeypatch.setattr(
        "mge.mge_roster_service._ensure_no_duplicate_governor", lambda *a, **k: False
    )

    # Simulate newer entry arriving during undo attempt by injecting before restore path checks.
    orig_restore = mge_roster_service._restore_undo_if_absent

    def _inject_newer_then_restore(k, e):
        with mge_roster_service._UNDO_LOCK:
            mge_roster_service._UNDO_BUFFER[k] = newer_entry
        orig_restore(k, e)

    monkeypatch.setattr(
        "mge.mge_roster_service._restore_undo_if_absent", _inject_newer_then_restore
    )

    res = mge_roster_service.undo_last_removal_in_session(event_id=55, actor_discord_id=999)
    assert not res.success
    with mge_roster_service._UNDO_LOCK:
        assert mge_roster_service._UNDO_BUFFER[key].snapshot["SignupId"] == 303
