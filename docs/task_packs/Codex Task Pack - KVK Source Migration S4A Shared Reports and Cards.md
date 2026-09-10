# Codex Task Pack — KVK Source Migration S4A Shared Reports and Cards

## Current entry handoff — 2026-09-10

S1/S2A/S2B/S3A/S3B are accepted and merged. S3B mirror #267/private #574 merge and post-merge
smoke evidence are retained in the [archived S3B pack](archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S3B%20Acceptance%20and%20Atomic%20Publication.md).
Start S4A in a new chat using its matching starter when granting **S4A G3**; this documentation
closeout does not grant it. Verify actual branches/HEADs/remotes/status before any edits.
Current mirror main `02385a0edc0ec83f77241e02648eabb3b7640ea6`; private main
`a8ad9f1d81cfb7884a9cdcc0b067c4346a204488`; SQL main
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Historical anchors are not reset targets.
Local pulls are complete; the bot machine has not been updated. Local S4A development needs
no bot-machine pull/restart. Routing remains disabled. Preserve S2A/S2B/S3B evidence databases;
use mocks unless a disposable SQL target and operations are explicitly authorized first.

Operator S3B smoke passed 36 tests in 9.11s plus imports and registration 36/100. The post-review
full suite stalled around 19% and remains incomplete; investigate and report that limitation in
S4A's required full-suite/log-noise validation. Earlier full passes are historical, not fresh.

Carry the accepted S3B endpoint amendment into every consumer: either endpoint may change;
supplied EndScanID >= StartScanID; distinct scans increase both ID and UTC. Equal endpoints
mean zero supported fight scores for all B0 members and no applicable aggregate. Blank/future
end remains interim; a present end pins the final; authorized endpoint updates permit replacement.
Preserve ordinary missing values, independent aggregate authority and separate daily SCANORDER.

### Required carried-forward documentation in the eventual S4A PR

The operator expressly requires this S3B closeout to accompany the S4A PR when separately
authorized. This allowance supplements section 11's runtime manifest; it does not authorize
extra code or immediate commit/push/PR. Inventory all tracked edits/deletions and untracked
Markdown at entry. Preserve the full thirteen-document manifest (fifteen physical paths),
including both sides of both archive renames, repaired links and appended delivery evidence.
Do not discard this work as unrelated dirt, omit untracked destinations or blanket-stage
unrelated files. Reconcile actual staged paths and preservation/link evidence before PR creation.

- Update: `README-DEV.md`.
- Update: `docs/reference/README.md`.
- Update: `docs/reference/kvk_source_migration/decision_and_evidence_register.md`.
- Update: `docs/reference/kvk_source_migration/phase_2_implementation_plan.md`.
- Update: `docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md`.
- Update: `docs/task_packs/KVK Source Migration - Programme Pack.md`.
- Update: `docs/task_packs/README.md`.
- Update: `docs/task_packs/archive/README.md`.
- Update: `docs/reference/local_sql_development.md`.
- Update: `docs/task_packs/Codex Task Pack - KVK Source Migration S4A Shared Reports and Cards.md`.
- Update: `docs/task_packs/Codex Chat Starter - KVK Source Migration S4A Shared Reports and Cards.md`.
- Archive move: `docs/task_packs/Codex Task Pack - KVK Source Migration S3B Acceptance and Atomic Publication.md` → `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S3B Acceptance and Atomic Publication.md`.
- Archive move: `docs/task_packs/Codex Chat Starter - KVK Source Migration S3B Acceptance and Atomic Publication.md` → `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S3B Acceptance and Atomic Publication.md`.


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

## S4A local implementation delivery — 2026-09-10

This appendix supersedes the historical prepared/G3-pending status above. The operator
explicitly approved **S4A G3 only** in this task. Implementation is delivered locally for
review, with the full-suite limitation below still open. No acceptance or next gate is
self-granted. The original pack and carried-forward closeout text are preserved.

### 1. Summary

Added an explicit V2 reporting facade over one S3B publication snapshot, preserving nullable
metrics, frozen B0 attribution, metric-specific cohorts, exact Decimal ordering, requested
versus selected endpoints, independent aggregate authority and stream UTC timestamps.
All twelve named blocks share that request snapshot. Aggregate raw tokens and displayed
units survive mapping; aggregate total KP remains unsupported. No window sums, aggregate
DKP coefficients, daily namespace changes or source activation were introduced.

New source entry points require explicit period/connection inputs. Existing production
dispatch, commands and legacy bare-dict reads remain on their legacy default. These are
locally testable source adapters, not evidence of activated Discord routing. Source-specific
admin inspection supports recent logical scans, window preview and read-only recompute
diagnostics; it does not invoke the legacy recompute procedure or build a new publication.

Whole-KVK card context stays separate from independent KS4 values and targets. Existing
mobile cards cannot represent full source/period/cohort/as-of context, so source rank fields
are suppressed; existing fallback payloads likewise receive no misleading overall rank.
The separately retained context names its tier-KP/B0 cohort basis and player endpoint time.

V3 private preview manifests pin KVK/source/period/publication, while V1/V2 sessions remain
readable with their original semantics. Reopening cannot retarget an existing session.
If the pinned publication is no longer selected when loaded, the reader fails closed and
requires a new session; it never silently switches publication or falls back to legacy.
Identity is pinned at request load, not a guarantee selection remains current through send.

### 2. File Manifest

Entry verification before edits:

- Bot: `main`, HEAD `02385a0edc0ec83f77241e02648eabb3b7640ea6`; origin
  `https://github.com/cwatts6/K98-bot-mirror.git`, production
  `https://github.com/cwatts6/K98-bot.git`. Existing worktrees were inventoried and retained.
- SQL: clean `main`, HEAD `44afa315dd6cbfe9fec101f2a39a62e534f5b583`; origin
  `https://github.com/cwatts6/K98-bot-SQL-Server.git`. No SQL repository edits or connections.
- Local Git objects confirm mirror #267 merge `e915f9727f9492fe4ecc02b5c0d9f3c6e443be13`
  and private #574 merge `a8ad9f1d81cfb7884a9cdcc0b067c4346a204488`. Archived S3B final
  review, merge and operator smoke evidence was read. Fresh GitHub API reads returned
  HTTP 401; local objects and archived readback are the verification evidence, not a
  claimed fresh remote API success. Operator smoke 36/9.11s remains historical.
- Created local branch `codex/kvk-source-s4a` without changing HEAD or pending files.
  Final bot/SQL HEADs and remotes remain the same. Staging is empty.

Exactly nineteen Python paths from section 11 were authored: three created and sixteen
modified below. This pack alone receives appended S4A documentation. All thirteen carried
documents/fifteen physical paths in the entry manifest remain included for a separately
authorized eventual PR, including both S3B source deletions and both untracked archive
destinations. No blanket staging or omission of untracked Markdown is authorized.

Task source/test byte digest (sorted path, NUL, bytes, NUL; SHA-256):
`11a09083b2396a47f2b3400531278e7e2530e8829efb0ae58248c495b668fa0e`.
The isolated security target is byte-identical to these nineteen root files.

### 3. New Files

- `kvk/services/new_source_reporting_service.py`
- `tests/test_kvk_source_reporting.py`
- `tests/test_kvk_source_card_context.py`

### 4. Modified Files

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

Documentation authored here: this evidence appendix only. The carried-forward documentation
manifest near the beginning of this pack remains authoritative and complete.

### 5. SQL Changes

None in the SQL repository. New parameterized read queries in the permitted bot DAL were
checked against `SourceWindowConfig`, `SourcePeriod`, `SourceObservationRevision`,
`SourceObservation`, `SourceCampConfig`, `SourceAggregateRevision` and `SourceLogicalScan`.
Result mapping was checked against `SourcePublication`, `SourcePlayerResult`,
`SourceKingdomReportRow` and `SourceCampReportRow`. S3B's transactional selection/integrity
reader is reused unchanged. Its pinned immutable IDs govern subsequent metadata reads;
those reads never choose another current revision or configuration.

No production/default/disposable SQL connection was used. Retained S2A/S2B/S3B evidence
databases were untouched. Runtime SQL-driver/transaction execution of new queries remains
unverified without a separately authorized disposable target and operations.

### 6. Helpers Reused

- S3B `load_snapshot`, `transaction`, `one`, `rows` and `SourceConflict`.
- Canonical `require_valid_embed_payload`, `truncate_text`, `pack_complete_units` and
  `neutralize_discord_mentions`, plus Discord Markdown escaping.
- Existing card renderer/font/layout, independent combat/target policies and service boundary.
- Existing preview `_contained`, `_read`, `_write`, FileLock, ownership checks and durable
  begin/transition/finish protocol; production daily claims are not used or reset.
- Existing synthetic S3A calculation fixtures and `result_values` for consumer tests.

New mapping/ranking helpers are source-specific: legacy default-zero/report-summation helpers
would erase unavailable values or change authority. Decimal sorting uses `copy_negate()`
to avoid ambient-context rounding of close high-precision values.

### 7. Refactor Findings

No new SQL in commands/views and no Discord types in the new reporting service. Legacy
reporting DAL sums/default-zero behavior is deliberately bypassed by explicit V2 readers,
not changed. Export grouping, ProcConfig WS1, independent rankings/history/targets and daily
KS4 paths remain outside this slice. No unrelated runtime refactor was performed.

### 8. Test Plan and Actual Outcomes

Commands used the repository `.venv/Scripts/python.exe`; system `python` lacks pytest.
Test mode was enabled. Full/broad runs removed S3B integration target environment overrides
and supplied synthetic SQL environment labels, so retained databases were not authorized
or exercised. Source consumer tests mock the DAL; fixtures contain synthetic rows only.

| Validation | Fresh outcome |
|---|---|
| Exact section 14 ten-file focused command | **111 passed in 10.81s** |
| Architecture validator | Passed; nineteen Python files checked |
| Deferred validator | Passed; thirteen Markdown files checked |
| Security-routing validator | Passed; zero errors/warnings |
| Test selector with the exact nineteen paths | Passed; full suite, imports and registration recommended |
| Exact nineteen-file pre-commit | Passed all applicable hooks, including Ruff, Black, Pyright and secret hook |
| Import smoke in test mode | Passed |
| Command registration | Passed; primary 36, grouped 100, no drift or duplicate risk |
| Required full pytest through log-noise wrapper | **Incomplete**: reproduced stall around 20%, terminated only this validation process tree |
| Broad run excluding two fallback-timeout tests | **3,785 passed, 34 skipped, 2 deselected in 141.87s**; operational logs unchanged |
| Isolated dashboard fallback-timeout test | Still stalled at 60 seconds; terminated |
| Isolated pagination fallback-timeout test | **1 passed in 1.44s** |
| Synthetic mobile card inspection | Both PNG renderers tested at 1180×640; private 590×320 preview inspected, source rank suppressed |
| Whitespace/diff check | Passed |

The broad command was `scripts/analyse_pytest_log_noise.py --pytest-args -v tests -k
"not test_real_timeout_cancels_blocked_dashboard_fallback_send and not
test_real_timeout_cancels_blocked_pagination_fallback_send"`. Its 34 skips include the
32 explicitly opt-in S3B SQL integration cases plus two existing skips. The separately
passing pagination test was initially excluded conservatively with the related failing
test; that isolated result is not represented as part of the broad-run count.

The full run used `--pytest-args -v tests -o faulthandler_timeout=45`. It stopped at
`tests/test_governor_dashboard_discord_views.py::test_real_timeout_cancels_blocked_dashboard_fallback_send`.
A private temporary pytest observer confirmed the test coroutine remains at line 1156,
`await fallback_started.wait()`, with its selection task no longer pending. The test starts
a 0.01-second real view timeout before asynchronous rendering/selection and waits without
a bound for the fallback event. This supports a test synchronization/timeout race; it does
not establish a production dashboard failure. No unrelated test/runtime fix was made.
The historical 19% stall now has a reproducible local test location, but the exact historical
process was not available for retrospective proof. The full-suite gate remains incomplete.

Sandboxed Black processes stalled; the exact-file check and required pre-commit run completed
successfully under reviewed local escalation. Only the task's own stalled formatter and
test processes were terminated. No bot process, service, Discord action or restart was used.

Scenario evidence: synthetic consumer tests exercise T35–T40/T52/T55 through direct aggregate
authority, absent overall, distinct stream timestamps, one snapshot, missing values and
bounded rendering; T60/T67 through independent card context and suppression; T61/T62 through
unchanged legacy/admin/preview and broad regression coverage; T70 through pending desired
endpoint versus retained result. S3A/S3B calculation and acceptance remain the owners of
11−10, 12−10, final 13−10, authorized replacement 14−10, B0 membership, increasing ID/UTC,
and semantic re-export deduplication. Their underlying code is unchanged. No mock result
is claimed as fresh live transactional, import/export or Discord smoke evidence.

Private local validation artifacts are retained under
`C:/Users/cwatt/AppData/Local/Temp/k98-s4a-z0e295b1` (entry preservation bytes, exact manifest,
full/broad/isolated logs, stall observer and synthetic PNGs); none belongs in Git.

### 9. Security Review Decision and Evidence

Bot: **Changes, Deep off**, isolated task-only target `.codex_scan_stage/s4a`, base/head
`02385a0edc0ec83f77241e02648eabb3b7640ea6` plus working-tree patch. Content identity:
`codex-security-snapshot/v1:sha256:3144228c960b9a74fcb73dfc03972c2c06ad3bd20a91a13a44888cef01d42912`.
Scan `4cdd29f8-6810-4c57-bac1-5baffd58b5f4` completed and canonical readback verified at
14:31:46 UTC: **12/12 runtime files, seven supporting test files, zero findings, deferred
security candidates or open questions**. Required preflight passed; Daybreak advisory was
`granted`, Daybreak Blue. Required independent threat-model challenge and complete diff
review ran through the security skill; no unrelated task or repository scan was created.

Canonical report, manifest, findings, coverage and SARIF stay privately under
`C:/Users/cwatt/AppData/Local/Temp/codex-security-scans-tFar8J/s4a/02385a0edc0ec83f77241e02648eabb3b7640ea6_20260910T142430Z_f61og1tt`.
The readback confirms the exact sealed target. SQL: separate no-change skip against clean
HEAD `44afa315dd6cbfe9fec101f2a39a62e534f5b583`. No private-history patch was created.
This appendix is a documentation-only skip; it changes no permission, runtime or data access.
Existing carried docs are preserved work, not silently included in the isolated runtime scan.

### 10. Deployment Steps

None authorized or performed. No pull/reset/merge/push/PR, production SQL, real import/export,
Discord action, bot-machine update/restart, deployment or activation. No predecessor or later
pack was executed. Local review worktree artifacts are excluded by an exact local Git exclude.

V3 sessions require this code to read them; old code cannot read V3. Disable unsupported
routing before downgrade and retain all manifests/publications. Source sessions never
silently become legacy sessions. Future activation must preserve caller authorization and
private destination checks; these service APIs do not grant permission by themselves.

### 11. Deferred Optimisations

#### Deferred Optimisation

- Area: `tests/test_governor_dashboard_discord_views.py:1121–1163`
- Type: consistency
- Description: The real 0.01-second dashboard timeout can finish selection before the
  fallback-start event, leaving the test waiting indefinitely at line 1156. Reproduced in
  the full S4A suite and a 60-second isolated run; a bounded observer identified the wait.
- Suggested Fix: In a separately scoped test repair, synchronize entry into the intended
  fallback path before triggering timeout and bound event waits; preserve cancellation
  assertions and determine whether any runtime change is actually needed.
- Impact: medium
- Risk: low
- Dependencies: Outside S4A's exact file manifest; separate approval for repair. The related
  pagination fallback test passed in isolation and is not proven defective.

**Review checkpoint:** local S4A implementation and focused/security/log-hygiene evidence
are delivered. Full-suite completion and live SQL/Discord integration remain explicit gaps.
Stop for operator review; no PR or subsequent slice is authorized by this delivery.

Final preservation/link readback: all fifteen entry paths preserved (this pack retains its
original byte prefix), all **125 relative Markdown links resolve**, and staging remains
empty. The appended pack's applicable hooks and final deferred/security-routing validators
passed. The nineteen Python files still match the frozen reviewed bytes exactly.

### Operator-Accepted Full-Suite Exception — 2026-09-10

The operator explicitly accepted the incomplete full-suite validation exception for S4A
and will check the full suite during PR validation. This clears the recorded local
PR-readiness blocker for the current S4A delivery; it does not convert the stalled run
into a pass. The actual outcomes above remain unchanged: the required full run and isolated
dashboard timeout test stalled, while the broad exclusion run and focused checks passed.
The suspected timing race remains an inference, and the separately scoped test repair
remains deferred. Historical or other PR runs are not fresh validation of this patch.

S4A is ready for PR preparation under this accepted exception. PR creation, commit/push,
promotion, deployment and activation still require their separately authorized scope.
The operator's acceptance does not authorize those actions or any additional implementation.
New-source routing remains disabled; live SQL/Discord integration remains unperformed.

### PR Preparation Authorization — 2026-09-10

The operator subsequently authorized creation of the mirror and private bot PRs as ready
for review. This supersedes earlier no-commit/push/PR wording only for this S4A delivery.
The complete thirteen-document carried-forward manifest, both sides of both archive
renames, repaired links and delivery evidence are included. The full-suite exception
above remains accepted, with the operator to check the suite during PR validation.
No merge, bot-machine update, restart, deployment, SQL operation or source activation is
authorized. The SQL repository has no changes and needs no PR.

The private PR will use a file-delta patch on production/main, preserving separate history.
The stock promotion script includes unconditional full pytest and reset-on-error behavior;
its equivalent patch/check/commit/push steps are used individually to honor the accepted
suite exception and preservation constraints. No reset or force push is required.


### PR Delivery Readback — 2026-09-10

- Mirror [PR #268](https://github.com/cwatts6/K98-bot-mirror/pull/268): open, ready for review;
  branch `codex/kvk-source-s4a`, implementation commit
  `e0ab51df40708684d899dbf87141b38be217db27`, base
  `02385a0edc0ec83f77241e02648eabb3b7640ea6`.
- Private [PR #575](https://github.com/cwatts6/k98-bot/pull/575): open, ready for review;
  branch `prod/kvk-source-s4a`, implementation commit
  `3ed1c960af2b188a49ccf113765e3f428a033e9d`, direct parent
  `a8ad9f1d81cfb7884a9cdcc0b067c4346a204488`. The exact file delta was applied on
  production/main; no mirror history was pushed to the private repository.
- All 34 physical manifest paths match between the two delivered implementations:
  nineteen Python paths and fifteen carried documentation paths (thirteen logical
  documents including both archive renames). All original closeout content is preserved;
  125 relative Markdown links resolve. Hooks normalized appended pack line endings only.
- Fresh staged-file hooks, including staged secret detection, passed on both branches.
  Architecture, deferred and security-routing validators passed. The existing S4A test
  outcomes above remain the evidence; no redundant full run or historical pass is claimed.
  The operator-accepted incomplete-suite exception is prominent in both PR descriptions.
- Separate private security review: Changes, Deep off, target
  `C:/discord_file_downloader/.codex_scan_stage/s4a-prod`, base/head
  `a8ad9f1d81cfb7884a9cdcc0b067c4346a204488` plus staged patch.
  Scan `311e487e-fd99-43fb-977b-79b1b75fafee`, snapshot
  `codex-security-snapshot/v1:sha256:8e8ce907817a459c987b2768ec450956b2cf83035d8ce3fe0e2ca1bc0c2f0204`,
  completed at 14:58:20 UTC with canonical readback verified: twelve runtime files and
  seven supporting tests reviewed, zero findings/deferred candidates/open questions.
  Dedicated preflight passed; Daybreak access granted (Daybreak Blue); independent
  architecture review completed. Private artifacts remain outside Git under
  `C:/Users/cwatt/AppData/Local/Temp/codex-security-scans-tFar8J/s4a-prod/a8ad9f1d81cfb7884a9cdcc0b067c4346a204488_20260910T145217Z_jx0pzs9x`.
  Tool-reported scan usage: 3,825,453 total tokens, including 3,699,072 cached input tokens.
- The earlier mirror scan still matches all nineteen Python files. This final delivery
  appendix is documentation only; it changes no runtime, configuration, authority or
  data-access behavior, so no additional discovery scan is required. The final evidence
  commits add only this same appendix on both branches.
- SQL remains clean main at `44afa315dd6cbfe9fec101f2a39a62e534f5b583`: separate
  no-change security skip and no SQL PR. No retained database was touched.

No merge, deployment, bot-machine update/restart, SQL operation, live import/export,
Discord action or source activation occurred. New-source routing remains disabled.
Stop for operator PR review and validation; no later slice is authorized.
