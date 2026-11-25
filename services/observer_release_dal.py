"""Read the existing committed observer ledger on the application connection."""

from datetime import datetime
from uuid import UUID

from kvk.dal.new_source_import_dal import SourceConflict, rows
from services.export_observer_contract import MIGRATION_ID


def committed_observer_receipt(cursor):
    cursor.execute(
        """
SELECT TOP (2) h.Status AS migration_status,h.ChecksumSha256 AS profile_sha256,
 h.GitCommit AS sql_commit,CONVERT(varchar(36),h.DeploymentId) AS deployment_id,
 d.Status AS deployment_status,d.GitCommit AS deployment_commit,
 d.BranchName AS deployment_profile,d.DatabaseName AS deployment_database,
 d.ErrorMessage AS binding,
 CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')) AS server,
 DB_NAME() AS [database],DB_ID() AS database_id,USER_NAME() AS principal,
 ORIGINAL_LOGIN() AS login,s.object_id AS sequence_object_id,
 s.create_date AS sequence_created,
 s.modify_date AS sequence_modified
FROM dbo.SchemaMigrationHistory h
JOIN dbo.DeploymentRunHistory d ON d.DeploymentId=h.DeploymentId
JOIN sys.sequences s ON s.object_id=OBJECT_ID(N'dbo.P02ObservationGeneration')
WHERE h.MigrationId=?;
""",
        MIGRATION_ID,
    )
    result = rows(cursor)
    if len(result) != 1:
        raise SourceConflict("One linked committed observer receipt is required.")
    receipt = result[0]
    for name in ("sequence_created", "sequence_modified"):
        stamp = receipt[name]
        if not isinstance(stamp, datetime) or stamp.microsecond % 1000:
            raise SourceConflict("Typed ODBC catalogue datetime at millisecond precision required.")
        receipt[name] = stamp.isoformat(timespec="microseconds")
    # SQL converts its uniqueidentifier to a hyphenated varchar using uppercase
    # hex. Canonicalize only that transport field; issuer checks stay exact.
    identifier = receipt.get("deployment_id")
    if not isinstance(identifier, str):
        raise SourceConflict("Hyphenated SQL deployment UUID required.")
    try:
        canonical = str(UUID(identifier))
    except ValueError as error:
        raise SourceConflict("Hyphenated SQL deployment UUID required.") from error
    if identifier.lower() != canonical:
        raise SourceConflict("Hyphenated SQL deployment UUID required.")
    receipt["deployment_id"] = canonical
    return receipt
