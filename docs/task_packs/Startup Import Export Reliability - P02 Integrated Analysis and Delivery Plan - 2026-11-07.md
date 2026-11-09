> **9 November 2026 qualification update:** Phase 1 coordinated SQL, shared latest names, exact numeric/export handling and selected recovery-observer concurrency passed independent full-size isolated verification. The current exports have 49,468 rows across 14 outputs; existing tied-rank and date-window differences are explicitly source-verified in the Phase 1 implementation record. Remaining D2-D4 work, whole-programme D5, release readiness and production/provider acceptance remain open.

> **Phase 1 approved, 7 November 2026:** SQL, names, numeric types and exact export implementation and isolated tests are authorized. See [Phase 1 implementation](Startup%20Import%20Export%20Reliability%20-%20P02%20Phase%201%20Implementation%20-%202026-11-07.md). Remaining contention/maintenance work and production deployment remain separate. Earlier plan-approval holds below are historical for Phase 1 only.

# P02 integrated analysis and delivery plan

Date: 7 November 2026. Owner: K98 Bot and SQL engineering; operational decisions
and production approval: Chris Watts.

## Current answer and scope

**P02 is not finished.** P02.1 is a locally qualified first slice, not the whole
package. The original contention analysis, the SQL cost dependency discovered in
its rehearsal, and the numeric-type investigation are now reconciled in this one
delivery plan. Source review and delivery design cover every original P02 finding
family. The retained-copy numeric analysis is complete and the operator confirms
no known external consumers. Fresh installed-job/use verification remains a release
readiness obligation. Phase 1 cost, output and selected observer-concurrency qualification passed on 9 November; remaining D5 qualification is still open.

The intended result is that checking status does not obstruct useful work, imports
avoid unnecessary SQL rewrites, exact counts survive reporting/export, maintenance
does not mislabel committed work, and real contention has usable ownership evidence.
The next normal import/export must preserve unfinished prior work rather than repeat
already committed stages. This is one solution delivered in reviewable slices,
with a combined acceptance gate; completing the summary rewrite alone cannot close P02.

This document is the current integrated delivery index under the existing
[P02 handover](Startup%20Import%20Export%20Reliability%20-%20P02%20Handover%20and%20Scope%20-%202026-11-06.md).
The [programme principles](Startup%20Import%20Export%20Reliability%20-%20Programme%20Principles%20-%202026-11-06.md),
[scope](Startup%20Import%20Export%20Reliability%20-%20Scope%20-%202026-11-02.md),
[tracker](Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md)
and [tracing](Startup%20Import%20Export%20Reliability%20-%20Tracing%20-%202026-11-02.md)
remain authoritative programme records. Earlier status paragraphs in those records
are history where superseded by this dated reconciliation.

Analysis and plan preparation are authorized. Existing local P02.1/name/summary
implementation approvals remain in force. This plan does not imply approval to
implement the newly specified datatype, maintenance, remaining-observer or legacy
changes, or to publish, deploy, recover production work or contact providers.

## Evidence actually available

| Area | Verified result | What it does not establish |
| --- | --- | --- |
| P02.1 recovery observers | Dedicated short SNAPSHOT reads replace producer-style guards in the mapped recovery families; actions retain current ownership/version checks. 516 focused offline and 122 native tests were recorded across completed runs. | Other observers and full P02 are not covered by that count. |
| Bot regression/release preparation | Full run: 12,022 passed, 15 expected-count failures, 1,125 skipped; all 15 corrected cases passed in an 870-test focused rerun. Bot Changes scan completed without findings. Exact updater transition/package prepared. | This is combined evidence, not one all-green full run or installed release. One unrelated native monitor-fingerprint assertion remains tracked. |
| Full SQL rehearsal | Both OFF/ON arms imported 415 rows and completed reports. 13/14 output sets matched; name equivalence selected different visible spellings. OFF 82.516 s; ON 144.781 s. | One pair is not a median study or proof snapshot alone caused the time difference. No provider delivery occurred. |
| Failed resource gate | ON observed version-store peak 1,843,712 KiB, above the unchanged 524,288 KiB ceiling. | Subsequent version cleanup does not erase this failed gate. |
| Deterministic names | Source/migration and 33 isolated SQL tests passed. | Full restored-history equality and release signing/source integration remain open. |
| Summary rewrite | All nine entry points implemented; 30 native tests passed across 42 output/state tables; SQL Changes review completed without findings. | Candidate full-scale cost, concurrent observers and production compatibility remain unqualified. |
| Summary cost | Retained statement evidence: historical-cache delete/insert work 118.841 s of 127.589 s, with 10,778,936 row actions. | This is target cost, not measured candidate savings or per-statement version-store bytes. |
| Numeric types | Each saved OFF/ON report has 2,452 rows, 49 numeric columns, 120,148 whole-number values; 67 exceed int range. 112/184 retained compiled summary plans contain float conversions. | Final exports do not certify all underlying history/caches, original precision, consumer metadata or new performance. |
| Restored schema reconciliation | All 75 target tables and 325 numeric columns match the retained schema inventory; 167 index/heap metadata rows are available. | Metadata is now supplemented by the completed value profile below; it does not establish installed production use. |
| Underlying numeric values | All 75 tables / 325 columns checked: 43,679,892 non-null numeric cells, no fractions, bigint conversion failures, float round-trip failures or identifier conversion collisions. 68,424 cells across 18 columns exceed int range. | Counts overlap across derived tables; exact stored-value conversion does not recover any historical precision already lost or establish future ranges. |
| Known consumers | Operator confirms no known external use. Restored matching job-step inventory is empty. | Restored msdb is not fresh production scheduling evidence; verify installed bindings before retirement/deployment. |
| Numeric export boundary | Synthetic nullable-integer DataFrame reproduces precision loss above 2^53; object/nullable-integer construction preserves the tested values. | Retained reports are below that boundary; no current corruption or complete provider fidelity is claimed. |
| Six incidents | 7 November 08:13 UTC inventory: five records share one retained pipeline; the sixth is an older cancellation projection. Import/player work is captured; config unconfirmed, target-cache/export not started. | Six rows are not six running jobs. No present recovery eligibility, all-account absence of blockers, or capture-file validity follows. |

Private evidence is in the root Bot workspace `.codex_artifacts/p021/`:
`QUALIFICATION-2026-11-07.md`, `summary-local-qualification.json`,
`summary-security-completion.json`, `summary-detail-review.json`,
`summary-numeric-plan-analysis.json`, `summary-retained-numeric-profile.json`,
`summary-numeric-export-analysis.json`, `p02-complete-analysis-review.json`,
`P02-complete-analysis-7173dab1d55d4fcf89be388552c6f1df.json`, and
`INCIDENT-REVIEW-2026-11-07.md`.
The original failures and invalid auxiliary decoding test remain preserved.

## Original P02 coverage and final design decisions

| Original finding / obligation | Source-confirmed problem and chosen direction | Delivery / closure evidence |
| --- | --- | --- |
| F01 / F26: factories and budgets | Dedicated SQL uses 5 s login, 15 s query, 1 s row-lock wait; producer overrides differ. Profile `_connect` catches helper execution failure and tries the legacy factory. Select the factory once by operation/context; remove execution-failure fallback; preserve original exception and cleanup facts. Define per-operation budgets, not a global increase. | D2. Test factory selection and all equivalent callers, native lock/query timeout, lost acknowledgement, cancellation/drain and actual player-report statement policy. |
| F03 / F09: observers and global/account/resource guards | P02.1 removes the producer guard from mapped recovery previews. Unowned-hold inspection and other account/resource/preparation/queue inspections still need disposition. Keep mutation locks and current-row checks; extend the shared passive snapshot contract only to complete read-only paths. | D2. Every original census path classified; observer-first and producer-first cases, stale previews, foreign owners, no writer refusal caused by observer ownership. |
| Resource/holder evidence and lock ordering | Current 51421 records requester SPID/return code/timing and explicitly unknown holder. This is incomplete holder attribution. Preserve resource namespaces and order; add bounded refusal-triggered holder evidence with observation time and provenance, never requester-as-holder inference. | D2. Controlled native holder/requester sessions must be distinguished. Use least-privilege reviewed diagnostic access; permission denial/race becomes explicit unavailable. Do not log every poll or grant broad server rights casually. |
| F12: authority scheduling | Pipe server serially dispatches authenticated requests; observations can perform SQL/private I/O before the next request is served. Keep single authority for mutations. Give exact allowlisted read-only observations bounded separate execution/admission so slow inspection cannot monopolize dispatch; retain peer authentication and physical drain. | D2. Test observation saturation, lost replies, mutation progress, unauthorized selectors, reconnect and shutdown. Do not parallelize arbitrary mutation dispatch. |
| F14: ordinary source reads | `resolve_season_read` takes exclusive season ownership and update locks for metadata. Read a consistent committed selection/route tuple in a short passive transaction; validate sealed relationships, then read immutable payload outside it. Mutation-time selection/config validation stays locked. | D2. Legacy/new-source choices, changed selection, both arrival orders, partial tuples and disabled snapshot must fail truthfully. Public routing remains permission-scoped. |
| F16 / F18 / F21 / F22: six maintenance stages | Business data/receipt atomicity is essential; optimizer upkeep, backup waiting and optional timing logs are not the same outcome. Keep required shape/index/identity checks and admission headroom. Move eligible post-success upkeep behind required commit/capture and producer guard release, under existing separately owned maintenance machinery. | D3, six-stage matrix below. Real child procedures and restart/failure cases, not stub-only success. Defer expensive maintenance only with a recorded due/outcome policy and capacity gates. |
| F20: shared file ownership | `acquire_lock` skips unlink after a raised body and wraps yield in acquisition exception handling. Separate acquisition from body; release only the lock this operation created in finally, preserving first failure. Verify immutable generation outside long writer-lock parsing where safe. | D3. Cache startup, ordinary/guided publication, Ark team/state and tracked-view wrapper all tested; body FileExistsError, cancellation, replacement/foreign sentinel and close failures included. Never delete a lock merely because it is old. |
| F31: legacy/manual execution | `UPDATE_ALL` invokes Rally; child deletes input before parent commit and prints failures. Installed use is not yet proven. Include the path in qualification by default; retire only on verified no-use plus explicit retirement approval. Otherwise add claim/identity, error propagation and post-commit archive semantics. | D4. Installed binding inventory plus parent rollback/file preservation, child error and direct invocation tests. No execution of legacy TEST or Rally merely to discover use. |
| SQL indexes/statistics/isolation | Keep RCSI off. Explicit SNAPSHOT remains preferred only if full cost/headroom passes. No blanket index addition or stats changes. ActivePreparationID index is a measured candidate, not a dependency assumed beneficial. | D1/D3/D5. Exact plans, read/write/maintenance cost and observer concurrency. If unchanged limits fail, revisit isolation architecture, not raise limits. |
| SQL polling versus signalling | Select short bounded passive reads using existing lifecycle evidence. SQL notifications/new outbox introduce subscription, writer, retention, recovery and deployment work not justified by current evidence. No push mechanism is required for this plan. | D2/D5. Measure observation scheduling/cost. Reopen signalling only if a measured unmet budget justifies the full durable cursor/ack/reconnect/duplicate/cleanup contract. Signals never authorize mutation. |
| Six-incident readiness | Preserve committed captures; verify exact failed config attempt/closure and original pipeline-export intent before using supported continuation. | D6 dependency on P03/P04; three unfinished stages, no original-upload replay and no cosmetic zero-incident gate. |

This completes the original source-level scope reconciliation. It does not turn
unmeasured runtime hypotheses (authority starvation, index benefit, maintenance
frequency or actual historical holder) into proved production causes.

For D2 implementation, keep the existing single mutation dispatcher and propose
one independently drained observation worker with at most one waiting observation;
further observations receive an explicit busy result. This is a new bounded
observation lane, not an increase to business-worker capacity or SQL time limits.
Authenticate each original pipe peer before admission and bind its reply to that
request; reject any selector that may mutate, reconcile, seal or invoke a provider.
The accept loop must remain responsive while an admitted observation executes.
Queue/execute/close phases and shutdown ownership receive separate tests. If a
selector cannot prove read-only behavior, it stays on the authoritative path.

The initial operation-policy manifest preserves the existing 5 s dedicated login,
15 s default execution, 1 s metadata lock budget, 15 s coordination total horizon,
and zero-wait global producer admission. Recovery snapshot statements retain 3 s
and zero row-lock wait. Existing explicit import/maintenance overrides remain
operation-specific. The player-report mismatch must be resolved by an explicit
compatible caller/SQL wait policy, initially within existing limits; a larger
execution budget requires measured justification and an explicit scope decision.
Connection retries cannot switch principal or replay a business operation. Full
physical cleanup may outlive the observer deadline and must retain its ownership.

## One SQL and numeric solution

Keep the existing endpoint rewrite as the reference candidate. It removes 32
persistent history-cache rewrites while retaining shared history, direct calls,
latest/delta/final results, watermark and transaction semantics. Raw history is
preserved. The original summary parent is unchanged in this qualified reference.

The numeric candidate will extend that reference across the same calculation
chain, not just change temporary columns. Source truth is the SQL repository.
Inventory: 75 tables comprising source, 42 output/state tables and 32 retained
history/rollback tables. The 42 output/state tables contain 139 float columns,
including 49 in SUMMARY_CHANGE_EXPORT. The nine children include HEALEDSUMMARY_PROC_OPT.

Selected proposed contract for plan approval:

- IDs, whole-number counts and representable signed deltas use bigint; bounded
  ranks/scans use int. Existing unrelated fractional fields/weights stay out.
- Decimal arithmetic handles averages before explicit whole-number rounding.
  Recommended behavior is consistent rounding to nearest whole number, halfway
  away from zero, across metrics. This deliberately corrects current bigint AVG
  truncation; enumerate changed aggregate rows against the reference. No silent
  rounding change or broad comparison tolerance is permitted.
- Compute potentially overflowing differences/sums in a checked exact domain,
  validate bigint bounds at the output boundary, and roll back on invalid input.
  Preserve NULL and negative-delta meaning; do not coerce invalid data to zero.
- Construct exact Python values before pandas can infer floats. Cover immutable
  capture and direct compatibility routes; retain existing snapshot bytes and
  their digests for already queued work. A schema change must not reserialize an
  old committed capture to make it look current.
- Keep current-range export cells numeric and current blank/display behavior.
  Values outside the provider's exact numeric range require an explicit lossless
  text representation and formula/consumer compatibility evidence; do not silently
  round them. IDs and arithmetic counts need separate column policies.
  Sheets numeric cells are doubles, not a bigint transport guarantee
  ([Google ExtendedValue](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/other#ExtendedValue)).

The endpoint rewrite and type alignment are separate comparison arms within the
same solution. This makes additional benefit measurable and expected semantic
changes reviewable. Integer alignment is justified by exactness and consistency;
float and bigint both use eight bytes, so no automatic storage saving is promised.

External consumers must be settled before retiring refresh of old caches. Broad
SELECT grants mean static-reference absence is insufficient. Recommended release
is one that has explicit consumer clearance; if an actual consumer exists, port
it to the supported endpoint contract or retain a scoped compatibility output and
requalify its cost. Do not hide this behind a permanently stale table. The legacy
TEST routine's destructive behavior requires a named operational disposition.

SQL detail: `C:/K98-bot-SQL-Server/docs/p021-summary-implementation.md`,
`docs/p021-summary-numeric-type-review.md`, `docs/p021-deterministic-names.md` and
`docs/p02-integrated-sql-delivery-plan.md` in the SQL repository.

## All six maintenance stages

| Stage | Actual surface | Keep in critical outcome | Move/qualify separately |
| --- | --- | --- | --- |
| Import Phase A | UPDATE_ALL2, IMPORT_STAGING_PROC_CORE | Claim/digest, typed validation, scan allocation, history writes, exact import receipt and archive integrity | Sampled statistics, conditional KS4 index maintenance; establish plan/headroom effects before moving |
| Configuration | sp_TARGETS_MASTER -> CREATE_DELTA_TABLES | Atomic configuration/delta publication, mutex ordering, shape/identity and completion | Conditional stats/rebuild/reorganize and DeltaProcessingLog; optional log failure cannot undo required business result |
| Player report | SP_Stats_for_Upload | Consistent report generation and provenance/capture | STATS_FOR_UPLOAD FULLSCAN and inherited statement budget mismatch |
| KVK output | sp_ExcelOutput_ByKVK and index/view children | Required schema/unique indexes, output/view publication and exact receipt | FULLSCAN and nonessential upkeep; retain required indexes even if they cost time |
| Final stats reports | usp_S11CompleteStatsReportsCore | Stage-specific completion and required outputs | CHECKPOINT, dashboard stats, backup signal/waits: distinguish pre-admission headroom from optional post-success maintenance |
| Explicit post-import | Python log management/maintenance_worker, usp_update_stats | Truthful committed outcome, captured output and retained physical worker ownership | Backup processing, waits and intentional sp_updatestats under separately owned maintenance; bounded backlog/headroom controls |

A deferred maintenance failure records maintenance pending/failed and can prevent
new work if capacity is unsafe. It must not rewrite a committed import as failed
or authorize replay. Durable maintenance ownership uses existing mechanisms where
they satisfy the exact task; any missing due/claim/completion record is part of D3,
not an unowned fire-and-forget task or general new scheduling framework.

## Delivery sequence and accountable outputs

| Slice | Scope / owner | Dependencies | Deliverable and exit |
| --- | --- | --- | --- |
| D0: close analysis inputs | Bot/SQL analysis + operator evidence | Existing retained VM and source | Read-only 75-table profile, retained bindings, exact outstanding evidence disposition. External production consumers/enablement are explicit release inputs, not assumed absent. |
| D1: SQL efficiency and exact numeric contracts | SQL + export DAL owner | D0 value/schema findings; numeric/rounding plan approval | Keep name fix/endpoint baseline, implement coordinated numeric/output change, indexes/migration/rollback and export precision cases. Local exact parity except enumerated approved aggregate differences. |
| D2: complete observer and connection policy | Bot coordination/DAL + SQL diagnostics owner | Existing P02.1; D1 cost qualification before enabling SNAPSHOT in production | Full caller/resource/budget matrix; factory policy, remaining passive reads, bounded observation scheduling and actual-holder diagnostics. Preserve guards/CAS for mutations. |
| D3: ownership and maintenance | Bot shared-helper + SQL owners | D2 lifecycle/budget contract; D1 baseline | F20 shared cleanup plus all six maintenance boundaries; exact commit/capture retained, background maintenance owned and restart-safe. |
| D4: legacy and release compatibility | SQL + operator/release owner | Current installed binding evidence | Qualified active legacy paths or explicit approved retirement; signing/source-pin/startup/updater compatibility for final combined files. |
| D5: integrated isolated qualification | Bot + SQL test owner | D1-D4 final candidate | Full import/report/output comparison, all observers and true child maintenance, balanced cost/concurrency/fault/restart tests; unchanged limits pass. |
| D6: release and retained-work readiness | Release owner + P03/P04 owners + operator | D5, current host/capture/claim evidence, separate release/action approval | Exact installation/rollback package; supported unfinished-stage recovery plan; no replay of committed import/player results. |
| D7: exercised acceptance and handoff | Operator + P05 acceptance owner | Approved release and exact actions | Installed contracts, original retained workflow disposition, required provider receipt and normal whole-flow acceptance. Carry remaining natural observations/P03/P04/P05 explicitly. |

D2/D3 source implementation can be developed after plan approval while D1 native
qualification proceeds, but changes remain separately reviewable and final combined
qualification is mandatory. Do not create a new chat, merge or deploy merely because
the plan contains these phases. The goal is a single coherent release decision,
not indefinite deferral of original P02 work into P05.

## Performance, correctness and non-interference acceptance

Keep all declared limits unchanged:

- Same original backup, identical 415-row canonical CSV, same exact SQL adaptations,
  deterministic name fix in every comparison arm, driver/runtime/memory/MAXDOP and
  maintenance conditions. Preserve cold/warm and failed runs; no relabelling.
- Warmup then at least five measured balanced OFF/ON pairs. Overall median ON
  ceiling = OFF x 1.20 + 1,000 ms; each recorded report stage = OFF x 1.20 + 250 ms.
  Compare endpoint-only and numeric candidates separately before the final pair.
- Actual candidate short observer helper retains its three-second statement budget;
  include both arrival orders and one bounded 30-second metadata snapshot. No
  observer-owned producer guard, unexpected writer refusal or cleanup uncertainty.
- Observed version-store peak below 512 MiB, disk reserve at least 8 GiB, sampled
  log usage below 70 percent, approved host free-memory prerequisite 8 GiB. The
  earlier 128 MiB synthetic screen is not a replacement for the full-workload gate.
- All 14 output sets checked, plus detailed summary tables/state and approved
  numeric metadata/rounding deltas. No discarded columns or broad float tolerances.
- The rehearsal's 1,800-second statement cap is a test bound, not a proposed Bot
  timeout increase. Retain distinct login/admission/execute/fetch/commit/cleanup
  budgets. New worker scheduling budgets must be specified before measurements;
  observation deadlines never prove physical cancellation.

Failure coverage: stale/foreign owners, known holder versus requester, missing
snapshot prerequisite, schema locks, cancellation before/after native entry,
rollback/commit/close uncertainty, lost acknowledgements, restart and alternate
factories; real maintenance child failures; cache body failures and successor
ownership; overflow/NULL/negative/halfway numeric cases; queued old payloads,
readonly permissions and diagnostic saturation/failure. Preserve first failure
and exact operation/attempt/parent/resource identity throughout P01 evidence.

## Release and rollback contract

Source qualification, host readiness, installation and exercised acceptance are
four separate verdicts. Create exact Bot and SQL Changes review targets for final
runtime patches; Deep off. The existing completed scans do not cover future code.

Build versioned migration/profile/source-pin changes for the final nine summaries,
parent/type changes and names; retain historical expected hashes and signing
contracts. The current local summary install/rollback scripts intentionally accept
only disposable K98DEV fixtures and cannot be used for VM or production deployment.
Resolve the known name source-byte drift in historical permission checks by a new
reviewed release contract, not by weakening old hashes. Enforce explicit target
selection for the actual release installer; legacy production defaults are inadequate.

Pre-drain on the real host: exact SQL settings/permission/signature and all three
protected startup contracts, installed updater/source, changed paths and ancestors,
ownership/ACL, retained processes/sessions/captures and headroom. SQL and Bot rollout
order must allow the predecessor until coordinated switchover, or require a reviewed
drained window if the datatype metadata is incompatible. Enable no production
SNAPSHOT prerequisite until its cost gate passes. One approved graceful restart
uses the protected updater and private main, never the mirror.

Rollback must restore a compatible Bot/SQL/profile set while preserving committed
new work and old payloads. Reverse type conversion must be proved lossless before
data has changed; bigint values outside exact float range make an automatic reverse
conversion unsafe. Use backup/forward correction and a recorded write boundary in
that case. Rebuilding legacy caches must use current authoritative history without
rewinding final report/state. Do not force-disconnect readers or force snapshot OFF;
drain and establish exact closure before any separately approved setting reversal.

## Related/deferred work reconciled

| Existing item | Decision |
| --- | --- |
| Task C Slice 14 SUMMARY_PROC | Brought forward by demonstrated P02.1 resource failure; endpoint rewrite delivered locally, numeric extension and full qualification owned by D1/D5 |
| Phase 3 retained ~190 legacy float key/scan entries | Take only this summary chain and its consumers into D1. Historical count is not a current production count. No blanket database conversion. |
| CFG-51421 / ProcConfig owner audit | Same F09 family, D2; no duplicate incident or blanket retry |
| Session-lock grant acknowledgement loss | Native D2/D5 qualification obligation; a closed client proxy alone does not prove server-session closure |
| ExportResource.ActivePreparationID index | Evaluate plans and write cost during D2/D5; add only with demonstrated benefit |
| Updater transition capacity and exact source pins | Verify actual final occupancy and historical preservation in D4; no general registry redesign assumed necessary |
| Native monitor fingerprint test | Existing unrelated assertion limitation; keep visible, do not weaken incident no-churn or count it as a new P02 regression |
| Broad import-core/stats orchestration decomposition | Remains deferred; D3 changes only proven maintenance/ownership boundaries |
| P01.6 snapshot decode/rebuild, Stats UI/SDK/ack, unrelated MGE/Ark domain performance | Stay after P01-P05 per operator choice unless new measured dependency is separately agreed. Shared F20 Ark caller testing is included without Ark redesign. |
| P03/P04 continuation, cancellation projection and notification history | Named D6/D7 dependencies; included in readiness, not falsely closed by P02 source tests |

For the brought-forward optimisation batch, qualitative engineering scores
(impact + frequency + risk reduction - effort, each 1-5) are: endpoint rewrite
5+5+4-3=11; summary type/export alignment 3+5+4-4=8; deterministic names
3+5+3-2=9. Frequencies describe core workflow reach, not measured incident rates.
These scores explain the bounded SQL batch; correctness and failed acceptance
gates take precedence. Other original P02 findings remain required regardless of score.

## Open evidence register and stop conditions

| ID | Evidence needed / responsible party | Current status and consequence |
| --- | --- | --- |
| A1 | Underlying 75-table numeric profile / isolated VM operator and SQL reviewer | Complete: successful read-only receipt reviewed, all 75 tables / 325 columns populated. Whole-number bigint contract is supported; plain int is unsafe for kill-point values. Preserve nulls, signed corrections and explicitly reviewed decimal averaging/rounding. |
| A2 | Actual external/ad hoc consumers and operational TEST/legacy use / operator + SQL owner | Source/dependency/grant analysis complete; operator reports no known external use; restored matching job inventory empty. D4 retains a fresh installed-binding check and explicit retirement decision. Continue preserving compatibility/legacy handling until then; no retirement inferred. |
| A3 | Final candidate cost, real-child faults, scheduling and concurrent-reader evidence / test owner | Phase 1 numerical/shared-name exports, five balanced OFF/ON pairs, observer-first, active-writer and 30-second recovery-metadata reader passed. Earlier failures remain preserved. D2-D4 and whole-programme D5 fault/restart/scheduling obligations remain open; raw-history snapshot DDL behavior is not qualified. |
| A4 | Exact incident request/capture/closure/account-wide predicates / P03/P04 and operator | Last bounded entry inventory reviewed; refresh at action time. Do not clear or continue from age/count alone. |
| A5 | Final release source/signing/updater/host custody / release owner | Versioned integration not yet delivered; no production-ready claim. |

Original P02 source/design reconciliation and the retained-copy numeric analysis
are complete. The operator's no-known-external-use response resolves the outstanding
planning question. A2's fresh installed-binding check belongs to D4 release readiness;
A3-A5 remain qualification, operational readiness and release obligations. This is
one complete delivery plan, not a declaration that P02 delivery or deployment passed.

## Validation of this planning change

Documentation and private read-only analysis helpers only; product runtime hashes
remain unchanged. Both new PowerShell collectors parse, and all 75 fixed aggregate
statements passed SQL Server PARSEONLY validation on verified local K98DEV. The
successful guest receipt collected all 75 profiles in 7.97 seconds, with no workload
or mutation. The first attempt stopped before numeric SQL because Windows PowerShell
5.1 wrapped the JSON array as one pipeline item; that receipt is preserved. Explicit
array materialization fixes the collector. The exact decoder/guard and both script
parsers passed on PowerShell 5.1 and 7.6, including rejection of four invalid counts. Collectors pin the retained host/VM/session/helper/query
bytes, require disconnected/read-only containment, bound each query to 20 seconds
and the profile loop to five minutes, and retain partial failure evidence locally.
No guest files, settings, services, workloads or provider state are changed.

Security routing: documentation-only formal Changes scan skipped for this planning
delta; private read-only collectors manually reviewed for exact target, fixed
queries, bounded outputs and no mutation. If promoted into a runtime/release patch,
they need the corresponding Changes review. Architecture/deferred/security
routing and test-selection gates passed; 16 introduced local links and whitespace checks passed. Generic Bot smoke-import/command-registration suggestions are skipped for this documentation-only change. Runtime suites are not
repeated for documentation because qualified executable bytes are unchanged.
