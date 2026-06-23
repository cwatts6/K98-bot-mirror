"""Generated dashboard card renderer for the /me command centre."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from player_self_service.service import PlayerSelfServiceSummary
from prekvk import report_image_renderer as text_renderer

WIDTH = 900
HEIGHT = 1020

BG = (11, 18, 31)
PANEL = (22, 33, 52)
TEXT = (246, 250, 255)
MUTED = (172, 188, 207)
GREEN = (74, 222, 128)
BLUE = (96, 165, 250)
GOLD = (250, 204, 21)
RED = (248, 113, 113)
LINE = (61, 82, 112)


@dataclass(frozen=True, slots=True)
class RenderedDashboardCard:
    filename: str
    image_bytes: BytesIO


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    return text_renderer._font(size, bold=bold)


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    return text_renderer._text_width(draw, text, font=font)


def _fit(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    width: int,
    size: int,
    min_size: int = 16,
    bold: bool = False,
) -> ImageFont.ImageFont:
    font = text_renderer._font_for_text(text, size, bold=bold)
    while size > min_size and _text_width(draw, text, font) > width:
        size -= 1
        font = text_renderer._font_for_text(text, size, bold=bold)
    return font


def _clean(value: object, *, fallback: str = "Unknown") -> str:
    text = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())
    return text or fallback


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    fill: tuple[int, int, int] = TEXT,
    font: ImageFont.ImageFont | None = None,
    bold: bool = False,
) -> None:
    font = font or _font(20, bold=bold)
    text_renderer._draw_text(draw, xy, text, fill=fill, font=font, bold=bold)


def _panel(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle(xy, radius=18, fill=PANEL, outline=LINE, width=2)


def _status_color(value: str) -> tuple[int, int, int]:
    normalized = value.strip().lower()
    if normalized in {"set", "on", "single", "multiple", "private", "public"}:
        return GREEN
    if normalized in {"not set", "none", "off", "not subscribed"}:
        return GOLD
    if normalized == "unknown":
        return RED
    return BLUE


def _status_label(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"set", "single", "multiple"}:
        return "READY"
    if normalized == "on":
        return "ON"
    if normalized == "public":
        return "PUBLIC"
    if normalized == "private":
        return "PRIVATE"
    if normalized in {"not set", "none"}:
        return "SETUP"
    if normalized in {"off", "not subscribed"}:
        return "OFF"
    if normalized == "unknown":
        return "CHECK"
    return _clean(value, fallback="STATUS").upper()


def _linked_display(value: str) -> str:
    normalized = value.strip().lower()
    if normalized.endswith(" linked"):
        normalized = normalized.removesuffix(" linked")
    return _clean(normalized, fallback="unknown")


def _account_lines(summary: PlayerSelfServiceSummary) -> tuple[str, ...]:
    accounts = summary.accounts
    return (
        f"Main: {accounts.main_label}",
        f"Linked: {_linked_display(accounts.linked_label)}",
        f"Accounts: {accounts.linked_count}",
    )


def _reminder_lines(summary: PlayerSelfServiceSummary) -> tuple[str, ...]:
    reminders = summary.reminders
    return (
        f"KVK: {reminders.event_summary}",
        f"Times: {reminders.time_summary}",
    )


def _preference_lines(summary: PlayerSelfServiceSummary) -> tuple[str, ...]:
    preferences = summary.preferences
    return (
        f"Inventory: {preferences.inventory_visibility}",
        "Exports: private",
    )


def _badge(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    fill: tuple[int, int, int],
) -> None:
    x, y = xy
    width = 150
    label = _status_label(text)
    font = _fit(draw, label, width=width - 32, size=22, min_size=15, bold=True)
    text_width = _text_width(draw, label, font)
    draw.rounded_rectangle((x, y, x + width, y + 40), radius=20, fill=fill + (70,))
    _draw_text(
        draw,
        (x + (width - text_width) // 2, y + 8),
        label,
        fill=TEXT,
        font=font,
        bold=True,
    )


def _section(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    status: str,
    status_color: tuple[int, int, int],
    lines: tuple[str, ...],
    action: str,
) -> None:
    _panel(draw, (x, y, x + w, y + h))
    _draw_text(
        draw, (x + 24, y + 24), title.upper(), fill=MUTED, font=_font(25, bold=True), bold=True
    )
    _badge(draw, (x + w - 188, y + 18), status, fill=status_color)

    cursor_y = y + 82
    for line in lines:
        clean = _clean(line, fallback="-")
        font = _fit(draw, clean, width=w - 48, size=34, min_size=22, bold=True)
        _draw_text(draw, (x + 24, cursor_y), clean, fill=TEXT, font=font, bold=True)
        cursor_y += 44

    draw.line((x + 24, y + h - 56, x + w - 24, y + h - 56), fill=LINE, width=1)
    action_text = f"Next: {action}"
    action_font = _fit(draw, action_text, width=w - 48, size=28, min_size=18, bold=True)
    _draw_text(draw, (x + 24, y + h - 38), action_text, fill=BLUE, font=action_font, bold=True)


def render_dashboard_card(
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
    generated_at_utc: datetime | None = None,
) -> RenderedDashboardCard:
    generated_at_utc = generated_at_utc or datetime.now(UTC)
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), BG + (255,))
    draw = ImageDraw.Draw(canvas, "RGBA")

    draw.rectangle((0, 0, WIDTH, 140), fill=(18, 31, 52, 255))
    draw.rectangle((0, 135, WIDTH, 140), fill=BLUE + (255,))
    _draw_text(draw, (36, 32), "K98 Personal Command Centre", font=_font(38, bold=True), bold=True)
    name = _clean(display_name, fallback="player")
    name_font = _fit(draw, name, width=470, size=28, min_size=18, bold=True)
    _draw_text(draw, (38, 86), name, fill=MUTED, font=name_font, bold=True)
    updated = generated_at_utc.strftime("%Y-%m-%d %H:%M UTC")
    updated_text = updated
    updated_font = _fit(draw, updated_text, width=340, size=22, min_size=15)
    _draw_text(draw, (WIDTH - 360, 88), updated_text, fill=MUTED, font=updated_font)

    accounts = summary.accounts
    reminders = summary.reminders
    preferences = summary.preferences

    _section(
        draw,
        x=40,
        y=145,
        w=820,
        h=275,
        title="Accounts",
        status=accounts.main_state,
        status_color=_status_color(accounts.main_state),
        lines=_account_lines(summary),
        action=accounts.next_action,
    )
    _section(
        draw,
        x=40,
        y=435,
        w=820,
        h=275,
        title="Reminders",
        status=reminders.state,
        status_color=_status_color(reminders.state),
        lines=_reminder_lines(summary),
        action=reminders.next_action,
    )
    _section(
        draw,
        x=40,
        y=725,
        w=820,
        h=275,
        title="Preferences",
        status=preferences.inventory_visibility,
        status_color=_status_color(preferences.inventory_visibility),
        lines=_preference_lines(summary),
        action=preferences.next_action,
    )
    output = BytesIO()
    canvas.convert("RGB").save(output, format="PNG", optimize=True)
    output.seek(0)
    return RenderedDashboardCard(
        filename=f"me_dashboard_{summary.discord_user_id}.png",
        image_bytes=output,
    )
