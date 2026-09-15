"""S10E capacity and rollover orchestration; no transaction spans provider I/O.

Providers and termination verifiers are explicitly composed dependencies. SQL state,
lease age and an operator assertion are never proof that an old writer has stopped.
"""

from dataclasses import dataclass
import json

from kvk.dal.new_source_import_dal import SourceConflict, digest
from kvk.services.new_source_export_service import GoogleSheetsTransport, compact_sheets_generation
from services.export_coordination_dal import bounded_json


@dataclass(frozen=True)
class Capacity:
    current_parts: int
    quarantined_parts: int
    protected_parts: int
    required_files: int
    registered_files: int


def capacity(manifest, *, quarantined_parts, protected_parts, slot_count, measured_parts=0):
    """Use the actual header/directory-aware partitioner, including one-period output."""
    if any(
        type(n) is not int or n < 0
        for n in (quarantined_parts, protected_parts, slot_count, measured_parts)
    ):
        raise ValueError("Exact nonnegative pool counts required.")
    if not 2 <= slot_count <= 16:
        raise SourceConflict("A pool requires two through sixteen registered slots.")
    layout = GoogleSheetsTransport.partition_manifest(manifest)
    parts = max(len(layout), measured_parts)
    required = 1 + parts + parts + max(parts, quarantined_parts) + parts + protected_parts
    result = Capacity(parts, quarantined_parts, protected_parts, required, 1 + slot_count)
    if required > result.registered_files:
        raise SourceConflict(
            f"Insufficient registered capacity: need {required} files including index; "
            f"have {result.registered_files}. P={parts}, Q={quarantined_parts}, R={protected_parts}."
        )
    return result


def capacity_for_snapshot(manifest, context, *, extra_quarantined=()):
    """Retain all other assigned representations until an explicit retirement proves release.

    Q counts exact quarantined files. R counts other protected assigned files; it is
    never inferred from a filename, provider label, age or a mutable current vector.
    """
    attempts = context.get("attempts", [])
    confirmed = {j["JobID"] for j in context.get("jobs", []) if j["State"] == "confirmed"}
    published = [a for a in attempts if a["JobID"] in confirmed and a["Phase"] == "published"]
    current = max(published, key=lambda a: a["Fence"], default={}).get("AttemptID")
    quarantined = set(extra_quarantined) | {
        s["FileID"] for s in context["slots"] if s["State"] == "quarantined"
    }
    protected = {
        s["FileID"]
        for s in context["slots"]
        if s["State"] == "retired" or (s["State"] == "active" and s["AttemptID"] != current)
    } - quarantined
    return capacity(
        manifest,
        quarantined_parts=len(quarantined),
        protected_parts=len(protected),
        slot_count=len(context["slots"]),
        measured_parts=max((a["PartCount"] - 1 for a in attempts), default=0),
    )


def checked_plan(snapshot, new_choice, *, actor, reason):
    pool, slots = snapshot["pool"], snapshot["slots"]
    if pool["PoolState"] != "active" or pool["OwnerID"] is not None:
        raise SourceConflict("Only an active, unowned pool can enter rollover.")
    if not reason or not reason.strip() or len(reason.encode("utf-16-le")) > 2048:
        raise ValueError("A bounded rollover reason is required.")
    if new_choice["SourceKey"] != pool["SourceKey"] or new_choice["KVK_NO"] == pool["ActiveKVK"]:
        raise SourceConflict("Choose another season with the same fixed source.")
    if pool["Epoch"] >= 2**63 - 1:
        raise SourceConflict("Pool epoch is exhausted; retire this pool.")
    if not 2 <= len(slots) <= 16 or snapshot["registration_count"] > 8:
        raise SourceConflict("Registration bounds include closed and blocked pools.")
    if any(s["State"] in {"quarantined", "retired"} for s in slots):
        raise SourceConflict("Quarantined or retired slots need explicit disposition first.")
    plan = dict(
        snapshot=snapshot,
        new_choice=new_choice,
        actor=str(actor.user_id),
        guild=str(actor.guild_id),
        channel=str(actor.channel_id),
        reason=reason.strip(),
    )
    return json.loads(bounded_json(plan))


class SourceOutputPoolService:
    def __init__(self, repository, *, transport_factory, termination_verifier, budget_factory):
        self.repository = repository
        self.transport_factory = transport_factory
        self.termination_verifier = termination_verifier
        self.budget_factory = budget_factory

    def run_pending(self, account):
        for operation_id in self.repository.pending(account):
            self.advance(operation_id)

    def preview(self, pool_id, new_kvk, *, actor, reason):
        return checked_plan(
            self.repository.snapshot(pool_id),
            self.repository.choice(new_kvk),
            actor=actor,
            reason=reason,
        )

    def confirm(self, operation_id, plan):
        # Repository rechecks every pinned identity/version before closing admission.
        return self.repository.confirm(operation_id, plan)

    def advance(self, operation_id):
        """Only an injected, explicitly admitted worker calls this; never a status read."""
        operation = self.repository.operation(operation_id)
        if operation["State"] == "completed":
            return operation
        if operation["State"] in {"uncertain", "blocked", "running"}:
            raise SourceConflict("Reconcile the exact retained operation; do not retry it.")
        if operation["State"] == "closing":
            drain = self.repository.drain_snapshot(operation_id)
            proof = self.termination_verifier(drain)
            if (
                not isinstance(proof, dict)
                or proof.get("snapshot_hash") != digest(drain).hex()
                or proof.get("all_writers_terminated") is not True
                or proof.get("remote_outcomes_reconciled") is not True
                or not proof.get("evidence_id")
            ):
                raise SourceConflict("Exact old-writer termination and reconciliation required.")
            self.repository.ready(operation_id, drain, proof)
        claim = self.repository.claim(operation_id)
        if claim is None:
            return self.repository.operation(operation_id)
        try:
            transport = self.transport_factory(operation)
            transport._request_pacer = self.budget_factory(claim.account)
            transport._request_guard = lambda request: self.repository.authorize(claim)
            for file_id in self.repository.files(operation_id):
                claim = self.repository.phase(claim, "private_pending", file_id)
                private = transport.rollover_private(file_id)
                claim = self.repository.phase(claim, "private_verified", file_id, private)
                claim = self.repository.phase(claim, "clear_pending", file_id)
                empty = transport.rollover_clear(file_id)
                claim = self.repository.phase(claim, "clear_verified", file_id, empty)
            index_file_id = json.loads(operation["PlanJson"])["snapshot"]["pool"]["IndexFileID"]
            claim = self.repository.phase(claim, "setup_pending", index_file_id)
            setup = transport.rollover_setup(
                index_file_id, operation["OldKVK"], operation["NewKVK"]
            )
            claim = self.repository.phase(claim, "setup_verified", index_file_id, setup)
            return self.repository.complete(claim)
        except BaseException:
            # Includes request completion/account pacing uncertainty. Never release.
            self.repository.uncertain(claim)
            raise


class SourceOutputPlanner:
    """Offline materialization preflight, outside every queue/ownership transaction."""

    def __init__(self, pools, generation_loader):
        self.pools, self.generation_loader = pools, generation_loader

    def __call__(self, intent_id, input_hash, registration):
        candidates = [
            self.pools.snapshot(self.pools.resolve(registration.kvk_no, file_id))
            for file_id in registration.destinations
            if self.pools.is_index(file_id)
        ]
        if len(candidates) != 1:
            raise SourceConflict("One exact registered pool index is required.")
        context = candidates[0]
        pool = context["pool"]
        files = tuple(sorted((pool["IndexFileID"], *(s["FileID"] for s in context["slots"]))))
        if (pool["AccountKey"], pool["Epoch"], files, pool["PoolState"]) != (
            registration.account,
            registration.epoch,
            registration.destinations,
            "active",
        ):
            raise SourceConflict("Registered pool identity or admission changed.")
        generation = compact_sheets_generation(self.generation_loader(intent_id, input_hash))
        needed = capacity_for_snapshot(generation.manifest(), context)
        return dict(
            pool_id=pool["PoolID"],
            pool_version=pool["Version"],
            registration_hash=pool["RegistrationHash"],
            epoch=pool["Epoch"],
            generation_key=generation.key,
            manifest_hash=digest(generation.manifest()).hex(),
            parts=needed.current_parts,
            required_files=needed.required_files,
        )


def retire_superseded_generations(
    *, pools, coordinator, claim, current_attempt_id, transport, verifier
):
    """Runs after exact new-pointer readback, before the owning job is released.

    Final/unknown retention and uncertain assignments remain protected. Failures
    propagate to owned delivery, retaining claims and any incomplete retirement.
    """
    from copy import deepcopy

    from kvk.dal.source_output_pool_dal import reusable_attempts

    while True:
        snapshot = pools.retirement_snapshot(coordinator, claim, current_attempt_id)
        candidates = reusable_attempts(snapshot, current_attempt_id)
        if not candidates:
            return
        if not callable(verifier):
            raise SourceConflict("Independent retirement termination/reference verifier required.")
        old_attempt_id = candidates[0]
        proof = verifier(deepcopy(snapshot), current_attempt_id, old_attempt_id)
        retirement = pools.retire_generation(
            coordinator, claim, current_attempt_id, snapshot, old_attempt_id, proof
        )
        for member in retirement["slots"]:
            transport.rollover_private(member["file_id"])
            empty = transport.rollover_clear(member["file_id"])
            pools.clear_retired_slot(coordinator, claim, retirement, member, empty)
