from __future__ import annotations

from functools import lru_cache
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
HONOR_RANKINGS_BACKGROUND = ASSET_DIR / "Honor_Rankings_Background.png"
PREKVK_RANKINGS_BACKGROUND = ASSET_DIR / "Pre_KVK_Rankings_Background.png"
HALL_OF_FAME_BACKGROUND = ASSET_DIR / "Hall_of_Fame_Kingdom_Records_Background.png"
DEFAULT_BACKGROUND = ASSET_DIR / "Default_card.jpg"
CURRENT_RANKING_BACKGROUNDS = {
    "kvk": KVK_RANKINGS_BACKGROUND,
    "honor": HONOR_RANKINGS_BACKGROUND,
    "prekvk": PREKVK_RANKINGS_BACKGROUND,
}

AMBER = (255, 183, 77)
METRIC_BLUE = (76, 151, 255)
BRIGHT_GOLD = (255, 232, 91)
BRIGHT_BLUE = (170, 230, 255)
CURRENT_RANKING_BLUE = (92, 190, 230)
BRIGHT_AMBER = (255, 198, 74)
RANK_SHADOW = (18, 10, 5, 155)


def _background_path(mode: str = "kvk") -> Path | None:
    mode_background = CURRENT_RANKING_BACKGROUNDS.get(mode, KVK_RANKINGS_BACKGROUND)
    for path in (mode_background, DEFAULT_BACKGROUND):
        if path.exists():
            return path
    return None


def can_render_current_rankings_top10_card(payload: RankingPayload) -> bool:
    return (
        payload.mode in CURRENT_RANKING_BACKGROUNDS and payload.limit == 10 and bool(payload.rows)
    )


def can_render_kvk_rankings_top10_card(payload: RankingPayload) -> bool:
    return can_render_current_rankings_top10_card(payload)


def can_render_hall_of_fame_top10_card(payload: RankingPayload) -> bool:
    return payload.mode == "records" and payload.limit == 10 and bool(payload.rows)


def _metric_color(metric: str) -> tuple[int, int, int]:
    if metric in {"honor", "overall", "stage1", "stage2", "stage3"}:
        return CURRENT_RANKING_BLUE
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


def _record_metric_color(metric: str) -> tuple[int, int, int]:
    if metric in {"kills", "dkp", "acclaim"}:
        return BRIGHT_GOLD
    if metric in {"killpoints", "prekvk", "honor"}:
        return BRIGHT_BLUE
    if metric in {"deads"}:
        return RED
    if metric in {"healed"}:
        return GREEN
    return GOLD


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
    if payload.mode == "honor":
        return ("Governor ID", "KVK")
    if payload.mode == "prekvk":
        by_prekvk_metric = {
            "overall": ("Stage 1", "Stage 2"),
            "stage1": ("Overall", "Power"),
            "stage2": ("Overall", "Stage 1"),
            "stage3": ("Overall", "Stage 2"),
        }
        return by_prekvk_metric.get(payload.metric, ("Overall", "Power"))
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


def _draw_shadowed_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    fill: tuple[int, int, int] = TEXT,
    font: ImageFont.ImageFont | None = None,
    bold: bool = False,
    shadow: tuple[int, int, int, int] = (0, 0, 0, 180),
    offset: tuple[int, int] = (2, 3),
) -> None:
    x, y = xy
    _draw_text(draw, (x + offset[0], y + offset[1]), text, fill=shadow, font=font, bold=bold)
    _draw_text(draw, xy, text, fill=fill, font=font, bold=bold)


def _draw_shadowed_fitted(
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
    _draw_shadowed_text(draw, xy, text, fill=fill, font=font, bold=bold)
    return font


def _draw_shadowed_right_fitted(
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
    _draw_shadowed_text(draw, (x, y), text, fill=fill, font=font, bold=bold)


def _draw_shadowed_center_fitted(
    draw: ImageDraw.ImageDraw,
    *,
    center_x: int,
    y: int,
    text: str,
    max_width: int,
    size: int,
    min_size: int,
    fill: tuple[int, int, int],
    bold: bool = True,
) -> None:
    font = _fit_font(draw, text, max_width=max_width, size=size, min_size=min_size, bold=bold)
    x = center_x - (_text_width(draw, text, font) // 2)
    _draw_shadowed_text(draw, (x, y), text, fill=fill, font=font, bold=bold)


def _draw_top_card(
    draw: ImageDraw.ImageDraw,
    *,
    payload: RankingPayload,
    row: RankingRow,
    box: tuple[int, int, int, int],
    accent: tuple[int, int, int],
) -> None:
    x0, y0, x1, y1 = box
    width = x1 - x0
    if payload.mode in {"honor", "prekvk"}:
        center_x = x0 + (width // 2)
        _draw_shadowed_center_fitted(
            draw,
            center_x=center_x,
            y=y0,
            text=f"#{row.rank}",
            max_width=width,
            size=48,
            min_size=32,
            fill=accent,
        )
        _draw_shadowed_center_fitted(
            draw,
            center_x=center_x,
            y=y0 + 52,
            text=row.governor_name,
            max_width=width,
            size=39,
            min_size=18,
            fill=TEXT,
        )
        _draw_shadowed_center_fitted(
            draw,
            center_x=center_x,
            y=y0 + 102,
            text=_primary_value(payload, row),
            max_width=width,
            size=52,
            min_size=28,
            fill=_metric_color(payload.metric),
        )
        support = _support_text(payload, row)
        if support:
            _draw_shadowed_center_fitted(
                draw,
                center_x=center_x,
                y=y0 + 162,
                text=support,
                max_width=width,
                size=21,
                min_size=14,
                fill=MUTED,
            )
        return

    rank_label = f"#{row.rank}"
    rank_font = _font(48, bold=True)
    _draw_text(draw, (x0 + 2, y0 + 3), rank_label, fill=RANK_SHADOW, font=rank_font)
    _draw_text(draw, (x0, y0), rank_label, fill=accent, font=rank_font, bold=True)
    name_max = width
    _draw_fitted(
        draw,
        (x0, y0 + 52),
        row.governor_name,
        max_width=name_max,
        size=39,
        min_size=18,
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
    bits = [f"Top {payload.limit}"]
    if payload.mode not in {"honor", "prekvk"}:
        bits.append(payload.metric_label)
    if payload.kvk_no is not None:
        bits.append(f"KVK {payload.kvk_no}")
    return "  |  ".join(bits)


def _footer(payload: RankingPayload) -> str:
    if payload.mode in {"honor", "prekvk"}:
        return f"Last refreshed {payload.freshness_label}" if payload.freshness_label else ""

    parts: list[str] = []
    if payload.freshness_label:
        parts.append(f"Last refreshed {payload.freshness_label}")
    if payload.filters:
        parts.append("Filters: " + ", ".join(payload.filters))
    if not parts:
        parts.append(f"Generated {payload.generated_at_utc:%Y-%m-%d %H:%M UTC}")
    return "  |  ".join(parts)


def _current_rankings_title(payload: RankingPayload) -> str:
    if payload.mode == "honor":
        return "Honor Rankings"
    if payload.mode == "prekvk":
        return "PreKvK Rankings"
    return "KVK Rankings"


def _current_card_filename(payload: RankingPayload) -> str:
    if payload.mode == "kvk":
        return f"kvk_rankings_top10_{payload.metric}.png"
    return f"kvk_rankings_{payload.mode}_top10_{payload.metric}.png"


def _records_background_path() -> Path | None:
    for path in (HALL_OF_FAME_BACKGROUND, DEFAULT_BACKGROUND):
        if path.exists():
            return path
    return None


@lru_cache(maxsize=1)
def _records_darkening_overlay() -> Image.Image:
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    pixels = overlay.load()
    edge_denominator = max(1.0, (WIDTH - 1) / 2)
    for y in range(HEIGHT):
        alpha = int(118 - (58 * y / max(1, HEIGHT - 1)))
        for x in range(WIDTH):
            edge = min(x, WIDTH - 1 - x) / edge_denominator
            edge_alpha = int((1 - min(1.0, edge)) * 46)
            pixels[x, y] = (0, 0, 0, max(42, alpha + edge_alpha))
    return overlay


def _record_kvk_label(row: RankingRow) -> str:
    if row.kvk_no is None:
        return "KVK unknown"
    if row.kvk_name:
        return f"KVK {row.kvk_no} - {' '.join(row.kvk_name.split())}"
    return f"KVK {row.kvk_no}"


def _records_context_line(payload: RankingPayload) -> str:
    return f"Top {payload.limit} all-time single-KVK {payload.metric_label}"


def _records_count_label(payload: RankingPayload) -> str:
    return f"TOP {payload.limit}"


def _records_total_label(payload: RankingPayload) -> str:
    count = payload.total_rows if payload.total_rows is not None else len(payload.rows)
    noun = "record" if count == 1 else "records"
    return f"from {count:,} {noun}"


def _draw_record_podium(
    draw: ImageDraw.ImageDraw,
    *,
    payload: RankingPayload,
    row: RankingRow,
    box: tuple[int, int, int, int],
    accent: tuple[int, int, int],
) -> None:
    x0, y0, x1, _y1 = box
    width = x1 - x0
    center_x = x0 + (width // 2)
    _draw_shadowed_center_fitted(
        draw,
        center_x=center_x,
        y=y0,
        text=f"#{row.rank}",
        max_width=width,
        size=47,
        min_size=32,
        fill=accent,
    )
    _draw_shadowed_center_fitted(
        draw,
        center_x=center_x,
        y=y0 + 48,
        text=row.governor_name,
        max_width=width,
        size=32,
        min_size=20,
        fill=TEXT,
    )
    _draw_shadowed_center_fitted(
        draw,
        center_x=center_x,
        y=y0 + 88,
        text=_format_cell_value(payload.metric, row.value),
        max_width=width,
        size=45,
        min_size=26,
        fill=_record_metric_color(payload.metric),
    )
    _draw_shadowed_center_fitted(
        draw,
        center_x=center_x,
        y=y0 + 142,
        text=_record_kvk_label(row),
        max_width=width,
        size=18,
        min_size=13,
        fill=MUTED,
        bold=False,
    )


def _draw_record_row(
    draw: ImageDraw.ImageDraw,
    *,
    payload: RankingPayload,
    row: RankingRow,
    box: tuple[int, int, int, int],
) -> None:
    x0, y0, x1, y1 = box
    _draw_shadowed_text(
        draw,
        (x0, y0 + 6),
        f"#{row.rank}",
        fill=GOLD,
        font=_font(25, bold=True),
        bold=True,
    )
    _draw_shadowed_fitted(
        draw,
        (x0 + 62, y0 + 5),
        row.governor_name,
        max_width=245,
        size=22,
        min_size=15,
    )
    _draw_shadowed_right_fitted(
        draw,
        right_x=x1,
        y=y0 + 5,
        text=_format_cell_value(payload.metric, row.value),
        max_width=155,
        size=23,
        min_size=15,
        fill=_record_metric_color(payload.metric),
    )
    _draw_shadowed_fitted(
        draw,
        (x0 + 62, y1 - 22),
        _record_kvk_label(row),
        max_width=x1 - x0 - 62,
        size=15,
        min_size=11,
        fill=MUTED,
        bold=False,
    )


def render_hall_of_fame_top10_card(payload: RankingPayload) -> RenderedRankingCard | None:
    """Render the Hall of Fame Top 10 card from an already-shaped records payload."""
    if not can_render_hall_of_fame_top10_card(payload):
        return None

    background = _records_background_path()
    if background is None:
        return None

    canvas = _load_background(background)
    canvas = Image.alpha_composite(canvas, _records_darkening_overlay())
    draw = ImageDraw.Draw(canvas, "RGBA")

    accent = _record_metric_color(payload.metric)
    _draw_shadowed_text(
        draw,
        (42, 33),
        "KD98 Hall of Fame",
        fill=GOLD,
        font=_font(36, bold=True),
        bold=True,
    )
    _draw_shadowed_fitted(
        draw,
        (42, 80),
        _records_context_line(payload),
        max_width=770,
        size=23,
        min_size=15,
        fill=MUTED,
        bold=False,
    )
    _draw_shadowed_right_fitted(
        draw,
        right_x=1138,
        y=34,
        text=_records_count_label(payload),
        max_width=270,
        size=38,
        min_size=26,
        fill=TEXT,
    )
    _draw_shadowed_right_fitted(
        draw,
        right_x=1138,
        y=84,
        text=_records_total_label(payload),
        max_width=270,
        size=23,
        min_size=16,
        fill=accent,
    )

    podium_rows = payload.rows[:3]
    podium_boxes = (
        (430, 160, 760, 338),
        (68, 190, 370, 354),
        (815, 190, 1117, 354),
    )
    podium_accents = (BRIGHT_GOLD, BRIGHT_BLUE, BRIGHT_AMBER)
    for row, box, row_accent in zip(podium_rows, podium_boxes, podium_accents, strict=False):
        _draw_record_podium(draw, payload=payload, row=row, box=box, accent=row_accent)

    rest_rows = payload.rows[3:10]
    row_boxes: list[tuple[int, int, int, int]] = []
    left_x, right_x = 58, 622
    y_start, row_h, gap = 380, 53, 6
    for idx in range(7):
        column_x = left_x if idx < 4 else right_x
        y = y_start + (idx if idx < 4 else idx - 4) * (row_h + gap)
        row_boxes.append((column_x, y, column_x + 500, y + row_h))
    for row, box in zip(rest_rows, row_boxes, strict=False):
        _draw_record_row(draw, payload=payload, row=row, box=box)

    if payload.freshness_label:
        _draw_shadowed_right_fitted(
            draw,
            right_x=1138,
            y=610,
            text=f"Updated {payload.freshness_label}",
            max_width=420,
            size=15,
            min_size=11,
            fill=MUTED,
            bold=False,
        )

    buf = BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return RenderedRankingCard(
        filename=f"kvk_hall_of_fame_top10_{payload.metric}.png",
        image_bytes=buf,
    )


def render_current_rankings_top10_card(payload: RankingPayload) -> RenderedRankingCard | None:
    """Render a current-ranking Top 10 spotlight card from an already-shaped ranking payload."""
    if not can_render_current_rankings_top10_card(payload):
        return None

    background = _background_path(payload.mode)
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

    _draw_text(
        draw,
        (42, 38),
        _current_rankings_title(payload),
        fill=GOLD,
        font=_font(34, bold=True),
        bold=True,
    )
    _draw_fitted(
        draw,
        (42, 84),
        _context_line(payload),
        max_width=830,
        size=22,
        min_size=15,
        fill=MUTED,
    )
    if payload.mode == "prekvk":
        _draw_right_fitted(
            draw,
            right_x=1138,
            y=58,
            text=payload.metric_label,
            max_width=320,
            size=38,
            min_size=24,
            fill=_metric_color(payload.metric),
        )
    elif payload.mode != "honor":
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
    if footer_text:
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
        filename=_current_card_filename(payload),
        image_bytes=buf,
    )


def render_kvk_rankings_top10_card(payload: RankingPayload) -> RenderedRankingCard | None:
    return render_current_rankings_top10_card(payload)
