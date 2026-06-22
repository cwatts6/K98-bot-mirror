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

Player Self-Service Command Centre status:

- Phase 1 audit/design is complete and archived.
- Phase 2 `/me` Command Shell and Navigation Foundation is delivered in mirror PR #164 and
  production PR #472, smoke tested successfully, and awaiting manual merge/promotion.
- The active next phase is Phase 3 Modern Account Centre.
- Active Phase 3 files:
  - `Codex Task Pack - Player Self-Service Command Centre Phase 3 Modern Account Centre.md`
  - `Codex Chat Starter - Player Self-Service Command Centre Phase 3 Modern Account Centre.md`
- Active programme file:
  - `Player Self-Service Command Centre - Programme Pack.md`
- Completed Phase 1/2 execution records are archived under `archive/`.

KVK Player Experience Redesign Phase 7 redirect/deprecation rollout is complete and awaiting PR
merge/promotion. Phase 1 audit/design, Phase 2A
Admin Collision Resolution, Phase 2B Player `/kvk` Scaffold, Phase 3 Modern `/kvk stats` Visual
Card, Phase 3B Stats Card Polish and Secondary Cards, Phase 3C Overall Rank and Card Polish,
Phase 4A Modern `/kvk targets`, the full Phase 4B modern `/kvk history` rollout, and Phase 5A
through Phase 5H unified `/kvk rankings` delivery, and Phase 6 admin command hardening are
complete.
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
production smoke testing. Phase 5A delivered the `/kvk rankings type:records` KD98 Hall of Fame
Top 10 single-KVK records foundation, shared rankings payload/DAL/service/rendering pieces,
Top 10/25/50 primary control policy, command reference updates, and review hardening in mirror
PR 152 and production PR 461. Phase 5A was smoke tested successfully and pushed to production.
Phase 5B delivered the shared `/kvk rankings` current-browser foundation for KVK, Honor, and
PreKvK in mirror PR 153 and production PR 462, including mode/metric selectors, Top 10/25/50
controls, no primary Top 100, PreKvK unified embed output under `/kvk rankings`, preservation of
the image-based legacy `/prekvk report`, Honor mode guard hardening, and production smoke-tested
table layout polish.
Phase 5C delivered the current KVK Top 10 visual ranking card in mirror PR 154 and production PR
463, including Kills default, KVK card metrics for Kills, % Kill Target, Deads, DKP, Acclaim, and
Tanking Score, embed fallback, Top 25/50 compact browser preservation, Top 100 exclusion, legacy
command preservation, image-based legacy `/prekvk report` preservation, production smoke testing,
and visual polish.
Phase 5D delivered the Hall of Fame records Top 10 visual cards in mirror PR 155 and production PR
464, including all existing records metrics, single-KVK record wording, metric-specific qualifying
record counts, records Top 10-only controls, embed fallback, repeated-governor preservation,
missing historical metric exclusion, production smoke testing, and visual polish.
Phase 5E delivered Honor and PreKvK Top 10 visual cards in mirror PR 156 and production PR 465,
preserving current KVK cards, Hall of Fame cards, Top 25/50 compact browser output, records Top
10-only controls, Honor channel gating, legacy commands, and image-based legacy `/prekvk report`.
Phase 5F-1 delivered private My Rank / Find Me in mirror PR 158 and production PR 466 for current
KVK, Honor, and PreKvK rankings, with single-account, multi-account, not-ranked, no-account, and
missing-data paths smoke tested successfully in production.
Phase 5F-2 delivered private Full List CSV export in mirror PR 159 and production PR 467 for
current KVK, Honor, and PreKvK rankings, with clean leaderboard-only CSV columns, formula-leading
cell escaping, private error handling, no primary Top 100 reintroduction, restored KVK `Kill
Points` and `Healed` metric selection, and successful production smoke testing.
Phase 5G delivered rankings wrap-up polish for Honor Top 25/50 compact values, PreKvK Top 25/50
compact alignment, near-billion value unit preservation, display-width-aware rows for
wide/special-character governor names, and current KVK Top 10 podium centering, while preserving
My Rank, Full List CSV, Top 10 cards, Top 25/50 controls, Top 100 exclusion, records Top 10-only
behavior, Honor gating, legacy ranking commands, and image-based legacy `/prekvk report`.
Phase 5H delivered ranking-card render/load performance optimisation for current KVK, Honor,
PreKvK, and Hall of Fame records Top 10 visual cards. Smoke testing confirmed the improvement was
solid and noticeable across all visual cards. No active Phase 5 delivery deferred optimisations
remain. The retained legacy-ranking consolidation/deprecation item is future Phase 7 rollout work,
not a Phase 5 closure blocker.
Phase 6 delivered `/kvk_admin` operator hardening in mirror PR 162 and production PR 470,
preserving the existing seven subcommands, permissions, channel restrictions, command
registration, service/DAL boundaries, SQL/import/recompute/export semantics, stats cache
behaviour, and Google Sheets contracts. Manual smoke testing completed successfully, and no active
Phase 6 admin/operator deferred optimisations remain. The retained legacy-ranking
consolidation/deprecation item has now been promoted into the Phase 7 task pack.
Phase 7 delivered tested deprecated redirects for `/mykvkstats`, `/mykvktargets`,
`/mykvkhistory`, `/kvk_rankings`, `/honor_rankings`, and `/prekvk report`, plus channel-limit
consistency for the canonical `/kvk` commands. Final removal of the deprecated command paths is
tracked in `docs/reference/deferred_optimisations.md` after the agreed no-feedback window.

Completed KVK Player Experience Redesign Phase 1 through Phase 7 execution records are archived
under `archive/`. The programme pack remains active until the Phase 7 PRs are merged and the
later final-removal cleanup is explicitly approved.
The Phase 4B task pack remains as the history delivery record in the archive:

`archive/Codex Task Pack - KVK Player Experience Redesign Phase 4B History Audit and Optioneering.md`

Latest completed starter:

`archive/Codex Chat Starter - KVK Player Experience Redesign Phase 5H Ranking Card Performance Optimisation.md`

Next active work:

Player Self-Service Command Centre Phase 3 Modern Account Centre is active. KVK final removal of
temporary deprecated command paths remains captured as a deferred cleanup item for execution after
the no-feedback window and operator approval.
