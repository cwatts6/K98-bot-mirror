# P0 Publication Timing Visibility

## Scope and evidence

The operator's saved KVK 16 publication check completed at 2026-10-20 19:42:10.998
UTC with outcome confirmed and duration 810.3 seconds. This proves that saved
check, not the cause of its duration. The latest complete report has zero open
incidents; all P0 acceptance obligations remain mandatory.

The authority runs in a separate interpreter. Its startup path did not install
a logging handler or enable INFO. A fresh-interpreter reproduction loaded its
runtime imports and observed zero root handlers, effective WARNING and disabled
publication phase INFO. Therefore the new phase records cannot be assumed present
in the operator's logs. Do not ask the operator to repeat a publication check merely
to reproduce this logging defect.

## Focused change

Enable one dedicated UTC stderr handler for the publication timing child logger
at authority startup. Keep root logging unchanged. Emit only the existing fixed
phase, completion flag and monotonic duration. Do not log provider contents,
credentials or exception prose. Repeated configuration must not duplicate lines.
No SQL, pacing, provider request, ownership, settlement or replay behavior changes.

The five phase measurements distinguish retained history, provider readback,
sealed history, sealed response replay and final origin verification. This patch
repairs observability; it does not claim a reduction of the 810-second duration.
Existing saved request timings remain useful for provider/pacing attribution.

## Validation and remaining release gates

Two fresh-interpreter regression cases passed: normal completion and an exception
whose exact outcome is preserved. They exercise authority startup up to a deliberate
stop before manifest access or SQL; timings are emitted exactly once and unrelated
INFO/private text remains absent. The combined publication/reconciliation selection
passed 163 tests in 167.95 seconds. Final lint, Changes security review, mirror/private parity,
exact updater transition and protected package rehearsal remain required before
deployment readiness. No production action has been performed.

After deployment, collect bounded phase records from the authority log for an
authorized check when one is needed. Retain the already confirmed receipt. Use
those timings and durable request evidence to choose the performance change;
do not weaken pacing or skip independent verification based on elapsed time.

## Remaining P0

Publication performance investigation proceeds alongside guided rollover
qualification. Missing-evidence/configuration conflicts, interrupted producers,
remaining pipeline stages and complete cross-family acceptance remain in
`P0 Final Recovery Acceptance.md`. No recovery gap is deferred to P1.
