from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from services.export_provider_adapter import ProviderAdapter, ProviderOutcomeUnknown


def authority_adapter(execution):
    from uuid import uuid4

    budget, authorize = Mock(), Mock()
    adapter = ProviderAdapter(
        budget=budget,
        authorize=authorize,
        destinations=["file-a"],
        execution=execution,
        stream_id=str(uuid4()),
    )
    return adapter, budget, authorize


def test_authority_bridge_never_executes_local_sdk_or_double_reserves():
    execute = Mock(return_value={"spreadsheetId": "file-a", "sheets": []})
    adapter, budget, authorize = authority_adapter(execute)
    request = SimpleNamespace(
        method="GET",
        uri="https://sheets.googleapis.com/v4/spreadsheets/file-a?fields=sheets.properties",
        body=None,
        execute=Mock(side_effect=AssertionError("Local SDK escaped")),
    )
    assert adapter.execute(request)["spreadsheetId"] == "file-a"
    execute.assert_called_once()
    assert execute.call_args.args[0]["operation"] == "sheets.get"
    authorize.assert_called_once_with(mutation=False)
    budget.assert_not_called()
    request.execute.assert_not_called()
    with pytest.raises(ValueError, match="Unrecorded"):
        adapter.call(Mock(), mutation=False, destination="file-a")


def test_authority_bridge_lost_response_is_not_replayed_with_new_identity():
    execute = Mock(side_effect=TimeoutError("IPC reply lost"))
    adapter, budget, authorize = authority_adapter(execute)
    request = SimpleNamespace(
        method="POST",
        uri="https://sheets.googleapis.com/v4/spreadsheets/file-a/values/A1:clear",
        body="{}",
        execute=Mock(),
    )
    for _ in range(2):
        with pytest.raises(ProviderOutcomeUnknown):
            adapter.execute(request)
    execute.assert_called_once()
    request.execute.assert_not_called()


def test_authority_gspread_bridge_returns_response_without_local_http():
    execute = Mock(return_value={"spreadsheetId": "file-a", "sheets": []})
    adapter, budget, authorize = authority_adapter(execute)
    original = Mock(side_effect=AssertionError("Local HTTP escaped"))
    http = SimpleNamespace(request=original)
    adapter.bind_gspread(http)
    response = http.request(
        "get",
        "https://sheets.googleapis.com/v4/spreadsheets/file-a",
        params={"includeGridData": "false"},
    )
    assert response.json()["spreadsheetId"] == "file-a"
    assert execute.call_args.args[0]["arguments"] == {"includeGridData": False}
    original.assert_not_called()
    with pytest.raises(ValueError, match="Unsupported"):
        http.request("get", "https://sheets.googleapis.com/v4/spreadsheets/file-a", headers={})
    assert execute.call_count == 1


def delivery_fixture(*, wrong_grid=False, wrong_readback=False, decimal_cells=False):
    import hashlib
    from threading import Event
    from uuid import uuid4

    from services.export_provider_adapter import LegacyProviderJob
    from services.legacy_export_snapshot_service import (
        LegacySnapshot,
        OutputSection,
        configuration_digest,
        output_digest,
    )

    sections = (
        OutputSection("data", ("GovernorID", "Name"), ((123, "=RAW literal"), (None, None))),
    )
    config = dict(
        destinations=["file-a"],
        outputs=[dict(section="data", file_id="file-a", tab="Data", grid_id=7, format_requests=[])],
    )
    if decimal_cells:
        from decimal import Decimal

        import pandas as pd

        from gsheet_module import plan_legacy_outputs

        sections, config = plan_legacy_outputs(
            dict(
                consumer="scan_data",
                spreadsheets={"Book": "file-a"},
                grid_ids={"file-a": {"Data": 7}},
                exports=[dict(sheet="Book", tab="Data", sort=0)],
            ),
            frames=[
                pd.DataFrame(
                    {
                        "Weight": [Decimal("10.1234567890123456789"), Decimal("2.50")],
                        "Name": ["ten", "two"],
                    }
                )
            ],
        )
        assert sections[0].rows == (("2.50", "two"), ("10.1234567890123456789", "ten"))
    snapshot = LegacySnapshot.capture(
        consumer="scan_data",
        preparation_id=str(uuid4()),
        config=config,
        generation=dict(
            completion="committed",
            commit_identity="exact-completion",
            output_sha256=output_digest(sections),
            config_sha256=configuration_digest(config),
        ),
        provenance={},
        sections=sections,
    )
    events = []

    class SDK:
        def __init__(self):
            self.rows = []

        def spreadsheets(self):
            return self

        def values(self):
            return self

        def permissions(self):
            return self

        def request(self, method, response):
            def execute(**kwargs):
                assert kwargs == {"num_retries": 0}
                events.append(method)
                return response() if callable(response) else response

            return SimpleNamespace(
                method=method,
                uri="https://sheets.googleapis.com/v4/spreadsheets/file-a",
                execute=execute,
            )

        def list(self, **kwargs):
            return self.request("GET", {"permissions": [{"type": "user", "role": "owner"}]})

        def get(self, **kwargs):
            if "fields" in kwargs:
                return self.request(
                    "GET",
                    {
                        "sheets": [
                            {
                                "properties": {
                                    "sheetId": 8 if wrong_grid else 7,
                                    "title": "Data",
                                    "gridProperties": {"rowCount": 1, "columnCount": 1},
                                }
                            }
                        ]
                    },
                )
            return self.request(
                "GET",
                lambda: {
                    "values": (
                        [["wrong"]]
                        if wrong_readback
                        else (self.rows if decimal_cells else self.rows[:-1])
                    )
                },
            )

        def batchUpdate(self, **kwargs):
            assert kwargs["body"]["requests"][0]["updateSheetProperties"]["properties"][
                "gridProperties"
            ] == {"rowCount": 3, "columnCount": 2}
            return self.request("POST", {})

        def clear(self, **kwargs):
            return self.request("POST", {})

        def update(self, **kwargs):
            assert kwargs["valueInputOption"] == "RAW"
            return self.request(
                "PUT", lambda: setattr(self, "rows", kwargs["body"]["values"]) or {}
            )

    sdk = SDK()
    dal, budget = Mock(), Mock()
    dal.begin_attempt.return_value = "attempt-1"
    job = dict(ConsumerKind="scan_data", InputHash=hashlib.sha256(snapshot.payload).digest())
    args = job, SimpleNamespace(fence=9, job_id="job-a"), dal, budget, Event(), snapshot.payload
    return LegacyProviderJob(lambda job: (sdk, sdk)), args, events


def test_complete_delivery_paces_every_request_and_confirms_exact_attempt():
    worker, args, events = delivery_fixture()
    worker(*args)
    dal, budget = args[2:4]
    assert budget.call_count == budget.completed.call_count == len(events) == 7
    assert events == ["GET", "GET", "POST", "POST", "PUT", "GET", "GET"]
    dal.verified.assert_called_once_with(args[1], "attempt-1", audience="private")
    receipt = dal.confirm.call_args.args[2]
    assert receipt["attempt_id"] == "attempt-1" and receipt["fence"] == 9
    assert receipt["files"] == ["file-a"]


def test_s11_legacy_delivery_refuses_unscoped_sdk_before_provider_call():
    worker, args, events = delivery_fixture()
    args[2].execution_evidence = True
    with pytest.raises(ProviderOutcomeUnknown, match="Independent authority stream"):
        worker(*args)
    assert events == []
    args[2].begin_attempt.assert_not_called()
    args[2].confirm.assert_not_called()


def test_s11_legacy_binds_real_authority_stream_and_retains_provider_failure(monkeypatch):
    from services.export_runtime_composition import AuthorityStream

    worker, args, events = delivery_fixture()
    args[2].execution_evidence = True
    client = Mock()
    stream = AuthorityStream(client, {})
    worker.authority_stream = lambda *_args: stream

    def adapter(**kwargs):
        assert kwargs["execution"].__self__ is stream
        assert kwargs["stream_id"] == stream.stream_id
        return SimpleNamespace(execute=Mock(side_effect=ProviderOutcomeUnknown("lost response")))

    monkeypatch.setattr("services.export_provider_adapter.ProviderAdapter", adapter)
    with pytest.raises(ProviderOutcomeUnknown):
        worker(*args)
    client.close_stream.assert_called_once_with(stream.stream_id)
    args[2].confirm.assert_not_called()
    assert events == []


def test_decimal_planning_snapshot_and_raw_delivery_preserve_exact_values():
    worker, args, events = delivery_fixture(decimal_cells=True)
    worker(*args)
    args[2].verified.assert_called_once()
    args[2].confirm.assert_called_once()
    assert "PUT" in events


@pytest.mark.parametrize("stop_at", ["claim", "cooldown", "clear"])
def test_coordinator_drains_admitted_delivery_and_blocks_next_account(monkeypatch, stop_at):
    from services import export_coordination_service as coordination
    from services.export_request_budget import RequestBudget

    worker, args, events = delivery_fixture()
    job, claim, dal, _, stop, payload = args
    job.update(SpoolKey="retained", SpoolBytes=len(payload), StorageOwner="local")
    dal.pending_intents.return_value = []
    dal.accounts.return_value = ["acct-a", "acct-b"]

    def claim_next(*args, **kwargs):
        if stop_at == "claim":
            stop.set()
        return claim

    dal.claim_next.side_effect = claim_next
    dal.authorize.return_value = job
    dal.reserve_request.return_value = dict(WaitSeconds=1, ReservedUTC="server-slot")
    dal.refresh_reservation.return_value = dict(WaitSeconds=0)
    waits = []

    def sleep(seconds):
        waits.append(seconds)
        if stop_at == "cooldown":
            stop.set()

    def completed(account):
        if stop_at == "clear" and events == ["GET", "GET", "POST", "POST"]:
            stop.set()

    dal.complete_request.side_effect = completed
    # Use the real reservation/wait/checkpoint implementation with offline sleep.
    monkeypatch.setattr(
        coordination, "RequestBudget", lambda *a, **kw: RequestBudget(*a, sleep=sleep, **kw)
    )
    storage = SimpleNamespace(storage_owner="local", read=Mock(return_value=payload))
    service = coordination.ExportCoordinator(dal, adapters={"scan_data": worker}, storage=storage)
    service.run_batch(stop)
    assert stop.is_set()
    assert events == ["GET", "GET", "POST", "POST", "PUT", "GET", "GET"]
    assert waits == [1] * 7
    assert dal.reserve_request.call_count == dal.refresh_reservation.call_count == 7
    assert dal.complete_request.call_count == 7
    assert dal.authorize.call_count == 15  # initial claim plus two guards per request
    dal.verified.assert_called_once()
    dal.publication_pending.assert_called_once()
    dal.confirm.assert_called_once()
    dal.fail.assert_not_called()
    dal.claim_next.assert_called_once_with("acct-a", storage_owner="local")
    service.run_batch(stop)
    assert dal.pending_intents.call_count == 1


def test_shutdown_drain_still_retains_unknown_completion():
    from services.export_coordination_service import ExportCoordinator

    worker, args, events = delivery_fixture()
    job, claim, dal, _, stop, payload = args
    job.update(SpoolKey="retained", SpoolBytes=len(payload), StorageOwner="local")
    dal.pending_intents.return_value = []
    dal.accounts.return_value = ["acct-a", "acct-b"]
    dal.claim_next.return_value = claim
    dal.authorize.return_value = job
    dal.reserve_request.return_value = dict(WaitSeconds=0, ReservedUTC="server-slot")
    dal.refresh_reservation.return_value = dict(WaitSeconds=0)

    def completed(account):
        if events == ["GET", "GET", "POST", "POST"]:
            stop.set()
            raise RuntimeError("Completion acknowledgement lost")

    dal.complete_request.side_effect = completed
    storage = SimpleNamespace(storage_owner="local", read=Mock(return_value=payload))
    ExportCoordinator(dal, adapters={"scan_data": worker}, storage=storage).run_batch(stop)
    assert events == ["GET", "GET", "POST", "POST"]
    dal.fail.assert_called_once_with(claim, retain_claims=True)
    dal.confirm.assert_not_called()
    dal.claim_next.assert_called_once()


def test_grid_conflict_is_detected_before_any_attempt_or_mutation():
    from services.legacy_export_snapshot_service import SnapshotUnavailable

    worker, args, events = delivery_fixture(wrong_grid=True)
    with pytest.raises(SnapshotUnavailable, match="conflicts"):
        worker(*args)
    assert events == ["GET", "GET"]
    args[2].begin_attempt.assert_not_called()


def test_failed_full_readback_retains_attempt_and_never_confirms():
    worker, args, events = delivery_fixture(wrong_readback=True)
    with pytest.raises(ProviderOutcomeUnknown, match="readback"):
        worker(*args)
    args[2].begin_attempt.assert_called_once()
    args[2].verified.assert_not_called()
    args[2].confirm.assert_not_called()


def adapter():
    budget, authorize = Mock(), Mock()
    return (
        ProviderAdapter(budget=budget, authorize=authorize, destinations=("file-a",)),
        budget,
        authorize,
    )


def test_google_execute_reserves_rechecks_and_checkpoints_actual_request():
    wrapped, budget, authorize = adapter()
    events = []
    budget.side_effect = lambda: events.append("reserve")
    budget.completed.side_effect = lambda: events.append("complete")
    authorize.side_effect = lambda **kw: events.append("authorize")
    request = SimpleNamespace(
        method="GET",
        uri="https://sheets.googleapis.com/v4/spreadsheets/file-a",
        execute=Mock(side_effect=lambda **kw: events.append("execute")),
    )
    wrapped.execute(request)
    assert events == ["authorize", "reserve", "authorize", "execute", "complete"]
    request.execute.assert_called_once_with(num_retries=0)


def test_gspread_multi_request_method_paces_every_http_request():
    wrapped, budget, _ = adapter()

    class Client:
        def request(self, method, endpoint):
            return "value"

        def many(self):
            return [
                self.request("get", "https://sheets.googleapis.com/v4/spreadsheets/file-a")
                for _ in range(3)
            ]

    client = wrapped.bind_gspread(Client())
    assert client.many() == ["value"] * 3
    assert budget.call_count == budget.completed.call_count == 3
    with pytest.raises(ValueError):
        wrapped.bind_gspread(client)


def test_gspread_internal_backoff_is_rejected_before_requests():
    from gspread.http_client import BackOffHTTPClient

    wrapped, budget, _ = adapter()
    with pytest.raises(ValueError, match="backoff"):
        wrapped.bind_gspread(BackOffHTTPClient.__new__(BackOffHTTPClient))
    budget.assert_not_called()


def test_mutation_failure_blocks_same_adapter_even_if_outer_wrapper_retries():
    wrapped, budget, _ = adapter()
    execute = Mock(side_effect=TimeoutError("ambiguous"))
    with pytest.raises(ProviderOutcomeUnknown):
        wrapped.call(execute, mutation=True, destination="file-a")
    with pytest.raises(ProviderOutcomeUnknown):
        wrapped.call(execute, mutation=True, destination="file-a")
    assert execute.call_count == budget.call_count == budget.completed.call_count == 1


@pytest.mark.parametrize("checkpoint", ["reservation", "completed", "rejected"])
def test_unknown_budget_checkpoint_retains_claim(checkpoint):
    wrapped, budget, _ = adapter()
    execute = Mock(return_value="ok")
    if checkpoint == "reservation":
        budget.side_effect = RuntimeError("lost commit")
    else:
        getattr(budget, checkpoint).side_effect = RuntimeError("lost commit")
        if checkpoint == "rejected":
            execute.side_effect = TimeoutError()
    with pytest.raises(ProviderOutcomeUnknown):
        wrapped.call(execute, mutation=False, destination="file-a")
    assert wrapped.uncertain


def test_gspread_retry_after_is_normalized_for_common_budget():
    wrapped, budget, _ = adapter()
    error = RuntimeError("limited")
    error.response = SimpleNamespace(status_code=429, headers={"Retry-After": "120"})
    with pytest.raises(RuntimeError):
        wrapped.call(Mock(side_effect=error), mutation=False, destination="file-a")
    response = budget.rejected.call_args.args[0].resp
    assert response.status == 429 and response["retry-after"] == "120"
    budget.completed.assert_called_once()


@pytest.mark.parametrize(
    "uri",
    [
        "http://sheets.googleapis.com/v4/spreadsheets/file-a",
        "https://evil.invalid/file-a",
        "https://sheets.googleapis.com/v4/spreadsheets/file-b",
        "https://www.googleapis.com/drive/v3/files",
    ],
)
def test_unregistered_or_discovery_request_never_escapes(uri):
    wrapped, budget, _ = adapter()
    request = SimpleNamespace(method="POST", uri=uri, execute=Mock())
    with pytest.raises(ValueError):
        wrapped.execute(request)
    budget.assert_not_called()
    request.execute.assert_not_called()
