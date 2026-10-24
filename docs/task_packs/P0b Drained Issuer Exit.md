# P0b drained issuer exit

## Scope and observed boundary

An operator-reported release stopped before source/seed/start/readiness because
the old issuer remained alive. Read-only native checks showed the old bot and
authority absent and the exact issuer still alive. A guarded administrative
closeout then rechecked protected termination/drain receipts, closed old SQL
session, no open authority session/provider stream, unchanged retained work and
all deployment stages unstarted. It stopped only the exact drained issuer.
Normal same-release deployment resume remains the verification step.

The precise production trigger was not recorded. Do not label a console failure
as confirmed production root cause. Reproduction demonstrates that the current
issuer enters its indefinite supervisor hold when a console write fails after
the protected drain receipt, or when final receipt writing/readback fails.
Successful receipt publication is followed by an unnecessary console flush,
which can also block. Missing process IDs alone never authorize closeout.

## Focused change

After native pair termination, SQL reconciliation and release of both empty
owned jobs, deployment receipt finalization is terminal. Successful handoff exits
without a console write. A finalization failure attempts an immutable private
diagnostic containing only release/request identity and bounded exception type,
then exits with status 12. Diagnostic failure cannot reinstate the supervisor hold.
No source is installed by the issuer. The updater still requires its exact
protected drain receipt and native exit; no missing or partial receipt is accepted.

Failures before successful drain retain the existing published-work supervisor
hold. Normal restart, live writer ownership, business outcomes, retained files,
SQL claims and activation flags are unchanged. There is no SQL migration,
dependency change, process-killing updater fallback or timeout-based claim release.

Reuse: existing `acknowledge_deployment`, `write_new_protected`, native termination,
SQL reconciliation and empty-job checks. The new diagnostic is local to the issuer;
no command/view/DAL layering changes or unrelated refactor.

## Validation and delivery gates

- Main-loop regressions first reproduce four old-code failures; unfinished SQL
  reconciliation and nonempty-job cases already retain the supervisor.
- Test successful receipt with unavailable post-drain console, write failure,
  post-write readback failure, failed diagnostic persistence, exact cleanup and
  absence of a second process pair or unadmitted-role termination.
- Pin one exact issuer transition in the installed updater. Reject additional,
  missing, renamed and foreign transition members.
- Run focused issuer/identity/custody/handoff and updater tests, required repository
  validators, final Changes security review (Deep off), separate mirror/private
  checks, source/package parity and protected package rehearsal.
- Real provider/SQL operations are not part of the unit reproduction. Packaging
  rehearsal does not certify live business outcomes.

## Guided verification

1. Finish the current retained deployment with the normal updater after verified
   closeout. Do not issue another restart for that retained release.
2. After this prevention change is reviewed/promoted, install its matching updater
   package and use the normal update workflow. One Discord graceful restart only
   when the updater requests it.
3. Confirm all four release stages verify, the expected source is installed and
   `/ops dl_bot_status` responds. Preserve any degraded import/export qualification.
4. The new issuer takes effect in the successor. Its deployment-exit behavior is
   naturally exercised when that successor later hands off another release; the
   deployment that installs this fix still drains the predecessor implementation.
5. If finalization fails, retain `deployment-handoff-failure-<release>.json`,
   existing receipts and the updater transcript. Do not restart or clear evidence.
   Diagnose the exact failed stage; a diagnostic is never a substitute drain proof.

All unfinished P0-F01 through P0-F05 in `P0 Final Recovery Acceptance.md` remain
mandatory, including publication outcomes, missing/damaged evidence, producer
continuation, rollover and the complete permission/concurrency/restart acceptance
matrix. This operational fix does not mark P0 complete or move any gap to P1.
