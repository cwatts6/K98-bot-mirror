# KVK Player Experience Redesign — Programme Pack

## 1. Programme Header

- Programme name: `KVK Player Experience Redesign`
- Date: `2026-06-03`
- Owner/context: K98 Bot command-surface and player-output modernisation
- Programme type: Product UX / Discord command architecture / visual output redesign / deferred optimisation programme
- One-pass approved: No

## 2. Programme Vision

Modernise the KVK player experience so the most-used KVK commands feel like a coherent product rather than a set of legacy data-dump embeds.

The end state should give players a clear `/kvk` command surface, modern generated visual cards, consistent terminology, and joined-up navigation between personal stats, targets, history, and rankings. The visual language should also prepare the bot for the longer-term KD98 website/webapp direction.

## 3. Why This Programme Exists

The current player-facing KVK outputs are useful but visually dated compared with the newer inventory image outputs. Commands such as `/mykvkstats`, `/mykvktargets`, `/mykvkhistory`, `/kvk_rankings`, `/honor_rankings`, PreKVK ranking/report commands, `/mygovernorid`, `/my_stats`, and `/player_profile` grew organically across several delivery phases.

The result is that players need to remember multiple command names, outputs are inconsistent, and KVK-specific journeys are not grouped around how users think:

- How am I doing in this KVK?
- What are my targets?
- What is my KVK history?
- Where do I rank?
- What should I do next?

This programme focuses first on the KVK-specific player surface because these commands are high-value, high-traffic during KVK, and closely related visually and functionally.

## 4. Target Command Model

### Player-facing command group

Target new player command group:

```text
/kvk stats
/kvk targets
/kvk history
/kvk rankings
```

Optional later expansion after the core group is stable:

```text
/kvk profile
/kvk help
/kvk settings
```

### Admin/operator command group

Delivered Phase 2A admin command group:

```text
/kvk_admin test_export
/kvk_admin refresh_stats_cache
/kvk_admin recompute
/kvk_admin export_all
/kvk_admin list_scans
/kvk_admin window_preview
/kvk_admin test_embed
```

The admin group is intentionally separated from the player `/kvk` group so player journeys remain clean and admin/operator tools do not clutter the public command surface. Phase 2A delivered this split in PR #140; `/kvk` is now reserved for the player scaffold.

## 5. Target User Journeys

### `/kvk stats`

Primary personal KVK dashboard.

Should answer:

- Who is this governor?
- Which KVK and scan is this based on?
- What is their KVK rank?
- How much KP have they gained?
- How much power have they gained/lost?
- How much Acclaim/contribution have they gained where the approved SQL output contract supports it?
- What is their likely playstyle?
- Are they performing well against expectations?

Target output style:

- modern generated image card
- KVK/camp themed background
- large headline metrics
- governor avatar/emblem
- rank badge
- colour-coded metric tiles
- scan freshness footer
- optional buttons to jump to targets/history/rankings

### `/kvk targets`

Personal KVK target and progress view.

Should answer:

- What are my active targets?
- How far through each target am I?
- What remains?
- Am I complete, on track, or behind?
- Is there a reason no target is set?

Target output style:

- progress-focused card or embed+image hybrid
- kill/dead/DKP progress blocks
- clear explanations for exempt, off-season, below-power, not-in-matchmaking, or unknown governor states

### `/kvk history`

Historical KVK performance view.

Should answer:

- How have I performed across recent KVKs?
- What was my rank, KP, deads, DKP, honor, and PreKVK performance?
- Am I improving?

Target output style:

- table/timeline first
- optional generated chart image later
- should preserve accessibility for longer historical data

### `/kvk rankings`

Unified KVK ranking browser.

Should replace or consolidate:

```text
/kvk_rankings
/honor_rankings
/prekvk ranking/report commands
```

Potential ranking modes:

- KVK overall
- kills / KP
- deads
- DKP
- honor
- PreKVK
- power
- pass windows
- acclaim/contribution where approved

Target output style:

- paginated embed first
- buttons/select menus for ranking type
- optional generated top-10/top-20 visual cards later

## 6. Visual Direction

The programme should move from traditional Discord text embeds toward generated image cards where the output benefits from layout, branding, visual hierarchy, and progress presentation.

The design direction should align with the modern inventory output approach and the planning mock-up shared during programme creation. The first implementation should define reusable visual primitives rather than hardcoding a one-off image.

Recommended reusable visual primitives:

- KVK card background provider
- governor identity block
- stat tile component
- progress bar / completion indicator
- rank badge
- freshness footer
- disclaimer/warning ribbon
- KVK phase/status chip
- metric colour policy
- image export helper with deterministic test mode

## 7. Design Principles

1. **Player-first command paths** — commands should map to player questions, not implementation history.
2. **Parallel migration** — new `/kvk` commands should be built alongside old commands until validated.
3. **No sudden removals** — legacy commands should remain during rollout, then redirect/deprecate later.
4. **Modern outputs without misleading metrics** — style must not hide unclear or unstable semantics.
5. **Preserve service/DAL boundaries** — commands and views stay thin.
6. **SQL source-of-truth validation** — KVK schema and procedure assumptions must be checked against `C:\K98-bot-SQL-Server`.
7. **Discord-safe UX** — button persistence, interaction safety, permissions, and command registration limits must remain protected.
8. **Website-ready thinking** — data shape and visual language should be reusable for the future KD98 webapp.

## 8. Programme Phases

### Phase 1 — Audit and Design Only

Audit the current KVK player commands, admin KVK commands, output formats, SQL/DAL/service dependencies, usage data, and visual generation options.

Deliver:

- current command map
- target command model
- player journey map
- admin command separation proposal
- output inventory
- metric/terminology review
- visual architecture proposal
- migration/deprecation plan
- implementation phase plan

No code changes.

### Phase 2A — Admin `/kvk` Collision Resolution

Status: complete. Delivered and merged in PR #140.

The former admin/operator `/kvk ...` commands were moved to `/kvk_admin ...` before the player scaffold was introduced:

```text
/kvk_admin test_export
/kvk_admin refresh_stats_cache
/kvk_admin recompute
/kvk_admin export_all
/kvk_admin list_scans
/kvk_admin window_preview
```

Old `/kvk ...` admin paths were intentionally removed from the active command surface. Permissions, channel restrictions, logging, usage tracking, service/DAL ownership, command-cache governance, and operator reference documentation were updated without changing SQL, import, recompute, export, or Google Sheets behaviour.

### Phase 2B — New `/kvk` Player Command Group Scaffold

Create the new `/kvk` player group in parallel with existing commands.

Initial subcommands:

```text
/kvk stats
/kvk targets
/kvk history
/kvk rankings
```

The first scaffold should reuse existing services and output behaviour as much as possible. The goal is safe command-surface migration, not visual redesign.

Legacy commands remain live.

Approved Phase 2B details:

- `/kvk rankings` should include KVK, honor, and PreKvK modes from the first scaffold.
- `/kvk stats` should keep private account selection while posting selected single-account stats publicly.
- KVK targets service/DAL cleanup belongs inside this programme.
- Acclaim/contribution metrics belong inside this programme after source-of-truth validation.

### Phase 3 — Modern `/kvk stats` Visual Card

Build the first modern KVK visual card for `/kvk stats`.

This phase establishes reusable card-generation primitives, KVK branding, metric tile patterns, and testable output contracts.

Before rendering, define a KVK stats service payload dataclass that normalizes governor identity, scan freshness, KVK rank, metric deltas, targets, Acclaim/contribution where approved, and warning states. Keep cache access in data/service layers and test payload construction separately from image rendering.

### Phase 4 — Modern `/kvk targets` and `/kvk history`

Apply the visual language to targets and history.

Targets should emphasise progress and next action. History should emphasise comparability across KVKs and may remain table-first until chart/card generation is justified.

### Phase 5 — Unified `/kvk rankings` Visual/UX Polish

Polish the already-scaffolded KVK, honor, and PreKVK ranking browser.

Support dropdowns/buttons for ranking type and pagination. Keep image output optional until embed pagination is stable.

### Phase 6 — Admin Command Hardening And Legacy Operator Cleanup

Harden the delivered `/kvk_admin` operator command surface after Phase 2A.

This phase should preserve all permissions, channel restrictions, logging, and existing service/DAL ownership.

### Phase 7 — Legacy Command Deprecation and Removal

After a usage-review period:

1. announce new commands
2. change old commands to redirect/help responses
3. monitor usage
4. remove old paths only after approval

## 9. Likely Source Commands and Areas

### Player commands to audit

- `/mykvkstats`
- `/mykvktargets`
- `/mykvkhistory`
- `/mygovernorid`
- `/my_stats`
- `/my_stats_export`
- `/player_profile`
- `/player_stats`
- `/kvk_rankings`
- `/honor_rankings`
- PreKVK ranking/report commands

### Admin/operator commands to audit

- `/kvk_recompute`
- `/kvk_export_all`
- `/kvk_list_scans`
- `/kvk_window_preview`
- any KVK cache/diagnostic/import/export commands

### Likely modules to audit

- `commands/stats_cmds.py`
- `commands/registry_cmds.py`
- `commands/telemetry_cmds.py`
- `commands/calendar_cmds.py`
- `commands/events_cmds.py`
- `kvk/`
- `stats_alerts/`
- `gsheet_module.py`
- `target_utils.py`
- `governor_registry.py`
- `player_stats_cache.py`
- `ui/views/`
- `image_utils` / inventory image-generation modules if present
- command registration validation scripts

### SQL repo areas to validate

- KVK schema objects
- KVK export procedures
- KVK aggregate functions/views
- PreKVK and honor ranking objects
- player profile/latest stats views
- any cache-refresh dependencies

Validate against:

```text
C:\K98-bot-SQL-Server
```

## 10. Cross-Programme Constraints

- Do not remove old commands until explicitly approved.
- Do not change KVK import/recompute/export semantics during command scaffold work.
- Do not change Google Sheets tab names or spreadsheet contracts unless a specific phase approves it.
- Do not introduce Basic Data or summary-tab ingestion.
- Display Acclaim/contribution metrics only after metric naming and source-of-truth rules are approved and validated.
- Do not put SQL in command or view modules.
- Do not add a new top-level command group without command registration governance approval.
- Do not break existing KVK season workflows during active KVK.

## 11. Programme-Level Validation Strategy

Each implementation phase should include:

- command registration validation
- focused command tests
- permission tests
- output-shape tests
- service/DAL contract tests where touched
- SQL validation where SQL-backed contracts are changed or depended on
- architecture boundary validation
- deferred item validation
- screenshot or generated-image artifact review for visual phases

Baseline commands to consider:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests
```

## 12. Programme Acceptance Criteria

The programme is complete when:

- players can use the new `/kvk` command group for stats, targets, history, and rankings
- KVK player outputs have a consistent modern style
- `/kvk stats` has a modern generated card output
- targets and history are visually aligned with the new style
- rankings are unified behind a coherent browser
- admin KVK commands are separated from player KVK commands
- Acclaim/contribution metrics are included where the approved SQL output contract supports them
- legacy commands are safely deprecated or removed after approval
- command registration validation remains green
- all data/SQL assumptions are validated against the SQL repo
- no new direct SQL exists in command/view layers
- documentation and command references are updated

## 13. Deferred / Future Opportunities

Do not include these in the early phases unless separately approved:

- full `/my` or `/player` global self-service redesign outside KVK
- full website implementation
- live web dashboard
- image-card generator shared across every bot feature
- advanced charting for historical KVK trends
- personalised recommendations based on remaining targets
- predictive “on track” modelling using scan cadence
- public player profile redesign outside KVK
- off-season stats redesign

## 14. Suggested Next Action

Proceed with:

```text
KVK Player Experience Redesign - Phase 2B Player /kvk Scaffold
```

Phase 1 audit/design and Phase 2A admin collision resolution are complete. Phase 2B can now scaffold the player `/kvk` group while preserving the legacy flat player commands.
