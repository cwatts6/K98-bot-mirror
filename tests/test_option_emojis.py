from __future__ import annotations

import pytest

from voting.option_emojis import (
    EMOJI_KIND_CUSTOM_DISCORD,
    EMOJI_KIND_UNICODE,
    normalize_option_emoji,
    option_display_label,
    option_emoji_from_row,
    option_emoji_sql_values,
)


def test_normalize_option_emoji_accepts_unicode() -> None:
    emoji = normalize_option_emoji("✅")

    assert emoji is not None
    assert emoji.kind == EMOJI_KIND_UNICODE
    assert emoji.text == "✅"
    assert option_display_label("Ready", emoji) == "✅ Ready"


def test_normalize_option_emoji_accepts_custom_discord_emoji() -> None:
    emoji = normalize_option_emoji("<a:ready:123456789012345678>")

    assert emoji is not None
    assert emoji.kind == EMOJI_KIND_CUSTOM_DISCORD
    assert emoji.name == "ready"
    assert emoji.emoji_id == "123456789012345678"
    assert emoji.animated is True
    assert option_display_label("Ready", emoji, card_fallback=True) == ":ready: Ready"


def test_normalize_option_emoji_rejects_partial_custom_markup() -> None:
    with pytest.raises(ValueError):
        normalize_option_emoji(":ready:")


def test_option_emoji_from_row_handles_mapping_metadata() -> None:
    emoji = option_emoji_from_row(
        {
            "EmojiKind": "CustomDiscord",
            "EmojiText": "<:ready:123>",
            "EmojiName": "ready",
            "EmojiID": "123",
            "EmojiAnimated": 0,
        }
    )

    assert emoji is not None
    assert emoji.card_text == ":ready:"


def test_option_emoji_sql_values_serializes_shared_storage_shape() -> None:
    emoji = normalize_option_emoji("<a:ready:123456789012345678>")

    assert option_emoji_sql_values(emoji) == (
        EMOJI_KIND_CUSTOM_DISCORD,
        "<a:ready:123456789012345678>",
        "ready",
        "123456789012345678",
        1,
    )
    assert option_emoji_sql_values(None) == (None, None, None, None, None)
