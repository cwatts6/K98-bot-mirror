# S10B — Shared Export Coordination Worker and Durable Budget

## Current status — S10E merged; S11 review/scope next, 2026-09-15

S10E Bot [mirror #280](https://github.com/cwatts6/K98-bot-mirror/pull/280),
[production #587](https://github.com/cwatts6/k98-bot/pull/587) and
[SQL #88](https://github.com/cwatts6/K98-bot-SQL-Server/pull/88) are merged and locally pulled.
Bot main/origin main `721ad7e0cd6b160ddddad328c2338a98bdfb6e0a`; production/main `3dbe63e7a47175df85ed17814ea06f9dd3d130b7`; SQL main/origin main `2352a898881d4b74d6eec153bb3cb381d6162041`.
**No changes have been pulled to the bot machine.** Repository delivery is complete;
SQL installation, real provider/Discord execution, runtime acceptance and activation remain unproven.

Next: **S11 Controlled Release and Acceptance, initial review/scope only**:
[task pack](../Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S11%20Controlled%20Release%20and%20Acceptance.md) and [starter](../Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S11%20Controlled%20Release%20and%20Acceptance.md).
Read the [S10E closeout and exact next-PR manifest](../../reference/kvk_source_migration/s10e_closeout_and_s11_handoff.md).
S11 starts from S7's eight-document release proposal plus mandatory carry-forward docs;
reconcile real composition/installation/operational gaps before proposing any runtime scope.
Its eventual authorized Bot PR MUST include every listed pending document, both S10E archive
move identities, this closeout and S11 pack/starter. Verify filename AND previous_filename,
exact content and absent-at-base proof; counts are insufficient. No standalone docs PR,
mixed repositories or manufactured implementation. Pending SQL closeout edits belong only
in the next genuine authorized SQL implementation PR; otherwise carry them forward.

Preserve all recovered documentation evidence, S6-OPS01/PERF01/CAP01, both uncertain publications
and retained data. S8A six scripts, S8B 50 cases/actual restore versus offline history, and S8C
seven local checks remain distinct. S10C/D/E static authoring is not installation/provider proof.
No predecessor rerun, SQL/provider/Discord operation, bot-machine pull/restart/deployment,
activation, new task creation or Git publication is authorized by this documentation closeout.
Earlier dated pending/next-slice instructions are historical and do not reopen accepted work.

## Historical S10D closeout — 2026-09-15

SQL #87 is merged and locally pulled at `80353a6280e523f30c27e724f71e7b47dadadd16`.
Bot main/origin main remains `bf3eccf964601e2975dd86eefe96f7b0153be3bb`; production/main remains
`aa1821adbde9ccda47797caa83b5d5a9958bfce9`. **No changes have been pulled to the bot machine.**
S10D authoring, offline checks and Changes security review are complete; SQL installation and
provider/Discord execution are not established. S10C remains source/static SQL evidence too.
See [S10D closeout and exact carry-forward manifests](../../reference/kvk_source_migration/s10d_closeout_and_s10e_handoff.md).

Next: **S10E Export Operator UX and Rollover, initial review/scope only**:
[task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md) and [starter](Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md).
The eventual authorized S10E Bot implementation PR MUST include every pending Bot document in
that closeout, this pack/starter and all required archive identities. Verify filename AND
previous_filename, or exact merged/content and absent-at-base proof. No standalone docs PR,
repository mixing, manufactured implementation or renewed predecessor/grouping approval.
Both SQL documents were delivered in #87; their new closeout edits stay in SQL for the next
actual authorized SQL implementation PR. S10E scope must assess any genuine SQL delta separately.

Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and every retained database/file.
S8A six scripts, S8B 50 cases/actual restore versus offline history, and S8C seven local checks
remain distinct; none is new live Discord or deployment evidence. Shutdown stops admission and
drains owned delivery; uncertainty retains claims. No lease-age/job-state release.
This documentation closeout authorizes no implementation, Git publication, SQL/provider/Discord
execution, real import/export, bot-machine action, deployment, activation, predecessor rerun or
new task. Earlier dated checkpoints are historical; the current closeout controls the next step.

## S10B implementation checkpoint — 2026-09-14

The operator approved scope and implementation in this task. The historical scope-only and predecessor closeout statements below remain evidence of their original authorization boundary; this checkpoint supersedes them for local S10B code and tests only. No Git publication, SQL/provider/Discord execution, real imports/exports, bot-machine pull/restart/deployment or activation is authorized. S10C/D/E/S11 remain separate.

The exact S7 S10B source/test manifest and the mandatory pending documentation manifest remain one eventual Bot implementation PR. SQL stays at merged #85, 3776dfa6b0892a8800d236fdf111c4d2f93c3813, with no SQL delta. No predecessor rerun or automatic new task occurred.


## Authority and entry state

Initial review/scope only. Prepare scope, risks, tests and an implementation plan for approval.
Do not implement or publish Git changes from this starter. S10A results are accepted; SQL #85 merged
at `3776dfa6b0892a8800d236fdf111c4d2f93c3813` and locally pulled. No bot-machine pull occurred.
Bot main/origin main `8e60e78d850a92b6ff84c6b870b8f0c6c5254806`; production/main
`289bc87e1379941fd6ddafe1a18bb5e7a993d09d`. Comparison anchors only, never reset instructions.
Recheck both repositories and preserve staged/unstaged/untracked/deleted/renamed work.

## Required reading

Read current AGENTS and all core references, the [S10A closeout/exact manifest](../../reference/kvk_source_migration/s10a_implementation_and_s10b_handoff.md),
[S7 contract](../../reference/kvk_source_migration/integration_contract_and_consumer_matrix.md),
[S7 exact manifests](../../reference/kvk_source_migration/integration_implementation_manifests.md),
[architecture/EndScanID amendment](../../reference/kvk_source_migration/phase_2_contract_and_architecture.md),
acceptance scenarios and retained S6/S8 execution/operator evidence. Use authoritative SQL in
`C:/K98-bot-SQL-Server`, including merged S10A six tables, intent/vector/selection/publication/receipt
contracts. Use architecture-scope, SQL-validation and test-selection skills; security routing
selects Changes with Deep off at the exact approved Bot patch after implementation approval.

## S7 implementation boundary to validate before approval

| Repository | Action | Exact path |
|---|---|---|
| Bot | Create | `services/export_coordination_service.py` |
| Bot | Create | `services/export_request_budget.py` |
| Bot | Create | `services/export_coordination_dal.py` |
| Bot | Create | `services/export_snapshot_store.py` |
| Bot | Create | `tests/test_kvk_export_coordination.py` |
| Bot | Create | `tests/test_kvk_export_sql_integration.py` |
| Bot | Modify | `kvk/services/new_source_recovery_service.py` |
| Bot | Modify | `kvk/services/new_source_export_service.py` |
| Bot | Modify | `kvk/services/new_source_delivery_service.py` |
| Bot | Modify | `kvk/dal/new_source_delivery_dal.py` |
| Bot | Modify | `kvk/dal/source_update_dal.py` |
| Bot | Modify | `bot_instance.py` |
| Bot | Modify | `bot_config.py` |
| Bot | Modify | `docs/reference/ENV_REFERENCE.md` |
| Bot | Modify | `docs/reference/runbook_startup.md` |
| Bot | Modify | `docs/reference/runbook_shutdown.md` |
| Bot | Modify | `tests/test_kvk_source_exports.py` |
| Bot | Modify | `tests/test_kvk_source_delivery.py` |
| Bot | Modify | `tests/test_kvk_source_recovery.py` |

Preserve running generation A when B arrives; pin immutable intent/publication/input vectors,
coalesce only eligible pending work, retain replay/repair identity and fair account admission.
Acquire resource sets deterministically with durable owner/fence/version CAS; uncertain jobs retain
claims until authoritative reconciliation. Job state alone cannot release a resource. Persist
account request reservations using server UTC, wait outside SQL transactions, and never hold a SQL
transaction across a provider request. Preserve attempts/parts and scoped legacy receipt identity.
Validate these temporal guarantees in DAL/service code: S10A constraints enforce static shape only.

Preserve independent stats/targets/publication/roster/history/daily consumers; fixed season source;
supplied overall/B0 and authoritative aggregates/DKP; UTC starts, SCANORDER, unused scans, movable
within-season windows, exact endpoint chain, sealed inputs/CAS, durable matched UpdateID, explicit
counterpart attestation and admission locks. No mixed sources, summed-fight overall, silent legacy
fallback or activation based on SourceRouting.Enabled alone.

Use existing SQL connection factories and service/DAL patterns. Validate `EXPORT_COORDINATION_ENABLED`
default false, `EXPORT_SNAPSHOT_ROOT` and `EXPORT_STORAGE_OWNER`; no actual .env edits or credentials.
Admission remains disabled until all required adapters and deployment gates exist. Review startup,
shutdown, stale ownership, durable spool validation and pinned-generation paths before coding.
No new top-level command, S10C legacy/scan adapters, S10D pool schema, S10E recovery/rollover,
S11 release implementation, predecessor rerun or general refactor expansion.

## Tests and approval output

Map S7-T09 through S7-T15 to this boundary and explicitly defer later-slice cases. Plan happy,
negative, duplicate/replay, restart, contention/CAS, uncertain-outcome and stale-owner cases;
A-running/B-arrives regression; durable budgets/cooldowns; immutable snapshots/storage owner;
receipt scope and attempt/part evidence. Validate actual SQL shapes before DAL implementation.
Offline doubles do not prove SQL concurrency or provider truth. SQL/provider/Discord execution
needs a separate exact operation/target plan; do not reuse predecessor execution approval.
Run or justify architecture, deferred-item, test-selection and security-routing validators;
select focused tests and full suite appropriately. Return exact affected paths, risks, unresolved
schema questions, static-versus-runtime guarantees, test plan and implementation approval checkpoint.

## Mandatory documentation delivery in the S10B implementation PR

Include every path in the closeout's current exact carry-forward table, this pack/starter and
any new handoff outputs together with S10B implementation. No standalone documentation PR;
no Bot documents in SQL; do not re-ask this grouping. Preserve both sides of both S9B moves.
S10A pack/starter source paths were never tracked at Bot base: preserve their explicit absence
proof and require the archived destination contents. Check GitHub filename AND previous_filename
coverage, or prove specific already-merged paths, never counts alone. Repeat for later promotion.

S6-OPS01/PERF01/CAP01 remain open; preserve both uncertain publications and all databases/files.
S8B accepted smoke/50-case/actual-restore is distinct from offline history, S8A six scripts and S8C
local checks. No live Discord acceptance inferred. No bot-machine pull/restart, deployment,
activation, real imports/exports, Git publication or automatic new task is authorized here.

## Local implementation validation complete

The approved S10B implementation is present locally. Final offline suite: 4,420 passed, 66 skipped, production logs unchanged. Focused suite: 230 passed, four SQL tests skipped. Final Changes/Deep-off security scan 6c3284aa-7c5f-4647-9299-de5feb5771c0 completed with no findings. See the S10A handoff document final S10B validation section for exact scope, snapshot identity, manifest proofs and retained gates. This post-scan status append is documentation only. Git publication, live execution and activation remain unauthorized.
