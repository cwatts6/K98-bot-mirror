# P02 D5c approved configuration admission packet

The operator explicitly approved the seven-row fixture and bounded tests from
the configuration fixture plan. Its proposal SHA256 remains
`f4c0258771d7be4032f8345b1b0c42519320de86f1d1b26844beeca7ff0c6813`.
Approval covers the seven exact rows, one rolled-back and one committed version
transition, and one stale-action refusal attempt. This packet performs only the
initial admission; overlap/action checks follow after receipt adjudication.

## Scope and transaction

`scripts/admit_p02_d5c_config_fixture.ps1` and
`.codex_artifacts/p025/d5c-config-admission-execution-packet.json` bind the exact
proposal, source files, accepted preservation receipt and original evidence.
The borrowed console session, host/VM/database identities, resources, isolation,
permissions, first-error history, completed maintenance ledger and candidate
definitions retain their existing guards. No production code or SQL source changes.

Within the owned SQL connection, require no existing transaction, begin one,
and prove all exact fixture keys/account references absent under held update
range locks with zero lock wait. Check the five captured object IDs, no enabled
triggers and no disabled/untrusted FK or CHECK constraints. Insert one preparation,
two idle resources, two memberships, one closed synthetic session and one closed
synthetic stream. Activate only the two exact idle resources with their pinned
versions. Read all seven full rows by explicit column names and compare every
field, case-sensitively and without relying on physical or result row order.
Only then issue one COMMIT and require a zero-transaction acknowledgement.

All values are explicitly typed bound parameters; no SQL identifier comes from
untrusted input. Binary hashes, UUIDs and dates are normalized solely for exact
evidence comparison. Row counts and duplicate/missing/foreign evidence remain
checked. The two resource activations have exact key/version/idle-owner predicates.
The five authoritative table definitions and captured FK graph were checked in
the approved proposal, including the cyclic membership admission sequence.

The synthetic session/stream records are labelled test metadata. They are not
evidence of an actual child exit, provider result, health success or deployment.
There are no provider request/event rows or dispatch calls. No import, report,
maintenance, new demand, installation, permission or isolation change occurs.

## Failure, custody and limits

Before acknowledged commit, any failure attempts owned ROLLBACK once within the
cleanup budget. A failed or ambiguous COMMIT remains ambiguous even if a later
rollback reports no active transaction. Such a receipt cannot authorize replay.
Rollback uncertainty roots the exact connection and fixture state; outer
unconfirmed jobs/runspaces remain retained. Disposal and an independent check
of the captured work-session birth establish physical SQL cleanup. No unowned
session is killed or released. After commit, never delete/reset the seven rows.

The wrapper reuses 24 existing identity/protection/resource observations unchanged.
It does not repeat the six cached maintenance-execution queries: that evidence
is already retained, and this packet invokes no procedure or maintenance child.
Paired ledger/history, permissions, ownership, candidate definitions, original
database protection, physical statistics and resource checks remain. This
scope adjustment fits the new transaction in the original command allowance.

The manifest reserves **24 metadata + 17 fixture/control statements (including
possible rollback) + seven connection/cancellation controls = 48/48 units**.
The successful path normally uses 47 reserved units. At most **159/2,048 rows**
are returned; global 512-row/result, 1 MiB receipt and 128 KiB manifest ceilings
remain. Five full-row reads represent seven rows, with no packed/truncated SQL
evidence. Each SQL statement has a three-second timeout. Work admission stops
at 30 seconds, cleanup at 42, outer stop at 45 plus ten seconds to observe; the
manual handoff requires cancellation/report before 60 seconds.

Current balance is **1,439 native seconds / 50 Windows-test seconds**, 21 inputs
consumed and no maintenance retry. The approved fixture scope remains capped at
180 seconds total: 60 admission and 120 later tests. It cannot use the final
1,000 seconds reserved for later D5 work. This SQL-only admission does not debit
the Windows-test allocation. New fixture rows are capped at seven of 64 total;
after confirmed admission 57 remain available only under separately reviewed
future proposals. No failure resets any allowance.

## Validation and review

517 offline PowerShell checks passed with no native connection, VM call or
application import. They verify parsing, inherited guard/custody helpers, all
24 preserved SQL statements/preimages, proposal/source/lineage hashes, parameter
types and conversions, remoting, result reordering, missing/foreign/duplicate
evidence, exact transaction sequence, every injected stage failure, one rollback,
no retry, and retained owner/original error after commit plus rollback uncertainty.
Only inert fake custody is cleared inside the isolated test process.

Architecture passed with zero Python files; deferred validation passed for all
three documents and security routing reported zero errors/warnings. The explicit
selector ran; broad recommendations are addressed by the skips below. Immutable
whitespace checks remain required.
Full application pytest, smoke imports, command registration and release tests
are skipped: no production runtime/deployment behavior changes and the wrapper
must not run native fixtures on the host. The reviewed test source and packet
remain immutable after handoff. No new production refactor/deferred item.

Security routing: **Changes review, Deep off**, exact collector/validator and
three-document scope delta. SQL source remains read-only, so there is no SQL
repository diff. Native handoff requires completed review and final hash checks.
Receipt adjudication precedes all overlap or stale-action execution. D5c and
all remaining D5 slices remain open; this admission alone is not qualification.

The first admission Changes review (`ae7b58f1-ec62-45ad-9b02-e12161216a02`)
completed with zero security findings. It identified a control-accounting gap:
failed work, owned rollback and closure observation can each request cancellation.
The corrected packet reserves all three, within the unchanged 48-unit ceiling.
No actual overflow was demonstrated because failure skips later observations.
The original script, validator, manifest, document and 516-check log are preserved;
no native admission has occurred. A focused correction review precedes handoff.

The focused correction review `73c48b3d-9c48-40af-bad1-67c2601148c6` is now
completed and sealed at `deb7b2e823994322cd1a1c1265f0a9870c6e6e7b`, with zero
security findings and no remaining preparation blocker. The first corrected
offline run stopped because rewriting line endings broke exact inherited-helper
comparison; original LF endings were restored and all 517 checks passed. Both
logs remain preserved. Deferred validation and security routing passed; immutable
diff whitespace passed. Review usage was 2,496,156 tokens for the first review
(2,430,080 cached input), and 1,931,944 for the correction (1,910,144 cached input).
The final preparation acceptance records the script/manifest pins and confirms
that the native intent is absent. One admission handoff is ready; native success
and the later consistency/stale-action tests remain unproven.
