"""Synthetic service and transaction tests; never connect to retained or production SQL."""

from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import Acceptance, SourceConflict, UncertainCommit, canonical
from kvk.services.new_source_admin_service import (
    SourceAccess,
    SourceActor,
    SourceAdminService,
    utc_text,
)
from kvk.services.new_source_artifact_store import ArtifactStore
from tests.kvk_source_fixtures import aggregate_bytes, player_bytes, player_row, rewrite_zip

NOW = datetime(2026, 9, 11, tzinfo=UTC)
ADMIN = SourceActor(10, 20, 30, frozenset())
UPLOADER = SourceActor(11, 20, 30, frozenset({40}))
ACCESS = SourceAccess(True, 20, 30, 10, frozenset({40}), frozenset({31}))
FIELDS = {
    "kind": "players",
    "period": "fight:pass4",
    "precision": "minute",
    "scan_start": "2026-09-05T15:26Z",
    "kingdoms": "101,102",
}


class MemoryRepository:
    """Fake destination for S5A policy tests, not evidence of SQL concurrency."""

    def __init__(self):
        self.receipts, self.accepted = {}, {}
        self.guard = {
            "period": None,
            "selection": None,
            "config": None,
            "mapping": [],
            "revision": None,
        }
        self.calls = []

    def create_receipt(self, *, artifact, admission, filename, kvk_no, payload):
        for row in self.receipts.values():
            if (
                row["MessageID"] == admission.message_id
                and row["AttachmentID"] == admission.attachment_id
            ):
                return deepcopy(row)
        rid = str(uuid4())
        self.receipts[rid] = {
            "AttemptID": rid,
            "ActorID": admission.actor,
            "GuildID": admission.guild_id,
            "ChannelID": admission.channel_id,
            "MessageID": admission.message_id,
            "AttachmentID": admission.attachment_id,
            "KVK_NO": kvk_no,
            "OriginalFilename": filename,
            "ArtifactHash": bytes.fromhex(artifact.sha256),
            "ByteCount": artifact.byte_count,
            "StorageKey": artifact.storage_key,
            "payload": payload,
            "Status": "received",
            "ObservationRevisionID": None,
            "AggregateRevisionID": None,
        }
        return deepcopy(self.receipts[rid])

    def read_receipt(self, rid, actor, guild):
        row = self.receipts[rid]
        if (row["ActorID"], row["GuildID"]) != (actor, guild):
            raise SourceConflict("owner scope")
        return deepcopy(row)

    def context(self, *args):
        return deepcopy(self.guard)

    def prepare(self, rid, actor, guild, version, proposal):
        row = self.read_receipt(rid, actor, guild)
        if row["payload"]["version"] != version:
            raise SourceConflict("stale")
        row["payload"]["history"].append({"proposal": row["payload"].get("proposal")})
        row["payload"].update(version=version + 1, proposal=deepcopy(proposal))
        row["payload"].pop("outcome", None)
        row.update(Status="validated", ObservationRevisionID=None, AggregateRevisionID=None)
        self.receipts[rid] = row
        return deepcopy(row)

    def confirm(self, rid, actor, guild, version, operation):
        row = self.read_receipt(rid, actor, guild)
        if row["payload"]["version"] != version:
            raise SourceConflict("stale")
        if row["payload"].get("outcome"):
            return row
        if canonical(self.guard) != canonical(row["payload"]["proposal"]["guard"]):
            raise SourceConflict("changed selection")
        result = operation(row, self, None)
        row["payload"]["outcome"] = result
        row.update(
            Status="accepted",
            ObservationRevisionID=result.get("observation_revision_id"),
            AggregateRevisionID=result.get("aggregate_revision_id"),
        )
        self.receipts[rid] = row
        return deepcopy(row)

    def accept_observation(self, prepared, artifact, admission):
        self.calls.append((prepared, admission))
        key = (prepared.metadata.event_identity, prepared.digest.sha256)
        duplicate = key in self.accepted
        if not duplicate:
            self.accepted[key] = str(uuid4())
        return Acceptance(self.accepted[key], "event", len(self.accepted), duplicate, True)

    def accept_aggregate(self, prepared, artifact, admission):
        result = self.accept_observation(prepared, artifact, admission)
        return replace(result, logical_scan_id=None)

    def onboard(self, cursor, **kwargs):
        self.calls.append(kwargs)
        return {"config_id": str(uuid4()), "state": "configuration approved; not published"}

    def correct_roster(self, cursor, **kwargs):
        self.calls.append(kwargs)
        return {
            "roster_id": "new-roster",
            "roster_version": 2,
            "observation_revision_id": kwargs["proposal"]["b0_revision"],
            "state": "roster correction approved; existing publications retained",
        }


@pytest.fixture
def rig(tmp_path):
    repo = MemoryRepository()
    store = ArtifactStore(tmp_path)
    service = SourceAdminService(ACCESS, repo, store, now=lambda: NOW)
    return service, repo


def upload(
    service, *, actor=ADMIN, content=None, filename="kvk16_players_20260905T1526Z.xlsx", **kwargs
):
    return service.stage_upload(
        actor,
        filename=filename,
        content=content or player_bytes(),
        message_id=uuid4().hex,
        attachment_id="1",
        **kwargs,
    )


def prepare(service, row, *, fields=None, actor=ADMIN, **kwargs):
    return service.prepare_metadata(
        actor,
        row["AttemptID"],
        row["payload"]["version"],
        fields or FIELDS,
        reason="Synthetic reviewed metadata",
        **kwargs,
    )


def test_receipt_survives_service_recreation_and_duplicate_click(rig):
    service, repo = rig
    row = prepare(service, upload(service))
    fresh = SourceAdminService(ACCESS, repo, service.artifacts, now=lambda: NOW)
    accepted = fresh.confirm(ADMIN, row["AttemptID"], 2)
    assert accepted["Status"] == "accepted"
    assert "not published" in fresh.summary(accepted)
    assert fresh.confirm(ADMIN, row["AttemptID"], 2) == accepted
    assert len(repo.calls) == 1


def test_semantic_reexport_and_utc_scan_start(rig):
    service, repo = rig
    content = player_bytes()
    for raw in (content, rewrite_zip(content)):
        row = prepare(service, upload(service, content=raw))
        result = service.confirm(ADMIN, row["AttemptID"], 2)
    assert result["payload"]["outcome"]["state"] == "duplicate"
    assert len(repo.accepted) == 1
    assert repo.calls[-1][0].metadata.candidate.scan_start_utc == utc_text(FIELDS["scan_start"])
    assert repo.calls[-1][0].metadata.candidate.scan_start_utc != NOW


@pytest.mark.parametrize(
    "actor",
    [
        replace(ADMIN, guild_id=99),
        replace(ADMIN, channel_id=99),
        replace(UPLOADER, role_ids=frozenset()),
        replace(ADMIN, user_id=0),
    ],
)
def test_access_rejects_before_private_storage(rig, actor):
    service, repo = rig
    with pytest.raises(PermissionError):
        upload(service, actor=actor)
    assert not repo.receipts


@pytest.mark.parametrize("action", ["finalize", "correct", "configure", "activate"])
def test_privileged_actions_fail_for_uploader(action):
    with pytest.raises(PermissionError):
        ACCESS.authorize(UPLOADER, action)


@pytest.mark.parametrize("case", ["expired", "owner", "version", "selection", "role"])
def test_confirm_revalidates_owner_privilege_time_and_versions(rig, case):
    service, repo = rig
    row = prepare(service, upload(service))
    actor, version = ADMIN, 2
    if case == "expired":
        service.now = lambda: NOW + timedelta(minutes=5)
    if case == "owner":
        actor = UPLOADER
    if case == "version":
        version = 1
    if case == "selection":
        repo.guard["selection"] = {"SelectionVersion": 9}
    if case == "role":
        service.access = replace(ACCESS, admin_id=99)
    with pytest.raises((PermissionError, SourceConflict)):
        service.confirm(actor, row["AttemptID"], version)
    assert not repo.calls


@pytest.mark.parametrize(
    "changed",
    [
        {"scan_start": "2026-03-29T01:30+01:00"},
        {"scan_start": "2026-10-25T01:30"},
        {"kingdoms": "101,101"},
        {"period": "fight:unknown space"},
    ],
)
def test_metadata_failures_do_not_accept(rig, changed):
    service, repo = rig
    with pytest.raises(ValueError):
        prepare(service, upload(service), fields={**FIELDS, **changed})
    assert not repo.calls


def test_ambiguous_b0_uses_explicit_season_and_attested_time(rig):
    service, repo = rig
    row = upload(service, filename="KVK_16_Baseline.xlsx", season=16)
    row = prepare(service, row, fields={**FIELDS, "scan_start": "2026-08-26T04:07Z"})
    service.confirm(ADMIN, row["AttemptID"], 2)
    assert repo.calls[0][0].metadata.candidate.scan_start_utc == utc_text("2026-08-26T04:07Z")


@pytest.mark.parametrize(
    "content",
    [
        b"not a workbook",
        player_bytes([player_row(), player_row()]),
        player_bytes([player_row(-1)]),
        player_bytes(headers=("Unknown",)),
    ],
)
def test_invalid_workbook_keeps_durable_received_state(rig, content):
    service, repo = rig
    row = upload(service, content=content)
    with pytest.raises(ValueError):
        prepare(service, row)
    assert repo.receipts[row["AttemptID"]]["Status"] == "received"
    assert not repo.calls


def aggregate_guard(repo):
    repo.guard.update(
        config={"ConfigVersionID": "config", "StartScanID": 10, "EndScanID": 13},
        mapping=[
            {"Kingdom": 101, "CampID": 1, "CampName": "North Camp"},
            {"Kingdom": 102, "CampID": 2, "CampName": "South Camp"},
        ],
    )


def test_live_to_final_same_content_is_an_explicit_admin_action(rig):
    service, repo = rig
    aggregate_guard(repo)
    fields = {
        **FIELDS,
        "kind": "aggregate",
        "scan_start": "2026-09-06T13:04Z",
        "coverage_start": FIELDS["scan_start"],
        "coverage_end": "2026-09-06T13:04Z",
        "as_of": "2026-09-06T13:04Z",
        "state": "final",
    }
    row = upload(
        service, content=aggregate_bytes(), filename="kvk16_pass4_totals_live_20260906T1304Z.xlsx"
    )
    with pytest.raises(PermissionError):
        prepare(service, row, fields=fields)
    repo.guard["revision"] = {"SelectedRevisionID": "prior", "SelectionVersion": 3}
    with pytest.raises(SourceConflict):
        prepare(
            service,
            row,
            fields=fields,
            action="finalize",
            expected_revision="prior",
            expected_revision_version=2,
        )
    row = prepare(
        service,
        row,
        fields=fields,
        action="finalize",
        expected_revision="prior",
        expected_revision_version=3,
    )
    result = service.confirm(ADMIN, row["AttemptID"], 2)
    assert result["payload"]["outcome"]["scan_id"] is None
    assert repo.calls[-1][1].admin_authorized is True


def test_equal_endpoints_reject_aggregate_before_acceptance(rig):
    service, repo = rig
    aggregate_guard(repo)
    repo.guard["config"]["EndScanID"] = 10
    row = upload(
        service, content=aggregate_bytes(), filename="kvk16_pass4_totals_live_20260906T1304Z.xlsx"
    )
    fields = {
        **FIELDS,
        "kind": "aggregate",
        "scan_start": "2026-09-06T13:04Z",
        "coverage_start": FIELDS["scan_start"],
        "coverage_end": "2026-09-06T13:04Z",
        "as_of": "2026-09-06T13:04Z",
        "state": "live",
    }
    with pytest.raises(SourceConflict, match="equal-endpoint"):
        prepare(service, row, fields=fields)
    assert not repo.calls


def accepted_b0(service):
    row = prepare(service, upload(service))
    return service.confirm(ADMIN, row["AttemptID"], 2)


def test_initial_configuration_is_reviewed_and_retains_b0(rig):
    service, repo = rig
    row = accepted_b0(service)
    row = service.prepare_configuration(
        ADMIN,
        row["AttemptID"],
        2,
        window="fight:pass4 | Pass 4 | 10 | 13",
        coverage="2026-09-05T15:26Z | 2026-09-07T07:21Z",
        mapping="101 | 1 | North Camp\n102 | 2 | South Camp",
        weights="10 | 20 | 40 | 2026-09-01T00:00Z",
        reason="Approve synthetic B0 configuration",
    )
    assert len(repo.calls) == 1
    result = service.confirm(ADMIN, row["AttemptID"], 3)
    assert repo.calls[-1]["b0_revision_id"] == result["ObservationRevisionID"]
    assert "not published" in result["payload"]["outcome"]["state"]


def test_expired_configuration_can_be_reprepared_from_durable_receipt(rig):
    service, repo = rig
    accepted = accepted_b0(service)
    aggregate_guard(repo)
    arguments = dict(
        window="fight:pass4 | Pass 4 | 10 | 14",
        coverage="",
        mapping="",
        weights="",
        reason="Reviewed endpoint",
    )
    draft = service.prepare_configuration(ADMIN, accepted["AttemptID"], 2, **arguments)
    service.now = lambda: NOW + timedelta(minutes=6)
    with pytest.raises(SourceConflict, match="expired"):
        service.confirm(ADMIN, draft["AttemptID"], 3)
    renewed = service.prepare_configuration(ADMIN, draft["AttemptID"], 3, **arguments)
    result = service.confirm(ADMIN, renewed["AttemptID"], 4)
    assert result["ObservationRevisionID"] == accepted["ObservationRevisionID"]


@pytest.mark.parametrize("start,end", [(10, 14), (11, 14), (10, 10), (12, None)])
def test_endpoint_configuration_needs_no_second_correction(rig, start, end):
    service, repo = rig
    row = accepted_b0(service)
    aggregate_guard(repo)
    row = service.prepare_configuration(
        ADMIN,
        row["AttemptID"],
        2,
        window=f"fight:pass4 | Pass 4 | {start} | {end or ''}",
        coverage="",
        mapping="",
        weights="",
        reason="Authorized endpoint update",
    )
    result = service.confirm(ADMIN, row["AttemptID"], 3)
    assert result["Status"] == "accepted"
    assert repo.calls[-1]["proposal"]["configuration"]["end"] == end
    assert repo.calls[-1]["proposal"]["action"] == "configure"


def test_endpoint_update_rejects_reversed_bounds_and_component_smuggling(rig):
    service, repo = rig
    row = accepted_b0(service)
    aggregate_guard(repo)
    for window, mapping in [
        ("fight:pass4 | Fight | 14 | 13", ""),
        ("fight:pass4 | Fight | 10 | 14", "101 | 1 | North"),
    ]:
        with pytest.raises(ValueError):
            service.prepare_configuration(
                ADMIN,
                row["AttemptID"],
                2,
                window=window,
                coverage="",
                mapping=mapping,
                weights="",
                reason="Synthetic change",
            )


def test_dal_receipt_owner_predicate_and_borrowed_connection():
    from kvk.dal.new_source_admin_dal import SourceAdminDAL, _BorrowedConnection

    cursor = Mock()
    cursor.fetchone.return_value = None
    with pytest.raises(SourceConflict):
        SourceAdminDAL._receipt(cursor, "receipt", "owner", "guild")
    sql, *params = cursor.execute.call_args.args
    assert "ActorID=?" in sql and "GuildID=?" in sql and "SourceKey=?" in sql
    assert params == ["receipt", "owner", "guild", "snapshot_report_v1", "s5a_draft"]
    connection = _BorrowedConnection(cursor)
    connection.commit()
    connection.rollback()
    connection.close()
    assert connection.cursor() is cursor
    cursor.commit.assert_not_called()


@pytest.mark.parametrize("failure", [None, "operation", "commit"])
def test_dal_confirmation_transaction_owns_atomic_acceptance(monkeypatch, failure):
    from kvk.dal import new_source_admin_dal as module

    guard = {"config": None}
    row = {
        "AttemptID": "receipt",
        "KVK_NO": 16,
        "Status": "validated",
        "payload": {"version": 2, "proposal": {"candidate": {}, "guard": guard}},
    }
    cursor = Mock()
    connection = Mock(autocommit=False)
    connection.cursor.return_value = cursor
    if failure == "commit":
        connection.commit.side_effect = RuntimeError("lost acknowledgement")
    dal = module.SourceAdminDAL(lambda: connection, Mock())
    monkeypatch.setattr(dal, "read_receipt", lambda *args: deepcopy(row))
    monkeypatch.setattr(dal, "_receipt", lambda *args: deepcopy(row))
    monkeypatch.setattr(dal, "_context", lambda *args: guard)
    operation = Mock(return_value={"observation_revision_id": "revision", "state": "accepted"})
    if failure == "operation":
        operation.side_effect = ValueError("synthetic failure")
    if failure:
        with pytest.raises(ValueError if failure == "operation" else UncertainCommit):
            dal.confirm("receipt", "owner", "guild", 2, operation)
    else:
        dal.confirm("receipt", "owner", "guild", 2, operation)
    assert connection.commit.call_count == (0 if failure == "operation" else 1)
    assert connection.rollback.call_count == (1 if failure == "operation" else 0)
    connection.close.assert_called_once()
    assert operation.call_count == 1


def test_disabled_factory_never_creates_artifacts_or_connection(monkeypatch):
    import bot_config
    from kvk.services import new_source_admin_service as service

    monkeypatch.setattr(bot_config, "KVK_SOURCE_INTAKE_ENABLED", False)
    artifact = Mock(side_effect=AssertionError("no filesystem"))
    monkeypatch.setattr(service, "ArtifactStore", artifact)
    with pytest.raises(PermissionError):
        service.configured_service()
    artifact.assert_not_called()


@pytest.mark.parametrize("change", ["roster", "scope"])
def test_onboarding_rejects_roster_growth_or_unmapped_b0_before_writes(monkeypatch, change):
    from kvk.dal import new_source_admin_dal as module

    cursor = Mock()
    retained = [{"RosterID": "retained", "B0RevisionID": "old"}] if change == "roster" else []
    answers = iter([retained, [{"GovernorID": 1001, "kingdom": 999, "power": 1}]])
    monkeypatch.setattr(module, "rows", lambda c: next(answers))
    dal = module.SourceAdminDAL(Mock(), Mock())
    with pytest.raises(SourceConflict):
        dal.onboard(
            cursor,
            kvk_no=16,
            proposal={"configuration": {"mapping": [(101, 1, "North")]}, "guard": {"config": None}},
            b0_revision_id="b0",
            actor="admin",
            reason="approved",
            utc=NOW,
        )
    assert all("INSERT" not in call.args[0] for call in cursor.execute.call_args_list)


def test_real_onboarding_sql_is_parameterized_and_keeps_routing_disabled(monkeypatch):
    from kvk.dal import new_source_admin_dal as module

    cursor = Mock()
    row_answers = iter([[], [{"GovernorID": 1001, "kingdom": 101, "power": 1}]])
    one_answers = iter([{"n": 1}, None])
    monkeypatch.setattr(module, "rows", lambda c: next(row_answers))
    monkeypatch.setattr(module, "one", lambda c: next(one_answers))
    spec = {
        "period_key": "fight:pass4",
        "label": "Synthetic label",
        "start": 10,
        "end": 13,
        "coverage_start": "2026-09-05T15:26+00:00",
        "coverage_end": "2026-09-07T07:21+00:00",
        "mapping": [(101, 1, "North")],
        "weights": ["10", "20", "40", "2026-09-01T00:00+00:00"],
    }
    dal = module.SourceAdminDAL(Mock(), Mock())
    result = dal.onboard(
        cursor,
        kvk_no=16,
        proposal={
            "configuration": spec,
            "guard": {"config": None, "period": None},
            "receipt_id": "receipt",
        },
        b0_revision_id="b0",
        actor="admin",
        reason="reviewed",
        utc=NOW,
    )
    assert result["state"] == "configuration approved; not published"
    calls = cursor.execute.call_args_list
    for call in calls:
        sql, *parameters = call.args
        assert sql.count("?") == len(parameters)
        assert "Synthetic label" not in sql
    writes = [call.args[0] for call in calls if "INSERT" in call.args[0]]
    assert any("SourceRosterMember" in sql for sql in writes)
    assert any("SourceRouting" in sql and "0,1" in sql for sql in writes)
    assert not any("SourceSelection" in sql or "SourceDelivery" in sql for sql in writes)


def test_real_dal_endpoint_configuration_calls_accepted_request_api(monkeypatch):
    from kvk.dal import new_source_admin_dal as module

    request = Mock(return_value={"RequestID": "request"})
    monkeypatch.setattr(module, "snapshot_endpoint_request", request)
    dal = module.SourceAdminDAL(Mock(), Mock())
    result = dal.onboard(
        Mock(),
        kvk_no=16,
        proposal={
            "configuration": {"start": 11, "end": 14},
            "guard": {"config": {"ConfigVersionID": "base"}, "period": {"PeriodID": "period"}},
            "receipt_id": "receipt",
        },
        b0_revision_id="b0",
        actor="admin",
        reason="endpoint correction",
        utc=NOW,
    )
    assert result == {"config_request_id": "request", "state": "configuration pending"}
    assert request.call_args.kwargs["new_start_scan_id"] == 11
    assert request.call_args.kwargs["new_end_scan_id"] == 14
    assert request.call_args.kwargs["origin"] == "admin"


@pytest.mark.parametrize("change", ["mapping", "weight", "effective", "coverage"])
def test_new_period_cannot_replace_frozen_season_components(monkeypatch, change):
    from decimal import Decimal

    from kvk.dal import new_source_admin_dal as module

    cursor = Mock()
    answers = iter(
        [
            [{"RosterID": "roster", "B0RevisionID": "b0"}],
            [{"Kingdom": 101, "CampID": 1, "CampName": "North"}],
        ]
    )
    monkeypatch.setattr(module, "rows", lambda c: next(answers))
    monkeypatch.setattr(
        module,
        "one",
        lambda c: {
            "ConfigVersionID": "config",
            "WeightT4X": Decimal(10),
            "WeightT5Y": Decimal(20),
            "WeightDeadsZ": Decimal(40),
            "EffectiveFromUTC": datetime(2026, 9, 1),
        },
    )
    spec = {
        "mapping": [(101, 1, "North")],
        "weights": ["10", "20", "40", "2026-09-01T00:00+00:00"],
        "coverage_start": "2026-09-05T00:00+00:00",
        "coverage_end": None,
    }
    period = None
    if change == "mapping":
        spec["mapping"] = [(101, 2, "South")]
    elif change == "weight":
        spec["weights"][0] = "99"
    elif change == "effective":
        spec["weights"][3] = "2026-09-02T00:00+00:00"
    else:
        period = {"CoverageStartUTC": datetime(2026, 9, 4), "CoverageEndUTC": None}
    with pytest.raises(SourceConflict):
        module.SourceAdminDAL(Mock(), Mock()).onboard(
            cursor,
            kvk_no=16,
            proposal={"configuration": spec, "guard": {"config": None, "period": period}},
            b0_revision_id="b0",
            actor="admin",
            reason="test",
            utc=NOW,
        )
    assert all("INSERT" not in call.args[0] for call in cursor.execute.call_args_list)


def roster_guard(revision):
    return {
        "roster": {"RosterID": "roster", "RosterVersion": 1, "B0RevisionID": "old"},
        "candidate_revision": revision,
        "member_digest": "00" * 32,
        "member_count": 4,
        "diff": {"added": [1005], "removed": [1003], "changed": [1002]},
        "publications": [
            {
                "PublicationID": "00000000-0000-4000-8000-000000000007",
                "SelectionVersion": 3,
                "PeriodState": "final",
            }
        ],
    }


def test_roster_correction_explicit_plan_resume_and_no_automatic_publication(rig):
    service, repo = rig
    receipt = accepted_b0(service)
    repo.guard = roster_guard(receipt["ObservationRevisionID"])
    preview = service.roster_preview(ADMIN, receipt["AttemptID"])
    assert "added=1, removed=1, changed=1" in service.summary(preview)
    assert "1005" not in service.summary(preview)
    plan = repo.guard["publications"][0]["PublicationID"] + " | retain"
    reviewed = service.prepare_roster_correction(
        ADMIN,
        receipt["AttemptID"],
        2,
        reason="Reviewed original B0 correction",
        publication_plan=plan,
    )
    fresh = SourceAdminService(ACCESS, repo, service.artifacts, now=lambda: NOW)
    outcome = fresh.confirm(ADMIN, reviewed["AttemptID"], 3)
    assert outcome["payload"]["outcome"]["roster_version"] == 2
    assert "retained" in outcome["payload"]["outcome"]["state"]
    assert repo.calls[-1]["proposal"]["publication_plan"] == {plan.split(" | ")[0]: "retain"}
    assert fresh.confirm(ADMIN, reviewed["AttemptID"], 3) == outcome
    assert repo.guard["publications"][0]["SelectionVersion"] == 3


@pytest.mark.parametrize("case", ["role", "missing_plan", "rewrite", "stale", "expired", "no_diff"])
def test_roster_correction_rejects_unreviewed_or_changed_context(rig, case):
    service, repo = rig
    receipt = accepted_b0(service)
    repo.guard = roster_guard(receipt["ObservationRevisionID"])
    plan = repo.guard["publications"][0]["PublicationID"] + " | retain"
    if case == "missing_plan":
        plan = ""
    if case == "rewrite":
        plan = plan.replace("retain", "replace")
    if case == "no_diff":
        repo.guard["diff"] = {"added": [], "removed": [], "changed": []}
    with pytest.raises((ValueError, PermissionError)):
        reviewed = service.prepare_roster_correction(
            UPLOADER if case == "role" else ADMIN,
            receipt["AttemptID"],
            2,
            reason="Reviewed change",
            publication_plan=plan,
        )
        if case == "stale":
            repo.guard["publications"][0]["SelectionVersion"] += 1
        if case == "expired":
            service.now = lambda: NOW + timedelta(minutes=6)
        service.confirm(ADMIN, reviewed["AttemptID"], 3)
    assert len(repo.calls) == 1  # Original acceptance only.


@pytest.mark.parametrize("invalid", [None, "later_observation", "unselected", "new_kingdom"])
def test_real_roster_preview_requires_corrected_original_b0(monkeypatch, invalid):
    from kvk.dal import new_source_admin_dal as module

    roster = {
        "RosterID": "r1",
        "RosterVersion": 1,
        "B0RevisionID": "old",
        "ObservationID": "b0-event",
    }
    revision = {
        "ObservationID": "other" if invalid == "later_observation" else "b0-event",
        "SelectedRevisionID": "other" if invalid == "unselected" else "corrected",
    }
    ones = iter([roster, revision])
    old = [
        {"GovernorID": 1, "kingdom": 101, "power": 10},
        {"GovernorID": 2, "kingdom": 101, "power": 20},
    ]
    new = [
        {"GovernorID": 1, "kingdom": 101, "power": 11},
        {"GovernorID": 3, "kingdom": 999 if invalid == "new_kingdom" else 101, "power": 30},
    ]
    answers = iter([old, new, []])
    monkeypatch.setattr(module, "one", lambda c: next(ones))
    monkeypatch.setattr(module, "rows", lambda c: next(answers))
    cursor = Mock()
    if invalid:
        with pytest.raises(SourceConflict):
            module.SourceAdminDAL._roster_context(cursor, 16, "corrected")
    else:
        result = module.SourceAdminDAL._roster_context(cursor, 16, "corrected")
        assert result["diff"] == {"added": [3], "removed": [2], "changed": [1]}
        assert result["member_count"] == 2
    assert all("INSERT" not in c.args[0] for c in cursor.execute.call_args_list)


def test_real_roster_write_appends_only_new_version_and_members(monkeypatch):
    from kvk.dal import new_source_admin_dal as module

    members = [{"GovernorID": 3, "kingdom": 101, "power": None}]
    monkeypatch.setattr(module, "rows", lambda c: members)
    guard = roster_guard("corrected")
    guard["member_digest"] = module.digest(members).hex()
    cursor = Mock()
    result = module.SourceAdminDAL(Mock(), Mock()).correct_roster(
        cursor,
        kvk_no=16,
        proposal={
            "guard": guard,
            "b0_revision": "corrected",
            "receipt_id": "receipt",
            "publication_plan": {"publication": "retain"},
        },
        actor="admin",
        reason="reviewed",
        utc=NOW,
    )
    assert result["roster_version"] == 2
    for call in cursor.execute.call_args_list:
        sql, *params = call.args
        assert sql.count("?") == len(params)
        assert "UPDATE" not in sql and "DELETE" not in sql
        assert "SourceSelection" not in sql and "SourceConfigVersion" not in sql


def test_s5a_accepted_final_report_composes_with_real_publication_service(rig):
    from kvk.models.new_source_reporting import AggregateSelection
    from kvk.services.new_source_publication_service import PublicationService
    from tests.kvk_source_fixtures import calculation_config, worked_calculation_inputs

    service, repo = rig
    aggregate_guard(repo)
    fields = {
        **FIELDS,
        "kind": "aggregate",
        "scan_start": "2026-09-07T15:26Z",
        "coverage_start": FIELDS["scan_start"],
        "coverage_end": "2026-09-07T15:26Z",
        "as_of": "2026-09-07T15:26Z",
        "state": "final",
    }
    receipt = upload(
        service, content=aggregate_bytes(), filename="kvk16_pass4_totals_final_20260907T1526Z.xlsx"
    )
    reviewed = prepare(service, receipt, fields=fields, action="finalize")
    accepted = service.confirm(ADMIN, reviewed["AttemptID"], 2)
    report = repo.calls[-1][0]
    aggregate = AggregateSelection("report", accepted["AggregateRevisionID"], report)
    b0, start, middle, end = worked_calculation_inputs()
    publisher = PublicationService(Mock(side_effect=AssertionError("No SQL target authorized")))
    publisher.dal = Mock()
    publisher.dal.build_candidate.return_value = {"Generation": 7}
    publisher.dal.select_publication.return_value = {"NewSelectionVersion": 4}
    candidate = publisher.build_candidate(
        config=calculation_config(), observations=(start, middle, end), b0=b0, aggregate=aggregate
    )
    assert candidate.snapshot.period_state.value == "final"
    assert candidate.snapshot.aggregate.report is report
    assert len(candidate.snapshot.calculation.players) == len(b0.observation.rows)
    outcome = publisher.select_publication(
        candidate,
        action_id="action",
        actor="admin",
        reason="Reviewed final",
        action_type="finalize",
        admin_authorized=True,
        expected_selection_version=3,
        expected_routing_version=1,
        destinations=(),
    )
    assert outcome["NewSelectionVersion"] == 4
    delegated = publisher.dal.select_publication.call_args.kwargs
    assert delegated["expected_selection_version"] == 3
    assert delegated["publication_id"] == candidate.snapshot.publication_id
    assert delegated["destinations"] == ()
    assert callable(delegated["validate_inputs"])


def test_reviewed_endpoint_request_composes_interim_final_and_replacement(rig):
    from kvk.models.new_source_reporting import EndpointChange
    from kvk.services.new_source_publication_service import PublicationService
    from tests.kvk_source_fixtures import (
        calculation_config,
        calculation_event,
        worked_calculation_inputs,
    )

    service, repo = rig
    receipt = accepted_b0(service)
    aggregate_guard(repo)
    reviewed = service.prepare_configuration(
        ADMIN,
        receipt["AttemptID"],
        2,
        window="fight:pass4 | Pass 4 | 10 | 14",
        coverage="",
        mapping="",
        weights="",
        reason="Approved end 14",
    )
    service.confirm(ADMIN, reviewed["AttemptID"], 3)
    approved = repo.calls[-1]["proposal"]
    b0, start, middle, end = worked_calculation_inputs()
    next_live = calculation_event(12, day=6)
    next_live = replace(
        next_live,
        observation=replace(
            next_live.observation,
            metadata=replace(
                next_live.observation.metadata,
                candidate=replace(
                    next_live.observation.metadata.candidate,
                    scan_start_utc=middle.scan_start_utc + timedelta(hours=1),
                ),
            ),
        ),
    )
    replacement = calculation_event(14, day=8)
    publisher = PublicationService(Mock(side_effect=AssertionError("No SQL target authorized")))
    publisher.dal = Mock()
    publisher.dal.build_candidate.return_value = {"Generation": 1}
    config = calculation_config()
    candidates = [
        publisher.build_candidate(config=config, observations=observations, b0=b0)
        for observations in (
            (start, middle),
            (start, middle, next_live),
            (start, middle, next_live, end),
        )
    ]
    assert [
        (
            c.snapshot.calculation.selection.start.logical_scan_id,
            c.snapshot.calculation.selection.end.logical_scan_id,
        )
        for c in candidates
    ] == [(10, 11), (10, 12), (10, 13)]
    updated = replace(config, version_id="config-2", end_scan_id=approved["configuration"]["end"])
    change = EndpointChange(
        "request",
        config.period_id,
        config.version_id,
        updated.version_id,
        13,
        14,
        "admin",
        approved["reason"],
    )
    previous = candidates[-1].snapshot.calculation.selection
    pending = publisher.build_candidate(
        config=updated,
        observations=(start, middle, next_live, end),
        b0=b0,
        previous=previous,
        endpoint_change=change,
    )
    assert pending.snapshot.player_state.value == "live"
    corrected = publisher.build_candidate(
        config=updated,
        observations=(start, middle, next_live, end, replacement),
        b0=b0,
        previous=previous,
        endpoint_change=change,
    )
    assert corrected.snapshot.player_state.value == "corrected_final"
    assert corrected.snapshot.calculation.selection.end.logical_scan_id == 14
    publisher.select_publication(
        corrected,
        action_id="endpoint-action",
        expected_selection_version=3,
        expected_routing_version=1,
        actor="admin",
        reason=approved["reason"],
        action_type="endpoint_update",
        request_id=change.request_id,
        destinations=(),
    )
    assert publisher.dal.select_publication.call_args.kwargs["action_type"] == "endpoint_update"
    assert publisher.dal.select_publication.call_args.kwargs["request_id"] == "request"
