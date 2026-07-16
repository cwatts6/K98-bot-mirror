# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5E Premium Preferences Summary Card

<!-- codex-security-routing: allow-standard reason="archived historical execution record; not active security-routing guidance" -->
<!-- codex-security-routing: allow-generic reason="archived historical execution terminology retained for delivery traceability" -->

Status: complete, operator accepted, merged in mirror PR #224 and production PR #531, and deployed
on 2026-07-16. This starter is retained as the archived implementation instruction record.

## Completion Record

- Delivered the private `1702x924` Personal Settings card with the invoking-user avatar in the
  approved top-left identity treatment, DST-aware local-time/UTC fallback, regional-profile
  coverage, exact Inventory privacy state/copy, deterministic insight, and same-payload fallback.
- Removed deprecated Inventory navigation, VIP content, direct privacy toggles, and Change Governor
  from Preferences; retained one in-place `Manage settings` action.
- Re-hosted Update VIP under Manage Accounts with explicit linked-governor resolution and current-
  access revalidation while preserving VIP meaning and persistence.
- Added the approved atomic field-specific profile DAL upsert without a SQL schema or deployment
  change.
- Final validation recorded `2637 passed, 2 skipped`; repository gates, visual review, security/PR
  review, patch-based promotion, operator acceptance, and deployment completed.
- Phase 5F Premium Inventory Summary Card remains the next slice, with its task pack and starter to
  be created separately.

## Copy/Paste Starter

```text
Codex, begin Player Self-Service Command Centre v2 Phase 5E: Premium Preferences Summary Card.

Approval state:
- GovernorOS v2 Phases 1-5D.1 are complete and operator accepted
- Phase 5D Reminders is complete in mirror PR #222 and production PR #529
- Phase 5D.1 Authoritative Next Scheduled Alert Projection is complete in mirror PR #223 and
  production PR #530
- Phase 5E is now the next active implementation slice
- the Phase 5E product/content/interaction contract is approved
- the Governor's Accord backdrop is approved and present locally at
  assets/me/cards/me_preferences.png
- the asset must be exactly 1702x924 and fully opaque; verify this in the audit
- runtime implementation is approved subject to the required audit, architecture, and plan gates
- one-pass execution is not approved
- do not reopen the locked product decisions unless repository evidence proves one is unsafe or
  impossible

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5E Premium Preferences Summary Card.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5D Premium Reminders Summary Card.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5D.1 Authoritative Next Scheduled Alert Projection.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card.md
- the archived/current Task - Generate GovernorOS Preferences Centre Governor's Accord Backdrop V1
- the GovernorOS Visual Design Bible where present
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Follow the conditional reading order in docs/reference/README.md for Discord views, rendering/file
handling, SQL-backed profile/preferences, testing, and deployment.

Validate every touched existing profile, Inventory visibility, and GovernorInventoryProfile
contract against:
C:\K98-bot-SQL-Server

No SQL deployment, schema change, view/index/procedure change, or data migration is approved.

Use these skills:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review
- codex-security:security-scan
- k98-promotion-check only at the later production-promotion gate

Mandatory workflow:
1. Audit and scope review, then stop for approval.
2. Architecture validation and exact file manifest, then stop for approval.
3. Implementation plan, then stop for approval.
4. Implement only after approval.
5. Run focused/full validation, visual QA, Codex Security, and K98 PR review.
6. Create/review the mirror PR and complete operator Discord smoke.
7. Run promotion check and production promotion only after acceptance.

First audit and report, with repository evidence:
- the exact /me preferences command -> view -> summary service -> renderer -> same-payload fallback
  chain
- the exact current parent navigation, attachment replacement, timeout, cancellation, stale,
  foreign, forged, superseded, and concurrent behavior
- the exact Manage Profile child-window implementation, field catalogs, pagination, save/autosave,
  clear/null semantics, child replacement, and host refresh
- the exact Inventory visibility service/repository/persistence owner and every output path affected
  by the public/private preference
- whether private direct /me resources, /me materials, and /me speedups remain private under the
  current contract, and the exact player-facing consequence copy that is truthful
- the exact Update VIP journey: governor resolution, >25 behavior, access checks, VIP catalog/range,
  not-set semantics, save service, persistence, logging, stale revalidation, and host refresh
- the exact Manage Accounts task selector, component budget, and current find/register/replace/remove
  flows that must remain unchanged
- the authoritative timezone, country, and preferred-language catalogs and friendly-label helpers
- the authoritative timezone-conversion helper/runtime support and whether it handles DST plus
  non-whole-hour offsets without network access
- current renderer/avatar/text-fitting helpers proven by Accounts and Reminders
- current background validation, file/stream lifecycle, fallback, and timeout tests
- exact likely files to review, modify, or create
- test gaps and any refactor trigger
- verification that assets/me/cards/me_preferences.png is exactly 1702x924, fully opaque, and safe
  for runtime use

Do not code during the first audit response. Stop after the audit report and proposed approval
checkpoint.

Locked product ownership:
- /me preferences remains private, author-gated, Discord-user scoped, and independent of a selected
  governor
- optional selected Dashboard governor context exists only for a validated Dashboard return
- selected governor context must never filter Preferences, set local time, or preselect a VIP editor
- Preferences becomes the Personal Settings centre for:
  - saved timezone
  - saved location/country
  - preferred-language metadata
  - derived local-time context
  - Inventory privacy and sharing
- Preferences is not a catch-all for account, reminder, export, report, or unrelated defaults
- Inventory visibility remains the single user-level privacy mutation owned by Preferences
- governor-specific VIP editing moves out of Preferences and into Manage Accounts -> Update VIP
- this is a UI ownership migration, not a VIP data-model or account-management redesign

Locked successful output:
- standalone private attachment, not an embed-wrapped image
- exact 1702x924 PNG
- runtime backdrop assets/me/cards/me_preferences.png
- stable filename me_preferences_<discord_user_id>.png
- invoking-user bounded circular Discord avatar with the accepted safe fallback
- long/Unicode name fitting and duplicate-safe Kingdom 1198 identity
- render off the event loop
- same-authorized-payload private fallback with no second service fetch
- deliberate clearing/replacement of prior attachments
- complete image/buffer/Discord-file stream cleanup on success, fallback, send/edit failure,
  navigation, timeout, cancellation, stale suppression, and concurrency
- graceful timeout preserves the last valid private card, disables controls, and rejects later
  interactions without refetching or rerendering merely to mark timeout

Locked main card hierarchy:

PERSONAL SETTINGS                                      PRIVATE | PUBLIC
<Discord display name and Kingdom 1198>                <0-3 of 3 profile details set>

LOCAL TIME REFERENCE | UTC REFERENCE
<24-hour local time or UTC time>
<saved timezone and current DST-aware UTC offset, or set-timezone guidance>
<location and preferred-language context where available>

REGIONAL PROFILE                         PRIVACY & SHARING
Timezone                                 Inventory visibility: PRIVATE | PUBLIC
Location                                 Exact current visibility consequence
Preferred language

SETTINGS INSIGHT
<one deterministic sentence>

Manage settings
Update your regional profile and inventory privacy.

<local-time/reminder-UTC context>                       Refreshed <full UTC date-time>

Locked state and content rules:
- the header state is exactly PRIVATE or PUBLIC and reflects Inventory visibility
- PRIVATE uses restrained positive green/teal treatment
- PUBLIC uses amber/gold awareness treatment, not error-red
- do not invent READY, REVIEW, or SETUP for Preferences
- profile coverage is exactly the count of recognised usable timezone, location, and preferred
  language values out of three
- optional unset location/language values are neutral
- unavailable legacy values are surfaced honestly and do not count as usable
- use friendly player-facing labels from authoritative catalogs; do not expose raw unknown keys
- Preferred language remains metadata only; do not claim or implement full interface localization

Locked local-time rules:
- build one aware UTC generated_at value per request
- use that same value for the local-time hero and full UTC refreshed footer
- valid saved timezone -> LOCAL TIME REFERENCE
- missing/unavailable timezone -> honest UTC REFERENCE fallback
- display time in 24-hour HH:mm format; do not infer or add a 12-hour preference
- derive the current UTC offset at generated_at, including DST and half-/quarter-hour offsets
- use clear labels such as UTC, UTC+1, UTC-3, UTC+5:30
- no live ticking clock, background job, scheduled refresh, external time service, or network call
- do not infer timezone from location, preferred language, Discord locale, device, IP, or nationality
- this card does not change Reminder Centre UTC presentation or any reminder scheduling semantics

Locked Privacy & Sharing rules:
- trace the exact existing visibility behavior before finalizing copy
- show Inventory visibility: PRIVATE or PUBLIC
- explain only the consequences genuinely controlled by the existing preference
- do not imply that private direct /me resources, /me materials, or /me speedups become public
- do not post a public message merely because the setting changes
- do not add per-governor visibility, sharing history, telemetry, or new privacy defaults

Locked Settings Insight priority:
1. unavailable/invalid saved profile metadata that needs review
2. no usable timezone, because local-time context cannot be shown
3. Inventory is public, so sharing deserves deliberate awareness
4. one or more optional profile values are not set
5. complete regional profile with private Inventory as the neutral-positive state

Render exactly one deterministic sentence, normally no more than two clauses.
Do not infer that location and timezone should match. Do not infer nationality, fluency, preferred
event time, risk, or a recommendation from cross-player popularity.

Locked main Discord component rows:
Row 1: Accounts | Reminders | Preferences (active and disabled)
Row 2: Dashboard | Exports
Row 3: Manage settings

Component rules:
- retain the blue-primary first-row navigation pattern
- remove deprecated Inventory navigation from Preferences
- remove direct Set Public/Set Private, Update VIP, and Manage Profile buttons from the main page
- show one success-style Manage settings action
- paint no fake buttons into the image
- show no Change Governor on Preferences

Locked Manage Settings child journey:
- Manage settings replaces the existing private content in place
- repeated clicks must not create duplicate child windows
- provide Regional profile and Privacy & sharing controls plus Back to Preferences
- reuse existing timezone/location/language catalogs, validation, pagination, save/autosave, null,
  clear, and persistence semantics
- do not add a cross-field transaction unless the current service already owns one
- remove the permanent row of three Clear Timezone/Country/Language host buttons
- expose Not set/Clear deliberately inside the relevant field update flow
- if a field select is already at Discord's 25-option limit, use a contextual clear step rather than
  dropping a genuine option or restoring three permanent clear buttons
- after save/clear, refresh the same child state so the stored result is visible
- Back to Preferences rebuilds the parent from current authorized state and replaces attachments and
  components cleanly

Locked Inventory visibility mutation:
- state-aware action: private offers Make Public; public offers Make Private
- display the current state and exact consequence before mutation
- require explicit confirmation in both directions
- re-read/revalidate current state at confirmation time
- cancel returns without mutation
- use the existing service and persistence contract
- success must immediately reflect the new privacy pill on the refreshed Preferences parent or an
  equally clear operator-approved reflected state
- no new public output is created by the mutation

Locked VIP migration:
- remove the VIP list from the Preferences card and fallback
- remove Update VIP from the Preferences parent and Manage Settings
- Preferences should not fetch per-governor VIP solely for rendering
- add Update VIP at the existing task-selection level inside Manage Accounts
- do not add a new Accounts main-card button solely for VIP

Target reused journey:
Manage Accounts
-> Update VIP
-> explicitly select/resolve linked governor
-> select VIP level
-> Save VIP
-> recheck current registry linkage/access immediately before write
-> existing VIP service/persistence
-> clear result and return/refresh Accounts management host

VIP migration rules:
- retained Dashboard governor context must never silently select the governor
- zero linked governors receive register-account guidance and no write
- one linked governor may be preselected only if current behavior already does so, while still showing
  identity and rechecking access
- multiple and >25 governors use the accepted paged selector/resolver where required
- preserve current VIP labels, allowed values/range, not-set semantics, write contract, logging, and
  error handling
- preserve find/register/replace/remove/confirm/cancel, ownership/claim, slot, lookup, registry, and
  host-refresh behavior
- do not change Account Summary, Inventory calculations, or SQL definitions
- a successful save must be visible on an Accounts surface that already displays VIP without a stale
  cached payload

Recommended typed summary shape, subject to architecture review:

PreferencesSummaryPayload
- Discord-user identity
- generated_at_utc
- InventoryVisibilitySummary
- RegionalProfileSummary
- TimeReferenceSummary
- profile_details_set
- profile_details_total = 3
- profile supporting text
- one deterministic Settings Insight
- warnings/unavailable saved values

InventoryVisibilitySummary
- is_public
- state_label PRIVATE | PUBLIC
- exact player-facing consequence text

RegionalProfileSummary
- timezone PreferenceValueSummary
- location PreferenceValueSummary
- preferred_language PreferenceValueSummary

PreferenceValueSummary
- set/unset
- available/unavailable
- stored key/code retained internally
- friendly label
- optional player-facing code

TimeReferenceSummary
- LOCAL | UTC_FALLBACK
- display time
- timezone label when usable
- UTC-offset label when usable
- optional location/language context
- supporting line

Service rules:
- commands/views do not own timezone conversion, coverage, consequence copy, insight priority, SQL,
  or VIP business logic
- summary construction is read-only and side-effect free
- no N+1 governor reads
- no missing value is silently converted to zero, false, private, or valid
- do not fetch VIP for the Preferences card unless a still-shared internal payload genuinely requires
  it and removing the read would require a separately approved broad refactor

Exact safe-zone geometry from the approved backdrop task:
- full canvas: x 0-1702, y 0-924
- header/identity: x 92-1610, y 48-202
- local-time/UTC hero: x 92-1610, y 214-390
- transition band: x 0-1702, y 396-416
- Regional Profile: x 92-1000, y 426-650
- Privacy & Sharing: x 1020-1610, y 426-650
- inter-column gap: x 1000-1020, y 426-650
- Settings Insight: x 92-1610, y 664-752
- Manage explanation: x 92-1610, y 766-848
- footer: x 92-1610, y 858-920

Likely files to audit, not assumptions about final ownership:
- commands/me_cmds.py
- ui/views/player_self_service_views.py
- current Preferences/Profile child-view modules discovered from that route
- current Accounts Manage child-view modules discovered from that route
- player_self_service/service.py
- player_self_service/page_cards.py
- current Accounts/Reminders page-specific model/renderer helpers
- inventory/profile_service.py
- current Inventory visibility repository/service path
- current GovernorInventoryProfile VIP repository/service path
- timezone/country/language catalog/helper modules
- attachment/edit/timeout/avatar/text-fitting helpers
- tests/test_me_cmds.py
- tests/test_player_self_service_views.py
- tests/test_player_self_service_service.py
- tests/test_player_self_service_page_cards.py
- focused Inventory profile/visibility and Accounts management tests
- command registration/smoke tests

Architecture constraints:
- keep commands and views thin
- keep data access in repository/DAL/service ownership
- no direct SQL in commands or views
- create a dedicated Preferences model/renderer/helper module only if repository inspection proves
  that extending current shared files would materially worsen ownership
- do not create a broad summary-card renderer or view framework
- reuse proven avatar, text-fitting, fallback, attachment, timeout, and selector helpers where they
  genuinely fit
- capture useful out-of-scope debt as structured deferred optimisations instead of widening 5E

Escalate and stop before implementation if:
- the backdrop is missing, corrupt, non-opaque, or not exactly 1702x924
- current saved timezone cannot produce authoritative local time without a new dependency or
  persistence change
- the current Inventory visibility consequence cannot be stated accurately
- moving Update VIP requires changing registry authority, VIP meaning, SQL schema, or account
  lifecycle rules
- Manage Accounts cannot accommodate the task without a material component/workflow redesign
- current clear semantics would be changed by the proposed field-specific presentation
- a broad shared framework appears necessary
- an out-of-scope defect must be fixed to deliver safely

Do not silently omit the local-time hero, retain VIP in Preferences, add a direct public toggle,
substitute a new setting, or widen the scope to work around a blocker.

Out of scope:
- new preference/profile fields
- preferred/default governor
- 12/24-hour preference
- application-wide local-versus-UTC toggle
- automatic timezone/location detection
- full interface localization/translation
- Reminder Centre UTC-policy changes
- per-governor Inventory visibility
- privacy audit history or sharing telemetry
- new VIP source/default/range/business definition
- account registry, ownership, claim, slot, lookup, replace, or remove redesign
- SQL schema/table/view/index/procedure changes or data migration
- Inventory reports/imports/ranges/exports/filenames/Google Sheets changes
- command additions, renames, redirects, or removals
- broad renderer/view framework
- changes to Reminders, Phase 5F Inventory summary, Phase 5G Exports summary, History, or Inspect

Command surface:
- no new top-level command
- no new /me grouped subcommand
- preserve /me preferences, /me accounts, legacy redirects, decorators, private response behavior,
  command-cache behavior, and usage-log identity
- update canonical documentation so regional profile/Inventory privacy belong to Preferences and VIP
  editing belongs to Manage Accounts
- run command registration validation and focused registration tests

Required automated coverage:
- complete/partial/all-unset profile combinations
- valid IANA timezones in standard time and DST
- UTC, positive/negative, half-hour, and quarter-hour offsets where supported
- local date differing from UTC date
- missing/unavailable timezone and unknown saved catalog values
- exact profile coverage and Settings Insight priority
- one injected generated_at driving hero and footer
- no location/timezone mismatch inference
- exact 1702x924 render and stable filename
- strict backdrop size/opacity validation
- PRIVATE/PUBLIC pills, local/UTC hero, long/Unicode labels, two-line privacy copy, maximum insight
- avatar success/fallback and duplicate-safe Kingdom identity
- same-payload fallback; render/file/send/edit failures; attachment replacement and stream close
- direct entry and selected-Dashboard return
- no/one/multiple/>25 governors do not filter Preferences
- no Change Governor, no Inventory nav, one Manage settings action, no old three main actions
- author/foreign/stale/forged/superseded/concurrent/timeout/cancellation paths
- field save and field-specific clear/Not set flows
- child replacement, reflected state, Back refresh
- public/private confirm/cancel/stale revalidation/failure/no-public-post behavior
- no VIP in Preferences card/fallback/Manage Settings
- Update VIP inside Manage Accounts for zero/one/multiple/>25 governors
- preselection prohibition, access recheck, stale/foreign/forged/concurrent denial
- unchanged VIP values/range/not-set/save behavior
- unchanged Accounts find/register/replace/remove/ownership/claim/slot flows
- Account Summary and Inventory VIP compatibility

Repository gates, using actual supported paths:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe -m pre_commit run -a
- .\.venv\Scripts\python.exe -m pytest -q tests

Visual matrix at original 1702x924, Discord desktop, and mobile preview:
1. Private Inventory; all three values set; DST-active timezone.
2. Public Inventory; all three values set.
3. Private Inventory; timezone unset and UTC-reference hero.
4. Private Inventory; one value set.
5. All profile values unset.
6. Invalid/unavailable saved timezone or catalog value.
7. Long/Unicode display name and long labels.
8. Maximum intended Settings Insight and two-line privacy consequence.
9. Avatar-unavailable fallback.
10. Same-payload fallback embed.

Manual mirror Discord smoke must cover:
- private standalone /me preferences card
- avatar/identity, privacy pill, profile coverage, local time/offset, and refreshed UTC timestamp
- DST correctness and UTC fallback
- truthful public/private consequence copy
- no VIP, direct toggle, or Change Governor on Preferences
- approved navigation rows and one Manage settings action
- Manage Settings in-place save, field-specific clear, Back refresh
- visibility confirmation/cancel/stale revalidation/reflected host refresh
- Manage Accounts -> Update VIP with explicit governor and VIP selection
- unchanged account tasks
- selected-Dashboard return without Preferences filtering or VIP preselection
- graceful timeout and late-interaction rejection
- same-payload fallback
- desktop/mobile readability

Before PR handoff:
- run Codex Security because the slice touches privacy mutation, author-gated interactions,
  governor access, persisted settings, and file/attachment handling
- run k98-pr-review
- record exact test counts/skips and visual sample manifest
- do not promote until operator smoke and visual acceptance pass

Required final delivery output:
1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes and validation evidence
6. Helpers Reused
7. Product-contract confirmation and approved deviations
8. Refactor Findings
9. Focused/full tests and results
10. Visual sample manifest
11. Codex Security and K98 PR-review results
12. Mirror deployment and operator smoke
13. Production promotion/deployment steps
14. Rollback plan
15. Deferred Optimisations
16. Phase 5F handoff status

Expected rollback is code-only: revert the Phase 5E changes and restore the previous Preferences
renderer/action composition and Update VIP entry point. No data rollback should be required because
profile, visibility, VIP, registry, and SQL contracts remain unchanged.

After the audit, stop and ask for approval before architecture execution. Do not begin coding in the
first response.
```
