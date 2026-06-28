from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from core import visual_text
from inventory.capacity_calculations import (
    rss_healing_capacity,
    rss_training_capacity,
    speedup_healing_capacity,
    speedup_training_capacity,
)
from inventory.models import (
    InventoryReportPayload,
)

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"

WIDTH = 1400
HEIGHT = 980
BG = (12, 48, 96)
PANEL = (22, 74, 132)
PANEL_2 = (29, 91, 154)
TEXT = (245, 250, 255)
MUTED = (174, 205, 232)
GREEN = (73, 222, 128)
RED = (248, 113, 113)
GOLD = (250, 204, 21)
GRID = (31, 83, 139)
AXIS = (122, 168, 210)
CHART_FILL_ALPHA = 14
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


@dataclass(frozen=True)
class RenderedInventoryImage:
    filename: str
    image_bytes: BytesIO


@lru_cache(maxsize=32)
def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return visual_text.font(size, bold=bold)


def _compact(value: int | float | None, suffix: str = "") -> str:
    if value is None:
        return "N/A"
    val = float(value)
    abs_val = abs(val)
    for limit, unit in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if abs_val >= limit:
            out = f"{val / limit:.1f}".rstrip("0").rstrip(".")
            return f"{out}{unit}{suffix}"
    return f"{int(val):,}{suffix}"


def _delta_text(
    delta: int | float | None, *, days: bool = False
) -> tuple[str, tuple[int, int, int]]:
    if delta is None:
        return "N/A", MUTED
    sign = "+" if delta > 0 else ""
    if days:
        return f"{sign}{int(round(delta)):,}d", GREEN if delta >= 0 else RED
    return f"{sign}{_compact(delta)}", GREEN if delta >= 0 else RED


def _paste_icon(canvas: Image.Image, path: Path, box: tuple[int, int, int, int]) -> None:
    if not path.exists():
        return
    try:
        icon = Image.open(path).convert("RGBA")
        icon.thumbnail((box[2] - box[0], box[3] - box[1]), Image.Resampling.LANCZOS)
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
    _paste_icon(canvas, logo, (44, 32, 116, 104))
    _draw_text(draw, (132, 40), title, fill=TEXT, font=_font(34, bold=True), bold=True)
    _draw_text(
        draw,
        (132, 82),
        f"{governor_name} ({governor_id})  |  Range {range_key}",
        fill=MUTED,
        font=_font(20),
    )
    if avatar_bytes:
        try:
            avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA").resize((76, 76))
            canvas.alpha_composite(avatar, (1280, 34))
        except Exception:
            pass


def _panel(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], fill=PANEL) -> None:
    draw.rounded_rectangle(xy, radius=14, fill=fill, outline=(71, 139, 202), width=2)


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
) -> None:
    _panel(draw, xy)
    x1, y1, x2, y2 = xy
    content_w = x2 - x1 - 40
    if icon:
        _paste_icon(canvas, icon, (x1 + 16, y1 + 18, x1 + 62, y1 + 64))
        title_x = x1 + 72
        title_w = x2 - title_x - 18
    else:
        title_x = x1 + 20
        title_w = content_w
    title_font = _fit_font(draw, title, max_width=title_w, size=18, min_size=13, bold=True)
    value_font = _fit_font(draw, value, max_width=content_w, size=34, min_size=24, bold=True)
    delta_font = _fit_font(draw, delta, max_width=content_w, size=20, min_size=11, bold=True)
    _draw_text(draw, (title_x, y1 + 20), title, fill=MUTED, font=title_font, bold=True)
    value_xy = (x1 + 20, y1 + 68)
    _draw_text(draw, value_xy, value, fill=TEXT, font=value_font, bold=True)
    value_box = draw.textbbox(value_xy, value, font=value_font)
    separator_y = min(max(value_box[3] + 14, y1 + 108), y2 - 36)
    draw.line((x1 + 18, separator_y, x2 - 18, separator_y), fill=(65, 127, 187), width=1)
    max_delta_lines = 1 if _text_width(draw, delta, delta_font, bold=True) <= content_w else 2
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
            (x1 + 20, separator_y + 10 + (idx * 22)),
            line,
            fill=delta_color,
            font=delta_font,
            bold=True,
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
    _panel(draw, xy, fill=(9, 36, 78))
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
        _draw_text(draw, (x1 + 20, y - 9), label, fill=AXIS, font=_font(15))
    draw.line((plot[0], plot[1], plot[0], plot[3]), fill=AXIS, width=2)
    draw.line((plot[0], plot[3], plot[2], plot[3]), fill=AXIS, width=2)

    axis_indices = sorted({0, len(labels) // 2, len(labels) - 1})
    for idx in axis_indices:
        x = plot[0] + (plot[2] - plot[0]) * idx / max(len(labels) - 1, 1)
        draw.line((x, plot[3], x, plot[3] + 6), fill=AXIS, width=1)
        _draw_text(
            draw,
            (x - 24, plot[3] + 12),
            _date_axis_label(labels[idx]),
            fill=AXIS,
            font=_font(15),
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
    legend_x = plot[0]
    for name, color in zip(series.keys(), colors, strict=False):
        draw.rounded_rectangle((legend_x, y2 - 42, legend_x + 22, y2 - 22), radius=4, fill=color)
        _draw_text(draw, (legend_x + 30, y2 - 46), name, fill=TEXT, font=_font(17))
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
        return None
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), BG)
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
        ("Food", "food", ASSET_DIR / "RSS" / "food.png"),
        ("Wood", "wood", ASSET_DIR / "RSS" / "wood.png"),
        ("Stone", "stone", ASSET_DIR / "RSS" / "stone.png"),
        ("Gold", "gold", ASSET_DIR / "RSS" / "gold.png"),
        ("Total RSS", "total", ASSET_DIR / "RSS" / "total.png"),
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
    velocity_text = "N/A" if velocity is None else f"{velocity / 1_000_000:+.1f}m/day"
    velocity_color = MUTED if velocity is None else (GREEN if velocity >= 0 else RED)

    vip_code = payload.governor_profile.vip_level_code if payload.governor_profile else None
    train_capacity = rss_training_capacity(latest)
    heal_capacity = rss_healing_capacity(latest, vip_code)
    forecast = None if velocity is None else total_latest + (velocity * 30)
    insight_boxes = [
        ("RSS Velocity", velocity_text, "range delta", None, velocity_color),
        (
            "RSS Troop Training Capacity",
            f"{train_capacity.troops_millions:,.1f}m troops",
            (
                f"Limit {train_capacity.limiting_resource} | "
                f"{train_capacity.power_millions:,.1f}m Power | "
                f"{train_capacity.mge_points_millions:,.1f}m MGE"
            ),
            ASSET_DIR / "Training" / "Training.png",
            TEXT,
        ),
        (
            "RSS Troop Healing Capacity",
            f"{heal_capacity.troops_millions:,.1f}m troops",
            (
                f"Limit {heal_capacity.limiting_resource} | "
                f"{heal_capacity.kills_millions or 0:,.1f}m kills | "
                f"{heal_capacity.kill_points_millions or 0:,.1f}m KP | "
                f"{heal_capacity.vip_note}"
            ),
            ASSET_DIR / "healing" / "healing.png",
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
        canvas, f"inventory_resources_{payload.governor_id}_{payload.range_key.value}.png"
    )


def render_speedups_report(
    payload: InventoryReportPayload, *, avatar_bytes: bytes | None = None
) -> RenderedInventoryImage | None:
    if not payload.speedups:
        return None
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), BG)
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
        ("Universal", "universal_days", ASSET_DIR / "Universal" / "Universal.png"),
        ("Training", "training_days", ASSET_DIR / "Training" / "Training.png"),
        ("Healing", "healing_days", ASSET_DIR / "healing" / "healing.png"),
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
                f"{train_capacity.power_millions or 0:,.1f}m Power | "
                f"{train_capacity.mge_points_millions or 0:,.1f}m MGE | "
                f"{train_capacity.vip_note}"
            ),
            ASSET_DIR / "Training" / "Training.png",
        ),
        (
            "Total Healing Speedup Capacity",
            f"{int(round(heal_capacity.source_days)):,}d",
            (
                f"{heal_capacity.healed_millions or 0:,.1f}m healed | "
                f"{heal_capacity.kills_millions or 0:,.1f}m kills | "
                f"{heal_capacity.kill_points_millions or 0:,.1f}m KP | "
                f"{heal_capacity.vip_note}"
            ),
            ASSET_DIR / "healing" / "healing.png",
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
        canvas, f"inventory_speedups_{payload.governor_id}_{payload.range_key.value}.png"
    )


def render_materials_report(
    payload: InventoryReportPayload, *, avatar_bytes: bytes | None = None
) -> RenderedInventoryImage | None:
    if not payload.materials:
        return None
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), BG)
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
        ("Bone", latest.animal_bone_legendary),
        ("Leather", latest.leather_legendary),
        ("Ebony", latest.ebony_legendary),
        ("Iron", latest.iron_ore_legendary),
        ("Choice Chests", latest.choice_chest_legendary),
    ]
    box_w = 246
    for idx, (title, value) in enumerate(kpis):
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
    )
    _draw_kpi(
        canvas,
        draw,
        (750, 326, 1328, 474),
        title=f"Net Change ({payload.range_key.value})",
        value=total_delta_label,
        delta="range delta",
        delta_color=total_delta_color,
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
        canvas, f"inventory_materials_{payload.governor_id}_{payload.range_key.value}.png"
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


def _export(canvas: Image.Image, filename: str) -> RenderedInventoryImage:
    generated = ImageDraw.Draw(canvas)
    _draw_text(
        generated,
        (44, 944),
        "Generated from approved inventory imports",
        fill=MUTED,
        font=_font(16),
    )
    _draw_text(
        generated,
        (1110, 944),
        f"{datetime.now(UTC):%Y-%m-%d %H:%M UTC}",
        fill=MUTED,
        font=_font(16),
    )
    buf = BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return RenderedInventoryImage(filename=filename, image_bytes=buf)
