# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5D Premium Reminders Summary Card

Status: next active GovernorOS product/visual workshop. Implementation is not yet approved.

```text
Codex, begin Player Self-Service Command Centre v2 Phase 5D: Premium Reminders Summary Card.

Approval state:
- Phase 5C Accounts is complete and operator accepted
- Phase 5D repository inspection and product/visual workshop are approved
- Phase 5D runtime implementation is not approved yet
- I have improvement ideas to work through before the Reminders hierarchy is locked
- do not treat the existing card or empty space as approval for a particular metric or layout

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
- the GovernorOS Visual Design Bible where present

Use these skills:
- k98-architecture-scope
- k98-discord-command-feature
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review

Use k98-sql-validation only if an approved idea proves SQL-facing. Use Codex Security review after
implementation approval because the eventual slice touches private Discord interactions,
file/attachment handling, and restart-sensitive reminder workflows.

First inspect and report a concise workshop map:
- current `/me reminders` command/view/summary-service/renderer/fallback flow
- current combined KVK and calendar status fields and their authoritative sources
- current Manage, KVK autosave, Calendar Settings, confirmation DM, Remove All, revalidation, and
  host-refresh paths
- persisted state, restart/rehydration, unsubscribe cancellation, and duplicate-send protections
- current 1702x924 backdrop/card at original, Discord desktop, and Discord mobile sizes
- existing navigation rows, attachment lifecycle, timeout behavior, and tests
- exact files likely to change only after design approval

Locked programme baseline:
- private/ephemeral and author-gated
- Discord-user reminder scope; no Change Governor and no selected-governor filter
- optional selected Dashboard governor is return context only
- standalone 1702x924 private attachment is the default premium format
- stable me_reminders_<discord_user_id>.png filename unless explicitly changed
- best-effort author-validated Discord avatar at upper left is the default identity treatment
- same-authorized-payload fallback; no render-failure refetch
- render off-loop, deliberate attachment replacement, complete stream cleanup
- graceful timeout preserves the report and disables/rejects controls
- real Discord components, page-relevant navigation, and no broad renderer/view framework

Do not change reminder scheduling, event sources, event/time choices, calendar lead times, DMs,
persistence, SQL, legacy redirects, or another `/me` page during the workshop.

After the inspection, help me work through my ideas. Organise them into:
1. what the card should answer immediately
2. content and genuine data
3. hierarchy and state/guidance rules
4. actions and navigation
5. backdrop, avatar, typography, and responsive presentation
6. behavior changes that would require a separate approval gate

Offer two or three coherent options where useful. Do not implement until I explicitly approve the
final Phase 5D contract. Once approved, update the task pack/starter with the locked contract before
coding.
```
