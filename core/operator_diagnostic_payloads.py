"""Pure helpers for safe, truthful operator diagnostic Discord payloads.

This module complements, rather than replaces, :mod:`core.discord_embed_limits`.
It owns message-content, complete-unit preview, redaction, attachment-name, and
destination upload-budget policy used by operator diagnostic routes.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
import re
from typing import Any

MAX_MESSAGE_CONTENT_CHARACTERS = 2000
MAX_ATTACHMENTS_PER_MESSAGE = 10
DEFAULT_ATTACHMENT_SIZE_LIMIT_BYTES = 10 * 1024 * 1024

_SENSITIVE_KEY_PATTERN = (
    r"(?:[a-z0-9]+[_-]+)*(?:secret[_-]?access[_-]?key|access[_-]?key[_-]?id|"
    r"private[_-]?key|api[_-]?key|client[_-]?secret|connection[_-]?string|"
    r"token|secret|password|passwd|pwd)"
)
_AUTHORIZATION_KEY_PATTERN = r"(?:[a-z0-9]+[_-]+)*authorization"
_DIAGNOSTIC_SENSITIVE_KEY_PATTERN = rf"(?:{_SENSITIVE_KEY_PATTERN}|{_AUTHORIZATION_KEY_PATTERN})"
_AUTHORIZATION_LINE_START_RE = re.compile(
    rf"(?i)(?P<key_quote>[\"']?)\b{_AUTHORIZATION_KEY_PATTERN}\b" r"(?P=key_quote)\s*[:=]"
)
_PRIVATE_KEY_PEM_START_RE = re.compile(
    rf"(?i)(?P<prefix>(?P<key_quote>[\"']?)\b{_SENSITIVE_KEY_PATTERN}\b"
    r"(?P=key_quote)\s*[:=]\s*[\"']?)"
    r"-----BEGIN [^-\r\n]*PRIVATE KEY-----"
)
_PRIVATE_KEY_PEM_END_RE = re.compile(r"(?i)-----END [^-\r\n]*PRIVATE KEY-----")
_SENSITIVE_INDENTED_VALUE_START_RE = re.compile(
    rf"(?i)(?:[\"']?\b{_DIAGNOSTIC_SENSITIVE_KEY_PATTERN}\b[\"']?)"
    r"\s*[:=]\s*(?:[|>](?:[1-9][+-]?|[+-][1-9]?)?)?"
    r"(?:[^\S\r\n]+#.*)?[^\S\r\n]*$"
)
_QUOTED_SENSITIVE_LINE_START_RE = re.compile(
    rf"(?i)(?:[\"']?\b{_DIAGNOSTIC_SENSITIVE_KEY_PATTERN}\b[\"']?)" r"\s*[:=]\s*(?P<quote>[\"'])"
)
_QUOTED_SENSITIVE_ASSIGNMENT_RE = re.compile(
    rf"(?i)(?P<key_quote>[\"']?)(?P<key>\b{_DIAGNOSTIC_SENSITIVE_KEY_PATTERN}\b)"
    r"(?P=key_quote)(?P<separator>\s*[:=]\s*)(?P<value_quote>[\"'])"
    r"(?P<value>(?:\\[\s\S]|(?!(?P=value_quote)|\\)[\s\S])*)(?P=value_quote)"
)
_UNTERMINATED_QUOTED_SENSITIVE_ASSIGNMENT_RE = re.compile(
    rf"(?im)(?P<key_quote>[\"']?)(?P<key>\b{_DIAGNOSTIC_SENSITIVE_KEY_PATTERN}\b)"
    r"(?P=key_quote)(?P<separator>[^\S\r\n]*[:=][^\S\r\n]*)"
    r"(?P<value_quote>[\"'])(?:\\[^\r\n]|\\(?=\r?$)|"
    r"(?!(?P=value_quote)|\\)[^\r\n])*(?=\r?$)"
)
_SENSITIVE_ASSIGNMENT_RE = re.compile(
    rf"(?i)(?P<key_quote>[\"']?)(?P<key>\b(?:{_SENSITIVE_KEY_PATTERN})\b)"
    r"(?P=key_quote)(?P<separator>\s*[:=]\s*)"
    r"(?P<value>(?!\s*[\"']|\s*\[REDACTED\])[^\s,;}\]\"']+)"
)
_AUTHORIZATION_ASSIGNMENT_RE = re.compile(
    rf"(?i)(?P<key_quote>[\"']?)(?P<key>\b{_AUTHORIZATION_KEY_PATTERN}\b)"
    r"(?P=key_quote)"
    r"(?P<separator>\s*[:=]\s*)"
    r"(?P<value>(?!\s*[\"']|\s*\[REDACTED\])[^\r\n;]+)"
)
_BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_SIGNED_QUERY_RE = re.compile(
    r"(?i)([?&](?:sig|signature|token|key|secret|x-amz-signature)=)[^&#\s]+"
)
_CONNECTION_PASSWORD_RE = re.compile(r"(?i)(\b(?:pwd|password)\s*=\s*)[^;\r\n]+")


@dataclass(frozen=True, slots=True)
class PackedUnits:
    """A bounded preview containing only complete units and a truthful count."""

    text: str
    shown: int
    omitted: int


def _redact_quoted_assignment(match: re.Match[str]) -> str:
    line_breaks = re.findall(r"\r\n|\r|\n", match.group("value"))
    redacted_value = "[REDACTED]" + "".join(f"{line_break}[REDACTED]" for line_break in line_breaks)
    return (
        f"{match.group('key_quote')}{match.group('key')}{match.group('key_quote')}"
        f"{match.group('separator')}{match.group('value_quote')}"
        f"{redacted_value}{match.group('value_quote')}"
    )


def redact_diagnostic_text(value: Any) -> str:
    """Redact common credential-bearing forms without changing line ordering."""

    text = "" if value is None else str(value)
    text = _QUOTED_SENSITIVE_ASSIGNMENT_RE.sub(_redact_quoted_assignment, text)
    text = _UNTERMINATED_QUOTED_SENSITIVE_ASSIGNMENT_RE.sub(
        lambda match: (
            f"{match.group('key_quote')}{match.group('key')}{match.group('key_quote')}"
            f"{match.group('separator')}{match.group('value_quote')}[REDACTED]"
        ),
        text,
    )
    text = _AUTHORIZATION_ASSIGNMENT_RE.sub(
        lambda match: (
            f"{match.group('key_quote')}{match.group('key')}{match.group('key_quote')}"
            f"{match.group('separator')}[REDACTED]"
        ),
        text,
    )
    text = _BEARER_RE.sub("Bearer [REDACTED]", text)
    text = _SENSITIVE_ASSIGNMENT_RE.sub(
        lambda match: (
            f"{match.group('key_quote')}{match.group('key')}{match.group('key_quote')}"
            f"{match.group('separator')}[REDACTED]"
        ),
        text,
    )
    text = _SIGNED_QUERY_RE.sub(r"\1[REDACTED]", text)
    return _CONNECTION_PASSWORD_RE.sub(r"\1[REDACTED]", text)


def _physical_lines(value: Any) -> list[str]:
    text = "" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if text.endswith("\n"):
        text = text[:-1]
    return text.split("\n")


def _unescaped_quote_index(value: str, quote: str, *, start: int = 0) -> int:
    escaped = False
    for index in range(start, len(value)):
        character = value[index]
        if character == "\\" and not escaped:
            escaped = True
            continue
        if character == quote and not escaped:
            return index
        escaped = False
    return -1


def iter_redacted_diagnostic_line_pairs(
    values: Iterable[Any],
) -> Iterator[tuple[str, str]]:
    """Yield raw/redacted physical lines while retaining chronological context."""

    authorization_continuation = False
    sensitive_indented_value = False
    private_key_block = False
    quoted_continuation: str | None = None

    for value in values:
        for line in _physical_lines(value):
            if private_key_block:
                pem_end = _PRIVATE_KEY_PEM_END_RE.search(line)
                suffix = line[pem_end.end() :] if pem_end else ""
                yield line, f"[REDACTED]{redact_diagnostic_text(suffix)}"
                if pem_end:
                    private_key_block = False
                continue

            if quoted_continuation is not None:
                closing_index = _unescaped_quote_index(line, quoted_continuation)
                if closing_index < 0:
                    yield line, "[REDACTED]"
                    continue
                suffix = line[closing_index + 1 :]
                yield line, f"[REDACTED]{quoted_continuation}{redact_diagnostic_text(suffix)}"
                quoted_continuation = None
                continue

            if authorization_continuation and line[:1].isspace():
                indentation = line[: len(line) - len(line.lstrip())]
                yield line, f"{indentation}[REDACTED]"
                continue
            authorization_continuation = False

            if sensitive_indented_value and line[:1].isspace():
                indentation = line[: len(line) - len(line.lstrip())]
                yield line, f"{indentation}[REDACTED]"
                continue
            sensitive_indented_value = False

            pem_start = _PRIVATE_KEY_PEM_START_RE.search(line)
            if pem_start:
                pem_end = _PRIVATE_KEY_PEM_END_RE.search(line, pem_start.end())
                suffix = line[pem_end.end() :] if pem_end else ""
                yield line, (
                    f"{line[: pem_start.start()]}{pem_start.group('prefix')}[REDACTED]"
                    f"{redact_diagnostic_text(suffix)}"
                )
                private_key_block = pem_end is None
                continue

            quoted_start = _QUOTED_SENSITIVE_LINE_START_RE.search(line)
            if quoted_start:
                quote = quoted_start.group("quote")
                if _unescaped_quote_index(line, quote, start=quoted_start.end()) < 0:
                    quoted_continuation = quote

            yield line, redact_diagnostic_text(line)
            authorization_continuation = bool(_AUTHORIZATION_LINE_START_RE.search(line))
            sensitive_indented_value = bool(_SENSITIVE_INDENTED_VALUE_START_RE.search(line))


def redact_diagnostic_lines(values: Iterable[Any]) -> list[str]:
    """Return redacted physical lines without losing multiline secret context."""

    return [redacted for _, redacted in iter_redacted_diagnostic_line_pairs(values)]


def neutralize_discord_mentions(value: Any) -> str:
    """Keep diagnostic content readable without creating Discord notifications."""

    text = "" if value is None else str(value)
    text = re.sub(
        r"(?i)@(everyone|here)\b",
        lambda match: f"@\u200b{match.group(1)}",
        text,
    )
    return re.sub(r"<@(?=[!&]?\d+>)", "<@\u200b", text)


def utf8_size(value: Any) -> int:
    """Return the encoded byte size used by Discord multipart uploads."""

    return len(("" if value is None else str(value)).encode("utf-8"))


def safe_attachment_filename(value: Any, *, default: str = "diagnostic.txt") -> str:
    """Return a conservative transport name; source names remain in file content."""

    raw = str(value or default).strip()
    stem, dot, suffix = raw.rpartition(".")
    if not dot:
        stem, suffix = raw, "txt"
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem).strip("._") or "diagnostic"
    suffix = re.sub(r"[^A-Za-z0-9]+", "", suffix)[:12] or "txt"
    return f"{stem[:100]}.{suffix}"


def resolve_attachment_size_limit(destination: Any) -> int:
    """Resolve the current interaction/guild upload entitlement conservatively."""

    candidates = (
        getattr(destination, "attachment_size_limit", None),
        getattr(getattr(destination, "guild", None), "filesize_limit", None),
        getattr(getattr(destination, "channel", None), "guild", None),
    )
    for candidate in candidates:
        if candidate is not None and not isinstance(candidate, (int, float)):
            candidate = getattr(candidate, "filesize_limit", None)
        try:
            parsed = int(candidate)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            return parsed
    return DEFAULT_ATTACHMENT_SIZE_LIMIT_BYTES


def omission_marker(omitted: int, label: str, *, singular_label: str | None = None) -> str:
    """Return the canonical exact count-bearing exhaustion marker."""

    noun = label
    if omitted == 1:
        noun = singular_label if singular_label is not None else label.removesuffix("s")
    return f"… {omitted} {noun} not shown."


def pack_complete_units(
    units: Iterable[Any],
    *,
    limit: int,
    label: str,
    separator: str = "\n",
    prefix: str = "",
    suffix: str = "",
) -> PackedUnits:
    """Pack whole units within ``limit`` and reserve room for an omission marker.

    Units that cannot fit are omitted as whole units. Later units are not promoted
    ahead of an earlier oversized unit, preserving source ordering.
    """

    values = ["" if item is None else str(item) for item in units]
    if limit < len(prefix) + len(suffix):
        raise ValueError("limit is too small for prefix and suffix")
    if not values:
        return PackedUnits(f"{prefix}{suffix}", 0, 0)

    selected: list[str] = []
    for index, value in enumerate(values):
        candidate = separator.join([*selected, value])
        omitted = len(values) - index - 1
        marker = omission_marker(omitted, label) if omitted else ""
        candidate_body = separator.join(part for part in (candidate, marker) if part)
        if len(prefix) + len(candidate_body) + len(suffix) <= limit:
            selected.append(value)
            continue
        break

    shown = len(selected)
    omitted = len(values) - shown
    marker = omission_marker(omitted, label) if omitted else ""
    body = separator.join([*selected, *([marker] if marker else [])])

    # A very long label could make even the marker too large. Keep the exact count.
    if len(prefix) + len(body) + len(suffix) > limit:
        marker = f"… {omitted} item(s) not shown."
        while selected:
            selected.pop()
            omitted = len(values) - len(selected)
            marker = f"… {omitted} item(s) not shown."
            body = separator.join([*selected, marker])
            if len(prefix) + len(body) + len(suffix) <= limit:
                break
        if not selected:
            body = marker[: max(0, limit - len(prefix) - len(suffix))]
    return PackedUnits(f"{prefix}{body}{suffix}", len(selected), len(values) - len(selected))


def safe_diagnostic_content(prefix: str, detail: Any) -> str:
    """Build bounded diagnostic content with centralized redaction and mention safety."""

    return pack_complete_units(
        [prefix, neutralize_discord_mentions(redact_diagnostic_text(detail))],
        limit=MAX_MESSAGE_CONTENT_CHARACTERS,
        label="diagnostic lines",
    ).text
