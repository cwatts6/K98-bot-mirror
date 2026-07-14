# Codex Task Pack - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card`
- Date: `2026-07-13`
- Owner/context: Follow-on from completed and operator-accepted GovernorOS v2 Phase 5B.
- Task type: `visual/product workshop | generated Accounts card | standalone Discord delivery`
- One-pass approved: `No`
- Implementation approved: `No - work through operator ideas and approve the visual/product contract first`
- Status: `next - scope prepared; awaiting operator ideas, prototype, and approval checkpoints`

## 2. Required Reading

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5B Premium Inventory Report Backdrops and Visual Alignment.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 4 Premium Governor Dashboard Renderer.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 6 Guided Management Cards and Workflow Simplification.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Use:

- `k98-architecture-scope`
- `k98-discord-command-feature`
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review`
- `codex-security:security-scan` when available

## 3. Context

GovernorOS v2 Phases 1-5B are complete. Phase 4 established the premium standalone generated-card,
blue-navigation, same-payload fallback, attachment cleanup, avatar, and governor-selector contract.
Phase 5B applied the premium standard to Inventory reports and completed operator smoke/final visual
acceptance on 2026-07-13.

`/me accounts` already works and is well tested. It is a private Discord-user/all-linked-governor
summary page backed by the existing Player Self-Service summary payload. Its generated 1702x924 PNG
uses `assets/me/cards/me accounts.png`, is sent inside an attachment embed, and has a concise private
embed fallback. The page has global navigation plus one `Manage` action. `Manage` opens the existing
guided private Governor ID lookup, add/register, replace, and remove journey with confirmation,
current-state revalidation, and host-card refresh.

The operator has improvement ideas to work through. Phase 5C starts as a visual/product workshop;
it must not assume that the existing background, information hierarchy, or proposed composition is
approved merely because this scope pack exists.

## 4. Objective

Create a premium Accounts summary card and standalone private delivery that feels consistent with
the accepted GovernorOS dashboard and Inventory reports, while preserving every current account,
privacy, navigation, fallback, and guided-management behavior.

## 5. Current Contract To Preserve

### Page semantics

- `/me accounts` summarizes the invoking Discord user's complete linked-governor registry.
- It is not selected-governor scoped and must not be filtered by the optional dashboard governor.
- It remains private/ephemeral and author-gated.
- Current summary fields are main-account label/state, linked count/state, account names, and the
  service-owned next action/guidance.
- Empty, unavailable, one-account, and multiple-account states remain honest and explicit.

### Account management

- `Manage` remains the only Accounts page success action unless a separate behavior change is
  explicitly approved.
- Preserve Governor ID/name lookup, available-slot selection, add/register, replace, remove,
  confirmation/cancellation, current-state revalidation, and mutation result wording.
- Preserve ownership/claim rules, slot definitions, registry authority, DAL/service boundaries,
  audit behavior, and host-card refresh after a successful mutation.
- Foreign, stale, forged, timed-out, cancelled, duplicate, and concurrent actions remain privately
  denied or safely suppressed.

### Current renderer/delivery

- Current output is 1702x924 with stable filename `me_accounts_<discord_user_id>.png`.
- Current runtime background is `assets/me/cards/me accounts.png`; it is an existing asset, not an
  automatically approved Phase 5C composition.
- Rendering occurs off the event loop through `player_self_service/page_cards.py`.
- Successful output is currently an embed-wrapped `attachment://` image.
- `build_accounts_embed(...)` is the private same-payload fallback.
- Existing edit/fallback paths clear prior attachments and close file streams.

## 6. Approval-Gated Visual/Product Workshop

Before implementation, review the operator's ideas and provide an architecture/scope response plus
at least one representative prototype or wireframe. Confirm:

1. The information hierarchy: player identity, main governor, linked count, named accounts/slots,
   open capacity, overall status, and Manage guidance.
2. Which desired information already exists in the authorized summary payload. Any new field,
   slot-level property, capacity calculation, SQL query, or business rule must be called out and
   split into a separately approved data/behavior slice before renderer work.
3. Backdrop provenance and whether `me accounts.png` is retained/reworked or replaced.
4. Runtime dimensions. Default is the current 1702x924 and stable filename; any new dimension
   requires explicit approval after original-size, Discord desktop, and Discord mobile comparison.
5. Runtime versus source-master policy. Runtime uses only the approved production-size asset;
   source masters are not loaded by the bot.
6. Player Discord avatar placement and safe local fallback.
7. Account/slot iconography, panel opacity, typography, contrast, long-name fitting, empty state,
   unavailable state, and mobile legibility.
8. Exact Discord component rows and labels. Buttons/dropdowns remain real Discord components and
   are not painted into the image.
9. That implementation is presentation/delivery-only unless the operator explicitly expands scope.

Do not treat discussion of an idea as approval to implement it. Record the accepted decisions in
this task pack before coding.

## 7. Target Presentation And Delivery Contract

Default target after approval:

- Render a standalone 1702x924 PNG with stable filename for successful Accounts output.
- Remove the successful-image embed container so Discord displays the attachment at full width.
- Retain the current private Accounts embed as fallback from the same already-loaded summary.
- Do not refetch data merely because avatar retrieval, rendering, file creation, edit, or delivery
  fails.
- Use the invoking player's Discord avatar best-effort, capped to an appropriate size and timeout,
  with a fixed local page/KD98 fallback.
- Preserve Unicode/grapheme-safe display-name and governor-name rendering with fitted bounds.
- Show only genuine payload values and service-owned guidance; do not invent governors, open slots,
  status, counts, or action results for visual balance.
- Preserve stable attachment replacement and stream cleanup on success, fallback, stale
  suppression, cancellation, timeout, navigation, and account-mutation refresh.

## 8. Navigation And Governor Context

Global navigation remains:

- Row 0, blue primary: `Accounts`, `Reminders`, `Preferences`.
- Row 1, secondary: `Dashboard`, `Inventory`, `Exports`.
- Accounts is disabled while active.
- Page-specific `Manage` remains a success action below global navigation.

Governor rules:

- Do not add `Change Governor` to Accounts, including for users with more than 25 governors.
- Accounts represents all governors linked to the Discord user.
- `dashboard_governor_id` may be carried only as return context when Accounts was opened from a
  selected dashboard.
- `Dashboard` returns to that governor after a fresh access check when context is valid.
- Direct `/me accounts` entry has no implicit selected governor; Dashboard uses the existing
  no/one/multiple-governor journey.
- Retained context must not filter Accounts or bypass any account/governor authorization rule.

## 9. Architecture Direction

- Keep account summaries and mutations in the existing services/DAL.
- Keep Discord routing, components, fallback edits, timeout behavior, and author gating in the
  existing views.
- Keep visual composition in the established page-card renderer unless the approved prototype
  proves a narrow Accounts-specific renderer is safer. Do not create a broad new renderer/view
  framework in Phase 5C.
- Reuse `core.visual_text`, current attachment cleanup helpers, the current Accounts fallback embed,
  and the Governor dashboard/Inventory avatar-read pattern where appropriate.
- Do not import renderer-private helpers across renderer families.

## 10. Data, SQL, Persistence, And Security

No SQL, DAL query, model field, payload field, account slot, registry rule, cache, persistence,
startup, scheduler, config, command-registration, or version change is expected.

If the approved design needs data not present in `AccountStatus`, stop and scope it separately.
Validate any later SQL-facing expansion against `C:\K98-bot-SQL-Server` before implementation.

Run Codex Security review when available because private Discord content, user-controlled names,
avatar/network reads, local assets, attachments/streams, fallbacks, guided account mutations, and
author-gated interactions are in regression scope.

## 11. Compatibility Contract

- `/me accounts` remains private and all-linked-governor scoped.
- Existing legacy redirects to `/me accounts` remain unchanged.
- Account lookup/add/replace/remove/confirmation behavior remains unchanged.
- Current summary values, empty/unavailable semantics, filename, and default dimensions remain
  unchanged unless an explicit visual checkpoint approves dimensions.
- Navigation to Reminders, Preferences, Dashboard, Inventory, and Exports remains available.
- No Change Governor on Accounts.
- Same-payload fallback, attachment replacement, and stream cleanup remain mandatory.
- No change to other `/me` pages, direct Inventory reports, `/myinventory`, exports, or Google
  Sheets behavior.

## 12. Do Not Do In Phase 5C

- No SQL, DAL query, account model/payload field, slot, claim/ownership, lookup, calculation,
  persistence, or registry redesign.
- No command registration, redirect, visibility, permission, author-gating, interaction, or guided
  Manage redesign without separate approval.
- No Reminders, Preferences, Inventory summary, Exports summary, Dashboard, direct report, History,
  Inspect, Export Stats, Last Login, Olympia, CrystalTech, website/API, or public `/kvk` change.
- No broad visual-card framework or renderer-private helper sharing.
- No fake account data, dummy slots, invented status, or decorative controls presented as actions.

## 13. Test Strategy

Focused coverage should include:

- exact approved dimensions and stable `me_accounts_<discord_user_id>.png` filename
- approved backdrop/avatar/fallback selection
- zero, one, multiple, long-name, Unicode, partial, and unavailable summaries
- genuine main/linked/name/status/action-guidance accuracy
- standalone successful delivery and same-payload private embed fallback
- direct `/me accounts` entry and selected-dashboard-to-Accounts-to-Dashboard return
- absence of Change Governor for one, multiple, and more-than-25 linked governors
- unchanged global button rows, active disabled state, and `Manage` placement
- unchanged lookup/add/replace/remove/confirmation/cancellation/current-state revalidation
- mutation host-card refresh in standalone format
- avatar missing/corrupt/timeout, renderer failure, edit/delivery failure, fallback
- attachment replacement and stream cleanup across success/failure/cancellation/timeout/stale paths
- foreign, forged, stale, timed-out, cancelled, duplicate, and concurrent interaction denial
- original-size, Discord desktop, and Discord mobile visual samples
- existing page-card, player-self-service view, account service, UI import, command registration, and
  legacy redirect regressions

Repository gates:

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

## 14. Manual Discord Smoke

After implementation approval and delivery:

1. Direct `/me accounts` opens privately with no selected-governor filtering.
2. Zero, one, and multiple linked-account cards show accurate content.
3. The standalone card is readable at desktop, mobile, and original size.
4. `Manage` lookup/add/replace/remove/cancel/confirm journeys remain correct.
5. Successful mutation refreshes the host card without stale attachments.
6. Dashboard return preserves valid selected context when Accounts was opened from a dashboard.
7. Direct entry returns through the normal dashboard governor-resolution journey.
8. Change Governor is absent for one, multiple, and more-than-25 governors.
9. Other global navigation buttons retain page and attachment behavior.
10. Avatar fallback, renderer fallback, timeout, foreign, stale, and concurrent paths are safe.

## 15. Acceptance Criteria

- [ ] Operator ideas and visual hierarchy are reviewed before implementation.
- [ ] Backdrop provenance, runtime dimensions, master policy, avatar, icons, and typography are approved.
- [ ] Every requested visual value is mapped to an existing authorized payload field or split out.
- [ ] Successful Accounts output is a premium standalone private PNG with stable filename.
- [ ] Same-payload private embed fallback and all attachment/stream cleanup paths remain tested.
- [ ] Accounts remains all-linked-governor scoped with no Change Governor.
- [ ] Dashboard return context works without filtering Accounts or bypassing access.
- [ ] Guided Manage behavior and host-card refresh remain unchanged.
- [ ] No SQL/DAL/service/payload/registry/command/permission/interaction expansion is introduced.
- [ ] Focused/full validation, visual samples, security review, and operator smoke are recorded.
- [ ] Programme, briefing, canonical, task-pack, starter, and deferred docs reflect delivery.

## 16. Remaining Summary-Card Handoff

After Phase 5C completes, execute separately:

- Phase 5D: Premium Reminders Summary Card
- Phase 5E: Premium Preferences Summary Card
- Phase 5F: Premium Inventory Summary Card
- Phase 5G: Premium Exports Summary Card

Each page reuses the accepted shared format but receives its own asset/content/action approval. None
shows Change Governor; each preserves its current data and behavior contract.
