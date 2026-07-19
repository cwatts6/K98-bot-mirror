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


def _preference_row(
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    label: str,
    value: str,
    available: bool,
) -> None:
    _draw(draw, (112, y), label.upper(), font=_font(23, bold=True), fill=MUTED, bold=True)
    _draw_fit(
        draw,
        (420, y - 6),
        value,
        width=1150,
        size=36,
        min_size=22,
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
        _draw(draw, (112, 230), "REGIONAL PROFILE", font=_font(29, bold=True), fill=BLUE, bold=True)
        _preference_row(
            draw,
            y=292,
            label="Timezone",
            value=profile.timezone.friendly_label,
            available=profile.timezone.is_available,
        )
        _preference_row(
            draw,
            y=370,
            label="Location",
            value=profile.location.friendly_label,
            available=profile.location.is_available,
        )
        _preference_row(
            draw,
            y=448,
            label="Preferred language",
            value=profile.preferred_language.friendly_label,
            available=profile.preferred_language.is_available,
        )

        time_ref = payload.time_reference
        _draw(draw, (112, 535), time_ref.heading, font=_font(23, bold=True), fill=BLUE, bold=True)
        _draw(draw, (112, 574), time_ref.display_time, font=_font(56, bold=True), bold=True)
        _draw_fit(
            draw,
            (365, 579),
            time_ref.supporting_line,
            width=1213,
            size=29,
            min_size=19,
            fill=TEXT,
            bold=True,
        )
        if time_ref.regional_context:
            _draw_fit(
                draw,
                (365, 626),
                time_ref.regional_context,
                width=1213,
                size=21,
                min_size=15,
                fill=MUTED,
            )

        _draw(draw, (112, 672), "SETTINGS INSIGHT", font=_font(21, bold=True), fill=BLUE, bold=True)
        _draw_fit(
            draw, (112, 708), payload.settings_insight, width=1475, size=27, min_size=19, bold=True
        )

        _draw(draw, (112, 760), "MANAGE", font=_font(22, bold=True), fill=GREEN, bold=True)
        _draw_fit(
            draw,
            (112, 797),
            "Update your saved timezone, location, and preferred language.",
            width=1475,
            size=18,
            min_size=14,
            fill=MUTED,
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
