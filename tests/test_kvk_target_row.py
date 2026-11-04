from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from kvk.models.kvk_target_row import (
    TargetRow,
    TargetRowContractError,
    serialize_target_row,
    target_row_from_mapping,
)


def _mapping(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "GovernorID": 2441482,
        "GovernorName": "  Governor One  ",
        "Power": "123,000,000",
        "DKP_Target": 50_000_000,
        "Kill_Target": 20_000_000,
        "Deads_Target": 1_000_000,
        "Min_Kill_Target": 5_000_000,
        "TargetRank": 4,
        "KVK_NO": 16,
    }
    row.update(overrides)
    return row


def test_target_row_is_immutable_and_round_trips_schema_version_two_shape():
    row = target_row_from_mapping(_mapping(), expected_kvk_no=16)

    assert row == TargetRow(
        governor_id="2441482",
        governor_name="Governor One",
        power=123_000_000,
        dkp_target=50_000_000,
        kill_target=20_000_000,
        deads_target=1_000_000,
        min_kill_target=5_000_000,
        target_rank=4,
        kvk_no=16,
    )
    assert target_row_from_mapping(serialize_target_row(row), expected_kvk_no=16) == row
    with pytest.raises(FrozenInstanceError):
        row.power = 1  # type: ignore[misc]


def test_target_row_preserves_nullable_targets_and_invalid_power_behavior():
    row = target_row_from_mapping(
        _mapping(
            Power="not a number",
            DKP_Target=None,
            Kill_Target=None,
            Deads_Target=None,
            Min_Kill_Target=None,
            TargetRank=None,
        )
    )

    assert row.power is None
    assert row.dkp_target is None
    assert row.kill_target is None
    assert row.deads_target is None
    assert row.min_kill_target is None
    assert row.target_rank is None


@pytest.mark.parametrize("target_rank", [0, -2, "+3", "-4"])
def test_target_row_preserves_exact_nullable_bigint_rank(target_rank: object):
    row = target_row_from_mapping(_mapping(TargetRank=target_rank))

    assert row.target_rank == int(target_rank)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("TargetRank", Decimal("4"), 4),
        ("TargetRank", 4.0, 4),
        ("DKP_Target", Decimal("50000000"), 50_000_000),
        ("Kill_Target", 20_000_000.0, 20_000_000),
    ],
)
def test_target_row_accepts_exact_integral_sql_numeric_values(
    field: str,
    value: object,
    expected: int,
):
    row = target_row_from_mapping(_mapping(**{field: value}))

    attribute = {
        "TargetRank": "target_rank",
        "DKP_Target": "dkp_target",
        "Kill_Target": "kill_target",
    }[field]
    assert getattr(row, attribute) == expected


def test_target_row_ignores_extra_publication_fields_but_requires_canonical_fields():
    row = target_row_from_mapping(_mapping(PublicationVersion=3))
    assert row.governor_id == "2441482"

    incomplete = _mapping()
    del incomplete["Kill_Target"]
    with pytest.raises(TargetRowContractError, match="Kill_Target"):
        target_row_from_mapping(incomplete)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("GovernorID", True),
        ("GovernorID", 2441482.0),
        ("GovernorID", 0),
        ("KVK_NO", 0),
        ("TargetRank", 1.5),
        ("TargetRank", Decimal("1.5")),
        ("TargetRank", float("inf")),
        ("DKP_Target", -1),
        ("DKP_Target", Decimal("NaN")),
        ("Kill_Target", 1.25),
        ("Deads_Target", True),
    ],
)
def test_target_row_rejects_lossy_or_invalid_integer_values(field: str, value: object):
    with pytest.raises(TargetRowContractError, match=field):
        target_row_from_mapping(_mapping(**{field: value}))


def test_target_row_rejects_cross_kvk_mapping():
    with pytest.raises(TargetRowContractError, match="requested KVK"):
        target_row_from_mapping(_mapping(KVK_NO=15), expected_kvk_no=16)
