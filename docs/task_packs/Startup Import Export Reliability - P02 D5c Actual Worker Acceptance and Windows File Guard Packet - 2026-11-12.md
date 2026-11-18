# P02 D5c actual-worker acceptance and Windows file guard packet

## Accepted result and limits

D5a/b are accepted. The single D5c actual maintenance run is now accepted with
observed overlap, durable completion and physical cleanup. Original receipt
`17b03e3cfccc4d02a709a12c2665eddd` remains a failed collector result; follow-up
`f18ca1a3eabf4a20969d5ac624336e3a` supplies the missing bounded poststate, not a
replacement run. Its SHA256 is
`F951EF8C93DED11C038010E97AB8BBFC1E7B8E8884ADA35D844741C13445F3A7`.

Claim `82334f18-8d76-47f1-a0e6-912439287cd3` completed generation 2 for request
`468fc60f-8424-4637-b576-99717c7ad062`. First error 15247 and its timestamp remain.
All five other complete work records and cache identities/counters are unchanged.
The old post_import plan retains count 2; a new plan has count 1, with creation and
execution in the exact actual call window. Its set_options differs (251 versus
4347); the prior D5b recovery explicitly selected ARITHABORT ON. No repeated
execution, eviction or permission change is inferred from cached-plan row count.
Protected metadata, source definitions, physical counts and closure pass.

Acceptance is saved in `d5c-actual-worker-completion-acceptance.json`. Host elapsed
1.4352494 seconds is debited as two, leaving **1,453 native seconds**. **21 inputs
remain consumed; no actual-child attempt is available.** All original evidence
and limits remain binding. No runtime change, deployment or input replay occurred.

## Next scope and architecture

Within the existing approved D5c test-directory scope, prepare one Windows
file-guard foundation invocation. Use the current unchanged `core/file_lock.py`
source and verified Python 3.11.9 on the existing isolated VM. A test-only runner
loads two exact, hash-verified module instances, each with its own untouched
admission registry, and exercises their real Windows handles. This prevents
the process-local registry from being mistaken for physical exclusivity.

The scope is explicitly **one process with independent registries**. It does not
prove cross-process scheduling, crash recovery, reader decode ordering or caller
parity. Those stay open; no whole-C11 acceptance follows from this packet.
No production helper, caller, SQL definition, dependency or deployment file changes.
No new refactor is justified by this fixture; existing caller coverage remains a
qualification obligation, not deferred debt.

The fixture runner owns only a fresh random directory under
`Q:\D5b-20261111\d5c-windows-file-guards-<run>`. The wrapper rejects redirected
ancestors, existing files, changed runtime or source hashes and changed session,
VM, database, resource or history preimages. It stages only a source bundle and
runner, then starts verified base Python with `-I -S -B` and a hidden window.
The bundle uses standard-library code only, with no application startup, pyodbc,
network, provider or additional child process.

## Fixed cases and cleanup

1. Writer A acquires the exact new file object. Writer B, through an upper-case
   and parent-directory alias, must time out immediately without body entry.
   After A's acknowledged release and physical object disappearance, B enters
   once and releases its owned object.
2. Reverse the two independent registry owners and require the same evidence.
3. Create a labelled foreign-sentinel fixture, require refusal with no body
   entry, and preserve its exact 53 bytes and SHA256. Leave it as evidence.

Every admission uses timeout zero; no sleeps, retries, age/PID takeover or
registry clearing. The helper releases only its own handle-created object.
The actor checks both registries for unresolved custody. The wrapper verifies
normal exact-process exit, output bounds, fixed case identities, source hash,
zero active/uncertain custody and physical object absence, then independently
hashes the retained foreign sentinel. A forced termination is failure, never a
successful drain; uncertain exact-process custody is retained and dependent work
stops. No arbitrary process or foreign file is killed or deleted.

The inherited SQL preparation/poststate ledger remains exactly the reviewed
read-only diagnostic's 30 statements, six reserved connection/cancellation units,
171 maximum metadata rows, 48-unit/512-per-result/2,048-total ceilings. It checks
the exact accepted six full completed work records and candidate/permissions/
ownership/backup/source protection around the file actor. File work adds zero SQL
commands. At most one metadata connection is open during the one Python actor;
the closure observer follows confirmed work/process closure only.

Actor work deadline 10 seconds; wrapper process deadline 15 seconds; total work
30 seconds/cleanup 42 seconds; outer watchdog 45 plus 10 seconds and manual stop
before 60 seconds. The one-MiB receipt, 64-KiB individual actor files, disk reserves,
log/version-store ceilings, fixed 8-GiB/4-CPU/zero-NIC VM and existing 1,800-second
aggregate limit remain. Debit full host duration rounded up from 1,453; retain
the original D5c Windows allocation and at least 1,000 seconds for later slices.

## Preparation validation and review

Six isolated Python tests passed with inert guards only. They check both schedules,
foreign-file preservation, refusal of a bypassing guard, unconfirmed custody,
deadline-before-admission and source hash refusal before execution. No native
Windows lock or guest work was run by these tests.

The first PowerShell validation found that pipeline-wrapped strings were compared
as object metadata when checking case names. Its source, tests and failing log
are preserved as `d5c-windows-file-guards-first.ps1`,
`d5c-windows-file-guards-first-tests.ps1`, and
`d5c-windows-file-guards-offline.txt`. Only the new case-name check changed to an
explicit fixed-name/count comparison. No production comparison helper changed.
The corrected wrapper passed **82 offline PowerShell 5.1 checks**, including
remoting, malformed/missing evidence, process cleanup admission, source/manifest
pins, unchanged SQL ledger and byte-identical inherited safety helpers.

Security routing: **Changes**, Deep off, exact Bot-only packet/test/documentation
delta from `0de81220d360898aaa7cee8299559884037a77c3`. Fixed staging, owned process
and elevated receipt handling require review before handoff. SQL definitions and
queries are unchanged, verified against the accepted diagnostic; no SQL repo
diff or separate SQL scan is introduced. Architecture (two Python files), deferred
items (three documents), security routing (zero warnings/errors), explicit-path
test selection and Ruff passed. Changes review and immutable whitespace checks
are pending. Full application imports, whole pytest/native fixtures, Discord command
registration and release checks are skipped because this isolated fixture changes
none of those surfaces and startup/native execution is outside offline scope.

## Remaining sequence

After this receipt is adjudicated, continue C11 actual caller parity and C08
Windows authority scheduling with unique owned fixtures. C01 full inspectors/
account orders and diagnostic variants remain distinct from accepted guard tests.
C04-C06 committed synthetic tuple/CAS tests still need exact IDs and full foreign
key closure, then the reserved explicit approval. Native restricted-rights and
disabled-SNAPSHOT cases lack an authorized supported path; retain those gaps until
an explicit concrete exception or disposition is approved. Do not silently count
offline substitutes as native passes.

D5d failure/recovery schedules, D5e balanced cost comparisons and D5f final
obligation reconciliation remain. D6 production release and D7/P05 acceptance are
separate. P03 blockers and essential P04 work precede the first normal import/export.

## Reviewed handoff ready

Changes review `6532fff9-efe4-4b94-ae6d-c5deb8ff2684` completed with zero findings,
all seven changed paths covered, and no independent correctness/handoff blocker.
Immutable range `0de81220d360898aaa7cee8299559884037a77c3` to
`05133c8876435722ae95bec8aca0284978f08962`. Canonical sealed results were read back.
Measured review usage: 1,927,842 total tokens, 1,898,496 cached input tokens.
Snapshot whitespace passed; all seven working files matched before this status
appendix. The normal branch/index and unrelated work remain untouched. This
appendix changes no executable behavior and needs no repeat scan or native test.

One manual invocation is ready under existing approval:

- Script SHA256: `5B94A64D66057B7405C3D832A3F979B293B6F302B7B9FB7D583DAC327CA60B47`.
- Manifest SHA256: `09e08b25185b9c8054e21424d98b4df7d434733dd6b8546d85fee34ca22af2b1`.

The execution intent was absent at handoff verification. Use the existing elevated
console and `$global:D5bReportSession`; stop on error/incomplete output, do not
retry, and report full host duration. Keep the window open. No native file check
has run yet. Balance **1,453 seconds**, **21 inputs consumed**, **zero maintenance
retry**; adjudicate the resulting receipt before dependent work.

## Native file foundation accepted

Receipt `d5c-windows-file-guards-result-6d714508e6524b8bbcfc8bd3724ffc2b.json`,
SHA256 `B934BF6F5BF93C8F3C576FD8B4168720D22A803292AAAAC09D4265D792D52127`,
passed local adjudication. Both held-writer/alias refusals and post-release entries
passed. The foreign sentinel bytes remained exact. PID 4148 exited normally,
without forced termination; all guard custody and physical cleanup checks passed.
The full completed ledger, all six cached-procedure records (including both
post_import plans), protected metadata and before/after state remained unchanged.

Host duration 1.4254922 seconds debits two. **1,451 native seconds remain**, with
two seconds consumed from the 60-second D5c Windows allocation. The 21-input
allowance remains consumed and zero maintenance retries are available. Acceptance
is `d5c-windows-file-guards-acceptance.json`; it explicitly leaves cross-process,
caller parity and D5d crash/uncertain-close evidence open.

The first local adjudication compared a new connection's connect_time with the
previous packet's connect_time. That assertion draft is retained as
`adjudicate_d5c_windows_file_guards_first.py`. The corrected local adjudicator
treats all four connection-birth fields as invocation-specific, requires them
present, checks a distinct connection identity, and verifies this invocation's
own context and physical absence. No native retry or runtime change occurred.
