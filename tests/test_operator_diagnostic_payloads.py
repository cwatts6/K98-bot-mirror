from types import SimpleNamespace

from core.discord_embed_limits import require_valid_embed_payload
from core.operator_diagnostic_payloads import (
    DEFAULT_ATTACHMENT_SIZE_LIMIT_BYTES,
    MAX_MESSAGE_CONTENT_CHARACTERS,
    content_pages,
    pack_complete_units,
    redact_diagnostic_text,
    resolve_attachment_size_limit,
    safe_attachment_filename,
    utf8_size,
)


def test_complete_unit_packing_exact_boundary_and_one_over() -> None:
    exact = pack_complete_units(["A" * 20], limit=20, label="rows")
    over = pack_complete_units(["A" * 21], limit=20, label="rows")

    assert exact.text == "A" * 20
    assert exact.shown == 1
    assert exact.omitted == 0
    assert over.shown == 0
    assert over.omitted == 1
    assert "1 row not shown" in over.text
    assert "A" not in over.text


def test_complete_unit_packing_reserves_truthful_omission_marker() -> None:
    packed = pack_complete_units(["first", "second", "X" * 200], limit=45, label="rows")

    assert packed.shown == 2
    assert packed.omitted == 1
    assert packed.text.splitlines() == ["first", "second", "… 1 row not shown."]


def test_redaction_is_consistent_for_preview_and_attachment_text() -> None:
    source = (
        "Authorization: Bearer abc.def\n"
        "password=hunter2;server=db\n"
        "https://example.test/file?X-Amz-Signature=abc123&part=1"
    )

    redacted = redact_diagnostic_text(source)

    assert "abc.def" not in redacted
    assert "hunter2" not in redacted
    assert "abc123" not in redacted
    assert redacted.count("[REDACTED]") == 3
    assert redacted.splitlines()[1].endswith(";server=db")


def test_utf8_size_measures_encoded_bytes() -> None:
    assert utf8_size("a") == 1
    assert utf8_size("🦊") == 4


def test_attachment_filename_is_conservative_and_deterministic() -> None:
    name = safe_attachment_filename("../Sensitive report 🦊.reallylongextension")

    assert name == "Sensitive_report.reallylongex"
    assert len(name) <= 113


def test_attachment_limit_resolution_prefers_interaction_then_guild() -> None:
    interaction = SimpleNamespace(
        attachment_size_limit=1234, guild=SimpleNamespace(filesize_limit=99)
    )
    channel = SimpleNamespace(guild=SimpleNamespace(filesize_limit=5678))

    assert resolve_attachment_size_limit(interaction) == 1234
    assert resolve_attachment_size_limit(channel) == 5678
    assert resolve_attachment_size_limit(object()) == DEFAULT_ATTACHMENT_SIZE_LIMIT_BYTES


def test_content_pages_preserve_normal_units_and_mark_pathological_unit() -> None:
    pages = content_pages(["first", "second", "X" * 2100], limit=80)

    assert pages[0] == "first\nsecond"
    assert pages[1] == "… 1 complete item not shown; see attached diagnostic."
    assert all(len(page) <= MAX_MESSAGE_CONTENT_CHARACTERS for page in pages)


def test_inventory_audit_embed_marks_records_beyond_field_limit(monkeypatch) -> None:
    from commands import inventory_cmds

    monkeypatch.setattr(
        inventory_cmds.audit_service,
        "summarize_json_comparison",
        lambda _record: "unchanged",
    )
    records = [
        SimpleNamespace(
            import_batch_id=index,
            status="completed",
            confidence_score=1.0,
            governor_id=1000 + index,
            discord_user_id=2000 + index,
            import_type="resources",
            flow_type="command",
            debug_reference="none",
        )
        for index in range(30)
    ]

    embed = inventory_cmds._build_inventory_audit_embed(records, days=7)

    require_valid_embed_payload(embed)
    assert len(embed.fields) == 25
    assert embed.fields[-1].name == "Audit display compacted"
    assert embed.fields[-1].value == "… 6 audit batches not shown."
