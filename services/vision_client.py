from __future__ import annotations

import base64
from collections.abc import Callable
from dataclasses import dataclass, field
from inspect import isawaitable
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_FALLBACK_CONFIDENCE_THRESHOLD = 0.90


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
                "additionalProperties": True,
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
        "For resources, extract Food, Wood, Stone, Gold, From Items, and Total Resources "
        "as integer quantities after expanding K/M/B suffixes. "
        "For speedups, extract Building, Research, Training, Healing, and Universal "
        "speedups as total_minutes where possible. "
        "Use warnings for missing rows, unreadable values, low confidence, or mismatched "
        "image type. If the image is not readable, use detected_image_type unknown and "
        "a confidence_score below 0.70."
    )


def _image_data_url(image_bytes: bytes, content_type: str | None) -> str:
    mime = (content_type or "image/png").strip() or "image/png"
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime};base64,{encoded}"


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
            error=(
                "Vision response JSON missing required field(s): "
                + ", ".join(missing_keys)
            ),
        )

    detected_raw = payload.get("detected_image_type")
    if not isinstance(detected_raw, str) or not detected_raw.strip():
        return InventoryVisionResult(
            ok=False,
            model=model,
            prompt_version=prompt_version,
            fallback_used=fallback_used,
            error=(
                "Vision response field 'detected_image_type' must be a non-empty string."
            ),
        )

    detected = detected_raw.strip().lower()
    allowed_detected_types = {"unknown", "photo", "screenshot"}
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
                "Vision response field 'values' must be a dict "
                f"(got {type(values).__name__})."
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

        primary = await self._analyse_with_model(
            self.config.model,
            image_bytes,
            filename=filename,
            content_type=content_type,
            import_type_hint=import_type_hint,
            fallback_used=False,
        )
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
        if fallback.ok and fallback.confidence_score >= primary.confidence_score:
            return fallback
        return primary

    def _should_try_fallback(self, result: InventoryVisionResult) -> bool:
        if result.fallback_used:
            return False
        if not result.ok:
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
                        "content": [
                            {
                                "type": "input_text",
                                "text": _build_prompt(import_type_hint, self.config.prompt_version),
                            },
                            {
                                "type": "input_image",
                                "image_url": _image_data_url(image_bytes, content_type),
                            },
                        ],
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
