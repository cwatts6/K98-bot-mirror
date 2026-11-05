"""Synthetic Google child; real rollover worker, authority journals and SQL proofs."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID

from core.export_execution_host import DeploymentBoundary
from kvk.services.new_source_export_service import GoogleSheetsTransport
from kvk.services.source_output_pool_service import SourceOutputPoolService
from services.export_coordination_dal import ExportCoordinationDAL
from services.export_execution_protocol import ProviderRequest, validate_response
from services.export_reconciliation_service import TrustedProofIssuer
from services.export_runtime_composition import (
    AuthorityReconciler,
    AuthorityStream,
    LocalAuthorityClient,
    OutputOperationStreams,
    RuntimeRegistration,
)
from tests.test_export_enrollment_service import FakeChild
from tests.test_kvk_source_delivery import google_delivery


def install_worker(r, activation):
    _, _, api = google_delivery()
    registration = RuntimeRegistration(activation["registration"])
    pools = r.rpc.pools
    sheets = registration.sheets(pools.snapshot(activation["replacement_id"]))
    template = deepcopy(api.files_data["fake-index"])
    for file_id in activation["mapping"].values():
        api.files_data[file_id] = dict(
            deepcopy(template),
            id=file_id,
            permissions=[
                dict(type="user", role="owner", emailAddress=sheets.owner_email),
                dict(type="user", role="writer", emailAddress=sheets.service_account_email),
            ],
        )
        api.grids[file_id] = dict(
            Sheet1=dict(
                sheetId=42, title="Sheet1", gridProperties=dict(rowCount=1000, columnCount=26)
            )
        )
    provider = SimpleNamespace(failure=None, sent=[])

    class Child(FakeChild):
        def execute(self, message):
            typed = ProviderRequest.parse(message)
            assert typed.target in activation["mapping"].values()
            provider.sent.append(typed)
            args = typed.arguments
            if typed.operation.startswith("drive."):
                _, resource, method = typed.operation.split(".")
                args["fileId"] = typed.target
                result = api.execute("/" + resource, method, args, 0)
            else:
                args["spreadsheetId"] = typed.target
                path = (
                    "/spreadsheets/values"
                    if typed.operation.startswith("sheets.values.")
                    else "/spreadsheets"
                )
                result = api.execute(path, typed.operation.split(".")[-1], args, 0)
                if typed.operation == "sheets.values.get":
                    result["range"] = args["range"]
                else:
                    result["spreadsheetId"] = typed.target
                if typed.operation == "sheets.batchUpdate":
                    result["replies"] = [{} for _ in args["body"]["requests"]]
                if typed.operation == "sheets.values.update":
                    values = args["body"]["values"]
                    result.update(
                        updatedRange=args["range"],
                        updatedRows=len(values),
                        updatedColumns=max(map(len, values), default=0),
                        updatedCells=sum(map(len, values)),
                    )
            validate_response(typed, result)
            return result

    authority = r.service.authority
    if not hasattr(r, "verification_host"):
        r.verification_host = authority.host
    authority.host = SimpleNamespace(
        create_suspended=lambda identifier: Child(identifier, provider)
    )
    authority.store.read = lambda receipt: authority.store.read_reference(
        str(UUID(receipt.key)), bytes.fromhex(receipt.sha256)
    )
    boundary = DeploymentBoundary.__new__(DeploymentBoundary)
    boundary._raw = b"synthetic disposable host; no native verification"
    boundary._manifest = dict(r.broker.boundary._manifest)
    boundary._manifest["deployment_boundary"]["host"] = dict(
        hostname=r.f.sql.execute(
            "SELECT HostIdentity FROM #ExportExecutionSession WHERE SessionID=?",
            authority.session_id,
        )
        .fetchval()
        .lower()
    )
    boundary.recheck = Mock(return_value=boundary.fingerprint)
    r.broker.boundary = boundary
    local = LocalAuthorityClient(r.broker)
    r.broker.issuer = TrustedProofIssuer(
        authority=authority,
        boundary=boundary,
        registration=registration,
        coordinator=ExportCoordinationDAL(
            r.f.connect, preparations=True, output_operations=True, execution_evidence=True
        ),
        pools=pools,
        client=local,
    )
    # Bind callback dispatch and private proof production to the same disposable
    # boundary. Native process protection is covered by the package rehearsal.
    r.rpc.client._invoke = lambda message: r.broker.dispatch(
        dict(message, deployment_hash=boundary.fingerprint)
    )
    r.rpc.client.stream = lambda scope: AuthorityStream(r.rpc.client, scope)
    reconciler = AuthorityReconciler(r.rpc.client)
    r.adapter.base.reconciler = reconciler
    streams = OutputOperationStreams(pools=pools, client=r.rpc.client)

    def transport(operation, stream):
        return GoogleSheetsTransport.from_authority(
            registration=sheets,
            reuse_guard=lambda *_: False,
            protected_file_ids=registration.value()["protected_file_ids"],
            execution=stream.execute,
            stream_id=stream.stream_id,
            authorize=lambda **_: None,
        )

    worker = SourceOutputPoolService(
        pools,
        transport_factory=transport,
        termination_verifier=reconciler.drain,
        budget_factory=lambda _: Mock(),
        authority_stream_factory=streams,
    )
    return worker, provider.sent
