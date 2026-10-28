"""Failure boundaries use real preparation/readiness and board adapters, no live IO."""

import asyncio
from copy import deepcopy
from datetime import UTC, datetime
from threading import Event
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from core.owned_work import drain_thread
from mge import (
    mge_embed_manager as boards,
    mge_publish_service as publish,
    mge_simplified_flow_service as flow,
    mge_simplified_leadership_service as leadership,
)
from mge.dal import mge_review_dal as review, mge_roster_dal as roster
from mge.dataset_errors import MgeDatasetError
from mge.mge_roster_execution import run_roster_mutation


def signup(sid=1):
    return dict(
        EventId=77,
        SignupId=sid,
        GovernorId=100 + sid,
        GovernorNameSnapshot="Fixture",
        RequestedCommanderId=1,
        RequestPriority="High",
        PreferredRankBand="1-5",
        SignupCreatedUtc=datetime(2026, 1, 1, tzinfo=UTC),
    )


def award(sid=1, **changes):
    return dict(
        EventId=77,
        SignupId=sid,
        AwardId=1000 + sid,
        GovernorId=100 + sid,
        AwardStatus="awarded",
        AwardedRank=sid,
        TargetScore=8000000,
        **changes,
    )


@pytest.fixture
def dataset(monkeypatch):
    state = {"review": [signup()], "awards": [award()], "reads": [], "writes": []}

    def read_review(*_):
        state["reads"].append("review")
        return deepcopy(state["review"])

    def read_awards(*_):
        state["reads"].append("awards")
        return deepcopy(state["awards"])

    def insert(**kw):
        state["writes"].append(kw)
        row = award(kw["signup_id"])
        row.update(
            AwardStatus=kw["award_status"],
            AwardedRank=kw["awarded_rank"],
            WaitlistOrder=kw["waitlist_order"],
            TargetScore=None,
        )
        state["awards"].append(row)
        return row["AwardId"]

    monkeypatch.setattr(review, "run_query", read_review)
    monkeypatch.setattr(roster, "run_query", read_awards)
    monkeypatch.setattr(roster, "insert_award", insert)
    return state


@pytest.mark.parametrize(
    "module,method", [(review, "fetch_signup_review_rows"), (roster, "fetch_event_awards")]
)
def test_strict_error_is_not_empty_and_legacy_contract_remains(monkeypatch, module, method):
    def fail(*_):
        raise RuntimeError("private connection detail")

    monkeypatch.setattr(module, "run_query", fail)
    with pytest.raises(MgeDatasetError) as exc:
        getattr(module, method)(77, strict=True)
    assert exc.value.state == "unavailable"
    assert "private" not in str(exc.value)
    assert getattr(module, method)(77) == []
    monkeypatch.setattr(module, "run_query", lambda *_: [])
    assert getattr(module, method)(77, strict=True) == []


def test_payload_reuses_snapshot_but_publish_readiness_loads_fresh(dataset):
    first = leadership.get_leadership_board_payload(77)
    assert first["publish"]["publish_ready"]
    assert dataset["reads"] == ["review", "awards", "awards"]
    dataset["awards"][0]["TargetScore"] = None
    current = flow.evaluate_publish_readiness(77)
    assert not current["publish_ready"]
    assert first["publish"]["publish_ready"]  # not a mutable cross-call cache
    assert dataset["writes"] == []


def test_successfully_empty_is_valid_and_not_a_read_failure(dataset):
    dataset.update(review=[], awards=[])
    result = flow.get_ordered_leadership_rows(77)
    assert result["availability"] == "loaded_empty"
    assert flow.evaluate_dataset_readiness(result)["publish_ready"]  # existing policy
    assert dataset["reads"] == ["review", "awards"]


@pytest.mark.parametrize("failed_read", ["review", "awards"])
def test_read_failure_stops_before_placement_and_blocks_readiness(
    dataset, monkeypatch, failed_read
):
    dataset["awards"] = []

    def fail(*_):
        raise RuntimeError("unavailable")

    monkeypatch.setattr(review if failed_read == "review" else roster, "run_query", fail)
    result = flow.evaluate_publish_readiness(77)
    assert not result["publish_ready"]
    assert result["dataset_availability"] == "unavailable"
    assert dataset["writes"] == []


def test_partial_placement_is_incomplete_and_never_replayed(dataset, monkeypatch):
    dataset.update(review=[signup(1), signup(2), signup(3)], awards=[])
    original = roster.insert_award

    def insert(**kw):
        if kw["signup_id"] == 2:
            dataset["writes"].append(kw)
            return None  # rejection/unknown legacy outcome, not rollback proof
        return original(**kw)

    monkeypatch.setattr(roster, "insert_award", insert)
    result = flow.evaluate_publish_readiness(77)
    assert result["dataset_availability"] == "incomplete"
    assert [r["signup_id"] for r in dataset["writes"]] == [1, 2]
    assert len(dataset["awards"]) == 1


def test_post_placement_readback_failure_preserves_partial_outcome(dataset, monkeypatch):
    dataset["awards"] = []
    count = 0

    def read(*_):
        nonlocal count
        count += 1
        if count == 2:
            raise RuntimeError("readback unavailable")
        return []

    monkeypatch.setattr(roster, "run_query", read)
    result = flow.evaluate_publish_readiness(77)
    assert result["dataset_availability"] == "incomplete"
    assert len(dataset["writes"]) == 1


def test_self_heal_policy_retains_manual_ranks_rejections_and_waitlist(dataset):
    dataset["review"] = [signup(i) for i in range(1, 18)]
    dataset["awards"] = [award(i, ManualOrderOverride=True) for i in range(1, 16)]
    rejected = award(16)
    rejected.update(AwardStatus="rejected", AwardedRank=None)
    dataset["awards"].append(rejected)
    result = flow.get_ordered_leadership_rows(77)
    assert result["counts"]["roster_count"] == 15
    assert result["counts"]["rejected_count"] == 1
    assert result["counts"]["waitlist_count"] == 1
    assert [r["ComputedAwardedRank"] for r in result["roster_rows"]] == list(range(1, 16))
    assert len(dataset["writes"]) == 1 and dataset["writes"][0]["signup_id"] == 17
    assert dataset["writes"][0]["award_status"] == "waitlist"


def test_wrong_event_after_placement_is_incomplete(dataset, monkeypatch):
    dataset["awards"] = []
    original = roster.insert_award

    def insert(**kw):
        result = original(**kw)
        dataset["awards"][0]["EventId"] = 88
        return result

    monkeypatch.setattr(roster, "insert_award", insert)
    result = flow.evaluate_publish_readiness(77)
    assert result["dataset_availability"] == "incomplete"
    assert not result["publish_ready"]
    assert len(dataset["writes"]) == 1


@pytest.mark.parametrize("bad", ["review", "awards"])
def test_wrong_event_snapshot_never_enters_placement(dataset, bad):
    dataset[bad][0]["EventId"] = 88
    with pytest.raises(MgeDatasetError, match="could not be verified"):
        flow.get_ordered_leadership_rows(77)
    assert dataset["writes"] == []


@pytest.mark.asyncio
async def test_unavailable_payload_preserves_board_without_discord_or_identity_writes(
    dataset, monkeypatch
):
    monkeypatch.setattr(boards, "fetch_event_for_embed", lambda _: {"EventId": 77})
    monkeypatch.setattr(boards, "MGE_LEADERSHIP_CHANNEL_ID", 1)

    def fail(*_):
        raise RuntimeError("unavailable")

    monkeypatch.setattr(review, "run_query", fail)
    bot = SimpleNamespace()  # any Discord access would fail the test
    assert not await boards.sync_event_leadership_embed(bot=bot, event_id=77)
    assert dataset["writes"] == []


@pytest.mark.asyncio
async def test_publish_blocks_on_fresh_failed_load_before_adapter_or_mutation(dataset, monkeypatch):
    assert leadership.get_leadership_board_payload(77)["publish"]["publish_ready"]

    def fail(*_):
        raise RuntimeError("unavailable")

    monkeypatch.setattr(review, "run_query", fail)
    result = await publish.publish_event_awards(
        adapter=SimpleNamespace(), event_id=77, actor_discord_id=1
    )
    assert not result.success and "Publication has not started" in result.message


@pytest.mark.asyncio
async def test_prepare_shares_roster_worker_owner_and_cancellation_does_not_release_it(dataset):
    entered, release, queued = Event(), Event(), Event()

    def mutate():
        entered.set()
        assert release.wait(5)
        dataset["awards"][0]["TargetScore"] = None

    first = asyncio.create_task(run_roster_mutation(77, mutate))
    assert await asyncio.to_thread(entered.wait, 2)

    def prepare():
        queued.set()
        return leadership.get_leadership_board_payload(77)

    second = asyncio.create_task(drain_thread(prepare))
    try:
        assert await asyncio.to_thread(queued.wait, 2)
        first.cancel()
        await asyncio.sleep(0)
        first.cancel()
        assert not first.done() and not second.done()
        assert dataset["reads"] == []
        assert await run_roster_mutation(78, lambda: "independent") == "independent"
    finally:
        release.set()
        await asyncio.gather(first, return_exceptions=True)
    result = await second
    assert not result["publish"]["publish_ready"]


@pytest.mark.asyncio
async def test_leadership_error_response_is_private_and_not_empty_roster(monkeypatch):
    from ui.views.mge_simplified_leadership_view import MGESimplifiedLeadershipView

    interaction = SimpleNamespace(
        response=SimpleNamespace(is_done=lambda: True), followup=SimpleNamespace(send=AsyncMock())
    )
    view = MGESimplifiedLeadershipView(event_id=77)
    await view.on_error(MgeDatasetError("incomplete", "placement_unconfirmed"), None, interaction)
    assert interaction.followup.send.call_args.kwargs["ephemeral"] is True
    assert "could not be verified" in interaction.followup.send.call_args.args[0]
    view.stop()


@pytest.mark.parametrize("action", ["targets", "reset", "promote"])
def test_dataset_dependent_writers_return_safe_failure(dataset, monkeypatch, action):
    def fail(*_):
        raise RuntimeError("private SQL detail")

    monkeypatch.setattr(review, "run_query", fail)
    if action == "targets":
        result = publish.generate_targets_from_rank1(
            event_id=77, rank1_target_millions=8, actor_discord_id=1
        )
    elif action == "reset":
        result = leadership.reset_active_ranks(event_id=77, actor_discord_id=1)
    else:
        result = leadership.move_waitlist_to_roster_with_optional_demote(
            event_id=77, promote_award_id=1001, actor_discord_id=1
        )
    assert not result.success and "could not be verified" in result.message
    assert dataset["writes"] == []


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["targets", "reset"])
async def test_real_modal_and_confirmation_reply_privately_on_dataset_failure(
    dataset, monkeypatch, action
):
    from tests.test_p1_owned_operations import Interaction
    from ui.views import mge_simplified_leadership_view as views

    def fail(*_):
        raise RuntimeError("private SQL detail")

    monkeypatch.setattr(review, "run_query", fail)
    monkeypatch.setattr(views, "is_admin_or_leadership_interaction", lambda _: True)
    interaction = Interaction()
    interaction.followup.send = AsyncMock()
    if action == "targets":
        control = views._GenerateTargetsModal(event_id=77)
        control.rank1 = SimpleNamespace(value="8")
        await control.callback(interaction)
    else:
        control = views._ResetRanksConfirmView(event_id=77)
        await control.confirm.callback(interaction)
        control.stop()
    reply = interaction.followup.send.call_args
    assert reply.kwargs["ephemeral"] is True
    assert "could not be verified" in reply.args[0]
    assert dataset["writes"] == []
