# Codex Task Pack — KVK Source Migration S4B Versioned Exports and Delivery

## Current S4B entry handoff — 2026-09-10

**S4A is complete, operator smoke accepted and merged.** Mirror [#268](https://github.com/cwatts6/K98-bot-mirror/pull/268) merged on 2026-09-10 at 16:12:39 UTC as `eba04639eced51e368d6fc7036284f25640ce871`; private bot [#575](https://github.com/cwatts6/k98-bot/pull/575) merged at 16:13:04 UTC as `021fc7adc9952ab07d21517e8e47f3966c285f7a`.
Operator candidate smoke on `055b9590e1114661ff0369c7815fbbea82661454` passed imports, registration **36/100** without drift/duplicates, **134 focused tests in 11.97s**, and **3,810 full-suite tests with 34 skipped in 134.19s**. Both pytest runs left operational logs unchanged. This closes the S4A full-suite gap; earlier stalls and passes remain historical evidence, not a post-merge rerun.
Local mirror `main` is `7baf92c7badc3f40006841046825a788bc823373`; local `production/main` is `021fc7adc9952ab07d21517e8e47f3966c285f7a`; SQL `main` remains `44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Bot and SQL checkouts were clean at closeout entry. Local pulls are complete, per operator and local refs; **nothing has been pulled to the bot machine**.
S4A pack/starter are archived. **Next: S4B Versioned Exports and Delivery in a new chat, with separate S4B G3 approval.** S4B's pack requires all pending closeout documents and both archive rename sides in its eventual separately authorized PR. Prior S3B closeout documents were included in the merged S4A PRs.
Source routing remains disabled. No bot-machine update/restart, SQL deployment, live imports/exports, Discord action or activation is needed for S4B local development. Use mocks/fake destinations unless a disposable SQL target and exact operations are explicitly authorized first; preserve retained S2A/S2B/S3B databases. Historical prerequisite wording below does not reopen completed slices.

Read the [archived S4A final evidence](archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S4A%20Shared%20Reports%20and%20Cards.md) before edits. S3B/S4A prerequisites are accepted. **S4B G3 remains pending; no S4B implementation has started.** Reverify branches/HEADs/remotes/status at entry and preserve this pending documentation.

### Required carried-forward documentation in the eventual S4B PR

The operator requires this complete thirteen-document closeout manifest (fifteen physical paths) in the eventual separately authorized S4B PR. This supplements section 11 for documentation only. Preserve tracked edits, source deletions and untracked Markdown archive destinations; include both sides of both renames, repaired links and final delivery evidence. Do not blanket-stage unrelated work. Reconcile the actual staged manifest and verify preservation/links before PR creation; carry the same documentation into the private counterpart when separately authorized. This is not permission to commit/push/create a PR now.

- Update: `README-DEV.md`.
- Update: `docs/reference/README.md`.
- Update: `docs/reference/kvk_source_migration/decision_and_evidence_register.md`.
- Update: `docs/reference/kvk_source_migration/phase_2_implementation_plan.md`.
- Update: `docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md`.
- Update: `docs/task_packs/KVK Source Migration - Programme Pack.md`.
- Update: `docs/task_packs/README.md`.
- Update: `docs/task_packs/archive/README.md`.
- Update: `docs/reference/local_sql_development.md`.
- Update: `docs/task_packs/Codex Task Pack - KVK Source Migration S4B Versioned Exports and Delivery.md`.
- Update: `docs/task_packs/Codex Chat Starter - KVK Source Migration S4B Versioned Exports and Delivery.md`.
- Archive move: `docs/task_packs/Codex Task Pack - KVK Source Migration S4A Shared Reports and Cards.md` → `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S4A Shared Reports and Cards.md`.
- Archive move: `docs/task_packs/Codex Chat Starter - KVK Source Migration S4A Shared Reports and Cards.md` → `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S4A Shared Reports and Cards.md`.

## 1. Task Header

- Prepared 2026-09-09; owner Chris Watts; Phase 2B specification.
- G2 architecture approved, including authorized EndScanID corrections. **S4B G3 pending.**
- One-pass implementation approved: **No**. Execute only after explicit approval of this slice.
- Proposed isolated branch `codex/kvk-source-s4b`; not created during planning.
- Type: bot implementation.

## 2. Required Reading

Read current AGENTS.md, README-DEV.md, docs/reference/README.md and its required core references,
the canonical task template, root/applicable SECURITY.md and relevant skills. Then read the
[approved contract](../reference/kvk_source_migration/phase_2_contract_and_architecture.md),
[implementation plan](../reference/kvk_source_migration/phase_2_implementation_plan.md),
[70 scenarios](../reference/kvk_source_migration/phase_2_acceptance_scenarios.md), latest programme/
register updates and this pack. User decisions override historical missing-B0/G2-pending wording.
For SQL-facing work read authoritative SQL instructions, sql_schema/README.md, migrations/README.md,
SQL_DATA_MIGRATION_GUARDRAILS and exact relevant snapshots. No inferred schema from Python alone.

## 3. Objective

Export exact selected periods with precision and durable destination receipts; never reconstruct overall by adding fights or revisions.

## 4. Background

Planning anchors: bot main `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`; SQL main
`fc0e94ebd2e0a98286069c8a8b71365dd5178657`. Recheck branches/HEADs/remotes/status at execution,
preserve existing work and record actual start/end hashes. Local definitions are not deployed proof.
No pull/reset/checkout to make a working copy match historical evidence. Use an authorized isolated
branch/worktree where needed. Phase-1 C01-C65 anchor dependencies; G2 fixes source semantics.

## 5. Scope

Predecessors: S3B/S4A accepted and S4B G3; fake destinations for implementation tests.

Only the section 11 manifest and requirements below. No generic refactor, WS1 reliability repair,
daily SCANORDER change, legacy backfill or independent stats/targets/history/profile migration.
No private workbook/player-row fixtures. No provider-formula or unavailable later-fight request.
This pack alone never authorizes pull/reset/merge/push/PR, live SQL, real imports/exports, Discord
actions, restarts, deployment or activation. Code validation uses mocks or explicit disposable SQL.
S6 additionally stops at G4 before any live action. No automatic next slice.

## 6. Source Deferred Items

Not derived from deferred work. Known legacy export grouping/summation and ProcConfig WS1 debt
remain separate. Capture only newly evidenced unrelated non-security debt in canonical format.

## 7. Codex Skills To Use

Architecture-scope, test-selection, security-review-routing and final PR-review apply. SQL-validation
applies to SQL-facing contracts. Discord-command-feature applies to S4A/S5A/S5B interaction work.
Promotion-check applies only when S6 reaches separately authorized G4 review. Deferred-capture and
spreadsheet inspection are conditional; no subagents required.

### Security Review Decision

Current pack authoring: bot docs-only skip; SQL no-change skip. Future execution: Bot Changes review for this exact implementation diff, Deep off; SQL no-change skip. Prerequisite SQL slices have separate reviews.
Use k98-security-review-routing first; record exact immutable base/head or task-only authored patch,
Scan type Changes and Deep off. Never scan/stage unrelated dirty files or combine bot/SQL histories.
No routine standard/deep audit. Retain scan coverage/results privately; no public finding details.

## 8. Mandatory Workflow

1. Confirm explicit S4B approval and predecessor evidence; otherwise scope/review and stop.
2. Capture worktrees and exact manifest; recheck drift and source/SQL contracts before edits.
3. Implement only the approved boundary with assigned tests; preserve unrelated work.
4. Run checks, review exact diff/security target and report actual outcomes/limitations.
5. Stop at delivery; no automatic next task, G4 action or self-approval.

## 9. Focused Audit Requirements

Inspect section 11 read paths for helper semantics, layering, period/identity/availability and
regression contracts. Static source continuity does not prove current live rows/jobs or external
readers. Operator-attested SQL/config parity remains separately labelled. No credential discovery
or RDP required for this planning/implementation boundary. Evidence condition: Real external behavior is G4/private-smoke evidence; fake transports cannot prove external exactly-once.

## 10. Architecture Targets

kvk/models and kvk/schemas own pure types; kvk/services business rules; kvk/dal parameterized SQL,
transactions and mapping; commands/routes/views thin adapters. New SQL only in the SQL repository.
Follow the implementation-plan interfaces/lock order and approved source/field dictionary.
No second domain implementation in DL_bot.py or gsheet_module.py; no duplicated SQL calculation.

## 11. Exact File Manifest

All paths below are relative to **C:/discord_file_downloader**.
New files are proposed, not present yet; predecessor-created modifications require accepted delivery.
No wildcard authorizes extra files. Append implementation evidence to this pack after execution;
do not rewrite unrelated indexes. Migration date/sequence is the sole controlled allocation exception
in implementation-plan section 4; final name must be recorded before authoring and never renamed after merge.

### Read only

- `kvk/rendering/kvk_rankings_csv.py`
- `kvk/services/kvk_admin_service.py`
- `stats_alerts/interface.py`
- `core/discord_embed_limits.py`

### Create

- `kvk/services/new_source_export_service.py`
- `kvk/services/new_source_delivery_service.py`
- `kvk/dal/new_source_delivery_dal.py`
- `kvk/rendering/new_source_export.py`
- `tests/test_kvk_source_exports.py`
- `tests/test_kvk_source_delivery.py`

### Modify

- `kvk/services/kvk_export_service.py`
- `gsheet_module.py`
- `tests/test_kvk_export_service.py`

## 12. Implementation Requirements

Close C29-C34: ten export sections, per-fight/comparison/ALL_WINDOWS outputs. Version binder schema, no positional legacy fallback for V2. Preserve legacy export/generic sum helper; new exporter never invokes it for overall.
Player overall B0-to-end and supplied final aggregate overall independent. Missing fields/overall blank plus status, never zero. Group stable IDs, labels separately; raw precision/unit and Decimal strings, no FLOAT. Reuse RAW Sheets/CSV formula protection without changing independent ranking outputs.
gsheet_module.py gets thin dispatch only; new services own generation manifest and writes. Write private generation outputs, verify complete required sections, then expose current link; timeout cannot mark partial output current. Do not retain stale tabs under a new-success label.
SourceDelivery claims/fences serialize destinations and recheck selected generation. Separate SQL-selected, export-complete and Discord receipt; uncertain send/edit never blind replacement. Normal cadence/daily ownership unchanged. No background integration until S5B.
Test fake Sheets/Discord transports, partial writes, delayed stale writes, repeated ranges, source/period/precision and uncertain receipts. No actual export, real message or credential fixture. Explicit publication/destination arguments, no independent latest query midway.

Either endpoint may change; supplied EndScanID >= StartScanID. Distinct scans increase both ScanID and UTC. Equal endpoints mean zero supported fight scores for every B0 member, with aggregates not applicable; ordinary missing values remain explicit. Preserve semantic re-export deduplication and UTC scan start.

All slices retain B0 eligibility/attribution, exact endpoints, total-deaths player DKP and supplied
aggregate authority. Interim 11−10 then 12−10; EndScanID=13 gives 13−10; authorized update to 14
is itself correction authority for 14−10 without a second command. Pending desired endpoint cannot
label an older result current/final. It does not authorize weight/map/roster/source-content changes.
Daily namespaces remain separate; aggregate uploads/re-exports do not allocate a new player scan.

### Command Surface Governance

No command count change. Preserve permission/visibility/version/usage identity. Run or justify skipping actual command inventory/registration based on touched surfaces.

## 13. Refactor Decisions

Only new-source extraction and adapters in this manifest. Retain legacy behavior while preventing
its null-to-zero, upload-time, growing-roster and aggregate-recalculation rules leaking into new
source. No generic exporter/ProcConfig cleanup. Inspect helper semantics before reuse; expanding
the manifest requires bounded review, not opportunistic refactoring.

## 14. Testing Requirements

Scenario ownership: T16/T55-T59/T63/T65-T67; exact section/source/period and failed delivery handling.

- `python -m pytest -q tests/test_kvk_source_exports.py tests/test_kvk_source_delivery.py tests/test_kvk_export_service.py tests/test_kvk_all_upload_route.py`

For bot code run architecture/deferred/security-routing validators and test selector with exact
paths, applicable pre-commit on task files, focused tests and justified broader checks. S4/S5
shared integrations require full pytest and scripts/analyse_pytest_log_noise.py. S1/S3A may
justify focused-only. No historical suite result is a fresh pass. Safe smoke/registration uses
test environment; SQL tests never use default production targets. Static regex checks do not
prove transactions/concurrency. Report blocked integration separately; never substitute live SQL.

## 15. Acceptance Criteria

- [ ] Explicit slice approval and prerequisites; exact manifest and preservation verified.
- [ ] Assigned scenarios pass with actual evidence, including applicable failure/restart/permission cases.
- [ ] Legacy and independent sources preserved; no wrong period, zero fallback or precision loss.
- [ ] Exact per-repo security targets reviewed or precise skip justified.
- [ ] Remaining integration/live limits explicit; no automatic next slice or live action.

## 16. Required Delivery Output

Use canonical eleven parts: Summary; File Manifest; New Files; Modified Files; SQL Changes;
Helpers Reused; Refactor Findings; Test Plan with outcomes; Security Review Decision and Evidence;
Deployment Steps (none unless separately approved); Deferred Optimisations.

Rollback: Stop destination workers; retain last verified export link/history/receipts. Rollback cannot retract shared downloads or messages. No deletion of uncertain artifacts to hide failure.

## 17. Proposed PR Summary

Describe concrete behavior, exact manifest, actual tests/security target, dependencies and rollback
limits. Keep private player rows/credentials/findings out of Git. No PR creation authorized by
preparation. End with slice status and next required gate.

**Prepared only. S4B G3 pending; no implementation executed.**

## S4A closeout documentation validation — 2026-09-10

This pending change is documentation only: eleven updated files and two archive moves (thirteen logical documents, fifteen physical paths). Security routing: documented bot Changes-scan skip because only status/evidence, links and future handoff instructions changed; no runtime/configuration/permissions/data-access effect. SQL repo is unchanged, separate no-change skip. No new runtime tests are required for these documentation edits; the operator S4A results above remain attributed to the tested candidate. These local edits are intentionally uncommitted for the separately authorized S4B PR. No S4B code, new task, merge, push, deployment or activation was performed.

Closeout checks passed: 119 local Markdown links resolve; both archived documents preserve original historical text with rebased links; architecture, deferred-item and security-routing validators and git diff --check passed. Test selector recommends import/registration smoke; those are skipped for this documentation-only closeout because no Python or registration behavior changed. The earlier preservation-check assertion was a local text-decoding mismatch; explicit UTF-8 comparison passed.

## S4B G3 implementation delivery — 2026-09-10

This appendix supersedes the historical S4B-pending/prepared-only statements above. The operator explicitly approved **S4B G3 only** in the implementation task. S3B/S4A prerequisites were accepted; current core instructions, approved architecture including EndScanID, Phase 2B plan, acceptance scenarios and this pack were reviewed before edits. S4B is implemented locally for review, with the integration limits below. This is not operator acceptance, PR authorization or activation approval.

### 1. Summary

Implemented explicit V2 source exports and durable delivery orchestration. Ten named sections plus ALL_WINDOWS and COMPARISONS retain publication/selection/configuration IDs, requested versus selected endpoints, UTC scan start, B0 attribution, independent supplied aggregates and exact value/raw/unit/precision text. Comparisons retain separate facts without inventing cross-basis ranks or adding fights into overall. Omitted overall remains blank with an unavailable status within the requested export.

Delivery writes generation-specific private ranges, verifies the complete twelve-table manifest, then invokes current-pointer publication behind a selection/claim gate. Destination ownership and monotonically increasing fences, confirmed deduplication and restart reconciliation distinguish SQL selection, export completeness and Discord delivery. Ambiguous publication/send/edit remains blocked until receipt reconciliation; elapsed time alone cannot reclaim it.

Entry and final repository identity are unchanged:
- Bot checkout: main, HEAD `7baf92c7badc3f40006841046825a788bc823373`; origin K98-bot-mirror, production K98-bot. Local production/main remains `021fc7adc9952ab07d21517e8e47f3966c285f7a`.
- SQL checkout: main, HEAD `44afa315dd6cbfe9fec101f2a39a62e534f5b583`; origin K98-bot-SQL-Server; clean throughout.
- GitHub readback verified S4A mirror #268 and private #575 merged at the hashes in the entry handoff. Archived final evidence agrees with the operator's 134/3,810-test results, unchanged logs and 36/100 registration. Those are predecessor evidence; fresh S4B results follow.
- No branch/commit/PR was created. The main checkout index remains empty. A detached, task-only security worktree at the bot HEAD holds only the nine Python paths for review; its narrow local exclusion keeps it out of delivery. No predecessor or successor pack was executed.

### 2. File Manifest

The implementation changes exactly the six created and three modified Python paths in section 11, plus this append-only delivery record. All thirteen carried-forward logical documents (fifteen physical paths) in the entry manifest remain required for a separately authorized S4B PR, including both original deletions and both untracked S4A archive destinations. All other pending documentation was preserved byte-for-byte; this pack retains its original content before the appendix. No unrelated files are staged.

### 3. New Files

- `kvk/services/new_source_export_service.py`: explicit selected snapshot loading, immutable versioned generation and all twelve output tables.
- `kvk/services/new_source_delivery_service.py`: private write/verify/publish orchestration, separate Discord receipts and read-only remote reconciliation.
- `kvk/dal/new_source_delivery_dal.py`: injected connection, pinned source reads, parameterized SourceDelivery claims, destination locks, selection checks and receipt fencing.
- `kvk/rendering/new_source_export.py`: exact text tables, content hashes, RAW values and formula-protected CSV bytes.
- `tests/test_kvk_source_exports.py`: synthetic export, endpoint, B0, precision, identity, binder and comparison contracts.
- `tests/test_kvk_source_delivery.py`: fake transport/repository failure, retry, stale write, uncertainty, restart and mocked DAL contracts.

### 4. Modified Files

- `kvk/services/kvk_export_service.py`: explicit V2 named binder and loader; legacy binder rejects incompatible non-DataFrame input. Existing legacy section binding remains covered.
- `gsheet_module.py`: thin injected V2 dispatch only; existing legacy export and generic summation helpers remain intact.
- `tests/test_kvk_export_service.py`: version/shape rejection and thin-dispatch isolation tests.
- This pack: appended actual delivery evidence. Existing closeout documents and archive moves are carried forward, not rewritten by this implementation.

### 5. SQL Changes

No SQL repository edits, migrations, database connections or SQL execution. The bot DAL uses existing contracts verified against authoritative snapshots at the SQL HEAD above, especially KVK.SourceDelivery (compound publication/destination key, destination identity bounds, owner/fence, allowed states and 1,024 UTF-16-unit receipt), SourcePublication and SourceWeightConfig, and the existing selected-period/configuration helpers. Values are parameterized. No ProcConfig, daily SCANORDER, staging/output schema or stored procedure was changed.

Transaction and session-lock behavior was inspected and exercised through mocks, **not a disposable SQL Server**. Actual lock contention, disconnect/commit ambiguity and server constraints remain integration evidence gaps. Retained S2A/S2B/S3B databases were not used or altered.

### 6. Helpers Reused

Reused S3B `load_snapshot`, S4A `fetch_source_report_metadata`, configuration `locked_period`/`desired_config`, import DAL `transaction`/`one`/`rows`/`SourceConflict`, publication `RESULT_METRICS`, canonical source identity, legacy section names and ranking CSV `_csv_text_cell`. Existing calculation/resolver helpers supply synthetic endpoint test evidence. Helper semantics were checked before reuse: no new-source call to legacy overall summation, upload-time selection, null-to-zero conversion or growing-roster attribution.

### 7. Refactor Findings

Layering is retained: SQL and receipt persistence in DAL, generation/delivery rules in services, literal rendering in rendering, one thin gsheet adapter. No generic exporter, ProcConfig/WS1, command, ranking-output or independent source refactor was performed.

Final local review found no additional blocking code/security issue within the dormant injected boundary. Merge approval remains with the operator; no merge or production readiness is asserted. Concrete transport integration and real SQL behavior remain unverified as detailed below.

### 8. Test Plan with Outcomes

Fresh validation used the existing `.venv/Scripts/python.exe` and synthetic data/fake destinations:

- Exact pack command, through `scripts/analyse_pytest_log_noise.py`: `-m pytest -q tests/test_kvk_source_exports.py tests/test_kvk_source_delivery.py tests/test_kvk_export_service.py tests/test_kvk_all_upload_route.py` — **75 passed in 5.06s**; operational logs unchanged.
- Full suite through the same log-hygiene wrapper — **3,865 passed, 34 skipped in 164.56s**; operational logs unchanged. The 34 skips are reported skips, not passes.
- Safe imports passed. Command registration: **36 primary / 100 grouped**, no drift or duplicates.
- Architecture validator: **9 Python paths passed**. Deferred-item validation passed on the carried documentation. Security-routing validator: **0 errors / 0 warnings**. Exact nine-path test selector recommended full suite/imports/registration; all were completed.
- Applicable pre-commit hooks passed on the exact nine-file security worktree, including formatting/lint, secret scanning and type checks. Initial hook run normalized mixed line endings in four new files; the repeat passed. Final main-checkout bytes match the checked worktree. YAML/other hooks with no matching files skipped normally.
- Final `git diff --check`, carried-document preservation and local Markdown link checks passed.
- Initial system Python lacked pytest; validation was rerun using the existing project virtual environment. This was an environment issue, not a test pass.

Scenario evidence: T16/T55 cover raw precision, unsupported values and version binding; T56 retains each selected fight and separate overall; T57/T58 cover partial/private writes, exact manifests, delayed old private ranges and stale selected versions; T59 covers ambiguous sends/edits and cadence admission; T63 covers inert CSV/RAW Sheets text and large IDs; T65 covers mocked reconciliation/fence recovery; T66 is protected by explicit source binding/no legacy fallback and the full regression suite, with no live downgrade exercised; T67 labels separate facts instead of unsupported comparisons. Endpoint fixtures exercise interim 11−10 and 12−10, final 13−10 and the authorized endpoint update to 14−10 using the existing resolver/calculator; equal endpoints retain all four synthetic B0 members with zero supported fight DKP and aggregate not applicable. Ordinary missing fields remain blank/status.

**Integration limits:** no concrete Sheets/file/Discord provider adapter is installed by this slice. Injected transports own private audience/path selection, RAW compliance, authoritative remote manifest/receipt verification, atomic/fenced pointer publication, bounded operation timeouts and proof that an absent operation cannot complete later. Caller-owned cadence/authorization is an input contract, not new user authorization logic. Disabled source routing is preserved by unchanged wiring; these explicit APIs are not a universal live-operation prohibition. Real SQL concurrency, remote exactly-once behavior, Discord mention/packing at the eventual adapter, large-roster/provider limits and live rollback/downgrade remain unproved. These limits must be resolved in separately authorized integration/private smoke; no background integration was added before S5B.

### 9. Security Review Decision and Evidence

Bot review: **Changes**, Deep **off**, exact task-only nine-Python-file working-tree patch against base/head `7baf92c7badc3f40006841046825a788bc823373`. Pending closeout Markdown was excluded from the runtime scan and preserved; documentation changes only carry evidence/links and this record, with no runtime effect.

Completed scan `36df6ec5-92f0-4f06-abbb-ed99c51e73b6` at 2026-09-10 16:47:57 UTC: **0 reportable findings**, complete static coverage of six runtime files plus three supporting test files; no deferred candidates. Patch digest: `codex-security-snapshot/v1:sha256:6e85299037b8e4920380d04622bca632660830a6bcae886360ebc8985ccde114`. Required capability preflight passed, Daybreak advisory returned granted, and an independent architecture worker supplied the retained threat model. The sealed canonical report/findings/coverage remain in the private local scan directory under `%TEMP%/codex-security-scans-9H1QC0/s4b/7baf92c7badc3f40006841046825a788bc823373_20260910T163658Z_f5jyy3_k`. Canonical readback confirmed completed status and the exact digest. Measured token usage was not supplied by the completed-scan response. Remote transport/real SQL limits in part 8 remain; complete diff coverage does not prove live integration.

SQL review: separate **no-change skip**, base/head `44afa315dd6cbfe9fec101f2a39a62e534f5b583`, clean checkout. Prior SQL slices retain their own evidence; bot/SQL histories were not combined. No standard/deep audit or automatic new task was launched.

### 10. Deployment Steps

**None authorized or performed.** Source routing remains disabled. No pull/reset/merge/push/PR, production SQL, real import/export, Discord action, bot-machine update/restart, deployment or activation. Stop for S4B review; a future PR requires separate authorization and the complete thirteen-document/fifteen-path closeout manifest.

If a later authorized delivery needs rollback, stop destination workers, retain the last verified link/history/receipts and reconcile uncertainty. Shared downloads/messages cannot be retracted by a code rollback. Do not delete ambiguous artifacts to conceal failure.

### 11. Deferred Optimisations

No newly evidenced unrelated optimisation item was introduced. Existing legacy grouping/summation and ProcConfig WS1 debt remain separate. The explicit integration gaps above are required future validation boundaries, not silently accepted proof or generic cleanup work.

## S4B adapter completion and early file-creation proof — 2026-09-10

The operator approved proceeding with the concrete adapter and early separate private file creation after clarifying that KVK LIST is the existing configuration workbook. This narrowly extends the earlier no-real-export boundary to the synthetic Google smoke below. It does not authorize real SQL/player exports, Discord actions, deployment, activation, PRs or successor packs. This appendix supersedes the earlier statement that no concrete Sheets adapter exists.

### 1. Summary

Added a concrete Google Sheets adapter over injected Google discovery clients. It creates a private generation workbook and a separate current-link index, locates them using destination/generation appProperties rather than names, writes bounded RAW ranges, reads back and hashes all twelve sections, and updates the index only through the existing selection/delivery gate. The factory accepts explicit credentials and uses bounded HTTP timeouts; no credential discovery or defaults are installed. Lost private-create responses now produce uncertain delivery state and block blind retries.

Read-only Google metadata confirmed KVK LIST contains KVK_WINDOWS, KVK_DKPWeights and KVK_CampMap. No values, formulas, tabs, permissions or configuration were changed there. Source routing and legacy exports remain unchanged.

### 2. File Manifest

The original exact nine-Python-file S4B manifest is unchanged. This continuation changes only three of those paths plus this appended record. All thirteen carried-forward documents/fifteen physical paths and both archive rename sides remain preserved for the separately authorized PR. Bot main/HEAD remains `7baf92c7badc3f40006841046825a788bc823373`; SQL main/HEAD remains `44afa315dd6cbfe9fec101f2a39a62e534f5b583`, clean. Remotes remain origin=mirror/production=private bot and SQL origin=SQL repository. Main index is empty; no commits or branches were created. A new detached security worktree preserves the earlier sealed review.

### 3. New Files

No additional source/test paths beyond the six already listed in the original S4B delivery. Two explicitly authorized, synthetic remote smoke workbooks were created and retained:
- [Synthetic generation](https://docs.google.com/spreadsheets/d/1EImkw3wSxTC4gJ2FQiMbml-DaQdDSKNWn-3V74ZMVSQ/edit?usp=drivesdk).
- [Synthetic current-link index](https://docs.google.com/spreadsheets/d/1faFf_3LYyRIoq1qsgolKh2pzztFCAZfhpk6iq--E9iw/edit?usp=drivesdk).

Both were verified unshared, with only an owner permission. These contain synthetic fixtures only, not private player rows or configuration copied from KVK LIST.

### 4. Modified Files

- `kvk/services/new_source_export_service.py`: GoogleSheetsTransport with explicit bounded-client factory, metadata identity, privacy/protected-file checks, creation, RAW range writes, complete readback, current pointer and conservative receipt reconciliation.
- `kvk/services/new_source_delivery_service.py`: RemoteOutcomeUnknown keeps ambiguous private creation uncertain instead of declaring it retryable.
- `tests/test_kvk_source_delivery.py`: stateful Google request fake executes the concrete adapter; creation, repeated delivery, chunking, restart, lost pointer/create responses, protected/shared/ambiguous files, unexpected tabs, changed contents and stale fences.
- This pack: appended current implementation and actual smoke evidence; historical evidence retained.

### 5. SQL Changes

None. No SQL connection, schema change or retained database use. Existing SourceDelivery/selection contracts remain as validated in the original delivery. Real SQL transaction/concurrency evidence is still absent.

### 6. Helpers Reused

Reused ExportTable/manifest hashes, exact source generation, existing receipt builder, SourceConflict and durable delivery orchestration. Existing gsheet client/write patterns informed Google API use; the legacy clear-and-rewrite/retry wrappers were not reused because they do not provide generation isolation or conservative non-idempotent mutation handling. No changes to legacy Google authentication or export APIs.

### 7. Refactor Findings

The concrete adapter stays inside the approved source service file; gsheet_module remains thin. No generic export or operational reliability refactor. SDK mutation calls explicitly use zero automatic API retries. Privacy is enforced before data writes; unshared owner-only My Drive workbooks are supported, shared drives/shared recipients are rejected. Existing config IDs can be supplied through protected_file_ids; remote generation metadata must also match before any existing file is used.

### 8. Test Plan with Outcomes

- Exact focused S4B suite: **84 passed in 7.57s**; operational logs unchanged.
- Fresh full suite: **3,874 passed, 34 skipped in 175.47s**; operational logs unchanged.
- Imports passed; registration **36 primary / 100 grouped**, no drift/duplicates.
- Architecture validation passed on nine Python paths; security-routing validator 0 errors/0 warnings. Exact changed-path selector requested full suite/imports/registration, all completed.
- Applicable exact-file pre-commit hooks passed, including Ruff, Black, secrets and Pyright. Initial direct Black CLI invocations stalled and were interrupted; direct formatting plus the required hook run completed successfully.
- Final patch byte comparison, documentation preservation, deferred-item validation, links and git diff --check passed.

**Actual remote proof:** the connected Google account created the separate synthetic generation, wrote all twelve sections, and read back **904 cells** matching exact literal strings, with no formula or number coercion. The bounded sample contains one row per populated section; it is not a complete roster or scale test. After successful readback, the separate index was written and read back with the matching generation digest, fence 1 and exact generated-file URL. Digest: `9d8eefb288639f25beb497c92355751b82aad5115001c71b71fa59d18545df93`.

**Evidence boundary:** the configured local Google credentials file was absent. Therefore this real smoke used the Google Drive connector, with literal stringValue cells; it did not run the Python SDK adapter's authentication, RAW values.update, appProperties creation/search or SQL claim path against live Google/SQL. Those adapter paths executed against the stateful mock Google client. Do not treat the connector smoke as full deployed-adapter proof.

Remaining: provide an authorized runtime credential/storage identity compatible with the unshared-owner-only adapter before its direct SDK smoke; shared-drive/team sharing requires a separately reviewed destination policy. Large-roster/provider sizing, real SQL concurrency, live delayed writes and end-to-end restart recovery remain unproved. An uncertain create with insufficient terminal evidence remains blocked for operator reconciliation. Concrete Discord/file transports remain outside this Sheets continuation; no background integration or public posting was added.

### 9. Security Review Decision and Evidence

Completed **Changes** review, Deep **off**, for the final exact nine-file task patch, base/head `7baf92c7badc3f40006841046825a788bc823373`. Scan `f4ec6632-9b31-42df-b616-ffbc581cc123`; digest `codex-security-snapshot/v1:sha256:1d13e42d419c8b71643da7d9e6646b1c43947dfc95e9086f98a3273011b53051`. Sealed readback: **zero reportable findings**, complete coverage of six runtime files plus three test files, no deferred candidates. Fresh preflight passed; Daybreak granted; independent architecture pass retained. The earlier scan remains historical evidence for the earlier interface-only patch. Canonical artifacts are retained privately under `%TEMP%/codex-security-scans-9H1QC0/s4b-adapter/7baf92c7badc3f40006841046825a788bc823373_20260910T180802Z_dne0s_5l`. Measured token usage was not returned.

SQL: separate no-change skip at `44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Documentation only records authorized scope/evidence; no separate runtime effect. No standard/deep audit or automatic new task was launched.

### 10. Deployment Steps

None. Only the two separately authorized synthetic Google files above were created. No KVK LIST edits, real data export, SQL/Discord operation, production change, restart, deployment or activation. Retain smoke files for review. No cleanup/deletion was performed. Stop at S4B review; PR remains separately authorized.

### 11. Deferred Optimisations

No unrelated optimisation item added. Existing WS1 and legacy aggregation debt remain separate. Credential/storage compatibility, direct SDK smoke, real SQL concurrency and later integration are explicit readiness gaps, not silently accepted operational guarantees.

## S4B authorized disposable SQL and representative-volume evidence (2026-09-10)

This continuation records the operator's My Drive destination decision and authorization to create synthetic files and a disposable SQL database. It supersedes the preceding real-SQL-concurrency gap only to the extent measured below. No runtime or test source bytes changed in this continuation; the prior exact Changes security review remains applicable to those bytes.

### 1. Scope and authorization

My Drive is the intended storage. Created only the new local `K98_S4B_Disposable_20260910` on verified `9SX2VF4\K98DEV`; installed the two accepted prerequisite migrations into this empty database, without executing predecessor task packs. Retained S2A/S2B/S3B databases were not written or removed. No production connection, Discord action, activation, restart, Git promotion or PR.

### 2. Credential finding

`constants.py` reads `GOOGLE_CREDENTIALS_FILE` from environment/.env, defaults to `credentials.json`, and resolves it against the bot directory. `gsheet_module.get_gsheet_client` loads this as a service-account JSON credential. The effective local filename is absent; no credential content was read or recorded. The bot-machine credential's presence was not checked. Google documents that service accounts cannot own files and have no Drive storage quota. Owner-only My Drive creation therefore needs user OAuth credentials, or explicitly configured Workspace user impersonation where applicable. The adapter already accepts injected Google credentials, but a runtime user-authentication path and direct SDK proof remain outstanding. The connected Google account's earlier file creation does not establish bot runtime authentication.

### 3. SQL proof method

A guarded temporary harness outside Git (`%TEMP%/k98-s4b-sql-proof.py`) connected only to the exact new local database and verified actual server/database on every connection. It reused synthetic observation/config fixtures, created synthetic season `66499316`, selected an interim publication, loaded the pinned export through the real DAL and exercised delivery with fake remote destinations. Source routing remained disabled. This was a nine-check integration harness, not nine additional pytest tests.

### 4. SQL outcomes

All nine checks passed: pinned SQL export loading; confirmed delivery; duplicate suppression without further transport writes; receipt read through a fresh repository; two-connection destination exclusion; private-write failure followed by successful retry; retry fence increment to 2; uncertain publish persistence; refusal of blind retry after uncertainty. Twelve export tables contained 5,696 cells in this small synthetic fixture. The database is retained for review. This is not full restart/delayed-network or combined live-Google/SQL validation.

### 5. Representative legacy sizing

Read-only inspection of the existing KVK_ALLPLAYER_OUTPUT identified KVK 15, 9,194 populated unique player IDs in Player_Full, nine configured windows, and 83 scan-log entries. Scan-log row counts range from 5,000 to 9,194 and total 634,738; maximum seven imports on one legacy timestamp date. These are import-log timestamps, not authoritative UTC scan starts. Observed current workbook rows must not redefine fixed B0 eligibility.

Player_Windowed populated window-label counts: Baseline 11,990; Pass 4 8,856; 1st Altar 7,701; 2nd Altar 7,861; 3rd Altar 8,016; Pass 7 8,317; Great Zig 8,246; Pass 8 8,246; Pass 9 8,246; Full 9,194. These are rows, not independently deduplicated people per window. No private player IDs or names were saved in Git.

### 6. Newly established capacity blocker

The current generation emits 18 player metric rows per player, copied into its typed section (40 columns), ALL_WINDOWS (40), and COMPARISONS (41). A single 5,000-player period therefore needs at least 10,890,000 player cells, before headers, aggregate facts and ingest diagnostics. Google Sheets has a 10,000,000-cell spreadsheet limit. The current single-workbook layout cannot support representative volume. This is an implementation readiness blocker, not an expected deferred operational check. No oversized synthetic Google workbook was attempted.

### 7. Proposed bounded next design

Use a compact physical Sheets projection with period/publication metadata stored once, player metrics represented as columns, explicit missing/status fields retained, and bounded workbooks per period or shard referenced by a versioned index. Preserve exact selected endpoints, UTC scan starts, B0 membership, independent aggregates and semantic deduplication. Validate cell budgets before any remote creation. The exact projection/manifest adjustment has not been implemented or approved as a changed schema by this evidence entry.

### 8. Validation boundary

The preceding 84 focused / 3,874 full pytest results remain historical results for unchanged source bytes; they were not rerun for this evidence-only continuation. New evidence is the isolated real-SQL nine-check harness and read-only representative-volume inspection. Neither closes the direct Python Google SDK authentication/appProperties path or production-sized export proof.

### 9. Security review

No runtime patch changes; retain the preceding exact Changes review, Deep off. SQL repository has no diff; installing accepted migrations in the newly authorized disposable database does not create a SQL repo patch. No standard/deep scan or automatic task was started.

### 10. Delivery and gaps

The earlier private synthetic generation and index remain the actual Google creation evidence. SQL claim/concurrency proof is now available. Remaining blockers: configure My Drive user credentials without committing secrets; replace the oversized physical layout and validate realistic synthetic volume; run direct SDK creation/readback/appProperties/reconciliation plus combined SQL delivery. Full delayed-operation and restart recovery still require explicit measured evidence. No live destination activation is authorized.

### 11. Preservation

All pending S4A closeout documentation and archive moves are retained. This evidence is appended only to the S4B pack. The exact nine source/test files and thirteen-document/fifteen-path future PR boundary remain unchanged. Stop for review; no PR or operational rollout.

## S4B registered My Drive adapter and capacity fixes — final delivery (2026-09-10)

This is the current delivery record. It supersedes earlier adapter/storage/capacity gap statements only where the measured evidence below closes them. The operator approved user-created My Drive files shared with the existing service account as Editor, synthetic validation and fixing the identified issues. Earlier entries remain historical evidence.

### 1. Summary

Implemented explicitly registered, reusable native Google Sheets destinations. The adapter does not create files or change sharing. Missing/inaccessible registered files return setup-required instructions to create/share/register a replacement. It validates the specified owner and service-account Editor, rejects additional sharing and protected destinations, and uses the existing service-account credential model; user OAuth is not required.

Fixed the real provider rejection when replacing the last sheet: one atomic batch shrinks old grids, adds generation-specific replacement tabs, then deletes retired tabs. Added a lossless compact physical Sheets projection and deterministic row partitioning across workbooks. Every logical section and directory link is read back and verified before the index changes. Canonical V2/CSV output remains separate; no source calculation or legacy overall summation was substituted.

Exact B0 membership, endpoint identities, UTC scan starts, equal-endpoint zero supported fight scores/aggregate not-applicable, explicit ordinary missing values, separate aggregate overall and semantic generation deduplication remain covered. No daily SCANORDER or routing change.

### 2. File Manifest

Exactly the section 11 nine Python paths remain the source/test boundary: six new files and three modified files listed below. This pack is the only documentation path appended during the fixes. All thirteen carried-forward logical documents/fifteen physical paths at entry remain required for any separately authorized PR, including both source deletions and untracked destinations of the S4A pack/starter archive moves. Existing Markdown content was hash-verified before this appendix; final preservation checks cover all other bytes and repaired local links.

Bot remains `main` at `7baf92c7badc3f40006841046825a788bc823373`, origin=K98-bot-mirror and production=private K98-bot. SQL remains clean `main` at `44afa315dd6cbfe9fec101f2a39a62e534f5b583`, origin=K98-bot-SQL-Server. The primary index is empty. Exact source bytes were copied into a detached local security worktree; no branch, commit, pull, push or PR was created.

### 3. New Files

- `kvk/services/new_source_export_service.py`: pinned canonical generation, compact Sheets loading, registered destination validation, multipart writing/readback, directory/current pointer and conservative reconciliation.
- `kvk/services/new_source_delivery_service.py`: durable orchestration, setup-required outcomes, explicit receipt identity and uncertainty handling.
- `kvk/dal/new_source_delivery_dal.py`: pinned reads, parameterized claims/fences, destination serialization, publication gate and conservative slot-reuse eligibility.
- `kvk/rendering/new_source_export.py`: exact text/Decimal/UTC tables, stable hashes and inert CSV rendering.
- `tests/test_kvk_source_exports.py`: endpoint/B0/precision/source contracts and lossless projection/multiple-period tests.
- `tests/test_kvk_source_delivery.py`: fake destinations, SQL contract tests, provider request model, setup/ACL/retention/reuse, multipart verification and replacement-order regression coverage.

### 4. Modified Files

- `kvk/services/kvk_export_service.py`: explicit named V2 binding and dormant loading; legacy schema fallback is rejected.
- `gsheet_module.py`: thin explicit new-source delivery dispatch; other changed hunks are mechanical formatting, with legacy export behavior retained.
- `tests/test_kvk_export_service.py`: strict binder and thin dispatch isolation tests.
- This S4B pack: append-only actual delivery/evidence, preserving previous entries.

### 5. SQL Changes

No SQL repository patch or new schema/migration. Reuse eligibility reads accepted `SourceDelivery`, `SourcePublication` and `SourceSelection` definitions. It rejects missing evidence, selected/final publications, claimed/uncertain operations and non-failed Discord references. Existing destination locks and owner/fence checks remain authoritative; no receipt/history deletion or age-based reclamation.

Fresh guarded synthetic integration ran only against `K98_S4B_Disposable_20260910` on verified local `9SX2VF4\K98DEV`. Temporary harnesses `%TEMP%/k98-s4b-sql-proof.py` and `%TEMP%/k98-s4b-reuse-proof.py` passed twelve checks using synthetic season `46989389`: the preceding nine claim/dedup/concurrency/failure/uncertainty checks, plus selected reuse denied, superseded terminal live reuse allowed, and uncertain reuse denied. These are twelve harness assertions, not additional pytest tests. Routing stayed disabled. Retained predecessor databases were preserved.

### 6. Helpers Reused

Reused existing source snapshot/calculation contracts, explicit ExportSelection/ExportTable hashes, V2 binder, CSV formula neutralization, parameterized transaction/selection locking and receipt construction. Google values are literal RAW strings with bounded request batches and HTTP timeouts. The adapter uses explicit file IDs; there is no name lookup, OAuth setup, automatic sharing, credential discovery or default production connection.

For larger Sheets exports use `load_sheets_generation(connect=..., selections=...)`: it compacts each pinned period before combination. The concrete transport also prepares a canonical input before claiming delivery. The compact manifest determines the actual delivery key; downstream consumers must use the returned receipt's key. For a changed multi-period generation, the caller must supply a suitable changed selection as its delivery anchor. An unchanged anchor with a changed key is rejected by the DAL; the adapter does not infer another selection or silently overwrite a confirmed receipt. This caller orchestration case is not covered by a multi-period delivery integration test.

### 7. Refactor Findings

The earlier single-workbook capacity blocker is fixed in the physical adapter. Context is referenced once and metric values/status/raw/unit/precision/rank/cohort remain reconstructible. Logical sections are partitioned by rows; the first workbook DIRECTORY links all parts. A 9,000,000-cell adapter ceiling with directory reserve leaves headroom below the provider maximum. Insufficient registered slots fail before destructive reuse.

Retention is deliberately conservative: current, uncertain, referenced and final generations cannot be reused. Any generation containing a final stream is retained in full. Thus nine files is an initial current/staging allowance at the measured size, not a lifetime cap; repeated mixed live/final generations can require further registered sets. Smaller retention storage would require a separately reviewed layout/lifecycle change, not silent deletion of final evidence.

### 8. Test Plan and Actual Outcomes

- Exact four-file pack pytest command through `scripts/analyse_pytest_log_noise.py`: **103 passed in 7.64s**, operational logs unchanged.
- Fresh full suite through the same log guard: **3,893 passed, 34 skipped in 171.08s**, operational logs unchanged. Only formatting followed that full run; focused tests and validation ran on the final source bytes.
- Imports passed; registration remained **36 primary / 100 grouped**, no drift or duplicates.
- Architecture validator passed all nine Python paths; security-routing validator passed with zero errors/warnings; test selector requested full pytest/imports/registration, all completed.
- Applicable pre-commit checks passed, including Ruff, Pyright and hardcoded-secret detection. The Black CLI stalled; its hook was explicitly skipped and all nine files instead passed direct Black API formatting/checking with repository settings (100 columns, Python 3.11). No source bytes changed after the sealed scan snapshot.
- Synthetic capacity harness `%TEMP%/k98-s4b-capacity-proof.py`: **10,000 players across ten periods**, **34,217,924 logical grid cells**, **four workbooks per generation**, **194.22s** local build. Physical part sizes were 8,989,895 / 8,989,959 / 8,989,966 / 7,248,432 cells. **Nine files** covers two sets plus index before retention needs. Fixtures were wholly synthetic, sized from aggregate legacy evidence; no private player rows were saved. This proves projection/partition sizing, not large Google upload throughput.
- Real synthetic provider proof: [registered-slot API proof workbook](https://docs.google.com/spreadsheets/d/1ckptZ3ShITfhWmxIDfPCd2rWEJ1Aquig8qwoX_t6ICE/edit). The previously rejected delete-last-sheet batch was replaced with shrink/add/delete; the provider accepted it and returned the sole replacement tab at the requested 2-by-27 grid. The earlier two synthetic files remain retained. Connector execution does not prove Python SDK service-account authentication/appProperties or combined SQL/Google delivery.

Remaining integration evidence: direct service-account SDK metadata/write/readback/reconciliation; combined disposable-SQL/Google execution; large-upload duration/quota behavior; measured delayed-operation and process-restart recovery. No claim of remote exactly-once is made. Uncertain operations remain blocked for reconciliation.

### 9. Security Review Decision and Evidence

Fresh final **Changes** review, Deep **off**, completed and sealed: scan `3b880d6c-6a3e-43fc-aa9d-fee9ad797176`, exact nine-file working-tree snapshot at base/head `7baf92c7badc3f40006841046825a788bc823373`; digest `codex-security-snapshot/v1:sha256:9cde29285aaa057b15111825afa99501460886fa8e94a61add679292d88a7cb3`. Complete coverage of six runtime and three test files, **zero reportable findings**, no deferred security candidates. Dedicated preflight ready, Daybreak status=granted/program=Daybreak Blue; a bounded discovery worker reviewed the large adapter and its tests, parent reviewed the remaining files/supporting controls. Canonical completed artifacts were read back successfully.

Private artifacts: `%TEMP%/codex-security-scans-9H1QC0/s4b-capacity-fixed/7baf92c7badc3f40006841046825a788bc823373_20260910T212314Z_nl3u1gmz/` (`report.md`, manifest, findings, coverage and SARIF). Tool-reported rollout usage: 1,165,995 total tokens, including 1,119,488 cached input; this is the tool's accounting, not an independently measured review-only budget. The preceding registered scan `97c5bef9-c020-4514-9f5c-79dfd1e18d8e` was recovered and sealed but covers earlier bytes; it does not replace this final scan.

SQL separate no-change skip at `44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Documentation records scope/evidence only. No standard/deep audit or automatic new task.

### 10. Deployment Steps

None. Source routing remains disabled; no production SQL/data, real exports, Discord actions, bot-machine update/restart, activation, deployment, Git promotion or PR. Stop at S4B review.

To unblock direct runtime smoke, provide dedicated blank native Sheets IDs owned in the operator's My Drive and shared only with the service account as Editor, plus secure availability of the existing JSON credential in the authorized test environment. A small proof needs an index and two slots; the representative full-size current/staging proof needs an index and eight slots. Supply the credential path securely, not its contents in chat/Git. No new OAuth account is needed. The existing connector-created proof files are not automatically registered or assumed to satisfy the service-account ACL contract.

### 11. Deferred Optimisations

No unrelated optimisation item added. Existing WS1/legacy aggregation debt remains outside this slice. The explicit caller-anchor contract, conservative final retention, direct-auth/provider-volume/restart evidence and later dormant API integration remain visible review limitations. Implementation fixes and local validation are complete for this continuation; external smoke and operational activation are not represented as complete.


## S4B direct service-account preflight and SDK fix (2026-09-11)

### 1. Summary

The operator supplied three dedicated test Sheets and the local production-model service-account JSON. Direct authentication and exact-file metadata/content reads succeeded. All files are correctly named, blank native spreadsheets with one Sheet1 tab, operator ownership and service-account Editor access. Each also has anyone/reader sharing; the registered private-output contract rejects this. The operator was asked to set General access to Restricted. No file content, metadata, sharing or SQL data was changed by this preflight.

### 2. File Manifest

The exact nine-source-file and thirteen-document/fifteen-path boundaries remain. This continuation modifies only the export service, its delivery test file and this append-only evidence. Both repositories retain their preceding branches/HEADs/remotes; SQL remains clean. Pending S4A documents/archive moves and untracked Markdown are preserved.

### 3. New Files

No new Git files. Temporary private preflight script/metadata and public system-CA bundle reside outside Git. The supplied credential is Git-ignored; its contents were not displayed or recorded in evidence.

### 4. Modified Files

`kvk/services/new_source_export_service.py`: pass `timeout=timeout` to httplib2.Http. The positional argument incorrectly selected its cache parameter and raised AttributeError before authentication. `tests/test_kvk_source_delivery.py`: regression constructs both real HTTP objects through mocked API build and verifies bounded timeout plus disabled cache. This pack records outcomes.

### 5. SQL Changes

None. Existing SourceDelivery schema was cross-checked; no SQL smoke operations were started while the file ACL prerequisite is unmet. The authorized disposable database and all retained predecessor databases remain untouched in this continuation.

### 6. Helpers Reused

Existing registered transport and Google service-account SDK. Local certificate validation required a temporary CA bundle sourced from the existing system trust store through HTTPLIB2_CA_CERTS for the smoke process. TLS verification remained enabled; no persistent certificate/config change or new trust root was installed.

### 7. Refactor Findings

The direct SDK path exposed a constructor defect missed by request-level mocks; fixed narrowly. No OAuth, production wiring, sharing change or unrelated refactor.

### 8. Test Plan and Outcomes

Exact four-file focused command through log-noise guard: 104 passed in 9.59s. Fresh full suite: 3,894 passed, 34 skipped in 168.86s. Both left operational logs unchanged. Imports and registration 36/100 passed without drift. Architecture nine-file check, security-routing validator, applicable hooks including Ruff/Pyright/secrets passed; selector-required full/import/registration gates completed. Black hook remained skipped for the previously recorded CLI issue; modified files were formatted with its API and repository settings.

Direct service-account authentication/read gap is closed. The three observed titles are K98 S4B TEST - Index, Slot 01 and Slot 02. Owner plus service-account writer plus anyone/reader is the observed three-permission state. Real writes/appProperties, combined disposable-SQL/Google delivery, large-upload performance and process restart/delayed-operation recovery remain unproved. No request-level mocked pass is substituted for these outcomes.

### 9. Security Review Decision and Evidence

Final Changes review, Deep off: cbd27586-19f7-4c66-9668-05169215c16e. Exact nine-file snapshot base/head 7baf92c7badc3f40006841046825a788bc823373; digest codex-security-snapshot/v1:sha256:8240ef228e8b105ef2eee4692e79ed82f26b4d127f27a3c2324515b8b630a8e7. Complete coverage, zero reportable findings/deferred candidates, sealed readback verified. Prior full review retained for byte-identical code; independent fresh review covered both changed SDK hunks and the installed constructor contract. Preflight ready; Daybreak granted / Daybreak Blue. SQL separate no-change skip at 44afa315dd6cbfe9fec101f2a39a62e534f5b583. No standard/deep audit or new task.

Private artifacts: %TEMP%/codex-security-scans-Lnj9jc/s4b-sdk-smoke/7baf92c7badc3f40006841046825a788bc823373_20260911T095414Z_g1k1j125/. Tool-reported rollout usage 1,778,250 total tokens including 1,730,688 cached input; not an independently measured review-only budget.

### 10. Deployment Steps

None. No writes to the supplied Sheets, production/Discord operations, Git promotion, restart, deployment or activation. Next required input is confirmation that all three files have General access Restricted, retaining owner and service-account Editor. Credential and file IDs are otherwise sufficient for the small synthetic smoke.

### 11. Deferred Optimisations

No unrelated optimisation added. Existing retention/anchor and operational proof limits remain recorded. Preserve the prior complete delivery evidence; this preflight closes authentication/read only.


## S4B real SDK / disposable SQL smoke — measured outcome (2026-09-11)

This record supersedes the preceding no-write/pending-ACL status. The operator changed all three test files to Restricted; fresh service-account reads verified exactly owner and service-account Editor permissions before writes. The operator also clarified that production exports must support Anyone with the link / Viewer for players. That is a required production behavior, not an instruction to publish these synthetic test files.

### 1. Summary

Real service-account plus disposable-SQL delivery confirmed two synthetic generations. Initial interim export took 35.11s; the selected final replacement took 28.02s. Complete logical manifests were read back. A separate process subsequently reloaded the final receipt, reconciled its actual remote manifest/pointer and deduplicated repeat delivery. A later slot-reuse attempt became uncertain and remains blocked; do not label the whole smoke passed.

### 2. File Manifest

No further source changes after the preceding sealed nine-file SDK-fix review. This evidence is appended only to the S4B pack. The complete existing documentation/archive manifest remains preserved. Credential and temporary harness/result files stay outside Git.

### 3. New Files

No new Git files or new Google files. The three operator-created native Sheets were the only remote write targets. Temporary harnesses/results are retained privately as %TEMP%/k98-s4b-real-sdk-proof.py, k98-s4b-real-sdk-reopen.py, k98-s4b-real-sdk-reuse.py and k98-s4b-real-sdk-result.json.

### 4. Modified Files

Only this evidence appendix in Git since the preceding validation. Remote index and both registered slots received synthetic content/metadata through the actual adapter; no permission changes were made by the adapter or smoke.

### 5. SQL Changes

No SQL repository/schema change. Exact server/database checks guarded every connection to local 9SX2VF4\K98DEV / K98_S4B_Disposable_20260910. Synthetic season 48303483 supplied interim and final publications; season 39356343 supplied a fresh live publication for retired-slot reuse, preserving the first season's configured final endpoint. Both seasons' SourceRouting.Enabled remained false. Predecessor databases and production were untouched.

### 6. Helpers Reused

Actual GoogleSheetsTransport.from_credentials, DeliveryRepository, load_sheets_generation, deliver_export and read-only reconciliation; accepted synthetic source/import/publication helpers supplied two synthetic players per season. The existing test database was reused without reset. No legacy data was imported/exported.

### 7. Refactor Findings and Remaining Blockers

The extra reconciliation reads hit Google Sheets HTTP 429, ReadRequestsPerMinutePerUser=60. Paced read-only recovery at 2.1 seconds between adapter requests passed in a separate process. This pacing is a temporary harness measure, not a production adapter rate limiter. Production shares the service-account/project quota; do not infer sufficient production throughput from this small smoke.

The third attempt selected the reusable superseded interim slot, rebound its appProperties to the new generation, then returned uncertain after 13.55s. Readback shows Slot 01 retains its old generation tabs while metadata identifies the attempted replacement. The provider mutation's underlying error was not retained by the orchestration result, so its exact cause is unproved. Improve sanitized provider-error evidence and reconcile/recover this state before retry or further destination writes. No blind retry, receipt reset, manual tab cleanup or assumed absence proof was performed.

Production public Viewer sharing is currently rejected by the exact-two-permission check. It requires an explicit supported publication/audience policy and validation before activation; simply changing production sharing would break this adapter. Private staging, verified publication, output audience and retained-final behavior must stay explicit. This smoke does not authorize public exposure or activation.

### 8. Test Plan and Actual Outcomes

Passed: direct credential authentication; exact IDs/owner/editor/blank preflight; real metadata binding and literal writes; initial and replacement private generation creation; twelve-section full readback; index/fence publication; durable confirmed receipts; repeated-delivery deduplication; separate-process final receipt reload and real remote reconciliation. Full-source validation remains the preceding fresh 104 focused / 3,894 full / 34 skipped result, with operational logs unchanged.

Not passed: actual retired-slot reuse. Read-only final inspection confirmed SQL receipt uncertain, reconciliation unknown, and current index unchanged at final generation fence 2. Quota handling, failed-reuse diagnostics/recovery, large uploads/multipart network throughput, crash-during-operation behavior and production public Viewer support remain open. No exactly-once or complete restart/failure-recovery claim.

### 9. Security Review Decision and Evidence

Source bytes remain identical to sealed Changes scan cbd27586-19f7-4c66-9668-05169215c16e, Deep off, with zero reportable findings. The existing runtime/security limitations remain; the new observations above are operational evidence, not another code patch or a reason to run a standard/deep scan. SQL repository separate no-change skip retained. No new task or promotion.

### 10. Deployment Steps / Retained Remote State

None. [Test index](https://docs.google.com/spreadsheets/d/1xwF92PbxgXD0InA-ekuEPkN8MA5pgd1navpMyxEe6_Y/edit) still points to [verified final Slot 02](https://docs.google.com/spreadsheets/d/1_Jb6hkBreXTR256MEYgFAraKDjytcQtCjEPe26qABFg/edit#gid=1373862699). Slot 01 and its uncertain receipt are retained for diagnosis. No further setup input is required for these three test files or the credential. Preserve their restricted sharing while recovery is reviewed; public production support is a separate outstanding implementation requirement before rollout. No production/Discord/restart/deployment/activation or Git promotion occurred.

### 11. Deferred Optimisations

No unrelated optimisation added. The evidenced quota/reuse recovery defects and public Viewer requirement are readiness blockers to address, not accepted deferred production behavior. Stop at review with the two confirmed deliveries and uncertain third attempt clearly distinguished.


## S4B recovery, pacing and public Viewer proof (2026-09-11)

This appendix supersedes the previous open reuse/recovery/public-audience status. The operator approved implementing and proving the proposed recovery and public Viewer model. Only synthetic files/data and the existing isolated S4B database were used; public permission changes below apply only to those synthetic test outputs.

### 1. Summary

Fixed frozen-grid slot reuse, added sanitized provider diagnostics, bounded read retries and process-wide service-account pacing, and implemented explicit private/public_viewer publication. Recovery durably fences a stopped private attempt and quarantines every possible old slot before continuing in disjoint registered files. Publication/permission uncertainty is never reclaimed by this path.

### 2. File Manifest

The same exact nine Python paths remain the complete code/test manifest. The thirteen-document/fifteen-physical-path manifest remains intact, including both sides of both S4A archive renames and repaired links. This continuation appends only this S4B pack; its entire prior byte prefix and all other pending Markdown are preserved. No PR or Git promotion is authorized/performed.

### 3. New Files

No additional Git files beyond the already approved manifest. Two operator-owned synthetic recovery workbooks were created and shared with the existing service account as Editor. Private scripts/results stay outside Git: %TEMP%/k98-s4b-public-recovery.py, k98-s4b-public-recovery-result.json, k98-s4b-public-cycle.py and k98-s4b-public-cycle-result.json. The credential remains Git-ignored and untracked; no key material or private player data is included here.

### 4. Modified Files

Changes in this continuation are limited to kvk/services/new_source_export_service.py, kvk/services/new_source_delivery_service.py, kvk/dal/new_source_delivery_dal.py, tests/test_kvk_source_delivery.py and this evidence appendix. The adapter unfreezes grids in a separate first subrequest before shrinking/adding/deleting tabs in one atomic batch. Sanitized diagnostics retain only allowlisted operation, HTTP status and reason; provider prose, request URLs/bodies and values are omitted. BatchGet reduces verification reads; real SDK requests are paced at 2.1 seconds per service-account identity per process. GET 429/503 retries are bounded to three attempts; mutations are not automatically retried.

### 5. SQL Changes

No SQL repository/schema changes. The existing KVK.SourceDelivery columns and nvarchar(1024) Receipt contract were verified against the SQL source of truth. Private and publication-pending checkpoints, attempt slot identities and quarantine evidence use that bounded receipt. Recovery issues a new owner/fence while retaining quarantine evidence across later receipts. Oversized evidence fails closed; no schema widening or evidence truncation. Every smoke connection asserts the exact local server and K98_S4B_Disposable_20260910 database. Retained predecessor databases and production remain untouched.

### 6. Helpers Reused

Actual GoogleSheetsTransport.from_credentials, DeliveryRepository, load_sheets_generation, deliver_export and remote reconciliation; existing synthetic accepted-observation/publication fixtures. Exact operator registration remains required. Missing/inaccessible files return setup instructions to create/register dedicated Sheets and grant the service account Editor; the runtime adapter still does not create Drive files or configure OAuth. An explicit public_viewer registration permits only owner, service-account Editor and one non-searchable anyone/reader permission. Other users, domains, public writers and searchable sharing fail closed.

### 7. Refactor Findings

A minimal real Google reproduction confirmed HTTP 400 when shrinking a grid with a frozen header: Google rejected deleting all non-frozen rows. Separate unfreeze then shrink/add/delete subrequests succeeded. The previous uncertain attempt was not blindly retried or declared absent: both original slots were quarantined, its SQL fence advanced from 3 to 4, and the same exact generation was rebuilt in fresh slots. The original two workbooks were read back unchanged.

Before reusing a formerly public slot, the adapter removes Viewer sharing and confirms Restricted access. It writes and verifies all twelve logical sections and the directory privately; only then may it grant Viewer access and update the fenced index. Any ambiguous grant or pointer operation stays uncertain. Readback and deduplication use durable SQL evidence. A previously confirmed private delivery does not silently change audience on a repeat call.

### 8. Test Plan and Actual Outcomes

Exact four-file pack tests through the log guard: **117 passed in 8.21s** on final source; operational logs unchanged (preceding focused run: 117 in 7.74s).
Fresh full suite through the same log guard: **3,907 passed, 34 skipped in 149.24s**; operational logs unchanged.
Imports and registration passed at 36 primary / 100 grouped, without drift. Architecture, deferred-item and security-routing validators passed; selector-required full/import/registration checks completed. Applicable pre-commit checks including Ruff, Pyright and secrets passed. The known Black CLI stall was handled by an explicit hook skip plus direct Black API validation of all nine files with repository settings. Only lint/import/annotation/formatting changes followed the full suite; focused tests passed on final byte-identical scan source.

Real combined service-account SDK and guarded disposable-SQL results:

| Operation | Outcome | Duration | Durable fence |
| --- | --- | --- | --- |
| Recover exact previously uncertain private generation into fresh slots | Confirmed; original slots unchanged | 148.69s | 4 |
| Next selected endpoint publication | Confirmed; fresh-client reconciliation and dedup passed | 141.16s | 5 |
| Reuse retired public slot, rebuild privately, verify and republish | Confirmed; fresh-client reconciliation and dedup passed | 140.06s | 6 |

All three runs completed full remote manifest/directory readback with no terminal provider error recorded. The two new slots are [recovery Slot 03](https://docs.google.com/spreadsheets/d/1bcqUkN3fySc34BsEDo_nflU3hfHJLqe5pBM6med9VS4/edit) and [Slot 04](https://docs.google.com/spreadsheets/d/1H9kXpIl0Vg5zv1CoLghp680j0Q90mD3fE_IpIIPG-7M/edit). The [test index](https://docs.google.com/spreadsheets/d/1xwF92PbxgXD0InA-ekuEPkN8MA5pgd1navpMyxEe6_Y/edit) now identifies fence 6 and [the verified reused generation](https://docs.google.com/spreadsheets/d/1bcqUkN3fySc34BsEDo_nflU3hfHJLqe5pBM6med9VS4/edit#gid=326190829). Synthetic seasons used in this continuation: 39356343 and 218947299; routing remained disabled.

The earlier local 10,000-player/ten-period capacity result remains sizing evidence only: four workbooks per generation, initially nine files for current/staging/index. Large multipart Google upload throughput and shared production quota under load remain unmeasured. Process pacing cannot coordinate another machine/process using the same service account. New tests cover bounded read retry, no mutation retry, sanitized errors, private/public ordering, unexpected ACL rejection, ambiguous permission outcomes, quarantine persistence, and refusal to recover publication uncertainty. An actual process kill while a provider request remains in flight was not induced; deterministic fault tests and durable recovery/readback are the evidence, not a universal exactly-once guarantee.

### 9. Security Review Decision and Evidence

Fresh final Changes review, Deep off, completed/sealed/read back: scan `15b30d80-e074-4a01-87ce-1237b1ca30d9`. Exact isolated target `.codex_scan_stage/s4b-recovery-public`, base/head `7baf92c7badc3f40006841046825a788bc823373`, digest `codex-security-snapshot/v1:sha256:0221b7a40a9151e5e80baaac575872522dcbb2ba066ee0d5ee6924b788aa31ac`. All six runtime and three test files accounted for; zero reportable findings, no deferred security candidates. Dedicated capability preflight ready; Daybreak status=granted, program=Daybreak Blue. Independent architecture and bounded whole-file adapter reviews supplemented the parent DAL/service/wrapper/renderer/test review. Canonical source anchors were checked. No source bytes changed after the scan snapshot.

Private report and canonical artifacts: `%TEMP%/codex-security-scans-Lnj9jc/s4b-recovery-public/7baf92c7badc3f40006841046825a788bc823373_20260911T103850Z_45c_j1zw/`. Tool-reported complete rollout accounting: 5,825,194 total tokens; 5,802,601 input, including 5,588,480 cached input. This is the tool's rollout measurement, not an independently measured review-only budget.

Separate SQL no-change skip: clean main at `44afa315dd6cbfe9fec101f2a39a62e534f5b583`, origin K98-bot-SQL-Server. Bot main remains `7baf92c7badc3f40006841046825a788bc823373`, production/main `021fc7adc9952ab07d21517e8e47f3966c285f7a`; origin K98-bot-mirror and production K98-bot remotes unchanged. Primary index remains empty. No standard/deep audit or automatic user task was created.

### 10. Deployment Steps / Retained Remote State

None. Source routing remains disabled. No production SQL/data/import/export, Discord action, restart, deployment, activation, pull/reset/merge/push or PR. The synthetic index remains the stable entry point; original Slot 01 and Slot 02 are retained and quarantined from future adapter writes. New registered slots are the recovery/current-staging set. Public Viewer sharing is enabled only for verified synthetic outputs and their index. Missing future capacity still requires owner-created registered workbooks. No OAuth setup or additional user input is needed for this small proof.

### 11. Deferred Optimisations and Remaining Gaps

No unrelated optimisation item was added. The concrete frozen-grid, diagnostic, private recovery and public Viewer implementation blockers are closed by the recorded tests and real smoke. Production activation, large shared-quota throughput, real crash-during-request testing and the previously documented multi-period changed-anchor orchestration proof remain outside the completed evidence. Conservative final/reference retention and bounded recovery evidence can require more files or a fresh destination; do not reclaim retained/quarantined files to bypass those limits. Stop for S4B review; no predecessor/later pack was executed.


## S4B multi-period closure and named handoff - 2026-09-11

### 1. Summary

The operator approved completing the remaining synthetic multi-period test and updating the documentation so the remaining checks have explicit owners and acceptance gates. S4B-MP01 is now complete at the component-integration boundary. No runtime fix was required. S5B/S6 were documented, not executed; S4B stays local for review, with no PR, merge or activation.

### 2. File Manifest

This continuation changes only `tests/test_kvk_source_delivery.py` and the following documentation paths:

- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/kvk_source_migration/decision_and_evidence_register.md`
- `docs/reference/kvk_source_migration/phase_2_implementation_plan.md`
- `docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S4B Versioned Exports and Delivery.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S5B Endpoint Config and Recovery Integration.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S6 Release Readiness and Controlled Activation.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S4B Versioned Exports and Delivery.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S5B Endpoint Config and Recovery Integration.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S6 Release Readiness and Controlled Activation.md`
- `docs/task_packs/KVK Source Migration - Programme Pack.md`
- `docs/task_packs/README.md`

The eventual separately authorized S4B PR must preserve the original thirteen-document/fifteen-physical-path manifest, including both sides of both S4A archive renames, and add these four explicitly authorized documentation paths:

- `docs/task_packs/Codex Task Pack - KVK Source Migration S5B Endpoint Config and Recovery Integration.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S5B Endpoint Config and Recovery Integration.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S6 Release Readiness and Controlled Activation.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S6 Release Readiness and Controlled Activation.md`

Total documentation handoff: **seventeen logical documents / nineteen physical paths**, alongside the unchanged nine-Python-file S4B implementation manifest. This is a documentation-only expansion authorized by the current request, not permission to implement another slice or stage unrelated files.

### 3. New Files

No new application/test/document paths. Only private temporary preservation evidence was created. Added a narrow local Git exclusion for the already existing `.codex_scan_stage/s4b-recovery-public/` review checkout, which was appearing as untracked; no review artifact/source was deleted or changed and the primary index remains empty.

### 4. Modified Files

One new parameterized test, `test_multi_period_delivery_uses_changed_anchor_and_deduplicates`, covers each of two fights changing in turn. The real generation loader, delivery orchestration, DeliveryRepository.claim decision and Google transport are composed with injected SQL I/O and fake Google storage. The test checks unchanged-anchor rejection before remote calls, successful changed-anchor publication, an increasing fence, unchanged period facts, both fights in ALL_WINDOWS, missing overall explicitly not_received, changed metric output, exact remote manifest/current pointer, retained previous workbook and zero additional calls after receipt reload/repeat. Input order does not change the generation key.

The documentation assigns stable check IDs, owners, closure evidence and approval gates in the [follow-up register](../reference/kvk_source_migration/phase_2_implementation_plan.md#s4b-follow-ups), then links them from current entry points, evidence registers, programme pack and affected task packs/starters. All prior Markdown bytes, pending closeout edits and archive moves are preserved.

### 5. SQL Changes

None. SQL remains clean main `44afa315dd6cbfe9fec101f2a39a62e534f5b583`; origin K98-bot-SQL-Server unchanged. No database connection or SQL operation was performed in this continuation. The new test replaces database I/O; it is not evidence of real multi-period SQL concurrency or live Google execution.

### 6. Helpers Reused

Existing export_input, FakeRepository, google_delivery/GoogleMemoryAPI, ExportSelection, load_sheets_generation, DeliveryRepository.claim and deliver_export. Test-only repository state records confirmed receipts per publication so the production claim decision can distinguish an unchanged confirmed anchor from a changed period. The adapter and runtime persistence implementation remain unchanged.

### 7. Refactor Findings

No runtime defect or unrelated refactor was found. The initial test expectation omitted the intentional missing-overall placeholder; it was corrected to assert the explicit unavailable status, preserving the production contract. No application behavior was changed to satisfy the test.

### 8. Test Plan and Actual Outcomes

- New parameterized integration test: **2 passed in 1.57s**.
- Exact four-file focused suite through the log guard: **119 passed in 8.90s**, operational logs unchanged.
- Fresh full suite through the same guard: **3,909 passed, 34 skipped in 152.62s**, operational logs unchanged.
- Imports passed; command registration **36 primary / 100 grouped**, no drift or duplicates.
- Architecture validator passed all nine Python paths; deferred validator passed all seventeen Markdown documents; security-routing validator passed with zero errors/warnings. Selector-required full/import/registration gates completed.
- Applicable pre-commit checks passed, including Ruff, Pyright and hardcoded-secret detection. Black CLI hook remained explicitly skipped for the recorded stall; direct Black API formatting/checking uses repository settings. AST comparison against the sealed review target proves the test file differs only by the new parameterized test. All six runtime files remain byte-identical.

Synthetic component integration is the closed S4B evidence. Real multi-period caller/SQL integration belongs to S5B-REC01; real external interruption and representative shared-quota multipart measurements remain S6 gates. No new real SQL/Google/Discord smoke was performed.

### 9. Security Review Decision and Evidence

The six runtime files match sealed Changes review `15b30d80-e074-4a01-87ce-1237b1ca30d9`, Deep off, zero findings. The original nine-file scan remains immutable; it does not include this added test. Incremental security decision: documented no-new-scan for the exact additive synthetic test and documentation delta, reviewed locally. The new test has no live/default connection, credential access, network client, subprocess or production mutation; SQL reads/transactions and Google storage are injected fakes. No permission/configuration/dependency or runtime persistence behavior changed. Existing runtime review evidence is retained, not represented as a fresh scan of different bytes. SQL has a separate no-change skip. No standard/deep scan or automatic new task.

### 10. Deployment Steps

None. Bot remains main `7baf92c7badc3f40006841046825a788bc823373`; origin K98-bot-mirror and production K98-bot remotes unchanged. Source routing remains disabled. No pull/reset/merge/push/PR, production SQL/data, real import/export, Discord action, restart, deployment or activation. Stop for S4B review; S5A is the next separately approved implementation slice after S4B closeout.

### 11. Remaining Acceptance Work

These are named programme acceptance checks, not unspecified optimisation debt:

- **S4B-MP01: complete** - synthetic multi-period component delivery and receipt reload/deduplication.
- **S5B-REC01: open** - default-off worker/caller wiring, disposable SQL transaction/return-error/restart proof, changed-anchor orchestration and daily-claim preservation.
- **S6-OPS01: open before activation** - separately authorized isolated process interruption during private writes, public grants and pointer publication, with durable/external recovery evidence.
- **S6-PERF01: open before activation** - agreed duration/cadence/request budget and measured representative multipart upload/readback under shared quota conditions.
- **S6-CAP01: open before activation** - provisioned current/staging/retained/quarantined capacity and bounded-receipt exhaustion handling; no silent evidence truncation or reuse of protected history.

The S5B/S6 packs and starters now require these IDs explicitly. S6 G3 prepares reviewable plans only; operational execution still needs separate G4/exact-target approval. Required runtime/schema changes discovered by rehearsal need a bounded approved manifest, not automatic expansion of S6.


## S4B mirror PR 269 review fixes - 2026-09-11

### 1. Summary

Operator authorized checking, fixing, responding to and resolving review comments on mirror PR #269. The multipart terminal-rejection retry defect is fixed; the binder test now imports its required names locally. No later slice is implemented.

### 2. File Manifest

This continuation changes exactly `kvk/services/new_source_export_service.py`, `tests/test_kvk_source_delivery.py`, `tests/test_kvk_export_service.py` and this task pack. The complete original PR manifest, seventeen-document/nineteen-physical-path handoff and both S4A archive moves remain preserved.

### 3. New Files

No new repository files. Private security artifacts remain outside Git.

### 4. Modified Files

The adapter validates all existing generation bindings for canonical unique part numbers and an exact manifest, preserves those bindings, and fills only missing parts from blank or safely released slots. Partial sets already built or current require reconciliation. Retained, current, referenced and quarantined destinations remain protected; unknown mutations still block retries. A fresh client can resume terminal 400/403/429 binding rejection without overwriting prior part identity. Strict complete-part, directory and full data verification still precede publication. The two binder constants are imported alongside the local V2 binder import.

### 5. SQL Changes

None. Authoritative SQL remains clean at `44afa315dd6cbfe9fec101f2a39a62e534f5b583`; SourceDelivery receipt/state contracts were inspected. No database connection or live provider operation occurred.

### 6. Helpers Reused

Existing partition_manifest, binding/ACL/private/reuse checks and strict complete-generation verification. Tests reuse GoogleMemoryAPI, FakeRepository and extracted multipart fixture setup from the existing split-parts test.

### 7. Refactor Findings

The in-scope retry defect was fixed and the import-maintainability comment addressed. No unrelated runtime refactor or new deferred optimisation. Two incidental punctuation encoding changes in existing test comments were restored before commit; AST equivalence confirmed no behavioral delta.

### 8. Test Plan and Actual Outcomes

- Twelve multipart regression/negative cases passed in 2.32s: blank and retired-slot retries for 400/403/429, recreated client with reordered registration, exact manifest/current pointer and deduplication, conflicting binding evidence, and uncertain response blocking.
- Exact four-file pack suite: **131 passed in 8.07s**; operational logs unchanged.
- Full suite: **3,921 passed, 34 skipped in 127.41s**; operational logs unchanged.
- Imports passed; registration 36 primary / 100 grouped without drift or duplicates. Selector-required full/import/registration gates completed.
- Architecture and security-routing validators passed; Black API passed with repository settings; final Git diff whitespace check passed. Staged hooks and documentation validation are required during packaging.
- An initial retry fixture omitted the changed selection version from its snapshot and was corrected. An initial focused invocation named a nonexistent report test and collected no tests; the exact pack command above was then run successfully. Neither initial attempt is counted as a pass.

### 9. Security Review Decision and Evidence

Incremental Changes review **b60a799b-cf56-4db0-b634-70427a297431**, Deep off, completed and sealed on 2026-09-11 at 12:02:48 UTC with **zero findings**, covering the runtime fix and both changed test files. Base/head for the immutable working-tree snapshot: `235e8f60fb042803da055d10544fa7419eca1cb4`; snapshot digest `codex-security-snapshot/v1:sha256:e4d9cf32eef51765812f0ca34b87b03c2ef5883d794cd0566e39841e0c437773`. Existing whole-S4B review remains separate retained evidence. SQL has a separate no-change skip.

The first draft submission incorrectly included server-owned coverage fields; validation rejected it and completion failed because scan-manifest.json did not exist. Following the operator's recovery request, the same running scan was repaired using accepted semantic fields, canonical artifacts were verified, and finalization/readback succeeded. This was a tooling/reporting failure, not a vulnerability finding. No replacement, standard or deep scan was started. Subsequent restoration of two test-comment punctuation sequences and this evidence appendix are nonexecutable changes with a documented incremental scan skip; test AST and runtime content are unchanged.

### 10. Deployment Steps

Push only the reviewed fix commit to the existing mirror PR #269, respond with concrete evidence and resolve the addressed inline threads. No private PR/push, merge, deployment, restart, Discord action or activation. Source routing remains disabled.

### 11. Remaining Acceptance Work

S4B-MP01 remains complete. S5B-REC01 and S6-OPS01/PERF01/CAP01 remain explicitly open under their existing owners and approval gates; this fake-destination fix does not close live integration, process-interruption, shared-quota throughput or capacity acceptance.

Final packaging: deferred-document validation and staged Ruff, Pyright, hardcoded-secret, merge-conflict, file-size and logging checks passed. Automatic whitespace/EOF/line-ending rewriting hooks were skipped to preserve prior Markdown bytes; Black CLI retains its documented stall skip and direct API validation passed. Git diff whitespace checks passed.
