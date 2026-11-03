from __future__ import annotations

from datetime import UTC, datetime

from mge.dal import mge_leadership_dal


def test_fetch_leadership_embed_state_reads_event_columns(monkeypatch) -> None:
    monkeypatch.setattr(
        "mge.dal.mge_leadership_dal.fetch_event_for_embed",
        lambda event_id: {
            "EventId": event_id,
            "LeadershipEmbedMessageId": 111,
            "LeadershipEmbedChannelId": 222,
        },
    )

    state = mge_leadership_dal.fetch_leadership_embed_state(5)

    assert state == {"message_id": 111, "channel_id": 222}


def test_fetch_leadership_embed_state_handles_missing_event(monkeypatch) -> None:
    monkeypatch.setattr("mge.dal.mge_leadership_dal.fetch_event_for_embed", lambda event_id: None)

    state = mge_leadership_dal.fetch_leadership_embed_state(5)

    assert state == {"message_id": 0, "channel_id": 0}


def test_update_leadership_embed_state_persists_to_event(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _update(**kwargs):
        captured.update(kwargs)
        return True

    monkeypatch.setattr(
        "mge.dal.mge_leadership_dal.update_event_leadership_embed_ids",
        _update,
    )

    now = datetime.now(UTC)
    ok = mge_leadership_dal.update_leadership_embed_state(
        event_id=10,
        message_id=444,
        channel_id=555,
        now_utc=now,
    )

    assert ok is True
    assert captured["event_id"] == 10
    assert captured["message_id"] == 444
    assert captured["channel_id"] == 555
    assert captured["now_utc"] == now
