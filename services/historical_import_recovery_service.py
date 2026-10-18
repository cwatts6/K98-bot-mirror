"""Review and retire obsolete captured exports while preserving unknown SQL history."""

import json
import re

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_snapshot_store import SnapshotReceipt
from services.historical_import_recovery_dal import HistoricalImportRecoveryDAL
from services.legacy_export_snapshot_service import LegacySnapshot, configuration_digest
from services.producer_recovery_review import registration_review

ACTION = "retire_historical_export"
SUMMARY = (
    "Captured output exists, but no exact SQL execution receipt was recorded. "
    "The original SQL outcome and original fault remain unproven. Review the saved input "
    "and original/current settings. If this old export is no longer needed, explicitly "
    "retire it; otherwise leave it open for investigation. Do not rerun the import to clear this incident."
)


class HistoricalImportRecovery:
    def __init__(self, outcomes, runtime):
        self.dal = HistoricalImportRecoveryDAL(outcomes)
        self.runtime = runtime

    def evidence_token(self, state):
        return digest(
            dict(
                database=state["token"],
                registration=json.loads(self.runtime.configuration)["scan_data"],
            )
        ).hex()

    def verify(self, state):
        prep = state["preparation"]
        request = json.loads(prep["RequestJson"])
        generation = json.loads(prep["GenerationJson"] or "{}")
        if not isinstance(request, dict) or not isinstance(generation, dict):
            raise SourceConflict("Historical request or generation is malformed.")
        if bytes(prep["RequestHash"]) != digest(request):
            raise SourceConflict("The saved request no longer matches its original hash.")
        inner = request.get("request")
        if (
            not isinstance(inner, dict)
            or inner.get("producer")
            or request.get("consumer") != "scan_data"
            or request.get("storage_owner") != self.runtime.store.storage_owner
            or inner.get("kind") != "scan_data"
            or not isinstance(inner.get("config"), dict)
        ):
            raise SourceConflict("This preparation requires its typed producer recovery workflow.")
        if state["execution"] or state["resources"] or state["streams"] or prep.get("JobID"):
            raise SourceConflict(
                "Execution, held access or provider evidence requires its separate guided recovery."
            )
        marker = generation.pop("historical_disposition", None)
        closed = marker is not None
        if prep["State"] != ("unavailable" if closed else "captured"):
            raise SourceConflict("Only an unqueued historical capture can be retired.")
        if closed and (
            not isinstance(marker, dict)
            or set(marker) != {"token", "actor", "reason", "sql_outcome"}
            or marker.get("sql_outcome") != "unproven"
            or not re.fullmatch(r"[0-9a-f]{64}", str(marker.get("token", "")))
            or not re.fullmatch(r"recovery:[0-9a-fA-F-]{36}", str(marker.get("actor", "")))
            or not isinstance(marker.get("reason"), str)
            or not 1 <= len(marker["reason"]) <= 512
        ):
            raise SourceConflict("The saved historical decision does not verify.")
        receipt = SnapshotReceipt(
            prep["SpoolKey"],
            prep["SpoolBytes"],
            bytes(prep["SpoolHash"]).hex(),
            prep["StorageOwner"],
        )
        snapshot = LegacySnapshot.load(self.runtime.store.read(receipt))
        metadata = snapshot.metadata()
        if (
            metadata["preparation_id"] != str(prep["PreparationID"]).lower()
            or metadata["consumer"] != "scan_data"
            or metadata["generation"] != generation
            or generation.get("commit_identity") != str(prep["PreparationID"]).lower()
            or generation.get("registration_sha256") != configuration_digest(inner["config"])
            or metadata["provenance"]
            != dict(owner=str(prep["OwnerID"]).lower(), fence=prep["Fence"])
        ):
            raise SourceConflict(
                "The retained capture, ownership or original registration does not verify."
            )
        return closed

    def inspect(self, source_id):
        state = self.dal.inspect(source_id)
        prep = state["preparation"]
        blocker = None
        try:
            closed = self.verify(state)
        except SourceConflict as error:
            closed, eligible = False, False
            blocker = str(error)
        except (ValueError, TypeError, KeyError, OSError):
            closed, eligible = False, False
            blocker = "The saved request or captured bytes are missing, malformed or fail their saved hash/identity checks."
        else:
            eligible = not closed
        context = self.context(prep, closed=closed, eligible=eligible)
        context["verification_blocker"] = blocker
        actions = {}
        if eligible:
            actions[ACTION] = dict(
                label="Retire historical export",
                check="Confirm you have reviewed the original input and destinations and this old export is no longer needed. Its SQL outcome remains unknown.",
                effect="Prevent future queueing of this exact capture, preserve its input references, captured bytes and unknown SQL history, and record your decision. No SQL replay, provider write or resource release occurs.",
                review_details=True,
                review_title="Review historical input and configuration",
                review_description=SUMMARY,
            )
        explanation = (
            "Admin retired this obsolete export. Original SQL outcome remains unproven; retained evidence is preserved. This does not certify an import or spreadsheet delivery."
            if closed
            else (
                SUMMARY
                if eligible
                else f"{blocker} Retain this incident and its evidence; no retirement, release or replay is authorized."
            )
        )
        return (
            dict(
                title="Historical import / captured export",
                outcome="unproven",
                resolution="historical_export_retired" if closed else None,
                explanation=explanation,
                actions=actions,
                failure_context=context,
            ),
            self.evidence_token(state),
            closed,
        )

    def context(self, prep, *, closed=False, eligible=False):
        # These are retained checkpoint assertions, never execution receipts or
        # an assertion that the original input/configuration caused a failure.
        try:
            generation = json.loads(prep.get("GenerationJson") or "{}")
            producer = generation.get("producer", {})
            request = json.loads(prep["RequestJson"])["request"]
            original = request["config"]
        except (ValueError, TypeError, KeyError, AttributeError):
            producer, original = {}, None
        if not isinstance(producer, dict):
            producer = {}
        filename = producer.get("completed_filename")
        procedure = producer.get("procedure")
        current = json.loads(self.runtime.configuration)["scan_data"]
        return dict(
            input_file=(
                filename
                if isinstance(filename, str)
                and re.fullmatch(r"stats_[0-9a-f]{32}\.ready\.csv", filename)
                else None
            ),
            input_identity_source="retained_producer_checkpoint_not_execution_receipt",
            original_upload_name="not_recorded",
            producer_procedure=(
                procedure
                if isinstance(procedure, str)
                and re.fullmatch(r"(?:dbo|KVK)\.[A-Za-z_][A-Za-z0-9_]{0,100}", procedure)
                else None
            ),
            original_fault="not_recorded",
            sql_outcome="unproven",
            registration_matches=original == current,
            original_registration_sha256=(
                configuration_digest(original) if original is not None else None
            ),
            current_registration_sha256=configuration_digest(current),
            current_blocker=(
                None
                if closed
                else (
                    "historical_decision_required"
                    if eligible
                    else "historical_verification_required"
                )
            ),
            summary=(
                "Historical export retired by admin; SQL outcome remains unknown."
                if closed
                else SUMMARY
            ),
        )

    def review_details(self, source_id, action, token):
        state = self.dal.inspect(source_id)
        if action != ACTION or self.evidence_token(state) != token or self.verify(state):
            raise SourceConflict("Historical evidence changed. Reopen this incident.")
        prep = state["preparation"]
        context = self.context(prep, eligible=True)
        fields = [dict(label="Historical SQL outcome", text=SUMMARY)]
        fields.extend(
            registration_review(
                dict(
                    preparation=prep,
                    current_registration=json.loads(self.runtime.configuration)["scan_data"],
                    producer=dict(
                        inputs=dict(
                            context,
                            preparation_id=str(prep["PreparationID"]),
                            created_utc=str(prep["CreatedUTC"]),
                            captured_bytes=prep["SpoolBytes"],
                            captured_sha256=bytes(prep["SpoolHash"]).hex(),
                        )
                    ),
                )
            )
        )
        return fields

    def execute(self, source_id, token, actor, reason):
        self.dal.retire(source_id, token, actor, reason, self.verify, self.evidence_token)

    def reconcile(self, source_id, action):
        state = self.dal.inspect(source_id)
        expected = dict(
            token=action["EvidenceHash"],
            actor=f"recovery:{action['ActionID']}",
            reason=action["Reason"],
            sql_outcome="unproven",
        )
        generation = json.loads(state["preparation"]["GenerationJson"] or "{}")
        marker = generation.get("historical_disposition") if isinstance(generation, dict) else None
        try:
            closed = self.verify(state)
        except (SourceConflict, ValueError, TypeError, KeyError, OSError):
            # A saved decision with unavailable independent verification remains
            # pending; loss of its bytes cannot turn an applied action into failure.
            if marker == expected:
                return None
            # The guarded snapshot contains no marker for this action. The
            # atomic disposition therefore did not apply, even if lost/corrupt
            # spool bytes leave the database evidence token unchanged. Settle
            # the intent so inspect can keep showing its verification blocker.
            return "not_applied"
        if closed:
            marker = json.loads(state["preparation"]["GenerationJson"])["historical_disposition"]
            return "verified" if marker == expected else "not_applied"
        if self.evidence_token(state) != action["EvidenceHash"]:
            return "not_applied"
        self.execute(source_id, expected["token"], expected["actor"], expected["reason"])
        state = self.dal.inspect(source_id)
        return (
            "verified"
            if self.verify(state)
            and json.loads(state["preparation"]["GenerationJson"])["historical_disposition"]
            == expected
            else None
        )
