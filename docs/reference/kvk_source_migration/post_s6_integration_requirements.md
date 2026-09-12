# KVK Source Migration — post-S6 integration requirements

## S7 planning delivery — 2026-09-12

Chris Watts approved S7 documentation/read-only work in the task starter. The
[implementation-ready contract and C01–C65/indirect consumer matrix](integration_contract_and_consumer_matrix.md)
and [exact Bot/SQL/test manifests](integration_implementation_manifests.md) are delivered
for review. Stop at that review; S8–S11 implementation and all operations remain
separately authorized. S7-D01–D09 are settled; no predecessor evidence is reopened.
Latest S7 status supersedes earlier planning-approval-pending wording only.


2026-09-12. Operator decisions are settled requirements; the additional runtime
implementation and live operations are not yet authorized. This amendment governs
the next slices and supersedes conflicting earlier partial-publication, switching
and spreadsheet-retention recommendations. Earlier test results remain historical.

## 1. Delivered baseline and release boundary

S1–S5B remain accepted. S6's documentation and synthetic rehearsal are delivered,
operator accepted and merged in mirror #272 and production-repository #579. This
does not close the feature or activate public V2 readers. See the exact revisions
and authority distinctions in [handoff evidence](post_s6_handoff_log.md).

The current code can accept source inputs, calculate and select publications,
export versioned generations and reconcile deliveries. It does not implement the
ordinary public routing switch identified in PR #272. Matched-pair gating,
immutable season source choice, shared export admission, manual recovery and
safe cross-season file rollover require an explicit implementation assessment.
Do not equate existing component APIs with complete user-facing integration.

## 2. Settled operator decisions

| ID | Requirement | Consequence and implementation obligation |
|---|---|---|
| S7-D01 | Exactly one data source per KVK: legacy or new importer, fixed for the whole KVK | Record the choice durably before the season starts; reject conflicting source admission/serving. Do not infer a source change from the most recently uploaded file. Separate source identity from serving enabled/disabled. |
| S7-D02 | All affected KVK outputs use that season's chosen source | Inventory ordinary commands, reports, cards, exports, caches, diagnostics and scheduled readers. No diagnostic-only completion claim. Source-independent daily systems retain their existing contracts and claim ownership; every exclusion needs evidence, not a silent omission. |
| S7-D03 | Player and kingdom/camp data are available together; wait for a matched pair | Validate/accept each stream independently but publish a new public update and enqueue its export only when the intended pair is complete and compatible. Either upload order must work. Arrival adjacency is not identity. |
| S7-D04 | A corrected file may reuse its unchanged counterpart | Require explicit confirmation of that counterpart's continuing validity for the same KVK/reporting context; record exact revision IDs and actor. No synthetic reupload or mutation of the unchanged input. |
| S7-D05 | Export after each eligible completed import update | Normal frequency 1–2/day, peak 2–3/day; no fixed duration cap. This supersedes a proposal for fixed-time scheduled exports. Duplicate/semantic reuploads do not create a new update/export. |
| S7-D06 | Finish the running export; then process the latest complete pending update | Preserve all accepted input/publication history. Coalesce superseded pending export requests only; never alter an in-flight generation. Pending intent and admission must survive restart. |
| S7-D07 | Protect against conflicts among new-source, all-KVK and scan-data importer/export tasks | Inventory shared provider/account/destination/SQL resources and all manual/automatic callers across processes. Apply common enforceable admission and pacing where resources conflict; an S6 process-local lock alone is insufficient. |
| S7-D08 | Output files are active for a KVK and reusable for the next; no spreadsheet archive is required | Define explicit end-of-KVK rollover, drain/fence old jobs, prevent late old-season writes, and remove stale tabs/content safely. Reuse files only after proving they are no longer current or uncertain. Input/publication/audit history is retained separately. |
| S7-D09 | Add a KVK export-only operator capability | Use the selected complete publication without reimport/recalculation. Integrate with the same durable queue, authorization, deduplication, status and reconciliation as automatic exports. A confirmed export no-op and an explicit damaged-output rebuild are distinct operations. |

These choices need no repeated product approval during S7. Technical designs,
exact file/test/SQL manifests and live operational targets still require review.
An export-only command name and its registration are not implemented by this file.

## 3. Matched update semantics and edge cases

Design an explicit update identity and revision association. It must bind KVK,
source, period/report family, intended coverage/as-of context, exact player
observation revisions, aggregate revision, configuration and roster. Do not invent
an aggregate player ScanID or require identical timestamps for independently
authoritative reports. Kingdom and camp tabs form their validated aggregate report.
An overall aggregate remains its separate supplied report, never a sum of fights.

The first valid stream may be stored privately, but ordinary public reads and
automatic exports retain the last complete eligible publication until the pair is
ready. With no eligible previous publication, show waiting/unavailable. If desired
endpoint/config changes make an older result stale, label it as previous/pending;
do not misrepresent it as the current final. Diagnostics may inspect incomplete
inputs privately with explicit stream state. Field-level missing metrics remain
unavailable: a complete pair is not proof that every metric exists.

Baseline onboarding, no-fight periods, overall reports, and configuration-only
updates must receive explicit transition rules in S7. Matched-pair admission must
not deadlock B0 setup or require fabricated no-fight aggregates. Every normal
combat update requires its matched pair; exceptions follow the existing approved
domain contracts rather than becoming an undocumented bypass.

Preserve B0 eligibility/kingdom attribution, UTC scan start, exact per-metric
endpoints and semantic re-export deduplication. Interim 11−10 then 12−10; final
13−10; authorized EndScanID 14 itself permits replacement 14−10 without a separate
correction command. Endpoint changes do not authorize an aggregate correction.
Where an existing aggregate remains valid, associate that exact accepted revision
under the approved counterpart-reuse rule; specify its confirmation boundary
without introducing a second player-endpoint correction command.

## 4. Export and rollover design obligations

An import must commit its accepted state and durable export intent before a worker
starts external writes. Do not hold SQL transaction locks over a roughly 38-minute
Google export. Each export pins an immutable complete generation. If newer complete
updates arrive during it, finish the running export and select the latest eligible
pending update next; retain skipped-publication history and explain that it was not
exported. A failed/uncertain current attempt must reach a permitted recovery state
before the destination can advance; no lease timeout or blind replay proves safety.

Common admission must include automatic triggers and manual exports across the
three relevant consumers. Separate conflicting destination writes from account-wide
request budgets. Specify fairness, cancellation, worker fencing, restart discovery,
late completions and consistent lock ordering. Evidence should establish which
imports can safely proceed during export using immutable snapshots rather than
unnecessarily serializing unrelated SQL work.

Reuse a bounded file pool with safe staging/current generations during the active
KVK; dropping the archival requirement does not make in-place partial publication
safe. Size active + staging + recovery quarantine + reserve from the actual largest
generation. At rollover, fence the old season, retain audit references and prove no
old writer can act before repurposing files. Keep prior receipts honest about a
retired remote representation. No automatic deletion of input/publication history.

The stable user-facing entry point and individual part-link lifetime must be stated
in the design. Historical spreadsheet links may show the next KVK after approved
rollover; no old spreadsheet archive is promised. Existing uncertain rehearsal
outputs remain evidence until their disposition is separately authorized.

## 5. Observed reuse opportunities and limitations

Read-only observations at bot `a2f148fa9bd4fb367fd46d0500a768c14fee915b`:

| Existing path | Relevance |
|---|---|
| `upload_routes/kvk_all_route.py`; `kvk_all_importer.py` | Legacy successful-import path schedules auto-export when enabled. It does not prove a shared lock across all consumers. |
| `gsheet_module.py` | Legacy exports open named spreadsheets and clear/write worksheets; additional outputs open existing files or create missing ones. Empty outputs can be skipped, so complete rollover cleanup is not established. |
| `commands/admin_cmds.py` | General run_gsheets_export exists; it is not proof of a safe new-source KVK export/rebuild operation. |
| `kvk/services/new_source_publication_service.py` | Existing publication supports independent stream states, including absent aggregates; public matched-pair gating is a new integration requirement. |
| `kvk/services/new_source_recovery_service.py` | Current generation delivery/recovery can be reused only after compatibility with matched pairs and queue ownership is demonstrated. |
| `kvk/dal/new_source_config_dal.py`; `kvk/dal/new_source_admin_dal.py`; `stats_alerts/embeds/kvk.py` | Routing row lock/onboarding and explicit diagnostic V2 selection do not switch ordinary readers. |

SQL at `44afa315dd6cbfe9fec101f2a39a62e534f5b583`: SourceRouting stores Enabled,
RoutingVersion, SourceKey and approval/capability fields; its source constraint is
snapshot_report_v1. SourceDelivery stores per-publication/destination state,
owner/fence and nvarchar(1024) receipt. These are not demonstrated complete schemas
for immutable legacy/new season choice, paired updates or shared queue admission.
S7 must decide reuse/extensions against authoritative SQL, not guess new columns.

## 6. Remaining decisions are engineering outputs

S7 must produce the exhaustive consumer/caller matrix, source-choice lifecycle,
pair/correction state machine, durable queue and rollover model, command permission
and recovery UX, SQL delta options, exact implementation/test/security manifests
and credible effort estimates per slice. Bring back only a demonstrated business
tradeoff or incompatible domain exception; do not re-ask the nine settled decisions.

See the amended [implementation plan](phase_2_implementation_plan.md) and the
[next S7 task pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md).
