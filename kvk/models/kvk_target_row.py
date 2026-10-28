from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
import math
from typing import Any

_CANONICAL_FIELDS = frozenset(
    {
        "GovernorID",
        "GovernorName",
        "Power",
        "DKP_Target",
        "Kill_Target",
        "Deads_Target",
        "Min_Kill_Target",
        "TargetRank",
        "KVK_NO",
    }
)


class TargetRowContractError(ValueError):
    """A SQL or cache target row did not satisfy the canonical row contract."""


def _required_fields(row: Mapping[str, Any]) -> None:
    missing = sorted(_CANONICAL_FIELDS.difference(row))
    if missing:
        raise TargetRowContractError(
            f"Target row is missing required fields: {', '.join(missing)}."
        )


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or isinstance(value, float):
        raise TargetRowContractError(f"Target row contained an invalid {field}.")
    if isinstance(value, int):
        converted = value
    elif isinstance(value, str) and value.strip().isdigit():
        converted = int(value.strip())
    else:
        raise TargetRowContractError(f"Target row contained an invalid {field}.")
    if converted <= 0:
        raise TargetRowContractError(f"Target row contained an invalid {field}.")
    return converted


def _optional_nonnegative_int(value: Any, field: str) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        raise TargetRowContractError(f"Target row contained an invalid {field}.")
    if isinstance(value, int):
        converted = value
    elif isinstance(value, float):
        if not math.isfinite(value) or not value.is_integer():
            raise TargetRowContractError(f"Target row contained an invalid {field}.")
        converted = int(value)
    elif isinstance(value, Decimal):
        if not value.is_finite() or value != value.to_integral_value():
            raise TargetRowContractError(f"Target row contained an invalid {field}.")
        converted = int(value)
    elif isinstance(value, str) and value.strip().isdigit():
        converted = int(value.strip())
    else:
        raise TargetRowContractError(f"Target row contained an invalid {field}.")
    if converted < 0:
        raise TargetRowContractError(f"Target row contained an invalid {field}.")
    return converted


def _optional_int(value: Any, field: str) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        raise TargetRowContractError(f"Target row contained an invalid {field}.")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isfinite(value) and value.is_integer():
            return int(value)
        raise TargetRowContractError(f"Target row contained an invalid {field}.")
    if isinstance(value, Decimal):
        if value.is_finite() and value == value.to_integral_value():
            return int(value)
        raise TargetRowContractError(f"Target row contained an invalid {field}.")
    if isinstance(value, str):
        normalized = value.strip()
        digits = normalized[1:] if normalized[:1] in ("+", "-") else normalized
        if digits.isdigit():
            return int(normalized)
    raise TargetRowContractError(f"Target row contained an invalid {field}.")


def _power(value: Any) -> int | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return None
    try:
        return int(str(value).replace(",", "").replace(" ", ""))
    except (TypeError, ValueError, OverflowError):
        return None


@dataclass(frozen=True, slots=True)
class TargetRow:
    governor_id: str
    governor_name: str
    power: int | None
    dkp_target: int | None
    kill_target: int | None
    deads_target: int | None
    min_kill_target: int | None
    target_rank: int | None
    kvk_no: int


def target_row_from_mapping(
    row: Mapping[str, Any],
    *,
    expected_kvk_no: int | None = None,
) -> TargetRow:
    """Parse the canonical SQL/cache row shape without accepting legacy aliases."""
    _required_fields(row)
    governor_id = str(_positive_int(row["GovernorID"], "GovernorID"))
    kvk_no = _positive_int(row["KVK_NO"], "KVK_NO")
    if expected_kvk_no is not None and kvk_no != expected_kvk_no:
        raise TargetRowContractError("Target row KVK_NO did not match the requested KVK.")

    return TargetRow(
        governor_id=governor_id,
        governor_name=str(row["GovernorName"] or "").strip(),
        power=_power(row["Power"]),
        dkp_target=_optional_nonnegative_int(row["DKP_Target"], "DKP_Target"),
        kill_target=_optional_nonnegative_int(row["Kill_Target"], "Kill_Target"),
        deads_target=_optional_nonnegative_int(row["Deads_Target"], "Deads_Target"),
        min_kill_target=_optional_nonnegative_int(row["Min_Kill_Target"], "Min_Kill_Target"),
        target_rank=_optional_int(row["TargetRank"], "TargetRank"),
        kvk_no=kvk_no,
    )


def serialize_target_row(row: TargetRow) -> dict[str, Any]:
    """Return the stable schema-version-2 JSON representation for one target row."""
    return {
        "GovernorID": row.governor_id,
        "GovernorName": row.governor_name,
        "Power": row.power,
        "DKP_Target": row.dkp_target,
        "Kill_Target": row.kill_target,
        "Deads_Target": row.deads_target,
        "Min_Kill_Target": row.min_kill_target,
        "TargetRank": row.target_rank,
        "KVK_NO": row.kvk_no,
    }
