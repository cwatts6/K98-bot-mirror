"""Shared Pillow text helpers for generated visual cards."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import unicodedata

from PIL import ImageDraw, ImageFont


def is_variation_selector(codepoint: int) -> bool:
    return 0xFE00 <= codepoint <= 0xFE0F


def is_emoji_modifier(codepoint: int) -> bool:
    return 0x1F3FB <= codepoint <= 0x1F3FF


def is_regional_indicator(codepoint: int) -> bool:
    return 0x1F1E6 <= codepoint <= 0x1F1FF


def is_tag_char(codepoint: int) -> bool:
    return 0xE0020 <= codepoint <= 0xE007F


def is_combining_or_modifier(ch: str) -> bool:
    codepoint = ord(ch)
    return (
        unicodedata.combining(ch) > 0
        or is_variation_selector(codepoint)
        or is_emoji_modifier(codepoint)
        or is_tag_char(codepoint)
        or codepoint == 0x20E3
    )


def text_clusters(text: str) -> list[str]:
    clusters: list[str] = []
    idx = 0
    while idx < len(text):
        cluster = text[idx]
        idx += 1

        if is_regional_indicator(ord(cluster)):
            if idx < len(text) and is_regional_indicator(ord(text[idx])):
                cluster += text[idx]
                idx += 1
            clusters.append(cluster)
            continue

        while idx < len(text):
            ch = text[idx]
            codepoint = ord(ch)
            if is_combining_or_modifier(ch):
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


def font_candidates_for_char(ch: str, *, bold: bool = False) -> list[str]:
    return font_candidates_for_text(ch, bold=bold)


def font_candidates_for_text(text: str, *, bold: bool = False) -> list[str]:
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
def font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
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
def font_for_char(ch: str, size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    return font_for_text(ch, size, bold=bold)


@lru_cache(maxsize=512)
def font_for_text(text: str, size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    for candidate in font_candidates_for_text(text, bold=bold):
        if not font_supports_text(candidate, text):
            continue
        try:
            return ImageFont.truetype(candidate, size=size)
        except Exception:
            continue
    return font(size, bold=bold)


def cluster_font_size(text: str, base_size: int) -> int:
    codepoints = [ord(ch) for ch in text]
    if any(0x0E00 <= codepoint <= 0x0E7F for codepoint in codepoints) or any(
        0x3000 <= codepoint <= 0x9FFF or 0xAC00 <= codepoint <= 0xD7AF for codepoint in codepoints
    ):
        return base_size + 4
    return base_size


def coverage_codepoints(text: str) -> list[int]:
    return [
        ord(ch)
        for ch in text
        if ord(ch) != 0x200D and not is_variation_selector(ord(ch)) and not is_tag_char(ord(ch))
    ]


@lru_cache(maxsize=512)
def font_coverage(font_path: str) -> frozenset[int] | None:
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
def font_supports_text(font_path: str, text: str) -> bool:
    codepoints = coverage_codepoints(text)
    if not codepoints:
        return True
    coverage = font_coverage(font_path)
    if coverage is None:
        return True
    return all(codepoint in coverage for codepoint in codepoints)


def fit_text_to_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    width: int,
    base_font: ImageFont.ImageFont,
    bold: bool = False,
) -> str:
    if text_width(draw, text, font=base_font, bold=bold) <= width:
        return text
    out = ""
    suffix = "."
    for cluster in text_clusters(text):
        candidate = f"{out}{cluster}{suffix}"
        if text_width(draw, candidate, font=base_font, bold=bold) > width:
            break
        out += cluster
    return (out.rstrip() + suffix) if out.strip() else suffix


def text_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    font: ImageFont.ImageFont,
    bold: bool = False,
) -> int:
    width = 0
    for cluster in text_clusters(text):
        base_size = getattr(font, "size", 20)
        cluster_font = font_for_text(cluster, cluster_font_size(cluster, base_size), bold=bold)
        box = draw.textbbox((0, 0), cluster, font=cluster_font)
        width += int(box[2] - box[0])
    return width


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int] | tuple[int, int, int, int],
    bold: bool = False,
) -> None:
    x, y = xy
    for cluster in text_clusters(text):
        base_size = getattr(font, "size", 20)
        cluster_font = font_for_text(cluster, cluster_font_size(cluster, base_size), bold=bold)
        draw.text((x, y), cluster, fill=fill, font=cluster_font)
        box = draw.textbbox((0, 0), cluster, font=cluster_font)
        x += int(box[2] - box[0])


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    max_width: int,
    size: int,
    min_size: int,
    bold: bool = False,
) -> ImageFont.ImageFont:
    fitted = font_for_text(text, size, bold=bold)
    while size > min_size and text_width(draw, text, font=fitted, bold=bold) > max_width:
        size -= 1
        fitted = font_for_text(text, size, bold=bold)
    return fitted


def fit_common_font(
    draw: ImageDraw.ImageDraw,
    values: list[str] | tuple[str, ...],
    *,
    max_width: int,
    size: int,
    min_size: int,
    bold: bool = False,
) -> ImageFont.ImageFont:
    fitted = font(size, bold=bold)
    while size > min_size and any(
        text_width(draw, value, font=fitted, bold=bold) > max_width for value in values
    ):
        size -= 1
        fitted = font(size, bold=bold)
    return fitted
