"""Grouped decisions use real disposable captures and independently saved intents."""

import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import digest
from services.export_snapshot_store import SnapshotReceipt
from services.historical_retirement_group_dal import HistoricalRetirementGroupDAL
from services.historical_retirement_group_service import HistoricalBatchAdapter
from services.recovery_dal import RecoveryDAL
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryActor, RecoveryService, SourceConflict
from tests.test_guided_recovery import ACTOR
from tests.test_historical_import_recovery_sql import historical as historical
from tests.test_import_capture_recovery_sql import recovery as recovery
from tests.test_recovery_sql import store as store

pytestmark = [
    pytest.mark.skipif(
        os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Disposable SQL opt-in"
    ),
    pytest.mark.parametrize("recovery", ["scan_data"], indirect=True),
]


def clone_capture(r, *, destination=None):
    prep = dict(r.outcomes.inspect(r.source)["preparation"])
    receipt = SnapshotReceipt(
        prep["SpoolKey"], prep["SpoolBytes"], bytes(prep["SpoolHash"]).hex(), prep["StorageOwner"]
    )
    payload = json.loads(r.runtime.store.read(receipt))
    source = str(uuid4())
    request = json.loads(prep["RequestJson"])
    request["request"]["operation"] = source
    generation = json.loads(prep["GenerationJson"])
    if destination:
        from services.legacy_export_snapshot_service import configuration_digest

        request["request"]["config"]["destinations"] = [destination]
        payload["config"]["destinations"] = [destination]
        generation["registration_sha256"] = configuration_digest(request["request"]["config"])
        generation["config_sha256"] = configuration_digest(payload["config"])
    prep.update(RequestJson=json.dumps(request), RequestHash=digest(request))
    generation["commit_identity"] = source
    payload.update(preparation_id=source, generation=generation)
    retained = r.runtime.store.put(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    )
    prep.update(
        PreparationID=source,
        GenerationJson=json.dumps(generation),
        SpoolKey=retained.key,
        SpoolBytes=retained.byte_count,
        SpoolHash=bytes.fromhex(retained.sha256),
    )
    prep["EnqueueSequence"] = r.owner.execute(
        r.rewrite("SELECT MAX(EnqueueSequence)+1 FROM dbo.ExportPreparation")
    ).fetchval()
    columns = list(prep)
    r.owner.execute(
        r.rewrite(
            f"INSERT dbo.ExportPreparation ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})"
        ),
        *(prep[c] for c in columns),
    )
    r.adapter.historical.verify(r.adapter.historical.dal.inspect(source))
    return source


def setup(r, store, sources):
    batch = HistoricalBatchAdapter(store)
    service = RecoveryService(
        store,
        {"stats_import": r.adapter, batch.kind: batch},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    incidents = [service.review_source(ACTOR, "stats_import", source) for source in sources]
    return service, incidents


@pytest.mark.asyncio
async def test_group_selection_confirmation_restart_and_complete_report(
    historical, store, monkeypatch
):
    from ui.views import historical_retirement_view as view, recovery_review_view as review

    r = historical
    other = clone_capture(r)
    service, incidents = setup(r, store, [r.source, other])

    async def call(method, *args):
        return getattr(service, method)(*args)

    for module in (view, review):
        monkeypatch.setattr(module, "call", call)
        monkeypatch.setattr(module, "actor_for", lambda _: ACTOR)
        monkeypatch.setattr(module, "safe_defer", AsyncMock(return_value=True))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    await view.show_batches(interaction)
    payload = interaction.followup.send.call_args.kwargs
    assert payload["ephemeral"] and len(payload["embed"].fields) == 4
    selection = next(c for c in payload["view"].children if hasattr(c, "options"))
    assert len(selection.options) == 2 and not any(o.default for o in selection.options)
    assert all("2026-10-15" in o.label for o in selection.options)
    await payload["view"].technical.callback(interaction)
    technical_view = interaction.followup.send.call_args.kwargs["view"]
    assert not any("confirmation" in getattr(item, "label", "") for item in technical_view.children)
    assert not store.pending_actions(incidents[0]["IncidentID"])
    selection._selected_values = [incidents[0]["IncidentID"]]
    selection._interaction = SimpleNamespace(data={})
    await selection.callback(interaction)
    confirm = interaction.followup.send.call_args.kwargs["view"]
    assert not store.pending_actions(incidents[0]["IncidentID"])
    await confirm.confirm.callback(interaction)
    group = interaction.followup.send.call_args.kwargs["view"].row
    assert group["evidence"]["approved_count"] == 1
    assert r.outcomes.inspect(r.source)["preparation"]["State"] == "captured"
    restarted, _ = setup(r, store, [])
    assert HistoricalRetirementGroupDAL(store).pending_repairs("stats_import") == [
        incidents[0]["IncidentID"]
    ]
    final = restarted.refresh(incidents[0]["IncidentID"])
    assert final["State"] == "resolved" and not final["pending_action"]
    assert restarted.refresh(incidents[1]["IncidentID"])["State"] == "open"
    progress = restarted.refresh(group["IncidentID"])
    assert progress["State"] == "resolved" and progress["evidence"]["verified_count"] == 1
    import io
    import zipfile

    report = restarted.download_complete_report(ACTOR)
    with zipfile.ZipFile(io.BytesIO(report["content"])) as archive:
        rows = [json.loads(line) for line in archive.read("incidents.jsonl").splitlines()]
    saved = next(x for x in rows if x["source_kind"] == "historical_batch")
    assert saved["diagnosis"]["members"][0]["id"] == incidents[0]["IncidentID"]
    assert saved["diagnosis"]["verified_count"] == 1
    repeated = service.approve_historical_group(ACTOR, confirm.group, confirm.selected)
    assert repeated["IncidentID"] == group["IncidentID"]
    assert repeated["State"] == "resolved"
    assert not store.pending_actions(incidents[0]["IncidentID"])


def test_changed_member_after_approval_does_not_block_other_retirements(historical, store):
    r = historical
    other = clone_capture(r)
    service, incidents = setup(r, store, [r.source, other])
    preview = service.review_historical_groups(ACTOR)["groups"][0]
    group = service.approve_historical_group(ACTOR, preview, [m["id"] for m in preview["members"]])
    prep = r.outcomes.inspect(other)["preparation"]
    (r.runtime.store.root / prep["SpoolKey"]).write_bytes(b"corrupt")
    assert service.refresh(incidents[1]["IncidentID"])["State"] == "open"
    assert service.refresh(incidents[0]["IncidentID"])["State"] == "resolved"
    progress = service.refresh(group["IncidentID"])
    assert progress["evidence"]["outcome"] == "completed_with_exceptions"
    assert progress["evidence"]["verified_count"] == progress["evidence"]["changed_count"] == 1


@pytest.mark.parametrize("change", ["configuration", "revision", "duplicate", "foreign", "empty"])
def test_stale_or_invalid_selection_saves_no_group_approvals(historical, store, change):
    r = historical
    other = clone_capture(r)
    service, incidents = setup(r, store, [r.source, other])
    group = service.review_historical_groups(ACTOR)["groups"][0]
    selected = [m["id"] for m in group["members"]]
    if change == "configuration":
        config = json.loads(r.runtime.configuration)
        config["scan_data"]["destinations"] = ["different_workbook"]
        r.runtime.configuration = json.dumps(config)
    elif change == "revision":
        r.owner.execute(
            r.rewrite("UPDATE dbo.ExportPreparation SET Version=Version+1 WHERE PreparationID=?"),
            other,
        )
    elif change == "duplicate":
        selected.append(selected[0])
    elif change == "foreign":
        selected.append(str(uuid4()))
    else:
        selected = []
    with pytest.raises(SourceConflict):
        service.approve_historical_group(ACTOR, group, selected)
    assert not HistoricalRetirementGroupDAL(store).pending_groups()
    assert all(not store.pending_actions(i["IncidentID"]) for i in incidents)


def test_cross_admin_and_cross_scope_group_review_refused(historical, store):
    service, incidents = setup(historical, store, [historical.source])
    group = service.review_historical_groups(ACTOR)["groups"][0]
    for actor in (RecoveryActor(9, 2, 3), RecoveryActor(1, 9, 3), RecoveryActor(1, 2, 9)):
        with pytest.raises(SourceConflict):
            service.approve_historical_group(actor, group, [incidents[0]["IncidentID"]])
    other = RecoveryDAL(store.connect, account="foreign", storage_owner="test-disk", guild_id=2)
    foreign, _ = setup(historical, other, [])
    with pytest.raises(SourceConflict):
        foreign.approve_historical_group(ACTOR, group, [incidents[0]["IncidentID"]])


def test_unchosen_changed_member_does_not_prevent_selected_decision(historical, store):
    r = historical
    other = clone_capture(r)
    service, incidents = setup(r, store, [r.source, other])
    group = service.review_historical_groups(ACTOR)["groups"][0]
    r.owner.execute(
        r.rewrite("UPDATE dbo.ExportPreparation SET Version=Version+1 WHERE PreparationID=?"), other
    )
    approved = service.approve_historical_group(ACTOR, group, [incidents[0]["IncidentID"]])
    assert approved["evidence"]["approved_count"] == 1
    assert not store.pending_actions(incidents[1]["IncidentID"])


def test_lost_group_reply_resumes_saved_approvals_without_duplicate(historical, store, monkeypatch):
    service, incidents = setup(historical, store, [historical.source])
    group = service.review_historical_groups(ACTOR)["groups"][0]
    original = HistoricalRetirementGroupDAL.approve_selected

    def lost(self, *args):
        original(self, *args)
        raise TimeoutError("lost group commit acknowledgement")

    monkeypatch.setattr(HistoricalRetirementGroupDAL, "approve_selected", lost)
    accepted = service.approve_historical_group(ACTOR, group, [incidents[0]["IncidentID"]])
    restarted, _ = setup(historical, store, [])
    assert not restarted.review_historical_groups(ACTOR)["groups"]
    pending = HistoricalRetirementGroupDAL(store).pending_groups()
    assert len(pending) == 1
    assert pending == [accepted["IncidentID"]]
    repeated = restarted.approve_historical_group(ACTOR, group, [incidents[0]["IncidentID"]])
    assert repeated["IncidentID"] == accepted["IncidentID"]
    assert restarted.refresh(incidents[0]["IncidentID"])["State"] == "resolved"
    assert restarted.refresh(pending[0])["evidence"]["verified_count"] == 1


def test_repeated_selection_matches_only_exact_actor_members_and_configuration(historical, store):
    from copy import deepcopy

    other = clone_capture(historical)
    service, incidents = setup(historical, store, [historical.source, other])
    group = service.review_historical_groups(ACTOR)["groups"][0]
    selected = [r["IncidentID"] for r in incidents]
    accepted = service.approve_historical_group(ACTOR, group, selected)
    repeated = service.approve_historical_group(ACTOR, group, list(reversed(selected)))
    assert repeated["IncidentID"] == accepted["IncidentID"]
    dal = HistoricalRetirementGroupDAL(store)
    assert dal.existing_approval(group, group["members"], "discord:9") is None
    assert dal.existing_approval(group, group["members"][:1], "discord:1") is None
    changed = deepcopy(group)
    changed["configuration"]["current"] = "a" * 64
    assert dal.existing_approval(changed, changed["members"], "discord:1") is None
    changed = deepcopy(group)
    changed["members"][0]["token"] = "b" * 64
    assert dal.existing_approval(changed, changed["members"], "discord:1") is None
    with pytest.raises(SourceConflict):
        service.approve_historical_group(RecoveryActor(9, 2, 3), group, selected)
    assert len(dal.pending_groups()) == 1


def test_duplicate_atomic_approval_returns_original_without_new_intents(historical, store):
    service, _ = setup(historical, store, [historical.source])
    group = service.review_historical_groups(ACTOR)["groups"][0]
    dal = HistoricalRetirementGroupDAL(store)
    first = dal.approve_selected(group, group["members"], "discord:1")
    assert dal.approve_selected(group, group["members"], "discord:1") == first
    assert dal.pending_groups() == [first]
    assert len(store.pending_actions(group["members"][0]["id"])) == 1


def test_batch_pagination_and_maximum_group_fit_existing_sql_contract(historical, store):
    r = historical
    sources = [r.source] + [clone_capture(r) for _ in range(25)]
    service, incidents = setup(r, store, sources)
    first = service.review_historical_groups(ACTOR)
    group = first["groups"][0]
    assert len(group["members"]) == 25 and first["next_after"]
    approval = service.approve_historical_group(ACTOR, group, [m["id"] for m in group["members"]])
    assert approval["evidence"]["approved_count"] == 25
    second = service.review_historical_groups(ACTOR, first["next_after"])
    assert len(second["groups"][0]["members"]) == 1 and second["next_after"] is None
    assert {m["id"] for m in group["members"]}.isdisjoint(
        {m["id"] for m in second["groups"][0]["members"]}
    )


def test_last_moment_incident_revision_change_rolls_back_entire_group(historical, store):
    r = historical
    other = clone_capture(r)
    service, incidents = setup(r, store, [r.source, other])
    group = service.review_historical_groups(ACTOR)["groups"][0]
    row = incidents[1]
    store.observe(
        "stats_import", row["SourceID"], dict(row["evidence"], changed=True), row["EvidenceHash"]
    )
    with pytest.raises(SourceConflict):
        HistoricalRetirementGroupDAL(store).approve_selected(group, group["members"], "discord:1")
    assert all(not store.pending_actions(row["IncidentID"]) for row in incidents)
    assert not HistoricalRetirementGroupDAL(store).pending_groups()


def test_different_original_configurations_are_separate_review_groups(historical, store):
    r = historical
    other = clone_capture(r, destination="different_workbook")
    service, _ = setup(r, store, [r.source, other])
    groups = service.review_historical_groups(ACTOR)["groups"]
    assert len(groups) == 2 and all(len(g["members"]) == 1 for g in groups)
    assert len({g["configuration"]["original"] for g in groups}) == 2
    assert len({g["configuration"]["current"] for g in groups}) == 1
