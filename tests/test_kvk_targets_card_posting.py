from __future__ import annotations

from types import SimpleNamespace

import pytest

from commands import kvk_targets_card_posting as posting
from kvk.models.kvk_targets_card import KvkTargetMetricProgress, KvkTargetsCardPayload

pytestmark = pytest.mark.asyncio


def _payload() -> KvkTargetsCardPayload:
    return KvkTargetsCardPayload(
        governor_id="1",
        governor_name="Gov",
        kvk_no=15,
        kvk_name="Tides of War",
        camp_name="Wind",
        target_state="active",
        status_label="Push now",
        status_detail="Targets are active.",
        next_action="Fight now.",
        power=None,
        metrics=(KvkTargetMetricProgress("Kills", 5, 10, 50.0, 5),),
    )


def _payload_with_placeholder_metric() -> KvkTargetsCardPayload:
    return KvkTargetsCardPayload(
        governor_id="1",
        governor_name="Gov",
        kvk_no=15,
        kvk_name="Tides of War",
        camp_name="Wind",
        target_state="active",
        status_label="Push now",
        status_detail="Targets are active.",
        next_action="Fight now.",
        power=None,
        metrics=(
            KvkTargetMetricProgress("Kills", 5, 10, 50.0, 5),
            KvkTargetMetricProgress(
                "Acclaim Target",
                4_700_000,
                None,
                None,
                None,
                "Target coming next KVK",
            ),
        ),
    )


class DummyFollowup:
    def __init__(self):
        self.sent = []

    async def send(self, **kwargs):
        self.sent.append(kwargs)


class DummyMessage:
    def __init__(self, *, fail_edit: bool = False):
        self.fail_edit = fail_edit
        self.edits = []

    async def edit(self, **kwargs):
        if self.fail_edit:
            raise RuntimeError("edit failed")
        self.edits.append(kwargs)


class DummyFile:
    def __init__(self):
        self.reset_calls = []

    def reset(self, *, seek=True):
        self.reset_calls.append(seek)


async def test_post_targets_falls_back_to_embed_when_card_disabled(monkeypatch):
    payload = _payload()
    followup = DummyFollowup()
    interaction = SimpleNamespace(followup=followup, message=None)

    async def fake_payload(_gid):
        return payload

    monkeypatch.setattr(posting, "_card_enabled", lambda: False)
    monkeypatch.setattr(posting, "build_kvk_targets_card_payload", fake_payload)

    result = await posting.post_kvk_targets_output(interaction, "1", ephemeral=True)

    assert result is payload
    assert followup.sent
    assert followup.sent[0]["ephemeral"] is True
    assert followup.sent[0]["embed"].title == "KVK Targets - Gov"


async def test_post_targets_component_edits_selector_message(monkeypatch):
    payload = _payload()
    message = DummyMessage()
    interaction = SimpleNamespace(followup=DummyFollowup(), message=message)

    async def fake_payload(_gid):
        return payload

    monkeypatch.setattr(posting, "build_kvk_targets_card_payload", fake_payload)
    monkeypatch.setattr(posting, "_card_enabled", lambda: False)

    await posting.post_kvk_targets_output(interaction, "1", ephemeral=False)

    assert message.edits
    assert message.edits[0]["view"] is None
    assert message.edits[0]["embed"].title == "KVK Targets - Gov"


async def test_post_targets_component_sends_followup_when_edit_fails(monkeypatch):
    payload = _payload()
    message = DummyMessage(fail_edit=True)
    followup = DummyFollowup()
    interaction = SimpleNamespace(followup=followup, message=message)

    async def fake_payload(_gid):
        return payload

    monkeypatch.setattr(posting, "build_kvk_targets_card_payload", fake_payload)
    monkeypatch.setattr(posting, "_card_enabled", lambda: False)

    await posting.post_kvk_targets_output(interaction, "1", ephemeral=False)

    assert not message.edits
    assert followup.sent
    assert followup.sent[0]["embed"].title == "KVK Targets - Gov"


async def test_send_or_edit_rewinds_file_before_followup_after_edit_failure():
    message = DummyMessage(fail_edit=True)
    followup = DummyFollowup()
    interaction = SimpleNamespace(followup=followup, message=message)
    file = DummyFile()

    await posting._send_or_edit(interaction, ephemeral=True, file=file)

    assert file.reset_calls == [True]
    assert followup.sent == [{"file": file, "ephemeral": True}]


async def test_fallback_embed_formats_placeholder_metric_note():
    embed = posting.build_targets_fallback_embed(_payload_with_placeholder_metric())

    acclaim = next(field for field in embed.fields if field.name == "Acclaim Target")

    assert acclaim.value == "4.7M\nTarget coming next KVK"
    assert "/ N/A" not in acclaim.value
