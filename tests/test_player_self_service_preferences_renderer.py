from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from io import BytesIO

from PIL import Image
import pytest

from player_self_service import preferences_renderer as renderer
from player_self_service.preferences_summary import (
    InventoryVisibilitySummary,
    PreferencesSummaryPayload,
    PreferenceValueSummary,
    RegionalProfileSummary,
    TimeReferenceSummary,
)


def _payload(*, public: bool = False) -> PreferencesSummaryPayload:
    regional = RegionalProfileSummary(
        timezone=PreferenceValueSummary(
            True, True, "United Kingdom", "Europe/London", "Europe/London"
        ),
        location=PreferenceValueSummary(True, True, "United Kingdom (GB)", "GB", "GB"),
        preferred_language=PreferenceValueSummary(True, True, "English (en-GB)", "en-GB", "en-GB"),
    )
    return PreferencesSummaryPayload(
        discord_user_id=42,
        display_name="Governor Tester",
        kingdom_id=1198,
        generated_at_utc=datetime(2026, 7, 15, 12, 34, tzinfo=UTC),
        inventory_visibility=InventoryVisibilitySummary(
            is_public=public,
            state_label="PUBLIC" if public else "PRIVATE",
            consequence_text=(
                "Detailed Inventory reports opened through /me inventory or /myinventory may be posted in the channel."
                if public
                else "Detailed Inventory reports opened through /me inventory or /myinventory are shown only to you."
            ),
            is_explicit=True,
        ),
        regional_profile=regional,
        time_reference=TimeReferenceSummary(
            mode="LOCAL",
            heading="LOCAL TIME REFERENCE",
            display_time="13:34",
            timezone_label="United Kingdom",
            utc_offset_label="UTC+1",
            supporting_line="United Kingdom • UTC+1",
            regional_context="United Kingdom (GB) • English (en-GB)",
        ),
        profile_details_set=3,
        profile_details_total=3,
        profile_supporting_text="3 of 3 profile details set",
        settings_insight="Your regional profile is complete and detailed Inventory reports remain private.",
    )


def _avatar_bytes() -> bytes:
    stream = BytesIO()
    with Image.new("RGB", (120, 120), (240, 20, 30)) as image:
        image.save(stream, format="PNG")
    return stream.getvalue()


@pytest.mark.parametrize("public", [False, True])
def test_render_preferences_card_is_exact_png_with_stable_filename(public: bool) -> None:
    rendered = renderer.render_preferences_card(_payload(public=public))

    assert rendered.filename == "me_preferences_42.png"
    assert rendered.width == 1702
    assert rendered.height == 924
    with Image.open(BytesIO(rendered.image_bytes)) as image:
        assert image.format == "PNG"
        assert image.size == (1702, 924)
        assert image.mode == "RGB"


def test_render_preferences_card_places_circular_avatar_at_top_left() -> None:
    without_avatar = renderer.render_preferences_card(_payload())
    with_avatar = renderer.render_preferences_card(_payload(), avatar_bytes=_avatar_bytes())

    with Image.open(BytesIO(without_avatar.image_bytes)) as base_image:
        base_pixel = base_image.getpixel((109, 83))
    with Image.open(BytesIO(with_avatar.image_bytes)) as avatar_image:
        avatar_pixel = avatar_image.getpixel((109, 83))
    assert avatar_pixel != base_pixel
    assert avatar_pixel[0] > 150


def test_render_preferences_card_accepts_avatar_failure_and_long_unicode_text() -> None:
    payload = replace(
        _payload(),
        display_name="🛡️ 王国の統治者 — Très Long Governor Name " * 5,
        settings_insight="One or more saved profile details are unavailable and need review. " * 3,
    )

    rendered = renderer.render_preferences_card(payload, avatar_bytes=b"not an image")

    with Image.open(BytesIO(rendered.image_bytes)) as image:
        assert image.size == (1702, 924)


def test_render_preferences_card_rejects_wrong_sized_backdrop(tmp_path, monkeypatch) -> None:
    path = tmp_path / "wrong.png"
    Image.new("RGB", (100, 100), "black").save(path)
    monkeypatch.setattr(renderer, "BACKDROP_PATH", path)

    with pytest.raises(ValueError, match="1702x924"):
        renderer.render_preferences_card(_payload())


def test_render_preferences_card_rejects_non_opaque_backdrop(tmp_path, monkeypatch) -> None:
    path = tmp_path / "transparent.png"
    image = Image.new("RGBA", (1702, 924), (0, 0, 0, 255))
    image.putpixel((0, 0), (0, 0, 0, 0))
    image.save(path)
    image.close()
    monkeypatch.setattr(renderer, "BACKDROP_PATH", path)

    with pytest.raises(ValueError, match="fully opaque"):
        renderer.render_preferences_card(_payload())
