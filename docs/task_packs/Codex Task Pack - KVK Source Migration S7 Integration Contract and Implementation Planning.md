# KVK Source Migration S7 — Integration Contract and Implementation Planning

## Current status — S7 approved; S8A pack prepared, 2026-09-12

Chris Watts approved the S7 contract and exact implementation manifests, then authorized
preparation of the next pack and starter. The approved technical direction includes initial
account serialization, durable legacy snapshots with worker affinity where needed, and the
stated quarantine/reserve allowance. Settled S7 decisions are not reopened.

**Next: S8A SQL Foundation, after separate file-implementation authorization.**
[Task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8A%20SQL%20Foundation.md); [implementation starter](Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S8A%20SQL%20Foundation.md).
Preparation is documentation-only. No S8A SQL/runtime/config implementation, database
execution, Git publication or activation is authorized by this status. Preserve the full
27-path Bot carry-forward union, including both S6 archive move sides and both S7 outputs;
SQL implementation belongs in its own repository and review. Historical status blocks below
retain their original evidence; this latest status supersedes pending S7 review wording.

## 1. Task header and authority

2026-09-12. Owner: Chris Watts. Type: documentation and read-only integration scope.
Prepared after merged S6 evidence and the operator's settled behavior decisions.
**S7 documentation/read-only execution approved by Chris Watts in the task starter;
contract and manifests delivered for review.** Approval of this pack permits its exact
documentation/read-only scope only; it cannot authorize runtime, SQL or live work.
The post-S6 documentation refresh is already authorized and carried with this pack.

## 2. Required reading

Read current AGENTS.md, README-DEV.md, the reference index and its seven core
requirements. Read root/applicable SECURITY.md for context and apply security
routing. Then read:

- [Settled integration requirements](../reference/kvk_source_migration/post_s6_integration_requirements.md)
- [Handoff, merge evidence and exact carry-forward manifest](../reference/kvk_source_migration/post_s6_handoff_log.md)
- [Amended implementation plan](../reference/kvk_source_migration/phase_2_implementation_plan.md)
- [Approved architecture and amendment](../reference/kvk_source_migration/phase_2_contract_and_architecture.md)
- [Acceptance scenarios including S7-T01–T16](../reference/kvk_source_migration/phase_2_acceptance_scenarios.md)
- [C01–C65 dependency matrix](../reference/kvk_source_migration/phase_1_dependency_matrix.csv)
- [S6 evidence log](../reference/kvk_source_migration/release_evidence_log.md), [readiness](../reference/kvk_source_migration/release_readiness_and_rollback.md) and [archived S6 pack](archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S6%20Release%20Readiness%20and%20Controlled%20Activation.md)

Use conditional ENV_REFERENCE, canonical command reference, startup/shutdown,
diagnostics and helper references only where the traced paths require them.
Read authoritative SQL repository instructions/schema before proposing SQL changes.

## 3. Objective

Produce an implementation-ready contract for all ordinary KVK outputs using one
fixed source per KVK and complete matched updates, with safe import-triggered
exports, manual export recovery and reusable output files. Identify the exact
missing connections and their file/test/SQL boundaries. Do not repeat the completed
source audit or claim existing adapters establish public end-to-end integration.

## 4. Entry and preserved evidence

Recheck both branches, HEADs, remotes and status. Entry anchors are Bot
`a2f148fa9bd4fb367fd46d0500a768c14fee915b`, SQL
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`; local production/main is
`a8c9c515066ca6ef079120b76dd160e3389badab`. They are comparison anchors, not reset
instructions. Mirror #272 and production-repository #579 are merged; local
deployment is operator-reported. No production runtime deployment or fresh
post-merge smoke is evidenced. Preserve all pending documentation from this handoff.

All preceding slices remain accepted. S6 measurements are accepted with stated
limits; OPS01/PERF01/CAP01 retain operational work and the public routing prerequisite
remains open. Retain exact tested revisions, security targets, disposable databases,
Google file IDs, hashes and uncertain publication states from the archived evidence.

## 5. Scope and exclusions

In scope: trace current callers, define contracts and state transitions, validate
existing SQL shapes read-only, prepare exact implementation/test/security manifests
for S8–S11, and update only the documented Markdown manifest.

No runtime/test/SQL/config edits, connections to SQL servers, real file imports or
exports, Google/Discord actions, credential inspection, production deployment,
restart or activation. No Git pull/reset/merge/push/PR/commit without separate
authorization. No automatic predecessor, successor or new task execution. Do not
open a codebase or deep security scan. No private player data or credentials in Git.

## 6. Skills and security decision

| Skill | Decision |
|---|---|
| k98-architecture-scope | Use to map layers, state and implementation boundaries |
| k98-sql-validation | Use for read-only authoritative schema comparison and proposed persistence design |
| k98-discord-command-feature | Use for the proposed grouped export-only/recovery UX and permission design; no command implementation |
| k98-test-selection | Use to assign meaningful implementation coverage and current documentation checks |
| k98-security-review-routing | Use; current Bot Markdown-only skip and SQL no-change skip |
| k98-pr-review | Use for completed documentation review before any separately authorized handoff |
| k98-promotion-check | Not applicable to S7 execution; promotion is not authorized |
| k98-deferred-optimisation-capture | Conditional on evidenced unrelated debt; new integration requirements are delivery blockers, not deferred optimizations |

Current scan decision: documented skip for exact Bot handoff/S7 Markdown delta
against its verified entry HEAD; no executable permission/config/data-access change.
SQL remains a separate unchanged repository. Record actual final targets.
Future S8–S10 runtime/SQL changes require separate exact Changes reviews per repo,
Deep off, after security routing. No scan is started by this planning pack.

## 7. Mandatory work and engineering outputs

1. Verify entry and preserve all changes before edits. Read settled S7-D01–D09;
   do not re-ask answered product decisions.
2. Trace every C01–C65 consumer and newly discovered indirect caller from upload to
   SQL/services/cache/report/card/export/dispatch and back. For each, record exact
   file/function, current source selection, proposed seam, chosen-source coverage,
   version/cache ownership, test and supported/excluded rationale. Source-independent
   daily systems keep their contracts; no unexamined exclusions under “all outputs”.
3. Specify immutable season source choice separately from serving availability.
   Decide onboarding and legacy-history compatibility, concurrent first imports,
   rejection of conflicting streams, restart persistence and safe disabled behavior.
4. Specify pair identity, validation, independent acceptance versus public selection,
   counterpart-reuse confirmation, configuration changes, B0/no-fight/overall cases,
   stale/missing labels and atomic complete-publication/export intent.
5. Specify common admission for all three consumers and manual paths, exact shared
   resources, cross-process account pacing, immutable running export, durable latest
   pending coalescing, fairness, cancellation, failure/uncertainty and restart fencing.
6. Specify a grouped admin export-only/rebuild/status UX. Reuse existing services
   where valid. Distinguish confirmed no-op, failed retry, uncertain reconcile and
   explicit damaged-output rebuild. Do not invent top-level command approval.
7. Size active/staging/quarantine/reserve and specify season rollover, no late old
   writer, stale-tab cleanup, stable entry link, retired remote receipts and preserved
   input/publication history. No lifetime spreadsheet archive requirement.
8. Validate existing SourceRouting/SourceSelection/SourcePublication/SourceDelivery,
   inputs/config/action schemas and all relevant legacy constraints against SQL.
   Record exact proposed migrations/objects and separate SQL/Bot manifests; do not
   infer that existing tables provide a pair registry or shared export queue.
9. Assign exact existing/new test files to S7-T01–T16, plus T01–T70 contracts affected
   by the amendment. Define targeted, full/log-isolated, registration and per-repo
   security gates for implementation; include disposable operation approvals later.
10. Produce ordered PR-sized S8–S11 boundaries with exact paths, dependencies,
    compatibility/migration/rollback design, risk and evidence-based effort estimate.
    Split a proposed slice when needed. Do not author speculative runnable later
    packs before contract/manifest review. Stop for review; no implementation starts.

## 8. Architecture and refactor controls

Services own publication/queue/rollover policy; DAL owns SQL and transaction state;
commands/views own permission checks, confirmation and presentation. Critical state
is durable, not only an asyncio lock or process-local pacing timestamp. Do not hold
SQL transactions over provider writes. Reuse accepted publication/delivery fencing
where compatible; never erase receipt uncertainty or bypass semantic deduplication.
No broad legacy exporter or reliability WS1 rewrite unless a necessary dependency
is evidenced and added to a separately approved bounded manifest.

## 9. Exact S7 file permissions and carry-forward

**Required carry-forward:** every path in the handoff log's exact manifest,
including both deleted source paths and both new S6 archive destinations. It is
part of the next slice PR, not ignorable pre-existing work. Archived evidence may
receive only status/link corrections with its measured content preserved.

**Additional S7 Create paths (not yet created or executed by the handoff):**

- `docs/reference/kvk_source_migration/integration_contract_and_consumer_matrix.md`
- `docs/reference/kvk_source_migration/integration_implementation_manifests.md`

S7 may refine the current requirements, plan, scenarios, S7 pack/starter and handoff
log within the carry-forward manifest. All other sources are read-only. No runtime
or SQL write permission is hidden in an investigation path or future manifest.
Before an eventual PR, compare actual Files changed including previous_filename for
renames to the union of this exact handoff manifest and the two S7 Create paths;
prove any excluded path was already merged. Carry approved docs through separately
authorized later production promotion as well.

## 10. Validation and acceptance

Check all changed Markdown links/anchors, exact old/new archive paths, preservation
of measured evidence, decision-to-design/test traceability and both repo states.
Run architecture/deferred/security-routing validators, exact-path test selector and
git diff --check. Runtime tests/smoke/registration may be skipped for documentation
only with the reason recorded; proposed coverage must not be reported as passed.
If staging is separately approved, run staged secrets checks. Report environment or
hook limitations exactly; no blanket pass claim.

Acceptance requires the complete consumer matrix, state/SQL/command designs and
exact implementation/test/security manifests, a finite remaining-work list and
operator-reviewable estimates. Confirm no unresolved question repeats S7-D01–D09.
Live targets, new rehearsal execution and G4/G5 acceptance remain separate gates.

## 11. Canonical delivery

Use the canonical eleven sections: Summary; File Manifest; New Files; Modified
Files; SQL Changes; Helpers Reused; Refactor Findings; Test Plan with actual outcomes;
Security Review Decision and Evidence; Deployment/Rollback; Follow-ups and Approval.
Link the handoff proof and identify accepted evidence versus unexecuted next-slice requirements.


## S7 documentation delivery — stop for review

The two authorized Create outputs are available:

- [Contract and consumer matrix](../reference/kvk_source_migration/integration_contract_and_consumer_matrix.md)
- [Exact implementation manifests and canonical eleven-section delivery](../reference/kvk_source_migration/integration_implementation_manifests.md)

[Local validation and carry-forward proof](../reference/kvk_source_migration/post_s6_handoff_log.md#s7-documentation-delivery-and-validation)
records actual checks. No runtime/SQL/config/test implementation, Git publication,
rehearsal, predecessor, successor or live operation was performed. Review the contract
and exact manifests before authorizing another slice. No settled decision is re-asked.
