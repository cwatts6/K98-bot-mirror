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
        configuration=r.runtime.configuration,
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
    state = r.dal.snapshot(r.run_id)
    action = str(uuid4())
    r.dal.decide(
        r.run_id,
        "player_cache",
        r.dal.token(state),
        dict(
            action=action, token="a" * 64, reason="explicit cache refresh", choice="continue_stage"
        ),
    )
    with pytest.raises(SourceConflict, match="confirmed continuation"):
        r.dal.start(r.run_id, "player_cache")
    assert r.dal.start(r.run_id, "player_cache", action_id=action) == action


def test_independent_stage_failure_retains_prior_decision_and_operation(pipeline):
    r = pipeline
    operation = r.dal.start(r.run_id, "maintenance")
    r.dal.observe(r.run_id, "maintenance", operation, dict(outcome="unconfirmed"), verified=False)
    state = r.dal.snapshot(r.run_id)
    action = str(uuid4())
    r.dal.decide(
        r.run_id,
        "maintenance",
        r.dal.token(state),
        dict(
            action=action,
            token="b" * 64,
            reason="new maintenance decision",
            choice="continue_stage",
        ),
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
        )
