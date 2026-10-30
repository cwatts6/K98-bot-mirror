"""A separate current-configuration decision after an explicit unknown disposition."""

from kvk.dal.new_source_import_dal import SourceConflict, rows, transaction
from services.configuration_continuation import ConfigurationContinuation
from services.configuration_continuation_dal import ConfigurationContinuationDAL
from services.export_coordination_dal import identity
from services.unreceipted_producer_recovery import UnreceiptedProducerDAL


class LegacyConfigurationContinuationDAL(ConfigurationContinuationDAL):
    def pending(self, after=None):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (20) PreparationID FROM dbo.ExportPreparation WHERE AccountKey=? AND StorageOwner=? "
                "AND ConsumerKind='scan_data' AND State='unavailable' "
                "AND JSON_VALUE(GenerationJson,'$.unconfirmed_producer_disposition.action') IS NOT NULL "
                "AND ISNULL(JSON_VALUE(GenerationJson,'$.configuration_continuation.choice'),'')<>'keep_prior' "
                "ORDER BY CASE WHEN PreparationID>CAST(? AS uniqueidentifier) THEN 0 ELSE 1 END,PreparationID",
                self.account,
                self.storage_owner,
                identity(after) if after else None,
            )
            return [identity(row["PreparationID"]) for row in rows(cursor)]

    def original(self, source_id):
        legacy = UnreceiptedProducerDAL(
            self.connect, account=self.account, storage_owner=self.storage_owner
        )
        preview = legacy.inspect(source_id)
        if preview["action"] != "retained_unknown":
            raise SourceConflict("The explicit unknown-outcome disposition must verify first.")
        return preview["preparation"]

    def review_context(self, root):
        return dict(
            original_export_disposition=None,
            original_outcome="unconfirmed",
            original_sources={},
            failure_context={
                "summary": "The original configuration source registration and transaction outcome were not retained. The empty original source fields mean unknown; only the current source links are being approved for a new read."
            },
        )


class LegacyConfigurationContinuation(ConfigurationContinuation):
    kind = "legacy_configuration_continuation"
    title = "Fresh configuration after an unknown legacy result"
    initial_explanation = (
        "The legacy result remains unknown and its exact hold was explicitly closed. "
        "Review a separate read and atomic publication of current configuration, or keep "
        "the existing configuration without certifying it. No original transaction is replayed."
    )

    def inspect(self, source_id):
        evidence, token, resolved = super().inspect(source_id)
        if evidence["outcome"] == "prior_configuration_retained":
            evidence["explanation"] = (
                "Admin retained the existing configuration. Its legacy transaction outcome and freshness remain unconfirmed; no new publication or export is claimed."
            )
        return evidence, token, resolved
