"""Deterministic Pillow renderer for the Phase 5D premium Reminders card."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core import visual_text
from player_self_service.reminders_summary import RemindersSummaryPayload

WIDTH = 1702
HEIGHT = 924
BACKDROP_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "me" / "cards" / "me_reminders.png"
)

TEXT = (242, 247, 255, 255)
MUTED = (177, 197, 222, 255)
BLUE = (91, 190, 255, 255)
GREEN = (76, 214, 143, 255)
GOLD = (255, 206, 92, 255)
RED = (255, 132, 132, 255)
SHADOW = (0, 0, 0, 190)
PANEL = (5, 10, 24, 96)
PANEL_EDGE = (94, 145, 210, 64)


@dataclass(frozen=True, slots=True)
class RenderedRemindersCard:
    filename: str
    image_bytes: BytesIO


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    return visual_text.font(size, bold=bold)


def _clean(value: object, *, fallback: str = "—") -> str:
    text = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())
    return text or fallback


def _fit(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    width: int,
    size: int,
    min_size: int,
    bold: bool = False,
) -> ImageFont.ImageFont:
    return visual_text.fit_font(
        draw,
        text,
        max_width=width,
        size=size,
        min_size=min_size,
        bold=bold,
    )


def _draw(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int, int] = TEXT,
    bold: bool = False,
) -> None:
    visual_text.draw_text(
        draw,
        (xy[0] + 2, xy[1] + 2),
        text,
        font=font,
        fill=SHADOW,
        bold=bold,
    )
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
    font = _fit(draw, cleaned, width=width, size=size, min_size=min_size, bold=bold)
    fitted = visual_text.fit_text_to_width(
        draw,
        cleaned,
        width=width,
        base_font=font,
        bold=bold,
    )
    _draw(draw, xy, fitted, font=font, fill=fill, bold=bold)


def _panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], *, radius: int = 22) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=PANEL, outline=PANEL_EDGE, width=2)


def _status_color(state: str) -> tuple[int, int, int, int]:
    return {"ACTIVE": GREEN, "REVIEW": GOLD, "OFF": MUTED}.get(state, BLUE)


def _status_badge(draw: ImageDraw.ImageDraw, text: str) -> None:
    x1, y1, x2, y2 = 1390, 62, 1608, 126
    color = _status_color(text)
    draw.rounded_rectangle(
        (x1, y1, x2, y2), radius=26, fill=(4, 11, 24, 205), outline=color, width=3
    )
    font = _font(32, bold=True)
    width = visual_text.text_width(draw, text, font=font, bold=True)
    _draw(draw, (x1 + (x2 - x1 - width) // 2, y1 + 10), text, font=font, fill=color, bold=True)


def _draw_system(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    width: int,
    title: str,
    state_line: str,
    events: str,
    times: str,
    coverage: str,
) -> None:
    _panel(draw, (x, 414, x + width, 650))
    _draw(draw, (x + 22, 430), title, font=_font(27, bold=True), fill=BLUE, bold=True)
    _draw_fit(
        draw,
        (x + 22, 468),
        state_line,
        width=width - 44,
        size=31,
        min_size=22,
        bold=True,
    )
    _draw_fit(
        draw,
        (x + 22, 511),
        events,
        width=width - 44,
        size=30,
        min_size=20,
        fill=TEXT,
    )
    _draw_fit(
        draw,
        (x + 22, 554),
        times,
        width=width - 44,
        size=29,
        min_size=19,
        fill=MUTED,
    )
    _draw_fit(
        draw,
        (x + 22, 600),
        coverage,
        width=width - 44,
        size=25,
        min_size=18,
        fill=GOLD,
        bold=True,
    )


def render_reminders_card(payload: RemindersSummaryPayload) -> RenderedRemindersCard:
    with Image.open(BACKDROP_PATH) as source:
        source.load()
        if source.size != (WIDTH, HEIGHT):
            raise ValueError(f"Reminders backdrop must be {WIDTH}x{HEIGHT}; got {source.size}")
        alpha = source.getchannel("A") if "A" in source.getbands() else None
        if alpha is not None and alpha.getextrema() != (255, 255):
            raise ValueError("Reminders backdrop must be fully opaque")
        canvas = source.convert("RGBA")

    draw = ImageDraw.Draw(canvas, "RGBA")
    state_text = payload.configuration_state.value

    _draw(draw, (94, 62), "REMINDER CENTRE", font=_font(42, bold=True), fill=MUTED, bold=True)
    _status_badge(draw, state_text)

    identity = f"{_clean(payload.display_name, fallback='player')} ({payload.kingdom_id})"
    _draw_fit(
        draw,
        (94, 125),
        identity,
        width=930,
        size=49,
        min_size=28,
        bold=True,
    )
    _draw_fit(
        draw,
        (1070, 151),
        payload.state_supporting_text,
        width=538,
        size=28,
        min_size=19,
        fill=_status_color(state_text),
        bold=True,
    )

    _panel(draw, (92, 226, 1610, 382), radius=24)
    _draw(draw, (116, 241), payload.hero.headline, font=_font(27, bold=True), fill=BLUE, bold=True)
    _draw_fit(
        draw,
        (116, 283),
        payload.hero.primary_line,
        width=1470,
        size=42,
        min_size=25,
        bold=True,
    )
    if payload.hero.secondary_line:
        _draw_fit(
            draw,
            (116, 337),
            payload.hero.secondary_line,
            width=1470,
            size=27,
            min_size=19,
            fill=MUTED,
        )

    _draw_system(
        draw,
        x=92,
        width=748,
        title="KVK REMINDERS",
        state_line=payload.kvk.state_count_line,
        events=payload.kvk.event_summary,
        times=payload.kvk.time_summary,
        coverage=payload.kvk.coverage_label,
    )
    _draw_system(
        draw,
        x=862,
        width=748,
        title="CALENDAR REMINDERS",
        state_line=payload.calendar.state_count_line,
        events=payload.calendar.event_summary,
        times=payload.calendar.time_summary,
        coverage=payload.calendar.coverage_label,
    )

    _panel(draw, (92, 664, 1610, 752), radius=20)
    _draw(draw, (116, 676), "REMINDER INSIGHT", font=_font(23, bold=True), fill=BLUE, bold=True)
    _draw_fit(
        draw,
        (116, 710),
        payload.insight,
        width=1470,
        size=28,
        min_size=19,
        bold=True,
    )

    _panel(draw, (92, 766, 1610, 848), radius=20)
    _draw(draw, (116, 778), "Manage reminders", font=_font(28, bold=True), fill=GOLD, bold=True)
    _draw_fit(
        draw,
        (116, 814),
        "Choose KVK and calendar events and when each alert is sent.",
        width=1470,
        size=24,
        min_size=18,
        fill=MUTED,
    )

    footer = f"Refreshed {payload.generated_at_utc:%H:%M UTC} • Schedule times shown in UTC"
    _draw_fit(
        draw,
        (96, 872),
        footer,
        width=1510,
        size=23,
        min_size=18,
        fill=MUTED,
    )

    output = BytesIO()
    canvas.convert("RGB").save(output, format="PNG", optimize=True)
    output.seek(0)
    return RenderedRemindersCard(
        filename=f"me_reminders_{payload.viewer_discord_id}.png",
        image_bytes=output,
    )
