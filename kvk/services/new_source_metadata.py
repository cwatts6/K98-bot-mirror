"""Explicit UTC metadata validation without clocks, paths, SQL or admission effects."""

from dataclasses import fields, replace
from datetime import UTC, datetime, timedelta
import re

from kvk.models.new_source_observation import (
    MetadataCandidate,
    MetadataConfirmation,
    SourceScope,
    ValidatedSourceMetadata,
)
from kvk.schemas.new_source_schema import (
    INT_MAX,
    SOURCE_KEY,
    ReportState,
    SourceKind,
    SourceValidationError,
    TimePrecision,
)

_FILENAME = re.compile(
    r"kvk(?P<kvk>[1-9][0-9]*)_(?:players|(?P<period>[a-z][a-z0-9_-]*)_totals_"
    r"(?P<state>live|final))_(?P<time>[0-9]{8}T(?:[0-9]{4}|[0-9]{6})Z)"
    r"(?: \([1-9][0-9]*\))?\.xlsx"
)
_EDITABLE = frozenset(f.name for f in fields(MetadataCandidate)) - {
    "original_filename",
    "ambiguity",
    "source_key",
}


def _reject(code: str) -> None:
    raise SourceValidationError(
        code, "Metadata requires explicit valid scope and UTC confirmation."
    )


def _utc(value: object) -> bool:
    return (
        isinstance(value, datetime)
        and value.tzinfo is not None
        and value.utcoffset() == timedelta(0)
        and value.microsecond == 0
    )


def parse_filename_metadata(basename: str) -> MetadataCandidate:
    """Unknown/invalid names return typed ambiguity; never guess an event time."""
    if not isinstance(basename, str) or len(basename) > 255:
        _reject("filename_length")
    candidate = MetadataCandidate(
        original_filename=basename, ambiguity="explicit_metadata_required"
    )
    if any(c in basename for c in ("/", "\\", ":", "\x00")):
        return replace(candidate, ambiguity="basename_required")
    match = _FILENAME.fullmatch(basename)
    if not match:
        return candidate
    token = match["time"]
    precision = TimePrecision.MINUTE if len(token) == 14 else TimePrecision.SECOND
    try:
        stamp = datetime.strptime(
            token, "%Y%m%dT%H%MZ" if precision == TimePrecision.MINUTE else "%Y%m%dT%H%M%SZ"
        ).replace(tzinfo=UTC)
        kvk = int(match["kvk"])
        if kvk > INT_MAX:
            return replace(candidate, ambiguity="invalid_season")
    except ValueError:
        return replace(candidate, ambiguity="invalid_calendar_time")
    period = match["period"]
    return replace(
        candidate,
        kind=SourceKind.AGGREGATE if period else SourceKind.PLAYERS,
        kvk_no=kvk,
        scan_start_utc=stamp,
        time_precision=precision,
        period_key=("overall" if period == "overall" else f"fight:{period}") if period else None,
        report_state=ReportState(match["state"]) if period else None,
        ambiguity=None,
    )


def validate_source_metadata(
    candidate: MetadataCandidate,
    overrides: MetadataConfirmation,
    scope: SourceScope,
    *,
    previous_metadata: ValidatedSourceMetadata | None = None,
) -> ValidatedSourceMetadata:
    """Validate a candidate; prior same-artifact/digest identity requires explicit review.

    The later admission service supplies previous_metadata when evidence already exists.
    This pure function cannot discover aliases or authorize database acceptance itself.
    """
    if (
        type(scope.kvk_no) is not int
        or not 0 < scope.kvk_no <= INT_MAX
        or not isinstance(scope.kingdoms, tuple)
        or not scope.kingdoms
        or any(type(k) is not int or not 0 < k <= INT_MAX for k in scope.kingdoms)
        or len(set(scope.kingdoms)) != len(scope.kingdoms)
        or not isinstance(scope.period_keys, tuple)
        or any(
            not isinstance(k, str)
            or not re.fullmatch(r"overall|(?:fight|no_fight):[a-z][a-z0-9_-]{0,63}", k)
            for k in scope.period_keys
        )
        or len(set(scope.period_keys)) != len(scope.period_keys)
    ):
        _reject("invalid_scope")
    if (
        not isinstance(overrides.values, tuple)
        or any(not isinstance(pair, tuple) or len(pair) != 2 for pair in overrides.values)
        or not isinstance(overrides.confirmed_fields, tuple)
        or any(not isinstance(name, str) for name in overrides.confirmed_fields)
    ):
        _reject("invalid_confirmation")
    values = dict(overrides.values)
    if (
        len(values) != len(overrides.values)
        or not set(values) <= _EDITABLE
        or not set(overrides.confirmed_fields) <= _EDITABLE
    ):
        _reject("invalid_override_fields")
    if (
        not isinstance(overrides.actor, str)
        or not 0 < len(overrides.actor.strip()) <= 128
        or not _utc(overrides.confirmed_at_utc)
        or not isinstance(overrides.reason, str)
        or len(overrides.reason) > 512
    ):
        _reject("confirmation_provenance")
    for name, value in values.items():
        old = getattr(candidate, name)
        if old is not None and old != value:
            if name not in overrides.confirmed_fields or not overrides.reason.strip():
                _reject("metadata_conflict")
    c = replace(candidate, **values, ambiguity=None)
    if (
        c.source_key != SOURCE_KEY
        or type(c.kvk_no) is not int
        or c.kvk_no != scope.kvk_no
        or not isinstance(c.kind, SourceKind)
        or not _utc(c.scan_start_utc)
        or not isinstance(c.time_precision, TimePrecision)
        or not isinstance(c.event_discriminator, str)
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", c.event_discriminator)
    ):
        _reject("invalid_identity")
    if c.time_precision == TimePrecision.MINUTE and c.scan_start_utc.second != 0:
        _reject("time_precision_conflict")
    if c.event_discriminator != "main" and (
        "event_discriminator" not in overrides.confirmed_fields or not overrides.reason.strip()
    ):
        _reject("event_discriminator_confirmation")
    if c.period_key is not None and c.period_key not in scope.period_keys:
        _reject("unknown_period")
    if c.kind == SourceKind.AGGREGATE:
        if (
            c.period_key is None
            or c.period_key.startswith("no_fight:")
            or not isinstance(c.report_state, ReportState)
            or c.report_state
            not in (ReportState.LIVE, ReportState.FINAL, ReportState.CORRECTED_FINAL)
            or not all(_utc(t) for t in (c.coverage_start_utc, c.coverage_end_utc, c.as_of_utc))
        ):
            _reject("aggregate_coverage_required")
        if not c.coverage_start_utc <= c.coverage_end_utc <= c.as_of_utc:
            _reject("aggregate_coverage_order")
        if c.period_key == "overall" and c.report_state == ReportState.LIVE:
            _reject("overall_requires_final")
    elif any(
        v is not None
        for v in (c.coverage_start_utc, c.coverage_end_utc, c.as_of_utc, c.report_state)
    ):
        _reject("player_aggregate_metadata")
    result = ValidatedSourceMetadata(c, scope, overrides)
    if previous_metadata is not None:
        previous = previous_metadata.candidate
        changed = tuple(
            name
            for name in (
                "kind",
                "kvk_no",
                "scan_start_utc",
                "time_precision",
                "event_discriminator",
                "period_key",
                "coverage_start_utc",
                "coverage_end_utc",
                "as_of_utc",
            )
            if getattr(previous, name) != getattr(c, name)
        )
        if changed and (
            not set(changed) <= set(overrides.confirmed_fields) or not overrides.reason.strip()
        ):
            _reject("evidence_identity_conflict")
    return result
