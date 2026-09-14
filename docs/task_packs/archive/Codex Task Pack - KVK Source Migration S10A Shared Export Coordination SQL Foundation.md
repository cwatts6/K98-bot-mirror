# KVK Source Migration S10A — Shared Export Coordination SQL Foundation

> Archived 2026-09-14: S10A accepted, SQL #85 merged and locally pulled. No bot-machine pull.
> Historical approval/scope wording below is superseded by the current S10A/S10B handoff.

> 2026-09-14: the operator subsequently approved local implementation and closure of the scoped gaps.
> See [S10A implementation/handoff](../../reference/kvk_source_migration/s10a_implementation_and_s10b_handoff.md).
> Initial-scope wording below is retained history. SQL execution and Git publication remain unapproved.


## Authority and entry state

Prepared 2026-09-14. **Initial review/scope only. SQL/runtime implementation and Git publication
are not authorized.** Documentation closeout, archival and this task preparation are approved.
Do not create a new task automatically. S7 decisions and predecessor acceptance remain settled.

S9B mirror #277, production #584 and SQL #84 are merged and locally pulled. No changes have
been pulled to the bot machine. See the [S9B closeout](../../reference/kvk_source_migration/s9b_closeout_and_s10a_handoff.md)
for exact merge evidence, delivered versus pending manifests, final reviews and execution limits.
Comparison anchors, never reset instructions:

- Bot main/origin main: `8e60e78d850a92b6ff84c6b870b8f0c6c5254806`.
- Bot production/main: `289bc87e1379941fd6ddafe1a18bb5e7a993d09d`.
- SQL main/origin main: `d0916f742f9c88743b97107dfca1f3acbcb32c2e`.

Recheck both repositories, staged/unstaged/untracked/deleted/renamed files and remote identities.
Preserve every pending document, database and evidence file. Do not reset to these anchors.

## Required reading

Read current AGENTS and all seven core documents routed by README-DEV and the reference index.
Use k98-architecture-scope, k98-sql-validation and k98-test-selection for scope; security routing
selects the later review. Read authoritative SQL-repository guidance and migration conventions.

- [Approved S7 contract / consumer matrix](../../reference/kvk_source_migration/integration_contract_and_consumer_matrix.md).
- [Exact implementation manifests and object requirements](../../reference/kvk_source_migration/integration_implementation_manifests.md), especially S10A, schema, locking, rollback and S7-T09 through S7-T15.
- [Architecture / EndScanID amendment](../../reference/kvk_source_migration/phase_2_contract_and_architecture.md).
- [Acceptance scenarios](../../reference/kvk_source_migration/phase_2_acceptance_scenarios.md) and [post-S6 requirements](../../reference/kvk_source_migration/post_s6_integration_requirements.md).
- [Retained S6 handoff](../../reference/kvk_source_migration/post_s6_handoff_log.md), [S8B closeout](../../reference/kvk_source_migration/s8b_closeout_and_s8c_handoff.md), and [S8C execution/operator evidence](../../reference/kvk_source_migration/s8c_folder_intake_smoke_evidence.md).
- Authoritative definitions under `C:/K98-bot-SQL-Server`, especially existing SourceExportIntent,
  SourceExportIntentPublication, source selection/update/publication and retained delivery records.

## Scope and exact initial SQL manifest

S10A provides the additive shared export coordination schema. It does not implement the Bot
queue worker, provider adapters, pool lifecycle, admin recovery flows or activation. These remain
S10B/C/D/E and S11. Existing grouped commands stay intact; no new top-level command.

The approved S7 manifest reserves the following nine paths. The already-approved migration README
carry-forward adds a second documentation path, giving **ten initial SQL delivery paths**:

| Action | Exact SQL path |
|---|---|
| Create after date/sequence reconciliation | `migrations/20260912_002_shared_export_coordination.sql` |
| Create | `sql_schema/dbo.ExportJob.Table.sql` |
| Create | `sql_schema/dbo.ExportJobResource.Table.sql` |
| Create | `sql_schema/dbo.ExportResource.Table.sql` |
| Create | `sql_schema/dbo.ExportRequestBudget.Table.sql` |
| Create | `sql_schema/dbo.ExportAttempt.Table.sql` |
| Create | `sql_schema/dbo.ExportAttemptPart.Table.sql` |
| Create | `validation/kvk_source/s10_export_coordination.sql` |
| Modify, mandatory carry-forward | `docs/SQL_DELIVERY_LOG.md` |
| Modify, mandatory carry-forward | `migrations/README.md` |

**Migration filename is a historical S7 reservation, not permission to backdate a new migration.**
At scope time select the exact actual-creation-date filename and available sequence, present that
specific path amendment in the implementation plan, and obtain implementation approval before
writing SQL. Never rename a merged migration. Additional paths require an explicit scope amendment.

At handoff preparation, read-only searches found the existing S8A intent/publication tables;
the six general export tables and reserved shared-export migration were absent. Revalidate this
at task entry. Do not infer schema from Python or create duplicate existing objects.

## Mandatory documentation delivery — do not omit at PR creation

The eventual S10A SQL implementation PR **must include both updated SQL documents above** together
with the approved implementation paths. They are not optional follow-up documentation. Reconcile
all pending SQL paths before committing and verify exact provider filename/previous_filename
coverage before ready-for-review, or prove specific paths already merged with matching content.

The [closeout's exact pending Bot documentation manifest](../../reference/kvk_source_migration/s9b_closeout_and_s10a_handoff.md#exact-pending-bot-documentation-manifest)
is a separate mandatory carry-forward into the next Bot implementation PR, **S10B**. This includes
all updated reference/evidence/navigation documents, this S10A task pack and starter, the S9B closeout,
and the old AND new paths for both S9B archive moves. S10A scope must inventory and preserve that
set; its closeout must pass the exact set plus any new outputs to S10B. Do not put Bot files into
SQL, SQL files into Bot, or create a standalone documentation PR. Do not re-ask this approved grouping.
Counts alone are insufficient; always check filename AND previous_filename and explicit exemptions.
Publication remains separately authorized after implementation, tests and review.

## Architecture and persistence review

Map each requirement to the existing S7 object contract and authoritative definitions before DDL:

- ExportJob: all three consumer kinds, replay identity including destination/epoch/repair,
  source intent linkage, durable immutable spool identity/storage owner, queue state and owner/fence.
- ExportJobResource / ExportResource: frozen deterministic resource sets, exclusive account,
  destination and SQL-snapshot ownership, CAS versions and blocked/uncertain ownership.
- ExportRequestBudget: shared account/budget-kind identity, durable cooldown/interval version,
  server UTC reservation precision; later provider waits occur outside SQL transactions.
- ExportAttempt / ExportAttemptPart: durable attempt sequencing, owner/fence/epoch, bounded
  manifests and receipt fields, file uniqueness/parts, verification/ACL state and quarantine.

Validate keys, exact types/collations, length limits, nullable tuple rules, allowed states, FKs,
uniqueness and indexes against the contract. Resolve cyclic Job/Resource ownership FKs with an
explicit creation/order plan. Separate static SQL constraints from temporal immutability,
resource acquisition, fairness and state transitions that require later authorized DAL transactions.
Do not claim a CHECK constraint alone seals inputs or enforces worker admission over time.

Preserve running A while newer B/C intents arrive, retain superseded/coalesced history and original
fairness tickets, and distinguish duplicate replay from explicitly authorized repair. Lease expiry,
worker timeout or a failed callback must never release an uncertain provider claim or erase an
attempt. Preserve old receipts byte-for-byte; ambiguous associations remain blocked. No migration
may clear the two retained uncertain publications or silently map them as failed/available.

S10A is additive. Classify actual data changes explicitly and plan missing-object/idempotence,
partial-application and conflict handling. Plan rollback as disabled admission / forward correction;
do not drop history-bearing tables after data exists. Do not enable new writers while old writers
bypass admission. No change to actual .env files, provider registrations, credentials or bot config.

## Preserved source and independent-consumer contract

Maintain fixed source per season; supplied overall and B0 cohort; no summed-fight overall,
mixed sources or silent legacy camp/rank fallback. Preserve independent stats and target numbers,
target publication/roster/history/daily consumers, authoritative aggregates/DKP, UTC starts,
daily SCANORDER, retained unused scans and movable within-season windows. Preserve the exact
endpoint chain, CAS/sealed inputs, durable matched UpdateID, explicit counterpart attestation and
admission locks. SourceRouting.Enabled alone is insufficient. S10A adds persistence support and
must not activate routing, exporters or any operator execution flow.

## Tests and approval packet

Return one scope packet with exact paths/amendments, object/column/FK/index mapping, SQL versus
future Bot responsibilities, migration classification/order/recovery, risks, test design and a
stepwise implementation plan. Identify real unresolved schema questions without re-asking settled
S7 decisions. Stop for implementation approval after that packet.

When implementation is approved, select static validation and authored SQL cases for:

- valid/invalid consumers, states, tuples, key lengths and scoped relationships;
- replay duplicates versus distinct repair/epoch identity and retained intent references;
- deterministic job-resource uniqueness, ownership tuple constraints and uncertain-state retention;
- shared budget keys, cooldown precision and UTC semantics;
- attempt sequence/part/file uniqueness, manifest/receipt bounds and invalid FK/state rejection;
- additive migration first-run/re-run/partial-state behavior, existing-history preservation and
  forward-safe rollback; separate structural checks from later concurrent worker integration tests.

Inspect existing SQL repository validators, contract checks, PowerShell parsing and documentation
reference rules. Do not embed a cross-repository Bot file URL that SQL CI misreads as a local path;
use a verified companion PR link when available. Existing pytest results are retained evidence,
not S10A tests. Bot runtime pytest can be skipped for this docs-only preparation; choose fresh
checks appropriate to the implementation later.

Authored SQL tests are not permission to execute them. Any SQL/disposable-database run requires
separate exact target, operations, backup/data-safety and approval. No live connection or predecessor
rerun during initial scope. Review executable SQL with k98-security-review-routing followed by
**Changes, Deep off**, at the exact SQL base/head or patch; assess any Bot documentation delta
independently with a precise skip. No routine whole-codebase or deep security scan.

## Retained gates and excluded work

Keep S6-OPS01/PERF01/CAP01 open, both uncertain publications and all retained databases/backups/files.
S8B accepted smoke/50-case and actual-restore evidence remains distinct from offline runner-history
support, S8A six-script evidence and S8C evidence. S8C seven local operator checks PASS is not live
Discord acceptance. No SQL/provider/Discord execution, real imports/exports, bot-machine pull,
restart/deployment, activation, Git publication or automatic new task. S10B/C/D/E and S11 remain
separately scoped work; no coordinator implementation under this preparation authorization.
