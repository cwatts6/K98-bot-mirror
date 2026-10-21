"""Guided settlement and capture for atomic configuration publication."""

from services.player_report_recovery_dal import PlayerReportRecoveryDAL
from services.player_report_recovery_service import (
    PlayerReportCaptureRecovery,
    PlayerReportRecoveryAdapter,
)


class ConfigurationProducerDAL(PlayerReportRecoveryDAL):
    producer_kind = "configuration_import"
    closure_key = "configuration_cancelled"
    cancel_action = "cancel_configuration"
    export_dispositions = frozenset({"configuration_only_v1", "pipeline_export_v1"})

    @classmethod
    def validate_read_request(cls, request):
        """Validate saved root publication intent, without executing or replaying it."""
        from kvk.dal.new_source_import_dal import SourceConflict
        from services.export_coordination_dal import identity

        if not isinstance(request, dict) or set(request) != {
            "read_configuration",
            "configuration_import",
        }:
            raise SourceConflict("Exact configuration import read request required.")
        association = request["configuration_import"]
        if (
            not isinstance(association, dict)
            or set(association) != {"producer", "sources", "outputs", "invocation_mode"}
            or association["invocation_mode"] != "publish"
            or not all(isinstance(association[k], dict) for k in ("sources", "outputs"))
        ):
            raise SourceConflict("Exact configuration import read association required.")
        producer = association["producer"]
        if (
            not isinstance(producer, dict)
            or "parent" in producer
            or set(producer) != cls.producer_fields(producer)
            or producer.get("kind") != cls.producer_kind
            or type(producer.get("atomic_checkpoint")) is not int
            or producer["atomic_checkpoint"] != 1
        ):
            raise SourceConflict("Exact root configuration import producer required.")
        identity(request["read_configuration"])
        identity(producer["operation"])

    @classmethod
    def producer_fields(cls, producer):
        from services.export_coordination_dal import identity

        fields = super().producer_fields(producer)
        if "parent" in producer:
            identity(producer["parent"])
            fields |= {"parent"}
        return fields


class ConfigurationProducerCapture(PlayerReportCaptureRecovery):
    request_dal = ConfigurationProducerDAL
    procedure = "ProcConfig and sp_TARGETS_MASTER"


class ConfigurationProducerRecovery(PlayerReportRecoveryAdapter):
    kind = "configuration_producer"
    title = "Configuration publication recovery"
    output_name = "configuration and target output"
    cancel_action = "cancel_configuration"
    closure_key = "configuration_cancelled"
    close_label = "Close rolled-back config & release"
    open_outcome = "configuration_not_committed"
    automatic_action = "complete_configuration_only"
    automatic_reason = (
        "Original SQL-only configuration intent and committed retained output verified"
    )
    no_export_outcome = "configuration_only_completed"
    no_export_label = "Verify configuration-only completion"
    no_export_pending = "This SQL-only configuration refresh needs no export decision. Automatic verification is pending."
    no_export_explanation = (
        "This invocation requested SQL configuration and target refresh only. "
        "Its atomic SQL checkpoint and retained captured bytes are verified, "
        "and the original no-export disposition is closed. This does not certify "
        "spreadsheet delivery or subsequent cache freshness."
    )

    def _no_export(self, preview):
        """Use the shared no-export closeout only for this producer's explicit intent."""
        request = self.dal.request(preview["preparation"])
        return request["request"]["producer"].get("export_disposition") == "configuration_only_v1"

    def inspect(self, source_id):
        evidence, token, resolved = super().inspect(source_id)
        if evidence["outcome"] == "configuration_cancelled":
            evidence["explanation"] = (
                "This configuration attempt is closed and its exact reservation is released. "
                "The prior configuration and target publication are preserved. "
                "This does not claim a new configuration import or cache refresh completed."
            )
            request = self.dal.request(self.dal.inspect(source_id)["preparation"])
            if "parent" not in request["request"]["producer"]:
                evidence["recovery_links"] = [
                    dict(
                        label="Choose configuration continuation",
                        kind="configuration_continuation",
                        source_id=source_id,
                    )
                ]
        elif self.cancel_action in evidence["actions"]:
            evidence["explanation"] = (
                "The typed atomic contract and SQL locks verify that this attempt did not "
                "commit configuration changes or target publication. Review the closure below."
            )
            evidence["actions"][self.cancel_action].update(
                check="Confirm this rolled-back configuration attempt should be closed. The prior configuration and targets remain; no new import or cache refresh is claimed.",
                effect="Exclude live execution, verify the atomic receipt is absent, fence the old attempt, release only its reservation and verify the saved closure. No SQL or provider write is replayed.",
            )
        return evidence, token, resolved
