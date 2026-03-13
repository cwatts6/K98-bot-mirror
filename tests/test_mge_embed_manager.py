from __future__ import annotations

from datetime import UTC, datetime

from mge.mge_embed_manager import build_mge_main_embed


def _event(mode: str = "controlled"):
    now = datetime.now(UTC)
    return {
        "EventName": "MGE Infantry",
        "VariantName": "Infantry",
        "StartUtc": now,
        "EndUtc": now,
        "SignupCloseUtc": now,
        "EventMode": mode,
        "RulesText": "rules text",
    }


def test_controlled_embed_render():
    embed = build_mge_main_embed(_event("controlled"), ["GovA", "GovB"])
    assert embed.title == "MGE Infantry"
    assert any(f.name == "Mode" and f.value == "controlled" for f in embed.fields)


def test_open_embed_render():
    embed = build_mge_main_embed(_event("open"), ["GovA"])
    assert any(f.name == "Mode" and f.value == "open" for f in embed.fields)


def test_public_list_governor_name_only():
    embed = build_mge_main_embed(_event("controlled"), ["GovA"])
    public = next(f.value for f in embed.fields if f.name == "Signups (Public)")
    assert "GovA" in public
    assert "<@" not in public
