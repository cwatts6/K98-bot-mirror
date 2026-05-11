from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class KvkExportSectionSpec:
    name: str
    legacy_index: int
    required_columns: frozenset[str]


KVK_EXPORT_SECTION_SPECS: tuple[KvkExportSectionSpec, ...] = (
    KvkExportSectionSpec(
        "KVK_Scan_Log",
        0,
        frozenset(
            {
                "kvk_no",
                "scanid",
                "scantimestamputc",
                "sourcefilename",
                "row_count",
                "importedatutc",
                "uploaderdiscordid",
            }
        ),
    ),
    KvkExportSectionSpec(
        "KVK_Windows",
        1,
        frozenset(
            {
                "kvk_no",
                "windowname",
                "windowseq",
                "startscanid",
                "endscanid",
                "effectiveendscanid",
                "notes",
                "updatedatutc",
            }
        ),
    ),
    KvkExportSectionSpec(
        "KVK_DKP_Weights",
        2,
        frozenset({"kvk_no", "weightt4x", "weightt5y", "weightdeadsz", "effectivefromutc"}),
    ),
    KvkExportSectionSpec(
        "KVK_Player_Windowed",
        3,
        frozenset(
            {
                "kvk_no",
                "windowname",
                "governor_id",
                "name",
                "kingdom",
                "kp_gain",
                "kp_gain_recalc",
                "kills_gain",
                "t4_kills",
                "t5_kills",
                "kp_loss",
                "healed_troops",
                "deads",
                "max_contribute_gain",
                "cur_contribute_gain",
                "starting_power",
                "dkp",
                "last_scan_id",
                "computed_at_utc",
            }
        ),
    ),
    KvkExportSectionSpec(
        "KVK_Kingdom_Windowed",
        4,
        frozenset(
            {
                "kvk_no",
                "windowname",
                "kingdom",
                "camp_name",
                "kp_gain",
                "kills_gain",
                "t4_kills",
                "t5_kills",
                "kp_loss",
                "healed_troops",
                "deads",
                "max_contribute_gain",
                "cur_contribute_gain",
                "dkp",
                "last_scan_id",
                "computed_at_utc",
            }
        ),
    ),
    KvkExportSectionSpec(
        "KVK_Camp_Windowed",
        5,
        frozenset(
            {
                "kvk_no",
                "windowname",
                "camp_name",
                "kp_gain",
                "kills_gain",
                "t4_kills",
                "t5_kills",
                "kp_loss",
                "healed_troops",
                "deads",
                "max_contribute_gain",
                "cur_contribute_gain",
                "dkp",
                "last_scan_id",
                "computed_at_utc",
            }
        ),
    ),
    KvkExportSectionSpec(
        "KVK_Player_Full",
        6,
        frozenset(
            {
                "kvk_no",
                "windowname",
                "governor_id",
                "name",
                "kingdom",
                "kp_gain",
                "kp_gain_recalc",
                "kills_gain",
                "t4_kills",
                "t5_kills",
                "kp_loss",
                "healed_troops",
                "deads",
                "max_contribute_gain",
                "cur_contribute_gain",
                "starting_power",
                "dkp",
                "last_scan_id",
                "computed_at_utc",
            }
        ),
    ),
    KvkExportSectionSpec(
        "KVK_Kingdom_Full",
        7,
        frozenset(
            {
                "kvk_no",
                "windowname",
                "kingdom",
                "camp_name",
                "kp_gain",
                "kills_gain",
                "t4_kills",
                "t5_kills",
                "kp_loss",
                "healed_troops",
                "deads",
                "max_contribute_gain",
                "cur_contribute_gain",
                "dkp",
                "last_scan_id",
                "computed_at_utc",
            }
        ),
    ),
    KvkExportSectionSpec(
        "KVK_Camp_Full",
        8,
        frozenset(
            {
                "kvk_no",
                "windowname",
                "camp_name",
                "kp_gain",
                "kills_gain",
                "t4_kills",
                "t5_kills",
                "kp_loss",
                "healed_troops",
                "deads",
                "max_contribute_gain",
                "cur_contribute_gain",
                "dkp",
                "last_scan_id",
                "computed_at_utc",
            }
        ),
    ),
    KvkExportSectionSpec(
        "KVK_Ingest_Negatives",
        9,
        frozenset(
            {
                "kvk_no",
                "scanid",
                "governor_id",
                "name",
                "kingdom",
                "field_name",
                "value",
                "recorded_at_utc",
            }
        ),
    ),
)

KVK_EXPORT_SECTION_NAMES: tuple[str, ...] = tuple(spec.name for spec in KVK_EXPORT_SECTION_SPECS)
KVK_EXPORT_SECTION_BY_NAME: Mapping[str, KvkExportSectionSpec] = {
    spec.name: spec for spec in KVK_EXPORT_SECTION_SPECS
}


class KvkExportBindingError(ValueError):
    """Raised when SQL export result sets cannot be mapped to required KVK sections."""


def normalise_export_columns(df: pd.DataFrame) -> frozenset[str]:
    return frozenset(str(column).strip().lower() for column in df.columns)


def _matches_spec(df: pd.DataFrame, spec: KvkExportSectionSpec) -> bool:
    return spec.required_columns.issubset(normalise_export_columns(df))


def _window_name_values(df: pd.DataFrame) -> set[str]:
    window_column = next(
        (column for column in df.columns if str(column).strip().lower() == "windowname"),
        None,
    )
    if window_column is None or df.empty:
        return set()
    return {
        str(value).strip().casefold()
        for value in df[window_column].dropna().unique()
        if str(value).strip()
    }


def _section_score(df: pd.DataFrame, spec: KvkExportSectionSpec) -> int:
    if not _matches_spec(df, spec):
        return -1

    columns = normalise_export_columns(df)
    if spec.name.startswith("KVK_Camp_") and "kingdom" in columns:
        return -1
    if spec.name.startswith("KVK_Kingdom_") and "governor_id" in columns:
        return -1
    if spec.name.startswith("KVK_Player_") and "governor_id" not in columns:
        return -1

    score = len(spec.required_columns)
    windows = _window_name_values(df)
    if spec.name.endswith("_Full") and windows and windows != {"full"}:
        return -1
    # Three-way scoring: _Full with full-only windows = +100 (preferred),
    # _Windowed with pass/altar windows = +50, _Windowed with full-only windows = +0
    # (accepted but lowest priority — supports Full-only KVKs before any windows exist).
    if spec.name.endswith("_Full") and windows == {"full"}:
        score += 100
    if spec.name.endswith("_Windowed") and (not windows or windows != {"full"}):
        score += 50
    return score


def bind_kvk_export_sections(
    result_sets: Sequence[pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Bind SQL export result sets to stable section names.

    The current SQL procedure has no explicit result-set metadata, so this binder
    uses schema signatures first and keeps the existing positional contract as a
    compatibility tie-breaker. Extra compatible result sets are ignored once all
    required sections are bound.
    """
    sections: dict[str, pd.DataFrame] = {}
    assigned_indexes: set[int] = set()

    for spec in KVK_EXPORT_SECTION_SPECS:
        if spec.legacy_index >= len(result_sets):
            continue
        df = result_sets[spec.legacy_index]
        if _section_score(df, spec) >= 0:
            sections[spec.name] = df
            assigned_indexes.add(spec.legacy_index)

    for spec in KVK_EXPORT_SECTION_SPECS:
        if spec.name in sections:
            continue

        candidates: list[tuple[int, int]] = []
        for index, df in enumerate(result_sets):
            if index in assigned_indexes:
                continue
            score = _section_score(df, spec)
            if score >= 0:
                legacy_bonus = 10 if index == spec.legacy_index else 0
                candidates.append((score + legacy_bonus, index))

        if candidates:
            _, index = max(candidates)
            sections[spec.name] = result_sets[index]
            assigned_indexes.add(index)

    missing = [spec.name for spec in KVK_EXPORT_SECTION_SPECS if spec.name not in sections]
    if missing:
        raise KvkExportBindingError(
            "KVK export result sets missing required section(s): " + ", ".join(missing)
        )

    return sections


def get_kvk_export_section(
    sections: Mapping[str, pd.DataFrame] | Sequence[pd.DataFrame],
    section_name: str,
) -> pd.DataFrame:
    if isinstance(sections, Mapping):
        try:
            return sections[section_name]
        except KeyError as exc:
            raise KvkExportBindingError(f"Missing KVK export section: {section_name}") from exc

    bound_sections = bind_kvk_export_sections(sections)
    return bound_sections[section_name]


def get_kvk_export_section_by_legacy_index(
    sections: Mapping[str, pd.DataFrame] | Sequence[pd.DataFrame],
    legacy_index: int,
) -> pd.DataFrame:
    for spec in KVK_EXPORT_SECTION_SPECS:
        if spec.legacy_index == legacy_index:
            return get_kvk_export_section(sections, spec.name)
    raise KvkExportBindingError(f"Unknown legacy KVK export result-set index: {legacy_index}")


def resolve_kvk_export_section_name(section_ref: str | int) -> str:
    if isinstance(section_ref, str):
        if section_ref not in KVK_EXPORT_SECTION_BY_NAME:
            raise KvkExportBindingError(f"Unknown KVK export section: {section_ref}")
        return section_ref

    for spec in KVK_EXPORT_SECTION_SPECS:
        if spec.legacy_index == section_ref:
            return spec.name
    raise KvkExportBindingError(f"Unknown legacy KVK export result-set index: {section_ref}")


def section_ref_to_name(section_ref: Any) -> str | None:
    if section_ref is None:
        return None
    if isinstance(section_ref, str):
        return section_ref
    if isinstance(section_ref, int):
        return resolve_kvk_export_section_name(section_ref)
    return None
