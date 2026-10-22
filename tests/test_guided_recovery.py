"""Recovery outcome/authorization/restart tests with a durable-store contract fake."""

from copy import deepcopy
from datetime import UTC, datetime
from threading import Lock
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit
from services.import_recovery_service import ImportRecoveryAdapter
from services.recovery_service import RecoveryActor, RecoveryService

ACTOR = RecoveryActor(1, 2, 3)


class Store:
    def __init__(self):
        self.row = None
        self.actions = []
        self.lock = Lock()
        self.lose_claim_ack = False

    def observe(self, kind, source_id, evidence, token, *, resolved=False):
        state = "resolved" if resolved else "open"
        with self.lock:
            if self.row is None:
                self.row = dict(
                    IncidentID=str(uuid4()),
                    SourceKind=kind,
                    SourceID=source_id,
                    Revision=0,
                    EvidenceHash=None,
                    State="open",
                    FirstSeenUTC=datetime.now(UTC),
                )
            if (self.row["EvidenceHash"], self.row["State"]) != (token, state):
                self.row["Revision"] += 1
            self.row.update(
                evidence=evidence,
                EvidenceHash=token,
                State=state,
                LastSeenUTC=datetime.now(UTC),
            )
            return deepcopy(self.row)

    def get(self, key):
        assert key == self.row["IncidentID"]
        return deepcopy(self.row)

    def pending_actions(self, key):
        return [deepcopy(a) for a in self.actions if a["State"] in {"dispatched", "unknown"}]

    def latest_publication_action(self, key):
        self.get(key)
        return next(
            (
                deepcopy(a)
                for a in reversed(self.actions)
                if a["ActionKind"] == "verify_publication"
            ),
            None,
        )

    def claim(self, key, revision, token, kind, actor, reason):
        with self.lock:
            for action in self.actions:
                if (
                    action["State"] in {"dispatched", "unknown"}
                    or action["IncidentRevision"] == revision
                ):
                    return action["ActionID"], False
            assert (revision, token) == (self.row["Revision"], self.row["EvidenceHash"])
            action = dict(
                ActionID=str(uuid4()),
                IncidentRevision=revision,
                EvidenceHash=token,
                ActionKind=kind,
                State="dispatched",
                Actor=actor,
                Reason=reason,
                CreatedUTC=datetime.now(UTC),
                UpdatedUTC=datetime.now(UTC),
            )
            self.actions.append(action)
            if self.lose_claim_ack:
                raise UncertainCommit("lost intent commit acknowledgment")
            return action["ActionID"], True

    def finish(self, key, action_id, state, result):
        for action in self.actions:
            if action["ActionID"] == str(action_id):
                action.update(State=state, result=result, UpdatedUTC=datetime.now(UTC))


class ImportDAL:
    def __init__(self, state="partial"):
        self.state = state
        self.resolution = None
        self.version = 1
        self.calls = []
        self.lock = Lock()
        self.lose_ack = False
        self.fail = False

    def inspect(self, key):
        decision = (
            "resolved"
            if self.resolution
            else {"partial": "supersede_partial", "rolled_back": "release_failure"}.get(
                self.state, "hold"
            )
        )
        return dict(
            action=decision,
            token=f"{self.version:064x}",
            execution=dict(State=self.state, ScanOrder=17, Resolution=self.resolution),
            explanation=None,
        )

    def settle(self, key, *, token, actor, reason, allow_partial):
        with self.lock:
            if self.fail:
                raise TimeoutError("SQL unavailable")
            if self.resolution:
                return "resolved"
            if token != self.inspect(key)["token"]:
                raise SourceConflict("stale")
            assert self.state != "partial" or allow_partial
            self.calls.append((actor, reason))
            self.resolution = "supersede_partial" if self.state == "partial" else "release_failure"
            self.version += 1
            if self.lose_ack:
                raise UncertainCommit("commit succeeded, reply lost")


def setup(state="partial"):
    dal, store = ImportDAL(state), Store()
    adapter = ImportRecoveryAdapter(dal)
    service = RecoveryService(store, {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3)
    source = str(uuid4())
    evidence, token, resolved = adapter.inspect(source)
    row = store.observe(adapter.kind, source, evidence, token, resolved=resolved)
    return service, dal, store, row


def execute(service, row, actor=ACTOR, action="supersede_partial"):
    return service.execute(
        actor,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        action,
        "Reviewed the affected scan and accepted the stated consequences",
    )


def test_partial_confirmation_releases_once_and_verifies_without_import_replay():
    service, dal, store, row = setup()
    assert execute(service, row)["State"] == "resolved"
    assert execute(service, row)["State"] == "resolved"
    assert len(dal.calls) == 1
    assert store.actions[0]["State"] == "verified"


def test_lost_settlement_ack_is_read_back_and_verified():
    service, dal, store, row = setup()
    dal.lose_ack = True
    assert execute(service, row)["State"] == "resolved"
    assert len(dal.calls) == 1
    assert store.actions[0]["State"] == "verified"


def test_restart_after_lost_intent_ack_resumes_only_receipted_sql_settlement():
    service, dal, store, row = setup()
    store.lose_claim_ack = True
    with pytest.raises(UncertainCommit):
        execute(service, row)
    assert dal.calls == []
    restarted = RecoveryService(store, service.adapters, admin_id=1, guild_id=2, channel_id=3)
    assert restarted.refresh(row["IncidentID"])["State"] == "resolved"
    assert len(dal.calls) == 1
    assert dal.calls[0][0] == "recovery:" + store.actions[0]["ActionID"]


def test_unavailable_sql_keeps_original_action_then_recovers_same_identity():
    service, dal, store, row = setup()
    dal.fail = True
    assert execute(service, row)["State"] == "open"
    assert store.actions[0]["State"] == "unknown"
    assert execute(service, row)["State"] == "open"
    assert len(store.actions) == 1
    dal.fail = False
    assert service.refresh(row["IncidentID"])["State"] == "resolved"
    assert len(dal.calls) == 1


def test_changed_evidence_retires_old_sql_intent_and_requires_new_confirmation():
    service, dal, store, row = setup()
    dal.fail = True
    pending = execute(service, row)
    assert pending["pending_action"]["state"] == "unknown"
    dal.version += 1
    dal.fail = False
    fresh = service.refresh(row["IncidentID"])
    assert store.actions[0]["State"] == "not_applied"
    assert fresh["pending_action"] is None
    assert not dal.calls
    with pytest.raises(SourceConflict, match="evidence changed"):
        execute(service, row)
    assert execute(service, fresh)["State"] == "resolved"
    assert len(dal.calls) == 1 and len(store.actions) == 2


def test_normal_capture_requires_queue_admission_before_incident_closes():
    service, dal, store, row = setup("completed")
    inspected = dal.inspect(row["SourceID"])
    inspected.update(captured=True)
    dal.inspect = lambda _: inspected
    fresh = service.refresh(row["IncidentID"])
    assert fresh["State"] == "open"
    inspected["preparation"] = dict(JobID="queue-receipt")
    fresh = service.refresh(row["IncidentID"])
    assert fresh["State"] == "resolved"
    assert "Export delivery is a separate outcome" in fresh["evidence"]["explanation"]
    assert not dal.calls and not store.actions


def test_capture_verification_requires_receipt_owner_spool_and_released_resource():
    from services.stats_import_outcome_dal import StatsImportOutcomeDAL
    from tests.test_stats_import_outcomes import evidence

    prep, receipt, resources = evidence("completed")
    prep.update(State="captured", SpoolKey="captured-output", SpoolBytes=1024, SpoolHash=b"h" * 32)
    assert StatsImportOutcomeDAL.capture_completed(prep, receipt, [])
    assert not StatsImportOutcomeDAL.capture_completed(prep, receipt, resources)
    for field, value in [
        ("State", "writing"),
        ("SpoolHash", None),
        ("SpoolBytes", 0),
        ("OwnerID", str(uuid4())),
    ]:
        changed = dict(prep, **{field: value})
        assert not StatsImportOutcomeDAL.capture_completed(changed, receipt, [])


@pytest.mark.parametrize(
    "actor", [RecoveryActor(9, 2, 3), RecoveryActor(1, 9, 3), RecoveryActor(1, 2, 9)]
)
def test_permission_change_prevents_read_and_repair(actor):
    service, dal, store, row = setup()
    with pytest.raises(SourceConflict):
        service.review(actor, row["IncidentID"])
    with pytest.raises(SourceConflict):
        execute(service, row, actor)
    assert not store.actions and not dal.calls


def test_stale_preview_cannot_accept_new_evidence():
    service, dal, store, row = setup()
    dal.version += 1
    with pytest.raises(SourceConflict, match="evidence changed"):
        execute(service, row)
    assert not dal.calls and not store.actions


@pytest.mark.parametrize("state", ["running", "import_committed", "completed", "unknown"])
def test_unproven_or_completed_import_has_no_discard_button(state):
    service, dal, store, row = setup(state)
    assert row["evidence"]["actions"] == {}
    with pytest.raises(SourceConflict, match="not permitted"):
        execute(service, row)
    assert not dal.calls


def test_partial_requires_its_specific_action():
    service, dal, store, row = setup()
    with pytest.raises(SourceConflict, match="not permitted"):
        execute(service, row, action="release_failure")
    assert not dal.calls


def test_concurrent_confirmations_have_one_business_transition():
    from concurrent.futures import ThreadPoolExecutor

    service, dal, store, row = setup()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: execute(service, row), range(2)))
    assert all(r["State"] == "resolved" for r in results)
    assert len(dal.calls) == 1
    assert len(store.actions) == 1


@pytest.mark.asyncio
async def test_persistent_entry_and_preview_have_explicit_confirmation(monkeypatch):
    import bot_config
    from ui.views import recovery_view as view

    for key, val in [("ADMIN_USER_ID", 1), ("GUILD_ID", 2), ("NOTIFY_CHANNEL_ID", 3)]:
        monkeypatch.setattr(bot_config, key, val)
    service, dal, store, row = setup()
    interaction = SimpleNamespace(
        user=SimpleNamespace(id=1),
        guild_id=2,
        channel_id=3,
        response=SimpleNamespace(is_done=lambda: False, defer=AsyncMock()),
        followup=SimpleNamespace(send=AsyncMock()),
    )
    monkeypatch.setattr(view, "call", AsyncMock(return_value=row))
    assert view.RecoveryEntryView().is_persistent()
    buttons = view.RecoveryIncidentView(row)
    action = next(b for b in buttons.children if b.label == "Keep partial reports & release")
    await action.callback(interaction)
    view.call.assert_awaited_once_with("review", ACTOR, row["IncidentID"])
    sent = interaction.followup.send.call_args.kwargs
    assert sent["ephemeral"] is True
    assert isinstance(sent["view"], view.RecoveryConfirmView)
    assert "reporting unfinished or unknown" in sent["embed"].fields[0].value
    assert not dal.calls


@pytest.mark.asyncio
async def test_expired_interaction_never_dispatches(monkeypatch):
    from ui.views import recovery_view as view

    _, _, _, row = setup()
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=False))
    monkeypatch.setattr(view, "call", AsyncMock())
    confirm = view.RecoveryConfirmView(row, "supersede_partial")
    await confirm.children[0].callback(Mock())
    view.call.assert_not_called()


@pytest.mark.asyncio
async def test_pending_or_unavailable_verification_hides_repair_buttons():
    from ui.views.recovery_view import RecoveryIncidentView, incident_embed

    _, _, _, row = setup()
    row["pending_action"] = {"state": "unknown", "kind": "supersede_partial"}
    assert [item.label for item in RecoveryIncidentView(row).children] == [
        "Recheck",
        "Download recovery report",
        "Review unfinished reports",
    ]
    assert any(field.name == "Repair being verified" for field in incident_embed(row).fields)
    row["pending_action"] = None
    row["evidence"]["check_unavailable"] = "TimeoutError"
    assert [item.label for item in RecoveryIncidentView(row).children] == [
        "Recheck",
        "Download recovery report",
        "Review unfinished reports",
    ]
    assert any(field.name == "Verification unavailable" for field in incident_embed(row).fields)


@pytest.mark.asyncio
async def test_skip_export_preview_shows_consequences_and_season(monkeypatch):
    from services.import_capture_recovery_service import ABANDON_CAPTURE_ACTION
    from ui.views import recovery_view as view

    _, _, _, row = setup()
    row["evidence"].update(season=7, actions={"abandon_capture": ABANDON_CAPTURE_ACTION})
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(view, "call", AsyncMock(return_value=row))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        item
        for item in view.RecoveryIncidentView(row).children
        if item.label == "Keep SQL; skip this export"
    )
    await button.callback(interaction)
    view.call.assert_awaited_once_with("review", ACTOR, row["IncidentID"])
    sent = interaction.followup.send.call_args.kwargs
    assert sent["ephemeral"] and isinstance(sent["view"], view.RecoveryConfirmView)
    assert "no spreadsheet export" in sent["embed"].fields[0].value
    assert "older spreadsheet may remain out of date" in sent["embed"].fields[0].value
    assert sent["view"].action == "abandon_capture"
    assert any(
        field.name == "KVK season" and field.value == "7"
        for field in view.incident_embed(row).fields
    )


@pytest.mark.asyncio
async def test_alert_footer_opens_exact_incident_after_view_recreation(monkeypatch):
    from ui.views import recovery_view as view

    _, _, _, row = setup()
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "show_incident", AsyncMock())
    interaction = SimpleNamespace(message=SimpleNamespace(embeds=[view.incident_embed(row)]))
    recreated = view.RecoveryEntryView()
    await recreated.children[0].callback(interaction)
    view.show_incident.assert_awaited_once_with(interaction, row["IncidentID"])


@pytest.mark.asyncio
async def test_queued_export_skip_requires_guided_confirmation(monkeypatch):
    from tests.test_export_recovery import job_fixture
    from ui.views import recovery_view as view

    adapter, snapshot = job_fixture(consumer="all_kvk")
    _, _, _, row = setup()
    row["evidence"] = adapter.inspect(snapshot["job"]["JobID"])[0]
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(view, "call", AsyncMock(return_value=row))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        item
        for item in view.RecoveryIncidentView(row).children
        if item.label == "Keep SQL; skip queued export"
    )
    await button.callback(interaction)
    view.call.assert_awaited_once_with("review", ACTOR, row["IncidentID"])
    sent = interaction.followup.send.call_args.kwargs
    assert sent["ephemeral"] and isinstance(sent["view"], view.RecoveryConfirmView)
    assert "spreadsheet may remain out of date" in sent["embed"].fields[0].value
    assert sent["view"].action == "skip_unstarted"
    adapter.coordinator.skip_unstarted.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kind,label",
    [
        ("legacy_configuration_continuation", "Review fresh configuration decision"),
        ("export_job", "Continue original recovery"),
        ("export_rollover", "Continue original recovery"),
        ("stats_import", "Review import and capture"),
    ],
)
async def test_verified_stage_retains_navigation_to_remaining_work(monkeypatch, kind, label):
    from ui.views import recovery_view as view

    _, _, _, row = setup()
    row["State"] = "resolved"
    row["evidence"].update(
        actions={}, recovery_links=[dict(label=label, kind=kind, source_id="retained-parent")]
    )
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(view, "call", AsyncMock(return_value=row))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(b for b in view.RecoveryIncidentView(row).children if b.label == label)
    await button.callback(interaction)
    view.call.assert_awaited_once_with("review_source", ACTOR, kind, "retained-parent")
    assert interaction.followup.send.call_args.kwargs["ephemeral"] is True
