# P02 D5c disappearance acceptance and ambiguous ownership plan

Receipt `d5c-holder-disappeared-result-11fe13982ff64eb1b32c649e2d03a224.json`
matches SHA256 `51a2affcd87f9597886dd7ba24ca93d156c6627f94f9cfdd5c4fed82f256433f`.
Saved-file adjudication accepted the exact grant, -1/NoLock refusal, acknowledged
release and unchanged diagnostic returning unavailable/holder_disappeared_or_ambiguous.
The original refusal remained primary; no owner was guessed. Actor PID 4156 and
SQL sessions 57/58 match independent connection-birth evidence. Both owned
connections closed, the actor exited, and the work/actor sessions were absent.
All seven fixture rows, permissions, original failure history, completed work,
candidate definitions and resources passed preservation checks. No rights or
application data changed. The receipt records 43 units, 115 reserved rows and
24,847 bytes; actor actual rows were five of eight reserved.

Host time 1.3682665 seconds debits two: **1,400 native seconds**, **50 Windows-test
seconds**, **21 inputs consumed**, zero new inputs. The disappearance allowance
is consumed; preserve the original packet, intent and receipt without repeat.
Saved acceptance: `d5c-holder-disappeared-acceptance.json`.

## Next already-authorized lock-only case

C07 still needs an explicit ambiguous diagnostic result. Preserve the maximum
of two concurrent SQL actors plus one observer. Use the documented case where
one session has two ownership records for the same application resource: one
Session owner and one Transaction owner. This tests ambiguous ownership records,
not two different users or a historical production holder. Microsoft documents
this exact ownership distinction in [sys.dm_tran_locks](https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-objects/sys-dm-tran-locks-transact-sql?view=sql-server-ver16).

1. Verify the unchanged host/VM/copy/runtime and all protected preimages. Open
   exactly two administrator actor connections and verify independent births.
2. Holder acquires the fixed global lock Shared/Session. Begin a lock-only
   transaction and acquire that same resource Shared/Transaction, both zero-wait.
3. Requester makes one Exclusive/Session zero-wait request; require -1/NoLock.
4. Invoke the unchanged optional diagnostic once on that requester. Require two
   exact rows for the known holder, SESSION/S and TRANSACTION/S, matching both
   connection births. The diagnostic must return unavailable rather than choosing
   one owner. Preserve the original refusal and the one-second diagnostic budget.
5. Roll back the owned transaction once, acknowledge zero transaction count and
   the remaining Shared/Session lock, release that exact session lock once, then
   close both connections and verify physical absence and unchanged records.

No new fixture, account, rights, settings or business workload. No maintenance,
writer, isolation, foreign-scope or disappearance repeat. This is a new bounded
schedule, not a retry. It needs no third SQL actor. Unexpected admission, missing
or extra diagnostic rows, wrong ownership/birth, failed release/rollback or
uncertain cleanup fails the case and stops dependent work. Close only owned
connections; never replay an uncertain rollback/release or kill other sessions.

## Preparation gates and limits

Build new test-only files without modifying consumed evidence or production
source. Reuse the reviewed two-session wrapper and unchanged 23 preservation
observations. Planned actor budget: 13 units, nine SQL statements, ten success
rows, eleven reserved rows. With outer control and preservation, total 46 of
48 units and 153 planned rows. Preserve 512 rows/result, 2,048 total, 1 MiB receipt,
all resource floors and 1,000 native seconds for later slices. One 60-second host
ceiling within 1,400 remaining seconds; Windows-test allocation is unaffected.

Before native handoff, run focused inert-transport tests of the actual diagnostic,
including zero/one/three rows, wrong owner modes or identities, failed admission,
rollback/release and cleanup uncertainty. Validate PowerShell identities,
accounting, one-shot admission and immutable lineage. Review the exact frozen
packet in Changes mode, Deep off. No native action occurs during preparation.

Denied-metadata and long-resource cases remain separate. All D5c groups and later
D5 slices are tracked independently; this plan does not authorize deployment.

## Offline preparation outcome

Ten actual-diagnostic Python tests passed. The first expanded PowerShell 5.1
control test rejected a valid pair at the generic canonical comparison of sorted
owner strings. Its exact wrapper, actor, manifest, validator and failure are
preserved under `d5c-ambiguity-offline-failure-ownership-comparison`. No native
attempt occurred. The corrected gate requires exactly one literal SESSION and
one literal TRANSACTION record without that generic string comparison. It does
not relax row count, modes, session identities, connection GUIDs or birth times.
All 146 PowerShell checks now pass, including wrong owner/mode/session/connection/
birth, missing records and single-close refusal. No production source changed.

One actor owns both lock lifetimes; the transaction is rolled back once before
the Session lock is released, then connections close in reverse creation order.
Failure cleanup attempts an owned transaction rollback only if no rollback has
already been attempted. Unknown rollback/release or diagnostic cleanup cannot be
accepted or replayed. The native actor remains unexecuted pending frozen review.
