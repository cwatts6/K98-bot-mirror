from __future__ import annotations

import pytest

from event_calendar.reminder_prefs import (
    add_event_type_bucket,
    add_offsets_for_event_type,
    clear_event_types,
    clear_offsets_for_event_type,
    default_prefs,
    normalize_prefs,
    remove_event_type_bucket,
    remove_offsets_for_event_type,
    set_enabled,
)


def test_add_multiple_types_and_remove_one():
    known = {"egg", "mge", "20gh"}
    prefs = default_prefs()

    prefs = add_event_type_bucket(prefs, event_type="egg", known_event_types=known)
    prefs = add_event_type_bucket(prefs, event_type="mge", known_event_types=known)
    prefs = add_event_type_bucket(prefs, event_type="20gh", known_event_types=known)

    assert set(prefs["by_event_type"].keys()) == {"egg", "mge", "20gh"}

    prefs = remove_event_type_bucket(prefs, event_type="mge", known_event_types=known)
    assert set(prefs["by_event_type"].keys()) == {"egg", "20gh"}


def test_add_multiple_offsets_and_remove_one():
    known = {"egg", "mge", "20gh"}
    prefs = set_enabled(default_prefs(), True)

    prefs = add_offsets_for_event_type(
        prefs, event_type="egg", offsets=["24h"], known_event_types=known
    )
    prefs = add_offsets_for_event_type(
        prefs, event_type="egg", offsets=["1h"], known_event_types=known
    )
    prefs = add_offsets_for_event_type(
        prefs, event_type="egg", offsets=["start"], known_event_types=known
    )

    assert prefs["by_event_type"]["egg"] == ["1h", "24h", "start"]

    prefs = remove_offsets_for_event_type(
        prefs, event_type="egg", offsets=["1h"], known_event_types=known
    )
    assert prefs["by_event_type"]["egg"] == ["24h", "start"]


def test_all_type_is_exclusive():
    known = {"egg", "mge"}
    prefs = default_prefs()

    prefs = add_event_type_bucket(prefs, event_type="egg", known_event_types=known)
    prefs = add_event_type_bucket(prefs, event_type="all", known_event_types=known)
    assert set(prefs["by_event_type"].keys()) == {"all"}

    prefs = add_event_type_bucket(prefs, event_type="mge", known_event_types=known)
    assert set(prefs["by_event_type"].keys()) == {"mge"}


def test_invalid_type_rejected():
    known = {"egg", "mge"}
    with pytest.raises(ValueError):
        add_event_type_bucket(default_prefs(), event_type="unknown", known_event_types=known)


def test_clear_helpers():
    known = {"egg", "mge"}
    prefs = default_prefs()
    prefs = add_offsets_for_event_type(
        prefs, event_type="egg", offsets=["all"], known_event_types=known
    )
    assert "egg" in prefs["by_event_type"]

    prefs = clear_offsets_for_event_type(prefs, event_type="egg", known_event_types=known)
    assert "egg" not in prefs["by_event_type"]

    prefs = add_event_type_bucket(prefs, event_type="mge", known_event_types=known)
    prefs = clear_event_types(prefs)
    assert prefs["by_event_type"] == {}


def test_backward_compat_normalize_shape():
    raw = {"enabled": True, "by_event_type": {"egg": ["24h", "24h", "start"]}}
    out = normalize_prefs(raw)
    assert out["enabled"] is True
    assert out["by_event_type"]["egg"] == ["24h", "start"]
