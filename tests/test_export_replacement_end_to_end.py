"""Retained legacy publication through SQL, typed authority and final verification.

Only the child provider is simulated. SQL objects are session-local, Google SDK
requests use bundled discovery, and no HTTP request is allowed to execute.
"""

from copy import deepcopy
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from services.export_execution_authority import ExecutionUncertain
from services.export_execution_protocol import ProviderRequest, encode
from services.export_provider_adapter import LegacyProviderJob
from services.export_replacement_authority import ReplacementAuthority
from services.export_runtime_composition import (
    AuthorityStream,
    LegacyExecutionStreams,
    RuntimeRegistration,
)
from tests import test_export_target_containment_sql as fixture_module
from tests.test_export_enrollment_service import FakeChild
from tests.test_export_replacement_activation_sql import activation as activation
from tests.test_export_replacement_delivery_sql import (
    delivery as delivery,
    pytestmark as pytestmark,
    recovery as recovery,
)
from tests.test_export_replacement_verification_sql import (
    contained_job as contained_job,
    proposal_service as proposal_service,
    verification as verification,
)


@pytest.fixture
def publication(monkeypatch, request):
    monkeypatch.setattr(fixture_module, "TABLES", (*fixture_module.TABLES, "dbo.ExportAttemptPart"))
    r = request.getfixturevalue("delivery")
    r.delivery.execute(r.f.job, r.activated, "publish_replacement", **r.queue_args)
    return prepare_publication(r)


def prepare_publication(r):
    """Wire the real delivery and verifier around a deterministic provider child."""
    r.coordinator = r.delivery.dal.coordinator
    r.claim = r.coordinator.claim_next("test-account", storage_owner="disk")
    assert r.claim is not None
    r.running = r.coordinator.authorize(r.claim)
    r.provider = SimpleNamespace(failure=None, sent=[], rows={}, grids={}, children=[])

    class Child(FakeChild):
        def execute(self, message):
            typed = ProviderRequest.parse(message)
            assert typed.target in r.activated["mapping"].values(), (
                "Old unknown-write output must never be touched"
            )
            r.provider.sent.append(typed)
            if r.provider.failure == typed.operation:
                raise TimeoutError("Injected lost publication response")
            arguments = typed.arguments
            if typed.operation == "drive.permissions.list":
                return dict(permissions=[dict(type="user", role="owner")])
            if typed.operation == "sheets.get":
                return dict(
                    spreadsheetId=typed.target,
                    sheets=[dict(properties=p) for p in r.provider.grids.values()],
                )
            if typed.operation == "sheets.batchUpdate":
                for instruction in arguments["body"]["requests"]:
                    if "addSheet" in instruction:
                        properties = deepcopy(instruction["addSheet"]["properties"])
                        r.provider.grids[properties["sheetId"]] = properties
                return dict(
                    spreadsheetId=typed.target, replies=[{} for _ in arguments["body"]["requests"]]
                )
            if typed.operation == "sheets.values.clear":
                r.provider.rows.clear()
                return dict(spreadsheetId=typed.target, clearedRange=arguments["range"])
            if typed.operation == "sheets.values.update":
                r.provider.rows["values"] = deepcopy(arguments["body"]["values"])
                values = r.provider.rows["values"]
                return dict(
                    spreadsheetId=typed.target,
                    updatedRange=arguments["range"],
                    updatedRows=len(values),
                    updatedColumns=len(values[0]),
                    updatedCells=sum(map(len, values)),
                )
            if typed.operation == "sheets.values.get":
                return dict(deepcopy(r.provider.rows), range=arguments["range"])
            raise AssertionError(typed.operation)

    def create(identifier):
        child = Child(identifier, r.provider)
        r.provider.children.append(child)
        return child

    authority = r.service.authority
    authority.host = SimpleNamespace(create_suspended=create)
    registration = RuntimeRegistration(r.activated["registration"])

    def open_stream(identifier, scope):
        registration.authorize_scope(scope)
        authority.open_stream(
            stream_id=identifier,
            scope=dict(
                scope,
                ScopeJson=encode(scope["ScopeJson"]).decode(),
                RegistrationHash=bytes.fromhex(scope["RegistrationHash"]),
                SnapshotHash=bytes.fromhex(scope["SnapshotHash"]),
            ),
        )

    client = SimpleNamespace(
        open_stream=open_stream, close_stream=authority.close_stream, execute=authority.execute
    )
    client.stream = lambda scope: AuthorityStream(client, scope)
    streams = LegacyExecutionStreams(
        coordinator=r.coordinator,
        preparations=SimpleNamespace(execution_evidence=True, output_operations=True),
        client=client,
        account="test-account",
        storage_owner="disk",
        configuration=registration.value()["legacy_configuration"],
    )
    from googleapiclient.discovery import build

    http = SimpleNamespace(request=Mock(side_effect=AssertionError("Live HTTP is forbidden")))
    sheets = build("sheets", "v4", http=http, static_discovery=True)
    drive = build("drive", "v3", http=http, static_discovery=True)
    r.worker = LegacyProviderJob(lambda _: (sheets, drive), authority_stream=streams.delivery)
    final = ReplacementAuthority.__new__(ReplacementAuthority)
    final.connect, final.authority = r.f.connect, authority
    r.delivery.verify_delivery = final.verify_delivery
    r.publish = lambda: r.worker(
        r.running, r.claim, r.coordinator, Mock(), Event(), r.spools[r.running["SpoolKey"]]
    )
    r.http = http
    return r


def test_retained_export_closes_only_after_real_delivery_and_original_journal(publication):
    r = publication
    assert not r.delivery.inspect(r.f.job, r.activated)["resolved"]
    r.publish()
    result = r.delivery.inspect(r.f.job, r.activated)
    assert result["resolved"] and result["stage"] == "replacement_delivered"
    assert r.provider.rows == dict(values=[["ID", "Value"], [1, "retained"]])
    assert all(c.terminated for c in r.provider.children)
    assert (
        r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", r.f.job).fetchval()
        == "uncertain"
    )
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementDelivery").fetchval() == 1
    r.http.request.assert_not_called()


def test_lost_provider_write_stays_open_with_link_to_replacement_recovery(publication):
    r = publication
    r.provider.failure = "sheets.values.update"
    with pytest.raises(ExecutionUncertain, match="closure"):
        r.publish()
    r.coordinator.fail(r.claim, retain_claims=True)
    result = r.delivery.inspect(r.f.job, r.activated)
    assert not result["resolved"] and result["stage"] == "replacement_needs_attention"
    assert result["job_id"] == r.claim.job_id
    assert sum(q.operation == "sheets.values.update" for q in r.provider.sent) == 1
    r.http.request.assert_not_called()
