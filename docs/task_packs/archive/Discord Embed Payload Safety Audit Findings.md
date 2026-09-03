# Discord Embed Payload Safety Audit Findings

Status: Phases 1 and 2A merged; Phase 2B delivered and production-merged; Phase 2C evidence-led tests/documentation implementation complete with no runtime correction required
Audit date: 2026-09-01; implementation and operator-smoke update 2026-09-02; Phase 2C update 2026-09-03
Repository: `C:\discord_file_downloader`
Scope: bot repository only; functional Discord payload audit, not a Codex Security codebase scan

## 1. Baseline and scope

After `git fetch origin --prune`, the checked-out branch is `main` at
`cca6d9cdb0dd15ba99403b89f03d1fede69f0e68` (`Mirror: 2026-09-01T14:09:23Z from
0ad875f2`). Fetched `origin/main` resolves to the same commit. The preparation reference therefore
remains the current mirror head, but this was revalidated rather than assumed.

The working tree was already dirty and all pre-existing changes were documentation-only. The
observed paths were:

- modified: `docs/calendar/event_calendar_task-9-pinned-calendar-embed.md`,
  `docs/reference/archive/deferred_optimisations_resolved.md`,
  `docs/reference/deferred_optimisations.md`, `docs/reference/runbook_startup.md`,
  `docs/task_packs/README.md`, and `docs/task_packs/archive/README.md`;
- deleted at their old locations and untracked in `docs/task_packs/archive/`: the Pinned Calendar
  Tracker chat starter and task pack;
- untracked: this task's chat starter and task pack (the on-disk task-pack filename ends in
  `.md.md`).

No pre-existing runtime or test changes were observed. These user-owned documentation changes must
be preserved and intentionally included when the eventual PR is prepared, after inspecting their
final diff.

The task is still bot-only. The SQL source-of-truth repository
`C:\K98-bot-SQL-Server` was also checked and was clean on `main...origin/main`. This task does not
change or rely on a new SQL object, column, procedure, cache schema, or data contract. If that
remains true, the SQL security review is a documented no-diff skip.

## 2. Incident reproduction and test gap

Current code builds the field as:

```python
"\n".join(_event_line(e) for e in week_events[:12])
```

The exact KVK 16 launch-week fixture renders as follows:

| # | Event | Rendered block characters |
|---:|---|---:|
| 1 | Preparation phase | 90 |
| 2 | Pre-KVK Starts! | 85 |
| 3 | KVK Map opens! | 84 |
| 4 | Marauders | 79 |
| 5 | Four Kings Enter... | 89 |
| 6 | Karuak | 76 |
| 7 | Finding a Foothold | 88 |
| 8 | Crusader Camp | 83 |
| 9 | Marauders' Forts | 86 |
| 10 | Megingjörð (Artifact) | 91 |
| 11 | Shoring Up | 80 |
| 12 | Crusader Fortress | 87 |

The blocks total 1,018 characters. The 11 join separators add 11, producing an exact field value
length of **1,029**, five above Discord's 1,024-character field-value limit. The current builder is
bounded by event count, not payload length.

`tests/test_prekvk_embed.py` replaces `get_all_upcoming_events()` with an empty list in both current
tests, so the failed field is never constructed. Its fake channel accepts arbitrary embed payloads
without Discord validation. The existing focused baseline remains green (`8 passed`) across the
Pre-KVK, embed helper, local-time title, and fighting-lifecycle tests, demonstrating the coverage
gap rather than disproving the incident.

## 3. Pre-KVK runtime flow

### Entry and state selection

Successful upload processing and admin/test routes ultimately call
`stats_alerts.interface.send_stats_update_embed()`. The interface evaluates the KVK state and the
Pass 4 fighting-open state. When fighting opens it removes `prekvk_msg_id`; it routes to the stats
or off-season channel and sends the Kingdom Summary before choosing KVK, Pre-KVK, or off-season
output.

### Event selection and formatting

`stats_alerts/embeds/prekvk.py` loads upcoming events from the Sheet-backed event cache. Event names
come from column B (`row[1]`) of `Chronicle_BOT_DATES` and `Major_BOT_DATES`. The builder:

1. normalizes each start time to aware UTC;
2. selects starts from `now - 1 hour` through `now + 7 days`, inclusive;
3. keeps only `chronicle` and `major` types;
4. sorts by start time;
5. renders at most the first 12 complete event blocks into one field.

Each block is `• **name** — starts <t:timestamp:R>` followed by a newline and the full formatted
date. The visible embed currently uses the first 12 events, while `LocalTimeToggleView` receives all
selected `week_events`. The fix should preserve both the selection rule and that existing view
cardinality unless separately approved.

### Edit, send, ping, state, and guards

- The builder loads `prekvk_msg_id` from the stats-alert state file.
- If the message exists and its creation date is today in UTC, it silently edits that message with
  the rebuilt embed and view. This path does not ping, run daily guards, or claim a send.
- A stale, missing, or failed-to-fetch message ID is removed and persisted. An edit failure also
  clears the ID and falls through to a fresh send.
- A non-test fresh send first checks that neither `offseason_daily` nor `offseason_weekly` was sent,
  then checks `prekvk_daily`. Guard read errors are logged and fail open.
- A fresh non-test send mentions `@everyone`; test sends do not. Allowed mentions are explicitly
  limited to the same condition.
- After a successful send, the returned message ID is saved as `prekvk_msg_id`.
- Off-season and daily guard skips raise `PreKvkSkip`, which the interface handles without treating
  it as a send failure.

### Current claim owners and defects

There are two current owners of `prekvk_daily`:

1. `stats_alerts/embeds/prekvk.py` claims after a successful fresh non-test send.
2. `stats_alerts/interface.py` claims again when the module returns `"sent"`.

The module call also passes an unintended positional empty tuple to `claim_send()` through
`run_blocking_in_thread()`. Because `claim_send(kind, *, max_per_day=1)` accepts no second positional
argument, this raises `TypeError` and then takes the `asyncio.to_thread()` recovery path. The normal
executor path therefore performs an avoidable failing invocation before the successful fallback.

Recommended ownership is the Pre-KVK module, because only it knows whether the result was a fresh
send, same-day edit, test send, skip, or failure. Remove the interface import/use for
`prekvk_daily`; retain the module claim only after a successful fresh non-test send; and call:

```python
await run_blocking_in_thread(
    claim_send,
    "prekvk_daily",
    max_per_day=1,
    name="claim_send_prekvk",
    meta={"key": "prekvk_daily"},
)
```

No claim should occur on edit, test, skip, or send failure. The current separate check/send/claim
sequence has a cross-process race window; changing it to a reservation protocol is a broader state
design and is deferred rather than folded into this behavior-preserving fix.

## 4. Existing limit helpers and ownership assessment

| Location | Current behavior and tests | Dependencies | Assessment |
|---|---|---|---|
| `embed_utils.send_embed_safe()` | Knows only 1,024 field values and 6,000 aggregate. It supports inline log fields, attachments, fallback sends, and a boolean result. Tests cover one small and one large log case. It does not enforce title, description, field-name, field-count, footer, author, or embed-count limits. Its total excludes log fields and other components. Its aggregate-overflow branch appends attachment-note fields without replacing originals, so it can duplicate fields and miscount both fields and characters. | Heavy legacy module: `discord`, file/telemetry helpers, image generation, constants, and other runtime utilities. | Keep its public sender behavior, but make it consume the canonical primitive and build/validate one final field plan before sending. It should not own the contract model. |
| `embed_utils.LocalTimeToggleView` and event formatters | Title clipping to 256 is tested. Grouped event values are built from complete lines under 1,024. A single event's dynamic name can still become an over-256 field name. History/failure pages also use dynamic file/path/error text without a complete contract check. | Same heavy module. | Same-root, low-risk compatibility fixes are suitable while this file is touched; final payload checks should use the canonical primitive. |
| `stats_alerts/embeds/kvk.py` | Local `_truncate_and_log()` limits selected field values to 1,024. Fixed two-embed route; no complete field-name/count/footer/author/aggregate or all-embeds check. | KVK renderer and data services. | Normal current payload appears bounded; do not duplicate a new model here. Adopt the canonical validator later or at a common final boundary. |
| `ui/views/calendar.py` | Local limits of 25 fields, 1,024 values, and a 5,800 soft aggregate; it chunks/truncates with a marker. Footer is not reserved in the budget, and calendar-page descriptions are not hard-bounded to 4,096. | Calendar domain, persistence, views. | Useful prior art, not canonical ownership. Broader pagination/product choices are deferred. |
| `mge/mge_content_renderer.py` | Limits field names to 256, splits values at 1,024, and caps 25 fields with a marker. Tests cover field limits. It has no 6,000 combined budget. | MGE content model. | Strong local policy for its current contract; keep it and later add the canonical final validation rather than rewrite its product behavior now. The standalone main-embed builder is test-only in the current call graph. |
| `ark/embeds.py` | Splits roster lines under 1,024 and clips pathological individual lines; tests cover roster field values. Dynamic alliance titles, notes, updates, result notes, field count, and aggregate remain unbounded. | Ark services/views/scheduler. | Broader dynamic-cardinality policy is deferred; it is not the confirmed Pre-KVK root cause. |
| Voting/survey services and dashboards | Service inputs use conservative title/description limits; dashboard fields clip to 1,024 and pages are sent/edited one at a time. Tests cover clipping and pagination. | Voting/survey services and views. | Safe for current validated contracts. |

The repository has useful local policies but no single dependency-light representation of the full
Discord contract. Adding more output-specific constants would create a third competing model.

## 5. Functional runtime inventory and disposition

The inventory searched constructors, `add_field`/description/footer/author mutations, and outbound
channel/message/interaction/follow-up/DM/webhook-style send and edit routes. It did not stop at
`discord.Embed(`. Test, documentation, and script-only results were separated from live paths.

| Path / function family | Delivery route and visibility | Dynamic source / cardinality | Current limits and tests | Realistic failure mode | Disposition |
|---|---|---|---|---|---|
| `stats_alerts/embeds/prekvk.py::send_prekvk_embed` | Scheduled/admin channel send; first fresh production send pings everyone; same-day public edit | Sheet event names; first 12 visible, all selected in local-time view | Count-only upcoming field; current tests use zero events | Confirmed 1,029 field value; dynamic field/name/aggregate overflow | **fix now** |
| `embed_utils.py::send_embed_safe` | Shared channel/DM-style destination send, optional fallback and attachments | Caller dictionaries; arbitrary field names/values/count | Partial 1,024/6,000 logic; two log tests | Duplicate fields, >25 fields, uncounted text, invalid names/title/components | **fix now** |
| `embed_utils.py::LocalTimeToggleView`, `format_event_embed`, `format_fight_embed`, history/failure views | Interaction edits and caller-owned sends | Sheet names, filenames, paths/errors; bounded page/event counts | Title and grouped value checks; incomplete name/final checks | Dynamic field name >256; pathological page aggregate | **fix now** for same-file name/final-boundary defects; redesign deferred |
| `stats_alerts/embeds/kvk.py` and off-season renderers | Scheduled/admin public channel sends; KVK can use multiple fixed embeds | SQL/cache summaries and ranking blocks; fixed renderer layout | Local value truncator; renderer tests | Pathological source text could exceed aggregate/name limits | **safe** for current contract; canonical adoption later |
| `ui/views/calendar.py` pinned embed and pages | Persistent public message edits and ephemeral/public interaction pages | Sheet events, cache metadata, configurable window | Canonical final validation, complete-item packing, continuation fields, and exact omission markers | Public calendar UX redesign remains separate | **safe** after Phase 2A |
| `event_embed_manager.py`, `event_scheduler.py`, `event_calendar/reminders.py`, daily KVK overview | Scheduled channel posts, edits, reminder DMs/channels | Sheet-controlled event names/descriptions; bounded event counts in some routes | Canonical final validation, bounded pathological free text, complete-event packing, and fallback/state regressions | Representative restart/pinned-edit production smoke passed; public/DM reminders were not manually forced and retain deterministic coverage | **safe** after Phase 2A |
| `mge/mge_content_renderer.py` and live MGE views/services | Public/ephemeral interaction sends and edits | Configured rules, brackets, awards; service-bounded content | 256/1,024/25 local policy with focused tests | Only pathological combined aggregate remains | **safe** current contract; canonical final check deferred |
| `mge` standalone `build_mge_main_embed` | No live caller found; tests only | Test content | Focused tests | No current delivery failure | **not runtime** |
| `ark/embeds.py`, scheduler, team publish/views | Scheduled/public and ephemeral team output | Alliance/player rosters, notes, results; potentially high cardinality | Roster chunks only; focused tests | >25 fields/6,000 aggregate or long notes/title | **defer** product-aware compaction/export policy |
| Voting and survey create/dashboard/result flows | Ephemeral setup, public dashboards, original-response/follow-up edits | User questions/options/votes; service-enforced cardinality | Conservative service limits, 1,024 clips, one page at a time; substantial tests | No realistic contract breach inside current validation | **safe** |
| Player self-service, targets, rankings/history, admin diagnostics, bot-health and queue embeds | Mixed ephemeral, DM, admin/private and public channel paths | SQL/player data, filenames, errors, logs; mostly bounded page sizes | Local slicing/clipping varies; route tests vary | Long external labels/error text or aggregate overflow in pathological data | **defer** by owning feature; use canonical validator during later changes |
| Fixed help, confirmation, status, command-error, and small control embeds | Mostly ephemeral/private; some fixed public messages | Fixed copy or a small number of validated values | Structurally small and covered indirectly | No realistic limit breach | **safe** |
| Tests, docs, examples, and render-only objects with no outbound call graph | None | Fixtures/static | N/A | Cannot fail a live Discord request | **not runtime** |

The automated similarity checker did not complete within two bounded 90-second attempts even after
excluding `.git`, virtual environments, tests, and docs. It was terminated cleanly. Manual literal
search plus function-level constructor/mutation/delivery analysis was completed instead; this tool
limitation does not change the dispositions above.

## 6. Canonical low-level model

Create dependency-light `core/discord_embed_limits.py`, with no `discord.py` import and no imports
from `embed_utils.py`. It should be the single owner of these inclusive hard limits:

| Component | Limit |
|---|---:|
| Embeds per message | 10 |
| Title | 256 |
| Description | 4,096 |
| Fields per embed | 25 |
| Field name | 256 |
| Field value | 1,024 |
| Footer text | 2,048 |
| Author name | 256 |
| Combined characters across every embed in the message | 6,000 |

The primitive should accept mappings and structurally accept objects exposing `to_dict()`. It
should provide:

- immutable, path-specific violations such as
  `embeds[0].fields[10].value: 1029/1024` and
  `message.embed_text_total: 6001/6000`;
- component and aggregate usage/remaining-budget calculations;
- deterministic helpers for bounded text with an explicit marker, without embedding product
  choices such as pagination, attachment, omission, or which list item has priority.

Tests must cover every exact boundary and every one-over boundary, including 10 versus 11 embeds,
25 versus 26 fields, and 6,000 versus 6,001 combined characters across one and several embeds.
Discord's current Message resource documentation is the authoritative contract source.

This primitive should be canonical instead of forcing all delivery through `send_embed_safe()`.
That sender has a specific dictionary input, `inline=False` behavior, attachment/fallback policy,
boolean return contract, and channel/DM-style `send()` semantics. Forcing it onto existing
`discord.Embed` objects would alter interaction originals, follow-ups, edits, ephemeral visibility,
views, files, allowed mentions, multi-embed messages, and return types. A validator/budget primitive
can be used by builders and at send/edit boundaries without taking ownership of those behaviors.

## 7. Exact Pre-KVK compaction policy

Preserve event source, time window, types, sort order, first-12 visible cap, formatting, links,
state logic, visibility, and the all-selected-events local-time view.

1. Format each selected logical event as the current complete two-line block.
2. Greedily pack complete blocks into fields no longer than 1,024, splitting only between events.
3. Name the first field `🗓️ Next 7 days:` and continuations
   `🗓️ Next 7 days (continued):`.
4. Account for field-name characters, all earlier embed content, the 25-field limit, and the 6,000
   combined limit before committing a field. Reserve space and field slots for the existing
   `Get ready`, optional `Links`, and footer content.
5. For the exact 12-event fixture, events 1-11 form a 941-character first value; event 12 forms an
   87-character continuation. No name or timestamp is lost.
6. If one event block alone is too large, normalize embedded line breaks and truncate only its
   event-name segment with an explicit ellipsis marker. Reconstruct the Markdown wrapper and retain
   the complete relative timestamp and formatted date line. Never cut an event block, timestamp,
   or Markdown delimiter arbitrarily.
7. If field slots or aggregate budget are exhausted, omit whole remaining visible events and add
   an explicit `… N more events — see Timeline` marker. If necessary, remove the last complete
   block(s) until the marker fits. The marker counts only omitted items from the existing first-12
   visible set; it must not silently expand or otherwise change event selection.
8. Validate the final payload before both `message.edit()` and `channel.send()`. Log only structural
   metrics (builder, field count, aggregate, maximum field length, continuation/compaction/omission
   counts), never event content.

## 8. Proposed implementation boundary

### Runtime files to change now

- add `core/discord_embed_limits.py`;
- update `stats_alerts/embeds/prekvk.py` for logical-event chunking, final validation, and the one
  correctly shaped post-send claim;
- update `stats_alerts/interface.py` to remove its duplicate `prekvk_daily` claim ownership;
- update `embed_utils.py` to consume the canonical model, construct replacement fields before
  mutating the embed, prevent duplicate attachment-note fields, account for every final component,
  enforce field names/count, and preserve its public send/fallback/attachment/boolean behavior.

Within `embed_utils.py`, bound confirmed dynamic field-name paths in `LocalTimeToggleView`, event
formatters, and history/failure pages using the same primitive. Do not mechanically rewrite every
builder and do not add another helper.

### Tests to add or change now

- add `tests/test_discord_embed_limits.py`;
- update `tests/test_prekvk_embed.py`;
- update `tests/test_embed_utils.py`;
- update `tests/test_local_time_embed_title.py`;
- update `tests/test_stats_alerts_fighting_lifecycle.py`.

No command, permission, visibility, source-data contract, SQL, cache, or KVK state changes are in
scope. Documentation after implementation should update this audit, the task status/index, and the
structured deferred register. No runtime or test file has been changed during this initial phase.

## 9. Deferred optimisation candidates

### Event/calendar renderer contract convergence

- **Area:** `event_embed_manager.py`, `event_scheduler.py`, `event_calendar/reminders.py`, daily KVK
  overview, and `ui/views/calendar.py`
- **Type:** Consistency / Architecture
- **Description:** These routes have fragmented title, description, field, footer, page, and
  aggregate policies. Some use Sheet-controlled labels. Calendar pagination needs an owning-output
  decision between chunking, pagination, omission markers, and attachment/export.
- **Suggested Fix:** Adopt the canonical validator and define tested product-specific compaction at
  each common renderer boundary.
- **Impact:** High
- **Risk:** Medium
- **Dependency:** Canonical primitive and product approval for changed page presentation

### Ark high-cardinality payload policy

- **Area:** `ark/embeds.py`, Ark scheduler, team publication, and related views
- **Type:** Architecture / Consistency
- **Description:** Roster values are split, but dynamic titles, notes, updates, result notes, field
  count, and aggregate size are not modeled together.
- **Suggested Fix:** Add a canonical budget and choose chunk/page/attach/omit-with-marker behavior
  for each Ark output, with pathological cardinality tests.
- **Impact:** Medium-High
- **Risk:** Medium
- **Dependency:** Canonical primitive and Ark presentation decision

### Rankings/history and diagnostic long-list output

- **Area:** KVK rankings/history views, player/admin history pages, bot-health/queue diagnostics
- **Type:** Consistency / Maintainability
- **Description:** Page-count assumptions and local clipping do not uniformly prove the complete
  embed contract for long external labels, paths, or errors.
- **Suggested Fix:** Inventory by feature, apply the canonical final validator, and select
  pagination, attachment/export, or explicit omission markers rather than silent truncation.
- **Impact:** Medium
- **Risk:** Medium
- **Dependency:** Canonical primitive and owning-feature tests

### Atomic Pre-KVK dispatch reservation

- **Area:** `stats_alerts/guard.py` and the Pre-KVK dispatch flow
- **Type:** Reliability / Architecture
- **Description:** The existing guard check, Discord send, and post-success claim are separate, so
  concurrent processes can both pass the read before either records the claim.
- **Suggested Fix:** Design a reserve/commit/release protocol with stale-reservation recovery and
  idempotency tests. Do not claim before a send without a safe release path.
- **Impact:** Medium
- **Risk:** High
- **Dependency:** Persistence/state design approval

## 10. Test and validation plan

Focused regression and behavior tests:

- exact 12-event fixture: prove 1,029 before the fix, then assert two valid fields, event order,
  all names/timestamps, 941/87 values, and unchanged first-12/all-view cardinality;
- empty, exact-boundary, one-over, multi-chunk, field-slot exhaustion, aggregate exhaustion, and
  pathological single-event cases, including an explicit omission marker;
- first fresh production send pings exactly once; test sends never ping;
- same-day edit uses the same safe builder, keeps the message ID, creates no new message/claim, and
  emits no ping;
- send failure persists no new ID and claims nothing; stale ID/edit failure behavior remains
  deterministic;
- exactly one `prekvk_daily` claim after a successful fresh non-test send, zero on edit/skip/test/
  failure, and no `TypeError` fallback;
- shared sender small-log and large-log compatibility, no duplicate original/note fields, valid
  field names/values/count/aggregate, attachment failure, fallback, and boolean return behavior;
- every canonical limit at exact and one-over boundaries, with path-specific violations and
  multi-embed aggregate coverage;
- LocalTime/event/history/failure compatibility for dynamic overlong field names and values;
- permission/visibility category unchanged and no command-registration change.

Selector output for the proposed file set requires full `tests`, `scripts/smoke_imports.py`, and
`scripts/validate_command_registration.py`. The implementation phase should run, in order:

1. the focused files above;
2. `python scripts/validate_architecture_boundaries.py`;
3. `python scripts/validate_deferred_items.py`;
4. `python scripts/validate_codex_security_routing.py`;
5. `python scripts/select_tests.py` for the final changed paths;
6. `python scripts/smoke_imports.py` and `python scripts/validate_command_registration.py`;
7. `.venv\Scripts\python.exe -m pre_commit run --all-files`;
8. `.venv\Scripts\python.exe -m pytest -q tests` (full suite), with log-noise review.

Unrelated failures are to be documented, not expanded into this PR.

## 11. Security routing

- **Bot:** final implementation requires a Codex Security **Changes** diff review against the
  intended base/head or final uncommitted patch. Deep must be off. Review focus is payload
  validation, Sheet/user-controlled data, ping/visibility preservation, attachment/log redaction,
  failure behavior, and claim state.
- **SQL:** documented skip if `C:\K98-bot-SQL-Server` still has no diff.
- **Excluded:** no standard codebase scan and no deep/multi-pass codebase scan. This functional
  repository-wide payload inventory does not authorize either.

## 12. Production smoke and rollback

Production promotion and deployment remain a separate approval and normal promotion workflow.
After that approval, smoke first through an admin/test route with no everyone mention, verify full
event names, continuation fields, links, and local-time behavior, and confirm no Discord 50035
response. At an approved time, verify one controlled fresh send produces one guard row and that a
same-day refresh edits the existing message without a second ping, message, or claim. Confirm KVK,
Kingdom Summary, and off-season routing remain unchanged and structural logs contain no payload
content.

Rollback is to revert the bot PR/commit and redeploy the prior bot revision through the normal
workflow. There is no SQL deploy, data migration, cache migration, or Sheet rollback. Shortening
the Sheet value is not the application fix and must not become a rollback dependency.

## 13. Approval outcome

On 2026-09-02 the operator approved the four-runtime-file boundary, five focused test files,
dependency-light canonical ownership, complete-event chunking and omission behavior, and the
Pre-KVK module as sole `prekvk_daily` owner. The operator then selected the separate-phase option
for wider remediation. No Phase 2 runtime work is authorized in this PR.

## 14. Approved implementation and Phase 2 decision

The operator approved the focused Phase 1 boundary on 2026-09-02 and selected the separate-phase
option for the wider audit findings. Implementation is on
`codex/discord-embed-payload-safety`, based on the revalidated
`cca6d9cdb0dd15ba99403b89f03d1fede69f0e68` mirror head.

Phase 1 now contains:

- dependency-light `core/discord_embed_limits.py` with all hard component, embed-count, field-count,
  and combined-message limits;
- complete-event Pre-KVK packing with the exact 1,029-character legacy regression producing
  941- and 87-character fields, pathological single-name compaction, truthful omission markers,
  reserved trailing-field/footer budget, and final validation before both edit and send;
- one module-owned, correctly offloaded post-success `prekvk_daily` claim and no interface claim;
- a repaired `send_embed_safe()` final field plan that bounds names/values/count/aggregate, moves
  overflow content to attachments by replacement instead of duplication, validates before send,
  and preserves mention, fallback, attachment, and boolean behavior;
- same-root shared-helper protection for local-time, event/fight, processing-history, and failure
  field names/values with explicit omission behavior where aggregate budget is exhausted.

Final focused validation after PR review is `40 passed`. The full suite passed with
`3059 passed, 2 skipped`;
pre-commit, architecture-boundary validation, deferred-item validation, test selection, import
smoke, command-registration validation, security-routing validation, and `git diff --check` also
passed. The log-noise gate also passed after the review fixes (`3059 passed,
2 skipped`; production operational logs unchanged).

The final bot security gate used scan type **Changes** against the working-tree snapshot based on
`cca6d9cdb0dd15ba99403b89f03d1fede69f0e68`, with Deep off. Scan
`dada5066-00ba-4c84-bec9-cd70b5e2d213` completed with full coverage and no reportable findings.
The accepted PR-review fixes received a second Changes-only review for the exact range
`4509b600..ac5c5e01`; scan `59865dd8-4628-4aa2-baba-3192ad5f5563` also completed with full
coverage and no reportable findings.
The SQL gate is a documented no-diff skip. No standard or deep codebase scan was run. Final K98 PR
review found no blocking or non-blocking code findings after bounding the shared sender's
Forbidden/HTTP fallback description with the already-safe title.

Mirror PR #251 carries the implementation and status commits `a7034a49` and `4509b600`, followed
by review-fix commit `ac5c5e01`. All five inline review comments were accepted and addressed:
defensive log-limit parsing, one-shot iterable materialisation, the ten-attachment cap, singular
omission-marker copy, and correction of the task-pack filename from `.md.md` to `.md`. Production
PR #558 carries the production promotion patch; both PRs await the operator's manual merge.

The agreed follow-up sequence is:

1. **Phase 2A — completed:** event/calendar payload convergence without command, visibility,
   selection, reminder-state, or restart-semantics changes;
2. **Phase 2B — delivered:** evidence-led Ark payload hardening, validation, Changes-only review,
   production-candidate promotion, and successful candidate smoke; manual merges and final
   production-main verification remain operator-owned;
3. **Phase 2C — implementation complete, review pending:** authoritative contracts proved live
   player-facing rankings/history payloads safe; regression and delivery records changed without a
   runtime diff;
4. **Phase 2D:** operator diagnostics payload convergence with privacy/redaction, attachment, and
   fallback policies kept separate from player outputs;
5. **Phase 2E:** Ark persistence/orchestration policy and delivery observability: confirmation-update
   retention, team-builder audit-service extraction, and unambiguous registration outcome logging;
6. **Phase 2F:** active public-reminder tracker atomic replacement with unchanged identity,
   scheduling, mention, and rehydration contracts;
7. **Phase 2G:** atomic Pre-KVK dispatch reservation only after evidence and an approved
   reserve/commit/release persistence design.

These items are staged in `docs/reference/deferred_optimisations.md` using the required structured
format. They are not part of the Phase 1 runtime diff.

## 15. Operator smoke evidence and final interpretation

On 2026-09-02 KVK state resolution selected KVK 16 `DRAFT`, and `/ops test_embed` produced:

```text
[PREKVK] Embed payload validated fields=13 chars=1847 max_field_value=530
         event_fields=1 compacted_events=0 omitted_events=0
[PREKVK] Edited existing message id=1544617668999381044
         in channel=1209532242506813540
[/ops test_embed] success (kvk=True, dur=1.33s)
```

The persisted `prekvk_msg_id` was `1544617668999381044`, matching the edited Discord message. The
observed `prekvk_daily` count was `1`. No new Pre-KVK message or Discord `50035` response appeared.

This accepts the canonical validation and same-day edit path. The reason no new message was sent
was the valid same-day message ID, not the daily guard: test mode bypasses off-season/daily guard
checks and performs no claim. In normal production, the guard controls a fresh-send fallback only
when no editable current message exists. A scheduled fresh-send ping and post-success claim remain
a natural operational observation; they were not independently exercised by this test command.

Phase 1, Phase 2A, and Phase 2B are archived as delivered records. Phase 2C rankings/history has
completed its approved tests/documentation-only implementation. The other audit deferrals retain
the named Phase 2D-2G ownership above.

## 16. Phase 2A delivery and operator acceptance

Phase 2A was delivered through mirror PR #252 and production PR #559, pending the operator's manual
merges. It reused the unchanged canonical helper, added final-contract validation to the approved
event/calendar renderers, retained complete logical items, and added exact count-bearing omission
markers. The final review correction made the one-event omission marker grammatically singular and
retained an exact full-marker assertion.

Focused Phase 2A and lifecycle coverage passed `74`, the calendar selector equivalent passed `157`,
and the final full and log-noise suites each passed `3078 passed, 2 skipped`. Architecture,
deferred, security-routing, selector, import-smoke, command-registration, and pre-commit gates
passed. Changes-only reviews `5accb59e-3e97-4b4e-aa54-647e9b396700` and
`8ce35934-d12f-4e21-bd7e-b2f9940b8dea` ran with Deep off and found zero reportable issues. The final
copy-only grammar correction received a precise incremental security skip, and SQL was a no-diff
skip.

Production restart smoke on 2026-09-02 completed pinned-calendar rehydration, armed the daily
refresh and reminder-loop tasks, and edited existing message `1488086669876920341` in place for 27
events. Payload metrics were `fields=15`, `chars=4789`, `max_field_value=533`,
`compacted_events=0`, and `omitted_events=0`. The next daily refresh scheduled normally, with no
duplicate or Discord `50035` rejection.

This is representative acceptance of restart/rehydration, persistent message identity, and the
pinned edit path. It did not independently exercise a public reminder, a DM reminder, fallback, or
an omission marker because none was safely forced in production. Those unchanged paths, state and
mention boundaries, and exact-boundary/pathological payload behavior retain deterministic automated
coverage. Phase 2B subsequently delivered without reopening Phase 1 or Phase 2A behavior.

## 17. Phase 2B approval and implementation evidence

On 2026-09-02 the operator approved the evidence-led Ark findings matrix, 45-member registration
and 30-member maximum credible team assumptions, result-priority policy, complete-unit packing,
visible compaction, count-bearing omission markers, attachment-free delivery, header-bearing
first-publication chunks, exact modification manifest, Changes-only security routing, SQL no-diff
skip, smoke boundary, and rollback.

Implementation is on `codex/discord-embed-payload-safety-phase-2b` from base `4290b0fc`. It changes
only the approved Ark render/delivery and interaction presentation paths plus focused tests and
records. The unchanged canonical helper validates registration, locked/cancelled, confirmation,
completed result, public/DM reminder, cancellation DM, team header/body, fuzzy selector,
team-builder, and report payloads. First-publication text accounts for the full header and splits
mention and no-Discord-name units below the 1,800-character soft limit while retaining SQL-backed
first-publication-only behavior and `AllowedMentions(users=True)`.

Deterministic evidence covers 255-character alliances, 45 schema-maximum governor snapshots,
1,024/1,025 values, aggregate/field exhaustion, pathological confirmation updates and result
notes, maximum credible teams, all-no-Discord-name suffixes, and character-budgeted report pages.
The Ark family passes `188`; the complete suite and log-noise run each pass
`3090 passed, 2 skipped`, with production operational logs unchanged. UI imports, architecture,
deferred-item, security-routing, test selection, import smoke, command registration, full
pre-commit, Ruff, Black, and Pyright pass. The SQL repository remains clean and receives a
documented no-diff security skip. Bot Changes scan
`79603f53-69f8-4586-9296-760385dd9420` reviewed
`4290b0fcc3d2568fca3a7fb7715f8baa06477f95..fccde886db2589382d279e6e0ef361dba16369af`
with Deep off, complete coverage of all 11 runtime review items, and zero reportable findings. Its
sealed manifest, coverage, findings, Markdown, and SARIF records were retained by the scan
workbench. Mirror PR #253 and production PR #560 carry the result. The later delivery-record
updates are documentation-only and receive a precise incremental security skip.

Phase 2B does not change command registration, permissions, public/ephemeral/DM visibility,
selection/order/status/lifecycle, caps, roster or team assignment, reminder eligibility/preferences/
timing/deduplication, message IDs, tracker or state formats, scheduler names/cadence, SQL/DAL,
fallback boundaries, startup, or rehydration. Rankings/history, diagnostics, active-reminder atomic
persistence, atomic Pre-KVK reservation, confirmation-update retention, and team-builder audit
service extraction remain separate deferred work.

## 18. Phase 2B operator candidate-smoke acceptance and follow-up ownership

On 2026-09-02 the operator successfully exercised match `52` using its existing registration
message reference. The builder and delivery logs recorded `fields=4`, `chars=346`,
`compacted_units=0`, `omitted_units=0`, `announcement_already_sent=True`,
`should_announce=False`, `force_repost=False`, `has_existing_ref=True`, and
`state_changed=False`. No duplicate, exception, or Discord `50035` occurred.

This accepts the candidate registration edit path and confirms that the first-publication-only ping,
existing message identity, and state boundary remained unchanged. The log field
`delivered=False` reflects the pre-existing move/repost return value on an in-place edit rather
than a failed delivery; its ambiguity is captured for Phase 2E with explicit success/failure and
edit/move/recreate outcome tests. It is not a reason to reopen the accepted Phase 2B payload diff.

Every Phase 2B deferral now has named ownership:

- Phase 2C: rankings and history payload convergence;
- Phase 2D: operator diagnostics payload convergence;
- Phase 2E: confirmation-update retention policy, team-builder audit-service extraction, and Ark
  registration outcome observability;
- Phase 2F: atomic `active_reminders` persistence;
- Phase 2G: evidence/design-gated atomic Pre-KVK dispatch reservation.

The existing KVK History once-only offload audit remains a coordinated but separate task: Phase 2C
preserves its current executor behavior and does not absorb that reliability change. Mirror PR
#253's tree is present on mirror `main`, and production PR #560 is merged.

## 19. Phase 2C approval and evidence-led implementation

On 2026-09-03 the operator approved the audit recommendation to make no runtime payload change.
Review against mirror base `e525fb355b5b831bcc84c349df944ee7725776f9` and SQL source-of-truth
commit `fc0e94ebd2e0a98286069c8a8b71365dd5178657` proved all live current-rankings,
Hall-of-Fame, My Rank, history-card, history-fallback, and private-export boundaries safe under
their authoritative source and maximum-cardinality contracts.

The test-only implementation covers KVK, Honor, and Pre-KVK Top 10/25/50 payloads at source maxima;
the Hall of Fame maximum of 4,030 description and 4,187 aggregate characters; an out-of-contract
single-unit 4,097-character description rejection; grouped-message aggregate rejection; and a
complete maximum-contract three-row history fallback below the 2,000-character content limit.
Focused validation passed `79`, and the full suite passed `3104 passed, 2 skipped`. Architecture,
deferred-item, security-routing, import-smoke, command-registration, pre-commit, and independent
production-log-noise gates passed.

Changes-only security scan `25a90732-3ad2-4ee0-9138-d1f4f11bbf36` reviewed the exact bot range
`e525fb355b5b831bcc84c349df944ee7725776f9..fa67d842dfc8858e2edd844313c74e1686cf830e`
with Deep off, complete coverage of all nine changed files, and zero findings. SQL is a documented
no-diff skip. The later scan-result wording is documentation-only and receives a precise incremental
security skip.

No command, runtime builder, view, service, DAL, SQL, config, cache, state, permission, channel,
owner, visibility, mention, attachment, export, fallback, identity, timeout, startup, restart, or
executor behavior changed. Phase 2D-2G and the separate KVK History once-only executor audit retain
their existing ownership.
