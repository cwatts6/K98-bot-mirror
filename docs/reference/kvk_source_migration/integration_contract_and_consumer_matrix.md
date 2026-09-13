# S7 integration contract and consumer matrix

## Current status — S7/S8A complete and merged; S8B next, 2026-09-13

S7's approved contract/manifests and S8A's SQL foundation are complete and merged.
The operator confirms successful smoke acceptance and local pulls; **no changes have
been pulled to the bot machine**. Retained S8A evidence includes six successful disposable
scripts; the later runner input fix has offline validation only. No fresh post-merge
SQL run, production runtime deployment or activation is claimed.

**Next: start S8B Bot Source and Matched Update Services in a new chat, review/scope first.**
Use the [S8B pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8B%20Bot%20Source%20and%20Matched%20Update%20Services.md) and [starter](../../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S8B%20Bot%20Source%20and%20Matched%20Update%20Services.md).
Read the [canonical closeout, merge evidence and exact S8B carry-forward manifest](s8a_closeout_and_s8b_handoff.md).
Do not reopen settled S7 decisions or repeat S8A implementation. Further SQL execution
requires exact target/backup/row-preview/operation approval; S8B implementation needs its
own approval after scope review. Public routing remains S9 work; SourceRouting.Enabled
alone does not implement it. S6-OPS01/PERF01/CAP01, both uncertain publications and all
retained databases/files remain preserved. Earlier dated sections are historical evidence.

2026-09-12. Documentation/read-only S7 approved by Chris Watts in the task starter.
**Design delivered for review; runtime, SQL, configuration and operations are not approved.**
Read with [exact manifests and validation](integration_implementation_manifests.md),
[settled decisions](post_s6_integration_requirements.md), the
[approved architecture](phase_2_contract_and_architecture.md) and
[handoff](post_s6_handoff_log.md). S7-D01–D09 are settled, not questions.

## 1. Scope summary and evidence boundary

Ordinary whole-KVK reports, linked card context, diagnostics and spreadsheet outputs
need an actual season resolver and a complete-update selection. Existing V2 adapters
are useful foundations, not public integration. Source-independent KS4 metrics,
targets, finalized history and calendar systems retain the approved architecture's
ownership; every C01–C65 row below is classified explicitly. No all-kingdom records
enter daily SCANORDER or replace independent target/profile/history data.

Read-only entry: Bot main/origin/main `a2f148fa9bd4fb367fd46d0500a768c14fee915b`,
local production/main `a8c9c515066ca6ef079120b76dd160e3389badab`; SQL main/origin/main
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Bot origin is
`https://github.com/cwatts6/K98-bot-mirror.git`, production is
`https://github.com/cwatts6/K98-bot.git`.
SQL origin is `https://github.com/cwatts6/K98-bot-SQL-Server.git`. Bot has the 23-path
handoff delta; SQL is clean. Tracking refs are local observations, not freshly fetched
remote heads. No fetch or provider query was used. SQL has no tracked AGENTS.md or
SECURITY.md; the supplied Bot/SQL-source instructions and migrations/README.md apply.

Mirror #272 and production-repository #579 are accepted merged evidence. Local
deployment is operator-attested. Neither production runtime deployment nor a fresh
post-merge smoke is established. All S1–S5B and S6 acceptance remains intact.

## 2. Fixed season source and serving contract — S7-D01/D02

Add `KVK.SeasonSource`, keyed by positive int KVK_NO, containing immutable
SourceKey (`legacy_full_data` or `snapshot_report_v1`), ChoiceID UUID, ChosenBy,
ChosenUTC, Reason, provenance and lifecycle (`planned`, `open`, `closing`, `closed`).
SourceKey/ChoiceID cannot be updated or deleted by ordinary workflow APIs. Lifecycle
changes use monotonic SeasonVersion CAS. Serving is a separate availability decision:
for new source retain SourceRouting.Enabled, RoutingVersion, DisplayPeriodID and
CapabilitiesVersion. Disabling serving never changes SeasonSource or permits legacy fallback.

New seasons require explicit admin choice before either importer accepts facts.
Neither first upload wins a source race nor channel selection chooses the season source.
Concurrent same-choice requests return the same audited choice; opposing requests
conflict. Enforce this again at the DAL acceptance transaction, including legacy intake
after its timestamp-based KVK resolution, before writing accepted rows or recomputing.
New intake without onboarding returns setup required; no implicit legacy default.
Distinct player observations remain accepted oldest first, with both logical ScanID and
UTC scan start increasing; do not use the older architecture draft's delayed-arrival example
to bypass the approved ordering amendment. A delayed older distinct event is rejected for
normal admission; corrections/semantic aliases retain their accepted identities.

Compatibility: a reviewed migration inventories historical legacy KVKs from existing
KVK_Scan and records legacy choices with migration provenance; existing new SourceRouting/
observations require explicit classification because S6 synthetic and partial selections
must not become public choices by accident. If both streams exist, migration reports the
conflict and does not choose. Do not infer identity from Enabled. Historical compatibility
is provided by these explicit SeasonSource rows with migration provenance, not a second
implicit-source rule: a read without a choice is unavailable. Backfill reviewed legacy seasons
before enabling ordinary reader integration; do not infer legacy from a moving date cutoff.
No data backfill is authorized in S7.

Proposed `resolve_season_read(kvk_no, period=None, capability=...)` returns one token:
source, ChoiceID/SeasonVersion, RoutingVersion, selected PeriodID, PublicSelectionVersion,
UpdateID/PublicationID, selected and desired config IDs, availability and reason. Resolve
under one short DAL transaction. A legacy token dispatches to unchanged legacy semantics;
a new token requires enabled serving, understood capability version and complete selection.
Missing row, incompatible schema, disabled serving, missing selection and failed integrity
are explicit unavailable outcomes. Database failure must not be interpreted as legacy.
Private diagnostics may deliberately inspect accepted incomplete state with admin access;
ordinary calls cannot inject a source or publication to bypass the resolver.

Requests load all blocks from the token's immutable publication. Cache keys include
source/KVK/period/publication/public-selection-version/schema and desired config version;
pointer resolution is authoritative on each new request, so notification loss cannot
serve old data as current indefinitely. Request-held cards/views remain pinned and labelled;
refresh replaces the whole envelope. Final action callbacks recheck actor and CAS versions.
Independent player/target/history cache keys and daily send counters are unchanged.

## 3. Matched update and endpoint contract — S7-D03/D04

Use a durable UpdateID UUID created by explicit metadata confirmation, not arrival order,
filename adjacency or equal timestamps. An update scope binds SourceKey/KVK_NO/PeriodID,
report family, intended coverage start/end and as-of context, config and roster versions.
Each accepted stream can reference that UpdateID. Existing attempts, immutable revisions,
semantic digests and logical-scan registry remain the acceptance authority.

For a normal fight, a sealed `KVK.SourceUpdate` binds exact start/end player revision IDs
and ScanIDs, aggregate report/revision ID (both kingdom/camp tabs), config/roster,
player and aggregate finality, confirmer and confirmation provenance. Enforce composite
same-source/KVK/period FKs and verify observation-to-logical-binding identity in the DAL.
An aggregate has no player ScanID. Both aggregate tabs are already one accepted revision.

Compatibility is a validated declared reporting context, not timestamp equality. Player
scan-start UTC and aggregate coverage/as-of remain independently visible. The metadata
confirmation names the intended update and exact stream revisions; coverage must belong
to the same fight and declared live/final scope, use its frozen camp map and expected
kingdom/camp identities, and contain no conflicting period designation. A new as-of value
does not silently retag another update. Unknown A1 fight assignment remains unselectable.
No numerical equality test with player sums, kingdom sums or regenerated aggregate DKP.

| Transition | Durable result and public effect |
|---|---|
| Create context; player first or aggregate first | Accept independently; `waiting_player` or `waiting_aggregate`; public selection unchanged |
| Second compatible accepted stream | Validate versions and membership; seal immutable revision tuple; candidate build may start |
| Incompatible second stream or stale confirmation | Reject association; preserve accepted input privately; public selection unchanged |
| Correction of one stream | Create successor update referencing correction and exact unchanged counterpart; require counterpart-validity confirmation with actor/reason/context |
| Complete candidate | In one transaction seal selection and export intent after CAS recheck; preserve prior complete selection/history |
| Duplicate semantic re-export | Existing attempt outcome/alias only; no new scan, update generation or export request |
| Build failure/restart | Resume sealed tuple; no reimport, guessed counterpart or MAX-scan reselection |

Counterpart confirmation can be supplied in the same normal import/config confirmation.
It names base update, retained counterpart revision, intended new player/config context and
actor. It is invalidated by any changed referenced revision/config/roster/coverage. Unattended
config refresh cannot manufacture an operator's attestation. If the attestation was supplied
while an authorized endpoint was pending, arrival of that exact endpoint resumes automatically.

Preserve interim 11−10, then 12−10, final 13−10. An authorized EndScanID change to 14
permits replacement 14−10 **without another correction command**. The normal config
confirmation may also confirm that the exact retained aggregate remains valid for the new
context. Without that confirmation or a new matched aggregate, the player calculation can
complete privately but public selection waits. This is pair eligibility, not a second
authorization to correct the player endpoint. No synthetic aggregate upload is required.
The old 13−10 result is labelled previous/config pending against desired 14; it is not current
final. Failed config processing retains durable desired intent; endpoint chains and CAS prevent
older builders winning. Unrelated weight/map/roster changes still need their own reviewed authority.

### Domain exceptions, not generic partial-publication bypasses

| Context | Rule |
|---|---|
| B0 onboarding | Accept/freeze eligible roster and B0 kingdom attribution privately without aggregate; no combat public update/export intent is generated by onboarding |
| Configured equal endpoints/no-fight | All frozen B0 members receive supported zero fight scores under the accepted resolver, including absent scan members; no combat ranks; aggregate `not_applicable`; explicit typed no-fight update can select without fabricated report |
| Missing individual metric/member endpoints | Keep available/unavailable states; complete pair means both intended streams, not every metric or governor usable; never substitute zero |
| Overall before its aggregate | Player B0→latest calculation remains private; ordinary overall reports say waiting for separate overall aggregate; last eligible complete overall may be shown as previous |
| Complete overall | Bind separately supplied final overall aggregate to explicitly selected B0→end player context; independently label stream finality; no fight sum or arbitrary first/last player fallback |
| Config-only display rename | Reuse exact immutable inputs with new reviewed config provenance; no numerical rewrite; no-op digest creates no export |
| Config changes inputs/coverage | Successor update must meet pair rules; endpoint authority is carried from SourceConfigRequest; weight/map/roster changes never inherit endpoint-only authority |
| Legacy season | Legacy Full Data is the legacy complete source unit; do not demand the new two-workbook format or reinterpret historical calculations |

Earlier T40 partial-stream public selection and generic final-unavailable substitution are
superseded for normal public combat updates. Accepted private component behavior remains
historical evidence. T36 player overall without aggregate is now private-only; an explicit
unavailable public message is permitted. T66 cross-source fallback is prohibited within a
fixed-source season, even if legacy observations exist. T58 stale pending export is coalesced;
an already running export follows the finish-current rule below.

## 4. Atomic complete selection and export intent

Retain SourcePublication and SourceSelection as accepted component history. Add
`KVK.SourceCompleteSelection`, keyed by source/KVK/period, pointing to sealed UpdateID
and a complete immutable PublicationID with increasing PublicSelectionVersion. Ordinary
reads/exports must use this gate, not an arbitrary complete SourcePublication (which can
legitimately have missing aggregate under predecessor contracts).

A sealed update selects its explicitly matched player/aggregate revisions even if a newer
unmatched stream has been accepted. Existing `validate_snapshot_inputs` checks the global
latest logical scan for live candidates; S8B must replace that check for paired publication
with sealed-update identity/CAS validation, so an unmatched input cannot starve a complete
pair. Accepted correction policy still applies.

Build facts outside the selection transaction. The short commit locks season then period,
checks fixed source, lifecycle, expected public/config/input versions and sealed pair,
verifies complete counts/hash, advances the complete pointer, records action and inserts
`KVK.SourceExportIntent` plus its `SourceExportIntentPublication` rows. The intent pins the
full current complete per-period vector, including unchanged periods, for one season update.
The vector includes public versions, config IDs and a content hash. No target registration
is needed to retain intent; missing destination leaves `waiting_destination`, not lost work.

All new-source writers use one SQL lock order: SeasonSource → SourceRouting → sorted
period selection rows (component and complete) → config/request/update rows → intent/vector
rows. Adapt existing routing-first helpers to acquire the season guard first; no opposite
ordering. The season guard serializes vector snapshots, so simultaneous completed periods
cannot lose each other's membership.

The stable intent key is source/KVK/vector-hash/export-schema, with a new explicit rebuild
revision only for output repair. Publication commit acknowledgment loss returns existing
selection/intent. Intake acceptance followed by failed candidate build remains accepted
and resumable; public commit and export intent cannot diverge. SourceAction alone cannot
record season/queue/rollover actions because its schema requires a period and new publication.

Publication availability and spreadsheet readiness are separate receipts. Public command
data may use the new complete SQL publication while Sheets still shows an older confirmed
export; label export age/key separately. Automatic import export does not authorize an extra
Discord send. Existing stats dispatch remains the sole owner of its daily claim policy.

## 5. Shared coordination and restart contract — S7-D05/D06/D07

New source uses durable SQL job/admission state shared with all-KVK and scan-data export
wrappers. `dbo.ExportJob` binds consumer, season when relevant, immutable input/intent,
account identity, registered destination set, pool epoch, state, owner/fence and enqueue
sequence. `dbo.ExportJobResource` records conflicts; `dbo.ExportResource` owns active
job/owner/fence and blocked reason. General tables use dbo because daily exports are not
new-source KVK publications. One coordinator database is required for all participating
machines/processes; separate local DBs cannot establish mutual exclusion.

Resources: resolved Google spreadsheet IDs (including index, parts and all legacy output
files), account identity plus project budget, and legacy SQL snapshot resource for mutable
source tables/config. Sheet titles are discovery labels, not resource identity. Register IDs
before mutation; aliases to the same file conflict. Provisioning must reserve account admission
before discovery/create and register returned IDs before content mutation. Overlap between
new pool and legacy/scan output IDs is rejected at registration. No user-supplied arbitrary URL.

Use conservative one-running-export-per-account admission initially. Other accounts with
disjoint destinations can proceed. New immutable input acceptance and candidate calculation
can proceed while a provider export runs. Legacy SQL ingestion/recompute/config and scan-data
snapshot acquisition share a short SQL-resource/session lock through their Bot wrappers,
released before provider work. Capture all export result sets/config/provenance together into
an immutable durable spool with SQL digest/length/owner receipt, then use only that snapshot.
Do not read mutable tables between provider tabs. Snapshot capture and legacy writers must
participate in the same admission protocol across processes; external SQL agents/standalone
scripts are a deployment inventory gate, not an assumed participant. No UPDATE_ALL2 transaction
wrapper: it owns/rejects ambient transactions; use session admission outside its internal phases.

Acquire legacy SQL snapshot admission once at the producer orchestration boundary and pass a
validated ownership token to nested DAL/config helpers; do not reacquire the same exclusive
resource through another connection while the caller holds it. Keep the producer's import
receipt, committed output provenance and snapshot capture associated under that admission.
Config provider reads are collected before entering the SQL portion. Failure after SQL commit
but before spool registration records pending snapshot work for that committed generation;
if mutable output has since advanced, report that mismatch and require a fresh explicitly
identified snapshot, never label newer values as the failed import's output.

Spool location is a registered private durable storage root shared by eligible workers; do not
use a temporary directory or credential-relative path as authority. Missing/corrupt spool makes
the job blocked; rebuild snapshot only before external mutation, with a new audited job identity.
If no shared storage is provisioned, pin spool jobs to a worker/storage identity; another machine
can report/reconcile but cannot claim execution. New-source jobs can reload immutable SQL facts.

Legacy all-KVK acceptance and recompute currently commit separately. A raw ScanID alone
does not prove output completion. Its coordinated producer records a ready snapshot/job only
after successful recompute and consistent export capture, with exact scan/config/output hashes
in provenance. Manual legacy export may reuse a verified ready snapshot without recompute;
if no valid completion provenance exists, report setup/output unavailable rather than invent
a complete publication. Daily jobs similarly pin their existing committed output/header proof.
This adds export evidence without repurposing SourcePublication for legacy or daily schemas.

Account budget is separate from destination ownership. `dbo.ExportRequestBudget` reserves
the next request time using SQL UTC under a short transaction, then waits outside SQL.
Initially preserve the measured conservative 2.1-second spacing; this is an engineering
starting budget, not a provider quota claim. Wrap both gspread HTTP requests and google-api
execute calls, including reads, retries, grants and formatting. A second process cannot bypass
it. 429/503 update a common cooldown from bounded validated Retry-After/backoff; mutation
ambiguity does not become permission for blind replay. Other account consumers must be
registered or operationally excluded at S11; this code cannot pace unknown external clients.

Lock order: account admission, sorted destination IDs/pool epoch, then short job-row CAS;
season/period/publication transactions never wait for provider admission. Budget reservations
are independent short transactions. No SQL transaction spans any Google request, including
pointer publication. Current `DeliveryRepository.publication_gate` holds a transaction around
publication and checks latest selection; replace that use for coordinated jobs with durable
attempt/epoch authorization before each external phase and monotonic destination sequencing.

| Job state/event | Required transition |
|---|---|
| A running; complete B then C arrive | A's vector never changes; B pending request becomes `coalesced` with SupersededBy=C; B inputs/publication/intent remain; C is latest pending |
| A completes | Record remote verification and confirmed receipt; release resources; latest pending C becomes eligible, subject to account fairness |
| Several consumers waiting | Oldest admission ticket across consumers; replacing one consumer's pending vector retains its original ticket age; no manual priority jump; after each job admit the oldest eligible ticket |
| Failure before any provider mutation | Audited retry eligible; recheck epoch/source; no new import or calculation |
| Failure after private writes | Retain attempt and exact parts; use accepted quarantine/fresh-slot recovery only after old worker cannot advance publication |
| Grant/pointer timeout, process loss or late completion | Mark uncertain and block conflicting destination; lease expiry/session loss is not absence proof; probe exact attempt evidence; no automatic takeover |
| Cancellation/shutdown | Stop new admission; pending remains durable; running worker checkpoints and drains where possible; detaching a timed-out thread does not release its resources |
| A superseded while running | Allow A to finish against pinned authorized job/epoch even though public selection has advanced; C then advances the export pointer; never overwrite a newer confirmed destination sequence |

A failed/uncertain A must reach a permitted terminal or isolated recovery state before C can
advance that destination. SQL fences cannot cancel an already submitted Google request.
Keep the blocked epoch until readback plus terminated-worker evidence resolves uncertainty;
for private abandoned attempts isolate fresh files and forbid old pointer/grant phases.
Do not implement automatic lease-steal publication. Long jobs (accepted ~38 minutes) make
unconditional timeouts unsafe. Coalescing affects pending new-source exports only; daily
SCANORDER jobs/import history retain their existing ordering and are not discarded.

## 6. Grouped export-only UX — S7-D09

Extend existing `/kvk_admin source` action choices rather than create a top-level command:
`export`, `export_status`, `export_reconcile`, `export_rebuild`, and `rollover_preview`/
`rollover_confirm`. Season choice and pair association are additional `source` actions
`choose_source` and `match_update`; extend existing intake confirmation for UpdateID and
counterpart validity. Final option names/signature changes are reviewed with registration.
Commands/views enforce configured guild/channel/admin role and recheck current authority at
confirmation. Services accept typed actor authorization context, not Discord objects.

Export takes KVK and a registered destination key, pins the selected complete vector, and
queues without parsing, importing, recalculating, changing endpoints or publishing Discord.
Ephemeral reply: queued/running/waiting for counterpart/confirmed/no-op/blocked for reconciliation,
with period/as-of and current output link only when confirmed. Ordinary `export_all` delegates
to the fixed-source service; legacy export behavior remains for legacy seasons. Recompute on
new source is private inspection/build policy, not an export-only shortcut or implicit correction.

Confirmed same generation returns no-op with zero provider calls. Failed safe retry retains
identity. Uncertain attempt uses readback/reconcile, never `retry=true`. Damaged confirmed
output requires explicit rebuild preview and confirmation with reason, expected generation/
epoch and fresh RepairID: same accepted input/publication/vector, new export attempt. Retain
original confirmed receipt and damage/rebuild audit. A status query is read-only. Stale buttons,
wrong owner/guild, expired token or lost role cannot enqueue. Rehydrate confirmation from SQL
or make it expire safely on restart; no in-memory-only authority. No raw private rows/paths in replies.

## 7. File pool and rollover — S7-D08; S6-CAP01

Let P be the maximum measured/planned parts per generation from the existing partitioner,
including headers/directory and the 9,000,000-cell per-part ceiling. Initial recommended
capacity is **1 stable index + P active + P staging + max(P,Q) quarantine + P reserve + R**,
where Q is actual quarantined parts and R is other protected final/referenced parts that
cannot yet retire. For P=2, Q<=2 and R=0 this is nine files, a minimum allowance rather than
a guarantee for the retained S6 pools. This covers one quarantined generation, not unlimited
uncertain attempts. Recompute P/Q/R before writes for actual 36-kingdom/mixed reports and future
period counts. Do not equate the synthetic two-kingdom benchmark with a production maximum.

Register pool/slot ownership durably with unique file IDs and epoch. A slot is free, staging,
active, quarantined or retired; assignments/attempt-part receipts are append-only history.
Never overwrite current, uncertain, still-owned or quarantined files based on age. Preflight
all required parts and receipt capacity before claim/provider mutation. Normalize new multipart
receipts into attempt/part rows rather than growing the existing nvarchar(1024) JSON indefinitely.
Existing SourceDelivery receipts remain byte-preserved; migration does not truncate or rewrite them.
Keep the current registration bounds (at most eight registrations and sixteen slots per
registration) until a separately reviewed limit change. A computed allowance exceeding those
bounds returns setup required before mutation. During the KVK, existing final/live-reference
protection remains; at rollover explicit retirement releases confirmed historical remote
representations while retaining their input/publication facts. No final-history deletion is needed.

Rollover: preview exact old/new KVK, all jobs/receipts/file IDs and epoch; freeze old-season
admission (`closing`); finish/reconcile running work; cancel only never-started pending export
requests with audit; preserve publications/inputs; increment epoch after proving no old writer
can act; mark confirmed remote receipts `retired` by a separate disposition event. Their old
URL means retired/reused, not a continuing archive. Discord messages are not silently edited
or removed. The stable index shows season ended/setup until the next verified generation.

Before reusing a file, remove prior public Viewer exposure under explicit rollover authority,
verify private ACL, clear all prior tabs/data/formatting/named ranges and replace with the
expected empty manifest. Read back before assignment to the new epoch. Uncertain ACL/clear
leaves quarantine. Exact current/uncertain index cannot be reused under a new epoch without
resolving the old pointer operation; using a new index instead is a separately reviewed destination
change. New generation fully verifies privately, then audience grants and pointer publication
follow the accepted receipt protocol. Late old completions fail epoch validation and do not free
slots. There is no lifetime spreadsheet-archive requirement; SQL/input/audit history remains.

## 8. Authoritative SQL comparison and proposed state

Source snapshots read at SQL `44afa315dd6cbfe9fec101f2a39a62e534f5b583`; no SQL server
connection or execution. SQL deployment remains unsafe until future migrations/tests/review.

| Existing exact object | Verified constraint and design consequence |
|---|---|
| KVK.SourceRouting | PK KVK_NO; SourceKey check only snapshot_report_v1; Enabled approval guard and FK to SourceSelection; add separate SeasonSource, do not reinterpret this as legacy choice |
| KVK.SourceSelection | Composite source/KVK/period PK and scoped publication FK; SelectionVersion >0; no pair registry; add SourceCompleteSelection |
| KVK.SourcePublication | UUID PK, scoped unique keys, config/roster/start/end/aggregate FKs; complete BuildState proves counts/hash but permits absent aggregate; retain historical rows and require sealed update for public pointer |
| KVK.SourceDelivery | PK publication/kind/destination; destination <=128; receipt nvarchar(1024); owner/fence/state constraints; cannot identify arbitrary legacy/daily jobs or repeated repaired output attempts |
| KVK.SourceImportAttempt | Guild/message/attachment/action replay unique; exactly one accepted revision kind; provenance JSON <=65536 bytes; no explicit pair ID; association belongs in SourceUpdate |
| KVK.SourceObservationRevision / SourceLogicalScan / SourceScanBinding | Separate immutable revision/scan binding namespace; association must verify exact observation behind each logical scan; aggregates never allocate scans |
| KVK.SourceAggregateRevision / SourceKingdomReportRow / SourceCampReportRow | Scoped accepted revision with both tab sets; Decimal/raw precision remain authoritative; pair does not recompute values |
| KVK.SourceConfigVersion / SourceWindowConfig / SourceCampConfig / SourceWeightConfig | Versioned roster/window/map/decimal coefficient snapshots; references remain immutable; no changes to sheet A:F/A:D contracts |
| KVK.SourceConfigRequest | Endpoint chain, desired/base config, Origin/Actor/Reason, requested/pending/applied/rejected; replay unique by config hash/base; use for endpoint authority, not aggregate attestation |
| KVK.SourceAction | Period/new-publication required; limited action enum and provenance; retain publication actions, use new queue/season audit fields for other scopes |
| KVK.KVK_AllPlayers_Stage / Raw / Player_Baseline / Player_Windowed / Kingdom_Windowed / Camp_Windowed | Legacy keys omit source/revision and recompute rebuilds partition; no new-source inserts or semantic reinterpretation |
| KVK.KVK_Windows / KVK.KVK_CampMap / KVK.KVK_DKPWeights | Source-independent configuration input; version before new-source use; no sheet layout or inferred ID namespace change |
| dbo.ProcConfig / dbo.STAGING_STATS / dbo.STATS_FOR_UPLOAD / dbo.EXCEL_FOR_KVK_* / dbo.KingdomScanData4 | Daily target/history pipeline, not a destination for new all-kingdom facts; retain exact output and SCANORDER contracts |

New entity column/key specifications and exact migration paths are in the manifest document.
No new UDT is required. Old SQL procedures/views/functions remain legacy contracts. Missing
proposed objects are deliberate creates, not claims of deployed schema. Read-only discovery found
no `KVK.SourceEndpointRequest`: the actual existing object is `KVK.SourceConfigRequest`.

## 9. Consumer matrix

Each row below records the current entry symbol/path at the verified Bot/SQL heads, current
source and proposed seam. Historical C IDs are retained. `R` means fixed-source resolver and
complete token from section 2; `Q` means shared admission/snapshot/pacing from section 5;
`I` means deliberately independent per approved architecture, with no source migration.
Tests are exact Bot paths under `tests/` unless prefixed SQL. A listed test is planned coverage,
not a new pass. Current line locations are navigation aids, not historic Phase-1 line assertions.

| ID | Current exact entry | Current source → output | Proposed seam and chosen-source coverage | Version/cache owner | Planned test files |
|---|---|---|---|---|---|
| C01 | `DL_bot.py:518` — `on_message` | legacy whole-KVK / Discord channel dispatch → handle_kvk_all_upload | R admission before legacy acceptance; new private route remains first; Q automatic export handoff | R token/pinned publication; Q job vector where exported | `tests/test_kvk_all_upload_route.py`; `tests/test_kvk_source_upload_route.py` |
| C02 | `upload_routes/kvk_all_route.py:271` — `handle_kvk_all_upload` | legacy whole-KVK / PROKINGDOM_CHANNEL_ID attachments → ingest_kvk_all_excel | R admission before legacy acceptance; new private route remains first; Q automatic export handoff | R token/pinned publication; Q job vector where exported | `tests/test_kvk_all_upload_route.py`; `tests/test_kvk_source_upload_route.py` |
| C03 | `kvk_all_importer.py:42` — `ingest_kvk_all_excel` | legacy whole-KVK / prepare_kvk_all_import → ingest_prepared_import | R admission before legacy acceptance; new private route remains first; Q automatic export handoff | R token/pinned publication; Q job vector where exported | `tests/test_kvk_all_upload_route.py`; `tests/test_kvk_source_upload_route.py` |
| C04 | `kvk/services/kvk_all_import_service.py:72` — `read_full_data_workbook` | legacy whole-KVK / Full Data only → canonical frame | Legacy-only parser unchanged; fixed-source rejection occurs before accepted persistence, never parse new source as Full Data | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_import_service.py`; `tests/test_kvk_new_source_parser.py` |
| C05 | `kvk/services/kvk_all_import_service.py:175` — `coerce_full_data_frame` | legacy whole-KVK / legacy frame → stage fields | Legacy-only parser unchanged; fixed-source rejection occurs before accepted persistence, never parse new source as Full Data | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_import_service.py`; `tests/test_kvk_new_source_parser.py` |
| C06 | `kvk/dal/kvk_all_import_dal.py:289` — `ingest_prepared_import` | legacy whole-KVK / stage insert + ingest procedure → raw + recomputed outputs | R fixed-source check after resolved KVK and before accepted writes; Q legacy SQL snapshot admission | R token/pinned publication; Q job vector where exported | `tests/test_kvk_all_import_dal.py`; `tests/test_kvk_season_source.py` |
| C07 | `services/kvk_all_import_audit_service.py:1` — `services/kvk_all_import_audit_service.py` | legacy whole-KVK / upload audit context → dbo.ImportAuditBatch/ImportAuditPhase through shared service | Preserve best-effort audit; add job/choice IDs at caller; audit is not admission authority | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_import_audit_service.py` |
| C08 | SQL `sql_schema/KVK.sp_KVK_AllPlayers_Ingest.StoredProcedure.sql:1` — `sp_KVK_AllPlayers_Ingest` | legacy whole-KVK / KVK.KVK_AllPlayers_Stage → KVK.KVK_Scan | Legacy-only proc, R guarded Bot DAL; historical SQL preserved; external writers require S11 inventory | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_import_dal.py`; `tests/test_kvk_all_recompute_sql_contract.py` |
| C09 | SQL `sql_schema/KVK.sp_KVK_AllPlayers_Ingest.StoredProcedure.sql:1` — `sp_KVK_AllPlayers_Ingest` | legacy whole-KVK / KVK.KVK_AllPlayers_Stage → KVK.KVK_AllPlayers_Raw | Legacy-only proc, R guarded Bot DAL; historical SQL preserved; external writers require S11 inventory | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_import_dal.py`; `tests/test_kvk_all_recompute_sql_contract.py` |
| C10 | SQL `sql_schema/KVK.sp_KVK_AllPlayers_Ingest.StoredProcedure.sql:1` — `sp_KVK_AllPlayers_Ingest` | legacy whole-KVK / KVK.KVK_AllPlayers_Stage → KVK.KVK_Player_Baseline | Legacy-only proc, R guarded Bot DAL; historical SQL preserved; external writers require S11 inventory | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_import_dal.py`; `tests/test_kvk_all_recompute_sql_contract.py` |
| C11 | SQL `sql_schema/KVK.sp_KVK_AllPlayers_Ingest.StoredProcedure.sql:1` — `sp_KVK_AllPlayers_Ingest` | legacy whole-KVK / KVK.KVK_AllPlayers_Stage → KVK.KVK_Ingest_Negatives | Legacy-only proc, R guarded Bot DAL; historical SQL preserved; external writers require S11 inventory | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_import_dal.py`; `tests/test_kvk_all_recompute_sql_contract.py` |
| C12 | SQL `sql_schema/KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql:1` — `sp_KVK_Recompute_Windows` | legacy whole-KVK / KVK_Scan/Windows/Raw/Baseline/Weights/CampMap → KVK.KVK_Player_Windowed | Legacy-only recompute; R rejects new-season invocation; Q snapshot lock in caller; no new facts written here | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_recompute_sql_contract.py`; `tests/test_kvk_admin_service.py` |
| C13 | SQL `sql_schema/KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql:1` — `sp_KVK_Recompute_Windows` | legacy whole-KVK / KVK.KVK_Player_Windowed → KVK.KVK_Kingdom_Windowed | Legacy-only recompute; R rejects new-season invocation; Q snapshot lock in caller; no new facts written here | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_recompute_sql_contract.py`; `tests/test_kvk_admin_service.py` |
| C14 | SQL `sql_schema/KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql:1` — `sp_KVK_Recompute_Windows` | legacy whole-KVK / KVK.KVK_Player_Windowed + CampMap → KVK.KVK_Camp_Windowed | Legacy-only recompute; R rejects new-season invocation; Q snapshot lock in caller; no new facts written here | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_recompute_sql_contract.py`; `tests/test_kvk_admin_service.py` |
| C15 | SQL `sql_schema/dbo.fn_KVK_Player_Aggregated.UserDefinedFunction.sql:1` — `fn_KVK_Player_Aggregated` | legacy whole-KVK / KVK.KVK_Player_Windowed + KVK_Windows → dbo.fn_KVK_Player_Aggregated | Legacy-only object retained; new R service bypasses legacy sum/rank objects; no runtime direct view activation | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_public_routing.py`; `tests/test_kvk_stats_card_sql_contract.py` |
| C16 | SQL `sql_schema/dbo.fn_KVK_Kingdom_Aggregated.UserDefinedFunction.sql:1` — `fn_KVK_Kingdom_Aggregated` | legacy whole-KVK / KVK.KVK_Kingdom_Windowed + KVK_Windows → dbo.fn_KVK_Kingdom_Aggregated | Legacy-only object retained; new R service bypasses legacy sum/rank objects; no runtime direct view activation | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_public_routing.py`; `tests/test_kvk_stats_card_sql_contract.py` |
| C17 | SQL `sql_schema/dbo.fn_KVK_Camp_Aggregated.UserDefinedFunction.sql:1` — `fn_KVK_Camp_Aggregated` | legacy whole-KVK / KVK.KVK_Camp_Windowed + KVK_Windows → dbo.fn_KVK_Camp_Aggregated | Legacy-only object retained; new R service bypasses legacy sum/rank objects; no runtime direct view activation | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_public_routing.py`; `tests/test_kvk_stats_card_sql_contract.py` |
| C18 | SQL `sql_schema/KVK.vw_FightingDataset.View.sql:1` — `vw_FightingDataset` | legacy whole-KVK / KVK_Player_Windowed + KVK_Windows → KVK.vw_FightingDataset | Legacy-only object retained; new R service bypasses legacy sum/rank objects; no runtime direct view activation | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_public_routing.py`; `tests/test_kvk_stats_card_sql_contract.py` |
| C19 | SQL `sql_schema/KVK.vw_Player_Overall_KVK_Rank.View.sql:1` — `vw_Player_Overall_KVK_Rank` | legacy whole-KVK / KVK.KVK_Player_Windowed Full → KVK.vw_Player_Overall_KVK_Rank | Legacy-only object retained; new R service bypasses legacy sum/rank objects; no runtime direct view activation | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_public_routing.py`; `tests/test_kvk_stats_card_sql_contract.py` |
| C20 | `kvk/dal/kvk_reporting_dal.py:58` — `fetch_top_players` | legacy whole-KVK / fn_KVK_Player_Aggregated + latest KVK_DKPWeights → players_by_kills/deads/dkp; our_top_players | R at enclosing report service; new publication DAL supplies ranks and independent aggregate rows; legacy query only with legacy token | R token/pinned publication; Q job vector where exported | `tests/test_kvk_reporting_service.py`; `tests/test_kvk_source_reporting.py` |
| C21 | `kvk/dal/kvk_reporting_dal.py:105` — `fetch_top_kingdoms` | legacy whole-KVK / fn_KVK_Kingdom_Aggregated + latest KVK_DKPWeights → kingdoms_by_kills/deads/dkp | R at enclosing report service; new publication DAL supplies ranks and independent aggregate rows; legacy query only with legacy token | R token/pinned publication; Q job vector where exported | `tests/test_kvk_reporting_service.py`; `tests/test_kvk_source_reporting.py` |
| C22 | `kvk/dal/kvk_reporting_dal.py:138` — `fetch_top_camps` | legacy whole-KVK / fn_KVK_Camp_Aggregated + latest KVK_DKPWeights → camps_by_kills/deads/dkp | R at enclosing report service; new publication DAL supplies ranks and independent aggregate rows; legacy query only with legacy token | R token/pinned publication; Q job vector where exported | `tests/test_kvk_reporting_service.py`; `tests/test_kvk_source_reporting.py` |
| C23 | `kvk/dal/kvk_reporting_dal.py:170` — `fetch_kingdom_summary` | legacy whole-KVK / KVK_Kingdom_Windowed + latest KVK_DKPWeights → our_kingdom | R at enclosing report service; new publication DAL supplies ranks and independent aggregate rows; legacy query only with legacy token | R token/pinned publication; Q job vector where exported | `tests/test_kvk_reporting_service.py`; `tests/test_kvk_source_reporting.py` |
| C24 | `kvk/dal/kvk_reporting_dal.py:206` — `fetch_camp_summary` | legacy whole-KVK / KVK_Camp_Windowed + latest KVK_DKPWeights → our_camp | R at enclosing report service; new publication DAL supplies ranks and independent aggregate rows; legacy query only with legacy token | R token/pinned publication; Q job vector where exported | `tests/test_kvk_reporting_service.py`; `tests/test_kvk_source_reporting.py` |
| C25 | `kvk/services/kvk_reporting_service.py:68` — `load_allkingdom_reporting_blocks` | legacy whole-KVK / kvk_reporting_dal → 12 report blocks | R ordinary service entry; one token for all twelve blocks; V2 never passes legacy zero normalization | R token/pinned publication; Q job vector where exported | `tests/test_kvk_reporting_service.py`; `tests/test_kvk_public_routing.py` |
| C26 | `stats_alerts/embeds/kvk.py:153` — `build_kvk_preview` | legacy whole-KVK / allkingdom blocks + KVK metadata → two fighting embeds | R ordinary preview/send, same V2 renderer as diagnostic; stale/unavailable explicit | R token/pinned publication; Q job vector where exported | `tests/test_kvk_embed.py`; `tests/test_kvk_public_routing.py` |
| C27 | `stats_alerts/interface.py:24` — `_send_stats_update_embed` | legacy whole-KVK / ks4 lifecycle + fighting preview → send_kvk_embed and guard claim | R through build_kvk_preview; preserve CSV daily cap/receipt ownership; wake is not automatic Discord authorization | R token/pinned publication; Q job vector where exported | `tests/test_stats_alerts_fighting_lifecycle.py`; `tests/test_stats_alerts_guard.py` |
| C28 | `admin_helpers.py:101` — `log_processing_result` | legacy whole-KVK / kingdom processing successful steps → send_stats_update_embed | R through build_kvk_preview; preserve CSV daily cap/receipt ownership; wake is not automatic Discord authorization | R token/pinned publication; Q job vector where exported | `tests/test_stats_alerts_fighting_lifecycle.py`; `tests/test_stats_alerts_guard.py` |
| C29 | SQL `sql_schema/KVK.sp_KVK_Get_Exports.StoredProcedure.sql:1` — `sp_KVK_Get_Exports` | legacy whole-KVK / KVK scan/config/windowed/negative objects → ten named export result sets | Legacy sections remain legacy; R selects V2 generation builder for new season; never bind V2 by legacy positional inference | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_export_service.py`; `tests/test_kvk_source_exports.py` |
| C30 | `kvk/services/kvk_export_service.py:272` — `bind_kvk_export_sections` | legacy whole-KVK / ten SQL result sets → stable section names | Legacy sections remain legacy; R selects V2 generation builder for new season; never bind V2 by legacy positional inference | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_export_service.py`; `tests/test_kvk_source_exports.py` |
| C31 | `gsheet_module.py:3326` — `run_kvk_proc_exports_with_alerts` | legacy whole-KVK / sp_KVK_Get_Exports → primary and additional Google spreadsheets | R/Q wrapper delegates to immutable generation or legacy snapshot with durable job; no direct public new-source write | R token/pinned publication; Q job vector where exported | `tests/test_kvk_export_coordination.py`; `tests/test_gsheet_module.py` |
| C32 | `gsheet_module.py:1891` — `_aggregate_windowed_dfs` | legacy whole-KVK / player/kingdom/camp Windowed sections → ALL_WINDOWS | Legacy-only summation/pivots retained; R new export bypasses and uses exact period vector/independent overall; Q all provider writes | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_source_exports.py`; `tests/test_kvk_export_service.py` |
| C33 | `gsheet_module.py:2059` — `create_additional_kvk_spreadsheets` | legacy whole-KVK / windowed sections → Pass4/Altar1-3/Pass7/Pass8/GreatZig/Pass9 and comparison sheets | Legacy-only summation/pivots retained; R new export bypasses and uses exact period vector/independent overall; Q all provider writes | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_source_exports.py`; `tests/test_kvk_export_service.py` |
| C34 | `gsheet_module.py:782` — `export_dataframe_to_sheet` | legacy whole-KVK / DataFrame → Google Sheets RAW values | Q transport pacing/destination ownership; retain RAW values, literal text and formatting | R token/pinned publication; Q job vector where exported | `tests/test_gsheet_module.py`; `tests/test_kvk_export_coordination.py` |
| C35 | `commands/stats_cmds.py:483` — `kvk_export_all` | legacy whole-KVK / admin service/export runner → Sheets | R grouped admin service; export through Q, new recompute cannot silently rewrite finals, private previews retain explicit pinning | R token/pinned publication; Q job vector where exported | `tests/test_kvk_admin_service.py`; `tests/test_kvk_embed_diagnostic_command.py`; `tests/test_kvk_export_operator.py` |
| C36 | `commands/stats_cmds.py:556` — `kvk_recompute` | legacy whole-KVK / admin service/recompute proc → windowed outputs | R grouped admin service; export through Q, new recompute cannot silently rewrite finals, private previews retain explicit pinning | R token/pinned publication; Q job vector where exported | `tests/test_kvk_admin_service.py`; `tests/test_kvk_embed_diagnostic_command.py`; `tests/test_kvk_export_operator.py` |
| C37 | `commands/stats_cmds.py:582` — `kvk_list_scans` | legacy whole-KVK / admin DAL/KVK_Scan → recent-scan diagnostic | R grouped admin service; export through Q, new recompute cannot silently rewrite finals, private previews retain explicit pinning | R token/pinned publication; Q job vector where exported | `tests/test_kvk_admin_service.py`; `tests/test_kvk_embed_diagnostic_command.py`; `tests/test_kvk_export_operator.py` |
| C38 | `commands/stats_cmds.py:720` — `kvk_window_preview` | legacy whole-KVK / admin DAL/Windows/Scan/Player_Windowed → window diagnostic | R grouped admin service; export through Q, new recompute cannot silently rewrite finals, private previews retain explicit pinning | R token/pinned publication; Q job vector where exported | `tests/test_kvk_admin_service.py`; `tests/test_kvk_embed_diagnostic_command.py`; `tests/test_kvk_export_operator.py` |
| C39 | `commands/stats_cmds.py:614` — `test_kvk_embed` | legacy whole-KVK / build_kvk_preview → isolated embed | R grouped admin service; export through Q, new recompute cannot silently rewrite finals, private previews retain explicit pinning | R token/pinned publication; Q job vector where exported | `tests/test_kvk_admin_service.py`; `tests/test_kvk_embed_diagnostic_command.py`; `tests/test_kvk_export_operator.py` |
| C40 | `kvk/dal/kvk_stats_card_dal.py:19` — `fetch_kvk_stats_card_context` | legacy whole-KVK / Player_Windowed Full preferred + CampMap + overall rank view → /kvk stats card context | R card context only; new source reads frozen B0 camp/rank from publication, never legacy camp fallback | R token/pinned publication; Q job vector where exported | `tests/test_kvk_source_card_context.py`; `tests/test_kvk_stats_card_dal.py` |
| C41 | `services/kvk_personal_service.py:21` — `load_kvk_personal_stats` | kingdom-only KS4 / utils.load_stat_row → /kvk stats main statistics | I main KS4 numerator/targets; separate source context via C43, no all-kingdom metric injection | Existing independent owner; no source cache mutation | `tests/test_kvk_personal_service.py`; `tests/test_kvk_personal_views.py` |
| C42 | `commands/kvk_cmds.py:541` — `register_kvk` | mixed / personal/target/history/rank services → /kvk stats/targets/history/rankings | Mixed: I command main stats/targets/history/rankings; R source context via posting helper; view refresh remains whole-token | R token/pinned publication; Q job vector where exported | `tests/test_kvk_cmds.py`; `tests/test_kvk_stats_card_views.py` |
| C43 | `kvk/services/kvk_stats_card_service.py:182` — `build_kvk_stats_card_payload` | mixed / stats cache + C40 context → stats card/renderers/fallback | R context resolver invoked by ordinary payload; preserve I main measures; separate labelled source/cohort or suppress context | R token/pinned publication; Q job vector where exported | `tests/test_kvk_stats_card_payload.py`; `tests/test_kvk_source_card_context.py` |
| C44 | `player_stats_cache.py:755` — `_build_cache_sync` | kingdom-only KS4 / SP_Stats_for_Upload + STATS_FOR_UPLOAD → player stats JSON cache | I immutable validated KS4 cache provenance/atomic replacement; no new-source invalidation | Existing independent owner; no source cache mutation | `tests/test_processing_pipeline_build_cache.py` |
| C45 | SQL `sql_schema/dbo.SP_Stats_for_Upload.StoredProcedure.sql:1` — `SP_Stats_for_Upload` | kingdom-only KS4 / ProcConfig/KingdomScanData4/KVKFinalReportHeader/EXCEL_FOR_KVK_n → dbo.STATS_FOR_UPLOAD | I KS4 output/final-header contracts; Q consistent legacy snapshot acquisition, no source schema rewrite | Existing independent owner; no source cache mutation | `tests/test_kvk_history_dal.py`; `tests/test_kvk_rankings_finalized_sql_contract.py` |
| C46 | SQL `sql_schema/dbo.sp_ExcelOutput_ByKVK.StoredProcedure.sql:1` — `sp_ExcelOutput_ByKVK` | kingdom-only KS4 / KS4 + ProcConfig + delta tables → STAGING_STATS then EXCEL_FOR_KVK_n + final report header | I KS4 output/final-header contracts; Q consistent legacy snapshot acquisition, no source schema rewrite | Existing independent owner; no source cache mutation | `tests/test_kvk_history_dal.py`; `tests/test_kvk_rankings_finalized_sql_contract.py` |
| C47 | SQL `sql_schema/dbo.IMPORT_STAGING_PROC_CORE.StoredProcedure.sql:1` — `IMPORT_STAGING_PROC_CORE` | kingdom-only KS4 / immutable fallback CSV + receipt → IMPORT_STAGING | I daily SCANORDER and fallback receipts; Q Bot pipeline session admission around mutable SQL work; no all-kingdom intake | Existing independent owner; no source cache mutation | `tests/test_processing_pipeline.py`; `tests/test_kvk_export_coordination.py` |
| C48 | SQL `sql_schema/dbo.UPDATE_ALL2.StoredProcedure.sql:1` — `UPDATE_ALL2` | kingdom-only KS4 / IMPORT_STAGING → KS5 -> KS4 -> delta/output orchestration | I daily SCANORDER and fallback receipts; Q Bot pipeline session admission around mutable SQL work; no all-kingdom intake | Existing independent owner; no source cache mutation | `tests/test_processing_pipeline.py`; `tests/test_kvk_export_coordination.py` |
| C49 | `processing_pipeline.py:163` — `execute_processing_pipeline` | kingdom-only KS4 / fallback queue/stats_module → cache/config/export/delivery steps | I import lifecycle/cache order; Q capture committed snapshot and durable job, remove timeout-detached ownership release | Existing independent owner; no source cache mutation | `tests/test_processing_pipeline.py`; `tests/test_processing_pipeline_run_step_and_normalization.py` |
| C50 | `kvk/services/kvk_rankings_service.py:445` — `build_kvk_rankings_payload` | kingdom-only KS4 / utils.load_stat_cache → current rankings cards/Top25/50/My Rank/CSV | I KS4 rankings (Top25/50/My Rank/CSV), not whole-KVK reporting rank; preserve cache cohort | Existing independent owner; no source cache mutation | `tests/test_kvk_rankings_service.py`; `tests/test_kvk_rankings_browser_view.py` |
| C51 | `kvk/dal/kvk_history_dal.py:135` — `fetch_modern_history_rows_for_governors` | kingdom-only KS4 / v_EXCEL_FOR_KVK_Started + KVKFinalReportHeader → /kvk history service/cards/export | I finalized KS4 history/output headers; no retroactive new source history population | Existing independent owner; no source cache mutation | `tests/test_kvk_history_dal.py`; `tests/test_kvk_history_service.py` |
| C52 | `kvk/dal/kvk_rankings_dal.py:22` — `fetch_hall_of_fame_records` | kingdom-only KS4 / v_EXCEL_FOR_KVK_Started + final header → rankings records/cards/CSV | I finalized KS4 Hall of Fame; no cross-source record ranking | Existing independent owner; no source cache mutation | `tests/test_kvk_rankings_finalized_sql_contract.py`; `tests/test_kvk_rankings_records_view.py` |
| C53 | SQL `sql_schema/dbo.sp_TARGETS_MASTER.StoredProcedure.sql:1` — `sp_TARGETS_MASTER` | kingdom-only KS4 / ProcConfig + KS4 + target helper outputs → KVK_Target_Publication/Row and target views | I frozen target publication and versioned cache; no B0 target roster replacement; Q only where config import shares provider budget | Existing independent owner; no source cache mutation | `tests/test_kvk_target_publication.py`; `tests/test_kvk_target_cache_repository.py` |
| C54 | `kvk/target_cache_repository.py:1` — `kvk/target_cache_repository.py` | kingdom-only KS4 / v_KVK_TARGETS_FOR_BOT via publication DAL → /kvk targets cards/views | I frozen target publication and versioned cache; no B0 target roster replacement; Q only where config import shares provider budget | Existing independent owner; no source cache mutation | `tests/test_kvk_target_publication.py`; `tests/test_kvk_target_cache_repository.py` |
| C55 | `player_self_service/stats_service.py:427` — `build_personal_stats_payload` | kingdom-only KS4 / personal_stats_dal/usp_GetPersonalStatsDaily → /me stats/Stats views | I daily personal account statistics; no all-kingdom profile or counter admission | Existing independent owner; no source cache mutation | `tests/test_kvk_source_independent_consumers.py` |
| C56 | SQL `sql_schema/dbo.vDaily_PlayerExport.View.sql:1` — `vDaily_PlayerExport` | kingdom-only KS4 / KingdomScanData4 + alliance/rally daily views → stats export DAL/CSV/Sheets downloads | I daily SCANORDER export view; Q only shared provider wrapper, not metric migration | Existing independent owner; no source cache mutation | `tests/test_kvk_source_independent_consumers.py`; `tests/test_kvk_export_coordination.py` |
| C57 | `player_self_service/governor_dashboard_dal.py:74` — `fetch_governor_dashboard_data` | kingdom-only KS4 / KS4 latest + location/civilization → /me dashboard | I latest daily profile/dashboard; no new-source VIP/profile overwrite | Existing independent owner; no source cache mutation | `tests/test_kvk_source_independent_consumers.py` |
| C58 | `leadership_player_review/dal.py:419` — `fetch_kvk_history` | kingdom-only KS4 / usp_GetLeadershipPlayerKvkHistory → /stats player leadership report | I leadership finalized history; source basis labels preserved | Existing independent owner; no source cache mutation | `tests/test_kvk_source_independent_consumers.py` |
| C59 | `stats_alerts/embeds/kingdom_summary.py:379` — `send_kingdom_summary` | kingdom-only KS4 / dbo.KS → standalone kingdom summary | I standalone kingdom daily summary and claim; R fighting embed remains separate adjacent component | Existing independent owner; no source cache mutation | `tests/test_stats_alerts_offseason_flow.py`; `tests/test_stats_alerts_fighting_lifecycle.py` |
| C60 | `daily_KVK_overview_embed.py:30` — `post_or_update_daily_KVK_overview` | calendar / event_cache → daily KVK calendar embed | I calendar/event timing and scheduled message owner; not combat source data | Existing independent owner; no source cache mutation | `tests/test_daily_kvk_overview_lifecycle.py` |
| C61 | `proc_config_import.py:582` — `run_proc_config_import` | shared configuration / KVK LIST named sheet ranges → ProcConfig + KVK Details/Windows/Weights/CampMap | Version desired endpoints via existing S5B hook; bind counterpart confirmation; Q account reads/SQL snapshot admission; no sheet column change | R token/pinned publication; Q job vector where exported | `tests/test_kvk_source_config_hook.py`; `tests/test_kvk_source_config_service.py`; `tests/test_proc_config_import.py` |
| C62 | SQL `sql_schema/KVK.sp_KVK_Ingest_Cleanup.StoredProcedure.sql:1` — `sp_KVK_Ingest_Cleanup` | legacy whole-KVK / Stage/Diagnostics/Negatives → retained diagnostics and cleanup counts | Legacy diagnostics-only cleanup retained; never new pair/input/publication/receipt cleanup owner | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_recompute_sql_contract.py` |
| C63 | `kvk/dal/kvk_lifecycle_dal.py:136` — `fetch_max_scan_order` | shared lifecycle / KS4 max ScanOrder + KVK Details/ProcConfig → kvk_state and seasonal dispatch | I daily lifecycle from KS4 max SCANORDER; new logical scans cannot open/finish daily state | Existing independent owner; no source cache mutation | `tests/test_kvk_lifecycle_dal.py`; `tests/test_stats_alerts_fighting_lifecycle.py` |
| C64 | `kvk/rendering/kvk_rankings_csv.py:82` — `_csv_text_cell` | kingdom-only KS4 / rankings payload → download CSV | I rankings CSV semantics; reuse existing formula-prefix escaping for any human export; preserve numeric type | Existing independent owner; no source cache mutation | `tests/test_kvk_source_exports.py`; `tests/test_kvk_rankings_service.py` |
| C65 | `bot_instance.py:1` — `bot_instance.py` | shared orchestration / startup/background scheduling → stats caches/event overview | I existing startup caches/schedulers; register coordinated recovery without automatic recompute/send; Q durable discovery after restart | Existing independent owner; no source cache mutation | `tests/test_kvk_source_recovery.py`; `tests/test_kvk_export_coordination.py` |

## 10. Indirect callers and resource ownership

| ID | Exact caller chain / current evidence | Required integration and test |
|---|---|---|
| N01 | `DL_bot.py:on_message` now invokes `upload_routes/kvk_source_route.py:handle_configured_kvk_source_upload` before legacy routes | Keep private intake precedence/authorization; both admission DALs check SeasonSource. `tests/test_kvk_source_upload_route.py`, `tests/test_kvk_all_upload_route.py` |
| N02 | `kvk_all_importer.py:_auto_export_kvk` → `gsheet_module.py:run_kvk_proc_exports_with_alerts`; route schedules independent task | Q job ownership replaces detached export execution; notify confirmed completion only. `tests/test_kvk_all_upload_route.py`, `tests/test_kvk_export_coordination.py` |
| N03 | `commands/admin_cmds.py:run_gsheets_export_command` callback → `gsheet_module.py:run_all_exports`; `processing_pipeline.py:execute_processing_pipeline` also calls it through a timeout/thread wrapper | Both manual and automatic scan exports use same durable Q job; timeout cannot release still-running worker. `tests/test_processing_pipeline.py`, `tests/test_kvk_export_coordination.py` |
| N04 | `gsheet_module.py:run_single_export`, `transfer_and_sort`, `run_kvk_export_test` are public/manual compatibility entry points | All provider calls, including test/provisioning wrappers, require registered resource admission; snapshots captured once. `tests/test_gsheet_module.py`, `tests/test_kvk_export_coordination.py` |
| N05 | `stats_alerts/allkingdoms.py:load_allkingdom_blocks` → ordinary reporting; `stats_alerts/embeds/kvk.py:send_kvk_embed` → `build_kvk_preview` without selection | R automatic resolution, missing pair/disabled route explicit; existing public receipt and cap logic remain. `tests/test_kvk_public_routing.py`, `tests/test_stats_alerts_fighting_lifecycle.py` |
| N06 | `commands/kvk_stats_card_posting.py:post_kvk_stats_output` → `build_kvk_stats_card_payload` → context; `ui/views/kvk_stats_card_views.py` holds the rendered payload; `ui/views/kvk_personal_views.py` invokes that posting flow | R ordinary context must not fetch legacy camp when new source unavailable; old views remain labelled/pinned or refresh wholesale. `tests/test_kvk_stats_card_posting.py`, `tests/test_kvk_stats_card_views.py` |
| N07 | `stats_alerts/kvk_diagnostics.py` and `stats_alerts/kvk_diagnostic_sessions.py` persist explicit diagnostic selection | Keep private pinned session/replay contract, add public-token provenance to ordinary-source diagnostics; never make injection a public activation mechanism. `tests/test_kvk_embed_diagnostic_lifecycle.py`, `tests/test_kvk_embed_diagnostics.py` |
| N08 | `kvk/services/new_source_recovery_service.py:RecoveryIntakeAdapter.confirm`, `RecoveryService.run_batch`, `deliver_current_exports`; `bot_instance.py:1786` registers recovery | Pair-aware discovery → complete selection/intent → Q; no direct delivery of every raw SourceSelection; restart recovers pinned intent. `tests/test_kvk_source_recovery.py`, `tests/test_kvk_source_pairs.py` |
| N09 | `proc_config_import.py:run_proc_config_import` → `snapshot_config_import`; `SourceConfigRequest` endpoint chains | Persist counterpart attestation reference with desired update, separate from config authority; account pacing also covers Google config reads. `tests/test_kvk_source_config_hook.py`, `tests/test_kvk_source_pairs.py` |
| N10 | `config/sheet_config.json` supplies 14 local scan export queries: KS, POWER_BY_MONTH, ALL_STATS_FOR_DASHBAORD, STATS_FOR_UPLOAD, RALLY_EXPORT, SUMMARY_CHANGE_EXPORT, ALL_GOVS, ALL_GOVS_NAMES, ALL_GOVS_ALLIANCES, v_TARGETS_FOR_UPLOAD, INACTIVE_GOVERNORS, SCAN_LIST, ROK_TRACKER.dbo.ALL_GOVS, ROK_TRACKER.dbo.v_PlayerAccounts_Migrate | All are independent daily/profile/target/history exports; Q shared provider resources. Two tabs share Governor Names, two share Governors, two share KVK LIST. Register spreadsheet IDs and preserve SCANORDER, not new logical IDs. Local config is read-only evidence, not live parity. `tests/test_kvk_source_independent_consumers.py`, `tests/test_kvk_export_coordination.py` |
| N11 | `kvk/services/kvk_targets_card_service.py:build_kvk_targets_presentation_input` calls `load_kvk_stats_card_context` at line 305; its three result paths copy camp_name into target payload; renderer displays it | R applies to camp context only. Add source/period/stale context label through `kvk/models/kvk_targets_card.py` and `kvk/rendering/kvk_targets_card_renderer.py`; target numbers/cache/roster stay independent. Missing complete context suppresses camp rather than querying legacy. `tests/test_kvk_targets_card_service.py`, `tests/test_kvk_targets_card_renderer.py`, `tests/test_kvk_targets_card_posting.py` |
| N12 | `gsheet_module.py:run_kvk_source_export` directly delegates to `deliver_export`; no current production caller found in tracked Python | Require authorized Q job/epoch at delivery boundary; explicit diagnostic/test composition is not an ordinary bypass. `tests/test_kvk_source_delivery.py`, `tests/test_kvk_export_coordination.py` |

The current caller symbols and view paths above were checked in source. New files are
only the separately enumerated future Creates.

Repository search cannot inventory external SQL clients, deployed export job config,
or other machines sharing an account. Those are explicit S11 parity/admission gates. The bounded
code inventory includes direct wrappers and scheduled/manual callers; no unknown external reader
is declared migrated. All intended deployed consumers must be classified before activation.

## 11. Retained S6 evidence and remaining technical review

Canonical exact results, IDs, SHA-256 hashes, tested revisions and failure JSON remain in
[archived S6 pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S6%20Release%20Readiness%20and%20Controlled%20Activation.md),
[release evidence](release_evidence_log.md) and [readiness](release_readiness_and_rollback.md).
These files are preserved byte-for-byte from S7 entry. They are incorporated as evidence,
not replaced by this summary or claimed rerun. S6 ran Bot `85f303f6bd82bdc9a5cfc2d713da5480e1fa694a`
and SQL `44afa315dd6cbfe9fec101f2a39a62e534f5b583`, disposable `K98_S6_Disposable_20260912`
on `9SX2VF4\K98DEV` via `lpc:localhost\K98DEV`. All other retained predecessor databases remain.

| Gate | Accepted evidence and exact retained state | Remaining owner/work |
|---|---|---|
| S6-OPS01 | Private-write exit/recovery changed owner/fence 1→2 and quarantined original slots 01–02; original pointer interruption publication `e19c89ac-7977-5f28-ae4c-031807cd1728` remains publication_pending (original slots 05–06); grant interruption `54a2480a-26fb-5bad-a3f5-9321525a731c` remains publication_pending (benchmark slots 05–06); blind retry/private reclaim blocked | S10 implement queue/epoch recovery; S11 exact interruption evidence and operator disposition. Do not repair either retained uncertainty here |
| S6-PERF01 | 5,806 players × ten periods, 17,831,186 logical cells / 17,831,355 physical; two parts; generation load 92.281s, full export/readback 2248.609s, 991 export calls, no recorded HTTP errors; other importers operator-attested idle | S10 prove cross-process admission/pacing/fairness; S11 deployed profile. Normal 1–2/day, peak 2–3/day accepted; no new duration-cap decision |
| S6-CAP01 | Original nine and benchmark seven file IDs/ACLs/receipts in archive; receipt overflow fails before claim/provider, retained-slot refusal after four GETs/no mutation. Large benchmark publication `390dd712-10c4-5cc3-befd-7dbb067e300c`, export hash `eca93ecc70fe04cb836a483fafb65fa17cd0a990730d4ca77e5d55667557b9ea` | S10 normalized part receipts, bounded pool and rollover; S11 actual capacity/ACL/epoch proof; no archive horizon question |

Evidence directory: `C:/Users/cwatt/AppData/Local/Temp/k98-s6-rehearsal-x8tpc14d`.
`benchmark-results.json` SHA-256 `3587bbafc0bc145744c79ff03cb51e119915ad373ec3dd428385051880615e7b`.
These are retained references; S7 did not open credentials, raw workbooks or connect to those targets.
S6's player-only benchmark publications are accepted component evidence, not proof of the new
matched-publication gate. Its successful pointer-ack-loss case is distinct from the unresolved
in-flight pointer case; no exactly-once provider claim follows.

Exact unresolved receipts (historical readback, not a fresh probe):

| Evidence | Pointer interruption | Viewer-grant interruption |
|---|---|---|
| Artifact | `provider-pointer_readback.json` | `benchmark-ops/provider-grant_readback.json` |
| Index ID | `19jOzLAnEildMoxEQNqLsnkcB8tPo0w9Kym5_cbLof_g` | `1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY` |
| Part IDs | `1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg`; `1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0` | `1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ`; `1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk` |
| Export key | `e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a` | `c19df611173a42517f45c61fdc76693d1f363187b1ea83bc3677de3966b7d85c` |
| SQL state / phase | claimed / publication_pending | claimed / publication_pending |
| Owner / fence / selection version | `bca05d8c-2fa1-43b2-a036-9905e45150f0` / 4 / 5 | `487a17d9-c64d-4116-9274-143ddffbabb1` / 3 / 1 |
| Observed index still selected | Prior key `78792a5a9782b69ca430cc3a5deeecf5a8e8ff7090dd547cbe533d229c589d56`, fence 2, directory in original slot03 | Prior key `e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a`, fence 2, directory in benchmark slot03 |

Original quarantined IDs remain `1eWty-3Zr4RGfpA4eqpSTiVSNYZwrzUiXbG0kQ7yybMU`
and `1oMIBoMqDp5od5hwEoAqlsvs8kK7svCsYcd0VEHb8Oxw`. Both unresolved cases report
blind_retry_blocked and private_reclaim_blocked. The exact JSON/ACL readbacks and all
artifact hashes remain in the archived pack; no retained file counts as available new capacity.

Only evidenced technical tradeoffs remain for contract review:

1. **Coordinator availability versus scope:** proposed conservative account serialization and
   durable SQL budget are simplest to prove with the three current writers. Per-destination
   concurrent exports could improve latency but need quota/fairness evidence not supplied by S6.
   Recommend serialized account jobs initially; no fixed schedule is proposed.
2. **Legacy snapshot storage:** new-source facts already reload from immutable SQL; legacy
   `transfer_and_sort` reads mutable SQL per tab. Recommend a registered durable spool with
   SQL manifest/owner, plus worker affinity if storage is not shared. Provisioning topology is
   a later environment choice; SQL blobs would increase database/storage and migration scope.
3. **Pool reserve:** recommend one quarantined generation and one spare generation (nine files
   for P=2); more quarantine needs additional approved capacity or blocks progress. S6 proves
   refusal, not a production upper bound. Retained uncertain files never count as free reserve.

These are engineering recommendations for review, not repeated S7-D01–D09 questions.
No unrelated reliability WS1 rewrite is required by this contract. Required extraction of
legacy export snapshot/admission/pacing is a bounded integration dependency, not deferred debt.
