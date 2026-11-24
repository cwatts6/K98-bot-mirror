"""Two read-only boundary calls in the existing, isolated P02 proof database.

Executed as the sealed representative entry point. This qualifies source and
installation binding, not a deployment contract or whole-caller acceptance.
"""

from dataclasses import asdict
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import time

APPLICATION_CONTEXT_SQL = (
    "SET TRANSACTION ISOLATION LEVEL READ COMMITTED; SET NOCOUNT ON; "
    "SET ANSI_NULLS ON; SET QUOTED_IDENTIFIER ON; "
    "EXECUTE AS LOGIN='S11_ExportApplication_P02Qual'"
)


def prove(owner, binding, generation, save):
    """Exercise the real owner and comparison with exactly two boundary reads."""
    from services.catalogue_observation_contract import ObservationInstallation
    from services.catalogue_observation_dal import ObservationContractError, read_boundary

    installation = ObservationInstallation(binding)
    modules = dict(installation.modules)
    timings = []
    with owner:
        owner.observation_phase("application")
        cursor = owner().cursor()
        cursor.execute(APPLICATION_CONTEXT_SQL)
        while cursor.nextset():
            raise AssertionError("Unexpected context setup result")
        started = time.perf_counter()
        observed = read_boundary(cursor, modules, installation=installation)
        timings.append(time.perf_counter() - started)
        assert observed.generation == generation
        save(
            "progress.json",
            dict(stage="protected-first-boundary-passed", boundary=asdict(observed)),
        )
        # Challenge the expected document, never the SQL object. A fresh process
        # must not silently learn and adopt its current sequence identity.
        wrong = dict(binding, sequence_object_id=binding["sequence_object_id"] + 1)
        wrong_installation = ObservationInstallation(wrong)
        started = time.perf_counter()
        try:
            read_boundary(cursor, modules, installation=wrong_installation)
        except ObservationContractError as error:
            assert str(error) == "Observation differs from protected target/sequence installation."
        else:
            raise AssertionError("Unapproved installation accepted")
        timings.append(time.perf_counter() - started)
    assert owner.first_failure is None
    assert len(owner.connections) == 1 and all(c.closed for c in owner.connections)
    assert owner.statements == 4  # Owner setup, application context, two boundaries.
    facts = dict(
        generation=observed.generation,
        boundary=asdict(observed),
        replacement_identity_refused=True,
        boundary_reads=2,
        owner_dispatches=owner.statements,
        boundary_seconds=timings,
        cleanup="acknowledged",
        complete_catalogue_repeated=False,
        whole_caller_acceptance=False,
        login_mode="Windows lab login impersonating the application login; no SQL-auth claim",
    )
    save("catalogue-cost-result.json", facts)
    assert max(timings) <= 0.250, facts
    return facts


def main():
    packet = Path(__file__).resolve().parents[2]
    manifest = json.loads((packet / "manifest.json").read_bytes())
    if (
        os.environ.get("COMPUTERNAME") != "MINI_AMD"
        or manifest["database"] != "K98_P025_D5e_Cost_20261115"
        or manifest["stage"] != "protected-observation-binding"
    ):
        raise ValueError("Exact isolated observer fixture required")
    for name, expected in manifest["files"].items():
        member = (packet / name).resolve()
        if (
            not member.is_relative_to(packet)
            or hashlib.sha256(member.read_bytes()).hexdigest() != expected
        ):
            raise ValueError("Sealed proof member differs: " + name)

    def save(name, value):
        with (packet / name).open("x", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, default=str)

    receipt = dict(
        schema="p02-observer-protected-binding/1",
        started=datetime.now(UTC).isoformat(),
        database=manifest["database"],
        checks=[],
        production_operations=0,
        business_operations=0,
        sql_object_changes=0,
        permissions_changed=0,
        scope_limit="Source-pinned installation binding only; release issuer and three-contract caller remain pending.",
    )
    owner = None
    try:
        pair = runpy.run_path(str(packet / "Verify-NewPair.py"))
        pair["activate_contract_archive"](
            packet / "contract_verifier.zip", manifest["archive_sha256"], packet / "application"
        )
        budget = runpy.run_path(str(packet / "Verify-RunningRelease.py"))
        sys.path.append(r"C:\discord_file_downloader\venv\Lib\site-packages")
        import pyodbc

        pyodbc.pooling = False
        connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};SERVER=lpc:localhost;"
            "Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;"
            "DATABASE=K98_P025_D5e_Cost_20261115"
        )
        owner = budget["ObservationConnections"](
            lambda: pyodbc.connect(connection_string, autocommit=True, timeout=5)
        )
        facts = prove(owner, manifest["installation"], manifest["generation"], save)
        receipt["checks"].append(
            dict(name="protected-first-read-and-replacement-refusal", passed=True, facts=facts)
        )
        receipt["outcome"] = "passed"
    except BaseException as error:
        receipt.update(
            outcome="failed", failure=dict(type=type(error).__name__, detail=str(error)[:2000])
        )
        raise
    finally:
        if owner is not None:
            receipt["owner"] = owner.evidence()
            receipt["connections_closed"] = sum(c.closed for c in owner.connections)
        receipt["finished"] = datetime.now(UTC).isoformat()
        first = sys.exception()
        try:
            save("receipt.json", receipt)
        except BaseException as error:
            if first is None:
                raise
            first.add_note("Receipt save also failed: " + type(error).__name__)


if __name__ == "__main__":
    main()
