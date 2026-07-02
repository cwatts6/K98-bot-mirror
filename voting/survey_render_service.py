from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core import visual_text
from voting.result_visibility import public_results_hidden
from voting.survey_models import RenderedSurveyCard, SurveySnapshot

ROOT = Path(__file__).resolve().parents[1]
SURVEY_BACKGROUND = ROOT / "assets" / "vote" / "vote.png"
FALLBACK_BACKGROUND = ROOT / "assets" / "kvk" / "cards" / "Default_card.jpg"
WIDTH = 1180
HEIGHT = 640
TEXT = (255, 255, 255)
MUTED = (209, 213, 219)
PANEL = (12, 18, 28, 178)
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
    for path in (SURVEY_BACKGROUND, FALLBACK_BACKGROUND):
        if path.exists():
            with Image.open(path) as image:
                return image.convert("RGBA").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    return Image.new("RGBA", (WIDTH, HEIGHT), (13, 20, 33, 255))


def _fmt_dt(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")


def _status(snapshot: SurveySnapshot, now_utc: datetime) -> tuple[str, tuple[int, int, int]]:
    if snapshot.status == "Closed" or snapshot.closed_at_utc is not None:
        return "Closed", RED
    minutes_left = (snapshot.closes_at_utc - now_utc).total_seconds() / 60
    if minutes_left <= 0:
        return "Closed", RED
    if minutes_left <= 60:
        return "Closing Soon", GOLD
    return "Open", GREEN


def _pct(count: int, total: int) -> str:
    if total <= 0:
        return "0%"
    value = (int(count) / int(total)) * 100
    return f"{value:.1f}".rstrip("0").rstrip(".") + "%"


def _top_option_line(snapshot: SurveySnapshot) -> str:
    lines: list[str] = []
    total = int(snapshot.total_responses or 0)
    for question in snapshot.questions[:5]:
        if not question.options:
            continue
        top_count = max(int(option.response_count or 0) for option in question.options)
        leaders = [option.label for option in question.options if int(option.response_count or 0) == top_count]
        if top_count == 0:
            lines.append(f"Q{question.sort_order}: no responses yet")
        else:
            lines.append(
                f"Q{question.sort_order}: {', '.join(leaders[:2])} ({top_count}, {_pct(top_count, total)})"
            )
    return "\n".join(lines) or "No questions configured."


def render_survey_card(
    snapshot: SurveySnapshot, *, now_utc: datetime | None = None
) -> RenderedSurveyCard:
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
    _draw_text(
        draw,
        (48, 145),
        f"Closes: {_fmt_dt(snapshot.closes_at_utc)}",
        fill=GOLD,
        font=_font(22, bold=True),
        bold=True,
    )

    hidden = public_results_hidden(snapshot, now_utc=now)
    headline = (
        "Results hidden until close"
        if hidden
        else f"Responses: {int(snapshot.total_responses or 0):,}"
    )
    headline_font = _fit_font(draw, headline, max_width=900, size=32, min_size=20, bold=True)
    _draw_text(draw, (66, 228), headline, fill=GOLD, font=headline_font, bold=True)

    if hidden:
        detail = f"{len(snapshot.questions)} required choice questions"
    else:
        detail = _top_option_line(snapshot)
    detail_font = _fit_font(draw, detail.splitlines()[0], max_width=960, size=24, min_size=16)
    y = 292
    for line in detail.splitlines()[:5]:
        _draw_text(draw, (66, y), line, fill=TEXT if not hidden else MUTED, font=detail_font)
        y += 38

    footer = (
        f"Required questions: {len(snapshot.questions)}    "
        f"Last updated: {_fmt_dt(now)}    Survey #{snapshot.survey_id}"
    )
    footer_font = _fit_font(draw, footer, max_width=1000, size=22, min_size=16, bold=True)
    _draw_text(draw, (48, 578), footer, fill=MUTED, font=footer_font, bold=True)

    buf = BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return RenderedSurveyCard(filename=f"survey_{snapshot.survey_id}.png", image_bytes=buf)
