# Codex Task Pack - Discord Embed Payload Safety Phase 2E Ark Persistence Orchestration and Delivery Observability

## 1. Task Header

- Task name: `Discord Embed Payload Safety Phase 2E Ark Persistence Orchestration and Delivery Observability`
- Date: `2026-09-03`
- Owner/context: `Chris Watts / next planning slice after Phase 2D candidate acceptance`
- Task type: `deferred optimisation batch / architecture and observability`
- One-pass approved: `no`
- Status: `prepared for audit/scope; implementation not approved`
- Repository: `K98-bot-mirror` bot repository first; SQL is evidence-only unless separately approved

## 2. Required Reading And Prerequisites

Before work, read current `AGENTS.md`, `README-DEV.md`, `docs/reference/README.md`, its indexed core
standards, root/applicable `SECURITY.md`, the archived Discord Embed Payload Safety audit and Phase
2B/2D delivery records, and the three source items in `docs/reference/deferred_optimisations.md`.

Phase 1 through Phase 2D behavior is prerequisite, not scope to reopen. Phase 2D candidate delivery,
review, automated validation, and operator smoke are accepted through mirror PR #255 and production
PR #562, but both manual merges and final production-main verification were pending when this pack
was prepared. Revalidate both remotes, branch/head, worktree, PR merge states, the final production
main revision, and presence of Phase 1-2D before recommending an implementation base. Read-only
audit may start before merge; runtime/test changes require an approved base containing the accepted
Phase 2D tree.

## 3. Objective

Make Ark restart-sensitive history policy, team-builder audit orchestration, and registration
delivery telemetry explicit without changing the user workflow. First determine whether production
evidence justifies a confirmation-update retention change; then propose only the smallest coherent
service and outcome-model corrections supported by the audit.

The implementation, if approved, must preserve command placement, permissions, interaction
audience, Ark match/roster/team meaning, Discord message identity, announcement behavior, SQL/DAL
contracts, JSON compatibility, restart behavior, and every send/edit/recreate decision.

## 4. Background And Source Deferred Items

### Confirmation-update history

- Area: `ark/state/ark_state.py`, `ark/confirmation_flow.py`, and persisted
  `confirmation_updates` in `ark_message_state.json`.
- Type: architecture.
- Evidence: updates are append-only and unbounded in persisted state; Phase 2B bounded only their
  rendered representation. Retention changes historical visibility and restart data.
- Suggested decision: measure real cardinality and operator use, define retention/archive and
  compatibility semantics, and select `fix now` or `defer`. SQL storage is not pre-approved.
- Impact: medium; risk: medium; dependencies: production evidence and operator policy decision.

### Team-builder audit-service boundary

- Area: `ui/views/team_builder_views.py`, `ark/ark_draft_service.py`, Ark audit coordination, and
  `ark/dal/ark_dal.py`.
- Type: architecture.
- Evidence: the view directly imports `insert_audit_log` for auto-balance, reset, and remove while
  related persistence/publish workflows already use service boundaries. The architecture validator
  carries a narrow exception.
- Suggested decision: move audit coordination behind the narrowest existing or new Ark service
  contract while preserving exact audit action names, actor/match/governor IDs, detail JSON,
  persistence-before-audit order, failure behavior, acknowledgement, and webhook refresh sequence.
- Impact: medium; risk: medium; dependencies: interaction and audit-failure tests.

### Registration delivery outcomes

- Area: `ark/registration_messages.py`, `ark/registration_flow.py`, and structured runtime logs.
- Type: consistency.
- Evidence: a successful in-place edit returns `(False, False)` because the first boolean means
  moved/reposted, but `ensure_message_result` logs it as `delivered=False`; the same pair can follow
  a caught edit failure.
- Suggested decision: define an explicit, stable outcome vocabulary distinguishing at least
  `edited`, `moved`, `reposted`, `recreated`, and `failed`, while preserving existing delivery,
  return, persistence, announcement, and caller behavior or providing a compatibility adapter.
- Impact: medium; risk: low; dependencies: operator approval of vocabulary and log-contract tests.

## 5. Scope

### In Scope

- Measure persisted confirmation-update cardinality, age, duplication, size, restart use, and the
  operational need for full history without copying private state values into documentation.
- Produce retention options covering keep-all, bounded most-recent history with a visible count,
  archival, and separately approved SQL durability; state migration, backward compatibility,
  failure recovery, concurrent save behavior, and rollback for each.
- Inventory every producer, serializer, loader, renderer, refresh, and cleanup path for
  `confirmation_updates`; do not infer safety from the Phase 2B embed bound alone.
- Inventory all team-builder assign/remove/reset/auto-balance/publish/unpublish audit ownership and
  distinguish DAL-owned persistence auditing from view-owned operational auditing.
- Propose a service boundary that removes the view's direct DAL audit import without duplicating
  audits or changing action order, exceptions, Discord acknowledgements, or webhook edits.
- Inventory every `upsert_registration_message()` caller and outcome path: missing destination,
  unavailable channel, fresh send, same-channel edit, move, forced repost, deleted-message
  recreation, ordinary edit failure, send failure, and state-persist failure.
- Define explicit registration outcome logging and tests with unchanged message/state behavior.
- Update documentation and structured deferred records for every accepted, rejected, or still-gated
  item.

### Out Of Scope

- Any Phase 1-2D embed/content/attachment/redaction policy or operator-diagnostic behavior.
- Phase 2F atomic `active_reminders` replacement and Phase 2G atomic Pre-KVK reservation.
- Stats or KVK History once-only executor work.
- Ark command names/options/grouping, permissions, guild/channel restrictions, public/ephemeral/DM
  audience, requester ownership, mentions, reminder schedules, match lifecycle, roster/team rules,
  message/view identity, timeouts, startup, scheduler, or rehydration semantics.
- SQL schema/procedure/DAL-query changes, a new database, JSON shape changes, config/dependency
  changes, or data migration without separate evidence, SQL validation, operator approval, and a
  companion SQL plan where applicable.

## 6. Skills And Security Routing

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before implementation to map persistence, service, interaction, and approval boundaries. |
| `k98-discord-command-feature` | use if implementation touches the team-builder view or registration Discord flow | Preserve interaction and delivery contracts. |
| `k98-sql-validation` | use for audit; implementation-gated | Confirm no current SQL contract is implicated; mandatory before proposing durable SQL storage or DAL changes. |
| `k98-test-selection` | use | Select focused state, service, delivery, view, restart, and log-contract tests. |
| `k98-deferred-optimisation-capture` | use | Keep Phase 2F/2G and rejected retention options owned without expanding this slice. |
| `k98-pr-review` | use after implementation | Whole-diff architecture, interaction, test, and promotion-readiness review. |
| `k98-promotion-check` | use only after review | Required before production promotion/deployment. |
| `k98-security-review-routing` | use | Bot runtime changes route to Changes-only with Deep off; no routine Codebase or Deep scan. |

### Security Review Decision

| Repository | Decision | Target | Expected setup / execution | Evidence |
|---|---|---|---|---|
| Bot | Changes review after implementation | Exact approved Phase 2E base..head | `Changes + Deep Off` | Required because restart-sensitive state, Discord interactions, audit records, identifiers, and operational logs are touched. |
| SQL | Documented skip if unchanged; otherwise stop for separate approval and review | SQL repo worktree/base..head | `Not applicable` when no diff | Audit the authoritative SQL repo; a skip is valid only if no SQL object, DAL query, migration, or persistence contract changes. |

Do not start a Standard/Codebase or Deep scan. Suspected vulnerabilities route to Codex Security
triage; they are not deferred-optimisation findings.

## 7. Mandatory First Response And Stop Gate

The first response is audit/scope and architecture planning only. Do not edit runtime code or tests.
It must:

1. confirm mirror/production branch heads, worktree, Phase 1-2D presence, PR #255/#562 merge states,
   final production-main verification state, intended base, and bot-first scope;
2. map every confirmation-update producer through JSON load/save, render, refresh, restart, failure,
   and cleanup behavior, with privacy-safe production cardinality evidence;
3. offer evidence-based retention choices and state which choice is recommended, deferred, or needs
   a product decision; include compatibility, migration, recovery, concurrency, and rollback;
4. map team-builder action, persistence, audit, acknowledgement, webhook, permission/ownership,
   timeout, and failure order, and identify the exact service boundary;
5. map every registration upsert caller and all send/edit/move/repost/recreate/failure outcomes,
   current tuple consumers, state writes, announcement decisions, and logs;
6. propose an outcome vocabulary and backward-compatible API shape without altering runtime
   delivery decisions;
7. provide a findings matrix using `safe`, `fix now`, `defer`, or `not runtime`;
8. explain how commands, permissions, visibility, ownership, mentions, ordering, match/team meaning,
   message/view identity, timeouts, SQL/DAL, JSON compatibility, restart/rehydration, scheduler, and
   executor behavior remain unchanged;
9. name the exact approved runtime, test, documentation, and any separately gated SQL files;
10. provide selector-driven tests, security routing, SQL no-diff criteria, smoke, rollback, and
    explicit approval questions.

Stop after the first response. Implementation requires separate operator approval of the findings,
retention decision, outcome vocabulary, and exact file manifest.

## 8. Architecture And Contract Requirements

- Views own Discord presentation and interaction acknowledgement, not direct DAL audit writes.
- Services own the coherent persistence-plus-audit orchestration required by an action; DAL retains
  raw storage operations. Reuse an existing service only when ownership remains clear.
- Preserve current audit action names and exact detail shapes unless the audit proves a defect and
  the operator separately approves a compatibility change.
- Preserve current registration `@everyone` behavior and `AllowedMentions`: announcement is sent
  only under the existing `should_announce` decision and never added to edit/failure paths.
- An explicit outcome must describe what happened without turning expected missing-message
  recreation into failure or a caught edit failure into success. Logs must not add private message
  content or new identifiers.
- Confirmation-history policy must not silently discard data. Any bound needs a documented count,
  age/cardinality rule, when pruning occurs, and what historical visibility is lost or archived.
- Existing JSON must load without manual edits. Failed save/migration must not partially replace the
  last valid state. Do not introduce a state-format version or SQL dependency by implication.

## 9. Candidate File Manifest

### Review

- `ark/state/ark_state.py`
- `ark/confirmation_flow.py`
- `ark/embeds.py`
- `ark/registration_messages.py`
- `ark/registration_flow.py`
- `ark/ark_draft_service.py`
- `ark/confirm_publish_service.py`
- `ark/team_publish.py`
- `ark/dal/ark_dal.py`
- `ui/views/team_builder_views.py`
- `commands/ark_cmds.py`
- current state, registration, confirmation, draft, DAL, publish, view, and command tests

### Candidate Modify After Approval

- `ark/registration_messages.py`
- `ark/registration_flow.py`
- `ark/ark_draft_service.py` or one narrowly approved Ark team-builder service
- `ui/views/team_builder_views.py`
- `ark/state/ark_state.py` and `ark/confirmation_flow.py` only if retention is approved
- focused tests named below
- this pack, its starter, `README-DEV.md`, task-pack indexes, archived audit findings, and deferred
  register

### Candidate Create After Approval

- `ark/team_builder_service.py` only if the audit proves that extending `ark/ark_draft_service.py`
  would blur ownership
- `tests/test_ark_team_builder_service.py` if a new service is created
- no SQL file unless separately approved

## 10. Refactor And Batch Decisions

Scores use `(Impact + Frequency + Risk Reduction) - Effort`, with each factor rated 1-5.

| Candidate | Impact | Frequency | Risk reduction | Effort | Score | Initial disposition |
|---|---:|---:|---:|---:|---:|---|
| Explicit registration delivery outcomes | 3 | 3 | 3 | 2 | 7 | Strong `fix now` candidate after vocabulary approval |
| Team-builder audit-service extraction | 3 | 2 | 3 | 3 | 5 | Coherent `fix now` architecture candidate after sequence audit |
| Confirmation-update retention policy | 3 | 2 | 3 | 4 | 4 | Evidence/product-policy gated; `defer` is valid if cardinality or history needs do not justify mutation |

The items share Ark state/orchestration/observability context but are not all-or-nothing. Do not use
the batch label to force a persistence change unsupported by evidence.

## 11. Testing And Validation

Use `scripts/select_tests.py` plus risk-based selection. At minimum consider:

- `tests/test_ark_registration_message_move.py` for fresh send, same-channel edit, move, forced
  repost, missing-message recreation, ordinary failure, state-ref change, and mention behavior;
- `tests/test_ark_registration_messages.py` and `tests/test_ark_registration_flow.py` for callers,
  announcements, persistence/touch decisions, exact log outcomes, and compatibility;
- `tests/test_ark_confirmation_flow.py`, `tests/test_ark_confirmation_embed.py`,
  `tests/test_ark_state_json_migration.py`, and new focused retention tests only if policy changes;
- `tests/test_ark_draft_service.py`, `tests/test_ark_dal_team_workflow.py`,
  `tests/test_ark_team_publish_mention.py`, `tests/test_ark_confirm_publish_service.py`, and focused
  team-builder view/service tests for exact audit actions/details, no duplicates, error order,
  permission/ownership, acknowledgement, webhook fallback, and timeout behavior;
- unchanged command inventory/registration, import smoke, restart compatibility, operational log
  templates, and no unexpected mention regressions.

Required baseline gates:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
```

Before PR handoff, run focused pytest, `scripts/smoke_imports.py`, command-registration validation,
pre-commit, full pytest, and log-noise review, or record a precise non-applicable reason.

## 12. Smoke, Deployment, And Rollback

Production smoke is approval-gated and must use a naturally safe Ark match or test fixture. Observe
one existing registration edit and, only when naturally available, one move/recreate path; verify
the explicit outcome, unchanged message reference/state write, announcement choice, no duplicate,
no unexpected mention, and no Discord `50035`. Exercise team-builder auto-balance/reset/remove only
with an operator-approved non-production-impacting match and verify the existing ephemeral/webhook
behavior plus exactly one unchanged audit record. If retention changes, restart and confirm legacy
JSON loads, the chosen bound/archive rule is visible and deterministic, and no message reference is
lost. Do not manufacture a failure, delete a live message, or mutate production history solely for
smoke.

Rollback is a bot-PR revert and redeploy. A retention change additionally requires the approved
backup/restore or forward-compatible JSON rollback procedure. No SQL rollback should exist unless a
separately approved SQL design and PR were added.

## 13. Acceptance Criteria

- [ ] Audit evidence supports every `fix now`; unsupported retention mutation is deferred.
- [ ] No command, permission, audience, ownership, mention, message identity, or Ark domain behavior changes.
- [ ] The team-builder view no longer performs approved direct DAL audit orchestration, with no
      duplicate/missing audit and unchanged error/interaction order.
- [ ] Registration logs unambiguously distinguish successful edit/move/repost/recreate from failure.
- [ ] Existing caller and return behavior is preserved or migrated through an approved compatibility layer.
- [ ] Existing Ark JSON loads unchanged; any approved retention policy is explicit, recoverable, and tested.
- [ ] SQL remains unchanged or has separate approval, source-of-truth validation, and review evidence.
- [ ] Selected and full validation gates pass or unrelated failures are precisely documented.
- [ ] Bot Changes-only security review covers the final approved base..head with Deep off.
- [ ] Phase 2F, Phase 2G, and executor audits remain separately owned.

## 14. Required Delivery Output

Return: summary; exact file manifest; retention evidence and decision; outcome vocabulary; service
boundary; modified/new files; SQL changes or no-diff statement; preserved contracts; test and
security evidence; smoke and rollback; deferred items; PR links; and any operator-owned final
verification. Do not claim delivery, merge, or production verification before it occurs.

## 15. Follow-Up Roadmap

- Phase 2F: atomic `active_reminders` replacement with unchanged reminder identity, timing, mentions,
  and rehydration.
- Phase 2G: evidence/design-gated atomic Pre-KVK reserve/commit/release semantics.
- Separate tasks: Stats and KVK History once-only executor audits.

No deferred item is made ownerless by this preparation.
