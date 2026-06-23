"""Generated dashboard card renderer for the /me command centre."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from player_self_service.service import PlayerSelfServiceSummary
from prekvk import report_image_renderer as text_renderer

WIDTH = 1180
HEIGHT = 640

BG = (11, 18, 31)
PANEL = (22, 33, 52)
PANEL_ALT = (28, 43, 68)
TEXT = (246, 250, 255)
MUTED = (172, 188, 207)
SOFT = (105, 123, 148)
GREEN = (74, 222, 128)
BLUE = (96, 165, 250)
GOLD = (250, 204, 21)
RED = (248, 113, 113)
TEAL = (45, 212, 191)
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


def _badge(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    fill: tuple[int, int, int],
) -> None:
    x, y = xy
    font = _font(19, bold=True)
    width = _text_width(draw, text, font) + 28
    draw.rounded_rectangle((x, y, x + width, y + 34), radius=17, fill=fill + (70,))
    _draw_text(draw, (x + 14, y + 7), text, fill=fill, font=font, bold=True)


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
        draw, (x + 24, y + 22), title.upper(), fill=MUTED, font=_font(21, bold=True), bold=True
    )
    _badge(draw, (x + w - 150, y + 18), status, fill=status_color)

    cursor_y = y + 74
    for line in lines:
        clean = _clean(line, fallback="-")
        font = _fit(draw, clean, width=w - 48, size=26, min_size=17, bold=True)
        _draw_text(draw, (x + 24, cursor_y), clean, fill=TEXT, font=font, bold=True)
        cursor_y += 40

    draw.line((x + 24, y + h - 58, x + w - 24, y + h - 58), fill=LINE, width=1)
    action_text = f"Next: {action}"
    action_font = _fit(draw, action_text, width=w - 48, size=21, min_size=15, bold=True)
    _draw_text(draw, (x + 24, y + h - 40), action_text, fill=BLUE, font=action_font, bold=True)


def render_dashboard_card(
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
    generated_at_utc: datetime | None = None,
) -> RenderedDashboardCard:
    generated_at_utc = generated_at_utc or datetime.now(UTC)
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), BG + (255,))
    draw = ImageDraw.Draw(canvas, "RGBA")

    draw.rectangle((0, 0, WIDTH, 150), fill=(18, 31, 52, 255))
    draw.rectangle((0, 145, WIDTH, 150), fill=BLUE + (255,))
    _draw_text(draw, (48, 36), "K98 Personal Command Centre", font=_font(43, bold=True), bold=True)
    name = _clean(display_name, fallback="player")
    name_font = _fit(draw, name, width=620, size=30, min_size=18, bold=True)
    _draw_text(draw, (50, 92), name, fill=MUTED, font=name_font, bold=True)
    updated = generated_at_utc.strftime("%Y-%m-%d %H:%M UTC")
    updated_text = f"Private dashboard | {updated}"
    updated_font = _fit(draw, updated_text, width=430, size=21, min_size=15)
    _draw_text(draw, (WIDTH - 470, 92), updated_text, fill=MUTED, font=updated_font)

    accounts = summary.accounts
    reminders = summary.reminders
    preferences = summary.preferences
    exports = summary.exports

    _section(
        draw,
        x=44,
        y=190,
        w=340,
        h=270,
        title="Accounts",
        status=accounts.main_state,
        status_color=_status_color(accounts.main_state),
        lines=(
            f"Main: {accounts.main_label}",
            f"Linked: {accounts.linked_label}",
            f"Accounts: {accounts.linked_count}",
        ),
        action=accounts.next_action,
    )
    _section(
        draw,
        x=420,
        y=190,
        w=340,
        h=270,
        title="Reminders",
        status=reminders.state,
        status_color=_status_color(reminders.state),
        lines=(
            f"KVK: {reminders.event_summary}",
            f"Times: {reminders.time_summary}",
            "DMs: best effort",
        ),
        action=reminders.next_action,
    )
    _section(
        draw,
        x=796,
        y=190,
        w=340,
        h=270,
        title="Preferences",
        status=preferences.inventory_visibility,
        status_color=_status_color(preferences.inventory_visibility),
        lines=(
            f"Inventory: {preferences.inventory_visibility}",
            f"Exports: {exports.stats_export}",
            exports.privacy_note,
        ),
        action=preferences.next_action,
    )

    draw.rounded_rectangle((44, 500, 1136, 586), radius=18, fill=PANEL_ALT, outline=LINE, width=2)
    _draw_text(draw, (72, 526), "Quick Launch", fill=MUTED, font=_font(21, bold=True), bold=True)
    quick = "KVK stats | targets | history | rankings | inventory | exports"
    quick_font = _fit(draw, quick, width=760, size=25, min_size=16, bold=True)
    _draw_text(draw, (254, 524), quick, fill=TEXT, font=quick_font, bold=True)
    _draw_text(
        draw,
        (72, 560),
        "Use the dashboard menu below. Existing channel and visibility rules still apply.",
        fill=SOFT,
        font=_font(18),
    )

    output = BytesIO()
    canvas.convert("RGB").save(output, format="PNG", optimize=True)
    output.seek(0)
    return RenderedDashboardCard(
        filename=f"me_dashboard_{summary.discord_user_id}.png",
        image_bytes=output,
    )
