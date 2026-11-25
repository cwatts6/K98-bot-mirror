# D5c final queue and hold safeguard batch

The operator authorizes grouped final-action checks and additional bounded runs.
This packet exercises four G1 routes: queue_admission/withdraw_queued,
withdraw_health_probe, close_withdrawn_read, and unowned_sql_hold/clear_unowned_hold.
It adds no production changes and does not claim the other 69 policy routes.

## Scope and architecture

Run 63 queue scenarios (21 per action), 23 hold scenarios and seven runner controls:
93 cases in one development-host-only pass, 300 seconds, 1 MiB combined receipts,
stop at the first failure. No limit extension is required. No VM step is needed.
Source service/DAL bodies, original snapshot, scope, eligibility, digest, wire,
identity, mutex, CAS, retry decorator and reconciliation logic are compiled as-is.
Only SQL transport/transaction effects and diagnostics are inert. The hold writer
session boundary is explicitly simulated; its acquisition/refusal is not physical
SQL-lock proof. The original scan-lock response guard inside clear is exercised.

Tests reach final updates with valid controls and refuse changed tokens, version,
fence, owner, request identity, foreign account/storage, execution and reservations.
They verify lost CAS and failure between update and receipt insertion. Saved-action
checks require exact identity and independent saved-receipt verification; stale or
busy reconciliation must not dispatch another mutation. No provider or import runs.

The inert cursor enforces a finite SQL protocol and parameter shapes, including
global foreign-producer/stream blockers. It models commit/rollback, not SQL Server
isolation or atomicity. Existing native C05 fixtures remain separately required.
Queue routes have no separate physical producer-lock acquisition: they require an
account mutex, locked preparation/dependency reads and initial-state CAS. That
distinction is retained rather than inventing a producer-guard test for them.

## SQL and reuse

Read authoritative ExportPreparation, ExportPreparationResource, ExportResource,
ExportExecutionStream, StatsImportExecution, ExportUnownedHoldDisposition and
ACQUIRE_KS4_IMPORT_LOCK definitions in C:/K98-bot-SQL-Server. Preserve their hashes
in the packet. Test-only labelled shapes are not native fixture installation.
Keep the exact shared sql_snapshot:legacy_outputs key and global blocker queries.
No settings, rights, schema or production DAL changes are included.

Reuse the reviewed isolated no-site runner with new output/test identities.
Derive every selected source dependency from r.load AST calls; pin exact paths.
Install the real read/import guard during load-only preflight before qualification.
Retain all worker V2 pins, accepted results and original failure evidence. Never
rewrite a failed intent/result. Tests stay in tests; tooling stays in scripts and
artifact preparers. No new runtime helper or deferred optimisation is introduced.

## Review and execution

Freeze runner, test, preparer, packet and this plan in a review-only Git snapshot;
preserve ordinary HEAD/index. Run a narrow Changes review, Deep off, because the
test harness executes SQL-facing source and handles files. Complete independent
review before the one-pass runner. Correct related preparation failures with
preserved evidence and a versioned packet under existing approval.

Command after review: `C:/Program Files/Python311/python.exe -I -S -B scripts/run_p02_d5c_final_queue_hold.py`.
Adjudicate exact IDs, expected refusals, loaded source closure, no pending tasks or
extra threads, all pins unchanged and actual bounds before accepting any result.
Full pytest, smoke imports and command-registration startup are intentionally
excluded from this no-application-startup packet. Architecture/deferred/security
routing/test-selector release gates remain for a PR handoff; no PR or deployment
is delivered here. No new runtime behavior exists to refactor.

Balances stay 1305 native seconds including 1000 protected for later D5 phases,
50 Windows-test seconds, 11/64 synthetic rows and 21 consumed inputs. This pass
uses zero new inputs, zero native operations and no exhausted native retries.
The user's broader approval is retained; any actual future extension is recorded
against its own packet rather than silently increasing these bounds.

This can add offline final-guard evidence for four routes. It cannot close C04,
C05, C06, all 73 routes, D5d/e/f or D6 deployment by itself.
