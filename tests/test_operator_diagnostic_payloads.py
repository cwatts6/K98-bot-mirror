from types import SimpleNamespace

import pytest

from core.discord_embed_limits import require_valid_embed_payload
from core.operator_diagnostic_payloads import (
    DEFAULT_ATTACHMENT_SIZE_LIMIT_BYTES,
    neutralize_discord_mentions,
    omission_marker,
    pack_complete_units,
    redact_diagnostic_text,
    resolve_attachment_size_limit,
    safe_attachment_filename,
    safe_diagnostic_content,
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


def test_redaction_consumes_quoted_keys_and_complete_quoted_values() -> None:
    source = (
        '{"token": "live-secret", "Authorization": "Bearer auth secret"}\n'
        'token="secret with spaces"\n'
        "'client_secret': 'another spaced secret'\n"
        'password="escaped \\" secret"'
    )

    redacted = redact_diagnostic_text(source)

    for secret in (
        "live-secret",
        "auth secret",
        "secret with spaces",
        "another spaced secret",
        "escaped",
    ):
        assert secret not in redacted
    assert redacted.count("[REDACTED]") == 5
    assert '{"token": "[REDACTED]"' in redacted
    assert '"Authorization": "[REDACTED]"' in redacted


def test_diagnostic_mentions_are_neutralized_without_hiding_identity() -> None:
    source = "@everyone @here <@123> <@!456> <@&789>"

    neutralized = neutralize_discord_mentions(source)

    assert "@everyone" not in neutralized
    assert "@here" not in neutralized
    assert "<@123>" not in neutralized
    assert "<@!456>" not in neutralized
    assert "<@&789>" not in neutralized
    assert neutralized.replace("\u200b", "") == source
    assert neutralize_discord_mentions("ordinary user@example.com text") == (
        "ordinary user@example.com text"
    )


def test_safe_diagnostic_content_redacts_and_neutralizes_mentions() -> None:
    content = safe_diagnostic_content(
        "Failed:", "sheet @everyone from <@123> role <@&456> token=secret"
    )

    assert "@everyone" not in content
    assert "<@123>" not in content
    assert "<@&456>" not in content
    assert "secret" not in content
    assert "[REDACTED]" in content


def test_command_modules_reuse_canonical_diagnostic_content_helper() -> None:
    from commands import admin_cmds, stats_cmds, subscriptions_cmds

    assert admin_cmds._safe_operator_content is safe_diagnostic_content
    assert stats_cmds._safe_diagnostic_error is safe_diagnostic_content
    assert subscriptions_cmds._safe_diagnostic_error is safe_diagnostic_content


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


def test_omission_marker_supports_explicit_singular_label() -> None:
    assert (
        omission_marker(1, "audit batches", singular_label="audit batch")
        == "… 1 audit batch not shown."
    )
    assert omission_marker(2, "audit batches", singular_label="audit batch") == (
        "… 2 audit batches not shown."
    )


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


@pytest.mark.asyncio
async def test_subscriber_list_reserves_field_for_omission_marker(monkeypatch) -> None:
    from commands import subscriptions_cmds

    class FakeBot:
        def __init__(self) -> None:
            self.application_commands = []

        def slash_command(self, **_kwargs):
            return lambda callback: callback

        def add_application_command(self, command) -> None:
            self.application_commands.append(command)

    class FakeInteraction:
        attachment_size_limit = DEFAULT_ATTACHMENT_SIZE_LIMIT_BYTES

        def __init__(self) -> None:
            self.edits: list[dict] = []

        async def edit_original_response(self, **kwargs):
            self.edits.append(kwargs)

    async def fake_defer(_ctx, *, ephemeral: bool) -> None:
        assert ephemeral is True

    subscribers = {
        str(1000 + index): {
            "username": f"User {index:02d}",
            "subscriptions": ["fights"],
            "reminder_times": ["5m"],
        }
        for index in range(26)
    }
    monkeypatch.setattr(subscriptions_cmds, "safe_defer", fake_defer)
    monkeypatch.setattr(subscriptions_cmds, "get_all_subscribers", lambda: subscribers)
    monkeypatch.setattr(subscriptions_cmds, "dm_scheduled_tracker", {})
    monkeypatch.setattr(subscriptions_cmds, "dm_sent_tracker", {})
    monkeypatch.setattr(subscriptions_cmds, "active_task_count", lambda _uid: 0)

    bot = FakeBot()
    subscriptions_cmds.register_subscriptions(bot)
    group = bot.application_commands[0]
    handler = next(command.callback for command in group.subcommands if command.name == "list")
    while hasattr(handler, "__wrapped__"):
        handler = handler.__wrapped__
    interaction = FakeInteraction()

    await handler(SimpleNamespace(interaction=interaction))

    response = interaction.edits[-1]
    embed = response["embed"]
    require_valid_embed_payload(embed)
    assert len(embed.fields) == 25
    assert embed.fields[-1].name == "Subscriber display compacted"
    assert embed.fields[-1].value == "… 2 subscribers not shown."
    assert len(response["attachments"]) == 1

    subscribers.pop("1025")
    exact_interaction = FakeInteraction()

    await handler(SimpleNamespace(interaction=exact_interaction))

    exact_response = exact_interaction.edits[-1]
    exact_embed = exact_response["embed"]
    require_valid_embed_payload(exact_embed)
    assert len(exact_embed.fields) == 25
    assert exact_embed.fields[-1].name == "User 24 • <@1024>"
    assert exact_response["attachments"] == []
