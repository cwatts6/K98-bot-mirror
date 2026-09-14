# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 7 `/me` Visual Consistency, Content Audit and Programme Closeout

Status: completed initiation record. Phase 7 passed final Discord smoke and was operator accepted
on 2026-07-19. Do not restart this starter; use the active Phase 8 starter for follow-on work.

## Copy/Paste Starter

```text
Codex, begin Player Self-Service Command Centre v2 Phase 7: /me Visual Consistency, Content Audit and
Programme Closeout.

Approval state:
- GovernorOS v2 Phase 6 is complete and operator accepted on 2026-07-18
- current command baseline is 37 top-level, 100 grouped, 8 /me, and 2 /inventory
- Phase 7 adds/removes/renames no command and requires no command resync
- /me stats is the accepted visual reference
- the former /me history proposal is closed with no implementation
- /kvk history remains the one canonical KVK-history route
- Phase 7 is a narrow visual/content consistency pass, not a feature or data redesign
- one-pass execution is not approved
- first response must be audit/scope only; do not code

Canonical /me group:
- /me dashboard
- /me accounts
- /me reminders
- /me preferences
- /me resources
- /me speedups
- /me materials
- /me stats

Surfaces in scope:
- Dashboard 1180x760 plus fallback
- Accounts 1702x924
- Account Summary Overview/Combat/Economy
- Reminders 1702x924
- Preferences 1702x924
- Stats Overview/Activity/Combat 1702x924
- Resources/Speedups/Materials 1400x980
- same-payload fallbacks
- common navigation/state/timeout/freshness presentation

Locked reference:
- use player_self_service/stats_renderer.py as the default visual contract
- reference colours:
  TEXT (248,251,255,255)
  MUTED (190,210,235,255)
  BLUE (91,190,255,255)
  GOLD (255,206,92,255)
  GREEN (76,225,148,255)
  AMBER (255,196,78,255)
  RED (255,132,132,255)
  SHADOW (0,0,0,190)
  PANEL (3,11,27,220)
  panel edge (91,190,255,180), width 2
- use the Stats typography hierarchy, right-aligned state/header pattern, compact numbers,
  source/generated separation, blue navigation, fallback, accessibility, transition safety,
  preserve-and-disable timeout, and cleanup as the reference
- adapt proportionally for different dimensions
- do not force every page into Stats geometry

Visual family rules:
- core 1702x924 summary cards should align closely
- Dashboard keeps 1180x760 and its governor-specific layout/avatar
- Inventory keeps 1400x980, report-specific backdrops, icons, charts, ranges, exports, and category
  accents
- align shared visual language, not every page structure

State semantics:
- green = ready/current/active/success
- blue = neutral information/selection
- amber = review/partial/stale/incomplete
- red = no data/unavailable/failed
- muted = off/disabled/expired
- use dark pill fill, semantic outline, readable text, and the same relative top-right position
- UTC is neutral blue, not warning amber
- OFF is muted unless it represents an error

Content audit:
- — = missing individual value
- Not recorded = meaningful never-recorded state
- NO DATA = healthy whole-source/card empty
- UNAVAILABLE = dependency/request failure
- do not replace genuine zero
- standard UTC date: 18 Jul 2026, 14:05 UTC
- keep Data refreshed, Inventory uploaded, Location updated, and Generated separate
- audit K/M/B, signed deltas, percentages, days, minutes, donations, RSS, KP Loss, Tanking Score,
  singular/plural, snapshot vs period labels
- no calculation or data-source change

Narrow shared helper:
- a small player_self_service/visual_contract.py may own proven common colours, typography scale,
  state mapping, panel tokens, formatting, and bounded primitives
- do not create a universal renderer/grid/payload/view framework
- require at least two identical consumers before extraction

Do not:
- add /me history or a History dashboard action
- change /kvk history
- change commands, SQL, DAL, payloads, metrics, formulas, ranks, permissions, privacy, exports,
  account resolution, selectors, timeouts, or public behaviour
- resize all cards
- remove Inventory category accents
- perform broad view/lifecycle consolidation
- introduce leadership work under /me

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- engineering/execution/testing/skills/deferred references
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- the matching Phase 7 task pack
- archived Phase 6, Phase 5B, Phase 5C, Phase 5D, and Phase 5E packs
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Audit these areas:
- player_self_service/stats_renderer.py
- player_self_service/accounts_renderer.py
- player_self_service/reminders_renderer.py
- player_self_service/preferences_renderer.py
- player_self_service/governor_dashboard_renderer.py
- inventory/report_image_renderer.py
- player_self_service/page_cards.py
- relevant player_self_service views
- core/visual_text.py
- assets/me/cards and assets/Inventory/cards
- all visual tests and sample generators

First response: audit only.

Report:
A. exact card/page/renderer/asset/file inventory
B. every card dimension, filename, backdrop, avatar, fallback, state, footer, and timeout
C. colour-token comparison against Stats
D. typography-size/weight hierarchy comparison
E. state-pill wording/colour/position comparison
F. panel border/radius/opacity and alignment comparison
G. missing-value/date/number/unit/navigation copy comparison
H. intentional product differences versus accidental drift
I. exact narrow shared-helper candidates with at least two identical consumers
J. before-contact-sheet plan and visual sample matrix
K. no-feature-change file manifest
L. provisional Changes/Deep-off security routing
M. focused/full/visual validation plan
N. rollback and Discord smoke plan
O. command-count proof that 37/100/8/2 remains unchanged

Stop after the audit and wait for operator approval.
```
