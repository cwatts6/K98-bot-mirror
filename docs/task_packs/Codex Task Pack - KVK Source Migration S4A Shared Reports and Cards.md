# Codex Task Pack — KVK Source Migration S4A Shared Reports and Cards

## 1. Task Header

- Prepared 2026-09-09; owner Chris Watts; Phase 2B specification.
- G2 architecture approved, including authorized EndScanID corrections. **S4A G3 pending.**
- One-pass implementation approved: **No**. Execute only after explicit approval of this slice.
- Proposed isolated branch `codex/kvk-source-s4a`; not created during planning.
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

Serve V2 report blocks and independently labelled card context while preserving legacy consumers and isolated diagnostic sessions.

## 4. Background

Planning anchors: bot main `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`; SQL main
`fc0e94ebd2e0a98286069c8a8b71365dd5178657`. Recheck branches/HEADs/remotes/status at execution,
preserve existing work and record actual start/end hashes. Local definitions are not deployed proof.
No pull/reset/checkout to make a working copy match historical evidence. Use an authorized isolated
branch/worktree where needed. Phase-1 C01-C65 anchor dependencies; G2 fixes source semantics.

## 5. Scope

Predecessors: S3B accepted and S4A G3; new source routing remains disabled.

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

1. Confirm explicit S4A approval and predecessor evidence; otherwise scope/review and stop.
2. Capture worktrees and exact manifest; recheck drift and source/SQL contracts before edits.
3. Implement only the approved boundary with assigned tests; preserve unrelated work.
4. Run checks, review exact diff/security target and report actual outcomes/limitations.
5. Stop at delivery; no automatic next task, G4 action or self-approval.

## 9. Focused Audit Requirements

Inspect section 11 read paths for helper semantics, layering, period/identity/availability and
regression contracts. Static source continuity does not prove current live rows/jobs or external
readers. Operator-attested SQL/config parity remains separately labelled. No credential discovery
or RDP required for this planning/implementation boundary. Evidence condition: No live data for synthetic tests. Actual production/preview smoke requires later explicit authorization.

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

- `kvk/dal/kvk_reporting_dal.py`
- `stats_alerts/interface.py`
- `kvk/services/kvk_rankings_service.py`
- `kvk/services/kvk_export_service.py`
- `services/kvk_personal_service.py`

### Create

- `kvk/services/new_source_reporting_service.py`
- `tests/test_kvk_source_reporting.py`
- `tests/test_kvk_source_card_context.py`

### Modify

- `kvk/services/kvk_reporting_service.py`
- `stats_alerts/allkingdoms.py`
- `stats_alerts/embeds/kvk.py`
- `kvk/dal/kvk_stats_card_dal.py`
- `kvk/services/kvk_stats_card_service.py`
- `kvk/models/kvk_stats_card.py`
- `kvk/rendering/kvk_stats_card_renderer.py`
- `kvk/dal/kvk_admin_dal.py`
- `kvk/services/kvk_admin_service.py`
- `stats_alerts/kvk_diagnostics.py`
- `stats_alerts/kvk_diagnostic_sessions.py`
- `tests/test_kvk_reporting_service.py`
- `tests/test_kvk_embed.py`
- `tests/test_kvk_stats_card_payload.py`
- `tests/test_kvk_stats_card_renderer.py`
- `tests/test_kvk_embed_diagnostics.py`

## 12. Implementation Requirements

Close C15-C28/C35-C43. Add explicit V2 load facade; preserve legacy bare-dict service on legacy path, but never strip V2 metadata and apply default-zero normalization. Reuse canonical embed packing with one request snapshot across all twelve blocks.
New readers use S3B DAL; legacy SQL functions/views and legacy reporting DAL calculations untouched. Player metric ranks use selected cohort; aggregate DKP/totals direct from report revision. Explicit overall and selected fight separate, unknown values labelled. No sum windows or coefficients in new aggregate reads.
Mixed /kvk stats retains independent KS4 metrics/targets; whole-KVK context separately labelled with source/period/cohort/as-of or suppressed if renderer cannot represent distinction. Do not treat rank as rank of independent numerator; test mobile image and fallback limits.
Admin recompute/list-scans/window-preview/test_embed resolve source-specific diagnostics privately and preserve legacy contracts. Existing preview sessions remain readable, new manifests pin source/publication; no implicit retargeting. Explicit backwards-readable session version if needed, old-code downgrade limitation recorded.
No production dispatch policy, daily claim reset, command registration, permission edits, SQL writes or source activation. Export work belongs to S4B. Tests cover each output family and existing legacy/preview behavior, not just a new facade.

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

Scenario ownership: T35-T40/T52/T55/T60-T62/T67/T70; legacy/admin/preview regressions.

- `python -m pytest -q tests/test_kvk_source_reporting.py tests/test_kvk_source_card_context.py tests/test_kvk_reporting_service.py tests/test_kvk_embed.py tests/test_kvk_stats_card_payload.py tests/test_kvk_stats_card_renderer.py tests/test_kvk_embed_diagnostics.py tests/test_kvk_historical_preview.py tests/test_kvk_admin_service.py tests/test_discord_embed_limits.py`

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

Rollback: Disable new routing before reverting adapters or unsupported session schemas. Retain old/new session manifests/publications; no implicit old-code serving of new data.

## 17. Proposed PR Summary

Describe concrete behavior, exact manifest, actual tests/security target, dependencies and rollback
limits. Keep private player rows/credentials/findings out of Git. No PR creation authorized by
preparation. End with slice status and next required gate.

**Prepared only. S4A G3 pending; no implementation executed.**
