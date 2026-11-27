# P02 D5c guard acceptance and remaining feasibility - 2026-11-12

Status: baseline and both schema guard orders accepted; remaining feasibility
packet passed offline checks and completed Changes review, awaiting its one
operator-console execution. D5c/d/e/f are not complete.

Reader-first receipt `f15f0ec376bc47f1a74f3052aace278d` matches SHA256
`A7020B1B6A91E91C8D89BC57FBCB6827C58E1FE14054220D28A8D984CD5699C2`.
Independent adjudication checked all24 observations and preimages. The reader
recorded SNAPSHOT/Shared; the distinct contender returned-1/NoLock. After
acknowledged reader rollback, isolation restoration and close, the scheduled
contender acquired Exclusive and released toNoLock. Both actor sessions were
independently absent; PID6132 exited normally. No original state/permission/
claim/backup changes occurred. All prior evidence remains preserved.

The42,606-byte receipt has48 reserved command units and41 reserved row units;
actual counts are24 wrapper statements/29rows and7 child statements/6rows.
Host0.8967231 seconds consumes one, leaving **1,470 native seconds**, including
470 of the proposed D5c allocation. **21 inputs remain consumed**. Acceptance is
recorded in `.codex_artifacts/p025/d5c-schema-reader-first-acceptance.json`.

Together with the accepted holder-first receipt, this proves the existing schema
guard protocol in both arrival orders with real driver/managed-reader cleanup.
It does not prove actual maintenance-child overlap or other native D5c families.

## Remaining read-only feasibility packet

Retain all27 accepted V3 readiness statements and add seven bounded metadata
reads, with no business workload or new connection target:

| Observation | Maximum rows | Purpose |
| --- | ---: | --- |
| postImportFullPreimage | 1 | Full existing maintenance row, including request/time fields, for a concrete next-generation proposal. |
| maintenanceEntryCounts | 6 | Existing procedure-execution counters; reused D5b metadata query, not new execution. |
| physicalStatistics | 8 | Existing statistics metadata on the same eight D5b objects; no statistics work. |
| remainingDatabaseOptions | 2 | Catalog state for the protected original and disposable copy; no connection to the original or settings change. |
| existingReaderMappings | 5 | Existing database/server identity mapping and current observer's impersonation capability; no impersonation/authentication/grant. |
| fixtureObjectInventory | 21 | Presence/type of exact source-validated table names used by season/unowned-hold fixtures. |
| fixtureForeignKeys | 128 | Direct incoming/outgoing FK edges involving those objects, including external dependencies; no fixture rows. |

Total34 statements, maximum308 rows,512 per result/2,048 total and one-MiB
receipt limits remain. Three-second SQL statements, unchanged work/cleanup
deadlines and60-second manual stop apply. Same exact session, VM, database and
resource gates. Prior failures and all three accepted native receipts are pinned.
All existing paired state checks and independent SQL-session closure are retained.
Missing objects, unmapped users or unsuitable options are findings, never implicit
authority to create, repair, grant or toggle anything. A cap failure stops without
raising limits or retrying.

This prepares the specific outstanding decisions. The source plan requires a
separately approved, labelled D5c post_import demand before actual-worker overlap;
the completed generation1/claim and original15247 evidence cannot be replayed.
The real worker acquires schema ownership only for pending work, so re-running
the six completed claims would not qualify it. Committed synthetic tuple tests
also require exact IDs/FK closure and explicit approval; the historical native
fixtures create databases/users, drop FKs and delete whole tables and must not
be run here. No new demand, fixture insertion, permission/isolation exception,
extra database or resource increase is included in this inventory.

The preserved guard ordering is a foundation for the unchanged real worker.
Its own guards and physical entry must be observed; if a native scheduling window
does not establish overlap, record it unexercised rather than loop or infer it
from timestamps. Keep at most two actors and one observer. Remaining factory/
rights, disabled-isolation, Windows handle, action-time, D5d failure/restart and
D5e balanced-cost requirements still need their specific evidence.

The collector passes103 PS5.1 parser, remoting, existing safety-gate, fixed-read
and authoritative-object checks. No new Python/native child is introduced.
Full application tests/startup are skipped for this fixed metadata collector;
run the source/deferred/security-routing checks and path selector. Changes review
of this exact collector/test/manifest/doc delta is required, Deep off. No SQL
repository implementation change is proposed.

## Review finalization and handoff

Changes scan `acd3a865-6d81-4aae-be94-6866e60fed3b` is completed with no
findings and all four changed files accounted for. Exact review range:
`7d4beb43253845b400f6bfb4d6b1eb3e1fdd52d4` to
`d16c6b3aef44b8b4349491d367093a5345fc6895`; Deep was off.
The first finalization refused an incomplete saved draft. Its failure remains in
the conversation/tool history. On the operator's instruction to fix and continue,
the same scan was resumed, the coverage record corrected, its successful save
checked before finalization, and the completed sealed result read back. No
collector, SQL work or permission change occurred during this correction.
Recorded review usage: 2,066,285 tokens, including 1,948,160 cached input tokens.

Executable script SHA256:
`3F5FD0CF8B07B95C8AC9944FB98C7D7BED49B06F4866865CF7121F7885F02E71`.
Manifest SHA256:
`34583d4bc1a7886894df9bc67787d5db041ffb8d153f619024da017a744a1a10`.
Both remain byte-identical to the reviewed snapshot. The manifest's inherited
descriptive 35/40-second deadline fields are not consumed by the collector.
Actual unchanged code stops work admission at 30 seconds and cleanup admission
at 42 seconds; the outer runner requests stop at 45 seconds and allows ten
seconds to join. The operator must cancel/report a hang before 60 seconds.
The host stopwatch includes the whole packet and cleanup; debit its rounded-up
elapsed time from 1,470 seconds only after receiving the execution evidence.

This appended review-status clarification changes no executable or manifest.
Source review and prior 103 offline checks remain applicable; no repeated native
or application test is warranted for this prose update. No new security surface
is introduced, so no second Changes scan is required for this status-only text.
