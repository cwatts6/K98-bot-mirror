# P0 pipeline decision storage correction

## Scope and cause

The read-only production diagnostic confirms the enabled, trusted decision-history
constraint matches the authoritative SQL schema: 32,768 UTF-16 bytes. The affected
configuration stage has one 20,010-byte decision containing a 19,298-byte full
registration. Appending another full registration for an explicit unfinished
disposition exceeds the SQL limit. The generic Python serializer permitted
65,536 bytes. SQL error 547 rolls back the decision; repeated failed actions are
not applied. The isolated reproduction produces the same named constraint error
and proves the stage snapshot is unchanged.

This is a serialization/SQL-contract mismatch, not a permission failure or a
reason to rerun an import. Earlier export closeout and receipt fixes do not change
this separate pipeline decision journal.

## Correction

- Keep the complete current-registration comparison and locked evidence review.
- For a terminal disposition or independently verified observation, save the
  canonical SHA-256 registration fingerprint instead of another full snapshot.
- Preserve all prior history entries, original registration, previous operation,
  previous state and previous evidence. No history is truncated or rewritten into
  a different representation.
- Continuations still save their full registration, and dispatch still compares
  that snapshot against current registration. Terminal states cannot dispatch.
- Match the existing 32,768-byte SQL limits for pipeline inputs, stage evidence
  and decision history before issuing a write. Exceeding a bound fails closed.

No SQL schema, grants or stored procedures change. No producer reservations,
credentials, URLs, import/report receipts or activation flags change. The updater
contains an exact source transition for the single changed runtime module.

## Validation and acceptance

Test production-sized legacy history followed by disposition and verified receipt
adoption; preserve completed stages and independent import receipts; reconcile a
lost reply after recreating the recovery adapter; reject dispatch from terminal
states; reject exhausted history without truncation. Retain the existing tests
for stale evidence, current-registration changes, foreign account/storage scope,
live workers, permission gating and continuation identity. Exercise the same
regressions under a disposable restricted SQL login with real pipeline checks and
foreign key, and no rights to change import receipts or export resources.

Validate exact UTF-16 serialized boundaries, nonfinite JSON rejection, fixed updater
membership and both source hashes. Run the project validation gates, full suite,
Changes security review, PR reviews and isolated protected updater rehearsal.

Deployment only installs the correction. Afterwards the operator rechecks the
remaining pipeline and confirms its intended stage disposition. Keeping a stage
unfinished records that decision; it does not claim cache freshness or delivery.
Follow the next stage shown by fresh evidence. A later normal new scan establishes
fresh import/export acceptance using the unchanged output URLs. Existing completed
imports and reporting stages must not be repeated. All F01-F05 acceptance obligations
remain; tracked-view restoration and the full P1 programme remain next. The accepted
publication timing evidence is not rerun.

### Deferred Optimisation
- Area: `services/processing_pipeline_receipt_dal.py` decision journal and `dbo.ProcessingPipelineStage.DecisionJson`
- Type: architecture
- Description: A bounded inline history cannot support arbitrarily many separately confirmed continuations carrying full registration snapshots. The correction retains existing history and rejects genuinely exhausted journals before writing; it does not introduce unbounded history capacity.
- Suggested Fix: Scope a normalized append-only decision table with separately referenced immutable registration snapshots, preserving historical action identity, reviewed tokens, previous evidence and restart reconciliation. Migrate only through a separately reviewed SQL contract; never discard prior decisions to make room.
- Impact: medium
- Risk: medium
- Dependencies: Separate Bot and SQL scope, migration and restricted-account validation; preserve existing P0 receipts and P1 priorities.
