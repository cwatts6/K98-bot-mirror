"""One guided unknown-write recovery, from isolation to verified replacement delivery.

Every choice belongs to a durable recovery action. Inspection and reconciliation
use original receipts; neither a missing response nor a restart replays a write.
"""

import json

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity
from services.export_replacement_check_recovery import inspect_read_check
from services.export_replacement_input import replacement_fields, replacement_input
from services.export_replacement_proposal_recovery import discard_service, inspect_lost_proposal


def choice(label, check, effect, *, input=False):
    result = dict(label=label, check=check, effect=effect)
    if input:
        result["input"] = True
    return result


class ReplacementWorkflow:
    def __init__(
        self,
        *,
        proposals,
        verification,
        activation,
        plan_factory,
        continuation,
        proposal_writer=None,
    ):
        self.proposals, self.verification, self.activation = proposals, verification, activation
        self.plan_factory, self.continuation = plan_factory, continuation
        self.registration = proposals.registration
        self.account = self.registration.value()["account"]
        self.proposal_writer = proposal_writer or proposals

    def _state(self, job_id):
        isolated = self.proposals.containment.inspect(job_id)
        proposals = self.proposals.dal.for_job(job_id, account=self.account)
        result = dict(
            job_id=job_id,
            isolation=isolated,
            proposal=None,
            check=None,
            activation=None,
            delivery=None,
            current_registration_sha256=self.proposal_writer.registration.fingerprint,
            configuration_readiness=None,
            lost_proposal=None,
        )
        # The containment inspector contains private ledger details before its
        # decision. Only its opaque review token and bounded target IDs leave it.
        result["isolation"] = {
            k: isolated.get(k) for k in ("outcome", "token", "targets", "actor", "reason")
        }
        if proposals:
            activated = [
                r
                for r in self.activation.dal.chain(self.account)
                if identity(r["ReplacementID"]) in proposals
            ]
            if len(activated) > 1:
                raise SourceConflict("The original job has conflicting replacement activations.")
            try:
                result["proposal"] = self.proposals.inspect(proposals[-1])
            except (SourceConflict, ValueError, KeyError, TypeError):
                if activated:
                    raise
                lost = inspect_lost_proposal(self, proposals[-1])
                if lost["job_id"] != job_id:
                    raise SourceConflict("Lost proposal belongs to another recovery.")
                result["lost_proposal"] = lost
                result["check"] = lost["checking"]
                return result
            checks = self.verification.dal.list_for_plan(proposals[-1], account=self.account)
            if checks:
                result["check"] = (
                    self.verification.inspect(checks[-1])
                    if activated
                    else inspect_read_check(self.verification, checks[-1])
                )
            if activated:
                result["activation"] = self.activation.verify(activated[0], self.registration)
                result["delivery"] = self.continuation.inspect(job_id, result["activation"])
            elif (
                result["check"]
                and result["check"]["state"] == "verified"
                and any(f.get("configuration_summary") for f in result["check"].get("files", []))
            ):
                result["configuration_readiness"] = self.verification.configuration_readiness(
                    result["check"]["verification_id"]
                )
        return result

    def inspect(self, job_id):
        state = self._state(identity(job_id))
        actions, resolved = {}, False
        isolated, proposal, checked = state["isolation"], state["proposal"], state["check"]
        if isolated["outcome"] != "targets_isolated":
            stage = "isolation_required"
            explanation = "The old write may still arrive. Retire its complete output set, then use verified fresh files to publish the retained input. The original uncertainty will remain in the audit history."
            actions["isolate_targets"] = choice(
                "Retire affected outputs",
                "Confirm the listed old outputs must no longer be used. Warn readers that those links may still change.",
                "Permanently fence these targets and release this job's exact reservations. Continue here to replace the outputs; this does not confirm delivery.",
            )
        elif state["activation"] is not None:
            delivery = state["delivery"]
            stage, explanation = delivery["stage"], delivery["explanation"]
            resolved = delivery["resolved"]
            actions = delivery["actions"]
        elif state["lost_proposal"] is not None:
            stage = "replacement_proposal_required"
            explanation = (
                "The saved proposal cannot be verified. Its original approval will remain "
                "unverified. Re-enter the intended replacement links, confirm a new proposal, "
                "then run a complete fresh check before activation. The old outputs stay isolated."
            )
            if checked is not None:
                stage = "proposal_read_discard_required"
                explanation += " First discard the unfinished read associated with that proposal."
                actions["discard_replacement_check"] = choice(
                    "Discard unfinished read",
                    "Confirm this read result and its unverified proposal must be abandoned. No old write will be retried.",
                    "Verify the complete typed read ledger, fence that attempt and release only its exact reservations. Then offer the replacement form and a new verification.",
                )
            else:
                actions["choose_replacements"] = choice(
                    "Re-enter replacement links",
                    "Review every required output role, owner and sharing policy. Enter the intended replacement files again.",
                    "Save a new admin decision with fresh private evidence. Require a new complete read check before activation and retained-input publication.",
                    input=True,
                )
        elif self.registration.fingerprint != self.proposal_writer.registration.fingerprint and (
            checked is None or checked["state"] != "checking"
        ):
            stage = "refresh_replacement_choices"
            explanation = (
                "Another recovery updated the output registration while these choices were being reviewed. "
                "Re-enter the replacement links against the current registration, then run a fresh check. "
                "The earlier proposal and verification remain in the audit history."
            )
            actions["choose_replacements"] = choice(
                "Refresh replacement choices",
                "Review the current output roles and enter the fresh replacement files again.",
                "Create a new immutable proposal that preserves the other completed recovery. Recheck the files before activation.",
                input=True,
            )
        elif checked is not None and checked["state"] == "checking":
            stage = "checking_replacements"
            explanation = "The read-only check has been admitted. Recheck progress here. If its response was lost, verify the original journal; if it cannot verify, discard this read attempt and start a fresh check. No old write is retried."
            actions["finish_replacement_check"] = choice(
                "Verify original check",
                "Keep the replacement files unchanged while the bot verifies its retained journal.",
                "Accept only a complete original readback and positive child closure. This makes no new provider request.",
            )
            actions["discard_replacement_check"] = choice(
                "Discard this read check",
                "Confirm this unfinished read result can be discarded. The old uncertain write stays isolated.",
                "Verify the complete typed read ledger, fence this check and release its exact reservations. Then offer a fresh verification or new file choices.",
            )
            explanation += " " + checked.get("diagnostic", "")
            if "files_total" in checked:
                explanation += (
                    f" Read requests issued for {checked['files_requested']} of "
                    f"{checked['files_total']} files. Completed read requests alone do not "
                    "confirm verification; the original journal must pass all checks."
                )
            if checked.get("can_finish") is not True:
                actions.pop("finish_replacement_check", None)
        elif checked is not None and checked["state"] == "verified":
            stage = "activation_required"
            explanation = "All replacement files passed owner, sharing and blank-content checks. Confirm activation, then publish the original retained input to the replacements."
            actions["activate_replacements"] = choice(
                "Use verified replacements",
                "Confirm the displayed new files are the intended output locations and remain unchanged since verification.",
                "Seal the new registration and retire the original pool where applicable. Delivery remains open until the retained input is published and verified.",
            )
            if any(f.get("configuration_summary") for f in checked["files"]):
                explanation = "Replacement owner, sharing, configuration schema and blank output checks passed. Open Review output links to inspect the configuration tab counts and links. Verify the actual settings against your intended season, then confirm activation."
                actions["activate_replacements"] = choice(
                    "Use verified replacements",
                    "Open each replacement configuration workbook. Verify season and scan IDs, target bands, exemptions, dates, weights, windows and camp mappings. Empty optional tabs retain existing SQL settings; blank ProcConfig cells also retain stored values. Confirm the complete intended settings, row counts and sharing; keep the files unchanged after checking.",
                    "Switch configuration reads and report outputs together. Protect the copied configuration tabs, then offer publication of the retained report. The original files remain isolated.",
                )
                actions["choose_replacements"] = choice(
                    "Update configuration copy",
                    "Correct the listed configuration cells in the fresh workbook, then enter its links again. The bot must check the edited copy before activation.",
                    "Save a fresh proposal and offer a new read-only check. Original uncertain outputs remain isolated.",
                    input=True,
                )
                if not state["configuration_readiness"]["ready"]:
                    stage = "configuration_attention"
                    explanation = state["configuration_readiness"]["issue"]
                    actions.pop("activate_replacements", None)
        else:
            stage = "choose_replacements" if proposal is None else "verification_required"
            explanation = "The old targets are permanently isolated. The form lists every required replacement, its owner and sharing policy. Saved pages survive reopening and restart."
            actions["choose_replacements"] = choice(
                "Enter replacement links",
                "Prepare each fresh workbook using its displayed role checklist, including copied configuration tabs where listed. Apply the listed owner and sharing permissions.",
                "Save the complete file mapping for verification. Pasting links does not authorize writes or activate them.",
                input=True,
            )
            if proposal is not None:
                actions["verify_replacements"] = choice(
                    "Check replacement files",
                    "Confirm the proposed files are ready for read-only owner, sharing and content verification.",
                    "Start one bounded read-only check of the complete proposed set. Its durable identity prevents a duplicate check after a lost reply.",
                )
            if checked is not None and checked["state"] == "unverifiable":
                stage = "replacement_recheck_required"
                explanation = (
                    "The saved replacement check can no longer be verified. Its typed read ledger "
                    "is settled and owns no reservations. Run a fresh check of the proposed files, "
                    "or enter different files. The lost result remains unverified in the history; "
                    "only a complete new readback can authorize activation."
                )
                actions["verify_replacements"] = choice(
                    "Run fresh read check",
                    "Confirm these replacement files are still intended. Keep them unchanged while the bot checks owner, sharing, configuration where applicable and output contents again.",
                    "Create a new durable read attempt and verify its complete private journal. Do not replay the old uncertain write, restore a missing result or release any existing owner.",
                )
        evidence = dict(
            title="Unknown-write replacement recovery",
            outcome=stage,
            explanation=explanation,
            actions=actions,
            targets=isolated["targets"],
            replacements=proposal["mapping"] if proposal else {},
            delivery=state["delivery"],
        )
        if checked and checked["state"] == "verified":
            evidence["configuration_checks"] = {
                f["file_id"]: f["configuration_summary"]
                for f in checked.get("files", [])
                if f.get("configuration_summary")
            }
            if state["configuration_readiness"] is not None:
                evidence["configuration_preflight"] = state["configuration_readiness"]["files"]
        return evidence, digest(state).hex(), resolved

    def _reviewed(self, job_id, token):
        evidence, actual, resolved = self.inspect(job_id)
        if actual != token or resolved:
            raise SourceConflict("Replacement recovery changed. Review its current choices.")
        state = self._state(job_id)
        if digest(state).hex() != token:
            raise SourceConflict("Replacement recovery changed. Review its current choices.")
        return evidence, state

    def input_fields(self, job_id, action, token):
        evidence, state = self._reviewed(job_id, token)
        if action != "choose_replacements" or action not in evidence["actions"]:
            raise SourceConflict("The replacement form is no longer available.")
        return replacement_fields(self.proposal_writer.registration, state["isolation"]["targets"])

    def validate_input(self, job_id, action, token, payload):
        self.input_fields(job_id, action, token)
        _, state = self._reviewed(job_id, token)
        owner, mapping = replacement_input(
            self.proposal_writer.registration, state["isolation"]["targets"], payload
        )
        from uuid import uuid4

        from services.export_replacement_plan import replacement_registration

        replacement_registration(
            self.proposal_writer.registration,
            targets=state["isolation"]["targets"],
            replacements=mapping,
            replacement_id=str(uuid4()),
        )
        return f"Verify {len(mapping)} fresh spreadsheets owned by {owner}. The original targets remain isolated. Review the saved role/link pairs on each form page before confirming."

    def execute(self, job_id, action, token, actor, reason, *, payload=None):
        evidence, state = self._reviewed(job_id, token)
        if action not in evidence["actions"]:
            raise SourceConflict("This replacement step is no longer available.")
        action_id = identity(actor.removeprefix("recovery:"))
        if actor != "recovery:" + action_id:
            raise SourceConflict("Durable admin recovery identity required.")
        if action == "isolate_targets":
            self.proposals.containment.apply(
                job_id, token=state["isolation"]["token"], actor=actor, reason=reason
            )
        elif action == "choose_replacements":
            owner, mapping = replacement_input(
                self.proposal_writer.registration, state["isolation"]["targets"], payload
            )
            self.proposal_writer.propose(
                job_id,
                token=state["isolation"]["token"],
                replacements=mapping,
                owner_email=owner,
                actor=actor,
                reason=reason,
            )
        elif action == "verify_replacements":
            plan = self.plan_factory(state["proposal"], action_id)
            self.verification.start(plan, actor=actor, reason=reason)
        elif action == "finish_replacement_check":
            self.verification.finish(state["check"]["verification_id"])
        elif action == "discard_replacement_check":
            verifier = (
                discard_service(
                    self,
                    state["lost_proposal"]["replacement_id"],
                    state["check"]["verification_id"],
                )
                if state["lost_proposal"]
                else self.verification
            )
            verifier.discard(
                state["check"]["verification_id"],
                token=state["check"]["token"],
                actor=actor,
                reason=reason,
            )
        elif action == "activate_replacements":
            self.activation.apply(
                state["proposal"]["replacement_id"],
                state["check"]["verification_id"],
                token=state["check"]["token"],
                actor=actor,
                reason=reason,
            )
        else:
            self.continuation.execute(
                job_id, state["activation"], action, actor=actor, reason=reason
            )

    def reconcile(self, job_id, action):
        state = self._state(job_id)
        kind, key = action["ActionKind"], action["ActionID"]
        actor = "recovery:" + key
        lost = state["lost_proposal"]
        if lost is not None:
            if kind == "choose_replacements" and key == lost["replacement_id"]:
                # Admission remains recorded, but lost approval is never recreated.
                return "not_applied"
            if kind == "verify_replacements" and key in lost["checks"]:
                return "verified"  # Original read admission only, not its result.
            if kind == "discard_replacement_check":
                for check_id in lost["checks"]:
                    service = discard_service(self, lost["replacement_id"], check_id)
                    snapshot, _ = service._snapshot(check_id)
                    if snapshot["attempt"]["State"] == "discarded":
                        try:
                            checked = service.inspect(check_id)
                        except (SourceConflict, ValueError, KeyError, TypeError):
                            # _state independently verified the complete terminal
                            # read ledger and released ownership. Lost evidence
                            # cannot prove this action succeeded, but must not
                            # hide a later intact discard or replay the old one.
                            continue
                        if checked["actor"] == actor and checked["reason"] == action["Reason"]:
                            return "verified"
                if lost["checking"] is None:
                    return "not_applied"
        if kind == "isolate_targets" and state["isolation"]["actor"] == actor:
            return "verified"
        if kind == "choose_replacements":
            row = self.proposals.dal.read(key, account=self.account)
            if row is not None:
                proposal = self.proposals.verify(row)
                owner, mapping = replacement_input(
                    self.registration,
                    state["isolation"]["targets"],
                    json.loads(action["InputJson"]),
                )
                if (
                    proposal["job_id"] != job_id
                    or proposal["mapping"] != mapping
                    or proposal["owner_email"] != owner
                ):
                    raise SourceConflict(
                        "Saved replacement choices differ from their action receipt."
                    )
                return "verified"
        if kind == "verify_replacements":
            checked = inspect_read_check(self.verification, key)
            if checked is not None:
                if (
                    state["proposal"] is None
                    or checked["replacement_id"] != state["proposal"]["replacement_id"]
                ):
                    raise SourceConflict("Verification belongs to another replacement proposal.")
                return "verified"  # Admission of this step only; incident remains open.
        if (
            kind == "finish_replacement_check"
            and state["check"]
            and state["check"]["state"] == "verified"
        ):
            return "verified"
        if kind == "finish_replacement_check":
            # This step dispatches no provider operation. If it did not settle,
            # unlock the guided discard choice instead of retrying a bad journal
            # forever as an uncertain admin action.
            return "not_applied"
        if (
            kind == "discard_replacement_check"
            and state["check"]
            and state["check"]["state"] == "discarded"
            and state["check"]["actor"] == actor
        ):
            return "verified"
        if (
            kind == "activate_replacements"
            and state["activation"]
            and state["activation"]["activation_id"] == key
        ):
            return "verified"
        if state["activation"] is not None and kind not in {
            "activate_replacements",
            "finish_replacement_check",
        }:
            result = self.continuation.reconcile(job_id, state["activation"], action)
            if result is not None:
                return result
        if self.inspect(job_id)[1] != action["EvidenceHash"]:
            return "not_applied"
        self.execute(
            job_id,
            kind,
            action["EvidenceHash"],
            actor,
            action["Reason"],
            payload=json.loads(action["InputJson"]) if action.get("InputJson") else None,
        )
        return None
