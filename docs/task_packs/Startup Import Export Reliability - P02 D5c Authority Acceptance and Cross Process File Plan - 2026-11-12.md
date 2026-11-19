# P02 D5c authority acceptance and cross-process file plan

## Status and authority

The private authority-channel fixture is accepted from receipt
`d5c-authority-pipe-result-316b355fc64441f1877e051106a07939.json`, SHA256
`B97242AD2DE507B005225A5BC92B6DD118CFEE26DF56C50F98E6F1EEA9AA3FBC`.
It proves peer rejection, bounded queue admission, control-message progress,
serialization and cleanup under inert dispatch. It is not a production identity
or crash-recovery acceptance. Its saved independent acceptance records 1,445
remaining native seconds, eight Windows seconds consumed and 52 remaining.

Existing approval to complete the D5 slices covers this C11 test-directory check.
No additional permission, committed SQL fixture, input, maintenance demand,
installation, import, report or production execution is proposed. All 21 inputs
remain consumed. The actual-maintenance allowance remains exhausted.

## Scope and architecture

Two independently owned Python processes use the exact unchanged
`core/file_lock.py` implementation on one fresh qualification-folder lock. The
PowerShell wrapper owns both process objects directly. Neither actor can launch
another process. Both use the existing pinned interpreter with isolated startup,
site loading disabled and bytecode disabled. Seven immutable barrier files bind
the run, role, phase and both exact process IDs to a create-new parent plan.

Actor A holds the lock while B must refuse without entering; after A releases,
B must enter and hold while A refuses. B then releases, A must enter once, and
both actors must exit normally. The uppercase path alias must resolve to the
same lock. The wrapper independently checks the exact eight remaining evidence
files, their bounded contents and hashes, both retained process exits, and the
absence of the owned lock. Prior one-process foreign-sentinel and caller evidence
is retained; this packet does not repeat those cases or perform death tests.

Test harnesses live in `scripts/p02_d5c_file_processes.py` and
`scripts/run_p02_d5c_file_processes.ps1`; tests are in the matching `tests/` files.
Production callers and guard implementation remain unchanged. The 30 existing
read-only SQL observations and all expected preservation values are copied
exactly from the accepted authority packet; no SQL schema or procedure change
is introduced. SQL definitions remain authoritative in `C:\K98-bot-SQL-Server`.
This is bounded qualification orchestration, not a new command/service/DAL path.

## Bounds and custody

- 1,445 native seconds and 52 Windows-test seconds remain before execution.
- Packet ceiling 51 seconds: 45-second host wait, three-second stop observation,
  three-second receipt allowance. Full host elapsed time is debited, rounded up.
- Each actor has a 12-second barrier deadline; the pair has a shared 15-second
  wait budget. Normal guest work stops at 30 seconds and cleanup observation at
  42. No protection may be held beyond the existing 30-second bound.
- The ledger plans 40 units: 30 SQL observations, six SQL connection/cancellation
  controls and four process start/join controls. At most two owned-process forced
  terminations are cleanup-only, staying below 48. All row/receipt caps remain:
  512 per result, 2,048 overall and 1 MiB receipt; each actor output is at most
  64 KiB, each of eight fixture records at most 4 KiB.
- Existing VM identity, fixed RAM/CPUs, isolation, volume identity, disk reserves,
  log/version-store checks and all history/source pins remain mandatory.
- Only retained, directly created process objects may be terminated. Unknown
  owners remain rooted in the guest; an uncertain job/runspace remains rooted in
  the calling console. SQL closure observation is refused if either actor's exit
  is unconfirmed. No broad process search, foreign kill, reset or evidence delete.
- A create-new execution intent prevents automatic replay. Any error, forced
  termination, incomplete witness or changed state stops acceptance and requires
  adjudication; there is no test retry in the native packet.

## Offline findings and retained first failure

The first six-test preparation run failed with `PermissionError(13, 'Permission
denied')` in one actor and a peer barrier timeout. Its original actor, test file
and log are preserved under `.codex_artifacts/p025/` with `first` or
`offline-python` names. That version did not retain the exception traceback, so
the exact failing operation cannot be established. Adding traceback retention
produced a passing diagnostic run; a bounded ten-case diagnostic did not reproduce
the failure. This is **not evidence of a root-cause fix** and does not overwrite
the original failure or justify any production change.

A deterministic injected publication-denial test now proves the original error
is propagated, publication is attempted once, owned protection is released and
no successor evidence is invented. All seven offline Python tests pass. The
149 PowerShell checks cover remoted evidence, both actor orders, changed/foreign
witnesses, normal/forced/unknown cleanup, partial launch, no observer admission
with uncertain custody, unchanged SQL/history and manifest/source pins. A real
Windows access refusal still causes this packet to stop; it is never retried.

The unexplained preparation-only access refusal remains an explicit reliability
limitation for independent review. Cross-process native evidence is pending.

## Review and validation gates

Security decision: **Changes review**, Deep off, restricted to the four new
harness/test files and this three-document acceptance update. These files handle
process ownership and filesystem effects; a security skip is inappropriate.
Baseline `fb82c738e977734bdaa20aaf1e46b0628f2e7303`; the immutable review head,
review result and exact handoff hashes will be recorded after validation.
No SQL-repository diff is introduced. Read-only metadata queries are unchanged.

Ruff, focused offline tests, architecture, deferred-item and security-routing
validators, selector and whitespace checks are required. Full application pytest,
smoke imports and command registration are skipped: no app runtime/registration
code changes, and app startup is outside this bounded offline preparation. The
tests exercise protocol and ownership with fake native locking/processes; they
do not count as native cross-process qualification. Existing scoped packet-helper
duplication is retained to preserve immutable earlier scripts; this adds no
production abstraction or deferred release requirement.

## Completion boundary

No console handoff before final review. Native acceptance requires both results,
exact peer witnesses, post-release admission, unforced normal exits, unchanged
metadata and confirmed connection cleanup. D5c remains open for other obligations;
D5d recovery, D5e performance and D5f reconciliation remain. D6 release and live
acceptance are separate and are not implied by this plan.

## First review and bounded harness correction

Changes review `ee726653-40bf-4109-9998-47598762658b` completed for baseline
`fb82c738e977734bdaa20aaf1e46b0628f2e7303` to
`5b37b067f9e752b313741e0b4add91aefa84e254`. All seven files were covered, with
zero security candidates and one definite operational handoff blocker. The
actor's mutation filter refused `mkdir` on its existing fixture root, while the
unchanged guard always checks that parent with `mkdir(exist_ok=True)`. The fake
guard in the initial protocol tests omitted that parent check. No native handoff
occurred. The reviewed first actor/test/wrapper/manifest remain separately saved.

The corrected harness permits only a mkdir check on the existing fixture root;
root removal, chmod, utime, file writes and creation of a missing fixture root
remain refused. Production guard bytes are unchanged. An added regression uses
the actual guard control flow, omits module-level native DLL binding and replaces
only native owners with fakes. It verifies the parent check, single body entry,
release and empty custody, plus forbidden root mutations. Eight Python tests pass.
This deterministic harness defect does not explain the earlier intermittent
offline PermissionError, which remains preserved and unlocalized.

The corrected actor hash is carried in the manifest and the manifest hash in
the wrapper; SQL, expected states, budgets and native scope remain unchanged.
The corrected immutable review uses `5b37b067` as its baseline. Native work awaits
that review and the same one-time handoff requirement.

## Corrected packet reviewed and ready

Changes review `8ace1922-1759-47ec-b88a-50a05c6cdad6` completed and sealed for
`5b37b067f9e752b313741e0b4add91aefa84e254` to
`9cb9e8e85fad9e183e582ff3ee92655f8d7c343c`, covering all four changed files.
The prior mkdir blocker is resolved, with no security candidates or additional
concrete handoff blockers. The original intermittent access failure remains an
explicit preparation limitation, not a resolved production issue. Both canonical
sealed review results were read back. First review measured 2,400,792 total tokens
(2,368,384 cached input); correction review measured 1,883,602 total tokens
(1,874,432 cached input).

Eight offline Python tests, 149 PowerShell checks, Ruff, architecture, deferred
items, security routing, selector and immutable whitespace checks passed. Skipped
application/release tests retain the rationale above. All seven packet/evidence
working files matched the final snapshot before this status appendix. Fourteen
lineage/history pins, exact production guard, bundled actor and source hashes
matched. The native execution intent is absent. Normal HEAD/index are preserved.

Preparation acceptance is saved in
`.codex_artifacts/p025/d5c-file-processes-preparation-acceptance.json`.
The ready one-time handoff uses:

- Script SHA256 `37AAA929EC771928FF567E7CBF6B38BB5B6A9F0339063FD4131CECFEAA4B4C9B`.
- Manifest SHA256 `38633d28d05929f51ac2310829d5ccb8039b2797a34e996c6c86f90f96578246`.
- Existing `$global:D5bReportSession` only, full host stopwatch required, stop
  on any error/incomplete result and cancel/report a hang before 51 seconds.

No native attempt has occurred. The balance remains 1,445 native seconds and
52 Windows seconds, with 21 inputs consumed and no maintenance retry. This final
evidence-only appendix changes no executable bytes or scope.

## Native two-process acceptance

Receipt `d5c-file-processes-result-22f295f3cedc4f57882dd3c156c9ab5c.json`, SHA256
`EB5D677136D98B087DEC00933B2C3C4DC7A0DB47DF57561150BFB64442E706AF`, passes
independent adjudication. Both exact actors (5316 and 5944, distinct recorded
births) refuse while their peer holds protection, enter once after release and
exit normally without forced termination. The seven barrier witnesses and
parent plan match the exact run and role/PID mapping. All eight independently
read final files match their byte counts and recomputed hashes; the owned lock
is absent. Both registries are empty and no external attempt was made.

All 30 preservation observations passed: 40 reserved command units, 109 rows,
unchanged protected state, full completed ledger including original failure,
verified resources and physical SQL connection cleanup. Source guard and packet
hashes match. Acceptance is recorded in
`.codex_artifacts/p025/d5c-file-processes-acceptance.json`.
Full host elapsed time 1.8283451 seconds debits two. Current balance is **1,443
native seconds, 50 Windows-test seconds, 21 inputs consumed, no maintenance
retry**. This accepts C11's normal cross-process arrival orders. Crash and
uncertain-close schedules remain D5d, and the original intermittent offline
PermissionError remains unexplained; this native pass does not overwrite it.
