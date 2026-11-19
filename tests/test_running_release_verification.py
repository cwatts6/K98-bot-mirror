"""No production operations: pure models and native PowerShell fixture orchestration."""

import base64
from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from scripts.package_k98_running_verification import RECEIPTS, build, validate_profile
from scripts.verify_k98_running_release import (
    ObservationConnections,
    VerificationBudgetExceeded,
    verify_sessions,
)
from services.application_maintenance_dal import SchemaObservationRefused, schema_observation

ROOT = Path(__file__).resolve().parents[1]
PS = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"


def test_source_successor_is_exact_indivisible_and_preserves_historical_registry(monkeypatch):
    from scripts import prepare_k98_update as updater

    transitions = updater.reviewed_transitions()
    assert (
        hashlib.sha256(json.dumps(transitions[:94], sort_keys=True).encode()).hexdigest()
        == "e2a68465696d60ebb6207fcb4c627f4314be99294aa9b591f4624544b798733d"
    )
    family = transitions[-1]
    assert family["id"] == updater.P02_CATALOG_TRANSITION
    assert {m["path"] for m in family["members"]} == updater.P02_CATALOG_PATHS
    raw = {
        m["path"]: (ROOT / m["path"]).read_bytes().replace(b"\r\n", b"\n")
        for m in family["members"]
    }
    for m in family["members"]:
        assert hashlib.sha256(raw[m["path"]]).hexdigest() == m["after_sha256"]
    marker = b"fixture-pinned-hash:"
    real_hash = updater.sha256
    monkeypatch.setattr(
        updater,
        "sha256",
        lambda value: (
            value[len(marker) :].decode() if value.startswith(marker) else real_hash(value)
        ),
    )
    before = {m["path"]: marker + m["before_sha256"].encode() for m in family["members"]}
    read = lambda rev, p: (before if rev == "before" else raw).get(p)
    assert updater.matches_protocol_transition(family, read, "before", "after")
    for path in raw:
        with pytest.raises(ValueError):
            updater.check_transition_inventory(
                [p for p in raw if p != path], read, "before", "after"
            )
        original = raw[path]
        raw[path] += b"\n# unknown\n"
        assert not updater.matches_protocol_transition(family, read, "before", "after")
        raw[path] = original


@pytest.mark.parametrize("result,code", [(-1, 12), (-2, 1), (-3, 1), (-999, 1)])
def test_only_acknowledged_timeout_is_pending(result, code):
    from scripts.verify_k98_running_release import failure_result

    actual, record = failure_result(SchemaObservationRefused(result))
    assert actual == code and record["schema_lock_result"] == result
    assert record["verified"] is False and record["retry"] is False


def test_cleanup_uncertainty_overrides_refusal_and_redacts_error_prose():
    from core.sql_connection_custody import SqlCleanupUnknown
    from scripts.verify_k98_running_release import failure_result

    error = SqlCleanupUnknown("private driver credentials must not appear")
    error.__cause__ = SchemaObservationRefused(-1)
    code, record = failure_result(error)
    assert code == 1 and record["schema_lock_result"] is None
    assert "private" not in json.dumps(record)


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "busy",
        "schema_drift",
        "process_exit",
        "journal_changed",
        "admission_failed",
        "history_failed_after_sql",
        "admission_changed_after_sql",
        "stream_open",
    ],
)
def test_complete_running_verifier_preserves_native_sql_and_admission_gates(
    tmp_path, monkeypatch, fault
):
    import core.export_deployment_handoff as handoff
    import core.export_process_identity as processes
    import core.export_startup_windows as windows
    import kvk.dal.new_source_admin_dal as admin
    from scripts.read_k98_startup_evidence import (
        StartupHistoryRefused,
        check_admission,
        failure_record,
    )
    from scripts.verify_k98_running_release import verify

    rows, config, journal = session_fixture()
    state = tmp_path / "state"
    state.mkdir()
    name = "incarnation-00000000000000000107-40000000-0000-0000-0000-000000000004.json"
    path = state / name
    journal.update(
        sequence=107,
        policy_sha256="p",
        bindings={role: dict(pid=pid) for role, pid in (("authority", 1), ("bot", 2))},
    )
    journal["publication"].update(plan_sha256="plan", version=1)
    journal["publication"]["manifests"]["bot"] = "d" * 64
    previous = config["old_journal"]["Record"]
    previous["sequence"] = 106
    config.update(
        release_id="r",
        target="t",
        new_state_directory=str(state),
        new_policy_sha256="p",
        old_policy=dict(StateDirectory=str(tmp_path / "old")),
        expected_preparation=[],
        expected_resources=[],
        account="fixture",
        host="MINI_AMD",
    )
    config["old_journal"].update(Path=str(tmp_path / "previous.json"), SHA256="previous")
    publication = tmp_path / "runtime" / "40000000-0000-0000-0000-000000000004"
    policy = dict(
        state_directory=str(state), seed_plan=dict(path=str(tmp_path / "seed.json"), sha256="seed")
    )
    profile = dict(
        stage=str(tmp_path), journal_name=name, journal_sha256="journal", start_sha256="start"
    )
    records = {
        str(path): journal,
        config["old_journal"]["Path"]: previous,
        policy["seed_plan"]["path"]: dict(
            commit_file=str(tmp_path / "runtime" / "seed" / "commit.json")
        ),
        str(publication / "commit.json"): journal["publication"],
        str(publication / "ManualProcessPairPlan-CANDIDATE.json"): dict(
            manifests={
                "authority": str(tmp_path / "authority.json"),
                "bot": str(tmp_path / "bot.json"),
            }
        ),
        str(tmp_path / "authority.json"): {},
        str(tmp_path / "bot.json"): {},
        str(publication / "AutomaticIssuer.json"): dict(
            version=1, plan_sha256="plan", issuer=dict(pid=3)
        ),
        str(tmp_path / "start-requested.json"): dict(release_id="r"),
    }
    path.write_text(json.dumps(journal))
    monkeypatch.setattr(windows, "administrative_path", lambda p, **kw: Path(p))
    handles = [Mock() for _ in range(3)]
    monkeypatch.setattr(processes, "open_pinned_process", lambda pid, binding: handles[pid - 1])
    monkeypatch.setattr(windows, "signalled", lambda h: fault == "process_exit")
    termination = Mock()
    monkeypatch.setattr(handoff, "RecordedTermination", lambda *a: termination)
    connections = []
    acquisitions = []

    class RawCursor:
        description = None

        def execute(self, sql, *args):
            if "dm_exec_sessions" in sql:
                self.answer = ("NoLock", "NoLock", 2)
            elif "sp_getapplock" in sql:
                acquisitions.append(sql)
                self.answer = (-1 if fault == "busy" else 0,)
            elif "sp_releaseapplock" in sql:
                self.answer = (0, "NoLock")
            elif "ExportExecutionStream" in sql:
                self.description = [("SessionID",), ("State",)]
                self.values = (
                    [("00000000-0000-0000-0000-000000000001", "open")]
                    if fault == "stream_open"
                    else []
                )
            elif "ExportExecutionSession" in sql:
                self.description = [(key,) for key in rows[0]]
                self.values = [tuple(row.values()) for row in rows]
            elif "ExportPreparation" in sql:
                self.description = []
                self.values = []
            elif sql != "SET LOCK_TIMEOUT 0":
                raise AssertionError(sql)

        def fetchone(self):
            return self.answer

        def fetchmany(self, limit):
            return self.values

        def close(self):
            pass

    def connect(**kw):
        assert kw == dict(sql_profile="application")
        connection = Mock()
        connection.cursor.side_effect = RawCursor
        connections.append(connection)
        return connection

    monkeypatch.setattr(admin, "configured_connection", connect)

    def sql(config, policy, connection_factory):
        connection = connection_factory()
        cursor = connection.cursor()
        with schema_observation(cursor):
            if fault == "schema_drift":
                raise SourceConflict("catalogue drift")
        if fault == "journal_changed":
            (state / "incarnation-extra.json").write_text("{}")
        return dict(actual="compared actual catalogue")

    def admission(*args, **kwargs):
        if fault == "admission_failed":
            raise ValueError("initial admission failed")
        return dict(outcome="installed")

    pair = dict(
        read=lambda p, digest=None: json.dumps(records[str(p)]).encode(),
        startup_admission_result=admission,
        bot_from_policy=lambda p: dict(sql_contract=dict(profile="application")),
        verify_sql_contracts=sql,
    )
    observe = Mock(return_value=dict(raw=b"fixture startup", evidence=dict(fixture=True)))
    startup_reader = dict(
        observe=observe,
        check_admission=check_admission,
        StartupHistoryRefused=StartupHistoryRefused,
        failure_record=failure_record,
    )
    if fault == "history_failed_after_sql":
        observe.side_effect = [observe.return_value, ValueError("later log failure")]
    if fault == "admission_changed_after_sql":
        pair["startup_admission_result"] = Mock(side_effect=[dict(outcome="installed"), {}])
    if fault:
        with pytest.raises((SourceConflict, ValueError)) as caught:
            verify(profile, config, pair, policy, startup_reader=startup_reader)
        if fault == "admission_changed_after_sql":
            from scripts.verify_k98_running_release import failure_result

            code, record = failure_result(caught.value, startup_reader=startup_reader)
            assert code == 1 and record["verified"] is False and record["retry"] is False
            assert record["startup_observation"]["failure_category"] == "admission_changed"
            assert record["startup_observation"]["evidence"] == dict(fixture=True)
    else:
        result = verify(profile, config, pair, policy, startup_reader=startup_reader)
        assert result["stage"] == "RUNNING_RELEASE_VERIFIED" and result["session_id"] == "new"
        assert result["provider_delivery_verified"] is False
        assert observe.call_count == 2
        assert (
            result["startup_evidence_before"]
            == result["startup_evidence_after"]
            == dict(fixture=True)
        )
    assert len(acquisitions) == (0 if fault == "admission_failed" else 1)
    for connection in connections:
        connection.close.assert_called_once()
    for handle in handles:
        handle.Close.assert_called_once()
    termination.verify.assert_called_once()


def profile():
    release = "10000000-0000-0000-0000-000000000001"
    value = dict(
        version=2,
        kind="running_release_verification_v1",
        host="MINI_AMD",
        sid="S-1-5-21-1-2-3-1001",
        release_id=release,
        target="a" * 40,
        work=r"C:\ProgramData\K98\S11\updates\20000000-0000-0000-0000-000000000002",
        stage=r"C:\ProgramData\K98\S11\automatic-startup\30000000-0000-0000-0000-000000000003\release-"
        + release,
        journal_name="incarnation-00000000000000000107-40000000-0000-0000-0000-000000000004.json",
        original_retirement_path=r"C:\ProgramData\K98\S11\updates\retirements\50000000-0000-0000-0000-000000000005\complete.json",
        receipts={name: "b" * 64 for name in RECEIPTS},
        startup_log_anchor=dict(sha256="d" * 64, bytes=3000000, offset=2383156),
    )
    value.update(
        {
            name + "_sha256": "c" * 64
            for name in (
                "active",
                "bindings",
                "manifest",
                "start",
                "journal",
                "original_retirement",
                "failure_evidence",
            )
        }
    )
    return value


@pytest.mark.parametrize("damage", ["path", "extra", "receipt", "hash", "retired", "type"])
def test_packet_refuses_unreviewed_profile(damage):
    p = profile()
    if damage == "path":
        p["stage"] += r"\..\escape"
    elif damage == "extra":
        p["force"] = True
    elif damage == "receipt":
        p["receipts"]["start.complete.json"] = "b" * 64
    elif damage == "hash":
        p["bindings_sha256"] = "wrong"
    elif damage == "type":
        p["version"] = True
    else:
        p["original_retirement_path"] = p["original_retirement_path"].replace(
            "50000000-0000-0000-0000-000000000005", p["release_id"]
        )
    with pytest.raises(ValueError):
        validate_profile(p)


def test_complete_packet_authenticates_every_member_and_preserves_input():
    p = profile()
    before = deepcopy(p)
    raw, sealed = build(p, ROOT)
    assert p == before
    payload = json.loads(
        base64.b64decode(re.search(rb"FromBase64String\('([A-Za-z0-9+/=]{100,})'\)", raw)[1])
    )
    for name, digest in sealed["members"].items():
        assert hashlib.sha256(base64.b64decode(payload[name])).hexdigest() == digest
    assert json.loads(base64.b64decode(payload["profile.json"])) == sealed
    assert b"__PROFILE_HASH__" not in raw and b"__PAYLOAD__" not in raw
    assert b"Run the normal updater" not in raw


@pytest.mark.parametrize("result", [-1, -2, -3, -999])
def test_acknowledged_schema_refusal_retains_exact_code_and_never_retries(result):
    cursor = Mock()
    cursor.fetchone.side_effect = [("NoLock", "NoLock", 2), (result,)]
    with pytest.raises(SchemaObservationRefused) as caught:
        with schema_observation(cursor):
            pytest.fail("No schema query may follow refusal")
    assert isinstance(caught.value, SourceConflict) and caught.value.result == result
    assert cursor.execute.call_count == 2
    assert not any("sp_releaseapplock" in call.args[0] for call in cursor.execute.call_args_list)


def test_observation_factory_uses_fresh_zero_wait_connections_and_one_close():
    raw = Mock()
    raw.cursor.return_value = Mock()
    factory = ObservationConnections(lambda: raw)
    owner = factory()
    assert raw.timeout == 3 and raw.autocommit is True
    raw.cursor.return_value.execute.assert_called_once_with("SET LOCK_TIMEOUT 0")
    owner.close()
    factory.close()
    assert raw.close.call_count == 1 and raw.cursor.return_value.close.call_count == 1


@pytest.mark.parametrize("phase", ["cursor", "connection", "setup"])
def test_cleanup_failure_never_retries_close_or_becomes_verified(phase):
    from core.sql_connection_custody import SqlCleanupUnknown

    raw = Mock()
    cursor = raw.cursor.return_value
    factory = ObservationConnections(lambda: raw)
    if phase == "setup":
        cursor.execute.side_effect = RuntimeError("setup failed")
    if phase == "cursor":
        cursor.close.side_effect = RuntimeError("lost cursor close")
    if phase == "connection":
        raw.close.side_effect = RuntimeError("lost connection close")
    if phase in {"setup", "cursor"}:
        with pytest.raises(RuntimeError):
            factory()
    else:
        factory()
    if phase == "setup":
        factory.close()
    else:
        with pytest.raises(SqlCleanupUnknown):
            factory.close()
        with pytest.raises(SqlCleanupUnknown):
            factory.close()
    assert raw.close.call_count == 1 and cursor.close.call_count == 1


def test_total_observation_budget_and_statement_limit_prevent_next_dispatch():
    now = [0]
    raw = Mock()
    factory = ObservationConnections(lambda: raw, clock=lambda: now[0])
    owner = factory()
    cursor = owner.cursor()
    factory.statements = 256
    with pytest.raises(VerificationBudgetExceeded):
        cursor.execute("SELECT 1")
    factory.statements = 0
    now[0] = 46
    with pytest.raises(VerificationBudgetExceeded):
        cursor.execute("SELECT 1")
    assert raw.cursor.return_value.execute.call_count == 1
    factory.close()


def session_fixture():
    then = datetime(2026, 11, 18, 19)
    config = dict(
        old_session=dict(SessionID="old", Version=1),
        old_journal=dict(Record=dict(publication=dict(manifests=dict(authority="a" * 64)))),
    )
    journal = dict(publication=dict(manifests=dict(authority="b" * 64)))
    common = dict(AuthorityPrincipal="S11_ExportApplication", HostIdentity="mini_AMD")
    rows = [
        dict(
            common,
            SessionID="old",
            State="closed",
            Version=2,
            ManifestHash="A" * 64,
            CreatedUTC=then,
            ClosedUTC=then + timedelta(seconds=1),
        ),
        dict(
            common,
            SessionID="new",
            State="open",
            Version=1,
            ManifestHash="B" * 64,
            CreatedUTC=then + timedelta(seconds=2),
            ClosedUTC=None,
        ),
    ]
    return rows, config, journal


@pytest.mark.parametrize(
    "damage", [None, "extra", "open_old", "manifest", "principal", "overlap", "version", "closed"]
)
def test_sessions_require_closed_predecessor_and_exact_single_successor(damage):
    rows, config, journal = session_fixture()
    if damage == "extra":
        rows.append(deepcopy(rows[-1]))
    elif damage == "open_old":
        rows[0]["State"] = "open"
    elif damage == "manifest":
        rows[1]["ManifestHash"] = "c" * 64
    elif damage == "principal":
        rows[1]["AuthorityPrincipal"] = "other"
    elif damage == "overlap":
        rows[0]["ClosedUTC"] = rows[1]["CreatedUTC"] + timedelta(seconds=1)
    elif damage == "version":
        rows[1]["Version"] = 2
    elif damage == "closed":
        rows[1]["ClosedUTC"] = rows[1]["CreatedUTC"]
    if damage:
        with pytest.raises(ValueError):
            verify_sessions(rows, config, journal)
    else:
        assert verify_sessions(rows, config, journal) == "new"


@pytest.mark.parametrize(
    "damage", [None, "preparation", "resource", "foreign_stream", "closure", "overlap", "shape"]
)
def test_retained_work_requires_unchanged_ownership_and_contained_closure(damage):
    from scripts.verify_k98_running_release import verify_retained_work

    identity = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    preparation = dict(PreparationID=identity, State="uncertain", Version=3)
    resource = dict(ResourceKey="sheet", ActivePreparationID=identity, OwnerID=identity, Fence=7)
    config = dict(
        account="fixture",
        host="MINI_AMD",
        expected_preparation=[preparation],
        expected_resources=[resource],
    )
    observed_preparation = dict(preparation, PreparationID=identity.upper())
    observed_resource = dict(resource, OwnerID=identity.upper())
    then = datetime(2026, 11, 18, 19)
    stream = dict(
        StreamID=identity,
        SessionID=identity,
        State="read_contained",
        Purpose="probe",
        PreparationID=identity,
        JobID=None,
        OutputOperationID=None,
        NestedToken=None,
        Epoch=None,
        ActiveAccountKey=None,
        SessionState="closed",
        HostIdentity="mini_AMD",
        CreatedUTC=then,
        ClosedUTC=then + timedelta(seconds=1),
        SessionClosedUTC=then + timedelta(seconds=2),
        ClosureReference="retained",
        ClosureHash=b"a" * 32,
        EventDigest=b"b" * 32,
    )
    if damage == "preparation":
        observed_preparation["Version"] = 4
    elif damage == "resource":
        observed_resource["Fence"] = 8
    elif damage == "foreign_stream":
        stream["State"] = "open"
    elif damage == "closure":
        stream["ClosureHash"] = b"short"
    elif damage == "overlap":
        stream["SessionClosedUTC"] = then
    elif damage == "shape":
        stream["JobID"] = identity

    class RetainedCursor:
        def execute(self, sql, parameter):
            assert parameter in {"fixture", identity}
            self.rows = (
                [observed_preparation]
                if "ExportPreparation" in sql
                else [observed_resource] if "ExportResource" in sql else [stream]
            )
            self.description = [(key,) for key in self.rows[0]]

        def fetchmany(self, limit):
            assert limit == 129
            return [tuple(row.values()) for row in self.rows]

    if damage:
        with pytest.raises(ValueError):
            verify_retained_work(RetainedCursor(), config, "successor")
    else:
        verify_retained_work(RetainedCursor(), config, "successor")


def test_retained_inventory_refuses_overflow():
    from scripts.verify_k98_running_release import bounded_rows

    cursor = Mock(description=[("State",)])
    cursor.fetchmany.return_value = [("open",)] * 129
    with pytest.raises(ValueError, match="exceeds bound"):
        bounded_rows(cursor)


@pytest.mark.skipif(os.name != "nt", reason="PowerShell 5.1 generated-packet parser")
def test_complete_generated_packet_parses_in_powershell_51(tmp_path):
    packet = tmp_path / "packet.ps1"
    packet.write_bytes(build(profile(), ROOT)[0])
    script = tmp_path / "parse.ps1"
    script.write_text(
        "param($Path)\n$tokens=$null;$errors=$null\n$null=[System.Management.Automation.Language.Parser]::ParseFile($Path,[ref]$tokens,[ref]$errors)\nif($errors.Count){$errors|Out-String|Write-Error;exit 1}\n"
    )
    result = subprocess.run(
        [PS, "-NoProfile", "-NonInteractive", "-File", str(script), str(packet)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(os.name != "nt", reason="Actual PowerShell historical evidence gate")
@pytest.mark.parametrize(
    "damage", ["none", "active", "manifest", "extra_receipt", "readiness", "drain", "seed"]
)
def test_native_evidence_gate_preserves_exact_original_stage_boundary(tmp_path, damage):
    script = tmp_path / "evidence.ps1"
    script.write_text(r"""
param($Root,$Damage)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $Root 'scripts/K98-VerifyRunningRelease.ps1')
$profile=[pscustomobject]@{active_sha256='a';release_id='r';work='C:\work';stage='C:\state\release-r';bindings_sha256='b';manifest_sha256='m';sid='s';host='MINI_AMD';target='t';receipts=[pscustomobject]@{'source.intent.json'='si';'source.complete.json'='sc';'seed.intent.json'='ei';'seed.complete.json'='ec';'start.intent.json'='ti'};start_sha256='s';original_retirement_path='C:\retired.json';original_retirement_sha256='r'}
$config=[pscustomobject]@{release_id='r';target='t';sid='s';host='MINI_AMD';root='C:\discord_file_downloader';new_state_directory='C:\new';new_seed_directory='C:\seed';old_policy=[pscustomobject]@{StateDirectory='C:\state';SHA256='policy'};old_journal=[pscustomobject]@{Record=[pscustomobject]@{sequence=106;publication='pub'}}}
function Read-RetirementBytes {return ,([byte[]]@(1))}
function Read-RetirementJson($Path,$Expected='') {
 $leaf=Split-Path -Leaf $Path
 switch($leaf) {
 'active.json' {return [pscustomobject]@{release_id=$(if($Damage -ceq 'active'){'different'}else{'r'});directory='C:\work'}}
 'ReleaseBindings.json' {return $config}
 'release.json' {return [pscustomobject]@{version=4;release_id='r';steps=@('source','seed','start','readiness')|ForEach-Object{[pscustomobject]@{id=$_;kind=$(if($Damage -ceq 'manifest'){'sql'}else{$_})}}}}
 'retired.json' {return [pscustomobject]@{kind='retired_without_verified_readiness'}}
 'deployment-request.json' {return [pscustomobject]@{release_id='r';policy_sha256='policy';sequence=106;publication='pub'}}
 'deployment-drained-r.json' {return [pscustomobject]@{stage='deployment_drained';release_id='r';request_sha256=$(if($Damage -ceq 'drain'){'different'}else{'hash'});previous=$config.old_journal.Record}}
 default {$parts=$leaf.Split('.');return [pscustomobject]@{release_id='r';step=$parts[0];stage=$(if($parts[1] -ceq 'complete'){'verified'}else{'starting'})}}
 }
}
function Get-ChildItem {
 $names=@('source.intent.json','source.complete.json','seed.intent.json','seed.complete.json','start.intent.json')
 if($Damage -ceq 'extra_receipt'){$names+='start.complete.json'}
 foreach($name in $names){[pscustomobject]@{Name=$name;PSIsContainer=$false}}
}
function Test-Path {return ($Damage -ceq 'readiness')}
function Same($A,$B) {return (($A|ConvertTo-Json -Compress) -ceq ($B|ConvertTo-Json -Compress))}
function Hash {return 'hash'}
function Seed-Complete {return ($Damage -cne 'seed')}
function Get-RetirementRuntime {return [pscustomobject]@{policy='policy'}}
function Assert-RetirementSource {}
$null=Assert-RunningReleaseEvidence $profile
""")
    result = subprocess.run(
        [PS, "-NoProfile", "-NonInteractive", "-File", str(script), str(ROOT), damage],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert (result.returncode == 0) == (damage == "none"), result.stdout + result.stderr


@pytest.mark.skipif(os.name != "nt", reason="PowerShell 5.1 parser and actual classification")
@pytest.mark.parametrize(
    "warning,expected",
    [
        (
            "Export coordinator unavailable error_type=ObservationBusy",
            "fresh_import_export_health_evidence_unavailable",
        ),
        (
            "Export coordinator unavailable error_type=SourceConflict",
            "runtime_admission_unavailable",
        ),
        ("Export coordinator unavailable", "runtime_admission_unavailable"),
        (
            "Export coordinator unavailable error_type=ObservationBusyFake",
            "runtime_admission_unavailable",
        ),
        ("S11 export admission remains closed", "runtime_admission_unavailable"),
    ],
)
def test_native_readiness_distinguishes_observer_contention(tmp_path, warning, expected):
    script = tmp_path / "classify.ps1"
    script.write_text(
        "param($Root,$Warning)\n. (Join-Path $Root 'scripts/K98-SourceUpdate.ps1') -Action Library\n(Import-ExportStatus $Warning).reason\n"
    )
    result = subprocess.run(
        [PS, "-NoProfile", "-NonInteractive", "-File", str(script), str(ROOT), warning],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected


@pytest.mark.skipif(os.name != "nt", reason="Actual PowerShell verification-only orchestration")
@pytest.mark.parametrize(
    "outcome,answer,drift",
    [(0, True, 0), (12, True, 0), (1, True, 0), (0, False, 0), (0, True, 3), (0, True, 4)],
)
def test_native_orchestration_cannot_restart_replay_or_accept_failed_verification(
    tmp_path, outcome, answer, drift
):
    # Only the external reads and verifier process are substituted. Execute the
    # real orchestration, persistence, lock scopes and post-verification branches.
    raw = (ROOT / "scripts/K98-VerifyRunningRelease.ps1").read_text()
    # Redirect only the fixed updates root into this isolated fixture.
    raw = raw.replace("$updates='C:\\ProgramData\\K98\\S11\\updates'", "$updates=$Fixture")
    (tmp_path / "operator.lock").write_bytes(b"")
    stage = tmp_path / "release"
    stage.mkdir()
    (tmp_path / "deployment-r.lock").write_bytes(b"")
    (tmp_path / "original.intent.json").write_bytes(b"immutable first failure")
    probe = tmp_path / "Verify-RunningRelease.py"
    probe.write_text(
        "import json,sys\nfrom pathlib import Path\nPath(__file__).with_suffix('.called').write_text('once')\nprint(json.dumps(dict(stage='RUNNING_RELEASE_VERIFIED',release_id='r',target='t',sequence=107,provider_delivery_verified=False,retry=False)))\nsys.exit("
        + str(outcome)
        + ")\n"
    )
    fixture = tmp_path / "harness.ps1"
    fixture.write_text(
        r"""
param($Root,$Fixture,$Python,[int]$Drift,[string]$Answer)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $Root 'scripts/K98-SourceUpdate.ps1') -Action Library
. (Join-Path $Root 'scripts/K98-FailedReadiness.ps1')
"""
        + raw
        + r"""
$profile=[pscustomobject]@{stage=(Join-Path $Fixture 'release');release_id='r';target='t';work=$Fixture;sid='fixture';members=@{};start_sha256='hash';failure_evidence_sha256='hash'}
$script:checks=0
function Assert-RunningReleaseEvidence {
 $script:checks++
 if($Drift -and $script:checks -eq $Drift){throw 'identity changed'}
 $script:c=[pscustomobject]@{venv=[pscustomobject]@{path=$Python;sha256='fixture'}}
 return [pscustomobject]@{processes=@();journal=[pscustomobject]@{sequence=107}}
}
function Open-RetirementProcesses {return ,@()}
function Assert-RetirementProcesses {}
function Read-RetirementBytes($Path,$Expected='', $Limit=0){if(Test-Path -LiteralPath $Path){return ,([IO.File]::ReadAllBytes($Path))};return ,([byte[]]@(1))}
function Read-RetirementJson {return [pscustomobject]@{log_offset=0}}
function Read-RunningStartupText {$script:runningStartupObservationHash='fixture';return "Logged in as fixture`n[BOOT] full_startup_sequence completed successfully`nExport coordinator unavailable error_type=ObservationBusy"}
function Read-Host {return $Answer}
function Write-RetirementBytes($Path,$Bytes){[IO.File]::WriteAllBytes($Path,$Bytes)}
function ApplyStart {throw 'FORBIDDEN'}
function Start-ScheduledTask {throw 'FORBIDDEN'}
function Assert-Drained {throw 'FORBIDDEN'}
Invoke-RunningReleaseVerification $profile 'profile' $Fixture
"""
    )
    # Drive the parameterized fixture through a literal, quoted wrapper.
    driver = tmp_path / "driver.ps1"
    q = lambda s: "'" + str(s).replace("'", "''") + "'"
    driver.write_text(
        f"& {q(fixture)} -Root {q(ROOT)} -Fixture {q(tmp_path)} -Python {q(sys.executable)} -Drift {drift} -Answer {q('CONFIRM ONLINE' if answer else '')}\n"
    )
    result = subprocess.run(
        [PS, "-NoProfile", "-NonInteractive", "-File", str(driver)],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert (result.returncode != 0) == bool(outcome == 1 or drift), result.stdout + result.stderr
    assert (tmp_path / "verified.json").exists() == bool(outcome == 0 and answer and not drift)
    assert probe.with_suffix(".called").exists() == answer
    assert len(list(tmp_path.glob("attempt-*.json"))) == int(answer)
    assert (tmp_path / "original.intent.json").read_bytes() == b"immutable first failure"
