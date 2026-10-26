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
        backup = (
            self.copies.inspect_backup(reference, bytes.fromhex(binding["sha256"]))
            if not good
            else None
        )
        actions = {}
        replacement = None
        containment = None
        registration = None
        resolved = len(good) == 2
        if len(good) == 2:
            outcome = "verified"
            explanation = "Both protected evidence copies match the original saved hash. Normal recovery will verify the operation separately; restoring evidence does not establish write success."
        elif good or backup["state"] == "verified":
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
            if not good:
                explanation = "Both protected evidence copies are unavailable. A locally staged encrypted backup decrypts and matches the original SQL hash. Confirm restoration below; the original operation still needs its own verification."
                actions[action].update(
                    label="Restore verified backup",
                    check="Confirm restoration from the staged backup that matches the original SQL hash. This restores evidence only; it does not certify the operation or release ownership.",
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
            if "target isolation" in binding["kinds"]:
                from services.export_evidence_containment import open_recovery, summary

                try:
                    containment = summary(open_recovery(self.broker, reference))
                except SourceConflict:
                    pass
                if containment is not None:
                    resolved = containment["verified"] is not None
                    outcome = (
                        "current_fences_verified" if resolved else "fence_attestation_required"
                    )
                    explanation = (
                        "A separate sealed attestation independently verifies the current permanent target fences and closed dispatch ledger. The original private receipt remains unavailable and the original provider outcome remains unknown. Continue the linked replacement recovery."
                        if resolved
                        else "The original private receipt is unavailable. Independent SQL owner, target and request-ledger checks verify the present isolation. Confirm a new attestation to continue replacement recovery; it will not reconstruct the lost receipt, terminate an old worker or claim delivery."
                    )
                    if not resolved:
                        actions["attest_containment"] = dict(
                            label="Verify current isolation",
                            check="Confirm a separate present-state isolation attestation. Retain the original receipt as unavailable and the old write outcome as unknown. The old files may still receive delayed writes and must remain retired.",
                            effect="Recheck the complete permanent target set, exact owner/fence, closed streams and retained request/event seals, then save and independently verify a new private receipt. No original receipt, reservation, job or provider file is changed.",
                        )
            if binding["kinds"] == ["replacement activation"]:
                from services.export_registration_attestation import open_recovery, summary

                try:
                    registration = summary(open_recovery(self.broker, reference))
                except (SourceConflict, OSError, KeyError, ValueError):
                    pass
                if registration is not None:
                    resolved = registration["verified"]
                    outcome = (
                        "registration_dependencies_verified"
                        if resolved
                        else "registration_attestation_required"
                    )
                    explanation = (
                        "A separate receipt verifies this registration from its independently verified proposal, containment and complete readback journal. The original activation receipt remains unavailable. This does not certify delivery or recover any other missing history."
                        if resolved
                        else "The activation receipt is unavailable. Its authenticated predecessor, original proposal, containment and complete file-read journal independently derive the exact SQL registration. Confirm a separate attestation to recover this registration dependency; no provider request or registration change is performed."
                    )
                    if not resolved:
                        actions["attest_registration"] = dict(
                            label="Verify registration evidence",
                            check="Confirm a separate attestation of the independently verified registration dependencies. The missing original receipt stays missing and original publication remains separately verified.",
                            effect="Re-derive the exact registration from authenticated predecessors, sealed file choices and the original complete read journal. Compare the SQL binding and save a new independently verified receipt. No targets, access policy, ownership or provider files are changed.",
                        )
        evidence = dict(
            title="Private recovery evidence",
            outcome=outcome,
            explanation=explanation,
            actions=actions,
            evidence_reference=binding["reference"],
            evidence_kinds=binding["kinds"],
            copies={key: value["state"] for key, value in copies.items()},
        )
        if backup is not None:
            evidence["backup_candidate"] = backup["state"]
            if (
                backup["state"] != "verified"
                and replacement is None
                and containment is None
                and registration is None
            ):
                evidence["required_evidence"] = [
                    "Download this recovery report and preserve the original SQL evidence binding and damaged files. Do not rerun the operation or release its reservations.",
                    "On the bot machine, use the installed authority manifest's evidence_root folder. Obtain the original encrypted evidence file from a trusted backup made for the same Windows identity; do not send plaintext or credentials through Discord.",
                    f"Copy that encrypted file into the protected evidence folder as {self.copies.backup_key(reference)}. Leave the primary and replica files untouched. Required decrypted SHA-256: {binding['sha256']}.",
                    "Choose Recheck. Only a decryptable, hash-matching backup enables Restore verified backup, followed by separate confirmation. If no backup verifies, retain the incident for independently verified successor recovery; it is not resolved by an admin assertion.",
                ]
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
        if containment is not None:
            evidence["original_receipt_verified"] = False
            evidence["containment_attestation_id"] = (
                containment["verified"]["attestation_id"] if containment["verified"] else None
            )
            evidence["recovery_links"] = [
                dict(
                    label="Continue original recovery",
                    kind=(
                        "export_rollover"
                        if containment["owner_kind"] == "rollover"
                        else "export_job"
                    ),
                    source_id=containment["source_id"],
                )
            ]
        if registration is not None:
            evidence.update(
                original_receipt_verified=False,
                registration_attestation_id=(
                    registration["attestation"]["ActionID"] if resolved else None
                ),
                registration_sha256=registration["registration_sha256"],
            )
        return dict(
            evidence=evidence,
            token=digest(
                dict(
                    binding=binding,
                    copies=copies,
                    replacement=replacement,
                    backup=backup,
                    containment=containment,
                    registration=registration,
                )
            ).hex(),
            resolved=resolved,
        )

    def dispatch(self, message):
        operation = message.get("operation")
        fields = {"version", "action", "operation"}
        if operation in {"pending", "pending_page"}:
            fields.add("after")
        elif operation in {"inspect", "restore", "attest", "attest_registration"}:
            fields.add("reference")
            uuid_text(message.get("reference"))
            if operation in {"restore", "attest", "attest_registration"}:
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
            if operation in {"pending", "pending_page"}:
                after = message["after"]
                if after is not None:
                    uuid_text(after)
                page = self.catalog.page(after)
                wrapped = not page and after is not None
                page = page or self.catalog.page()
                if operation == "pending_page":
                    return dict(references=page, wrapped=wrapped)
                return page
            current = self.inspect(message["reference"])
            if operation == "attest_registration":
                from services.export_registration_attestation import apply, open_recovery

                if (
                    current["token"] != message["token"]
                    or "attest_registration" not in current["evidence"]["actions"]
                ):
                    raise SourceConflict("Registration evidence changed; reopen its confirmation.")
                state = open_recovery(self.broker, message["reference"])
                apply(
                    state["service"],
                    state["row"],
                    state["base"],
                    token=state["token"],
                    actor=message["actor"],
                    reason=message["reason"],
                )
                return self.inspect(message["reference"])
            if operation == "attest":
                from services.export_containment_attestation import apply
                from services.export_evidence_containment import open_recovery

                if (
                    current["token"] != message["token"]
                    or "attest_containment" not in current["evidence"]["actions"]
                ):
                    raise SourceConflict("Isolation review changed; reopen its confirmation.")
                state = open_recovery(self.broker, message["reference"])
                apply(
                    state["service"],
                    state["snapshot"],
                    token=state["token"],
                    actor=message["actor"],
                    reason=message["reason"],
                )
                return self.inspect(message["reference"])
            if operation == "restore":
                if current["token"] != message["token"] or not set(
                    current["evidence"]["actions"]
                ) & {"restore_evidence", "protect_evidence"}:
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
    automatic_action = "protect_evidence"
    automatic_reason = "Protect the original hash-verified evidence with a second encrypted copy"

    def __init__(self, client):
        self.client = client

    def pending_recovery(self, *, after=None):
        return self.client.evidence_recovery("pending", after=after)

    def discovery_page(self, *, after=None):
        """Read-only page with SQL-order wrap evidence, without guessing UUID order."""
        return self.client.evidence_recovery("pending_page", after=after)

    def inspect(self, source_id):
        result = self.client.evidence_recovery("inspect", reference=source_id)
        return result["evidence"], result["token"], result["resolved"]

    def execute(self, source_id, action, token, actor, reason):
        if action not in {
            "restore_evidence",
            "protect_evidence",
            "attest_containment",
            "attest_registration",
        }:
            raise SourceConflict("Unsupported evidence repair.")
        return self.client.evidence_recovery(
            {"attest_containment": "attest", "attest_registration": "attest_registration"}.get(
                action, "restore"
            ),
            reference=source_id,
            token=token,
            actor=actor,
            reason=reason,
        )

    def reconcile(self, source_id, action):
        evidence, token, resolved = self.inspect(source_id)
        if action["ActionKind"] in {"attest_containment", "attest_registration"}:
            marker = (
                "containment_attestation_id"
                if action["ActionKind"] == "attest_containment"
                else "registration_attestation_id"
            )
            if resolved:
                return (
                    "verified"
                    if evidence.get(marker) == str(action["ActionID"]).lower()
                    else "not_applied"
                )
            if token != action["EvidenceHash"] or action["ActionKind"] not in evidence["actions"]:
                return "not_applied"
            # Retry only this already-approved metadata attestation against the
            # unchanged review, under the same authority lock and action identity.
            # It cannot release ownership or replay provider/business work.
            self.execute(
                source_id,
                action["ActionKind"],
                token,
                "recovery:" + str(action["ActionID"]),
                action["Reason"],
            )
            verified, _, complete = self.inspect(source_id)
            return (
                "verified"
                if complete and verified.get(marker) == str(action["ActionID"]).lower()
                else None
            )
        if resolved:
            return "verified" if evidence["outcome"] == "verified" else "not_applied"
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
