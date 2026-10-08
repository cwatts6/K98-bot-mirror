# KVK Source Migration — Phase 1 audit

Date: 2026-09-09. Status: audit delivered for operator review; architecture and implementation unapproved.

## 1. Conclusion and boundary

The samples support separate player-snapshot and authoritative aggregate ingestion. They do **not** fit the current whole-KVK importer. Its only accepted sheet is `Full Data`; it takes upload time, creates a growing first-seen baseline, permits missing-endpoint fallback, and derives kingdom/camp totals from players. Downstream readers also recalculate aggregate DKP and add configured windows. These are evidenced incompatibilities with D05–D11, not reasons to relax those requirements.

Recommend separate source-specific raw/staging and versioned publication, with shared reporting services where their metric/availability contracts can be extended honestly. Do not write new source values directly into the current output tables. The [design comparison and next slice](phase_1_decisions_and_next_slice.md) is a recommendation, not approval.

The four originals and earlier numeric diagnostics were rechecked. B0 is absent and is **not P1**. Master-eligible population, eligible gains/ranks, current KVK-16 configuration and deployed SQL parity remain unverified. The aggregate report's actual period remains a narrowly scoped source question after inspecting current window logic. All independent local inspection and offline source checks proceeded without these inputs.

No application, importer, processing procedure, SQL mutation, external export, Discord action, restart, Git synchronization or deployment was executed. Temporary analysis used the system temporary directory. No player rows, names, IDs or original workbooks were added to these deliverables.

## 2. Repository and evidence grounding

| Repository | Observed branch and HEAD | Remotes | Initial worktree |
|---|---|---|---|
| `C:\discord_file_downloader` | `main`, `1a3a5de3d2e9f349c276725f6271ef19a7517c4f` | origin `cwatts6/K98-bot-mirror`; production `cwatts6/K98-bot` | Existing modified and untracked documentation, including programme/register and task index. No initial runtime diff. |
| `C:\K98-bot-SQL-Server` | `main`, `fc0e94ebd2e0a98286069c8a8b71365dd5178657` | origin `cwatts6/K98-bot-SQL-Server` | Clean. |

These are local observations. No fetch/remote-ref parity check was performed; “synced” was not converted into an unsupported remote or deployment claim. Initial modified/untracked file hashes were retained for preservation checks. The final [validation log](phase_1_validation_log.md) lists initial changes and task-authored paths separately.

`README-DEV.md` records earlier operator evidence for production `1e72949dc69f1a1e5a529dbf1951039fe0ba74a6`, a clean production tree and restart. The diagnostics runbook records natural ACTIVE KVK-16 delivery and empty fighting blocks in earlier observations. Those records support the reported symptom/history; this audit did not inspect the running process or authenticate its present version. A sent receipt does not establish correct source content.

SQL `sql_schema/README.md` distinguishes generated snapshots from deployable `migrations/`. This audit treats checked-in definitions as the local contract, not proof of live objects. No named, already-authorized read-only DB connection was supplied or established. Credentials and live caches were not searched to construct one. Current SQL configuration, agent jobs, permissions, external readers and deployed module hashes remain deployed-state gaps.

Canonical template: `docs/templates/Codex Task Pack Template.md`. The Phase-1 pack preserves its scope/architecture/implementation gates and eleven-part delivery shape, omits deferred-origin section 6 as inapplicable, and explicitly authorizes these audit documents. Historical assessment instructions are evidence only; the current user request and D01–D13 govern the work.

## 3. Original-byte reproduction

Private root: `%LOCALAPPDATA%\K98\kvk-source-migration\evidence`. `README_EVIDENCE.md` was read before the historical assessment. Workbooks were opened with openpyxl read-only, formula-preserving reads and external links disabled; no formulas were evaluated and files were never saved. SHA-256 and sizes match the manifest for all four originals.

| Role | SHA-256 | Bytes |
|---|---|---:|
| P1 | `512e0268ab5ca524b1bc1a94971a27299e67bb5a5e2cdc1da9b61f3394cfdfe1` | 1530165 |
| P2 | `eae10b1cf83ee00332857333fbb26bda8e0a43078c4c3db8bc191adbbe8ac974` | 1536535 |
| A1 | `563e7a67948dbcde211764e30645a1188d06d7e39335e5793335a23f6ea9d2e3` | 13345 |
| L1 | `8426056320609bd0083be445441011c6d251512b1da924c997b61ab4c13f847b` | 4206666 |

Methods: count keyed records, compare Governor-ID sets, subtract numeric endpoints over the intersection, and group diagnostic deltas by source kingdom. Expand abbreviated text with Decimal; the last displayed unit is `10^(decimal exponent) * suffix multiplier`. Compare six metrics per kingdom against that unit; do not interpret it as a production tolerance. Normalize camp names by case/whitespace for diagnostic joins. The first case-sensitive companion check was corrected before adopting results; no source content changed.

| Claim | Status and reproduced finding | Exact source/method |
|---|---|---|
| E01 | verified: P1 5729 keyed unique governors, P2 5720; identical 36 headers | P1 `Scan!A1:AJ5730`; P2 `Scan!A1:AJ5721`; keyed count and set uniqueness |
| E02 | verified: 36 kingdoms each; 5682 matched, 47 start-only, 38 end-only; zero matched kingdom changes | P1/P2 Governor ID and Kingdom columns; set operations |
| E03 | verified: 1198 175/176 rows, 175 matched, 0/1 unmatched | P1 `Scan!A399:AJ573`; P2 `Scan!A399:AJ574`; source-filtered diagnostic only |
| E04 | verified: 4 camps, 36 unique kingdoms | A1 `Camp Stats!A1:I5`, keyed `Kingdom Stats!A1:J37` |
| E05 | verified: nine standalone numbers after blank row 38 | A1 `Kingdom Stats!E39:E47`; whole used range is `A1:J47`, not a 46-record table |
| E06 | verified: all 288 kingdom metric cells are strings; suffixes are stored text | A1 `Kingdom Stats!C2:J37`; Decimal expansion preserves displayed precision, not hidden digits |
| E07 | verified: `Dead`, `T4+T5DEAD`, `DKP`; no separate tier-death inputs | A1 both header rows; authoritative DKP accepted by requirement |
| E08 | verified distinct fields: player Total Kill Points versus aggregate KP (T4+T5) | P1/P2 `Scan!M`; A1 kingdom `E`, camp `D` |
| E09 | verified diagnostic 1198: T4 51499097, T5 213208491, tier KP 4779160790, total KP 4780647527; difference 1486737 | P1/P2 `Scan!K:M`, end minus start over 175 common IDs; 10/20 arithmetic is not KVK-16 weight evidence |
| E10 | verified diagnostic 1198: deaths 25592768; healed 226713307; current Acclaim 74140436 | P1/P2 `Scan!O:P,AC`; exact integer subtraction |
| E11 | verified diagnostic: 216/216 comparisons within one displayed unit | 36 kingdoms × T4/T5/tier KP/Dead/Healed/Acclaim; original kingdom CSV deltas also match |
| E12 | verified: 21/32 camp metric comparisons differ from summed displayed kingdoms | A1 both tables, eight metrics × four case-normalized camps; original camp CSV differences match; no replacement or reconciliation requirement |
| E13 | verified distinction: Current/Highest Acclaim differ in 3115 P1 and 2918 P2 rows; 1198 Highest Acclaim delta 539721 | P1/P2 `AC:AD`; legacy has separate current/max contribution and healed/extrema families; semantic equivalence is conditional |
| E14 | verified L1: Basic 15811, Full 9194, Summary 32, Summary Full 32 | L1 `A1:N15812`, `A1:AQ9195`, `A1:E33`, `A1:L33`; only Full Data is consumed by current code |
| E15 | verified structural limitation | L1 Full Data minimum/maximum/first-last fields versus P1/P2 snapshot headers: two observations cannot recover intervening extrema or per-player first/last capture |
| E16 | verified: zero negative matched deltas for T1–T5, total KP, deaths, healed, current/highest Acclaim; 2062 negative power and 2093 negative troop-power deltas | P1/P2 numeric endpoint comparisons; no universal negative clamp justified |
| E17 | verified: VIP always zero; 65/80 null Alliance values | P1/P2 `F` and `C`; six Alliance cells in each workbook are formula-typed, not ordinary literal strings; preserve text boundary without evaluation |

The private 175-row diagnostic CSV's 4900 numeric endpoint/delta cells match recalculation. All 36 coverage rows match, the 85 unmatched IDs match the symmetric difference, all 216 kingdom deltas match, and all 32 camp difference values match. This validates the stated diagnostic claims, not every private display-name string. Complete header inventory is represented by the [field compatibility matrix](phase_1_field_compatibility.csv).

Historical instructions to derive aggregate DKP, request the inaccessible split/formula, add death weights, filter to 1198, backfill later-only governors, or ask about timezone are superseded. Historical KVK LIST observations remain unverified as current source/SQL data. Neither sample date similarity nor these arithmetic matches proves equal provider periods. No same-period legacy/new parity test is possible from L1 versus P1/P2/A1.

## 4. Forward trace: intake, identity and processing

Evidence references C01–C65 below resolve to exact repository commits, files and symbol/line ranges in the [dependency matrix](phase_1_dependency_matrix.csv).

**Admission (C01–C07).** `DL_bot.on_message` routes in sequence, returning after the first handled route. Whole-KVK admission checks the configured Pro Kingdom channel and attachments; permission enforcement depends on that channel's actual ACL, which was not inspected live. It reads each matching attachment, records audit phases, checks SQL headroom, offloads to a process and optionally schedules export. Multiple attachments are separate imports, not one transaction. The route recognizes XLSX/XLS/CSV; the parser rejects CSV and requires normalized `Full Data`. Basic Data and both Summary tabs are unused. The current 43-header contract includes aliases for first/last timestamps and legacy differences. Unknown columns are inventoried; missing expected columns reject. Numeric coercion accepts integral inputs and integer-literal strings, maps malformed/fractional metrics to null, and rejects missing ID/kingdom. New formats must have separate structural validation.

**Timestamp contradiction (C02/C06/C08).** The whole-KVK route passes `message.created_at`; no filename timestamp parsing occurs in that route, wrapper, service or DAL. `ensure_aware_utc` labels naive values UTC or converts aware values to UTC. SQL stores second-resolution naive UTC plus a separate imported timestamp. Thus the belief that this importer already uses filename UTC scan start is disproved locally. Required new grammar for P1/P2 is a validated trailing `YYYY-MM-DD_HHMM.xlsx` observation timestamp in UTC, preserving minute precision. An optional seconds variant and any renamed-copy suffix need explicit grammar tests; never use upload time as fallback. A1 lacks unambiguous year/minute-level observation mapping in its filename. Its mapping cannot be inferred from arrival order or nearby daily scans. L1's filename is also not parsed by this whole-KVK route.

**Identity and retry (C06–C11/C47).** Stage uses `IngestToken` UUID and global identity `row_no`; it has no governor uniqueness constraint. Raw's PK is `(KVK_NO,ScanID,governor_id)`, so duplicates can fail the ingest transaction. `KVK_Scan` allocates `MAX(ScanID)+1` **within KVK**, under transaction locks. Duplicate identity is exactly `(KVK_NO,ScanTimestampUTC,FileHash)`; same hash at another upload time is different, and changed hash at the same time allocates another scan. Renaming alone is not the duplicate key. ImportAudit correlation/hash is observability, not a source-selection lock. No correction pointer or immutable finalized-window generation is represented.

The adjacent global `SCANORDER` is different: `IMPORT_STAGING_PROC_CORE` allocates MAX across `KingdomScanData4`, `KingdomScanData5` and `KS4_ImportFileReceipt`, plus one under locks. It parses row `updated_on` to minute-resolution `ScanDate`. This namespace does not reset per KVK. `ProcConfig` and `KVK_Details` fighting bounds use that daily namespace; `KVK_Windows` uses whole-KVK `ScanID`. Historical 10/24, 866/888 and 1090/1112 are not interchangeable. No active `SCAN_Dates` importer was found in the searched bot config/export modules or SQL snapshots; historical sheet observations do not assign new scan IDs.

**Baseline/window behavior (C10/C12).** Ingest appends every previously unseen governor to `KVK_Player_Baseline`, using that file's `max_power` (or zero) and allocated scan ID. This is first-seen growth, not a designated master whitelist. Recompute emits a synthetic Baseline row with zeros for each baseline governor. For named windows it reads exact start/end rows, but FULL OUTER JOIN includes either endpoint; absent endpoint/metric falls back to legacy differences and zero. Missing start, missing end, genuine zero and malformed metrics can therefore collapse into plausible numbers. Intermediate scans are unnecessary for endpoint-based metrics; their absence does not alone prevent a two-endpoint gain.

Open ends and configured ends beyond available MAX ScanID are capped to latest; missing intermediate numbered endpoint does not select a nearest observation. Completed windows are not frozen: every recompute rebuilds all output rows for that KVK using current weights and CampMap. `Full` is a separate per-player first-baseline-to-latest calculation, not the sum of configured fighting windows. Starting power gates DKP to zero when nonpositive. New processing must independently enforce B0 eligibility, exact window observations and per-metric availability. Preserve signed power changes and distinguish counter regression from absent data; diagnostic handling is not approval to publish a regressed counter.

**Metric precedence (C12–C24).** Current v2 uses `max_kill_points`, `max_kills_iv/v`, `max_dead`, `max_units_healed`, `max_max_contribute` and `max_cur_contribute` endpoint differences when both exist, otherwise legacy differences. `kp_gain` is all-tier KP; `kp_gain_recalc` is `10*T4+20*T5`; `kp_loss` is healed ×20. Player DKP uses latest configured X/Y/Z; there is no source-date cutoff on latest EffectiveFromUTC. Current/highest Acclaim remain distinct; public export calls current contribution `acclaim_gain`. Kingdom/camp rollups sum player facts and recalculate DKP. Reporting DAL repeats DKP calculation rather than reading stored aggregate DKP. Changing just the writer would therefore be insufficient.

## 5. SQL/storage contracts and configuration

All named objects below are backed by same-named files in SQL `sql_schema/` at the recorded HEAD. These are current local DDL, not deployed rows.

| Objects | Grain/types/constraints | Consequence |
|---|---|---|
| `KVK.KVK_AllPlayers_Stage`, `KVK.KVK_AllPlayers_Raw` | Stage token + identity row; Raw composite PK KVK/scan/governor; bigint counters nullable; name nvarchar(64), kingdom int, camp tinyint; datetime2(0) metadata; Raw indexes KVK/camp, governor, KVK/kingdom | Can retain some endpoint values, but extrema semantics and no source-kind/revision dimension prevent honest drop-in reuse. |
| `KVK.KVK_Scan` | PK KVK/ScanID; unique KVK/timestamp/hash; int IDs, varbinary(32) hash, filename nvarchar(255), datetime2(0) | One logical stream per allocated ID; source/report revision and precision absent. |
| `KVK.KVK_Player_Baseline` | PK KVK/governor; int baseline_scan_id, bigint starting_power, non-null | No designated-roster identity or roster version; growing writer is incompatible. |
| `KVK.KVK_Player_Windowed` | PK KVK/window/governor; WindowName nvarchar(40); combat values bigint NOT NULL; dkp FLOAT NOT NULL; last_scan_id int; contribution defaults zero | Missing data cannot be represented as null; source/version absent from PK. |
| `KVK.KVK_Kingdom_Windowed`, `KVK.KVK_Camp_Windowed` | PK KVK/window/entity; bigint non-null metrics, FLOAT DKP; non-null labels; camp name capacity differs (100 kingdom, 40 camp); no combined tier-death/raw-precision field | Not safe source storage; direct writes collide with legacy rebuild and lose precision/metric meaning. No DKP computed column here: the conflict is procedure/DAL calculation. |
| `KVK.KVK_Windows` | PK KVK/WindowName; WindowSeq tinyint nullable; Start/End int nullable; Notes nvarchar(200); checks start >=1 and end >= start when both set | Structure can remain; actual endpoint namespace and source mapping must be explicit. No FK proves existence of either scan. |
| `KVK.KVK_CampMap` | PK KVK/Kingdom; CampID tinyint 1–8; CampName nvarchar(40) | Four named source camps fit capacity. Normalize case/whitespace then require unique configured name/ID resolution and all 36 memberships; no new sheet columns needed. |
| `KVK.KVK_DKPWeights` | PK KVK/EffectiveFromUTC; X/Y/Z FLOAT non-null | Retain one WeightDeadsZ. Recompute selects latest row, not historical publication version. |
| `dbo.ProcConfig` | PK KVKVersion/ConfigKey; ConfigValue FLOAT nullable | Daily-scan/config namespace, not whole-KVK scan registry. |
| diagnostics/negative tables; cleanup proc | durable diagnostic fields; default stage 24h, diagnostic 90d, negative 365d; DryRun defaults true | Cleanup is not rollback and does not restore raw or published selection. No cleanup executed. |

`proc_config_import.run_proc_config_import` reads `KVK_Windows!A1:F`, `KVK_CampMap!A1:D`, `KVK_DKPWeights!A1:D`, KVK Details, ProcConfig, target bands and exemptions. It normalizes known headers and deletes/replaces included KVK partitions for the three KVK tables in the transactional route. Missing KVK-16 sheet rows do not prove that an old SQL partition was removed. Weights import does not supply EffectiveFromUTC, so the SQL default provides import time. KVK Details is replaced after validation. Postcommit `sp_TARGETS_MASTER` is a separate side effect; no call to whole-KVK recompute was found there. The nontransactional option has a narrower ProcConfig path. These behaviors explain why source-sheet, imported-data and reporting-refresh readiness must be checked separately.

The existing Reliability WS1 design owns truthful config-import completion and offload concerns. No runtime prerequisite fix is approved or proved necessary just to complete this audit. Any dependency on WS1 before migration release must return as a bounded approval item.

Current KVK-16 readiness remains unknown: require actual windows/weights/map/details, source sheet read/version, import report, whole-KVK scan registry, raw/output counts and publication timestamps. Do not inherit KVK-15 weights or add missing rows during Phase 1.

## 6. Backward consumer trace and period findings

The CSV provides individual edges, and the following groups explain their practical meaning.

- **Direct whole-KVK consumers:** fighting embeds' player/kingdom/camp Top 5 blocks and own-kingdom/camp summaries (C20–C28); all ten SQL export sections and primary/per-window/cumulative/comparison Sheets (C29–C34); `/kvk_admin export_all`, `recompute`, `list_scans`, `window_preview`, and `test_embed` (C35–C39). Admin mutation/export commands were inspected, never run.
- **Mixed consumer:** `/kvk stats` main metrics use kingdom-only `STATS_FOR_UPLOAD` JSON, while camp and overall rank come from whole-KVK Full rows (C40–C43). The card's numerator/targets/combat measures must not silently acquire a different period or source than its rank/context. Overall rank orders tier-KP descending, then governor ID, over Full population. Its source population will change under B0.
- **Independent main stats/history/targets:** KS4 → delta/output procedures → `EXCEL_FOR_KVK_n`/`KVKFinalReportHeader` → `STATS_FOR_UPLOAD` → cache feeds personal stats and current rankings. History and records use finalized `v_EXCEL_FOR_KVK_Started` plus completion headers and ended lifecycle. Target publication is separately versioned, frozen and cached. Source migration of whole-KVK does not automatically repair or replace these paths (C44–C54).
- **Adjacent systems:** `/me stats` and dashboard, `/stats player` leadership review, daily CSV/Sheets account exports, standalone `dbo.KS` kingdom summary and calendar overview have independently traced sources (C55–C60). Honor and PreKVK ranking modes read their own raw/score registries through `kvk_stats_dal`; neither is a new whole-KVK consumer. Retired flat KVK stats/history/rankings commands redirect to grouped commands, not a hidden alternate importer.

**Aggregate period (Q03).** Existing kingdom/camp rows are isolated player-derived fighting-window deltas; SQL `fn_KVK_*_Aggregated` adds configured windows with non-null starts. Sheets `_aggregate_windowed_dfs` also adds windows; the comparison builder pivots missing windows to zero. Baseline and equal-start/end produce zero player differences, not permission to label an unrelated cumulative aggregate zero-length. The `Full` export is separately baseline-to-latest. Neither an end scan nor matching first-fight sample arithmetic authorizes labelling A1's apparent 26-August baseline totals as a later individual window. For a fixed-baseline report, select and label the cumulative period directly; do not place it in every fighting-window row or subtract reports without an approved contract. The remaining source decision is whether future aggregate exports actually isolate each fighting window or remain fixed-baseline cumulative, and which truthful output labels/availability apply in the latter case.

**Caches/refresh.** Whole-KVK block reads are current SQL queries, not a generation-bound snapshot shared across all queries. Stage, raw ingestion, recompute, asynchronous export and public delivery are separate stages. On recompute/export failure, committed raw data may exist with stale outputs or partially updated external sheets. Re-upload may be rejected as duplicate if the timestamp/hash are preserved; rerunning only recompute may be the appropriate existing operator action, but no automatic recovery claim is made. Governor-keyed stats cache, target publication cache, last-KVK cache, request-held view payloads, diagnostic previews and CSV dispatch guards have different lifecycles. New source selection must include KVK, source, period/window, endpoint/report IDs, publication revision, roster/weight/map identity in the snapshot/cache contract, and invalidate dependent previews without resetting daily claims. Closed windows need frozen selections rather than “latest on every read.”

**Output constraints.** Retain provider aggregate DKP and precision; do not force equality with eligible-player DKP. Total-KP versus tier-KP labels, tanking ratios and denominator cohorts require explicit basis. Canonical combat helper returns healed×20 and KP×100/(healed×20+deads) with availability checks; replacing KP with another basis changes that ratio. Existing reporting normalizes missing Acclaim to zero; Sheets comparison fills absent windows with zero; these need availability handling before reuse. Names/camps participate in some export grouping keys and can split one identity after a label change. Existing Sheets writes use RAW; rankings CSV text escapes formula prefixes. The new parsers should retain literal text without evaluating formula-typed Alliance cells; the offline audit did not execute them. Existing embed packing/limits should be reused and tested with added source/period labels, not expanded indiscriminately.

## 7. Coverage limits, risks and next action

Static backwards searches covered every direct `KVK_*_Windowed`, `KVK_AllPlayers_Raw`, `KVK_Scan`, `fn_KVK_*` and FightingDataset reference in bot Python and SQL snapshots, then followed the discovered runtime call paths. The CSV records exact inspected sources. SQL migrations/deploy inventory and trigger-name searches were inspected as context; no checked-in whole-KVK trigger edge was found. Absence from those files does not prove absence of dynamically constructed SQL, deployed Agent jobs, external notebooks/Sheets consumers or DBA routines. The SQL repo contains a job-inventory query; it was not executed. No full security discovery scan was launched.

Highest-impact migration risks are wrong period labels/double counting, roster growth or missing-observation zeros, aggregate DKP overwrite, namespace collisions, source mixing in cards/caches and inability to reconstruct old extrema from new snapshots. These are design requirements for the next task, not Phase-1 fixes. The two repositories' separate histories and daily versus whole-KVK contracts must remain separate through implementation review.

The audit supports operator review with B0/live-state/period limitations explicit. It does not approve G1, G2, implementation, source activation or release. See the next-slice document for the remaining operator decisions and stop point.

## Follow-up: designated B0 and operator decisions — 2026-09-09

This update supersedes earlier statements that B0 is absent, the provider-period choice is unresolved,
and separate-source direction has not been agreed. Earlier evidence remains historical; implementation
and detailed architecture are still unapproved. The operator supplied the workbook in direct response
to the request for their available master roster. Workbook content is evidence, not task instructions.

**B0:** `C:\Users\cwatt\Downloads\KVK_16_Baseline.xlsx`, 1,551,054 bytes,
SHA-256 `d28d58b3505eac2cfaffc144130ce8816f270496dee439842c49fc06064fe147`. Read-only openpyxl, `data_only=False`, `keep_links=False`;
no save or formula evaluation. One sheet, `Scan!A1:AJ5807`, 36 headers identical to P1/P2.
5,806 nonblank data rows and unique positive integral Governor IDs; zero duplicate/invalid IDs
or invalid kingdom IDs; same 36-kingdom set as P1/P2. No kingdom changes among matched B0/P1
or B0/P2 IDs. This validates supplied-roster identity/shape, not source activation or live SQL.

| B0 roster coverage in the P1/P2 sample window | Governors |
|---|---:|
| Both starting and ending observations | 5,410 |
| Starting observation only | 45 |
| Ending observation only | 7 |
| Neither observation | 344 |
| Total designated eligible roster | 5,806 |

P1 contains 5,455 B0 members and 274 outsiders; P2 contains 5,417 members and 303 outsiders.
272 of the previously matched 5,682 governors are outside B0 and must be ignored for player gains.
The 396 eligible governors without both endpoints remain eligible but have no calculable gain for
this sample window. Missing P1 = 351; missing P2 = 389. Kingdom 1198 has 176 roster members,
171 with both endpoints; the prior 175-player diagnostic must not become the eligible cohort.
These are set intersections against B0, not a new filename/kingdom filter.

All 5,410 eligible pairs have integral observations for the 12 checked fields below. No negative
combat/contribution deltas; signed Power/Troops Power declines occur in 2,049/2,080 pairs.
No player DKP was calculated: active KVK-16 weights remain unverified. These are offline endpoint
calculations, not acceptance of actual configured window IDs or provider aggregate reconciliation.

| Field | Sum of P2 minus P1 over B0-eligible paired observations |
|---|---:|
| T1 Kills | 69,480,370 |
| T2 Kills | 11,603,722 |
| T3 Kills | 6,454,477 |
| T4 Kills | 1,235,205,687 |
| T5 Kills | 5,105,172,805 |
| Total Kill Points | 114,518,434,394 |
| Dead | 756,298,635 |
| Healed | 5,358,213,213 |
| Acclaim | 1,771,324,408 |
| Highest Acclaim | 106,897,871 |
| Power | -8,069,022,777 |
| Troops Power | -8,152,068,958 |

B0 has nine formula-typed cells in Alliance (`C`), 89 null Alliance values and all 5,806 VIP values
zero. No formulas were evaluated. These optional profile fields do not invalidate roster IDs and
must not overwrite unrelated profile data. All 12 checked B0 numeric fields are integral.
The filename contains no scan-start timestamp, and the 36 headers contain no timestamp field.
Roster membership is usable without that timestamp. If B0 is later selected as a numerical
whole-KVK starting observation, its actual UTC scan-start provenance must first be supplied;
do not use filesystem dates, upload time or P1 instead. No date is inferred here.

**Operator period decision:** use separate reports for each fight. During a fight, newer accepted
reports supersede displayed values of the previous revision for that same fight; do not add revisions.
A final fight report closes that period. One separate final overall KVK report supplies authoritative
overall kingdom/camp totals and DKP; do not replace it with sums of fight reports. The provider also
supports running totals, but they are not the selected normal fight workflow. Earlier A1 remains
an illustrative aggregate sample, not retrospectively certified as a particular fight-period report.

**Operator design direction:** new source separate is agreed. Exact revision selection, correction
of finals, source/report identity, publication and UI contracts remain next-design work. Earlier
proposal to require explicit correction of a finalized report remains a recommendation, not an
already implemented capability. No Phase 2, code, SQL or deployment is authorized by this update.

## Pass 4 chronology and three-scan follow-up — 2026-09-09

Latest operator evidence supersedes the earlier missing-B0-time wording. B0 scan start is
**2026-08-26 04:07 UTC** (operator statement; not inferred from filesystem metadata). Only one
fight has occurred, Pass 4. Naming conventions are open for us to design; current names must not
be treated as a provider-fixed grammar. These are confirmed scan starts at minute precision.

| Role | Supplied private filename under `C:\Users\cwatt\Downloads` | UTC scan start | SHA-256 | Bytes |
|---|---|---|---|---:|
| F1S | `auto_pass_lvl4_before_2026-09-05_1526 (1).xlsx` | 2026-09-05 15:26 | `331b224592c34d3968cb9c69dd5b55e536daea3b9323289d45bad381270afcb6` | 1530140 |
| F1M | `pass_4_scan2_2026-09-06_1304.xlsx` | 2026-09-06 13:04 | `1a736a749ce16ef1842f621cf8994045b19ec4726412b20bc6e97bb498c2b660` | 1536824 |
| F1E | `end_of_zone_5_2026-09-07_0721 (1).xlsx` | 2026-09-07 07:21 | `fb80119717b1cc3eb399dc5c81683ffd7f4f502568d0f630603981374b2e4486` | 1536544 |

All three contain one player `Scan` sheet with the same 36 headers as B0/P1/P2; **they are not
kingdom/camp aggregate reports**. F1S/F1M/F1E have 5,729/5,724/5,720 unique positive integral IDs,
36 kingdoms each, no duplicate/invalid governor IDs, and six formula-typed cells each (not evaluated).
Ranges: F1S A1:AJ5730, F1M A1:AJ5725, F1E A1:AJ5721. Read-only openpyxl with `data_only=False`,
`keep_links=False`; no file saves, copies into Git or external content execution.

F1S versus original P1: same ID set and zero differing values in 206,244 keyed cells.
F1E versus original P2: same ID set and zero differing values in 205,920 keyed cells.
Both original byte hashes differ. This proves parsed cell-value equality, not byte, formatting or
package-metadata equality; the reason for the package difference was not assumed or investigated.
Retain both byte identities as evidence. Phase 2 must distinguish re-exports with equivalent source
values from real corrections; a changed byte hash alone is insufficient to classify that distinction.

| Endpoint pair | B0-eligible governors with both observations |
|---|---:|
| Pass 4 start to middle (live progress) | 5,433 |
| Middle to end (diagnostic subinterval only) | 5,414 |
| Pass 4 start to end (whole fight) | 5,410 |
| B0 to Pass 4 end (overall-to-date observation coverage, not final KVK) | 5,417 |

F1M contains 5,438 eligible governors and 286 outsiders. 5,409 eligible governors appear in all
three fight scans; one has start/end but no middle. A missing intermediate observation must not
invalidate an otherwise valid two-endpoint result. Middle-to-end is not the full fight and the
middle cannot substitute for a missing start. Do not add results across changing cohorts.

Across all four endpoint pairs, the 12 previously checked fields have integral observations for
every paired governor. T1–T5 Kills, Total Kill Points, Dead, Healed, Acclaim and Highest Acclaim
have no negative paired deltas. Power/Troops Power declines occur and remain valid signed metrics;
counts by interval are retained in the temporary aggregate validation JSON. No DKP/weights or
production scan IDs were assigned. Existing eligible start/end findings remain unchanged.

**SQL/configuration evidence:** user confirms local SQL/config repo synced with production and
subsequently offers RDP access if local information is insufficient. Both local HEADs/remotes remain
as recorded; SQL status is clean. This is operator-attested synchronization, not an independent
live query. Scoped `rg --files` checks in SQL exports/deploy/docs and config-related snapshots,
plus reads of Windows/Weights/Map definitions, establish local DDL access; those table definitions
contain structure, not current KVK-16 row values. Migration reference searches do not prove active
configuration. An example deployment config is not an authenticated connection. No DB/RDP session,
credential search, procedure or configuration change occurred. Local evidence is sufficient for
Phase 2 design; live rows/jobs can be checked later if a specific dependent decision requires them.

No later-fight source can be supplied yet; use synthetic later-fight scenarios rather than re-asking.
Optional aggregate live/final examples remain a different source category, not a blocker. Do not
wait for the final whole-KVK report. The task pack/starter now incorporate all these facts and
continue to stop before implementation. This follow-up does not execute Phase 2.
