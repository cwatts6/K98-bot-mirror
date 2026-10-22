# P0 guided rollover qualification

## Scope and evidence boundary

Complete the existing rollover admin workflow under the deployed action policy:
continue an unstarted operation, verify a completed phase journal, or isolate an
uncertain old pool and complete the original season change on verified replacements.
No old uncertain provider phase is replayed. No schema, dependency or activation
flag change is proposed. This is a focused P0-F04 candidate, not P0 completion.

The operator has authorized implementation, disposable validation, security review,
mirror/private PRs and updater packaging. Merge, production deployment and repairs
remain operator actions. Do not manufacture a live failure to demonstrate recovery.

## Runtime changes

- Enable the ten existing rollover recovery actions only after qualification.
- Run drain/completion proof issuance through the existing single proof worker and
  progress protocol, keeping authority status and health refusals responsive.
- Show original request time, old/new season, saved phase and original/current pool
  comparison. Missing original exceptions remain unknown; a settings difference is
  not identified as the cause.
- Preserve a return path while handling blockers and saved replacement forms.
  Reopened replacement operations reconstruct their original rollover link from
  the hash-checked immutable plan. Every navigation rechecks admin authorization.
- Bound recursive replacement ancestry and reject cycles before loading more history.

Services retain decisions and presentation policy; the DAL and private authority
retain ownership, transactional settlement and proof validation. Views route private
interactions without SQL or provider logic. The private ancestry implementation is
validated in the production checkout; it is not added to the scrubbed mirror.

## Qualification

The production-policy regression originally refused replacement input. The new
end-to-end fixture uses RecoveryService, real admin buttons and confirmations,
saved input revisions, the authority protocol, local temporary SQL, the real
rollover worker, phase journals, proof issuance/consumption and final original
incident closeout. Google responses and native transport are simulated. Native
custody/startup verification belongs to the separate protected package rehearsal.

The matrix covers normal completion; interruption after committed private, clear
and setup pending/verified phases; replacement failure followed by another guided
replacement; and a lost final settlement acknowledgement. A stopped uncertain
operation cannot issue another provider request. Each replacement must finish its
own independent verification before its original incident closes. Earlier uncertain
operations retain their audit state and isolated files.

Existing tests cover old-writer/live-stream refusal, changed season choices,
missing/changed journals, wrong registration, incomplete setup, stale confirmation,
permissions, lost admission replies and exact resource release. Final results and
package evidence must be recorded before merge readiness is claimed.

SQL contracts were checked against the source-of-truth repository and its reviewed
installed-schema checkout at b663308a. Tests use local K98DEV temporary objects only.
No SQL migration is required. Full SQL/provider acceptance is not inferred from mocks.

Security route: **Changes**, exact mirror and private final diffs, Deep off. Final
security and PR reviews, CI and protected updater rehearsal remain required gates.
The updater permits only the complete eight-file `guided_rollover_v1` transition
with exact before/after hashes. It retains the normal protected drain and one-start
protocol. Never manually restart or replay an unresolved release.

## Guided production verification after deployment

### Local review evidence

The guided SQL phase matrix passed eight cases, including lost phase/settlement
acknowledgements; the final normal chain and three existing replacement SQL cases
also passed. Targeted recovery/UI/proof tests passed, as did the mirror selection
(82 passed, two private-only skips), import smoke, command registration and a
38-test operational-log isolation check.

The broad private run reported 8,723 passes, 884 skips and eight passing subtests.
Its 12 SQL-source setup errors were caused by the default older source checkout;
all 23 affected tests passed with the reviewed installed-schema checkout selected.
Its one stale probe-transition assertion was corrected to verify the exact named
rollover successor chain; 127 updater tests then passed. Final CI remains required.

Changes scans c94d8e2c-8b66-480f-8864-a928e478ebbd (private) and
a33b64bc-165f-43d9-9f0c-91d9390f5ac5 (mirror) completed with no findings.
Post-scan changes are limited to this validation record and the test-only exact
successor-chain assertion in `test_probe_busy_transition.py`. They add no runtime,
configuration, permission, persistence or deployment behavior; no additional
security discovery is required for that bounded documentation/test correction.

1. Open the recovery centre and use an existing rollover only if one is present.
   Confirm its original season change and review the concise input/configuration
   summary. Keep copies of any old-season output still needed.
2. For an unstarted rollover, review linked blockers first, return to the rollover,
   and confirm continuation only when the displayed checks permit it.
3. For an uncertain phase, review permanent isolation, enter fresh replacement links,
   verify ownership/blank contents, activate, then confirm the original season change
   on the replacement pool. These are separate saved decisions.
4. Use Recheck while an accepted action runs. Do not issue another check or restart.
   Follow a failed replacement's linked recovery and return to the original.
5. Confirm final independent verification and resolved status, then download the
   complete report. An uncertain original remains uncertain in retained history.

No eligible incident means there is nothing to repair. Healthy status alone does
not prove a future rollover path. Do not change configuration or trigger rollover
solely for release acceptance.

## Remaining P0

All obligations in `P0 Final Recovery Acceptance.md` remain mandatory. In particular,
unattributed legacy delivery holds and loss of all valid ownership/registration
evidence still require their P0-F02 workflow; no new allowlist grants bypass them.
Historical partial producers, durable pipeline stages and the startup cache deadline
remain P0-F03. The final cross-family matrix and natural production acceptance remain
P0-F05. None is deferred to P1.
