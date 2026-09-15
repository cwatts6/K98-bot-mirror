# KVK Source Migration — post-S6 integration requirements

## Current status — S10B merged and locally pulled; S10C scope next, 2026-09-14

S10B mirror #278 and production #585 are merged; local pulls are complete.
**No changes have been pulled to the bot machine.** Repository delivery is not deployment or activation.
Bot main/origin main: `8ae66da6e12b53781c5df0d46a8ee79314cecead`; production/main:
`40c2e48111ebbe44d58d71269dea63a6dd9388b7`. SQL #85 remains accepted at
`3776dfa6b0892a8800d236fdf111c4d2f93c3813`; no S10B SQL delta.
Final retained offline validation: **4,433 passed / 66 skipped**; review fixes are in both repositories.
See [S10B closeout and exact S10C documentation manifest](s10b_closeout_and_s10c_handoff.md) for exact delivery/content proof and evidence boundaries.

Next: **S10C Legacy and Scan Export Adapters, initial review/scope only**: [task pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10C%20Legacy%20and%20Scan%20Export%20Adapters.md) and [starter](../../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10C%20Legacy%20and%20Scan%20Export%20Adapters.md).
Completed S10B pack/starter are archived; retained runbooks, databases, files and evidence stay available.
Every pending Bot document and both S10B archive move sides must accompany the eventual S10C Bot implementation PR.
Verify exact filename AND previous_filename or exact merged/absent-at-base proof; counts alone are insufficient.
No standalone documentation PR or repository mixing. The two pending SQL documents stay in the next authorized SQL PR.

Preserve S6-OPS01/PERF01/CAP01 and both uncertain publications. S8A six scripts, S8B 50-case/actual-restore
and offline-runner evidence, and S8C seven local checks remain distinct. No new live Discord evidence is claimed.
This closeout authorizes no S10C implementation, Git publication, SQL/provider/Discord execution, real imports/exports,
bot-machine pull/restart/deployment, activation, predecessor rerun or automatic new task.
Earlier dated statuses and approvals below are historical; settled acceptance and grouping stay settled.

## Historical S10A closeout status — 2026-09-14

S10A SQL #85 is merged and locally pulled at `3776dfa6b0892a8800d236fdf111c4d2f93c3813`.
All five disposable fixture modes, 76 unique cases in install and constraints, direct apply/rerun,
backup/actual restore and final preservation checks passed; final CI passed. Results accepted.
No changes have been pulled to the bot machine; no production SQL deployment or activation.
S9B mirror #277, production #584 and SQL #84 remain delivered. Bot comparison anchors are unchanged.

Next: **S10B Shared Export Coordination Worker and Durable Budget, initial review/scope only**.
Use the [S10B task pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10B%20Shared%20Export%20Coordination%20Worker%20and%20Durable%20Budget.md) and [starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10B%20Shared%20Export%20Coordination%20Worker%20and%20Durable%20Budget.md).
The [S10A closeout and exact carry-forward manifest](s10a_implementation_and_s10b_handoff.md) controls delivery.
Completed S10A and S9B packs/starters are archived; retained execution/operator evidence stays available.
Every pending Bot document and archive destination belongs in the eventual S10B implementation PR.
Check exact filename AND previous_filename, with explicit absent-at-base proof for never-committed
S10A source paths. No standalone documentation PR or repository mixing; grouping is settled.
Both mandatory SQL delivery documents were included and merged in SQL #85.

Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and all retained databases/files.
S8B accepted smoke/50-case and actual-restore evidence remains distinct from offline runner history,
S8A six-script evidence and S8C seven local checks; S8C is not live Discord acceptance.
No S10B implementation, Git publication, runtime execution, deployment, activation or automatic new task
is authorized by this closeout. SourceRouting.Enabled alone never enables source activation.
Earlier dated checkpoints below are historical.


## Historical S8B closeout status — 2026-09-13

S8B is complete, operator accepted, successfully smoke tested and delivered through merged
production #581 and SQL #81. Local pulls are complete; **no changes have been pulled to the
bot machine**. Mirror #274 is closed without a merge record; its delivered content is verified
in synchronized mirror main. See the [canonical closeout and exact carry-forward manifest](s8b_closeout_and_s8c_handoff.md)
for merge/content proof, final offline tests and the distinct historical disposable/runner evidence.
No fresh post-merge SQL or bot-machine smoke, deployment or activation is claimed.

**Next: S8C Intake and Admin Pairing UX in a new chat, initial review/scope only.**
Use the [S8C pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8C%20Intake%20and%20Admin%20Pairing%20UX.md) and [starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S8C%20Intake%20and%20Admin%20Pairing%20UX.md).
The eventual separately authorized S8C Bot PR must include all closeout documentation and both
sides of both S8B archive moves, checking actual filename and previous_filename; SQL delivery-log
carry-forward is separate. S7 decisions and predecessor acceptance remain settled. S9 public
routing and S10 export coordination remain later work; SourceRouting.Enabled alone is insufficient.
Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and all retained databases/files.
Earlier dated scope/approval/next-slice statements are historical and do not reopen accepted work.

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
[next S7 task pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md).
