from __future__ import annotations

from io import BytesIO
import unicodedata

from PIL import Image, ImageDraw, ImageFont

from core import visual_text
from prekvk.models import PreKvkReportPayload, RenderedPreKvkReportImage
from prekvk.report_service import SORT_LABELS

WIDTH = 1680
HEADER_H = 172
ROW_H = 38
FOOTER_H = 70
BG = (12, 31, 55)
PANEL = (19, 48, 83)
HEADER = (30, 76, 126)
TEXT = (245, 250, 255)
MUTED = (166, 196, 225)
LINE = (54, 108, 164)
GOLD = (250, 204, 21)
BLUE = (96, 165, 250)


_is_variation_selector = visual_text.is_variation_selector
_is_emoji_modifier = visual_text.is_emoji_modifier
_is_regional_indicator = visual_text.is_regional_indicator
_is_tag_char = visual_text.is_tag_char
_is_combining_or_modifier = visual_text.is_combining_or_modifier
_text_clusters = visual_text.text_clusters
_font_candidates_for_char = visual_text.font_candidates_for_char
_font_candidates_for_text = visual_text.font_candidates_for_text
_font = visual_text.font
_font_for_char = visual_text.font_for_char
_font_for_text = visual_text.font_for_text
_cluster_font_size = visual_text.cluster_font_size
_coverage_codepoints = visual_text.coverage_codepoints
_font_coverage = visual_text.font_coverage
_font_supports_text = visual_text.font_supports_text


def _compact(value: int | None) -> str:
    if value is None:
        return "N/A"
    abs_val = abs(float(value))
    for threshold, unit in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if abs_val >= threshold:
            out = f"{float(value) / threshold:.1f}".rstrip("0").rstrip(".")
            return f"{out}{unit}"
    return f"{int(value):,}"


def _clean_text(value: str, max_chars: int) -> str:
    cleaned = unicodedata.normalize("NFC", str(value or ""))
    cleaned = cleaned.replace("\r", " ").replace("\n", " ")
    cleaned = " ".join(cleaned.split()) or "Unknown"
    return cleaned if len(cleaned) <= max_chars else cleaned[: max_chars - 1].rstrip() + "."


def _fit_text_to_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    width: int,
    font: ImageFont.ImageFont,
    bold: bool = False,
) -> str:
    return visual_text.fit_text_to_width(draw, text, width=width, base_font=font, bold=bold)


def _text_width(
    draw: ImageDraw.ImageDraw, text: str, *, font: ImageFont.ImageFont, bold: bool = False
) -> int:
    return visual_text.text_width(draw, text, font=font, bold=bold)


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    bold: bool = False,
) -> None:
    visual_text.draw_text(draw, xy, text, fill=fill, font=font, bold=bold)


def _cell(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    width: int,
    align: str = "left",
    font: ImageFont.ImageFont | None = None,
    fill: tuple[int, int, int] = TEXT,
    bold: bool = False,
) -> None:
    font = font or _font(20)
    x, y = xy
    if align == "right":
        x = x + width - _text_width(draw, text, font=font, bold=bold)
    elif align == "center":
        x = x + max(0, (width - _text_width(draw, text, font=font, bold=bold)) // 2)
    _draw_text(draw, (x, y), text, fill=fill, font=font, bold=bold)


def render_prekvk_report(payload: PreKvkReportPayload) -> RenderedPreKvkReportImage | None:
    if not payload.rows:
        return None
    height = HEADER_H + ROW_H * (len(payload.rows) + 1) + FOOTER_H
    canvas = Image.new("RGBA", (WIDTH, height), BG)
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle(
        (28, 28, WIDTH - 28, height - 28), radius=18, fill=PANEL, outline=LINE, width=2
    )
    draw.text(
        (58, 48), f"PreKvK Report - KVK {payload.kvk_no}", fill=TEXT, font=_font(36, bold=True)
    )
    draw.text(
        (58, 94),
        f"Sorted by {SORT_LABELS[payload.sort_by]} | Top {payload.limit}",
        fill=MUTED,
        font=_font(22),
    )
    if payload.scan_id is not None:
        draw.text((1180, 54), f"Scan {payload.scan_id}", fill=BLUE, font=_font(22, bold=True))
    if payload.source_filename:
        draw.text((1180, 90), _clean_text(payload.source_filename, 34), fill=MUTED, font=_font(18))

    cols = [
        ("Rank", 58, 78, "left"),
        ("GovernorName", 150, 360, "left"),
        ("Power", 540, 150, "right"),
        ("Stage 1", 730, 150, "right"),
        ("Stage 2", 910, 150, "right"),
        ("Stage 3", 1090, 150, "right"),
        ("Overall", 1288, 180, "right"),
    ]
    y = HEADER_H
    draw.rounded_rectangle((48, y, WIDTH - 48, y + ROW_H), radius=8, fill=HEADER)
    for title, x, w, align in cols:
        _cell(
            draw,
            (x, y + 8),
            title,
            width=w,
            align=align,
            font=_font(18, bold=True),
            fill=TEXT,
            bold=True,
        )

    for idx, row in enumerate(payload.rows):
        y = HEADER_H + ROW_H * (idx + 1)
        if idx % 2 == 0:
            draw.rectangle((48, y, WIDTH - 48, y + ROW_H), fill=(15, 41, 72))
        rank_fill = GOLD if row.rank <= 3 else TEXT
        name_font = _font(18)
        governor_name = _fit_text_to_width(
            draw,
            _clean_text(row.governor_name, 40),
            width=360,
            font=name_font,
        )
        values = [
            (str(row.rank), 58, 78, "left", rank_fill),
            (governor_name, 150, 360, "left", TEXT),
            (_compact(row.power), 540, 150, "right", MUTED if row.power is None else TEXT),
            (
                _compact(row.stage1_points),
                730,
                150,
                "right",
                MUTED if row.stage1_points is None else TEXT,
            ),
            (
                _compact(row.stage2_points),
                910,
                150,
                "right",
                MUTED if row.stage2_points is None else TEXT,
            ),
            (
                _compact(row.stage3_points),
                1090,
                150,
                "right",
                MUTED if row.stage3_points is None else TEXT,
            ),
            (_compact(row.overall_points), 1288, 180, "right", TEXT),
        ]
        for value, x, w, align, fill in values:
            _cell(draw, (x, y + 8), value, width=w, align=align, font=name_font, fill=fill)

    footer = (
        "Legacy total-only imports show N/A for stage columns."
        if not payload.has_stage_data
        else "Direct-stage PreKvK data path"
    )
    draw.text((58, height - 52), footer, fill=MUTED, font=_font(17))
    draw.text(
        (1280, height - 52),
        f"Generated {payload.generated_at_utc:%Y-%m-%d %H:%M UTC}",
        fill=MUTED,
        font=_font(17),
    )
    buf = BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return RenderedPreKvkReportImage(
        filename=f"prekvk_report_kvk{payload.kvk_no}_{payload.sort_by.value}_top{payload.limit}.png",
        image_bytes=buf,
    )
