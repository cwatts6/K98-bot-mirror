from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from services.vision_client import (
    InventoryVisionClient,
    InventoryVisionConfig,
    _detect_speedup_duration_row_bounds,
    _speedup_duration_crop_data_url,
    build_inventory_vision_schema,
)


class FakeResponses:
    def __init__(self, payloads, calls):
        self._payloads = payloads
        self._calls = calls

    def create(self, **kwargs):
        self._calls.append(kwargs)
        payload = self._payloads.pop(0)
        if isinstance(payload, Exception):
            raise payload
        return {"output_text": json.dumps(payload)}


class FakeClient:
    def __init__(self, payloads, calls):
        self.responses = FakeResponses(payloads, calls)


def _config(**overrides):
    values = {
        "api_key": "test-key",
        "model": "gpt-4.1-mini",
        "fallback_model": "gpt-5.2",
        "prompt_version": "inventory_vision_v1",
    }
    values.update(overrides)
    return InventoryVisionConfig(**values)


def _null_resource_row() -> dict:
    return {"from_items_value": None, "total_resources_value": None}


def _null_speedup_row() -> dict:
    return {
        "raw_duration_text": None,
        "day_digits_text": None,
        "day_digits_verification_text": None,
        "total_minutes": None,
        "total_hours": None,
        "total_days_decimal": None,
    }


def _null_material_row() -> dict:
    return {
        "normal": None,
        "advanced": None,
        "elite": None,
        "epic": None,
        "legendary": None,
        "legendary_equivalent": None,
    }


def _null_values() -> dict:
    return {
        "resources": {
            "food": _null_resource_row(),
            "wood": _null_resource_row(),
            "stone": _null_resource_row(),
            "gold": _null_resource_row(),
        },
        "speedups": {
            "building": _null_speedup_row(),
            "research": _null_speedup_row(),
            "training": _null_speedup_row(),
            "healing": _null_speedup_row(),
            "universal": _null_speedup_row(),
        },
        "materials": {
            "choice_chests": _null_material_row(),
            "leather": _null_material_row(),
            "iron_ore": _null_material_row(),
            "ebony": _null_material_row(),
            "animal_bone": _null_material_row(),
        },
    }


def _walk_schema_objects(schema):
    if isinstance(schema, dict):
        schema_type = schema.get("type")
        if schema_type == "object" or (isinstance(schema_type, list) and "object" in schema_type):
            yield schema
        for value in schema.values():
            yield from _walk_schema_objects(value)
    elif isinstance(schema, list):
        for item in schema:
            yield from _walk_schema_objects(item)


def test_schema_is_strict_for_openai_structured_outputs():
    schema = build_inventory_vision_schema()

    object_schemas = list(_walk_schema_objects(schema))

    assert object_schemas
    assert all(item.get("additionalProperties") is False for item in object_schemas)
    assert schema["properties"]["values"]["additionalProperties"] is False


@pytest.mark.asyncio
async def test_missing_api_key_returns_structured_error():
    client = InventoryVisionClient(_config(api_key=""))

    result = await client.analyse_image(b"fake image")

    assert not result.ok
    assert result.error == "OPENAI_API_KEY is not configured."
    assert result.model == "gpt-4.1-mini"


@pytest.mark.asyncio
async def test_primary_success_parses_structured_json_without_fallback():
    calls = []
    resources_values = _null_values()
    resources_values["resources"]["food"] = {
        "from_items_value": 7000000000,
        "total_resources_value": 8000000000,
    }
    payloads = [
        {
            "detected_image_type": "resources",
            "confidence_score": 0.96,
            "warnings": [],
            "values": resources_values,
        }
    ]

    client = InventoryVisionClient(
        _config(),
        client_factory=lambda _api_key: FakeClient(payloads, calls),
    )

    result = await client.analyse_image(
        b"fake image",
        filename="resources.png",
        content_type="image/png",
        import_type_hint="resources",
    )

    assert result.ok
    assert result.detected_image_type == "resources"
    assert result.confidence_score == 0.96
    assert result.values["resources"]["food"]["from_items_value"] == 7000000000
    assert result.model == "gpt-4.1-mini"
    assert not result.fallback_used
    assert len(calls) == 1
    assert calls[0]["model"] == "gpt-4.1-mini"


@pytest.mark.asyncio
async def test_speedups_use_fallback_model_as_first_pass_when_configured():
    calls = []
    speedups_fallback = _null_values()
    speedups_fallback["speedups"]["universal"] = {
        "raw_duration_text": "2d 0h 0m",
        "day_digits_text": "2",
        "day_digits_verification_text": "2",
        "total_minutes": 2880,
        "total_hours": 48.0,
        "total_days_decimal": 2.0,
    }
    payloads = [
        {
            "detected_image_type": "speedups",
            "confidence_score": 0.94,
            "warnings": [],
            "values": speedups_fallback,
        },
    ]

    client = InventoryVisionClient(
        _config(),
        client_factory=lambda _api_key: FakeClient(payloads, calls),
    )

    result = await client.analyse_image(b"fake image", import_type_hint="speedups")

    assert result.ok
    assert result.model == "gpt-5.2"
    assert result.fallback_used
    assert result.confidence_score == 0.94
    assert result.values["speedups"]["universal"]["total_minutes"] == 2880
    assert result.values["speedups"]["universal"]["raw_duration_text"] == "2d 0h 0m"
    assert result.values["speedups"]["universal"]["day_digits_text"] == "2"
    assert result.values["speedups"]["universal"]["day_digits_verification_text"] == "2"
    assert [call["model"] for call in calls] == ["gpt-5.2"]


@pytest.mark.asyncio
async def test_speedups_use_primary_model_when_no_fallback_is_configured():
    calls = []
    speedups = _null_values()
    speedups["speedups"]["universal"] = {
        "raw_duration_text": "2d 0h 0m",
        "day_digits_text": "2",
        "day_digits_verification_text": "2",
        "total_minutes": 2880,
        "total_hours": 48.0,
        "total_days_decimal": 2.0,
    }
    payloads = [
        {
            "detected_image_type": "speedups",
            "confidence_score": 0.94,
            "warnings": [],
            "values": speedups,
        },
    ]

    client = InventoryVisionClient(
        _config(fallback_model=None),
        client_factory=lambda _api_key: FakeClient(payloads, calls),
    )

    result = await client.analyse_image(b"fake image", import_type_hint="speedups")

    assert result.ok
    assert result.model == "gpt-4.1-mini"
    assert not result.fallback_used
    assert [call["model"] for call in calls] == ["gpt-4.1-mini"]


@pytest.mark.asyncio
async def test_speedup_prompt_requests_day_digits_text():
    calls = []
    payloads = [
        {
            "detected_image_type": "unknown",
            "confidence_score": 0.95,
            "warnings": [],
            "values": _null_values(),
        }
    ]
    client = InventoryVisionClient(
        _config(fallback_model=None),
        client_factory=lambda _api_key: FakeClient(payloads, calls),
    )

    await client.analyse_image(b"fake image", import_type_hint="speedups")

    prompt = calls[0]["input"][0]["content"][0]["text"]
    assert "day_digits_text" in prompt
    assert "day_digits_verification_text" in prompt
    assert "confidence_score below 0.90" in prompt


@pytest.mark.asyncio
async def test_speedup_import_sends_labeled_zoom_sheet():
    pytest.importorskip("PIL")
    from PIL import Image

    calls = []
    image_path = Path("downloads") / "test_speedup_crop.png"
    image_path.parent.mkdir(exist_ok=True)
    image = Image.new("RGB", (1200, 800), "navy")
    image.save(image_path)
    image_bytes = image_path.read_bytes()
    payloads = [
        {
            "detected_image_type": "unknown",
            "confidence_score": 0.95,
            "warnings": [],
            "values": _null_values(),
        }
    ]
    client = InventoryVisionClient(
        _config(fallback_model=None),
        client_factory=lambda _api_key: FakeClient(payloads, calls),
    )

    await client.analyse_image(image_bytes, content_type="image/png", import_type_hint="speedups")

    content = calls[0]["input"][0]["content"]
    image_parts = [item for item in content if item["type"] == "input_image"]
    text_parts = [item["text"] for item in content if item["type"] == "input_text"]
    assert len(image_parts) == 5
    assert all(item["image_url"].startswith("data:image/png;base64,") for item in image_parts)
    assert "Building day-token crop:" in text_parts
    assert "Universal day-token crop:" in text_parts


@pytest.mark.asyncio
async def test_speedup_import_falls_back_to_original_image_when_crops_fail(monkeypatch):
    calls = []
    payloads = [
        {
            "detected_image_type": "unknown",
            "confidence_score": 0.95,
            "warnings": [],
            "values": _null_values(),
        }
    ]
    monkeypatch.setattr("services.vision_client._speedup_day_token_crop_data_urls", lambda _: [])
    client = InventoryVisionClient(
        _config(fallback_model=None),
        client_factory=lambda _api_key: FakeClient(payloads, calls),
    )

    await client.analyse_image(b"fake image", content_type="image/png", import_type_hint="speedups")

    content = calls[0]["input"][0]["content"]
    image_parts = [item for item in content if item["type"] == "input_image"]
    assert len(image_parts) == 1


def test_speedup_duration_crop_rejects_invalid_image():
    assert _speedup_duration_crop_data_url(b"not an image") is None


def test_speedup_duration_row_detection_ignores_header_text():
    pytest.importorskip("PIL")
    from PIL import Image, ImageDraw

    image = Image.new("L", (1000, 800), 0)
    draw = ImageDraw.Draw(image)
    draw.rectangle((550, 150, 650, 170), fill=255)
    expected_rows = []
    for y in (260, 350, 440, 530, 620):
        draw.rectangle((700, y, 880, y + 22), fill=255)
        expected_rows.append((y, y + 22))

    rows = _detect_speedup_duration_row_bounds(image.convert("RGB"), 550, 980)

    assert rows == expected_rows


@pytest.mark.asyncio
async def test_api_failure_returns_structured_error():
    calls = []
    payloads = [RuntimeError("network down"), RuntimeError("still down")]

    client = InventoryVisionClient(
        _config(),
        client_factory=lambda _api_key: FakeClient(payloads, calls),
    )

    result = await client.analyse_image(b"fake image")

    assert not result.ok
    assert result.error == "OpenAI vision request failed: RuntimeError"
    assert result.model == "gpt-4.1-mini"
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_non_dict_json_response_returns_structured_error():
    """If the model returns valid JSON that is not a dict (e.g. a list), parsing should
    return a structured failure rather than raising AttributeError."""
    calls = []

    class _ListResponses:
        def __init__(self):
            self._calls = calls

        def create(self, **kwargs):
            self._calls.append(kwargs)
            return {"output_text": "[1, 2, 3]"}

    class _ListClient:
        def __init__(self):
            self.responses = _ListResponses()

    client = InventoryVisionClient(
        _config(fallback_model=None),
        client_factory=lambda _: _ListClient(),
    )

    result = await client.analyse_image(b"fake image")

    assert not result.ok
    assert result.error is not None
    assert "not a dict" in result.error
    assert result.model == "gpt-4.1-mini"


@pytest.mark.asyncio
async def test_fallback_lower_confidence_preserves_primary_result():
    """When the fallback model returns a lower confidence score than the primary, the
    primary result should be returned rather than the inferior fallback."""
    calls = []
    primary_values = _null_values()
    primary_values["resources"]["food"] = {
        "from_items_value": 1000,
        "total_resources_value": None,
    }
    fallback_values = _null_values()
    fallback_values["resources"]["food"] = {
        "from_items_value": 500,
        "total_resources_value": None,
    }
    payloads = [
        {
            "detected_image_type": "resources",
            "confidence_score": 0.89,  # just below 0.90 threshold -> fallback triggered
            "warnings": [],
            "values": primary_values,
        },
        {
            "detected_image_type": "resources",
            "confidence_score": 0.30,  # fallback produces worse result
            "warnings": ["very uncertain"],
            "values": fallback_values,
        },
    ]

    client = InventoryVisionClient(
        _config(),
        client_factory=lambda _api_key: FakeClient(payloads, calls),
    )

    result = await client.analyse_image(b"fake image", import_type_hint="resources")

    # Primary (0.89) should be kept over the weaker fallback (0.30)
    assert result.ok
    assert result.confidence_score == 0.89
    assert result.model == "gpt-4.1-mini"
    assert not result.fallback_used
    assert result.values["resources"]["food"]["from_items_value"] == 1000
    assert [call["model"] for call in calls] == ["gpt-4.1-mini", "gpt-5.2"]


def test_service_import_does_not_import_database_modules():
    code = (
        "import services.vision_client, sys; "
        "print('pyodbc' in sys.modules); "
        "print('constants' in sys.modules)"
    )

    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout.splitlines() == ["False", "False"]
