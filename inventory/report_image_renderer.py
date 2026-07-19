from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from io import BytesIO
import logging
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

from core import visual_text
from inventory.capacity_calculations import (
    rss_healing_capacity,
    rss_training_capacity,
    speedup_healing_capacity,
    speedup_training_capacity,
)
from inventory.models import (
    InventoryReportPayload,
    InventoryReportView,
)
from player_self_service import visual_contract

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"
CARD_ASSET_DIR = ASSET_DIR / "Inventory" / "cards"
ICON_ASSET_DIR = ASSET_DIR / "Inventory" / "icons"

WIDTH = 1400
HEIGHT = 980
BG = (12, 48, 96)
PANEL = (5, 8, 20, 222)
PANEL_2 = (8, 12, 28, 232)
TEXT = visual_contract.TEXT
MUTED = visual_contract.MUTED
GREEN = visual_contract.GREEN
RED = visual_contract.RED
GOLD = visual_contract.GOLD
GRID = (78, 89, 121, 205)
AXIS = (173, 184, 216)
PANEL_OUTLINE = visual_contract.PANEL_EDGE
SEPARATOR = visual_contract.PANEL_EDGE
CHART_FILL_ALPHA = 6
CHART_MAX_DATE_LABELS = 6
RESOURCE_ACCENT = (96, 204, 120)
SPEEDUP_ACCENT = (50, 190, 222)
MATERIAL_ACCENT = (255, 139, 61)
RESOURCE_CHART_COLORS = {
    "Food": (82, 196, 113),
    "Wood": (181, 116, 62),
    "Stone": (156, 163, 175),
    "Gold": (245, 180, 52),
}
MATERIAL_CHART_COLORS = {
    "Bone": (205, 213, 223),
    "Leather": (255, 104, 48),
    "Ebony": (224, 96, 221),
    "Iron": (27, 173, 224),
    "Choice Chests": (255, 207, 0),
}

REPORT_BACKDROP_PATHS = {
    InventoryReportView.RESOURCES: (CARD_ASSET_DIR / "inventory_resources_governoros_backdrop.png"),
    InventoryReportView.SPEEDUPS: (CARD_ASSET_DIR / "inventory_speedups_governoros_backdrop.png"),
    InventoryReportView.MATERIALS: (CARD_ASSET_DIR / "inventory_materials_governoros_backdrop.png"),
}

REPORT_ACCENTS = {
    InventoryReportView.RESOURCES: RESOURCE_ACCENT,
    InventoryReportView.SPEEDUPS: SPEEDUP_ACCENT,
    InventoryReportView.MATERIALS: MATERIAL_ACCENT,
}

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RenderedInventoryImage:
    filename: str
    image_bytes: BytesIO


def _report_canvas(view: InventoryReportView) -> Image.Image:
    """Load an approved production backdrop or return the legacy-safe background."""

    path = REPORT_BACKDROP_PATHS[view]
    try:
        with Image.open(path) as source:
            if source.size != (WIDTH, HEIGHT):
                raise ValueError(
                    f"Inventory backdrop must be {WIDTH}x{HEIGHT}; received {source.size}"
                )
            return source.convert("RGBA")
    except (OSError, ValueError, UnidentifiedImageError):
        logger.warning(
            "inventory_report_backdrop_unavailable view=%s path=%s",
            view.value,
            path,
            exc_info=True,
        )
        return Image.new("RGBA", (WIDTH, HEIGHT), BG)


@lru_cache(maxsize=32)
def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return visual_text.font(size, bold=bold)


def _compact(value: int | float | None, suffix: str = "") -> str:
    rendered = visual_contract.format_compact_number(value)
    return rendered if rendered == visual_contract.MISSING_VALUE else f"{rendered}{suffix}"


def _delta_text(
    delta: int | float | None, *, days: bool = False
) -> tuple[str, tuple[int, int, int, int]]:
    if delta is None:
        return visual_contract.MISSING_VALUE, MUTED
    sign = "+" if delta > 0 else ""
    if days:
        return f"{sign}{int(round(delta)):,}d", GREEN if delta >= 0 else RED
    return visual_contract.format_compact_number(delta, signed=True), GREEN if delta >= 0 else RED


def _paste_icon(canvas: Image.Image, path: Path, box: tuple[int, int, int, int]) -> None:
    if not path.exists():
        return
    try:
        with Image.open(path) as source:
            icon = source.convert("RGBA")
        icon.thumbnail((box[2] - box[0], box[3] - box[1]), Image.Resampling.LANCZOS)
        corners = (
            icon.getpixel((0, 0)),
            icon.getpixel((max(icon.width - 1, 0), 0)),
            icon.getpixel((0, max(icon.height - 1, 0))),
            icon.getpixel((max(icon.width - 1, 0), max(icon.height - 1, 0))),
        )

        def is_light_neutral(pixel: tuple[int, ...]) -> bool:
            rgb = pixel[:3]
            return min(rgb) >= 235 and max(rgb) - min(rgb) <= 8

        if sum(is_light_neutral(pixel) for pixel in corners) >= 3:
            pixels = icon.load()
            for y in range(icon.height):
                for x in range(icon.width):
                    pixel = pixels[x, y]
                    if is_light_neutral(pixel):
                        pixels[x, y] = (*pixel[:3], 0)
        x = box[0] + ((box[2] - box[0]) - icon.width) // 2
        y = box[1] + ((box[3] - box[1]) - icon.height) // 2
        canvas.alpha_composite(icon, (x, y))
    except Exception:
        return


def _draw_header(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    title: str,
    logo: Path,
    governor_name: str,
    governor_id: int,
    range_key: str,
    avatar_bytes: bytes | None,
) -> None:
    avatar_drawn = False
    if avatar_bytes:
        try:
            with Image.open(BytesIO(avatar_bytes)) as source:
                avatar = ImageOps.fit(
                    ImageOps.exif_transpose(source).convert("RGBA"),
                    (72, 72),
                    method=Image.Resampling.LANCZOS,
                )
            mask = Image.new("L", avatar.size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 71, 71), fill=255)
            canvas.paste(avatar, (44, 32), mask)
            draw.ellipse((42, 30, 118, 106), outline=PANEL_OUTLINE, width=2)
            avatar_drawn = True
        except Exception:
            pass
    if not avatar_drawn:
        _paste_icon(canvas, logo, (44, 32, 116, 104))
    _draw_text(draw, (132, 36), title, fill=TEXT, font=_font(38, bold=True), bold=True)
    context = f"{governor_name} ({governor_id})  |  Range {range_key}"
    context_font = _fit_font(
        draw,
        context,
        max_width=1210,
        size=21,
        min_size=14,
    )
    _draw_text(
        draw,
        (132, 82),
        context,
        fill=MUTED,
        font=context_font,
    )


def _panel(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    fill=PANEL,
    *,
    accent: tuple[int, int, int] | None = None,
) -> None:
    draw.rounded_rectangle(xy, radius=16, fill=fill, outline=PANEL_OUTLINE, width=2)
    if accent is not None:
        x1, y1, _x2, y2 = xy
        draw.rounded_rectangle(
            (x1 + 14, y1 + 15, x1 + 23, y2 - 15),
            radius=5,
            fill=(*accent, 245),
        )


def _text_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    *,
    bold: bool = False,
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
    return visual_text.fit_font(
        draw,
        text,
        max_width=max_width,
        size=size,
        min_size=min_size,
        bold=bold,
    )


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    *,
    fill: tuple[int, int, int] | tuple[int, int, int, int],
    font: ImageFont.ImageFont,
    bold: bool = False,
) -> None:
    visual_text.draw_text(draw, (int(xy[0]), int(xy[1])), text, fill=fill, font=font, bold=bold)


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int = 2,
    bold: bool = False,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or _text_width(draw, candidate, font, bold=bold) <= max_width:
            current = candidate
            continue
        lines.append(current)
        current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and words:
        lines[-1] = visual_text.fit_text_to_width(
            draw,
            lines[-1],
            width=max_width,
            base_font=font,
            bold=bold,
        )
    return lines or [text]


def _draw_kpi(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    *,
    title: str,
    value: str,
    delta: str,
    delta_color: tuple[int, int, int],
    icon: Path | None = None,
    accent: tuple[int, int, int] | None = None,
) -> None:
    _panel(draw, xy, accent=accent)
    x1, y1, x2, y2 = xy
    content_x = x1 + 34 if accent else x1 + 20
    content_w = x2 - content_x - 18
    if icon:
        _paste_icon(canvas, icon, (content_x, y1 + 14, content_x + 48, y1 + 62))
        title_x = content_x + 58
        title_w = x2 - title_x - 18
    else:
        title_x = content_x
        title_w = content_w
    title_font = _fit_font(draw, title, max_width=title_w, size=19, min_size=13, bold=True)
    value_font = _fit_font(draw, value, max_width=content_w, size=36, min_size=24, bold=True)
    delta_font = _fit_font(draw, delta, max_width=content_w, size=21, min_size=11, bold=True)
    _draw_text(draw, (title_x, y1 + 20), title, fill=MUTED, font=title_font, bold=True)
    value_xy = (content_x, y1 + 68)
    _draw_text(draw, value_xy, value, fill=TEXT, font=value_font, bold=True)
    value_box = draw.textbbox(value_xy, value, font=value_font)
    separator_y = min(max(value_box[3] + 14, y1 + 108), y2 - 36)
    draw.line((content_x, separator_y, x2 - 18, separator_y), fill=SEPARATOR, width=1)
    max_delta_lines = 1 if _text_width(draw, delta, delta_font, bold=True) <= content_w else 2
    delta_line_step = max(14, int(getattr(delta_font, "size", 12)) + 3)
    for idx, line in enumerate(
        _wrap_text(
            draw,
            delta,
            font=delta_font,
            max_width=content_w,
            max_lines=max_delta_lines,
            bold=True,
        )
    ):
        _draw_text(
            draw,
            (content_x, separator_y + 7 + (idx * delta_line_step)),
            line,
            fill=delta_color,
            font=delta_font,
            bold=True,
        )


def _draw_empty_kpi(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    *,
    title: str,
    icon: Path | None = None,
    accent: tuple[int, int, int] | None = None,
) -> None:
    _panel(draw, xy, fill=(7, 10, 23, 210), accent=accent)
    x1, y1, x2, y2 = xy
    content_x = x1 + 34 if accent else x1 + 20
    if icon:
        _paste_icon(canvas, icon, (content_x, y1 + 14, content_x + 48, y1 + 62))
        title_x = content_x + 58
    else:
        title_x = content_x
    title_font = _fit_font(
        draw,
        title,
        max_width=x2 - title_x - 18,
        size=19,
        min_size=13,
        bold=True,
    )
    _draw_text(draw, (title_x, y1 + 20), title, fill=MUTED, font=title_font, bold=True)
    _draw_text(draw, (content_x, y1 + 66), "—", fill=(131, 136, 157), font=_font(32))
    separator_y = min(y1 + 108, y2 - 38)
    draw.line((content_x, separator_y, x2 - 18, separator_y), fill=SEPARATOR, width=1)
    _draw_text(
        draw,
        (content_x, separator_y + 10),
        "Not recorded",
        fill=(131, 136, 157),
        font=_font(17),
    )


def _render_empty_report(
    payload: InventoryReportPayload,
    *,
    title: str,
    report_label: str,
    logo: Path,
    filename: str,
    kpis: list[tuple[tuple[int, int, int, int], str, Path | None]],
    chart_xy: tuple[int, int, int, int],
    avatar_bytes: bytes | None,
    view: InventoryReportView,
) -> RenderedInventoryImage:
    canvas = _report_canvas(view)
    draw = ImageDraw.Draw(canvas, "RGBA")
    accent = REPORT_ACCENTS[view]
    _draw_header(
        canvas,
        draw,
        title=title,
        logo=logo,
        governor_name=payload.governor_name,
        governor_id=payload.governor_id,
        range_key=payload.range_key.value,
        avatar_bytes=avatar_bytes,
    )
    for xy, kpi_title, icon in kpis:
        _draw_empty_kpi(canvas, draw, xy, title=kpi_title, icon=icon, accent=accent)

    _panel(draw, chart_xy, fill=PANEL_2)
    x1, y1, x2, y2 = chart_xy
    for idx in range(1, 5):
        y = y1 + ((y2 - y1) * idx / 5)
        draw.line((x1 + 48, y, x2 - 48, y), fill=GRID, width=1)

    overlay_w = min(860, x2 - x1 - 96)
    overlay_h = min(224, y2 - y1 - 64)
    overlay_x1 = x1 + ((x2 - x1 - overlay_w) // 2)
    overlay_y1 = y1 + ((y2 - y1 - overlay_h) // 2)
    overlay = (overlay_x1, overlay_y1, overlay_x1 + overlay_w, overlay_y1 + overlay_h)
    draw.rounded_rectangle(
        overlay,
        radius=18,
        fill=(7, 10, 23, 238),
        outline=PANEL_OUTLINE,
        width=2,
    )
    heading = f"{visual_contract.NO_DATA} • No approved {report_label} data recorded"
    heading_font = _fit_font(
        draw,
        heading,
        max_width=overlay_w - 72,
        size=32,
        min_size=24,
        bold=True,
    )
    heading_width = _text_width(draw, heading, heading_font, bold=True)
    _draw_text(
        draw,
        (overlay_x1 + ((overlay_w - heading_width) / 2), overlay_y1 + 34),
        heading,
        fill=TEXT,
        font=heading_font,
        bold=True,
    )
    guidance = "Upload a matching Inventory screenshot to start this report."
    guidance_width = _text_width(draw, guidance, _font(22))
    _draw_text(
        draw,
        (overlay_x1 + ((overlay_w - guidance_width) / 2), overlay_y1 + 92),
        guidance,
        fill=MUTED,
        font=_font(22),
    )
    action = "Use /inventory import or upload in the Inventory channel"
    action_width = _text_width(draw, action, _font(20, bold=True), bold=True)
    _draw_text(
        draw,
        (overlay_x1 + ((overlay_w - action_width) / 2), overlay_y1 + 142),
        action,
        fill=GOLD,
        font=_font(20, bold=True),
        bold=True,
    )
    return _export(
        canvas,
        filename,
        payload=payload,
        source_label="NO DATA • Waiting for an approved inventory import",
    )


def _chart_ticks(min_v: float, max_v: float, *, count: int = 5) -> list[float]:
    if count <= 1:
        return [max_v]
    if max_v == min_v:
        step = max(abs(max_v) * 0.25, 1.0)
        min_v -= step * 2
        max_v += step * 2
    span = max_v - min_v
    return [min_v + (span * idx / (count - 1)) for idx in range(count)]


def _axis_label(value: float, *, suffix: str = "") -> str:
    return _compact(value, suffix=suffix)


def _date_axis_label(label: str) -> str:
    text = str(label)
    if len(text) >= 10 and text[4:5] == "-" and text[7:8] == "-":
        return text[5:10]
    return text[:10]


def _series_values(series: dict[str, list[float]]) -> list[float]:
    if not series:
        return []
    return [max(float(value), 0.0) for values in series.values() for value in values]


def _chart_date_indices(point_count: int, *, max_labels: int = CHART_MAX_DATE_LABELS) -> list[int]:
    """Return evenly spaced upload indices for readable date labels."""

    if point_count <= 0 or max_labels <= 0:
        return []
    if point_count <= max_labels:
        return list(range(point_count))
    if max_labels == 1:
        return [0]
    return sorted(
        {round(label_idx * (point_count - 1) / (max_labels - 1)) for label_idx in range(max_labels)}
    )


def _chart_marker_radius(point_count: int) -> int:
    if point_count <= 12:
        return 5
    if point_count <= 31:
        return 4
    if point_count <= 60:
        return 3
    return 2


def _draw_data_marker(
    draw: ImageDraw.ImageDraw,
    point: tuple[float, float],
    color: tuple[int, int, int],
    *,
    radius: int,
) -> None:
    x, y = (round(point[0]), round(point[1]))
    draw.polygon(
        ((x, y - radius), (x + radius, y), (x, y + radius), (x - radius, y)),
        fill=color,
        outline=PANEL_2[:3],
        width=1 if radius <= 2 else 2,
    )


def _line_chart(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    series: dict[str, list[float]],
    labels: list[str],
    colors: list[tuple[int, int, int]],
    *,
    y_suffix: str = "",
) -> None:
    _panel(draw, xy, fill=PANEL_2)
    x1, y1, x2, y2 = xy
    visible_values = _series_values(series)
    if len(labels) < 2 or not visible_values:
        _draw_text(
            draw,
            (x1 + 24, y1 + 26),
            "Trend graph unavailable",
            fill=MUTED,
            font=_font(22),
        )
        return

    min_v = 0.0
    max_v = max(visible_values)
    if max_v <= 0:
        max_v = 1.0
    span = max_v
    plot = (x1 + 96, y1 + 42, x2 - 42, y2 - 78)
    ticks = _chart_ticks(min_v, max_v)
    for tick in ticks:
        y = plot[3] - ((tick - min_v) / span) * (plot[3] - plot[1])
        draw.line((plot[0], y, plot[2], y), fill=GRID, width=1)
        label = _axis_label(tick, suffix=y_suffix)
        _draw_text(draw, (x1 + 20, y - 9), label, fill=AXIS, font=_font(16))
    draw.line((plot[0], plot[1], plot[0], plot[3]), fill=AXIS, width=2)
    draw.line((plot[0], plot[3], plot[2], plot[3]), fill=AXIS, width=2)

    date_font = _font(16)
    for idx in _chart_date_indices(len(labels)):
        x = plot[0] + (plot[2] - plot[0]) * idx / max(len(labels) - 1, 1)
        draw.line((x, plot[3], x, plot[3] + 6), fill=AXIS, width=1)
        date_label = _date_axis_label(labels[idx])
        label_width = _text_width(draw, date_label, date_font)
        _draw_text(
            draw,
            (x - (label_width / 2), plot[3] + 12),
            date_label,
            fill=AXIS,
            font=date_font,
        )

    series_with_colors = list(zip(series.items(), colors, strict=False))
    fill_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    fill_draw = ImageDraw.Draw(fill_layer, "RGBA")
    for (_name, values), color in sorted(
        series_with_colors,
        key=lambda item: max(item[0][1]) if item[0][1] else 0,
        reverse=True,
    ):
        pts = []
        for idx, val in enumerate(values):
            x = plot[0] + (plot[2] - plot[0]) * idx / max(len(values) - 1, 1)
            y = plot[3] - (max(float(val), 0.0) / span) * (plot[3] - plot[1])
            pts.append((x, y))
        if len(pts) >= 2:
            area = [(pts[0][0], plot[3]), *pts, (pts[-1][0], plot[3])]
            fill_draw.polygon(area, fill=(*color[:3], CHART_FILL_ALPHA))
    canvas.alpha_composite(fill_layer)
    for (_name, values), color in series_with_colors:
        pts = []
        for idx, val in enumerate(values):
            x = plot[0] + (plot[2] - plot[0]) * idx / max(len(values) - 1, 1)
            y = plot[3] - (max(float(val), 0.0) / span) * (plot[3] - plot[1])
            pts.append((x, y))
        if len(pts) >= 2:
            draw.line(pts, fill=color, width=4)
        marker_radius = _chart_marker_radius(len(pts))
        for point in pts:
            _draw_data_marker(draw, point, color, radius=marker_radius)
    legend_x = plot[0]
    for name, color in zip(series.keys(), colors, strict=False):
        draw.rounded_rectangle((legend_x, y2 - 42, legend_x + 22, y2 - 22), radius=4, fill=color)
        _draw_text(draw, (legend_x + 30, y2 - 46), name, fill=TEXT, font=_font(18))
        legend_x += 180


def _latest_delta(points: list[Any], attr: str) -> tuple[float | int, float | int | None]:
    latest = points[-1]
    latest_value = getattr(latest, attr)
    if len(points) < 2:
        return latest_value, None
    earliest = points[0]
    return latest_value, latest_value - getattr(earliest, attr)


def _aware(value: Any) -> Any:
    if getattr(value, "tzinfo", None) is None and hasattr(value, "replace"):
        return value.replace(tzinfo=UTC)
    return value


def render_resources_report(
    payload: InventoryReportPayload, *, avatar_bytes: bytes | None = None
) -> RenderedInventoryImage | None:
    if not payload.resources:
        if payload.view != InventoryReportView.RESOURCES:
            return None
        box_w = 250
        kpis = [
            (
                (44 + idx * (box_w + 16), 140, 44 + idx * (box_w + 16) + box_w, 284),
                title,
                icon,
            )
            for idx, (title, icon) in enumerate(
                [
                    ("Food", ICON_ASSET_DIR / "RSS" / "food.png"),
                    ("Wood", ICON_ASSET_DIR / "RSS" / "wood.png"),
                    ("Stone", ICON_ASSET_DIR / "RSS" / "stone.png"),
                    ("Gold", ICON_ASSET_DIR / "RSS" / "gold.png"),
                    ("Total RSS", ICON_ASSET_DIR / "RSS" / "total.png"),
                ]
            )
        ]
        kpis.extend(
            (
                (44 + idx * 330, 314, 344 + idx * 330, 470),
                title,
                icon,
            )
            for idx, (title, icon) in enumerate(
                [
                    ("RSS Velocity", None),
                    (
                        "RSS Troop Training Capacity",
                        ICON_ASSET_DIR / "Speedups" / "Training.png",
                    ),
                    (
                        "RSS Troop Healing Capacity",
                        ICON_ASSET_DIR / "Speedups" / "healing.png",
                    ),
                    ("RSS Forecast", None),
                ]
            )
        )
        return _render_empty_report(
            payload,
            view=InventoryReportView.RESOURCES,
            title="Resources Inventory",
            report_label="Resources",
            logo=ASSET_DIR / "rss_logo.png",
            filename=f"inventory_resources_{payload.governor_id}_{payload.range_key.value}.png",
            kpis=kpis,
            chart_xy=(44, 510, 1356, 924),
            avatar_bytes=avatar_bytes,
        )
    canvas = _report_canvas(InventoryReportView.RESOURCES)
    draw = ImageDraw.Draw(canvas, "RGBA")
    _draw_header(
        canvas,
        draw,
        title="Resources Inventory",
        logo=ASSET_DIR / "rss_logo.png",
        governor_name=payload.governor_name,
        governor_id=payload.governor_id,
        range_key=payload.range_key.value,
        avatar_bytes=avatar_bytes,
    )
    latest = payload.resources[-1]
    attrs = [
        ("Food", "food", ICON_ASSET_DIR / "RSS" / "food.png"),
        ("Wood", "wood", ICON_ASSET_DIR / "RSS" / "wood.png"),
        ("Stone", "stone", ICON_ASSET_DIR / "RSS" / "stone.png"),
        ("Gold", "gold", ICON_ASSET_DIR / "RSS" / "gold.png"),
        ("Total RSS", "total", ICON_ASSET_DIR / "RSS" / "total.png"),
    ]
    box_w = 250
    for idx, (title, attr, icon) in enumerate(attrs):
        value, delta = _latest_delta(payload.resources, attr)
        delta_label, color = _delta_text(delta)
        _draw_kpi(
            canvas,
            draw,
            (44 + idx * (box_w + 16), 140, 44 + idx * (box_w + 16) + box_w, 284),
            title=title,
            value=_compact(value),
            delta=delta_label,
            delta_color=color,
            icon=icon,
            accent=RESOURCE_ACCENT,
        )

    total_latest, total_delta = _latest_delta(payload.resources, "total")
    days = (
        max(
            (_aware(payload.resources[-1].scan_utc) - _aware(payload.resources[0].scan_utc)).days, 1
        )
        if len(payload.resources) >= 2
        else 0
    )
    velocity = (total_delta / days) if total_delta is not None and days else None
    velocity_text = (
        visual_contract.MISSING_VALUE if velocity is None else f"{velocity / 1_000_000:+.1f}M/day"
    )
    velocity_color = MUTED if velocity is None else (GREEN if velocity >= 0 else RED)

    vip_code = payload.governor_profile.vip_level_code if payload.governor_profile else None
    train_capacity = rss_training_capacity(latest)
    heal_capacity = rss_healing_capacity(latest, vip_code)
    forecast = None if velocity is None else total_latest + (velocity * 30)
    insight_boxes = [
        ("RSS Velocity", velocity_text, "range delta", None, velocity_color),
        (
            "RSS Troop Training Capacity",
            f"{train_capacity.troops_millions:,.1f}M troops",
            (
                f"Limit {train_capacity.limiting_resource} | "
                f"{train_capacity.power_millions:,.1f}M Power | "
                f"{train_capacity.mge_points_millions:,.1f}M MGE"
            ),
            ICON_ASSET_DIR / "Speedups" / "Training.png",
            TEXT,
        ),
        (
            "RSS Troop Healing Capacity",
            f"{heal_capacity.troops_millions:,.1f}M troops",
            (
                f"Limit {heal_capacity.limiting_resource} | "
                f"{heal_capacity.kills_millions or 0:,.1f}M kills | "
                f"{heal_capacity.kill_points_millions or 0:,.1f}M KP | "
                f"{heal_capacity.vip_note}"
            ),
            ICON_ASSET_DIR / "Speedups" / "healing.png",
            TEXT,
        ),
        ("RSS Forecast", _compact(forecast), "30 days", None, TEXT),
    ]
    for idx, (title, value, delta, icon, color) in enumerate(insight_boxes):
        _draw_kpi(
            canvas,
            draw,
            (44 + idx * 330, 314, 344 + idx * 330, 470),
            title=title,
            value=value,
            delta=delta,
            delta_color=color,
            icon=icon,
            accent=RESOURCE_ACCENT,
        )

    if len(payload.resources) >= 2:
        resource_series = {
            "Food": [float(p.food) for p in payload.resources],
            "Wood": [float(p.wood) for p in payload.resources],
            "Stone": [float(p.stone) for p in payload.resources],
            "Gold": [float(p.gold) for p in payload.resources],
        }
        _line_chart(
            canvas,
            draw,
            (44, 510, 1356, 924),
            resource_series,
            [str(p.scan_utc) for p in payload.resources],
            [RESOURCE_CHART_COLORS[name] for name in resource_series],
        )
    else:
        _draw_text(
            draw,
            (56, 526),
            "Latest approved scan only. Trend graph appears after a second approved scan.",
            fill=MUTED,
            font=_font(24),
        )

    return _export(
        canvas,
        f"inventory_resources_{payload.governor_id}_{payload.range_key.value}.png",
        payload=payload,
        uploaded_at_utc=latest.scan_utc,
    )


def render_speedups_report(
    payload: InventoryReportPayload, *, avatar_bytes: bytes | None = None
) -> RenderedInventoryImage | None:
    if not payload.speedups:
        if payload.view != InventoryReportView.SPEEDUPS:
            return None
        return _render_empty_report(
            payload,
            view=InventoryReportView.SPEEDUPS,
            title="Speedups Inventory",
            report_label="Speedups",
            logo=ASSET_DIR / "speedup_logo.png",
            filename=f"inventory_speedups_{payload.governor_id}_{payload.range_key.value}.png",
            kpis=[
                (
                    (60, 148, 440, 300),
                    "Universal",
                    ICON_ASSET_DIR / "Speedups" / "Universal.png",
                ),
                (
                    (490, 148, 870, 300),
                    "Training",
                    ICON_ASSET_DIR / "Speedups" / "Training.png",
                ),
                (
                    (920, 148, 1300, 300),
                    "Healing",
                    ICON_ASSET_DIR / "Speedups" / "healing.png",
                ),
                (
                    (140, 338, 650, 498),
                    "Total Speedup Training Capacity",
                    ICON_ASSET_DIR / "Speedups" / "Training.png",
                ),
                (
                    (750, 338, 1260, 498),
                    "Total Healing Speedup Capacity",
                    ICON_ASSET_DIR / "Speedups" / "healing.png",
                ),
            ],
            chart_xy=(44, 540, 1356, 924),
            avatar_bytes=avatar_bytes,
        )
    canvas = _report_canvas(InventoryReportView.SPEEDUPS)
    draw = ImageDraw.Draw(canvas, "RGBA")
    _draw_header(
        canvas,
        draw,
        title="Speedups Inventory",
        logo=ASSET_DIR / "speedup_logo.png",
        governor_name=payload.governor_name,
        governor_id=payload.governor_id,
        range_key=payload.range_key.value,
        avatar_bytes=avatar_bytes,
    )
    attrs = [
        (
            "Universal",
            "universal_days",
            ICON_ASSET_DIR / "Speedups" / "Universal.png",
        ),
        ("Training", "training_days", ICON_ASSET_DIR / "Speedups" / "Training.png"),
        ("Healing", "healing_days", ICON_ASSET_DIR / "Speedups" / "healing.png"),
    ]
    for idx, (title, attr, icon) in enumerate(attrs):
        value, delta = _latest_delta(payload.speedups, attr)
        delta_label, color = _delta_text(delta, days=True)
        _draw_kpi(
            canvas,
            draw,
            (60 + idx * 430, 148, 440 + idx * 430, 300),
            title=title,
            value=f"{int(round(value)):,}d",
            delta=delta_label,
            delta_color=color,
            icon=icon,
            accent=SPEEDUP_ACCENT,
        )

    latest = payload.speedups[-1]
    vip_code = payload.governor_profile.vip_level_code if payload.governor_profile else None
    train_capacity = speedup_training_capacity(latest, vip_code)
    heal_capacity = speedup_healing_capacity(latest, vip_code)
    capacity_boxes = [
        (
            "Total Speedup Training Capacity",
            f"{int(round(train_capacity.source_days)):,}d",
            (
                f"{train_capacity.troops or 0:,.0f} troops | "
                f"{train_capacity.power_millions or 0:,.1f}M Power | "
                f"{train_capacity.mge_points_millions or 0:,.1f}M MGE | "
                f"{train_capacity.vip_note}"
            ),
            ICON_ASSET_DIR / "Speedups" / "Training.png",
        ),
        (
            "Total Healing Speedup Capacity",
            f"{int(round(heal_capacity.source_days)):,}d",
            (
                f"{heal_capacity.healed_millions or 0:,.1f}m healed | "
                f"{heal_capacity.kills_millions or 0:,.1f}M kills | "
                f"{heal_capacity.kill_points_millions or 0:,.1f}M KP | "
                f"{heal_capacity.vip_note}"
            ),
            ICON_ASSET_DIR / "Speedups" / "healing.png",
        ),
    ]
    for idx, (title, value, detail, icon) in enumerate(capacity_boxes):
        _draw_kpi(
            canvas,
            draw,
            (140 + idx * 610, 338, 650 + idx * 610, 498),
            title=title,
            value=value,
            delta=detail,
            delta_color=TEXT,
            icon=icon,
            accent=SPEEDUP_ACCENT,
        )

    if len(payload.speedups) >= 2:
        _line_chart(
            canvas,
            draw,
            (44, 540, 1356, 924),
            {
                "Universal": [p.universal_days for p in payload.speedups],
                "Training": [p.training_days for p in payload.speedups],
                "Healing": [p.healing_days for p in payload.speedups],
            },
            [str(p.scan_utc) for p in payload.speedups],
            [(250, 204, 21), (96, 165, 250), (248, 113, 113)],
            y_suffix="d",
        )
    else:
        _draw_text(
            draw,
            (56, 560),
            "Latest approved scan only. Trend graph appears after a second approved scan.",
            fill=MUTED,
            font=_font(24),
        )
    return _export(
        canvas,
        f"inventory_speedups_{payload.governor_id}_{payload.range_key.value}.png",
        payload=payload,
        uploaded_at_utc=latest.scan_utc,
    )


def render_materials_report(
    payload: InventoryReportPayload, *, avatar_bytes: bytes | None = None
) -> RenderedInventoryImage | None:
    if not payload.materials:
        if payload.view != InventoryReportView.MATERIALS:
            return None
        box_w = 246
        return _render_empty_report(
            payload,
            view=InventoryReportView.MATERIALS,
            title="Materials Inventory",
            report_label="Materials",
            logo=ASSET_DIR / "materials_logo.png",
            filename=f"inventory_materials_{payload.governor_id}_{payload.range_key.value}.png",
            kpis=[
                (
                    (44 + idx * (box_w + 16), 144, 44 + idx * (box_w + 16) + box_w, 286),
                    title,
                    icon,
                )
                for idx, (title, icon) in enumerate(
                    [
                        ("Bone", ICON_ASSET_DIR / "Materials" / "bone.png"),
                        ("Leather", ICON_ASSET_DIR / "Materials" / "leather.png"),
                        ("Ebony", ICON_ASSET_DIR / "Materials" / "ebony.png"),
                        ("Iron", ICON_ASSET_DIR / "Materials" / "iron.png"),
                        (
                            "Choice Chests",
                            ICON_ASSET_DIR / "Materials" / "choicechest.png",
                        ),
                    ]
                )
            ]
            + [
                ((72, 326, 650, 474), "Total Legendary Materials", None),
                ((750, 326, 1328, 474), f"Net Change ({payload.range_key.value})", None),
            ],
            chart_xy=(44, 520, 1356, 924),
            avatar_bytes=avatar_bytes,
        )
    canvas = _report_canvas(InventoryReportView.MATERIALS)
    draw = ImageDraw.Draw(canvas, "RGBA")
    _draw_header(
        canvas,
        draw,
        title="Materials Inventory",
        logo=ASSET_DIR / "materials_logo.png",
        governor_name=payload.governor_name,
        governor_id=payload.governor_id,
        range_key=payload.range_key.value,
        avatar_bytes=avatar_bytes,
    )
    latest = payload.materials[-1]
    kpis = [
        (
            "Bone",
            latest.animal_bone_legendary,
            ICON_ASSET_DIR / "Materials" / "bone.png",
        ),
        (
            "Leather",
            latest.leather_legendary,
            ICON_ASSET_DIR / "Materials" / "leather.png",
        ),
        (
            "Ebony",
            latest.ebony_legendary,
            ICON_ASSET_DIR / "Materials" / "ebony.png",
        ),
        ("Iron", latest.iron_ore_legendary, ICON_ASSET_DIR / "Materials" / "iron.png"),
        (
            "Choice Chests",
            latest.choice_chest_legendary,
            ICON_ASSET_DIR / "Materials" / "choicechest.png",
        ),
    ]
    box_w = 246
    for idx, (title, value, icon) in enumerate(kpis):
        attr = {
            "Bone": "animal_bone_legendary",
            "Leather": "leather_legendary",
            "Ebony": "ebony_legendary",
            "Iron": "iron_ore_legendary",
            "Choice Chests": "choice_chest_legendary",
        }[title]
        _value, delta = _latest_delta(payload.materials, attr)
        delta_label, color = _delta_text(delta)
        _draw_kpi(
            canvas,
            draw,
            (44 + idx * (box_w + 16), 144, 44 + idx * (box_w + 16) + box_w, 286),
            title=title,
            value=f"{value:,.1f}",
            delta=delta_label,
            delta_color=color,
            icon=icon,
            accent=MATERIAL_ACCENT,
        )

    total_delta = (
        latest.total_legendary - payload.materials[0].total_legendary
        if len(payload.materials) >= 2
        else None
    )
    total_delta_label, total_delta_color = _delta_text(total_delta)
    _draw_kpi(
        canvas,
        draw,
        (72, 326, 650, 474),
        title="Total Legendary Materials",
        value=f"{latest.total_legendary:,.2f}",
        delta=total_delta_label,
        delta_color=total_delta_color,
        accent=MATERIAL_ACCENT,
    )
    _draw_kpi(
        canvas,
        draw,
        (750, 326, 1328, 474),
        title=f"Net Change ({payload.range_key.value})",
        value=total_delta_label,
        delta="range delta",
        delta_color=total_delta_color,
        accent=MATERIAL_ACCENT,
    )

    if len(payload.materials) >= 2:
        series = {
            "Bone": [p.animal_bone_legendary for p in payload.materials],
            "Leather": [p.leather_legendary for p in payload.materials],
            "Ebony": [p.ebony_legendary for p in payload.materials],
            "Iron": [p.iron_ore_legendary for p in payload.materials],
            "Choice Chests": [p.choice_chest_legendary for p in payload.materials],
        }
        _line_chart(
            canvas,
            draw,
            (44, 520, 1356, 924),
            series,
            [str(p.scan_utc) for p in payload.materials],
            [MATERIAL_CHART_COLORS[name] for name in series],
        )
    else:
        _draw_text(
            draw,
            (56, 548),
            "Only one approved Materials import is available. Add another approved import to show trends.",
            fill=MUTED,
            font=_font(24),
        )
    return _export(
        canvas,
        f"inventory_materials_{payload.governor_id}_{payload.range_key.value}.png",
        payload=payload,
        uploaded_at_utc=latest.scan_utc,
    )


def render_inventory_reports(
    payload: InventoryReportPayload, *, avatar_bytes: bytes | None = None
) -> list[RenderedInventoryImage]:
    rendered = [
        render_resources_report(payload, avatar_bytes=avatar_bytes),
        render_speedups_report(payload, avatar_bytes=avatar_bytes),
        render_materials_report(payload, avatar_bytes=avatar_bytes),
    ]
    return [item for item in rendered if item is not None]


def _export(
    canvas: Image.Image,
    filename: str,
    *,
    payload: InventoryReportPayload,
    uploaded_at_utc: Any | None = None,
    source_label: str | None = None,
) -> RenderedInventoryImage:
    generated = ImageDraw.Draw(canvas)
    uploaded_label = source_label
    if uploaded_label is None:
        uploaded_label = f"Inventory uploaded {_format_inventory_timestamp(uploaded_at_utc)}"
    _draw_text(
        generated,
        (44, 944),
        uploaded_label,
        fill=MUTED,
        font=_font(16),
    )
    _draw_text(
        generated,
        (1050, 944),
        f"Generated {_format_inventory_timestamp(payload.generated_at_utc)}",
        fill=MUTED,
        font=_font(16),
    )
    buf = BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return RenderedInventoryImage(filename=filename, image_bytes=buf)


def _format_inventory_timestamp(value: Any | None) -> str:
    if value is None:
        return visual_contract.MISSING_VALUE
    if isinstance(value, datetime):
        aware = value.replace(tzinfo=UTC) if value.tzinfo is None else value
        return visual_contract.format_utc_datetime(aware)
    return str(value)
