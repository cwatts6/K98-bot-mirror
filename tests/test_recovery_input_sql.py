"""Guided page persistence and confirmation CAS on actual temporary SQL tables."""

import json
import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.recovery_service import RecoveryService
from tests.test_guided_recovery import ACTOR
from tests.test_recovery_sql import store as store

pytestmark = pytest.mark.skipif(
    os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Explicit temporary SQL opt-in"
)


class Adapter:
    def __init__(self):
        self.receipts = {}
        self.calls = []

    def inspect(self, source_id):
        return (
            dict(
                title="Replacement files",
                explanation="Choose fresh files",
                actions=dict(
                    choose=dict(
                        label="Choose replacement files",
                        input=True,
                        check="Verify these are fresh",
                        effect="Record this proposal",
                    )
                ),
            ),
            "a" * 64,
            bool(self.receipts),
        )

    def input_fields(self, source_id, action, token):
        return [
            dict(key=str(i), label=f"Output {i}", help="Paste a fresh file link", max_length=512)
            for i in range(6)
        ]

    def validate_input(self, source_id, action, token, payload):
        if len(set(payload.values())) != 6:
            raise SourceConflict("Six distinct files required")
        return "Six fresh files selected."

    def execute(self, source_id, action, token, actor, reason, *, payload):
        self.calls.append((actor, payload))
        self.receipts[actor] = payload

    def reconcile(self, source_id, action):
        receipt = self.receipts.get("recovery:" + str(action["ActionID"]).lower())
        return (
            "verified"
            if receipt is not None and receipt == json.loads(action["InputJson"])
            else None
        )


def setup(store):
    adapter = Adapter()
    service = RecoveryService(store, {"export_job": adapter}, admin_id=1, guild_id=2, channel_id=3)
    row = service.review_source(ACTOR, "export_job", str(uuid4()))
    return service, adapter, row


def save(service, row, page, version):
    fields = service.input_page(ACTOR, row["IncidentID"], "choose", page)["fields"]
    return service.save_input(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "choose",
        page,
        version,
        {f["key"]: "fresh-file-" + f["key"] for f in fields},
    )


def test_pages_survive_restart_and_confirm_exact_saved_input(store):
    service, adapter, row = setup(store)
    assert save(service, row, 0, 0)["completed"] == 5
    restarted = RecoveryService(store, service.adapters, admin_id=1, guild_id=2, channel_id=3)
    assert (
        restarted.input_page(ACTOR, row["IncidentID"], "choose", 0)["fields"][0]["value"]
        == "fresh-file-0"
    )
    assert save(restarted, row, 1, 1)["completed"] == 6
    preview = restarted.input_confirmation(ACTOR, row["IncidentID"], "choose")
    result = restarted.execute_input(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "choose",
        preview["draft_version"],
    )
    assert result["State"] == "resolved" and not result["pending_action"]
    assert len(adapter.calls) == 1 and len(adapter.calls[0][1]) == 6


def test_stale_parallel_forms_cannot_overwrite_newer_page(store):
    service, _, row = setup(store)
    save(service, row, 0, 0)
    with pytest.raises(SourceConflict, match="newer choices"):
        save(service, row, 1, 0)
    with pytest.raises(SourceConflict, match="every guided page"):
        service.input_confirmation(ACTOR, row["IncidentID"], "choose")


def test_edited_choices_invalidate_confirmation_and_direct_execute_cannot_bypass_form(store):
    service, adapter, row = setup(store)
    save(service, row, 0, 0)
    save(service, row, 1, 1)
    preview = service.input_confirmation(ACTOR, row["IncidentID"], "choose")
    save(service, row, 0, 2)
    with pytest.raises(SourceConflict, match="choices changed"):
        service.execute_input(
            ACTOR,
            row["IncidentID"],
            row["Revision"],
            row["EvidenceHash"],
            "choose",
            preview["draft_version"],
        )
    with pytest.raises(SourceConflict, match="guided recovery form"):
        service.execute(
            ACTOR, row["IncidentID"], row["Revision"], row["EvidenceHash"], "choose", "Bypass form"
        )
    assert not adapter.calls


def test_pending_action_prevents_further_input_even_after_restart(store):
    service, adapter, row = setup(store)
    save(service, row, 0, 0)
    save(service, row, 1, 1)
    draft = store.input_draft(row["IncidentID"], "choose")
    action_id, acquired = store.claim(
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "choose",
        "discord:1",
        "Confirm",
        payload=draft["input"],
        draft_version=draft["version"],
    )
    assert acquired
    with pytest.raises(SourceConflict, match="no longer available"):
        service.input_page(ACTOR, row["IncidentID"], "choose", 0)
    assert not adapter.calls
