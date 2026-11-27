# Codex Chat Starter - Discord Voting Post Framework Phase 21 Private Engagement Graph Assessment Audit and Design

Archived historical starter for the Phase 21 audit/design slice. Phase 21 was audit-closed on
2026-07-08 with no graph requirement and no runtime implementation.

```text
Codex, start Discord Voting Post Framework Phase 21: Private Engagement Graph Assessment Audit and
Design.

Phase 1 through Phase 20 are complete or audit-closed. Phase 20 delivered the private per-user
engagement CSV export under /vote_admin engagement. Smoke testing confirmed Export CSV is done,
data is as expected, controls work well, role filters behave as planned, and regression tests are
successful.

Phase 21 objective:
Audit whether the Phase 20 CSV data justifies adding one or two private engagement graphs.
Candidate graph questions include participation distribution summary, lowest-participation capped
chart, combined vote/survey participation by user, separate vote/survey series, or survey-only
participation. The audit may also conclude that CSV export is enough and no graph should be built
now.

Start with audit/scope confirmation. Do not implement graph/image generation, dashboard pages,
command options, SQL/DAL changes, file cleanup behavior, public output, retention/redaction
behavior, or SQL-native combined reporting until I approve the graph value, product scope, privacy
model, data contract, compatibility, documentation, tests, rollout, rollback, and operator
communication plan.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/reference/K98 Bot - Project Engineering Standards.md
- docs/reference/K98 Bot - Coding Execution Guidelines.md
- docs/reference/K98 Bot - Testing Standards.md
- docs/reference/K98 Bot - Skills & Refactor Triggers.md
- docs/reference/K98 Bot - Deferred Optimisation Framework.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md
- docs/task_packs/Discord Voting Post Framework - Programme Pack.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 20 Per-User Engagement Export List and Graph Audit and Design.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 21 Private Engagement Graph Assessment Audit and Design.md

Use these skills as applicable:
- k98-architecture-scope
- k98-sql-validation if the audit proposes SQL-facing reporting changes, SQL-native graph data
  contracts, new indexes, or new DAL reads beyond Phase 20 contracts
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before runtime PR handoff if implementation is approved
- k98-promotion-check before production promotion if implementation is approved
- codex-security security review before runtime PR handoff if implementation touches permissions,
  Discord interactions, SQL/data access, generated graph files/images, private data, file handling,
  user-controlled input, or restart-sensitive flows

Candidate Phase 21 audit scope to confirm:
- Confirm whether graph output is needed at all after reviewing Phase 20 CSV data.
- Confirm graph semantics:
  - participation distribution summary
  - lowest-participation capped chart
  - combined vote/survey participation by user
  - separate vote and survey participation series
  - survey-only participation
  - another operator-approved graph question
- Confirm graph ownership:
  - private attachment generated from /vote_admin engagement
  - private summary embed plus attachment
  - no graph output if CSV is sufficient
  - avoid /vote_admin dashboard unless the audit proves the graph belongs there
- Confirm graph input contract:
  - reuse Phase 20 engagement reporting/export contract if possible
  - no CSV schema changes unless separately approved
  - no SQL-native combined reporting unless performance or consumer needs justify it
  - no raw text/detail answers or per-answer detail
- Confirm graph limits:
  - user-count cap for named-user charts
  - fallback to distribution summary for large audiences
  - label truncation and privacy wording
  - deterministic ordering and tie-breaks
  - zero-data or all-zero participation behavior
- Confirm generated artifact posture:
  - private admin/leadership delivery only
  - no public graph
  - Discord upload size limits
  - temporary file or in-memory image generation
  - cleanup behavior if files are written
  - graceful timeout/error handling
- Confirm tests, Codex Security requirement, deployment order, rollback posture, smoke checks, and
  deferred follow-up work.

Do not include in Phase 21 unless separately approved:
- Public engagement graphs, public dashboards, or public voter-level/detail output.
- Paged or scrollable Discord per-user lists.
- Workbook output.
- Phase 20 CSV schema changes.
- Raw text/detail answer reporting.
- Per-answer response detail.
- Retention/redaction policy changes.
- SQL-native combined vote/survey reporting views/procedures.
- New voting or survey answer types.
- /vote_admin command aliases, new top-level commands, or help panels.
- Changing submitted vote or survey response semantics.
- Changing Phase 16 survey update locks.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Per-rating comments.
- Generated-card custom emoji asset fetching or animation.

Expected validation for the audit/docs portion:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py

Stop after the audit/scope packet unless I explicitly approve implementation.
```
