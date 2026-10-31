"""Legacy-only audience receipts preserve the separately strict S11 pool policy."""

import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import checked_attempt_manifest, legacy_attempt_audiences
from services.export_provider_adapter import (
    LegacyProviderJob,
    ProviderOutcomeUnknown,
    recorded_clients,
)
from services.legacy_export_snapshot_service import (
    LegacySnapshot,
    OutputSection,
    SnapshotUnavailable,
    configuration_digest,
    output_digest,
)


def policy(audience):
    return dict(
        audience=audience,
        editors=["sheets-service@example.com"],
        coordination_scope="application_writers_only",
    )


@pytest.mark.parametrize(
    "audience,permissions,expected",
    [
        ("anyone_writer", [{"type": "anyone", "role": "writer"}], "public_editor"),
        ("anyone_reader", [{"type": "anyone", "role": "reader"}], "public_viewer"),
        ("private", [{"type": "user", "role": "owner"}], "private"),
    ],
)
def test_exact_registered_legacy_audience(audience, permissions, expected):
    adapter = LegacyProviderJob(Mock(), legacy_file_access={"file-a": policy(audience)})
    assert adapter._audience("file-a", dict(permissions=permissions)) == expected


@pytest.mark.parametrize(
    "response",
    [
        dict(permissions=[{"type": "anyone", "role": "reader"}]),
        dict(permissions=[]),
        dict(permissions=[{"type": "domain", "role": "writer"}]),
        dict(permissions=[{"type": "anyone", "role": "writer"}], nextPageToken="more"),
    ],
)
def test_changed_or_incomplete_legacy_policy_is_refused(response):
    adapter = LegacyProviderJob(Mock(), legacy_file_access={"file-a": policy("anyone_writer")})
    with pytest.raises(SnapshotUnavailable):
        adapter._audience("file-a", response)


def test_unregistered_file_does_not_inherit_another_files_public_writer_exception():
    adapter = LegacyProviderJob(Mock(), legacy_file_access={"file-a": policy("anyone_writer")})
    with pytest.raises(SnapshotUnavailable):
        adapter._audience("other-file", dict(permissions=[{"type": "anyone", "role": "writer"}]))


def test_legacy_policy_is_copied_not_mutable_after_registration():
    source = {"file-a": policy("anyone_writer")}
    adapter = LegacyProviderJob(Mock(), legacy_file_access=source)
    source["file-a"]["audience"] = "private"
    assert (
        adapter._audience("file-a", dict(permissions=[{"type": "anyone", "role": "writer"}]))
        == "public_editor"
    )


def delivery(*, changed=False):
    import hashlib
    from threading import Event

    sections = (OutputSection("data", ("GovernorID",), ((123,),)),)
    files = ["private-file", "reader-file", "writer-file"]
    config = dict(
        destinations=files,
        outputs=[
            dict(section="data", file_id=f, tab="Data", grid_id=7, format_requests=[])
            for f in files
        ],
    )
    snapshot = LegacySnapshot.capture(
        consumer="scan_data",
        preparation_id=str(uuid4()),
        config=config,
        generation=dict(
            completion="committed",
            commit_identity="fixture",
            output_sha256=output_digest(sections),
            config_sha256=configuration_digest(config),
        ),
        provenance={},
        sections=sections,
    )
    scope = dict(legacy_file_access={"writer-file": policy("anyone_writer")})
    requests = []
    acl_reads = {}

    def execute(message):
        requests.append(message)
        f = message["target"]
        operation = message["operation"]
        if operation == "drive.permissions.list":
            acl_reads[f] = acl_reads.get(f, 0) + 1
            role = None if f == "private-file" else "reader" if f == "reader-file" else "writer"
            if changed and f == "writer-file" and acl_reads[f] > 1:
                role = "reader"
            return dict(permissions=[] if role is None else [dict(type="anyone", role=role)])
        if operation == "sheets.get":
            return dict(
                spreadsheetId=f,
                sheets=[
                    dict(
                        properties=dict(
                            sheetId=7, title="Data", gridProperties=dict(rowCount=2, columnCount=1)
                        )
                    )
                ],
            )
        if operation == "sheets.values.get":
            return dict(range=message["arguments"]["range"], values=[["GovernorID"], [123]])
        if operation == "sheets.batchUpdate":
            return dict(
                spreadsheetId=f, replies=[{} for _ in message["arguments"]["body"]["requests"]]
            )
        if operation == "sheets.values.clear":
            return dict(spreadsheetId=f, clearedRange=message["arguments"]["range"])
        if operation == "sheets.values.update":
            return dict(
                spreadsheetId=f,
                updatedRange=message["arguments"]["range"],
                updatedRows=2,
                updatedColumns=1,
                updatedCells=2,
            )
        raise AssertionError("Unexpected provider operation")

    stream = SimpleNamespace(stream_id=str(uuid4()), execute=execute)
    owner = Mock()
    owner.__enter__ = Mock(return_value=stream)
    owner.__exit__ = Mock(return_value=False)
    adapter = LegacyProviderJob(
        lambda _: recorded_clients(), authority_stream=Mock(return_value=owner), **scope
    )
    dal = Mock()
    dal.execution_evidence = True
    dal.begin_attempt.return_value = str(uuid4())
    job = dict(ConsumerKind="scan_data", InputHash=hashlib.sha256(snapshot.payload).digest())
    args = (
        job,
        SimpleNamespace(fence=9, job_id=str(uuid4())),
        dal,
        Mock(),
        Event(),
        snapshot.payload,
    )
    return adapter, args, requests


def test_recorded_mixed_legacy_delivery_pins_and_confirms_each_audience():
    adapter, args, requests = delivery()
    adapter(*args)
    dal = args[2]
    expected = {
        "private-file": "private",
        "reader-file": "public_viewer",
        "writer-file": "public_editor",
    }
    manifest = dal.begin_attempt.call_args.args[1]
    assert manifest["staging_audience"] == "legacy_registered"
    assert manifest["legacy_audiences"] == expected
    assert dal.verified.call_args.kwargs == {"audience": "legacy_registered"}
    receipt = dal.confirm.call_args.args[2]
    assert receipt["audience"] == "legacy_registered" and receipt["file_audiences"] == expected
    assert len([r for r in requests if r["operation"] == "drive.permissions.list"]) == 6
    assert all(
        r["operation"] not in {"drive.permissions.create", "drive.permissions.delete"}
        for r in requests
    )


def test_acl_change_after_writes_retains_uncertainty_without_confirmation():
    adapter, args, _ = delivery(changed=True)
    with pytest.raises(ProviderOutcomeUnknown):
        adapter(*args)
    args[2].begin_attempt.assert_called_once()
    args[2].confirm.assert_not_called()
    args[2].verified.assert_not_called()


@pytest.mark.parametrize("consumer", ["new_source", "config", None])
def test_s11_pool_or_config_cannot_use_legacy_audiences(consumer):
    document = dict(
        generation=dict(
            staging_audience="legacy_registered", legacy_audiences={"file-a": "public_editor"}
        )
    )
    with pytest.raises(SourceConflict):
        legacy_attempt_audiences(document, ["file-a"], consumer)


def test_audience_map_must_cover_exact_attempted_files():
    document = dict(
        generation=dict(
            staging_audience="legacy_registered", legacy_audiences={"file-a": "private"}
        )
    )
    with pytest.raises(SourceConflict):
        legacy_attempt_audiences(document, ["file-a", "file-b"], "scan_data")


def test_legacy_policy_cannot_label_s11_index_parts():
    part = dict(
        FileID="file-a",
        Role="index",
        ManifestHash="a" * 64,
        GridCount=1,
        RowCount=1,
        CellCount=1,
        PartNo=1,
    )
    document = dict(
        generation=dict(
            staging_audience="legacy_registered", legacy_audiences={"file-a": "private"}
        ),
        parts=[
            dict(file_id="file-a", role="index", manifest_hash="a" * 64, grids=1, rows=1, cells=1)
        ],
    )
    attempt = dict(
        ConsumerKind="scan_data",
        ManifestJson=json.dumps(document),
        ManifestHash=digest(document),
        PartCount=1,
    )
    with pytest.raises(SourceConflict, match="index or generation"):
        checked_attempt_manifest(attempt, [part])
