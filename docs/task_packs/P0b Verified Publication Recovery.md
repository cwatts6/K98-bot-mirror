# P0b verified publication recovery

## Scope and current boundary

This is the next focused P0-F01/F05 change after replacement PRs #405/#657.
It is work in progress, not reviewed or deployment-ready. It does not authorize
production repairs, merging or deployment. All other P0-F01 through P0-F05 rows
in `P0 Final Recovery Acceptance.md` remain mandatory; none is deferred to P1.

Replacement PRs #405/#657 are now merged and deployed at private revision
`2726deae890896dd4f87716ce13b2906c071b354`. The protected r2 rehearsal passed.
The 20 October 05:52 UTC report contains 17,492 resolved incidents, no open
incidents or required repairs, and a healthy monitor. ProcConfig import completed.
The updater verified deployment while explicitly withholding fresh import/export
health certification. These observations do not complete P0.

## User outcome

From **Check published outputs**, an admin can select a retained publication by
season/date and input identity without finding a job ID. Listing uses SQL only.
A separate confirmation performs the authority check. The incident includes the
original creation time, retained input, registered output links and a comparison
of original/current output membership. Missing fault facts remain explicitly unknown.

An admin can verify an interrupted source publication and, when exact evidence
proves absence or content damage, queue one separate physical repair using the
original retained source generation. The original uncertain attempt is never
replayed. The original incident stays open until the repair has confirmed delivery,
with a direct Review repair export button while it is pending or fails, and
Return to original export navigation. A repair requiring replacement closes its
parent only after the replacement delivery is independently verified; retirement
alone does not certify delivery.

An initial observational proof refusal must not strand a new admin action ahead
of replacement recovery. Only a durable initial-probe-refusal marker can close
that check as not applied. Unknown retirement or SQL settlement remains subject
to its own receipt reconciliation. Verified nonapplication opens one fresh decision
revision; repeated old confirmations and completion receipts cannot advance it again.

## Implementation findings and fixes under validation

- The retained-output repair path was rechecking current season weights. The repair
  now preserves the exact original input/configuration under its consumed authority
  proof, locked snapshot and separate repair identity. Ordinary new exports retain
  their current-weight check. No weights are recalculated or imported by recovery.
- Queuing a repair previously resolved its original incident immediately. Keep it
  open and linked until independently confirmed delivery. A failure during the
  successor publication must remain actionable through that link.
- An unsuccessful initial publication proof previously left a pending admin action
  whose refresh could fail repeatedly. Distinguish a durably recorded pre-mutation
  refusal from unknown settlement/retirement, preserving all original reservations.
- A finished not-applied action previously owned the unchanged incident revision,
  preventing another guided decision. Advance exactly once after independent
  nonapplication verification; do not advance unknown or successful actions.

Services own decisions and concise context; DAL owns transactions and revisions.
Existing Discord confirmations, private responses and authorization are reused.
SQL contracts are checked against reviewed SQL checkout `b663308a`, including
ExportReconciliationProof, its issue procedure, ExportAttemptPart and RecoveryAction.
No schema migration is currently proposed.

## Acceptance still required before publication

- Validate concise original-input/configuration and output-location presentation;
  distinguish retained configuration from current destination registration and
  explicitly identify unavailable historical input/fault facts.
- Validate actual guided callback coverage for permissions, changed evidence,
  repeated confirmation, lost repair admission reply, restart, failure during the
  successor delivery, and return navigation to the original incident.
- Preserve the strict boundary between complete readback proving content damage
  and missing/changed ownership, ACL, directory or pointer evidence. The latter
  must follow their separately verified recovery paths, not become damage by exception.
- Reconcile damage detection and still-needed captures with the full P0 matrix;
  do not claim all publication failures covered by the three exposed actions.
- Validate current-weight guards for ordinary exports and mismatched repair input,
  including closed season, changed pool registration, quarantine and capacity.
- Run architecture, deferred-item, test-selection and security-routing gates,
  affected tests and full CI. Separate mirror/private Changes scans, Deep off.
- Qualify the exact updater transition, mirror/private patch parity and protected
  package rehearsal. Provide operator verification without manufacturing production
  failures. No final readiness or P0 completion claim before these gates pass.

## Evidence boundary

The disposable tests exercise production policy, actual Discord button/confirmation
callbacks, authority broker and private journals, proof production/consumption,
temporary SQL transactions, separate queue admission, normal capacity refresh and
final delivery. Provider child, host boundary, immutable source-generation loading
and Discord transport are simulated. They do not certify live Google delivery,
native process custody or production admission.

## Operator verification after the reviewed package is deployed

1. Run `/ops dl_bot_status`, open the recovery centre and download the complete
   report. Confirm monitoring is current and compare required repairs with the
   preceding report. A zero incident count alone does not certify live delivery.
2. Use **Check published outputs**. Choose an output you recognise by its season,
   date and retained input. Use **Review output links** to identify its registered
   files. Listing and reviewing these details do not start a provider check.
3. Choose **Check published output** and confirm its displayed consequences. A
   verified unchanged output remains resolved. A complete read proving damage
   opens a separate **Rebuild verified damage** decision. An interrupted export
   proven absent offers **Retry verified absent export**. Do not deliberately
   damage or remove production files to exercise these paths.
4. If a natural eligible incident exists, confirm the applicable repair only when
   the retained output is still needed. The original incident remains open while
   its separate export runs. Follow **Review repair export**, then **Return to
   original export**. Only confirmed delivery closes the original incident.
5. Download the complete report again. Retain the action/repair receipts, original
   uncertain history and any refusal details. An unknown writer, permissions,
   pointer or ownership failure must remain protected and must not claim repair.

No SQL migration, dependency or configuration-flag change is required. Install
this release's matching updater package before the normal protected update;
restart once only when the updater prompts. Do not remove receipts or force a
second startup. Final package hash, CI and rehearsal evidence are release gates.

## Local validation checkpoint

A 418-case affected run passed 416 cases. Its two failures were a changed refusal
message expectation and a synchronous test constructing a Discord view without
an event loop; both tests were corrected. A subsequent 71-case diagnostics,
adapter, UI and refusal run passed. Final temporary-SQL and updater checks are
still running. Architecture, deferred items, security-routing, test selection,
Ruff, import smoke and command registration passed. Pyright returned no errors;
its 25 local dependency/source warnings are not represented as runtime acceptance.
Security route is separate exact mirror/private **Changes** diffs, Deep off.

This checkpoint is not a merge/package approval. Final results belong in the
PR descriptions and exact package verification record.
