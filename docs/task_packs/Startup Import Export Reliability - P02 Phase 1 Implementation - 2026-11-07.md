> **Current status, 9 November 2026:** Phase 1 isolated SQL, shared latest names, numeric/export accuracy and recovery-reader qualification passed. Production release and the remaining P02 phases are separate. See the final acceptance section below.

# P02 Phase 1: SQL, names, numeric types and exact exports

7 November 2026. Implementation and isolated testing approved. Production
deployment remains separate. This is Phase 1 of the integrated P02 plan; the
remaining contention and maintenance phases are unchanged.

## Delivered candidate

The previously qualified nine-procedure endpoint rewrite is preserved as a frozen
comparison baseline. The Phase 1 candidate keeps its reduction from full history
cache deletion/reinsertion to first/last endpoint rows. The deterministic governor
name fix remains included and unchanged from its qualified form.

The candidate aligns 139 formerly float columns in 31 active output tables:
whole-number IDs/counts/deltas become bigint and bounded PowerRank fields become
int. The 32 legacy history caches retain their original definitions and contents
for explicit compatibility/rollback; no cache/table retirement is performed.
Raw KingdomScanData4 history is unchanged. SUMMARY_PROC's joins/output ordering
remain unchanged, now operating on matching integer column types.

All nine summary children use exact temporary count/ID fields. Differences are
calculated in decimal(38,0) before checked assignment to bigint. Averages use
decimal(38,6) before rounding to the nearest whole number, halfway away from zero.
Eight ordinary direct-call procedures now own a nested transaction/error boundary;
the alternate healed path already had one. An unrepresentable result rolls back
output/state changes instead of leaving partially refreshed results. Parent
transaction ownership, cutoff/ranking/state and no-new-scan semantics remain.

The approved consistent-rounding change corrects truncation in healed, ranged and
kill-point aggregate rows. In the retained synthetic regression dataset, exactly
44 fields change: 8 healed, 10 kill-point, 4 ranged and their 22 parent-export
counterparts. All are in the three aggregate governor rows. For example, an
average delta previously reported as 2692 becomes 2693, and -886 becomes -887.
Each difference is checked against an independent Decimal oracle; ordinary player
rows must compare exactly. The full-size dataset needs its own explicit difference
list, rather than assuming these fixture counts apply there.

## Export contract

The existing immutable-capture DAL and direct compatibility route construct frames
from original SQL values before pandas can infer float for nullable integer
columns. Direct row iteration uses tuples so a neighbouring fractional column
cannot coerce an integer. Standard integer columns retain integer formatting.

- Ordinary IDs/counts within the consecutive double integer range remain numeric.
- Larger exact integer IDs/counts are RAW decimal text. No rounding is allowed.
  Spreadsheet formulas requiring numeric arithmetic on those large text counts
  need an exact-number consumer; automatic spreadsheet arithmetic is not claimed.
- Decimal cells remain exact RAW text, preserving existing immutable capture rules.
- Nulls remain blank. Dates and ordinary fractions retain their established format.
- Large approximate float inputs are rejected for new output; they are not
  presented as recovered original integers. Direct output validates cells before
  clearing a worksheet.
- Existing immutable payload bytes and hashes are never regenerated. Both old
  numeric captures and new text-valued captures retain legacy-export/1 decoding.

Helpers live in core/export_numeric.py and services/export_output_dal.py, used by
the existing gsheet_module.py and services/legacy_export_snapshot_dal.py boundaries.
No commands, UI, permission, provider admission or import allocation changes.

## Local schema qualification and rollback

SQL qualification/p02_phase1 contains the frozen endpoint module/table definitions,
numeric/hash manifest, canonical index layout and guarded apply.py. It deliberately
accepts only the verified local K98DEV instance and UUID-named fixture databases
with matching session/database ownership tokens. It cannot install into the retained
VM or production. It is a qualification helper, not a production release installer.

The transaction verifies source bodies/options/signatures, types/nullability,
indexes/primary keys and stored values; blocks concurrent writers; drops/recreates
reviewed dependent indexes while preserving primary-key names; alters existing
columns; and installs the reviewed bodies. Unknown/mixed layouts and signed modules
are refused. Repeat installation/rollback validates the complete known state.

Rollback returns to the endpoint-only candidate with its deterministic name fix,
without replaying reports or rewinding watermarks. It refuses output or source
values that would exceed safe float compatibility. Rolling all the way back to the
old full-history rewrite remains the separate prior package, including its current
history-cache refresh. A database restore is not silently substituted for rollback.

## Validation and remaining gates

- Final native SQL run: 91 passed (28 Phase 1, 30 preserved endpoint, 33 names).
  Includes all nine direct entries, parent/subsequent corrections, cutoffs, nulls,
  signed deltas, decimal averaging, 2^31/2^53/bigint limits, aggregate-sum overflow
  avoidance, checked-delta overflow, failure rollback, duplicates, caller permissions,
  migration repeat/rollback, signatures, source/owner/index drift and schema faults.
- Native SQL to real Bot capture and immutable serializer passed: summary plus
  names, 49 numeric summary fields, 9,007,199,254,740,993 preserved as exact text,
  ordinary IDs numeric, bytes unchanged after load. Python network connections
  blocked; no provider calls. Owned databases removed after the test.
- Full Bot run completed: 11,949 passed, 41 failed, 62 fixture errors, 1,125 skipped,
  in 1,203.50 seconds. Of the 41 failures, 34 were caused by a too-long Windows
  temporary path; all passed with a short private path outside Git. The other seven
  failures and 62 fixture errors concerned the previous Bot/SQL source definitions.
- Final combined regression: **2,085 passed, 5 skipped in 160.01 seconds**. Includes
  every failed/error case from that full run, all transition families, exact-number
  export tests, SQL historical compatibility and affected import/configuration callers.
  The pytest failure cache confirms none of the original 103 failed/error node IDs
  remains failing. This is reconciled full-plus-focused evidence, not a claim of a
  second all-green full-suite run.
- The earlier interrupted run placed private export spools inside Git; that test
  setup error is preserved in its log. Subsequent path-length failures are also
  preserved. Use a short, unique system-temporary path outside Git for this suite.
- Architecture (48 files), deferred (45 documents), security routing, Ruff,
  command registration and import smoke passed. The smoke check uses documented
  test settings and UTF-8. Ruff was rerun without cache after a cache-write permission
  failure; neither workaround changes product behavior.
- Final separate Changes reviews completed: 20/20 Bot and 52/52 SQL source items,
  zero findings, Deep off. Bot scan 4854d794-c7d5-43fa-8ee6-d41469664bb8 supersedes
  its first Phase 1 scan after release-definition preparation. SQL scan
  c5ab155b-4fbd-417b-aea3-a7c3e15a271a remains valid: all original SQL source is
  unchanged. The new generated historical-source reference was independently
  verified in a documented supporting-artifact addendum; it has no runtime or
  installation effect. Supporting-test changes were recorded by the Bot reviewer.
  Static security review is not runtime acceptance.
- Full-size restored import/report cost and concurrency qualification remain open.
  Native fixture tests do not satisfy that gate. Prior ON version-store failure
  remains binding; no candidate speedup or resource pass is claimed.
- Fresh installed bindings, SQL signing/source profiles, installed updater-tool
  qualification and explicit rehearsal/release installers remain required before
  installation. The local Bot source transition is now prepared as described below. Historical
  source pins correctly reject changed bytes and must not be weakened. Production
  approval, incident continuation and provider acceptance remain separate.

## Exact Bot package and preserved SQL history

`p02_phase1_sql_exports_v1` is a complete 18-member alternative from the same
original Bot predecessor as the uninstalled P02.1 candidate. It includes all 15
observer-family members plus the two exact-number helpers and gsheet_module.py.
All 18 real HEAD/candidate source pairs passed exact package admission. All prior
68 registry entries remain canonically identical; their digest is
`e597ff1675273105575034624721bd81205a795e6d9fde30cc96ffa8d4f113b5`.
Unknown, missing, modified and partially inventoried members are refused. The
installed predecessor still refuses this new package until its updater is properly
upgraded. No updater or runtime was installed by these checks.

The registry reader now accommodates exactly 69 entries, with the new family
limited to its fixed 18 members. Its bounded serialization capacity is 177,152
bytes, including Windows newlines. These release-format bounds are separate from
the unchanged workload, memory, disk, timeout and concurrency limits below.

SQL qualification/p02_phase1/released_sources.json preserves nine original source
texts and their historical release hashes, plus exact candidate source/body hashes.
Original sources match HEAD after newline normalization; stored CRLF bytes match
the historical permission manifest exactly. Bot tests authenticate the complete
reference, current source and body before checking the old permission forms. They
reject unreviewed source prefixes. Runtime permission allowlists and historical
SQL manifests remain unchanged. The local qualification installer never reads this
test reference; passing these tests does not admit Phase 1 under an old SQL profile.

## Existing limits, unchanged

| Check | Limit |
| --- | --- |
| Host free memory before starting the VM | At least 8 GiB; operator-approved reduction from 16 GiB |
| Guest free disk reserve | At least 8 GiB |
| Observed version store | Below 512 MiB |
| Sampled database log use | Below 70 percent |
| Measurement | Warm-up followed by five balanced measured pairs |
| Overall ON median | At most OFF median x 1.20 + 1,000 ms |
| Each report-stage ON median | At most OFF median x 1.20 + 250 ms |
| Short recovery observer statement | 3 seconds, zero row-lock wait |
| Concurrent reader exercise | Real short observers and a bounded 30-second held reader |
| Full rehearsal statement cap | 1,800 seconds; a test bound, not a Bot timeout increase |
| Existing connection/coordination defaults | 5-second dedicated login, 15-second default query, 1-second metadata lock wait, 15-second coordination horizon; explicit long-operation overrides retained |

The 8 GiB host check is the existing VM startup prerequisite, not an additional
8 GiB reservation imposed after the VM is already running. These are acceptance
and headroom limits, not new application timeouts. The isolated
test VM remains 4 CPUs / 8 GiB RAM / no network adapters. RCSI is unchanged.

## Evidence and ownership

Private evidence: root Bot .codex_artifacts/p021/phase1-sql-final,
phase1-sql-export-integration.json, phase1-bot-full-corrected.log,
phase1-reconciled-regression.log, phase1-bot-package-validation.json, the preserved
phase1-bot-full.log and the unchanged earlier
rehearsal/analysis receipts. Both repositories retain separate review targets.
SQL owns schemas/procedures and migration; Bot owns exact capture/formatting;
the operator owns the elevated VM session and eventual production decision.

## Full-size summary correctness result, 8 November 2026

The V2 workload completed both SQL arms and verified both rollbacks. Its original
receipt remains StoppedForReview because the final checker incorrectly required
one row per synthetic governor ID in every export. POWER_BY_MONTH legitimately
contains 53 distinct months for each of the three average IDs, as confirmed by
the retained rows and the SQL contract grouping by governor and month.

No VM workload was repeated. The corrected offline verifier first checked every
retained evidence file against the host receipt, then compared all 112 captures:
42 summary/state outputs plus 14 export queries for each arm. Non-summary outputs
are compared as complete exact multisets, including synthetic IDs and multiplicity.
Only the eight final summaries and their combined table/export have the one-row
average contract. Duplicate final averages still fail. Historical rows cannot be
added, removed or changed under this correction.

Result: **full-size rollback-only summary correctness passed**. All ordinary
player rows match exactly. There are 21 independently verified rounding changes:
eight healed values, nine kill-point values and four ranged values. Their copies
in the combined table and export make 63 changed captured cells in total. All
432 aggregate cells across the eight summaries and two combined-output copies
were verified, including cells that did not change. No tolerance or blanket
average-row exemption was used.

The actual candidate SQL-to-export-frame check passed for 827,703 cells with no
provider calls. Both arms restored original procedure definitions, numeric/index
contracts and output/name fingerprints. The host receipt confirms read-only,
snapshot ON, RCSI off, restricted access and disabled file commands afterwards.
The OFF-only samples recorded peak log usage 28.189 percent, zero version-store
KB, and minimum free disk 9.213 GiB. These satisfy the existing resource limits for
this exercise; they do not establish the snapshot-ON limits or concurrency result.

Timing limitation: the runner returned its timing dictionary only after comparison.
The checker exception prevented it being saved. No procedure timings or speed-up
are inferred from file times or sample spacing. Subsequent rehearsal runners must
persist completed workload timings and capture status before output adjudication,
so a checker failure cannot discard completed measurements or encourage a replay.

Regression validation passed 11 offline tests covering 53 historical rows per ID,
added/removed/changed historical rows, duplicate/missing final averages, ordinary
player changes, incorrect or unchanged-but-wrong parent averages, approved rounding,
column drift, exact positive/negative rounding and canonical scalar validation.
The verifier uses exact rational arithmetic and has no SQL or network calls.

Authoritative derived evidence:
`C:\discord_file_downloader\.codex_artifacts\p021\phase1-summary-v2-offline-verification-4bc7d9633a8f478dbc609ff2c5ea1781.json`.
Original operator receipt:
`C:\discord_file_downloader\.codex_artifacts\p021\P02-phase1-summary-comparison-a622fb963fdd434db7fb7b1af887ab1b.json`.
Original failed-checker receipt, all captured outputs, source packages and earlier
failure evidence remain unchanged. Do not rerun V1 or V2 for this result.

Phase 1 is not yet fully accepted. Remaining delivery gates are a fresh baseline
import/report/immutable-export rehearsal with the combined candidate, warm-up and
five balanced OFF/ON timing pairs, short observers and the bounded held-reader
case. The approved full-size SQL and numeric source package is unchanged; only
the evidence checker was corrected. Production deployment remains separate and
all existing limits remain unchanged.

## Fresh import/export qualification prepared — 8 November 2026

The operator authorized the fresh import/export rehearsal and snapshot timing /
concurrency qualification, retaining every existing limit and keeping production
deployment separate. The first new command is
`C:\discord_file_downloader\.codex_artifacts\p021\Invoke-P02Phase1FreshOffRehearsal.ps1`.
It is a one-shot OFF functional warm-up, not the measured performance result.
It has been prepared and locally validated; its full-size guest result is pending.

The host preserves and hashes the previous ON evidence and all V2 comparison
evidence before resetting only the owned database ID 7 from the pinned backup.
The original failed input and both historical archived inputs remain intact.
Runtime dependencies are checked before restore. The SQL candidate commits all
139 numeric-column changes and 11 procedure definitions together before the
canonical 415-row import/report workload. Actual Bot capture, formatting and
immutable payload serialization run against all 14 outputs; payload reload must
be byte-identical. There is no provider delivery or application startup.

Completed SQL timings and stage result sets are saved before outcome checks;
each captured output is saved separately. Both successful and stopped execution
evidence is copied to a new host folder. A stopped run is reviewed, never replayed
automatically. Read-only containment and disabled guest file commands are checked
at completion. No forced session termination or other-database deletion is used.

Validation: 13 offline tests passed, including actual Bot formatting of 49,472
retained rows / 827,703 cells across 14 exports, unchanged threshold negatives,
package/custody pins and timing persistence. Native local SQL tested successful
commit, a forced late installation failure with full schema/body rollback, and
post-commit names/summary execution. The test proxy substitutes only the two
VM-specific identity/data-size SELECT results in an independently guarded local
fixture; the real local target is refused by the VM adapter. PowerShell 5.1 parsed
all three wrappers; 20 changed/uncertain states were refused; 40 SQL statements
parsed against local SQL. Disposable native fixtures were removed.

Next sequence remains:

1. Review this fresh OFF receipt, all output semantics and immutable payload.
2. Run an ON functional warm-up from the same fresh baseline.
3. Run five measured OFF/ON pairs with alternating arrival order, preserving each
   completed run before the next baseline reset. Install the same candidate before
   workload timing; do not measure migration or restore as import duration.
4. Exercise actual recovery observers in both arrival orders, then the bounded
   30-second held-reader case. Check physical cleanup and no retained locks.
5. Assess timing and resource evidence together; prepare production release only
   as a separate, explicitly reviewed step.

Unchanged limits: four CPUs / 8 GiB VM memory; at least 8 GiB guest free disk;
observed version-store peak below 512 MiB; sampled log use below 70 percent;
ON median at most OFF median × 1.20 + 1,000 ms overall and + 250 ms per report
stage; observer statement timeout 3 seconds and zero row-lock wait; RCSI off.
The explicit 1,800-second rehearsal statement cap does not alter Bot limits.
Warm-ups are excluded from measured medians. No snapshot speed-up or concurrency
acceptance is claimed before the required runs complete.

Security routing: private ignored rehearsal artifacts lack a supported Git diff
target. A separate immutable artifact risk review was completed; it is not a new
Git Changes vulnerability scan. Existing Bot/SQL source reviews remain separate.
No Codebase/Deep scan, release, merge, restart or production action was performed.

Prepared run: `4b84746f36d84161a3840506bca54368`; manifest SHA-256 `f905353e859bfad1788b1776c0962dac3a375152c0216d960d02ca18b00d20e1`.
Private evidence: `phase1-fresh-off-seal.json`, `phase1-fresh-offline-export-proof.json`, `phase1-fresh-native-validation.json`.

## Post-restore capacity stop and integrity continuation — 8 November 2026

Receipt `P02-phase1-fresh-off-434414227539458abc676f1a2dc08c83.json` confirms
the restore completed in 40.30 seconds, owner verification passed and the owned
database returned to read-only/restricted containment. The full integrity check,
candidate installation and fresh import/export did not run. All 150 prior ON/V2
evidence files had already been preserved and verified on the host.

The integrity capacity guard incorrectly counted its entire 1,794,114 KiB
estimate (1.711 GiB) as additional disk usage. Earlier live evidence recorded
2.027 GiB of unallocated space inside already-allocated tempdb data files.
Current capacity is not inferred from that older measurement: the new continuation
remeasures both free extents and filesystem space immediately before CHECKDB.

`Complete-P02Phase1FreshOffRehearsal.ps1` is a separate one-shot continuation of
the exact stopped receipt. It has no restore route. It admits CHECKDB only when
the entire estimate fits existing free tempdb extents and filesystem free space
is at least 8 GiB. No growth allowance, reserve reduction, shrink, deletion or
file resizing is introduced. After CHECKDB, unchanged tempdb file allocations,
the 8 GiB reserve, pre-import business state and containment must still verify.
Only then may the unchanged original guest execution wrapper submit the first
pending import. Original stopped receipts, executable package and evidence remain
unchanged. An attempted integrity check has its own exclusive marker and cannot
be replayed automatically.

Validation passed under Windows PowerShell 5.1: historical false-stop regression,
exact reserve boundary, six invalid-capacity cases and thirteen changed-baseline
refusals. Fifteen literal SQL statements parsed; live local tempdb row shape,
the actual estimate-message parser and full CHECKDB passed on a new owned local
fixture, which was removed. The immutable four-file continuation artifact received
a separate risk review. This remains private-artifact review, not a new Git Changes
vulnerability scan or production acceptance.

Continuation source seal: `phase1-integrity-continuation-seal.json`.
Prepared command:
`C:\discord_file_downloader\.codex_artifacts\p021\Complete-P02Phase1FreshOffRehearsal.ps1`.
Execution is pending the retained Administrator session. Fresh-output review,
balanced OFF/ON timings and short/held-reader concurrency remain open. Every
existing limit remains unchanged and production deployment remains separate.

Capacity semantics were checked against Microsoft's
[CHECKDB ESTIMATEONLY documentation](https://learn.microsoft.com/en-us/sql/t-sql/database-console-commands/dbcc-checkdb-transact-sql)
and [tempdb free-extent documentation](https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-objects/sys-dm-db-file-space-usage-transact-sql).

## Integrity passed; read-only preflight corrected — 8 November 2026

Receipt `P02-phase1-fresh-continuation-6c2f3f9969c84b2b92e340f83d9d8ad3.json`
confirms the full integrity check passed in 26.85 seconds. The 1,837,172,736-byte
workspace estimate fit within 2,175,139,840 bytes of existing free tempdb extents;
no tempdb file grew. Filesystem free space afterwards was 9,869,873,152 bytes,
above the unchanged 8 GiB reserve. Restore was not repeated.

The next stage stopped in `ReadOnlyPythonPreflight`, before input publication,
candidate installation or import. No execution-started/result/export artifact
exists in the returned 22-file evidence set. The wrapper retained only the first
traceback line because Windows PowerShell 5.1 treats redirected native stderr as
an error under Stop. Source review identified an independent incorrect expectation:
the OFF runner required snapshot OFF while the database was read-only. A broad
mode-token replacement had changed that metadata check as well as workload mode.

V2 is a distinct package/run/preparation/owner/input. Only the Python read-only
metadata tuple changes to ON. Actual writable workload mode still explicitly sets
OFF and verifies numeric snapshot state zero before installation. Every SQL/Bot
source and other package member is byte-identical to V1. The shared Python launcher
now uses hidden Start-Process with Wait, separate durable stdout/stderr files and
the physical exit code; missing exit code and existing log paths fail closed.
Prior read-only diagnosis and both current execution callsites use that helper.
Executed scripts, receipts and original input/evidence remain unchanged.

The new host first verifies the exact stopped receipt and all 22 retained files.
Live guest guards require the pre-import 1244 / 486427 / 1092 baseline, read-only
containment, absent execution markers and no publication of the old attempt's
input. A bounded read-only reproduction must retain the complete traceback and
confirm the known metadata error before new work can begin. A different cause
stops with the full evidence. No restore or CHECKDB is repeated.

Validation: 13 complete-preflight, negative-state, ownership/replay and exact
package-delta tests passed. Native local SQL independently verified five state
transitions, including read-only ON reporting from writable OFF and the return to
OFF when writable again; the disposable fixture was removed. Actual PowerShell
5.1 tests reproduced old stderr truncation and verified complete traceback/exit1,
successful warning/exit0, paths containing spaces, rejection of existing logs and
unsafe labels, and equivalence of the embedded launcher. Four scripts parsed.
The separate immutable artifact risk assessment passed schema validation; no new
Git Changes vulnerability scan, Codebase/Deep scan or production action is claimed.

Prepared command:
`C:\discord_file_downloader\.codex_artifacts\p021\Invoke-P02Phase1FreshOffRehearsalV2.ps1`.
Source seal: `phase1-fresh-v2-seal.json`. The retained Administrator session is
required for execution. Fresh-output review, OFF/ON measured pairs and concurrency
remain pending. Existing limits and separate production deployment remain intact.

## Evidence-array handoff correction — 8 November 2026

Receipt `P02-phase1-fresh-v2-873b38c0fa174446901a73a68b907de7.json` stopped at
the first evidence-count check. Python diagnosis, V2 package preparation and the
fresh workload had not started. Restore/integrity were not repeated.

The exact receipt reproduces a Windows PowerShell 5.1 boundary defect: wrapping
the ConvertFrom-Json pipeline directly produced one outer array item containing
the 22 evidence records. The new reviewer decodes first and then wraps that value.
The exact 22-file count and every filename, byte-length and SHA-256 check remain
unchanged. The V2 execution package and guest executor remain byte-identical.

Tests ran the actual complete reviewer source and baseline helper in eight
separate Windows PowerShell 5.1 jobs using the actual host JSON serialization and
Invoke-Command argument boundary. Guest OS/files/SQL/Python were explicitly
simulated. The original failure reproduced; the full valid path passed; missing
records, changed hash/size, nested arrays, singleton objects and a different Python
failure were rejected. This is control-flow qualification, not a VM workload result.

The separately sealed V3 host is pinned to the latest stop and original preflight
receipt. It reuses the unstarted V2 run `8ac5bc5767e24a60b728c6a8fd8227d2` and
contains no restore or CHECKDB repetition. All original evidence remains intact.
New command:
`C:\discord_file_downloader\.codex_artifacts\p021\Invoke-P02Phase1FreshOffRehearsalV3.ps1`.
Evidence: `phase1-evidence-handoff-validation.json`, `phase1-fresh-v3-seal.json`.
The private immutable artifact review passed validation; no new Git vulnerability
scan or production action is claimed. Execution and the remaining fresh-output,
snapshot timing and concurrency gates remain pending. Existing limits are unchanged.


## Fresh OFF completion and rolling-window verification — 8 November 2026

Receipt `P02-phase1-fresh-v3-c9fe1d4429e1460792a21df712daa3ab.json` records
an actual completed import, not another preflight failure. The candidate's 139
numeric columns and 11 procedures committed; the 415-row import reached scan
1245/counter 1093; report continuation reached stage 3; the input was archived;
history contains 486842 rows. Do not replay this import.

The 13 report stages completed. Import plus reports took 15.437 seconds, including
3.100 seconds for SUMMARY_PROC; immutable capture took another 6.125 seconds.
These are one OFF warmup observation, not balanced timing acceptance. Fifteen
resource samples recorded minimum free disk 9834631168 bytes, maximum observed
log use 2.399260044 percent, and zero version-store KB. All limits are unchanged.

All 39 copied evidence files match their recorded sizes and hashes. The actual
Bot captured 14 immutable export sections, 49472 rows and 827703 cells, with no
provider calls. The 17515646-byte payload has SHA-256
`5cf5550cdbdc47386da53d007409acd554c6777a59f6f679117589319bcffec9`.
The actual Bot immutable loader also reloads those saved bytes unchanged locally.

The sole stop is the final checker expecting snapshot OFF after READ_ONLY. SQL
Server reports ON for READ_ONLY, as independently established by the retained
native state-transition tests. The workload explicitly set OFF and required
numeric state zero while writable. Final evidence is READ_ONLY/RESTRICTED_USER,
Broker disabled, and xp_cmdshell/show advanced options restored to zero. Original
receipt, result, source package and failure remain unmodified. Derived review:
`phase1-fresh-v3-offline-review-4a3fd953d94d49078b32a02972ec2c14.json`.

Thirteen canonical exports match the earlier validated candidate exactly as
multisets. SUMMARY_CHANGE_EXPORT has 126 changed rows, confined to eight rolling
six-/twelve-month fields. The earlier comparison froze its clock and the fresh run
used the actual clock. This is a plausible explanation, not an accepted waiver:
independent source-date/value verification must finish before resetting this
database for ON. Fresh-output correctness is therefore still open.

Prepared `Collect-P02Phase1CompletedSource.ps1` performs SELECT-only checks and
captures 486842 source rows plus eight summaries, their combined export and state
into a new bounded evidence folder. It checks exact VM/session/no-network binding,
4 CPU/8 GiB allocation, retained 39-file hashes, archive identity, read-only SQL
containment, completed import/report identity, physical files and all 172 installed
module hashes. No restore, import, report execution, database setting, service,
provider or production action is included. Disk reserve remains 8 GiB. Per-file
capture is bounded to 500000 rows and 256 MiB uncompressed row bytes.

Validation: 39 Python tests passed, including full retained-evidence review,
immutable reload, completion/resource refusal cases, all containment fields,
every read-guard branch and capture replay refusal. Eighteen separate Windows
PowerShell 5.1 processes exercised the complete guest wrapper and JSON handoff
with simulated guest OS/files/SQL-process boundaries. Valid collection passed;
wrong host, active tasks/processes, disk, prior file hash/size/count, nested arrays,
unsafe path, archive/source changes, replay and incomplete results were refused.
This is local harness validation, not execution of the new guest collector.

Canonical SQL row captures omit original Decimal scale/type metadata; they must
not be reconstructed as inferred int/float cursor values to claim identical
format requests. The actual saved payload/loader proof remains distinct from
source-value correctness. No inferred numeric-type formatting waiver is applied.

Security boundary: this new read-only collector is in ignored private artifacts,
outside Git Changes scan targets. Its fixed SQL, exact ownership, path/hash guards,
new-only evidence writes and hidden local Python launcher were reviewed locally.
No new Codex Security vulnerability scan is claimed; earlier Bot/SQL Changes
reviews remain separate. Full runtime tests, registration/smoke gates and new
whole-repository scans are not repeated for this private collector/documentation
step. No PR/promotion/deployment is requested. Snapshot warmup, five balanced
timing pairs and real observer/held-reader concurrency remain pending after the
source verification gate; production deployment remains separate.


## Exact stored-definition fingerprints — 8 November 2026

The read-only source collector stopped before capturing any rows. Receipt
`P02-phase1-completed-source-3eef1109bdf54b339a95246092e458aa.json` and all
five copied files were verified by size/hash and preserved. No import, report,
restore, database setting or production action occurred.

The definition guard compared submitted ALTER PROCEDURE text with the stored
definition. A new native local qualification reused the complete candidate
installer in fresh, owned disposable K98DEV fixtures: all 139 numeric changes
and 11 procedures committed, the late-failure rollback test and post-commit
names/summary calls passed, and the fixtures were removed. All 11 stored
definitions began CREATE PROCEDURE. Replacing only the initial ALTER keyword
with CREATE in each submitted body reproduced every stored SHA-256 exactly;
the remainder of every body was byte-identical. Evidence:
`phase1-definition-storage-86345d0ee7b54f8abe5f9e598c6fb77b.json`.
This proves the fingerprint defect locally; the corrected VM inventory is still
required and unexpected differences are not waived.

The separately sealed V2 source collector changes only these 11 expected stored
fingerprints. The other 161 hashes, complete 172-object membership check,
containment/ownership checks and all existing resource limits remain unchanged.
It also retains actual hashes and explicit missing/unexpected/changed-object
details before rejecting a mismatch. Changed definitions are captured within
262144 bytes each and 4 MiB total; omitted bodies remain explicitly marked and
do not count as a successful comparison. No SQL-body whitespace normalization
or broad mismatch allowance is used.

Command prepared for the retained Administrator session:
`C:\discord_file_downloader\.codex_artifacts\p021\Collect-P02Phase1CompletedSourceV2.ps1`.
It reads the already-completed database, writes a fresh evidence folder, and
preserves the failed source collection and original OFF evidence. It does not
repeat the import, reports, restore or integrity check.

Validation: 48 Python tests passed, including native-fingerprint reconciliation,
exact mismatch refusal, bounded diagnostics, full collector success/failure
control flow, evidence preservation and physical connection closure. Eighteen
separate PowerShell 5.1 handoff cases passed with the new contract. The actual
native SQL installation/storage test also passed as described above. These
results do not claim the V2 guest collector has run or that rolling-window
correctness, snapshot timing or concurrency is accepted.

Security routing remains scoped to private ignored qualification artifacts:
the fixed SELECT queries and existing VM/file/ownership boundaries did not
change. Exact fingerprint changes and bounded mismatch reporting were reviewed
locally; they are outside Git Changes scan targets, and no new vulnerability
scan is claimed. No production runtime/SQL implementation changed. Whole-bot
runtime, command-registration and smoke checks are not repeated for this
collector/documentation correction; native and focused checks cover its changed
behavior. Production deployment remains separate.


## OFF source verification accepted; ON warmup prepared — 8 November 2026

V2 source receipt `P02-phase1-completed-source-v2-0f97baae34c348c1889711e5d97192f4.json`
completed without errors. All transferred files/captures match their recorded
hashes and sizes; all 172 installed definitions match exactly. Before/after
containment is identical and read-only. The 486842 source rows and all eight
2452-row child summaries, combined export and nine state rows are preserved.

An independent Python oracle checked both captured summary versions against the
source scan history. It uses ScanOrder endpoints, SQL calendar-month subtraction,
the original NULL behavior, exact integers and independent aggregate rounding.
It verified 39840 endpoint cells across 415 affected governors, 432 aggregate
cells and 16272 unchanged unaffected child-summary rows. The 265 changed ordinary
window cells are explained exactly by the cutoff moving from the earlier frozen
2026-11-08 09:40:59 to the fresh summary's 17:33:26.348–17:33:29.447 interval.
There are no source rows on an ambiguous cutoff within that execution interval.
All 117696 numeric cells in the combined export also match the verified children,
including the existing NULL-to-zero rule for Healed, Ranged and KillPoints.

Evidence: `phase1-fresh-source-verification-efb82c5c37084be6ac92058a41a83f09.json`
(extends the preserved first proof `1f25e8a17d4a4ed4854b4434730ce937`). This closes
the fresh OFF source/output discrepancy; none was waived and no import/report
was repeated. Thirteen other exports retain the earlier exact multiset match;
the actual Bot immutable payload and byte-identical reload proof are unchanged.

The sealed ON warmup is `9c43963e5a25475caee3e59cfaaafdff`, prepared via
`Invoke-P02Phase1OnWarmup.ps1`. It revalidates exact completed OFF ownership,
all original inputs, the 172 candidate definitions and copied evidence before
resetting only database ID 7 from the same checksummed backup. It retains the
original failure, earlier OFF/ON/comparison, latest OFF and source evidence.
The other databases are not restore/delete targets. It preserves four existing
input files and publishes one new uniquely named test input only after baseline
and package preflight checks pass.

Restore validation reuses the tested existing-tempdb-workspace gate and full
CHECKDB; the 8 GiB free-disk reserve is unchanged. The 139-column/11-procedure
installation commits while writable snapshot mode is OFF. ON is enabled and
numeric state 1 verified before the import. The final read-only state correctly
expects SQL's ON metadata report. Native stdout/stderr/exit capture is retained;
one-shot markers prevent blind replay. The actual Bot/SQL implementation bytes
and 415-row input are unchanged. Additional bounded child-summary captures run
after timed import/report work so the ON result can be independently verified
without another guest collection request.

Local validation: 22 focused Python tests passed, covering endpoint/null/calendar
semantics, all combined summary values, ON preflight, complete success/failure
lifecycle ordering, replay refusal, cleanup and actual retained-summary capture.
Windows PowerShell 5.1 parses all three new wrappers; exact completed-state
guards accept the eligible fixture and reject 20 changed/uncertain cases. Native
K98DEV validation parsed 44 literal statements and verified writable ON plus
retained ON across read-only transitions in a new disposable database, which
was removed. The new helper's nine fixed SELECTs use the already collected and
source-validated summary tables. No VM warmup execution is claimed yet.

One local lifecycle test in the default Windows temporary directory encountered
a sharing-denied atomic result-file replacement. The focused suite passed in a
new explicit workspace test directory. No retry of SQL/business work, result-write
retry, runtime limit change or production workaround was introduced.

Security review scope: private ignored rehearsal artifacts have no Git Changes
baseline. The changed mode/restore guards, exact identity and evidence bindings,
bounded reads/writes and existing native launcher were reviewed locally, with
the targeted/native tests above; no new Codex Security vulnerability scan is
claimed. Existing Bot/SQL Changes reviews remain separate. No production runtime
implementation changed. Whole-bot runtime/registration/smoke checks are not
repeated for this rehearsal/documentation step; standard architecture/deferred/
security-routing documentation gates remain applicable.

The ON run is a warmup, not the five balanced measured OFF/ON pairs. Overall
median allowance remains 20 percent plus 1000 ms; each report stage remains
20 percent plus 250 ms. Version store stays below 512 MiB, log usage below
70 percent and free disk at least 8 GiB. Actual short recovery observers still
require the unchanged three-second statement limit and zero row-lock wait;
both arrival orders and the bounded 30-second held reader remain unqualified.
Production deployment and overall Phase 1 acceptance remain separate and open.


## ON warmup verified; balanced timing batch prepared — 8 November 2026

Receipt `P02-phase1-on-warmup-b8df03fc91234b0fb0248fc5327003fc.json`
passed with no errors. Independent host verification rehashed all 55 evidence
files and verified the completed 415-row import, all 13 report stages, archived
input, 139-column/11-procedure installation and final restricted read-only state.
Installation used snapshot OFF; the actual workload used numeric snapshot state
1. Server file-command settings returned to zero; no other database or provider
was targeted.

All 14 canonical export sections match the independently accepted OFF run
exactly as row multisets: 49472 rows and 827703 cells. Eight child summaries
also match. The actual Bot immutable export configuration, shapes and values
match OFF, including exact large-number representation; its byte-identical
reload was verified. Different preparation/generation identities legitimately
give different payload hashes. No result difference was waived.

The ON warmup import/report procedure took 14.625 seconds versus the retained
OFF warmup's 15.437 seconds. These are warmups, not a measured performance
conclusion. Sixteen resource samples showed at least 9786245120 free bytes,
maximum log usage 2.405596 percent, and peak version store 5184 KiB (5.0625 MiB).
These pass the unchanged 8 GiB / below 70 percent / below 512 MiB gates.
Proof: `phase1-on-warmup-verification-5b4a4ce5ffbe4e35899255b8cfd20b2e.json`.

The next authorized action is one invocation of
`Invoke-P02Phase1BalancedComparison.ps1` in the retained Administrator Windows
PowerShell session. It runs ten separately owned fresh fixtures in the order
OFF/ON, ON/OFF, OFF/ON, ON/OFF, OFF/ON. Each arm starts from the same checksummed
backup, commits the unchanged Phase 1 package while snapshot mode is OFF, then
sets and verifies its intended workload mode. Only the owned database ID 7 is
eligible. The other databases, original inputs and prior evidence remain intact.

Before every reset the predecessor's complete evidence is rehashed, its proof
and exact manifest checked, and completed execution/report/archive ownership
revalidated. New package, run folder, input, preparation and owner identities are
preallocated and unique. Prior evidence is copied and verified before reset.
Receipts are exclusively created; any failed preparation, workload, verification
or timing gate stops the batch. There is no automatic replay or resume of stopped
work. The fixed host receipt is `P02-phase1-balanced-batch.json`; each arm also
has its own immutable evidence set and derived verification record.

After each arm, the host verifies all exports and actual immutable payloads
before permitting the next reset. The rolling-month summaries are independently
checked against the retained 486842 source rows, including 19920 affected
endpoint cells, 432 aggregate cells and 117696 combined summary cells. Existing
unaffected rows, identity/name/rank, null semantics and exact output precision
remain required. A source row on an ambiguous execution-time cutoff stops the
batch. This accounts for legitimate clock movement without accepting arbitrary
differences. Summary evidence collection follows timed work.

Five OFF and five ON samples are required. The overall ON median allowance is
OFF times 1.20 plus 1000 ms; each of 13 report stages is OFF times 1.20 plus
250 ms. The same per-run disk, log, version-store and statement bounds remain.
Timing comparison must pass every stage, not only an overall average.

Local qualification: 17 package/validator tests passed, including all ten
generated variants, retained real outputs, clock/source oracle, exact threshold
boundaries and disk/log/version/timing failures. Six complete generated-OFF
lifecycle tests passed with injected install/setting/import/containment/close
failures and replay refusal. Eight separate-process Windows PowerShell 5.1 batch
tests passed: complete success, preparation/execution/verification failures,
wrong wrapper path/hash, wrong verification identity and timing refusal. Replay
preserves the original receipt and starts no further action. All 31 generated
PowerShell scripts parse; ten predecessor/archive guards accept their exact
fixtures and reject 200 changed/uncertain states. Tests use mocked SQL/VM
boundaries; no measured VM workload has yet run.

The first separate-process test run inherited PowerShell 7's module search path
through Python and could not discover Get-FileHash. The test subprocess now
uses the native Windows PowerShell module directory; all eight scenarios then
passed. A Python regex escape warning was corrected without changing the
pattern; the sealed source-pin test and all PowerShell guard checks passed again.
No guest workaround, retry or weakened guard was introduced.

Scope/security: only private ignored rehearsal orchestration and these records
changed in this step; installed Bot/SQL payload bytes are unchanged. Private
artifacts have no Git Changes baseline; `security-diff-scan` is therefore skipped
for this private artifact handoff, with the scoped local review recorded below.
Local review covered fixed VM/database identity, source/package hashes, filename
and evidence membership, predecessor custody, exclusive receipts, process exit
capture, failure sequencing and resource gates. Existing separate Bot/SQL Changes
reviews remain applicable to their unchanged implementation targets; these
harness tests are not a production security or concurrency acceptance claim.
Architecture (48 Python files), deferred items (45 Markdown files), security
routing and explicit-path test selection passed. Whole-Bot pytest, smoke imports
and command registration are not repeated for private orchestration/documentation
with no Bot runtime changes. Native SQL parsing is not repeated because the
generated wrappers retain the already qualified SQL statement bodies and fixed
database target; only bound run/owner identities and exact archive inventories
change. All generated PowerShell bodies and both Python workload modes were
qualified as above.

Seal: `phase1-balanced-batch-seal.json`. Balanced timing acceptance remains open
until the actual ten-run receipt is verified. Actual recovery-observer concurrency
in both arrival orders and the bounded 30-second held reader remain the following
separate step, with the unchanged three-second observer limit and zero row-lock
wait. Keeping deliberate overlap out of baseline timing prevents contaminated
performance measurements. No production deployment, provider delivery, merge,
push or overall Phase 1 acceptance is authorized or claimed by this handoff.


## Balanced timing accepted; observer-first rehearsal prepared — 8 November 2026

The operator completed all ten authorized measured runs. Receipt
`P02-phase1-balanced-batch.json` is `BalancedTimingAndOutputsPassed`, with zero
errors and ten verified runs. Independent review rehashed all 550 evidence files,
the executed packages and predecessor chain, reconciled each proof to the batch,
and recalculated overall and all 13 stage medians from captured durations.
Proof: `phase1-balanced-verified-cac2998afe2f4a2f9698669111f1bcfe.json`.

Median import/report procedure time is 14390 ms OFF and 14328 ms ON, against
the unchanged maximum 18268 ms. All 13 stages pass; summary medians are 3027 ms
OFF and 2996 ms ON. This establishes acceptable measured snapshot overhead,
not a material speed-up attributable to snapshot mode. The workload package
already contains the SQL/names/types/export improvements in both arms.
Each arm passed full output/immutable-export verification and its independent
source-summary oracle. Minimum sampled/final free disk across the batch was
9421275136 bytes, maximum log usage 2.413309 percent, and maximum version store
5184 KiB. All limits remain unchanged. No warmup is counted among the five pairs.

The following step is one separately owned observer-first full rehearsal,
`f2378d2723ae4203b24d398a2d20afb9`, using
`Invoke-P02Phase1ObserverFirst.ps1`. The existing completed batch is not replayed.
Its exact final execution, manifest, input archive and evidence are checked and
preserved before resetting only the owned test database from the same backup.
The current inventory is one retained ready file plus fourteen archived files.
Installation, full CHECKDB, input and output checks retain their qualified guards.
The Bot/SQL payload and input bytes are unchanged. There is one additional pinned
private helper; expected top-level evidence membership is 56 files.

After isolated preparation is committed, the wrapper releases its own seed
guard. The actual pinned StatsImportOutcomeDAL inspector opens a dedicated
snapshot connection and pauses briefly after its first preparation read. The
producer verifies that this session holds no application/data locks, then
reacquires its normal global session guard with zero wait before the observer
continues. This proves observer-first admission overlap. It does not claim a
long-duration reader or guaranteed overlap with a later import statement.
The short synchronization interval is bounded below three seconds; the actual
observer's existing three-second SQL statement timeout and zero lock wait stay
unchanged. The inspector must retain prepared/version-1 snapshot evidence and
report busy while the producer owns the guard. The full 415-row import/reports
and local immutable export then complete under the same package.

The helper requires thread termination, acknowledged physical connection close
and absence of the old SQL session. After captures finish, the producer releases
its own remaining wrapper guard and a fresh actual inspector must see completed
execution version 4. It performs no settlement, recovery action or provider
request. Any synchronization, admission, observer, cleanup, workload or evidence
failure stops the run; a completed import is never automatically retried.
All original failure evidence and other databases remain preserved.

The saved observer proof will be checked by `verify_phase1_observer_first.py`,
which also reuses the full source/output/precision/resource validator. Concurrent
procedure and stage durations must remain within the same absolute allowances
computed from the measured OFF medians (overall 18268 ms; individual stage
thresholds in `phase1-balanced-results.json`). This is one concurrency sample,
not another median comparison or replacement of the completed baseline.

Local qualification: 10 package/lifecycle tests passed, including observer-start,
finish and completion failures, cleanup ordering, preexisting installation/import
failure cases and replay refusal. Twelve proof tests passed, rejecting wrong
arrival order, retained locks/session, refused admission, mixed versions, missing
fresh outcome and exceeded reader/statement bounds. Three wrappers parse in
Windows PowerShell 5.1; the exact last-run/fifteen-file guard passes and rejects
20 changed states. The exact packaged inspector/snapshot modules also import
with network/provider access disabled and without opening SQL.

Two native checks passed using the authoritative three-table fixture in a new
disposable local K98DEV database: actual inspector-first overlap/consistent
snapshot/busy/fresh completion, and abort/physical close. Early fixture checks
exposed mismatched storage-owner test data and a duplicate test cleanup lock
release; both test-only issues were corrected. The exact leftover disposable
database from the cleanup failure was verified to have no sessions and removed;
the final fixture cleaned up successfully. No retained application database or
VM workload was used by these native tests. A failed local package-template build
also remains as an unexecuted private draft; the prepared command above is unique.

Security routing: `security-diff-scan` is skipped for this private ignored harness,
which has no Git Changes baseline, and documentation-only record additions.
The installed runtime payload is unchanged. Local scoped review covers exact
VM/database/predecessor identity, pinned source, archive custody, exclusive
receipts, thread/connection cleanup, bounded SELECT-only observation, zero-wait
producer admission and no recovery/provider path. Existing Bot/SQL Changes
reviews remain separate; this is not a new automated security scan claim.
Whole-Bot pytest, smoke imports and command registration are not repeated for
private qualification orchestration without Bot runtime changes. Architecture,
deferred-item, security-routing and explicit-path selector gates apply to these
record additions. New DMV/lock statements were exercised by the native tests;
the unchanged restore/import/report SQL remains covered by the completed batch.

Balanced timing/output acceptance is now complete. Observer-first full-size
qualification is prepared but unexecuted. Import-first concurrency and the
bounded 30-second held reader remain subsequent explicit obligations. Overall
Phase 1 acceptance, production deployment and provider-delivery acceptance
remain separate and open. The operator must run this new command once in the
retained elevated guest-session window; no repeat of the completed batch is needed.


## Observer-first accepted; writer-first rehearsal prepared — 8 November 2026

The operator completed `f2378d2723ae4203b24d398a2d20afb9` without errors.
Independent verifier `verify_phase1_observer_first.py` rehashed all 56 evidence
files and verified the whole workload, independent source-summary calculations,
all exports, exact immutable values, resource use and concurrency evidence.
Proof: `phase1-observer-first-verified-f2378d2723ae4203b24d398a2d20afb9.json`.
The original receipt SHA256 is
`b25657ae5bdf67e0615c6ee451b156fc7a027f63d0a0d7084b957c312ed4cf7f`.

Producer session 52 acquired its zero-wait global guard with result 0 while
observer session 55 was paused after its first snapshot read. The inspector
held no conflicting application/data locks, retained preparation version 1 and
prepared execution version 1, and returned busy while the producer was active.
The synchronized read interval was approximately 62 ms; the slowest recorded
observer statement was approximately 16 ms. The physical observer connection
closed and its SQL session was absent. A new actual inspector then saw completed
execution version 4 after the producer guard was released. No settlement or
recovery mutation occurred.

The full import/report procedure took 15141 ms, below the unchanged 18268 ms
allowance. Every stage passed its existing threshold, including SUMMARY_PROC at
3434 ms against 3882.4 ms. All 14 exports and immutable capture checks passed.
Minimum sampled/final free disk was 9384558592 bytes, maximum log use 2.401656
percent and peak version store 5184 KiB. The completed baseline and original
failure evidence remain preserved; production and provider delivery are untouched.

The next one-shot command is `Invoke-P02Phase1WriterFirst.ps1`, run identity
`0d1d23a054004121ab250a693b1b3d97`. This is a new isolated fixture, not a replay
of observer-first or the measured batch. It pins the completed observer-first
receipt/proof and package, copies its evidence before reset, verifies the exact
completed ownership and current input inventory, and restores only owned
database ID 7. The input inventory is one retained ready file plus fifteen
archived files. Existing CHECKDB, disk reserve, owner, source-definition,
other-database, no-network and no-provider guards remain unchanged.

The actual producer acquires its normal zero-wait session guard and commits the
test preparation. A dedicated bounded watcher then waits for a real active
`usp_S11RunStatsImport` request on that exact producer session and database.
Only after seeing that request does it invoke the actual pinned recovery
inspector. It must observe the same producer request still active after the
inspection; a lock alone, thread start, elapsed time or absent request is not
accepted as request overlap. The watcher uses three-second statements, up to
101 samples at 50 ms intervals and a five-second start gate. It performs only
bounded system-view reads, closes physically, and does not change the producer's
existing SQL timeout or admission behavior.

The inspector uses the unchanged three-second statement limit and zero lock
wait. There is no deliberate held-reader interval in this case. It must return
busy promptly, keep a valid consistent state/version snapshot, and close its
dedicated physical connection. Both observation sessions must disappear. After
the reports and immutable export finish, a fresh inspector must see completed
execution version 4. The workload still passes every existing output, source,
precision, overall/stage timing and resource gate. Expected top-level evidence
membership is 57 files; `verify_phase1_writer_first.py` checks the active-request
proof and reuses the full qualified workload verifier. No recovery action or
provider request is exercised.

Local qualification passed: 25 focused package/lifecycle/proof tests, including
start/finish/completion failures, replay refusal, wrong arrival/request identities,
missing locks or cleanup evidence, invalid state/version and exceeded budgets.
Three native SQL tests passed in a new disposable K98DEV database: real active
request observed before/after the actual inspector, refusal when no matching
request exists, and refusal when the producer guard is absent. The native fixture
procedure simulates request duration and receipt transition only; full import
overlap remains for the VM run. The fixture cleaned up successfully. All three
PowerShell wrappers parse under Windows PowerShell 5.1; the exact sixteen-file
predecessor guard passes and rejects twenty changed states.

Worker-written progress fields are declared before the thread starts so progress
serialization does not race dictionary membership changes. A local lifecycle
test encountered the previously observed Windows sharing-denied atomic file
replacement; a fresh test directory passed the full 25-test suite. No result-write
retry, SQL retry, weakened gate or guest workaround was added. The new packaged
helper and inspector import without SQL/provider access; the native-tested
snapshot/observation/inspector module bytes match the sealed runtime package.

Security routing: `security-diff-scan` is skipped for private ignored orchestration
with no Git Changes baseline and the documentation-only record additions. The
Bot/SQL implementation bytes are unchanged. Local review covers pinned ancestry,
fixed ownership, exclusive receipts, bounded request detection, real-request
identity on both sides of inspection, dedicated connection/thread cleanup and
read-only inspection without action authority. Existing Bot/SQL Changes reviews
remain separate; no new automated security scan is claimed. Full Bot pytest,
smoke imports and command registration are not repeated for unchanged runtime
implementation. Architecture, deferred, security-routing and explicit-path test
selection gates apply to the records. The new request/lock queries were exercised
natively; the unchanged full workload and restore remain covered by the accepted
rehearsals.

The five-pair timing baseline and observer-first full-size test are accepted.
Writer-first full-size acceptance remains open pending this new receipt. The
bounded 30-second held reader follows afterward. Overall Phase 1 acceptance,
production deployment and provider-delivery acceptance remain separate and open.
The command must be run once in the retained elevated guest-session window;
return stopped evidence without repeating it.


## Writer-first checker stopped after successful SQL; evidence continuation — 8 November 2026

The writer-first receipt `P02-phase1-measured-0d1d23a054004121ab250a693b1b3d97.json`
stopped with one qualification error: the post-inspection request matcher returned
no row. All 33 transferred files were rehashed; the original receipt, helper,
package and failure remain unchanged. Offline review is recorded in
`phase1-writer-stopped-review.json` (receipt SHA256
`cc4271778b3ed470a4b6476cb2d22e0013dd9274f99c4dcb35c7c742071a069a`).

The captured SQL procedure returned SUCCESS with 415 inserted rows and all 13
report stages completed. Total procedure time was 15750 ms. The main runner
persisted this completion before checking concurrency, then stopped before its
durable receipt reads and export capture. Thus no import/report replay is needed;
fresh durable completion confirmation and all 14 exports remain to collect.
The database returned to read-only/restricted/Broker-disabled state and both
server file-command settings returned to zero. Existing disk/log/version limits
were preserved. No provider or production operation occurred.

The inspector observed running execution version 2 and returned busy in about
47 ms. Both inspector and watcher acknowledged physical close. The monitor had
seen the producer request before inspection, but its later query combined
session/request identity with mutable SQL text and current database filters.
Consequently the original run lacks the required post-inspection identity proof;
writer-first acceptance remains open. Neither a successful import nor a fast
busy result is substituted for that missing evidence.

Two new disposable native reproductions demonstrate that the original matcher
loses an active request during nested dynamic SQL and cross-database execution,
while session ID, request ID, physical connection ID and request start time stay
identical. Evidence: `request-identity-native-sys.json` and
`request-identity-native-master-sys.json`. This proves a defect in the matcher;
the failed VM run did not capture the unfiltered later row, so its precise
later SQL context cannot be reconstructed or retrospectively accepted.

A separate `phase1_concurrency_writer_v2.py` now identifies the original import
as before, then binds the later observation to all four stable request fields.
Current database and status remain recorded context, not continuity conditions.
This strengthens identity against replacement requests without requiring nested
SQL to retain parent text/context. Field meanings are defined in the official
[sys.dm_exec_requests reference](https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-objects/sys-dm-exec-requests-transact-sql?view=sql-server-ver17).
The executed helper is not edited. Six native tests passed for the V2 helper:
ordinary active-request overlap, absent-request refusal, absent-guard refusal,
nested SQL, cross-database context change and the collector's two ownership
queries against authoritative table definitions. Both new native fixtures were
removed after testing. V2 is locally qualified only; no fresh VM rerun is prepared
or authorized by this record, and no concurrency acceptance is claimed.

The immediate one-shot command is `Collect-P02Phase1WriterCompleted.ps1`.
It retains the current database as READ_ONLY and verifies exact VM/session,
database ID/files/owner, all 172 installed definitions, the stopped run's 33
evidence files and original archived input. It then checks completed execution,
continuation, archive receipt, scan population and exact preparation/resource
ownership. All database statements are SELECT-only; no restore, import, report
execution, settings change, settlement or provider request is performed.

Only a new evidence folder is written. The collector captures source and summary
tables plus the 14 configured output SELECTs, then reuses the pinned actual Bot
DAL/formatting/immutable capture with only the output destination redirected to
that new folder. The original result and run folder are preserved. The retained
extracted runtime must already exist; the collector cannot recreate it. Captures
retain exact large integers, fixed row/file bounds and the unchanged 8 GiB reserve.
Before/after containment and fingerprints must agree. Twenty-five tabular
captures plus the immutable export are required; failure leaves its own receipt.

Eighteen focused collector tests passed, covering full ownership/read guards,
changed-owner/resource/data/settings cases, exclusive output creation, exact
large-number capture, immutable destination isolation, complete main success/
failure paths and cleanup. All eighteen separate-process PowerShell 5.1 handoff
cases passed, including wrong VM, changed evidence, nested inventories, changed
archive, reparse paths, process failure and incomplete captures. Three wrappers
parse. The new ownership queries executed successfully in the native fixture.

Security routing: `security-diff-scan` is skipped for private ignored qualification
artifacts with no Git Changes baseline and documentation-only additions. The
installed Bot/SQL implementation is unchanged. Local review covers immutable
failure custody, exact completed ownership, READ_ONLY enforcement, bounded
SELECTs, pinned runtime imports and new-folder-only export writes. No new
automated security scan is claimed. Full Bot pytest, smoke imports and command
registration are not repeated for this private evidence task. Architecture,
deferred, security-routing and explicit-path selector checks apply to the records.

The measured timing baseline and observer-first acceptance remain valid.
Writer-first output verification and corrected overlap qualification remain
open, followed by the 30-second held reader. Production deployment remains
separate. Do not replay the stopped writer-first command or restore this copy
before the new completion/export evidence has been inspected and preserved.


## Writer completion verified; corrected overlap rehearsal prepared — 8 November 2026

Read-only completion receipt
`P02-phase1-writer-completed-0687e4d3388e4cbda3ea65b3b6556e7d.json`
passed independent verification in `verify_phase1_writer_completed.py`.
The exclusive proof is `phase1-writer-completed-verified.json`. All 31 newly
captured files and all 33 original failure files retain their recorded hashes.
The 172 installed definitions and before/after read-only containment match.
Durable execution, continuation, archive, population and exact preparation/
resource ownership confirm the completed 415-row import and all report stages.

All 14 exports pass: 49,472 rows and 827,703 cells. Thirteen non-window outputs
match the accepted warmup exactly. Rolling summaries match the 486,842 captured
source rows using the original report cutoff (19,920 endpoint cells, 432 aggregate
cells and 117,696 combined cells checked). The actual immutable payload preserves
exact numbers, reloads byte-identically and made no provider request. The original
15.750-second procedure and all 13 stages meet the unchanged timing allowances.
Minimum free space was 9,337,135,104 bytes; peak log usage 2.4027%; peak version
store 5,184 KB. The existing 8 GiB, 70% and 512 MiB limits remain unchanged.

This accepts the completed workload and exports, not the missing concurrency
proof. The original failed receipt remains failed. The earlier ten-run timing
comparison and observer-first acceptance remain valid. The precise SQL context
at the original failed post-inspection check is still unknown.

The separate one-shot `Invoke-P02Phase1WriterFirstV2.ps1` is prepared with run ID
`c8e5a804054c40d3b2e26308318d586e`. It pins the original failed receipt, completion
receipt and independent completion proof. Before restoring only the owned test
database, it verifies and copies both the 33 original failure files and 31 new
completion files, alongside earlier evidence. The predecessor archive inventory
contains sixteen archived inputs plus the original ready input. The existing
twenty-file bound is retained. Exclusive receipt and run-folder creation prevent
replay. Exact VM/session/database, disabled services, file-command and ownership
guards remain in force.

The SQL package, Bot runtime, input and formatting implementation are unchanged.
Only the concurrency helper selection changes to the separately qualified V2
helper. It anchors the same active import request by session, request, connection
and request start time across inspection; current SQL text/database may change
during nested execution. Physical connection cleanup, busy response, fresh
completed observation and all output/timing/resource gates still must pass.

Thirty focused package/lifecycle/proof tests passed, including failure cleanup,
replacement request rejection and permitted nested database-context changes.
Three wrappers parse under Windows PowerShell 5.1; the exact seventeen-file guard
passes and twenty changed states are refused. Packaged inspector/helper imports
pass without SQL/provider access, and the native-tested observation module bytes
match the package. The unchanged V2 helper retains the earlier six native test
results, including nested SQL and cross-database request continuity. Those tests
are local qualification, not a successful full-size VM V2 result.

Security routing: `security-diff-scan` is skipped for these private ignored
qualification artifacts without a Git Changes baseline and documentation-only
record additions. Installed Bot/SQL implementation bytes are unchanged. Local
review covers exact predecessor custody, completed ownership, bounded request
identity, exclusive runs and connection cleanup. No new automated security scan
is claimed. Full Bot pytest, smoke imports and command registration are not
repeated for this harness-only step; focused tests and architecture, deferred,
security-routing and explicit-path selector gates apply.

Writer-first V2 has not run. Its full-size overlap acceptance remains open,
followed by the bounded 30-second held reader. Overall Phase 1 acceptance and
production deployment remain separate. Run only the new V2 command once in the
retained Administrator session; return any stopped receipt without repeating it.


## Writer-first V2 completed SQL; cleanup qualification stopped — 8 November 2026

Receipt `P02-phase1-measured-c8e5a804054c40d3b2e26308318d586e.json`
stopped at `Closed observation session remains`. All 34 transferred evidence
files were rehashed and the sealed package remains unchanged. The saved SQL
result reports SUCCESS, 415 inserted rows and all thirteen report stages completed
in 15.500 seconds. It stopped before durable completion reads and export capture.
The database returned to READ_ONLY/RESTRICTED_USER with Broker disabled and the
two server file-command settings zero. There was no provider/production action.

The V2 request identity correction worked in this run: session 70/request 0,
connection `20139582-EBF5-42DF-A9DD-38D0BCF8558A`, start
`2026-11-08T20:43:59.833` remained identical before and after actual inspection.
The inspector saw prepared execution version 1 and returned busy. Both observer
and monitor acknowledged physical close. The later cleanup check used only the
recorded session numbers (75 and 74), after the import/report workload completed.
It did not record which check failed or the original observer/monitor connection
UUIDs. Consequently exact original connection disappearance remains unproved;
the stopped receipt is not retrospectively accepted.

A bounded, read-only native reproduction demonstrated session-number reuse in
two connections: a closed connection's number was allocated to a distinct new
physical connection. The old session-number-only predicate returned one while
the original physical connection UUID was absent. Evidence is
`connection-identity-native-proof.json`. This establishes a flaw in the checker,
not the precise cause of the retained VM failure. Current diagnostics cannot
reconstruct missing historical connection identities.

The new private `phase1_connection_identity.py` captures the exact connection
UUID plus session/connect/login context. Its cleanup evidence distinguishes a
replacement connection from the original, and refuses an original connection
or its lingering session without a connection. It uses bounded SELECTs with no
retry, delay, termination or changed timeout. Eleven focused tests passed,
including retained original, reused number, equal-resolution timestamps,
connectionless original session, invalid identities and evidence bounds.
`connection-identity-helper-native-proof.json` independently exercised live,
closed and reused connections with the actual helper. The native replacement
even shared the original connect/login timestamps; its distinct physical UUID
correctly identified it as a replacement. All test-owned connections closed.
Only the disposable test connections were used; no database/settings changed.
The helper is not installed in the executed package. Future writer/held-reader
qualification must use exact physical identity throughout. The earlier accepted
observer-first result recorded zero matching session rows, so this new ambiguity
does not invalidate its affirmative absence evidence.

Immediate continuation is the separate one-shot
`Collect-P02Phase1WriterV2Completed.ps1`. It verifies exact retained VM/session,
READ_ONLY owned database, 172 definitions, completed execution/report/archive and
preparation/resource ownership, and all 34 original failure files. It captures
the source, summaries, fourteen output SELECTs and actual immutable payload into
a new folder. It also records bounded current metadata for the three recorded
session numbers, explicitly marked as not proving original cleanup. The import,
reports, restore, database settings and provider calls are not run. Existing
8 GiB reserve and row/file caps remain unchanged.

Twenty-five focused collector/diagnostic tests passed, including full success/
failure cleanup, exact large-number exports, unchanged ownership/isolation gates
and diagnostic bounds. Eighteen separate Windows PowerShell 5.1 process cases
passed; three wrappers parse. The new diagnostic SELECT executed successfully on
local K98DEV. No new import rehearsal is prepared in this step. The earlier
fifteen-second test is not replayed to collect already completed outputs.

Security routing: `security-diff-scan` is skipped for private ignored qualification
artifacts without a Git Changes baseline and documentation-only additions.
Installed Bot/SQL implementation bytes remain unchanged. Local review covers
SELECT-only diagnostics, exact completed ownership, immutable failure custody,
new-folder-only bounded capture and physical connection identity. No new
automated security scan is claimed. Whole Bot pytest, smoke imports and command
registration are not repeated for this private harness step. Architecture,
deferred, security-routing and explicit-path selector gates apply to the records.

The ten-run timing comparison and observer-first acceptance remain valid.
V2 durable completion/output verification, full writer-first cleanup acceptance
and the thirty-second held reader remain open. Production deployment remains
separate. Do not repeat either stopped writer command or restore this copy before
the new completed output evidence has been collected, inspected and preserved.


## Writer V2 outputs verified; exact-connection V3 prepared — 8 November 2026

Read-only receipt `P02-phase1-writer-v2-completed-4a6cc579f20f431697a5afa3658f9102.json`
passed `verify_phase1_writer_v2_completed.py`. The exclusive proof is
`phase1-writer-v2-completed-verified.json`. All 31 capture files and 34 original
failure files match their recorded hashes; 172 installed definitions and the
before/after READ_ONLY containment match. Durable execution/report/archive and
exact preparation/resource ownership confirm the 415-row completed workload.

All fourteen exports pass: 49,472 rows and 827,703 cells. Thirteen non-window
outputs match the accepted warmup exactly; the rolling output matches captured
source using the original report cutoff. Source verification covered 19,920
endpoint cells, 432 aggregates and 117,696 combined cells across the retained
486,842-row source population. Actual immutable formatting preserves exact
numbers, reloads byte-identically and made no provider call. Total procedure
time was 15.500 seconds; all thirteen stage allowances passed. Minimum free
space was 9,294,471,168 bytes, peak log usage 2.40198% and version store 5,184 KB.

Both current connection inventories were empty for the recorded session numbers
70, 75 and 74. This is current-state evidence only. The original V2 cleanup
failure remains preserved and unaccepted; missing historical connection UUIDs
cannot be reconstructed from this later observation.

The new one-shot `Invoke-P02Phase1WriterFirstV3.ps1` is prepared for run
`310ef09a154640758691c48645347d45`. It pins the V2 stopped receipt, read-only
completion receipt and independent output proof, and preserves all 34 failure
files plus 31 new completion files before resetting only the owned test database.
Earlier failure, OFF, source, timing and observer-first evidence remains preserved.
The predecessor input inventory contains seventeen archived files and the original
ready file; the existing twenty-file bound remains unchanged. New exclusive
receipt/folder ownership prevents replay. Exact VM/session/database/ownership,
disabled services, file-command and disk/log/version guards are unchanged.

The installed SQL package, Bot runtime, input, report/export logic and timing
limits are unchanged. New private qualification helper versions track the exact
physical identity of the observer, request monitor and fresh completion inspector.
They record the connection UUID plus session/connect/login context before use,
acknowledged close, and subsequent current identity rows. A different physical
connection may reuse the old session number and timestamps without being confused
with the original. An original physical connection or its lingering session
without a connection is refused. No retry, extra hold, relaxed timeout or forced
connection termination was introduced. The corrected active-request identity
check from V2 remains in place. Executed V1/V2 helpers are unchanged.

Ten native cases passed across new disposable local fixtures: ordinary request
overlap, missing request, missing guard, nested SQL, cross-database execution,
authoritative ownership queries, live original monitor/observer/fresh-inspector
refusal, and real session-number reuse during the complete helper lifecycle.
Native reuse evidence `connection-reuse-writer-v3-native.json` shows a replacement
connection on the old monitor session while the original UUID is absent; all
three physical cleanup checks and fresh completed observation pass. Nested
proofs are `request-identity-v3-native-sys.json` and
`request-identity-v3-native-master-sys.json`. A local test procedure setup collision
was corrected with CREATE OR ALTER for the test-owned procedure, then remaining
cases passed. Every native fixture cleaned up without evicting sessions.

Fifty-four focused package/lifecycle/identity/proof checks passed. These cover
unchanged implementation bytes, exact predecessor bindings, failures throughout
the complete runner, replacement-request rejection, original connection leakage,
reused session/timestamps, fresh completion and independently recomputed cleanup
evidence. All three PowerShell wrappers parse under Windows PowerShell 5.1; the
exact eighteen-file predecessor guard passes and twenty changed states are
refused. Packaged inspector/helper imports pass without SQL/provider access;
native-tested helper and installed observation module bytes match the package.

Security routing: `security-diff-scan` is skipped for private ignored qualification
artifacts without a Git Changes baseline and documentation-only record additions.
Installed Bot/SQL implementation is unchanged. Local review covers immutable
failure custody, exact completed ownership, bounded physical/request identity,
exclusive runs, connection cleanup and independent evidence verification. No new
automated security scan is claimed. Whole Bot pytest, smoke imports and command
registration are not repeated for this harness-only step; focused/native tests
and architecture, deferred, security-routing and explicit-path selector gates apply.

The V3 VM workload has not run. Writer-first full-size cleanup acceptance remains
open, followed by the bounded thirty-second held reader. The ten-run timing and
observer-first acceptance remain valid. Overall Phase 1 acceptance, provider
delivery and production deployment remain separate. Run only the new V3 command
once in the retained Administrator window; return any stopped receipt without
repeating it. Existing limits remain unchanged.


## Writer V3 missed initial request; completed SQL preserved — 8 November 2026

Receipt `P02-phase1-measured-310ef09a154640758691c48645347d45.json`
stopped at `No actual import request observed within start gate`. All 37 transferred
files and the V3 seal were checked. The saved SQL result reports SUCCESS, 415
inserted rows and all thirteen report stages completed in 15.968 seconds. All
stage/overall allowances passed. Minimum free space was 9,278,074,880 bytes,
peak log usage 2.38889% and version store 4,864 KB. READ_ONLY/RESTRICTED_USER,
Broker-disabled containment and server file-command settings were restored.
No provider or production operation ran. Durable receipt reads and local output
capture were skipped when the qualification checker raised after completed SQL.

The producer session was 62; monitor 69 acknowledged close. No observer was
created and no actual inspection occurred. This is not a cleanup-test result.
The initial matcher still required the parent procedure name in current module
text and the current database ID. Both can change before the first poll when the
call enters nested SQL. The V3 receipt lacks unfiltered request samples and poll
count on failure, so its exact transient SQL context cannot be reconstructed.

Two new native reproductions passed with a deliberately delayed first sample
after immediate nested SQL, including execution in master. The old matcher missed
the active request while `sys.dm_exec_input_buffer` retained the submitted call
identity. Evidence: `initial-request-native-sys.json` and
`initial-request-native-master-sys.json`. The API describes statements submitted
to SQL Server: https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-views/sys-dm-exec-input-buffer-transact-sql?view=sql-server-ver17.
This proves a matcher defect, not the missing precise context of the VM failure.

Further native testing exposed asynchronous logout visibility: a connection can
be closed while its session metadata briefly remains. In the bounded read-only
128-connection check, seventeen had that transient state; all cleared within
31 ms (`close-visibility-native.json`). A preliminary candidate test stopped on
that condition, so it was not treated as qualified. The new private candidate
uses exact physical identity and a bounded read-only cleanup observation: at most
one second/101 samples, temporarily reducing the verification statement timeout
to one second and restoring it afterward. It records first/final identity rows,
elapsed time and sample count; a late result or genuinely retained connection
fails. No import/report/action retry, forced termination or increased operational
timeout was introduced. Five deterministic deadline/error/timeout-restoration
tests passed.

Candidate `phase1_concurrency_writer_v5.py` uses the submitted command to identify
the initial import, binds it to the producer's captured physical connection UUID,
then retains the existing stable request identity check across actual inspection.
Initial producer database identity remains recorded even when nested execution
changes current database. Poll count is retained on failure. It uses the new
private observer cleanup helper; previously executed helpers are unchanged.
Twelve native cases passed in one new disposable local fixture: immediate nested
SQL in either database, ordinary overlap, absent request/guard, later nested and
cross-database transitions, three deliberately unclosed connection roles, real
session reuse and the authoritative ownership-query case. The fixture cleaned
up without eviction. These are local candidate tests, not a new full VM pass.

The immediate one-shot is `Collect-P02Phase1WriterV3Completed.ps1`. Its collector
is byte-identical to the previously exercised read-only completion collector,
with a new contract, exact V3 preparation/input ownership, 37 preserved failure
files and an exclusive new evidence directory. It verifies 172 definitions,
completed execution/report/archive and exact preparation/resource ownership, then
captures source, summaries, fourteen configured output SELECTs and the actual
immutable payload. The retained extracted runtime must already exist. It runs
no import, report, restore, database setting or provider action. Existing 8 GiB
reserve and all capture bounds remain unchanged. Eighteen focused tests and
eighteen separate Windows PowerShell 5.1 process cases passed; three wrappers parse.

Before any next full workload package: integrate and test the complete candidate
control flow; make completed output capture independent of a safely terminated
qualification failure while retaining a failed overall result; and reconcile
the remaining input inventory against the unchanged cap. After V3 there are
eighteen archived inputs plus the original ready file (nineteen total); two more
ordinary fresh imports would exceed the twenty-file bound. Do not silently
raise that limit, delete retained evidence or reduce acceptance coverage. The
remaining writer-first and thirty-second-reader sequence must be explicitly
designed to fit the existing bounds before another full VM command is prepared.

Security routing: `security-diff-scan` is skipped for private ignored qualification
artifacts without a Git Changes baseline and documentation-only record additions.
Installed Bot/SQL implementation is unchanged. Local review covers immutable
failure custody, read-only completion, exact request/connection identity and
bounded logout observation. No new automated security scan is claimed. Whole Bot
pytest, smoke imports and command registration are not repeated for this private
harness task; focused/native tests and architecture, deferred, security-routing
and explicit-path selector checks apply.

The accepted timing baseline and observer-first test remain valid. V3 completed
output verification, full writer-first qualification and the thirty-second held
reader remain open. No new workload wrapper is prepared by this record. Keep
production deployment separate and do not replay the stopped V3 command.


## V3 outputs verified; remaining concurrency checks combined within limits — 8 November 2026

Receipt `P02-phase1-writer-v3-completed-44c56d0ae1b247539b2ae1fdfa51a480.json`
passed `verify_phase1_writer_v3_completed.py`. Its exclusive proof is
`phase1-writer-v3-completed-verified.json`. All 31 capture files and 37 original
failure files retain their recorded hashes. Exact preparation/resource ownership,
completed execution/report/archive, 172 definitions and READ_ONLY containment
passed. All fourteen exports pass (49,472 rows / 827,703 cells): thirteen match
the warmup exactly and the rolling summary matches captured source at the original
report cutoff. The 486,842-row source matches the retained source population;
19,920 endpoint cells, 432 aggregates and 117,696 combined cells were checked.
The actual immutable payload preserves exact numbers and reloads byte-identically
without a provider call. The 15.968-second procedure and every stage allowance
passed. Minimum free space including capture was 9,252,134,912 bytes, peak log
usage 2.38889% and version store 4,864 KB. The original V3 concurrency failure
remains failed; this accepts its completed workload/outputs only.

There is one fresh input slot left under the unchanged twenty-file bound. The
remaining short writer-first inspector and thirty-second snapshot reader now
share one fresh import, each retaining separate evidence and acceptance checks.
This adds simultaneous reader pressure; it does not isolate each reader's cost.
The accepted five-pair timing baseline remains the comparison, and the combined
run must meet the same overall/per-stage and resource ceilings. No retained input
is deleted or moved, no acceptance condition is dropped, and no cap is raised.

New one-shot `Invoke-P02Phase1CombinedConcurrency.ps1` owns run
`92190c2616a04481aca1abaaaf862eb4`. It pins the V3 stopped receipt, completion
receipt and independent proof, verifies/copies the 37 failure files and 31 output
capture files, and preserves earlier evidence before restoring only the owned
test database. Exact nineteen-file predecessor inventory (eighteen archived plus
one original ready) becomes twenty after the new import. Exclusive receipt and
run-folder creation prevent replay. SQL package, Bot runtime, input, reports,
export formatting, database ownership/isolation and all existing limits are
unchanged; only private qualification orchestration differs.

The real short inspector uses the locally qualified submitted-command matcher
bound to the exact producer connection, followed by stable request identity
before/after inspection. It retains the three-second statement budget, zero-lock
wait, conservative busy result, exact physical cleanup and fresh completed read.
The synthetic held reader sets SNAPSHOT before starting its transaction, captures
the old source population and proves no retained application/data locks. Once
the producer finishes, it reads the same old population inside that transaction,
then remains held until the scheduled thirty seconds, rolls back and closes.
A fresh producer read must see the new population. Each source statement is
bounded to three seconds; the held interval has only that existing statement/
cleanup allowance. Physical logout verification remains separately bounded to
one second with recorded samples and restored connection timeout.

The combined local native fixture passed all three cases: a full thirty-second
hold with the real short inspector and committed source change, early abort,
and incorrect baseline refusal. The successful hold measured 30.016 seconds,
retained no conflicting locks, preserved the old snapshot after commit and
returned the new population on a fresh read. Both readers rolled back/closed as
appropriate. The fixture used a minimal source control table and test-only
duration/receipt procedure; it is correctness/cleanup evidence, not full-size
performance qualification. An initial local transaction-order error was corrected
by setting SNAPSHOT before disabling autocommit, then all three cases passed.
The twelve previously qualified writer/request/physical-cleanup native cases
remain applicable to the byte-identical helper. Every fixture cleaned up.

The full workload runner now starts observers immediately before the actual
import call. If a qualification check fails after SQL completion, it records the
failure, shuts down both workers and independently verifies exact connection
cleanup before reading durable completion and capturing existing outputs. Unknown
or still-open connections stop this continuation. If cleanup is proven, the
fourteen exports and immutable payload are captured, while the overall result
still finishes StoppedForReview. A failed check can never become a passing run.
No import/report/action is retried. This avoids another separate collector just
because a safely terminated checker failed after completed SQL.

Ninety-one focused checks passed: full runner success/failure and no-replay paths,
safe/unsafe post-failure output capture, exact request/physical identities,
cleanup deadlines, held snapshot continuity/freshness, overlap ordering, all
partial-result refusals and immutable package/predecessor bindings. Three Windows
PowerShell 5.1 wrappers parse; the exact nineteen-file guard passes and twenty
changed states are refused. The packaged helpers/actual inspector import without
SQL/provider access and match native-tested implementation bytes.

`verify_phase1_combined.py` independently checks both reader proofs, recomputes
physical cleanup from captured identities, requires all timing/resource/output
gates and expects the complete 66-file result inventory. It has been tested with
native-shaped and deliberately corrupted evidence. No VM result for this new
package exists yet; none of its remaining acceptance gates is marked passed.

Security routing: `security-diff-scan` is skipped for private ignored qualification
artifacts without a Git Changes baseline and documentation-only record additions.
Installed Bot/SQL implementation is unchanged. Local review covers exact custody,
one-shot ownership, bounded threads/transactions/reads, safe post-failure capture,
unchanged limits and independent proofs. No new automated security scan is
claimed. Whole Bot pytest, smoke imports and command registration are not repeated
for this harness-only step; focused/native tests and architecture, deferred,
security-routing and explicit-path selector gates apply.

The timing baseline and observer-first acceptance remain valid. Both remaining
reader conditions must pass the combined full-size rehearsal and independent
review before concurrency is accepted. Production deployment, provider delivery
and overall release acceptance remain separate. Run the new combined command
once in the retained Administrator window and return a stopped receipt without
repeating it. Existing limits remain unchanged.

Timing interpretation for the combined rehearsal: its retained `procedureSeconds` starts before observer setup and ends when the SQL call returns, so the unchanged producer timing ceiling conservatively includes setup overhead. The remaining wait for the scheduled thirty-second reader is after that timer. This sample must not be described as a pure SQL-duration improvement or replace the accepted balanced timing medians.


## Shared latest names approved and implemented locally — 8 November 2026

The operator approved one shared display-name source, explicitly selected the
latest known name across historical and current reports, and declined a separate
name-performance benchmark. Correctness, resource limits and remaining concurrency
qualification remain required. Production deployment remains separate.

The combined run `92190c2616a04481aca1abaaaf862eb4` is NOT an overall pass.
`phase1-combined-partial-verified.json` independently verifies the completed
415-row import, reports, preserved captures and actual short writer-first observer,
including original connection cleanup and a fresh completed-state read. All 66
files retain their recorded hashes. Thirteen exports pass unchanged/source-oracle
checks; monthly power has exactly one historical name-label difference and no
numeric-cell difference. Outputs remain unaccepted until the name correction is
qualified. The original failed receipt and exports are unchanged.

The 30-second synthetic raw-history reader failed after 12.656 seconds with SQL
3961. The captured SQL messages specifically record index
`IX_KSD4_Gov_ScanOrder` at 35.06% fragmentation being rebuilt. A local native control
reproduced the raw-snapshot failure across REBUILD/CREATE INDEX; REORGANIZE and
UPDATE STATISTICS controls did not reproduce it. The real observer reads
ExportPreparation, StatsImportExecution and ExportResource, not raw scan history.
A separate local 30-second metadata test with concurrent state writes and raw-index
REBUILD passed, including stable old versions, fresh new versions, no conflicting
data/application locks and exact physical connection cleanup. This is controlled
local qualification, not a full-size VM import/30-second concurrency pass.

### Shared name implementation

`dbo.v_ReportGovernorNames` defines one newest nonempty name per GovernorID,
ordered by ScanOrder with a binary spelling tie-break. Null/blank observations
do not erase a known name. Zero and the three aggregate identities are excluded.
`dbo.usp_ApplyReportGovernorNames` applies that list after aggregation to a fixed
allowlist of 16 table targets plus the rally label. It changes display labels
only; it never inserts/deletes report rows or updates numerical fields. Unknown
IDs retain their existing label. Both report orchestrators materialize one list
for their batch; standalone callers resolve the same canonical source.

Current monthly rows retain their existing grouping and cardinality even where
different historical aliases now display the same latest name. Alias history in
ALL_GOVS_NAMES remains intentionally historical; alliances and raw scans are not
rewritten. Immutable already-captured provider payloads are not regenerated.

The 26-object patch covers the summary parent and nine metric entries, current
and legacy report orchestrators, governor information, inactive governors,
dashboard creators, stats upload, both rally producers, the KVK output producer,
account/target report views and the target-view regeneration path. Rally labels
are resolved only from the exact existing `name (GovernorID)` suffix, never by
matching a player name. Account records and archived target data stay unchanged;
their report views overlay the shared label. Target rollover preserves its
selected table, columns and order while retaining this same lookup.

Reviewed before/after source images are in
`qualification/p02_report_names/reviewed_sources.json`. The earlier numeric
qualification now reads `qualification/p02_phase1/numeric_modules.json`, whose
every body still matches the original numeric manifest. This explicitly keeps
that earlier stage reproducible; it does not include or install the new name
package. Original name migration and rollback images are unchanged. The new name
package must follow the numeric stage. Its final VM apply/rollback wrapper is
pending exact installed-definition and target-binding evidence; no production
installer or deployment is claimed ready.

### Validation and next evidence

Native local tests passed: 26 name-selection/publication/permission/rollback
cases; 11 actual summary-entry/shared-list integration cases; 28 unchanged numeric
regressions; two real target/account-view tests (including the actual rollover
view-generation fragment); and one 30-second metadata snapshot/DDL test. All
fixture databases were uniquely owned and cleaned up. These tests compare rows,
every non-name numerical cell and exact values above 2^53. No name-speed comparison
was run. The prior accepted five OFF/ON timing pairs are not replayed.

`Collect-P02Phase1SharedNamesEvidence.ps1` is prepared for the retained elevated
session. It pins the latest combined receipt and all 66 evidence files, verifies
the exact owned database/read-only containment and 172 installed module hashes,
then reads 24 existing affected definitions, target-view dependencies, the source
names, proposed canonical list and 14 current exports into a new evidence folder.
It installs nothing and performs no restore/import/report/provider/setting action.
Nineteen Python guard/capture tests and 18 separate-process PowerShell 5.1 handoff
cases passed. Its receipt is still pending. A currently selected target table must
be preserved; the repository's bootstrap view pointing to target table 15 is not
authority to redirect a live retained view that selects another KVK.

The twenty-input cap is now reached (19 archived and the original retained ready
file). No new import, deletion of evidence, cap increase or replay is prepared.
Full-size name/output qualification and the remaining VM long-reader acceptance
remain open. The raw-history long-reader failure must not be relabelled a pass;
any revised test must explicitly state its actual observer-metadata scope.

Security routing: the new SQL source and its dynamic target-view projection need
a fresh SQL Changes review against the current uncommitted patch; existing SQL
review results do not cover these additions. No Codebase/Deep scan is authorized.
Bot runtime is unchanged by this slice. Private read-only collector safeguards
are manually reviewed and exercised; ignored artifacts are not represented as a
Git-backed Changes scan. Production publication/deployment remains separate.

### Connected maintenance work

The source-index rebuild links this evidence to existing P02 D3 maintenance
ownership. Moving/reworking maintenance remains that planned package; it is not
silently included in the name change. The real observer metadata path and raw
source snapshot path have different DDL exposure. Original limit and production
boundaries are unchanged.


## Shared names evidence and rollback comparison — 9 November 2026

The approved policy remains latest known nonempty display name for all current
and historical reports, with historical alias records kept separately. No name
speed benchmark is required or performed. Production deployment remains separate.

The retained read-only evidence receipt
`P02-phase1-shared-names-evidence-b0fa2623ba354cc3b793d53fafc0d51b.json`
passed independent offline verification: all 21 transferred file hashes, 486,842
source rows, the deterministic 2,449-player name list, 24 affected installed SQL
definitions, all 14 current outputs and unchanged before/after containment.
The current target view is bound to `dbo.EXCEL_EXPORT_KVK_TARGETS_16`.
The local bootstrap now creates a view only when absent; reapplying it cannot
redirect an existing rollover view. The native rollover regression passed.

The completed SQL Changes scan `470eb6e0-3172-487c-9e0e-fe423ba54430` covers the
72 reviewed source/package files at snapshot
`29299ec68bdec6a1661e248399947c45214b2d73a725bf311c33d03ac42a3593`, based on
`dad628c7a353cc6391868d097a6ae5fb7a8d9e84`. Finalization and sealed readback passed
on 9 November; no security candidates were reported. A focused post-review delta
check covered the bootstrap guard, account-view whitespace, matching source
reference, test-only historical reconstruction, and isolated comparison wrapper.
It found no security candidates or blocking correctness issue. The stale
SELECT-only comparison header was corrected before handoff; the unexecuted
package was resealed. This supplemental static check is not a new full scan or
VM acceptance. Runtime grants, historical permission manifests and runtime
allowlists remain unchanged; the test authenticates each historical source stage.

Validation: the earlier 100 SQL tests remain the complete local regression
baseline. After the final bootstrap correction, both native view tests passed.
The exact four-definition comparison package and name publication passed a new
disposable native SQL rollback test. All 33 Bot historical compatibility tests
passed, including source-prefix and modified-reference rejection. Eighteen
comparison/control/cleanup tests and 20 separate-process PowerShell 5.1 handoff
cases passed. Python syntax, source seals and SQL whitespace checks passed.
Existing architecture, deferred and security-routing gates remain passed; the
test selector was rerun for the changed Bot test. Its broad pytest/smoke/command
recommendations are skipped for this slice because Bot runtime and registration
code are unchanged; the focused 33-case source/permission regression directly
exercises the test-only change. SQL and wrapper behavior has dedicated native,
negative, resource/containment and rollback coverage.

`Invoke-P02Phase1SharedNamesComparison.ps1` is prepared for one execution in the
retained elevated guest session. It verifies the exact completed read-only
baseline and preserved evidence, captures the existing 14 outputs, temporarily
enables writes only for the owned database, installs four name-publication
definitions inside a transaction, calls the static names-only CompletedReports
helper, and compares all outputs to the independently verified name list. Every
non-name cell and row multiplicity must remain unchanged; alias history is exact.
It then rolls back, compares every restored output exactly, verifies all 172
original module hashes, and verifies restored read-only containment. KVK16
projection order and selected table are preserved. There is no restore, new
import, report recalculation, provider call or production action. All other
candidate caller wiring remains qualified by the native local tests; this
four-object comparison does not claim a full VM install of all 26 changed objects.

The new VM comparison receipt is pending. The twenty-input cap remains reached;
no further fresh input or cap increase is prepared. The remaining full-size VM
long-reader qualification is still open. Actual short observer-first and
writer-first paths are separately accepted; local 30-second metadata-snapshot
testing passed, while the synthetic raw-history reader failed across index
REBUILD with SQL 3961. Preserve that distinction and P02 D3 maintenance ownership.
All existing resource limits and production separation remain unchanged.


## 9 November 2026 - verified shared names and one final integrated rehearsal

The retained shared-name rollback comparison is independently verified:
14 exports, 49,472 rows, 827,703 cells; exactly 4,717 display-name cells changed,
with zero numerical changes and unchanged row multiplicity. Historical aliases
are preserved. All 172 original SQL definitions and original output rows were
restored exactly, with read-only containment verified. KVK16 remains the target.
The private proof is `phase1-shared-names-comparison-verified.json`; receipt
`P02-phase1-shared-names-comparison-b5c75ea78ed74ab9b9a7c7904b503b31.json`
has SHA256 `333777c80134d772cee632c073201ed5a123182aaf3c02fce66bdb93ba87209c`.

The operator explicitly approved "Allow 21 files for one rehearsal". This changes
only the retained-input cap from 20 to 21 for the one final integrated run
`142c9a6cc57b4b728c3e06056b849d71`. The additional copy is the same 415-row,
78,035-byte input. All old inputs and evidence remain preserved. Four CPUs,
8 GiB VM memory, 8 GiB disk reserve, log below 70%, version store below 512 MiB,
producer and per-stage timing limits, reader statement/hold/cleanup budgets and
production separation are unchanged. No name-speed benchmark is required.

`Invoke-P02Phase1FinalIntegrated.ps1` is prepared to preserve the completed
comparison and previous failures, restore only the owned test database, install
the unchanged 139-column/11-procedure numerical package followed by the complete
26-object shared-name package, then run one fresh import and its reports. The
short actual recovery inspector and a 30-second reader of the same ownership
and status tables run around that import. All 14 raw exports and the actual Bot
immutable local payload are retained for independent verification. The input
inventory must be exactly 20 before reset and exactly 21 after completion.

Local qualification: 47 installer, generated-runner and independent-verifier
checks passed; three native reader lifecycle tests passed, including a full
30-second hold while the raw source index was rebuilt; the exact 26 SQL bodies
compiled in disposable native databases and rollback restored their original
module inventory. Three PowerShell 5.1 wrappers parsed, valid pre/post inventories
passed, and 27 altered states/inventories were refused. The source-summary oracle
was exercised against retained source scans with only the approved name overlay;
numerical computations and original stage times were retained. Synthetic test
fixtures produce no VM acceptance proof. Actual pinned Bot imports were checked.

Focused supplemental static review found no concrete defects in the private
installer/reader/wrappers, including the final 21-file inventory and bounded fresh
metadata read. This is supplemental tooling review, not a new full Git scan.
The completed SQL Changes scan and earlier full regression evidence remain
applicable to unchanged checked-in runtime sources. Production installation,
promotion and deployment remain separate and are not authorized by this run.

The complete 26-object fresh import and simultaneous held-reader VM receipt is
still pending. The earlier raw-history snapshot failure across index REBUILD
(SQL 3961) remains preserved; metadata-reader acceptance cannot establish that
arbitrary raw-history readers survive DDL. P02 D3 retains maintenance ownership.
Do not mark Phase 1 or all P02 complete until the integrated evidence is reviewed.

Current handoff checks: architecture boundaries, deferred-item validation,
security routing and Bot/SQL whitespace checks passed. The test selector was
run for the documentation delta. Its general smoke-import and command-registration
recommendations are skipped because neither Bot runtime nor command registration
changed in this slice; the exact packaged inspector/import path was checked
separately. The private tooling has its own focused native and failure tests.

Independent review of the new offline acceptance checker identified a parent
summary identity-multiplicity gap. It is corrected: the parent output must contain
exactly the verified child-summary player IDs, once each. A duplicate-player /
missing-player fault preserving total row count is now rejected. The focused
verifier suite passed 17 cases; follow-up review confirmed this specific fix.
No VM acceptance is claimed and the execution package was unchanged.


## 9 November 2026 - final installation handoff correction and same-input continuation

The final integrated attempt `142c9a6cc57b4b728c3e06056b849d71` stopped during
installation, before producer admission or import. All 45 retained evidence files
were authenticated. The 139-column/11-procedure numerical installation committed;
the shared-name installation had not begun. Read-only containment was restored.
The failed command and its package remain immutable and must not be rerun.

Root cause: the new shared-name installer treated the numerical install receipt's
submitted-body hashes as stored-definition hashes. SQL Server stores these eleven
ALTER PROCEDURE bodies with an initial CREATE keyword. The distinction had been
proven earlier in the source collector but was not carried into this new installer
handoff. The old native compilation test did not exercise this sequential handoff,
and the old installer mock used an empty numerical predecessor mapping. This was
a qualification-tooling error, not an observed import or report-data failure.

The separate v2 installer now authenticates submitted SQL evidence independently,
compares stored numerical definitions with only their leading DDL verb/spacing
normalized, and preserves exact body and unrelated-module checks. A native local
regression executes all eleven numerical definitions, reproduces SQL Server's
stored form, verifies the corrected handoff, rejects body drift, then compiles all
26 shared-name definitions and verifies rollback. It passed.

Read-only receipt `P02-phase1-final-install-state-255033b839394311b5ffda180949a0fc.json`
passed independent verification: 172 exact expected definitions, 139 converted
columns, unchanged history 1,244 / 486,427 rows, no matching execution/preparation/
resource ownership rows, and exactly 21 retained inputs. The same pending input
`stats_0cc4457d9042433ab82c81caab004447.ready.csv` remains ready. No extra input is
needed and the one-rehearsal 21-file allowance is not increased.

`Continue-P02Phase1FinalIntegrated.ps1`, attempt
`7aea1e23b649448ea68df59b714445cb`, is prepared to recheck this exact state, preserve
the original failure, and use a separate one-shot evidence directory for the same
approved pending workload. It skips restore and numeric reinstallation, applies
the corrected shared-name stage, then runs the pending import/report/export and
metadata concurrency checks. It does not publish another input. Original logical
run, preparation, owner, account, filename and digest remain unchanged.

Continuation qualification: 57 focused Python checks passed (installer 16,
runner/containment 14, independent output verifier 17, resume prerequisites 10),
plus the native sequential handoff/26-module rollback test. PowerShell 5.1 checks
parsed both collector and continuation wrappers, exercised the full read-only
collector with inert boundaries, rejected 28 changed installation states and nine
changed pending-input inventories. The 21-file final inventory check is unchanged.
The earlier 30-second reader native proof remains applicable: reader, concurrency,
Bot, SQL bodies and data/export limits are byte-identical to the sealed package.

Supplemental read-only review found no concrete defects in the continuation host,
guest, runner delta, v2 installer, resume contract or hash bindings. Checked-in Bot
and SQL runtime sources are unchanged, so the completed Changes reviews remain
applicable; private continuation tooling is covered by this explicit supplemental
review and targeted tests, not represented as a new whole-repository scan.

The continuation VM receipt and its independent acceptance remain pending.
Production deployment remains separate. No Phase 1/P02 completion is claimed.


## 9 November 2026 - Phase 1 isolated qualification accepted

The completed continuation `7aea1e23b649448ea68df59b714445cb` passed independent
verification. Receipt SHA256:
`c7f9ae17a8fc707b3241a8a809fb7a03026e203279008504137250b8563a5247`.
The original stopped attempt, its overstrict export comparison, all inputs and
all prior evidence remain preserved. No restore, numeric reinstall, second import
or additional ready input was used by the continuation.

Acceptance covers the coordinated endpoint SQL rewrite, 139 numeric columns,
all 26 shared-name SQL objects, latest names for 2,449 players, and all 14 raw and
actual-Bot immutable local exports. The current exports contain 49,468 rows and
827,683 cells. Source-based checks verified 19,920 endpoint cells, 432 aggregate
cells and 117,696 combined-summary cells, plus exact player membership and row
multiplicity. Historical alias output remains exact; KVK16 binding is preserved.
The actual immutable payload reload is byte-identical and no provider was called.

Two differences from the previous-day reference were explicitly adjudicated,
not ignored or relabelled as name changes:

- All 353 changed KVK ordinal ranks belong to zero-DKP players. The unchanged SQL
  uses ROW_NUMBER ordered only by DKP_SCORE, so this tie has no defined internal
  order. Both reports contain each of the same 415 players once, ranks 1-415 once,
  and descending scores. Every non-rank cell is unchanged apart from the approved
  latest display names. Positive-score ranks did not change.
- Four inactive rows dated 1 August 2026 05:59 aged past the existing 100-day lower
  cutoff. The actual procedure's saved local start/end log is 9 November 2026
  09:21:28.060 / 09:21:28.077, with server offset zero. The independent oracle
  recalculated membership and latest power/name/date from all 486,842 retained
  source rows, including SQL datetime rounding bounds. It requires exactly 571
  eligible rows, rejects ambiguous cutoff boundaries, and verifies every retained
  value. The four removals account exactly for the 4-row / 20-cell export decrease.

The original exact-reference verifier and its stop are retained. The separate
`verify_phase1_final_continuation_v2.py` plus `verify_phase1_report_semantics.py`
adds only these source-proven existing rank/date semantics. Seventeen fault tests
passed: duplicate/missing players, invalid/duplicate/fractional ranks, wrong
scores/statistics, wrong inactive names/power/dates/status, unexpected identities
and ambiguous date boundaries are rejected. Supplemental independent review found
no concrete defect in this adjudication. No workload package, report SQL or
acceptance resource/timing limit was changed to obtain the pass.

Concurrency qualification passed with the actual short recovery inspection during
an active writer and the same three-table recovery-metadata snapshot held for
30.031 seconds. The held transaction retained the prepared view after commit;
a fresh read saw completed version 4. No conflicting data/application locks were
held, and all original reader/monitor connection identities were verified closed
within the existing one-second bound. The earlier observer-first qualification
and five balanced OFF/ON pairs remain preserved and applicable. The 13.375-second
producer measurement, including observer setup, and all report stages passed the
unchanged timing ceilings; this single run is not a name-speed benchmark.

Resource limits passed: minimum free space 9,146,789,888 bytes (above 8 GiB),
maximum log use 2.4244%, maximum version store 5,184 KiB (below 512 MiB).
Exactly 21 inputs remain: the original ready input and 20 archives. The pending
input was imported once and archived. The owned test database returned to
READ_ONLY / RESTRICTED_USER, Broker/RCSI remain off, snapshot remains on, and
file-command settings returned to disabled. Other databases and production were
not targeted. No further rehearsal run is required for this Phase 1 scope.

Canonical private acceptance proof:
`phase1-final-continuation-adjudicated-7aea1e23b649448ea68df59b714445cb.json`.
Clock/log corroboration:
`P02-phase1-final-report-clock-eca6313027024a7aa1c9975f6e91bbcc.json`.

This closes Phase 1's isolated SQL/name/numeric/export and selected recovery-reader
qualification. It does not close all P02, authorize production deployment, prove
provider delivery, resolve the six production incident records, or qualify
arbitrary raw-history snapshot readers across index DDL. The original SQL 3961
raw-history failure remains owned by the P02 D3 maintenance work.

Next delivery gate: final coordinated Bot/SQL source and release-contract review,
versioned production installation/source-pin/signing/updater integration, fresh
installed binding/host custody and retained-work readiness evidence, and a
concrete rollout/rollback plan. Production action remains separately approved.
D2-D4 remaining observer/connection/maintenance/legacy scope, whole-programme D5
fault/restart qualification, and D6/D7 release/provider/exercised acceptance remain
open under the integrated plan. Do not substitute this isolated pass for them.

### Deferred Optimisation
- Area: SQL `dbo.sp_ExcelOutput_ByKVK`, `KVK_RANK` projection and downstream `STATS_FOR_UPLOAD` exports.
- Type: consistency
- Description: Existing ROW_NUMBER ordering uses only DKP_SCORE. Equal-score players have valid but unstable ordinal positions across recalculations; the qualified run permuted all 353 zero-score ranks without any score or other statistic change. This is an existing tie-policy limitation, not incorrect metric data or a new name regression.
- Suggested Fix: At the release/output-consistency review, explicitly decide and document a stable secondary key such as GovernorID ascending, or retain the current unspecified-tie policy. If changed, test repeated recalculation, report/export agreement and preservation of every score and player; do not silently change ordinal policy while closing the current name/numeric tests.
- Impact: low
- Risk: low
- Dependencies: SQL report owner decision on equal-score ordinal policy; separate from Phase 1's preserved-ranking contract and P02 D3 DDL ownership.
