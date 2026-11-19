# P02 D5c Stats inspector acceptance and account-lock plan

## Accepted result

The full Stats inspector global-owner-first result is accepted. Receipt
`d5c-stats-inspector-owner-result-5f2ec34a93a84a08ad22997b7c95dfbc.json`
has SHA256 `aaba1779da757e828021fcf65ce3bcae3e6005510efa5577462022c5892d9a95`.
The actual inspector raised the expected `ImportExecutionActive`, acknowledged
reader rollback/closure, and the holder subsequently proved its exact global
lock remained exclusive before owned rollback and closure. The process exited
normally; the independent observer found no matching work or actor sessions.

Both preservation observations agree: all eleven synthetic records, original
failure history, completed maintenance, permissions, ownership, candidate
definitions and statistics are preserved. Removed test accounts remain absent.
The original database remains protected. The packet used 48 reserved operations
and returned 108 rows, without any error or forced termination.

Full host elapsed time was 1.5278024 seconds, charged as two seconds. The saved
acceptance is `d5c-stats-inspector-owner-acceptance.json`. Remaining allowances
are 1,357 native seconds (including the 1,000-second later-phase reserve),
50 Windows-test seconds and 53 available synthetic rows. Eleven of 64 rows and
all 21 retained inputs remain consumed. This completed attempt must not repeat.

## Next distinct case

The account-owner-first packet invokes the same full Stats inspector once for
the same pending legacy fixture while a separate owned connection holds that
fixture account's existing mutex. It uses the actual unchanged
`coordination_lock_name` implementation. The expected resource is
`k98-export:e5a935323893e701666ff402d32c07ff2eef0f63259bdfc6d56808a4f0a904da`.

The actor records both actual availability query responses. It requires global
availability equal to one, then exact account availability equal to zero,
followed by the typed active-producer refusal. A global refusal cannot satisfy
this account case. Reader closure must be acknowledged before the holder is
verified exclusive, rolled back and closed. Unknown cleanup stops dependent
work and never authorizes a retry or forced session termination.

No application source, schema, ownership, permission, isolation setting or
retained record changes. No new fixture row, import, report, maintenance,
backup, provider request or recovery mutation is admitted. This case does not
prove other routes, reader-first ordering, fresh observations or action safety.

## Unchanged limits and preservation

The full packet still reserves 48 client operations: 21 outer metadata calls,
six outer control/cancellation operations and 21 actor operations. The actor's
exact expected count is ten SQL calls and seven rows; the additional account
probe is measured in the actual-source inert tests. Total planned rows are 112
under the unchanged 2,048-row ceiling.

The old standalone `copySessions` enumeration is replaced by a scalar count in
the adjacent one-row preservation query, using its identical database/user/
own-session exclusion filter. The count must be zero before the actor starts
and after it closes. Thus no absence gate is removed, no statement/row cap is
raised, and no session identity is invented. Actual work/actor birth absence
checks remain independent at the end. All other metadata statements, old
fixture hash and four-row byte-sensitive predicates are unchanged.

The manifest is 130,054 bytes under its existing 131,072-byte cap. The unused
duplicate `reader.expectedPreparation` is omitted; the complete proposal,
source bundle and preservation predicates retain the exact values. The 1 MiB
receipt limit, 60-second full packet ceiling, fixed VM, disk/log/version-store
reserves, 20-second actor watchdog, parent process custody and no-repeat intent
remain intact. This is a distinct already-authorized case, not a consumed retry.

## Validation and review gates

Thirteen isolated Python tests passed against the full unchanged source bundle,
including exact account refusal, mistaken global refusal, identity/scope/owner
failures, cleanup uncertainty, exact-byte preservation and unlisted SQL refusal.
244 Windows PowerShell 5.1 checks passed for parsing, pinned sources, remoted
evidence, negative results, identical session filter, custody and numeric gates.

The authoritative ExportPreparation schema and previously verified source pins
remain unchanged. No SQL repository patch is produced. Repository validators
and explicit test selection are recorded with readiness. Full pytest, command
registration, broad application imports and release tests remain outside this
isolated qualification packet; no runtime or deployment change is introduced.

Security routing is a focused immutable Changes review, Deep off, because the
new test packet reads SQL and stages an isolated process. Complete independent
review is required before the console handoff. No native execution is performed
during preparation or review.

D5a/D5b remain accepted; D5c still has partial C01/C04/C05/C06/C09 obligations.
D5d's 38 offline cases are accepted but its physical failure/restart coverage,
D5e and D5f remain open. D6 deployment remains separate and unauthorized.
