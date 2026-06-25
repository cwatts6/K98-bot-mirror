from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path
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


def _is_variation_selector(codepoint: int) -> bool:
    return 0xFE00 <= codepoint <= 0xFE0F


def _is_emoji_modifier(codepoint: int) -> bool:
    return 0x1F3FB <= codepoint <= 0x1F3FF


def _is_regional_indicator(codepoint: int) -> bool:
    return 0x1F1E6 <= codepoint <= 0x1F1FF


def _is_tag_char(codepoint: int) -> bool:
    return 0xE0020 <= codepoint <= 0xE007F


def _is_combining_or_modifier(ch: str) -> bool:
    codepoint = ord(ch)
    return (
        unicodedata.combining(ch) > 0
        or _is_variation_selector(codepoint)
        or _is_emoji_modifier(codepoint)
        or _is_tag_char(codepoint)
        or codepoint == 0x20E3
    )


def _text_clusters(text: str) -> list[str]:
    clusters: list[str] = []
    idx = 0
    while idx < len(text):
        cluster = text[idx]
        idx += 1

        if _is_regional_indicator(ord(cluster)):
            if idx < len(text) and _is_regional_indicator(ord(text[idx])):
                cluster += text[idx]
                idx += 1
            clusters.append(cluster)
            continue

        while idx < len(text):
            ch = text[idx]
            codepoint = ord(ch)
            if _is_combining_or_modifier(ch):
                cluster += ch
                idx += 1
                continue
            if codepoint == 0x200D and idx + 1 < len(text):
                cluster += ch + text[idx + 1]
                idx += 2
                continue
            break

        clusters.append(cluster)
    return clusters


def _font_candidates_for_char(ch: str, *, bold: bool = False) -> list[str]:
    return _font_candidates_for_text(ch, bold=bold)


def _font_candidates_for_text(text: str, *, bold: bool = False) -> list[str]:
    codepoints = [ord(ch) for ch in text]
    if (
        any(0x1F000 <= codepoint <= 0x1FAFF for codepoint in codepoints)
        or any(0x2600 <= codepoint <= 0x27BF for codepoint in codepoints)
        or any(unicodedata.category(ch) in {"So", "Sk"} for ch in text)
    ):
        return [
            "C:/Windows/Fonts/seguiemj.ttf",
            "C:/Windows/Fonts/seguisym.ttf",
        ]
    if any(0x0E00 <= codepoint <= 0x0E7F for codepoint in codepoints):
        return [
            "C:/Windows/Fonts/LeelaUIb.ttf" if bold else "C:/Windows/Fonts/LeelawUI.ttf",
            "C:/Windows/Fonts/LEELAWAD.TTF",
        ]
    if any(0x3400 <= codepoint <= 0x9FFF for codepoint in codepoints):
        return [
            "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/YuGothB.ttc" if bold else "C:/Windows/Fonts/YuGothM.ttc",
            "C:/Windows/Fonts/msgothic.ttc",
        ]
    if any(0x3000 <= codepoint <= 0x30FF for codepoint in codepoints) or any(
        0xAC00 <= codepoint <= 0xD7AF for codepoint in codepoints
    ):
        return [
            "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/YuGothB.ttc" if bold else "C:/Windows/Fonts/YuGothM.ttc",
            "C:/Windows/Fonts/msgothic.ttc",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf",
        ]
    return []


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


@lru_cache(maxsize=512)
def _font_for_char(ch: str, size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    return _font_for_text(ch, size, bold=bold)


@lru_cache(maxsize=512)
def _font_for_text(text: str, size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    for candidate in _font_candidates_for_text(text, bold=bold):
        if not _font_supports_text(candidate, text):
            continue
        try:
            return ImageFont.truetype(candidate, size=size)
        except Exception:
            continue
    return _font(size, bold=bold)


def _cluster_font_size(text: str, base_size: int) -> int:
    codepoints = [ord(ch) for ch in text]
    if any(0x0E00 <= codepoint <= 0x0E7F for codepoint in codepoints) or any(
        0x3000 <= codepoint <= 0x9FFF or 0xAC00 <= codepoint <= 0xD7AF for codepoint in codepoints
    ):
        return base_size + 4
    return base_size


def _coverage_codepoints(text: str) -> list[int]:
    return [
        ord(ch)
        for ch in text
        if ord(ch) != 0x200D and not _is_variation_selector(ord(ch)) and not _is_tag_char(ord(ch))
    ]


@lru_cache(maxsize=512)
def _font_coverage(font_path: str) -> frozenset[int] | None:
    if not Path(font_path).exists():
        return frozenset()
    try:
        from fontTools.ttLib import TTCollection, TTFont
    except Exception:
        return None
    try:
        font_obj = (
            TTCollection(font_path).fonts[0]
            if font_path.lower().endswith(".ttc")
            else TTFont(font_path, lazy=True)
        )
        coverage: set[int] = set()
        for table in font_obj["cmap"].tables:
            coverage.update(table.cmap.keys())
        return frozenset(coverage)
    except Exception:
        return None


@lru_cache(maxsize=512)
def _font_supports_text(font_path: str, text: str) -> bool:
    codepoints = _coverage_codepoints(text)
    if not codepoints:
        return True
    coverage = _font_coverage(font_path)
    if coverage is None:
        return True
    return all(codepoint in coverage for codepoint in codepoints)


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
    if _text_width(draw, text, font=font, bold=bold) <= width:
        return text
    out = ""
    suffix = "."
    for cluster in _text_clusters(text):
        candidate = f"{out}{cluster}{suffix}"
        if _text_width(draw, candidate, font=font, bold=bold) > width:
            break
        out += cluster
    return (out.rstrip() + suffix) if out.strip() else suffix


def _text_width(
    draw: ImageDraw.ImageDraw, text: str, *, font: ImageFont.ImageFont, bold: bool = False
) -> int:
    width = 0
    for cluster in _text_clusters(text):
        base_size = getattr(font, "size", 20)
        cluster_font = _font_for_text(cluster, _cluster_font_size(cluster, base_size), bold=bold)
        box = draw.textbbox((0, 0), cluster, font=cluster_font)
        width += int(box[2] - box[0])
    return width


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    bold: bool = False,
) -> None:
    x, y = xy
    for cluster in _text_clusters(text):
        base_size = getattr(font, "size", 20)
        cluster_font = _font_for_text(cluster, _cluster_font_size(cluster, base_size), bold=bold)
        draw.text((x, y), cluster, fill=fill, font=cluster_font)
        box = draw.textbbox((0, 0), cluster, font=cluster_font)
        x += int(box[2] - box[0])


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
