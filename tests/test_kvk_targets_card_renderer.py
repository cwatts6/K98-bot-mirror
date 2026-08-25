from __future__ import annotations

from kvk.models.kvk_targets_card import KvkTargetMetricProgress, KvkTargetsCardPayload
from kvk.rendering.kvk_targets_card_renderer import render_kvk_targets_card


def _payload(*, state: str = "active") -> KvkTargetsCardPayload:
    metrics = ()
    if state == "active":
        metrics = (
            KvkTargetMetricProgress("Kills", 12_000_000, 20_000_000, 60.0, 8_000_000),
            KvkTargetMetricProgress("Deads", 1_200_000, 1_000_000, 120.0, 0),
            KvkTargetMetricProgress("DKP", 25_000_000, 50_000_000, 50.0, 25_000_000),
        )
    return KvkTargetsCardPayload(
        governor_id="2441482",
        governor_name="A Very Long Governor Name",
        kvk_no=15,
        kvk_name="Tides of War",
        camp_name="Wind",
        target_state=state,
        status_label="Push now" if state == "active" else "Exempt",
        status_detail="Targets are active for this KVK.",
        next_action="Focus kills first: 8M remaining.",
        power=123_000_000,
        metrics=metrics,
        last_refreshed="2026-06-05 10:30 UTC",
        source_state="ACTIVE",
    )


def test_targets_renderer_returns_png_bytes_for_active_payload():
    rendered = render_kvk_targets_card(_payload())

    assert rendered is not None
    assert rendered.filename == "kvk_targets_2441482.png"
    data = rendered.image_bytes.getvalue()
    assert data.startswith(b"\x89PNG")
    assert len(data) > 1_000


def test_targets_renderer_returns_png_bytes_for_empty_state():
    rendered = render_kvk_targets_card(_payload(state="exempt"))

    assert rendered is not None
    assert rendered.image_bytes.getvalue().startswith(b"\x89PNG")
