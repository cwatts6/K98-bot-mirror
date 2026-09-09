# Codex Task Pack - Discord Embed Payload Safety Audit and Pre-KVK Overflow Fix

## 1. Task Header

- Task name: `Discord Embed Payload Safety Audit and Pre-KVK Overflow Fix`
- Date: `2026-09-01`
- Owner/context: `Chris Watts / 2026-08-24 Pre-KVK stats-alert incident and follow-up reliability review`
- Task type: `bug fix`
- One-pass approved: `no`
- Status: `delivered in mirror PR #251 and production PR #558; operator edit-path smoke accepted on 2026-09-02; awaiting manual merges`
- Approved Phase 1: canonical dependency-light embed contract, Pre-KVK complete-event chunking and
  omission marker, repaired shared sender, and sole module-owned `prekvk_daily` claim
- Approved follow-up direction: separate Phase 2 programme beginning with event/calendar payload
  convergence; Ark and ranking/diagnostic slices remain evidence-led; atomic reservation remains a
  separate reliability design

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`

Conditional references required for this task:

- `docs/reference/REVIEW_HELPERS.md`
- `docs/reference/events_and_dm_reminders.md`
- `docs/reference/runbook_diagnostics.md`
- `docs/reference/deferred_optimisations.md`
- root `SECURITY.md`
- the current `k98-architecture-scope`, `k98-discord-command-feature`,
  `k98-test-selection`, `k98-deferred-optimisation-capture`, `k98-pr-review`,
  `k98-promotion-check`, and `k98-security-review-routing` skills

Reconfirm Discord's current hard payload limits against the official Discord Developer
Documentation for the Message Resource and embed limits before implementation. The expected
contract at task preparation is:

| Component | Hard limit |
|---|---:|
| Rich embeds per message | 10 |
| Embed title | 256 characters |
| Embed description | 4,096 characters |
| Fields per embed | 25 |
| Field name | 256 characters |
| Field value | 1,024 characters |
| Footer text | 2,048 characters |
| Author name | 256 characters |
| Combined title/description/field/footer/author text across all embeds in one message | 6,000 characters |

Do not rely on Discord trimming or rejecting invalid data as the application's validation
boundary.

The KingdomScanData4/KS4 database prerequisite that previously blocked the fix is complete. This
task is expected to be bot-only. Do not change SQL schema, procedures, views, indexes, data, or
`ProcConfig`. If the audit unexpectedly identifies a genuine SQL dependency, stop and report it
rather than extending this task into the SQL repository.

## 3. Objective

Make the Pre-KVK stats alert independent of event-name length and guarantee that its generated
Discord payload remains valid without shortening authoritative source data.

At the same time, establish or repair one canonical, tested embed-limit boundary, correct the
adjacent Pre-KVK send-guard ownership defects, and complete a functional repository-wide audit of
live embed builders and delivery paths. Fix confirmed same-root-cause defects that are safe and
PR-sized; capture larger product or pagination redesigns as structured deferred optimisations.

## 4. Background

### 4.1 Production incident

On `2026-08-24 07:34 UTC`, the bot correctly selected the Pre-KVK route but Discord rejected the
message:

```text
discord.errors.HTTPException: 400 Bad Request (error code: 50035): Invalid Form Body
In embeds.0.fields.10.value: Must be 1024 or fewer in length.
```

The failed field was `🗓️ Next 7 days:` in `stats_alerts/embeds/prekvk.py`.

The current implementation caps the block by event count, not rendered payload size:

```python
value="\n".join(_event_line(e) for e in week_events[:12])
```

Each item includes the complete event name, Markdown, a Discord relative timestamp, a line break,
and a full UTC date-time. The normal KVK 16 launch-week fixture rendered to `1,029` characters,
which was five characters over Discord's `1,024`-character field-value limit.

The exact qualifying event set was:

| UTC start | Name |
|---|---|
| 2026-08-26 00:00 | Preparation phase |
| 2026-08-28 00:00 | Pre-KVK Starts! |
| 2026-08-28 00:00 | KVK Map opens! |
| 2026-08-28 00:00 | Marauders |
| 2026-08-28 00:00 | Four Kings Enter... |
| 2026-08-28 03:00 | Karuak |
| 2026-08-28 03:00 | Finding a Foothold |
| 2026-08-28 15:00 | Crusader Camp |
| 2026-08-30 00:00 | Marauders' Forts |
| 2026-08-30 03:00 | Megingjörð (Artifact) |
| 2026-08-30 03:00 | Shoring Up |
| 2026-08-30 15:00 | Crusader Fortress |

The displayed names originate from:

- `Chronicle_BOT_DATES` column B for `chronicle` events; column A is the start date and column C is
  the description, which is not displayed in this field.
- `Major_BOT_DATES` column B for `major` events; column A is the start date.

A temporary source-data workaround shortened `Megingjörð (Artifact)`. The permanent correction
must not depend on abbreviated source names. No Google Sheet content change belongs in the bot PR.

### 4.2 Current repository baseline to revalidate

The latest mirror observed while preparing this pack was:

```text
cwatts6/K98-bot-mirror
main @ cca6d9cdb0dd15ba99403b89f03d1fede69f0e68
Mirror timestamp: 2026-09-01T14:09:23Z
```

Revalidate the current branch and files before using this baseline.

The original overflow remains present in current `stats_alerts/embeds/prekvk.py`. Its existing tests
replace `get_all_upcoming_events()` with an empty list, so they never construct the failing field,
and the fake channel does not emulate Discord payload validation.

### 4.3 Adjacent defects already identified

The same review found two Pre-KVK send-guard defects that remain present:

1. `prekvk_daily` is claimed in both:
   - `stats_alerts/embeds/prekvk.py`, after a successful fresh send; and
   - `stats_alerts/interface.py`, after the module returns `"sent"`.
2. The module's `run_blocking_in_thread()` call passes an empty tuple as an unintended positional
   argument to `claim_send()`, deliberately falls through a `TypeError`, and then retries through
   `asyncio.to_thread()`.

The atomic guard itself, `stats_alerts/guard.py::claim_send()`, is the existing canonical daily
slot writer. The fix must establish one clear owner, invoke it correctly, and retain the important
contract that a failed Discord send does not consume a successful-send record.

### 4.4 Existing embed-safety code is fragmented

Current code contains several different, partially overlapping approaches:

- `embed_utils.send_embed_safe()` truncates some field values and attaches large log-like fields,
  but does not provide a complete Discord embed contract.
- Its total-overflow branch can append replacement fields without removing the originals, risking
  duplicate fields and making its total/field-count bookkeeping unreliable.
- `stats_alerts/embeds/kvk.py` has a local `_truncate_and_log()` field helper.
- `embed_utils.LocalTimeToggleView` performs a separate manual 1,024-character trim.
- `ui/views/calendar.py` owns separate field-count, field-value, and total-size constants and
  builder-specific budgeting.
- Ark, MGE, GovernorOS and some other subsystems already contain useful output-shape tests, but
  coverage is inconsistent across the codebase.

This task must not add another competing limit helper without deciding canonical ownership and
migration boundaries first.

## 5. Scope

### In Scope

- Reproduce the exact `1,029`-character Pre-KVK incident with a deterministic regression fixture.
- Replace count-only Pre-KVK event rendering with character-aware, logical-block-safe output.
- Preserve event order, timestamps, current selection rules, current 12-visible-event cap, links,
  state handling, first-send ping behavior, edit behavior, and local-time control unless a separate
  change is explicitly approved.
- Handle a pathological single event safely without cutting Markdown or a Discord timestamp token.
- Respect the complete field-count and total-message embed budget, not only the individual field
  value limit.
- Consolidate `prekvk_daily` claim ownership and remove the malformed offload invocation.
- Audit and repair the existing shared embed-safety boundary rather than creating an unrelated
  sender framework.
- Complete a repository-wide functional audit of live Python embed builders and all send/edit/
  follow-up/DM paths carrying `embed=` or `embeds=`.
- Review dynamic data from Discord users, Google Sheets, SQL rows, configuration, filenames, logs,
  cached events, and generated lists for realistic maximum length/cardinality.
- Fix additional confirmed same-root-cause issues when they are behavior-preserving, low-risk, and
  fit within the operator-approved implementation set.
- Add focused tests for every changed runtime path and shared primitive.
- Produce a durable audit record:
  `docs/task_packs/archive/Discord Embed Payload Safety Audit Findings.md`.
- Update `docs/task_packs/README.md`, `README-DEV.md`, and
  `docs/reference/deferred_optimisations.md` only as required by the approved delivery and findings.
- Complete a bot Changes-only security review against the final implementation diff.

### Out of Scope

- SQL repository changes or a new SQL deployment.
- Editing or normalising the KVK Timeline Google Sheet as the application fix.
- Rewriting event names, player names, poll titles, or other authoritative source data to fit.
- Changing slash-command names, registration, permissions, visibility, or command counts.
- A general Discord UX redesign or converting every long result into pagination/export.
- Replacing image/card rendering systems.
- Auditing ordinary non-embed message content except where it shares the exact outbound call and
  could invalidate that embed delivery.
- Globally monkeypatching or wrapping discord.py internals.
- Routing every embed through `send_embed_safe()` when that would lose views, inline layout,
  attachments, edit semantics, multiple-embed semantics, or existing return contracts.
- A standard or deep Codex Security codebase scan. The requested wider audit is a functional
  payload-safety audit, not authorisation for repository-wide security discovery.
- Unrelated cleanup found during the audit; capture it through the correct deferred or security
  workflow instead.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | `use` | Required to map shared-helper ownership, affected renderers/senders, test boundaries, and the exact approved remediation set before code changes. |
| `k98-discord-command-feature` | `use` | The task changes Discord embeds, message send/edit behavior, a persistent local-time view payload, and user-visible stats alerts. It does not approve command-surface changes. |
| `k98-sql-validation` | `not applicable` | The KS4 prerequisite is complete and the planned change is bot-only. Confirm no SQL diff or data-contract change is introduced. |
| `k98-test-selection` | `use` | Required to combine selector output with risk-based coverage for shared helpers, stats alerts, event views, and audit-found modules. |
| `k98-deferred-optimisation-capture` | `use` | Required for valid non-security embed debt that needs pagination, export, product design, or a separate high-risk refactor. |
| `k98-pr-review` | `use` | Required before handoff because a shared Discord helper and multiple output paths may be touched. |
| `k98-promotion-check` | `use` | Required before production promotion; no SQL sequencing or command resync is expected. |
| `k98-security-review-routing` | `use` | Route the final bot implementation through a diff-focused Changes review with Deep off. Do not start a standard or deep codebase audit. |

### Security Review Decision

| Repository | Decision | Target | Expected setup / execution | Evidence |
|---|---|---|---|---|
| Bot | `Changes review` | Final approved bot working-tree diff based on `cca6d9cdb0dd15ba99403b89f03d1fede69f0e68`, plus PR-review follow-up range `4509b600..ac5c5e01` | `Changes + Deep Off` using `$codex-security:security-diff-scan` | Initial scan `dada5066-00ba-4c84-bec9-cd70b5e2d213` and follow-up scan `59865dd8-4628-4aa2-baba-3192ad5f5563` both completed with full coverage and no reportable findings. |
| SQL | `documented skip` | `C:\K98-bot-SQL-Server` — no task files | `Not applicable` | The DB prerequisite is complete. This task changes no schema, procedure, view, index, role, data access, migration, deployment, or persistence contract. Confirm no SQL working-tree diff before handoff. |

The functional all-embed inventory is part of normal engineering audit. It does not change the
security decision to `standard codebase audit` or `deep codebase audit`.

## 8. Mandatory Workflow

1. Read the task pack and required repository guidance.
2. Revalidate the current mirror head and the confirmed incident path.
3. Run the functional embed inventory and produce the initial findings matrix.
4. Use `k98-security-review-routing` to record the provisional bot Changes-review target.
5. Complete architecture/scope analysis:
   - canonical shared limit primitive;
   - Pre-KVK renderer boundary;
   - send-guard ownership;
   - exact additional `fix now` candidates;
   - explicit deferred candidates;
   - tests and documentation.
6. **Stop for operator approval before changing runtime code or tests.**
7. After approval, implement only the agreed file/remediation set.
8. Run focused and broad validation selected through `k98-test-selection`.
9. Update the audit findings record with final dispositions and evidence.
10. Run `k98-pr-review`.
11. Run the bot Changes-only security review against the final intended base/head with Deep off.
12. Create the mirror PR and leave production promotion/deployment for the normal separately
    approved workflow.

The operator may approve the audit, architecture target, and implementation plan together after
the first response. A materially wider implementation set requires a new approval checkpoint.

## 9. Audit Requirements

### 9.1 Runtime inventory

Inventory live Python runtime paths, excluding archive documents and generated artifacts. Use
searches as discovery seeds, then inspect call paths manually or with AST-aware tooling so
multi-line calls are not missed:

```powershell
rg -n --glob "*.py" "discord\.Embed|from discord import Embed|Embed\(" .
rg -n --glob "*.py" "\.add_field\(|\.set_field_at\(|\.insert_field_at\(" .
rg -n --glob "*.py" "\.set_footer\(|\.set_author\(" .
rg -n --glob "*.py" "embed=|embeds=|webhook|followup\.send|response\.send_message|message\.edit" .
rg -n --glob "*.py" "1024|2048|4096|6000|_EMBED_|FIELD_VALUE_MAX" .
rg -n --glob "*.py" "send_embed_safe|send_embed\(" .
python scripts/find_similar_helpers.py --min-score 0.85
```

Review at minimum:

- channel sends;
- direct messages;
- interaction initial responses and follow-ups;
- message edits;
- webhook sends if any;
- one or multiple embeds;
- persistent and ephemeral views that rebuild embeds;
- fallback embeds used when image/report generation fails;
- scheduled, reminder, import-status, admin, leadership and public-report posts.

### 9.2 Audit matrix

Record one row per live builder or builder family with:

| Column | Required content |
|---|---|
| Path / function | Exact runtime owner |
| Delivery path | Send, edit, follow-up, DM, webhook, fallback |
| Visibility / impact | Public, private, admin, scheduled, pinged |
| Dynamic sources | Discord, SQL, Sheets, config, cache, file/log, fixed copy |
| Cardinality | Bounded count or realistic unbounded list |
| Current controls | Truncation, chunking, pagination, attachment, none |
| Full limits covered | Title, description, fields, names, values, footer, author, aggregate, embed count |
| Test evidence | Exact test or gap |
| Worst-case result | Valid, silent truncation, omitted content, invalid payload, uncertain |
| Decision | Safe, fix now, defer, dead/unreachable with evidence |
| Notes | Preserve/rollback and follow-up detail |

### 9.3 Triage rules

Classify `fix now` when one or more applies:

- the current incident is reproducible;
- a live builder accepts variable external/user/database data with no enforceable bound;
- a current shared helper can itself emit an invalid or internally inconsistent payload;
- the same root cause is confirmed and the correction is behavior-preserving and PR-sized;
- tests currently claim safety without exercising the dynamic output.

Classify `defer` when correction requires:

- a product decision between truncation, pagination, export or multiple messages;
- a major command/view redesign;
- a separate persistence or SQL contract;
- high-risk migration of a large unrelated subsystem;
- work not necessary to prevent the current invalid-payload family.

Do not classify an untriaged vulnerability as ordinary deferred optimisation.

### 9.4 Initial confirmed findings to revalidate

The first audit response must explicitly confirm or revise:

1. Pre-KVK `Next 7 days` is count-bounded but not character-bounded.
2. The existing launch fixture renders at 1,029 characters with current formatting.
3. `tests/test_prekvk_embed.py` does not exercise the event field.
4. `prekvk_daily` has duplicate claim ownership.
5. The module's current offloaded `claim_send()` call is malformed.
6. `send_embed_safe()` is not a complete Discord embed validator.
7. Its aggregate-overflow path can append replacement fields without replacing originals.
8. Multiple local field-limit helpers/constants exist and need a canonical ownership decision.
9. Some subsystems already contain good output-shape tests that should be reused as patterns.

### 9.5 Audit output

Create:

```text
docs/task_packs/archive/Discord Embed Payload Safety Audit Findings.md
```

The document must contain:

- scope and commit reviewed;
- search method;
- complete live builder/delivery inventory;
- existing helper/constant map;
- confirmed findings and severity;
- `fix now`, `defer`, `safe`, and `not runtime` dispositions;
- files changed;
- tests added or relied upon;
- unresolved questions;
- final validation and security evidence.

Do not report the audit as complete if only `discord.Embed(` constructors were searched; outbound
delivery and mutation paths must also be traced.

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Low-level Discord limit contract | One pure, dependency-light canonical primitive, either in `embed_utils.py` or an approved `core/discord_embed_limits.py`; do not leave competing constants/helpers |
| Builder-specific overflow policy | The owning renderer/service chooses chunk, paginate, attach, omit-with-marker, or truncate-with-marker |
| Pre-KVK rendering | Pure helpers in or immediately beside `stats_alerts/embeds/prekvk.py`; send/edit orchestration remains thin |
| Shared operational sender | Preserve `embed_utils.send_embed_safe()` public API and make it delegate to the canonical validation/normalisation contract |
| Pre-KVK send guard | Exactly one owner around the successful fresh-send boundary |
| Commands and views | Remain interaction/rendering owners only; no new SQL or unrelated business logic |
| Audit tooling | Existing scripts plus a narrow new static audit script only if the first response proves recurring value and receives approval |
| Documentation | `docs/task_packs/` audit findings, task index/status, deferred items where needed |
| Tests | Existing subsystem files plus one focused shared-limit test file if that is the cleanest ownership |

Do not force all builders through `send_embed_safe()`. It is a dict-based status sender and cannot
universally preserve inline fields, existing embed objects, views, attachments, edits, or
multi-embed layouts. The reusable boundary should be the limit model/validator and safe
builder primitives, not one mandatory outbound function.

## 11. Likely Files

The first response must revalidate and narrow this list.

### Review

- `stats_alerts/embeds/prekvk.py`
- `stats_alerts/interface.py`
- `stats_alerts/guard.py`
- `stats_alerts/embeds/kvk.py`
- `embed_utils.py`
- `ui/views/calendar.py`
- `event_calendar/reminders.py`
- `ark/embeds.py`
- `ark/team_publish.py`
- `ark/reminders.py`
- `mge/mge_embed_manager.py`
- `mge/mge_content_renderer.py`
- `voting/survey_presentation.py`
- `voting/discord_presentation.py`
- `voting/dashboard_presentation.py`
- `targets_embed.py`
- `kvk/rendering/kvk_rankings_embed.py`
- `honor_rankings_view.py`
- `crystaltech_ui.py`
- live `commands/`, `ui/views/`, `event_calendar/`, `stats_alerts/`, `ark/`, `mge/`, `voting/`
  and other runtime files discovered by the inventory
- related tests under `tests/`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/README.md`

### Modify — expected core set

- `stats_alerts/embeds/prekvk.py`
- `stats_alerts/interface.py`
- `embed_utils.py` or the approved canonical helper owner
- `tests/test_prekvk_embed.py`
- `tests/test_embed_utils.py`
- `tests/test_stats_alerts_fighting_lifecycle.py`
- any additional confirmed-offender module and its focused test after approval
- `docs/task_packs/README.md`
- `README-DEV.md`
- `docs/reference/deferred_optimisations.md` only when structured deferrals are created

### Create — expected

- `docs/task_packs/archive/Discord Embed Payload Safety Audit Findings.md`
- `tests/test_discord_embed_limits.py` if a distinct shared primitive is approved
- `core/discord_embed_limits.py` only if the architecture review selects it as the canonical
  extraction rather than retaining ownership in `embed_utils.py`

No SQL file is expected.

## 12. Implementation Requirements

### 12.1 Canonical limit model

Provide one reusable contract that can inspect a single embed or a sequence and report actionable
violations with component paths and actual/allowed counts, for example:

```text
embeds[0].fields[10].value: 1029/1024
embeds[1].footer.text: 2110/2048
message.embed_text_total: 6124/6000
```

It must cover:

- number of embeds;
- title;
- description;
- field count;
- field names;
- field values;
- footer text;
- author name;
- combined text across all embeds.

Builder-level conservative soft limits may remain where they serve a documented UX purpose, but
hard limits must have one canonical source.

The validator must not silently decide every UX policy. Callers should make deliberate,
testable choices. Runtime send helpers must validate the final transformed payload before sending.

### 12.2 Repair `send_embed_safe()`

Preserve its public signature, boolean result, mention behavior, fallback behavior, and existing
large-log attachment contract.

At minimum:

- build the final field/attachment plan before constructing the embed;
- constrain field names and values;
- prevent more than 25 fields;
- include every actual final text component in aggregate accounting;
- replace a field when moving content to an attachment rather than appending a duplicate;
- validate the final payload before send;
- retain meaningful warning logs when content is truncated or attached;
- do not log full user content, full logs, secrets, or protected data;
- add exact-boundary and one-over-boundary tests;
- preserve current small-log and large-log behavior already under test.

If the audit proves that the helper's current aggregate-overflow attachment behavior cannot be
repaired compatibly in the same PR, stop and propose a narrower compatible correction plus a
structured follow-up. Do not leave a known path that can generate duplicate fields without an
explicit disposition.

### 12.3 Correct Pre-KVK event rendering

Extract pure formatting/chunking helpers so the incident can be tested without a Discord network
call.

Required behavior:

- retain complete event blocks whenever they fit;
- split only between events;
- use `🗓️ Next 7 days:` for the first field and a clear continuation name for later fields;
- preserve event order and the current first-12 visible event cap;
- preserve full normal event names, including `Megingjörð (Artifact)`;
- preserve complete `<t:...:R>` tokens and balanced Markdown;
- use an explicit compact/truncated-name fallback for a single pathological event that cannot fit;
- account for fields already present in the embed;
- account for the 6,000-character combined limit;
- if all selected events cannot fit after safe compaction, include a truthful
  `… N more events — see Timeline` marker and retain the Timeline link;
- emit a concise structured warning when compaction, continuation or omission is used;
- apply the exact same safe builder output to both fresh send and existing-message edit paths.

Do not silently change the event source, date window, type filter, sorting, 12-event visible cap,
or the `LocalTimeToggleView` event set. If the audit finds that the view currently exposes a
different number of events from the visible field, report it as a separate behavior decision.

### 12.4 Consolidate Pre-KVK guard ownership

Establish one owner for `prekvk_daily`.

Expected direction, subject to the first audit response:

- retain the guard checks and post-success claim in the Pre-KVK module because it owns edit versus
  fresh-send behavior;
- remove the duplicate interface claim;
- call `claim_send("prekvk_daily", max_per_day=1)` correctly through
  `run_blocking_in_thread()` without the unintended positional tuple or TypeError fallback;
- claim only after a successful fresh send;
- do not claim after an edit, skip, test-mode send, or Discord exception;
- preserve the current off-season mutual exclusion and daily check;
- preserve `prekvk_msg_id` save/clear behavior and `@everyone` first-send behavior;
- if a post-send claim unexpectedly returns `False`, log the outcome clearly without pretending the
  message was not sent.

Do not redesign the whole stats-alert guard transaction or singleton model in this task. Capture a
separate item if the audit proves a cross-process race that requires a reserve/commit/release
protocol.

### 12.5 Wider-audit remediation

For each approved `fix now` item:

- use the canonical limit model;
- preserve output meaning, visibility, permissions, controls, and delivery route;
- prefer chunking/pagination for meaningful lists;
- prefer attachment for log/export-like content;
- use explicit omission or truncation markers when information is removed;
- avoid cutting links, Markdown, mentions, custom emoji syntax, or Discord timestamps mid-token;
- add a focused worst-case output-shape test;
- document rollback and any unavoidable presentation difference.

Do not perform broad mechanical replacement across all embed builders.

### 12.6 Logging and diagnostics

For changed send paths, log enough to diagnose another invalid payload without reproducing or
logging sensitive content:

- builder/path name;
- field count;
- aggregate character count;
- maximum field length;
- chosen overflow action;
- number of items omitted or moved;
- Discord error code/component path when available.

Do not log full field values, private report data, player data, tokens, URLs containing secrets, or
attachments.

### 12.7 Command surface governance

This task changes neither top-level command count nor grouped subcommand count.

- Do not add, rename, move or retire commands.
- Preserve permissions, visibility, decorators, usage identity and command-cache behavior.
- Run command-registration validation as a regression gate; no canonical command-reference change
  is expected.

## 13. Refactor Decisions

Initial decisions to revalidate and complete during the audit:

| Issue | Decision | Reason |
|---|---|---|
| Pre-KVK count-only event cap | `fix now` | Confirmed production invalid payload with a deterministic normal-data fixture |
| Missing Pre-KVK event-field regression coverage | `fix now` | Existing tests never construct the failed field |
| Duplicate `prekvk_daily` claim ownership | `fix now` | Same touched path, unclear responsibility and unnecessary duplicate I/O/logging |
| Malformed offloaded guard invocation | `fix now` | Known current defect in the same post-send path |
| Incomplete shared embed-limit model | `fix now` | Wider audit and repeatable tests need one reliable contract |
| `send_embed_safe()` duplicate-field aggregate-overflow behavior | `fix now`, subject to compatibility audit | A shared helper must not create a second invalid shape while attempting recovery |
| Local KVK/calendar/local-time limit helpers | `audit; consolidate where low-risk, otherwise defer` | Avoid a sweeping behavior change without output-by-output evidence |
| Embed outputs requiring new pagination/export product decisions | `defer` | Separate UX scope and operator decision |
| Google Sheet name shortening | `not applicable` | Source data must not be the safety control |
| SQL or KS4 change | `not applicable` | Prerequisite complete; no SQL dependency expected |
| Global discord.py send monkeypatch | `do not implement` | Too broad and likely to alter unrelated send/edit/view semantics |

Every deferred item must use the structure in
`docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 14. Testing Requirements

Use `k98-test-selection` and `scripts/select_tests.py`; the commands below are the expected
risk-based baseline, not a substitute for selector output.

### 14.1 Pre-KVK regression and behavior tests

Extend `tests/test_prekvk_embed.py` to cover:

1. The exact 12-event KVK 16 fixture reproduces the old `1,029`-character input.
2. The corrected embed sends successfully through the fake channel.
3. Every field name/value is within the hard limit.
4. The embed has no more than 25 fields and aggregate text is no more than 6,000.
5. All 12 normal event names and complete timestamps remain present and ordered.
6. Continuation fields split only between event blocks.
7. An exact-boundary event block remains unchanged.
8. A one-character-over and a very long single event are handled without broken Markdown or
   timestamp syntax.
9. More than 12 qualifying events preserves the current visible cap and does not silently change
   the local-time view contract.
10. Empty/no-upcoming-event behavior remains unchanged.
11. Existing-message edit uses the same safe output and does not create a new message.
12. Discord send failure does not save a message ID or claim the daily slot.
13. First fresh send retains the current `@everyone` behavior; test mode does not ping.
14. The source names can be full length; the test must not rely on the temporary Sheet
    abbreviation.

### 14.2 Guard ownership tests

Update or add focused stats-alert tests to prove:

- exactly one `prekvk_daily` claim after one successful fresh non-test send;
- zero claim on edit;
- zero claim on `PreKvkSkip`;
- zero claim on Discord failure;
- zero claim in test mode;
- no TypeError fallback is part of the normal path;
- routing still changes from Pre-KVK to KVK only when fighting opens.

### 14.3 Shared contract tests

Add exact-limit and one-over tests for:

- 10 versus 11 embeds;
- title 256/257;
- description 4,096/4,097;
- 25/26 fields;
- field name 256/257;
- field value 1,024/1,025;
- footer 2,048/2,049;
- author 256/257;
- aggregate 6,000/6,001 across one and multiple embeds;
- violation component paths and actual/limit values.

For `send_embed_safe()` also prove:

- existing small log remains inline;
- existing large log is attached;
- oversized non-log fields are handled with a marker;
- field names are safe;
- no duplicate field is produced during aggregate recovery;
- final field count and aggregate size are valid;
- fallback and boolean result behavior remains unchanged.

### 14.4 Audit-found path tests

For each additional approved runtime correction, add or extend a focused worst-case output test.
Reuse existing patterns in:

- `tests/test_kvk_embed.py`
- `tests/test_ark_embeds.py`
- `tests/test_mge_embed_field_limits.py`
- `tests/test_mge_embed_manager.py`
- `tests/test_player_self_service_stats_renderer.py`
- `tests/test_leadership_player_review.py`

Do not add superficial snapshot tests that merely mirror implementation strings.

### 14.5 Test-category decisions

| Category | Decision |
|---|---|
| Happy path | Required |
| Negative path | Required for one-over limits, malformed/pathological content and send failure |
| Regression | Required using the exact incident fixture |
| Permission boundary | No permission change; retain existing tests and confirm visibility/ping behavior |
| Restart/persistence | No persistence schema change; verify `prekvk_msg_id` edit/send behavior remains safe |
| Cache safety | No cache mutation change; use realistic cached event dictionaries as deterministic input |
| Format/output shape | Required for every changed builder |
| Logging | Assert key warning/outcome logs without asserting sensitive content |

### 14.6 Expected commands

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_prekvk_embed.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_stats_alerts_fighting_lifecycle.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_embed_utils.py tests\test_discord_embed_limits.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_embed.py tests\test_ark_embeds.py tests\test_mge_embed_field_limits.py tests\test_mge_embed_manager.py tests\test_player_self_service_stats_renderer.py tests\test_leadership_player_review.py
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

If `tests/test_discord_embed_limits.py` is not created because ownership remains in
`tests/test_embed_utils.py`, adjust the command and explain the decision. Record any unrelated
failures without expanding scope.

### 14.7 Manual smoke

After reviewed production promotion and bot restart:

1. Use the existing test/admin stats-alert route first so no production `@everyone` ping occurs.
2. Confirm the Pre-KVK embed renders the full current event names, continuation fields where
   needed, links and local-time control.
3. Confirm no Discord `50035 Invalid Form Body` is logged.
4. Exercise a normal fresh-send path at the approved operational time.
5. Confirm one and only one `prekvk_daily` row is recorded for the fresh send.
6. Trigger or observe the same-day edit path and confirm no additional guard row and no duplicate
   message.
7. Confirm Kingdom Summary, KVK and off-season routes remain unchanged.
8. Inspect logs for concise payload metrics and no sensitive field content.

No SQL deployment or command resync is expected.

#### Completed operator smoke — 2026-09-02

The operator ran `/ops test_embed` against KVK 16 in `DRAFT`. Discord accepted a final Pre-KVK
payload with `fields=13`, `chars=1847`, `max_field_value=530`, `event_fields=1`,
`compacted_events=0`, and `omitted_events=0`. The bot edited existing message
`1544617668999381044` in channel `1209532242506813540`; the persisted `prekvk_msg_id` matched,
the observed guard count was `1`, and no duplicate or `50035` rejection occurred.

This was an edit-path smoke. `/ops test_embed` runs with `is_test=True`, bypasses the daily guards,
does not ping, and does not claim. The valid same-day message ID selected the edit before guard
evaluation. Therefore the evidence does not independently prove a scheduled fresh-send ping or
post-success claim; those remain covered automatically and are a natural operational observation.

### 14.8 Rollback

Revert the bot implementation commit/PR and redeploy through the normal production workflow.

- No SQL rollback is required.
- No data migration is required.
- No cache schema rollback is required.
- The KVK Timeline Sheet remains independently editable and is not part of rollback.
- If a temporary shortened event name is later restored, the restored name must remain safe under
  both the corrected and rolled-back operational plan; therefore restore source copy only after the
  proper fix is deployed and accepted.

## 15. Acceptance Criteria

- [x] The current branch and incident path were revalidated before implementation.
- [x] The exact 12-event fixture proves the old payload was 1,029 characters.
- [x] Pre-KVK no longer depends on shortened source names.
- [x] Normal event blocks are preserved in order and split only at logical boundaries.
- [x] Pathological single items are handled without broken Markdown, timestamp, link, mention, or
      custom-emoji syntax.
- [x] Every changed payload satisfies title, description, field-count, field-name, field-value,
      footer, author, embed-count and 6,000-character aggregate limits.
- [x] The final payload is validated before both send and edit.
- [x] `prekvk_daily` has exactly one owner and one normal post-success claim.
- [x] Failed sends, successful edits, skips and test-mode sends do not claim the fresh-send slot;
      a successful fresh-send fallback after an edit failure claims exactly once.
- [x] The malformed empty-tuple offload path is removed.
- [x] `send_embed_safe()` cannot append duplicate replacement fields during aggregate recovery.
- [x] Existing small-log, large-log, fallback and boolean-result contracts are preserved.
- [x] The functional live embed inventory is complete and stored in the audit findings document.
- [x] Every live dynamic builder is classified as safe, fixed, deferred, or non-runtime with
      evidence.
- [x] Additional same-root-cause fixes were limited to the operator-approved set.
- [x] Larger UX/refactor findings were captured structurally rather than silently expanded.
- [x] No SQL, Google Sheet, command registration, permission or visibility contract changed.
- [x] Focused tests, selectors, validators, pre-commit and full pytest passed or documented.
- [x] The final bot diff received a Changes-only security review with Deep off.
- [x] Operator smoke confirmed a valid payload, same-day edit, matching message state, and no
      duplicate post.
- [ ] A scheduled fresh-send ping and post-success claim remain a natural operational observation;
      `/ops test_embed` bypasses daily guards and did not independently exercise that path.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. Helpers Reused
7. Functional Embed Audit Results
8. Refactor Findings
9. Test Plan and Results
10. Security Review Decision and Evidence
11. Deployment Steps and Smoke Evidence
12. Rollback
13. Deferred Optimisations

Include the final audit matrix or link to
`docs/task_packs/archive/Discord Embed Payload Safety Audit Findings.md`.

## 17. PR Summary Template

```md
## Summary

- Fix the confirmed Pre-KVK Discord embed overflow without abbreviating source event data.
- Establish one tested Discord embed-limit contract and repair the existing shared sender path.
- Consolidate Pre-KVK daily-send claim ownership.
- Complete the approved functional embed audit and remediate the agreed same-root-cause findings.

## Changes

- [List the exact Pre-KVK rendering changes.]
- [List the canonical helper/validator changes.]
- [List guard ownership changes.]
- [List additional approved audit-found fixes.]
- [Link the audit findings record.]

## Tests

- [List focused pytest commands and results.]
- [List validators, selector, pre-commit and full-suite result.]
- [Record manual smoke result or pending status.]

## Security Review

- Decision: `Changes review`
- Repository / target: `K98-bot-mirror final approved base..head`
- Expected setup / execution: `Changes + Deep Off`
- Evidence: `[final scan result or pending before handoff]`
- SQL decision: `documented skip — no SQL files or contracts changed`

## Deferred Optimisations

- [None, or list structured non-security follow-ups from the audit.]

## Risk / Rollback

- Risk: Shared embed-limit code can affect multiple delivery paths; mitigation is bounded caller
  adoption, exact-boundary tests, focused subsystem tests, full regression and production smoke.
- Rollback: Revert the bot PR and redeploy. No SQL, data or cache migration rollback is required.
```
