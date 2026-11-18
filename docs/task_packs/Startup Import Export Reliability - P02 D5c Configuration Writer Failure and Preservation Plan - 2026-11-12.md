# P02 D5c configuration writer failure and preservation plan

## Finding and evidence boundary

The one writer-first attempt is **failed**, not accepted or retried. Receipt
`d5c-config-writer-first-result-94111b1f5b734c7daf6157cf4651a4cc.json`
has verified SHA256
`1ef3224c4457dc171a177f5348ba71be8d657ab8605a276654a566f3558bd639`.
The original actor, wrapper, manifest, intent and receipt remain unchanged.

The outer message `Actor accounting changed` is secondary: its success-only
18-command check ran before checking the child failure. The child records SQLSTATE
25000/native 266 both during change and rollback, five commands, three statements
and seven fetched rows. Its reader factory was never called. The wrapper reserved
the full 18 commands/12 rows before starting it, so this is not a cap overrun.
The transaction attempt consumed one writer invocation; it must not be treated
as an unused attempt simply because the reader did not start.

The writer query fetches rows before calling `nextset()`, but assigns its return
value only after that call. Source plus the seven-row count supports a late-result
error after identity and both three-row results. Their values were not retained;
neither exact changed/restored tuples nor acknowledged rollback can be claimed.
The owned process exited normally with code 1, writer close returned, both outer
connections disposed, and the independent absence query found neither the outer
birth nor sessions bearing the unique actor application identity. Physical
closure is established. Nine paired poststate queries and final resources were
skipped, so current preservation still requires evidence.

[Microsoft's error reference](https://learn.microsoft.com/en-us/sql/relational-databases/errors-events/database-engine-events-and-errors-0-to-999?view=sql-server-ver17)
identifies 266 as a transaction-count mismatch across execution. The actor embeds
BEGIN and ROLLBACK in separate parameterized batches. A transaction boundary
crossing the driver's prepared execution is the leading source-based explanation,
not a recorded RPC trace. No runtime or production defect is established.

Host elapsed 1.6852581 seconds consumes two: **1,435 native seconds remain**,
**50 Windows-test seconds**, **21 inputs consumed**, no maintenance retry.
Configuration scope has 176 seconds left; its later-test suballocation has 118.
Seven of the 64 fixture rows remain consumed. The final 1,000 native seconds
remain reserved for later D5 work.

## Immediate read-only packet

`scripts/collect_p02_d5c_config_poststate.ps1` reuses the accepted admission
collector's identity, resource, source, receipt, history, deadline, SQL-reader and
physical-closure controls. It removes admission/activation/transaction commands
and all actor execution. It invokes only the five existing verification SELECTs
for the seven approved rows, then all existing paired preservation observations.
The final absence query also checks the failed actor's fixed application identity.
The SQL source files and exact proposal remain hash-pinned; no SQL repository edit
or inferred schema is involved. No catalog recollection or retained input reads.

The packet reserves **35 client/control units**: 24 metadata reads, five fixture
reads, four connection open/close operations and two possible cancels. Maximum
returned rows 144; existing 48-unit/2,048-row/512-per-result/1-MiB-receipt limits
remain. It retains three-second statement timeouts, zero lock wait, 30-second work,
42-second cleanup and 45+10-second outer custody limits; manual ceiling 60 seconds.
It uses one work connection, then an observer after disposal, and no child process.
Unknown custody blocks further work. Failure retains evidence; no reset or replay.

## Comparison defect found offline

A negative test changed Version 3 to 4 but the inherited fixture comparator did
not reject it. It converted rows to JSON strings, then passed those PowerShell-
wrapped strings through generic canonicalization, which compared their Length
properties. This is a test-helper defect; original executed files are preserved.
The new read-only packet compares sorted JSON text with ordinal equality directly,
including exact cardinality. The failed validator output and first prepared
collector are retained under `.codex_artifacts/p025`.

The accepted admission remains supported by its separate Python adjudicator,
which compared every complete row dictionary to the frozen expected values, not
string lengths. Equivalent `Assert-FixtureRows` callers are the original admission
and this follow-up; the original is evidence and must never be rerun. Future
configuration packets must use exact value comparisons. The broader general
canonicalizer is not changed in this packet; paired metadata uses object rows.

## Validation and continuation

161 offline PowerShell checks pass, including same-length version/identity/key/
state/hash mutations, duplicates, missing rows, remoted lists, typed GUID/binary/
date values, source/lineage hashes, read-only SQL membership, budgets and custody.
Targeted source/AST checks are appropriate; full application startup, pytest,
command registration and smoke imports are skipped because no application or
command runtime changed and this diagnostic must remain offline until handoff.
Security routing is **Changes review, Deep off**, for this collector, validator
and plan only. Completion of that review is required before the manual handoff.

After the read-only receipt, independently compare all seven rows and protected
state before considering continuation. A successful follow-up is later evidence,
not retroactive success of the failed attempt. Then prepare a versioned test-only
writer correction: separate transaction control from parameterized data batches,
retain fetched rows even if final result draining fails, and report the primary
child error before success accounting. Reconcile all controls within 48 units;
do not raise a limit or suppress error 266. Cover change/rollback nextset failures,
cleanup uncertainty, representation and exact identity with offline tests and
review before proposing another attempt. No corrected writer or retry is included
in this handoff. Committed transition/stale-action tests stay pending. D5c/d/e/f
and separate deployment authorization remain open.

## Reviewed handoff

Full Changes review `08b02dbb-1429-4853-a7d3-a2dbb48e9dfa` completed with zero
security findings and one operational blocker: a retained admission predicate
expected 17 steps instead of five. No native follow-up had run. The original
prepared files remain preserved. Correction review
`7d650cba-0acc-45ba-b9cd-576e02627f67` at `04f1b16c` completed with zero findings
and no remaining blocker; both sealed results were read back. The actual entry
predicate now accepts five and is tested against 0/4/6/17. **167 offline checks
pass**. The selector, deferred and security-routing gates pass; architecture
validation examined zero Python files because this patch contains only PowerShell
and documentation. No application or deployment tests were run.

Final collector SHA256:
`a3ab86a1c504a3e3383a4b5f417267ca105e442897c0dde5e92484ae585edb77`.
Manifest SHA256:
`30528db3f26ae3fffb341464472bf87eeffda02925a4f84e77753c6c7ea9261a`.
Measured review usage: original 3,223,415 tokens; correction 1,798,533 tokens.
One manual read-only attempt is ready within existing authorization, followed by
receipt adjudication. It does not authorize or perform a writer retry.
