from __future__ import annotations

from dataclasses import replace

from kvk.models.kvk_targets_card import KvkTargetMetricProgress, KvkTargetsCardPayload
from kvk.rendering import kvk_targets_card_renderer as renderer


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
        progress_state=state,
        status_label="Push now" if state == "active" else "Exempt",
        status_detail="Targets are active for this KVK.",
        next_action="Focus kills first: 8M remaining.",
        power=123_000_000,
        metrics=metrics,
        last_refreshed="2026-06-05 10:30 UTC",
        publication_state="OFFICIAL",
        target_source_scan=1059,
        target_published_at="2026-06-05 10:00 UTC",
    )


def test_targets_renderer_returns_png_bytes_for_active_payload():
    rendered = renderer.render_kvk_targets_card(_payload())

    assert rendered is not None
    assert rendered.filename == "kvk_targets_2441482.png"
    data = rendered.image_bytes.getvalue()
    assert data.startswith(b"\x89PNG")
    assert len(data) > 1_000


def test_targets_renderer_returns_png_bytes_for_empty_state():
    rendered = renderer.render_kvk_targets_card(_payload(state="exempt"))

    assert rendered is not None
    assert rendered.image_bytes.getvalue().startswith(b"\x89PNG")


def test_targets_renderer_prefers_canonical_unknown_publication_warning(monkeypatch):
    payload = replace(
        _payload(),
        publication_state="UNKNOWN",
        target_source_scan=None,
        warnings=("Target publication provenance could not be verified.",),
    )
    drawn_text: list[str] = []
    original_draw_text = renderer._draw_text

    def capture_draw_text(draw, xy, text, **kwargs):
        drawn_text.append(text)
        return original_draw_text(draw, xy, text, **kwargs)

    monkeypatch.setattr(renderer, "_draw_text", capture_draw_text)

    rendered = renderer.render_kvk_targets_card(payload)

    assert rendered is not None
    assert "Do not treat this target set as Official." in drawn_text
    assert "Target publication provenance could not be verified." not in drawn_text
