"""Actual scoped SQL journal, live exclusion, CAS and admin recovery dispatch."""

import json
import os
from pathlib import Path
import re
from types import SimpleNamespace
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.processing_pipeline_receipt_dal import PipelineReceiptDAL
from services.processing_pipeline_recovery import ProcessingPipelineRecovery
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryActor, RecoveryService
from tests.test_guided_recovery import ACTOR, Store
from tests.test_import_capture_recovery_sql import recovery as recovery

pytestmark = [
    pytest.mark.skipif(os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Local SQL opt-in"),
    pytest.mark.parametrize("recovery", ["scan_data"], indirect=True),
]


@pytest.fixture
def pipeline(recovery):
    r = recovery
    namespace = uuid4().hex
    names = {
        "dbo." + name: "##Pipeline_" + namespace + "_" + name
        for name in ("ProcessingPipelineRun", "ProcessingPipelineStage")
    }

    def rewrite(sql):
        for source, target in names.items():
            sql = sql.replace(source, target)
        return r.rewrite(sql)

    schema = Path(os.environ["K98_CAPTURE_SQL_SCHEMA"])
    for name in names:
        raw = (schema / (name + ".Table.sql")).read_text(encoding="utf-8-sig")
        raw = "\n".join(line for line in raw.splitlines() if "FOREIGN KEY" not in line)
        raw = re.sub(r"CONSTRAINT (\w+)", lambda m: "CONSTRAINT " + m[1] + "_" + namespace, raw)
        r.owner.execute(rewrite(raw))

    class Cursor:
        def __init__(self, inner):
            self.inner = inner

        def execute(self, sql, *args):
            self.inner.execute(rewrite(sql), *args)
            return self

        def __getattr__(self, key):
            return getattr(self.inner, key)

    class Connection:
        def __init__(self):
            self.inner = r.connect()

        @property
        def autocommit(self):
            return self.inner.autocommit

        @autocommit.setter
        def autocommit(self, value):
            self.inner.autocommit = value

        def cursor(self):
            return Cursor(self.inner.cursor())

        def __getattr__(self, key):
            return getattr(self.inner, key)

    runtime = SimpleNamespace(
        account="a",
        store=r.runtime.store,
        dal=SimpleNamespace(connect=Connection),
        configuration=json.dumps(
            dict(
                json.loads(r.runtime.configuration),
                config=dict(consumer="config", destinations=["input"]),
            )
        ),
    )
    dal = PipelineReceiptDAL(runtime)
    run_id = dal.create(dict(filename="retained.xlsx", rank=1, seed="A"))
    adapter = ProcessingPipelineRecovery(dal)
    store = Store()
    service = RecoveryService(
        store,
        {adapter.kind: adapter},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    evidence, token, complete = adapter.inspect(run_id)
    row = store.observe(adapter.kind, run_id, evidence, token, resolved=complete)
    return SimpleNamespace(
        dal=dal,
        adapter=adapter,
        run_id=run_id,
        service=service,
        store=store,
        incident=row["IncidentID"],
        owner=r.owner,
        rewrite=rewrite,
        runtime=runtime,
        base=r,
    )


def test_registration_is_complete_and_operation_identity_precedes_dispatch(pipeline):
    r = pipeline
    state = r.dal.snapshot(r.run_id)
    assert len(state["stages"]) == 7
    assert all(row["State"] == "not_started" for row in state["stages"].values())
    with r.dal.guard(r.run_id):
        operation = r.dal.start(r.run_id, "import")
        with pytest.raises(SourceConflict, match="live worker"):
            with r.dal.guard(r.run_id):
                pass
    assert operation == str(state["stages"]["import"]["OperationID"]).lower()
    with pytest.raises(SourceConflict, match="already has an intent"):
        r.dal.start(r.run_id, "import")
    assert r.dal.pending_recovery() == [r.run_id]


def test_disposition_is_permission_gated_preserves_unknown_and_never_releases_other_work(pipeline):
    r = pipeline
    row = r.service.review(ACTOR, r.incident)
    for actor in (RecoveryActor(99, 2, 3), RecoveryActor(1, 99, 3), RecoveryActor(1, 2, 99)):
        with pytest.raises(SourceConflict):
            r.service.review(actor, r.incident)
    assert "continue_stage" not in row["evidence"]["actions"]  # Import can never be replayed.
    before = r.owner.execute(
        r.rewrite("SELECT COUNT(*) FROM dbo.ExportResource WHERE OwnerID IS NOT NULL")
    ).fetchval()
    r.service.execute(
        ACTOR,
        r.incident,
        row["Revision"],
        row["EvidenceHash"],
        "retain_stage",
        "Preserve unfinished import",
    )
    stage = r.dal.snapshot(r.run_id)["stages"]["import"]
    assert stage["State"] == "skipped"
    assert json.loads(stage["EvidenceJson"])["original_outcome"] == "unconfirmed"
    assert (
        r.owner.execute(
            r.rewrite("SELECT COUNT(*) FROM dbo.ExportResource WHERE OwnerID IS NOT NULL")
        ).fetchval()
        == before
    )
    assert r.store.actions[0]["State"] == "verified"


def test_stale_confirmation_and_foreign_scope_do_not_mutate_pipeline(pipeline):
    r = pipeline
    row = r.service.review(ACTOR, r.incident)
    operation = r.dal.start(r.run_id, "import")
    r.dal.observe(r.run_id, "import", operation, dict(outcome="unconfirmed"), verified=False)
    with pytest.raises(SourceConflict):
        r.service.execute(
            ACTOR, r.incident, row["Revision"], row["EvidenceHash"], "retain_stage", "stale"
        )
    r.runtime.account = "foreign"
    with pytest.raises(SourceConflict, match="scope"):
        r.dal.snapshot(r.run_id)


def test_normal_caller_cannot_consume_confirmed_recovery_intent_after_lost_reply(pipeline):
    r = pipeline
    state = r.adapter._state(r.run_id)
    action = str(uuid4())
    r.dal.decide(
        r.run_id,
        "player_cache",
        r.dal.token(state),
        dict(
            action=action,
            token=r.dal.token(state),
            reason="explicit cache refresh",
            choice="continue_stage",
            registration=state["current_registration"],
        ),
        reviewed_state=state,
    )
    with pytest.raises(SourceConflict, match="confirmed continuation"):
        r.dal.start(r.run_id, "player_cache")
    assert r.dal.start(r.run_id, "player_cache", action_id=action) == action


def test_independent_stage_failure_retains_prior_decision_and_operation(pipeline):
    r = pipeline
    operation = r.dal.start(r.run_id, "maintenance")
    r.dal.observe(r.run_id, "maintenance", operation, dict(outcome="unconfirmed"), verified=False)
    state = r.adapter._state(r.run_id)
    action = str(uuid4())
    r.dal.decide(
        r.run_id,
        "maintenance",
        r.dal.token(state),
        dict(
            action=action,
            token=r.dal.token(state),
            reason="new maintenance decision",
            choice="continue_stage",
            registration=state["current_registration"],
        ),
        reviewed_state=state,
    )
    history = json.loads(r.dal.snapshot(r.run_id)["stages"]["maintenance"]["DecisionJson"])
    assert history[0]["previous_operation"] == operation
    assert history[0]["previous_state"] == "unconfirmed"
    with pytest.raises(SourceConflict, match="cannot be dispatched"):
        r.dal.decide(
            r.run_id,
            "import",
            r.dal.token(r.dal.snapshot(r.run_id)),
            dict(action=str(uuid4()), token="c" * 64),
            reviewed_state=state,
        )


def link_import(r):
    """Associate the existing completed SQL fixture without replaying it."""
    from kvk.dal.new_source_import_dal import digest

    operation = str(r.dal.snapshot(r.run_id)["stages"]["import"]["OperationID"]).lower()
    prep = r.base.outcomes.inspect(r.base.source)["preparation"]
    request = json.loads(prep["RequestJson"])
    request["request"]["producer"] = dict(operation=operation)
    r.owner.execute(
        r.rewrite(
            "UPDATE dbo.ExportPreparation SET RequestJson=?,RequestHash=? WHERE PreparationID=?"
        ),
        json.dumps(request),
        digest(request),
        r.base.source,
    )


def link_read(r, *, successor=False):
    from services.configuration_continuation_dal import ConfigurationContinuationDAL

    config = json.loads(r.runtime.configuration)
    config["config"] = dict(consumer="config", destinations=["input"])
    r.runtime.configuration = json.dumps(config)
    operation = str(r.dal.snapshot(r.run_id)["stages"]["configuration"]["OperationID"]).lower()
    source = r.base.runtime.dal.request(
        account="a",
        consumer="config",
        kvk_no=None,
        storage_owner="disk-a",
        request=dict(
            read_configuration=str(uuid4()),
            configuration_import=dict(
                invocation_mode="publish",
                producer=dict(
                    kind="configuration_import", atomic_checkpoint=1, operation=operation
                ),
                sources=config["config"],
                outputs=config["scan_data"],
            ),
        ),
        actor="test",
        reason="Isolated pipeline association",
    )
    r.base.runtime.dal.withdraw_unstarted(source)
    if not successor:
        return source
    marker = dict(
        action=str(uuid4()),
        token="a" * 64,
        reason="confirmed",
        choice="retry",
        configuration=config,
    )
    r.owner.execute(
        r.rewrite(
            "UPDATE dbo.ExportPreparation SET GenerationJson=?,Version=Version+1 WHERE PreparationID=?"
        ),
        json.dumps(dict(configuration_continuation=marker)),
        source,
    )
    return r.base.runtime.dal.request(
        account="a",
        consumer="scan_data",
        kvk_no=None,
        storage_owner="disk-a",
        request=ConfigurationContinuationDAL.child_request(source, marker),
        actor="test",
        reason="Isolated confirmed successor",
    )


@pytest.mark.parametrize("action", ["retain_stage", "verify_stage", "continue_stage"])
@pytest.mark.parametrize(
    "change", ["child", "read", "successor", "new_read", "registration", "execution", "reservation"]
)
def test_decision_rechecks_full_review_after_service_inspection(
    pipeline, monkeypatch, action, change
):
    r = pipeline
    link_import(r)
    linked = (
        link_read(r, successor=change == "successor") if change in {"read", "successor"} else None
    )
    if action == "continue_stage":
        for stage in ("import", "player_cache"):
            operation = r.dal.start(r.run_id, stage)
            r.dal.observe(
                r.run_id, stage, operation, dict(outcome="fixture_verified"), verified=True
            )
    shown, token, _ = r.adapter.inspect(r.run_id)
    assert action in shown["actions"]
    before = r.dal.snapshot(r.run_id)
    calls = []
    monkeypatch.setattr(r.adapter, "runner", lambda *_: calls.append("dispatched"))
    decide = r.dal.decide

    def change_then_decide(*args, **kwargs):
        if change in {"child", "read", "successor"}:
            r.owner.execute(
                r.rewrite(
                    "UPDATE dbo.ExportPreparation SET Version=Version+1 WHERE PreparationID=?"
                ),
                linked or r.base.source,
            )
        elif change == "new_read":
            link_read(r)
        elif change == "registration":
            r.runtime.configuration = json.dumps(dict(scan_data=dict(destinations=["changed"])))
        elif change == "execution":
            r.owner.execute(
                r.rewrite(
                    "UPDATE dbo.StatsImportExecution SET Version=Version+1 WHERE PreparationID=?"
                ),
                r.base.source,
            )
        else:
            r.owner.execute(
                r.rewrite(
                    "UPDATE dbo.ExportResource SET Version=Version+1 WHERE ActivePreparationID=?"
                ),
                r.base.source,
            )
        return decide(*args, **kwargs)

    monkeypatch.setattr(r.dal, "decide", change_then_decide)
    with pytest.raises(SourceConflict, match="evidence changed"):
        r.adapter.execute(
            r.run_id, action, token, "recovery:" + str(uuid4()), "Confirmed exact review"
        )
    assert r.dal.snapshot(r.run_id) == before
    assert calls == []


def test_full_review_verify_survives_lost_reply_without_import_dispatch(pipeline):
    r = pipeline
    link_import(r)
    _, token, _ = r.adapter.inspect(r.run_id)
    action = str(uuid4())
    r.adapter.execute(
        r.run_id, "verify_stage", token, "recovery:" + action, "Committed SQL receipt"
    )
    restarted = ProcessingPipelineRecovery(r.dal, runner=lambda *_: pytest.fail("No import replay"))
    receipt = dict(ActionID=action, ActionKind="verify_stage", EvidenceHash=token)
    assert restarted.reconcile(r.run_id, receipt) == "verified"
    assert restarted.reconcile(r.run_id, receipt) == "verified"
    history = json.loads(r.dal.snapshot(r.run_id)["stages"]["import"]["DecisionJson"])
    assert len(history) == 1 and history[0]["token"] == token


@pytest.mark.parametrize("new_association", [False, True])
def test_decision_holds_linked_evidence_until_stage_cas(pipeline, monkeypatch, new_association):
    import pyodbc

    from services import processing_pipeline_receipt_dal as module

    r = pipeline
    link_import(r)
    _, token, _ = r.adapter.inspect(r.run_id)
    original = module._cas
    blocked = []
    operation = str(r.dal.snapshot(r.run_id)["stages"]["configuration"]["OperationID"]).lower()
    request = json.dumps(
        dict(request=dict(configuration_import=dict(producer=dict(operation=operation))))
    )

    def attempt_concurrent_change(cursor, *args):
        r.owner.execute("SET LOCK_TIMEOUT 0")
        try:
            with pytest.raises(pyodbc.Error, match="1222"):
                if new_association:
                    r.owner.execute(
                        r.rewrite(
                            "INSERT dbo.ExportPreparation (PreparationID,AccountKey,ConsumerKind,RequestHash,EnqueueSequence,"
                            "State,Fence,Version,StorageOwner,RequestJson,Actor,Reason,CreatedUTC,UpdatedUTC) "
                            "VALUES (?, 'a','config',CAST(? AS binary(32)),2,'pending',0,1,'disk-a',?,'test','test',SYSUTCDATETIME(),SYSUTCDATETIME())"
                        ),
                        str(uuid4()),
                        b"z" * 32,
                        request,
                    )
                else:
                    r.owner.execute(
                        r.rewrite(
                            "UPDATE dbo.ExportPreparation SET Version=Version+1 WHERE PreparationID=?"
                        ),
                        r.base.source,
                    )
            blocked.append(True)
        finally:
            r.owner.execute("SET LOCK_TIMEOUT -1")
        return original(cursor, *args)

    monkeypatch.setattr(module, "_cas", attempt_concurrent_change)
    r.adapter.execute(
        r.run_id, "verify_stage", token, "recovery:" + str(uuid4()), "Stable locked evidence"
    )
    assert blocked == [True]


def test_inspection_refuses_mixed_association_snapshot(pipeline, monkeypatch):
    r = pipeline
    link_import(r)
    original = r.dal.configuration_result

    def mutate_during_read(operation):
        result = original(operation)
        r.owner.execute(
            r.rewrite("UPDATE dbo.ExportPreparation SET Version=Version+1 WHERE PreparationID=?"),
            r.base.source,
        )
        return result

    monkeypatch.setattr(r.dal, "configuration_result", mutate_during_read)
    with pytest.raises(SourceConflict, match="evidence changed"):
        r.adapter.inspect(r.run_id)


@pytest.mark.parametrize("lock", ["account", "producer_row"])
def test_busy_independent_writer_refuses_review_without_waiting_or_mutation(pipeline, lock):
    from kvk.dal.new_source_import_dal import transaction
    from services.export_coordination_dal import _mutex

    r = pipeline
    link_import(r)
    before = r.dal.snapshot(r.run_id)
    with transaction(r.dal.connect) as cursor:
        if lock == "account":
            _mutex(cursor, "account:a")
        else:
            cursor.execute(
                "SELECT * FROM dbo.ExportPreparation WITH (UPDLOCK,HOLDLOCK) WHERE PreparationID=?",
                r.base.source,
            )
            cursor.fetchall()
        with pytest.raises(SourceConflict, match="evidence is busy"):
            r.adapter.inspect(r.run_id)
    assert r.dal.snapshot(r.run_id) == before
