# Codex Task Pack - Discord Voting Post Framework Phase 16 Survey Authoring Edit Controls Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 16 Survey Authoring Edit Controls Audit and Design`
- Date: `2026-07-07`
- Owner/context: `Follow-up after Phase 15 emoji/icon support delivery and smoke testing`
- Task type: `audit | product scope | Discord interaction UX | survey builder polish | SQL/reporting compatibility review`
- One-pass approved: `no`
- Status: `complete, review-hardened, smoke/regression tested, and archived`

## 2. Objective

Audit and design guided survey authoring edit controls so admins can correct already-added draft
survey questions before publish, especially option emoji/icon metadata added in Phase 15.

Phase 15 smoke testing confirmed vote and survey emoji behavior works well, including Unicode emoji,
custom Discord emoji, animated custom emoji in Discord/status/dashboard, and generated-card custom
emoji text fallback. The same smoke pass exposed the remaining authoring gap: survey creation is
append-only once a question is added. If an admin forgets an emoji on an answer in question 1, they
must restart the survey build instead of editing the draft question/options.

This phase should confirm the simplest safe UX that makes survey creation easier for admins while
preserving existing survey semantics. Start with audit/scope confirmation. Do not implement builder
controls, post-publish update commands, SQL/DAL changes, player controls, export/report/dashboard
shape changes, or broad `/vote_admin` reshaping until the product scope, privacy model, SQL posture,
compatibility plan, permissions, tests, smoke plan, deployment order, rollback posture, and deferred
boundaries are approved.

Delivery closeout on 2026-07-07 confirmed the approved Phase 16 implementation is complete:

- Guided survey builder review/edit controls are delivered for already-added draft questions.
- Draft admins can edit question text, required/optional state, option labels, and option emoji
  metadata where those fields exist.
- Draft admins can delete and reorder questions before publish.
- `/vote_admin survey_update` is delivered for open published surveys, covering title,
  description, close time, reminder offsets, reminder `@everyone`, close `@everyone`, option
  icons, response changes, and result visibility.
- Post-publish option icons, response changes, and result visibility are allowed only while the
  survey is open and before submitted responses exist.
- Survey update locks correctly after a submitted response exists, and closed surveys are locked.
- Close-time updates rebuild pending reminders and audit the changed reminder schedule accurately.
- Submitted survey response semantics, option IDs, export/report/dashboard shapes,
  PublicLive/HiddenUntilClose behavior, draft/resume privacy boundaries, and restart-safe public
  openers were preserved.
- No SQL migration was required beyond the existing Phase 15 nullable emoji metadata.
- Broad `/vote_admin` reshaping, cross-survey/workbook exports, retention/redaction changes, and
  optional SQL-native combined reporting remain separate follow-up slices.

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
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 15 Emoji Icon Support and Visual Polish Audit and Design.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 16 Survey Authoring Edit Controls Audit and Design.md`

## 4. Delivered Baseline

Phase 1 through Phase 15 are complete and smoke tested. The voting framework supports:

- SQL-backed one-choice votes, single-question multi-select votes, and SQL-backed multi-question
  surveys.
- Choice, text, detail, optional, configurable rating, and complete ranking survey questions.
- Persisted survey drafts/resume for respondents, with unsubmitted drafts excluded from public
  results, private status, exports, report bundles, and dashboards.
- PublicLive and HiddenUntilClose result visibility.
- Private admin/leadership status, export, report bundle, and `/vote_admin dashboard` surfaces.
- Phase 15 option emoji metadata for vote and survey options, Unicode/custom Discord emoji display,
  guided option-polish controls, animated custom emoji display in Discord/status/dashboard, and
  generated-card custom emoji text fallback.

Phase 15 intentionally did not add emoji columns to exports/report bundles and did not redesign
survey authoring beyond option-polish entry.

## 5. Source Deferred Item

### Deferred Optimisation
- Area: `ui/views/survey_post_view.py`, `commands/vote_admin_cmds.py`, `voting/survey_service.py`, `voting/survey_dal.py`
- Type: consistency
- Description: Phase 15 smoke testing confirmed vote and survey option emoji display works, but exposed a survey authoring gap: survey creation is append-only once a question is added, and there is no `/vote_admin` survey update path for option emoji/icon metadata. If an admin forgets an emoji on an answer in question 1, they must restart the survey build instead of editing the draft question/options before publish or correcting approved display metadata after publish.
- Suggested Fix: Promoted into this Phase 16 audit/design task pack. Scope guided survey builder review/edit controls for previously added draft questions and their option emoji metadata, plus a narrowly permissioned survey option-icon update path for open surveys if approved. Preserve existing survey answer semantics, draft/submit privacy boundaries, restart-safe public openers, and private reporting/export contracts. Keep this separate from broad `/vote_admin` reshaping.
- Impact: medium
- Risk: medium
- Dependencies: Phase 15 option emoji metadata and builder controls are delivered and smoke tested; operator decision on whether post-publish survey option icon edits are allowed only while open, only before responses, or never after publish.

## 6. Candidate Phase 16 Scope To Confirm

### In Scope For Audit/Design

- Guided survey builder review controls that show already-added draft questions before publish.
- Guided edit controls for already-added draft question text, required/optional flag, and option
  labels/emoji metadata where safe.
- Option emoji/icon correction for draft single-choice, multi-select, and ranking questions.
- Whether rating question labels/scales can be edited before publish, and which changes are too
  semantically risky.
- Whether text/detail questions need prompt/required-flag edit only, or should remain add/remove
  only for the first slice.
- A simple admin UX that avoids compact syntax and keeps creation easy.
- Whether an explicit `Review survey` step should appear before publish.
- Whether deleting/reordering draft questions is required now or should remain a later slice.
- Whether a narrow post-publish survey option-icon update path is allowed for open surveys, and if
  so whether it is blocked after responses exist or only after close.
- SQL posture: prefer no new schema if existing Phase 15 option emoji metadata is sufficient; if
  update audit or concurrency needs require persistence changes, validate against
  `C:\K98-bot-SQL-Server` first.
- Restart safety expectations for unpublished builder state versus SQL-backed published surveys.
- PublicLive and HiddenUntilClose behavior after metadata-only icon updates.
- Private status, export, report bundle, and dashboard representation after metadata-only changes.
- Tests, smoke screenshots, Codex Security requirement, deployment order, rollback posture, and
  deferred follow-up work.

### Candidate Implementation Scope If Approved Later

- Add private guided builder review/edit controls for draft survey questions before publish.
- Add edit flows for option emoji metadata and other approved draft-safe fields.
- Add a narrow admin-only post-publish survey option-icon update path if approved.
- Preserve option IDs and answer semantics; do not reinterpret existing responses.
- Update services and DAL only where persistence or published-survey updates require it.
- Add focused tests for builder state transitions, validation, option metadata updates, restart-safe
  public opener compatibility, dashboard/status presentation, and command registration if commands
  change.

## 7. Out Of Scope Unless Separately Approved

- Broad `/vote_admin` reshaping.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing submitted survey response semantics.
- Post-publish question type changes, option deletes, option reordering, or label changes that
  would reinterpret existing responses.
- Cross-survey/workbook export redesign.
- Retention/redaction policy changes.
- SQL-native combined vote/survey reporting views/procedures.
- Public dashboards, public raw text/detail display, or public voter-level/detail exports.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Per-rating comments.
- Generated-card custom emoji asset fetching or animation.

## 8. Required Separate Follow-Up Slices

- `/vote_admin` Reshaping.
- Cross-survey/workbook export redesign.
- Retention/redaction policy changes.
- Optional SQL-native combined reporting views/procedures if reporting consumers or performance
  needs justify them.

Definitely not required unless a later operator decision reverses the status:

- Per-rating comments.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public voter-level/detail export posting.

## 8A. Delivery Validation And Smoke Evidence

Delivered through:

- Mirror PR: `cwatts6/K98-bot-mirror#211`
- Production PR: `cwatts6/K98-bot#518`
- SQL PR: `not required`
- Bot smoke test: `2026-07-07`

Automated validation included:

- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- focused survey admin update/view/DAL/post-view tests
- full pytest during implementation: `2379 passed, 2 skipped`
- pre-commit on touched files
- Codex Security diff scan with zero findings before the app report-publish race

Review hardening included the audit-row fix where close-time changes that rebuild pending
reminders now record `reminders: true` in `DetailsJson`.

Operator smoke/regression testing confirmed:

- Pre-publish review, edit, delete, and reorder all succeeded.
- Post-publish updates all succeeded.
- Survey update locks after a response is recorded.
- Survey updates are locked after close.
- Existing regression tests completed.

## 9. Codex Skills To Use

- `k98-architecture-scope`
- `k98-discord-command-feature` if Discord builder/player/dashboard/status/export controls are approved after audit
- `k98-sql-validation` if SQL option metadata, audit rows, constraints, DAL, or query-shape changes are proposed
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review` before runtime PR handoff if implementation is approved
- `k98-promotion-check` before production promotion if implementation is approved
- `codex-security` security review before runtime PR handoff if implementation touches permissions,
  Discord interactions, SQL/data access, generated reports/exports, private data, user-controlled
  text/emoji parsing, or restart-sensitive flows

## 10. Validation Expectations

For audit/docs-only work:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

If implementation is later approved, select focused tests after reading the current code and
`scripts/select_tests.py` output. Expected areas include:

- survey builder view tests
- survey service validation tests
- survey DAL metadata update tests if SQL-backed updates are approved
- dashboard/status presentation tests
- command registration validation if commands change
- smoke imports and restart-safe opener checks
- Codex Security diff scan before runtime PR handoff

## 11. Audit Packet Acceptance Criteria

The audit/scope packet is ready when it clearly answers:

- Which draft survey fields can be edited before publish.
- Whether draft question delete/reorder belongs in Phase 16 or a later slice.
- Whether post-publish survey option-icon updates are allowed, and under what state/response
  restrictions.
- Whether SQL schema changes are required or Phase 15 metadata is sufficient.
- How the UX stays simple for admins.
- How response semantics, privacy boundaries, exports/reports/dashboard summaries, and restart
  behavior are preserved.
- What tests, smoke checks, deployment order, rollback posture, and security review are required.

Stop after the audit/scope packet unless the operator explicitly approves implementation.
