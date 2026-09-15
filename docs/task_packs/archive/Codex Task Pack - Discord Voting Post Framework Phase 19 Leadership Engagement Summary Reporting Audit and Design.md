# Codex Task Pack - Discord Voting Post Framework Phase 19 Leadership Engagement Summary Reporting Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 19 Leadership Engagement Summary Reporting Audit and Design`
- Date: `2026-07-08`
- Owner/context: `Follow-up after Phase 18 closed cross-survey/workbook export redesign as not required`
- Task type: `audit | private leadership reporting product scope | privacy review | SQL/data compatibility review | dashboard/report design`
- One-pass approved: `no`
- Status: `archived; delivered in mirror PR #212 and production PR #519, smoke/regression tested on 2026-07-08`

## 2. Objective

Audit and design whether the voting framework should add a private leadership engagement summary
over vote and survey activity.

The need is different from Phase 18 workbook/export redesign. Phase 18 confirmed the existing
private CSV exports and report bundles are understood and sufficient. The new question is whether
leadership needs a higher-level private view or report that answers:

- Are we publishing too many votes or surveys?
- Is engagement healthy across recent voting/survey activity?
- Which players are participating often, rarely, or not at all?
- How does engagement vary by month or rolling time window?

Start with audit/scope confirmation. Do not implement new dashboard pages, report files, export
modes, command options, SQL/DAL changes, identity joins, public reporting, retention/redaction
behavior, or SQL-native combined reporting until the operator approves product scope, privacy
boundaries, data contract, compatibility, documentation, tests, rollout, rollback, and
communication plan.

## 2A. Completion Update

Phase 19 is complete. It delivered a compact private engagement mode in `/vote_admin dashboard`
with:

- `Total Polls`, `Total Users`, `Participation levels`, and `Monthly Snapshots`.
- Last month, last 3 months, and last 6 months windows.
- Role-filtered eligibility covering expected roles, all non-bot members, and individual Discord
  roles such as `Kingdom Leadership`.
- One-Discord-user counting regardless of multiple governor IDs.
- One participation opportunity per closed published vote or survey item; multi-select votes and
  multi-question surveys each count as one opportunity.
- Vote/response changes that update participation without multiplying it.
- Unsubmitted survey drafts excluded.
- Best and worst single poll in the selected time slice, with newest poll date as the tie-breaker.
- Graceful dashboard timeout/edit-failure handling.

The initial long per-user lowest-participation list was removed from the embed after smoke-test
feedback. The richer private per-user breakdown is now split into Phase 20 as a separate
audit/design task for an export, scrollable/paged list, graph, or staged combination.

Phase 19 did not add public reporting, raw text/detail answers, per-answer response detail,
existing export/report-bundle CSV schema changes, workbook outputs, retention/redaction changes,
command reshaping, top-level commands, governor-linked reporting, role-restricted voting, or
SQL-native combined reporting views/procedures.

Validation included focused vote-admin dashboard/reporting tests (`28 passed`), architecture and
deferred validators, selected-test review, smoke imports, command registration validation, UI import
coverage, full pytest (`2391 passed, 2 skipped`), SQL source validation for vote/survey title
columns, production promotion checks, pytest log-noise validation, review feedback resolution, and
a Codex Security diff scan with zero findings. Operator smoke/regression testing on 2026-07-08
confirmed the compact output, best/worst polls, role filtering, and raw-answer exclusion.

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
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 18 Cross Survey Workbook Export Redesign Audit and Design.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 19 Leadership Engagement Summary Reporting Audit and Design.md`

## 4. Delivered Baseline

Phase 1 through Phase 18 are complete and smoke tested or audit-closed. The voting framework
supports:

- SQL-backed one-choice votes, single-question multi-select votes, and multi-question surveys.
- Choice, text, detail, optional, configurable rating, and ranking survey questions.
- Configurable rating scales up to 1-10, endpoint labels, named rating choices, and option emoji
  metadata.
- Persisted survey drafts/resume for surveys only, with draft exclusion from result/export/report/
  dashboard surfaces until submit.
- PublicLive and HiddenUntilClose result visibility.
- Scheduler reminders, automatic close, manual close, disabled controls after close, restart-safe
  public openers, and one ballot/response per Discord user.
- Private admin/leadership status, export, report-bundle, and `/vote_admin dashboard` surfaces.
- Private totals-only vote CSV export and private voter-level vote audit CSV export.
- Private survey totals CSV export, response-detail CSV export, and report-bundle CSV export.
- Private dashboard-safe aggregate reporting contracts and private aggregate dashboard UI.
- `/vote_admin survey_update` for safe open-survey metadata updates with response-sensitive locks.
- Phase 17 decision to keep `/vote_admin` command paths unchanged.
- Phase 18 decision that single-survey workbook output and cross-survey aggregate workbook/report
  output are not required now.

Phase 18 intentionally did not change runtime commands, command registration, aliases, help panels,
permissions, autocomplete, usage tracking, SQL, exports, reports, dashboards, or public rendering.

## 5. Source Deferred Item

### Deferred Optimisation
- Area: `voting/reporting_service.py`, `voting/reporting_dal.py`, `/vote_admin dashboard`, future private leadership reporting
- Type: architecture
- Description: Phase 19 audited and then delivered a higher-level private participation and engagement summary over vote/survey activity by time window. Delivered measures include published vote/survey counts, total possible participation opportunities, actual vote/survey participation counts, aggregate engagement rate, monthly snapshots, role-filtered eligibility, and best/worst single poll. The long per-user participation breakdown was intentionally split into Phase 20 because it is too large for a focused embed.
- Suggested Fix: Completed through the Phase 19 private `/vote_admin dashboard` engagement mode. Follow-up per-user export/list/graph work is promoted into Phase 20 and remains approval-gated before implementation.
- Impact: medium
- Risk: high
- Dependencies: Phase 18 closed workbook/cross-survey export redesign as not required; active Phase 19 audit/design approval; SQL validation in `C:\K98-bot-SQL-Server`; privacy approval for Discord-name participation/non-participation reporting; Codex Security review before runtime PR handoff.

## 6. Candidate Phase 19 Scope To Confirm

### In Scope For Audit/Design

- Inventory current dashboard/reporting data contracts:
  - `/vote_admin dashboard`
  - `voting.reporting_service.build_admin_leadership_dashboard_report`
  - `voting.reporting_dal` vote/survey summary queries
  - vote and survey response/voter tables through SQL repo validation
- Define leadership questions and success criteria:
  - are vote/survey counts too high for the community
  - is engagement healthy over time
  - which users rarely participate and may need follow-up
  - which content types or time windows show low participation
- Confirm time-window options:
  - last month
  - last 3 months
  - last 6 months
  - monthly buckets such as June, July, and later months
  - whether custom date ranges are needed or explicitly out of scope
- Define counting rules:
  - vote post published count
  - survey post published count
  - open versus closed item inclusion
  - possible participation denominator
  - actual participant count
  - engagement rate
  - per-user participation count
  - treatment of vote changes and survey response changes
  - treatment of one multi-question survey as one participation opportunity
  - treatment of single-question multi-select votes as one participation opportunity
  - treatment of unsubmitted survey drafts as excluded
- Confirm whether engagement should include:
  - votes only
  - surveys only
  - combined vote/survey activity
  - separate and combined views
- Confirm privacy boundaries:
  - private admin/leadership delivery only
  - no public engagement dashboard
  - Discord identity allowed only in the approved private participation profile
  - no raw text/detail answers
  - no per-answer response detail unless separately approved
  - non-participation inference and leadership follow-up expectations
  - HiddenUntilClose semantics for currently open items
- Confirm command and UX ownership:
  - extend `/vote_admin dashboard` with a private engagement page or filter
  - add a new subcommand under existing `/vote_admin` only if dashboard extension is unsuitable
  - avoid new top-level commands
  - avoid `/vote_admin` reshaping or aliases
  - decide whether output is dashboard-only, report/export file, or staged combination
- Confirm SQL posture:
  - whether existing bot-side DAL/reporting queries are enough
  - whether additive bot-side DAL reads are enough
  - whether SQL-native views/procedures are justified by performance or consumer needs
  - exact SQL objects and indexes to validate before implementation
- Confirm tests, Codex Security requirement, deployment order, rollback posture, smoke checks, and
  deferred follow-up work.

### Candidate Implementation Scope If Approved Later

- Add only the approved private leadership engagement surface.
- Preserve existing `/vote_admin dashboard`, export, report-bundle, status, close, and update
  behavior unless explicitly approved.
- Keep existing private CSV/export profiles unchanged.
- Keep survey drafts excluded until final submit.
- Keep raw text/detail answers out of engagement summaries.
- Keep Discord identity out of aggregate-only summaries unless the approved profile is explicitly
  a private per-user participation profile.
- Use service-owned reporting contracts and DAL-owned SQL reads.
- Add focused tests for metrics, time windows, identity privacy, empty data, permission/private
  surface behavior, command/dashboard registration, and output shape.
- Update canonical command docs, task packs, operator guidance, and smoke references if command
  options or dashboard/report surfaces change.

## 7. Out Of Scope Unless Separately Approved

- New voting or survey answer types.
- `/vote_admin` command reshaping, command aliases, new top-level commands, or help panels.
- Changing submitted vote or survey response semantics.
- Changing Phase 16 survey update locks.
- Changing existing export/report-bundle CSV schemas.
- Single-survey workbook output or cross-survey aggregate workbook output.
- Public dashboards, public raw text/detail display, public participation reports, or public
  voter-level/response-detail exports.
- Raw text/detail answer reporting in engagement summaries.
- Retention/redaction policy changes.
- SQL-native combined vote/survey reporting views/procedures unless this audit produces a concrete
  need and the operator approves folding that SQL work into the implementation slice.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Per-rating comments.
- Generated-card custom emoji asset fetching or animation.

## 8. Remaining Separate Follow-Up Slices

- Retention/redaction policy changes.
- Optional SQL-native combined reporting views/procedures if reporting consumers or performance
  needs justify them and Phase 19 does not explicitly approve them.
- Cross-survey/workbook exports only if a future concrete workbook/comparison consumer appears.

Definitely not required unless a later operator decision reverses the status:

- Per-rating comments.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public voter-level/detail export posting.

## 9. Codex Skills To Use

- `k98-architecture-scope`
- `k98-sql-validation` because this audit depends on SQL-backed vote/survey participation data,
  identity fields, possible reporting queries, and any SQL-native reporting contracts proposed
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review` before runtime PR handoff if implementation is approved
- `k98-promotion-check` before production promotion if implementation is approved
- `codex-security` security review before runtime PR handoff if implementation touches
  permissions, Discord interactions, SQL/data access, generated reports/exports, private data,
  file handling, user-controlled input, or restart-sensitive flows

## 10. Validation Expectations

For audit/docs-only work:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

If implementation is later approved, expected validation areas include:

- existing voting reporting service tests
- existing dashboard presentation/view tests
- new engagement reporting service tests
- new engagement DAL tests or SQL contract tests
- time-window and monthly-bucket tests
- zero-data and low-data tests
- per-user private identity boundary tests
- tests proving raw text/detail answers are not included
- tests proving unsubmitted drafts are excluded
- permission/private delivery tests if the dashboard or command surface changes
- command registration validation if command options change
- smoke imports
- SQL repo validation if SQL-facing assumptions or SQL objects change
- Codex Security diff scan before runtime PR handoff
- manual Discord smoke testing for private delivery, dashboard/report navigation, date-window
  selection, expected metrics, and identity privacy

## 11. Audit Packet Acceptance Criteria

The audit/scope packet is ready when it clearly answers:

- Whether a private leadership engagement summary is needed now.
- Which leadership workflow it serves.
- Which current dashboard/report/export surfaces already cover part of the need.
- Which command path, dashboard page, report mode, or export mode would own any approved surface.
- Which time windows and monthly buckets are required.
- Which metrics are included and how each is calculated.
- How possible participation and actual participation are counted for one-choice votes,
  multi-select votes, and multi-question surveys.
- Whether vote/survey activity is shown separately, combined, or both.
- Whether output is aggregate-only, per-user private identity, or staged.
- Which private data fields are allowed.
- How draft exclusion, HiddenUntilClose, raw text/detail boundaries, and Discord identity
  boundaries are preserved.
- Whether SQL changes are required or existing bot-side contracts are enough.
- What tests, smoke checks, deployment order, rollback posture, and security review are required.

Stop after the audit/scope packet unless the operator explicitly approves implementation.

## 12. Audit / Scope Packet - Draft For Operator Approval

### Scope Summary

Phase 19 is justified as a private leadership engagement summary need, not as a workbook/export
redesign. Existing private exports and report bundles remain sufficient for single-vote and
single-survey inspection, and the current `/vote_admin dashboard` is useful for per-item aggregate
review. The gap is a higher-level participation view across multiple vote/survey posts and time
windows.

No implementation is approved by this packet. The recommended next implementation, if approved, is
an additive private engagement surface owned by the existing `/vote_admin dashboard` workflow. A
new `/vote_admin` subcommand should be used only if dashboard extension proves unsuitable after UI
design review. A new top-level command, public dashboard, public report, export schema change,
identity join, SQL-native combined reporting object, or retention/redaction change remains out of
scope unless explicitly approved.

### Current Contract Inventory

- `/vote_admin dashboard` is registered in `commands/vote_admin_cmds.py` and opens an ephemeral,
  admin/leadership-only `VoteAdminDashboardView`.
- `voting.reporting_service.build_admin_leadership_dashboard_report` builds a private,
  aggregate-only `DashboardReportingContract` for recent vote/survey items.
- `voting.reporting_models.DashboardReportingContract` explicitly marks the current profile as
  `admin_leadership_private_dashboard_safe`, with `contains_raw_text_or_detail=False` and
  `contains_discord_identity=False`.
- `voting.dashboard_presentation` refuses to render unsafe contracts and labels the current output
  as an aggregate-only private dashboard.
- `voting.reporting_dal` reads aggregate vote and survey summaries from SQL-backed tables. It
  intentionally omits Discord names, raw text answers, and detail text.
- Current dashboard filters cover all/votes/surveys/open/closed, but not rolling windows, monthly
  buckets, volume summaries, engagement rates, or per-user participation.
- Existing private vote/survey exports expose Discord identity only in explicitly private
  voter-audit or response-detail profiles for one closed item at a time.

### SQL / Data Contract Review

Validated SQL-backed source objects in `C:\K98-bot-SQL-Server`:

- `dbo.VotePosts`, `dbo.VotePostOptions`, `dbo.VotePostVotes`, `dbo.VotePostAudit`, and
  `dbo.VotePostReminders` from `20260701_002_add_vote_post_framework.sql`.
- `dbo.VotePostMultiSelectVotes` and `dbo.VotePostMultiSelectSelections` from
  `20260702_002_add_vote_post_multi_select.sql`.
- `dbo.SurveyPosts`, `dbo.SurveyQuestions`, `dbo.SurveyQuestionOptions`,
  `dbo.SurveyResponses`, `dbo.SurveyAnswers`, `dbo.SurveyAudit`, and `dbo.SurveyReminders` from
  `20260702_003_add_survey_post_framework.sql`.
- `dbo.SurveyResponseDrafts` from `20260706_001_add_survey_response_drafts.sql`; drafts are
  deliberately separate from submitted response rows and must remain excluded.
- `dbo.v_SurveyReportingQuestionSummary`, `dbo.v_SurveyReportingOptionSummary`, and
  `dbo.usp_SurveyReporting_ExportV2` from `20260705_001_add_survey_reporting_views.sql`; these
  are aggregate survey reporting contracts and intentionally exclude raw text/detail and Discord
  identity.
- Optional identity-population source candidates exist in `dbo.DiscordGovernorRegistry` and
  `dbo.sp_Registry_GetAllActive`, but using them would be an identity join and requires explicit
  approval. `DiscordGovernorRegistry` is governor-account based, not a complete Discord guild
  membership list.

The existing SQL contract can support participant counts for published vote/survey posts:

- One-choice votes: one participation per `dbo.VotePostVotes` row.
- Multi-select votes: one participation per `dbo.VotePostMultiSelectVotes` row; selections are
  detail, not extra participation opportunities.
- Surveys: one participation per `dbo.SurveyResponses` row; a multi-question survey is one
  participation opportunity.
- Survey drafts: excluded because they live in `dbo.SurveyResponseDrafts`, not submitted response
  tables.
- Response/vote changes: do not create extra participation; use the latest current row while
  optionally exposing changed/updated counts only in a later approved audit detail.

The existing SQL contract does not define the eligible population for non-participation. For an
aggregate server-wide engagement denominator, the implementation can reuse the existing Discord
guild-member count pattern from `server_status/member_count_channel.py`, with an explicit decision
about whether bot accounts are excluded. For per-user "who did not engage" reporting, a count alone
is not enough; the implementation needs an eligible-user roster. Phase 19 must approve one roster
source before per-user non-participation can be shown:

- current non-bot guild members resolved through Discord at report time, reusing or extracting the
  member enumeration pattern already used by registry audit/export flows;
- current non-bot guild members filtered by expected-participation Discord roles. This is likely
  the best fit if leadership wants to include roles such as `Kingdom Leadership`, exclude members
  with no meaningful role beyond `@everyone`, and compare engagement by role segment. Role IDs are
  safer than role names for configuration because names can be edited, but dashboard labels can
  still display the current role name;
- active registered Discord users from `dbo.DiscordGovernorRegistry`, preferably through
  `registry.registry_service.load_registry_as_dict(use_cache=False, allow_stale_on_error=False)`
  or an equivalent strict service/DAL helper. The legacy `registry/governor_registry.py`
  `load_registry()` façade can show the current dict shape, but it allows stale cache and returns
  `{}` on SQL failure, so it is not accurate enough as the direct reporting source for
  non-participation. This population is a registered-player population rather than total server
  membership;
- a leadership-maintained eligible roster; or
- known prior vote/survey participants only, with the limitation that true zero-participation users
  outside that known set cannot appear.

### Recommended Product Direction

Use a staged private model:

1. Add a private dashboard engagement view under the existing `/vote_admin dashboard` surface.
2. Include fixed rolling windows: last month, last 3 months, and last 6 months.
3. Include monthly buckets for the selected 6-month horizon, labelled by calendar month such as
   June and July.
4. Show votes and surveys separately and combined.
5. Add role-filtered eligibility if approved: leadership/admin can choose or preconfigure expected
   participation roles, with members who only have `@everyone` excluded from denominators and
   named non-participation lists by default.
6. Treat custom date ranges as out of scope for the first implementation unless the operator
   explicitly approves date-range UX.
7. Keep report/export files out of the first implementation unless leadership needs a shareable
   private artifact after seeing the dashboard design.

Recommended first-slice metrics:

- vote posts published;
- survey posts published;
- total published items;
- possible item opportunities, defined as the number of published items before an eligible-user
  population is approved;
- actual vote participants;
- actual survey participants;
- combined participation events;
- aggregate item-level engagement trend;
- per-user private participation count only after the approved population source and privacy
  wording are confirmed.

If an aggregate member-count denominator is approved, engagement rate should be:

```text
actual participation events / (eligible Discord users * published item opportunities)
```

where each vote post and each survey post is one opportunity per eligible Discord user. Since each
Discord user has only one current vote or survey response per item, multiple governor IDs must not
multiply the denominator or the participation count. If only a count is approved, the dashboard can
show aggregate engagement rates but cannot identify named non-participants. If no population count
or roster is approved, the dashboard must avoid presenting a true community-wide rate and instead
show volume and participant counts with clear private wording.

### Counting Rules To Approve

- Published item count includes posts with a non-null Discord `MessageID`.
- Closed items are included by default for final engagement statistics.
- Open items may appear in a separate "in progress" section, but must not be mixed into final
  engagement-rate judgments unless explicitly labelled as interim.
- HiddenUntilClose open items may show private admin/leadership participation counts, but no public
  behavior changes are allowed.
- Role-filtered views should count each Discord user once if they match the selected eligibility
  role set, even if they have multiple matching roles or multiple registered governors.
- Members with no meaningful role beyond `@everyone` should be excluded when the approved report
  mode is "expected participants only".
- Cancelled or launch-failed posts should be excluded from published engagement unless the operator
  wants an operational volume metric.
- One-choice vote changes count as one participant.
- Multi-select vote changes count as one participant and selection counts remain out of the
  engagement denominator.
- One multi-question survey counts as one participation opportunity and one response event.
- Optional skipped survey questions do not reduce survey participation once the response is
  submitted.
- Unsubmitted survey drafts are excluded.
- Raw text/detail answer content is excluded.
- Per-answer detail is excluded unless a later private response-detail profile is approved.

### Privacy Model To Approve

Minimum privacy boundary:

- private admin/leadership delivery only;
- no public engagement dashboard or public participation report;
- no raw text/detail answers;
- no per-answer response detail;
- no governor-linked reporting;
- no retention/redaction policy change;
- no public non-participation naming;
- no Discord identity in the aggregate dashboard-safe contract.

If per-user participation is approved, use a separate private identity profile rather than changing
the existing dashboard-safe aggregate profile. The profile should include only:

- Discord user ID as spreadsheet-safe text if exported later;
- resolved Discord display name where available;
- eligible opportunity count;
- participation count;
- non-participation count;
- engagement percentage;
- last participation timestamp.

Leadership communication should explicitly frame non-participation as a follow-up signal, not a
disciplinary conclusion, because notification delivery, time zones, Discord availability, and
member eligibility can affect participation.

### Architecture Direction

Recommended ownership if implementation is approved:

- `voting/reporting_models.py`: add new engagement dataclasses and a distinct privacy profile.
- `voting/reporting_dal.py`: add DAL-owned, parameterized/bounded SQL reads for engagement
  summaries and participant rows.
- `voting/reporting_service.py`: own time-window calculation, counting rules, population-source
  orchestration, role-filter eligibility, deduplicated Discord-user counting, and privacy-profile
  assembly.
- `voting/dashboard_presentation.py`: add engagement rendering only after the contract can prove
  the correct privacy profile.
- `ui/views/vote_admin_dashboard_view.py`: add dashboard mode/window controls only if approved;
  preserve owner-only private interaction checks and refresh behavior.
- `commands/vote_admin_cmds.py`: prefer no new command. If a new `/vote_admin` subcommand is later
  approved, keep the handler thin and service-backed.
- Tests: add focused service, DAL, presentation, view, command-registration, privacy, and
  zero-data coverage.

Do not add embedded SQL to command or view modules. Do not expand existing export services unless
report-file output is separately approved.

### SQL Posture

Recommended first implementation posture: additive bot-side DAL reads only. Do not add SQL-native
combined vote/survey reporting views or procedures unless one of these is true:

- representative-data performance shows bot-side queries are too expensive;
- another non-bot SQL consumer needs the same report;
- the operator explicitly wants SQL-owned reporting contracts for this summary.

Before implementation, validate exact columns and indexes again for:

- `dbo.VotePosts`: `VotePostID`, `MessageID`, `Status`, `CreatedAtUtc`, `ClosesAtUtc`,
  `ClosedAtUtc`, `ResultVisibility`, `VoteMode`;
- `dbo.VotePostVotes`: `VotePostID`, `DiscordUserID`, `CreatedAtUtc`, `UpdatedAtUtc`;
- `dbo.VotePostMultiSelectVotes`: `VotePostID`, `DiscordUserID`, `CreatedAtUtc`, `UpdatedAtUtc`;
- `dbo.SurveyPosts`: `SurveyID`, `MessageID`, `Status`, `CreatedAtUtc`, `ClosesAtUtc`,
  `ClosedAtUtc`, `ResultVisibility`;
- `dbo.SurveyResponses`: `SurveyID`, `DiscordUserID`, `CreatedAtUtc`, `UpdatedAtUtc`;
- approved population source, if any.

Index review is required before implementing rolling windows over larger production history,
because the current voting/survey indexes are primarily shaped around open-due scheduling,
per-post response uniqueness, and per-item reporting.

### Refactor Triggers

- Existing `/vote_admin dashboard` command/view/service layering is acceptable for a future
  additive engagement slice.
- Existing dashboard-safe contract intentionally blocks identity and raw detail; do not weaken it.
- The main unresolved trigger is product/data ambiguity around the eligible participant population.
  This is not a code defect; it must be resolved before implementation.
- Optional SQL-native combined reporting remains deferred unless performance or consumer needs are
  proven.

### Deferred Optimisation
- Area: `voting/reporting_dal.py`, `voting/reporting_service.py`, SQL repo vote/survey reporting contracts
- Type: architecture
- Description: SQL-native combined vote/survey engagement reporting views or procedures may become useful if rolling-window engagement queries grow expensive or if a direct SQL reporting consumer appears, but the current Phase 19 audit found no concrete need to add SQL-owned combined reporting before the private product workflow and eligible-user population are approved.
- Suggested Fix: Keep first implementation on additive bot-side DAL reads. Revisit SQL-native engagement views/procedures only after representative-data performance evidence or a direct SQL consumer requirement exists, then validate SQL objects, indexes, deployment order, rollback, and output-equivalence tests in the SQL repo.
- Impact: medium
- Risk: medium
- Dependencies: Approved Phase 19 product scope; representative data/performance evidence or direct SQL consumer need; SQL repo review in `C:\K98-bot-SQL-Server`.

### Test Strategy

For this audit/docs-only slice, run:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

If implementation is approved later, add or update:

- `tests/test_voting_reporting_service.py` for counting rules, windows, month buckets, population
  denominator behavior, role-filter eligibility, no-role exclusion, one-Discord-user counting
  despite multiple governors/roles, zero-data behavior, open/closed separation, and draft
  exclusion;
- `tests/test_voting_reporting_dal.py` for bounded SQL shape, no raw text/detail reads, and
  correct vote/survey participant row sources;
- `tests/test_vote_admin_dashboard_presentation.py` for private aggregate rendering and privacy
  refusal paths;
- `tests/test_vote_admin_dashboard_view.py` for mode/window controls, owner-only refresh, and
  expired/private behavior;
- `tests/test_vote_admin_cmds.py`, `tests/test_validate_command_registration.py`,
  `tests/test_command_inventory.py`, and `tests/test_command_registration_smoke.py` if command
  options or subcommands change;
- identity-profile tests proving Discord names appear only in the approved private per-user
  profile and raw answer content never appears.

Codex Security review is required before runtime PR handoff if implementation touches the private
identity profile, Discord interactions, SQL/data access, generated files, permissions, or dashboard
controls. For this docs-only audit, Codex Security can be skipped with the documented reason that
no runtime behavior changed.

### Rollout / Rollback / Smoke Direction

If bot-side dashboard implementation is approved with no SQL migration:

- deploy bot-only after tests and Codex Security review;
- rollback by reverting the bot PR;
- no database rollback needed;
- smoke with an admin/leadership account: open dashboard, switch engagement window/month, verify
  private-only delivery, verify aggregate counts, verify per-user profile privacy if approved, and
  verify existing dashboard item pages still work.

If SQL-native reporting is later approved:

- deploy SQL objects first;
- validate SQL deployment against a representative database;
- deploy bot after SQL validation;
- rollback by disabling bot usage first, then leaving additive SQL objects in place unless a
  separate destructive cleanup is approved.

### Open Questions / Approval Needed

Implementation must not start until the operator approves these decisions:

- Is the private leadership engagement summary needed now?
- Should first delivery be dashboard-only, report/export-file only, or staged dashboard first then
  optional file output?
- Are fixed windows last month, last 3 months, last 6 months, and 6-month monthly buckets enough?
- Are custom date ranges out of scope for the first implementation?
- Should open items be shown separately as interim, or excluded entirely?
- Which eligible-user population should define true non-participation and engagement rate?
- Is active `DiscordGovernorRegistry` acceptable as the first private eligible-user population, or
  should the report use current guild members, the existing member-count pattern,
  `registry.registry_service.load_registry_as_dict(...strict...)`, or a leadership-maintained
  roster instead?
- Should Phase 19 use role-filtered eligibility as the preferred model, for example include
  `Kingdom Leadership` and other expected-participation roles while excluding members with only
  `@everyone`?
- Should role filters be configured by Discord role ID, by dashboard selector, or both?
- What is the role precedence if a member has both an included role and a role leadership wants to
  exclude from expectations?
- Is private per-Discord-name participation/non-participation reporting approved, and which fields
  are allowed?
- Should votes and surveys be shown separately and combined, as recommended?
- Is additive bot-side DAL reporting approved as the SQL posture, with SQL-native combined
  reporting deferred?
- Is the proposed test, Codex Security, rollout, rollback, and smoke plan approved?
