from copy import deepcopy
import json
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit, digest
from tests.test_config_read_containment import setup
from tests.test_guided_recovery import ACTOR


def unstarted(monkeypatch, *, lost=False):
    client, dal, snapshot, source, _, docs, service, store = setup(monkeypatch)
    request = {"read_configuration": str(uuid4())}
    snapshot["preparation"].update(
        RequestJson=json.dumps(request), RequestHash=digest(request).hex()
    )
    snapshot["streams"] = []
    dal.target_data.side_effect = lambda *a, **k: deepcopy(
        dict(preparation=snapshot["preparation"], resources=snapshot["resources"], stream_ids=[])
    )

    def settle(target, expected, audit, *, containment):
        assert expected == snapshot and not target.stream_ids and containment["streams"] == {}
        snapshot["preparation"].update(State="unavailable", GenerationJson=json.dumps(audit))
        snapshot["resources"] = []
        if lost:
            raise UncertainCommit("Cancelled; acknowledgement lost")

    dal.settle.side_effect = settle
    return client, dal, snapshot, source, docs, service, store


@pytest.mark.parametrize("lost", [False, True])
def test_alert_guides_confirmed_cancellation_and_verifies_original_receipt(monkeypatch, lost):
    client, dal, snapshot, source, docs, service, store = unstarted(monkeypatch, lost=lost)
    row = service.review_source(ACTOR, "configuration_read", source)
    assert row["evidence"]["outcome"] == "unstarted_read"
    assert row["evidence"]["actions"]["contain_read"]["label"] == "Cancel unstarted read"
    assert service.recover_automatic(row["IncidentID"])["State"] == "open"
    dal.settle.assert_not_called()
    with pytest.raises(SourceConflict):
        client.apply_configuration_recovery(source, row["EvidenceHash"], "admin", "Cancel")
    resolved = service.execute(
        ACTOR, row["IncidentID"], row["Revision"], row["EvidenceHash"], "contain_read", "Cancel"
    )
    assert resolved["State"] == "resolved" and store.actions[0]["State"] == "verified"
    assert "cancelled before execution" in resolved["evidence"]["explanation"]
    service.refresh(row["IncidentID"])
    assert dal.settle.call_count == 1 and len(docs) == 1
    audit = json.loads(snapshot["preparation"]["GenerationJson"])
    assert audit["streams"] == {} and audit["before"]["streams"] == []
    assert audit["child_termination_verified"] is False


@pytest.mark.parametrize(
    "bad", ["request", "enrollment", "requests", "events", "foreign_owner", "stream"]
)
def test_incomplete_or_conflicting_unstarted_evidence_never_releases(monkeypatch, bad):
    client, dal, snapshot, source, _, service, _ = unstarted(monkeypatch)
    if bad in {"request", "enrollment"}:
        request = {} if bad == "request" else {"purpose": "output_enrollment"}
        snapshot["preparation"].update(
            RequestJson=json.dumps(request), RequestHash=digest(request).hex()
        )
    elif bad in {"requests", "events"}:
        snapshot[{"requests": "request_count", "events": "event_count"}[bad]] = 1
    elif bad == "foreign_owner":
        snapshot["resources"][0]["OwnerID"] = str(uuid4())
    else:
        snapshot["streams"] = [{"StreamID": str(uuid4())}]
    row = service.review_source(ACTOR, "configuration_read", source)
    assert not row["evidence"]["actions"]
    dal.settle.assert_not_called()


@pytest.mark.parametrize("damage", ["private", "sql"])
def test_cancellation_resolution_requires_the_committed_private_receipt(monkeypatch, damage):
    client, _, snapshot, source, docs, service, _ = unstarted(monkeypatch)
    row = service.review_source(ACTOR, "configuration_read", source)
    service.execute(
        ACTOR, row["IncidentID"], row["Revision"], row["EvidenceHash"], "contain_read", "Cancel"
    )
    if damage == "private":
        docs.clear()
    else:
        audit = json.loads(snapshot["preparation"]["GenerationJson"])
        audit["actor"] = "different"
        snapshot["preparation"]["GenerationJson"] = json.dumps(audit)
    with pytest.raises((SourceConflict, KeyError)):
        client.inspect_configuration_recovery(source)


@pytest.mark.asyncio
async def test_cancel_button_displays_the_unstarted_read_checklist(monkeypatch):
    from types import SimpleNamespace

    from ui.views import recovery_view as view

    _, dal, _, source, _, service, _ = unstarted(monkeypatch)
    row = service.review_source(ACTOR, "configuration_read", source)
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(view, "call", AsyncMock(return_value=row))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        b for b in view.RecoveryIncidentView(row).children if b.label == "Cancel unstarted read"
    )
    await button.callback(interaction)
    sent = interaction.followup.send.call_args.kwargs
    assert "no execution stream or provider requests" in sent["embed"].fields[0].value
    assert sent["ephemeral"] and sent["view"].action == "contain_read"
    dal.settle.assert_not_called()
