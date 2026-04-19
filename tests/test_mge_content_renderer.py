from __future__ import annotations

"""Tests for mge.mge_content_renderer.

All tests are self-contained — no DB, no Discord, no bot needed.
"""

from mge.mge_content_renderer import (
    is_structured_content,
    parse_mge_content_sections,
    render_legacy_mge_text,
    render_mge_content_to_embed_fields,
    render_mge_sections_to_embed_fields,
    split_field_value_safely,
)

# ---------------------------------------------------------------------------
# is_structured_content
# ---------------------------------------------------------------------------


def test_is_structured_content_true():
    """Text with # Header is detected as structured."""
    text = "# General Rules\nLine of text here."
    assert is_structured_content(text) is True


def test_is_structured_content_false():
    """Plain prose without any markers is not detected as structured."""
    text = "This is plain prose with no markers at all."
    assert is_structured_content(text) is False


def test_is_structured_content_bullet_detected():
    """Leading dash bullet is detected as structured."""
    text = "- First bullet\n- Second bullet"
    assert is_structured_content(text) is True


def test_is_structured_content_warning_detected():
    """! warning marker is detected as structured."""
    text = "! Important warning"
    assert is_structured_content(text) is True


def test_is_structured_content_empty():
    """Empty string is not structured."""
    assert is_structured_content("") is False


# ---------------------------------------------------------------------------
# parse_mge_content_sections
# ---------------------------------------------------------------------------


def test_parse_sections_basic():
    """# Header\\nLine\\n- Bullet parses correctly."""
    text = "# Rules\nThis is a rule.\n- Bullet item"
    sections = parse_mge_content_sections(text)

    assert len(sections) >= 1
    first = sections[0]
    assert first["type"] == "section"
    assert first["title"] == "Rules"
    lines = first["lines"]
    assert any("This is a rule." in line for line in lines)
    assert any("Bullet item" in line for line in lines)


def test_parse_sections_warning():
    """! Warning\\nText parses as warning section."""
    text = "! Watch Out\nThis is warning text."
    sections = parse_mge_content_sections(text)

    warning_sections = [s for s in sections if s["type"] == "warning"]
    assert warning_sections, "Expected at least one warning section"
    ws = warning_sections[0]
    assert "Watch Out" in ws["title"]


def test_parse_sections_multiple():
    """Multiple sections parse independently."""
    text = "# Section A\nLine A\n\n# Section B\nLine B"
    sections = parse_mge_content_sections(text)
    titles = [s["title"] for s in sections]
    assert "Section A" in titles
    assert "Section B" in titles


def test_parse_sections_empty():
    """Empty string returns a single plain fallback section."""
    sections = parse_mge_content_sections("")
    assert len(sections) == 1
    assert sections[0]["type"] == "plain"


def test_parse_sections_none_like():
    """None-like empty input returns a fallback section without crashing."""
    sections = parse_mge_content_sections("")
    assert isinstance(sections, list)
    assert len(sections) >= 1


# ---------------------------------------------------------------------------
# render_mge_sections_to_embed_fields
# ---------------------------------------------------------------------------


def test_render_fields_structured():
    """Structured text produces expected field names/values."""
    text = "# Registration\nSign up before Thursday.\n- Check your kills\n- Submit screenshot"
    sections = parse_mge_content_sections(text)
    fields = render_mge_sections_to_embed_fields(sections)

    assert fields, "Expected at least one field"
    names = [name for name, _ in fields]
    values = [value for _, value in fields]

    # Should have a field related to "Registration"
    assert any("Registration" in n for n in names)
    combined_values = "\n".join(values)
    assert "Check your kills" in combined_values


def test_render_fields_warning():
    """Warning section renders with ⚠️ prefix."""
    text = "! Deadline\nSubmit by Friday."
    sections = parse_mge_content_sections(text)
    fields = render_mge_sections_to_embed_fields(sections)

    names = [name for name, _ in fields]
    assert any("⚠️" in n for n in names)


def test_render_fields_empty_sections():
    """Empty sections list returns safe fallback."""
    fields = render_mge_sections_to_embed_fields([])
    assert len(fields) == 1
    assert fields[0] == ("Rules", "—")


# ---------------------------------------------------------------------------
# render_legacy_mge_text
# ---------------------------------------------------------------------------


def test_render_legacy_text():
    """Plain text renders as single field with fallback name."""
    text = "No structured markers here, just plain text."
    fields = render_legacy_mge_text(text)

    assert len(fields) >= 1
    name, value = fields[0]
    assert name == "Rules"
    assert "plain text" in value


def test_render_legacy_text_empty():
    """Empty text returns safe fallback."""
    fields = render_legacy_mge_text("")
    assert fields == [("Rules", "—")]


# ---------------------------------------------------------------------------
# split_field_value_safely
# ---------------------------------------------------------------------------


def test_split_field_value_safely_long():
    """Text > 1024 chars splits into multiple chunks, each ≤ 1024."""
    long_text = ("A" * 500 + "\n") * 5  # 2505 chars with newlines
    chunks = split_field_value_safely(long_text, limit=1024)

    assert len(chunks) > 1, "Expected multiple chunks for long text"
    for chunk in chunks:
        assert len(chunk) <= 1024, f"Chunk length {len(chunk)} exceeds 1024"


def test_split_field_value_safely_short():
    """Short text returns a single-element list."""
    text = "Short text."
    chunks = split_field_value_safely(text, limit=1024)
    assert chunks == ["Short text."]


def test_split_field_value_safely_empty():
    """Empty string returns ['—'] (never empty list)."""
    chunks = split_field_value_safely("", limit=1024)
    assert chunks == ["—"]


def test_split_field_value_safely_no_newline():
    """Text with no newlines is hard-split at the limit."""
    text = "X" * 2048
    chunks = split_field_value_safely(text, limit=1024)
    assert len(chunks) == 2
    for chunk in chunks:
        assert len(chunk) <= 1024


# ---------------------------------------------------------------------------
# render_mge_content_to_embed_fields — top-level entry point
# ---------------------------------------------------------------------------


def test_render_none_input():
    """None input returns safe fallback with at least one tuple."""
    fields = render_mge_content_to_embed_fields(None)
    assert isinstance(fields, list)
    assert len(fields) >= 1
    name, value = fields[0]
    assert name  # non-empty name
    assert value == "—"


def test_render_empty_string():
    """Empty string returns safe fallback."""
    fields = render_mge_content_to_embed_fields("")
    assert isinstance(fields, list)
    assert len(fields) >= 1
    _, value = fields[0]
    assert value == "—"


def test_render_malformed_input():
    """Completely unusual/malformed input does not raise."""
    fields = render_mge_content_to_embed_fields("##!!--\x00\xff" * 100)
    assert isinstance(fields, list)
    assert len(fields) >= 1


def test_render_structured_content_entry_point():
    """Top-level function correctly routes structured text through renderer."""
    text = "# Overview\nThis is the overview.\n- Check roster\n- Confirm targets"
    fields = render_mge_content_to_embed_fields(text, fallback_name="Rules")

    assert fields
    names = [n for n, _ in fields]
    values = [v for _, v in fields]
    assert any("Overview" in n for n in names)
    combined = "\n".join(values)
    assert "Check roster" in combined


def test_render_legacy_content_entry_point():
    """Top-level function correctly routes plain/legacy text."""
    text = "Plain text with no structured markers whatsoever."
    fields = render_mge_content_to_embed_fields(text, fallback_name="MyField")

    assert fields
    name, value = fields[0]
    assert name == "MyField"
    assert "Plain text" in value


def test_render_fallback_name_applied():
    """fallback_name parameter is used for unnamed fields."""
    text = "Some plain text."
    fields = render_mge_content_to_embed_fields(text, fallback_name="Reminders")
    assert fields[0][0] == "Reminders"
