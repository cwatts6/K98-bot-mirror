from __future__ import annotations

"""Structured plain-text parser and Discord embed field renderer for MGE content.

Admins write lightweight structured text; this module converts it to embed fields.

Structured syntax
-----------------
``# Section Header``  — section name rendered as bold embed field name
``- Bullet item``     — bullet item rendered with ``•`` prefix
``! Warning Title``   — warning block rendered with ``⚠️`` prefix as its own field
blank line            — section break
plain line            — paragraph text within the current section

Legacy / plain text
-------------------
If the text contains none of the structured markers (``#``, leading ``-``, ``!``),
it is treated as plain/legacy and rendered as-is with no reformatting.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_STRUCTURED_MARKERS = ("#", "!", "-")


def is_structured_content(text: str) -> bool:
    """Return True if *text* uses the structured marker syntax (``#``, leading ``-``, ``!``).

    Args:
        text: Raw content string to inspect.

    Returns:
        ``True`` when at least one structured marker is found at line start.
    """
    if not text:
        return False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("!"):
            return True
        if stripped.startswith("-") and len(stripped) > 1:
            return True
    return False


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def parse_mge_content_sections(text: str) -> list[dict[str, Any]]:
    """Parse structured plain text into a list of section dicts.

    Each dict has the shape::

        {
            "type": "section" | "warning" | "plain",
            "title": str,
            "lines": list[str],
        }

    Falls back to a single ``"plain"`` section on any error or on empty input.

    Args:
        text: Structured (or plain) content string.

    Returns:
        List of section dicts, always at least one element.
    """
    if not text or not text.strip():
        return [{"type": "plain", "title": "", "lines": []}]

    try:
        sections: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None

        def _flush() -> None:
            nonlocal current
            if current is not None:
                sections.append(current)
            current = None

        for raw_line in text.splitlines():
            line = raw_line.strip()

            if line.startswith("# "):
                # Section header
                _flush()
                title = line[2:].strip()
                current = {"type": "section", "title": title, "lines": []}

            elif line.startswith("!"):
                # Warning block — flush previous, treat rest as title + first line
                _flush()
                rest = line[1:].strip()
                # If there's a newline in the rest (multi-line !), first token is title
                current = {"type": "warning", "title": rest, "lines": []}

            elif line.startswith("- ") or line == "-":
                bullet = line[2:].strip() if line.startswith("- ") else ""
                if not bullet:
                    # Standalone "-" with no text — skip empty bullet
                    continue
                if current is None:
                    current = {"type": "section", "title": "", "lines": []}
                current["lines"].append(f"• {bullet}")

            elif line == "":
                # Blank line → section break; flush and start fresh unnamed section
                if current is not None and current["lines"]:
                    _flush()

            else:
                # Plain paragraph line within current section
                if current is None:
                    current = {"type": "section", "title": "", "lines": []}
                current["lines"].append(line)

        _flush()

        if not sections:
            return [{"type": "plain", "title": "", "lines": [text.strip()]}]

        return sections

    except Exception:
        logger.exception("parse_mge_content_sections failed — returning plain fallback")
        return [{"type": "plain", "title": "", "lines": [text.strip()]}]


# ---------------------------------------------------------------------------
# Renderer helpers
# ---------------------------------------------------------------------------


def split_field_value_safely(text: str, limit: int = 1024) -> list[str]:
    """Split *text* into chunks each ≤ *limit* characters, preferring newline boundaries.

    Args:
        text: Text to split.
        limit: Maximum characters per chunk (default 1024).

    Returns:
        List of chunks.  Never returns an empty list.
    """
    if not text:
        return ["—"]

    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break

        # Try to split at a newline boundary within the limit
        slice_ = remaining[:limit]
        split_pos = slice_.rfind("\n")
        if split_pos > 0:
            chunks.append(remaining[:split_pos])
            remaining = remaining[split_pos + 1 :]
        else:
            # No newline found — hard split
            chunks.append(slice_)
            remaining = remaining[limit:]

    return chunks or ["—"]


def render_legacy_mge_text(text: str, *, max_field_value: int = 1024) -> list[tuple[str, str]]:
    """Render a plain/legacy text blob as embed fields.

    Splits on *max_field_value* boundaries using :func:`split_field_value_safely`.

    Args:
        text: Plain text string.
        max_field_value: Maximum characters per embed field value.

    Returns:
        List of ``(name, value)`` tuples.
    """
    if not text or not text.strip():
        return [("Rules", "—")]

    chunks = split_field_value_safely(text.strip(), max_field_value)
    result: list[tuple[str, str]] = []
    for idx, chunk in enumerate(chunks):
        name = "Rules" if idx == 0 else f"Rules (cont.)"
        result.append((name, chunk or "—"))
    return result


def render_mge_sections_to_embed_fields(
    sections: list[dict[str, Any]],
    *,
    max_field_value: int = 1024,
) -> list[tuple[str, str]]:
    """Convert parsed sections to a list of ``(name, value)`` tuples for ``embed.add_field()``.

    Respects *max_field_value*.  Splits oversized content across continuation fields.
    Never returns empty values (minimum ``"—"``).

    Args:
        sections: List of section dicts produced by :func:`parse_mge_content_sections`.
        max_field_value: Maximum characters per embed field value.

    Returns:
        List of ``(name, value)`` tuples.  At least one tuple is always returned.
    """
    if not sections:
        return [("Rules", "—")]

    result: list[tuple[str, str]] = []

    try:
        for section in sections:
            sec_type = str(section.get("type") or "plain")
            title = str(section.get("title") or "").strip()
            lines: list[str] = list(section.get("lines") or [])

            if sec_type == "warning":
                # Warning: ⚠️ prefix on name, body is the warning text lines
                name = f"⚠️ {title}" if title else "⚠️ Warning"
                body = "\n".join(lines) if lines else "—"
                if not body.strip():
                    body = "—"
                for idx, chunk in enumerate(split_field_value_safely(body, max_field_value)):
                    result.append((name if idx == 0 else f"{name} (cont.)", chunk or "—"))

            elif sec_type == "section":
                name = f"**{title}**" if title else "Rules"
                body = "\n".join(lines) if lines else "—"
                if not body.strip():
                    body = "—"
                for idx, chunk in enumerate(split_field_value_safely(body, max_field_value)):
                    result.append((name if idx == 0 else f"{name} (cont.)", chunk or "—"))

            else:
                # plain
                name = title or "Rules"
                body = "\n".join(lines) if lines else "—"
                if not body.strip():
                    body = "—"
                for idx, chunk in enumerate(split_field_value_safely(body, max_field_value)):
                    result.append((name if idx == 0 else f"{name} (cont.)", chunk or "—"))

    except Exception:
        logger.exception("render_mge_sections_to_embed_fields failed — returning fallback")
        return [("Rules", "—")]

    return result or [("Rules", "—")]


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------


def render_mge_content_to_embed_fields(
    text: str | None,
    *,
    fallback_name: str = "Rules",
    max_field_value: int = 1024,
) -> list[tuple[str, str]]:
    """Top-level entry point for rendering MGE content to embed fields.

    Detects whether *text* is structured or legacy, parses, and renders to a list
    of ``(name, value)`` tuples suitable for ``embed.add_field()``.

    Safe fallback: always returns at least one tuple even on ``None``, empty string,
    or completely malformed input.

    Args:
        text: Raw content string (may be ``None``).
        fallback_name: Field name used when no section title is available.
        max_field_value: Maximum characters per embed field value.

    Returns:
        List of ``(name, value)`` tuples.
    """
    try:
        safe_text = str(text or "").strip()

        if not safe_text:
            return [(fallback_name, "—")]

        if is_structured_content(safe_text):
            sections = parse_mge_content_sections(safe_text)
            fields = render_mge_sections_to_embed_fields(sections, max_field_value=max_field_value)
        else:
            fields = render_legacy_mge_text(safe_text, max_field_value=max_field_value)

        if not fields:
            return [(fallback_name, "—")]

        # Apply fallback_name to unnamed leading fields
        patched: list[tuple[str, str]] = []
        for name, value in fields:
            effective_name = name if name.strip() not in ("", "Rules") else fallback_name
            patched.append((effective_name, value or "—"))

        return patched or [(fallback_name, "—")]

    except Exception:
        logger.exception("render_mge_content_to_embed_fields failed — returning safe fallback")
        return [(fallback_name, "—")]
