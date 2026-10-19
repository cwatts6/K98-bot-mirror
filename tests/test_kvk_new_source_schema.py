from dataclasses import FrozenInstanceError, fields

import pytest

from kvk.schemas.new_source_schema import (
    AGGREGATE_METRICS,
    CAMP_HEADERS,
    KINGDOM_HEADERS,
    PLAYER_HEADERS,
    ParseLimits,
    SourceValidationError,
    validate_headers,
)


def test_exact_schema_and_limits():
    assert len(PLAYER_HEADERS) == len(set(PLAYER_HEADERS)) == 36
    assert len(AGGREGATE_METRICS) == 8
    assert len(KINGDOM_HEADERS) == 10 and len(CAMP_HEADERS) == 9
    limits = ParseLimits()
    assert tuple(getattr(limits, f.name) for f in fields(limits)) == (
        20 * 1024**2,
        250 * 1024**2,
        100 * 1024**2,
        2000,
        200,
        50000,
        512,
        8,
        64,
        2000000,
        32767,
    )
    with pytest.raises(FrozenInstanceError):
        limits.max_camps = 9


@pytest.mark.parametrize("bad", [0, -1, True, 1.5, "20"])
def test_limits_reject_nonpositive_or_untyped(bad):
    with pytest.raises(ValueError):
        ParseLimits(max_entry_bytes=bad)


@pytest.mark.parametrize(
    "headers", [PLAYER_HEADERS[:-1], PLAYER_HEADERS + ("new",), ("Name",) + PLAYER_HEADERS[1:]]
)
def test_schema_rejects_missing_unknown_duplicate(headers):
    with pytest.raises(SourceValidationError, match="recognized"):
        validate_headers(headers, PLAYER_HEADERS)


def test_column_reordering_is_recognized():
    validate_headers(tuple(reversed(PLAYER_HEADERS)), PLAYER_HEADERS)
