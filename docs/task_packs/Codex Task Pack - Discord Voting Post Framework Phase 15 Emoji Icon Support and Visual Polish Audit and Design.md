# Codex Task Pack - Discord Voting Post Framework Phase 15 Emoji Icon Support and Visual Polish Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 15 Emoji Icon Support and Visual Polish Audit and Design`
- Date: `2026-07-07`
- Owner/context: `Follow-up after Phase 14 rating scale extensions delivery and smoke testing`
- Task type: `audit | product scope | Discord interaction UX | visual output polish | SQL/reporting compatibility review`
- One-pass approved: `no`
- Status: `active next voting slice; audit/scope only until architecture, SQL/reporting, privacy, permissions, and UX direction are approved`

## 2. Objective

Audit and design per-option emoji/icon support for the delivered voting and survey framework,
alongside a narrow visual-readability review for long labels and dense aggregate summaries observed
during Phase 14 smoke testing.

The goal is to decide whether emoji/icons should apply to one-choice votes, multi-select votes,
survey choice options, ranking options, generated public cards, private status/export/report
surfaces, and `/vote_admin dashboard`, without changing existing vote/survey semantics or exposing
new private data.

Phase 15 smoke testing later confirmed Discord button/select emoji rendering works for Unicode and
custom Discord emoji. Generated PNG cards intentionally fall back to custom emoji text such as
`:alert:` because the renderer does not fetch or animate Discord custom emoji assets. Smoke testing
also exposed a survey authoring gap: after adding question 1 in the guided survey builder, an admin
cannot edit that draft question's option emoji metadata, and there is no narrow survey option-icon
update path after publish. Capture this as Phase 15 follow-up scope rather than broad
`/vote_admin` reshaping.

Start with audit/scope confirmation. Do not implement SQL migrations, option metadata storage,
builder controls, player controls, renderer changes, export/report/dashboard shape changes, public
rendering changes, command changes, or broad card redesign until the product scope, privacy model,
SQL posture, compatibility plan, tests, smoke plan, deployment order, rollback posture, and
deferred boundaries are approved.

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
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 13 Private Dashboard UI Audit and Design.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 14 Rating Scale Extensions Audit and Design.md`
- `docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 15 Emoji Icon Support and Visual Polish Audit and Design.md`

## 4. Delivered Baseline

Phase 1 through Phase 14 are complete and smoke tested. The voting framework supports:

- SQL-backed one-choice votes, single-question multi-select votes, and SQL-backed multi-question
  surveys.
- Choice, text, detail, optional, fixed/custom rating, and complete ranking survey questions.
- Configurable rating scales up to 1-10, custom min/max scales, scale endpoint labels, and named
  rating choices.
- Persisted survey drafts/resume for surveys only, with draft answers excluded from public results,
  private dashboard summaries, status totals, exports, and report bundles until submit.
- PublicLive and HiddenUntilClose result visibility.
- Private admin/leadership live status, closed-only exports, survey report bundles, private
  dashboard-safe aggregate reporting contracts, and `/vote_admin dashboard`.
- Aggregate-only public results and dashboard-safe private summaries with no Discord identity,
  per-user rows, raw text/detail answers, or unsubmitted drafts.

Phase 14 smoke and regression testing on 2026-07-07 confirmed fixed 1-5 ratings, 1-10 ratings,
custom min/max scales, scale endpoint labels, named rating choices, save/draft/resume,
`/vote_admin dashboard`, export, repost, status, and other listed regression paths.

## 5. Source Deferred Item

Phase 15 promotes the active emoji/icon and visual polish deferred item.

### Deferred Optimisation
- Area: `voting/discord_presentation.py`, `voting/render_service.py`, `ui/views/vote_post_view.py`, `ui/views/survey_post_view.py`, `voting/survey_render_service.py`, SQL repo option metadata
- Type: consistency
- Description: Per-option emoji/icon support is approved for future voting framework scope because it can make public votes and surveys more readable and engaging. Current vote and survey options have labels and limited button styling but no emoji/icon metadata. Phase 14 smoke testing also showed that long named rating labels and dense distributions remain readable but can crowd generated cards and dashboard summaries, so the next visual polish slice should audit label-density/readability alongside emoji/icon support rather than leaving that observation loose.
- Suggested Fix: Promoted into the prepared Phase 15 Emoji/Icon Support and Visual Polish audit/design task pack. Scope whether emoji/icons apply to one-choice votes, multi-select votes, survey choice options, ranking options, generated cards, Discord buttons/selects, private status, exports, report bundles, and dashboard summaries. Validate Unicode/custom emoji input, SQL metadata needs, glyph/font fallback, output escaping, privacy boundaries, smoke screenshots, and long-label card/dashboard readability before implementation.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5 hidden-until-close, Phase 6 MultiSelect, Phase 7 choice-only surveys, Phase 9C ranking questions, Phase 13 dashboard UI, and Phase 14 rating scale extensions are delivered and smoke tested; renderer visual QA with representative emoji/custom emoji and long label cases; operator approval for exact surfaces before runtime changes.

## 6. Candidate Phase 15 Scope To Confirm

### In Scope For Audit/Design

- Confirm whether emoji/icon support applies to:
  - one-choice vote options,
  - multi-select vote options,
  - survey single-choice and multi-select options,
  - ranking survey options,
  - public cards,
  - Discord buttons/selects,
  - private status/export/report/dashboard summaries.
- Confirm whether rating labels receive no emoji support, or only benefit from visual density/card
  readability polish.
- Confirm whether emoji metadata is Unicode-only, custom Discord emoji, or both.
- Validate input safety, label-length interaction, custom emoji ID handling, fallback display when
  a custom emoji is unavailable, and spreadsheet/export representation.
- Validate current SQL option tables and whether additive metadata columns/tables are required.
- Confirm builder UX for safe emoji/icon selection without unsafe free-form values.
- Confirm whether guided survey builder review/edit controls should allow admins to correct option
  emoji/icon metadata on already-added draft questions before publish.
- Confirm whether a narrow post-publish survey option-icon update path is allowed for open surveys,
  and whether it should be blocked after responses exist or after close.
- Confirm player UX for buttons/select menus and restart-safe public openers.
- Confirm generated-card behavior, font/glyph fallback, text wrapping, truncation, and visual QA
  for dense labels and named rating distributions.
- Confirm PublicLive and HiddenUntilClose aggregate behavior remains unchanged.
- Confirm private status, export, report bundle, and dashboard representation remains
  aggregate-only and private-safe.
- Confirm tests, smoke screenshots, Codex Security requirement, deployment order, rollback
  posture, and deferred follow-up work.

### Candidate Implementation Scope If Approved Later

- Add additive option emoji/icon metadata for the approved surfaces.
- Update guided vote/survey builder controls for approved emoji/icon entry or selection.
- Add guided survey builder edit/review controls for previously added draft questions and their
  option emoji/icon metadata if approved.
- Add a narrow survey option-icon update path for open surveys if approved, preserving answer
  semantics and existing privacy/reporting boundaries.
- Update player-facing buttons/select labels while preserving existing behavior and limits.
- Update public card rendering with glyph fallback and mobile/desktop readability checks.
- Update private status/export/report/dashboard representation where approved.
- Add focused tests for validation, DAL/service mapping, view rendering, exports/reporting, card
  output shape, and command registration if command metadata changes.

## 7. Out Of Scope Unless Separately Approved

- Broad `/vote_admin` reshaping.
- Cross-survey/workbook export redesign.
- Retention/redaction policy changes.
- SQL-native combined vote/survey reporting views/procedures.
- Public dashboards, public raw text/detail display, or public voter-level/detail exports.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Per-rating comments.
- Changing existing one-choice, multi-select, choice/text/detail/optional/rating/ranking behavior
  except as narrowly approved for emoji/icon or visual-readability compatibility.

## 8. Required Separate Follow-Up Slices

- Survey builder question/option edit and survey option-icon update polish.
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

## 9. Candidate Deferred Scoring

| Candidate | Impact | Frequency | Risk reduction | Effort | Score | Decision |
|---|---:|---:|---:|---:|---:|---|
| Emoji/icon support for option-bearing voting surfaces | 3 | 4 | 2 | 3 | 6 | Good visual-polish batch candidate after rating-scale delivery. |
| Survey builder edit/update path for missed option emoji | 3 | 3 | 3 | 3 | 6 | Add to Phase 15 follow-up scope; keep separate from broad command reshaping. |
| Long label/card-density readability polish | 3 | 3 | 3 | 2 | 7 | Include in Phase 15 audit so Phase 14 smoke observation is not lost. |
| `/vote_admin` reshaping | 3 | 4 | 3 | 4 | 6 | Keep separate because it changes command surface and rollout communication. |
| Cross-survey/workbook exports | 4 | 2 | 3 | 4 | 5 | Keep separate until reporting consumers are concrete. |
| Retention/redaction policy | 4 | 2 | 4 | 4 | 6 | Keep separate because it is privacy/destructive-policy work. |
| SQL-native combined reporting | 3 | 2 | 3 | 4 | 4 | Keep optional until performance or consumer evidence exists. |

## 10. Codex Skills To Use

| Skill | Use |
|---|---|
| `k98-architecture-scope` | Required for product/architecture boundary decisions before coding. |
| `k98-discord-command-feature` | Required if builder/player/dashboard/status/export Discord controls are approved after audit. |
| `k98-sql-validation` | Required if SQL option metadata, constraints, DAL, or reporting/query-shape changes are proposed. |
| `k98-test-selection` | Required to select focused service/DAL/view/render/export/report/dashboard tests. |
| `k98-deferred-optimisation-capture` | Required to keep command reshaping, export redesign, retention, and optional SQL reporting separate. |
| `k98-pr-review` | Required before runtime PR handoff if implementation is approved. |
| `k98-promotion-check` | Required before production promotion if implementation is approved. |
| `codex-security:security-diff-scan` | Required before runtime PR handoff if implementation touches Discord interactions, SQL/data access, exports/reports, private data, user-controlled text, emoji parsing, or restart-sensitive flows. |

## 11. SQL And Reporting Questions To Validate

- Current `dbo.VotePostOptions` option metadata shape.
- Current `dbo.SurveyQuestionOptions` option metadata shape.
- Whether ranking options can reuse survey option metadata without changing ranking semantics.
- Whether emoji/icon metadata belongs on option rows or in a dedicated companion table.
- Whether custom Discord emoji IDs require guild-scoped storage and validation.
- How exports/report bundles/dashboard summaries should represent emoji/icon metadata.
- Whether existing SQL reporting views/procedures need changes or bot-side adapters are sufficient.
- Rollback posture if emoji metadata exists and bot code is rolled back.

## 12. Test Strategy

Expected audit/docs validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

If implementation is approved, likely focused tests include:

- `tests/test_voting_service.py`
- `tests/test_voting_dal.py`
- `tests/test_survey_service.py`
- `tests/test_survey_dal.py`
- `tests/test_survey_post_view.py`
- `tests/test_vote_post_view.py`
- `tests/test_survey_export_service.py`
- renderer/card output tests for vote/survey cards
- dashboard presentation/view tests if dashboard representation changes
- command registration validation if builder command surfaces change

Run smoke imports, command registration validation, full pytest, SQL repo validation if SQL changes
are proposed, and Codex Security review before runtime handoff if implementation is approved.

## 13. Manual Smoke Plan To Confirm During Audit

Candidate smoke plan if runtime implementation is approved:

1. Create a one-choice vote with approved emoji/icon metadata and confirm button/card/status/export
   behavior.
2. Create a multi-select vote with emoji/icon metadata and confirm private selector prefill and
   public aggregate behavior.
3. Create a survey with choice and ranking options using emoji/icons.
4. Confirm fixed 1-5, 1-10, and custom rating surveys remain compatible.
5. Confirm generated cards render emoji/icons or safe fallbacks on desktop and mobile screenshots.
6. Confirm long labels and named rating distributions remain readable on public cards and private
   dashboard summaries.
7. Confirm PublicLive and HiddenUntilClose behavior remains aggregate-only.
8. Confirm private status, export, report bundle, and dashboard output remains private-safe.
9. Restart the bot while an emoji/icon vote or survey is open and confirm public openers and
   private controls still work.
10. Confirm existing one-choice, multi-select, choice/text/detail/optional/rating/ranking survey
    behavior remains compatible.

## 14. Stop Point

Stop after the audit/scope packet unless implementation is explicitly approved.
