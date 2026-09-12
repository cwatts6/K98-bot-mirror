from __future__ import annotations


def test_normalize_kvk_mode_handles_common_spacing_and_separators():
    from kvk.theme import normalize_kvk_mode

    assert normalize_kvk_mode(" Heroic_Anthem ") == "heroic anthem"
    assert normalize_kvk_mode("Storm-of-Stratagems") == "storm of stratagems"
    assert normalize_kvk_mode(None) == ""


def test_targets_banner_lookup_uses_shared_mode_normalization(monkeypatch):
    import targets_embed

    monkeypatch.setattr(targets_embed, "SHOW_KVK_BANNER", True)
    monkeypatch.setattr(
        targets_embed,
        "KVK_BANNER_MAP",
        {"heroic anthem": "https://example.test/heroic.png"},
    )

    assert targets_embed._maybe_banner("Heroic_Anthem") == "https://example.test/heroic.png"
