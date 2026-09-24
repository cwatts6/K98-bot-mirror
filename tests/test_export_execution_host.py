from types import SimpleNamespace

import pytest

from core.export_execution_host import (
    DeploymentBoundary,
    HostBoundaryError,
    MessagePipe,
    PrivateEvidenceStore,
    WindowsProviderChild,
)


@pytest.mark.parametrize(
    "group,privilege,elevation,expected",
    [
        ("S-1-5-32-545", "SeChangeNotifyPrivilege", 1, True),
        ("S-1-5-32-544", "SeChangeNotifyPrivilege", 1, False),
        ("S-1-5-32-551", "SeChangeNotifyPrivilege", 1, False),
        ("S-1-5-21-111-222-333-512", "SeChangeNotifyPrivilege", 1, False),
        ("S-1-5-32-545", "SeDebugPrivilege", 1, False),
        ("S-1-5-32-545", "SeBackupPrivilege", 1, False),
        ("S-1-5-32-545", "SeImpersonatePrivilege", 1, False),
        ("S-1-5-32-545", "UnreviewedPrivilege", 1, False),
        ("S-1-5-32-545", "SeChangeNotifyPrivilege", 3, False),
    ],
)
def test_ipc_token_rejects_even_deny_only_groups_and_disabled_privileges(
    group, privilege, elevation, expected
):
    from core.export_execution_host import inspect_bot_token

    sid = "S-1-5-21-111-222-333-555"
    values = dict(
        user=(sid, 0),
        groups=[(group, 16)],
        privileges=[(123, 0)],
        elevation=elevation,
        elevated=0,
        ui=0,
    )
    security = SimpleNamespace(
        TokenUser="user",
        TokenGroups="groups",
        TokenPrivileges="privileges",
        TokenElevationType="elevation",
        TokenElevation="elevated",
        TokenUIAccess="ui",
        GetTokenInformation=lambda token, field: values[field],
        ConvertSidToStringSid=str,
        LookupPrivilegeName=lambda _, luid: privilege,
    )
    if expected:
        inspect_bot_token(object(), sid, security=security)
    else:
        with pytest.raises(HostBoundaryError, match="nonprivileged"):
            inspect_bot_token(object(), sid, security=security)


def test_ipc_authentication_reverts_and_closes_token_when_privileged_bot_is_refused(monkeypatch):
    import sys
    from unittest.mock import Mock

    from core.export_execution_host import authenticated_peer

    token = SimpleNamespace(Close=Mock())
    security = SimpleNamespace(
        TokenUser="user",
        OpenThreadToken=lambda *_: token,
        GetTokenInformation=lambda *_: ("bot-sid", 0),
        ConvertSidToStringSid=str,
        RevertToSelf=Mock(),
    )
    monkeypatch.setitem(sys.modules, "win32api", SimpleNamespace(GetCurrentThread=lambda: 1))
    monkeypatch.setitem(
        sys.modules, "win32pipe", SimpleNamespace(ImpersonateNamedPipeClient=Mock())
    )
    monkeypatch.setitem(sys.modules, "win32security", security)
    inspect = Mock(side_effect=HostBoundaryError("privileged"))
    monkeypatch.setattr("core.export_execution_host.inspect_bot_token", inspect)
    with pytest.raises(HostBoundaryError, match="privileged"):
        authenticated_peer(1, "bot-sid", bot_authority_sid="authority-sid")
    inspect.assert_called_once_with(token, "bot-sid", authority_sid="authority-sid")
    token.Close.assert_called_once()
    security.RevertToSelf.assert_called_once()


def deployment_fixture(tmp_path):
    """Synthetic normalized G4 records; never installation/provider evidence."""
    import hashlib
    from uuid import uuid4

    from services.export_execution_protocol import encode
    from tests.test_export_runtime_composition import installation_fixture, registration_fixture

    stamp = "2026-09-24T12:00:00Z"
    credential = dict(
        type="service_account",
        client_email="editor@example.iam.gserviceaccount.com",
        project_id="project",
        client_id="123456",
        private_key_id="a" * 40,
        token_uri="https://oauth2.googleapis.com/token",
    )
    credentials = tmp_path / "synthetic-key.json"
    credentials.write_bytes(encode(credential))
    _, sql = installation_fixture()
    m = dict(
        authority_sid="S-1-5-21-111-222-333-444",
        bot_sid="S-1-5-21-111-222-333-555",
        source_hashes={"fixture.py": "b" * 64},
        runtime_registration=registration_fixture(),
        sql_contract=sql,
        service_account_email=credential["client_email"],
        project_id="project",
        python=str(tmp_path / "python.exe"),
        child_script=str(tmp_path / "child.py"),
        credentials_file=str(credentials),
        evidence_root=str(tmp_path / "evidence"),
    )
    value = dict(
        version=1,
        deployment_id=str(uuid4()),
        host=dict(machine_guid=str(uuid4()), hostname="fixture-host"),
        authority_sid=m["authority_sid"],
        bot_sid=m["bot_sid"],
        identity=dict(
            service_account_email=credential["client_email"],
            previous_service_account_email="old@example.iam.gserviceaccount.com",
            project_id="project",
            client_id=credential["client_id"],
            private_key_id=credential["private_key_id"],
            credential_sha256=hashlib.sha256(credentials.read_bytes()).hexdigest(),
        ),
        paths={k: m[k] for k in ("python", "child_script", "credentials_file", "evidence_root")},
        review=dict(
            review_id=str(uuid4()),
            administrators=dict(
                windows="fixture-os-admin", sql="fixture-sql-admin", provider="owner@example.com"
            ),
            records={},
        ),
    )
    for name, source in (
        ("source_hash", "source_hashes"),
        ("registration_hash", "runtime_registration"),
        ("sql_contract_hash", "sql_contract"),
    ):
        value[name] = hashlib.sha256(encode(m[source])).hexdigest()
    files = {
        target: "owner@example.com"
        for configured in m["runtime_registration"]["legacy_configuration"].values()
        for target in configured["destinations"]
    }
    for pool in m["runtime_registration"]["pools"]:
        files.update(
            {
                target: pool["owner_email"]
                for target in [pool["index_file_id"], *pool["slot_file_ids"]]
            }
        )
    rows = {
        "bot_identity": [
            dict(
                host=value["host"],
                user_sid=m["bot_sid"],
                group_sids=["S-1-5-32-545"],
                privileges=["SeChangeNotifyPrivilege"],
                elevation_type=1,
                elevated=False,
                ui_access=False,
                observed_utc=stamp,
            )
        ],
        "host_acl": [
            dict(
                path=path,
                owner_sid=m["authority_sid"],
                sddl="O:SYD:(A;;FA;;;SY)",
                observed_utc=stamp,
            )
            for path in value["paths"].values()
        ],
        "identity_issuance": [
            dict(
                service_account_email=credential["client_email"],
                project_id="project",
                client_id=credential["client_id"],
                private_key_id=credential["private_key_id"],
                created_utc=stamp,
                issued_utc=stamp,
                custody_path=str(credentials),
                issuing_administrator="owner@example.com",
            )
        ],
        "key_inventory": [
            dict(
                service_account_email=credential["client_email"],
                user_managed_key_ids=[credential["private_key_id"]],
                credential_holders=[m["authority_sid"]],
                observed_utc=stamp,
            )
        ],
        "file_access": [
            dict(
                file_id=target,
                owner_email=owner,
                editors=[credential["client_email"]],
                audience="anyone_reader",
                observed_utc=stamp,
            )
            for target, owner in files.items()
        ],
        "writer_drain": [
            dict(
                host=value["host"],
                observed_utc=stamp,
                remaining_writers=[],
                sql_sessions=[],
                processes=[
                    dict(
                        pid=1234,
                        started_utc=stamp,
                        image_sha256="c" * 64,
                        exit_code=0,
                        exited_utc=stamp,
                    )
                ],
            )
        ],
        "sql_installation": [
            dict(
                contract_sha256=value["sql_contract_hash"],
                observed_utc=stamp,
                **{k: sql[k] for k in ("server", "database", "principal")},
            )
        ],
    }
    records = {}
    for kind, observations in rows.items():
        path = tmp_path / (kind + ".json")
        record = dict(
            version=1,
            kind=kind,
            deployment_id=value["deployment_id"],
            review_id=value["review"]["review_id"],
            observations=observations,
        )
        path.write_bytes(encode(record))
        value["review"]["records"][kind] = dict(
            path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()
        )
        records[kind] = record
    m["deployment_boundary"] = value
    from pathlib import Path

    reads = dict(
        inspect_path=lambda path, **_: Path(path),
        observe_host=lambda: value["host"],
        observe_sid=lambda: m["authority_sid"],
    )
    return m, records, reads


def test_deployment_boundary_rechecks_private_bytes_without_windows_or_provider(tmp_path):
    from pathlib import Path

    m, _, reads = deployment_fixture(tmp_path)
    boundary = DeploymentBoundary(m, **reads)
    assert boundary.recheck() == boundary.fingerprint
    Path(m["credentials_file"]).write_bytes(b"different credential")
    with pytest.raises(HostBoundaryError, match="credential bytes"):
        boundary.recheck()


@pytest.mark.parametrize("kind", sorted(DeploymentBoundary.RECORDS))
@pytest.mark.parametrize("damage", ["missing", "changed_bytes", "boolean", "foreign_review"])
def test_missing_altered_or_assertion_only_g4_records_never_admit(tmp_path, kind, damage):
    import hashlib
    from pathlib import Path
    from uuid import uuid4

    from services.export_execution_protocol import encode

    m, records, reads = deployment_fixture(tmp_path)
    reference = m["deployment_boundary"]["review"]["records"][kind]
    if damage == "missing":
        del m["deployment_boundary"]["review"]["records"][kind]
    else:
        record = records[kind]
        if damage == "foreign_review":
            record["review_id"] = str(uuid4())
        else:
            record["observations"] = [{"approved": True}]
        raw = encode(record)
        Path(reference["path"]).write_bytes(raw)
        if damage != "changed_bytes":
            reference["sha256"] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(HostBoundaryError):
        DeploymentBoundary(m, **reads)


@pytest.mark.parametrize(
    "damage",
    [
        "host",
        "sid",
        "old_identity",
        "source",
        "sql",
        "paths",
        "key",
        "extra_key_holder",
        "external_editor",
        "unclosed_writer",
    ],
)
def test_deployment_boundary_refuses_wrong_host_key_writer_or_contract(tmp_path, damage):
    import hashlib
    from pathlib import Path

    from services.export_execution_protocol import encode

    m, records, reads = deployment_fixture(tmp_path)
    boundary = m["deployment_boundary"]
    if damage == "host":
        reads["observe_host"] = lambda: dict(boundary["host"], hostname="other-host")
    elif damage == "sid":
        reads["observe_sid"] = lambda: m["bot_sid"]
    elif damage == "old_identity":
        boundary["identity"]["previous_service_account_email"] = m["service_account_email"]
    elif damage == "source":
        m["source_hashes"]["fixture.py"] = "d" * 64
    elif damage == "sql":
        m["sql_contract"]["principal"] = "another-principal"
    elif damage == "paths":
        m["evidence_root"] = str(tmp_path / "another-root")
    elif damage == "key":
        boundary["identity"]["private_key_id"] = "b" * 40
    else:
        kind = {
            "extra_key_holder": "key_inventory",
            "external_editor": "file_access",
            "unclosed_writer": "writer_drain",
        }[damage]
        record = records[kind]
        field = {
            "extra_key_holder": "credential_holders",
            "external_editor": "editors",
            "unclosed_writer": "remaining_writers",
        }[damage]
        record["observations"][0][field].append("outside-authority")
        reference = boundary["review"]["records"][kind]
        raw = encode(record)
        Path(reference["path"]).write_bytes(raw)
        reference["sha256"] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(HostBoundaryError):
        DeploymentBoundary(m, **reads)


def test_pipe_assembles_bounded_message_and_rejects_partial_write():
    chunks = iter([(234, b'{"version":'), (0, b"1}")])
    pipe = MessagePipe(
        1, api=SimpleNamespace(ReadFile=lambda *_: next(chunks), WriteFile=lambda *_: (0, 1))
    )
    assert pipe.receive() == {"version": 1}
    with pytest.raises(HostBoundaryError):
        pipe.send({"version": 1})


@pytest.mark.parametrize("chunk", [(0, b""), (5, b"{}")])
def test_pipe_disconnect_or_unknown_status_is_not_a_response(chunk):
    pipe = MessagePipe(1, api=SimpleNamespace(ReadFile=lambda *_: chunk))
    with pytest.raises(HostBoundaryError):
        pipe.receive()


def test_private_store_reads_back_encryption_and_detects_corruption(tmp_path):
    store = PrivateEvidenceStore(
        tmp_path, "test_authority", protect=lambda b: b[::-1], unprotect=lambda b: b[::-1]
    )
    receipt = store.put(b"private payload")
    assert (tmp_path / receipt.key).read_bytes() != b"private payload"
    assert store.read(receipt) == b"private payload"
    (tmp_path / receipt.key).write_bytes(b"corrupt")
    with pytest.raises(HostBoundaryError):
        store.read(receipt)


@pytest.mark.parametrize("signaled,active", [(258, 0), (0, 1)])
def test_child_without_exact_process_and_empty_job_cannot_prove_termination(signaled, active):
    class Handle:
        def Close(self):
            raise AssertionError("Unproven handles must remain retained")

    handle = Handle()
    child = WindowsProviderChild(
        identity="child",
        process=handle,
        thread=None,
        job=handle,
        pid=17,
        pipe=SimpleNamespace(handle=handle),
        sid="sid",
        api={
            "job": SimpleNamespace(
                TerminateJobObject=lambda *_: None,
                QueryInformationJobObject=lambda *_: {"ActiveProcesses": active},
            ),
            "event": SimpleNamespace(WaitForSingleObject=lambda *_: signaled),
        },
    )
    with pytest.raises(HostBoundaryError):
        child.terminate_and_observe()
    assert not child.terminated


@pytest.mark.parametrize("status", [202, 204, 301, 400, 401, 429, 503])
def test_child_transport_never_retries_or_follows_redirects(status):
    from uuid import uuid4

    from scripts.run_export_provider_child import execute_http
    from services.export_execution_protocol import ProtocolError, ProviderRequest

    calls = []

    class Session:
        def request(self, *args, **kwargs):
            calls.append((args, kwargs))
            return SimpleNamespace(status_code=status, close=lambda: None)

    request = ProviderRequest.parse(
        dict(
            version=1,
            request_id=str(uuid4()),
            stream_id=str(uuid4()),
            operation="sheets.values.clear",
            target="registered_file",
            arguments={"range": "Sheet1", "body": {}},
        )
    )
    with pytest.raises(ProtocolError):
        execute_http(
            request,
            session=Session(),
            credentials=SimpleNamespace(valid=True, token="test-token"),
            refresh_request=None,
        )
    assert len(calls) == 1
    assert calls[0][1]["allow_redirects"] is False
    assert calls[0][0][0] == "POST"


def test_child_batch_read_uses_one_fixed_get_with_ordered_ranges():
    from unittest.mock import Mock
    from uuid import uuid4

    from scripts.run_export_provider_child import execute_http
    from services.export_execution_protocol import ProviderRequest

    ranges = ["'A'!A1:B2", "'B'!A1:A1"]
    response = {"spreadsheetId": "registered_file", "valueRanges": [{"range": r} for r in ranges]}
    session = Mock()
    session.request.return_value = SimpleNamespace(
        status_code=200, json=lambda: response, close=Mock()
    )
    request = ProviderRequest.parse(
        dict(
            version=1,
            request_id=str(uuid4()),
            stream_id=str(uuid4()),
            operation="sheets.values.batchGet",
            target="registered_file",
            arguments={"ranges": ranges, "valueRenderOption": "FORMULA"},
        )
    )
    assert (
        execute_http(
            request,
            session=session,
            credentials=SimpleNamespace(valid=True, token="test-token"),
            refresh_request=None,
        )
        == response
    )
    session.request.assert_called_once()
    assert session.request.call_args.args == (
        "GET",
        "https://sheets.googleapis.com/v4/spreadsheets/registered_file/values:batchGet",
    )
    assert session.request.call_args.kwargs["params"]["ranges"] == ranges
    assert session.request.call_args.kwargs["allow_redirects"] is False


def test_live_windows_containment_is_a_separate_operation():
    import json
    import os
    from pathlib import Path
    import sys
    from uuid import uuid4

    from core.export_execution_host import WindowsExecutionHost

    if os.environ.get("K98_S11_WINDOWS_AUTHORIZED") != "S11_EXACT_CHILD_CONTAINMENT_APPROVED":
        pytest.skip(
            "No G4 authorization for disposable process/identity/pipe operations; mock evidence only"
        )
    path = Path(os.environ["K98_S11_WINDOWS_MANIFEST"])
    assert path.is_absolute() and path.is_file()
    manifest = json.loads(path.read_bytes())
    host = WindowsExecutionHost(
        python=sys.executable,
        child_script=Path(__file__).resolve().parents[1] / "scripts/run_export_provider_child.py",
        manifest=path,
        authority_sid=manifest["authority_sid"],
    )
    child = host.create_suspended(str(uuid4()))
    try:
        assert not child.resumed
        child.resume()
        assert child.resumed
        evidence = child.terminate_and_observe()
        assert evidence["process_signaled"] and evidence["job_empty"]
    finally:
        if not child.terminated:
            child.terminate_and_observe()
