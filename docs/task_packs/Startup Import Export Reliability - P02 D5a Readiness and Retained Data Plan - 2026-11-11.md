# P02 D5a readiness and retained-data feasibility — 2026-11-11

Status: **local evidence review complete; native readiness unverified**. This
packet proposes D5a.2, a bounded read-only inventory, for operator approval before
any native SQL/VM work. It does not approve a rehearsal or declare D5 complete.

Memory-gate correction, 2026-11-11: the original rule is at least 8 GiB free
**host memory before VM startup**, not an additional post-start host reserve
or an 8 GiB free-memory requirement inside the 8 GiB guest. See the
[source-grounded correction](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a2%20Memory%20Gate%20Correction%20-%202026-11-11.md).
The earlier version of this plan is preserved with its hash in the private
correction receipt. No original limit or input allowance is reduced.

## Scope and source custody

The approved [D5 scope](Startup%20Import%20Export%20Reliability%20-%20P02%20D5%20Scope%20Review%20-%202026-11-11.md)
and [full obligation reconciliation](Startup%20Import%20Export%20Reliability%20-%20P02%20D5%20Obligation%20Reconciliation%20-%202026-11-11.md)
remain authoritative: F01–F32, C01–C16, 73 action pairs, 52 actions, 22 kinds,
four empty kinds, and the separately counted Recheck/group/batch/outcome paths.
No obligation is dropped because historical component evidence exists.

Current Bot checkout: `main`, `e7443e37212ca91e20d531b3684cc369d0fe1505`, plus the
approved, uncommitted D5a.1 drain correction and its two tests. Their prior
[validation](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a1%20Drain%20Correction%20and%20Validation%20-%202026-11-11.md)
records 42 passes and the completed Changes security review. This review makes
no further runtime/test changes. The candidate is not yet an immutable published
release; a later execution manifest must bind the complete source plus patch.
Historical Phase 1 source ZIPs must not be relabelled as that candidate.

SQL checkout: clean `main`, `b924cedd53e29dd88c0e9e7b66208b4fdc1e53ba`.
Fixed payload remains `ba5c6acbefba0eb89cb18842a7f6c6811096759b`, migration
`20261111_001_p02_d4_combined`, profile `p02_d4_v1`: 30 objects, four ledgers,
six kinds, 13 predecessors plus 17 new objects, eight stable seed rows and
initially empty KVK work. Current migration/profile bytes match the fixed Git
payload. Their SHA-256 values are respectively
`8c0c99d92c14cac6da6e22076a5620927bac4c8af3deaa50950d66062381a8dc` and
`57944777e50b7dc9200220cfcc2ce767edb22a2e0972e02bc2cd6f04e23e8171`.

Last accepted installed Bot remains `97abcce1b2a9e71b3959eff74525c57930a703e6`;
Phase 1 SQL remains `a202a51440f17233800b49801bd31c3ead2a9227`. These are recorded
baselines, not a fresh installed-state observation. D2/D3/D4 installation is not
inferred from source delivery.

## Retained evidence reviewed locally

Private machine-readable audit:
`.codex_artifacts/p025/d5a-readiness-evidence-review.json`. It records every
filename, expected/actual size and SHA-256 without copying business row contents.

| Evidence | Fresh local verification | What it establishes and does not establish |
| --- | --- | --- |
| Final continuation attempt `7aea1e23b649448ea68df59b714445cb` | All 66 files / 23,738,306 bytes match their receipt. Receipt SHA-256 `c7f9ae17a8fc707b3241a8a809fb7a03026e203279008504137250b8563a5247` matches its independent adjudication. | Retained Phase 1 evidence is intact; no new execution or current guest-state proof. |
| Full-size summary comparison run `bd616a78f3df42ae8be3a4ad87d2dd10` | All 130 files / 6,647,357 bytes match their receipt, including 112 compressed captures: reference/candidate for 42 detailed states and 14 exports. | Baselines remain available. Original receipt is still `StoppedForReview`; later offline adjudication is separate. Its missing timings remain missing. |
| Immutable export | Included in the 66-file audit: 17,516,820 bytes, SHA-256 `24e9f15dc71d0e3ef2b0d2e08383f9c623bb37328521126336504b896775264c`. | Original 14-section payload bytes remain available; this is not proof that a new candidate generates the same bytes. |
| Final continuation result | Recorded 49,468 rows / 827,683 cells, 139 numeric columns and 26 shared-name objects; independent source/aggregate/summary checks are retained. | Historical numerical/name evidence only. Preserve the 353 tied zero-score ranks and execution-clock-based inactive cutoff adjudication; no new rank policy or current-date reinterpretation. |
| Historical five balanced OFF/ON pairs | Result and runner reviewed; the runner prepares reset/restore scripts between runs. | Historical Phase 1 cost evidence, not combined D5 cost evidence and not an executable plan under current limits. |

The comparison receipt SHA-256 is
`d51f4af53663f359714ae0201ddc0c8a6179ebf4f43e35d17067fc098546979f`.
Its offline adjudication checks synthetic aggregate fixtures separately from
unchanged player cells; the comparison's 827,703 export cells and final run's
827,683 cells are distinct datasets, not interchangeable counts.

The final receipt records the pending 415-row input completed once, scan 1245,
continuation stage 3 and an archived file receipt. It records 21 retained input
files: one original ready file and 20 archives, none claimed. All 21 have the
same 78,035-byte content hash. A surviving ready filename is neither a fresh
input allowance nor evidence that replay is required. The allowance is consumed.

Recorded final database `K98_P021_PreImport_20261107` was READ_ONLY,
RESTRICTED_USER, Broker off, SNAPSHOT on, RCSI off, with file-command settings
disabled. The record does not prove those conditions survived the PC crash.
Earlier host memory/service/session observations are also historical; a new
PowerShell process showing no sessions does not enumerate other processes.

## Feasibility under unchanged limits

| Remaining obligation | Feasible now from retained evidence | Still required before acceptance |
| --- | --- | --- |
| D5a exact custody/readiness | Local source and capture integrity; D5a.1 correction evidence retained. | Approved native read-only inventory of the exact isolated target, resources, source/SQL identity and input custody. |
| D5b outputs and actual maintenance | Existing 42-state/14-export data and immutable bytes provide baselines. | Execute the exact combined candidate on an authorized suitable state, compare numerics/names/old bytes and exercise all six real maintenance children. An empty queue or skipped child is not a pass. |
| D5c concurrency | Prior managed-reader observations remain bounded evidence. | Both arrival orders, real holders/factories/permission boundaries and controlled completion on the combined candidate. Current inventory does not acquire application locks or start workers. |
| D5d faults/cancel/restart | Approved local drain tests cover their specified schedules. | Native fault, disconnect, cancellation, late completion, cleanup and restart ownership cases on an authorized target; no production replay. |
| D5e measured cost | Historical Phase 1 results remain historical. | Warmup plus at least five balanced OFF/ON pairs with comparable preconditions, actual child work and all resource/stage limits. |
| D5f integration | Full obligation register and unresolved gates remain linked. | Final candidate evidence for every row, or explicit unresolved disposition; separate D6 decision. |

The last recorded target is completed and read-only. It supplies no authorized
fresh producer work or demonstrated repeatable mutable pre-state. Actual
maintenance changes ledgers/index/statistics state; read-only access cannot prove
its cost. Repeating the completed input, invoking the old reset/restore harness,
using a new copy, or treating a rollback-only run as equivalent is not authorized.
A smaller fixture cannot replace required retained full-size evidence. Inventory
may reveal existing state, but it cannot create permission to mutate it.

Therefore full native D5b–e qualification is **not currently executable under the
retained-state evidence and existing authorization**. This is a specific
feasibility gate, not a request to shrink D5 or replenish the allowance. After
inventory, return a case-to-prestate matrix showing which cases can use existing
state and which remain infeasible without a separate operator decision. Do not
propose a reset/restore/new input as an implicit continuation.

## Proposed D5a.2 execution packet — approval required before starting

Purpose: determine whether the retained isolated environment still matches its
last accepted receipts, and identify the remaining blockers. No workload is run.
Prepare and statically check a narrow collector against this packet after
approval; pin its bytes and exact allowlists in a new host-side receipt before
executing it. The old `Collect-P021GuestReadiness.ps1` is source material only:
its 20-second SQL timeout and broad inventory are not reused unchanged.

### Target and access gates

1. Host `9SX2VF4`, elevated Windows PowerShell 5.1 Desktop. Read identity,
   elevation, free physical memory and relevant disk space. Do not start a
   service, alter rights, change a schedule, or launch a visible helper without
   an explicit need for operator interaction.
2. Inspect only VM ID `2ac1b401-7076-4965-af71-de36ee0f9f9c`, expected name
   `K98-MGE-Qualification-20261029`. Require Running and zero network adapters.
   No start/resume, checkpoint, configuration change or alternate VM.
3. Reuse exactly one Opened/Available PowerShell Direct session matching that
   VM ID in the chosen elevated host process. Never guess a previous session
   number. If none exists, stop for an operator-created authenticated session;
   do not collect credentials in logs. If multiple sessions match, stop for
   disambiguation. Preserve a borrowed session after use.
4. Verify guest `MINI_AMD`, Microsoft virtual-machine identity, the same VM
   binding, and guest disk reserves. Stop before SQL if identity, isolation,
   authorization or an actual resource gate fails. Record host/guest memory
   as observations; assigned memory is not free physical memory. Preserve the
   original 8 GiB host **pre-start** prerequisite and 8 GiB guest disk reserve;
   do not invent an additional post-start host or guest free-memory threshold.

### Bounded read-only collection

One attempt, no automatic retry. Maximum 300 seconds wall time, at most 48 SQL
statements, at most 512 returned rows per statement and 2,048 rows overall,
host receipt at most 1 MiB. Caps include errors/diagnostics. Exceeding a cap is
an incomplete observation, not permission to truncate and declare success.
Cancel/dispose only owned operations on failure; retain a bounded failure
receipt. No guest-side evidence files or script installation are needed.

| Group | Exact permitted observation | Bounds and refusal behavior |
| --- | --- | --- |
| H: host/guest resources | Identity above; free memory and free space on the host receipt volume and guest volumes identified by the retained DB/input receipts. Read only the relevant SQL service and Bot/Python/PowerShell process identities, without arguments or environment dumps. | Two resource samples, before and after; at most 32 relevant process records. No process termination, service/task changes or broad machine inventory. Unexpected active business producer means stop. |
| F: input custody | The three retained Import_Ready/Import_Claimed/Import_Archive directories under `C:\discord_file_downloader\downloads` in the guest; names, sizes, SHA-256 only, compared to the final 21-file inventory. | Nonrecursive; stop on a reparse point in the path or its ancestors, unexpected subdirectory, extra file, changed size or path escape. At most 21 regular files / 2 MiB read. No copy, rename, archive, delete, claim, content export or replay. |
| S1: SQL identity/settings | Local shared-memory `lpc:localhost`, integrated authentication, initial `master`; server identity/version, exact target catalog row and its file paths/owner, collation/compatibility, read-only/access/Broker/SNAPSHOT/RCSI/trustworthy state; exact file-command configuration names from the retained receipt. | Only `K98_P021_PreImport_20261107`, historically database ID 7, on `MINI_AMD`. Match the complete identity tuple; database ID alone is insufficient. A missing/mismatched/changed target stops target reads. No alternate ROK_TRACKER/old MGE database. |
| S2: installed contract | In that target only, SELECT catalog existence/type/column metadata and definition fingerprints for the explicit union of retained module contracts and fixed 30-object D4 profile. Read at most eight allowlisted migration-history records and their matched deployment records if the verified tables/columns exist. | Materialize/pin names from the local receipts and SQL source before execution; no arbitrary discovery or whole-database definition export. Use the original SQL fingerprint encoding/canonicalization when comparing catalog fingerprints, not Git file hashes. Missing D4 objects may be an expected predecessor state; record absence, do not install them. |
| S3: retained ledger state | Only if catalog shapes match authoritative SQL source: six MaintenanceWork rows; MaintenanceConfigurationWork ID 1; MaintenanceBackupWork ID 1; MaintenanceKvkWork state/generation/claim metadata capped at 64 rows plus one overflow sentinel. | SELECT explicit verified columns only. No claim/complete/repair/reseed/expiry and no stored-procedure execution. Do not infer imported/report completion from a released claim or maintenance row. Missing ledgers are reported as missing. |
| S4: resource/closure receipt | Target log usage and target version-store allocation from permitted metadata views; owned SQL session identity/login time, then verification of closure by a separate owned observer connection. | Permission denial is a gap, never a grant/escalation or broad fallback. No business-table scans, row-count queries, DBCC, performance counters loop or arbitrary session inspection. |

Expected target data/log paths, recorded in the historical reset script's
identity guard (that script is not executed):
`C:\Program Files\Microsoft SQL Server\MSSQL16.MSSQLSERVER\MSSQL\DATA\K98_P021_PreImport_20261107.mdf`
and the same directory's `K98_P021_PreImport_20261107_log.ldf`. Compare owner
identity with the final retained contract; never repair it automatically.
Capture any available catalog incarnation identifier as a new observation,
without inventing a historical match. File paths/IDs alone do not prove unchanged
business rows; later D5 output checks remain necessary.

All SQL connections: pooling disabled, connect timeout 5 seconds, command timeout
3 seconds, session LOCK_TIMEOUT 0, READ COMMITTED, no explicit long transaction.
At most two owned SQL connections, used sequentially (work then closure
observer). Record the work connection's session ID and login time; disposal plus
the observer must distinguish an absent session from a reused ID. Dispose the
observer as well. If closure cannot be established, report cleanup uncertainty
and stop; do not KILL an uncertain owner. No deliberate metadata hold occurs
in this packet. Bound the overall host invocation independently of SQL timeouts.

Session-local timeout/isolation settings and ordinary connection telemetry are
the only SQL session effects. No DDL/DML, business EXEC, migration, updater,
permission probe that mutates state, statistics/index work, backup, SQL Agent
dispatch, provider/network call, restore, recovery, database-setting change or
Bot launch is authorized by this packet. Recheck exact VM isolation after the
collection and record whether it remained verifiable; do not change it.

### Stops, outcomes and next decision

Stop on identity/isolation/resource mismatch, unexpected active producer, input
custody drift, timeout/blocking, cap overflow, permission gap that prevents a
required observation, or uncertain connection cleanup. Do not retry under a
larger budget. A blocked/absent metadata result is not evidence that work is
absent. Keep all original and new failure receipts separately.

Return one of: **retained predecessor verified**, **unexpected state requiring
review**, or **inventory incomplete**, with exact missing observations. Even a
verified predecessor does not permit installation, input consumption, due-work
seeding or native qualification. Bring back the case/state feasibility matrix
and any next bounded execution proposal before mutation. No blanket D5b–e
authorization is requested now.

## Unchanged programme limits and downstream boundaries

- Consumed 21-input allowance; no new copy/reset/restore/input or schedule change.
- RCSI off; host free memory before VM startup and each relevant disk reserve
  at least 8 GiB. No additional 8 GiB post-start host or guest free-memory
  reservation applies. Optional
  statistics require sampled log below 70%; version store below 512 MiB.
- Observations: 3-second statements, zero row-lock wait. Later approved held
  metadata tests remain bounded to 30 seconds; none run in D5a.2.
- Later D5 cost: overall median ON at most OFF × 1.20 + 1,000 ms, each report
  stage at most OFF × 1.20 + 250 ms. At least five balanced pairs after warmup.
  The 1,800-second rehearsal cap does not increase any Bot timeout. D5a.2's
  smaller inventory envelope does not replace these rehearsal limits.
- Original CI failure, failed local drain reproductions and raw SQL 3961
  SNAPSHOT/history-across-REBUILD evidence remain unchanged. Managed metadata
  protection does not prove arbitrary reader/DDL safety. No retry erases them.
- D6 remains separate: actual-host source/updater/seed/process identity and
  rights, every changed path and ancestor including archives, coordinated
  transition and verified SQL receipt. After SQL commits, continue forward
  from that same verified receipt only. P03 blockers and essential P04 precede
  normal import/export. D7/P05 retain whole-flow/provider/natural acceptance.

## Validation and security routing for this review

Delta: this Markdown plan and ignored local evidence metadata only. No executable,
SQL, configuration, permission or deployment change. Existing runtime/test
modifications belong to the separately approved D5a.1 correction and remain
byte-pinned. No new deferred optimisation item: the retained-state/resource
questions are required D5a gates, already tracked here and in the full register.

Run architecture, deferred-item, security-routing, explicit-path test selection,
document links/whitespace and evidence/candidate custody checks. Runtime tests,
smoke imports, command registration, semantic-oracle reruns, native SQL/VM work
and full pytest are skipped for this documentation/evidence review: no behavior
changed and repeating them would not establish current native readiness.

Security review decision: documented skip for this exact Markdown/evidence
delta, inspected against the source/authorization limits above. It neither
implements nor executes the proposed collector. The earlier drain correction's
Changes scan remains its own evidence; it does not cover a future collector.
Before that implementation executes, make its own exact Changes/Deep-off review
decision and validate its fixed query/path allowlists and cleanup behavior.

Review results: architecture passed (zero applicable Python files), deferred-item
validation passed (one document), security-routing passed (zero errors/warnings),
and explicit-path test selection completed. Its generic smoke/registration and
release/schema/permission-test suggestions are skipped for the reasons above;
no manifest, command, schema or permission changed. The 196-file audit passed;
the three approved drain files and both original CI logs match their prior
hashes. Document links, whitespace and final evidence custody are checked
separately in the private review receipt. No native command or SQL connection
was made in this review, and no input allowance was consumed or replenished.
