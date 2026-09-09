from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core import visual_text
from voting.models import RenderedVoteCard, VoteSnapshot
from voting.option_emojis import option_display_label
from voting.outcomes import vote_outcome
from voting.result_visibility import public_results_hidden
from voting.vote_modes import VOTE_MODE_MULTI_SELECT, normalize_vote_mode

ROOT = Path(__file__).resolve().parents[1]
VOTING_BACKGROUND = ROOT / "assets" / "vote" / "vote.png"
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
            with Image.open(path) as image:
                return image.convert("RGBA").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    return Image.new("RGBA", (WIDTH, HEIGHT), (13, 20, 33, 255))


def _status(snapshot: VoteSnapshot, now_utc: datetime) -> tuple[str, tuple[int, int, int]]:
    if snapshot.status == "Closed" or snapshot.closed_at_utc is not None:
        return "Closed", RED
    minutes_left = (snapshot.closes_at_utc - now_utc).total_seconds() / 60
    if minutes_left <= 0:
        return "Closed", RED
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


def _is_closed(snapshot: VoteSnapshot, now_utc: datetime) -> bool:
    return (
        snapshot.status == "Closed"
        or snapshot.closed_at_utc is not None
        or snapshot.closes_at_utc <= now_utc
    )


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

    total = int(snapshot.total_votes or 0)
    total_selections = int(snapshot.total_selections or total)
    is_multi_select = normalize_vote_mode(snapshot.vote_mode) == VOTE_MODE_MULTI_SELECT
    hide_results = public_results_hidden(snapshot, now_utc=now)
    closed = _is_closed(snapshot, now)
    outcome = vote_outcome(snapshot) if closed and not hide_results else None
    winner_ids = set(outcome.winning_option_ids if outcome else ())
    options = snapshot.options[:6]
    count = max(1, len(options))
    chart_left = 66
    chart_right = WIDTH - 66
    chart_bottom = 456
    slot_w = (chart_right - chart_left) / count
    max_bar_h = 148
    bar_w = min(72, max(40, int(slot_w * 0.45)))
    for index, option in enumerate(options):
        center_x = int(chart_left + (slot_w * index) + (slot_w / 2))
        bar_left = center_x - (bar_w // 2)
        bar_right = center_x + (bar_w // 2)
        bar_top = chart_bottom - max_bar_h
        is_winner = closed and int(option.option_id) in winner_ids
        fill = GOLD if is_winner else BLUE
        draw.rounded_rectangle(
            (bar_left, bar_top, bar_right, chart_bottom), radius=14, fill=(51, 65, 85, 210)
        )
        fill_h = (
            int(max_bar_h * int(option.vote_count or 0) / total)
            if total and not hide_results
            else 0
        )
        if fill_h:
            draw.rounded_rectangle(
                (bar_left, chart_bottom - fill_h, bar_right, chart_bottom),
                radius=14,
                fill=fill,
            )
        if is_winner:
            draw.rounded_rectangle(
                (bar_left - 5, bar_top - 5, bar_right + 5, chart_bottom + 5),
                radius=18,
                outline=GOLD,
                width=3,
            )
        stat = (
            "Hidden"
            if hide_results
            else f"{_compact_count(option.vote_count)} | {_pct(option.vote_count, total)}"
        )
        stat_font = _fit_font(
            draw, stat, max_width=int(slot_w) - 12, size=20, min_size=14, bold=True
        )
        stat_x = center_x - (_text_width(draw, stat, stat_font, bold=True) // 2)
        _draw_text(
            draw, (stat_x, 218), stat, fill=GOLD if is_winner else MUTED, font=stat_font, bold=True
        )

        label = option_display_label(option.label, option.emoji, card_fallback=True)
        label_font = _fit_font(
            draw, label, max_width=int(slot_w) - 12, size=20, min_size=13, bold=True
        )
        label_w = _text_width(draw, label, label_font, bold=True)
        label_x = center_x - (label_w // 2)
        _draw_text(
            draw, (max(chart_left, label_x), 466), label, fill=TEXT, font=label_font, bold=True
        )

    if outcome:
        summary_font = _fit_font(
            draw, outcome.summary, max_width=760, size=24, min_size=16, bold=True
        )
        _draw_text(draw, (48, 520), outcome.summary, fill=GOLD, font=summary_font, bold=True)

    if hide_results:
        footer = (
            f"Results hidden until close    Last updated: {_fmt_dt(now)}    "
            f"Vote #{snapshot.vote_post_id}"
        )
    elif is_multi_select:
        footer = (
            f"Total voters: {_compact_count(total)}    "
            f"Selections: {_compact_count(total_selections)}    "
            f"Last updated: {_fmt_dt(now)}    Vote #{snapshot.vote_post_id}"
        )
    else:
        footer = (
            f"Total voters: {_compact_count(total)}    Last updated: {_fmt_dt(now)}    "
            f"Vote #{snapshot.vote_post_id}"
        )
    footer_font = _fit_font(draw, footer, max_width=1000, size=22, min_size=16, bold=True)
    _draw_text(draw, (48, 578), footer, fill=MUTED, font=footer_font, bold=True)

    buf = BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return RenderedVoteCard(filename=f"vote_{snapshot.vote_post_id}.png", image_bytes=buf)
