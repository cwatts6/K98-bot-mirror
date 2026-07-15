# Codex Task Pack - Player Self-Service Command Centre v2 Phase 5D Premium Reminders Summary Card

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 5D Premium Reminders Summary Card`
- Date: `2026-07-14`
- Owner/context: Follow-on from GovernorOS v2 Phase 5C Accounts, using the approved Phase 5C-5G premium summary-card contract.
- Task type: `read-only reminder projection | premium Reminders renderer | Discord interaction preservation`
- One-pass approved: `Yes - after the prerequisite gates below and within the locked product, data, visual, interaction, and compatibility contract`
- Product/content scope approved: `Yes`
- Runtime implementation approved: `Yes - prerequisite gates satisfied on 2026-07-14`
- Status: `operator functional smoke passed - visual refinement re-smoke pending`
- Planned runtime backdrop: `assets/me/cards/me_reminders.png`
- Approved production canvas: `1702 × 924 PNG`
- Stable output filename: `me_reminders_<discord_user_id>.png`

The product workshop is complete. Do not reopen the core hierarchy, status model, summary structure,
Manage journey, or no-Change-Governor decision unless repository evidence reveals a genuine blocker.

Artwork generation and mock-overlay review may proceed before the Phase 5C operator gate. Runtime
Phase 5D implementation must not begin until both prerequisite gates are satisfied.

## 2. Prerequisite Gates

Before implementation begins, record both of the following:

1. Phase 5C Accounts operator Discord smoke has passed and the Phase 5C slice is accepted for
   promotion under its own task pack.
2. The new clean Reminders backdrop has passed the Phase 5D background-generation task and is present
   at exactly:

```text
assets/me/cards/me_reminders.png
1702 × 924 PNG
```

Do not load a 2x source master at runtime. If the runtime asset is missing, corrupted, unexpectedly
transparent, or not exactly `1702 × 924`, stop and report the asset-specific blocker.

## 3. Required Reading

Read before implementation:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5D Premium Reminders Summary Card.md`
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card.md`
- the completed Phase 5B Inventory visual-alignment task pack in the archive
- the completed Phase 4 Premium Governor Dashboard Renderer task pack in the archive
- the completed guided account/reminder management workflow task pack in the archive
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- the GovernorOS Visual Design Bible
- `docs/task_packs/Task - Generate GovernorOS Reminders Centre Heralds Watch Backdrop v1.md`

Use the repository's current equivalents where filenames have moved.

Recommended skills/workflows:

- `k98-architecture-scope`
- `k98-discord-command-feature`
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review`
- `codex-security:security-scan` when available

## 4. Context And Approved Direction

`/me reminders` is already a correct, private, author-gated settings page. It confirms the player's
KVK and Calendar reminder choices by event type and alert time. Its existing guided `Manage` child
journey lets the player add, remove, or update choices and switch between KVK and Calendar. That
child journey works and is not being redesigned.

The current summary is useful but behaves mainly as a settings receipt. It repeats `ON`, gives every
setting similar visual weight, exposes implementation-facing values such as raw event keys, and does
not answer the most valuable operational question: **what alert will the player receive next?**

Phase 5D upgrades the host summary card so it answers, in order:

1. Are my reminder systems configured and usable?
2. What alert is due next, when an authoritative read-only projection is available?
3. Which event types and alert windows are covered by KVK and Calendar?
4. Is there one concrete item I should review?
5. How do I manage the choices?

The approved direction is deliberately narrow. It adds a premium presentation, friendly
normalisation, deterministic summary intelligence, and an optional read-only projection of existing
scheduler data. It does **not** change reminder behaviour.

## 5. Objectives

Deliver all of the following in one Phase 5D implementation:

1. A premium standalone `/me reminders` card using the approved `1702 × 924` backdrop and the locked
   hierarchy below.
2. An earned top-level `ACTIVE`, `REVIEW`, or `OFF` state based on the existing persisted settings.
3. A `NEXT SCHEDULED ALERT` hero when the existing reminder/event services can expose the exact next
   future alert through a read-only projection that shares scheduler semantics.
4. A truthful `REMINDER COVERAGE` or no-upcoming/unavailable hero when a next alert cannot be shown.
5. Compact, friendly KVK and Calendar summaries with player-facing event labels, canonical alert-time
   labels, counts, and coverage ranges.
6. One deterministic `REMINDER INSIGHT` chosen from the approved priority rules.
7. The existing guided `Manage` journey, KVK/Calendar toggle, persistence, restart behaviour, author
   gating, and reminder delivery behaviour preserved unchanged.
8. Standalone private attachment delivery, same-payload fallback, deliberate attachment replacement,
   off-event-loop rendering, and complete stream cleanup under the accepted GovernorOS contract.

## 6. Page Semantics And Governor Rule

- `/me reminders` represents the invoking Discord user's reminder settings.
- It is a Discord-user-level page, not a selected-governor page.
- It must not be filtered by an optional dashboard governor.
- It remains private/ephemeral and author-gated.
- Do not add `Change Governor`, including for users with multiple or more than 25 linked governors.
- An optional `dashboard_governor_id` may be retained only as return context so `Dashboard` can
  reopen the previously selected governor after a fresh access check.
- Direct `/me reminders` entry has no implicit governor context. Returning to Dashboard uses the
  existing no/one/multiple-governor journey.
- KVK versus Calendar switching remains inside the existing `Manage` child flow; do not add a second
  host-page toggle or separate host actions.
- The invoking Discord display name and fixed Kingdom 1198 context may be shown. Do not present one
  linked governor as though the page were scoped to that governor.
- The invoking Discord user's avatar uses the established circular `/me` header treatment, with the
  existing safe no-avatar fallback when Discord avatar bytes are unavailable.

## 7. Locked Main Reminders Card

### 7.1 Approved hierarchy

The populated card follows this hierarchy:

```text
[avatar] REMINDER CENTRE                             ACTIVE
         <Discord display name> (1198)     2 of 2 systems enabled

NEXT SCHEDULED ALERT
<event name>
<KVK or Calendar> • <alert stage> • <absolute alert time UTC>
Event starts <absolute time UTC>

KVK REMINDERS                             CALENDAR REMINDERS
ON • 1 event • 4 alert times             ON • 11 events • 5 alert times
Altars                                   20 GH • Ark of Osiris •
                                          Armament Reveal • +8 more
24h • 12h • 4h • At start               7d • 3d • 24h • 1h • At start
Coverage: 24h → start                    Coverage: 7d → start

REMINDER INSIGHT
<one deterministic actionable or reassuring sentence>

Manage reminders
Choose KVK and calendar events and when each alert is sent.

Scheduled times shown in UTC             Refreshed <DD Mon YYYY HH:MM UTC>
```

Every value is dynamic. The examples above are layout examples only and must never be used as dummy
runtime data.

### 7.2 Header and identity

Render:

- `REMINDER CENTRE`;
- the earned state pill: `ACTIVE`, `REVIEW`, or `OFF`;
- the invoking Discord display name with fixed Kingdom 1198 context;
- one concise supporting line describing system enablement or the review condition.

The display name must not append a second `(1198)` when Discord's current display name already ends
with that suffix. Right-align the supporting line to the same right edge as the earned state pill.

Use singular/plural grammar correctly.

Do not render a governor ID, account role, selected-governor name, or Change Governor control.

### 7.3 Top-level state contract

#### `ACTIVE`

Use `ACTIVE` when:

- at least one of KVK or Calendar reminders is enabled; and
- every enabled reminder system has at least one current, valid selected event type; and
- every enabled reminder system has at least one current, valid selected alert time.

A deliberately disabled system does not make the page `REVIEW`.

Recommended supporting copy:

```text
2 of 2 systems enabled
1 of 2 systems enabled
```

#### `REVIEW`

Use `REVIEW` when at least one enabled reminder system cannot produce reminders from its current
configuration, including:

- no valid event types selected;
- no valid alert times selected;
- a saved event/time selection is no longer recognised or supported and leaves the enabled system
  incomplete;
- another existing configuration condition already understood by the scheduler means the enabled
  system cannot dispatch.

Do not use `REVIEW` merely because:

- a system is intentionally off;
- no relevant event is currently scheduled;
- all future warning windows for one occurrence have passed;
- the external event source is temporarily unavailable;
- the player did not select the same settings as other players.

Recommended supporting copy:

```text
KVK needs an alert time
Calendar needs an event
2 settings need review
```

Use one specific issue when possible; otherwise use a count. Keep derivation deterministic.

#### `OFF`

Use `OFF` only when both KVK and Calendar reminder systems are disabled.

Supporting copy:

```text
All reminder systems are off
```

Saved inactive choices may still be summarised below. Do not erase or imply that those choices have
been deleted.

### 7.4 Hero contract

The hero is a discriminated presentation, not a fabricated value. Support these variants:

```text
NextScheduledAlertHero
NoUpcomingAlertHero
ReminderCoverageHero
ScheduleUnavailableHero
```

#### A. `NEXT SCHEDULED ALERT`

Use only when an authoritative read-only projection can identify a future alert that matches the
existing scheduler's real eligibility and timing rules.

Render:

```text
NEXT SCHEDULED ALERT
<player-facing event label>
<KVK or Calendar> • <canonical lead-time label> • <absolute alert time UTC>
Event starts <absolute event-start time UTC>
```

Rules:

- choose the future alert with the earliest `alert_at_utc` across both enabled systems;
- use the current scheduler's own future/eligible semantics rather than a parallel approximation;
- use a deterministic tie break after alert time, such as existing system/event ordering and event
  occurrence identity;
- show absolute date/time, never a static countdown such as `in 1h 23m`;
- include the year when the event is outside the generated card's current UTC year;
- `At start` means `alert_at_utc == event_start_at_utc` under the existing scheduler contract;
- do not imply delivery success or guarantee a DM beyond what the existing reminder system already
  guarantees.

#### B. `NO UPCOMING ALERT`

Use when the authoritative projection is healthy but there is no future alert candidate for the
current selections.

Approved wording examples:

```text
NO UPCOMING ALERT
No upcoming selected alerts are currently scheduled.
```

```text
NO UPCOMING ALERT
No alert remains before the next selected event.
```

Use the more specific second form only when the existing event projection can prove that a selected
occurrence exists and every selected warning time has already passed.

#### C. `REMINDER COVERAGE`

Use as the strict no-new-data fallback when the existing codebase does not expose an authoritative
read-only next-alert projection without introducing a parallel scheduler, new event source, new
persistence, or changed reminder semantics.

Example:

```text
REMINDER COVERAGE
KVK: 24h to event start
Calendar: 7d to event start
12 event types • 9 alert times
```

This fallback is an approved implementation outcome. Record the unavailable next-alert projection
as a deferred opportunity; do not duplicate scheduler logic merely to populate the hero.

#### D. `SCHEDULE UNAVAILABLE`

Use when the projection/event source normally exists but is temporarily unavailable for this
request.

Approved wording:

```text
SCHEDULE UNAVAILABLE
Upcoming alert preview is temporarily unavailable.
Your saved choices are shown below.
```

Do not change the top-level configuration state solely because this read failed. Preserve the
same-payload fallback and avoid a second fetch.

### 7.5 KVK and Calendar summary contract

Render two balanced system summaries:

```text
KVK REMINDERS
CALENDAR REMINDERS
```

Each summary contains, in order:

1. state/count line;
2. player-facing event list;
3. canonical selected alert-time list;
4. one coverage line.

#### State/count line

Enabled and complete:

```text
ON • 1 event • 4 alert times
ON • 11 events • 5 alert times
```

Disabled with saved choices:

```text
OFF • 1 saved event • 4 saved alert times
OFF • 11 saved events • 5 saved alert times
```

Enabled but incomplete:

```text
REVIEW • No events selected
REVIEW • No alert times selected
```

Disabled with no saved choices:

```text
OFF • No saved choices
```

Use genuine counts after current catalog normalisation. Do not count duplicate persisted keys twice.

#### Event labels

- Never display raw identifiers such as `armament_reveal`.
- Reuse the authoritative existing player-facing label map used by the Manage journey or event
  catalog.
- Preserve the authoritative existing event order; do not alphabetically reshuffle the summary.
- Show no more than three player-facing event names in the Calendar summary by default, followed by
  `+ <N> more` when required.
- KVK may show the full list when it fits within the same fixed bounds; the renderer must still use a
  deterministic maximum and fitted text.
- For a saved key no longer present in the current catalog, do not expose the key. Render a restrained
  `Unavailable event` indicator, include it in the review issue, and let Manage remain the place to
  correct the choice.

Example:

```text
20 GH • Ark of Osiris • Armament Reveal • +8 more
```

#### Alert-time labels

- Reuse the authoritative lead-time order from the Manage/scheduler contract.
- Normalise implementation synonyms such as `now` and `start` to the one player-facing label:
  `At start`.
- Use compact canonical labels such as `7d`, `3d`, `24h`, `12h`, `4h`, and `1h` only where those
  options genuinely exist.
- Never display an unknown raw lead-time key. Render `Unavailable alert time` and mark the enabled
  system for review when appropriate.

Example:

```text
7d • 3d • 24h • 1h • At start
```

#### Coverage label

Derive a concise range from the genuine selected alert times:

```text
Coverage: 24h → start
Coverage: 7d → 1h before start
Coverage: At start
Saved coverage: 7d → start
No active coverage
```

Rules:

- the first value is the longest selected lead time;
- the second value is the latest selected alert point before or at event start;
- use `start`, not `now`, in the coverage line;
- use `Saved coverage` when the system is off but choices remain;
- do not imply continuous coverage between selected points; this is a compact summary of the span of
  configured alert moments.

### 7.6 Reminder Insight contract

Render exactly one short deterministic insight, normally one sentence and no more than two clauses.

Priority is fixed:

1. configuration that cannot produce alerts;
2. a proven upcoming-event coverage gap;
3. one or both systems being disabled;
4. a neutral coverage characteristic worth reviewing;
5. a positive coverage summary.

#### Priority 1 - configuration issue

Examples:

```text
KVK reminders are enabled, but no alert times are selected.
Calendar reminders are enabled, but no event types are selected.
KVK reminders need an event and an alert time.
1 saved Calendar event is no longer available; review it in Manage.
```

#### Priority 2 - coverage gap

Use only when the existing event projection proves the condition:

```text
Altars is upcoming, but every selected KVK warning time has passed.
```

Do not treat this as a broken configuration when the player's settings are otherwise valid.

#### Priority 3 - disabled system

Examples:

```text
Calendar reminders are off; only KVK alerts will be sent.
KVK reminders are off; only Calendar alerts will be sent.
All reminders are off; use Manage to choose what you want to receive.
```

#### Priority 4 - neutral coverage characteristic

Use a factual observation about the player's selected lead-time span when it may be useful to review,
without calling a valid personal choice an error.

Examples:

```text
KVK coverage ends 4 hours before the event; no start-time alert is selected.
Calendar coverage begins 24 hours before an event and includes an alert at start.
```

Do not infer continuous coverage between selected alert moments.

#### Priority 5 - positive coverage

Examples:

```text
Both systems are active; coverage begins 7 days before event start.
12 event types are selected across both active reminder systems.
```

Rules for every insight:

- do not infer a favourite event;
- do not call a common choice a recommendation;
- do not compare the player with other players;
- do not claim that a reminder was or will be delivered unless existing delivery data proves it;
- do not use missing values as zero;
- use stable tie and ordering rules;
- omit a second clause when it adds no useful information.

### 7.7 Action explanation and footer

Render this image copy:

```text
Manage reminders
Choose KVK and calendar events and when each alert is sent.
```

The interactive control remains a real Discord component outside the PNG. Do not paint a fake
button into the image.

Render:

```text
Scheduled times shown in UTC             Refreshed <DD Mon YYYY HH:MM UTC>
```

`Refreshed` is the card-generation time, not a reminder delivery time or event-source timestamp.

Use UTC throughout Phase 5D. Do not add user-local timezone presentation unless a separately approved
contract explicitly identifies an authoritative existing timezone source and formatting policy.

## 8. Approved Backdrop Geometry

The renderer must compose around the approved `1702 × 924` asset and preserve these content zones:

| Zone | Coordinates |
|---|---|
| Outer architectural detail lanes | `x 0–72` and `x 1630–1702` |
| Header and identity | `x 92–1610`, `y 48–214` |
| Next Alert / Coverage hero | `x 92–1610`, `y 226–382` |
| Architectural transition | `y 386–410` |
| KVK summary | `x 92–840`, `y 414–650` |
| Calendar summary | `x 862–1610`, `y 414–650` |
| Inter-column gap | `x 840–862`, `y 414–650` |
| Reminder Insight | `x 92–1610`, `y 664–752` |
| Manage explanation | `x 92–1610`, `y 766–848` |
| Footer | `x 92–1610`, `y 858–920` |

The renderer may add restrained translucent treatment under content in keeping with existing
GovernorOS cards, but it must not rely on large opaque rescue panels. Preserve the backdrop's one-room
continuity and do not introduce a hard KVK/Calendar split that resembles two unrelated applications.

## 9. Data And Service Contract

### 9.1 Approved scope

Phase 5D approves a narrow read-only service/payload expansion for:

- top-level state derivation;
- friendly event/time normalisation;
- count and coverage summaries;
- deterministic insight selection;
- an optional authoritative next-alert/upcoming-alert projection from existing reminder and event
  services.

No SQL schema, table, view, index, new scheduler, new event source, new lead time, new DM behaviour,
new calendar behaviour, new persistence, or new reminder mutation is approved.

If an existing SQL-backed store is already used by reminder settings, it may continue to be read and
written only through the existing service/DAL boundaries and existing Manage mutations. Phase 5D
must not alter its schema or persistence semantics.

### 9.2 Recommended typed models

Prefer cohesive service-level models rather than passing renderer-specific dictionaries:

```text
RemindersSummaryPayload
- viewer_discord_id
- display_name
- kingdom_id
- generated_at_utc
- state: ACTIVE | REVIEW | OFF
- state_supporting_text
- kvk: ReminderSystemSummary
- calendar: ReminderSystemSummary
- hero: ReminderHero
- insight
- warnings / missing_fields

ReminderSystemSummary
- system: KVK | CALENDAR
- enabled
- completeness: COMPLETE | MISSING_EVENTS | MISSING_TIMES | MISSING_BOTH | UNAVAILABLE_SELECTION
- selected_event_keys
- selected_event_labels
- selected_event_count
- hidden_event_count
- unavailable_event_count
- selected_time_keys
- selected_time_labels
- selected_time_count
- unavailable_time_count
- includes_start
- longest_lead_time
- latest_alert_point
- coverage_label

NextScheduledReminderAlert
- system
- event_key or stable internal event identity
- event_label
- alert_at_utc
- event_start_at_utc
- lead_time_key
- lead_time_label
- occurrence_identity

ReminderHero
- kind: NEXT_ALERT | NO_UPCOMING | COVERAGE | UNAVAILABLE
- next_alert, optional
- headline
- primary_line
- secondary_line, optional
```

Names may follow repository conventions, but the responsibility split must remain equivalent.

### 9.3 Source direction

| UI/data field | Authoritative source direction |
|---|---|
| KVK enabled state | Existing persisted KVK reminder setting/service |
| Calendar enabled state | Existing persisted Calendar reminder setting/service |
| Selected event keys and order | Existing Manage/event-catalog contract |
| Player-facing event labels | Existing event label map/catalog used by the product |
| Selected alert-time keys and order | Existing Manage/scheduler lead-time contract |
| `At start` normalisation | Existing `now`/`start` semantics, normalised only in presentation |
| Next alert candidate | Existing reminder scheduling/event projection semantics, read-only |
| Event start time | Existing authoritative KVK/Calendar occurrence source already used by reminders |
| Card generated time | Current UTC clock injected through existing/testable time boundary |

Do not add a second event catalogue or copy an event-label dictionary into the renderer when an
existing authoritative source can be reused or extracted cleanly.

### 9.4 Authoritative next-alert projection rule

The card must not independently recreate reminder dispatch rules in a way that can drift from the
scheduler.

Preferred implementation order:

1. Reuse an existing service that already produces eligible reminder occurrences.
2. Extract a narrow pure/read-only projection helper from the scheduler's existing domain logic,
   keeping dispatch side effects separate.
3. If neither is possible without broad redesign, use the approved `REMINDER COVERAGE` hero and
   record the next-alert projection as deferred.

The projection must:

- consume the same enabled state, selected events, selected lead times, occurrence times, and
  eligibility rules as dispatch;
- return deterministic candidates without creating jobs, sending DMs, mutating last-run state, or
  marking anything delivered;
- filter/choose future alerts using an injected UTC clock;
- avoid per-event or per-selection N+1 database/service calls;
- degrade safely when one event source is unavailable;
- preserve exact UTC datetimes in the payload and format only in the renderer.

### 9.5 Assembly requirements

- Resolve the invoking user's current settings at request time through the existing service.
- Build both system summaries in one cohesive service call where practical.
- Keep exact raw keys internal; renderer receives friendly labels plus safe unavailable-selection
  indicators.
- Deduplicate duplicate persisted event/time keys for counts and presentation without changing the
  stored choices in Phase 5D.
- Preserve unknown/unavailable selections in warnings so Manage can be used to correct them.
- Use set-based/bulk event occurrence retrieval where the existing architecture supports it.
- Commands and views remain thin; no direct SQL or scheduler logic in Discord callbacks or renderers.
- No second data fetch is permitted merely because rendering, file creation, message editing, or
  delivery fails.

## 10. Existing Manage Journey - Preserve Exactly

The existing private guided Manage flow remains the source of truth for reminder mutation.

Preserve:

- entry from the host Reminders page;
- KVK versus Calendar toggle/switch;
- current event selections;
- current alert-time selections;
- add, remove, update, confirm, save, cancel, and back behaviour as currently implemented;
- current validation and revalidation immediately before persistence;
- current author gating;
- current timeout, stale, forged, foreign, duplicate, and concurrent handling;
- current restart/persistence behaviour;
- current DM scheduling and delivery behaviour;
- current calendar/event-source behaviour;
- current host-page refresh after a successful change.

Phase 5D may adapt the successful host refresh so it rebuilds the new summary payload/card. It must
not redesign the child flow, add recommendation presets, alter default choices, or change how
reminders are scheduled.

When a mutation succeeds, the refreshed host card must reflect the new state, hero, summaries, and
insight from a fresh authoritative payload. Render/fallback failure after that refresh must not repeat
the mutation.

## 11. Main Reminders Component Rows

Retain the accepted global navigation and existing Manage action as real Discord components.

Expected rows:

```text
Row 0: Accounts (blue) | Reminders (blue, disabled) | Preferences (blue)
Row 1: Dashboard | Exports
Row 2: Manage
```

If the current established component label is `Manage Reminders`, retain that exact existing label
instead; do not rename callbacks or redesign the journey merely for copy consistency.

Rules:

- the active `Reminders` navigation button is disabled;
- no Change Governor appears;
- no separate KVK or Calendar host button appears;
- disabled states, timeout handling, and author gating remain consistent with the other premium
  summary pages;
- buttons are never painted into the PNG.

## 12. Renderer And Delivery Contract

### 12.1 Main card

- Output: exactly `1702 × 924`.
- Runtime backdrop: `assets/me/cards/me_reminders.png`.
- Stable filename: `me_reminders_<discord_user_id>.png`.
- Successful output: standalone private attachment, not an embed-wrapped image.
- Fallback: concise private Reminders embed built from the same already-authorized
  `RemindersSummaryPayload`.
- Use the invoking author's already-authorized Discord avatar bytes and the shared circular `/me`
  treatment; unreadable or unavailable bytes fall back safely to the no-avatar header.

### 12.2 Renderer requirements

- Render off the event loop.
- Use deterministic Pillow output.
- Reuse `core.visual_text` and existing glyph/grapheme-safe fitting helpers where appropriate.
- Fit long/Unicode Discord names and event labels within fixed bounds.
- Use the approved event-list maximum and `+ <N> more` overflow.
- Preserve clear visual distinction between `ACTIVE`, `REVIEW`, and `OFF` without depending on colour
  alone.
- Use honest `—`, `No events selected`, `No alert times selected`, `Unavailable event`, and
  `Schedule preview unavailable` treatments.
- Format all schedule times in UTC with an explicit `UTC` suffix.
- Do not create a broad new visual-card framework or import renderer-private helpers across unrelated
  card families.
- Replace prior attachments deliberately on every in-place transition.
- Close every image/file stream on success, fallback, timeout, cancellation, stale suppression,
  navigation, and exception paths.

### 12.3 Fallback contract

The fallback embed must preserve the same hierarchy in concise form:

- top-level state and supporting line;
- next scheduled alert, no-upcoming state, coverage, or unavailable state;
- KVK summary;
- Calendar summary;
- one Reminder Insight;
- Manage guidance;
- refreshed UTC time.

Do not refetch reminder data after a render or send failure. Do not fall back to the legacy raw-key
copy when a friendly label has already been resolved in the payload.

## 13. Architecture Direction

- Keep command callbacks thin.
- Keep settings resolution, normalisation, state derivation, projection, coverage, and insight
  selection in services/domain helpers.
- Keep persistence and SQL access, where any already exists, in the established DAL/repository layer.
- Keep Discord routing, component state, author gating, timeout behaviour, and message edits in views.
- Keep visual composition in the established page-card renderer or a narrow Reminders-specific
  renderer when that produces clearer boundaries.
- Reuse existing attachment cleanup, fallback, UTC formatting, and navigation helpers.
- Reuse or extract scheduler domain logic narrowly; do not import side-effecting dispatch code into
  the renderer or view.
- Do not create a broad renderer/view framework as part of Phase 5D.
- Do not load the backdrop through user-controlled paths.

## 14. Privacy, Security, And Operational Safety

- All output remains private/ephemeral and author-gated.
- Do not expose private reminder selections in public channels or logs.
- Never trust component-provided user IDs, event keys, or settings as authorization.
- Re-resolve current author/view validity for every callback.
- Do not log full private reminder configurations unless the repository's existing structured audit
  contract explicitly requires a minimal safe field.
- Do not log DM content, event payloads, or generated card bytes.
- A read-only next-alert projection must never create, cancel, acknowledge, or mark a reminder job.
- A card refresh must never send a reminder DM.
- Keep user-controlled display names and any event-source labels bounded and safely rendered.
- Run Codex Security review because private settings, scheduler projections, user-controlled text,
  attachments, and long-lived Discord views are in scope.

## 15. Compatibility Contract

- `/me reminders` remains private and Discord-user scoped.
- Existing legacy redirects or aliases to `/me reminders` remain unchanged.
- Command registration and top-level command count remain unchanged.
- A version-only command metadata increment is permitted if repository conventions require it.
- Existing Accounts/Reminders/Preferences and Dashboard/Inventory/Exports navigation remains.
- No Change Governor.
- The guided Manage journey remains behaviourally unchanged.
- Existing KVK/Calendar enabled flags, event selections, alert-time selections, persistence, restart
  behaviour, scheduling, DMs, and calendar/event source remain unchanged.
- Successful summary delivery moves to or remains a standalone `1702 × 924` attachment under the
  shared premium summary-card contract.
- Same-payload fallback, attachment replacement, and stream cleanup remain mandatory.
- No change to Accounts, Preferences, Inventory summary, Exports summary, Dashboard, direct
  Inventory reports, `/myinventory`, export schemas, Inventory imports, Google Sheets, public `/kvk`,
  History, Inspect, or other reminder consumers.

## 16. Explicitly Out Of Scope

Do not implement any of the following in Phase 5D:

- favourite-event inference;
- player-popularity or most-common-selection recommendations;
- cross-player reminder telemetry or comparison;
- curated `Minimal`, `Standard`, or `Planning` presets;
- automatic addition/removal of reminder selections;
- changing defaults for new users;
- reminder delivery history or last-delivered status;
- DM success/failure telemetry;
- new event types or event sources;
- new alert lead times;
- calendar schema or scheduling changes;
- notification-volume throttling;
- public reminder cards;
- selected-governor reminder filtering;
- Change Governor;
- SQL schema, view, index, table, cache, startup, or persistence redesign;
- broad renderer/view framework work;
- unrelated Phase 5E-5G, Export Stats, History, Inspect, Last Login, Olympia, CrystalTech, website/API,
  or public `/kvk` changes.

Capture the following as deferred opportunities only:

- explicit player-pinned favourite event;
- kingdom-curated reminder presets inside Manage;
- delivery history and delivery-health reporting;
- `new event types available` review state;
- privacy-safe aggregate selection trends with minimum sample thresholds;
- actual upcoming-alert-volume preferences or digest modes.

## 17. Test Strategy

### 17.1 Data/service tests

Cover at minimum:

- both systems enabled and complete;
- only KVK enabled and complete;
- only Calendar enabled and complete;
- both systems off with saved choices;
- both systems off without saved choices;
- enabled system with no events;
- enabled system with no alert times;
- enabled system with neither events nor alert times;
- unavailable/unknown saved event and time keys without raw-key disclosure;
- duplicate persisted event/time keys deduplicated for counts and display;
- `ACTIVE`, `REVIEW`, and `OFF` derivation and supporting copy;
- singular/plural event/time grammar;
- authoritative event ordering;
- raw key to player-facing label mapping, including an example such as
  `armament_reveal` → `Armament Reveal` where that key exists;
- `now`/`start` normalisation to `At start` without changing persisted semantics;
- event-list overflow and `+ <N> more`;
- coverage labels with and without `At start`;
- coverage with one lead time;
- saved inactive coverage;
- exact UTC clock injection and year-boundary formatting data;
- deterministic insight priority and one-sentence output;
- disabled-system insight;
- configuration warning insight;
- no zero/missing confusion;
- graceful source/service failure.

Where an authoritative projection is implemented, additionally cover:

- one future alert;
- earliest alert across KVK and Calendar;
- deterministic tie handling;
- past alert candidates excluded using the scheduler's semantics;
- at-start alert;
- next selected event with all warning windows passed;
- no selected upcoming occurrences;
- event-source partial/unavailable degradation;
- no job creation, no dispatch mutation, and no persistence writes;
- set-based/bulk occurrence retrieval with no N+1 call pattern;
- exact parity with scheduler-domain eligibility fixtures where such fixtures exist.

Where the repository cannot expose an authoritative projection without broad redesign, cover the
approved `REMINDER COVERAGE` fallback and a deferred-item record instead of inventing projection
results.

### 17.2 Renderer tests

Cover:

- exact `1702 × 924` dimensions;
- exact approved backdrop path;
- stable filename;
- avatar and safe no-avatar-fallback layouts;
- `ACTIVE`, `REVIEW`, and `OFF` pills;
- `NEXT SCHEDULED ALERT`, `NO UPCOMING ALERT`, `REMINDER COVERAGE`, and `SCHEDULE UNAVAILABLE` heroes;
- long/Unicode Discord display name;
- long KVK and Calendar event labels;
- one, three, and overflow event summaries;
- all supported alert-time labels;
- off systems with saved inactive choices;
- enabled incomplete systems;
- one maximum-length Reminder Insight;
- absolute UTC timestamps and year boundary;
- no raw event/time keys in rendered output;
- original-size, normal Discord desktop, and mobile previews.

### 17.3 View/interaction tests

Cover:

- direct `/me reminders` entry;
- navigation from a selected dashboard and safe Dashboard return;
- exact global navigation rows and active-page disabled state;
- no Change Governor for one, multiple, more-than-25, and no linked governors;
- existing Manage entry and KVK/Calendar toggle;
- unchanged add/remove/update/confirm/cancel/back behaviour;
- successful mutation refresh of the new host payload/card;
- persisted settings survive the existing restart/reload path;
- same reminder dispatch configuration before and after the visual upgrade;
- standalone successful delivery and same-payload fallback;
- renderer/file/edit/send failure without a second data fetch;
- mutation success followed by render failure does not repeat the mutation;
- attachment replacement and stream cleanup across every transition;
- timeout, stale, foreign, forged, duplicate, cancelled, and concurrent interactions;
- unavailable schedule projection without host-page failure.

### 17.4 Regression and repository gates

Include existing reminder service, scheduler-domain, player-self-service view, page-card, UI import,
command registration, legacy redirect, navigation, fallback, and attachment-cleanup regressions.

Run the repository-prescribed focused selection plus:

```powershell
.\.venv\Scripts\python.exe scripts/validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts/validate_deferred_items.py
.\.venv\Scripts\python.exe scripts/select_tests.py
.\.venv\Scripts\python.exe scripts/smoke_imports.py
.\.venv\Scripts\python.exe scripts/validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts/analyse_pytest_log_noise.py
```

Run any repository-specific scheduler/reminder smoke or deterministic-clock suite discovered during
implementation.

## 18. Visual Sample Matrix

Create review samples from genuine-shaped synthetic payloads without inventing runtime data paths:

1. both systems active with a next KVK alert;
2. both systems active with a next Calendar alert;
3. one system active and one off with saved choices;
4. both systems off;
5. `REVIEW` because an enabled system has no alert times;
6. `REVIEW` because an enabled system has no event types;
7. no upcoming alert;
8. coverage fallback with no scheduler projection;
9. schedule temporarily unavailable;
10. long Discord name, long event names, maximum event overflow, and maximum insight length.

For each required state, review:

- original `1702 × 924` output;
- normal Discord desktop attachment display;
- smaller mobile-style display.

Reject any layout that exposes raw keys, makes the status ambiguous, lets the hero dominate at the
expense of the system summaries, or needs heavy emergency darkening over the approved backdrop.

## 19. Manual Discord Smoke

After automated validation and visual review:

1. Direct `/me reminders` opens privately as a standalone premium card using the approved backdrop.
2. The invoking user's genuine KVK and Calendar enabled states, event choices, and alert times match
   the existing settings exactly.
3. Raw event/time keys are replaced with correct player-facing labels.
4. `ACTIVE`, `REVIEW`, and `OFF` are exercised with genuine or safely staged settings.
5. A displayed next alert is compared with the existing scheduler/event data and is genuinely the
   earliest eligible future alert.
6. `At start` and pre-start warnings show the correct absolute UTC times.
7. No-upcoming, coverage-fallback, and schedule-unavailable states remain honest and readable.
8. KVK and Calendar summaries show correct counts, order, overflow, canonical time labels, and
   coverage ranges.
9. The deterministic Reminder Insight follows the approved priority and does not infer favourites or
   community recommendations.
10. `Manage` opens the unchanged guided child flow and the KVK/Calendar switch still works.
11. Add, remove, update, cancel, confirm, and back behaviour remain correct.
12. A successful change refreshes the summary card once and persists through the existing restart
    path.
13. Existing reminder dispatch/DM behaviour is unchanged by the card refresh and projection.
14. Accounts, Preferences, Dashboard, Inventory, and Exports navigation remains correct.
15. Change Governor is absent.
16. Fallback, timeout, foreign, stale, forged, concurrent, render failure, edit failure, and stream
    cleanup paths are safe.
17. Original-size, Discord desktop, and Discord mobile presentation are accepted.

## 20. Implementation Evidence And Acceptance Criteria

Implementation evidence recorded on 2026-07-14:

- Added one typed, read-only KVK/Calendar payload in
  `player_self_service/reminders_summary.py` for state, friendly labels, canonical alert times,
  genuine counts, deterministic overflow, saved/off treatment, coverage, hero variants, warnings,
  injected UTC time, and one priority-ordered insight.
- Added the deterministic `player_self_service/reminders_renderer.py`, which strictly
  requires the fully opaque `assets/me/cards/me_reminders.png` at `1702 × 924`, returns stable
  `me_reminders_<discord_user_id>.png`, and renders the approved hierarchy without changing the
  backdrop.
- Operator smoke on 2026-07-15 accepted Manage refresh and timeout behavior and requested the final
  visual refinement: shared Discord avatar, duplicate-safe Kingdom suffix, no deprecated Inventory
  navigation, right-aligned state support, and a split UTC footer with full refreshed date-time.
  These corrections are implemented and await the operator's final visual re-smoke.
- The refinement passed `83` renderer/view tests, `146` focused Accounts/Reminders/scheduler/
  dispatch regressions, full pytest (`2562 passed, 2 skipped`), architecture and deferred-item
  validation, smoke imports, command registration, pytest log-noise analysis, and all pre-commit
  hooks. The refined native-size sample passed local visual review.
- Kept `/me reminders` private and Discord-user scoped, rendered off-loop as a standalone
  attachment, retained the real component rows and unchanged guided Manage mutations, and preserved
  same-payload fallback, deliberate attachment replacement, timeout behavior, and stream cleanup.
  Final security review found and closed one non-security cleanup gap in the Manage-flow host refresh:
  its regenerated attachment files are now explicitly closed in `finally` on every outcome.
- Repository inspection found no safe existing cross-system next-alert projection: KVK and Calendar
  dispatch own materially different eligibility, grace, tracker, and sent-key rules. Runtime
  therefore uses the approved `REMINDER COVERAGE` hero; the shared pure-projection opportunity is
  recorded in `docs/reference/deferred_optimisations.md`.
- Focused renderer/service/view/mutation tests passed (`147 passed`); reminder/scheduler and
  deterministic-clock selection passed (`193 passed`); full pytest passed (`2551 passed, 2 skipped`).
- Architecture boundaries, command registration, smoke imports, and the ten-case original/desktop/
  mobile visual matrix passed. Visual evidence is under the task visualization output directory.
- Codex Security standard repository scan `8fcf96f6-44e0-4d87-8521-7de721444ef7` sealed against the
  corrected worktree snapshot with `85/85` review receipts and `42/42` complete candidate ledgers.
  It reported 20 pre-existing repository findings (`16 Medium`, `4 Low`) in authorization/import/
  Ark/MGE surfaces and no Phase 5D security finding. The generated report is retained in the scan
  workspace; those wider findings are not silently folded into this visual-only phase.
- No SQL, scheduler, event source, event type, lead time, persistence, retry, dispatch, DM, or
  duplicate-send behavior changed.
- Operator Discord smoke remains the final external gate and is intentionally not marked complete.

- [x] Phase 5C operator Discord smoke is recorded as passed before Phase 5D runtime work begins.
- [x] Approved `assets/me/cards/me_reminders.png` exists at exactly `1702 × 924`.
- [x] `/me reminders` renders a standalone private PNG with stable filename.
- [x] The approved header, hero, two-system summary, insight, action, and footer hierarchy is implemented.
- [x] `ACTIVE`, `REVIEW`, and `OFF` follow the locked configuration rules.
- [x] Disabled systems with saved choices are shown honestly as saved and inactive.
- [x] Raw event and alert-time keys are never displayed.
- [x] `now`/`start` presentation is normalised to `At start` without changing persisted semantics.
- [x] A next alert is shown only through authoritative read-only scheduler/event semantics.
- [x] The approved coverage fallback is used instead of a parallel scheduler when necessary.
- [x] No projection creates jobs, sends DMs, marks delivery, or mutates persistence.
- [x] One deterministic Reminder Insight follows the approved priority.
- [x] Existing Manage behaviour, KVK/Calendar toggle, persistence, restart, scheduling, DMs, and
      event sources are unchanged.
- [x] No Change Governor appears.
- [x] Same-payload fallback, attachment replacement, off-event-loop rendering, and stream cleanup are
      implemented and tested.
- [x] No SQL schema, scheduler, event-source, lead-time, calendar, DM, or persistence redesign is introduced.
- [x] Focused/full validation, visual samples, and Codex Security review are recorded.
- [ ] Operator Discord smoke is recorded.
- [x] Programme, briefing, canonical command reference, task-pack status, and deferred items are updated
      after delivery.

## 21. Remaining Decisions And Escalation Gates

There are no known blocking product or visual decisions.

The following is **not** an escalation: if the existing architecture cannot expose an exact next-alert
projection without creating parallel scheduler logic or widening scope, implement the approved
`REMINDER COVERAGE` hero and record the projection as deferred.

Stop and ask the operator only if repository inspection proves one of the following:

- the current Manage journey cannot be preserved without changing reminder business rules;
- the persisted settings do not distinguish KVK and Calendar enablement/selections as expected;
- there is no authoritative player-facing event-label source and adding one would change the Manage
  contract rather than merely centralise presentation;
- current scheduler semantics for `now` versus `start` are materially different and cannot be safely
  presented as one `At start` label;
- a SQL schema, new event source, new scheduler, or persistence change is required;
- the approved backdrop is absent, corrupted, or not exactly `1702 × 924`;
- Discord/mobile constraints make the locked hierarchy impossible without changing the product contract.

Do not silently omit one reminder system, display raw keys, substitute a popularity recommendation,
add a third reminder category, or redesign Manage to work around a blocker.

## 22. Handoff After Phase 5D

After Phase 5D automated validation and operator acceptance, execute separately:

- Phase 5E: Premium Preferences Summary Card
- Phase 5F: Premium Inventory Summary Card
- Phase 5G: Premium Exports Summary Card

Each page reuses the accepted standalone/fallback/navigation discipline but retains its own
page-specific content, data, asset, and interaction contract. None shows Change Governor.
