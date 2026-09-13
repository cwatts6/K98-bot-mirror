"""Matched-update orchestration. Accepted inputs survive failures; no external writes."""

import json
from uuid import NAMESPACE_URL, uuid5

from kvk.dal.new_source_import_dal import SourceConflict, canonical
from kvk.dal.new_source_recovery_dal import RecoveryDAL, endpoint_chain
from kvk.dal.source_update_dal import SourceUpdateDAL
from kvk.models.new_source_reporting import EndpointChange
from kvk.services.new_source_publication_service import PublicationService


class SourceUpdateService:
    def __init__(self, connect):
        self.dal = SourceUpdateDAL(connect)
        self.inputs = RecoveryDAL(connect)
        self.publisher = PublicationService(connect)

    def create(self, context, *, authorized, admin_authorized=False):
        return self.dal.create(context, authorized=authorized, admin_authorized=admin_authorized)

    def associate(self, update_id, **association):
        return self.dal.associate(update_id, **association)

    def publish(self, update_id):
        update = self.dal.resume_endpoint(update_id)
        if update["UpdateState"] == "selected":
            return self.dal.selected_result(update_id)
        if update["UpdateState"] != "ready":
            return None
        data = self.inputs.load_inputs(update["KVK_NO"], update["PeriodID"], update=update)
        config, previous = data["config"], data["previous"]
        confirmed_action = json.loads(update["ConfirmationJson"]).get("action", "publish")
        change = None
        request = None
        if (
            previous
            and previous.config.version_id != config.version_id
            and confirmed_action != "configure"
        ):
            chain = endpoint_chain(data["requests"], previous.config.version_id, config.version_id)
            first, request = chain[0], chain[-1]
            if update["RequestID"] != request["RequestID"]:
                raise SourceConflict("Sealed update lacks the exact endpoint request.")
            change = EndpointChange(
                str(request["RequestID"]),
                config.period_id,
                previous.config.version_id,
                config.version_id,
                first["OldEndScanID"],
                request["NewEndScanID"],
                request["Actor"],
                request["Reason"],
                first["OldStartScanID"],
                request["NewStartScanID"],
            )
            if (previous.config.start_scan_id, previous.config.end_scan_id) == (
                config.start_scan_id,
                config.end_scan_id,
            ):
                previous, change = None, None
        elif previous and previous.player_state.value not in ("final", "corrected_final"):
            previous = None
        if confirmed_action in ("correct", "configure"):
            previous, change = None, None
        candidate = self.publisher.build_candidate(
            config=config,
            observations=data["observations"],
            b0=data["b0"],
            aggregate=data["aggregate"],
            previous=previous,
            endpoint_change=change,
            sealed_update=update,
        )
        selected = data["selected"]
        component_version = selected["SelectionVersion"] if selected else 0
        routing_version = (data["routing"] or {}).get("RoutingVersion", 0)
        action_id = str(
            uuid5(
                NAMESPACE_URL,
                canonical(
                    (
                        update_id,
                        candidate.snapshot.publication_id,
                        component_version,
                        data["public_version"],
                        routing_version,
                        data["season_version"],
                    )
                ),
            )
        )
        result = self.publisher.select_publication(
            candidate,
            action_id=action_id,
            expected_selection_version=component_version,
            expected_routing_version=routing_version,
            expected_public_version=data["public_version"],
            expected_season_version=data["season_version"],
            actor=update["ConfirmedBy"],
            reason="Select confirmed complete source update",
            action_type="endpoint_update" if request else confirmed_action,
            request_id=update["RequestID"],
            admin_authorized=confirmed_action != "publish",
        )
        return result["complete"]
