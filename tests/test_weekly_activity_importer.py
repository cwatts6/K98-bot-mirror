from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest

from weekly_activity_importer import _completion_evidence, parse_activity_excel


def _workbook(rows: list[dict[str, object]]) -> bytes:
    frame = pd.DataFrame(rows)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False)
    return buffer.getvalue()


def _row(
    governor_id: object,
    *,
    building: object = 0,
    tech: object = 0,
) -> dict[str, object]:
    return {
        "GovernorID": governor_id,
        "Name": f"Governor {governor_id}",
        "Alliance": "k98A",
        "Power": 1,
        "Kill Points": 2,
        "Help Times": 3,
        "Rss Trading": 4,
        "Building": building,
        "Tech Donation": tech,
    }


def test_explicit_zero_is_valid_and_extra_source_rows_are_allowed():
    parsed = parse_activity_excel(_workbook([_row(1), _row(2, building=10, tech=20)]))

    assert parsed["BuildingTotal"].tolist() == [0, 10]
    assert parsed["TechDonationTotal"].tolist() == [0, 20]
    assert parsed.attrs["missing_metric_count"] == 0
    assert parsed.attrs["invalid_metric_count"] == 0

    evidence = _completion_evidence(parsed, {1})

    assert evidence.completion_state == "COMPLETE"
    assert evidence.expected_governor_count == 1
    assert evidence.observed_governor_count == 2
    assert evidence.missing_expected_governor_count == 0


def test_missing_and_invalid_metrics_are_distinguished_and_partial():
    parsed = parse_activity_excel(_workbook([_row(1, building=None), _row(2, tech="not-a-number")]))

    assert parsed.attrs["missing_metric_count"] == 1
    assert parsed.attrs["invalid_metric_count"] == 1

    evidence = _completion_evidence(parsed, {1, 2})

    assert evidence.completion_state == "PARTIAL"
    assert evidence.observed_governor_count == 0
    assert evidence.missing_expected_governor_count == 0
    assert evidence.missing_metric_count == 1
    assert evidence.invalid_metric_count == 1


def test_missing_expected_governor_marks_snapshot_partial():
    parsed = parse_activity_excel(_workbook([_row(1, building=10, tech=20)]))

    evidence = _completion_evidence(parsed, {1, 2})

    assert evidence.completion_state == "PARTIAL"
    assert evidence.missing_expected_governor_count == 1
    assert evidence.observed_governor_count == 1


@pytest.mark.parametrize("governor_id", [None, 0, -1, 1.5])
def test_invalid_governor_id_is_rejected(governor_id: object):
    with pytest.raises(ValueError, match="invalid GovernorID"):
        parse_activity_excel(_workbook([_row(governor_id)]))


def test_duplicate_governor_id_is_rejected():
    with pytest.raises(ValueError, match="duplicate GovernorID"):
        parse_activity_excel(_workbook([_row(1), _row(1)]))


def test_completion_requires_expected_scan_cohort():
    parsed = parse_activity_excel(_workbook([_row(1)]))

    with pytest.raises(RuntimeError, match="expected scan cohort"):
        _completion_evidence(parsed, set())
