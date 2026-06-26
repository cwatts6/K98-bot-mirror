from __future__ import annotations

import asyncio
import logging

import pytest

from player_self_service import profile_preference_service as svc


def test_country_display_derives_name_from_two_letter_code() -> None:
    assert svc.country_display_name("GB") == "United Kingdom (GB)"
    assert svc.normalize_country("United Kingdom") == ("GB", None)
    assert svc.normalize_country("uk") == ("GB", None)


def test_language_display_derives_name_from_tag() -> None:
    assert svc.language_display_name("en-GB") == "English (en-GB)"
    assert svc.normalize_language("English") == ("en", None)
    assert svc.normalize_language("pt-br") == ("pt-BR", None)


def test_language_validation_rejects_non_tag_characters() -> None:
    value, error = svc.normalize_language("en-<@42>")
    assert value is None
    assert "not recognised" in str(error)


def test_timezone_validation_accepts_iana_name() -> None:
    assert svc.normalize_timezone("Europe/London") == ("Europe/London", None)
    value, error = svc.normalize_timezone("London")
    assert value is None
    assert "IANA timezone" in str(error)


@pytest.mark.asyncio
async def test_set_profile_preference_preserves_other_fields_and_writes_country() -> None:
    writes = []

    def reader(_user_id: int):
        return {
            "TimezoneName": "Europe/London",
            "LocationCountryCode": None,
            "PreferredLanguageTag": "en-GB",
        }

    def writer(**kwargs):
        writes.append(kwargs)

    result = await svc.set_profile_preference(
        42,
        "country",
        "United Kingdom",
        reader=reader,
        writer=writer,
    )

    assert result.ok is True
    assert result.profile is not None
    assert result.profile.location_country_code == "GB"
    assert result.message == "Location country saved as United Kingdom (GB)."
    assert writes == [
        {
            "discord_user_id": 42,
            "timezone_name": "Europe/London",
            "location_country_code": "GB",
            "preferred_language_tag": "en-GB",
            "updated_by_discord_user_id": 42,
        }
    ]


@pytest.mark.asyncio
async def test_clear_profile_preference_preserves_other_fields() -> None:
    writes = []

    def reader(_user_id: int):
        return {
            "TimezoneName": "Europe/London",
            "LocationCountryCode": "GB",
            "PreferredLanguageTag": "en-GB",
        }

    def writer(**kwargs):
        writes.append(kwargs)

    result = await svc.clear_profile_preference(42, "timezone", reader=reader, writer=writer)

    assert result.ok is True
    assert result.profile is not None
    assert result.profile.timezone_name is None
    assert result.profile.location_country_code == "GB"
    assert writes[0]["timezone_name"] is None
    assert writes[0]["location_country_code"] == "GB"
    assert writes[0]["preferred_language_tag"] == "en-GB"


@pytest.mark.asyncio
async def test_set_profile_preference_rejects_invalid_country_without_write() -> None:
    writes = []

    def reader(_user_id: int):
        return None

    def writer(**kwargs):
        writes.append(kwargs)

    result = await svc.set_profile_preference(
        42, "country", "Atlantis", reader=reader, writer=writer
    )

    assert result.ok is False
    assert "not recognised" in result.message
    assert writes == []


@pytest.mark.asyncio
async def test_set_profile_preference_rejects_invalid_timezone_without_write() -> None:
    writes = []

    def reader(_user_id: int):
        return None

    def writer(**kwargs):
        writes.append(kwargs)

    result = await svc.set_profile_preference(
        42, "timezone", "London", reader=reader, writer=writer
    )

    assert result.ok is False
    assert "IANA timezone" in result.message
    assert writes == []


@pytest.mark.asyncio
async def test_set_profile_preference_rejects_invalid_language_without_write() -> None:
    writes = []

    def reader(_user_id: int):
        return None

    def writer(**kwargs):
        writes.append(kwargs)

    result = await svc.set_profile_preference(
        42, "language", "en-<@42>", reader=reader, writer=writer
    )

    assert result.ok is False
    assert "not recognised" in result.message
    assert writes == []


@pytest.mark.asyncio
async def test_set_profile_preference_reports_writer_failure(caplog) -> None:
    def reader(_user_id: int):
        return None

    def writer(**_kwargs):
        raise RuntimeError("db down")

    caplog.set_level(logging.ERROR)

    result = await svc.set_profile_preference(
        42,
        "language",
        "English",
        reader=reader,
        writer=writer,
    )

    assert result.ok is False
    assert "could not be saved" in result.message
    assert "profile_preference_set_failed user_id=42 field=language" in caplog.text


@pytest.mark.asyncio
async def test_set_profile_preference_success_log_excludes_profile_value(caplog) -> None:
    def reader(_user_id: int):
        return None

    def writer(**_kwargs):
        return None

    caplog.set_level(logging.INFO)

    result = await svc.set_profile_preference(
        42,
        "country",
        "United Kingdom",
        reader=reader,
        writer=writer,
    )

    assert result.ok is True
    assert "profile_preference_saved user_id=42 field=country" in caplog.text
    assert "United Kingdom" not in caplog.text


@pytest.mark.asyncio
async def test_profile_preference_propagates_cancellation() -> None:
    def reader(_user_id: int):
        raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        await svc.set_profile_preference(42, "language", "English", reader=reader)
