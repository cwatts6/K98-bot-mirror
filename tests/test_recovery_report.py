"""Report completeness, read-only behavior and configured-admin delivery."""

from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from services.recovery_service import RecoveryActor, SourceConflict
from tests.test_guided_recovery import ACTOR, setup
from tests.test_recovery_release_policy import pilot


def report_service(count=1):
    original, dal, store, row = setup("partial")
    service = pilot(original)
    records = []
    for index in range(count):
        item = deepcopy(row)
        item["IncidentID"] = str(uuid4())
        item["State"] = "resolved" if index % 2 else "open"
        item["pending_action"] = None
        item["evidence"]["private_request"] = "NEVER_EXPORT_ME"
        item["evidence"]["explanation"] = "Needs verification; password=DO_NOT_EXPORT"
        records.append(item)

    def page(*, after=None, through=None):
        start = (
            0
            if after is None
            else next(i + 1 for i, r in enumerate(records) if r["IncidentID"] == after)
        )
        return dict(
            rows=deepcopy(records[start : start + 100]),
            total=count,
            through=through or "2026-10-17 10:00:00",
            more=start + 100 < count,
        )

    store.report_page = Mock(side_effect=page)
    store.pending_actions = Mock(side_effect=AssertionError("Report must use paged action state"))
    service.refresh = Mock(side_effect=AssertionError("Report must not refresh or reconcile"))
    return service, store, records


def test_report_includes_all_states_across_pages_and_preserves_withheld_repairs():
    service, store, records = report_service(105)
    first = service.download_report(ACTOR)
    data = json.loads(first["content"])
    assert data["included_incidents"] == 100 and data["more_parts"]
    assert not data["complete"]
    assert {r["state"] for r in data["incidents"]} == {"open", "resolved"}
    repair = data["incidents"][0]["required_repairs"][0]
    assert repair["action"] == "supersede_partial"
    assert repair["availability"] == "not_enabled_in_release"
    second = service.download_report(ACTOR, first["next_after"], first["through"], 2)
    remaining = json.loads(second["content"])
    assert remaining["included_incidents"] == 5
    assert not remaining["more_parts"] and remaining["parts_complete_through_this_part"]
    assert [r["incident_id"] for r in data["incidents"] + remaining["incidents"]] == [
        r["IncidentID"] for r in records
    ]
    service.refresh.assert_not_called()
    assert store.actions == []
    assert b"NEVER_EXPORT_ME" not in first["content"]
    assert b"DO_NOT_EXPORT" not in first["content"]


@pytest.mark.parametrize(
    "actor", [RecoveryActor(9, 2, 3), RecoveryActor(1, 9, 3), RecoveryActor(1, 2, 9)]
)
def test_report_authorizes_before_reading_incidents(actor):
    service, store, _ = report_service()
    with pytest.raises(SourceConflict, match="configured admin"):
        service.download_report(actor)
    store.report_page.assert_not_called()


def test_empty_and_small_reports_are_complete():
    for count in (0, 1):
        service, _, _ = report_service(count)
        data = json.loads(service.download_report(ACTOR)["content"])
        assert data["complete"]
        assert data["total_recorded_incidents"] == count


def test_collection_failure_is_exportable_without_false_empty_or_secrets():
    from services.recovery_report import unavailable_report

    result = unavailable_report(RuntimeError("private credentials"))
    data = json.loads(result["content"])
    assert data["complete"] is False and data["incidents_available"] is False
    assert "incidents" not in data
    assert b"private credentials" not in result["content"]


@pytest.mark.parametrize(
    "kind,outcome,state,pending,unavailable,expected",
    [
        ("evidence_batch", "running", "open", None, None, "approved evidence group is running"),
        (
            "private_evidence",
            "recoverable",
            "open",
            {"kind": "protect_evidence", "state": "unknown"},
            None,
            "awaiting verification",
        ),
        ("export_job", "failed", "open", None, "TimeoutError", "Verification is unavailable"),
        ("evidence_batch", "verified", "resolved", None, None, "Resolved; no repair required"),
        (
            "evidence_batch",
            "completed_with_exceptions",
            "resolved",
            None,
            None,
            "finished with exceptions",
        ),
        ("stats_import", "partial", "open", None, None, "not enabled in this release"),
    ],
)
def test_report_next_step_distinguishes_active_work_from_unavailable_repairs(
    kind, outcome, state, pending, unavailable, expected
):
    from services.recovery_report import incident_report

    service, _, records = report_service()
    row = records[0]
    row.update(SourceKind=kind, State=state, pending_action=pending)
    row["evidence"].update(outcome=outcome)
    if kind != "stats_import":
        row["evidence"]["actions"] = {}
    if unavailable:
        row["evidence"]["check_unavailable"] = unavailable
    assert expected in incident_report(service, row)["next_step"]


@pytest.mark.parametrize("text", ["x", "é\n"])
def test_size_split_resumes_at_last_included_incident_without_omissions(text):
    service, _, records = report_service(10)
    for row in records:
        row["evidence"]["explanation"] = text * 12000
    identifiers, after, through, part = [], None, None, 1
    while True:
        report = service.download_report(ACTOR, after, through, part, 65536)
        assert len(report["content"]) <= 65536
        identifiers.extend(r["incident_id"] for r in json.loads(report["content"])["incidents"])
        after, through, part = report["next_after"], report["through"], part + 1
        if after is None:
            break
    assert identifiers == [r["IncidentID"] for r in records]


def test_report_serialization_is_linear_and_uses_paged_pending_action(monkeypatch):
    from services import recovery_report as module

    service, store, records = report_service(100)
    for row in records:
        row["evidence"]["explanation"] = "é" * 10000
    records[0]["pending_action"] = dict(state="unknown", kind="release_failure")
    calls, serialized_bytes = [], []
    original_encode = module.encode

    def measured(document):
        calls.append(len(document["incidents"]) if "incidents" in document else None)
        content = original_encode(document)
        serialized_bytes.append(len(content))
        return content

    monkeypatch.setattr(module, "encode", measured)
    report = service.download_report(ACTOR)
    data = json.loads(report["content"])
    assert data["incidents"][0]["pending_verification"] == records[0]["pending_action"]
    assert [count for count in calls if count is not None] == [0, 100]
    assert sum(serialized_bytes) < 3 * len(report["content"])
    store.pending_actions.assert_not_called()


@pytest.mark.asyncio
async def test_report_button_uses_ephemeral_file_and_auth_before_query(monkeypatch):
    from ui.views import recovery_view as module

    service, _, _ = report_service()
    result = service.download_report(ACTOR)
    call = AsyncMock(return_value=result)
    monkeypatch.setattr(module, "call", call)
    monkeypatch.setattr(module, "actor_for", Mock(return_value=ACTOR))
    monkeypatch.setattr(module, "safe_defer", AsyncMock(return_value=True))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    await module.show_report(interaction)
    sent = interaction.followup.send.call_args.kwargs
    assert sent["ephemeral"] is True
    assert json.loads(sent["file"].fp.getvalue())["complete"]
    assert module.RecoveryEntryView().is_persistent()
    call.reset_mock()
    monkeypatch.setattr(module, "actor_for", Mock(side_effect=SourceConflict("denied")))
    monkeypatch.setattr(module, "report_error", AsyncMock())
    await module.show_report(interaction)
    call.assert_not_called()


def test_missing_receipt_links_to_typed_admission_without_authorizing_release():
    from services.import_recovery_service import ImportRecoveryAdapter

    source, parent = str(uuid4()), str(uuid4())
    dal = SimpleNamespace(
        inspect=lambda _: dict(
            action="hold",
            token="a" * 64,
            execution=None,
            resources=[],
            preparation=dict(
                State="writing",
                Version=4,
                RequestJson=json.dumps(
                    {"request": {"producer": {"kind": "stats_import", "parent": parent}}}
                ),
            ),
        )
    )
    evidence, _, resolved = ImportRecoveryAdapter(dal).inspect(source)
    assert not resolved and not evidence["actions"]
    assert evidence["recovery_links"][0]["source_id"] == parent
    assert evidence["recovery_links"][0]["kind"] == "producer_refusal"
    assert evidence["receipt_diagnostics"]["receipt_present"] is False


@pytest.mark.asyncio
async def test_report_view_releases_attachment_and_preserves_continuation(monkeypatch):
    import weakref

    from ui.views import recovery_view as module

    class Attachment:
        pass

    content = Attachment()
    retained = weakref.ref(content)
    report = dict(content=content, next_after="last-incident", through="cutoff", part=4)
    view = module.RecoveryReportView(report)
    del report, content
    assert retained() is None
    show = AsyncMock()
    monkeypatch.setattr(module, "show_report", show)
    interaction = object()
    await view.children[0].callback(interaction)
    show.assert_awaited_once_with(interaction, "last-incident", "cutoff", 5)
