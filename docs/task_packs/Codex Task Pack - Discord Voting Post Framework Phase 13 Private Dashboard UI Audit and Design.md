# Codex Task Pack - Discord Voting Post Framework Phase 13 Private Dashboard UI Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 13 Private Dashboard UI Audit and Design`
- Date: `2026-07-06`
- Owner/context: `Follow-up after Phase 11 dashboard-safe reporting runtime contract and Phase 12 survey draft/resume delivery`
- Task type: `audit | product scope | private dashboard UX | Discord interaction design | reporting contract review`
- One-pass approved: `approved after audit/scope confirmation`
- Status: `implemented locally; awaiting operator Discord smoke/promotion`

## 2. Objective

Audit and design the private admin/leadership dashboard UI over the Phase 11 dashboard-safe
reporting service contract.

Phase 11 delivered aggregate vote/survey reporting payloads that exclude Discord identity,
per-user rows, raw text answers, and choice details. Phase 12 then delivered survey draft/resume
while preserving draft exclusion from public results, private dashboard summaries, status totals,
and exports until final submit. Phase 13 should now decide the safest private UI surface for those
approved aggregate summaries without changing existing export profiles or exposing detailed
response data.

Start with audit/scope confirmation. Do not implement new commands, command reshaping, new SQL
objects, public dashboards, retention/redaction behavior changes, cross-survey workbook exports,
raw text/detail exposure, or Discord interaction runtime changes until the product scope,
permissions, privacy, UX direction, SQL/reporting posture, tests, smoke plan, deployment order,
rollback posture, and deferred boundaries are approved.

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
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 11 Private Dashboard Reporting Runtime Audit and Design.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 12 Survey Draft Resume Audit and Design.md`
- `docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 13 Private Dashboard UI Audit and Design.md`

## 4. Delivered Baseline

Phase 1 through Phase 12 are complete and smoke tested. The voting framework now supports:

- SQL-backed vote posts, one-choice voting, single-question multi-select voting, and SQL-backed
  multi-question surveys.
- Choice, text, detail, optional, fixed 1-5 rating, and complete ranking survey questions.
- Persisted survey response drafts/resume for surveys only, with automatic draft save, explicit
  save-and-exit, restart-safe resume, stale duplicate-panel protection, and final-submit gating.
- One ballot/response per Discord user with response changes when enabled.
- Scheduler reminders, automatic close, manual close, disabled controls after close, and
  restart-safe public openers.
- Guided vote creation and guided survey builder controls.
- PublicLive and HiddenUntilClose result visibility.
- Aggregate-only public survey results, including text counts, rating summaries, and ranking
  summaries.
- Private admin/leadership live status.
- Private closed-only vote totals, voter audit, survey totals, survey response-detail, and survey
  report-bundle CSV exports.
- Private admin/leadership aggregate dashboard-safe reporting contract for vote/survey summaries.
- Dashboard-safe exclusion of Discord identity, per-user rows, raw text answers, choice details,
  and unsubmitted draft answers.
- Spreadsheet-safe Discord IDs and CSV formula safety in existing private export profiles.
- Audit metadata that records counts/status rather than full answer payloads.

Phase 12 smoke and regression testing on 2026-07-06 confirmed persisted survey drafts/resume,
duplicate stale-session protection, orange saved-draft warning copy, draft exclusion from result
and export surfaces, and preserved regression behavior.

## 4A. Delivered Runtime Shape

After audit/scope approval, Phase 13 implemented the first private Discord dashboard UI slice:

- Added `/vote_admin dashboard` under the existing approved `/vote_admin` group.
- Kept the command admin/leadership-gated and ephemeral/private.
- Reused the Phase 11 `build_admin_leadership_dashboard_report()` aggregate contract.
- Added a Discord presentation adapter and private non-persistent dashboard view with filters,
  pagination, refresh, and close controls.
- Preserved the dashboard-safe boundary: no Discord identity, no per-user rows, no raw text
  answers, no choice detail text, no unsubmitted survey draft answers, and no public posting.
- Preserved HiddenUntilClose public privacy while allowing private admin/leadership aggregate
  visibility through the dashboard.
- Added focused presentation/view/command-registration tests and updated the canonical command
  reference.

No SQL objects, public dashboard, generated card, export format, retention/redaction behavior,
cross-survey workbook output, rating-scale extension, emoji/icon support, governor-aware reporting,
role-restricted voting, saved templates, or broad `/vote_admin` reshape were added.

## 5. Source Deferred Item

Phase 13 promotes the active private dashboard UI deferred item.

### Deferred Optimisation
- Area: `voting/reporting_service.py`, future private dashboard UI, approved dashboard surface
- Type: architecture
- Description: Phase 11 delivered private admin/leadership aggregate dashboard-safe reporting contracts, but it did not deliver the actual dashboard UI/runtime surface that admins and leadership need to view those summaries. Without an explicit follow-up, the UI delivery could be obscured by broader export/reporting backlog items.
- Suggested Fix: Prepare a dedicated private dashboard UI slice using the Phase 11 reporting service contract. Confirm whether the surface is a Discord command/view, internal web/dashboard surface, generated dashboard file, or another approved private UI; validate permissions, privacy, HiddenUntilClose live-admin semantics, refresh/loading states, filters/pagination, SQL/reporting performance needs, tests, smoke plan, deployment order, rollback posture, and Codex Security requirements. Keep public dashboard, raw text/detail exposure, per-user identity, cross-survey/workbook exports, and retention/redaction policy changes separate unless explicitly approved.
- Impact: high
- Risk: high
- Dependencies: Phase 11 private aggregate reporting contract delivered and smoke/regression tested on 2026-07-06; Phase 12 persisted survey draft/resume delivered and smoke/regression tested on 2026-07-06; operator approval for dashboard UI surface and timing; `k98-discord-command-feature` if implemented in Discord; SQL repo validation if new reporting objects are proposed; Codex Security review before runtime PR handoff.

## 6. Proposed Phase 13 Scope

### In Scope For Audit/Design

- Confirm the private dashboard UI surface:
  - existing `/vote_admin` group subcommand,
  - existing status/export flow extension,
  - private Discord view/panel,
  - generated private summary file,
  - internal/private web surface,
  - or another explicitly approved surface.
- Confirm whether a new grouped subcommand is acceptable, and whether any command-surface changes
  require updates to `canonical_command_reference.md` and command registration validation.
- Confirm admin/leadership permission boundaries and private/ephemeral delivery expectations.
- Confirm dashboard-safe data boundary:
  - aggregate vote/survey summaries only,
  - no Discord identity,
  - no per-user answer rows,
  - no raw text answers,
  - no choice detail text,
  - no unsubmitted draft answers,
  - no public posting.
- Confirm HiddenUntilClose behavior for private admin/leadership dashboard users versus public
  visibility.
- Confirm dashboard UX model:
  - overview versus detail pages,
  - vote versus survey tabs or filters,
  - open/closed status filters,
  - pagination,
  - refresh behavior,
  - loading/error states,
  - mobile Discord readability,
  - generated-card or embed/file fallback if a Discord UI is chosen.
- Confirm whether Phase 11 service payloads are sufficient or whether narrow service/presentation
  adapters are needed.
- Validate whether any SQL changes are needed; prefer no new SQL objects unless performance,
  direct reporting consumers, or stability justify them.
- Confirm dashboard treatment for answer types:
  - one-choice votes,
  - multi-select votes,
  - survey choice/text/detail questions,
  - optional questions,
  - fixed 1-5 rating questions,
  - complete ranking questions,
  - persisted drafts, which must remain excluded.
- Confirm export/reporting boundaries:
  - existing private export profiles remain the approved detailed-review surfaces,
  - dashboard UI must not replace response-detail exports,
  - no cross-survey workbook export in this slice unless separately approved.
- Define tests, smoke plan, Codex Security requirement, deployment order, rollback posture, and
  promotion gates.
- Update deferred optimisation status so rating-scale extensions, emoji/icon support,
  `/vote_admin` reshaping, cross-survey/workbook exports, retention/redaction policy changes,
  optional SQL-native combined reporting, and definitely-not-required role/governor/template/public
  detail work remain visible and separate.

### Candidate Implementation Scope If Approved Later

Implementation is not pre-approved. Possible later runtime work may include:

- A private admin/leadership dashboard command or panel using the existing reporting service.
- Presentation adapters for Phase 11 dashboard-safe payloads.
- Paginated embeds or generated dashboard cards/files.
- Refresh controls and filter controls that preserve private delivery.
- Focused tests for permission boundaries, HiddenUntilClose private/admin behavior, draft
  exclusion, answer-type representation, pagination, and response-size limits.
- Command reference and command-registration updates if a grouped subcommand is approved.

## 7. Out Of Scope Unless Separately Approved

- Public dashboard implementation or public website.
- Raw text/detail dashboard display.
- Per-user response rows or voter-level dashboard display.
- Public raw text/detail export posting.
- Public voter-level/detail export posting.
- Cross-survey workbook exports.
- Retention/redaction policy changes.
- Rating-scale extensions or custom rating scales.
- Per-option emoji/icon support.
- Broad `/vote_admin` reshaping beyond a narrowly approved dashboard surface.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- SQL-native combined vote/survey reporting views/procedures unless the audit proves they are
  needed and the operator approves them.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing submitted survey or draft/resume behavior except as approved for dashboard
  exclusion/display compatibility.

## 8. Required Separate Follow-Up Slices

- Rating Scale Extensions.
- Emoji/Icon Support.
- `/vote_admin` Reshaping.
- Cross-survey/workbook export redesign.
- Retention/redaction policy changes.
- Optional SQL-native combined reporting views/procedures if reporting consumers or performance
  needs justify them.

Definitely not required unless a later operator decision reverses the status:

- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public voter-level/detail export posting.

## 9. Validation Expectations

For the audit/docs portion:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

If runtime implementation is later approved, select focused tests after the design is approved.
Likely areas include reporting service, reporting models, survey DAL/reporting DAL if adapters are
added, vote admin command tests, dashboard view tests, permission-boundary tests, HiddenUntilClose
privacy tests, draft-exclusion tests, smoke imports, command registration, full pytest, SQL
validation if SQL changes are proposed, and Codex Security review.

## 10. Stop Point

Stop after the audit/scope packet unless implementation is explicitly approved.
