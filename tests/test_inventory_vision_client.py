from __future__ import annotations

import json
import subprocess
import sys

import pytest

from services.vision_client import InventoryVisionClient, InventoryVisionConfig


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
    payloads = [
        {
            "detected_image_type": "resources",
            "confidence_score": 0.96,
            "warnings": [],
            "values": {"Food": {"from_items": 7000000000, "total": 8000000000}},
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
    assert result.values["Food"]["from_items"] == 7000000000
    assert result.model == "gpt-4.1-mini"
    assert not result.fallback_used
    assert len(calls) == 1
    assert calls[0]["model"] == "gpt-4.1-mini"


@pytest.mark.asyncio
async def test_low_confidence_escalates_to_fallback_model():
    calls = []
    payloads = [
        {
            "detected_image_type": "speedups",
            "confidence_score": 0.72,
            "warnings": ["Some values were hard to read."],
            "values": {"Universal": {"total_minutes": 1440}},
        },
        {
            "detected_image_type": "speedups",
            "confidence_score": 0.94,
            "warnings": [],
            "values": {"Universal": {"total_minutes": 2880}},
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
    assert result.values["Universal"]["total_minutes"] == 2880
    assert [call["model"] for call in calls] == ["gpt-4.1-mini", "gpt-5.2"]


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
