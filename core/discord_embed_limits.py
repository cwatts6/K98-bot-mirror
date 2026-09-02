"""Dependency-light Discord embed payload limits and budget helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

MAX_EMBEDS_PER_MESSAGE = 10
MAX_TITLE_CHARACTERS = 256
MAX_DESCRIPTION_CHARACTERS = 4096
MAX_FIELDS_PER_EMBED = 25
MAX_FIELD_NAME_CHARACTERS = 256
MAX_FIELD_VALUE_CHARACTERS = 1024
MAX_FOOTER_CHARACTERS = 2048
MAX_AUTHOR_CHARACTERS = 256
MAX_TOTAL_CHARACTERS = 6000


@dataclass(frozen=True, slots=True)
class EmbedLimitViolation:
    """One Discord embed contract violation with an actionable payload path."""

    path: str
    actual: int
    limit: int

    def __str__(self) -> str:
        return f"{self.path}: {self.actual}/{self.limit}"


@dataclass(frozen=True, slots=True)
class EmbedPayloadUsage:
    """Measured message-level and per-embed budget consumption."""

    embed_count: int
    total_characters: int
    field_counts: tuple[int, ...]

    @property
    def remaining_embeds(self) -> int:
        return max(0, MAX_EMBEDS_PER_MESSAGE - self.embed_count)

    @property
    def remaining_characters(self) -> int:
        return max(0, MAX_TOTAL_CHARACTERS - self.total_characters)

    def remaining_fields(self, embed_index: int = 0) -> int:
        if embed_index < 0 or embed_index >= len(self.field_counts):
            raise IndexError(f"embed index out of range: {embed_index}")
        return max(0, MAX_FIELDS_PER_EMBED - self.field_counts[embed_index])


class EmbedPayloadLimitError(ValueError):
    """Raised when a message embed payload exceeds Discord's hard limits."""

    def __init__(self, violations: Iterable[EmbedLimitViolation]):
        self.violations = tuple(violations)
        super().__init__("; ".join(str(item) for item in self.violations))


def truncate_text(value: Any, limit: int, *, marker: str = "…") -> str:
    """Return text within ``limit`` characters and mark any truncation explicitly."""

    text = "" if value is None else str(value)
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    if len(marker) >= limit:
        return marker[:limit]
    return f"{text[: limit - len(marker)]}{marker}"


def _text_length(value: Any) -> int:
    return len("" if value is None else str(value))


def _as_mapping(embed: Any) -> Mapping[str, Any]:
    if isinstance(embed, Mapping):
        return embed
    to_dict = getattr(embed, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            return payload
    raise TypeError("embed payload entries must be mappings or expose to_dict()")


def _normalise_embeds(embeds: Any) -> list[Mapping[str, Any]]:
    if isinstance(embeds, Mapping) or callable(getattr(embeds, "to_dict", None)):
        return [_as_mapping(embeds)]
    if isinstance(embeds, (str, bytes)):
        raise TypeError("embed payload must not be text")
    try:
        return [_as_mapping(embed) for embed in embeds]
    except TypeError:
        raise TypeError("embed payload must be an embed or an iterable of embeds") from None


def _fields(embed: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    raw_fields = embed.get("fields") or []
    if isinstance(raw_fields, (str, bytes)) or not isinstance(raw_fields, Iterable):
        return []
    return [field for field in raw_fields if isinstance(field, Mapping)]


def embed_character_count(embed: Any) -> int:
    """Count all text components included in Discord's 6,000-character budget."""

    payload = _as_mapping(embed)
    total = _text_length(payload.get("title")) + _text_length(payload.get("description"))

    author = payload.get("author")
    if isinstance(author, Mapping):
        total += _text_length(author.get("name"))

    footer = payload.get("footer")
    if isinstance(footer, Mapping):
        total += _text_length(footer.get("text"))

    for field in _fields(payload):
        total += _text_length(field.get("name"))
        total += _text_length(field.get("value"))
    return total


def measure_embed_payload(embeds: Any) -> EmbedPayloadUsage:
    """Measure embed count, total text, and each embed's field count."""

    payloads = _normalise_embeds(embeds)
    return EmbedPayloadUsage(
        embed_count=len(payloads),
        total_characters=sum(embed_character_count(embed) for embed in payloads),
        field_counts=tuple(len(_fields(embed)) for embed in payloads),
    )


def validate_embed_payload(embeds: Any) -> tuple[EmbedLimitViolation, ...]:
    """Return every hard-limit violation in a Discord message embed payload."""

    payloads = _normalise_embeds(embeds)
    violations: list[EmbedLimitViolation] = []

    if len(payloads) > MAX_EMBEDS_PER_MESSAGE:
        violations.append(EmbedLimitViolation("embeds", len(payloads), MAX_EMBEDS_PER_MESSAGE))

    for embed_index, embed in enumerate(payloads):
        component_limits = (
            ("title", embed.get("title"), MAX_TITLE_CHARACTERS),
            ("description", embed.get("description"), MAX_DESCRIPTION_CHARACTERS),
        )
        for component, value, limit in component_limits:
            actual = _text_length(value)
            if actual > limit:
                violations.append(
                    EmbedLimitViolation(f"embeds[{embed_index}].{component}", actual, limit)
                )

        author = embed.get("author")
        if isinstance(author, Mapping):
            actual = _text_length(author.get("name"))
            if actual > MAX_AUTHOR_CHARACTERS:
                violations.append(
                    EmbedLimitViolation(
                        f"embeds[{embed_index}].author.name",
                        actual,
                        MAX_AUTHOR_CHARACTERS,
                    )
                )

        footer = embed.get("footer")
        if isinstance(footer, Mapping):
            actual = _text_length(footer.get("text"))
            if actual > MAX_FOOTER_CHARACTERS:
                violations.append(
                    EmbedLimitViolation(
                        f"embeds[{embed_index}].footer.text",
                        actual,
                        MAX_FOOTER_CHARACTERS,
                    )
                )

        fields = _fields(embed)
        if len(fields) > MAX_FIELDS_PER_EMBED:
            violations.append(
                EmbedLimitViolation(
                    f"embeds[{embed_index}].fields",
                    len(fields),
                    MAX_FIELDS_PER_EMBED,
                )
            )
        for field_index, field in enumerate(fields):
            for component, limit in (
                ("name", MAX_FIELD_NAME_CHARACTERS),
                ("value", MAX_FIELD_VALUE_CHARACTERS),
            ):
                actual = _text_length(field.get(component))
                if actual > limit:
                    violations.append(
                        EmbedLimitViolation(
                            f"embeds[{embed_index}].fields[{field_index}].{component}",
                            actual,
                            limit,
                        )
                    )

    total_characters = sum(embed_character_count(embed) for embed in payloads)
    if total_characters > MAX_TOTAL_CHARACTERS:
        violations.append(
            EmbedLimitViolation(
                "message.embed_text_total",
                total_characters,
                MAX_TOTAL_CHARACTERS,
            )
        )
    return tuple(violations)


def require_valid_embed_payload(embeds: Any) -> EmbedPayloadUsage:
    """Return measured usage or raise with every hard-limit violation."""

    violations = validate_embed_payload(embeds)
    if violations:
        raise EmbedPayloadLimitError(violations)
    return measure_embed_payload(embeds)
