"""Configuration intent is explicit before admission and never inferred on recovery."""

import asyncio
import json
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.configuration_producer_recovery import ConfigurationProducerDAL
from services.legacy_export_snapshot_service import collect_producer_captures
from services.producer_recovery_intent import (
    configuration_import_intent,
    configuration_retry_intent,
    current_intent,
)
from tests.test_player_report_recovery import fixture


@configuration_import_intent
def config_work():
    return dict(current_intent())


def test_standalone_configuration_intent_precedes_admission(tmp_path, monkeypatch):
    from services.legacy_export_snapshot_service import SnapshotUnavailable
    from tests.test_legacy_export_snapshot import producer_runtime

    runtime, dal = producer_runtime(
        tmp_path,
        configuration={"scan_data": {"consumer": "scan_data", "destinations": ["target"]}},
    )
    monkeypatch.setattr(runtime, "_claim_unstarted", lambda *_args, **_kwargs: None)

    @configuration_import_intent
    def attempt():
        runtime.begin_writer("scan_data")

    with pytest.raises(SnapshotUnavailable, match="admission refused"):
        attempt()
    saved = dal.request.call_args.kwargs["request"]
    assert saved["producer"]["export_disposition"] == "configuration_only_v1"
    assert saved["producer"]["operation"] == saved["operation"]
    assert current_intent() is None
    dal.connect.assert_not_called()


@pytest.mark.asyncio
async def test_pipeline_and_standalone_configuration_keep_distinct_intents():
    @collect_producer_captures
    async def pipeline():
        return await asyncio.to_thread(config_work)

    assert (await pipeline())["export_disposition"] == "pipeline_export_v1"
    first = config_work()
    assert first["export_disposition"] == "configuration_only_v1"
    assert config_work()["operation"] != first["operation"]
    assert current_intent() is None


def test_existing_guided_retry_is_not_reinterpreted_as_no_export():
    with configuration_retry_intent(str(uuid4()), str(uuid4())) as intent:
        assert config_work() == intent
        assert "export_disposition" not in intent


def test_approved_configuration_only_retry_preserves_intent_before_admission():
    from services.configuration_continuation_dal import ConfigurationContinuationDAL

    action, parent = str(uuid4()), str(uuid4())
    marker = dict(
        action=action,
        choice="retry",
        configuration={"scan_data": {}},
        export_disposition="configuration_only_v1",
    )
    with configuration_retry_intent(
        action, parent, export_disposition=marker["export_disposition"]
    ) as intent:
        assert config_work() == intent
        assert ConfigurationContinuationDAL.child_request(parent, marker)["producer"] == intent
    assert current_intent() is None
    # Restarting an older marker preserves its exact request hash and unknown intent.
    del marker["export_disposition"]
    assert (
        "export_disposition"
        not in ConfigurationContinuationDAL.child_request(parent, marker)["producer"]
    )


@pytest.mark.asyncio
async def test_configuration_only_retry_cannot_be_collected_as_pipeline_export():
    @collect_producer_captures
    async def pipeline():
        return await asyncio.to_thread(config_work)

    with configuration_retry_intent(
        str(uuid4()), str(uuid4()), export_disposition="configuration_only_v1"
    ):
        with pytest.raises(SourceConflict, match="original export intent"):
            await pipeline()
    assert current_intent() is None


@pytest.mark.parametrize("value", [None, True, {}, "cache_only_v1"])
def test_saved_continuation_rejects_invalid_explicit_export_disposition(value):
    from services.configuration_continuation_dal import ConfigurationContinuationDAL

    with pytest.raises(SourceConflict, match="export intent"):
        ConfigurationContinuationDAL.child_request(
            str(uuid4()),
            dict(action=str(uuid4()), choice="retry", export_disposition=value),
        )


@pytest.mark.parametrize(
    "disposition",
    [None, "configuration_only_v1", "pipeline_export_v1", "cache_only_v1", True, {}, []],
)
def test_config_request_rejects_foreign_or_malformed_disposition(disposition):
    _, preview, _ = fixture()
    prep = preview["preparation"]
    request = json.loads(prep["RequestJson"])
    producer = request["request"]["producer"]
    producer["kind"] = "configuration_import"
    if disposition is not None:
        producer["export_disposition"] = disposition
    prep.update(RequestJson=json.dumps(request), RequestHash=digest(request))
    if disposition in (None, "configuration_only_v1", "pipeline_export_v1"):
        assert ConfigurationProducerDAL.request(prep) == request
    else:
        with pytest.raises(SourceConflict):
            ConfigurationProducerDAL.request(prep)
