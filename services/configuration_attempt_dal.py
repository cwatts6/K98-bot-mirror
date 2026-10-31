"""Locate only the original configuration operation in its registered custody."""

import json

from kvk.dal.new_source_import_dal import SourceConflict, digest, rows, transaction
from services.export_coordination_dal import identity


class ConfigurationAttemptDAL:
    def __init__(self, runtime):
        self.runtime = runtime

    def links(self, operation):
        runtime = self.runtime
        with transaction(runtime.dal.connect) as cursor:
            cursor.execute(
                "SELECT TOP(3) PreparationID,ConsumerKind,RequestJson,RequestHash "
                "FROM dbo.ExportPreparation WHERE AccountKey=? AND StorageOwner=? AND "
                "((ConsumerKind='config' AND "
                "JSON_VALUE(RequestJson,'$.request.configuration_import.producer.operation')=?) "
                "OR (ConsumerKind='scan_data' AND "
                "JSON_VALUE(RequestJson,'$.request.producer.kind')='configuration_import' AND "
                "JSON_VALUE(RequestJson,'$.request.producer.operation')=?))",
                runtime.account,
                runtime.store.storage_owner,
                identity(operation),
                identity(operation),
            )
            matches = rows(cursor)
        found = {}
        for row in matches:
            kind = row["ConsumerKind"]
            document = json.loads(row["RequestJson"])
            if kind in found or bytes(row["RequestHash"]) != digest(document):
                raise SourceConflict(
                    "Configuration attempt has ambiguous or changed original evidence."
                )
            found[kind] = identity(row["PreparationID"])
        return found
