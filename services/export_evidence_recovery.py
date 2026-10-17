"""Guided exact-byte restoration, independent of effective registration history."""

import re

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_evidence_catalog_dal import EvidenceCatalogDAL
from services.export_evidence_storage import EvidenceCopies
from services.export_execution_protocol import uuid_text


class EvidenceRecovery:
    def __init__(self, broker):
        self.broker = broker
        self.catalog = EvidenceCatalogDAL(
            broker.authority.dal.connect, broker.base_registration.value()["account"]
        )
        self.copies = EvidenceCopies(broker.authority.store)

    def inspect(self, reference):
        binding = self.catalog.get(reference)
        copies = self.copies.inspect(reference, bytes.fromhex(binding["sha256"]))
        good = {key for key, value in copies.items() if value["state"] == "verified"}
        actions = {}
        replacement = None
        resolved = len(good) == 2
        if len(good) == 2:
            outcome = "verified"
            explanation = "Both protected evidence copies match the original saved hash. Normal recovery will verify the operation separately; restoring evidence does not establish write success."
        elif good:
            outcome = "recoverable"
            explanation = "A protected evidence copy is missing or cannot be read, but another copy matches the original saved hash. The bot can restore the exact original bytes."
            action = "protect_evidence" if "primary" in good else "restore_evidence"
            actions[action] = dict(
                label=(
                    "Protect verified evidence"
                    if "primary" in good
                    else "Restore verified evidence"
                ),
                check="Confirm restoration of this saved evidence. The surviving copy has been decrypted and matched to the original SQL commitment. No provider result or admin assertion will be substituted.",
                effect="Preserve any damaged encrypted file, restore the missing or damaged copy, and independently decrypt and hash both copies. Then retry normal admission and the original recovery checks. No import or provider write is replayed and no reservation is released by this action.",
            )
        else:
            outcome = "backup_required"
            explanation = "Neither protected evidence copy verifies. The original operation remains unresolved. Exact backup restoration or a separately verified superseding recovery is required; confirmation alone cannot recreate this receipt."
            if binding["kinds"] == ["replacement proposal"]:
                from services.export_evidence_replacement import replacement_proposal_recovery

                try:
                    replacement = replacement_proposal_recovery(
                        self.broker, self.catalog, reference
                    )
                except SourceConflict:
                    pass
                if replacement is not None:
                    resolved = replacement["successor_check_id"] is not None
                    outcome = "superseded_proposal" if resolved else "fresh_proposal_required"
                    explanation = (
                        "A new admin proposal and complete fresh readback now verify. The lost proposal remains unverified. Publication is tracked separately."
                        if resolved
                        else "The original proposal cannot be verified. Use Recover replacement below to discard any unfinished read, re-enter the intended files and confirm a new proposal. The bot will check all files again before activation."
                    )
            if set(binding["kinds"]) <= {
                "replacement verification",
                "stream closure",
                "request payload",
                "request event",
            }:
                from services.export_evidence_replacement import replacement_check_recovery

                try:
                    replacement = replacement_check_recovery(self.broker, self.catalog, reference)
                except SourceConflict:
                    pass  # Never bypass a missing active-history or proposal commitment.
                if replacement is not None:
                    resolved = replacement["successor_check_id"] is not None
                    outcome = "superseded_read" if resolved else "fresh_read_required"
                    explanation = (
                        "A separate replacement check has independently verified the complete new readback. The lost read result remains unverified in the audit history. This resolves its recovery dependency, not the original unknown write or publication."
                        if resolved
                        else "The old read attempt is settled and holds no reservations, but its result cannot be verified. Use Recover replacement check below for the guided fresh read check or new file choices. Activation still requires a complete new verified journal."
                    )
        evidence = dict(
            title="Private recovery evidence",
            outcome=outcome,
            explanation=explanation,
            actions=actions,
            evidence_reference=binding["reference"],
            evidence_kinds=binding["kinds"],
            copies={key: value["state"] for key, value in copies.items()},
            replica_diagnostics=self.copies.diagnostics(reference),
        )
        if replacement is not None:
            evidence.update(
                evidence_recovery_job_id=replacement["job_id"],
                lost_check_id=replacement.get("lost_check_id"),
                successor_check_id=replacement["successor_check_id"],
            )
            if "lost_proposal_id" in replacement:
                evidence["lost_proposal_id"] = replacement["lost_proposal_id"]
                evidence["evidence_recovery_label"] = "Recover replacement"
            if replacement.get("owner_kind") == "rollover":
                evidence.pop("evidence_recovery_job_id")
                evidence["recovery_links"] = [
                    dict(
                        label=evidence.get("evidence_recovery_label", "Recover replacement check"),
                        kind="export_rollover",
                        source_id=replacement["job_id"],
                    )
                ]
        return dict(
            evidence=evidence,
            token=digest(dict(binding=binding, copies=copies, replacement=replacement)).hex(),
            resolved=resolved,
        )

    def dispatch(self, message):
        operation = message.get("operation")
        fields = {"version", "action", "operation"}
        if operation == "pending":
            fields.add("after")
        elif operation in {"inspect", "restore"}:
            fields.add("reference")
            uuid_text(message.get("reference"))
            if operation == "restore":
                fields |= {"token", "actor", "reason"}
                if (
                    not isinstance(message.get("token"), str)
                    or re.fullmatch(r"[0-9a-f]{64}", message["token"]) is None
                    or not isinstance(message.get("actor"), str)
                    or re.fullmatch(r"recovery:[0-9a-f-]{36}", message["actor"]) is None
                    or not isinstance(message.get("reason"), str)
                    or not 1 <= len(message["reason"].strip()) <= 512
                ):
                    raise SourceConflict("Exact reviewed evidence repair required.")
                uuid_text(message["actor"][9:])
        else:
            raise SourceConflict("Unknown evidence recovery operation.")
        if set(message) != fields:
            raise SourceConflict("Exact evidence recovery selector required.")
        self.broker.boundary.recheck()
        with self.broker.authority._lock:
            if operation == "pending":
                after = message["after"]
                if after is not None:
                    uuid_text(after)
                page = self.catalog.page(after)
                return page or self.catalog.page()
            current = self.inspect(message["reference"])
            if operation == "restore":
                if current["token"] != message["token"] or not current["evidence"]["actions"]:
                    raise SourceConflict(
                        "Evidence changed; review the current restoration choices."
                    )
                binding = self.catalog.get(message["reference"])
                self.copies.repair(message["reference"], bytes.fromhex(binding["sha256"]))
                current = self.inspect(message["reference"])
                if not current["resolved"]:
                    raise SourceConflict("Evidence restoration is not verified.")
            return current


class EvidenceRecoveryAdapter:
    kind = "private_evidence"
    observe_healthy = False

    def __init__(self, client):
        self.client = client

    def pending_recovery(self, *, after=None):
        return self.client.evidence_recovery("pending", after=after)

    def inspect(self, source_id):
        result = self.client.evidence_recovery("inspect", reference=source_id)
        return result["evidence"], result["token"], result["resolved"]

    def execute(self, source_id, action, token, actor, reason):
        if action not in {"restore_evidence", "protect_evidence"}:
            raise SourceConflict("Unsupported evidence repair.")
        return self.client.evidence_recovery(
            "restore",
            reference=source_id,
            token=token,
            actor=actor,
            reason=reason,
        )

    def reconcile(self, source_id, action):
        evidence, token, resolved = self.inspect(source_id)
        if resolved:
            return "not_applied" if evidence["outcome"].startswith("superseded_") else "verified"
        if token != action["EvidenceHash"] or action["ActionKind"] not in evidence["actions"]:
            # Repair is exact-byte and idempotent. Partial local restoration may
            # be reviewed afresh, but can never author an operation-success proof.
            return "not_applied"
        self.execute(
            source_id,
            action["ActionKind"],
            token,
            "recovery:" + str(action["ActionID"]),
            action["Reason"],
        )
        return "verified" if self.inspect(source_id)[2] else None
