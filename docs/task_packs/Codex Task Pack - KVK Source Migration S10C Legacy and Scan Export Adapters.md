# S10C — Legacy and Scan Export Adapters

## Implementation approval and preparation checkpoint — 2026-09-14

### PR review correction boundary — 2026-09-15

Second review correction: submission now returns only the authoritative enqueued `JobID` string,
and output planning rejects multiple logical spreadsheet registrations sharing a physical ID before
consuming frames. Seven regression cases cover both consumers, captured/materialized receipts,
early alias rejection and valid distinct destinations. The focused suite passed **106 tests** and
the provider adapter suite passed **16 tests**; Ruff and architecture/deferred/security-routing
validators passed. Test selection ran; the prior full suite and registration/import evidence remain
retained, with focused tests selected for these two runtime edits. No SQL change or execution.
Changes security review, Deep off, `9df134e0-ed0e-420a-bbab-196716faa809` completed with no findings
or deferred candidates against working-tree base/head `a82f43cf31daeba8ef0271a47f1bd7bc0235eacc`,
digest `codex-security-snapshot/v1:sha256:0ada2df9d44f85e045db8b2b9803f613f5e1a1336b123b87c8dcc7e12ef323fa`.
This evidence-only paragraph was added after sealing; its documentation-only delta is excluded
from another security scan because it changes no runtime, configuration, policy or trust boundary.
The exact 83-identity Bot boundary and separate eight-path SQL boundary remain unchanged.

The operator authorized action, responses and resolution for Bot PR #279 and separate SQL PR #86.
The pending-export correction also modifies `admin_helpers.py` and
`tests/test_admin_helpers_stats_delivery.py`, extending the exact Bot delivery union to **83 physical
path identities** (81 PR entries when both archive source/destination pairs are represented as renames).
These two paths accompany every previously mandated source/test/document/archive identity in the same
Bot PR; no standalone documentation PR or repository mixing.

The correction preserves Decimal precision as RAW text after numeric planning/sorting, marks failed
writer connection/session setup explicitly uncertain, keeps both ProcConfig branches under runtime
admission, and carries an explicit pending export result through telemetry, logs and live queue status.
Pending delivery neither fabricates provider completion nor masks other failed processing steps.
Both task README status banners move to the first block after their H1 without changing banner content.
SQL PR #86 separately tightens pending ownership and Actor collation and validates inherited S10A
resource columns/checks/indexes/FKs before first-install alteration/sealing. All SQL work is authoring
and offline/static validation only; current S6/S8 evidence and all execution gates remain unchanged.

Review-correction validation: **98 focused tests passed**, import smoke and registration passed
(36 top-level commands, no drift), architecture/deferred/security-routing checks passed, and both
README banner bodies were verified unchanged. SQL's static checker accepted the valid patch and
rejected six deliberately corrupted contract variants; no SQL was executed.
Separate correction Changes reviews, Deep off, completed with no reportable findings or deferred
candidates: Bot `b1bd7b3b-26a7-466c-92c3-56ff810e4f64` at
`codex-security-snapshot/v1:sha256:7889071e2e7feeac3b1b121b2d51539e6163629b002ff873628af12e6290fba5`,
SQL `eeb8cf3a-d063-4c0c-ba7e-97caf5aab5a4` at
`codex-security-snapshot/v1:sha256:19c735c6af83c989274ceff27251179534358bd3fca9856bc2c7d2c1e270868a`.
This subsequent evidence-only text update is covered by a documentation-only security skip.

The operator approved the expanded Bot scope and implementation direction after the initial
review. This supersedes the initial-review-only authority below for Bot authoring and offline
validation. Separate SQL authoring and offline/static validation were subsequently approved
for the exact eight-path manifest below. Publication, SQL execution, provider/Discord execution, deployment and
activation remain separately gated. Preserve all earlier evidence and the mandatory documentation union.

The original 26 action/path pairs and all 47 closeout documentation identities remain mandatory.
Approved additional Bot Modify paths are:

- `player_stats_cache.py`
- `services/export_coordination_dal.py`
- `tests/test_player_stats_cache.py`
- `tests/test_stats_module.py`
- `tests/test_stats_module_timeout.py`
- `tests/test_stats_module_cancelled.py`
- `tests/test_kvk_admin_service.py`
- `tests/test_kvk_export_sql_integration.py`

The initial approved Bot union is 81 physical identities. Exact manifest rows, including both
S10B archive move sides, govern delivery; counts are not proof. No standalone docs PR.

### Separate SQL proposal: preparation before immutable job admission

Static inspection at SQL `3776dfa6b0892a8800d236fdf111c4d2f93c3813` confirms that
`dbo.ExportJob.CK_ExportJob_Spool` requires a complete spool for legacy/daily work, while
`dbo.ExportResource` ownership requires an existing job/resource membership. A pending
capture or account-owned configuration/discovery request cannot honestly be represented as a
ready export job. Existing import-audit wrappers are best-effort and are not ownership authority.

Approved additive contract for authoring and offline/static validation only:

- `dbo.ExportPreparation`: durable request identity, consumer/writer scope, account, original
  fairness ticket, actor/reason, server-UTC timestamps, storage owner, owner/fence/version,
  immutable requested configuration identity, committed generation proof, capture state,
  complete spool receipt and optional resulting JobID. SQL commit ambiguity remains explicit;
  a scan number never supplies output completion. Preparation cannot mutate a sealed export job.
- `dbo.ExportPreparationResource`: exact preparation/resource membership; retain history.
- Add nullable `ActivePreparationID` to `dbo.ExportResource`, with scoped membership FK and
  mutually exclusive preparation/job ownership. All claims check both owner kinds and blocked
  state. No existing job, receipt, fence, attempt or part is rewritten or cleared.
- Use the existing account mutex and a shared ticket allocation across preparations and jobs.
  Account preflight is a separately claimed stage; release it before SQL snapshot work. A
  ready capture materializes its immutable ExportJob at the original ticket under account CAS.
  Active exports keep ownership; unready captures do not occupy provider resources. SQL writer
  ownership survives caller timeout; session admission alone cannot clear durable uncertainty.
- One producer holds the SQL snapshot resource and passes a validated owner token into nested
  helpers. UPDATE_ALL2 retains its own transactions. All-KVK commit can atomically record its
  generation proof on the same SQL connection; unknown UPDATE_ALL2 completion remains pending
  until authoritative evidence is available. Spool registration follows fsync/readback, and
  generation advance yields unavailable rather than recapturing newer output under an old ID.
- Preparation covers read-only configuration/provisioning admission as well as legacy and daily
  capture. It is not S10D pool allocation or S10E operator UX. No old resource is released merely
  because a preparation/job changed state or its lease aged.

Exact approved SQL-only authoring manifest (new objects are authored, not installed):

| Action | SQL repository path |
|---|---|
| Create | `migrations/20260914_002_legacy_export_preparation.sql` |
| Create | `sql_schema/dbo.ExportPreparation.Table.sql` |
| Create | `sql_schema/dbo.ExportPreparationResource.Table.sql` |
| Modify | `sql_schema/dbo.ExportResource.Table.sql` |
| Create | `validation/kvk_source/s10c_legacy_export_preparation.sql` |
| Create | `deploy/Test-LegacyExportPreparationContracts.ps1` |
| Modify | `docs/SQL_DELIVERY_LOG.md` |
| Modify | `migrations/README.md` |

The migration filename was unused at review and before authoring. The operator approved
authoring and offline/static validation only, never installation, database access or publication.
The SQL patch gets an independent Changes review, Deep off, against its exact base.
Bot deployment remains closed until this contract and all participating writer versions are
separately deployed/attested. Existing SQL documentation stays pending for that authorized SQL PR.

## Authority and entry state — 2026-09-14

### Approved implementation checkpoint — local authoring only

The approved Bot patch now contains the exact original 26 action/path pairs, the eight approved
additions above and all 47 pending documentation identities. A fresh path-by-path status comparison
found no missing or extra identities. Both S10B source blobs match the table in the closeout at
both Bot/production anchors; both archive destinations are absent at those bases and present
locally, with the source sides deleted. Both indexes remain empty. GitHub `filename` and
`previous_filename` verification remains required when an implementation PR is authorized.

Producer admission is explicit runtime composition, backed by the separate preparation contract.
Nested writers reuse the same owner. All-KVK ingest/recompute appends completion to its existing
transaction; UPDATE_ALL2 keeps its own transaction ownership and checkpoints only after its full
call returns. ProcConfig collects provider ranges before SQL admission and captures the resulting
daily/target outputs after refresh. A later failed producer invalidates the earlier pipeline capture.
Missing completion, capture/spool failure and lost acknowledgments retain evidence and claims.
Refused, unstarted requests are withdrawn by exact version/no-active-resource CAS; they do not
remain abandoned fairness tickets. Manual requests cannot select a preceding capture when the
newest preparation is unavailable, nor change its registration, account, season or storage owner.

Immutable payloads contain complete headers/rows, output plans, additional-output skip decisions,
configuration and producer provenance. Comparison Overall values come from SQL Full sections,
not fight-window sums. Delivery validates all destination/grid conflicts before mutation, records
attempts/parts, writes RAW values and verifies complete values and audience before a scoped receipt.
Both SDK request paths use common reservation, authorization recheck, completion and bounded
cooldown. Internal gspread backoff is rejected. Cancellation drains admitted SQL threads; unknown
provider/checkpoint outcomes retain ownership for reconciliation. S10B intent lifecycle and
one-period compaction remain unchanged.

Composition remains closed by default. Verified registrations must supply existing destination IDs
and captured grid identities; unresolved provisioning/custom partial export plans return unavailable.
This patch neither constructs live runtime clients from an activation flag nor enables S10D/E/S11.
All writer instances must be separately upgraded/attested before any later activation; an old writer
cannot be made safe by a session lock or a new schema alone.

Offline evidence on 2026-09-14:

- Full Bot suite: **4,480 passed, 67 skipped, 189.00 s** before the final capture/overall refinements.
- Final affected-path suite after those refinements: **261 passed, six skipped, 7.53 s**.
- Final SDK-backoff guard: **15 provider-adapter tests passed**.
- Subsequent input/admission and explicit nested-owner checks: **62 passed** across snapshot,
  importer DAL and upload-route tests. Pure workbook rejection precedes admission; valid imports
  retain admission through connection close/capture, and explicit tokens flow to nested helpers.
- Final combined affected-path suite after those corrections: **266 passed, six skipped, 7.23 s**.
- Architecture validation: 34 Python paths; deferred-items and security-routing validators passed.
- Import smoke passed; command registration retained 36 top-level commands with no drift.
- Ruff, Black-equivalent formatting and both repository whitespace checks passed. Black's CLI
  worker stalled on this Windows host; its in-process formatter checked the same changed files.
- SQL static checker passed exact table-snapshot/migration comparisons and required metadata
  signature checks. The negative SQL fixture and distinct opt-in S10C concurrency case are authored
  only. No database/schema execution, current-provider proof or actual restore is claimed.

Security routing requires separate **Changes / Deep off** reviews: Bot's complete uncommitted
patch at `8ae66da6e12b53781c5df0d46a8ee79314cecead`, and SQL's eight-path uncommitted patch at
`3776dfa6b0892a8800d236fdf111c4d2f93c3813`. Retain their immutable target digests and final reports
outside the delivery manifest. Final Bot review `63704de5-c4c1-4141-9b82-35a1845684f7`
completed with no reportable findings or deferred candidates against digest
`codex-security-snapshot/v1:sha256:d1bd76adcda0fb2250e2d7d58b60c989c7ce73fc7b8643373ef9390ca6f48f80`.
Separate SQL review `83778eb1-6169-4d08-ab6a-24ebfdd90f20` completed with no reportable findings
or deferred candidates against digest
`codex-security-snapshot/v1:sha256:c56aa47a8c0672f6c1cb8c2d52311d8a907ed8d17ebd865baff2914c15f2e8be`.
This subsequent review-result documentation update has no runtime/configuration effect and is
covered by a documentation-only security skip; reviewed runtime source bytes remain unchanged.
The final formatter inserted one blank line after a local import in the provider-adapter test;
that exact whitespace-only delta is covered by a formatting-only security skip.
Exact local path/action proof covers all 81 Bot and eight SQL identities, including each archive
destination's `filename`, source `previous_filename`, exact source blobs and destination absence
at both Bot bases. No PR exists: provider filename/previous_filename coverage remains a mandatory
publication/handoff gate when separately authorized. No merge/deployment readiness is claimed.
All S6 gates, both uncertain publications, retained databases/files and distinct S8 evidence remain
unchanged. No Git publication, SQL/provider/Discord operation or bot-machine action was performed.

### Historical initial-review authority

**Initial review/scope only.** Return scope, risks, tests and an implementation plan for approval.
This pack is prepared after accepted S10B code review and merged repository delivery; it does not
authorize S10C implementation, Git publication, execution, deployment or an automatic new task.
Do not reopen settled predecessor acceptance or documentation grouping.

S10B mirror #278 merged as `b83f1bc8fe667602204b353ff18f9fea30a875d3`; production #585 merged
as `40c2e48111ebbe44d58d71269dea63a6dd9388b7`. Local Bot main/origin main is synchronized at
`8ae66da6e12b53781c5df0d46a8ee79314cecead`; production/main is the production merge above.
SQL main/origin main remains accepted S10A #85 at `3776dfa6b0892a8800d236fdf111c4d2f93c3813`.
**No changes have been pulled to the bot machine.** Repository delivery is not runtime deployment.
Recheck both repositories and preserve staged, unstaged, untracked, deleted and renamed work.
These hashes are comparison anchors, never reset instructions.

## Required reading

Read current AGENTS and core references; the [S10B closeout and exact pending manifest](../reference/kvk_source_migration/s10b_closeout_and_s10c_handoff.md);
the [S7 contract/consumer matrix](../reference/kvk_source_migration/integration_contract_and_consumer_matrix.md),
[exact implementation manifests](../reference/kvk_source_migration/integration_implementation_manifests.md),
[architecture/EndScanID amendment](../reference/kvk_source_migration/phase_2_contract_and_architecture.md),
acceptance scenarios and retained S6/S8 evidence linked by the closeout. Read the S10B review
corrections in the [preceding handoff](../reference/kvk_source_migration/s10a_implementation_and_s10b_handoff.md).
Use authoritative SQL in `C:/K98-bot-SQL-Server`, including merged S10A tables and actual legacy
ingest/recompute/UPDATE_ALL2, ProcConfig, views and result shapes. Do not infer SQL from Python.
Use architecture-scope, SQL-validation and test-selection skills. After implementation approval,
security routing selects **Changes, Deep off**, on the exact Bot target; assess any SQL delta separately.

## Exact S7 S10C implementation boundary

The approved S7 boundary is reproduced below. Validate it against current source at scope time;
explain any necessary additions before implementation. The documentation union below is mandatory
in addition to these paths. Two commits within one bounded PR (snapshot capture and provider
integration) are permitted; do not split off a documentation PR.

| Repository | Action | Exact path |
|---|---|---|
| Bot | Create | `services/legacy_export_snapshot_service.py` |
| Bot | Create | `services/legacy_export_snapshot_dal.py` |
| Bot | Create | `services/export_provider_adapter.py` |
| Bot | Create | `tests/test_legacy_export_snapshot.py` |
| Bot | Create | `tests/test_export_provider_adapter.py` |
| Bot | Modify | `gsheet_module.py` |
| Bot | Modify | `processing_pipeline.py` |
| Bot | Modify | `stats_module.py` |
| Bot | Modify | `kvk_all_importer.py` |
| Bot | Modify | `upload_routes/kvk_all_route.py` |
| Bot | Modify | `commands/admin_cmds.py` |
| Bot | Modify | `commands/stats_cmds.py` |
| Bot | Modify | `kvk/services/kvk_admin_service.py` |
| Bot | Modify | `kvk/dal/kvk_admin_dal.py` |
| Bot | Modify | `kvk/dal/kvk_all_import_dal.py` |
| Bot | Modify | `proc_config_import.py` |
| Bot | Modify | `services/export_coordination_service.py` |
| Bot | Modify | `tests/test_gsheet_module.py` |
| Bot | Modify | `tests/test_gsheet_helpers.py` |
| Bot | Modify | `tests/test_gsheet_sorting.py` |
| Bot | Modify | `tests/test_kvk_all_upload_route.py` |
| Bot | Modify | `tests/test_kvk_all_import_dal.py` |
| Bot | Modify | `tests/test_processing_pipeline.py` |
| Bot | Modify | `tests/test_processing_pipeline_run_step_and_normalization.py` |
| Bot | Modify | `tests/test_proc_config_import.py` |
| Bot | Modify | `tests/test_kvk_export_coordination.py` |

## Scope and guarantees to validate

1. Route automatic and manual legacy all-KVK and scan-data exports through the common coordinator.
   Inventory every affected caller in C01-C65/N01-N12; commands remain thin and existing public
   command surface remains unchanged. Preserve fixed season source and independent stats, targets,
   roster, history and daily consumers. No silent legacy fallback or SourceRouting.Enabled-only activation.
2. Acquire legacy SQL snapshot admission once at the producer boundary and pass a validated ownership
   token to nested writer/config/DAL helpers. Do not reacquire the same exclusive resource on another
   connection. All participating import/recompute/config writers must share the protocol across
   processes. Collect provider configuration reads before the SQL portion. Do not wrap UPDATE_ALL2
   in an ambient transaction: it owns/rejects ambient transactions. Never hold a SQL transaction
   across provider requests, pacing waits or retries.
3. Capture all export result sets, headers, configuration and provenance consistently into an immutable
   durable spool before provider work. Use the existing snapshot store and durable SQL receipt for
   digest, length and storage-owner affinity; no per-tab reads of mutable output. A raw ScanID is not
   recompute completion proof. Associate committed import/recompute output and captured snapshot under
   the admission token. On commit-before-spool failure, retain pending capture evidence for that exact
   generation. If output advanced, report the mismatch; never label newer data as the earlier import.
   Manual export may reuse verified ready provenance without recompute; missing proof is unavailable.
4. Resolve registered spreadsheet IDs before mutation; aliases conflict and new-source pools cannot
   overlap legacy/daily outputs. One coordinator database and durable account/resource ownership are
   required across eligible processes. Admission is fair across automatic/manual consumers and accounts.
   Preserve daily SCANORDER and import history; never coalesce away daily work. Coalesce only eligible
   pending new-source work. Running A keeps its immutable inputs when B arrives.
5. Wrap actual gspread HTTP requests and google-api execute calls, including reads, formatting, grants
   and retries, in the shared durable account budget. Preserve server-UTC reservations, outside-SQL
   waits, 2100ms initial policy, completion checkpoint spacing, monotonic 429/503 cooldown and absolute
   HTTP-date interpretation against SQL UTC. Uncertain budget/feedback checkpoints retain claims.
   A local sleep or process-only limiter cannot replace the durable budget. Mutations cannot be blindly
   replayed after ambiguous outcomes. Resolve account/project identity consistently for both clients.
6. Preserve deterministic resource acquisition and owner/fence/version CAS, attempts and exact parts,
   scoped historical receipt identity and immutable replay/repair identity. A timeout or detached worker
   is not proof that provider activity stopped. Cancellation waits for actual worker completion or
   leaves durable uncertainty; no replacement writer is admitted by job state or lease age alone.
7. Reuse S10B registration-aware intent discovery/state transitions and per-period compaction. Preserve
   compact-before-next-read behavior and bounded transient long-form memory; final output still scales
   with generation size. Do not regress to eager ten-period expansion. Missing/corrupt/wrong-owner
   spools block execution; rebuilding requires the permitted new audited identity before mutation.

Preserve supplied overall/B0, authoritative kingdom/camp aggregates and DKP, UTC scan starts,
unused scans, movable within-season windows, exact 11-10/12-10/final13-10/authorized14-10 endpoint
chain, sealed inputs/CAS, durable matched UpdateID and explicit counterpart attestation. No mixed
sources, summed-fight overall, or export-time parsing/import/recalculation disguised as export-only.

## Tests, risks and approval output

Map S7-T10/T11/T16 to the actual affected paths; retain S7-T09 behavior. Cover happy, negative,
duplicate/replay, restart, concurrent writer/snapshot, post-commit capture failure, mutable-output
advance, missing/corrupt/wrong-owner spool, account fairness, alias IDs, mixed clients, pacing and
cooldown, uncertain requests and late-worker effects. Prove snapshots cannot mix result generations
and manual export does not invent completion. Test independent daily ordering/history and source
isolation. Run retained compaction regressions when integration touches the intent path.

Run or justify architecture, deferred-items, test-selection and security-routing validators; choose
focused tests, full pytest with production-log isolation, smoke imports and registration checks.
Offline doubles do not prove SQL concurrency, live provider pacing or production memory capacity.
List exact disposable/live tests needed later with targets and operations; predecessor execution
approval does not authorize them. No database or provider call is authorized by this pack.

Return exact source/test/documentation union, SQL object validation, static-versus-temporal guarantees,
risks, deployment prerequisites, tests and implementation plan for approval. No new top-level command,
S10D pool schema, S10E export-only/status/reconcile/rebuild/rollover UX or S11 release implementation.
Production composition remains closed until separately verified adapters and deployment attestations;
implementing adapters is not activation authority. External account clients and SQL writers remain an
S11 inventory gate, not assumed participants. No credential or actual .env changes.

## Mandatory documentation delivery in the eventual S10C PR

The [closeout's exact pending Bot table](../reference/kvk_source_migration/s10b_closeout_and_s10c_handoff.md#exact-pending-bot-documentation-manifest)
is part of the S10C Bot implementation PR, including this pack/starter, the new closeout, current
reference/runbook updates and **both source and destination paths of both S10B archive moves**.
Reconcile fresh status against that table; extend it for any later task-produced documents.
Do not omit documents because implementation tests pass or because the file count looks right.
Verify GitHub `filename` AND `previous_filename` coverage for every path. If a path is already merged,
provide its exact merged commit and content proof; if an origin was absent at base, prove that exact
absence. Repeat on promotion. Never claim archive-source deletion from destination count alone.

No standalone documentation PR, repository mixing or renewed grouping approval. The separate SQL
`docs/SQL_DELIVERY_LOG.md` and `migrations/README.md` updates stay in the SQL repository and must
accompany its next authorized SQL PR (an independently scoped S10C SQL delta if required, otherwise
S10D); never put them in the Bot PR or manufacture a SQL change to publish them.

Preserve S6-OPS01/PERF01/CAP01, both uncertain publications
`e19c89ac-7977-5f28-ae4c-031807cd1728` and `54a2480a-26fb-5bad-a3f5-9321525a731c`, all retained
databases/files, and distinct S8A six-script, S8B 50-case/actual-restore versus offline-runner, and
S8C seven local-check evidence. No live Discord acceptance follows. No real import/export, SQL/provider/
Discord execution, bot-machine pull/restart/deployment, activation, predecessor rerun or automatic task.
