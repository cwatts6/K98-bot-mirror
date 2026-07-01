from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core import visual_text
from voting.models import RenderedVoteCard, VoteSnapshot

ROOT = Path(__file__).resolve().parents[1]
VOTING_BACKGROUND = ROOT / "assets" / "voting" / "vote_background.png"
FALLBACK_BACKGROUND = ROOT / "assets" / "kvk" / "cards" / "Default_card.jpg"
WIDTH = 1180
HEIGHT = 640
TEXT = (255, 255, 255)
MUTED = (209, 213, 219)
PANEL = (12, 18, 28, 176)
GOLD = (255, 211, 87)
GREEN = (52, 211, 153)
BLUE = (96, 165, 250)
RED = (248, 113, 113)


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    return visual_text.font(size, bold=bold)


def _text_width(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, *, bold: bool = False
) -> int:
    return visual_text.text_width(draw, text, font=font, bold=bold)


def _fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    max_width: int,
    size: int,
    min_size: int,
    bold: bool = False,
) -> ImageFont.ImageFont:
    current = size
    font = visual_text.font_for_text(text, current, bold=bold)
    while current > min_size and _text_width(draw, text, font, bold=bold) > max_width:
        current -= 1
        font = visual_text.font_for_text(text, current, bold=bold)
    return font


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    fill=TEXT,
    font: ImageFont.ImageFont | None = None,
    bold: bool = False,
) -> None:
    visual_text.draw_text(draw, xy, text, fill=fill, font=font or _font(20, bold=bold), bold=bold)


def _load_background() -> Image.Image:
    for path in (VOTING_BACKGROUND, FALLBACK_BACKGROUND):
        if path.exists():
            return (
                Image.open(path).convert("RGBA").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
            )
    return Image.new("RGBA", (WIDTH, HEIGHT), (13, 20, 33, 255))


def _status(snapshot: VoteSnapshot, now_utc: datetime) -> tuple[str, tuple[int, int, int]]:
    if snapshot.status == "Closed" or snapshot.closed_at_utc is not None:
        return "Closed", RED
    minutes_left = (snapshot.closes_at_utc - now_utc).total_seconds() / 60
    if minutes_left <= 60:
        return "Closing Soon", GOLD
    return "Open", GREEN


def _compact_count(value: int) -> str:
    return f"{int(value):,}"


def _fmt_dt(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")


def _pct(count: int, total: int) -> str:
    if total <= 0:
        return "0%"
    value = (count / total) * 100
    return f"{value:.1f}".rstrip("0").rstrip(".") + "%"


def render_vote_card(
    snapshot: VoteSnapshot, *, now_utc: datetime | None = None
) -> RenderedVoteCard:
    now = now_utc or datetime.now(UTC)
    background = _load_background()
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay, "RGBA")
    odraw.rectangle((0, 0, WIDTH, 180), fill=(0, 0, 0, 100))
    odraw.rectangle((0, 520, WIDTH, HEIGHT), fill=(0, 0, 0, 95))
    odraw.rounded_rectangle((34, 205, WIDTH - 34, 508), radius=16, fill=PANEL)
    canvas = Image.alpha_composite(background, overlay)
    draw = ImageDraw.Draw(canvas, "RGBA")

    title_font = _fit_font(draw, snapshot.title, max_width=860, size=42, min_size=25, bold=True)
    _draw_text(draw, (46, 42), snapshot.title, fill=TEXT, font=title_font, bold=True)
    if snapshot.description:
        desc = snapshot.description.replace("\n", " ")
        desc_font = _fit_font(draw, desc, max_width=890, size=22, min_size=16)
        _draw_text(draw, (48, 100), desc, fill=MUTED, font=desc_font)

    status, color = _status(snapshot, now)
    draw.rounded_rectangle((940, 48, 1118, 90), radius=19, fill=(*color, 210))
    status_font = _fit_font(draw, status.upper(), max_width=145, size=22, min_size=16, bold=True)
    status_x = 1029 - (_text_width(draw, status.upper(), status_font, bold=True) // 2)
    _draw_text(draw, (status_x, 58), status.upper(), fill=(15, 23, 42), font=status_font, bold=True)

    deadline = f"Closes: {_fmt_dt(snapshot.closes_at_utc)}"
    _draw_text(draw, (48, 145), deadline, fill=GOLD, font=_font(22, bold=True), bold=True)

    total = snapshot.total_votes
    row_top = 230
    row_gap = 52
    bar_x = 390
    bar_w = 520
    for index, option in enumerate(snapshot.options[:5]):
        y = row_top + (index * row_gap)
        label_font = _fit_font(draw, option.label, max_width=290, size=24, min_size=16, bold=True)
        _draw_text(draw, (62, y), option.label, fill=TEXT, font=label_font, bold=True)
        draw.rounded_rectangle(
            (bar_x, y + 8, bar_x + bar_w, y + 28), radius=10, fill=(51, 65, 85, 230)
        )
        fill_w = int(bar_w * option.vote_count / total) if total else 0
        if fill_w:
            draw.rounded_rectangle((bar_x, y + 8, bar_x + fill_w, y + 28), radius=10, fill=BLUE)
        stat = f"{_compact_count(option.vote_count)} votes  |  {_pct(option.vote_count, total)}"
        stat_font = _fit_font(draw, stat, max_width=180, size=21, min_size=15, bold=True)
        _draw_text(draw, (936, y), stat, fill=MUTED, font=stat_font, bold=True)

    footer = f"Total voters: {_compact_count(total)}    Last updated: {_fmt_dt(now)}    Vote #{snapshot.vote_post_id}"
    footer_font = _fit_font(draw, footer, max_width=1000, size=22, min_size=16, bold=True)
    _draw_text(draw, (48, 560), footer, fill=MUTED, font=footer_font, bold=True)

    buf = BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return RenderedVoteCard(filename=f"vote_{snapshot.vote_post_id}.png", image_bytes=buf)
