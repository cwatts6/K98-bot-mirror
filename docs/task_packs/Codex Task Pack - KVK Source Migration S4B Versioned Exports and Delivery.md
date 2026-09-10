# Codex Task Pack — KVK Source Migration S4B Versioned Exports and Delivery

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
