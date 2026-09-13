from datetime import UTC, datetime, timedelta

from core.discord_embed_limits import validate_embed_payload
import daily_KVK_overview_embed as mod


def _events(count: int, *, name_length: int = 20):
    start = datetime.now(UTC) + timedelta(hours=1)
    return [
        {
            "name": f"{'N' * name_length}-{index}",
            "type": "ruins",
            "start_time": start + timedelta(minutes=index),
        }
        for index in range(count)
    ]


def test_daily_overview_retains_complete_events_and_exact_cap_marker():
    embed = mod.build_daily_KVK_overview_embed(_events(8))
    values = "\n".join(field.value for field in embed.fields)

    assert values.count("• **") == 6
    assert "… 2 more ruins events in the next 4 days — use Local Time" in values
    assert not validate_embed_payload(embed)


def test_daily_overview_pathological_single_event_is_compacted_not_dropped():
    embed = mod.build_daily_KVK_overview_embed(_events(1, name_length=8000))
    values = "\n".join(field.value for field in embed.fields)

    assert values.count("• **") == 1
    assert values.count("…") == 1
    assert "more ruins events" not in values
    assert not validate_embed_payload(embed)


def test_daily_overview_aggregate_exhaustion_has_exact_omission_counts():
    events = []
    for event_type in ("ruins", "altars", "chronicle", "major"):
        events.extend({**event, "type": event_type} for event in _events(6, name_length=900))

    embed = mod.build_daily_KVK_overview_embed(events)
    values = "\n".join(field.value for field in embed.fields)
    shown = values.count("• **")
    marker_total = sum(
        int(line.split()[1])
        for line in values.splitlines()
        if line.startswith("… ") and " more " in line
    )

    assert shown + marker_total == len(events)
    assert marker_total > 0
    assert not validate_embed_payload(embed)
