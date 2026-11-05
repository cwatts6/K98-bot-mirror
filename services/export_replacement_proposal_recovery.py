"""Abandon an unactivated proposal without recreating its lost approval.

SQL scope and protected policy authorize only investigation and read discard.
The ordinary proposal verifier remains mandatory for new reads and activation.
"""

import json

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity
from services.export_replacement_check_recovery import terminal_read_snapshot
from services.export_replacement_input import replacement_owners
from services.export_replacement_plan import replacement_registration
from services.export_replacement_verification_service import ReplacementVerificationService


def proposal_scope(workflow, replacement_id):
    if any(
        identity(r["ReplacementID"]) == replacement_id
        for r in workflow.activation.dal.chain(workflow.account)
    ):
        raise SourceConflict("An activated proposal requires original-history recovery.")
    record = workflow.proposals.dal.read(replacement_id, account=workflow.account)
    if record is None:
        raise SourceConflict("The original proposal scope is unavailable.")
    row = record["plan"]
    isolated = workflow.proposals.containment.inspect(row["JobID"])
    mapping = {r["OldFileID"]: r["NewFileID"] for r in record["targets"]}
    expected = replacement_registration(
        workflow.registration,
        targets=isolated["targets"],
        replacements=mapping,
        replacement_id=replacement_id,
    )
    if (
        row["ReplacementID"] != replacement_id
        or row["AccountKey"] != workflow.account
        or isolated["outcome"] != "targets_isolated"
        or isolated["actor"] != "recovery:" + row["ContainmentID"]
        or row["Actor"] != "recovery:" + replacement_id
        or len(mapping) != len(record["targets"])
        or row["BaseRegistrationHash"] != expected["base_registration_sha256"]
        or row["ProjectedRegistrationHash"] != expected["registration_sha256"]
        or json.loads(row["MappingJson"])
        != [dict(old=old, new=new) for old, new in sorted(mapping.items())]
    ):
        raise SourceConflict("The abandoned proposal scope does not match protected policy.")
    return dict(
        replacement_id=replacement_id,
        job_id=row["JobID"],
        mapping=mapping,
        token=digest(dict(record=record, isolation=isolated["token"])).hex(),
    )


class _ReadScope:
    def __init__(self, workflow, replacement_id, owner):
        self.workflow, self.replacement_id, self.owner = workflow, replacement_id, owner
        self.registration = workflow.registration
        self._read_receipt = workflow.proposals._read_receipt

    def inspect(self, replacement_id):
        if replacement_id != self.replacement_id:
            raise SourceConflict("Read discard belongs to another proposal.")
        scope = proposal_scope(self.workflow, replacement_id)
        if self.owner not in replacement_owners(self.registration, sorted(scope["mapping"])):
            raise SourceConflict("Read owner differs from protected replacement policy.")
        return dict(scope, owner_email=self.owner)


class _DiscardOnly(ReplacementVerificationService):
    def _admit(self, *args, **kwargs):
        raise SourceConflict("A lost proposal cannot authorize another provider check.")

    def _evidence(self, *args, **kwargs):
        raise SourceConflict("A lost proposal cannot establish successful verification.")


def discard_service(workflow, replacement_id, check_id):
    snapshot = workflow.verification.dal.snapshot(check_id, account=workflow.account)
    if snapshot is None or snapshot["attempt"]["ReplacementID"] != replacement_id:
        raise SourceConflict("Read attempt belongs to another proposal.")
    owner = json.loads(snapshot["preparation"]["RequestJson"])["owner_email"]
    return _DiscardOnly(
        dal=workflow.verification.dal,
        authority=workflow.verification.authority,
        proposals=_ReadScope(workflow, replacement_id, owner),
    )


def inspect_lost_proposal(workflow, replacement_id):
    scope = proposal_scope(workflow, replacement_id)
    keys = workflow.verification.dal.list_for_plan(replacement_id, account=workflow.account)
    snapshots, checking = [], []
    for key in keys:
        service = discard_service(workflow, replacement_id, key)
        snapshot, _ = service._snapshot(key)
        if snapshot["attempt"]["State"] == "checking":
            checking.append(service.inspect(key))
        else:
            snapshot = terminal_read_snapshot(service, key)
        snapshots.append(snapshot)
    if len(checking) > 1:
        raise SourceConflict("Conflicting unfinished replacement checks require investigation.")
    return dict(
        **scope,
        checks=keys,
        checking=checking[0] if checking else None,
        read_token=digest(snapshots).hex(),
    )
