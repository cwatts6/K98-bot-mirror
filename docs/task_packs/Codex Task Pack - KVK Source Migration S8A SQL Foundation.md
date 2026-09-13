# KVK Source Migration S8A — SQL Foundation

## 1. Summary and authority

Prepared 2026-09-12 for Chris Watts. S7's contract and exact implementation manifests
are operator-approved, including their recommended technical direction. The subsequent
instruction to proceed authorizes recording that approval and preparing this pack and
starter only. **S8A implementation has not been authorized or started by preparation.**

After separate file-implementation authorization, deliver the fixed-season-source,
matched-update, complete-selection and immutable-export-intent SQL foundation in the
authoritative SQL repository. Stop before database execution and Git publication.
S8B Bot writers and services follow separately; this schema does not implement public routing.

### Required reading and initial scope

Read current instructions in both repositories, Bot README-DEV, the reference index and
its required engineering, execution, testing, skills/refactor and deferred-optimisation
standards. Read applicable SECURITY.md as policy context, not scan authorization. Then read:

- [Approved integration contract and consumer matrix](../reference/kvk_source_migration/integration_contract_and_consumer_matrix.md)
- [Approved exact manifests](../reference/kvk_source_migration/integration_implementation_manifests.md), especially S8A and SQL object contracts
- [Architecture and EndScanID amendment](../reference/kvk_source_migration/phase_2_contract_and_architecture.md)
- [Phase 2 implementation plan](../reference/kvk_source_migration/phase_2_implementation_plan.md)
- [Post-S6 requirements](../reference/kvk_source_migration/post_s6_integration_requirements.md)
- [Acceptance scenarios](../reference/kvk_source_migration/phase_2_acceptance_scenarios.md)
- [Handoff and approval record](../reference/kvk_source_migration/post_s6_handoff_log.md)
- [S6 evidence](../reference/kvk_source_migration/release_evidence_log.md), [readiness](../reference/kvk_source_migration/release_readiness_and_rollback.md), [archived pack](archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S6%20Release%20Readiness%20and%20Controlled%20Activation.md) and [archived starter](archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S6%20Release%20Readiness%20and%20Controlled%20Activation.md)

In `C:\K98-bot-SQL-Server`, read `migrations/README.md`,
`docs/SQL_DATA_MIGRATION_GUARDRAILS.md`, `docs/SQL_DELIVERY_LOG.md`, migration-runner
conventions and authoritative definitions for every referenced key. Do not infer SQL
columns, types, collations or foreign-key eligibility from Bot usage.

Use k98-architecture-scope, k98-sql-validation, k98-test-selection and
k98-security-review-routing. Use k98-pr-review for the completed bounded change.
No promotion workflow or broad audit is selected. No subagent/new task is required.

Step 1 remains review/scope: recheck both branches/HEADs/remotes/status, instructions,
manifest and dependency drift. When file implementation is explicitly authorized, continue
within that approved boundary after the check; do not re-ask settled product decisions.
Resolve routine technical details from the contract and schema. Report evidenced manifest
or contract incompatibilities before expanding scope.

### Entry and preserved evidence

Preparation verified Bot main/origin main `a2f148fa9bd4fb367fd46d0500a768c14fee915b`,
local production/main `a8c9c515066ca6ef079120b76dd160e3389badab`, and SQL main/origin
main `44afa315dd6cbfe9fec101f2a39a62e534f5b583`. These are anchors, not reset instructions.
Bot origin is `https://github.com/cwatts6/K98-bot-mirror.git`; production is
`https://github.com/cwatts6/K98-bot.git`. SQL origin is
`https://github.com/cwatts6/K98-bot-SQL-Server.git`. SQL is clean; Bot carries documentation.
No fetch/pull/reset is needed to check local refs. Preserve all work and retained databases.

S1–S5B and S6 evidence remain accepted. Mirror #272 and production-repository #579
are merged; local deployment is operator-attested, not production runtime deployment
or fresh post-merge smoke. Carry S6-OPS01/PERF01/CAP01 and both retained uncertain
publications with the exact IDs, file sets, hashes, fences and states in the linked
S6 records. Those records are authoritative historical evidence, not S8A test targets.

## 2. File manifest

The SQL repository's exact implementation boundary is eight files:

| Action | SQL repository path |
|---|---|
| Create | `migrations/20260912_001_kvk_season_complete_updates.sql` |
| Create | `sql_schema/KVK.SeasonSource.Table.sql` |
| Create | `sql_schema/KVK.SourceUpdate.Table.sql` |
| Create | `sql_schema/KVK.SourceCompleteSelection.Table.sql` |
| Create | `sql_schema/KVK.SourceExportIntent.Table.sql` |
| Create | `sql_schema/KVK.SourceExportIntentPublication.Table.sql` |
| Create | `validation/kvk_source/s8_season_complete_updates.sql` |
| Modify | `docs/SQL_DELIVERY_LOG.md` |

Use the actual migration creation date and next available daily ordinal. If creation is
later than preparation or the name is occupied, record the exact replacement in this
pack and the approved manifest before writing; this naming-only adjustment is not a
new design decision. Never rename a merged migration or overwrite another contribution.

The Bot documentation carry-forward is a separate **27-path union**: all 23 paths in
handoff section 2, both S7 Create outputs, and this S8A pack and starter. Count both
S6 archive source deletions and both destinations. Preparation adds no other paths.
The next separately authorized Bot PR must carry that union or prove specific paths
already merged; a SQL PR cannot carry Bot files. Verify actual PR Files changed using
both filename and previous_filename against the respective repository manifest.
Do not wait for S8B and silently lose this documentation handoff. No PR is authorized now.

## 3. New files

Create only the seven SQL files listed above after file-implementation approval.
The migration is deployable source; snapshots are matching reference definitions,
not independent deployment scripts. The validation script contains synthetic,
explicit-target cases and execution prerequisites, but is not executed by file approval.
This preparation creates only this Markdown pack and its companion starter in Bot.

## 4. Modified files

The only existing SQL file to change is `docs/SQL_DELIVERY_LOG.md`. Record authored,
static-reviewed and later executed/deployed states distinctly; never label an unrun
migration deployed. Bot runtime, tests, configuration and existing SQL objects are
outside S8A. Documentation status/navigation may be maintained within the carry-forward
union. If an existing SQL object needs an alteration to make a required FK possible,
identify the exact object and amend the manifest before implementing that expansion.

## 5. SQL changes and contract

Implement the exact five object contracts in the approved manifest. Resolve physical
types and candidate keys against current authoritative definitions. Record which
invariants are enforced by SQL constraints and which require S8B's transactional DAL;
do not claim a CHECK/FK can enforce temporal immutability or complete-pair semantics alone.

- `KVK.SeasonSource`: one immutable choice per KVK, allowlisting legacy_full_data and
  snapshot_report_v1, durable choice/actor/provenance and versioned lifecycle. Choice
  and serving availability are distinct. Missing choice is unavailable, never fallback.
- `KVK.SourceUpdate`: scoped accepted player start/end revisions, aggregate report/revision,
  period/config/roster/coverage identity, explicit confirmed counterpart reuse and versioned
  waiting/sealed states. Wrong source/KVK/period cannot bind. Sealed inputs are immutable.
- `KVK.SourceCompleteSelection`: a separate complete public pointer; existing component
  selections and partial historical publications are not automatically promoted.
- `KVK.SourceExportIntent` and `KVK.SourceExportIntentPublication`: durable deduplicated
  season vector, exact publication/config versions and unchanged-period membership.
  S8B must commit public selection and intent atomically; S8A supplies the schema, not
  a working Bot transaction. Missing destination never erases an intent.

Validate referenced SourceRouting, SourceSelection, SourcePublication, input/revision,
configuration/roster and SourceConfigRequest keys and existing migration dependencies.
Add indexes only for the approved scoped lookups and integrity requirements. No UDT,
calculation procedure, ProcConfig, legacy output table, routing-enabled value or queue/
pool implementation is changed here. Existing SourceRouting permits only snapshot_report_v1;
do not widen it as a substitute for SeasonSource.

Preserve B0/private onboarding and no-fight zero/member rules; authoritative aggregate
and overall reports remain independent. Keep UTC scan starts, semantic deduplication,
daily SCANORDER and exact 11−10, 12−10, 13−10, authorized 14−10 endpoint semantics.
The last endpoint needs no additional correction command. Public combat output waits
for its validated matched pair. Do not manufacture aggregates or extra logical scans.

Document the agreed writer lock order: SeasonSource, SourceRouting, sorted component/
complete period selection rows, config/request/update rows, then intent/vector rows.
Its Bot enforcement is S8B. No provider call occurs inside a SQL transaction.

### Historical classification and migration safety

The approved historical backfill is `DataChange: Yes`. Author its narrow validation and
explicit reviewed classification input contract; do not invent real KVK rows or inspect a
live database. Missing/ambiguous/mixed-history classification must fail closed before
mutation, not auto-select a source from whichever upload arrived first. Do not automatically
activate accepted S6 input/history or modify any existing routing enablement.

Include required migration metadata, dependency preflight, preview predicates, expected
row-count checks, transaction/locking plan, backup requirement, pre/post-validation and
forward-fix notes. Synthetic fixture rows are distinct from an approved environment's
allowlist. Before execution, the operator must approve the exact database, backup evidence,
row preview/classification and operation script. An empty allowlist is not permission to
ignore existing unclassified history. Safe rerun verifies schema/constraints and existing
choices; it must reject conflicts or incompatible partial installation rather than skip them.

## 6. Helpers reused

Reuse SQL migration tracking/header and validation conventions. S8B later reuses existing
calculation, input digest, candidate publication and DAL transaction helpers. Do not add
a new migration runner, database connector, embedded credential or Bot helper in S8A.

## 7. Refactor findings

No general refactor is approved. Scoped FK eligibility, migration compatibility or constraint
gaps are S8A design findings to resolve within the manifest or report precisely. Existing
export pacing/worker/storage/pool concerns belong to S10, not this SQL foundation.
Capture genuinely unrelated debt only in the required deferred format; do not turn a
required integration invariant into deferred work or restart an accepted source audit.

## 8. Test plan with actual outcomes

Preparation outcomes belong in the handoff log. **No S8A SQL validation has run.**

After file approval, statically verify all eight paths, migration metadata/dependency order,
snapshot parity, types/collations/candidate keys, scoped FKs, uniqueness, state/nullability/
JSON bounds, no destructive history changes, and fail-closed classification. Use existing
offline repository checks only after inspecting that they do not connect/deploy. Inspect
the validation script rather than invoking sqlcmd or a migration runner. Record tooling
limitations; text inspection cannot prove SQL Server compilation, transactions or locks.

The exact planned validation file is `validation/kvk_source/s8_season_complete_updates.sql`.
Prepare separately runnable synthetic cases for install/rerun, incompatible partial schema,
same/different-source onboarding, mixed-history rejection, wrong-scope pairs/FKs, no-fight
rules, duplicate intent/vector scope and rollback preserving the original state. Describe
two-session schedules and expected observations for concurrency; a single SQL script's
sequential assertions do not prove races. No default database or predecessor database target.

After separately approved disposable execution, capture actual server/database, script
hash/revision, row counts, assertion outcomes and cleanup disposition. Preserve predecessor
databases. S8B owns the combined service/SQL lost-acknowledgment and atomic-publication tests
in `tests/test_kvk_source_sql_integration.py`, with `tests/test_kvk_season_source.py` and
`tests/test_kvk_source_pairs.py`; do not create or claim those tests in S8A. Relevant scenarios
are S7-T01, T04 and T08, plus the preserved endpoint/B0 contract under T07. Full integration
acceptance requires later evidence and cannot be replaced by static passes.

For the Bot Markdown companion, run architecture/deferred/security-routing validators,
exact-path select_tests and git diff --check; verify local links and retained evidence bytes.
Document skipping generic runtime/smoke/registration suggestions for Markdown-only changes.

## 9. Security review decision and evidence

Preparation: Bot Markdown-only documented skip at the exact current uncommitted patch;
SQL clean/no-change skip. No security scan is started by preparing this pack.

Future S8A SQL implementation touches persistence and integrity. Use
k98-security-review-routing, then security-diff-scan: **Scan type: Changes, Deep off**,
exact SQL base/head or immutable working patch verified immediately before review.
Record reviewed path coverage, scan/evidence ID, findings/dispositions and exact final
target after fixes. Bot documentation is a separate exact target with its own documented
skip unless executable scope is separately approved. Do not combine repository histories.
No standard/deep scan or automatic new task. File-implementation authorization may include
this bounded diff review, but does not authorize Git publication or SQL execution.

## 10. Deployment/rollback

Nothing is deployed by preparation or file implementation. No SQL server connection,
production SQL, real import/export, provider write, Discord, restart, deployment, activation,
predecessor rehearsal or successor execution is authorized. No commit/stage/push/PR/merge/
pull/reset/fetch or production promotion without separate authorization.

Schema precedes S8B/C writers and S9 readers. An additive installation is not activation.
Use disabled admission/serving during later rollout. Retain chosen-source/history and
receipts during rollback; do not drop populated tables or silently switch a season to legacy.
Manual/forward-fix notes must distinguish an empty disposable fixture from retained data.

## 11. Follow-ups and approval

Current exit: pack/starter prepared, S7 acceptance recorded, 27 Bot paths preserved,
SQL unchanged. Stop for separate **S8A file implementation and static validation**
authorization, using the companion starter if desired. Do not reopen S7-D01–D09 or the
approved initial account serialization, durable spool/worker-affinity and pool allowance.
Those latter implementation details belong to S10.

After S8A file review, bring back the exact disposable execution/row-classification plan;
Git publication is a separate gate. S8B remains separately authorized. Preserve S6's
accepted results and open operational gates until their affected integration evidence
is measured and accepted under S11. No automatic next task is created.
