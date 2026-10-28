"""Shared failure scenarios exercised through MGE and the existing event caller."""

import asyncio
from threading import Event
from types import SimpleNamespace

import pytest

from core.coalesced_work import CoalescedWork
from core.owned_work import drain_thread
from mge.mge_signup_service import ServiceResult
from ui.views.mge_signup_modal import MgeSignupModalPayload
from ui.views.mge_simplified_signup_form_view import MgeSimplifiedSignupFormView


class Interaction:
    def __init__(self, *, ack_error=False, reply_error=False, user_id=1):
        self.id = 1234
        self.user = SimpleNamespace(id=user_id, roles=[])
        self.guild = None
        self.events = []
        self.ack_error = ack_error
        self.reply_error = reply_error
        self.done = False
        self.response = SimpleNamespace(defer=self.defer, is_done=lambda: self.done)
        self.followup = SimpleNamespace(send=self.send)

    async def defer(self, **kwargs):
        self.events.append(("ack", kwargs))
        if self.ack_error:
            raise RuntimeError("simulated unknown acknowledgement")
        self.done = True

    async def send(self, text, **kwargs):
        self.events.append(("reply", text))
        if self.reply_error:
            raise RuntimeError("simulated response failure")


def form(refresh=None):
    payload = MgeSignupModalPayload(
        42, 100, "Fixture", set(), set(), on_success_refresh=refresh, owner_discord_id=1
    )
    view = MgeSimplifiedSignupFormView(payload=payload, commander_options={1: "Fixture"})
    view.selected_priority_rank_value = "high_1_5"
    view.selected_commander_id = 1
    return view


@pytest.mark.asyncio
async def test_reply_failure_does_not_erase_commit_or_skip_refresh(monkeypatch):
    from mge import mge_signup_service

    interaction = Interaction(reply_error=True)

    def mutate(**kwargs):
        assert interaction.done
        interaction.events.append(("commit", kwargs["operation_id"]))
        return ServiceResult(True, "Signup created.", 99)

    monkeypatch.setattr(mge_signup_service, "create_signup", mutate)
    view = form(lambda event: interaction.events.append(("refresh", event)))
    await view.submit_btn.callback(interaction)
    await view.submit_btn.callback(Interaction())
    assert [e[0] for e in interaction.events] == ["ack", "commit", "reply", "refresh"]
    assert interaction.events[0][1] == {"ephemeral": True, "invisible": False}


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", ["ack_unknown", "other_user", "shutdown"])
async def test_admission_failures_never_enter_mutation(monkeypatch, scenario):
    from core import interaction_safety
    from mge import mge_signup_service

    def forbidden(**kwargs):
        pytest.fail("mutation must not enter")

    monkeypatch.setattr(mge_signup_service, "create_signup", forbidden)
    if scenario == "shutdown":
        interaction_safety.close_private_operations()
    await form().submit_btn.callback(
        Interaction(
            ack_error=scenario == "ack_unknown", user_id=2 if scenario == "other_user" else 1
        )
    )


@pytest.mark.asyncio
async def test_mge_cancellation_drains_worker_and_presentation_once(monkeypatch):
    from mge import mge_signup_service

    entered, release = Event(), Event()
    calls = []

    def mutate(**kwargs):
        entered.set()
        assert release.wait(3)
        calls.append("committed")
        return ServiceResult(True, "saved", 99)

    monkeypatch.setattr(mge_signup_service, "create_signup", mutate)
    view = form(lambda event: calls.append("refreshed"))
    task = asyncio.create_task(view.submit_btn.callback(Interaction()))
    try:
        assert await asyncio.to_thread(entered.wait, 2)
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        await view.submit_btn.callback(Interaction())
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert calls == ["committed", "refreshed"]


@pytest.mark.asyncio
async def test_second_caller_event_receipt_cancellation_retains_ownership(monkeypatch):
    from services import event_delivery_service as delivery

    entered, release = Event(), Event()
    calls = []

    def begin(key, **kwargs):
        entered.set()
        assert release.wait(3)
        calls.append(key)
        return True

    monkeypatch.setattr(delivery.store, "begin", begin)
    task = asyncio.create_task(delivery.begin("fixture", kind="fixture", target="fixture"))
    try:
        assert await asyncio.to_thread(entered.wait, 2)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert calls == ["fixture"]


@pytest.mark.asyncio
async def test_shared_worker_preserves_context_and_exception():
    from contextvars import ContextVar

    from services.legacy_export_snapshot_service import drain_thread as compatibility

    marker = ContextVar("fixture")
    marker.set("owner")
    assert await drain_thread(marker.get) == await compatibility(marker.get) == "owner"

    def fail():
        raise ValueError("fixture")

    with pytest.raises(ValueError):
        await compatibility(fail)


@pytest.mark.asyncio
async def test_refresh_burst_coalesces_and_mutation_during_refresh_requires_new_pass():
    work = CoalescedWork()
    entered, release = asyncio.Event(), asyncio.Event()
    state = {"revision": 1}
    displayed = []

    async def refresh():
        revision = state["revision"]
        entered.set()
        await release.wait()
        displayed.append(revision)
        return True

    tasks = [work.request("event", refresh) for _ in range(20)]
    await entered.wait()
    state["revision"] = 2
    tasks += [work.request("event", refresh) for _ in range(20)]
    release.set()
    await asyncio.gather(*tasks)
    assert displayed == [1, 2]
    assert work.snapshot() == {
        "requests": 40,
        "passes": 2,
        "coalesced": 39,
        "pending": 0,
        "closed": False,
    }
    await work.drain()
    with pytest.raises(RuntimeError):
        work.request("event", refresh)


@pytest.mark.asyncio
async def test_refresh_failure_is_observed_and_new_request_can_recover():
    work = CoalescedWork()

    async def fail():
        raise ValueError("fixture")

    with pytest.raises(ValueError):
        await work.run("event", fail)
    assert work.snapshot()["passes"] == 1  # No automatic replay of a failed pass.
    assert work.snapshot()["exceptions"] == 1

    async def recover():
        return True

    assert await work.run("event", recover)
    assert work.snapshot()["pending"] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("newer_fails", [False, True])
async def test_newer_refresh_survives_failure_of_inflight_pass(newer_fails, caplog):
    work = CoalescedWork()
    entered, release = asyncio.Event(), asyncio.Event()
    calls = []

    async def first():
        calls.append("first")
        entered.set()
        await release.wait()
        raise ValueError("first failed")

    async def latest():
        calls.append("latest")
        if newer_fails:
            raise RuntimeError("latest failed")
        return True

    task = work.request("event", first)
    await entered.wait()
    assert work.request("event", latest) is task
    release.set()
    if newer_fails:
        with pytest.raises(RuntimeError, match="latest failed"):
            await task
    else:
        assert await task is True
    assert calls == ["first", "latest"]
    assert work.snapshot()["passes"] == 2
    assert work.snapshot()["pending"] == 0
    assert work.snapshot()["failed_passes"] == 1 + int(newer_fails)
    assert work.snapshot()["exceptions"] == 1 + int(newer_fails)
    assert "coalesced_refresh_failed error_type=ValueError" in caplog.text


@pytest.mark.asyncio
async def test_refresh_destinations_are_not_coalesced(monkeypatch):
    from mge import mge_embed_manager as manager

    destinations = []

    async def sync(**kwargs):
        destinations.append(kwargs["signup_channel_id"])

    monkeypatch.setattr(manager, "sync_event_signup_embed", sync)
    bot = object()
    await asyncio.gather(
        *[
            manager.request_signup_refresh(bot=bot, event_id=42, signup_channel_id=channel)
            for channel in (10, 11, 10)
        ]
    )
    assert sorted(destinations) == [10, 11]


@pytest.mark.asyncio
async def test_keyword_modal_callback_acknowledges_before_data_preparation(monkeypatch):
    from core.interaction_safety import private_operation
    from ui.views import mge_roster_builder_view as roster

    interaction = Interaction()

    class Handler:
        @private_operation
        async def callback(self, modal_interaction):
            assert modal_interaction.done

    await Handler().callback(modal_interaction=interaction)
    parent = roster.MgeRosterBuilderView(42, 1)
    monkeypatch.setattr(roster, "is_admin_or_leadership_interaction", lambda _: True)

    async def snapshot(signup_id):
        assert interaction.done
        return {"SignupId": signup_id}

    async def prepared(inter, row):
        interaction.events.append(("prepared", row["SignupId"]))

    monkeypatch.setattr(parent, "_applicant_snapshot", snapshot)
    selector = roster._SelectRow(
        placeholder="fixture",
        options=[],
        on_pick=lambda inter, value: parent._on_pick_applicant(inter, value, prepared),
    )
    selector._selected_values = ["99"]
    selector._interaction = SimpleNamespace(data={"values": ["99"]})
    await selector.callback(interaction)
    assert interaction.events[-1] == ("prepared", 99)


@pytest.mark.asyncio
async def test_form_uses_current_roles_instead_of_open_time_roles(monkeypatch):
    from mge import mge_signup_service
    from ui.views import mge_simplified_signup_form_view as forms

    view = form()
    view.payload.actor_role_ids = {999}
    monkeypatch.setattr(forms, "member_role_ids", lambda _: set())
    observed = []

    def mutate(**kwargs):
        observed.append(kwargs["actor_role_ids"])
        return ServiceResult(False, "permission changed")

    monkeypatch.setattr(mge_signup_service, "create_signup", mutate)
    await view.submit_btn.callback(Interaction())
    assert observed == [set()]
