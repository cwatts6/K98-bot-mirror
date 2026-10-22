"""Alert-to-disposition rehearsal with real SQL incidents and admin callbacks.

Discord transport and the configuration producer body are simulated. The producer
helper commits a real atomic receipt (optionally losing its reply). Capture cases
use actual SQL rows, immutable spool files, queue admission and worker execution,
with controlled transport failures. This is not installed-package or provider-
delivery proof; real business-publication checks live in the separate rehearsal.
"""

from contextlib import contextmanager
import json
import os
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from kvk.dal.new_source_import_dal import digest
from services.configuration_continuation import ConfigurationContinuation
from services.configuration_continuation_dal import ConfigurationContinuationDAL
from services.configuration_producer_recovery import ConfigurationProducerRecovery
from services.export_coordination_dal import ExportCoordinationDAL
from services.export_coordination_service import ExportCoordinator
from services.export_request_budget import BudgetCompletionUnknown
from services.legacy_export_snapshot_service import (
    LegacyExportRuntime,
    LegacySnapshot,
    OutputSection,
)
from services.recovery_dal import RecoveryDAL
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryService
from tests.test_configuration_continuation_sql import commit_child
from tests.test_import_capture_recovery_sql import recovery as recovery
from tests.test_player_report_recovery_sql import uncommitted
from tests.test_recovery_sql import store as store

pytestmark = [
    pytest.mark.skipif(
        os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Disposable SQL opt-in required"
    ),
    pytest.mark.parametrize("recovery", ["configuration_continuation"], indirect=True),
]


def button(view, label):
    matches = [b for b in view.children if getattr(b, "label", None) == label]
    assert len(matches) == 1, (
        type(view).__name__,
        label,
        [getattr(b, "label", None) for b in view.children],
    )
    return matches[0]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "choice",
    [
        "keep_prior",
        "skip_export",
        "skip_export_lost_reply",
        "capture",
        "capture_lost_queue_reply",
        "capture_unknown_request",
        "capture_corrupt_spool",
        "capture_delivered",
        "capture_write_reply_lost",
        "capture_readback_mismatch",
    ],
)
async def test_monitor_alert_to_verified_configuration_disposition(
    recovery, store, monkeypatch, choice
):
    import bot_config
    from services import recovery_runtime
    from stats_alerts import recovery_notifications
    from ui.views import recovery_review_view, recovery_summary_view, recovery_view

    r = recovery
    # This rehearsal follows an interrupted pipeline publication. A generic
    # SQL-only retry cannot authorize the export paths exercised below.
    request = json.loads(r.outcomes.inspect(r.source)["preparation"]["RequestJson"])
    request["request"]["producer"]["export_disposition"] = "pipeline_export_v1"
    r.owner.execute(
        r.rewrite(
            "UPDATE dbo.ExportPreparation SET RequestJson=?,RequestHash=? WHERE PreparationID=?"
        ),
        json.dumps(request),
        digest(request),
        r.source,
    )
    queue_calls = []
    if choice.startswith("capture"):
        # Real durable admission, snapshot verification and coordinator. Only
        # the input rows and eventual external transport are synthetic.
        coordinator = ExportCoordinationDAL(
            r.connect, preparations=True, output_operations=True, execution_evidence=True
        )
        r.runtime.account = "a"
        r.runtime.coordinator = coordinator
        r.runtime.verified_snapshot = lambda source: LegacyExportRuntime.verified_snapshot(
            r.runtime, source
        )

        def capture_sql(connection, scope):
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT CAST(7 AS int) AS value")
                rows = tuple(tuple(row) for row in cursor.fetchall())
            finally:
                cursor.close()
            return (OutputSection("output", ("value",), rows),), dict(
                scope,
                outputs=[dict(section="output", file_id="registered", tab="Report", grid_id=42)],
            )

        def enqueue(source):
            job_id = LegacyExportRuntime.enqueue_snapshot(r.runtime, source)
            queue_calls.append(job_id)
            if choice.endswith("lost_queue_reply") and len(queue_calls) == 1:
                raise TimeoutError("Queue commit succeeded; acknowledgement lost")
            return job_id

        r.runtime.capture = capture_sql
        r.runtime.enqueue_snapshot = enqueue
    generation = json.loads(r.outcomes.inspect(r.source)["preparation"]["GenerationJson"])
    uncommitted(r)
    r.runtime.account = "a"
    configuration = json.loads(r.runtime.configuration)
    configuration["config"] = dict(consumer="config", destinations=["source_sheet"])
    r.runtime.configuration = json.dumps(configuration)
    calls = []

    def run_configuration():
        calls.append(1)
        return commit_child(r, generation, lost_reply=choice.endswith("lost_reply"))

    # Reconstruct service, DAL and adapters on every callback: no view instance
    # or service memory can stand in for persisted incident/action evidence.
    @contextmanager
    def service_scope():
        producer = ConfigurationProducerRecovery(r.outcomes, r.service)
        continuation = ConfigurationContinuation(
            ConfigurationContinuationDAL(r.runtime, r.outcomes), producer, run_configuration
        )
        yield RecoveryService(
            RecoveryDAL(store.connect, account="a", storage_owner="disk-a", guild_id=2),
            {producer.kind: producer, continuation.kind: continuation},
            admin_id=1,
            guild_id=2,
            channel_id=3,
            presentation_policy=p0a_presentation,
        )

    for name, value in (("ADMIN_USER_ID", 1), ("GUILD_ID", 2), ("NOTIFY_CHANNEL_ID", 3)):
        monkeypatch.setattr(bot_config, name, value)
    monkeypatch.setattr(recovery_runtime, "recovery_service", service_scope)
    monkeypatch.setattr(recovery_runtime, "_retry_admission", lambda: True)
    monkeypatch.setattr(recovery_runtime, "_cursors", {})
    monkeypatch.setattr(recovery_runtime, "_incident_cursor", None)
    monkeypatch.setattr(recovery_runtime, "_priority_incident_cursor", None)
    for module in (recovery_view, recovery_review_view, recovery_summary_view):
        monkeypatch.setattr(module, "safe_defer", AsyncMock(return_value=True))

    async def empty_history(**kwargs):
        if False:
            yield None

    message = SimpleNamespace(id=40, author=SimpleNamespace(id=99), edit=AsyncMock())
    channel = SimpleNamespace(
        id=3,
        guild=SimpleNamespace(id=2),
        history=empty_history,
        send=AsyncMock(return_value=message),
        fetch_message=AsyncMock(return_value=message),
    )
    bot = SimpleNamespace(user=SimpleNamespace(id=99), get_channel=lambda _: channel)

    # Discover and notify without a dependent operation first failing.
    assert recovery_runtime.observe_recovery() == []
    await recovery_notifications.publish_recovery_alerts(bot)
    assert channel.send.call_count == 1
    alert = channel.send.call_args.kwargs
    message.embeds = [alert["embed"]]
    assert "source_sheet" not in str(alert["embed"].to_dict())
    overview_id = alert["embed"].footer.text.removeprefix("Recovery overview: ")
    with service_scope() as service:
        assert service.store.get(overview_id)["AlertMessageID"] == 40
        incident = next(row for row in service.store.list_open() if row["SourceID"] == r.source)
        incident_id = incident["IncidentID"]

    interaction = SimpleNamespace(
        user=SimpleNamespace(id=1),
        guild_id=2,
        channel_id=3,
        message=message,
        response=SimpleNamespace(is_done=lambda: True),
        followup=SimpleNamespace(send=AsyncMock()),
    )

    def current_view():
        sent = interaction.followup.send.call_args.kwargs
        assert sent["ephemeral"] is True
        return sent["view"]

    async def click(label):
        await button(current_view(), label).callback(interaction)

    # A reconstructed persistent overview opens the centre, where the admin
    # selects the operational incident before its evidence-bound repair.
    await button(recovery_view.RecoveryEntryView(), "Review & fix").callback(interaction)
    selection = next(item for item in current_view().children if hasattr(item, "options"))
    assert incident_id in [option.value for option in selection.options]
    selection._selected_values = [incident_id]
    interaction.data = {"values": [incident_id]}
    selection._interaction = interaction
    await selection.callback(interaction)
    await click("Close rolled-back config & release")
    assert r.outcomes.inspect(r.source)["action"] == "cancel_configuration"
    close_confirmation = current_view()
    await click("Confirm & apply repair")
    assert r.outcomes.inspect(r.source)["action"] == "cancelled"
    assert not r.outcomes.inspect(r.source)["resources"]
    await click("Choose configuration continuation")
    continuation_id = current_view().row["IncidentID"]

    if choice == "keep_prior":
        await click("Keep prior configuration")
        with service_scope() as service:
            assert service.store.get(continuation_id)["State"] == "open"
        await click("Confirm & apply repair")
        assert calls == []
    else:
        await click("Continue config for export")
        pages = 0
        while True:
            page = current_view()
            pages += 1
            assert calls == []
            advance = button(page, "Next checks")
            confirm = button(page, "Continue to confirmation")
            if advance.disabled:
                assert not confirm.disabled
                await confirm.callback(interaction)
                break
            assert confirm.disabled
            await advance.callback(interaction)
        assert pages > 1
        publication_confirmation = current_view()
        await click("Confirm & apply repair")
        assert calls == [1]
        await click("Review configuration result")
        child_id = current_view().row["SourceID"]
        child_row = current_view().row
        selected_action = "resume_capture" if choice.startswith("capture") else "abandon_capture"
        label = child_row["evidence"]["actions"][selected_action]["label"]
        await click(label)
        assert r.outcomes.inspect(child_id)["resources"]
        assert isinstance(current_view(), recovery_summary_view.RecoverySummaryView)
        await click("Continue to confirmation")
        assert r.outcomes.inspect(child_id)["resources"]
        assert calls == [1]
        await click("Confirm & apply repair")
        if choice.startswith("capture"):
            with service_scope() as service:
                # A fresh service reconciles a lost commit response without
                # repeating capture, creating another job or releasing by age.
                final_child = service.refresh(child_row["IncidentID"])
                assert final_child["State"] == "resolved"
                assert not service.store.pending_actions(child_row["IncidentID"])
            queued = r.outcomes.inspect(child_id)["preparation"]
            assert queued["State"] == "materialized"
            actual_id = str(queued["JobID"]).lower()
            assert queue_calls and set(queue_calls) == {actual_id}
            jobs = r.owner.execute(
                r.rewrite(
                    "SELECT JobID,State,SpoolHash FROM dbo.ExportPreparation WHERE PreparationID=?"
                ),
                child_id,
            ).fetchall()
            assert len(jobs) == 1 and bytes(jobs[0][2])
            assert r.owner.execute(r.rewrite("SELECT COUNT(*) FROM dbo.ExportJob")).fetchval() == 1
            deliveries = []
            if choice == "capture_corrupt_spool":
                (r.runtime.store.root / queued["SpoolKey"]).write_bytes(b"corrupt fixture")

            def before_dispatch(job, claim, dal, budget, stop, snapshot):
                assert str(job["JobID"]).lower() == actual_id
                assert LegacySnapshot.load(snapshot).metadata()["preparation_id"] == child_id
                deliveries.append(actual_id)
                if choice == "capture_unknown_request":
                    raise BudgetCompletionUnknown("Request checkpoint acknowledgement lost")
                raise RuntimeError("Controlled stop before external provider dispatch")

            # Reconstruction represents process restart. Execute real discovery,
            # account/target admission, spool verification and terminal CAS.
            provider = None
            if choice in {
                "capture_delivered",
                "capture_write_reply_lost",
                "capture_readback_mismatch",
            }:
                from tests.p0a_provider_fixture import provider_fixture

                provider = provider_fixture(
                    r,
                    configuration,
                    failure={
                        "capture_delivered": None,
                        "capture_write_reply_lost": "write_reply",
                        "capture_readback_mismatch": "readback",
                    }[choice],
                )
            worker = ExportCoordinator(
                ExportCoordinationDAL(
                    r.connect, preparations=True, output_operations=True, execution_evidence=True
                ),
                adapters={"scan_data": provider.adapter if provider else before_dispatch},
                storage=r.runtime.store,
                output_planner=lambda *_: pytest.fail("No new-source work belongs to this fixture"),
            )
            worker.run_batch(threading.Event())
            expected_deliveries = (
                [] if choice == "capture_corrupt_spool" or provider else [actual_id]
            )
            assert deliveries == expected_deliveries
            uncertain = choice in {
                "capture_unknown_request",
                "capture_write_reply_lost",
                "capture_readback_mismatch",
            }
            assert r.owner.execute(
                r.rewrite("SELECT State FROM dbo.ExportJob WHERE JobID=?"), actual_id
            ).fetchval() == (
                "confirmed"
                if choice == "capture_delivered"
                else "uncertain" if uncertain else "failed"
            )
            assert r.owner.execute(
                r.rewrite("SELECT COUNT(*) FROM dbo.ExportResource WHERE ActiveJobID=?"), actual_id
            ).fetchval() == (2 if uncertain else 0)
            worker.run_batch(threading.Event())
            assert deliveries == expected_deliveries
            if provider:
                provider.http.request.assert_not_called()
                assert provider.rows == dict(values=[["value"], [7]])
                assert sum(q.operation == "sheets.values.update" for q in provider.sent) == 1
                assert all(c.terminated for c in provider.children)
                assert provider.documents
                stream_state = r.owner.execute(
                    r.rewrite("SELECT State FROM dbo.ExportExecutionStream WHERE JobID=?"),
                    actual_id,
                ).fetchval()
                assert stream_state == (
                    "frozen" if choice == "capture_write_reply_lost" else "closed"
                )
                if choice == "capture_delivered":
                    from services.export_execution_dal import ExportExecutionDAL
                    from services.export_reconciliation_service import ClosedStreamVerifier

                    # Reconstruct the independent reader: a completed job label
                    # alone is not proof of intact request/response membership.
                    stream_id, registration_hash = r.owner.execute(
                        r.rewrite(
                            "SELECT StreamID,RegistrationHash FROM dbo.ExportExecutionStream WHERE JobID=?"
                        ),
                        actual_id,
                    ).fetchone()
                    proof = ClosedStreamVerifier(
                        dal=ExportExecutionDAL(r.connect), store=provider.authority.store
                    ).verify(
                        str(stream_id).lower(),
                        account="a",
                        registration_hash=bytes(registration_hash),
                    )
                    assert proof.dispatched_mutations > 0 and proof.successful_reads > 0
                    assert proof.request_count == len(provider.sent)
        else:
            assert current_view().row["State"] == "resolved"
            assert current_view().row["evidence"]["outcome"] == "export_skipped"
        assert not r.outcomes.inspect(child_id)["resources"]
        # A replayed old confirmation cannot republish, even after new services.
        await button(publication_confirmation, "Confirm & apply repair").callback(interaction)
        assert calls == [1]

    await button(close_confirmation, "Confirm & apply repair").callback(interaction)
    with service_scope() as service:
        final = service.refresh(continuation_id)
        assert final["State"] == ("open" if choice == "capture_corrupt_spool" else "resolved")
        assert not service.store.pending_actions(incident_id)
        assert not service.store.pending_actions(continuation_id)
        if choice == "capture_corrupt_spool":
            assert service.store.list_open()
            assert calls == [1]
        else:
            assert not service.store.list_open()
        assert not r.outcomes.inspect(r.source)["resources"]
