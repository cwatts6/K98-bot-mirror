from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from inventory.models import (
    InventoryReportPayload,
    InventoryResourcePoint,
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


@dataclass(frozen=True)
class RenderedInventoryImage:
    filename: str
    image_bytes: BytesIO


@lru_cache(maxsize=32)
def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
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
    draw.text((132, 40), title, fill=TEXT, font=_font(34, bold=True))
    draw.text(
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
    x1, y1, x2, _ = xy
    if icon:
        _paste_icon(canvas, icon, (x1 + 16, y1 + 18, x1 + 62, y1 + 64))
        title_x = x1 + 72
    else:
        title_x = x1 + 20
    draw.text((title_x, y1 + 20), title, fill=MUTED, font=_font(18, bold=True))
    draw.text((x1 + 20, y1 + 68), value, fill=TEXT, font=_font(34, bold=True))
    draw.text((x1 + 20, y1 + 112), delta, fill=delta_color, font=_font(20, bold=True))
    draw.line((x1 + 18, y1 + 104, x2 - 18, y1 + 104), fill=(65, 127, 187), width=1)


def _line_chart(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    series: dict[str, list[float]],
    labels: list[str],
    colors: list[tuple[int, int, int]],
) -> None:
    _panel(draw, xy, fill=(9, 36, 78))
    x1, y1, x2, y2 = xy
    all_values = [v for values in series.values() for v in values]
    if len(labels) < 2 or not all_values:
        draw.text((x1 + 24, y1 + 26), "Trend graph unavailable", fill=MUTED, font=_font(22))
        return

    min_v = min(all_values)
    max_v = max(all_values)
    span = max(max_v - min_v, 1)
    plot = (x1 + 70, y1 + 42, x2 - 42, y2 - 62)
    for i in range(5):
        y = plot[3] - (plot[3] - plot[1]) * i / 4
        draw.line((plot[0], y, plot[2], y), fill=(31, 83, 139), width=1)

    for (name, values), color in zip(series.items(), colors, strict=False):
        pts = []
        for idx, val in enumerate(values):
            x = plot[0] + (plot[2] - plot[0]) * idx / max(len(values) - 1, 1)
            y = plot[3] - ((val - min_v) / span) * (plot[3] - plot[1])
            pts.append((x, y))
        if len(pts) >= 2:
            area = [(pts[0][0], plot[3]), *pts, (pts[-1][0], plot[3])]
            draw.polygon(area, fill=(*color[:3], 58))
            draw.line(pts, fill=color, width=4)
    legend_x = plot[0]
    for name, color in zip(series.keys(), colors, strict=False):
        draw.rounded_rectangle((legend_x, y2 - 42, legend_x + 22, y2 - 22), radius=4, fill=color)
        draw.text((legend_x + 30, y2 - 46), name, fill=TEXT, font=_font(17))
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


def _capacity(point: InventoryResourcePoint, costs: dict[str, int]) -> tuple[float, str]:
    capacities = {
        "Food": point.food / costs["food"],
        "Wood": point.wood / costs["wood"],
        "Stone": point.stone / costs["stone"],
        "Gold": point.gold / costs["gold"],
    }
    limiting = min(capacities, key=capacities.get)
    return int(capacities[limiting] * 10) / 10, limiting


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

    train_cap, train_limit = _capacity(
        latest,
        {"food": 533_000_000, "wood": 533_000_000, "stone": 400_000_000, "gold": 400_000_000},
    )
    heal_cap, heal_limit = _capacity(
        latest,
        {"food": 213_300_000, "wood": 213_300_000, "stone": 160_000_000, "gold": 160_000_000},
    )
    forecast = None if velocity is None else total_latest + (velocity * 30)
    insight_boxes = [
        ("RSS Velocity", velocity_text, "range delta", None, velocity_color),
        (
            "RSS Troop Training Capacity",
            f"{train_cap:,.1f}m troops",
            f"Limit {train_limit} | {train_cap * 10:,.1f}m Power | {train_cap * 100:,.1f}m MGE",
            ASSET_DIR / "Training" / "Training.png",
            TEXT,
        ),
        (
            "RSS Troop Healing Capacity",
            f"{heal_cap:,.1f}m troops",
            f"Limit {heal_limit} | {heal_cap * 5:,.1f}m kills | {heal_cap * 20:,.1f}m KP",
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
        _line_chart(
            draw,
            (44, 510, 1356, 924),
            {
                "Food": [float(p.food) for p in payload.resources],
                "Wood": [float(p.wood) for p in payload.resources],
                "Stone": [float(p.stone) for p in payload.resources],
                "Gold": [float(p.gold) for p in payload.resources],
            },
            [str(p.scan_utc) for p in payload.resources],
            [(74, 222, 128), (250, 204, 21), (148, 163, 184), (251, 191, 36)],
        )
    else:
        draw.text(
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
    training_total = latest.training_days + latest.universal_days
    healing_total = latest.healing_days + latest.universal_days
    train_scale = training_total / 100
    heal_scale = healing_total / 100
    capacity_boxes = [
        (
            "Total Speedup Training Capacity",
            f"{int(round(training_total)):,}d",
            f"{train_scale * 136_000:,.0f} troops | {train_scale * 1.36:,.1f}m Power | {train_scale * 13.6:,.1f}m MGE",
            ASSET_DIR / "Training" / "Training.png",
        ),
        (
            "Total Healing Speedup Capacity",
            f"{int(round(healing_total)):,}d",
            f"{heal_scale * 6.1:,.1f}m healed | {heal_scale * 6.1:,.1f}m kills | {heal_scale * 122:,.1f}m KP",
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
            draw,
            (44, 540, 1356, 924),
            {
                "Universal": [p.universal_days for p in payload.speedups],
                "Training": [p.training_days for p in payload.speedups],
                "Healing": [p.healing_days for p in payload.speedups],
            },
            [str(p.scan_utc) for p in payload.speedups],
            [(250, 204, 21), (96, 165, 250), (248, 113, 113)],
        )
    else:
        draw.text(
            (56, 560),
            "Latest approved scan only. Trend graph appears after a second approved scan.",
            fill=MUTED,
            font=_font(24),
        )
    return _export(
        canvas, f"inventory_speedups_{payload.governor_id}_{payload.range_key.value}.png"
    )


def render_inventory_reports(
    payload: InventoryReportPayload, *, avatar_bytes: bytes | None = None
) -> list[RenderedInventoryImage]:
    rendered = [
        render_resources_report(payload, avatar_bytes=avatar_bytes),
        render_speedups_report(payload, avatar_bytes=avatar_bytes),
    ]
    return [item for item in rendered if item is not None]


def _export(canvas: Image.Image, filename: str) -> RenderedInventoryImage:
    generated = ImageDraw.Draw(canvas)
    generated.text(
        (44, 944),
        "Generated from approved inventory imports",
        fill=MUTED,
        font=_font(16),
    )
    generated.text(
        (1110, 944),
        f"{datetime.now(UTC):%Y-%m-%d %H:%M UTC}",
        fill=MUTED,
        font=_font(16),
    )
    buf = BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return RenderedInventoryImage(filename=filename, image_bytes=buf)
