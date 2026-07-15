# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5D Premium Reminders Summary Card

Status: approved implementation task. Phase 5C is complete and the Phase 5D product, content, visual,
interaction, and compatibility contract is locked.

```text
Codex, implement Player Self-Service Command Centre v2 Phase 5D: Premium Reminders Summary Card.

Approval state:
- Phase 5C Accounts is complete and operator accepted
- the Phase 5D product/content workshop is complete
- the Phase 5D information hierarchy, state rules, hero decision tree, summaries, insight priority,
  controls, avatar treatment as refined by operator smoke, and behavior boundaries are approved
- runtime implementation is approved
- the approved production backdrop is present at assets/me/cards/me_reminders.png and must be
  exactly 1702x924
- operator Discord smoke is the final post-implementation gate, not a pre-coding approval gate

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5D Premium Reminders Summary Card.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 4 Modern Reminder Centre.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 7 Unified Reminder Centre and Dashboard Card Alignment.md
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md
- docs/reference/events_and_dm_reminders.md
- the GovernorOS Visual Design Bible and approved Herald's Watch backdrop task where present

Use these skills/workflows:
- k98-architecture-scope
- k98-discord-command-feature
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review
- codex-security:security-scan after implementation

Use k98-sql-validation only if repository evidence unexpectedly proves an approved field is
SQL-facing. Do not introduce SQL work to obtain a visual-only outcome.

Before editing, inspect and report one concise implementation map:
1. current /me reminders command, view, summary service, renderer, fallback, and attachment flow;
2. authoritative KVK and Calendar enabled/event/time sources and their player-facing label maps;
3. current Manage, KVK autosave, Calendar Settings, confirmation DM, Remove All, revalidation,
   restart/rehydration, duplicate-send protection, and host-refresh paths;
4. whether an exact next-alert projection can be obtained by reusing an existing read-only service or
   extracting a narrow pure helper from scheduler-domain logic;
5. exact files to change and the focused tests selected;
6. verification that assets/me/cards/me_reminders.png is readable, fully opaque, and exactly 1702x924.

That inspection is not a new product workshop. Continue directly into implementation unless a true
section-21 blocker in the task pack is proven. In particular, inability to expose an authoritative
next-alert projection without duplicating scheduler logic is not a blocker: implement the approved
REMINDER COVERAGE hero and record the projection opportunity in deferred_optimisations.md.

Locked card hierarchy:

REMINDER CENTRE                                      ACTIVE | REVIEW | OFF
<Discord display name> (1198)                        <state supporting line>

NEXT SCHEDULED ALERT | NO UPCOMING ALERT | REMINDER COVERAGE | SCHEDULE UNAVAILABLE
<hero content from the approved discriminated contract>

KVK REMINDERS                              CALENDAR REMINDERS
<state/count>                              <state/count>
<friendly event summary>                   <friendly event summary>
<canonical alert-time labels>              <canonical alert-time labels>
<coverage line>                            <coverage line>

REMINDER INSIGHT
<one deterministic sentence from the approved priority>

Manage reminders
Choose KVK and calendar events and when each alert is sent.

Refreshed <HH:MM UTC> • Schedule times shown in UTC

Locked state rules:
- ACTIVE: at least one system is enabled and every enabled system has at least one valid event and
  one valid alert time
- REVIEW: an enabled system cannot produce reminders from its saved configuration, including
  missing events, missing alert times, or unavailable saved selections
- OFF: both systems are disabled; retain and label saved inactive choices honestly
- a deliberately disabled system, no upcoming event, passed warning windows, or a temporary event-
  source read failure does not by itself make the configuration REVIEW

Locked hero decision:
1. show NEXT SCHEDULED ALERT only from authoritative read-only scheduler/event semantics;
2. show NO UPCOMING ALERT when the projection is healthy but has no future candidate;
3. show REMINDER COVERAGE when an authoritative projection would require parallel scheduler logic,
   a new source, changed persistence, or wider redesign;
4. show SCHEDULE UNAVAILABLE when a normally available projection/source fails for this request;
5. use absolute UTC timestamps, not countdowns, and never imply delivery success.

Locked summary/intelligence rules:
- never expose raw keys such as armament_reveal
- reuse authoritative event labels and ordering
- normalize presentation synonyms now/start to At start only when repository semantics prove they
  are equivalent; otherwise stop under the task-pack escalation rule
- show genuine event/time counts, a deterministic overflow such as + N more, and honest saved/off or
  incomplete states
- derive coverage spans from selected moments without implying continuous coverage
- render exactly one Reminder Insight, prioritising configuration issues, then proven coverage gaps,
  disabled systems, neutral coverage characteristics, and finally positive coverage
- do not infer favourite events, recommend popularity-based settings, compare players, or fabricate
  reminder load

Locked interaction and delivery contract:
- private/ephemeral and author-gated
- Discord-user scope; no selected-governor filtering and no Change Governor
- optional selected Dashboard governor is return context only
- no Discord avatar on the Phase 5D card
- standalone 1702x924 private attachment using stable me_reminders_<discord_user_id>.png
- same-authorized-payload fallback with no render-failure refetch
- off-loop deterministic Pillow rendering
- deliberate attachment replacement and complete image/file-stream cleanup
- graceful timeout preserves the report, visibly disables controls, and rejects later interactions
- real Discord components only
- Row 0: Accounts | Reminders disabled | Preferences
- Row 1: Dashboard | Inventory | Exports
- Row 2: the existing Manage/Manage Reminders action
- no separate KVK or Calendar host-page buttons

Preserve exactly:
- current KVK and Calendar event types and alert-time choices
- KVK autosave/update wording and confirmation DM behavior
- Calendar Settings handoff
- Remove All confirmation and current-state revalidation
- scheduled/sent tracker cleanup and unsubscribe behavior
- persistence, restart/rehydration, duplicate-send prevention, retry, scheduler, event-source, and DM
  behavior
- legacy redirects, command registration, privacy, logging, and service ownership

Do not add or change:
- scheduler behavior, jobs, dispatch, event sources, event types, lead times, DM policy, Calendar
  semantics, SQL schema, persistence, defaults, presets, delivery history, popularity metrics,
  favourite-event inference, cross-player telemetry, public output, another /me page, or a broad
  renderer/view framework.

Implementation and validation:
- keep commands/views thin and projection/state/normalisation/insight logic in services/domain helpers
- reuse or narrowly extract scheduler-domain logic without side effects
- build one typed, same-payload Reminders summary contract
- cover ACTIVE/REVIEW/OFF, every hero variant, unknown selections, saved inactive choices, label and
  time normalization, overflow, coverage, insight priority, exact UTC handling, long/Unicode names,
  and source failure
- where next-alert projection is implemented, prove no jobs, DMs, acknowledgements, persistence
  writes, or N+1 occurrence reads are introduced and test parity with scheduler eligibility
- preserve Manage mutation/restart/dispatch regressions
- cover direct entry, selected-Dashboard return, fallback, render/edit/send failures, timeout,
  foreign/stale/forged/concurrent interactions, attachment replacement, and stream cleanup
- render original 1702x924, Discord desktop, and mobile visual samples for the task-pack matrix
- run architecture, deferred-item, selected-test, smoke-import, command-registration, pre-commit,
  full pytest, log-noise analysis, and the repository's reminder/scheduler deterministic-clock tests
- run Codex Security review
- update the programme pack, briefing, canonical reference, task-pack status, and deferred backlog
  with implementation evidence; do not mark operator smoke complete until the operator performs it

Stop and ask only for the explicit blockers in section 21 of the task pack. Do not silently omit one
system, display raw keys, add a popularity recommendation, redesign Manage, or widen the phase.
```
