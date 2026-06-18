from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from kvk.models.kvk_rankings import RankingPayload, RankingRow, RenderedRankingCard
from kvk.rendering.kvk_stats_card_renderer import (
    BLUE,
    GOLD,
    GREEN,
    HEIGHT,
    MUTED,
    RED,
    TEXT,
    WIDTH,
    _compact,
    _draw_text,
    _fit_font,
    _font,
    _load_background,
    _text_width,
)

ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / "assets" / "kvk" / "cards"
KVK_RANKINGS_BACKGROUND = ASSET_DIR / "KVK_Rankings_Background.png"
DEFAULT_BACKGROUND = ASSET_DIR / "Default_card.jpg"

AMBER = (255, 183, 77)
METRIC_BLUE = (76, 151, 255)
BRIGHT_GOLD = (255, 232, 91)
BRIGHT_BLUE = (170, 230, 255)
BRIGHT_AMBER = (255, 198, 74)
RANK_SHADOW = (18, 10, 5, 155)


def _background_path() -> Path | None:
    for path in (KVK_RANKINGS_BACKGROUND, DEFAULT_BACKGROUND):
        if path.exists():
            return path
    return None


def can_render_kvk_rankings_top10_card(payload: RankingPayload) -> bool:
    return payload.mode == "kvk" and payload.limit == 10 and bool(payload.rows)


def _metric_color(metric: str) -> tuple[int, int, int]:
    if metric in {"kills"}:
        return GREEN
    if metric in {"deads"}:
        return RED
    if metric in {"dkp"}:
        return METRIC_BLUE
    if metric in {"pct_kill_target"}:
        return GOLD
    if metric in {"acclaim"}:
        return GOLD
    if metric in {"tanking_score"}:
        return METRIC_BLUE
    return BLUE


def _format_cell_value(key: str, value: Any) -> str:
    if value is None or value == "":
        return "-"
    if key in {"% K/T", "% Kill Target", "pct_kill_target", "Tanking Score", "tanking_score"}:
        try:
            number = f"{float(value):.1f}".rstrip("0").rstrip(".")
            return f"{number}%"
        except Exception:
            return "-"
    if isinstance(value, str):
        return " ".join(value.split())
    try:
        return _compact(value)
    except Exception:
        return str(value)


def _primary_value(payload: RankingPayload, row: RankingRow) -> str:
    return _format_cell_value(payload.metric, row.value)


def _support_keys(payload: RankingPayload) -> tuple[str, str]:
    by_metric = {
        "power": ("Kills", "DKP"),
        "kills": ("Power", "DKP"),
        "pct_kill_target": ("Kills", "Power"),
        "deads": ("Power", "DKP"),
        "dkp": ("Kills", "Power"),
        "acclaim": ("Kills", "Healed"),
        "tanking_score": ("Kill Points", "Healed"),
    }
    return by_metric.get(payload.metric, ("Power", "Kills"))


def _support_text(payload: RankingPayload, row: RankingRow) -> str:
    parts: list[str] = []
    for key in _support_keys(payload):
        value = row.supporting_values.get(key)
        if value not in (None, ""):
            parts.append(f"{key} {_format_cell_value(key, value)}")
    return "  |  ".join(parts)


def _draw_fitted(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    max_width: int,
    size: int,
    min_size: int,
    fill: tuple[int, int, int] = TEXT,
    bold: bool = True,
) -> ImageFont.ImageFont:
    font = _fit_font(draw, text, max_width=max_width, size=size, min_size=min_size, bold=bold)
    _draw_text(draw, xy, text, fill=fill, font=font, bold=bold)
    return font


def _draw_right_fitted(
    draw: ImageDraw.ImageDraw,
    *,
    right_x: int,
    y: int,
    text: str,
    max_width: int,
    size: int,
    min_size: int,
    fill: tuple[int, int, int],
    bold: bool = True,
) -> None:
    font = _fit_font(draw, text, max_width=max_width, size=size, min_size=min_size, bold=bold)
    x = right_x - _text_width(draw, text, font)
    _draw_text(draw, (x, y), text, fill=fill, font=font, bold=bold)


def _draw_top_card(
    draw: ImageDraw.ImageDraw,
    *,
    payload: RankingPayload,
    row: RankingRow,
    box: tuple[int, int, int, int],
    accent: tuple[int, int, int],
) -> None:
    x0, y0, x1, y1 = box
    rank_label = f"#{row.rank}"
    rank_font = _font(48, bold=True)
    _draw_text(draw, (x0 + 2, y0 + 3), rank_label, fill=RANK_SHADOW, font=rank_font)
    _draw_text(draw, (x0, y0), rank_label, fill=accent, font=rank_font, bold=True)
    name_max = x1 - x0
    _draw_fitted(
        draw,
        (x0, y0 + 52),
        row.governor_name,
        max_width=name_max,
        size=39,
        min_size=24,
    )
    value = _primary_value(payload, row)
    _draw_fitted(
        draw,
        (x0, y0 + 102),
        value,
        max_width=name_max,
        size=52,
        min_size=28,
        fill=_metric_color(payload.metric),
    )
    support = _support_text(payload, row)
    if support:
        _draw_fitted(
            draw,
            (x0, y0 + 162),
            support,
            max_width=name_max,
            size=21,
            min_size=14,
            fill=MUTED,
        )


def _draw_row(
    draw: ImageDraw.ImageDraw,
    *,
    payload: RankingPayload,
    row: RankingRow,
    box: tuple[int, int, int, int],
) -> None:
    x0, y0, x1, y1 = box
    rank = f"#{row.rank}"
    _draw_text(draw, (x0, y0 + 10), rank, fill=GOLD, font=_font(23, bold=True))
    _draw_fitted(
        draw,
        (x0 + 60, y0 + 8),
        row.governor_name,
        max_width=260,
        size=22,
        min_size=16,
    )
    value = _primary_value(payload, row)
    _draw_right_fitted(
        draw,
        right_x=x1,
        y=y0 + 8,
        text=value,
        max_width=150,
        size=23,
        min_size=16,
        fill=_metric_color(payload.metric),
    )
    support = _support_text(payload, row)
    if support:
        _draw_fitted(
            draw,
            (x0 + 60, y1 - 22),
            support,
            max_width=x1 - x0 - 60,
            size=15,
            min_size=11,
            fill=MUTED,
        )


def _context_line(payload: RankingPayload) -> str:
    bits = [f"Top {payload.limit}", payload.metric_label]
    if payload.kvk_no is not None:
        bits.append(f"KVK {payload.kvk_no}")
    return "  |  ".join(bits)


def _footer(payload: RankingPayload) -> str:
    parts: list[str] = []
    if payload.freshness_label:
        parts.append(f"Last refreshed {payload.freshness_label}")
    if payload.filters:
        parts.append("Filters: " + ", ".join(payload.filters))
    if not parts:
        parts.append(f"Generated {payload.generated_at_utc:%Y-%m-%d %H:%M UTC}")
    return "  |  ".join(parts)


def render_kvk_rankings_top10_card(payload: RankingPayload) -> RenderedRankingCard | None:
    """Render the current KVK Top 10 spotlight card from an already-shaped ranking payload."""
    if not can_render_kvk_rankings_top10_card(payload):
        return None

    background = _background_path()
    if background is None:
        return None

    canvas = _load_background(background)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay, "RGBA")
    odraw.rounded_rectangle((0, 0, WIDTH - 1, HEIGHT - 1), radius=22, fill=(0, 0, 0, 82))
    odraw.rectangle((0, 0, WIDTH, 140), fill=(0, 0, 0, 82))
    odraw.rectangle((0, 330, WIDTH, HEIGHT), fill=(0, 0, 0, 92))
    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas, "RGBA")

    _draw_text(draw, (42, 38), "KVK Rankings", fill=GOLD, font=_font(34, bold=True), bold=True)
    _draw_fitted(
        draw,
        (42, 84),
        _context_line(payload),
        max_width=830,
        size=22,
        min_size=15,
        fill=MUTED,
    )
    _draw_right_fitted(
        draw,
        right_x=1138,
        y=40,
        text=f"TOP {payload.limit}",
        max_width=250,
        size=48,
        min_size=34,
        fill=TEXT,
    )
    _draw_right_fitted(
        draw,
        right_x=1138,
        y=92,
        text=payload.metric_label,
        max_width=250,
        size=21,
        min_size=15,
        fill=_metric_color(payload.metric),
    )

    top_rows = payload.rows[:3]
    top_boxes = (
        (405, 150, 775, 348),
        (42, 172, 370, 348),
        (810, 172, 1138, 348),
    )
    top_accents = (BRIGHT_GOLD, BRIGHT_BLUE, BRIGHT_AMBER)
    for row, box, accent in zip(top_rows, top_boxes, top_accents, strict=False):
        _draw_top_card(draw, payload=payload, row=row, box=box, accent=accent)

    rest_rows = payload.rows[3:10]
    row_boxes: list[tuple[int, int, int, int]] = []
    left_x, right_x = 42, 604
    y_start, row_h, gap = 365, 55, 7
    for idx in range(7):
        column_x = left_x if idx < 4 else right_x
        y = y_start + (idx if idx < 4 else idx - 4) * (row_h + gap)
        row_boxes.append((column_x, y, column_x + 534, y + row_h))
    for row, box in zip(rest_rows, row_boxes, strict=False):
        _draw_row(draw, payload=payload, row=row, box=box)

    footer_text = _footer(payload)
    _draw_right_fitted(
        draw,
        right_x=1138,
        y=610,
        text=footer_text,
        max_width=1058,
        size=17,
        min_size=12,
        fill=MUTED,
    )

    buf = BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return RenderedRankingCard(
        filename=f"kvk_rankings_top10_{payload.metric}.png",
        image_bytes=buf,
    )
