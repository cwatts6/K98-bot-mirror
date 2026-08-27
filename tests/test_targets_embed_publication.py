from __future__ import annotations

from dataclasses import replace

from kvk.models.kvk_targets_card import KvkTargetsCardPayload
from targets_embed import build_targets_fallback_embed


def _payload(**overrides) -> KvkTargetsCardPayload:
    payload = KvkTargetsCardPayload(
        governor_id="123",
        governor_name="Governor",
        kvk_no=16,
        kvk_name="Tides of War",
        camp_name=None,
        progress_state="active",
        status_label="Target review",
        status_detail="Target details",
        next_action="Act",
        power=100,
        metrics=(),
        publication_state="OFFICIAL",
        target_source_scan=1059,
        target_published_at="2026-08-26 19:22 UTC",
    )
    return replace(payload, **overrides)


def test_fallback_embed_shows_canonical_official_source():
    embed = build_targets_fallback_embed(_payload())

    assert "Official targets" in embed.description
    assert "matchmaking scan 1059" in embed.fields[0].value


def test_fallback_embed_unknown_publication_is_unverified():
    embed = build_targets_fallback_embed(
        _payload(publication_state="UNKNOWN", target_source_scan=None)
    )

    assert "Unverified targets" in embed.description
    assert any("Do not treat this target set as Official" in field.value for field in embed.fields)


def test_fallback_embed_known_state_without_source_scan_is_unverified():
    embed = build_targets_fallback_embed(_payload(target_source_scan=None))

    assert "Unverified targets" in embed.description


def test_fallback_embed_legacy_active_state_is_not_official():
    embed = build_targets_fallback_embed(_payload(publication_state="ACTIVE"))

    assert "Unverified targets" in embed.description
    assert "Official targets" not in embed.description
