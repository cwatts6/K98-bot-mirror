# P0 reporting recovery permission boundary

## Scope and authority

Implementation and disposable validation are approved. Review/scope completed before edits.
This corrective release addresses F03/F05 and retains all F01-F05 acceptance obligations.
It must not merge, deploy, replay an import, release a reservation, change activation flags,
or certify production import/export health automatically. Full P1 follows P0; tracked-view
restoration remains unconfirmed. The accepted 715-second / 132-request publication check
is retained and must not be repeated.

## Evidence and cause

The deployed reporting continuation calls the archive procedure directly before its public
reporting entry point. The restricted application user can execute the reporting wrapper
and validator, but cannot execute archive directly. The confirmed attempt therefore stops
with SQL permission error 229. The committed import and reporting receipts survive.
The recovery service previously recorded only the exception type; reconciliation then
replaced that result with a settlement label, hiding the original driver codes.

## Implementation

- Move the static archive call into the same-owner public reporting wrapper, after exact
  preparation/input/configuration/ownership/session-guard validation. The reporting core
  rechecks each transaction and skips committed stages. No import entry point is called.
- Preserve direct archive and claim-table denial. No grant expansion, execution-context
  elevation, receipt rewrite, or changed business calculation is required.
- Save bounded action-bound diagnostics (SQL state/number, exception type and allowlisted
  code locations) without raw exception prose. Preserve them through reconciliation and
  expose the latest result in the admin UI and batched recovery report. Diagnostics never
  authorize replay or determine durable settlement.
- Install one exact-preimage SQL module through a finite coordinated release profile.
  Reissue the paired source contracts and package the updater policy before deployment.

## Validation and acceptance

Restricted local SQL tests reproduce the direct-call denial, exercise the real validator,
wrapper, DAL and stage receipts, and use counted substitutes only for archive file I/O and
business calculations. Cover missing/changed authority, lost acknowledgements, partial
stage failure and unchanged committed scan identity. Separately qualify the full SQL metadata
and effective-permission contracts using a temporary restricted login on an isolated clone.
Run migration preflight/apply/verify/idempotent resume on a second local clone, plus protected
updater rehearsal, targeted regressions and the private full suite. Review log hygiene.

Security routing: Changes scans for exact bot mirror/private ranges and SQL range; Deep off.
No routine whole-codebase audit. Final review and CI must bind the final commits/package.

After an operator merges and deploys, verify exact source/startup independently of functional
health. Reopen the existing committed-scan incident and confirm only Finish remaining reports
once. Read the resulting stage receipts; continue cache/capture/export only through their
separate retained-work actions. A failed or uncertain repair remains open and must not trigger
another import or blind repeated confirmation. Natural production/provider evidence remains
an operator acceptance step after this release, not a result of local tests.

## Deferred scope

No new deferred optimisation item: this is a bounded correctness fix. Existing timing and
full P1 programme remain in their existing task packs; no broader refactor is included.
