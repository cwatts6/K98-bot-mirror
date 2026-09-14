# KVK Source Migration S9B — Stats/Target Card Context and Grouped Admin Source Dispatch

## S9B implementation authorization — 2026-09-14

The operator approved the initial review and implementation plan with the two exact path
amendments: `commands/kvk_targets_card_posting.py` for send/edit/retry freshness, and
`docs/reference/canonical_command_reference.md` for existing grouped-command semantics.
The original 22 runtime/test paths remain in scope; the amended runtime/test scope is **23**.
The mandatory documentation carry-forward is now **35 physical paths**. The eventual Bot
union is **58 physical paths**, including both sides of both S9A archive moves. This approval
permits local implementation and offline validation/review, not staging, commits, publication,
live operations or activation. The original scope-only starter below is historical.
SQL's two pending documentation paths remain a separate SQL PR in the same delivery cycle.


## Authority and required reading

Prepared 2026-09-14. **Initial review/scope only; S9B implementation is not authorized.**
The operator approved the S9A documentation closeout, archive moves and this S9B task preparation.
Do not create another task automatically. Review current AGENTS/core references, the
[S9A closeout](../reference/kvk_source_migration/s9a_closeout_and_s9b_handoff.md), [approved S7 contract/consumer matrix](../reference/kvk_source_migration/integration_contract_and_consumer_matrix.md),
[exact implementation manifests](../reference/kvk_source_migration/integration_implementation_manifests.md),
[architecture and EndScanID amendment](../reference/kvk_source_migration/phase_2_contract_and_architecture.md),
[acceptance scenarios](../reference/kvk_source_migration/phase_2_acceptance_scenarios.md),
[post-S6 requirements](../reference/kvk_source_migration/post_s6_integration_requirements.md), retained S6 evidence,
and [S8C execution/operator evidence](../reference/kvk_source_migration/s8c_folder_intake_smoke_evidence.md).
Read authoritative SQL and repository guidance (including AGENTS if present) in C:/K98-bot-SQL-Server without connecting to a database.
S7 decisions and predecessor acceptance remain settled. Do not re-ask them.

## Scope summary and affected areas

Connect ordinary stats-card and target-card callers to fixed-source complete context; complete
source-aware dispatch within the existing grouped admin commands. Trace calls without injected
providers. Keep main KS4/stat numerators, target numbers/publications, roster, independent caches,
history and daily consumers independent. Context must not change target arithmetic or authority.
The approved S7 runtime/test scope is exactly these **22 existing Bot paths**, verified at handoff:

| Repository | Action | Exact path |
|---|---|---|
| Bot | Modify | `kvk/services/kvk_stats_card_service.py` |
| Bot | Modify | `kvk/dal/kvk_stats_card_dal.py` |
| Bot | Modify | `kvk/models/kvk_stats_card.py` |
| Bot | Modify | `kvk/rendering/kvk_stats_card_renderer.py` |
| Bot | Modify | `commands/kvk_stats_card_posting.py` |
| Bot | Modify | `ui/views/kvk_stats_card_views.py` |
| Bot | Modify | `kvk/services/kvk_admin_service.py` |
| Bot | Modify | `kvk/dal/kvk_admin_dal.py` |
| Bot | Modify | `commands/stats_cmds.py` |
| Bot | Modify | `tests/test_kvk_source_card_context.py` |
| Bot | Modify | `tests/test_kvk_stats_card_payload.py` |
| Bot | Modify | `tests/test_kvk_stats_card_dal.py` |
| Bot | Modify | `tests/test_kvk_stats_card_posting.py` |
| Bot | Modify | `tests/test_kvk_stats_card_views.py` |
| Bot | Modify | `tests/test_kvk_admin_service.py` |
| Bot | Modify | `tests/test_kvk_embed_diagnostic_command.py` |
| Bot | Modify | `kvk/services/kvk_targets_card_service.py` |
| Bot | Modify | `kvk/models/kvk_targets_card.py` |
| Bot | Modify | `kvk/rendering/kvk_targets_card_renderer.py` |
| Bot | Modify | `tests/test_kvk_targets_card_service.py` |
| Bot | Modify | `tests/test_kvk_targets_card_renderer.py` |
| Bot | Modify | `tests/test_kvk_targets_card_posting.py` |

This table is the implementation boundary, not the complete delivery manifest. The initial complete union is **56 physical Bot paths** (22 runtime/test + 34 documentation),
before approved amendments. The eventual Bot PR must also include **every exact pending Bot documentation path** in the
[closeout carry-forward manifest](../reference/kvk_source_migration/s9a_closeout_and_s9b_handoff.md), including this pack, the starter, closeout,
updated evidence/work instruction and both old/new paths of both S9A archive moves.
The operator has approved this documentation grouping; do not create a standalone closeout PR
or seek renewed approval for carrying these documents. Refresh the exact union after approved
amendments. Before marking the PR ready, compare GitHub `filename` **and** `previous_filename`
against that union and prove each specific already-merged exemption with merge/content evidence.
Counts alone are insufficient. The delivered S9A 58-path union is historical proof, not a new
pending S9B runtime manifest. Carry the pending SQL `docs/SQL_DELIVERY_LOG.md` and
`migrations/README.md` in a **separate SQL-repository PR in the S9B delivery cycle**; never in Bot.
Git publication still needs separate authorization.

## Architecture direction and invariants

- Services own source resolution, authority, context assembly and availability/cache decisions;
  DAL owns validated SQL and row mapping. Commands/views own permissions, interaction lifecycle
  and rendering through services. No embedded SQL in commands/views or new top-level command.
- Reuse the merged S9A fixed-source selection and immutable SeasonRead contract. A season cannot
  mix sources or silently fall back to legacy. SourceRouting.Enabled alone is insufficient.
  S9A resolver paths are outside the 22-path boundary: propose an explicit amendment if needed.
- New-source card context comes from independently supplied current complete **overall** and the
  **B0 frozen cohort**. Do not derive it by summing fights or querying legacy camp/rank as fallback.
  Preserve authoritative kingdom/camp aggregates and DKP, independent overall, UTC starts,
  daily SCANORDER, exact endpoint chain, retained unused scans and movable within-season windows.
- Preserve matched durable UpdateID, publication identity, CAS/sealed inputs, explicit counterpart
  attestation and admission locks. Availability must distinguish disabled, missing, unsupported,
  incomplete and stale context; suppress unavailable source context while keeping valid independent
  card numbers. Label source, period/basis, as-of and cohort/rank availability honestly.
- Views and rendered-file caches must pin the full source/config/publication identity or refresh
  the whole card consistently. Recheck permission, ownership and freshness at action time; no
  partial old/new context, silent retarget or reuse after stale/restart invalidation.
- Grouped admin scans/windows/diagnostics must dispatch by fixed source. New-source recompute is
  inspection-only and cannot rewrite authoritative finals. Export requests remain subject to S10
  coordinator ownership; reject unavailable/unimplemented routes rather than bypassing it.
  Keep existing grouped commands within the 25-child limit; measure actual registration after edits.

## Initial caller, SQL and persistence review

Trace stats_cmds -> posting -> stats-card service/DAL/model/rendering -> cached view callbacks;
trace targets-card service -> shared context with its separate target-publication inputs. The current
explicit injected-source context tests do not establish ordinary caller integration. Inspect posting's
legacy-output fallback so a source-context failure cannot expose legacy camp context for a new-source
season. Trace grouped admin service/DAL dispatch and authorization, including stale private previews.
Validate every SQL object/column/parameter/result shape against authoritative definitions, including
existing overall/cohort/read selection and legacy card/admin queries. No SQL runtime amendment is
preapproved. Report missing objects or a required schema change before implementation; assess SQL
separately from Bot. Identify which view/cache state survives restart and how stale identities fail.

## Risks, performance and robustness

Highest risks are mixed-source context, cohort/rank mismatch, independent target/stat regressions,
stale cached interactions and grouped admin bypass of source authority or export admission.
Use one consistent read identity throughout assembly; avoid duplicate context queries across service
and renderer. Preserve S9A short authority locks and read/action revalidation; never place expensive
row loads or rendering inside admission locks. Define offline query-count and lock-boundary checks
where changed code adds reads; do not claim measured production improvement from unit tests.
S6-PERF01 remains open. No new global cache or broad refactor is approved merely for optimisation.
Fix in-scope layer/fallback/state issues after implementation approval. Inspect established helpers
before adding any. Capture actual out-of-scope debt using the Deferred Optimisation framework;
do not invent debt or defer untriaged security findings.

## Test strategy and security review

Map the above risks to the listed test paths and S7 ownership (C35–C38, C40, C42, C43; N06, N11),
checking adjacent independent consumers and preserved C41/C53/C54 behavior. Retain the full C01–C65
and N01–N12 ownership map; do not claim all consumers migrated in S9B. Select applicable S7 tests,
including T02, relevant T16, T52–T55 and T60–T64, against their exact definitions before implementation.
Test ordinary legacy/new callers; current complete overall/B0; unavailable/disabled/unsupported/stale
context; independent numeric payload equality; permission/ownership denial; cache token changes,
restart/stale actions, grouped dispatch, inspection-only recompute and export rejection boundaries.
Render synthetic stats/target samples with missing/stale context and long/Unicode labels after
approval; check readability and unchanged independent numbers. Use deterministic offline fixtures.

After approved runtime edits, run focused tests, architecture/deferred/security-routing validators,
exact-path test selection, import smoke, command-registration checks and the appropriate full offline
suite with operational-log isolation. Justify any skip. Review authoritative SQL statically; no SQL,
provider or live Discord execution is authorized by this pack. For current docs-only preparation,
see the separate closeout validation and documented security skips.
For implementation, use **k98-security-review-routing**, then **Changes with Deep off** against the
exact final Bot implementation target. Assess any SQL diff independently. No routine Codebase or
Deep scan. Run the normal whole-PR review after implementation; test success alone is insufficient.

## Implementation plan for approval

1. Recheck both repositories, preserve pending work and confirm the 22-path plus documentation
   union. Trace ordinary callers and authority/cache boundaries; validate SQL and helper reuse.
2. Return scope, affected layers, SQL findings, risks, test mapping, any exact amendments and the
   implementation plan for approval. Do not infer runtime approval from this task's preparation.
3. Once approved, wire shared card context through service/DAL/model/rendering, preserving
   independent stats/targets; harden view/cache lifecycle and grouped admin dispatch within scope.
4. Validate deterministic failure/authority cases, rendering and performance boundaries; complete
   runtime tests, security routing/Changes review and final PR review at the exact implementation.
5. Update evidence and the complete carry-forward manifest. Only when separately authorized,
   create Bot and separate SQL PRs, proving filenames/previous filenames and any merged exemptions.

## Operational boundary

S9A mirror #276, production #583 and SQL #83 are merged and locally pulled. No changes have been
pulled to the bot machine. No SQL/provider/Discord execution, real imports/exports, bot-machine
pull/restart/deployment, activation, predecessor rerun or Git publication is authorized here.
S10/S11 remain later work. Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and all
retained databases/backups/files. Keep S8B accepted smoke/50 cases and offline runner history
separate from S8A six-script evidence and S8C disposable SQL/folder/operator evidence.


## Local implementation outcome — 2026-09-14

Approved implementation with both exact amendments is complete locally. Full offline validation:
**4,333 passed / 62 skipped**, operational logs unchanged. Changes security review
`d9f0f04f-dfd6-4ffe-a5fa-f7194b15cfb6`: zero findings, Deep off. Architecture, deferred/routing
validators, imports, registration, visual inspection and whole-change review completed.
See the [S9B implementation record in the closeout](../reference/kvk_source_migration/s9a_closeout_and_s9b_handoff.md)
for exact manifest, hashes, test mapping, scan artifacts, limitations and retained evidence.
All work is unstaged/uncommitted. Publication remains separately authorized; Bot58 and separate
SQL2 delivery grouping is settled. No bot-machine, SQL, provider or live Discord operation occurred.
