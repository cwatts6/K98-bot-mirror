from __future__ import annotations

import json

from ark.state.ark_state import ArkJsonState


def test_load_messages_supports_legacy_top_level_shape(tmp_path):
    message_path = tmp_path / "ark_message_state.json"
    reminder_path = tmp_path / "ark_reminder_state.json"
    message_path.write_text(
        json.dumps(
            {
                "19": {
                    "registration": {"channel_id": 1001, "message_id": 2002},
                    "confirmation": {"channel_id": 3003, "message_id": 4004},
                    "confirmation_updates": ["Emergency withdraw: Test (1)"],
                }
            }
        ),
        encoding="utf-8",
    )
    reminder_path.write_text(json.dumps({"reminders": {}}), encoding="utf-8")

    state = ArkJsonState(
        message_state_path=str(message_path),
        reminder_state_path=str(reminder_path),
    )
    state.load()

    assert 19 in state.messages
    assert state.messages[19].registration is not None
    assert state.messages[19].registration.channel_id == 1001
    assert state.messages[19].confirmation is not None
    assert state.messages[19].confirmation.message_id == 4004
