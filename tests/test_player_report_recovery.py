"""Report recovery is a guided continuation of an exact atomic producer contract."""

import json
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.player_report_recovery_dal import PlayerReportRecoveryDAL
from services.player_report_recovery_service import (
    PlayerReportCaptureRecovery,
    PlayerReportRecoveryAdapter,
)
from tests.test_import_capture_recovery import fixture as stats_fixture


def fixture():
    original, preview, resources = stats_fixture()
    prep = preview["preparation"]
    request = json.loads(prep["RequestJson"])
    operation = str(uuid4())
    request.update(kvk_no=None)
    request["request"].update(
        operation=operation,
        producer=dict(kind="player_stats_report", atomic_checkpoint=1, operation=operation),
    )
    generation = original.generation(prep, preview["execution"])
    generation["producer"] = dict(procedure="dbo.SP_Stats_for_Upload", atomic_checkpoint=1)
    prep.update(
        KVK_NO=None,
        SpoolHash=None,
        SpoolBytes=None,
        RequestJson=json.dumps(request),
        RequestHash=digest(request),
        GenerationJson=json.dumps(generation),
        State="committed",
    )
    preview.update(execution=None, explanation=None, resources=resources)
    return PlayerReportCaptureRecovery(original.runtime, original.outcomes), preview, resources


def test_committed_report_offers_capture_and_skip_without_replay():
    service, preview, _ = fixture()
    evidence, _, resolved = PlayerReportRecoveryAdapter(service.outcomes, service).inspect("id")
    assert not resolved
    assert set(evidence["actions"]) == {"resume_capture", "abandon_capture"}
    assert "player-stat report" in evidence["actions"]["resume_capture"]["check"]
    assert evidence["title"] == "Player-stat report recovery"


@pytest.mark.parametrize(
    "change", ["hash", "contract", "procedure", "registration", "import_receipt"]
)
def test_invalid_contract_cannot_offer_a_repair(change):
    service, preview, _ = fixture()
    prep = preview["preparation"]
    if change == "hash":
        prep["RequestHash"] = b"x" * 32
    elif change == "contract":
        request = json.loads(prep["RequestJson"])
        request["request"]["producer"]["atomic_checkpoint"] = 0
        prep.update(RequestJson=json.dumps(request), RequestHash=digest(request))
    elif change == "import_receipt":
        preview["execution"] = {"State": "completed"}
    else:
        generation = json.loads(prep["GenerationJson"])
        generation["producer" if change == "procedure" else "registration_sha256"] = "foreign"
        prep["GenerationJson"] = json.dumps(generation)
    evidence, _, resolved = PlayerReportRecoveryAdapter(service.outcomes, service).inspect("id")
    assert not resolved and not evidence["actions"]


def test_uncommitted_attempt_has_explicit_verified_closure_action():
    service, preview, resources = fixture()
    prep = preview["preparation"]
    prep.update(State="uncertain", GenerationJson=None)
    preview["action"] = PlayerReportRecoveryDAL.action(prep, None, resources)
    adapter = PlayerReportRecoveryAdapter(service.outcomes, service)
    evidence, token, resolved = adapter.inspect("source")
    assert not resolved and set(evidence["actions"]) == {"cancel_report"}
    assert "does not refresh" in evidence["actions"]["cancel_report"]["check"]
    adapter.execute("source", "cancel_report", token, "admin", "close")
    service.outcomes.cancel.assert_called_once_with("source", token, "admin", "close")


@pytest.mark.parametrize(
    "field,value",
    [
        ("OwnerID", str(uuid4())),
        ("Fence", 999),
        ("ActiveJobID", str(uuid4())),
        ("ResourceKey", "other"),
    ],
)
def test_uncommitted_release_requires_exact_reservation(field, value):
    _, preview, resources = fixture()
    preview["preparation"].update(State="uncertain", GenerationJson=None)
    resources[0][field] = value
    with pytest.raises(SourceConflict):
        PlayerReportRecoveryDAL.action(preview["preparation"], None, resources)


def test_report_intent_is_stable_inside_one_invocation_and_removed_after():
    from services.producer_recovery_intent import current_intent, player_report_intent

    @player_report_intent
    def inner():
        return current_intent().copy()

    @player_report_intent
    def outer():
        return current_intent().copy(), inner()

    first, nested = outer()
    assert first == nested and first["atomic_checkpoint"] == 1
    assert current_intent() is None and inner()["operation"] != first["operation"]


@pytest.mark.asyncio
async def test_actual_report_button_requires_guided_confirmation(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from tests.test_guided_recovery import ACTOR, setup
    from ui.views import recovery_view as view

    service, preview, resources = fixture()
    preview["preparation"].update(State="uncertain", GenerationJson=None)
    preview["action"] = PlayerReportRecoveryDAL.action(preview["preparation"], None, resources)
    evidence, _, _ = PlayerReportRecoveryAdapter(service.outcomes, service).inspect("source")
    _, _, _, row = setup()
    row["evidence"] = evidence
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(view, "call", AsyncMock(return_value=row))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        b
        for b in view.RecoveryIncidentView(row).children
        if b.label == "Close failed report & release"
    )
    await button.callback(interaction)
    view.call.assert_awaited_once_with("review", ACTOR, row["IncidentID"])
    response = interaction.followup.send.call_args.kwargs
    assert response["ephemeral"] and response["view"].action == "cancel_report"
    assert "does not refresh" in response["embed"].fields[0].value
