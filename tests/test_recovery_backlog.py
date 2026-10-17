import io
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
import zipfile

import pytest

from services.recovery_service import RecoveryActor, SourceConflict
from tests.test_guided_recovery import ACTOR
from tests.test_recovery_report import report_service


def test_complete_report_includes_17431_incidents_in_one_bounded_download():
    service, store, records = report_service(17431)
    report = service.download_complete_report(ACTOR)
    assert len(report["content"]) < 8388608
    with zipfile.ZipFile(io.BytesIO(report["content"])) as archive:
        summary = json.loads(archive.read("summary.json"))
        details = [json.loads(line) for line in archive.read("incidents.jsonl").splitlines()]
    assert summary["complete"] and summary["included_incidents"] == 17431
    assert sum(g["count"] for g in summary["groups"]) == 17431
    assert [r["incident_id"] for r in details] == [r["IncidentID"] for r in records]
    assert "NEVER_EXPORT_ME" not in str(details) and "DO_NOT_EXPORT" not in str(details)
    assert not store.actions
    service.refresh.assert_not_called()


@pytest.mark.parametrize(
    "method",
    [
        "review_evidence_group",
        "approve_evidence_group",
        "download_complete_report",
        "backlog_summary",
    ],
)
@pytest.mark.parametrize(
    "actor", [RecoveryActor(9, 2, 3), RecoveryActor(1, 9, 3), RecoveryActor(1, 2, 9)]
)
def test_new_workflows_authorize_before_any_store_access(method, actor):
    service, store, _ = report_service()
    with pytest.raises(SourceConflict, match="configured admin"):
        getattr(service, method)(actor, *([{}] if method == "approve_evidence_group" else []))
    store.report_page.assert_not_called()


def test_incomplete_collection_never_labels_archive_complete():
    service, store, _ = report_service(3)
    original = store.report_page.side_effect
    store.report_page.side_effect = lambda **kw: dict(original(**kw), total=4)
    with pytest.raises(SourceConflict, match="coverage changed"):
        service.download_complete_report(ACTOR)


def test_archive_enforces_compressed_attachment_bound():
    from services.recovery_complete_report import BoundedArchive

    target = BoundedArchive(10)
    target.write(b"1234567890")
    with pytest.raises(SourceConflict, match="attachment limit"):
        target.write(b"x")


@pytest.mark.asyncio
async def test_group_confirmation_is_deferred_and_requires_configured_actor(monkeypatch):
    from ui.views import recovery_backlog_view as module

    preview = dict(count=1000, through="cutoff", token="a" * 64)
    monkeypatch.setattr(module, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(module, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(module, "call", AsyncMock(return_value=preview))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    await module.show_group(interaction)
    sent = interaction.followup.send.call_args.kwargs
    assert sent["ephemeral"] and "1000" in sent["embed"].title
    assert sent["view"].preview == preview
    assert "restart" in str(sent["embed"].to_dict())
    module.call.assert_awaited_once_with("review_evidence_group", ACTOR)
