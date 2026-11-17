# P02 D5e partial binding acceptance and grouped measured cost

## Reconciled receipt

The binding receipt `d5e-cost-bindings-result-2b60686248dd40ddb0ce1cd8c4f5194a.json`
has SHA256 `46a59b88184d5f6073614f1e9a70266c935fe772cf559baa0796c1ccb2766a60`.
Its collector exceeded the 700,000-byte aggregate SQL JSON limit at 700,217 bytes
while dumping statistics. This was an evidence collection failure, not a cost
arm execution. The guest retained complete modules (93), dependencies (170),
triggers (3), synonyms (0) and physical branches (35). The final preservation
flag is false because the sequence stopped before reaching it; it is not a
license to discard earlier complete evidence or replay accepted work.

Three full binding groups B1–B3 are accepted. B4–B8 remain uncredited. Physical
collector closure and the final connection disposal were independently recorded;
1.008972 elapsed seconds rounds up to two. The create-only partial acceptance
record and its adjudicator preserve the original failed receipt and intent.

| Accounting | Completed / expected or remaining |
| --- | --- |
| Fixed accepted behavioural/readiness checks | 100 / 100 |
| Binding checks | 3 / 8 |
| Cost arms | 0 / 12 |
| Total | **103 / 120** |
| Native time | **987 seconds** |
| Windows fault time | **49 seconds** |
| Synthetic row attempts | **83 / 95 used; 12 remain** |
| New database / copy-only backup allowance | **0 / 0 remain** |

Setup acceptance remains separate and accepted. Offline preparation tests never
increase native acceptance totals. No imports, production changes, deployment,
new databases or new backups are included in the continuation.

## Measured continuation

`scripts/run_p02_d5e_measured_cost_packet.ps1` uses the existing elevated native
PowerShell session and the exact cost database 11 born `2026-11-15 14:17:07.067`.
Its payload is `d5e-measured-cost-packet-20261115.json`; its Python actor is
`scripts/p02_d5e_measured_cost.py`. A new create-only host intent and private guest
directory make this a one-shot packet. Accepted receipts, original runners,
handoff manifests, SQL files and runtime binaries remain pinned.

The remaining binding checks precede measured writes. SQL compiler metadata
describes all 57 actual SELECT projections (491 columns), including export-12;
logical labels are never treated as object names. The module check binds all 93
object identities and exact catalog hashes. It separately checks dependencies,
enabled trigger boundaries and synonyms. Physical import/configuration branches
must remain skips, and the two KVK indexes must already exist. Statistics are
reduced to a single ordered branch digest/count summary, instead of collecting
thousands of verbose rows. Source statistics modification counts are represented
as eligible/not-eligible branches, not unstable absolute counters or timestamps.

SQL validation uses the authoritative SQL repository. Catalog CREATE versus
CREATE OR ALTER formatting is not repaired or normalized in the measured actor:
it pins the actual collected catalog body. The already accepted cost-copy
adaptation of GOVERNOR_NAMES_PROC uses the local KingdomScanData4 and preserves
the earlier comment encoding; the targets view remains bound to KVK16 rather
than the bootstrap KVK15. Player view definitions correspond to the reviewed
maintenance redeployment. Those differences are declared, not hidden by broad
whitespace normalization. Core header and quoted RowCount/backup guidance and
its accepted regression evidence remain unchanged.

The twelve original IDs, order and request UUIDs remain frozen: two equal
warmups followed by five balanced OFF/ON pairs. Both conditions execute the
actual names/summary procedures and all six real maintenance children, with
committed report work, fresh due generations and one possible configuration
log-row attempt per arm. Existing summary cursors alone supply the stimulus;
no new imported source rows are added. KVK work updates its existing row.
The backup ledger remains undemanded, and no backup dispatcher is called.

The measured candidate is the actual optional operation-evidence and diagnostic
sink source, loaded with exact source hashes. OFF has no sink; ON starts a fresh
sink and physically joins it. One parent and three real stage observations must
publish without refused, dropped, invalid, context-loss or failed records. This
measures the report/SQL workload with that optional diagnostic condition; it
does not claim a second qualification of the already accepted application DAL,
Windows fault cases, saturated observer path, or all bot call sites. SQL observer
count is explicitly zero in this actor.

All 57 outputs are retained as typed compressed raw rows. Exact column sequences,
row counts and order-independent full-cell multisets must agree. The sole
exception is the nine intentionally regenerated SUMMARY_PROC_STATE.LastRunTime
values: each raw timestamp must lie between that arm's SQL UTC clocks and each
checkpoint must equal 1245; the comparison then uses an explicit validated-clock
token. Every other date, name, duplicate and rank remains exact. Preflight rejects
source scan ties or a rolling 3/6/12-month boundary within the 600-second envelope.
A difference stops the packet
and retains raw evidence for adjudication, without replay. SQL clocks bound each
arm. Physical statistics branch summaries must also match after warmup.
Five measured values per mode are mandatory. Frozen median thresholds are
ON <= 1.2 * OFF + 1000 ms overall and +250 ms for each names/summary stage.
Overall time includes the actual workload, interstage safety checks and physical
sink drain, but excludes initial metadata binding and subsequent raw capture.
The sink closes before evidence capture, so capture cannot inflate the baseline
or provide extra drain time to ON. The separate arm wall clock still bounds all
work, checks, capture and cleanup to 45 seconds.

## Ownership and limits

One suspended native Python process is assigned to an exact owned Windows job
before resume, with process birth, token SID, membership and active-count checks.
The parent enforces a 30-second preflight and 45-second arm deadline independently
of the actor; the actor's smaller deadline leaves cleanup headroom. No broad
process stop or SQL KILL is used. Exact process join, empty job, absent application
SQL sessions, no active cost write transaction and collector disposal determine
whether elapsed time can be settled. Unknown closure retains custody and the
full reservation; unknown host output reserves all twelve possible attempts.

The total reservation is **600 native seconds, zero Windows seconds and at most
12 row attempts**. At maximum planned use 387 native seconds remain, above the
existing 185-second D5f minimum. No extension is requested. Limits include 1,800
actor statements, 12,000 metadata rows, 1.5 GiB raw output and 2 GiB retained
files; each compressed output is capped at 128 MiB and the host receipt at 1 MiB.
Guest C/Q and host C retain the 8 GiB floor; log usage stays below 70% and version
store below 512 MiB. Raw captures remain in the private guest directory, hashed
in the host receipt; they are not copied or deleted within the timing envelope.
Retained earlier databases and fixtures are checked before and after measured
work. All accepted evidence remains available on any failure.

## Validation and review

Focused Python controls exercise typed equality, fixed cost thresholds, partial
acceptance, create-only receipts, multi-result draining, cleanup despite deadline
failure, frozen output mappings and the actual diagnostic writer in an isolated
process. Native PowerShell 5.1 controls cover parser compatibility, custody,
finite deadlines, row reservations and durable receipt refusal. They execute no
SQL, VM workload or cost arms. Failures found during preparation are fixed before
handoff; the final handoff record gives exact hashes, counts and review outcome.

Architecture, deferred-item and security-routing validators are required. The
test selector recommends the broader suite; full pytest, application smoke and
Discord registration are skipped because only an isolated qualification packet
changes. Existing application and accepted native tests are not replayed.
Security routing selects **Changes**, the immutable packet-only Git range, with
Deep off. SQL source is read and pinned; there is no SQL repository patch or
deployment. An executable handoff requires the completed review record.
