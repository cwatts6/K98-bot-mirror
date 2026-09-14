# S9B closeout and S10A handoff

> Superseded handoff checkpoint, 2026-09-14: S10A is accepted, SQL #85 merged and locally
> pulled; no bot-machine pull. Use the [S10A closeout/current exact S10B manifest](s10a_implementation_and_s10b_handoff.md#s10a-final-closeout-and-s10b-delivery-manifest--2026-09-14).
> The historical39-path list below is preserved; current delivery includes the S10A archives
> and S10B pack/starter, with explicit absent-at-base exceptions for never-committed S10A sources.


## Delivered state — 2026-09-14

**S9B implementation, review and repository delivery are complete; not deployed.** The operator
reports all three PRs merged and locally pulled, with no bot-machine pull. Read-only GitHub checks
confirm every merge and final CI result. Bot and SQL were on main with clean worktrees at entry.

| Repository | Merge UTC | Merge commit | Final reviewed head |
|---|---|---|---|
| [K98-bot-mirror #277](https://github.com/cwatts6/K98-bot-mirror/pull/277) | 2026-09-14T13:27:27Z | `2a93217c4f7a7f610f0671b5de1a4d8f32dad0b9` | `e8b6295eb4fbd5a249c6d437c3ed8da8eafc440e` |
| [k98-bot #584](https://github.com/cwatts6/k98-bot/pull/584) | 2026-09-14T13:27:58Z | `289bc87e1379941fd6ddafe1a18bb5e7a993d09d` | `4355ce35c89db3c142317ecd327a281ed263c2a3` |
| [K98-bot-SQL-Server #84](https://github.com/cwatts6/K98-bot-SQL-Server/pull/84) | 2026-09-14T13:27:17Z | `d0916f742f9c88743b97107dfca1f3acbcb32c2e` | `604af8f88e42f43cc80d1848b37312526e56338f` |

Comparison anchors, **never reset instructions**: Bot HEAD/main/origin main
`8e60e78d850a92b6ff84c6b870b8f0c6c5254806`; production/main
`289bc87e1379941fd6ddafe1a18bb5e7a993d09d`; SQL HEAD/main/origin main
`d0916f742f9c88743b97107dfca1f3acbcb32c2e`. Recheck both repos and preserve pending work.

Each Bot PR has 56 provider entries covering all 58 physical paths, after checking exact
filename and previous_filename for both S9A archive moves. SQL #84 has exactly its delivery log
and migration README. Every delivered file blob matches current local HEAD; there are no missing
paths or already-merged exemptions. Provider evidence is retained at
`C:/Users/cwatt/AppData/Local/Temp/k98-s9b-merged-evidence.json`; merged PRs remain the durable proof.
This delivered union is separate from the fresh pending documentation manifest below.

## Delivered behavior and review corrections

Cards use complete fixed-source overall/B0 context and reject stale context-bearing output/views.
Independent KS4/stat numerators, target numbers, history, roster/publication/daily consumers remain
separate. Fallback retains independent history, personal bests, last-KVK summary, matchmaking and
T4/T5 detail without source camp/rank or attachments. Disabled visual cards avoid source loading.
Unavailable guild-channel permission interfaces reject before member lookup. Existing grouped
admin dispatch is source-aware; new-source recompute is inspection-only and exports remain blocked
until the later coordinated exporter. No new top-level command or S10 implementation was added.

All seven inline review threads were answered and resolved across mirror, SQL and production.
The optional shared card-banner compositor remains a structured deferred refactor in the previous
closeout. SQL companion-link/publication wording was corrected; a redundant cross-repository
file URL was removed to satisfy SQL documentation CI. Separate histories were preserved and the
final review-fix patch and all 58 resulting Bot path states matched mirror and production.

## Retained validation and limits

- Final production-checkout offline suite: **4,350 passed, 62 skipped**, 179.00 seconds;
  production operational logs unchanged. Focused posting/view tests: **32 passed**.
- Architecture checks covered all 23 Python paths; deferred validation covered 33 extant Markdown
  paths. Security routing, test selection, import smoke, registration and commit checks passed.
  Registration retained 36 top-level / 101 grouped commands, including eight kvk_admin children.
- Initial S9B Changes scan `d9f0f04f-dfd6-4ffe-a5fa-f7194b15cfb6`, fallback follow-up
  `67b463d9-683c-44c6-951e-ab473a74c743`, and production review-fix scan
  `958c6752-2296-4494-a8b8-ce79118b137e` each completed with zero findings, Deep off.
  Their exact targets remain in the earlier closeout and PR descriptions. They are distinct
  evidence, not a claim that one scan covers another snapshot. SQL had an independent docs-only skip.
- These are retained pre-merge results, not new post-merge execution or production measurements.
  The current documentation-only update has a precise security skip: no runtime, SQL behavior,
  config, permissions, dependencies or deployment behavior changes. No new scan is launched.

Final CI records:
- K98-bot-mirror: [command-governance](https://github.com/cwatts6/K98-bot-mirror/actions/runs/34846580997/job/103983888771) — success.
- k98-bot: [quality](https://github.com/cwatts6/k98-bot/actions/runs/34846586147/job/103983905197) — success.
- k98-bot: [scan](https://github.com/cwatts6/k98-bot/actions/runs/34846586071/job/103983904338) — success.
- k98-bot: [command-governance](https://github.com/cwatts6/k98-bot/actions/runs/34846586053/job/103983904123) — success.
- K98-bot-SQL-Server: [SQL repo validation](https://github.com/cwatts6/K98-bot-SQL-Server/actions/runs/34842409397/job/103970194080) — success.
- K98-bot-SQL-Server: [SQL repo validation](https://github.com/cwatts6/K98-bot-SQL-Server/actions/runs/34842404666/job/103970180469) — success.

Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and every retained database, backup
and file. S8B accepted disposable smoke/50-case and actual-restore evidence stays distinct from
its offline runner-history support, S8A six-script evidence and S8C evidence. S8C seven local
operator checks PASS is not live Discord acceptance. Authoritative aggregates/DKP, UTC starts,
daily SCANORDER, unused scans, movable within-season windows, exact endpoint chain, CAS/sealed
inputs, durable matched UpdateID, explicit counterpart attestation and admission locks remain.
SourceRouting.Enabled alone is insufficient. No bot-machine pull, restart, deployment, activation,
SQL/provider/Discord execution, real imports/exports or predecessor rerun is authorized here.

## Archive disposition

Only the completed S9B task pack and starter move into the task-pack archive. Their full content
and internal links are retained. S7 contracts/manifests, closeouts, operator instructions, S6/S8
execution evidence and all data files remain in place. Archive both sides in the pending manifest.

## Next slice and delivery grouping

Next is **S10A Shared Export Coordination SQL Foundation, initial review/scope only**. S10B/C
workers/adapters, S10D pool schema, S10E recovery/rollover and S11 operations remain later work.
Documentation preparation is approved; SQL/runtime implementation and Git publication are not.

The S10A SQL implementation PR must include **both** `docs/SQL_DELIVERY_LOG.md` and
`migrations/README.md` with its reviewed SQL manifest. Bot documentation cannot be placed in SQL:
the exact pending Bot set below is mandatory carry-forward into the next Bot implementation PR,
S10B. S10A must reconcile this set at entry and hand it onward intact, including its own pack,
starter, this closeout and both sides of both S9B archive moves. No standalone documentation PR.
Do not re-ask the approved documentation grouping. Additional S10A closeout outputs must be added
by exact path when authored. At each PR compare **filename AND previous_filename**, or prove a
specific already-merged file with merge and content evidence. Counts alone never suffice.

## Exact pending Bot documentation manifest

**39 physical Bot documentation paths** after the approved S10A implementation handoff; exact paths, not the count, control delivery.

| Action | Exact Bot path | Delivery |
|---|---|---|
| Modify | `README-DEV.md` | S10B Bot implementation PR |
| Modify | `docs/reference/README.md` | S10B Bot implementation PR |
| Modify | `docs/reference/canonical_command_reference.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/decision_and_evidence_register.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/integration_contract_and_consumer_matrix.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/integration_implementation_manifests.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_acceptance_scenarios.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_contract_and_architecture.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_evidence_and_validation_log.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_implementation_plan.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/post_s6_handoff_log.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/post_s6_integration_requirements.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/release_evidence_log.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/release_readiness_and_rollback.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8a_closeout_and_s8b_handoff.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8b_closeout_and_s8c_handoff.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8c_closeout_and_s9a_handoff.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8c_folder_intake_smoke_evidence.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8c_operator_work_instruction.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s9a_closeout_and_s9b_handoff.md` | S10B Bot implementation PR |
| Create | `docs/reference/kvk_source_migration/s9b_closeout_and_s10a_handoff.md` | S10B Bot implementation PR |
| Create | `docs/reference/kvk_source_migration/s10a_implementation_and_s10b_handoff.md` | S10B Bot implementation PR |
| Modify | `docs/reference/local_sql_development.md` | S10B Bot implementation PR |
| Create | `docs/task_packs/Codex Chat Starter - KVK Source Migration S10A Shared Export Coordination SQL Foundation.md` | S10B Bot implementation PR |
| Delete (archive origin) | `docs/task_packs/Codex Chat Starter - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` | S10B Bot implementation PR |
| Create | `docs/task_packs/Codex Task Pack - KVK Source Migration S10A Shared Export Coordination SQL Foundation.md` | S10B Bot implementation PR |
| Delete (archive origin) | `docs/task_packs/Codex Task Pack - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/KVK Source Migration - Programme Pack.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/README.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S7 Integration Contract and Implementation Planning.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S8A SQL Foundation.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S9A Public Routing and Availability.md` | S10B Bot implementation PR |
| Create (archive destination) | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S7 Integration Contract and Implementation Planning.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S8A SQL Foundation.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S9A Public Routing and Availability.md` | S10B Bot implementation PR |
| Create (archive destination) | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/README.md` | S10B Bot implementation PR |


## Exact pending SQL documentation manifest

| Action | Exact SQL path | Delivery |
|---|---|---|
| Modify | `docs/SQL_DELIVERY_LOG.md` | Mandatory in S10A SQL implementation PR |
| Modify | `migrations/README.md` | Mandatory in S10A SQL implementation PR |

No SQL runtime file is changed by this closeout. The S7 reserved S10A migration filename must
be reconciled with the actual authoring date and sequence during S10A scope before SQL is written;
never rename an already-merged migration. The initial S10A manifest is in its task pack.


## Documentation preparation validation

This closeout/preparation changed only Markdown: the exact 38 physical Bot paths above and two
SQL documentation paths. Both archive origins were compared to their HEAD content after stripping
only the added archive notice and normalizing link targets; original text was retained. All changed
local Markdown links and the SQL CI documentation-reference rule passed. Deferred-item validation
passed for all 36 extant changed Bot Markdown files, and security routing reported zero errors or
warnings. Whitespace checks passed in both repositories. No runtime pytest or SQL execution was
needed or performed for this documentation-only preparation. Both indexes remain empty; no commits,
PRs, pushes, deployment or activation were performed. Exact pending path proof is retained at
`C:/Users/cwatt/AppData/Local/Temp/k98-s10a-pending-manifest.json` and must be refreshed at S10A entry.


## S10A implementation approval — 2026-09-14

The operator approved local S10A implementation and closure of the scoped physical-design gaps.
See [S10A implementation and S10B handoff](s10a_implementation_and_s10b_handoff.md).
The ten SQL paths remain in the SQL repository; the added Bot handoff makes the exact pending
Bot carry-forward 39 paths. All original 38 paths and both S9B archive pairs remain mandatory
for S10B. No SQL execution, Git publication, deployment or activation is authorized.
