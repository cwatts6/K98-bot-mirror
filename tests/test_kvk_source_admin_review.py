"""S8C owner, review, configuration and exact-context tests; no SQL connection."""

from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
import json
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.models.source_integration import review_payload
from kvk.services.source_admin_review_service import (
    SourceAdminReviewService,
    validated_configuration,
)
from tests.test_kvk_source_admin import ACCESS, ADMIN, NOW, UPLOADER


def configuration():
    return dict(
        mapping=[[101, 1, "North"], [102, 2, "South"]],
        weights=["1.000000000001", "2", "3"],
        effective="2026-09-01T00:00:00+00:00",
        windows=[],
        weight_provenance="original kvk_list decimal tokens",
    )


class Reviews:
    def __init__(self):
        self.saved = {}
        self.context = dict(
            choice_id=str(uuid4()),
            season_version=2,
            period_id=str(uuid4()),
            period_kind="fight",
            config=dict(
                ConfigVersionID=str(uuid4()), RosterID=str(uuid4()), StartScanID=17, EndScanID=18
            ),
            scans={"17": str(uuid4()), "18": str(uuid4())},
            aggregate=None,
            base_update_id=None,
            request_id=None,
            configuration_review=None,
        )

    def create(self, *, actor, kvk_no, kind, payload, now, expires):
        key = str(uuid4())
        row = dict(
            ReviewID=key,
            KVK_NO=kvk_no,
            ReviewKind=kind,
            ActorID=str(actor.user_id),
            GuildID=str(actor.guild_id),
            ChannelID=str(actor.channel_id),
            Version=1,
            ReviewState="pending",
            payload=json.loads(review_payload(payload)),
            outcome=None,
            ExpiresUTC=expires,
            CreatedUTC=now,
        )
        self.saved[key] = row
        return deepcopy(row)

    def read(self, key, actor):
        row = self.saved[key]
        if (row["ActorID"], row["GuildID"], row["ChannelID"]) != tuple(
            str(v) for v in (actor.user_id, actor.guild_id, actor.channel_id)
        ):
            raise SourceConflict("Owner context differs.")
        return deepcopy(row)

    def seasons(self):
        return [16, 15]

    def match_context(self, *args):
        return deepcopy(self.context)


def pair(service, actor=ADMIN, **overrides):
    args = dict(
        season=16,
        period="fight:two",
        end_scan_id=18,
        coverage_start="2026-09-01T00:00:00Z",
        coverage_end="2026-09-02T00:00:00Z",
        as_of="2026-09-02T01:00:00Z",
        reason="Explicit pair review",
    )
    return service.prepare_match(actor, **(args | overrides))


@pytest.mark.parametrize(
    "fault",
    [
        "map_missing",
        "duplicate_kingdom",
        "bad_camp",
        "camp_alias",
        "weights_missing",
        "weight_precision",
    ],
)
def test_baseline_imported_configuration_rejects_missing_or_invalid_authority(fault):
    snapshot = configuration()
    if fault == "map_missing":
        snapshot["mapping"] = []
    if fault == "duplicate_kingdom":
        snapshot["mapping"].append(snapshot["mapping"][0])
    if fault == "bad_camp":
        snapshot["mapping"][0][1] = 9
    if fault == "camp_alias":
        snapshot["mapping"][1][2] = "North"
    if fault == "weights_missing":
        snapshot["weights"] = []
    if fault == "weight_precision":
        snapshot["weights"][0] = "1.0000000000001"
    with pytest.raises((SourceConflict, ValueError)):
        validated_configuration(snapshot)


def test_decimal_tokens_remain_exact():
    snapshot = configuration()
    assert validated_configuration(snapshot).entries[0] == (101, 1, "North")
    assert "1.000000000001" in review_payload(snapshot)
    with pytest.raises(ValueError):
        review_payload({"weights": [1.000000000001]})


@pytest.mark.parametrize("fault", ["role", "guild", "channel", "disabled"])
def test_pair_review_requires_fresh_admin_scope(fault):
    actor, access = ADMIN, ACCESS
    if fault == "role":
        actor = UPLOADER
    if fault == "guild":
        actor = replace(actor, guild_id=99)
    if fault == "channel":
        actor = replace(actor, channel_id=99)
    if fault == "disabled":
        access = replace(access, enabled=False)
    repository = Reviews()
    with pytest.raises(PermissionError):
        pair(SourceAdminReviewService(access, repository, lambda: NOW), actor)
    assert not repository.saved


def test_retained_scans_can_be_assigned_later_without_mutating_receipts():
    repo = Reviews()
    before = deepcopy(repo.context)
    service = SourceAdminReviewService(ACCESS, repo, lambda: NOW)
    row = pair(service)
    context = row["payload"]["context"]
    proof = json.loads(context["confirmation_json"])
    assert proof["period_assignment"] == dict(
        period_id=context["period_id"],
        config_version_id=context["config_version_id"],
        start_scan_id=17,
        end_scan_id=18,
        actor="10",
    )
    assert repo.context == before
    assert row["ReviewState"] == "pending" and row["outcome"] is None
    assert "UpdateID" not in repo.saved  # Preparing never calls an update writer.
    resumed = SourceAdminReviewService(ACCESS, repo, lambda: NOW + timedelta(seconds=20))
    assert (
        resumed.read(ADMIN, row["ReviewID"])["payload"]["context"]["update_id"]
        == context["update_id"]
    )


def test_pending_end_requires_exact_request_and_pins_existing_start():
    repo = Reviews()
    del repo.context["scans"]["18"]
    service = SourceAdminReviewService(ACCESS, repo, lambda: NOW)
    with pytest.raises(SourceConflict, match="exact pending"):
        pair(service)
    repo.context["request_id"] = str(uuid4())
    row = pair(service)
    pending = json.loads(row["payload"]["context"]["confirmation_json"])["pending_player"]
    assert pending == dict(
        start_scan_id=17, end_scan_id=18, start_revision_id=repo.context["scans"]["17"]
    )


def test_counterpart_proof_binds_actor_roster_configuration_and_coverage():
    repo = Reviews()
    repo.context["base_update_id"] = str(uuid4())
    revision = str(uuid4())
    row = pair(
        SourceAdminReviewService(ACCESS, repo, lambda: NOW), counterpart_revision_id=revision
    )
    proof = json.loads(row["payload"]["context"]["confirmation_json"])["counterpart"]
    assert proof["revision_id"] == revision and proof["actor"] == "10"
    assert proof["config_version_id"] == repo.context["config"]["ConfigVersionID"]
    assert proof["roster_id"] == repo.context["config"]["RosterID"]
    assert proof["as_of_utc"] == "2026-09-02T01:00:00"


def test_configuration_review_cannot_be_mislabelled_ordinary_publish():
    repo = Reviews()
    repo.context["configuration_review"] = str(uuid4())
    service = SourceAdminReviewService(ACCESS, repo, lambda: NOW)
    with pytest.raises(SourceConflict, match="corrected"):
        pair(service)
    row = pair(service, action="correct")
    assert (
        json.loads(row["payload"]["context"]["confirmation_json"])["configuration_review"]
        == repo.context["configuration_review"]
    )


def test_choice_requires_imported_season_and_does_not_choose_during_prepare():
    repo = Reviews()
    service = SourceAdminReviewService(ACCESS, repo, lambda: NOW)
    row = service.prepare_choice(ADMIN, 16, "legacy_full_data", "Explicit choice")
    assert row["payload"]["source"] == "legacy_full_data" and row["ReviewState"] == "pending"
    with pytest.raises(ValueError):
        service.prepare_choice(ADMIN, 999, "snapshot_report_v1", "not imported")


def test_read_review_rejects_wrong_owner_and_original_channel():
    repo = Reviews()
    service = SourceAdminReviewService(ACCESS, repo, lambda: NOW)
    row = pair(service)
    for actor in (UPLOADER, replace(ADMIN, channel_id=31)):
        with pytest.raises(SourceConflict):
            service.read(actor, row["ReviewID"])


@pytest.mark.parametrize("fault", ["stale", "expired", "wrong_owner"])
def test_review_dal_rejects_before_operation(monkeypatch, fault):
    from contextlib import nullcontext

    from kvk.dal import source_admin_review_dal as dal

    key = str(uuid4())
    cursor = Mock()
    row = dict(
        ReviewID=key,
        Version=3,
        ReviewState="pending",
        ExpiresUTC=(NOW + timedelta(seconds=5)).replace(tzinfo=None),
    )
    monkeypatch.setattr(dal, "transaction", lambda _: nullcontext(cursor))
    monkeypatch.setattr(
        dal, "one", Mock(return_value=None if fault == "wrong_owner" else {"KVK_NO": 16})
    )
    monkeypatch.setattr(dal, "lock_scope", Mock())
    repository = dal.SourceAdminReviewDAL(Mock())
    repository._read = Mock(return_value=row)
    operation = Mock()
    with pytest.raises(SourceConflict):
        repository.finish(
            key,
            ADMIN,
            2 if fault == "stale" else 3,
            now=NOW + timedelta(seconds=10) if fault == "expired" else NOW,
            operation=operation,
        )
    operation.assert_not_called()


def test_completed_review_replay_returns_original_outcome_without_operation(monkeypatch):
    from contextlib import nullcontext

    from kvk.dal import source_admin_review_dal as dal

    key, update = str(uuid4()), str(uuid4())
    cursor = Mock()
    row = dict(ReviewID=key, Version=2, ReviewState="completed", outcome={"update_id": update})
    monkeypatch.setattr(dal, "transaction", lambda _: nullcontext(cursor))
    monkeypatch.setattr(dal, "one", Mock(return_value={"KVK_NO": 16}))
    monkeypatch.setattr(dal, "lock_scope", Mock())
    repository = dal.SourceAdminReviewDAL(Mock())
    repository._read = Mock(return_value=row)
    operation = Mock()
    assert (
        repository.finish(key, ADMIN, 1, now=NOW, operation=operation)["outcome"]["update_id"]
        == update
    )
    operation.assert_not_called()


def test_cancelled_review_never_executes_prepared_operation(monkeypatch):
    from contextlib import nullcontext

    from kvk.dal import source_admin_review_dal as dal

    key = str(uuid4())
    cursor = Mock()
    row = dict(ReviewID=key, Version=1, ReviewState="pending", ExpiresUTC=NOW.replace(tzinfo=None))
    cancelled = row | dict(
        ReviewState="cancelled", Version=2, outcome={"state": "cancelled; accepted inputs retained"}
    )
    monkeypatch.setattr(dal, "transaction", lambda _: nullcontext(cursor))
    monkeypatch.setattr(dal, "one", Mock(side_effect=[{"KVK_NO": 16}, {"ReviewID": key}]))
    monkeypatch.setattr(dal, "lock_scope", Mock())
    repository = dal.SourceAdminReviewDAL(Mock())
    repository._read = Mock(side_effect=[row, cancelled])
    operation = Mock()
    assert repository.finish(key, ADMIN, 1, now=NOW, operation=operation, cancel=True) == cancelled
    operation.assert_not_called()


def retained_pair(repo, service):
    saved = pair(service)["payload"]["context"]
    fields = dict(
        kvk_no="KVK_NO",
        period_id="PeriodID",
        period_key="PeriodKey",
        choice_id="ChoiceID",
        config_version_id="ConfigVersionID",
        roster_id="RosterID",
        coverage_start_utc="CoverageStartUTC",
        coverage_end_utc="CoverageEndUTC",
        as_of_utc="AsOfUTC",
        update_kind="UpdateKind",
        request_id="RequestID",
        base_update_id="BaseUpdateID",
    )
    from datetime import datetime

    row = {
        column: (
            datetime.fromisoformat(saved[key]).replace(tzinfo=None)
            if key.endswith("_utc")
            else saved[key]
        )
        for key, column in fields.items()
    }
    row.update(
        UpdateID=saved["update_id"],
        ConfirmedBy=str(ADMIN.user_id),
        ConfirmedUTC=NOW.replace(tzinfo=None),
        ConfirmationJson=saved["confirmation_json"],
        UpdateState="waiting_aggregate",
        EndScanID=18,
    )
    repo.read_update = Mock(return_value=row)
    return row


def test_second_side_keeps_waiting_update_identity_and_original_confirmation():
    repo = Reviews()
    service = SourceAdminReviewService(ACCESS, repo, lambda: NOW)
    retained = retained_pair(repo, service)
    saved = pair(service, update_id=retained["UpdateID"], reason="Second file arrived")["payload"][
        "context"
    ]
    assert saved["update_id"] == retained["UpdateID"]
    assert saved["confirmation_json"] == retained["ConfirmationJson"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("ConfirmedBy", "other"),
        ("UpdateState", "selected"),
        ("KVK_NO", 99),
        ("EndScanID", 19),
        ("ConfigVersionID", "other"),
    ],
)
def test_waiting_pair_cannot_be_reowned_retagged_or_reopened(field, value):
    repo = Reviews()
    service = SourceAdminReviewService(ACCESS, repo, lambda: NOW)
    retained = retained_pair(repo, service)
    retained[field] = value
    with pytest.raises(SourceConflict):
        pair(service, update_id=retained["UpdateID"])


@pytest.mark.parametrize(
    "attest,compatible,expected_pairs", [(False, True, 0), (True, False, 0), (True, True, 1)]
)
def test_configuration_confirmation_requires_explicit_compatible_counterpart(
    monkeypatch, attest, compatible, expected_pairs
):
    import kvk.dal.new_source_import_dal as import_dal
    import kvk.services.new_source_config_service as config_module
    import kvk.services.source_admin_review_service as module

    repository = Reviews()
    service = SourceAdminReviewService(ACCESS, repository, lambda: NOW)
    period = dict(
        period_id=str(uuid4()),
        period_key="fight:two",
        base_config_id=str(uuid4()),
        desired_window=dict(StartScanID=17, EndScanID=18),
        base_update=dict(
            EndScanID=18,
            AggregateRevisionID=str(uuid4()),
            CoverageStartUTC="2026-09-01T00:00:00Z",
            CoverageEndUTC="2026-09-02T00:00:00Z",
            AsOfUTC="2026-09-02T01:00:00Z",
        ),
    )
    context = dict(snapshot=configuration(), periods=[period], season_version=2)
    repository.configuration_context = Mock(return_value=deepcopy(context))
    monkeypatch.setattr(module, "SourceAdminReviewDAL", lambda _: repository)
    request = dict(RequestID=str(uuid4()), DesiredConfigVersionID=str(uuid4()))
    request_call = Mock(return_value=request)
    monkeypatch.setattr(config_module, "request_configuration_update", request_call)
    monkeypatch.setattr(
        import_dal,
        "rows",
        lambda _: [dict(MappingDigest=b"a"), dict(MappingDigest=b"a" if compatible else b"b")],
    )
    prepare = Mock(return_value=dict(ReviewID=str(uuid4()), Version=1))
    confirm = Mock(
        return_value=dict(outcome=dict(update_id="exact-update", state="waiting_player"))
    )
    monkeypatch.setattr(module.SourceAdminReviewService, "prepare_match", prepare)
    monkeypatch.setattr(module.SourceAdminReviewService, "confirm", confirm)
    locked = dict(
        ReviewID=str(uuid4()),
        KVK_NO=16,
        payload=context | dict(reason="Reviewed imported correction", attest_counterparts=attest),
    )
    result = service._confirm_configuration(ADMIN, locked, Mock(), Mock())
    assert prepare.call_count == confirm.call_count == expected_pairs
    assert request_call.call_args.kwargs["new_end_scan_id"] == 18
    if expected_pairs:
        assert prepare.call_args.kwargs["action"] == "correct"
        assert (
            prepare.call_args.kwargs["counterpart_revision_id"]
            == period["base_update"]["AggregateRevisionID"]
        )
        assert result["periods"][0]["update_id"] == "exact-update"


def test_changed_configuration_is_rejected_before_any_request(monkeypatch):
    import kvk.services.new_source_config_service as config_module
    import kvk.services.source_admin_review_service as module

    repository = Reviews()
    repository.configuration_context = Mock(
        return_value=dict(snapshot=configuration(), periods=[], season_version=3)
    )
    monkeypatch.setattr(module, "SourceAdminReviewDAL", lambda _: repository)
    request = Mock()
    monkeypatch.setattr(config_module, "request_configuration_update", request)
    locked = dict(KVK_NO=16, payload=dict(snapshot=configuration(), periods=[], season_version=2))
    with pytest.raises(SourceConflict):
        SourceAdminReviewService(ACCESS, repository)._confirm_configuration(
            ADMIN, locked, Mock(), Mock()
        )
    request.assert_not_called()
