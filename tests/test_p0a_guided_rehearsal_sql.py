"""Alert-to-disposition rehearsal with real SQL incidents and admin callbacks.

Only Discord transport and the configuration producer body are simulated. The
producer helper commits a real atomic receipt (optionally losing its reply).
This is not installed-package, provider-delivery or business-publication proof.
"""

from contextlib import contextmanager
import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.configuration_continuation import ConfigurationContinuation
from services.configuration_continuation_dal import ConfigurationContinuationDAL
from services.configuration_producer_recovery import ConfigurationProducerRecovery
from services.recovery_dal import RecoveryDAL
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
    return next(b for b in view.children if b.label == label)


@pytest.mark.asyncio
@pytest.mark.parametrize("choice", ["keep_prior", "skip_export", "skip_export_lost_reply"])
async def test_monitor_alert_to_verified_configuration_disposition(
    recovery, store, monkeypatch, choice
):
    import bot_config
    from services import recovery_runtime
    from stats_alerts import recovery_notifications
    from ui.views import recovery_review_view, recovery_view

    r = recovery
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
        )

    for name, value in (("ADMIN_USER_ID", 1), ("GUILD_ID", 2), ("NOTIFY_CHANNEL_ID", 3)):
        monkeypatch.setattr(bot_config, name, value)
    monkeypatch.setattr(recovery_runtime, "recovery_service", service_scope)
    monkeypatch.setattr(recovery_runtime, "_retry_admission", lambda: True)
    monkeypatch.setattr(recovery_runtime, "_cursors", {})
    monkeypatch.setattr(recovery_runtime, "_incident_cursor", None)
    for module in (recovery_view, recovery_review_view):
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
    incident_id = alert["embed"].footer.text.removeprefix(recovery_view.FOOTER_PREFIX)
    with service_scope() as service:
        assert service.store.get(incident_id)["AlertMessageID"] == 40

    interaction = SimpleNamespace(
        user=SimpleNamespace(id=1),
        guild_id=2,
        channel_id=3,
        message=message,
        followup=SimpleNamespace(send=AsyncMock()),
    )

    def current_view():
        sent = interaction.followup.send.call_args.kwargs
        assert sent["ephemeral"] is True
        return sent["view"]

    async def click(label):
        await button(current_view(), label).callback(interaction)

    # A newly constructed persistent entry must recover the alert's identity.
    await button(recovery_view.RecoveryEntryView(), "Review & fix").callback(interaction)
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
        await click("Read & publish current config")
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
        label = child_row["evidence"]["actions"]["abandon_capture"]["label"]
        await click(label)
        assert r.outcomes.inspect(child_id)["resources"]
        await click("Confirm & apply repair")
        assert current_view().row["State"] == "resolved"
        assert current_view().row["evidence"]["outcome"] == "export_skipped"
        assert not r.outcomes.inspect(child_id)["resources"]
        # A replayed old confirmation cannot republish, even after new services.
        await button(publication_confirmation, "Confirm & apply repair").callback(interaction)
        assert calls == [1]

    await button(close_confirmation, "Confirm & apply repair").callback(interaction)
    with service_scope() as service:
        final = service.refresh(continuation_id)
        assert final["State"] == "resolved"
        assert not service.store.pending_actions(incident_id)
        assert not service.store.pending_actions(continuation_id)
        assert not service.store.list_open()
        assert not r.outcomes.inspect(r.source)["resources"]
