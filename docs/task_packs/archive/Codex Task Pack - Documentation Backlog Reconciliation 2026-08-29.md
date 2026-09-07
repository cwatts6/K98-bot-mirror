# Codex Task Pack — Documentation Backlog Reconciliation and Active-Work Index Cleanup

## 1. Task Header

- Task name: `Documentation Backlog Reconciliation and Active-Work Index Cleanup`
- Date: `2026-08-29`
- Owner/context: `KD98 / Kingdom 1198 bot documentation governance`
- Task type: `documentation-only | archive/index reconciliation | programme status correction | deferred-backlog hygiene`
- One-pass approved: `yes, within this exact documentation-only manifest`
- Runtime implementation approved: `no`
- SQL implementation approved: `no`
- Command resync required: `no`
- Bot restart required: `no`
- Production deployment required: `no`
- Starting precondition: the operator has already archived:
  - `Codex Task Pack - KingdomScanData4 Phase 5.2 Post-Stabilisation Cleanup.md`
  - `Codex Chat Starter - KingdomScanData4 Phase 5.2 Post-Stabilisation Cleanup.md`
  - `Codex Task Pack - Player Self-Service Command Centre v2 Phase 8.1 Leadership Player Review Visual Hierarchy Presence and Performance.md`
  - `Codex Chat Starter - Player Self-Service Command Centre v2 Phase 8.1 Leadership Player Review Visual Hierarchy Presence and Performance.md`
  - `MGE Process Polish - Phase 2 Initiation Statement.md`

Run this task from the operator's current local branch/worktree containing those archive moves. Do not
recreate, restore, duplicate, or independently repeat them from an older mirror snapshot.

## 2. Objective

Make the documentation set a reliable source of truth after the three completed workstreams were
archived.

The completed change must:

1. make `docs/task_packs/` accurately distinguish active execution packs, proposed/gated work,
   living programme records, retained contract fixtures, indexes, and reference assets;
2. remove every statement that still calls GovernorOS Phase 8.1 active or in validation;
3. describe MGE Task N as a bounded closure/regression audit rather than an untouched implementation
   task;
4. keep Phase 9 `/stats kingdom` proposed and approval-gated;
5. reconcile the deferred register against the current bot and SQL repository state;
6. move two resolved deferred items into the resolved-history document;
7. add the newly identified transaction-log backup cadence policy item;
8. retain historical delivery records without rewriting what was true at their delivery date.

## 3. Confirmed Starting State

Treat these as locked facts unless the current local Git history proves a more precise reference.

### Completed and archived

- KingdomScanData4 Phase 5.2 post-stabilisation cleanup is complete. Mirror PR #246 records the
  approved cleanup and the remaining transaction-log backup cadence policy question.
- GovernorOS Phase 8.1 is complete and operator accepted on `2026-07-23`. Mirror PR #231 and
  production PR #538 carry the bot delivery; SQL PRs #58 and #59 supplied the additive rank and
  exact-ID existence support.
- MGE Process Polish Phase 2 is complete and its initiation statement is now an archive record.
  Resolve its exact PR/commit reference from local Git history if one is available; do not invent
  a PR number.

### Still active or proposed

- Import Pipeline Task C Slice 13 remains the next existing import-architecture evidence pack, but
  its July object map and timing sample must be refreshed after the August KingdomScanData4
  import/locking/immutable-handoff/delta/provenance work.
- GovernorOS Phase 9 `/stats kingdom` remains proposed and gated. It is not approved for immediate
  runtime implementation merely because Phase 8.1 is complete.
- MGE Tasks A-M are delivered. Task N is a bounded closure audit over already-present wiring,
  rehydration, permission, startup, shutdown and cross-module regression evidence.
- The KVK_ALL Phase 4 Metric Source Rules and Phase 10 Metric Source Correction documents remain at
  their top-level paths only because SQL contract tests assert those paths. They are retained
  contract fixtures, not active task packs.

### Deferred-register corrections

- `dbo.vAllianceActivity_WeeklyCumulative` is resolved: SQL migration
  `20260727_000_retire_vAllianceActivity_WeeklyCumulative.sql` guarded and retired the invalid,
  unused view.
- The PR-based SQL promotion workflow is resolved: the SQL repository now has migration-driven
  deployment, PR validation, guarded deployment, migration/deployment history, safe export
  branches, drift checks, backup readiness and nightly export tooling.
- `dbo.IMPORT_STAGING_PROC` is now a narrow public wrapper. Any remaining decomposition item must
  target `dbo.IMPORT_STAGING_PROC_CORE` and its current staging/receipt boundaries.
- The old slow-pytest timing list is historical. The latest known full-suite result is
  `2999 passed, 2 skipped`, but no current `--durations` artifact exists, so a fresh profile is
  required before prioritising test optimisations.
- `event_calendar/pinned_embed.py::_save_tracker()` still uses direct `Path.write_text()`.
- `DL_bot.py::_offload_callable` still catches execution exceptions and falls through to another
  backend, so once-only callable failure semantics remain the highest-priority confirmed
  implementation-ready item.
- The Phase 5.2 cleanup found both 15-minute and 5-minute schedules enabled on the MINI_AMD
  transaction-log backup job. The intended policy has not been confirmed.

## 4. Exact File Manifest

Modify only these existing documentation files, in addition to the archive moves already completed:

1. `docs/task_packs/README.md`
2. `docs/task_packs/archive/README.md`
3. `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
4. `README-DEV.md`
5. `docs/task_packs/MGE Sign-Up Tool.md`
6. `docs/task_packs/mge_implementation_progress.md`
7. `docs/reference/deferred_optimisations.md`
8. `docs/reference/archive/deferred_optimisations_resolved.md`

Reference inputs supplied with this task:

- `deferred_optimisations_reconciled_proposal.md`
- `deferred_optimisations_resolved_append.md`

Do not modify:

- Python runtime code;
- SQL source, migrations, snapshots, jobs or schedules;
- configuration, dependencies, assets or generated caches;
- command registration, permissions or Discord visibility;
- the bodies of completed archived task packs except for an explicitly required archive-index link;
- historical delivery text merely to make old test counts or old phase wording look current.

## 5. Required Document Changes

### 5.1 `docs/task_packs/README.md`

Add a concise current-state section near the top. It must classify the surviving top-level files
rather than implying that every top-level Markdown file is an active executable task.

Use this model:

| Classification | Files / programme | Status |
|---|---|---|
| Active execution pack | Task C Slice 13 task pack and chat starter | Evidence pack exists; refresh July object/timing baseline before execution |
| Proposed/gated feature | Phase 9 `/stats kingdom` task pack and chat starter | Product direction retained; audit, SQL, visual, performance, security and scheduling gates still apply |
| Closure-audit records | `MGE Sign-Up Tool.md`, `mge_implementation_progress.md` | Tasks A-M complete; Task N bounded closure audit pending |
| Living programme record | Player Self-Service Command Centre v2 programme pack | Complete through Phase 8.1; Phase 9 proposed |
| Retained contract fixtures | KVK_ALL Phase 4 Metric Source Rules and Phase 10 Metric Source Correction | Completed records retained at asserted paths; not active work |
| Index/reference | `README.md`, `me_dashboard_screenshot.jpg` | Documentation index and visual reference |

Also:

- add a short `Recently archived` note for Phase 5.2, Phase 8.1 and MGE Process Polish Phase 2;
- remove or replace every stale statement that lists Phase 8.1 as active or in validation;
- update the MGE paragraph so it does not present Task N as a broad unstarted build;
- update the Slice 13 paragraph to require a current post-August evidence/object refresh;
- preserve the long historical delivery catalogue unless a statement is presently false.

### 5.2 `docs/task_packs/archive/README.md`

Add concise archive-index entries for:

1. KingdomScanData4 Phase 5.2 post-stabilisation cleanup;
2. GovernorOS Phase 8.1;
3. MGE Process Polish Phase 2.

For Phase 8.1, record completion and operator acceptance on `2026-07-23`, mirror PR #231,
production PR #538 and SQL PRs #58/#59.

For Phase 5.2, record mirror PR #246 and that the cleanup completed without runtime/SQL behaviour
change. Keep the transaction-log backup cadence as a separate unresolved policy item, not as
unfinished Phase 5.2 work.

For MGE Process Polish Phase 2, use the exact local Git evidence. If no authoritative PR number is
recorded, state that the completed initiation/delivery record is archived without inventing one.

Replace the stale sentence saying Phase 8.1 records remain active in `docs/task_packs/`.

### 5.3 Player Self-Service Command Centre v2 programme pack

Update only current-status statements and the phase matrix.

The programme header must state:

- GovernorOS is complete and operator accepted through Phase 8.1 on `2026-07-23`;
- Phase 8.1 refined the existing `/stats player` journey without adding a command;
- Phase 9 `/stats kingdom` remains proposed and approval-gated;
- the performance-evidence item for the delivered Phase 8.1 path remains in the deferred register
  and does not make the implementation pack active.

In the phase/status matrix:

- Phase 8: complete;
- Phase 8.1: complete and archived;
- Phase 9: proposed/gated, not implementation-ready.

Preserve historical Phase 1-8.1 design and delivery sections. Add supersession/current-status notes
rather than rewriting the historical record.

### 5.4 `README-DEV.md`

Replace the paragraph beginning with the equivalent of `Phase 8.1 is the active audit-first
refinement` with a completion record.

The replacement must say:

- Phase 8.1 completed and was operator accepted on `2026-07-23`;
- it retained `/stats player`, permissions, privacy and command surface;
- it delivered the final visual hierarchy, Presence/Last Active, location/shield, KVK/record,
  Power/Acclaim rank and exact-ID existence refinements;
- the task pack/starter are archived;
- representative SQL performance evidence remains separately deferred;
- Phase 9 remains proposed and gated.

Do not change current runtime instructions or test commands unless a path is actually invalid.

### 5.5 MGE programme records

#### `MGE Sign-Up Tool.md`

Add a status banner immediately below the title:

> **Status — 2026-08-29:** Tasks A-M are delivered. Task N is not an untouched implementation
> phase: command registration, startup cache refresh, lifecycle scheduling, SQL-backed message
> persistence, permission coverage and restart/rehydration regression tests already exist. The
> remaining action is a bounded closure audit. Do not continue broad MGE implementation from this
> pack unless that audit identifies a separately approved gap.

Keep the original feature specification as historical/acceptance context.

#### `mge_implementation_progress.md`

Change Task N from `Pending` to:

```text
🟨 Closure audit pending
```

Use a note equivalent to:

```text
Existing command/startup/cache/scheduler/permission/rehydration wiring is present.
Run one bounded closure and cross-module regression audit; document any proved gap as
a separate follow-on rather than silently expanding Task N.
```

Add a `Task N closure audit` checklist covering:

- `/mge` command registration and decorators;
- startup cache refresh;
- lifecycle scheduler registration after readiness;
- SQL-backed event/message identity;
- persistent view reattachment and restart behaviour;
- permission revalidation;
- shutdown/background-task cancellation;
- results-import route wiring;
- Ark/calendar/registry regression boundaries;
- focused tests and current command-registration validation.

Do not mark Task N complete in this documentation-only change unless current code, tests and a
recorded validation run prove every checklist item. If a gap is found, record it; do not implement
it in this PR.

### 5.6 Deferred optimisation register

Replace `docs/reference/deferred_optimisations.md` with the supplied
`deferred_optimisations_reconciled_proposal.md`, subject to a final current-tree verification.

The replacement intentionally:

- retains 25 active items;
- removes the resolved weekly cumulative-view item;
- removes the resolved SQL-promotion-workflow item;
- remaps the import-staging item to `dbo.IMPORT_STAGING_PROC_CORE`;
- refreshes the Slice 13, `stats_module.py`, pytest, dashboard, personal-stats, leadership-review,
  renderer-framework and legacy PreKvK wording;
- marks Phase 8.1 implementation complete while retaining its evidence-only performance item;
- adds `Status` and `Last verified` after the seven validator-required fields;
- links Slice 13 through `Promoted task pack`;
- adds the MINI_AMD transaction-log backup cadence policy item;
- keeps the offload once-only item as `implementation-ready — highest priority`;
- keeps pinned-calendar atomic persistence as `implementation-ready`.

Preserve this exact first-field order after every `### Deferred Optimisation` heading:

1. `Area`
2. `Type`
3. `Description`
4. `Suggested Fix`
5. `Impact`
6. `Risk`
7. `Dependencies`

`Status`, `Last verified`, and optional `Promoted task pack` must come after `Dependencies` so the
existing validator remains compatible.

### 5.7 Resolved deferred history

Append the supplied `deferred_optimisations_resolved_append.md` to
`docs/reference/archive/deferred_optimisations_resolved.md`.

It records:

- guarded retirement of `dbo.vAllianceActivity_WeeklyCumulative`;
- completion of the PR-based SQL promotion workflow.

Do not move the new backup-cadence item to resolved history. No schedule decision has been made.

## 6. Deferred Status Decisions

Use this status mapping during final review:

| Item | Status |
|---|---|
| Calendar sent-key state | evidence required |
| Inventory import view orchestration | later refactor |
| `IMPORT_STAGING_PROC_CORE` decomposition | active — remapped after KingdomScanData4 Phase 5 |
| `UPDATE_ALL2` / `SUMMARY_PROC` | promoted task pack — refresh required before execution |
| residual `stats_module.py` extraction | blocked by Task C Slice 13 |
| deprecated KVK command removal | operator-gated |
| slow pytest paths | re-audit required |
| Ark command orchestration | later refactor |
| remaining redirect-only paths | evidence and operator-gated |
| `InventoryReportPreference` retirement | destructive SQL audit-gated |
| dashboard KSD4 reads | evidence required — rebaseline |
| Personal Stats SQL performance | evidence required — rebaseline |
| Leadership Player Review performance | evidence required |
| Last Login | blocked by source contract |
| universal renderer/view framework | watchlist |
| broad export redesign | watchlist |
| public calendar/KVK calendar UX | proposed design programme |
| legacy PreKvK objects | SQL object revalidation required |
| queue-domain redesign | watchlist |
| SQL-backed queue persistence | conditional watchlist |
| pinned-calendar atomic tracker writes | implementation-ready |
| shared role-name permission fallback | policy-gated |
| upload admission/backpressure | evidence and design-gated |
| offload once-only failure semantics | implementation-ready — highest priority |
| transaction-log backup cadence | operator policy decision required |

Resolved history, not active register:

- `dbo.vAllianceActivity_WeeklyCumulative`;
- PR-based SQL promotion workflow.

## 7. Search and Consistency Checks

Before editing, search the current worktree for:

```text
Phase 8.1 is the active
Phase 8.1 refinement records remain
implementation is in validation
MGE Process Polish - Phase 2 Initiation Statement
vAllianceActivity_WeeklyCumulative
SQL development and deployment workflow
IMPORT_STAGING_PROC
1450 passed
387k rows
```

Classify each hit:

- current status text to update;
- valid historical delivery evidence to retain;
- SQL migration/resolved-history reference to retain;
- stale deferred entry to remove or rewrite.

After editing, verify:

- no completed Phase 5.2, Phase 8.1 or MGE Process Polish Phase 2 file remains at the top level;
- each archived source has exactly one archive copy;
- no current-status paragraph calls Phase 8.1 active;
- Phase 9 remains proposed/gated;
- MGE Task N is `Closure audit pending`, not `Pending implementation`;
- active deferred count is exactly 25;
- the two resolved items exist in resolved history;
- the backup-cadence item exists only in the active register;
- all documented paths exist or are explicitly historical.

## 8. Validation

Run from the bot repository root:

```powershell
python scripts/validate_deferred_items.py docs/reference/deferred_optimisations.md
python scripts/validate_deferred_items.py docs/reference/archive/deferred_optimisations_resolved.md
python scripts/validate_architecture_boundaries.py
python scripts/select_tests.py
python scripts/validate_codex_security_routing.py
python scripts/validate_command_registration.py
git diff --check
```

Also run a changed-file pre-commit pass where supported:

```powershell
pre-commit run --files `
  README-DEV.md `
  "docs/task_packs/README.md" `
  "docs/task_packs/archive/README.md" `
  "docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md" `
  "docs/task_packs/MGE Sign-Up Tool.md" `
  "docs/task_packs/mge_implementation_progress.md" `
  "docs/reference/deferred_optimisations.md" `
  "docs/reference/archive/deferred_optimisations_resolved.md"
```

A full runtime pytest run, SQL validation, bot restart, command resync and Discord smoke are not
required for a Markdown-only reconciliation. If repository policy automatically runs them, record
the result; otherwise record the explicit documentation-only skip.

## 9. Security Review Decision

Expected decision: documented skip.

Required rationale:

- exact diff is Markdown/archive/index only;
- no runtime, SQL, permission, input, data-access, configuration, dependency, deployment, network,
  filesystem-persistence implementation, command or schedule behaviour changes;
- the task documents existing reliability/security items but does not remediate them.

Run `python scripts/validate_codex_security_routing.py` and retain its result.

## 10. Definition of Done

The task is complete only when:

- the operator's five archive moves remain intact;
- the top-level task-pack index has an explicit current execution set;
- Phase 8.1 is consistently complete/archived in the task-pack README, archive README,
  GovernorOS programme pack and `README-DEV.md`;
- MGE A-M are shown complete and N is a bounded closure audit;
- Phase 9 remains proposed/gated;
- the active deferred register contains exactly 25 structurally valid items;
- weekly cumulative-view retirement and SQL promotion are in resolved history;
- the import-staging item names the current core procedure;
- old pytest/cardinality baselines are clearly historical, not current conclusions;
- the backup cadence item is added without changing a live SQL Agent schedule;
- all validators and `git diff --check` pass;
- the final response includes:
  - exact file manifest;
  - concise status changes;
  - validation results;
  - documented security skip;
  - any unresolved evidence gap;
  - recommended next engineering task: offload once-only callable failure semantics.
