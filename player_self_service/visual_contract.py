"""Bounded visual primitives shared by the private player self-service cards."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from io import BytesIO
from typing import TypeAlias

from PIL import Image, ImageDraw, ImageOps

from core import visual_text

Colour: TypeAlias = tuple[int, int, int, int]
Box: TypeAlias = tuple[int, int, int, int]

TEXT: Colour = (248, 251, 255, 255)
MUTED: Colour = (190, 210, 235, 255)
BLUE: Colour = (91, 190, 255, 255)
GOLD: Colour = (255, 206, 92, 255)
GREEN: Colour = (76, 225, 148, 255)
AMBER: Colour = (255, 196, 78, 255)
RED: Colour = (255, 132, 132, 255)
SHADOW: Colour = (0, 0, 0, 190)
PANEL: Colour = (3, 11, 27, 220)
PANEL_EDGE: Colour = (91, 190, 255, 180)
PILL_FILL: Colour = (4, 11, 24, 220)

MISSING_VALUE = "—"
NOT_RECORDED = "Not recorded"
NO_DATA = "NO DATA"
UNAVAILABLE = "UNAVAILABLE"

TITLE_SIZE = 42
IDENTITY_SIZE = 31
SCOPE_SIZE = 27
CONTEXT_SIZE = 24
STATE_SIZE = 30
SECTION_SIZE = 22
METRIC_LABEL_SIZE = 20
PRIMARY_VALUE_SIZE = 50
SECONDARY_VALUE_SIZE = 43
BODY_SIZE = 18
SUPPORT_SIZE = 17
CHART_SIZE = 16
FOOTER_SIZE = 16
SOURCE_SIZE = 14

CORE_AVATAR_BOX: Box = (96, 60, 240, 204)
CORE_STATE_PILL_BOX: Box = (1370, 48, 1605, 111)

_STATE_COLOURS: dict[str, Colour] = {
    "READY": GREEN,
    "CURRENT": GREEN,
    "ACTIVE": GREEN,
    "LOCAL": GREEN,
    "SUCCESS": GREEN,
    "UTC": BLUE,
    "SELECTED": BLUE,
    "INFO": BLUE,
    "REVIEW": AMBER,
    "PARTIAL": AMBER,
    "STALE": AMBER,
    "SETUP": AMBER,
    NO_DATA: RED,
    UNAVAILABLE: RED,
    "FAILED": RED,
    "OFF": MUTED,
    "DISABLED": MUTED,
    "EXPIRED": MUTED,
}


def state_colour(state: str) -> Colour:
    """Return the locked semantic colour for a visible state label."""
    return _STATE_COLOURS.get(str(state).strip().upper(), MUTED)


def format_utc_datetime(value: datetime | None) -> str:
    """Format an aware timestamp using the player self-service UTC contract."""
    if value is None:
        return MISSING_VALUE
    if value.tzinfo is None:
        raise ValueError("visual timestamps must be timezone-aware")
    return value.astimezone(UTC).strftime("%d %b %Y, %H:%M UTC")


def format_compact_number(value: int | float | Decimal | None, *, signed: bool = False) -> str:
    """Format a number with the shared uppercase K/M/B and signed-delta rules."""
    if value is None:
        return MISSING_VALUE
    if isinstance(value, bool):
        numeric = Decimal(int(value))
    else:
        try:
            numeric = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return MISSING_VALUE
    sign = "+" if signed and numeric > 0 else ""
    magnitude = abs(numeric)
    for divisor, suffix in (
        (Decimal("1000000000"), "B"),
        (Decimal("1000000"), "M"),
        (Decimal("1000"), "K"),
    ):
        if magnitude >= divisor:
            scaled = (numeric / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            rendered = f"{scaled:.2f}".rstrip("0").rstrip(".")
            return f"{sign}{rendered}{suffix}"
    if numeric == numeric.to_integral_value():
        rendered = f"{int(numeric):,}"
    else:
        rendered = f"{numeric:,.1f}".rstrip("0").rstrip(".")
    return f"{sign}{rendered}"


def draw_panel(
    draw: ImageDraw.ImageDraw,
    box: Box,
    *,
    radius: int = 18,
    fill: Colour = PANEL,
    edge: Colour = PANEL_EDGE,
    width: int = 2,
) -> None:
    """Draw one bounded panel; callers retain all page geometry."""
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=edge, width=width)


def draw_state_pill(
    draw: ImageDraw.ImageDraw,
    state: str,
    *,
    box: Box = CORE_STATE_PILL_BOX,
    size: int = STATE_SIZE,
    min_size: int = 20,
) -> None:
    """Draw the common dark, outlined, text-labelled state capsule."""
    label = str(state).strip().upper()
    colour = state_colour(label)
    draw.rounded_rectangle(box, radius=26, fill=PILL_FILL, outline=colour, width=3)
    x1, y1, x2, y2 = box
    available_width = max(1, x2 - x1 - 24)
    font = visual_text.fit_font(
        draw,
        label,
        max_width=available_width,
        size=size,
        min_size=min_size,
        bold=True,
    )
    fitted = visual_text.fit_text_to_width(
        draw,
        label,
        width=available_width,
        base_font=font,
        bold=True,
    )
    text_width = visual_text.text_width(draw, fitted, font=font, bold=True)
    text_bbox = draw.textbbox((0, 0), fitted, font=font)
    text_height = text_bbox[3] - text_bbox[1]
    position = (x1 + (x2 - x1 - text_width) // 2, y1 + max(5, (y2 - y1 - text_height) // 2))
    visual_text.draw_text(
        draw,
        (position[0] + 2, position[1] + 2),
        fitted,
        font=font,
        fill=SHADOW,
        bold=True,
    )
    visual_text.draw_text(draw, position, fitted, font=font, fill=colour, bold=True)


def paste_core_avatar(
    canvas: Image.Image,
    avatar_bytes: bytes | None,
    *,
    box: Box = CORE_AVATAR_BOX,
    fallback_text: str = "KD98",
) -> bool:
    """Paste the invoking-user avatar or the common deterministic fallback."""
    x1, y1, x2, y2 = box
    size = min(x2 - x1, y2 - y1)
    avatar: Image.Image | None = None
    if avatar_bytes:
        try:
            with Image.open(BytesIO(avatar_bytes)) as source:
                avatar = ImageOps.fit(
                    ImageOps.exif_transpose(source).convert("RGBA"),
                    (size, size),
                    method=Image.Resampling.LANCZOS,
                )
        except Exception:
            avatar = None

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    actual_avatar = avatar is not None
    if avatar is None:
        avatar = Image.new("RGBA", (size, size), (5, 13, 30, 245))
        fallback_draw = ImageDraw.Draw(avatar, "RGBA")
        font = visual_text.fit_font(
            fallback_draw,
            fallback_text,
            max_width=size - 24,
            size=max(20, size // 4),
            min_size=16,
            bold=True,
        )
        text_width = visual_text.text_width(fallback_draw, fallback_text, font=font, bold=True)
        bbox = fallback_draw.textbbox((0, 0), fallback_text, font=font)
        visual_text.draw_text(
            fallback_draw,
            ((size - text_width) // 2, (size - (bbox[3] - bbox[1])) // 2 - bbox[1]),
            fallback_text,
            font=font,
            fill=GOLD,
            bold=True,
        )
    try:
        canvas.paste(avatar, (x1, y1), mask)
    finally:
        avatar.close()
        mask.close()
    ImageDraw.Draw(canvas, "RGBA").ellipse(
        (x1 - 2, y1 - 2, x1 + size + 1, y1 + size + 1),
        outline=(BLUE[0], BLUE[1], BLUE[2], 190),
        width=3,
    )
    return actual_avatar
