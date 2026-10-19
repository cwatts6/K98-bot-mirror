"""Saved admin choices, authority RPC, activation and restart-safe rollover admission."""

import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from scripts.run_export_authority import AuthorityBroker
from services.export_execution_protocol import decode, encode
from services.export_recovery_service import RolloverRecoveryAdapter
from services.export_replacement_authority import ReplacementAuthority
from services.export_replacement_verification_service import ReplacementVerificationService
from services.export_runtime_composition import AuthorityClient, ExportRuntime, RuntimeLifetime
from services.recovery_service import RecoveryService
from services.rollover_replacement_adapter import RolloverReplacementAdapter
from tests import test_export_target_containment_sql as fixture_module
from tests.test_guided_recovery import ACTOR
from tests.test_recovery_sql import store as store
from tests.test_rollover_replacement_sql import (
    contained_job as contained_job,
    proposal_service as proposal_service,
    recovery as recovery,
    seed_choices,
    verification as verification,
)

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1"
    or os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1",
    reason="Explicit temporary SQL opt-in",
)


@pytest.fixture
def guided(monkeypatch, request, store):
    monkeypatch.setattr(fixture_module, "TABLES", (*fixture_module.TABLES, "KVK.SourceOutputFile"))
    monkeypatch.setattr(
        fixture_module,
        "PROCEDURES",
        (*fixture_module.PROCEDURES, "dbo.usp_ExportReplacementActivate"),
    )
    r = request.getfixturevalue("verification")
    registration = r.service.proposals.registration
    boundary = SimpleNamespace(
        fingerprint="b" * 64,
        recheck=Mock(return_value="b" * 64),
        _manifest=dict(
            service_account_email=registration.value()["service_account_email"],
            project_id="example",
            deployment_boundary=dict(
                identity=dict(client_id="test", private_key_id="test", credential_sha256="c" * 64)
            ),
        ),
    )
    broker = AuthorityBroker(r.service.authority, registration, boundary=boundary)
    broker.replacements = ReplacementAuthority(broker)
    messages = []
    client = AuthorityClient.__new__(AuthorityClient)

    def invoke(message):
        messages.append(decode(encode(message)))
        return decode(
            encode(
                dict(result=broker.dispatch(dict(message, deployment_hash=boundary.fingerprint)))
            )
        )["result"]

    client._invoke = invoke
    monkeypatch.setattr(ReplacementVerificationService, "start", ReplacementVerificationService.run)
    monkeypatch.setattr("services.export_coordination_service.wake_exports", Mock())
    runtime = ExportRuntime.__new__(ExportRuntime)
    RuntimeLifetime.__init__(runtime, SimpleNamespace())
    runtime.connect, runtime.client = r.f.connect, client
    runtime.registration = runtime.base_registration = registration
    runtime._legacy_streams = SimpleNamespace()
    runtime._legacy_adapter = SimpleNamespace()
    runtime.pools = r.service.proposals.containment.pools
    base = RolloverRecoveryAdapter(r.service.proposals.containment.discovery, runtime.pools, None)
    adapter = RolloverReplacementAdapter(base, runtime=runtime)
    runtime.legacy.recovery_adapters = (SimpleNamespace(base=SimpleNamespace()), adapter)
    service = RecoveryService(
        store, {"export_rollover": adapter}, admin_id=1, guild_id=2, channel_id=3
    )
    r.recovery, r.adapter, r.rpc, r.broker, r.messages = service, adapter, runtime, broker, messages
    r.row = service.review_source(ACTOR, "export_rollover", r.f.operation)
    return r


@pytest.mark.asyncio
async def test_guided_pages_survive_restart_then_verify_activate_and_queue_once(
    guided, monkeypatch
):
    from ui.views import recovery_view as view

    r = guided
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))

    async def call(method, *args):
        return getattr(r.recovery, method)(*args)

    monkeypatch.setattr(view, "call", call)

    async def click(action):
        current = r.recovery.review(ACTOR, r.row["IncidentID"])
        label = current["evidence"]["actions"][action]["label"]
        interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
        button = next(b for b in view.RecoveryIncidentView(current).children if b.label == label)
        await button.callback(interaction)
        preview = interaction.followup.send.call_args.kwargs
        assert preview["ephemeral"] is True
        assert isinstance(preview["view"], view.RecoveryConfirmView)
        assert preview["view"].action == action
        assert {f.name for f in preview["embed"].fields} >= {
            "Check before confirming",
            "What the bot will do",
            "Verification",
        }
        await preview["view"].children[0].callback(interaction)
        result = interaction.followup.send.call_args.kwargs
        assert result["ephemeral"] is True
        assert isinstance(result["view"], view.RecoveryIncidentView)
        return result["view"].row

    incident = r.row["IncidentID"]
    page = r.recovery.input_page(ACTOR, incident, "choose_replacements")
    assert page["pages"] == 2
    for number in range(page["pages"]):
        page = r.recovery.input_page(ACTOR, incident, "choose_replacements", number)
        row = page["row"]
        values = {
            f["key"]: (
                "owner@example.com"
                if f["key"] == "owner_email"
                else "https://docs.google.com/spreadsheets/d/guided-" + f["key"] + "/edit"
            )
            for f in page["fields"]
        }
        r.recovery.save_input(
            ACTOR,
            incident,
            row["Revision"],
            row["EvidenceHash"],
            "choose_replacements",
            number,
            page["draft_version"],
            values,
        )
    r.recovery = RecoveryService(
        r.recovery.store, {"export_rollover": r.adapter}, admin_id=1, guild_id=2, channel_id=3
    )
    review = r.recovery.input_confirmation(ACTOR, incident, "choose_replacements")
    row = review["row"]
    row = r.recovery.execute_input(
        ACTOR,
        incident,
        row["Revision"],
        row["EvidenceHash"],
        "choose_replacements",
        review["draft_version"],
    )
    assert row["State"] == "open" and row["evidence"]["outcome"] == "verification_required"
    row = await click("verify_replacements")
    assert row["evidence"]["outcome"] == "activation_required"
    row = await click("activate_replacements")
    assert row["State"] == "open" and row["evidence"]["outcome"] == "rollover_continuation_required"
    activation = r.rpc.client.replacement_recovery(
        r.f.operation, "context", owner_kind="rollover", token=row["EvidenceHash"]
    )
    dal = seed_choices(r, activation)
    row = await click("start_replacement_rollover")
    assert row["State"] == "open" and row["evidence"]["outcome"] == "replacement_rollover_closing"
    assert not row["pending_action"]
    restarted = RecoveryService(
        r.recovery.store, {"export_rollover": r.adapter}, admin_id=1, guild_id=2, channel_id=3
    )
    assert (
        restarted.review(ACTOR, incident)["evidence"]["delivery"]["operation_id"]
        == dal.read(r.f.operation, activation)["OperationID"]
    )
    assert r.f.sql.execute("SELECT COUNT(*) FROM #SourceOutputOperation").fetchval() == 2
    assert (
        r.f.sql.execute(
            "SELECT State FROM #SourceOutputOperation WHERE OperationID=?", r.f.operation
        ).fetchval()
        == "uncertain"
    )
    assert {
        m.get("operation") for m in r.messages if m["action"] == "rollover_replacement_recovery"
    } >= {"fields", "validate", "inspect", "execute", "context", "reconcile"}
