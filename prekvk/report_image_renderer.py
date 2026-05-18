from __future__ import annotations

from functools import lru_cache
from io import BytesIO
import unicodedata

from PIL import Image, ImageDraw, ImageFont

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


@lru_cache(maxsize=32)
def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


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
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    cleaned = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    cleaned = cleaned.replace("\r", " ").replace("\n", " ")
    cleaned = " ".join(cleaned.split()) or "Unknown"
    return cleaned if len(cleaned) <= max_chars else cleaned[: max_chars - 1].rstrip() + "."


def _cell(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    width: int,
    align: str = "left",
    font: ImageFont.ImageFont | None = None,
    fill: tuple[int, int, int] = TEXT,
) -> None:
    font = font or _font(20)
    x, y = xy
    if align == "right":
        box = draw.textbbox((0, 0), text, font=font)
        x = x + width - int(box[2] - box[0])
    elif align == "center":
        box = draw.textbbox((0, 0), text, font=font)
        x = x + max(0, (width - int(box[2] - box[0])) // 2)
    draw.text((x, y), text, fill=fill, font=font)


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
        _cell(draw, (x, y + 8), title, width=w, align=align, font=_font(18, bold=True), fill=TEXT)

    for idx, row in enumerate(payload.rows):
        y = HEADER_H + ROW_H * (idx + 1)
        if idx % 2 == 0:
            draw.rectangle((48, y, WIDTH - 48, y + ROW_H), fill=(15, 41, 72))
        rank_fill = GOLD if row.rank <= 3 else TEXT
        values = [
            (str(row.rank), 58, 78, "left", rank_fill),
            (_clean_text(row.governor_name, 28), 150, 360, "left", TEXT),
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
            _cell(draw, (x, y + 8), value, width=w, align=align, font=_font(18), fill=fill)

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
