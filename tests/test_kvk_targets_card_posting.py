from __future__ import annotations

from dataclasses import replace
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
        progress_state="active",
        status_label="Push now",
        status_detail="Targets are active.",
        next_action="Fight now.",
        power=None,
        metrics=(KvkTargetMetricProgress("Kills", 5, 10, 50.0, 5),),
        publication_state="OFFICIAL",
        target_source_scan=1059,
        target_published_at="2026-06-05 10:30 UTC",
    )


def _payload_with_placeholder_metric() -> KvkTargetsCardPayload:
    return KvkTargetsCardPayload(
        governor_id="1",
        governor_name="Gov",
        kvk_no=15,
        kvk_name="Tides of War",
        camp_name="Wind",
        progress_state="active",
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
        publication_state="OFFICIAL",
        target_source_scan=1059,
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


class DummyChannel:
    def __init__(self):
        self.sent = []

    async def send(self, **kwargs):
        self.sent.append(kwargs)


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


async def test_channel_output_uses_same_payload_for_public_image(monkeypatch):
    payload = _payload()
    channel = DummyChannel()
    interaction = SimpleNamespace(
        channel=channel,
        followup=DummyFollowup(),
        user=SimpleNamespace(id=1),
    )
    rendered_file = DummyFile()

    async def fake_payload(_gid):
        return payload

    async def fake_render(received_payload, *, user):
        assert received_payload is payload
        assert user is interaction.user
        return rendered_file

    monkeypatch.setattr(posting, "build_kvk_targets_card_payload", fake_payload)
    monkeypatch.setattr(posting, "_render_targets_file", fake_render)

    result = await posting.post_kvk_targets_channel_output(interaction, "1")

    assert result is payload
    assert channel.sent == [{"file": rendered_file}]
    assert interaction.followup.sent == []


async def test_channel_output_falls_back_to_canonical_embed(monkeypatch):
    payload = _payload()
    channel = DummyChannel()
    interaction = SimpleNamespace(
        channel=channel,
        followup=DummyFollowup(),
        user=SimpleNamespace(id=1),
    )

    async def fake_payload(_gid):
        return payload

    async def no_render(_payload, *, user):
        return None

    monkeypatch.setattr(posting, "build_kvk_targets_card_payload", fake_payload)
    monkeypatch.setattr(posting, "_render_targets_file", no_render)

    await posting.post_kvk_targets_channel_output(interaction, "1")

    assert channel.sent[0]["embed"].title == "KVK Targets - Gov"
    assert interaction.followup.sent == []


async def test_fallback_embed_formats_placeholder_metric_note():
    embed = posting.build_targets_fallback_embed(_payload_with_placeholder_metric())

    acclaim = next(field for field in embed.fields if field.name == "Acclaim Target")

    assert acclaim.value == "4.7M\nTarget coming next KVK"
    assert "/ N/A" not in acclaim.value


async def test_fallback_embed_shows_official_publication_source():
    embed = posting.build_targets_fallback_embed(_payload())

    assert "Official targets" in embed.description
    publication = next(field for field in embed.fields if field.name == "Target Publication")
    assert "exact matchmaking scan 1059" in publication.value
    assert "Published 2026-06-05 10:30 UTC" in embed.footer.text


async def test_fallback_embed_missing_publication_is_unverified():
    payload = _payload()
    payload = replace(
        payload,
        publication_state="UNKNOWN",
        target_source_scan=None,
        target_published_at=None,
        warnings=("Target publication provenance could not be verified.",),
    )

    embed = posting.build_targets_fallback_embed(payload)

    assert "Unverified targets" in embed.description
    warning = next(field for field in embed.fields if field.name == "Publication Warning")
    assert "Do not treat" in warning.value
    assert "provenance could not be verified" not in warning.value
