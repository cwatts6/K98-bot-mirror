# Codex Task Pack — KVK Source Migration S2A SQL Observation Facts

## 1. Task Header

- Prepared 2026-09-09; owner Chris Watts; Phase 2B specification.
- G2 architecture approved, including authorized EndScanID corrections. **S2A G3 pending.**
- One-pass implementation approved: **No**. Execute only after explicit approval of this slice.
- Proposed isolated branch `codex/kvk-source-s2a`; not created during planning.
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

Add isolated immutable source/roster/report storage and database-enforced uniqueness; no actual import, route or publication.

## 4. Background

Planning anchors: bot main `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`; SQL main
`fc0e94ebd2e0a98286069c8a8b71365dd5178657`. Recheck branches/HEADs/remotes/status at execution,
preserve existing work and record actual start/end hashes. Local definitions are not deployed proof.
No pull/reset/checkout to make a working copy match historical evidence. Use an authorized isolated
branch/worktree where needed. Phase-1 C01-C65 anchor dependencies; G2 fixes source semantics.

## 5. Scope

Predecessors: S1 typed schema/digest accepted; S2A G3; explicit disposable SQL target before integration acceptance.

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

1. Confirm explicit S2A approval and predecessor evidence; otherwise scope/review and stop.
2. Capture worktrees and exact manifest; recheck drift and source/SQL contracts before edits.
3. Implement only the approved boundary with assigned tests; preserve unrelated work.
4. Run checks, review exact diff/security target and report actual outcomes/limitations.
5. Stop at delivery; no automatic next task, G4 action or self-approval.

## 9. Focused Audit Requirements

Inspect section 11 read paths for helper semantics, layering, period/identity/availability and
regression contracts. Static source continuity does not prove current live rows/jobs or external
readers. Operator-attested SQL/config parity remains separately labelled. No credential discovery
or RDP required for this planning/implementation boundary. Evidence condition: Disposable SQL required for real constraint tests. No production substitute or credential discovery.

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

- `sql_schema/KVK.KVK_Scan.Table.sql`
- `sql_schema/KVK.KVK_AllPlayers_Raw.Table.sql`
- `sql_schema/KVK.KVK_Player_Baseline.Table.sql`
- `sql_schema/KVK.KVK_CampMap.Table.sql`
- `deploy/Test-KvkTargetPublicationContract.ps1`
- `deploy/Validate-SqlRepo.ps1`
- `migrations/README.md`

### Create

- `migrations/20260909_001_kvk_source_observation_facts.sql`
- `sql_schema/KVK.SourceArtifact.Table.sql`
- `sql_schema/KVK.SourceImportAttempt.Table.sql`
- `sql_schema/KVK.SourceObservation.Table.sql`
- `sql_schema/KVK.SourceObservationRevision.Table.sql`
- `sql_schema/KVK.SourcePlayerSnapshot.Table.sql`
- `sql_schema/KVK.SourceLogicalScan.Table.sql`
- `sql_schema/KVK.SourceRoster.Table.sql`
- `sql_schema/KVK.SourceRosterMember.Table.sql`
- `sql_schema/KVK.SourceAggregateReport.Table.sql`
- `sql_schema/KVK.SourceAggregateRevision.Table.sql`
- `sql_schema/KVK.SourceKingdomReportRow.Table.sql`
- `sql_schema/KVK.SourceCampReportRow.Table.sql`
- `deploy/Test-KvkSourceObservationContracts.ps1`
- `validation/kvk_source/observation_constraints.sql`

### Modify

- None.

## 12. Implementation Requirements

Create exactly the twelve S2A tables in plan section 4 and matching migration/snapshots. Existing objects untouched. Enforce cross-source/KVK and same-observation revision FKs; add circular selected-revision links after table creation with nullable pointer only during a controlled transaction. Positive IDs/ranges/unique keys mandatory.
SourceLogicalScan supports locked per-source/KVK allocation in later DAL, unique observation binding; no trigger/default allocation for alias or aggregate insert. Aggregate rows store eight dedicated Decimal/raw/unit column groups, no FLOAT or DKP calculation. Scope/map checks are service-owned with persisted provenance, not a universal 36-kingdom constraint.
Add static validator patterned on existing read-only text checks and synthetic constraint SQL inside an explicit rollback transaction, guarded to a disposable test database and requiring authorized execution. Cover duplicate keys, mismatched source/season, circular revision mismatch, numeric limits and transaction rollback. Static checks do not prove runtime locks.
Period FK arrives in S2B; foundation cannot activate. No new procedures/UDTs/triggers/permission grants, legacy recompute edits or ProcConfig rows. Migration date/sequence follows the controlled rule in plan section 4; record final path before authoring.

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

Scenario ownership: T13/T17/T46/T50; database identity foundations for T01-T08/T68.

- Run new deploy/Test-KvkSourceObservationContracts.ps1 for static contract checks.
- Run deploy/Validate-SqlRepo.ps1 with explicit RepoPath after reviewing its log writes.
- Run listed synthetic constraint SQL only against an explicitly authorized disposable database; retain rollback evidence.

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

Rollback: Manual: retain additive objects with source disabled. No DROP script or accepted-evidence deletion. Disposable transaction rolls back only its synthetic rows.

## 17. Proposed PR Summary

Describe concrete behavior, exact manifest, actual tests/security target, dependencies and rollback
limits. Keep private player rows/credentials/findings out of Git. No PR creation authorized by
preparation. End with slice status and next required gate.

**Prepared only. S2A G3 pending; no implementation executed.**
