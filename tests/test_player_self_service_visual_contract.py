from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO

from PIL import Image, ImageDraw
import pytest

from core import visual_contract as contract


def test_locked_colours_and_missing_labels_match_phase7_contract() -> None:
    assert contract.TEXT == (248, 251, 255, 255)
    assert contract.MUTED == (190, 210, 235, 255)
    assert contract.BLUE == (91, 190, 255, 255)
    assert contract.GOLD == (255, 206, 92, 255)
    assert contract.GREEN == (76, 225, 148, 255)
    assert contract.AMBER == (255, 196, 78, 255)
    assert contract.RED == (255, 132, 132, 255)
    assert contract.SHADOW == (0, 0, 0, 190)
    assert contract.PANEL == (3, 11, 27, 220)
    assert contract.PANEL_EDGE == (91, 190, 255, 180)
    assert contract.MISSING_VALUE == "—"
    assert contract.NOT_RECORDED == "Not recorded"
    assert contract.NO_DATA == "NO DATA"
    assert contract.UNAVAILABLE == "UNAVAILABLE"


@pytest.mark.parametrize(
    ("state", "expected"),
    (
        ("READY", contract.GREEN),
        ("CURRENT", contract.GREEN),
        ("ACTIVE", contract.GREEN),
        ("LOCAL", contract.GREEN),
        ("UTC", contract.BLUE),
        ("REVIEW", contract.AMBER),
        ("PARTIAL", contract.AMBER),
        ("STALE", contract.AMBER),
        ("SETUP", contract.AMBER),
        ("NO DATA", contract.RED),
        ("UNAVAILABLE", contract.RED),
        ("OFF", contract.MUTED),
        ("EXPIRED", contract.MUTED),
        ("unknown", contract.MUTED),
    ),
)
def test_state_semantics_are_text_stable_and_case_insensitive(state, expected) -> None:
    assert contract.state_colour(state.lower()) == expected


def test_utc_datetime_uses_standard_phase7_copy() -> None:
    value = datetime(2026, 7, 18, 15, 5, tzinfo=UTC)
    assert contract.format_utc_datetime(value) == "18 Jul 2026, 15:05 UTC"
    assert contract.format_utc_datetime(None) == "—"
    with pytest.raises(ValueError, match="timezone-aware"):
        contract.format_utc_datetime(datetime(2026, 7, 18, 15, 5))


@pytest.mark.parametrize(
    ("value", "signed", "expected"),
    (
        (None, False, "—"),
        (0, True, "0"),
        (999, False, "999"),
        (1_000, False, "1K"),
        (1_250_000, False, "1.25M"),
        (1_000_000_000, False, "1B"),
        (12_345, True, "+12.35K"),
        (-12_345, True, "-12.35K"),
        (Decimal("12.5"), False, "12.5"),
    ),
)
def test_compact_numbers_preserve_zero_sign_and_uppercase_units(value, signed, expected) -> None:
    assert contract.format_compact_number(value, signed=signed) == expected


def test_panel_and_state_pill_use_bounded_geometry() -> None:
    image = Image.new("RGBA", (420, 180), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    contract.draw_panel(draw, (10, 10, 200, 120))
    contract.draw_state_pill(draw, "UTC", box=(220, 20, 400, 90))
    assert image.getpixel((10, 50)) == contract.PANEL_EDGE
    assert image.getpixel((220, 55))[:3] == contract.BLUE[:3]
    image.close()


@pytest.mark.parametrize("state", ["READY", "PARTIAL", "UTC", "OFF"])
def test_state_pill_text_is_vertically_centred(state: str) -> None:
    box = (20, 20, 255, 83)
    image = Image.new("RGBA", (280, 110), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")

    contract.draw_state_pill(draw, state, box=box)

    colour = contract.state_colour(state)[:3]
    text_pixels = [
        (x, y)
        for y in range(box[1] + 8, box[3] - 8)
        for x in range(box[0] + 8, box[2] - 8)
        if image.getpixel((x, y))[:3] == colour
    ]
    assert text_pixels
    visible_midpoint = (min(y for _x, y in text_pixels) + max(y for _x, y in text_pixels)) / 2
    pill_midpoint = (box[1] + box[3]) / 2
    assert abs(visible_midpoint - pill_midpoint) <= 1.5
    image.close()


def test_core_avatar_draws_real_avatar_or_deterministic_fallback() -> None:
    avatar_stream = BytesIO()
    with Image.new("RGB", (256, 256), (220, 20, 60)) as avatar:
        avatar.save(avatar_stream, format="PNG")

    with Image.new("RGBA", (300, 260), (0, 0, 0, 0)) as real_canvas:
        assert contract.paste_core_avatar(real_canvas, avatar_stream.getvalue()) is True
        assert real_canvas.getpixel((150, 120))[0] > 180

    with Image.new("RGBA", (300, 260), (0, 0, 0, 0)) as fallback_canvas:
        assert contract.paste_core_avatar(fallback_canvas, b"not an image") is False
        assert fallback_canvas.getpixel((168, 132))[3] > 0
