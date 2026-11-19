# P02 D5c preservation acceptance and configuration fixture plan

## Accepted follow-up

Receipt `d5c-catalog-poststate-result-fcb10ba360ed4a2490f40f178daf7fd3.json`, SHA256
`EB0FDDADB8081B0281C0B5B11C9512D3C18C6BED6FF8820135B73DFF76117FA2`, passes
local adjudication. All 30 observations completed within 36 reserved client
units and 109 rows. Paired protected records, candidate definitions, permissions,
original database protection, full maintenance/error history, cached execution
evidence, resources and physical SQL cleanup match both the accepted baseline
and the failed catalog attempt's initial state. Both connections were disposed;
the captured work-session birth was absent. No workload ran.

Full host 1.1728617 seconds debits two: **1,439 native seconds remain**, with
**50 Windows-test seconds**, 21 inputs consumed and no maintenance retry.
Acceptance is saved in `.codex_artifacts/p025/d5c-catalog-poststate-acceptance.json`.
The original catalog receipt remains incomplete and unchanged; this later state
cannot recreate the original skipped observation instant.

## Smallest complete next fixture

The captured source/installed relationship graph supports a self-contained
configuration-preparation fixture with **seven rows in five existing tables**.
It avoids the historical fixtures' deleted tables and omitted constraints.
This is the first allocation from the 64-new-row ceiling; 57 would remain.
No retained application row is used as a mutation fixture.

The exact field values, binary hashes, identities, order and limits are in
`.codex_artifacts/p025/d5c-config-fixture-proposal.json` (11,140 bytes), SHA256
`f4c0258771d7be4032f8345b1b0c42519320de86f1d1b26844beeca7ff0c6813`.
It is inert proposal data, not an executable native packet.

| Table | New rows | Purpose |
| --- | --- | --- |
| dbo.ExportPreparation | 1 | Labelled uncertain configuration preparation, initial version 3 |
| dbo.ExportResource | 2 | Private test account/destination ownership, initial versions 22 and 19 |
| dbo.ExportPreparationResource | 2 | Immutable membership linking those exact resources |
| dbo.ExportExecutionSession | 1 | Explicitly synthetic closed session metadata |
| dbo.ExportExecutionStream | 1 | Explicitly synthetic closed probe metadata with zero requests/events |

The preparation ID is `7afa9c30-00b0-5626-a866-604e921dfd35`; account is
`d5c_config_20261112`, storage owner `d5c_qualification_only`. The resource keys
are `account:d5c_config_20261112` and
`destination:d5c-config-fixture-20261112`. All other IDs and every column value
are pinned in the proposal. The synthetic session/closure fields are test
metadata only and must never count as physical child death, provider completion,
deployment success or recovery proof. No provider request/event is created.

Local validation checked every supplied column against the captured installed
names, required nullability, string/binary lengths and UUID shapes. All non-null
FK tuples resolve to exactly one of the seven proposed rows, including every
intermediate admission state. Relevant source CHECK constraints were reviewed.
Resources enter idle, their memberships are added, then their active references
are set; constraints stay enabled throughout. All inserts name columns explicitly.
Physical column order is irrelevant. Native key absence and constraint checks
remain execution gates, not facts inferred from the proposal.

## Proposed bounded execution

1. Prepare and test an exact admission wrapper. It must prove every primary key,
   resource/account key and account/request-hash unique key absent. Within one
   transaction insert the seven rows in the pinned order, activate only the two
   fixture resources, read back exact values and commit once. Stop and roll back
   on mismatch; an uncertain commit is investigated, never replayed.
2. Run the actual configuration recovery read paths with the writer first.
   Tentatively change only the preparation version 3 to 4 and resource versions
   22/19 to 23/20. Require the passive reader to retain the old committed tuple;
   acknowledge rollback. This creates no additional rows.
3. Establish the actual reader snapshot first, then commit that exact three-row
   transition once. Require the existing reader to see 3/22/19 and a fresh reader
   to see 4/23/20, with all other fields stable. No work is dispatched.
4. Submit the saved old snapshot once to the actual configuration DAL settlement
   boundary. Require `SourceConflict` before mutation, preserve the resulting
   evidence and verify the fixture remains uncertain and owned at 4/23/20.
   This is a stale-action refusal check, not authorization to settle retained work.

No wildcard UPDATE, broad DELETE, table reset, constraint disablement, fabricated
provider outcome, new maintenance demand or retry is included. Preserve all seven
final rows as labelled evidence. The actual production DAL/reader guards must be
used unchanged; test adapters may supply exact connection factories and barriers
only. No copied implementation may stand in for those paths. Import/startup
closure, packet hashes, offline checks and focused Changes review are required
before any console handoff; this plan is not native readiness.

The admission ceiling is 60 seconds; overlap and stale-action packets together
are at most 120 seconds, **180 seconds total from the existing budget**. Preserve
48 client units per packet, 512 rows/result, 2,048 rows total, 1 MiB receipts,
three-second observation statements, two SQL actors plus one closure observer,
all disk/log/version-store limits and owned cleanup. The final wrapper ledger
must fit these ceilings before handoff; no limit increase is implied. No packet
may consume the final 1,000 seconds reserved for later D5 work. Actual host time,
including failure and cleanup, is rounded up and debited once per packet.

## Approval boundary and remaining work

The existing D5c plan explicitly reserves committed synthetic rows for separate
approval. Approval requested here is only these seven rows, the one rolled-back
and one committed version transition, and the one stale-action refusal attempt
after offline preparation/review. The original database, failed receipts and
five other completed maintenance jobs remain untouched.

No permission grant, new principal, impersonation, isolation toggle, extra VM
resource, database copy, import replay or production change is included. Those
exceptions are not prerequisites for this fixture. The broader season/queue/pool
fixtures, restricted-rights and disabled-isolation cases still need exact plans.
D5d fault schedules, D5e balanced cost runs and D5f reconciliation remain open.
This fixture can close representative configuration consistency/stale-action
evidence; it does not alone close C05/C06 or D5c.

## Validation disposition

This turn changes only evidence, inert proposal data and Markdown; no application
runtime, SQL source or native script changes. Security discovery and runtime
tests are skipped for this proposal with that precise scope. Execute the usual
focused Changes review for the eventual native wrapper. Validate Markdown links,
deferred-item structure, routing and whitespace before approval handoff. No
production refactor or deferred optimisation item is introduced.

Documentation validation passed: three files checked by the deferred validator,
architecture validator with zero production Python files, security routing with
zero errors/warnings, and 30 local links plus whitespace checked. The explicit
selector ran; smoke/registration/release recommendations are skipped for the
inert proposal scope above. Source-only proposal validation introduced no native
elapsed-time or input debit. Committed-fixture authorization is still pending.

## Operator authorization received

The operator replied **Approve the seven-row fixture and bounded tests**.
The exact seven-row proposal and the rolled-back/committed version transitions
and one stale-action refusal are authorized within the stated 180-second scope.
No further confirmation is required for that scope. Permission/isolation/new
maintenance and other fixture proposals remain separate. No row has yet been
admitted. See the [admission packet](Startup%20Import%20Export%20Reliability%20-%20P02%20D5c%20Approved%20Configuration%20Admission%20Packet%20-%202026-11-12.md)
for the bounded transaction, preservation checks and review gate.
