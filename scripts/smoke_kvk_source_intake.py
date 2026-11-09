"""Explicit local console transport for the approved S8C disposable smoke only.

Run from the repository root with ``python -m scripts.smoke_kvk_source_intake``.
No bot startup, provider adapter, unattended watcher or database setup occurs here.
All identities are synthetic, including interactive confirmations.
"""

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from kvk.dal.new_source_admin_dal import SourceAdminDAL
from kvk.dal.source_admin_review_dal import SourceAdminReviewDAL
from kvk.services.new_source_admin_service import SourceAccess, SourceActor, SourceAdminService
from kvk.services.new_source_artifact_store import ArtifactStore
from kvk.services.source_admin_review_service import SourceAdminReviewService

SERVER = r"9SX2VF4\K98DEV"
DATABASE = "K98_S8C_Disposable_20260913_intake"
ROOT = Path("C:/K98-S8C-Smoke/20260913")
TARGET = f"{SERVER}|{DATABASE}"
ACTOR = SourceActor(10, 20, 30, frozenset())
ACCESS = SourceAccess(True, 20, 30, 10, frozenset({40}), frozenset({31}))
MAX_BYTES = 20 * 1024 * 1024


def connect():
    """Never consume environment/config connection settings or permit another target."""
    import pyodbc

    connection = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER=lpc:localhost\\K98DEV;"
        f"DATABASE={DATABASE};Trusted_Connection=yes;TrustServerCertificate=yes",
        autocommit=False,
        timeout=10,
    )
    try:
        actual = tuple(
            connection.cursor()
            .execute("SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')),DB_NAME()")
            .fetchone()
        )
        if actual != (SERVER, DATABASE):
            raise RuntimeError(f"Unexpected disposable SQL identity: {actual!r}")
        connection.rollback()
        return connection
    except BaseException:
        connection.close()
        raise


def read_workbook(inbox, relative_name):
    inbox = inbox.resolve(strict=True)
    candidate = Path(relative_name)
    if candidate.is_absolute() or candidate.drive:
        raise ValueError("Use a relative XLSX path beneath the smoke inbox.")
    path = (inbox / candidate).resolve(strict=True)
    if not path.is_relative_to(inbox) or path.suffix.lower() != ".xlsx":
        raise ValueError("Use an XLSX file beneath the smoke inbox.")
    with path.open("rb") as stream:
        content = stream.read(MAX_BYTES + 1)
    if not content or len(content) > MAX_BYTES:
        raise ValueError("Workbook must contain between 1 byte and 20 MiB.")
    return path.name, content


class FolderIntake:
    """Small transport adapter; SQL outcomes remain owned by production services."""

    def __init__(self, approved_target):
        if approved_target != TARGET:
            raise ValueError("Supply the exact approved disposable server|database.")
        for directory in (ROOT / "inbox", ROOT / "artifacts", ROOT / "evidence"):
            if not directory.is_dir() or directory.is_symlink() or directory.resolve() != directory:
                raise ValueError(f"Expected existing local smoke directory: {directory}")
        with closing(connect()):
            pass
        store = ArtifactStore(ROOT / "artifacts")
        self.intake = SourceAdminService(ACCESS, SourceAdminDAL(connect, store), store)
        self.reviews = SourceAdminReviewService(ACCESS, SourceAdminReviewDAL(connect))
        self.transcript = ROOT / "evidence" / f"console-{uuid4()}.jsonl"

    def record(self, event, value):
        entry = dict(
            event=event,
            actor="SYNTHETIC LOCAL ACTOR 10; not live operator attestation",
            value=value,
        )
        with self.transcript.open("a", encoding="utf-8") as output:
            output.write(json.dumps(entry, default=str) + "\n")

    def upload(self, season, files):
        if not isinstance(files, list) or not 1 <= len(files) <= 2:
            raise ValueError("Select one or two files explicitly.")
        # Validate every path and byte bound before retaining the first receipt.
        workbooks = [read_workbook(ROOT / "inbox", name) for name in files]
        message = str(uuid4().int)[:18]
        rows = []
        for filename, content in workbooks:
            row = self.intake.stage_upload(
                ACTOR,
                filename=filename,
                content=content,
                message_id=message,
                attachment_id=str(uuid4().int)[:18],
                season=season,
            )
            self.record(
                "upload",
                dict(filename=filename, sha256=hashlib.sha256(content).hexdigest(), row=row),
            )
            rows.append(row)
        return rows

    def action(self, operation, arguments):
        operations = {
            "receipt": self.intake.receipt,
            "metadata": self.intake.prepare_metadata,
            "window": self.intake.prepare_configuration,
            "cancel_receipt": self.intake.cancel,
            "choose_source": self.reviews.prepare_choice,
            "configuration": self.reviews.prepare_configuration,
            "match": self.reviews.prepare_match,
            "review": self.reviews.read,
            "cancel_review": self.reviews.cancel,
            "update_status": self.reviews.update_status,
        }
        if operation not in operations:
            raise ValueError("Unknown operation; confirmation uses the separate confirm operation.")
        result = operations[operation](ACTOR, **arguments)
        self.record(operation, result)
        return result

    def confirm(self, kind, identifier, version, acknowledgement):
        expected = f"CONFIRM SYNTHETIC {kind} {identifier} {version}"
        if acknowledgement != expected or kind not in ("receipt", "review"):
            raise ValueError("Explicit confirmation must name the exact kind, UUID and version.")
        service = self.intake if kind == "receipt" else self.reviews
        result = service.confirm(ACTOR, identifier, version)
        self.record(
            "explicit synthetic confirmation", dict(acknowledgement=acknowledgement, row=result)
        )
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approved-target", required=True)
    args = parser.parse_args()
    adapter = FolderIntake(args.approved_target)
    print(f"SYNTHETIC LOCAL SMOKE ONLY: {TARGET}\nEvidence: {adapter.transcript}")
    print(
        'Enter JSON {"operation": "upload", "arguments": {"season": 900001, "files": ["players.xlsx"]}}.'
    )
    print(
        "Other operations: receipt, metadata, window, choose_source, configuration, match, review,"
    )
    print(
        "cancel_receipt, cancel_review, update_status, confirm. Arguments match the production service."
    )
    print(
        "For confirm use kind, identifier, version; the console requests the exact confirmation phrase. Type quit to exit."
    )
    while True:
        try:
            line = input("S8C> ")
            if line.strip() == "quit":
                break
            command = json.loads(line)
            operation, arguments = command["operation"], command["arguments"]
            if operation == "upload":
                result = adapter.upload(**arguments)
            elif operation == "confirm":
                arguments.pop("acknowledgement", None)
                phrase = f"CONFIRM SYNTHETIC {arguments['kind']} {arguments['identifier']} {arguments['version']}"
                result = adapter.confirm(**arguments, acknowledgement=input(f"Type {phrase}: "))
            else:
                result = adapter.action(operation, arguments)
            for row in result if isinstance(result, list) else [result]:
                if isinstance(row, dict) and "ReviewID" in row:
                    print(adapter.reviews.summary(row))
                elif isinstance(row, dict) and "AttemptID" in row:
                    print(adapter.intake.summary(row))
            print(json.dumps(result, indent=2, default=str))
        except (EOFError, KeyboardInterrupt):
            break
        except Exception as exc:
            adapter.record("failure", dict(type=type(exc).__name__, message=str(exc)))
            print(f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
