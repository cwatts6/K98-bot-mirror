"""New cache-only intentions never reinterpret historical or pipeline work."""

import json

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.legacy_export_snapshot_service import collect_producer_captures
from services.player_report_recovery_dal import PlayerReportRecoveryDAL
from services.producer_recovery_intent import current_intent, player_cache_intent
from tests.test_player_report_recovery import fixture


@player_cache_intent
def cache_work():
    return dict(current_intent())


def test_cache_invocation_records_no_export_before_execution_and_resets():
    value = cache_work()
    assert value["export_disposition"] == "cache_only_v1"
    assert value["kind"] == "player_stats_report"
    assert current_intent() is None
    assert cache_work()["operation"] != value["operation"]


def test_cache_intent_is_persisted_even_when_admission_is_refused(tmp_path, monkeypatch):
    from services.legacy_export_snapshot_service import SnapshotUnavailable
    from tests.test_legacy_export_snapshot import producer_runtime

    runtime, dal = producer_runtime(
        tmp_path, configuration={"scan_data": {"consumer": "scan_data", "destinations": ["target"]}}
    )
    monkeypatch.setattr(runtime, "_claim_unstarted", lambda *_args, **_kwargs: None)

    @player_cache_intent
    def attempt():
        runtime.begin_writer("scan_data")

    with pytest.raises(SnapshotUnavailable, match="admission refused"):
        attempt()
    saved = dal.request.call_args.kwargs["request"]
    assert saved["producer"]["export_disposition"] == "cache_only_v1"
    assert saved["producer"]["operation"] == saved["operation"]
    dal.connect.assert_not_called()


@pytest.mark.asyncio
async def test_pipeline_capture_intent_is_preserved_across_thread_offload():
    import asyncio

    @collect_producer_captures
    async def pipeline():
        return await asyncio.to_thread(cache_work)

    assert (await pipeline())["export_disposition"] == "pipeline_export_v1"
    assert cache_work()["export_disposition"] == "cache_only_v1"


@pytest.mark.parametrize(
    "disposition", [None, "cache_only_v1", "pipeline_export_v1", "invented", True, {}, []]
)
def test_request_validation_preserves_legacy_and_rejects_unknown_intent(disposition):
    _, preview, _ = fixture()
    prep = preview["preparation"]
    request = json.loads(prep["RequestJson"])
    if disposition is not None:
        request["request"]["producer"]["export_disposition"] = disposition
    prep.update(RequestJson=json.dumps(request), RequestHash=digest(request))
    if disposition in (None, "cache_only_v1", "pipeline_export_v1"):
        assert PlayerReportRecoveryDAL.request(prep) == request
    else:
        with pytest.raises(SourceConflict):
            PlayerReportRecoveryDAL.request(prep)
