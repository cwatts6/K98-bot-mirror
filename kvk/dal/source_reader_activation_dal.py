"""Read immutable intent calculation scope without loading player results."""

from kvk.dal.new_source_import_dal import SourceConflict, one, transaction
from kvk.dal.source_update_dal import read_export_intent


def intent_scope(connect, intent_id, expected_hash):
    with transaction(connect) as cursor:
        intent, vector = read_export_intent(cursor, intent_id)
        if bytes(intent["VectorHash"]) != expected_hash:
            raise SourceConflict("Activation intent hash differs.")
        versions = set()
        for member in vector:
            cursor.execute(
                "SELECT CalculationVersion FROM KVK.SourcePublication WHERE PublicationID=? "
                "AND SourceKey=? AND KVK_NO=? AND PeriodID=? AND BuildState='complete'",
                member["PublicationID"],
                intent["SourceKey"],
                intent["KVK_NO"],
                member["PeriodID"],
            )
            publication = one(cursor)
            if publication is None:
                raise SourceConflict("Complete pinned publication required for activation.")
            versions.add(publication["CalculationVersion"])
        return intent["KVK_NO"], versions
