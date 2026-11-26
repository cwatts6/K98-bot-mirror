# P02 D5c caller acceptance and existing pipe runtime inventory

## Current evidence and scope

The eight actual file caller critical-section cases are accepted by
`.codex_artifacts/p025/d5c-file-callers-acceptance.json`. The immutable native
receipt SHA256 is `4D707D332E754C771B5D70C5330CC584104EAD495786B10910F7F390F03C5768`.
Its 1.9503936 host seconds consumes two, leaving **1,449 native seconds** and four
seconds consumed from the 60-second Windows allocation. The 21-input allowance
remains consumed; no maintenance retry or new demand is available. Original
failure evidence, the six completed work records, cached execution history,
candidate definitions and protected metadata are unchanged. C11 cross-process
and D5d crash/uncertain-close evidence remain open.

C08 needs the existing Windows pipe runtime. The reviewed source uses pywin32
for private pipe creation, exact local peer authentication, overlapped messages
and handle cleanup (`core/export_execution_host.py`,
`core/export_process_identity.py`, `scripts/run_export_authority.py`). Earlier
Python/pyodbc inventory did not establish those files. This prerequisite check
does not run the old native test or start an authority listener.

## Concrete next execution

Run `scripts/collect_p02_d5c_pipe_runtime.ps1` once in the same elevated Windows
PowerShell 5.1 console, borrowing `$global:D5bReportSession`. The helper pins the
host, exact session/VM identity, running state, four CPUs, fixed 8 GiB memory,
zero network adapters, host disk reserve, guest identity and exact Q volume.
The 8 GiB host-memory floor remains a pre-start rule; it is not reinterpreted as
a post-start or guest-memory gate.

Only these eight existing paths under
`C:\discord_file_downloader\venv\Lib\site-packages` are inspected:

1. `win32\win32api.pyd`
2. `win32\win32file.pyd`
3. `win32\win32pipe.pyd`
4. `win32\win32security.pyd`
5. `win32\win32event.pyd`
6. `pywin32_system32\pywintypes311.dll`
7. `win32\lib\pywintypes.py`
8. `pywin32.version.txt`

No recursive search, directory inventory, file contents in receipts, Python or
DLL loading, SQL connection, pipe creation, workload, installation, permission
change or database/VM change occurs. It returns present/absent, bytes and SHA256.
Absence is a successful observation, not permission to install. Hashes do not
establish loadability, binary provenance or security of the installed package.
Future native packet review must pin observed bytes and preserve containment.

Every existing path ancestor is checked for reparse points, including when the
leaf is missing. A present file is opened read-only with shared reads, capped at
32 MiB and hashed through the same held stream. Fixed ordered result paths are
checked after remoting. Guest C/Q reserves stay at 8 GiB. Thirty seconds bounds
the guest result (25-second between-file cutoff), a 35-second owned-job wait
and the existing 45+10-second outer deadline remain below the 60-second manual
ceiling. A blocked read is subject to that outer deadline. Unconfirmed jobs or
runners are retained and stop dependent work; borrowed sessions are not removed.

The host writes one create-new intent and a unique receipt below the existing
artifact directory. A second invocation refuses the existing intent. Receipts
are capped at 1 MiB; remote output at 64 KiB. No SQL row/statement allowance is
spent. Full host elapsed time is charged rounded up against 1,449 seconds and
the Windows allocation. No automatic retry, reset, deletion or follow-on action.

## Validation and review decision

58 Windows PowerShell 5.1 offline checks passed. They parse the packet without
running it, test accepted/remoted/missing-file results, reject 15 malformed
result variants, compare host and guest fixed allowlists, and verify deadline,
custody and effect restrictions. The first validator's AST `SafeGetValue` call
was unsupported for an array expression; its source and failure log are retained.
The corrected validator reads literal AST nodes and executes no guest code.

Python tests, bot startup/Discord registration, native Windows/SQL tests and
release smoke tests are skipped: no Python runtime, app or SQL source changes.
The architecture/deferred/test-selector/security-routing gates are run for the
new PowerShell packet and these evidence documents. SQL source is unchanged;
the new collector contains no SQL. Runtime/security review is limited to the
actual added collector/validator and evidence updates.

Security decision: **Changes**, Deep off. Base is
`49b9483352046cac7d1ae6b1b15e80acb00b1ba7`; the immutable review head will contain
only the two new PowerShell files and three evidence documents. Review checks
read-only dependency access, exact borrowed-session routing, reparse handling,
bounded output/time, create-new evidence and retained uncertainty. No production
promotion is included. Native handoff waits for this review to complete.

## Following this receipt

Adjudicate availability, exact bytes, deadlines and host debit before building
C08's unique private-pipe fixture. That later fixture must use inert dispatch,
bounded active/waiting admission, serial control progress and physical cleanup;
it remains a separate reviewed execution packet. C11 cross-process, wider SQL
contention/permission/isolation cases and D5d/e/f remain unresolved. D6 production
release and D7/P05 live acceptance remain separate from this qualification.

## Offline custody correction before handoff

Initial Changes review `f3ea84d8-9684-427a-8653-00ce3775dcaf`, range
`49b9483352046cac7d1ae6b1b15e80acb00b1ba7` to
`ba6e06fa2ff8c8634ddcb366055d5b0d43620554`, completed with zero security findings
and all five paths covered. Its independently identified operational blocker
was retained explicitly: an unfinished job was saved in a worker-runspace global,
then the outer caller disposed that runspace. That draft was never handed off or
run. The immutable snapshot and original offline evidence remain available.
Measured review usage: 1,811,562 total tokens, 1,789,056 cached input tokens.

The correction passes the exact job back through shared control state and retains
the owning runner in the user's console whenever a job is unresolved. The outer
deadline path retains the runner even when stopping it acknowledges completion;
unknown cleanup is never converted into permission to continue. Normal confirmed
completion alone disposes the runner. No remote operation or limit changed.

68 PowerShell 5.1 checks now pass, including actual separate-runspace transfer of
an inert object, reference identity of retained job/runner/session, retained
runspace inspectability, joined-stop custody and confirmed-path disposal. This
adds no guest activity. The earlier 58-check result remains historical evidence.
The prior completed native packets are immutable and are not replayed to test
their timeout branches; their accepted receipts demonstrated normal completion.
All future D5 packets must preserve outer-console ownership on uncertain cleanup;
D5d must exercise that branch without mistaking successful-path evidence for it.

The narrow correction requires its own Changes review of the collector,
validator and this document before a single native invocation. No runtime
correction, native retry, permission change or new input is included.

## Corrected handoff ready

Changes review `509af4b7-4239-49bc-88e1-492013ffe918` completed with all three
changed paths covered, zero security findings and no remaining handoff blocker.
Independent review confirms outer-console custody in both normal-return and
timeout paths. The sealed canonical results were read back. Range:
`ba6e06fa2ff8c8634ddcb366055d5b0d43620554` to
`045d08245f7e01dad31d82d7d30b624501cb6d2f`. Measured usage: 1,638,913 total tokens,
1,629,056 cached input tokens. All three working files matched the review snapshot
before this status appendix; ordinary HEAD/index and unrelated changes remain
untouched. The intent is absent and the preceding native receipt hash matches.

Ready for one invocation of `scripts/collect_p02_d5c_pipe_runtime.ps1` with
`-Session $global:D5bReportSession`, script SHA256
`42B88261A7FE005002E1F0293F5D967A7FA6362953B4F8CB5C9E4C6699B68738`.
Capture the whole host elapsed time. Stop on error/incomplete output; do not retry,
install, delete or change settings. Cancel/report a hang before 60 seconds and
keep the elevated console open. Review the resulting receipt before any next
native step. The balance is still **1,449 seconds**, **21 inputs consumed**, and
**zero maintenance retries**. Preparation acceptance is
`.codex_artifacts/p025/d5c-pipe-runtime-preparation-acceptance.json`.
This final evidence-only appendix changes no executable behavior and requires no
repeat runtime/security scan. D5c/d/e/f and D6 release remain open.

## Native runtime inventory accepted

Receipt `d5c-pipe-runtime-result-196b659ae9114a299ae6e9420f363b76.json`, SHA256
`17523613DF2679B6C371DFD8C6967A1B9416BE1807E57FBFE09EFD4C4292F738`, passed
independent adjudication. All eight exact files exist and have bounded sizes and
SHA256 values; the inventory executed none of them. No installation is needed
for the proposed fixture. The VM identity/reserves and host postchecks passed;
the borrowed session returned available. No SQL/workload or permission change.

Full host time 1.6050238 seconds consumes two, leaving **1,447 native seconds**.
Six of the 60-second Windows allocation are consumed; 21 inputs remain consumed,
with no maintenance retry. Availability and exact bytes do not establish binary
provenance or loadability. Acceptance: `.codex_artifacts/p025/d5c-pipe-runtime-acceptance.json`.
