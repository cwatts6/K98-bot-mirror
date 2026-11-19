from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone

from kvk_source_fixtures import CONFIRMATION, SCOPE, metadata
import pytest

from kvk.models.new_source_observation import MetadataConfirmation, SourceScope
from kvk.schemas.new_source_schema import (
    ReportState,
    SourceKind,
    SourceValidationError,
    TimePrecision,
)
from kvk.services.new_source_metadata import parse_filename_metadata, validate_source_metadata


@pytest.mark.parametrize("suffix", ["", " (1)", " (25)"])
def test_t09_strict_filename_and_download_suffix(suffix):
    result = parse_filename_metadata(f"kvk16_players_20260905T1526Z{suffix}.xlsx")
    assert result.scan_start_utc == datetime(2026, 9, 5, 15, 26, tzinfo=UTC)
    assert result.time_precision == TimePrecision.MINUTE
    assert result.original_filename.endswith(f"{suffix}.xlsx")


def test_t09_seconds_precision_is_distinct():
    result = parse_filename_metadata("kvk16_players_20260905T152601Z.xlsx")
    assert result.scan_start_utc.second == 1
    assert result.time_precision == TimePrecision.SECOND


@pytest.mark.parametrize(
    "name",
    [
        "kvk16_players_20260230T1526Z.xlsx",
        "legacy.xlsx",
        "../kvk16_players_20260905T1526Z.xlsx",
        "C:\\private.xlsx",
        "kvk16_players_20260905T2460Z.xlsx",
        "kvk16_players_20260905T1526Z.csv",
    ],
)
def test_t10_unknown_invalid_or_path_names_never_guess(name):
    result = parse_filename_metadata(name)
    assert result.scan_start_utc is None and result.ambiguity
    with pytest.raises(SourceValidationError):
        validate_source_metadata(result, CONFIRMATION, SCOPE)


@pytest.mark.parametrize("token", ["20260329T0130Z", "20261025T0130Z"])
def test_t11_dst_does_not_shift_utc(token):
    candidate = parse_filename_metadata(f"kvk16_players_{token}.xlsx")
    result = validate_source_metadata(candidate, CONFIRMATION, SCOPE)
    assert result.candidate.scan_start_utc.hour == 1
    assert result.candidate.scan_start_utc.utcoffset() == timedelta(0)


def test_t12_b0_explicit_attestation_without_filename_time():
    candidate = parse_filename_metadata("KVK_16_Baseline.xlsx")
    overrides = replace(
        CONFIRMATION,
        values=(
            ("kind", SourceKind.PLAYERS),
            ("kvk_no", 16),
            ("scan_start_utc", datetime(2026, 8, 26, 4, 7, tzinfo=UTC)),
            ("time_precision", TimePrecision.MINUTE),
        ),
    )
    result = validate_source_metadata(candidate, overrides, SCOPE)
    assert result.candidate.scan_start_utc.minute == 7
    assert result.confirmation.actor == "synthetic-operator"
    with pytest.raises(FrozenInstanceError):
        result.candidate.kvk_no = 17


def test_t10_conflicting_filename_time_requires_specific_confirmation():
    candidate = metadata().candidate
    overrides = replace(
        CONFIRMATION, values=(("scan_start_utc", datetime(2026, 9, 6, tzinfo=UTC)),)
    )
    with pytest.raises(SourceValidationError) as error:
        validate_source_metadata(candidate, overrides, SCOPE)
    assert error.value.code == "metadata_conflict"
    approved = replace(
        overrides, confirmed_fields=("scan_start_utc",), reason="Explicit event review"
    )
    assert validate_source_metadata(candidate, approved, SCOPE).candidate.scan_start_utc.day == 6


def test_t06_same_evidence_different_identity_requires_review():
    previous = metadata()
    candidate = replace(previous.candidate, scan_start_utc=datetime(2026, 9, 6, tzinfo=UTC))
    with pytest.raises(SourceValidationError) as error:
        validate_source_metadata(candidate, CONFIRMATION, SCOPE, previous_metadata=previous)
    assert error.value.code == "evidence_identity_conflict"
    approved = replace(
        CONFIRMATION, confirmed_fields=("scan_start_utc",), reason="Distinct event attested"
    )
    assert (
        validate_source_metadata(
            candidate, approved, SCOPE, previous_metadata=previous
        ).event_identity
        != previous.event_identity
    )


def test_t08_minute_second_and_simultaneous_event_provenance():
    previous = metadata()
    candidate = replace(previous.candidate, time_precision=TimePrecision.SECOND)
    with pytest.raises(SourceValidationError):
        validate_source_metadata(candidate, CONFIRMATION, SCOPE, previous_metadata=previous)
    candidate = replace(previous.candidate, event_discriminator="second-event")
    with pytest.raises(SourceValidationError):
        validate_source_metadata(candidate, CONFIRMATION, SCOPE)
    approval = replace(
        CONFIRMATION, confirmed_fields=("event_discriminator",), reason="Independent event"
    )
    assert (
        validate_source_metadata(candidate, approval, SCOPE).candidate.event_discriminator
        == "second-event"
    )


@pytest.mark.parametrize(
    "stamp",
    [
        datetime(2026, 1, 1),
        datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=1))),
        datetime(2026, 1, 1, microsecond=1, tzinfo=UTC),
    ],
)
def test_naive_non_utc_and_unrepresented_precision_reject(stamp):
    with pytest.raises(SourceValidationError):
        validate_source_metadata(
            replace(metadata().candidate, scan_start_utc=stamp), CONFIRMATION, SCOPE
        )


def test_aggregate_needs_explicit_coverage_and_overall_final():
    candidate = parse_filename_metadata("kvk16_pass4_totals_live_20260906T1304Z.xlsx")
    with pytest.raises(SourceValidationError):
        validate_source_metadata(candidate, CONFIRMATION, SCOPE)
    result = metadata(aggregate=True)
    with pytest.raises(SourceValidationError):
        validate_source_metadata(
            replace(result.candidate, period_key="overall"), result.confirmation, SCOPE
        )
    final = replace(result.candidate, period_key="overall", report_state=ReportState.FINAL)
    assert (
        validate_source_metadata(final, result.confirmation, SCOPE).candidate.period_key
        == "overall"
    )


@pytest.mark.parametrize(
    "scope",
    [
        SourceScope(17, (101, 102)),
        SourceScope(16, (101, 101)),
        SourceScope(True, (101,)),
        SourceScope(16, ()),
    ],
)
def test_invalid_scope_rejects(scope):
    with pytest.raises(SourceValidationError):
        validate_source_metadata(metadata().candidate, CONFIRMATION, scope)


def test_missing_confirmation_provenance_rejects():
    with pytest.raises(SourceValidationError):
        validate_source_metadata(metadata().candidate, MetadataConfirmation(), SCOPE)
