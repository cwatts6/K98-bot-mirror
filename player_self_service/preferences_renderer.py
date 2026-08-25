"""Deterministic Pillow renderer for the profile-only Personal Settings card."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core import visual_contract, visual_text
from player_self_service.accounts_renderer import format_discord_heading
from player_self_service.preferences_summary import PreferencesSummaryPayload

WIDTH = 1702
HEIGHT = 924
BACKDROP_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "me" / "cards" / "me_preferences.png"
)

TEXT = visual_contract.TEXT
MUTED = visual_contract.MUTED
BLUE = visual_contract.BLUE
GREEN = visual_contract.GREEN
AMBER = visual_contract.AMBER
SHADOW = visual_contract.SHADOW


@dataclass(frozen=True, slots=True)
class RenderedPreferencesCard:
    filename: str
    image_bytes: bytes
    width: int = WIDTH
    height: int = HEIGHT


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    return visual_text.font(size, bold=bold)


def _clean(value: object, *, fallback: str = "—") -> str:
    text = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())
    return text or fallback


def _draw(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int, int] = TEXT,
    bold: bool = False,
) -> None:
    visual_text.draw_text(draw, (xy[0] + 2, xy[1] + 2), text, font=font, fill=SHADOW, bold=bold)
    visual_text.draw_text(draw, xy, text, font=font, fill=fill, bold=bold)


def _draw_fit(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    width: int,
    size: int,
    min_size: int,
    fill: tuple[int, int, int, int] = TEXT,
    bold: bool = False,
) -> None:
    cleaned = _clean(text)
    font = visual_text.fit_font(
        draw, cleaned, max_width=width, size=size, min_size=min_size, bold=bold
    )
    fitted = visual_text.fit_text_to_width(draw, cleaned, width=width, base_font=font, bold=bold)
    _draw(draw, xy, fitted, font=font, fill=fill, bold=bold)


def _draw_fit_right(
    draw: ImageDraw.ImageDraw,
    *,
    right: int,
    y: int,
    text: str,
    width: int,
    size: int,
    min_size: int,
    fill: tuple[int, int, int, int] = TEXT,
    bold: bool = False,
) -> None:
    cleaned = _clean(text)
    font = visual_text.fit_font(
        draw, cleaned, max_width=width, size=size, min_size=min_size, bold=bold
    )
    fitted = visual_text.fit_text_to_width(draw, cleaned, width=width, base_font=font, bold=bold)
    fitted_width = visual_text.text_width(draw, fitted, font=font, bold=bold)
    _draw(draw, (right - fitted_width, y), fitted, font=font, fill=fill, bold=bold)


def _status_badge(draw: ImageDraw.ImageDraw, state: str) -> None:
    visual_contract.draw_state_pill(draw, state)


def _panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    radius: int = 18,
) -> None:
    visual_contract.draw_panel(draw, box, radius=radius)


def _wrapped_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    width: int,
    size: int,
    min_size: int,
    max_lines: int,
    bold: bool = False,
) -> tuple[ImageFont.ImageFont, tuple[str, ...]]:
    cleaned = _clean(text)
    words = cleaned.split()
    for candidate_size in range(size, min_size - 1, -1):
        font = visual_text.font_for_text(cleaned, candidate_size, bold=bold)
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if (
                not current
                or visual_text.text_width(draw, candidate, font=font, bold=bold) <= width
            ):
                current = candidate
                continue
            lines.append(current)
            current = word
        if current:
            lines.append(current)
        if len(lines) <= max_lines and all(
            visual_text.text_width(draw, line, font=font, bold=bold) <= width for line in lines
        ):
            return font, tuple(lines)

    font = visual_text.font_for_text(cleaned, min_size, bold=bold)
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(lines) < max_lines - 1 and (
            not current or visual_text.text_width(draw, candidate, font=font, bold=bold) <= width
        ):
            current = candidate
            continue
        if len(lines) < max_lines - 1:
            lines.append(current)
            current = word
            continue
        current = f"{current} {word}".strip()
    if current:
        lines.append(
            visual_text.fit_text_to_width(
                draw,
                current,
                width=width,
                base_font=font,
                bold=bold,
            )
        )
    return font, tuple(lines[:max_lines])


def _draw_wrapped_fit(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    width: int,
    size: int,
    min_size: int,
    max_lines: int,
    line_gap: int,
    fill: tuple[int, int, int, int] = TEXT,
    bold: bool = False,
) -> None:
    font, lines = _wrapped_lines(
        draw,
        text,
        width=width,
        size=size,
        min_size=min_size,
        max_lines=max_lines,
        bold=bold,
    )
    for index, line in enumerate(lines):
        _draw(draw, (xy[0], xy[1] + index * line_gap), line, font=font, fill=fill, bold=bold)


def _preference_card(
    draw: ImageDraw.ImageDraw,
    *,
    box: tuple[int, int, int, int],
    label: str,
    value: str,
    available: bool,
) -> None:
    _panel(draw, box)
    x0, y0, x1, _ = box
    _draw(
        draw,
        (x0 + 20, y0 + 18),
        label.upper(),
        font=_font(20, bold=True),
        fill=BLUE,
        bold=True,
    )
    _draw_fit(
        draw,
        (x0 + 20, y0 + 67),
        value,
        width=x1 - x0 - 40,
        size=36,
        min_size=20,
        fill=TEXT if available else AMBER,
        bold=True,
    )


def render_preferences_card(
    payload: PreferencesSummaryPayload,
    *,
    avatar_bytes: bytes | None = None,
) -> RenderedPreferencesCard:
    with Image.open(BACKDROP_PATH) as source:
        source.load()
        if source.size != (WIDTH, HEIGHT):
            raise ValueError(f"Preferences backdrop must be {WIDTH}x{HEIGHT}; got {source.size}")
        alpha = source.getchannel("A") if "A" in source.getbands() else None
        if alpha is not None and alpha.getextrema() != (255, 255):
            raise ValueError("Preferences backdrop must be fully opaque")
        canvas = source.convert("RGBA")

    try:
        visual_contract.paste_core_avatar(canvas, avatar_bytes)
        draw = ImageDraw.Draw(canvas, "RGBA")

        _draw(
            draw,
            (270, 48),
            "PERSONAL SETTINGS",
            font=_font(42, bold=True),
            fill=TEXT,
            bold=True,
        )
        _draw_fit(
            draw,
            (270, 103),
            format_discord_heading(payload.display_name, kingdom_id=payload.kingdom_id),
            width=730,
            size=31,
            min_size=20,
            fill=visual_contract.GOLD,
            bold=True,
        )
        _draw_fit(
            draw,
            (270, 149),
            f"Kingdom {payload.kingdom_id} • Regional profile",
            width=730,
            size=27,
            min_size=18,
            bold=True,
        )
        _status_badge(draw, "LOCAL" if payload.time_reference.mode == "LOCAL" else "UTC")
        _draw_fit_right(
            draw,
            right=1605,
            y=127,
            text=payload.profile_supporting_text,
            width=595,
            size=24,
            min_size=17,
            fill=MUTED,
        )

        profile = payload.regional_profile
        _draw(draw, (95, 230), "REGIONAL PROFILE", font=_font(29, bold=True), fill=BLUE, bold=True)
        _preference_card(
            draw,
            box=(95, 276, 578, 455),
            label="Timezone",
            value=profile.timezone.friendly_label,
            available=profile.timezone.is_available,
        )
        _preference_card(
            draw,
            box=(608, 276, 1091, 455),
            label="Location",
            value=profile.location.friendly_label,
            available=profile.location.is_available,
        )
        _preference_card(
            draw,
            box=(1121, 276, 1605, 455),
            label="Preferred language",
            value=profile.preferred_language.friendly_label,
            available=profile.preferred_language.is_available,
        )

        time_ref = payload.time_reference
        _panel(draw, (95, 485, 980, 705))
        _draw(draw, (119, 503), time_ref.heading, font=_font(21, bold=True), fill=BLUE, bold=True)
        _draw(draw, (119, 548), time_ref.display_time, font=_font(60, bold=True), bold=True)
        _draw_fit(
            draw,
            (340, 555),
            time_ref.supporting_line,
            width=616,
            size=29,
            min_size=17,
            fill=TEXT,
            bold=True,
        )
        if time_ref.regional_context:
            _draw_fit(
                draw,
                (340, 605),
                time_ref.regional_context,
                width=616,
                size=21,
                min_size=14,
                fill=MUTED,
            )

        _panel(draw, (1010, 485, 1605, 705))
        _draw(
            draw,
            (1034, 503),
            "SETTINGS INSIGHT",
            font=_font(21, bold=True),
            fill=BLUE,
            bold=True,
        )
        _draw_wrapped_fit(
            draw,
            (1034, 552),
            payload.settings_insight,
            width=547,
            size=27,
            min_size=18,
            max_lines=4,
            line_gap=34,
            bold=True,
        )

        _panel(draw, (95, 722, 1605, 803))
        _draw(draw, (119, 738), "MANAGE", font=_font(18, bold=True), fill=GREEN, bold=True)
        _draw_fit(
            draw,
            (285, 734),
            "Update your saved timezone, location, and preferred language.",
            width=1296,
            size=20,
            min_size=14,
            fill=TEXT,
        )

        footer_context = (
            "Local time uses your saved timezone; reminder scheduling remains in UTC."
            if time_ref.mode == "LOCAL"
            else "Set a timezone for local context; reminder scheduling remains in UTC."
        )
        _draw_fit(draw, (95, 845), footer_context, width=930, size=16, min_size=12, fill=MUTED)
        refreshed = f"Generated {visual_contract.format_utc_datetime(payload.generated_at_utc)}"
        font = visual_text.fit_font(
            draw, refreshed, max_width=520, size=16, min_size=12, bold=False
        )
        width = visual_text.text_width(draw, refreshed, font=font)
        _draw(draw, (1605 - width, 845), refreshed, font=font, fill=MUTED)

        stream = BytesIO()
        try:
            canvas.convert("RGB").save(stream, format="PNG", optimize=True)
            image_bytes = stream.getvalue()
        finally:
            stream.close()
        return RenderedPreferencesCard(
            filename=f"me_preferences_{payload.discord_user_id}.png",
            image_bytes=image_bytes,
        )
    finally:
        canvas.close()
