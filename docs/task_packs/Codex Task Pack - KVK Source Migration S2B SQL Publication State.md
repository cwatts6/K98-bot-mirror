# Codex Task Pack — KVK Source Migration S2B SQL Publication State

## 1. Task Header

- Prepared 2026-09-09; owner Chris Watts; Phase 2B specification.
- G2 architecture approved, including authorized EndScanID corrections. **S2B G3 pending.**
- One-pass implementation approved: **No**. Execute only after explicit approval of this slice.
- Proposed isolated branch `codex/kvk-source-s2b`; not created during planning.
- Type: SQL implementation.

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

Persist configuration versions, endpoint requests, immutable publications, disabled source routing and delivery receipts.

## 4. Background

Planning anchors: bot main `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`; SQL main
`fc0e94ebd2e0a98286069c8a8b71365dd5178657`. Recheck branches/HEADs/remotes/status at execution,
preserve existing work and record actual start/end hashes. Local definitions are not deployed proof.
No pull/reset/checkout to make a working copy match historical evidence. Use an authorized isolated
branch/worktree where needed. Phase-1 C01-C65 anchor dependencies; G2 fixes source semantics.

## 5. Scope

Predecessors: S2A accepted and S2B G3; explicit disposable SQL target for FK/state checks.

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

Current pack authoring: bot docs-only skip; SQL no-change skip. Future execution: Bot no-change skip; SQL Changes review for this exact migration/snapshot/validator diff, Deep off.
Use k98-security-review-routing first; record exact immutable base/head or task-only authored patch,
Scan type Changes and Deep off. Never scan/stage unrelated dirty files or combine bot/SQL histories.
No routine standard/deep audit. Retain scan coverage/results privately; no public finding details.

## 8. Mandatory Workflow

1. Confirm explicit S2B approval and predecessor evidence; otherwise scope/review and stop.
2. Capture worktrees and exact manifest; recheck drift and source/SQL contracts before edits.
3. Implement only the approved boundary with assigned tests; preserve unrelated work.
4. Run checks, review exact diff/security target and report actual outcomes/limitations.
5. Stop at delivery; no automatic next task, G4 action or self-approval.

## 9. Focused Audit Requirements

Inspect section 11 read paths for helper semantics, layering, period/identity/availability and
regression contracts. Static source continuity does not prove current live rows/jobs or external
readers. Operator-attested SQL/config parity remains separately labelled. No credential discovery
or RDP required for this planning/implementation boundary. Evidence condition: Disposable SQL required for constraints. Active production config/jobs remain later readiness evidence.

## 10. Architecture Targets

kvk/models and kvk/schemas own pure types; kvk/services business rules; kvk/dal parameterized SQL,
transactions and mapping; commands/routes/views thin adapters. New SQL only in the SQL repository.
Follow the implementation-plan interfaces/lock order and approved source/field dictionary.
No second domain implementation in DL_bot.py or gsheet_module.py; no duplicated SQL calculation.

## 11. Exact File Manifest

All paths below are relative to **C:/K98-bot-SQL-Server**.
New files are proposed, not present yet; predecessor-created modifications require accepted delivery.
No wildcard authorizes extra files. Append implementation evidence to this pack after execution;
do not rewrite unrelated indexes. Migration date/sequence is the sole controlled allocation exception
in implementation-plan section 4; final name must be recorded before authoring and never renamed after merge.

### Read only

- `sql_schema/KVK.KVK_Windows.Table.sql`
- `sql_schema/KVK.KVK_DKPWeights.Table.sql`
- `sql_schema/KVK.KVK_CampMap.Table.sql`
- `sql_schema/dbo.ProcConfig.Table.sql`
- `migrations/README.md`

### Create

- `migrations/20260909_002_kvk_source_publication_state.sql`
- `sql_schema/KVK.SourceConfigVersion.Table.sql`
- `sql_schema/KVK.SourceWindowConfig.Table.sql`
- `sql_schema/KVK.SourceCampConfig.Table.sql`
- `sql_schema/KVK.SourceWeightConfig.Table.sql`
- `sql_schema/KVK.SourcePeriod.Table.sql`
- `sql_schema/KVK.SourceScanBinding.Table.sql`
- `sql_schema/KVK.SourceConfigRequest.Table.sql`
- `sql_schema/KVK.SourcePublication.Table.sql`
- `sql_schema/KVK.SourcePlayerResult.Table.sql`
- `sql_schema/KVK.SourceSelection.Table.sql`
- `sql_schema/KVK.SourceRouting.Table.sql`
- `sql_schema/KVK.SourceAction.Table.sql`
- `sql_schema/KVK.SourceDelivery.Table.sql`
- `deploy/Test-KvkSourcePublicationContracts.ps1`
- `validation/kvk_source/publication_constraints.sql`

### Modify

- `sql_schema/KVK.SourceAggregateReport.Table.sql`

## 12. Implementation Requirements

Create exactly thirteen S2B tables in plan section 4. Modify only S2A SourceAggregateReport snapshot to add same-source/KVK period FK after validation, without orphan deletion/backfill. Mirror Windows/Map structures in new config tables; existing sheets/tables unchanged.
SourceSelection has same-scope publication FK and monotonic version; SourceRouting.Enabled defaults false. Completeness/hash/counts require S3B transaction validation, not status flag alone. Request idempotency includes base config so 13-to-14-to-13 is a new action. Old versions remain immutable.
Nullable result metrics carry statuses; DKP decimal(38,6), weight decimal(38,12) plus source round-trip strings. Aggregate values remain immutable report references. Actions retain provenance and SourceDelivery stores owner/fence/pending/uncertain/confirmed receipts.
Static validator and rollback-only disposable SQL cover source/period FKs, duplicate generations, disabled defaults, absent-end retention, exact numeric ranges and retained history. No new procedures, grants or activation. Runtime CAS/concurrency remains S3B/S4B responsibility.

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

Scenario ownership: Storage foundations T29/T31/T43/T45/T47-T54/T65/T69-T70.

- Run new deploy/Test-KvkSourcePublicationContracts.ps1 and explicit-repo Validate-SqlRepo.ps1 after reviewing log effects.
- Run listed synthetic constraint SQL only in an authorized disposable database; static pass is not transaction proof.

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

Rollback: Retain new tables disabled; never drop foundation data or alter legacy config. Later source-aware selection rollback requires validated service.

## 17. Proposed PR Summary

Describe concrete behavior, exact manifest, actual tests/security target, dependencies and rollback
limits. Keep private player rows/credentials/findings out of Git. No PR creation authorized by
preparation. End with slice status and next required gate.

**Prepared only. S2B G3 pending; no implementation executed.**
