"""Timing adds evidence without changing response, worker or privacy contracts."""

import asyncio
from datetime import UTC, datetime, timedelta
import logging
from types import SimpleNamespace

import pytest

from core.interaction_safety import private_operation
from core.operation_timing import record_timing, timed_stage, timing_scope
from core.owned_work import drain_thread
from tests.test_p1_owned_operations import Interaction, form


def stages(caplog):
    return [r.operation_stage for r in caplog.records if hasattr(r, "operation_stage")]


@pytest.mark.asyncio
async def test_context_crosses_owned_thread_and_nested_callbacks_without_second_ack(caplog):
    caplog.set_level(logging.INFO)

    class View:
        @private_operation
        async def child(self, interaction):
            return await drain_thread(lambda: record_timing("fixture_dal", 0.002))

        @private_operation
        async def parent(self, interaction):
            await self.child(interaction)

    interaction = Interaction()
    interaction.created_at = datetime.now(UTC) - timedelta(seconds=1)
    await View().parent(interaction)
    rows = stages(caplog)
    assert len({r["reference"] for r in rows}) == 1
    assert [r["disposition"] for r in rows if r["stage"] == "acknowledgement"] == [
        "confirmed",
        "already_acknowledged",
    ]
    assert sum(e[0] == "ack" for e in interaction.events) == 1
    assert {r["stage"] for r in rows} >= {
        "fixture_dal",
        "worker_queue_wait",
        "worker_execution",
        "interaction_age_at_entry",
    }


@pytest.mark.asyncio
async def test_failed_ack_records_non_entry_without_token_or_exception_text(caplog):
    caplog.set_level(logging.INFO)

    class View:
        @private_operation
        async def callback(self, interaction):
            pytest.fail("must not enter")

    await View().callback(Interaction(ack_error=True))
    assert any(r["disposition"] == "unconfirmed" for r in stages(caplog))
    assert "simulated unknown acknowledgement" not in caplog.text


@pytest.mark.asyncio
async def test_real_signup_and_rank_callbacks_qualify_shared_timing(monkeypatch, caplog):
    from mge import mge_signup_service
    from mge.mge_roster_service import RosterResult
    from ui.views import mge_simplified_leadership_view as views

    caplog.set_level(logging.INFO)
    monkeypatch.setattr(
        mge_signup_service,
        "create_signup",
        lambda **_: mge_signup_service.ServiceResult(True, "Saved", signup_id=1),
    )
    signup = form()
    await signup.submit_btn.callback(Interaction())
    first = {r["reference"] for r in stages(caplog)}
    caplog.clear()
    monkeypatch.setattr(views, "is_admin_or_leadership_interaction", lambda _: True)
    monkeypatch.setattr(
        views.mge_roster_service, "set_rank", lambda **_: RosterResult(True, "Saved")
    )

    async def refresh(**_):
        return {"public": True, "leadership": True}

    monkeypatch.setattr(views.mge_embed_manager, "refresh_mge_boards", refresh)
    modal = views._AdjustRankModal(event_id=77, award_id=1)
    modal.rank_value = SimpleNamespace(value="2")
    interaction = Interaction()
    interaction.client = object()
    await modal.callback(interaction)
    second = {r["reference"] for r in stages(caplog)}
    assert len(first) == len(second) == 1 and first.isdisjoint(second)
    assert {r["stage"] for r in stages(caplog)} >= {
        "acknowledgement",
        "private_response",
        "worker_execution",
    }
    signup.stop()


def test_interrupted_stage_is_redacted_and_scope_is_reset(caplog):
    caplog.set_level(logging.INFO)
    with pytest.raises(RuntimeError), timing_scope(), timed_stage("fixture"):
        raise RuntimeError("private-payload-do-not-log")
    assert stages(caplog)[0]["disposition"] == "interrupted"
    assert "private-payload" not in caplog.text
    caplog.clear()
    record_timing("outside_scope", 1)
    assert stages(caplog) == []


@pytest.mark.asyncio
async def test_cancelled_stage_records_interruption_and_propagates(caplog):
    caplog.set_level(logging.INFO)
    with pytest.raises(asyncio.CancelledError), timing_scope(), timed_stage("fixture"):
        raise asyncio.CancelledError()
    assert stages(caplog)[0]["disposition"] == "interrupted"
