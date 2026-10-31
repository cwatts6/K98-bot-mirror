"""Real authority/SQL delivery with a deterministic child and no provider HTTP.

Private journal bytes use a hash-checked in-memory store; native custody and
encryption are qualified separately. SQL transitions are complete source bodies.
"""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from services.export_execution_authority import ExportExecutionAuthority
from services.export_execution_dal import ExportExecutionDAL
from services.export_execution_protocol import ProviderRequest, encode
from services.export_provider_adapter import LegacyProviderJob
from services.export_runtime_composition import (
    AuthorityStream,
    LegacyExecutionStreams,
    RuntimeRegistration,
)
from tests.test_config_read_containment import private_store
from tests.test_export_enrollment_service import FakeChild
from tests.test_export_runtime_composition import registration_fixture


def provider_fixture(r, configuration, *, failure=None):
    session = str(uuid4())
    r.owner.execute(
        r.rewrite(
            "INSERT dbo.ExportExecutionSession "
            "(SessionID,AuthorityPrincipal,HostIdentity,BootID,ExecutableHash,ManifestHash,"
            "ProtocolVersion,State,Version,CreatedUTC) "
            "VALUES (?,USER_NAME(),'disposable-rehearsal',?,CAST(? AS binary(32)),"
            "CAST(? AS binary(32)),1,'open',1,SYSUTCDATETIME())"
        ),
        session,
        str(uuid4()),
        b"e" * 32,
        b"m" * 32,
    )
    value = registration_fixture()
    value.update(account="a", storage_owner="disk-a")
    value["legacy_configuration"].update(configuration)
    value["protected_file_ids"] = sorted(
        {f for scope in value["legacy_configuration"].values() for f in scope["destinations"]}
    )
    registration = RuntimeRegistration(value)
    state = SimpleNamespace(failure=failure, sent=[], rows={}, grids={}, children=[], documents={})

    class Child(FakeChild):
        def execute(self, message):
            typed = ProviderRequest.parse(message)
            assert typed.target == "registered"
            state.sent.append(typed)
            args = typed.arguments
            if typed.operation == "drive.permissions.list":
                return dict(permissions=[dict(type="user", role="owner")])
            if typed.operation == "sheets.get":
                return dict(
                    spreadsheetId=typed.target,
                    sheets=[dict(properties=p) for p in state.grids.values()],
                )
            if typed.operation == "sheets.batchUpdate":
                for item in args["body"]["requests"]:
                    if "addSheet" in item:
                        p = deepcopy(item["addSheet"]["properties"])
                        state.grids[p["sheetId"]] = p
                return dict(
                    spreadsheetId=typed.target, replies=[{} for _ in args["body"]["requests"]]
                )
            if typed.operation == "sheets.values.clear":
                state.rows.clear()
                return dict(spreadsheetId=typed.target, clearedRange=args["range"])
            if typed.operation == "sheets.values.update":
                state.rows["values"] = deepcopy(args["body"]["values"])
                if failure == "write_reply":
                    raise TimeoutError("Write applied; response lost")
                values = state.rows["values"]
                return dict(
                    spreadsheetId=typed.target,
                    updatedRange=args["range"],
                    updatedRows=len(values),
                    updatedColumns=len(values[0]),
                    updatedCells=sum(map(len, values)),
                )
            if typed.operation == "sheets.values.get":
                values = deepcopy(state.rows)
                if failure == "readback":
                    values = dict(values=[["value"], [999]])
                return dict(values, range=args["range"])
            raise AssertionError(typed.operation)

    def create(identifier):
        child = Child(identifier, state)
        state.children.append(child)
        return child

    authority = ExportExecutionAuthority(
        session_id=session,
        dal=ExportExecutionDAL(r.connect),
        store=private_store(state.documents),
        host=SimpleNamespace(create_suspended=create),
        budget_factory=lambda _: Mock(),
    )

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
        coordinator=r.runtime.coordinator,
        preparations=SimpleNamespace(execution_evidence=True, output_operations=True),
        client=client,
        account="a",
        storage_owner="disk-a",
        configuration=value["legacy_configuration"],
    )
    from googleapiclient.discovery import build

    state.http = SimpleNamespace(request=Mock(side_effect=AssertionError("Live HTTP forbidden")))
    sheets = build("sheets", "v4", http=state.http, static_discovery=True)
    drive = build("drive", "v3", http=state.http, static_discovery=True)
    state.adapter = LegacyProviderJob(lambda _: (sheets, drive), authority_stream=streams.delivery)
    state.authority = authority
    return state
