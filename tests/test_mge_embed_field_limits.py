from __future__ import annotations

"""Tests for Discord embed field limit enforcement in MGE content renderer.

Validates:
- 25-field overflow does not break message send (truncates gracefully)
- Field value > 1024 chars is split correctly
- Field name > 256 chars is truncated to 256
"""

import pytest

from mge.mge_content_renderer import (
    MAX_EMBED_FIELDS,
    render_mge_content_to_embed_fields,
    render_mge_sections_to_embed_fields,
    split_field_value_safely,
)


def test_overflow_25_fields_does_not_raise() -> None:
    """Content producing > 25 sections does not raise an exception."""
    lines = [f"# Section {i}\nContent {i}." for i in range(30)]
    text = "\n\n".join(lines)
    try:
        fields = render_mge_content_to_embed_fields(text, fallback_name="Rules")
    except Exception as exc:
        pytest.fail(f"render_mge_content_to_embed_fields raised unexpectedly: {exc}")
    assert fields, "Must return at least one field"


def test_overflow_25_fields_truncates_to_max() -> None:
    """Content producing > 25 sections is truncated to MAX_EMBED_FIELDS (25)."""
    lines = [f"# Section {i}\nContent {i}." for i in range(30)]
    text = "\n\n".join(lines)
    fields = render_mge_content_to_embed_fields(text, fallback_name="Rules")
    assert len(fields) <= MAX_EMBED_FIELDS, (
        f"Fields count {len(fields)} exceeds Discord limit of {MAX_EMBED_FIELDS}"
    )


def test_overflow_adds_continuation_notice() -> None:
    """When truncated, the last field indicates overflow."""
    sections = [{"type": "section", "title": f"S{i}", "lines": [f"L{i}"]} for i in range(30)]
    fields = render_mge_sections_to_embed_fields(sections)
    assert len(fields) <= MAX_EMBED_FIELDS
    last_name, last_value = fields[-1]
    assert (
        "overflow" in last_name.lower()
        or "overflow" in last_value.lower()
        or "truncated" in last_value.lower()
    ), f"Last field should indicate overflow/truncation, got: ({last_name!r}, {last_value!r})"


def test_field_value_over_1024_is_split() -> None:
    """A field value > 1024 chars is split into multiple chunks ≤ 1024 each."""
    long_text = "A" * 2048
    chunks = split_field_value_safely(long_text, limit=1024)
    assert len(chunks) >= 2, "Long text must be split into multiple chunks"
    for chunk in chunks:
        assert len(chunk) <= 1024, f"Chunk length {len(chunk)} exceeds 1024"


def test_field_value_split_never_empty() -> None:
    """split_field_value_safely never returns an empty list."""
    for text in ("", "short", "X" * 3000):
        chunks = split_field_value_safely(text, limit=1024)
        assert chunks, f"Expected non-empty chunk list for input length {len(text)}"


def test_field_name_over_256_is_truncated() -> None:
    """Section title > 256 chars is truncated to 256 in the rendered field name."""
    long_title = "T" * 300
    sections = [{"type": "section", "title": long_title, "lines": ["body"]}]
    fields = render_mge_sections_to_embed_fields(sections)
    assert fields, "Must return at least one field"
    first_name, _ = fields[0]
    assert len(first_name) <= 256, (
        f"Field name length {len(first_name)} exceeds 256-char Discord limit"
    )


def test_warning_field_name_over_256_is_truncated() -> None:
    """Warning section with long title is also truncated to 256."""
    long_title = "W" * 300
    sections = [{"type": "warning", "title": long_title, "lines": ["Warning body."]}]
    fields = render_mge_sections_to_embed_fields(sections)
    for name, _ in fields:
        assert len(name) <= 256, (
            f"Warning field name length {len(name)} exceeds 256-char Discord limit"
        )
