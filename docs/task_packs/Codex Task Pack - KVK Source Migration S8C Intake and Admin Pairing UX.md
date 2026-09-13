# KVK Source Migration S8C — Intake and Admin Pairing UX

## 1. Task header and authority

Prepared 2026-09-13 for Chris Watts. Type: bounded Bot interaction integration.
S8B is complete, operator accepted, successfully smoke tested and delivered through merged
production #581 and SQL #81. Local pulls are complete; no changes have been pulled to the bot
machine. Mirror #274 is closed without a merge record; its delivered content is verified in the
synchronized mirror. See the closeout for exact evidence and comparison anchors.

**Ready for a new chat, initial review/scope only. One-pass implementation approved: no.**
This preparation does not begin S8C or create a new chat. After scope approval, continue within
that approval without re-asking settled S7 decisions or predecessor acceptance.

## 2. Required reading

Read current AGENTS.md, README-DEV.md, docs/reference/README.md and all indexed core engineering,
execution, testing, skills/refactor and deferred-optimisation standards. Read root/applicable
SECURITY.md as policy context. Then read:

- [S8B closeout and exact S8C documentation carry-forward](../reference/kvk_source_migration/s8b_closeout_and_s8c_handoff.md)
- [Approved S7 contract and consumer matrix](../reference/kvk_source_migration/integration_contract_and_consumer_matrix.md), especially fixed source, matched updates, counterpart confirmation and C61/N09
- [Approved manifests](../reference/kvk_source_migration/integration_implementation_manifests.md), S8C and S7-T01/T03/T05
- [Architecture and EndScanID amendment](../reference/kvk_source_migration/phase_2_contract_and_architecture.md) and [acceptance scenarios](../reference/kvk_source_migration/phase_2_acceptance_scenarios.md)
- [Archived S8B implementation, disposable and review evidence](archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8B%20Bot%20Source%20and%20Matched%20Update%20Services.md)
- [Retained S6 evidence](../reference/kvk_source_migration/release_evidence_log.md), [readiness](../reference/kvk_source_migration/release_readiness_and_rollback.md), [post-S6 requirements](../reference/kvk_source_migration/post_s6_integration_requirements.md)
- [Canonical command reference](../reference/canonical_command_reference.md); conditional helper and startup/recovery references where actual callers require them

Read authoritative SQL repository instructions, migrations/README.md, SQL_DATA_MIGRATION_GUARDRAILS.md,
docs/SQL_DELIVERY_LOG.md and relevant object definitions in C:\K98-bot-SQL-Server. Validate actual
SeasonSource, SourceUpdate (including PeriodKind versus UpdateKind), complete selection/intent,
config/request, revision, roster and ProcConfig shapes. Do not infer physical columns from S7's
proposed tables or Python alone. Read files only; SQL execution needs separate exact approval.

## 3. Objective and boundaries

Connect existing private intake, admin controls and normal configuration confirmation to the
accepted S8B source and matched-update services. Users explicitly choose the season source and
confirm the intended update context; accepted unmatched input remains private until a complete
eligible pair or typed domain exception can select atomically.

No new top-level command. Prefer the existing grouped admin surface. S9 owns ordinary public
routing/cards, and S10 owns export workers, pacing, export-only recovery and rollover. Persisting
an S8B export intent is not provider execution. SourceRouting.Enabled alone does not implement
public routing. No activation or runtime configuration change belongs to S8C.

## 4. Exact implementation manifest

These 13 Modify paths are the approved S7 S8C boundary: seven runtime files, five test files and
one command-reference document. Recheck their current contents in the new chat. Unlisted runtime,
test, SQL or config edits need an evidenced scope amendment before implementation.

| Action | Repository-relative path |
|---|---|
| Modify | `commands/stats_cmds.py` |
| Modify | `ui/views/kvk_source_import_view.py` |
| Modify | `upload_routes/kvk_source_route.py` |
| Modify | `upload_routes/kvk_all_route.py` |
| Modify | `kvk/services/new_source_admin_service.py` |
| Modify | `kvk/dal/new_source_admin_dal.py` |
| Modify | `proc_config_import.py` |
| Modify | `docs/reference/canonical_command_reference.md` |
| Modify | `tests/test_kvk_source_admin.py` |
| Modify | `tests/test_kvk_source_import_view.py` |
| Modify | `tests/test_kvk_source_upload_route.py` |
| Modify | `tests/test_kvk_all_upload_route.py` |
| Modify | `tests/test_kvk_source_config_hook.py` |

## 5. Mandatory documentation delivery

The complete physical-path manifest in [closeout section 3](../reference/kvk_source_migration/s8b_closeout_and_s8c_handoff.md#3-exact-documentation-carry-forward-manifest)
is an additional required part of S8C. Include every pending closeout/reference/index edit,
both S8B archive source deletions AND both archive destinations, this pack/starter and the new
closeout. Preserve local documentation when branching; pre-existing work is not an exclusion.

The eventual separately authorized Bot PR must include the union of section 4, every closeout
documentation path, and approved amendments. Before handoff, verify actual GitHub Files changed
`filename` and `previous_filename`, not just counts or a local diff. A specific omitted path needs
exact merged commit/content evidence. Repeat equivalent verification for production promotion.
The old 51-path S8B delivery is already verified in merged production and synchronized local main;
do not require empty repeat edits to unchanged merged files.

The two SQL documentation paths, `docs/SQL_DELIVERY_LOG.md` and `migrations/README.md`, are
separate SQL PR carry-forward, with exact actions in the closeout. Never include them in the Bot
PR. No SQL implementation is selected by this pack; assess SQL independently.

## 6. Required behavior and architecture

- Explicitly authorized fixed source onboarding precedes both importers. Missing choice returns
  setup required; conflicting source rejects; same-choice retry reuses existing audited identity.
  No first-upload-wins choice, implicit legacy default or source replacement.
- Confirm durable UpdateID and exact source/KVK/period/config/roster/coverage/as-of context through
  accepted S8B APIs. Support player-first and aggregate-first intake. Show waiting state privately;
  do not publish a partial component or bypass complete selection through predecessor APIs.
- A reused counterpart needs explicit retained revision/base update, actor, reason and validity
  attestation for the intended context. Revalidate permissions and versions at confirmation.
  Reject wrong actor/guild/channel/role and stale revision/config/roster/coverage. Do not infer a
  pair from filenames, arrival order or equal timestamps; aggregates have no player ScanID.
- Normal import/config confirmation can supply counterpart validity. Unattended ProcConfig refresh
  must retain pending desired intent without inventing attestation. Preserve exact 11−10, 12−10,
  final 13−10 then authorized 14−10 without another correction command. Exact pending endpoint
  arrival resumes using valid retained authority; absent pair leaves old final previous/config-pending.
- Preserve private B0 onboarding, frozen roster/kingdom attribution, UTC scan starts, semantic
  deduplication, typed equal-endpoint/no-fight rules, independent authoritative aggregates and
  separate overall. Preserve daily SCANORDER and legacy complete Full Data semantics.
- Commands/views handle permissions, safe defer and rendering; services own orchestration; DAL
  owns persistence. Reuse S8B durable CAS, sealed inputs, complete selection and full-vector intent.
  Callback retries/restart must reload durable state and return the original result, including
  superseded duplicate updates. Do not keep authoritative confirmation only in view memory.
- Retain the final S8B admission fix: an admitted legacy generation holds its season lock through
  recomputation; new imports reject after closing. Do not reintroduce an intermediate commit.

## 7. Skills, helper reuse and refactor checks

| Skill | Decision |
|---|---|
| k98-architecture-scope | Use for initial review, actual caller map and implementation plan |
| k98-discord-command-feature | Use for permissions, views, callback/restart behavior and grouped commands |
| k98-sql-validation | Use for actual S8B API/schema and ProcConfig contract alignment |
| k98-test-selection | Use for focused, permission, restart and broad regression gates |
| k98-deferred-optimisation-capture | Conditional: unrelated non-security debt only, required format |
| k98-pr-review | Use before eventual PR handoff |
| k98-promotion-check | Only when production promotion is separately authorized |
| k98-security-review-routing | Use before implementation review; decision below |

Inspect existing decorators, permission helpers, core/interaction_safety.py and
file_utils.run_blocking_in_thread before adding helpers. Reuse accepted parser/artifact/intake,
source/update/config services and diagnostic redaction. Audit direct SQL in commands/views,
business policy in callbacks, stale predecessor calls, duplicated guards, hidden coupling and
view-only state. Fix only required S8C seams; document unrelated debt without reopening predecessors.

## 8. Tests and security decision

Cover S7-T01/T03/T05 at the caller boundary: same/opposing/missing source; both upload orders;
first side creates no complete selection or intent; exact UpdateID; correction with valid/stale
counterpart; semantic duplicate/callback retry; wrong actor/guild/channel/role; failed second side;
restart with retained identity; B0/no-fight/overall; config confirmation and pending exact endpoint.
Run all five manifested tests, affected S8B pair/season/recovery/config tests, and relevant parser,
window, calculation and command-registration regressions. Test availability/error responses and
permission revalidation, not only mocked success calls.

Baseline registration is 36 top-level / 101 grouped. Propose exact grouped signature/count changes
in scope, update canonical command documentation and respect Discord group limits. Top-level
baseline changes are outside this manifest. Run registration validator and applicable inventory/
registration tests. Run architecture, deferred, security-routing and exact-path test selector,
lint/type/pre-commit, smoke imports and full offline pytest through analyse_pytest_log_noise.py
before broad handoff. Runtime tests are not SQL deployment or operator smoke evidence.

Security routing for this preparation: documented skip, Markdown status/planning/archive/link
changes only, no runtime/config/permission/data-access/deployment behavior changed. Future S8C Bot
implementation requires `$codex-security:security-diff-scan` at its exact final Git target:
**Scan type: Changes; Deep: Off.** Resolve the actual base/head or working patch before starting.
SQL's two documentation paths have an independent documentation-only skip unless separately approved SQL implementation is
needed; any such implementation has its own exact Changes target. No standard/deep codebase audit
or automatic scan/task is selected by this pack.

## 9. Initial review output and acceptance gates

Return actual repo state, exact scope, current service/API and SQL/caller risks, permission and
restart design, helper/refactor decisions, test plan and exact proposed implementation sequence
for approval. Do not re-ask S7 decisions or completed S8B acceptance. Implementation, publication,
promotion and operational execution remain separate gates according to operator authorization.

Acceptance requires the manifested UX paths to use S8B contracts with the tests above, no partial
selection/attestation bypass, preserved endpoints/domain rules, documented command surface, final
Changes evidence and exact PR documentation carry-forward verification. Record measured tests and
any unresolved environmental limits honestly; do not label mocked SQL/provider work as live smoke.

Preserve S6-OPS01/PERF01/CAP01, both uncertain publications, all retained databases/backups/files
and prior evidence. No SQL connection/execution, provider writes, real imports/exports, Discord
action, bot-machine pull, restart, deployment, activation, predecessor operation, Git publication
or new chat is authorized by this starter. Comparisons are not reset instructions.


## Current S8C implementation authorization - 2026-09-13

The operator approved the revised scope and implementation plan. Implement the amended
[contract](../reference/kvk_source_migration/integration_contract_and_consumer_matrix.md) and
[exact 69-path Bot / 6-path SQL manifests](../reference/kvk_source_migration/integration_implementation_manifests.md).
This supersedes the initial-scope-only boundary above; all operational and Git-publication
restrictions remain. Offline validation completed: 4,202 tests passed / 62 skipped, operational logs unchanged.
No live SQL/provider/Discord or bot-machine evidence is claimed. Preserve all pending documentation and both sides of both S8B archive moves.
