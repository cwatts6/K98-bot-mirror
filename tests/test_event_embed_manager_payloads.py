from datetime import UTC, datetime, timedelta
import logging

from core.discord_embed_limits import (
    MAX_DESCRIPTION_CHARACTERS,
    MAX_TITLE_CHARACTERS,
    validate_embed_payload,
)
import event_embed_manager as mod


def _event(**overrides):
    event = {
        "name": "Ruins",
        "type": "ruins",
        "description": "Prepare the marches.",
        "start_time": datetime.now(UTC) + timedelta(hours=2),
    }
    event.update(overrides)
    return event


def test_live_event_embed_compacts_pathological_free_text_as_complete_components():
    embed = mod.build_event_embed(_event(name="N" * 600, description="D" * 7000))

    assert len(embed.title) == MAX_TITLE_CHARACTERS
    assert embed.title.endswith("…")
    assert len(embed.description) == MAX_DESCRIPTION_CHARACTERS
    assert embed.description.endswith("\n\u200b")
    assert "**Starts <t:" in embed.description
    assert not validate_embed_payload(embed)


def test_live_event_embed_preserves_exact_title_boundary_and_compacts_one_over():
    prefix_length = len("\ud83d\udcc5 ")
    exact = mod.build_event_embed(_event(name="N" * (MAX_TITLE_CHARACTERS - prefix_length)))
    one_over = mod.build_event_embed(_event(name="N" * (MAX_TITLE_CHARACTERS - prefix_length + 1)))

    assert len(exact.title) == MAX_TITLE_CHARACTERS
    assert not exact.title.endswith("…")
    assert len(one_over.title) == MAX_TITLE_CHARACTERS
    assert one_over.title.endswith("…")
    assert not validate_embed_payload([exact, one_over])


def test_live_event_payload_metrics_do_not_log_source_content(caplog):
    secret = "operator-private-event-text"
    with caplog.at_level(logging.INFO, logger=mod.__name__):
        mod.build_event_embed(_event(name=secret, description=secret))

    assert "renderer=live_event" in caplog.text
    assert "fields=" in caplog.text
    assert "chars=" in caplog.text
    assert secret not in caplog.text
