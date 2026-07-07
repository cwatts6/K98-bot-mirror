from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
import re

EMOJI_KIND_UNICODE = "Unicode"
EMOJI_KIND_CUSTOM_DISCORD = "CustomDiscord"
MAX_UNICODE_EMOJI_LEN = 16
MAX_CUSTOM_EMOJI_NAME_LEN = 64
MAX_CUSTOM_EMOJI_ID_LEN = 32
MAX_CUSTOM_EMOJI_TEXT_LEN = 120

_CUSTOM_EMOJI_RE = re.compile(r"^<(?P<animated>a?):(?P<name>[A-Za-z0-9_]{2,64}):(?P<id>[0-9]{2,32})>$")


@dataclass(frozen=True)
class OptionEmoji:
    kind: str
    text: str
    name: str | None = None
    emoji_id: str | None = None
    animated: bool = False

    @property
    def card_text(self) -> str:
        if self.kind == EMOJI_KIND_CUSTOM_DISCORD and self.name:
            return f":{self.name}:"
        return self.text


def _clean_text(value: str | None) -> str:
    return str(value or "").strip()


def normalize_option_emoji(value: str | None) -> OptionEmoji | None:
    text = _clean_text(value)
    if not text:
        return None
    match = _CUSTOM_EMOJI_RE.match(text)
    if match:
        name = match.group("name")
        emoji_id = match.group("id")
        return OptionEmoji(
            kind=EMOJI_KIND_CUSTOM_DISCORD,
            text=text,
            name=name,
            emoji_id=emoji_id,
            animated=bool(match.group("animated")),
        )
    if "<" in text or ">" in text or ":" in text:
        raise ValueError("Use a Unicode emoji or paste one complete custom Discord emoji.")
    if len(text) > MAX_UNICODE_EMOJI_LEN:
        raise ValueError(f"Unicode emoji text must be {MAX_UNICODE_EMOJI_LEN} characters or fewer.")
    return OptionEmoji(kind=EMOJI_KIND_UNICODE, text=text)


def _row_value(row: object, key: str) -> object | None:
    if isinstance(row, Mapping):
        return row.get(key)
    try:
        return getattr(row, key)
    except AttributeError:
        return None


def option_emoji_from_row(row: object) -> OptionEmoji | None:
    kind = _clean_text(_row_value(row, "EmojiKind"))
    text = _clean_text(_row_value(row, "EmojiText"))
    if not kind or not text:
        return None
    if kind == EMOJI_KIND_CUSTOM_DISCORD:
        name = _clean_text(_row_value(row, "EmojiName"))
        emoji_id = _clean_text(_row_value(row, "EmojiID"))
        animated = bool(int(_row_value(row, "EmojiAnimated") or 0))
        if not name or not emoji_id:
            return None
        return OptionEmoji(
            kind=kind,
            text=text,
            name=name,
            emoji_id=emoji_id,
            animated=animated,
        )
    if kind == EMOJI_KIND_UNICODE:
        return OptionEmoji(kind=kind, text=text)
    return None


def option_display_label(label: str, emoji: OptionEmoji | None, *, card_fallback: bool = False) -> str:
    clean_label = str(label or "").strip()
    if emoji is None:
        return clean_label
    prefix = emoji.card_text if card_fallback else emoji.text
    return f"{prefix} {clean_label}".strip()
