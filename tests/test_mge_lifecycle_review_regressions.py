"""Real callback and service interleavings uncovered by delivery review."""

import asyncio
from threading import Event
from types import SimpleNamespace

import pytest

from mge import mge_roster_service as service
from mge.mge_roster_execution import run_roster_mutation
from tests.test_p1_owned_operations import Interaction


@pytest.mark.asyncio
async def test_two_rank_additions_share_whole_service_ownership(monkeypatch):
    entered, release = Event(), Event()
    rows = []
    reads = []

    def signup(signup_id, event_id):
        reads.append(signup_id)
        if signup_id == 1:
            entered.set()
            assert release.wait(3)
        return dict(
            SignupId=signup_id,
            EventId=event_id,
            GovernorId=signup_id,
            IsActive=1,
            RequestedCommanderId=1,
        )

    def insert(**kwargs):
        rows.append(
            dict(
                AwardId=1,
                GovernorId=kwargs["governor_id"],
                AwardStatus="awarded",
                AwardedRank=kwargs["awarded_rank"],
            )
        )
        return 1

    monkeypatch.setattr(service.mge_roster_dal, "fetch_signup_snapshot", signup)
    monkeypatch.setattr(service.mge_roster_dal, "fetch_event_awards", lambda _: list(rows))
    monkeypatch.setattr(service.mge_roster_dal, "insert_award", insert)
    monkeypatch.setattr(service.mge_roster_dal, "insert_award_audit", lambda **_: True)
    first = asyncio.create_task(
        run_roster_mutation(
            42,
            service.add_signup_with_rank,
            event_id=42,
            signup_id=1,
            target_rank=1,
            actor_discord_id=1,
        )
    )
    assert await asyncio.to_thread(entered.wait, 2)
    second = asyncio.create_task(
        run_roster_mutation(
            42,
            service.add_signup_with_rank,
            event_id=42,
            signup_id=2,
            target_rank=1,
            actor_discord_id=2,
        )
    )
    try:
        await asyncio.sleep(0)
        assert reads == [1]
    finally:
        release.set()
    a, b = await asyncio.gather(first, second)
    assert a.success and not b.success and "occupied" in b.message
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_notes_cannot_restore_a_stale_rank_and_cancellation_retains_owner(monkeypatch):
    entered, release = Event(), Event()
    row = dict(AwardId=1, EventId=42, AwardedRank=1, AwardStatus="awarded")
    writes = []

    def fetch(_):
        snapshot = dict(row)
        entered.set()
        assert release.wait(3)
        return snapshot

    def update(**kwargs):
        row["AwardedRank"] = kwargs["awarded_rank"]
        row["InternalNotes"] = kwargs["internal_notes"]
        writes.append("notes")
        return True

    def rank(**kwargs):
        row["AwardedRank"] = kwargs["new_rank"]
        writes.append("rank")
        return {"ok": True}

    monkeypatch.setattr(service.mge_roster_dal, "fetch_award_by_id", fetch)
    monkeypatch.setattr(service.mge_roster_dal, "update_award", update)
    monkeypatch.setattr(service.mge_roster_dal, "apply_set_rank_atomic", rank)
    first = asyncio.create_task(
        run_roster_mutation(
            42, service.update_internal_notes, award_id=1, notes="retained", actor_discord_id=1
        )
    )
    assert await asyncio.to_thread(entered.wait, 2)
    first.cancel()
    second = asyncio.create_task(
        run_roster_mutation(42, service.set_rank, award_id=1, new_rank=2, actor_discord_id=2)
    )
    try:
        await asyncio.sleep(0)
        assert not first.done() and writes == []
        # Unrelated events can progress while this event remains owned.
        assert await run_roster_mutation(43, lambda: "independent") == "independent"
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await first
    assert (await second).success
    assert writes == ["notes", "rank"] and row["AwardedRank"] == 2
    assert row["InternalNotes"] == "retained"


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["Open", "Fixed"])
async def test_cancel_after_mode_change_entry_reports_processing(monkeypatch, mode):
    from ui.views import mge_admin_view as views

    entered, release = Event(), Event()

    def switch(**kwargs):
        entered.set()
        assert release.wait(3)
        return SimpleNamespace(success=True, deleted_signup_count=2, updated_row_count=1)

    monkeypatch.setattr(views, "switch_event_to_" + mode.lower(), switch)
    deps = views.MGEAdminViewDeps(refresh_embed=lambda _: None, is_admin=lambda _: True)
    view = getattr(views, "ConfirmSwitch" + mode + "View")(42, deps)
    task = asyncio.create_task(view.confirm_switch.callback(Interaction()))
    assert await asyncio.to_thread(entered.wait, 2)
    cancel = Interaction()
    cancel.done = True
    try:
        await view.cancel.callback(cancel)
        assert "already processing" in cancel.events[-1][1]
        assert not view._completed
    finally:
        release.set()
    await task
    assert view._completed


@pytest.mark.asyncio
async def test_prepared_publish_reminders_modal_has_exactly_one_ack(monkeypatch):
    from ui.views import mge_publish_view as views

    monkeypatch.setattr(views, "is_admin_or_leadership_interaction", lambda _: True)
    monkeypatch.setattr(
        views.mge_publish_dal, "fetch_event_publish_context", lambda _: {"RuleMode": "fixed"}
    )
    monkeypatch.setattr(
        views.mge_publish_dal, "fetch_default_award_reminders_text", lambda _: "Fixture reminder"
    )
    view = views.MgePublishView(event_id=42)
    prepared = []
    calls = []

    async def offer(interaction, modal):
        assert interaction.done
        prepared.append(modal)

    async def publish(**kwargs):
        assert kwargs["interaction"].done
        calls.append(kwargs["reminders_text_override"])

    monkeypatch.setattr(views, "offer_prepared_modal", offer)
    monkeypatch.setattr(view, "_run_publish", publish)
    await view.publish.callback(Interaction())
    submission = Interaction()
    original = submission.response.defer

    async def defer(**kwargs):
        assert not submission.done, "double acknowledgement"
        await original(**kwargs)

    submission.response.defer = defer
    await prepared[0].callback(submission)
    assert calls == ["Fixture reminder"]
    assert len([event for event in submission.events if event[0] == "ack"]) == 1


@pytest.mark.parametrize("ranks, expected", [([], 99), ([1], None), (list(range(1, 16)), None)])
def test_insert_rechecks_rank_and_capacity_under_event_lock(monkeypatch, ranks, expected):
    from datetime import UTC, datetime

    from mge.dal import mge_roster_dal as dal

    calls = []

    class Cursor:
        def execute(self, sql, params):
            self.sql = sql
            calls.append(sql)

        def fetchone(self):
            if "FROM dbo.MGE_Events" in self.sql:
                return ("controlled", "signup_open")
            if "FROM dbo.MGE_Signups" in self.sql:
                return (100, True)
            return (99,)

        def fetchall(self):
            return [(rank,) for rank in ranks]

    monkeypatch.setattr(dal, "exec_with_cursor", lambda callback: callback(Cursor()))
    result = dal.insert_award(
        event_id=42,
        signup_id=1,
        governor_id=100,
        governor_name_snapshot="Fixture",
        requested_commander_id=1,
        requested_commander_name="Fixture",
        awarded_rank=1,
        award_status="awarded",
        waitlist_order=None,
        internal_notes=None,
        assigned_by_discord_id=1,
        now_utc=datetime.now(UTC),
    )
    assert result == expected
    assert "MGE_Events WITH (UPDLOCK, HOLDLOCK)" in calls[0]
    assert "MGE_Awards WITH (UPDLOCK, HOLDLOCK)" in calls[2]
    assert any("INSERT INTO" in call for call in calls) == (expected is not None)
