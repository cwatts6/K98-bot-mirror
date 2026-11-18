# P1 MGE native SQL qualification packet

Prepared and executed 28 October 2026. **Exact target approved by the operator;
all 15 named native cases passed. Fixture retained.**
This packet qualifies the local implementation; it does not deploy the bot or
settle the historical MGE interaction. No production connection or provider call.

## Approved bounded target

| Item | Exact approved value |
|---|---|
| Instance | `9SX2VF4\K98DEV` |
| New database | `K98_P1_MGE_Qualification_20261028` |
| Data file | `C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\K98_P1_MGE_Qualification_20261028.mdf` |
| Log file | `C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\K98_P1_MGE_Qualification_20261028_log.ldf` |
| Recovery / Broker | SIMPLE; Broker remains disabled |
| Data | Synthetic MGE-only records, at most 2,000 audit rows; no restored user data |
| Retention | Retain the fixture and evidence after the run; cleanup is a separate action |

Actual instance identity, target absence and both file paths were verified before
creation. SQL Server version is `16.0.1210.3`. Exactly the seven tables below were
installed from SQL revision `7e91989f619deb46836194c7e705b0a9eb2ebe11` with retained
source hashes. Recovery is SIMPLE and Broker was explicitly disabled after creation
(the instance default had enabled it). No existing database/file was overwritten.
Every fixture connection verified server, database name and the recorded database ID.

The local SQL development contract requires a **different exact approved database
and file target** for new transaction fixtures. Database 22, retained S11 databases,
their backup/media paths, production, READ_WRITE changes and blanket schema
installation are excluded. This packet is separate from historical S11 approval.

## Minimum source graph

Use the authoritative SQL repository at `C:\K98-bot-SQL-Server`, retaining its
revision and file hashes before installation. Only these seven table definitions
and their own declared defaults, checks, foreign keys and indexes are needed:

1. `sql_schema/dbo.MGE_Variants.Table.sql`
2. `sql_schema/dbo.MGE_Commanders.Table.sql`
3. `sql_schema/dbo.MGE_Events.Table.sql`
4. `sql_schema/dbo.MGE_Signups.Table.sql`
5. `sql_schema/dbo.MGE_SignupAudit.Table.sql`
6. `sql_schema/dbo.MGE_Awards.Table.sql`
7. `sql_schema/dbo.MGE_AwardAudit.Table.sql`

Events reference variants; signups reference events/commanders; awards reference
events/signups/commanders; both audit tables reference events. No view, procedure,
calendar, registry, import, export, agent job, login grant or provider dependency
is installed. Explicit fixture connection factories must assert this database on
every connection; the normal bot database configuration must not supply a fallback.

## Execution and evidence requirements

| Case | Required observation |
|---|---|
| Create/edit/withdraw | Real production DAL writes signup and mandatory audit together; withdrawal removes its award and writes cleanup audit in the same commit |
| Required-write failure | Inject a statement failure before commit; a separate connection observes no partial signup/audit/cleanup |
| Commit acknowledgement loss | A connection proxy commits then raises; result stays unknown; a new connection positively reconciles the exact operation receipt; no second mutation |
| Rollback failure | Retain unknown, connection identity and trace; no automatic replay |
| Two create callers | Same event/governor cannot produce two active signups; retain actual winner/loser outcomes and audit counts |
| Withdrawal versus roster add | Gate two sessions at the event boundary; no active award can be inserted behind a completed withdrawal |
| Two rank additions | Both target rank 1 with different governors; at most one is inserted and the locked count/rank check rejects the other |
| Stale edit / closed event | Change snapshot or status in the competing session; mutation must reject after acquiring event ownership |
| Resource lifecycle | Record session/connection ownership, commit/rollback/close and any still-outstanding work; do not expire uncertain work |

Use explicit gates and separate sessions for concurrency. A delay alone is not
proof that the competing statement reached the expected boundary. Retain the
actual result, audit rows and lock/wait evidence. Do not kill a session or retry a
write just because it takes longer than expected.

## Measurement requirements

Use identical synthetic sizes and isolation/session settings for baseline and
candidate, recording SQL version, source hashes, warm-up and sample counts:

- Median and p95 transaction duration for create/edit/withdraw; at least 20 measured
  operations after warm-up, with logical reads, CPU and elapsed time retained.
- Statement and connection counts per operation; required audit/cleanup counts.
- Actual receipt-lookup plan and reads at 0, 100 and 1,000 event-audit rows. The
  existing EventId index is known from source; plan choice and JSON filter cost
  must be observed rather than assumed.
- Contended and unrelated-event latency, lock wait, deadlock/timeout outcomes and
  maximum concurrent workers. Keep the process-only roster owner distinct from SQL
  coordination.
- Baseline and candidate complete end-to-end mutation duration. Early interaction
  acknowledgement is already measured offline and must not be counted as SQL speedup.

The raw result must identify every unexecuted or inconclusive case. No index or
transaction speedup is claimed until these measurements exist. A problematic plan
is evidence for a separate bounded optimisation decision, not permission to change
schema during qualification.

## Executed results and limits

- All 15 named cases passed: create/edit with audit, four required-write failures,
  rollback acknowledgement failure, lost commit acknowledgement, exact receipt
  reconciliation, stale/closed admission, unrelated-event progress, competing
  creates, withdrawal versus roster add, competing ranks and connection closure.
- The two controlled contention cases positively matched `LCK_M_U` to the held
  owner. An unrelated event completed in 4.79 ms while that owner remained held.
  At most three mutation workers were active; no deadlock/timeout was observed.
  Controlled gates establish ordering, not production contention latency.
- Durations have 20 samples per operation/mode after two warm-ups. Native median
  create/edit/withdraw changed from 1.760/1.579/1.891 ms to 1.739/1.737/1.479 ms;
  p95 changed from 2.268/1.921/2.473 ms to 2.431/1.993/2.092 ms.
- Connection/commit counts fell from 2/2/3 to 1/1/1. Statement counts rose from
  3/2/3 to 5/5/6 for the added checks. A separate 20-cycle session-counter pass
  measured median logical reads of 46/30/37 versus 87/84/80.5. Median CPU was
  below millisecond resolution; observer overhead is excluded from timing claims.
- Actual receipt plans selected a clustered scan at all three sizes, with
  15/17/31 logical reads and 142/242/1,142 total audit rows respectively. The
  existing EventId index did not guarantee a seek. Plan XML and raw SQL IO/timing
  output are retained locally; sanitized counters and plan hashes are committed.
- All observed connections closed; 1,262 synthetic audit rows remain. Target,
  files, seven-table boundary and 2,000-row audit ceiling were preserved.

The baseline is the original separate DAL workflow reconstructed with preserved
statements and explicit fixture connection closure. The duration fixture has no
award for withdrawal cleanup; award removal is separately tested for atomicity.
Native duration excludes UI/service preparation and provider calls. Complete
callback duration was measured with simulated IO in the offline benchmark; live
Discord/provider end-to-end duration and acceptance were not exercised. Sustained
contention, production-size scaling and genuine deadlock/timeout recovery remain
unmeasured. No schema optimisation or broad performance claim follows from these
small warm-cache samples.

The local execution harnesses and raw receipts are under `.codex_artifacts/`:
`mge_native_qualification.py`, `mge_native_costs.py`, `mge-native-results.json`,
`mge-native-costs.json` and `mge-native-install-receipt.json`. They are retained
execution evidence for this exact approved target, not a general database installer
or a script to rerun blindly. A future run needs an absence/ownership check and a
fresh bounded fixture plan. Their hashes, source/schema hashes, samples and results
are in [native benchmark evidence](../benchmarks/p1_mge_native_sql_20261028.json).

## Completion boundary

Native qualification can close only its named cases and measured costs. Protected
updater transition review, mirror/production promotion, deployment/restart, live
callbacks, original-board visual confirmation and historical outcome disposition
remain separate. No natural P1/P0 acceptance is manufactured by this fixture.

See [implementation and offline evidence](P1%20MGE%20Lifecycle%20-%20Implementation%20and%20Evidence.md)
and [local SQL development boundaries](../reference/local_sql_development.md).
