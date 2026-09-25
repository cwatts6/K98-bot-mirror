# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 3 Governor Selector and Dashboard Shell

Status: archived execution starter. Phase 3 completed and operator smoke passed on 2026-07-10 in
mirror PR #217 and production PR #524. Phase 4 has also completed; use the active Phase 5A direct
inventory report starter for the next slice.

The copy/paste block below is retained as historical execution context and should not be used to
start new work.

## Copy/Paste Starter

```text
Codex, start Player Self-Service Command Centre v2 Phase 3: Governor Selector and Dashboard Shell.

Context:
Phase 2 is complete. It delivered typed governor dashboard context/payload models, linked-governor
resolution for no/one/multiple states, default-deny self-view access, explicit gating for future
inspect mode, a validated dashboard DAL/service, self-view versus inspect-safe separation, null-safe
field handling, and focused tests. Operator smoke testing confirmed all existing /me and legacy
commands work, and all pytest and repository validation scripts passed.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 3 Governor Selector and Dashboard Shell.md
- docs/task_packs/archive/Player Self-Service Command Centre v2 Phase 1 Governor Dashboard Product Blueprint and Audit Report.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 2 Governor Context and Dashboard Data Foundation.md
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Use these skills:
- k98-architecture-scope
- k98-discord-command-feature
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review
- codex-security:security-scan

Approval checkpoint:
The existing registry linkage is the authorization source used by current self-service commands.
Confirm that it remains the approved authority for this Phase 3 rollout. If stronger governor
ownership verification is required first, stop and scope that as a separate hardening slice.

Objective:
Make /me dashboard governor-first by wiring the Phase 2 resolution and payload services into a
private Discord selector and fallback dashboard shell.

Selector decision:
- Phase 2 created no Discord selector.
- Add a dashboard-specific, author-gated selector/view for Phase 3.
- Do not wire account_picker.AccountPickerView directly: it is a one-shot picker with bundled
  lookup/register/refresh behavior and does not fit in-place dashboard context switching.
- Reuse Phase 2 governor options/context/access services plus established interaction-safety,
  timeout, and message-edit patterns.

Required journey:
1. No linked governors: private setup shell with Accounts as the primary action.
2. One linked governor: open its dashboard shell directly.
3. Multiple linked governors: show the private selector before fetching dashboard data.
4. Selected governor: recheck linkage/access, build the Phase 2 payload, and edit the private
   message in place.
5. Change Governor: available only for multiple linked governors and returns to the selector.
6. Denied/unavailable/stale/foreign interactions: fail privately and safely.

Dashboard shell:
- Show the approved Phase 2 fields in a concise fallback embed/shell.
- Include governor identity, self-view account type/optional VIP, alliance, power, kill points,
  highest acclaim, dead, helps, healed, Ark joined/won/win ratio, Autarch count, Conduct Score,
  Civilisation, and freshness where available.
- Keep missing values safe and predictable.
- Exclude Olympia completely.
- Keep the shell renderer-independent so Phase 4 can replace it with the premium PNG card.

Do not do in this phase:
- Do not build the final premium PNG renderer.
- Do not add /me resources, /me materials, /me speedups, /me history, or /me inspect.
- Do not enable unlinked inspect mode.
- Do not alter Accounts, Reminders, Preferences, Inventory, or Exports semantics.
- Do not redirect, remove, or alter /my_stats, /myinventory, /stats player, /player_profile,
  /mykvkcrystaltech, or /kvk history.
- Do not change inventory output, export schemas, or stats export semantics.
- Do not add Olympia fields or placeholders.
- Do not add SQL schema changes.

Expected command surface impact:
- No top-level command count change.
- No /me grouped subcommand count change.
- /me dashboard visible behavior and command version change only.

Test requirements:
- no/one/multiple/unavailable/denied states
- author gate, stale interaction, and forged/unlinked selection denial
- access recheck before payload fetch
- one-account direct open and multi-account Change Governor
- safe missing data, missing VIP, and zero Ark joined
- no Olympia fields/text
- private response behavior
- existing /me and legacy command compatibility
- command registration and decorator/version checks

Run focused tests selected from touched files plus:
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests

Run Codex Security review because access, private data, Discord interactions, and user-controlled
selector values are in scope.
```
