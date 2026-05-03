from __future__ import annotations

import base64
from collections.abc import Callable
from dataclasses import dataclass, field
from inspect import isawaitable
import io
import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_FALLBACK_CONFIDENCE_THRESHOLD = 0.90
_SPEEDUP_DAY_TEXT_RE = re.compile(r"^\s*(\d[\d,]*)(?:\s*d\b.*)?$", re.IGNORECASE)


class VisionClientError(RuntimeError):
    """Raised when the vision service cannot produce a usable structured result."""


@dataclass(frozen=True)
class InventoryVisionConfig:
    api_key: str | None
    model: str
    fallback_model: str | None
    prompt_version: str
    fallback_confidence_threshold: float = DEFAULT_FALLBACK_CONFIDENCE_THRESHOLD


@dataclass(frozen=True)
class InventoryVisionResult:
    ok: bool
    detected_image_type: str = "unknown"
    values: dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    warnings: list[str] = field(default_factory=list)
    prompt_version: str = ""
    model: str = ""
    fallback_used: bool = False
    error: str | None = None
    raw_json: dict[str, Any] = field(default_factory=dict)


def default_config() -> InventoryVisionConfig:
    from bot_config import (
        OPENAI_API_KEY,
        OPENAI_VISION_FALLBACK_MODEL,
        OPENAI_VISION_MODEL,
        OPENAI_VISION_PROMPT_VERSION,
    )

    return InventoryVisionConfig(
        api_key=OPENAI_API_KEY,
        model=OPENAI_VISION_MODEL,
        fallback_model=OPENAI_VISION_FALLBACK_MODEL,
        prompt_version=OPENAI_VISION_PROMPT_VERSION,
    )


def build_inventory_vision_schema() -> dict[str, Any]:
    nullable_number = {"type": ["number", "null"]}
    nullable_integer = {"type": ["integer", "null"]}

    resource_row = {
        "type": "object",
        "additionalProperties": False,
        "required": ["from_items_value", "total_resources_value"],
        "properties": {
            "from_items_value": nullable_integer,
            "total_resources_value": nullable_integer,
        },
    }
    speedup_row = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "raw_duration_text",
            "day_digits_text",
            "day_digits_verification_text",
            "total_minutes",
            "total_hours",
            "total_days_decimal",
        ],
        "properties": {
            "raw_duration_text": {"type": ["string", "null"]},
            "day_digits_text": {"type": ["string", "null"]},
            "day_digits_verification_text": {"type": ["string", "null"]},
            "total_minutes": nullable_integer,
            "total_hours": nullable_number,
            "total_days_decimal": nullable_number,
        },
    }
    material_row = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "normal",
            "advanced",
            "elite",
            "epic",
            "legendary",
            "legendary_equivalent",
        ],
        "properties": {
            "normal": nullable_integer,
            "advanced": nullable_integer,
            "elite": nullable_integer,
            "epic": nullable_integer,
            "legendary": nullable_integer,
            "legendary_equivalent": nullable_number,
        },
    }

    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["detected_image_type", "confidence_score", "warnings", "values"],
        "properties": {
            "detected_image_type": {
                "type": "string",
                "enum": ["resources", "speedups", "materials", "unknown"],
            },
            "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
            "warnings": {"type": "array", "items": {"type": "string"}},
            "values": {
                "type": "object",
                "additionalProperties": False,
                "required": ["resources", "speedups", "materials"],
                "properties": {
                    "resources": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["food", "wood", "stone", "gold"],
                        "properties": {
                            "food": resource_row,
                            "wood": resource_row,
                            "stone": resource_row,
                            "gold": resource_row,
                        },
                    },
                    "speedups": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "building",
                            "research",
                            "training",
                            "healing",
                            "universal",
                        ],
                        "properties": {
                            "building": speedup_row,
                            "research": speedup_row,
                            "training": speedup_row,
                            "healing": speedup_row,
                            "universal": speedup_row,
                        },
                    },
                    "materials": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "choice_chests",
                            "leather",
                            "iron_ore",
                            "ebony",
                            "animal_bone",
                        ],
                        "properties": {
                            "choice_chests": material_row,
                            "leather": material_row,
                            "iron_ore": material_row,
                            "ebony": material_row,
                            "animal_bone": material_row,
                        },
                    },
                },
            },
        },
    }


def _build_prompt(import_type_hint: str | None, prompt_version: str) -> str:
    hint = import_type_hint or "unknown"
    return (
        "You are extracting Rise of Kingdoms inventory data from a screenshot. "
        f"Prompt version: {prompt_version}. "
        f"Expected import type hint: {hint}. "
        "Return only structured JSON matching the supplied schema. "
        "Classify the image as resources, speedups, materials, or unknown. "
        "Always include the resources, speedups, and materials objects required by the "
        "schema. Use null for fields that do not apply to the detected image type or "
        "cannot be read. For resources, extract food, wood, stone, and gold from-items "
        "and total-resources values as integer quantities after expanding K/M/B suffixes. "
        "For speedups, transcribe only the visible day token for Building, Research, "
        "Training, Healing, and Universal rows into raw_duration_text. "
        "For speedups, the request may include five separate labeled high-contrast OCR strip "
        "images instead of the full screenshot. Each labeled strip shows only one speedup "
        "row's black-on-white day token, such as '1,242d'. Use those labeled strip images "
        "as the source of truth. Preserve thousands separators and every leading digit. "
        "Then copy only the visible day digits immediately before the 'd' into day_digits_text, "
        "preserving commas if shown. Ignore hours and minutes for day_digits_text and calculations. "
        "After that, independently read only the same day digits again into "
        "day_digits_verification_text; do not copy the first answer. Compare "
        "raw_duration_text, day_digits_text, and day_digits_verification_text before returning. "
        "8 can look like 7, 5 can look like 3, and 2 can look like 1 in this UI, so zoom in "
        "mentally on the final digit of each day value. If the day reads disagree, add a warning "
        "for that row and set confidence_score below 0.90 so the fallback model can retry. "
        "For example, '1,242d 3h 35m' must have day_digits_text and "
        "day_digits_verification_text set to '1,242' and must be stored as 1242 days, with "
        "total_minutes set to 1788480, total_hours set to 29808, and total_days_decimal set "
        "to 1242. Do not drop the leading thousands digit or round down by one or two days. "
        "Use warnings for missing rows, unreadable values, low confidence, or mismatched "
        "image type. If the image is not readable, use detected_image_type unknown and "
        "a confidence_score below 0.70."
    )


def _image_data_url(image_bytes: bytes, content_type: str | None) -> str:
    mime = (content_type or "image/png").strip() or "image/png"
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _is_speedup_hint(import_type_hint: str | None) -> bool:
    return (import_type_hint or "").strip().lower() == "speedups"


def _speedup_duration_crop_data_url(image_bytes: bytes) -> str | None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None

    try:
        row_images = _speedup_day_token_crop_images(image_bytes)
        if not row_images:
            return None

        label_width = 260
        row_gap = 18
        row_height = max(crop.height for _, crop in row_images)
        canvas_width = label_width + max(crop.width for _, crop in row_images) + 32
        canvas_height = (row_height * len(row_images)) + (row_gap * (len(row_images) + 1))
        canvas = Image.new("RGB", (canvas_width, canvas_height), (12, 18, 28))
        draw = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype("arial.ttf", 38)
        except OSError:
            font = ImageFont.load_default()

        y = row_gap
        for label, crop in row_images:
            draw.text(
                (24, y + max(0, (row_height - 38) // 2)), label, fill=(255, 255, 255), font=font
            )
            canvas.paste(crop, (label_width, y + max(0, (row_height - crop.height) // 2)))
            y += row_height + row_gap

        output = io.BytesIO()
        canvas.save(output, format="PNG")
    except Exception:
        logger.debug("[inventory_vision] could not build speedup duration crop", exc_info=True)
        return None

    return _image_data_url(output.getvalue(), "image/png")


def _speedup_day_token_crop_data_urls(image_bytes: bytes) -> list[tuple[str, str]]:
    try:
        row_images = _speedup_day_token_crop_images(image_bytes)
    except Exception:
        logger.debug("[inventory_vision] could not build speedup token crops", exc_info=True)
        return []

    data_urls: list[tuple[str, str]] = []
    for label, crop in row_images:
        output = io.BytesIO()
        crop.save(output, format="PNG")
        data_urls.append((label, _image_data_url(output.getvalue(), "image/png")))
    return data_urls


def _speedup_day_token_crop_images(image_bytes: bytes) -> list[tuple[str, Any]]:
    try:
        from PIL import Image, ImageEnhance
    except ImportError:
        return []

    with Image.open(io.BytesIO(image_bytes)) as image:
        image = image.convert("RGB")
        width, height = image.size
        if width < 200 or height < 200:
            return []

        labels = ("Building", "Research", "Training", "Healing", "Universal")
        duration_x1 = int(width * 0.55)
        duration_x2 = int(width * 0.98)
        row_bounds = _detect_speedup_duration_row_bounds(image, duration_x1, duration_x2)
        if len(row_bounds) < len(labels):
            row_bounds = _fallback_speedup_duration_row_bounds(height)
        scale = 3
        row_images = []
        for label, (row_top, row_bottom) in zip(labels, row_bounds, strict=False):
            row_padding = max(24, int(height * 0.03))
            crop = image.crop(
                (
                    duration_x1,
                    max(0, row_top - row_padding),
                    duration_x2,
                    min(height, row_bottom + row_padding),
                )
            )
            crop = crop.resize(
                (crop.width * scale, crop.height * scale),
                Image.Resampling.LANCZOS,
            )
            crop = ImageEnhance.Contrast(crop).enhance(1.25)
            crop = ImageEnhance.Sharpness(crop).enhance(1.6)
            crop = _to_high_contrast_ocr_strip(crop)
            crop = _crop_first_dark_text_token(crop)
            row_images.append((label, crop))
    return row_images


def _detect_speedup_duration_row_bounds(
    image: Any, duration_x1: int, duration_x2: int
) -> list[tuple[int, int]]:
    gray = image.convert("L")
    width, height = gray.size
    pixels = gray.load()
    min_row_pixels = max(3, int((duration_x2 - duration_x1) * 0.015))
    bright_rows = []
    for y in range(int(height * 0.10), int(height * 0.93)):
        count = 0
        for x in range(duration_x1, duration_x2):
            if pixels[x, y] >= 150:
                count += 1
        if count >= min_row_pixels:
            bright_rows.append(y)

    if not bright_rows:
        return []

    row_groups: list[list[int]] = [[bright_rows[0], bright_rows[0]]]
    max_row_gap = max(3, int(height * 0.01))
    for y in bright_rows[1:]:
        if y - row_groups[-1][1] <= max_row_gap:
            row_groups[-1][1] = y
        else:
            row_groups.append([y, y])

    min_group_height = max(10, int(height * 0.015))
    candidates = []
    min_value_x = int(width * 0.60)
    for top, bottom in row_groups:
        if bottom - top < min_group_height or ((top + bottom) / 2) < height * 0.20:
            continue

        bright_x_values = [
            x
            for y in range(top, bottom + 1)
            for x in range(duration_x1, duration_x2)
            if pixels[x, y] >= 150
        ]
        if not bright_x_values or min(bright_x_values) < min_value_x:
            continue
        candidates.append((top, bottom))
    return candidates[:5]


def _fallback_speedup_duration_row_bounds(height: int) -> list[tuple[int, int]]:
    row_half_height = max(28, int(height * 0.038))
    return [
        (
            max(0, int(height * center_y_ratio) - row_half_height),
            min(height, int(height * center_y_ratio) + row_half_height),
        )
        for center_y_ratio in (0.355, 0.470, 0.585, 0.700, 0.815)
    ]


def _to_high_contrast_ocr_strip(image: Any) -> Any:
    from PIL import Image

    gray = image.convert("L")
    width, height = gray.size
    pixels = gray.load()
    threshold = 138
    bright_points: list[tuple[int, int]] = []
    for y in range(height):
        for x in range(width):
            if pixels[x, y] >= threshold:
                bright_points.append((x, y))
    if not bright_points:
        return image.convert("RGB")

    min_row_pixels = max(2, int(width * 0.01))
    bright_rows = []
    for y in range(height):
        count = 0
        for x in range(width):
            if pixels[x, y] >= threshold:
                count += 1
        if count >= min_row_pixels:
            bright_rows.append(y)

    if bright_rows:
        row_groups: list[list[int]] = [[bright_rows[0], bright_rows[0]]]
        max_row_gap = max(3, int(height * 0.025))
        for y in bright_rows[1:]:
            if y - row_groups[-1][1] <= max_row_gap:
                row_groups[-1][1] = y
            else:
                row_groups.append([y, y])
        main_group = max(row_groups, key=lambda group: group[1] - group[0])
        bright_points = [(x, y) for x, y in bright_points if main_group[0] <= y <= main_group[1]]

    min_x = max(0, min(x for x, _ in bright_points) - 18)
    max_x = min(width - 1, max(x for x, _ in bright_points) + 18)
    min_y = max(0, min(y for _, y in bright_points) - 18)
    max_y = min(height - 1, max(y for _, y in bright_points) + 18)
    gray = gray.crop((min_x, min_y, max_x + 1, max_y + 1))
    width, height = gray.size
    pixels = gray.load()
    margin_x = 36
    margin_y = 22
    output = Image.new("RGB", (width + (margin_x * 2), height + (margin_y * 2)), "white")
    output_pixels = output.load()
    for y in range(height):
        for x in range(width):
            if pixels[x, y] >= threshold:
                output_pixels[x + margin_x, y + margin_y] = (0, 0, 0)
    return output


def _crop_first_dark_text_token(image: Any) -> Any:
    gray = image.convert("L")
    width, height = gray.size
    pixels = gray.load()
    min_dark_pixels = max(2, int(height * 0.05))
    dark_columns = []
    for x in range(width):
        count = 0
        for y in range(height):
            if pixels[x, y] <= 80:
                count += 1
        if count >= min_dark_pixels:
            dark_columns.append(x)

    if not dark_columns:
        return image

    max_character_gap = max(20, int(width * 0.02))
    groups: list[list[int]] = [[dark_columns[0], dark_columns[0]]]
    for x in dark_columns[1:]:
        if x - groups[-1][1] <= max_character_gap:
            groups[-1][1] = x
        else:
            groups.append([x, x])

    token = groups[0]
    padding = max(18, int(width * 0.012))
    left = max(0, token[0] - padding)
    right = min(width, token[1] + padding)
    return image.crop((left, 0, right, height))


def _build_image_content(
    image_bytes: bytes,
    *,
    content_type: str | None,
    import_type_hint: str | None,
    prompt_version: str,
) -> list[dict[str, str]]:
    content = [
        {
            "type": "input_text",
            "text": _build_prompt(import_type_hint, prompt_version),
        }
    ]
    if _is_speedup_hint(import_type_hint):
        crop_urls = _speedup_day_token_crop_data_urls(image_bytes)
        if crop_urls:
            for label, crop_url in crop_urls:
                content.append({"type": "input_text", "text": f"{label} days-only crop:"})
                content.append({"type": "input_image", "image_url": crop_url})
            return content

    content.append(
        {
            "type": "input_image",
            "image_url": _image_data_url(image_bytes, content_type),
        }
    )
    return content


def _parse_speedup_day_text(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = _SPEEDUP_DAY_TEXT_RE.match(text)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def _has_speedup_day_text_disagreement(result: InventoryVisionResult) -> bool:
    if not result.ok or result.detected_image_type != "speedups":
        return False

    values = result.values.get("speedups") if isinstance(result.values, dict) else None
    if not isinstance(values, dict):
        return False

    for row in values.values():
        if not isinstance(row, dict):
            continue
        candidates = {
            candidate
            for candidate in (
                _parse_speedup_day_text(row.get("raw_duration_text")),
                _parse_speedup_day_text(row.get("day_digits_text")),
                _parse_speedup_day_text(row.get("day_digits_verification_text")),
            )
            if candidate is not None
        }
        if len(candidates) > 1:
            return True
    return False


def _extract_response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    if isinstance(response, dict):
        output_text = response.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text
        output = response.get("output", [])
    else:
        output = getattr(response, "output", [])

    chunks: list[str] = []
    for item in output or []:
        content = (
            item.get("content", []) if isinstance(item, dict) else getattr(item, "content", [])
        )
        for part in content or []:
            if isinstance(part, dict):
                text = part.get("text")
            else:
                text = getattr(part, "text", None)
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()


def _parse_result_payload(
    text: str, *, model: str, prompt_version: str, fallback_used: bool
) -> InventoryVisionResult:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return InventoryVisionResult(
            ok=False,
            model=model,
            prompt_version=prompt_version,
            fallback_used=fallback_used,
            error=f"Vision response was not valid JSON: {exc.msg}",
        )

    if not isinstance(payload, dict):
        return InventoryVisionResult(
            ok=False,
            model=model,
            prompt_version=prompt_version,
            fallback_used=fallback_used,
            error=f"Vision response JSON was not a dict (got {type(payload).__name__}).",
        )

    required_keys = ("detected_image_type", "confidence_score", "values")
    missing_keys = [key for key in required_keys if key not in payload]
    if missing_keys:
        return InventoryVisionResult(
            ok=False,
            model=model,
            prompt_version=prompt_version,
            fallback_used=fallback_used,
            error=("Vision response JSON missing required field(s): " + ", ".join(missing_keys)),
        )

    detected_raw = payload.get("detected_image_type")
    if not isinstance(detected_raw, str) or not detected_raw.strip():
        return InventoryVisionResult(
            ok=False,
            model=model,
            prompt_version=prompt_version,
            fallback_used=fallback_used,
            error=("Vision response field 'detected_image_type' must be a non-empty string."),
        )

    detected = detected_raw.strip().lower()
    allowed_detected_types = {"resources", "speedups", "materials", "unknown"}
    if detected not in allowed_detected_types:
        return InventoryVisionResult(
            ok=False,
            model=model,
            prompt_version=prompt_version,
            fallback_used=fallback_used,
            error=(
                "Vision response field 'detected_image_type' must be one of: "
                + ", ".join(sorted(allowed_detected_types))
                + f" (got {detected_raw!r})."
            ),
        )

    confidence_raw = payload.get("confidence_score")
    try:
        confidence = float(confidence_raw)
    except (TypeError, ValueError):
        return InventoryVisionResult(
            ok=False,
            model=model,
            prompt_version=prompt_version,
            fallback_used=fallback_used,
            error=(
                "Vision response field 'confidence_score' must be numeric "
                f"(got {type(confidence_raw).__name__})."
            ),
        )

    values = payload.get("values")
    if not isinstance(values, dict):
        return InventoryVisionResult(
            ok=False,
            model=model,
            prompt_version=prompt_version,
            fallback_used=fallback_used,
            error=(
                "Vision response field 'values' must be a dict " f"(got {type(values).__name__})."
            ),
        )

    required_values_sections = ("resources", "speedups", "materials")
    missing_sections = [key for key in required_values_sections if key not in values]
    if missing_sections:
        return InventoryVisionResult(
            ok=False,
            model=model,
            prompt_version=prompt_version,
            fallback_used=fallback_used,
            error=(
                "Vision response 'values' missing required section(s): "
                + ", ".join(missing_sections)
            ),
        )

    warnings_raw = payload.get("warnings") or []
    warnings = (
        [str(item) for item in warnings_raw]
        if isinstance(warnings_raw, list)
        else [str(warnings_raw)]
    )

    return InventoryVisionResult(
        ok=True,
        detected_image_type=detected,
        values=values,
        confidence_score=max(0.0, min(confidence, 1.0)),
        warnings=warnings,
        prompt_version=prompt_version,
        model=model,
        fallback_used=fallback_used,
        raw_json=payload,
    )


class InventoryVisionClient:
    def __init__(
        self,
        config: InventoryVisionConfig | None = None,
        *,
        client_factory: Callable[[str], Any] | None = None,
    ) -> None:
        self.config = config or default_config()
        self._client_factory = client_factory

    async def analyse_image(
        self,
        image_bytes: bytes,
        *,
        filename: str | None = None,
        content_type: str | None = None,
        import_type_hint: str | None = None,
    ) -> InventoryVisionResult:
        if not self.config.api_key:
            return InventoryVisionResult(
                ok=False,
                model=self.config.model,
                prompt_version=self.config.prompt_version,
                error="OPENAI_API_KEY is not configured.",
            )
        if not image_bytes:
            return InventoryVisionResult(
                ok=False,
                model=self.config.model,
                prompt_version=self.config.prompt_version,
                error="No image bytes were provided.",
            )

        if _is_speedup_hint(import_type_hint):
            speedup_model = self.config.fallback_model or self.config.model
            return await self._analyse_with_model(
                speedup_model,
                image_bytes,
                filename=filename,
                content_type=content_type,
                import_type_hint=import_type_hint,
                fallback_used=speedup_model != self.config.model,
            )

        primary = await self._analyse_with_model(
            self.config.model,
            image_bytes,
            filename=filename,
            content_type=content_type,
            import_type_hint=import_type_hint,
            fallback_used=False,
        )
        primary_has_day_disagreement = _has_speedup_day_text_disagreement(primary)
        if not self._should_try_fallback(primary):
            return primary

        fallback_model = self.config.fallback_model
        if not fallback_model or fallback_model == self.config.model:
            return primary

        logger.info(
            "[inventory_vision] escalating to fallback model=%s after primary model=%s "
            "confidence=%.3f ok=%s",
            fallback_model,
            self.config.model,
            primary.confidence_score,
            primary.ok,
        )
        fallback = await self._analyse_with_model(
            fallback_model,
            image_bytes,
            filename=filename,
            content_type=content_type,
            import_type_hint=import_type_hint,
            fallback_used=True,
        )
        if (
            primary_has_day_disagreement
            and fallback.ok
            and not _has_speedup_day_text_disagreement(fallback)
        ):
            return fallback
        if fallback.ok and fallback.confidence_score >= primary.confidence_score:
            return fallback
        return primary

    def _should_try_fallback(self, result: InventoryVisionResult) -> bool:
        if result.fallback_used:
            return False
        if not result.ok:
            return True
        if _has_speedup_day_text_disagreement(result):
            return True
        return result.confidence_score < self.config.fallback_confidence_threshold

    async def _analyse_with_model(
        self,
        model: str,
        image_bytes: bytes,
        *,
        filename: str | None,
        content_type: str | None,
        import_type_hint: str | None,
        fallback_used: bool,
    ) -> InventoryVisionResult:
        try:
            client = self._create_client()
            response_or_coro = client.responses.create(
                model=model,
                input=[
                    {
                        "role": "user",
                        "content": _build_image_content(
                            image_bytes,
                            content_type=content_type,
                            import_type_hint=import_type_hint,
                            prompt_version=self.config.prompt_version,
                        ),
                    }
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "inventory_vision_result",
                        "strict": True,
                        "schema": build_inventory_vision_schema(),
                    }
                },
            )
            response = await response_or_coro if isawaitable(response_or_coro) else response_or_coro
        except Exception as exc:
            logger.exception(
                "[inventory_vision] OpenAI vision request failed model=%s filename=%s",
                model,
                filename,
            )
            return InventoryVisionResult(
                ok=False,
                model=model,
                prompt_version=self.config.prompt_version,
                fallback_used=fallback_used,
                error=f"OpenAI vision request failed: {type(exc).__name__}",
            )

        text = _extract_response_text(response)
        if not text:
            return InventoryVisionResult(
                ok=False,
                model=model,
                prompt_version=self.config.prompt_version,
                fallback_used=fallback_used,
                error="OpenAI vision response did not include output text.",
            )
        return _parse_result_payload(
            text,
            model=model,
            prompt_version=self.config.prompt_version,
            fallback_used=fallback_used,
        )

    def _create_client(self) -> Any:
        if self._client_factory is not None:
            return self._client_factory(str(self.config.api_key))

        from openai import AsyncOpenAI

        return AsyncOpenAI(api_key=self.config.api_key)
