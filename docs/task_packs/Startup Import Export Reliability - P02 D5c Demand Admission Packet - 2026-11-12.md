# P02 D5c demand admission packet - 2026-11-12

Status: the operator approved the bounded maintenance scope. The first packet
is prepared, passes 155 offline PS5.1 checks and completed Changes review.
No native work ran and the balance remains 1,462 seconds, 21 inputs consumed.

This implements only step 1 of the approved
[actual-worker plan](Startup%20Import%20Export%20Reliability%20-%20P02%20D5c%20Global%20Orders%20Acceptance%20and%20Actual%20Worker%20Plan%20-%202026-11-12.md).
It creates one pending generation-2 request, ID
`468fc60f-8424-4637-b576-99717c7ad062`, on the existing disposable copy. It calls
no worker/child, import/report/backup/provider procedure and changes no permission,
ownership, isolation or resource setting. No production or SQL source is edited.

## Evidence and transaction boundary

The pinned manifest carries the accepted 19-field post_import preimage, prior
six-row ledger, owner/permissions, candidate fingerprints, backup state and exact
failure/acceptance receipt hashes. Create-new history files are flushed first on
the host and then on Q:. The guest hash acknowledgement must return to the host
before SQL admission begins; the SQL phase rechecks the guest file and all path
ancestors for reparse points. The history is explicitly historical evidence;
fresh SQL must match it before any mutation, not silently refresh the preimage.

Fresh read-only preflight checks identity, resources, six completed claims,
original protection and all 30 installed images. An exclusive Session worker
guard must be acknowledged before the admission batch. Under UPDLOCK/HOLDLOCK,
that batch checks all 19 post_import columns with NULL-safe EXCEPT semantics,
six completed/coalesced rows and the exact backup state. It refuses an existing
new request ID. Only the unchanged `usp_MaintenanceDue` is called, once, with
post_import and all optional flags zero. Before commit it verifies the four
permitted changed fields, all retained post_import fields, the complete other
five rows in both EXCEPT directions and backup state. SQL timestamps are bounded
by the admission batch's own start/end clock. The candidate later creates its
own ClaimID; this packet preserves generation 1's claim and first error 15247.

After acknowledged commit, a fresh full-row read must match exactly the planned
generation-2 pending state. Owned guard release is attempted at most once, even
if another step fails. Postchecks compare the expected pending ledger, unchanged
child counters/statistics, ownership, permissions, backup, original protection
and resources. Independent captured-session-birth absence and both connection
disposals remain mandatory. Missing commit/release/cleanup acknowledgement is
incomplete and stops dependent work; the intent/history is never deleted or reset.

## Bounds and validation

The packet retains 30 existing metadata statements unchanged and adds four
demand statements plus two repeated read-only counter/statistics postchecks:
36 SQL statements, 170 maximum returned rows. Eight extra client-control units
are reserved without refund, for a planned total of 44 below the original 48.
The SQL statement admission guard stops at 40, preserving those eight units.
One work connection is followed by one independent closure connection; no Python
child or concurrent actor is started. Existing three-second SQL, 30/42-second
guest work/cleanup, 45-second outer stop plus ten-second join, 60-second manual
ceiling, one-MiB receipt and disk/log/version-store limits remain. History staging
must acknowledge within ten seconds and the SQL phase cannot start after host
second 12. Full host elapsed time is charged; no native balance is consumed yet.

Authoritative source checked: `dbo.MaintenanceWork`, `usp_MaintenanceDue`,
`usp_RunMaintenance`, `usp_MaintenancePostImport`, and the inherited backup
metadata contract in `C:\K98-bot-SQL-Server\sql_schema`. All 19 column types,
procedure arguments, worker resource and transaction ownership follow source.
No new DAL or production helper/refactor is justified; this is qualification
tooling with no command/view or application-startup change.

Offline PS5.1 AST extraction executes only isolated functions with fake readers
and demand acknowledgements. The 155 checks cover remoting, inherited SQL/pins,
metadata row/command caps, exact scope, durable-history ordering, refusal before
admission, lost commit reply, altered request/claim/failure, uncertain release,
and a second admission attempt stopping before SQL. SQL predicate structure is
source-reviewed; these tests do not claim native SQL execution/transaction proof.

Two initial validator failures are preserved with their source snapshots and
logs in p025: an optional inherited timeout field was absent, then canonicalizing
the entire manifest encountered empty objects. The corrections inspect optional
fields only when present and compare the full remoting serialization directly.
Executable controls and native bounds were not relaxed; the corrected pass ran
no SQL, VM, registry collection or history write. No existing evidence was replaced.

Architecture/deferred/security-routing validators and explicit-path test
selection apply. Application smoke, command-registration, full pytest and native
release suites are skipped: this bounded offline selection changes only the
test packet and must not bootstrap the application or historical VM fixtures.

Security route: Changes, Deep off, exact four-file packet delta against the last
reviewed owner-first snapshot. Include wrapper, validator, manifest and this doc;
read unchanged supporting helpers/policies as needed. SQL repository is source
authority only, with no SQL patch/review target. Complete that review before
handing over one hash-pinned console command. No new approval is needed for the
approved demand, but a successful receipt still requires independent adjudication
before any of the five blocked-worker cases or the one actual-child allowance.

## Completed review and one-time handoff

Changes scan `3c79a33f-6efc-4d99-9aab-c6653ad1985d` completed with zero findings
and all four changed files covered. The full wrapper and validator received
independent review; the manifest transaction was checked against authoritative
SQL source. Immutable range `9dfc244baa46b61108e5353a04605a40dc994c52` to
`2d0e0f4a8acf85410c3cc236ca5106245296371a`, Deep off. The final draft save was
verified before completion, and the sealed completed coverage was read back.
Measured usage: 1,769,422 total tokens, including 1,757,952 cached input tokens.

Architecture validation passed with zero changed Python files, deferred validation
passed for this Markdown file, security routing returned zero errors/warnings,
and explicit-path selection completed. Suggested full application/release/native
suites are skipped for the bounded test-only reasons above. Snapshot whitespace
checks passed. All four files matched their immutable reviewed bytes before this
status-only addition. No intent, result or host history file existed at handoff.

Final script SHA256:
`392543B1EC5A5DDFCAA8431348BA9E9B109A6816D205D491F2A6C6B19676F599`.
Manifest SHA256:
`92fa30da6959a937717f8e0f52db5cc9421c5b3e763db17b20daf3ab7dee8a36`.

The same elevated PS5.1 console and authenticated D5bReports session run this
once. Retain the full outer host stopwatch and stop/report incomplete output;
do not repeat or remove its intent/history. Adjudicate before any actual worker.
This appended review record changes no executable or security boundary; a second
Changes scan for the documentation-only status record is not required.
