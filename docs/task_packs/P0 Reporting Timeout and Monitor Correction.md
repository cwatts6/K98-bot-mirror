# P0 reporting timeout and monitor correction

## Scope and evidence boundary

Approved corrective work continues the existing reporting recovery. The production
report shows an already committed import and two committed reporting stages. The
latest repair failed with SQLSTATE HYT00 while consuming reporting result sets.
The application connection uses a 15-second query timeout; ordinary stats execution
already uses a 595-second query budget. Reporting continuation inherited the short
inspection timeout because it did not create a dedicated reporting cursor.

The correction sets a bounded 595-second timeout before creating that cursor,
drains every result set, closes it and restores the previous connection timeout.
Inspection, cleanup, session locks, ownership checks and stage receipts retain
their existing behavior. The continuation still invokes only the guarded reporting
wrapper. It cannot dispatch the committed import or infer completion from a released
reservation. Failure continues through the existing rollback and reconciliation path.

Monitor reports also retained ProgrammingError failures at queue snapshot reads,
but discarded their SQL codes. The existing rotating incident pages can delay a
fresh check of those saved failures while they keep overall monitoring unhealthy.
The correction retains bounded SQLSTATE/error-number diagnostics without exception
prose, and rechecks a bounded page of failed incidents each cycle before the ordinary
pages. Only a fresh successful observation clears a saved failure. Existing normal
pagination continues, so persistent failures do not prevent other checks.

An isolated restricted-account test reproduces SQLSTATE 42000/error 1222 at the
same queue snapshot under writer contention. It verifies a subsequent successful
snapshot without releasing or changing retained work. This is a demonstrated
failure mechanism, not proof of the original errors whose codes were discarded.
No permission widening, automatic cancellation or blanket healthy classification
is proposed.

## SQL and validation

SQL source of truth remains `C:\K98-bot-SQL-Server`, pinned contract commit
`85ccbd4c68936d5ae82f1850bcf25e178a6d7267`. The existing reporting wrapper,
private core, stage receipts and ownership guards are unchanged. No SQL migration
or new grant is required. SQL test connections now forward their timeout property
to the real driver rather than shadowing it in a Python fixture.

Required regression evidence includes the old 15-second timeout after stage 2,
successful stage-3 continuation with the corrected budget, unchanged first/second
receipt timestamps and scan identity, and duplicate acknowledgement readback with
exactly one execution of each synthetic stage. Restricted-account denial tests for
direct archive/core execution remain required. Cursor creation, execution and
result-drain failures must restore the short timeout. Monitor tests cover redaction,
saved failures outside rotating pages, scoped failure selection and successful
fresh-check clearing. Run isolated SQL tests, full private pytest with operational
log hygiene, architecture/deferred/security-routing gates, smoke, registration,
formatting and lint. Verify all three installed SQL contract comparators using the
restricted login in the local reference database.

Security route: **Changes**, Deep off, exact final mirror and private diffs.
There is no SQL repository diff to scan. Review parameterization, scope, unchanged
execution guards, bounded diagnostics and retained failure semantics.

## Promotion and acceptance

Prepare mirror and private bot PRs through patch-based promotion. Validate installed
r10 updater compatibility against the exact private predecessor and candidate,
qualify a source-only packet and rehearse protected source installation/re-entry.
The installed r10 tool refuses the protected monitor files without an exact
transition. The replacement updater adds one fixed four-file bundle with exact
predecessor/candidate hashes, retaining all earlier transitions and registry bounds.
Missing or changed companion bytes remain refused. The operator package must
identify reviewed heads, checksums, CI/review results, fixed updater upgrade/deploy
commands and interruption handling. Do not merge or deploy as part of implementation.

After operator deployment, recheck the original reporting incident and submit the
offered remaining-report repair once. Require durable stage 3, preserved import
identity and stages 1/2, and resolved reporting state. A timeout or unknown result
requires evidence/reconciliation, not another submission. Check monitor codes and
fresh observations separately. Capture, caches and provider export retain their
own completion receipts and recovery actions.

All F01-F05 acceptance obligations remain open until their required evidence is
present. Retain the accepted 715-second / 132-request publication check and verified
415-row startup cache with 29 September provenance. Do not repeat either. Wider
timing optimisation remains deferred; tracked-view restoration is unconfirmed P1,
and the full P1 programme follows P0. This corrective release is not P0 acceptance.
