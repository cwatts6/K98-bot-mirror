# Codex Task Pack - Discord Voting Post Framework Phase 21 Private Engagement Graph Assessment Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 21 Private Engagement Graph Assessment Audit and Design`
- Date: `2026-07-08`
- Owner/context: `Follow-up after Phase 20 delivered the private per-user engagement CSV export`
- Task type: `audit | private leadership reporting product scope | graph value assessment | privacy review | file/artifact handling review`
- One-pass approved: `no`
- Status: `archived; audit closed as not required on 2026-07-08 with no runtime graph implementation and no active deferred item`

## 2. Objective

Audit whether the Phase 20 CSV export data justifies adding one or two private engagement graphs.

Phase 20 delivered `/vote_admin engagement`, a private CSV export with all eligible users sorted
highest engagement first, role names, eligible opportunities, vote/survey split counts,
participation count, missed count, engagement rate, and last participation date. Operator smoke
confirmed Export CSV is done, data is as expected, controls work well, role filters behave as
planned, and regression tests are successful.

Phase 21 must decide whether graph output adds real value or whether CSV remains sufficient. Do not
implement graph/image generation, dashboard pages, command options, SQL/DAL changes, file cleanup
behavior, public output, retention/redaction behavior, or SQL-native combined reporting until the
operator approves product scope, privacy boundaries, data contract, compatibility, documentation,
tests, rollout, rollback, and communication plan.

## 2A. Completion Update

Phase 21 is audit-closed. After reviewing the Phase 20 CSV output and operator workflow, the
operator confirmed there is no current requirement for a generated engagement graph. The CSV export
already provides the full private data set, and leadership can create ad hoc graphs from the export
when needed. If a graph proves useful later, it should return as a new requirement with concrete
semantics, audience, privacy, artifact-handling, tests, rollout, rollback, and communication scope.

No runtime implementation is approved or required from this phase:

- no graph/image generation;
- no `/vote_admin engagement` control changes;
- no `/vote_admin dashboard` changes;
- no command options, aliases, or new commands;
- no SQL/DAL changes;
- no CSV schema changes;
- no workbook output;
- no public output;
- no file cleanup, retention, or redaction behavior changes;
- no SQL-native combined reporting.

The active deferred optimisation item for future private engagement graphs has been removed rather
than left in the backlog.

## 3. Required Reading

Read first:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/Discord Voting Post Framework - Programme Pack.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 20 Per-User Engagement Export List and Graph Audit and Design.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 21 Private Engagement Graph Assessment Audit and Design.md`

Use these skills as applicable:

- `k98-architecture-scope`
- `k98-sql-validation` if the audit proposes SQL-facing reporting changes, SQL-native graph data
  contracts, new indexes, or new DAL reads beyond Phase 20 contracts
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review` before runtime PR handoff if implementation is approved
- `k98-promotion-check` before production promotion if implementation is approved
- `codex-security` security review before runtime PR handoff if implementation touches
  permissions, Discord interactions, SQL/data access, generated graph files/images, private data,
  file handling, user-controlled input, or restart-sensitive flows

## 4. Delivered Baseline

Phase 1 through Phase 20 are complete and smoke tested or audit-closed. The voting framework now
supports:

- SQL-backed one-choice votes, single-question multi-select votes, and multi-question surveys.
- Choice, text, detail, optional, configurable rating, and ranking survey questions.
- Persisted survey drafts/resume for surveys only, with drafts excluded from public/private result
  and export/reporting surfaces until final submit.
- PublicLive and HiddenUntilClose result visibility.
- Private admin/leadership vote and survey status, exports, report bundles, and `/vote_admin
  dashboard`.
- Private leadership engagement summary reporting delivered in Phase 19.
- Private per-user engagement CSV export delivered in Phase 20 under `/vote_admin engagement`.

Phase 20 intentionally did not add graphs, workbooks, paged Discord lists, public reporting, raw
answer/detail reporting, retention/redaction changes, SQL-native combined reporting, governor-linked
reporting, role-restricted voting, templates, or per-rating comments.

## 5. Closed Source Deferred Item

### Deferred Optimisation
- Area: `voting/engagement_export_service.py`, `/vote_admin engagement`, future private engagement graphs
- Type: architecture
- Description: Phase 20 delivered the private per-user engagement CSV export and intentionally removed paged Discord lists from scope because they are hard to manage and add little value for large user counts. Operator smoke confirmed the CSV data, controls, and role filters are working as expected. Graph output remains deferred until leadership reviews the CSV data and identifies one or two specific visual questions worth rendering.
- Suggested Fix: Promoted into this Phase 21 audit/design task pack. Confirm whether a graph should be built at all; if yes, decide whether it should be a distribution summary, lowest-participation capped chart, combined vote/survey participation chart, separate vote/survey series, or survey-only view. Define user-count limits, privacy copy, artifact generation/cleanup, tests, rollout, rollback, and Codex Security review before implementation.
- Impact: medium
- Risk: medium
- Dependencies: Phase 20 private CSV export delivered and smoke/regression tested; active Phase 21 audit/design approval; concrete leadership graph question; graph/image artifact privacy and file-handling approval.

Closeout: the operator confirmed there is no current graph requirement. This item was removed from
`docs/reference/deferred_optimisations.md` rather than kept as active deferred work.

## 6. Candidate Phase 21 Scope Confirmed

Phase 21 selected the `no graph output because CSV is sufficient` outcome.

### Audit Findings

- The Phase 20 CSV export remains the correct ownership surface for private per-user engagement
  detail.
- No generated graph should be built without a concrete leadership requirement.
- Graphs can be created externally from the CSV if leadership needs ad hoc visual analysis.
- If a recurring graph proves useful, it should be defined in a fresh task pack rather than kept as
  an open-ended deferred item.
- `/vote_admin dashboard` should remain focused on private vote/survey inspection.
- `/vote_admin engagement` should remain the private select-driven CSV export flow.
- Public engagement graphs and public voter-level/detail output remain out of scope.

### Explicitly Out Of Scope Unless Separately Approved

- Public engagement graphs, public dashboards, or public voter-level/detail output.
- Paged or scrollable Discord per-user lists.
- Workbook output.
- Phase 20 CSV schema changes.
- Raw text/detail answer reporting.
- Per-answer response detail.
- Retention/redaction policy changes.
- SQL-native combined vote/survey reporting views/procedures unless explicitly approved.
- New voting or survey answer types.
- `/vote_admin` command aliases, new top-level commands, or help panels.
- Changing submitted vote or survey response semantics.
- Changing Phase 16 survey update locks.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Per-rating comments.
- Generated-card custom emoji asset fetching or animation.

## 7. Closed Design Decision

No graph/image output is required now. Future graph work should begin only after leadership can name
the specific graph question and confirm that the CSV-derived ad hoc approach is not sufficient.

## 8. Recommended Starting Posture

Final design posture:

- Keep Phase 20 CSV export as the deeper private engagement data path.
- Close the private engagement graph deferred item as not required now.
- Do not add graph/image generation, graph files, extra controls, SQL-native graph contracts, or
  dashboard graph placement.
- If future graph requirements emerge, start with a new audit/design slice and require Codex
  Security review before runtime handoff because generated artifacts, Discord interactions, private
  data, file handling, and SQL/data access would be touched.

## 9. Test Strategy

For this audit/docs-only closeout, run:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

If graph implementation is approved in a future fresh task, add or update:

- graph data-shaping tests for selected graph semantics, limits, sorting, and zero-data behavior;
- graph/image generation tests with deterministic dimensions and labels;
- private view/command tests for graph delivery and oversized/error handling;
- tests proving raw text/detail answers and per-answer detail remain absent;
- command registration tests if any `/vote_admin` subcommand or control changes;
- Codex Security diff scan before runtime PR handoff.

## 10. Rollout / Rollback / Smoke Direction

Phase 21 has no runtime rollout:

- no bot deployment required;
- no SQL deployment required;
- no rollback required beyond reverting documentation if needed;
- no smoke test required beyond preserving the already smoke-tested Phase 20 CSV export.

If bot-side graph implementation is approved with no SQL migration:

- deploy bot-only after tests and Codex Security review;
- rollback by reverting the bot PR;
- no database rollback needed;
- smoke with an admin/leadership account: open `/vote_admin engagement`, select window and role
  filter, generate the graph, verify private delivery, verify counts against the CSV/top-level
  engagement summary, confirm graph labels are readable, confirm raw answers are absent, and
  confirm existing CSV export still works.

If SQL-native graph/reporting data is later approved:

- deploy SQL objects first;
- validate SQL deployment against a representative database;
- deploy bot after SQL validation;
- rollback by disabling bot usage first, then leaving additive SQL objects in place unless a
  separate destructive cleanup is approved.
