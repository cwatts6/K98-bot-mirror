from __future__ import annotations

import pandas as pd
import pytest

from kvk.services.kvk_export_service import (
    KVK_EXPORT_SECTION_NAMES,
    KvkExportBindingError,
    bind_kvk_export_sections,
)


def _df(columns: list[str], rows: list[dict] | None = None) -> pd.DataFrame:
    return pd.DataFrame(rows or [], columns=columns)


SCAN_COLS = [
    "KVK_NO",
    "ScanID",
    "ScanTimestampUTC",
    "SourceFileName",
    "Row_Count",
    "ImportedAtUTC",
    "UploaderDiscordID",
]
WINDOW_COLS = [
    "KVK_NO",
    "WindowName",
    "WindowSeq",
    "StartScanID",
    "EndScanID",
    "EffectiveEndScanID",
    "Notes",
    "UpdatedAtUTC",
]
WEIGHT_COLS = ["KVK_NO", "WeightT4X", "WeightT5Y", "WeightDeadsZ", "EffectiveFromUTC"]
PLAYER_COLS = [
    "KVK_NO",
    "WindowName",
    "governor_id",
    "name",
    "kingdom",
    "campid",
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
]
KINGDOM_COLS = [
    "KVK_NO",
    "WindowName",
    "kingdom",
    "campid",
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
]
CAMP_COLS = [
    "KVK_NO",
    "WindowName",
    "campid",
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
]
NEGATIVE_COLS = [
    "KVK_NO",
    "ScanID",
    "governor_id",
    "name",
    "kingdom",
    "campid",
    "field_name",
    "value",
    "recorded_at_utc",
]


def _legacy_result_sets() -> list[pd.DataFrame]:
    player_rows = [
        {"WindowName": "Pass 4", "governor_id": 1, "max_contribute_gain": 10},
        {"WindowName": "Full", "governor_id": 1, "max_contribute_gain": 20},
    ]
    return [
        _df(SCAN_COLS),
        _df(WINDOW_COLS),
        _df(WEIGHT_COLS),
        _df(PLAYER_COLS, player_rows),
        _df(KINGDOM_COLS, [{"WindowName": "Pass 4", "kingdom": 1}]),
        _df(CAMP_COLS, [{"WindowName": "Pass 4", "campid": 1}]),
        _df(PLAYER_COLS, [{"WindowName": "Full", "governor_id": 1}]),
        _df(KINGDOM_COLS, [{"WindowName": "Full", "kingdom": 1}]),
        _df(CAMP_COLS, [{"WindowName": "Full", "campid": 1}]),
        _df(NEGATIVE_COLS),
    ]


def test_bind_kvk_export_sections_from_legacy_positional_results() -> None:
    sections = bind_kvk_export_sections(_legacy_result_sets())

    assert tuple(sections) == KVK_EXPORT_SECTION_NAMES
    assert sections["KVK_Player_Windowed"].columns.tolist() == PLAYER_COLS


def test_bind_kvk_export_sections_ignores_extra_compatible_result_set() -> None:
    result_sets = _legacy_result_sets()
    result_sets.insert(0, _df(["unrelated", "diagnostic"]))

    sections = bind_kvk_export_sections(result_sets)

    assert set(sections) == set(KVK_EXPORT_SECTION_NAMES)
    assert "max_contribute_gain" in sections["KVK_Player_Windowed"].columns


def test_bind_kvk_export_sections_reports_missing_required_section() -> None:
    result_sets = _legacy_result_sets()
    # Remove both player result sets so the binder cannot satisfy either player section.
    # Delete the higher index first to avoid shifting the lower index.
    del result_sets[6]  # KVK_Player_Full
    del result_sets[3]  # KVK_Player_Windowed

    with pytest.raises(KvkExportBindingError, match="KVK_Player"):
        bind_kvk_export_sections(result_sets)


def test_bind_kvk_export_sections_accepts_full_only_windowed_result_set() -> None:
    """Full-only KVKs emit _Windowed result sets with only 'Full' WindowName rows.

    The binder must accept and bind these rather than hard-rejecting them, so
    that primary export paths don't fail before any Pass/Altar windows exist.
    """
    player_full_only = _df(PLAYER_COLS, [{"WindowName": "Full", "governor_id": 1}])
    kingdom_full_only = _df(KINGDOM_COLS, [{"WindowName": "Full", "kingdom": 1}])
    camp_full_only = _df(CAMP_COLS, [{"WindowName": "Full", "campid": 1}])

    result_sets = [
        _df(SCAN_COLS),
        _df(WINDOW_COLS),
        _df(WEIGHT_COLS),
        player_full_only,  # index 3 – Windowed position, Full-only content
        kingdom_full_only,  # index 4
        camp_full_only,  # index 5
        player_full_only,  # index 6 – Full position
        kingdom_full_only,  # index 7
        camp_full_only,  # index 8
        _df(NEGATIVE_COLS),
    ]

    sections = bind_kvk_export_sections(result_sets)

    assert set(sections) == set(KVK_EXPORT_SECTION_NAMES)
    # Windowed sections are bound even though window values are all "Full"
    assert "KVK_Player_Windowed" in sections
    assert "KVK_Player_Full" in sections
