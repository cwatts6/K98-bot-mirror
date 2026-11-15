# P02 D5d G2-G4 grouped native packet

Prepared, tested, reviewed and frozen under existing approval. Native execution
is awaiting the concrete fixture extension: the 67-row allowance is exhausted.
No accepted evidence was replayed. Status: ready pending fixture approval.

## Scope and accounting

Prepare one host PowerShell handoff, with stop-on-uncertainty between cases.
Original service, custody, file-lock and SQL maintenance bodies are loaded from
pinned source. No application source or authoritative SQL source is changed.
New tooling belongs in scripts and tests. No command/view, provider, import or
report generation is introduced. D5b's actual six-child correctness carries
forward; injected child failures here qualify the maintenance dispatch boundary,
not every statement inside each expensive child.

Native denominator: 24 cases (11 G2, nine G3, four G4).
The remaining 21 original synthetic restart checks are tracked separately from
native checks; their loader and exact selection must pass before execution.
G1 remains 47/47 behavioral and 11/11 controls. Earlier 31 behavioral custody
checks, seven controls and 42 drain checks remain separate carried evidence.
Planned new G1-G4 behavior total is 92: 47 completed, 45 pending. This is a
planning denominator for this G1-G4 tranche. The 24 native IDs below are exact;
the 21 original offline restart variants still need their reviewed loader. Preparation
controls are never counted as product cases. Any change to this denominator must
state the missing risk or duplicated coverage that justified it.

## Architecture and SQL boundary

Reuse core/recovery_sql_snapshot.py, core/sql_connection_custody.py,
core/owned_work.py, core/file_lock.py, event_calendar/sql_lifecycle.py,
services/maintenance_dal.py and services/maintenance_backup_dal.py. Each uncertain
native owner lives in a separate disposable process; its original registry is
never reset. An independent connection checks session ID, login time and native
connection ID after the exact process handle signals. PID/SPID alone, proxy close
or a cancelled awaiter cannot prove physical closure. Unknown cleanup stops
dependent cases. No blanket SQL KILL or process-name termination is allowed.

The proposed new database is K98_P025_D5d_Fault_20261115, created only when absent,
on the retained qualification Q: volume. Original databases 7, 8 and 9 are checked
read-only and never mutated. Original MaintenanceWork, MaintenanceConfigurationWork,
MaintenanceKvkWork and MaintenanceBackupWork table definitions and RunMaintenance,
BackupClaim and BackupAcknowledge procedures are read from the authoritative SQL
repository. Six explicitly labelled inert child procedures write a single test
effect marker then raise the fixed fault; real backup dispatch is always injected.
No real backup, provider or consumed input is invoked.

Proposed fixture allowance: 16 newly attempted synthetic rows: six maintenance,
one configuration, one backup, six committed-effect markers and two transaction
markers (one intentionally rolled back still counts as consumed). No old rows are
reset. Fresh backup generations use this new fixture only, with every transition
receipted and the unknown state last; uncertainty is never cleared for reuse.

## Bounds and retained evidence

Plan a 240-second host wall-clock ceiling including cleanup, within the 248-second
unreserved D5d balance; preserve the 1,000-second D5e/f reserve. Windows file/job
cases have a separate combined 40-second ceiling within the remaining 50 seconds.
Inputs stay 21 consumed, zero new. A fixture extension, if approved, raises the
synthetic-row ceiling from 67 to 83; it does not reset prior accounting.
All attempts, partial fixtures, database files, sentinels, source bundles and
receipts remain. A one-shot intent precedes guest staging and database creation.
No automatic retry or cleanup deletion. Failure must retain unfinished case IDs
and deduct elapsed/reserved time conservatively.

## Validation and review before handoff

Test source loading, complete fake-driver schedules, exact case membership,
fault firing, wrong births/targets, statement/row bounds, one-shot intent,
serialization, output limits, process closure and host timeout custody. Parse
and exercise pure functions using Windows PowerShell 5.1. Run architecture,
deferred-item and security-routing validators and explicit-path test selection.
Broad application pytest/import/registration runs are not selected: production
source is unchanged and accepted schedules must not be replayed.

Security decision: Changes review of only the new packet/builder/tests and
fixture source, Deep off, against the current Bot HEAD. No SQL-repository diff
exists; original SQL definitions are pinned inputs. Review child launch, native
target isolation, fresh files, fault injections and preservation independently.
No refactor/deferred optimisation is introduced. Final native acceptance still
requires operator execution and receipt reconciliation; this draft is not a
claim that G2-G4 or all D5d obligations are closed.

## Exact running count

| Evidence set | Expected | Completed | Pending |
| --- | ---: | ---: | ---: |
| G1 accepted behavioral schedules | 47 | 47 | 0 |
| G2 grouped native cancellation/custody | 11 | 0 | 11 |
| G3 grouped native maintenance/backup uncertainty | 9 | 0 | 9 |
| G4 grouped native transaction/file/job lifetime | 4 | 0 | 4 |
| G4 original synthetic restart/birth variants | 21 | 0 | 21 |
| **Planned G1-G4 behavioral total** | **92** | **47** | **45** |

G2 IDs: `cancel_before`, `cancel_after`, `owner_failure`, `grant_direct`,
`grant_alternate`, `rollback`, `reset`, `cursor`, `close`, `guard_release`,
`file_uncertain`. G3 IDs: `failure_import`, `failure_configuration`,
`failure_player_report`, `failure_kvk_output`, `failure_final_stats`,
`failure_post_import`, `backup_requested`, `backup_not_attempted`,
`backup_unknown`. G4 native IDs: `commit_lost`, `precommit_exit`, `file_crash`,
`named_job`. Prefix each ID with its group and a dot as in the manifest.

The 21 pending variants in `tests/test_export_child_restart.py` are: exact old
closure 3; wrong/unverifiable birth 7; caller-private birth 1; private-birth I/O
failure 2; exact Windows observer 6; other-host/invalid birth 1; private-verifier
birth binding 1. The separate real Windows lifecycle test in that file is not
silently counted as executed by this packet. Native `named_job` instead calls
the pinned original observer and retirement validator against the actual live,
empty and destroyed named jobs from this packet.

Earlier accepted custody (31 behavioral plus 7 controls), drain (42), G1 runner
controls (11), and D5c family/inspector/route/native counts remain carried evidence,
not additions to this 92-case denominator and not replays. Completing the native
packet would move this tranche to 71/92, subject to receipt adjudication. It does
not itself close the 21 restart variants, all inherited D5d obligations, D5e/f,
or the separately authorized D6 production stage.

## Preparation evidence and review corrections

Latest preparation passes: 12 Python test groups in
`.codex_artifacts/p025/d5d-grouped-tests-05.txt` and 45 actual Windows PowerShell
5.1 controls in `.codex_artifacts/p025/d5d-grouped-ps-tests-04.txt`. These include
source bootstrap, all injected schedule families, transaction/lost-reply branches,
original retirement verification, one-shot refusal, publication ordering,
wrong/expired accounting, and cleanup failures. These are preparation controls,
not accepted native product qualification. Earlier failed/preliminary outputs
are retained; later passes do not erase them.

Initial review corrected eight issues: native retirement evidence was incomplete;
observer closure was inferred; a thrown close could avoid Windows debit; case
counts advanced before cleanup; host/guest clocks were disconnected; disk reserve
was sampled before allocation; early job creation could leak its handle; and the
Windows structure layout lacked an x64 gate. It also added private staging at
creation, granting the observed local SQL service traversal only on the packet
root and Modify only on `dbfiles`.

A correction review identified two further issues. All three handshake signals
now use create-new `.pending` files, flushed and closed before an atomic,
no-overwrite rename. The guest receives the numeric remaining duration and uses
its monotonic clock as well as UTC for admission and cleanup reserve. A lagging
guest clock cannot restore time already consumed by host preparation. Failed
publication retains evidence and stops; no retry is introduced.

The initial full five-file Changes review is scan
`9db31609-ff6e-4e9f-912f-cbedf7fd29f6`, snapshot `259c7a9ddc0294da8854a5707dca95c7b4582517`.
The first four-file correction review is scan
`b9ead87a-fc29-49e3-909b-6c1b6c5303e2`, snapshot `676b90ec4b6a833471afcbe985626d2a59e8aba5`.
Both finished with no reportable vulnerability, but explicitly withheld native
handoff for the correctness issues above. The final narrow correction snapshot
is `78f96e125b95e09ae2f8d2e4549cec086f2d3910`, scan
`220865d8-f48e-4c04-bb24-32071e1723aa`; completed with full four-file delta coverage,
zero reportable vulnerabilities and both remaining correctness blockers resolved.
These are unreferenced review commits made with separate indexes; the ordinary
branch, index and accepted application changes are preserved. Deep scan is off.

Architecture, deferred-item and security-routing checks passed. Explicit-path
test selection recommended broad pytest, smoke/registration and release checks;
these are deliberately skipped for this isolated qualification-tooling change:
no production module was edited, no registration changed, and accepted native
schedules must not replay. Targeted source loading and meaningful injected tests
cover the new tooling. Ruff critical error checks passed. This is not a merge,
promotion or deployment handoff.

Final frozen manifest: `.codex_artifacts/p025/d5d-grouped-packet.json`, 143,379 bytes,
SHA-256 `a48cc2645194b2d0cd77a036819f7e29c061c4c3e071b1d59de5a86fe2898286`.
Runner `scripts/run_p02_d5d_grouped_packet.ps1` SHA-256:
`01dce1527b0a274eaebf369133c3a18a70226002631245c77fa5f68ca38f9829`.
The final manifest bootstrapped all 15 selected modules with zero native cases.
Its 34 source/evidence pins and seven authoritative SQL pins matched. All 2,403
G1-preserved file hashes and both repository HEADs were checked unchanged after
preparation. Native/Windows time, inputs and fixture-row balances are unchanged.

Tool-reported review usage: initial scan 6,912,332 total tokens (6,834,816 cached
input); correction 1,837,111 (1,763,584 cached input); final correction 755,851
(731,392 cached input). These are aggregate rollout counters returned per scan,
not incremental billing, not additive work estimates, and not qualification time.

## Extension required before native handoff

Approve only the concrete additional fixture scope: one new disposable database
`K98_P025_D5d_Fault_20261115` with retained files under
`Q:\D5dGrouped-20261115`, and 16 newly attempted synthetic rows, increasing the
ceiling from 67 to 83. The existing 67 rows remain consumed and untouched.
Original DB7, copy DB8 and hold DB9 remain read-only to this packet.

No time extension or new input is requested. The 240-second host reservation
fits inside the 248-second unreserved balance and leaves at least 1,008 seconds,
including the protected 1,000-second D5e/f reserve. The 40-second Windows sublimit
fits the remaining 50 seconds. Any uncertain timeout retains the full reservation
pending reconciliation rather than treating a stopped waiter as physical closure.

The runner refuses without the fixture-extension switch. No command containing
that switch is handed over until the extension is approved. Afterwards, use the
existing elevated Windows PowerShell 5.1 session and pinned runner/manifest hashes;
retain its receipt and stop on any mismatch, error or incomplete physical closure.
