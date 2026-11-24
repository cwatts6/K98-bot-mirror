"""Continue only the unaccepted read; never replay the committed lab install."""

import base64
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time


def unprotect(blob):
    command = (
        "$ErrorActionPreference='Stop';"
        "[void][Reflection.Assembly]::Load('System.Security, Version=4.0.0.0, "
        "Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a');"
        "[Console]::Out.Write([Text.Encoding]::UTF8.GetString("
        "[Security.Cryptography.ProtectedData]::Unprotect("
        "[Convert]::FromBase64String([Console]::In.ReadToEnd()),$null,"
        "[Security.Cryptography.DataProtectionScope]::CurrentUser)))"
    )
    result = subprocess.run(
        [
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
        ],
        input=base64.b64encode(blob).decode(),
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode or not 32 <= len(result.stdout) <= 128:
        raise ValueError("Private retained lab credential unavailable")
    return result.stdout


def main():
    packet = Path(__file__).resolve().parents[2]
    manifest = json.loads((packet / "manifest.json").read_bytes())
    if (
        os.environ.get("COMPUTERNAME") != "MINI_AMD"
        or manifest["stage"] != "restored-application-observer"
        or manifest["continuation"]["guest_directory"] != r"Q:\P02Observer\20261120131206690"
        or manifest["production_eligible"] is not False
    ):
        raise ValueError("Exact lab continuation required")
    for name, digest in manifest["files"].items():
        path = (packet / name).resolve()
        if (
            not path.is_relative_to(packet)
            or hashlib.sha256(path.read_bytes()).hexdigest() != digest
        ):
            raise ValueError("Sealed continuation member differs")
    setup = runpy.run_path(str(packet / "qualification/p02_observer/application_setup.py"))
    read, execute, sha, encode = (setup[k] for k in ("read", "execute", "sha", "encode"))
    sys.path[:0] = [str(packet / "bot"), r"C:\discord_file_downloader\venv\Lib\site-packages"]
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"
    import pyodbc

    from kvk.dal.new_source_import_dal import SourceConflict
    from services.application_observation_admission import AdmissionBinding, AdmissionMetadata
    from services.catalogue_observation_contract import reviewed_protocol_modules
    from services.catalogue_observation_dal import BOUNDARY_SQL
    from services.export_observer_contract import observation_record

    pyodbc.pooling = False
    budget = runpy.run_path(str(packet / "Verify-RunningRelease.py"))
    receipt = dict(
        schema="p02-observer-application-continuation/1",
        started=datetime.now(UTC).isoformat(),
        production_operations=0,
        business_operations=0,
        installation_replayed=False,
        stages=[],
        connections_closed=0,
    )

    def save(name, value):
        with (packet / name).open("x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, default=str)

    def stage(name, **facts):
        receipt["stages"].append(dict(name=name, **facts))
        save("stage-" + str(len(receipt["stages"])) + ".json", receipt["stages"][-1])

    class RecordedAdmission(AdmissionMetadata):
        def _save(self, cursor, observation):
            # Retain exact native rows before a comparator may reject them.
            save(
                "cold-application-observation.json",
                dict(observation=observation.value, boundary=observation_record(observation)),
            )
            return super()._save(cursor, observation)

    principal = manifest["principal"]
    base = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=lpc:localhost;Encrypt=yes;TrustServerCertificate=yes;DATABASE=ROK_TRACKER;"
    admin = owner = password = None
    login_verified = False
    failed = False
    try:
        continuation = manifest["continuation"]
        blob = (Path(continuation["guest_directory"]) / "lab-credential.dpapi").read_bytes()
        assert sha(blob) == continuation["credential_sha256"]
        password = unprotect(blob)
        admin = pyodbc.connect(base + "Trusted_Connection=yes", autocommit=True, timeout=5)
        admin.timeout = 3
        execute(admin, "SET NOCOUNT ON; SET LOCK_TIMEOUT 0")
        execute(admin, setup["GUARD_SQL"])
        assert sha(encode(read(admin, setup["HISTORY_SQL"]))) == manifest["history_sha256"]
        snapshot = read(
            admin,
            f"SELECT name,source_database_id,state_desc,is_read_only FROM sys.databases WHERE name='{manifest['snapshot']}'",
        )
        assert len(snapshot) == 1 and snapshot[0]["source_database_id"] == 12
        assert snapshot[0]["state_desc"] == "ONLINE" and snapshot[0]["is_read_only"]
        login = read(
            admin,
            f"SELECT name,is_disabled FROM sys.sql_logins WHERE name='{principal}' AND sid=0x{manifest['login_sid']}",
        )
        assert len(login) == 1 and login[0]["is_disabled"]
        login_verified = True
        observed = read(admin, setup["IDENTITY_SQL"])
        binding = continuation["binding"]
        assert len(observed) == 1
        identity = observed[0]
        assert identity["database_id"] == binding["database_id"]
        assert identity["sequence_object_id"] == binding["sequence_object_id"]
        assert (
            identity["sequence_created"].isoformat(timespec="microseconds")
            == binding["sequence_created"]
        )
        assert (
            identity["sequence_modified"].isoformat(timespec="microseconds")
            == binding["sequence_modified"]
        )
        assert identity["generation"] == 1
        stage("committed-fixture-reused", binding=binding, snapshot=snapshot)
        if "grant_repair" in manifest:
            repair = json.loads(
                (packet / "qualification/p02_observer/lab-grant-repair.json").read_bytes()
            )
            assert repair["grant_count"] == manifest["grant_repair"]["grants"] == 126
            assert repair["objects"] == manifest["grant_repair"]["objects"] == 62
            assert len(repair["batches"]) == 8
            execute(
                admin,
                "IF NOT EXISTS(SELECT 1 FROM sys.database_principals "
                f"WHERE name=N'{principal}' AND sid=0x{manifest['login_sid']}) "
                "THROW 51973,'Exact lab user binding required.',1;",
            )
            deadline = time.monotonic() + 20
            execute(admin, "BEGIN TRANSACTION")
            try:
                for statement in repair["batches"]:
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Bounded lab grant setup expired")
                    execute(admin, statement)
                execute(admin, "COMMIT TRANSACTION")
            except BaseException:
                execute(admin, "IF @@TRANCOUNT>0 ROLLBACK TRANSACTION")
                raise
            # Record commit before any subsequent read/comparison can fail.
            stage(
                "application-grants-commit-acknowledged",
                grants=repair["grant_count"],
                objects=repair["objects"],
                profile_sha256=repair["profile_sha256"],
            )
            after = read(admin, setup["IDENTITY_SQL"])
            assert len(after) == 1 and after[0]["generation"] > identity["generation"]
            assert {k: v for k, v in after[0].items() if k != "generation"} == {
                k: v for k, v in identity.items() if k != "generation"
            }
            stage("grant-invalidation-confirmed", generation=after[0]["generation"])
        execute(admin, f"ALTER LOGIN [{principal}] ENABLE")
        approved = dict(manifest["approved"], observation_installation=binding)
        modules = reviewed_protocol_modules()
        context = AdmissionBinding(
            sha(b"lab-read-only-claim"),
            sha(b"lab-config"),
            sha(b"lab-registration"),
            sha(encode(approved)),
            sha(encode(modules)),
        )
        owner = budget["ObservationConnections"](
            lambda: pyodbc.connect(
                base + f"UID={principal};PWD={{{password}}}", autocommit=True, timeout=5
            )
        )
        with owner:
            owner.observation_phase("application")
            origin = owner().cursor()
            with RecordedAdmission(
                context, approved=approved, expected_modules=modules
            ) as evidence:
                started = time.perf_counter()
                evidence.collect(origin)
                stage(
                    "complete-application-observation",
                    seconds=time.perf_counter() - started,
                    dispatches=owner.statements,
                    scope_names=487,
                )
                producer = owner().cursor()
                producer.execute("BEGIN TRANSACTION")
                entry_start = len(owner.observations)
                started = time.perf_counter()
                reused = evidence.consume(producer, context)
                seconds = time.perf_counter() - started
                entry = owner.observations[entry_start:]
                producer.execute("SELECT @@TRANCOUNT,XACT_STATE()")
                assert tuple(producer.fetchone()) == (1, 1)
                producer.execute("ROLLBACK TRANSACTION")
                assert sum(row["sql_sha256"] == sha(BOUNDARY_SQL.encode()) for row in entry) == 2
                save(
                    "application-observation.json",
                    dict(observation=reused.value, boundary=observation_record(reused)),
                )
                stage(
                    "same-admission-reuse",
                    seconds=seconds,
                    dispatches=len(entry),
                    boundary_reads=2,
                    borrowed_transaction_preserved=True,
                )
        assert sha(encode(read(admin, setup["HISTORY_SQL"]))) == manifest["history_sha256"]
        receipt["outcome"] = "passed"
    except BaseException as error:
        failed = True
        receipt.update(outcome="failed", failure=budget["sql_error_facts"](error))
        if isinstance(error, SourceConflict):
            receipt["failure"]["contract_reason"] = str(error)[:1000]
    finally:
        if admin is not None:
            if login_verified:
                try:
                    execute(admin, f"ALTER LOGIN [{principal}] DISABLE")
                    state = read(
                        admin,
                        f"SELECT name,is_disabled FROM sys.sql_logins WHERE name='{principal}' AND sid=0x{manifest['login_sid']}",
                    )
                    assert len(state) == 1 and state[0]["is_disabled"]
                    receipt["lab_login_cleanup"] = state
                except BaseException as error:
                    failed = True
                    receipt["login_cleanup_failure"] = type(error).__name__
            try:
                admin.close()
                receipt["connections_closed"] += 1
            except BaseException as error:
                failed = True
                receipt["admin_cleanup_failure"] = type(error).__name__
        password = None
        if owner is not None:
            receipt["owner"] = owner.evidence()
            receipt["connections_closed"] += sum(c.closed for c in owner.connections)
        receipt["finished"] = datetime.now(UTC).isoformat()
        if failed:
            receipt["outcome"] = "failed"
        save("receipt.json", receipt)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
