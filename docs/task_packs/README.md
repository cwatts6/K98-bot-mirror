# Task Packs

Active task packs live in this folder. Completed DL_bot upload-routing, startup/lifecycle, and
completed command-platform programme packs were moved to `archive/` to keep the active task-pack
list focused.

Do not continue the completed DL_bot programme as Phase 6M. Open a fresh task pack for the
queue-domain redesign, optional SQL-backed queue persistence, SQL deployment workflow, or pinned
calendar tracker atomic-write hardening when one of those programmes is approved.

The Command Platform Audit & Optimisation Programme is complete. Its programme pack, phase packs,
and chat starters are archived under `archive/`.

Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 5A, Phase 6, Phase 7, the programme pack, and
the superseded command-surface balancing audit pack are archived as execution records.

Phase 7 was completed in PR 139 (`codex/command-platform-phase-7-governance`), merged, and pushed
to production on 2026-06-02. It closed the Command Platform Audit & Optimisation Programme by
adding command-registration validator baseline enforcement, JSON/Markdown inventory artifact
output, pre-commit validation, focused command-governance CI, and command-change checklist
material.

Player self-service workflow redesign and public calendar/KVK calendar UX redesign remain separate
deferred optimisation programmes, not additional command-platform phases.

KVK Player Experience Redesign is active. Phase 1 audit/design, Phase 2A Admin Collision
Resolution, Phase 2B Player `/kvk` Scaffold, Phase 3 Modern `/kvk stats` Visual Card, Phase 3B
Stats Card Polish and Secondary Cards, Phase 3C Overall Rank and Card Polish, Phase 4A Modern
`/kvk targets`, and the full Phase 4B modern `/kvk history` rollout are complete.
Phase 2A moved admin/operator commands from `/kvk ...` to `/kvk_admin ...` in PR 140. Phase 2B
added the player `/kvk stats`, `/kvk targets`, `/kvk history`, and `/kvk rankings` scaffold in PR
141, then was promoted to production. Phase 3, Phase 3B, and Phase 3C delivered the modern
`/kvk stats` image-card rollout, mode-specific card backgrounds, secondary More Stats and History
cards, SQL-backed KVK overall rank context, and production promotion in PRs 142, 143, and 144.
Phase 4A delivered the modern `/kvk targets` card, target service/DAL/payload boundary, fallback
handling, and production promotion in PR 145. Phase 4Bi/4Bii/4Biii delivered the modern
`/kvk history` card journey: Last 3 History, Summary, Trends, CSV export controls, `/kvk stats`
History-button removal, and the retained legacy `/mykvkhistory` graph/table/CSV path. Phase 4Biv
removed the stale command-level selector option, preserved explicit governor lookup, polished CSV
export data with healed, KillPoints, PreKVK, Honor, and derived `TankingScorePct`, and passed
production smoke testing.

Phase 4 is complete. Use the programme pack for the next active programme phase, Phase 5 unified
`/kvk rankings` visual/UX polish. The Phase 4B task pack remains as the delivery record:

`Codex Task Pack - KVK Player Experience Redesign Phase 4B History Audit and Optioneering.md`
