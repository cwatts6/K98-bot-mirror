from __future__ import annotations

from datetime import UTC, datetime

import pytest

from kvk.models.kvk_target_publication import TargetPublicationMetadata
from kvk.services import kvk_target_publication_service as service


def _metadata(**overrides) -> TargetPublicationMetadata:
    values = {
        "publication_id": 41,
        "kvk_no": 16,
        "publication_state": "OFFICIAL",
        "source_scan_order": 1059,
        "source_scan_type": "MATCHMAKING_SCAN",
        "configured_draft_scan": 1040,
        "configured_matchmaking_scan": 1059,
        "published_at_utc": datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
        "target_row_count": 2,
        "output_object_name": "dbo.EXCEL_EXPORT_KVK_TARGETS_16",
        "publication_version": 1,
        "publication_signature": "2ad2a141-c5bf-4075-927b-832e44477e55",
    }
    values.update(overrides)
    return TargetPublicationMetadata(**values)


@pytest.mark.parametrize("fighting_state", ["DRAFT", "ACTIVE", None])
def test_exact_matchmaking_publication_is_official_before_and_during_pass4(fighting_state):
    resolution = service.resolve_target_publication_state(
        _metadata(),
        requested_kvk_no=16,
        fighting_state=fighting_state,
        observed_row_count=2,
    )

    assert resolution.state == "OFFICIAL"
    assert resolution.reason == service.MATCHMAKING_SOURCE_CONFIRMED


def test_verified_official_publication_becomes_historic_only_when_kvk_ends():
    resolution = service.resolve_target_publication_state(
        _metadata(),
        requested_kvk_no=16,
        fighting_state="ENDED",
        observed_row_count=2,
    )

    assert resolution.state == "HISTORIC"
    assert resolution.reason == service.OFFICIAL_PUBLICATION_KVK_ENDED


def test_draft_can_prove_applied_scan_below_configured_draft_scan():
    resolution = service.resolve_target_publication_state(
        _metadata(
            publication_state="DRAFT",
            source_scan_order=1038,
            source_scan_type="DRAFTSCAN",
        ),
        requested_kvk_no=16,
        fighting_state="DRAFT",
        observed_row_count=2,
    )

    assert resolution.state == "DRAFT"
    assert resolution.reason == service.DRAFT_SOURCE_CONFIRMED


@pytest.mark.parametrize(
    ("overrides", "requested_kvk", "row_count", "reason"),
    [
        ({"publication_state": None}, 16, 2, service.PUBLICATION_STATE_MISMATCH),
        ({"source_scan_order": 1060}, 16, 2, service.MATCHMAKING_SCAN_MISMATCH),
        ({"source_scan_type": "LATEST_SCAN"}, 16, 2, service.INVALID_SOURCE_TYPE),
        ({"publication_signature": None}, 16, 2, service.INVALID_PUBLICATION_IDENTITY),
        ({"output_object_name": "dbo.v_TARGETS_FOR_UPLOAD"}, 16, 2, service.OUTPUT_OBJECT_MISMATCH),
        ({}, 15, 2, service.PUBLICATION_KVK_MISMATCH),
        ({}, 16, 1, service.ROW_COUNT_MISMATCH),
    ],
)
def test_unproved_publications_resolve_unknown(overrides, requested_kvk, row_count, reason):
    resolution = service.resolve_target_publication_state(
        _metadata(**overrides),
        requested_kvk_no=requested_kvk,
        fighting_state="DRAFT",
        observed_row_count=row_count,
    )

    assert resolution.state == "UNKNOWN"
    assert resolution.reason == reason


def test_missing_metadata_is_unknown_not_official():
    resolution = service.resolve_target_publication_state(
        None,
        requested_kvk_no=16,
        fighting_state="ACTIVE",
    )

    assert resolution.state == "UNKNOWN"
    assert resolution.reason == service.MISSING_PUBLICATION_METADATA


@pytest.mark.parametrize(
    ("state", "label", "source_fragment"),
    [
        ("DRAFT", "Draft", "Draft target set from scan 1040"),
        ("OFFICIAL", "Official", "exact matchmaking scan 1059"),
        ("HISTORIC", "Historical", "Historical official set"),
        ("UNKNOWN", "Unverified", "could not be verified"),
        (None, "Unverified", "could not be verified"),
        ("ACTIVE", "Unverified", "could not be verified"),
    ],
)
def test_publication_display_copy_is_canonical_and_fails_closed(state, label, source_fragment):
    source_scan = 1040 if state == "DRAFT" else 1059

    display = service.target_publication_display(state, source_scan_order=source_scan)

    assert display.label == label
    assert source_fragment in display.source_text


@pytest.mark.parametrize("state", ["DRAFT", "OFFICIAL", "HISTORIC"])
@pytest.mark.parametrize("source_scan", [None, 0, -1, "invalid", True])
def test_publication_display_requires_positive_source_scan(state, source_scan):
    display = service.target_publication_display(state, source_scan_order=source_scan)

    assert display.state == "UNKNOWN"
    assert display.label == "Unverified"
    assert "could not be verified" in display.source_text
    assert "Do not treat this target set as Official" in display.warning_text
