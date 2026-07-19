#!/usr/bin/env python3
"""Apply the agreed GovernorOS Phase 7-9 documentation update to a local K98-bot checkout.

Run from the extracted bundle directory:

    python apply_documentation_updates.py C:\\path\\to\\K98-bot-mirror

The script is deliberately fail-closed: it validates expected headings/content before replacing them.
It is idempotent for an already-applied checkout.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys
import textwrap


BUNDLE_ROOT = Path(__file__).resolve().parent


def _dedent(value: str) -> str:
    return textwrap.dedent(value).strip("\n") + "\n"


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one old block, found {count}")
    return text.replace(old, new, 1)


def replace_between(
    text: str,
    start_marker: str,
    end_marker: str,
    new_block: str,
    *,
    label: str,
) -> str:
    if new_block.strip() in text:
        return text
    start = text.find(start_marker)
    if start < 0:
        raise RuntimeError(f"{label}: start marker not found: {start_marker!r}")
    end = text.find(end_marker, start)
    if end < 0:
        raise RuntimeError(f"{label}: end marker not found: {end_marker!r}")
    return text[:start] + new_block.rstrip() + "\n\n" + text[end:]


def append_once(text: str, line: str) -> str:
    if line in text:
        return text
    return text.rstrip() + "\n" + line.rstrip() + "\n"


def update_programme_pack(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    text = replace_between(
        text,
        "- Owner/context:",
        "- Programme type:",
        _dedent(
            """
            - Owner/context: KD98 / Kingdom 1198 player experience modernisation after the original Player
              Self-Service Command Centre programme completed in production PR #486. GovernorOS v2 is
              complete and operator accepted through Phase 6 on 2026-07-18. Phase 7 now closes the retained
              `/me` product with a visual/content consistency audit; Phase 8 modernises the one leadership
              `/stats player` journey, aligns canonical combat metrics, and removes `/player_profile`; Phase 9
              adds private `/stats kingdom`. The former `/me history` proposal is closed with no build and
              `/kvk history` remains canonical.
            """
        ),
        label="programme owner/context",
    )

    text = replace_once(
        text,
        "9. **Current KVK stays `/kvk`; personal history can live in `/me`** — current/live KVK reporting remains under `/kvk`; retrospective personal history can gain a private `/me` entry point later.",
        "9. **Keep product ownership clear** — `/me` owns personal linked-governor self-service, `/kvk history` remains the canonical KVK-history surface, and leadership review belongs under the permission-gated `/stats` group.",
        label="programme design principle 9",
    )

    text = replace_between(
        text,
        "### Planned grouped additions, subject to later phase approval",
        "### Product placement model",
        _dedent(
            """
            ### Closed KVK history placement decision

            ```text
            /me history will not be implemented.
            /kvk history remains canonical.
            ```

            No redirect, alias, implicit handoff, or Dashboard History action is added.

            ### Approved future grouped addition

            ```text
            /stats kingdom
            ```

            ### Specialist commands after Phase 7

            ```text
            /stats player      <- modernise in Phase 8
            /player_profile    <- remove in Phase 8 with no redirect
            /mykvkcrystaltech  <- retained specialist workflow
            /kvk history       <- canonical KVK-history route
            /inventory import
            /inventory audit
            ```
            """
        ),
        label="programme target additions/retirements",
    )

    text = replace_between(
        text,
        "### Product placement model",
        "## 8. Target Workflow Model",
        _dedent(
            """
            ### Product placement model

            ```text
            /me dashboard      = private selected-governor command centre
            /me accounts       = all-linked portfolio, management, Account Summary, and Download data
            /me reminders      = Discord-user reminder settings
            /me preferences    = Discord-user regional profile and LOCAL/UTC reference
            /me resources      = private selected-governor resource report and report-page export
            /me speedups       = private selected-governor speedups report and report-page export
            /me materials      = private selected-governor materials report and report-page export
            /me stats          = private selected-governor or explicit All Linked Period Performance
            /inventory import  = Inventory screenshot capture
            /inventory audit   = admin Inventory import audit
            /stats player      = Phase 8 private leadership review for one selected Governor ID
            /stats kingdom     = Phase 9 private leadership kingdom trends and completed-KVK summary
            /kvk history       = canonical public/channel-gated KVK History, Summary, Trends, and CSV
            /mykvkcrystaltech  = specialist workflow outside this programme for now
            ```

            `/me` remains the invoking player's self-service product. Arbitrary-governor and kingdom
            leadership analysis belongs under `/stats`.
            """
        ),
        label="programme product placement",
    )

    text = replace_once(
        text,
        "viewer mode: self | inspect",
        "viewer mode: self | leadership_review",
        label="programme viewer mode",
    )
    text = replace_once(
        text,
        "This context should flow through resources, materials, speedups, history, and future export actions. It should not be stored in a way that trusts stale/forged Discord component data without rechecking access.",
        "This context should flow through resources, materials, speedups, stats, and future selected-governor actions. It should not be stored in a way that trusts stale/forged Discord component data without rechecking access.",
        label="programme context preservation",
    )

    text = replace_between(
        text,
        "### Leadership inspect journey, later phase",
        "## 9. Governor Dashboard Product Model",
        _dedent(
            """
            ### Leadership player-review journey, Phase 8

            ```text
            Leadership/admin runs /stats player
            -> enter Governor ID or normalized/fuzzy governor name
            -> resolve ambiguity privately
            -> build one selected-governor leadership payload
            -> show Overview, Kingdom Activity, KVK Performance, and Player Record
            -> exclude Discord-user settings and unnecessary relationship metadata
            -> permit linked-governor navigation without aggregating their performance
            ```

            Phase 8 uses a dedicated stable-role-ID and channel gate. It does not reuse the self-view
            governor picker or create `/me inspect`.
            """
        ),
        label="programme leadership journey",
    )

    text = text.replace("- KVK History\n", "", 1)

    roadmap_block = _dedent(
        """
        ### Decision Record — KVK History Placement

        Status: `closed on 2026-07-18; no implementation required`.

        Decision:

        - `/kvk history` remains the canonical KVK-history command.
        - `/me history` will not be registered.
        - No Dashboard History action, redirect, alias, or implicit handoff is added.
        - Phase 8 and Phase 9 may reuse KVK services/data directly without creating a player-facing
          duplicate command.

        ### Phase 7 — `/me` Visual Consistency, Content Audit and Programme Closeout

        Status: `proposed; task pack and chat starter prepared`.

        Goal: complete the retained `/me` product by aligning typography, font scale, colours, panel
        borders, alignment, state pills, freshness wording, missing-value treatment, navigation, fallbacks,
        and mobile readability, using the accepted `/me stats` card as the reference.

        Deliver:

        - Audit Dashboard, Accounts, Account Summary, Reminders, Preferences, Stats, and the three direct
          Inventory reports.
        - Keep the core 1702x924 summary family closely aligned.
        - Preserve Dashboard 1180x760 and Inventory 1400x980 specialist layouts.
        - Preserve report-specific Inventory accents, charts, icons, ranges, exports, and backdrops.
        - Standardise semantic state colours, dates, numbers, units, missing values, footer/freshness copy,
          navigation, timeout copy, panel borders, and relative typography.
        - Permit a small `player_self_service/visual_contract.py` only for proven identical primitives.
        - Create before/after contact sheets and original/desktop/mobile visual matrices.
        - Make no command, SQL, DAL, payload, metric, calculation, permission, privacy, export, selector,
          or product-ownership change.

        Command impact: none; remain `37 top-level / 100 grouped / 8 me / 2 inventory`.

        Approval gate: audit first, then exact visual contract/file manifest/contact-sheet plan, then
        implementation plan. One-pass execution is not approved.

        ### Phase 8 — Leadership `/stats player` Modernisation, Canonical Combat Metric Alignment and `/player_profile` Retirement

        Status: `proposed; task pack and chat starter prepared`.

        Goal: replace fragmented leadership player tools with one private, permission-gated,
        decision-oriented review of a selected Governor ID.

        Locked command outcome:

        - Modernise existing `/stats player`.
        - Do not create `/me inspect`.
        - Remove `/player_profile` in the same accepted release.
        - No `/player_profile` redirect or alias.
        - Selected Governor ID is the performance scope; linked governors are context/navigation only.

        Locked permission outcome:

        - Leadership role IDs: Leadership channel and its child threads.
        - Admin user: Leadership channel/threads and Notify channel/threads.
        - Never authorize by role name alone, Ark Setup membership, DM context, or another channel.
        - Recheck authorization on every interaction.

        Locked player-review output:

        - Pages: Overview, Kingdom Activity, KVK Performance, Player Record.
        - Periods: 30/90/180/360 days; 90 default.
        - Exact preceding equal-length comparison; up to 720 days of source history.
        - Header: governor name/ID, alliance, Power, City Hall, scan freshness, X:Y, location freshness,
          and reported shield end when present.
        - State: CURRENT/STALE/PARTIAL/NO DATA; 48-hour kingdom-scan freshness threshold.
        - Separate Scan Presence from source coverage.
        - Activity metrics: Forts, Helps, Tech Donations, RSS Gathered, Building Minutes, Power Change.
        - Period total, average/reporting day, previous-period change, current-kingdom rank, percentile,
          and source coverage for each metric.
        - Activity Index v1 weights `30/22/18/14/10/6`, all six components required, no renormalisation,
          no qualitative bands, and production distribution replay before final acceptance.
        - Latest completed KVK plus last-three target/trend context.
        - Active linked governor names/IDs, aliases with First/Last observed, and scan-derived alliance
          episodes.
        - Maximum two deterministic evidence-based leadership prompts.
        - Private Definitions/Method panel.

        Locked source/SQL work:

        - Add `GovernorNameHistory.LastSeen` and internal observation count with backfill/upsert.
        - Add `RallyDailySnapshotHeader`; completed date plus absent governor row means zero, absent header
          means missing.
        - Correct Rally import to transactional date replacement before writing completion.
        - Alliance Activity covers every current alliance/member with explicit zero Building/Tech.
        - Add bounded leadership procedure(s), source-history gap audit, dedicated leadership audit table,
          90-day identified retention, and purge.
        - Exclude negative monotonic-counter resets; keep negative Power Change.
        - Index changes remain plan/read/timing/concurrency gated.

        Canonical combat metric:

        ```text
        KP Loss = Healed Troops * 20
        Tanking Score = Kill Points / (KP Loss + Deads) * 100
        ```

        Higher is better. Apply it globally to Account Summary parity, KVK stats, KVK history
        cards/summary/trends/CSV/ranks, KVK rankings, `/stats player`, and future `/stats kingdom`.
        Rename `Lowest Tanking Score` to `Highest Tanking Score`, reverse ranking/trend direction, and
        remove old-formula playstyle bands until replay supports replacements.

        Healed ranking is lower-is-better only among engaged participants with positive Kill Points and at
        least one of kills, deads, or healed.

        Command impact after Phase 8: `36 top-level / 100 grouped / 8 me / 1 stats / 2 inventory`.

        Approval gate: command/caller/permission/source/history/formula audit, SQL design, architecture,
        performance plan, visual wireframes, dedicated bot and SQL Changes reviews with Deep off, deploy
        SQL before bot, resync, and operator smoke.

        ### Phase 9 — Leadership `/stats kingdom`

        Status: `proposed; programme scope and task pack/chat starter prepared`.

        Goal: provide authorized leadership one private kingdom-level view of current strength,
        twelve-month dynamic-roster movement, and the latest four completed KVKs.

        Deliver:

        - Add private grouped `/stats kingdom`.
        - Reuse the Phase 8 dedicated permission, audit, private delivery, fallback, timeout, transition,
          Definitions, and canonical combat-metric contracts.
        - Two pages: Kingdom Overview and KVK Summary.
        - Current metrics: total Power, Kill Points, Deads, Healed, T4+T5 Kills, Total Kingdom Acclaim,
          Active Governors, and Average Power per Active Governor.
        - Total Kingdom Acclaim means dynamic-roster `SUM(HighestAcclaim)`.
        - Twelve-month graph uses the final complete scan and dynamic roster for each month; current month
          is MTD; missing months are not interpolated.
        - One selectable chart metric rather than incompatible overlaid scales.
        - Net Active-Governor Change over twelve months.
        - Last four completed/finalized KVK blocks using `KVK_NAME`.
        - Per KVK: KP, T4+T5, deads, healed, `SUM(Acclaim)`, participants, Acclaim per Participant,
          KP Loss, and ratio-of-sums Tanking Score.
        - Participants are distinct Governor IDs with final-event Acclaim greater than zero.
        - Acclaim per Participant is `SUM(Acclaim) / Participants`.
        - Use one authoritative final row per Governor ID/KVK; never sum overlapping Pass and Full windows.
        - No public sharing, export, arbitrary kingdom selector, or `/me` change in the first release.

        Command impact after Phase 9: `36 top-level / 101 grouped / 8 me / 2 stats / 2 inventory`.

        Approval gate: prove monthly final-scan and KVK final-row uniqueness, approve SQL result sets,
        visual wireframes, performance/security plan, then implement SQL before bot, resync, and smoke.

        ### Phase 10 — Usage-Led Migration Review

        Status: `future proposed review`.

        Goal: use fresh qualified usage and player/leadership feedback to decide remaining compatibility
        cleanup one route at a time.

        Phase 10 does not reopen:

        - completed Phase 5F Inventory retirements;
        - Phase 5G export retirements;
        - Phase 6 `/my_stats` retirement;
        - Phase 8 `/player_profile` removal;
        - the closed `/me history` decision;
        - canonical `/kvk history` ownership.

        Candidate review scope includes remaining redirect-only account/reminder/KVK paths,
        `/mykvkcrystaltech`, and any proven zero-caller compatibility helpers.

        ### Phase 11 — Future “Sticky” Player Features

        Status: `future programme candidate; not a committed implementation slice`.

        Candidate ideas:

        - Personal bests.
        - Best KVK.
        - Lifetime record badges.
        - Current streaks.
        - Recent changes since last scan.
        - Rank-gap or target-distance insights.
        - Kingdom top-10 record appearances.
        - Visual achievement badges.
        - Website-ready profile endpoint or export.

        Entry gate: complete and observe Phases 7-9, define one measurable player-value hypothesis and
        validated source per feature, then create a new task pack or successor programme.
        """
    )
    text = replace_between(
        text,
        "### Phase 7 — Private `/me history` Entry Point",
        "## 13. In Scope for the Programme",
        roadmap_block,
        label="programme phases 7-11",
    )

    text = replace_once(
        text,
        "- Private `/me` KVK history entry point.\n- Leadership/admin `/me inspect`, later and separately permission-gated.\n- Usage-based migration planning for remaining legacy/specialist commands.",
        "- Phase 7 `/me` visual consistency, content audit, and programme closeout.\n- Phase 8 leadership `/stats player` modernisation, global Tanking Score alignment, and `/player_profile` retirement.\n- Phase 9 private `/stats kingdom` current-strength, twelve-month, and completed-KVK reporting.\n- Phase 10 usage-based migration planning for remaining redirect/compatibility commands.",
        label="programme in-scope roadmap bullets",
    )

    text = replace_once(
        text,
        "- Redirecting or removing `/stats player`, `/player_profile`, `/mykvkcrystaltech`, or\n  `/kvk history` without their own evidence and approval. Phase 6 separately approves `/my_stats`\n  removal and must not retain a redirect.",
        "- Adding `/me history`; `/kvk history` remains canonical.\n- Changing `/stats player` or removing `/player_profile` before the separately approved Phase 8\n  implementation/deployment gate.\n- Changing `/mykvkcrystaltech` or public/channel-gated `/kvk history` without their own evidence and\n  approval.",
        label="programme out-of-scope leadership/history",
    )

    modules_block = _dedent(
        """
        ### Likely Python modules

        ```text
        commands/me_cmds.py
        player_self_service/visual_contract.py (Phase 7 candidate, narrow only)
        player_self_service/governor_dashboard_renderer.py
        player_self_service/accounts_renderer.py
        player_self_service/reminders_renderer.py
        player_self_service/preferences_renderer.py
        player_self_service/stats_renderer.py
        inventory/report_image_renderer.py
        player_self_service/page_cards.py
        relevant player_self_service view modules
        core/visual_text.py

        commands/stats_cmds.py
        leadership_player/models.py (or approved equivalent)
        leadership_player/service.py
        leadership_player/dal.py
        leadership_player/renderer.py
        leadership_player/views.py
        leadership_player/insights.py
        leadership_kingdom/models.py (or approved equivalent)
        leadership_kingdom/service.py
        leadership_kingdom/dal.py
        leadership_kingdom/renderer.py
        leadership_kingdom/views.py
        kvk/combat_metrics.py
        kvk_state.py
        services/kvk_history_service.py
        kvk/dal/kvk_history_dal.py
        kvk/services/kvk_stats_card_service.py
        kvk/services/kvk_rankings_service.py
        kvk/rendering/kvk_history_renderer.py
        kvk/rendering/kvk_stats_card_renderer.py
        commands/player_profile_flow.py (retire after zero-caller proof)
        embed_player_profile.py (retire only if command-specific and zero-caller)
        services/profile_lookup_service.py (retain if shared)
        ```
        """
    )
    text = replace_between(
        text,
        "### Likely Python modules",
        "### SQL contracts to validate when touched",
        modules_block,
        label="programme likely modules",
    )

    sql_block = _dedent(
        """
        Likely SQL-backed objects:

        - `dbo.KingdomScanData4`
        - `dbo.PlayerLocation`
        - `dbo.DiscordGovernorRegistry`
        - `dbo.GovernorNameHistory`
        - `dbo.AllianceActivitySnapshotHeader`
        - `dbo.AllianceActivitySnapshotRow`
        - `dbo.cur_RallyDaily`
        - proposed `dbo.RallyDailySnapshotHeader`
        - proposed dedicated leadership review audit table
        - `dbo.BotCommandUsage`
        - `dbo.KVK_Details`
        - `KVK.KVK_Player_Windowed`
        - `KVK.KVK_Kingdom_Windowed`
        - `dbo.v_EXCEL_FOR_KVK_All`
        - `dbo.v_EXCEL_FOR_KVK_Started`
        - Phase 6 `dbo.usp_GetPersonalStatsDaily`
        - proposed bounded leadership player and kingdom review procedures

        Phase 8 requires a source-history earliest/latest/gap audit up to 720 days. Phase 9 requires
        authoritative final monthly scans and one final row per Governor ID/completed KVK. Any new index
        remains evidence-gated on actual plans, logical reads, timings, memory grants, and concurrency.
        """
    )
    text = replace_between(
        text,
        "Likely SQL-backed objects:",
        "## 16. Cross-Programme Constraints",
        sql_block,
        label="programme likely SQL",
    )

    text = replace_once(
        text,
        "- Preserve top-level command count unless explicitly approved. Phase 5F reduced the surface to 39 top-level and 8 `/me`; Phase 5G delivered 38 top-level and 7 `/me`; Phase 6 explicitly approves 37 top-level and 8 `/me` by adding grouped `/me stats` and removing top-level `/my_stats`. Grouped subcommands move from 99 to 100; `/inventory` remains 2.",
        "- Preserve the Phase 6 baseline through Phase 7: 37 top-level, 100 grouped, 8 `/me`, and 2 `/inventory`. Phase 8 explicitly removes top-level `/player_profile`, producing 36 top-level with grouped unchanged. Phase 9 adds grouped `/stats kingdom`, producing 101 grouped and two `/stats` subcommands while top-level remains 36.",
        label="programme command constraints",
    )
    text = replace_once(
        text,
        "- Do not leak Discord-user private settings into leadership inspect mode.",
        "- Do not leak Discord-user private settings into leadership `/stats player` or `/stats kingdom`.",
        label="programme leadership privacy constraint",
    )
    text = replace_once(
        text,
        "- Keep `/kvk history` unchanged when adding private `/me history`.",
        "- Keep `/kvk history` canonical and do not add `/me history`.",
        label="programme KVK history constraint",
    )

    text = replace_once(
        text,
        "- [x] `/stats player` remains available until the separately approved Inspect/leadership decision.\n- [ ] A private `/me history` path exists while `/kvk history` remains unchanged.\n- [ ] `/me inspect` is permission-gated, private by default, and excludes Discord-user private data.\n- [x] Legacy commands are only redirected/removed after usage evidence and explicit operator approval; Phase 5F Inventory retirements meet that gate.\n- [x] Documentation reflects GovernorOS v2 completion through Phase 6, the accepted Phase 6 inheritance contract, and the remaining Phase 7-10 boundaries.",
        "- [x] The KVK history placement review is closed: `/kvk history` remains canonical and `/me history` will not be implemented.\n- [ ] Phase 7 aligns the retained `/me` visual/content system without command, data, permission, or product changes.\n- [ ] Phase 8 modernises private `/stats player`, aligns canonical Tanking Score globally, and removes `/player_profile` with no redirect.\n- [ ] Phase 9 adds private `/stats kingdom` with dynamic-roster monthly trends and the latest four completed KVKs.\n- [x] Legacy commands are only redirected/removed after usage evidence and explicit operator approval; Phase 5F, Phase 5G, Phase 6, and the approved future Phase 8 removal each have route-specific decisions.\n- [x] Documentation reflects GovernorOS v2 completion through Phase 6 and the approved Phase 7-11 roadmap.",
        label="programme acceptance roadmap",
    )

    next_action = _dedent(
        """
        ## 20. Suggested Next Action

        Phase 6 is complete. Phase 7 is the next active implementation candidate.

        Start with the Phase 7 audit only:

        - compare every retained `/me` renderer/card/fallback against the accepted `/me stats` contract;
        - separate intentional specialist differences from accidental drift;
        - propose the exact visual token, state, typography, panel, alignment, date/number, missing-value,
          navigation, and contact-sheet plan;
        - make no command, SQL, metric, permission, privacy, or product change;
        - stop for operator approval before implementation.

        After Phase 7 acceptance, Phase 8 becomes the leadership `/stats player` and canonical combat
        metric slice. Phase 9 follows with `/stats kingdom`. Phase 10 is usage-led compatibility review,
        and Phase 11 remains an uncommitted future feature candidate.

        Active task packs and starters:

        - `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 7 Visual Consistency Content Audit and Programme Closeout.md`
        - `docs/task_packs/Codex Chat Starter - Player Self-Service Command Centre v2 Phase 7 Visual Consistency Content Audit and Programme Closeout.md`
        - `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 8 Leadership Stats Player Modernisation Canonical Combat Metric Alignment and Player Profile Retirement.md`
        - `docs/task_packs/Codex Chat Starter - Player Self-Service Command Centre v2 Phase 8 Leadership Stats Player Modernisation Canonical Combat Metric Alignment and Player Profile Retirement.md`
        - `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 9 Leadership Stats Kingdom.md`
        - `docs/task_packs/Codex Chat Starter - Player Self-Service Command Centre v2 Phase 9 Leadership Stats Kingdom.md`

        Completed Phase 6 and earlier execution records remain archived and are not rewritten except for
        explicit historical corrections.
        """
    )
    text = replace_between(
        text,
        "## 20. Suggested Next Action",
        "## 21. Programme Change Log",
        next_action,
        label="programme next action",
    )

    change_row = "| 2026-07-18 | Phase 7-9 roadmap approved and task-packed | Closed `/me history` with no build; made Phase 7 the `/me` visual/content closeout using `/me stats` as reference; approved Phase 8 `/stats player`, canonical Tanking alignment, Rally completion/alias/audit SQL foundations, and `/player_profile` removal; approved Phase 9 `/stats kingdom` dynamic-roster overview and Acclaim-based completed-KVK participation; created all three task packs and chat starters. |"
    text = append_once(text, change_row)

    path.write_text(text, encoding="utf-8")


def update_taskpack_readme(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "- Completed Phase 6 records are archived under `archive/`. Remaining Phases 7-10 inherit the accepted\n  premium presentation and interaction contracts but require new operator-approved task packs.",
        _dedent(
            """
            - Completed Phase 6 records are archived under `archive/`.
            - The former proposed `/me history` Phase 7 is closed with no build; `/kvk history` remains
              canonical.
            - Active GovernorOS v2 task packs:
              - `Codex Task Pack - Player Self-Service Command Centre v2 Phase 7 Visual Consistency Content Audit and Programme Closeout.md`
              - `Codex Chat Starter - Player Self-Service Command Centre v2 Phase 7 Visual Consistency Content Audit and Programme Closeout.md`
              - `Codex Task Pack - Player Self-Service Command Centre v2 Phase 8 Leadership Stats Player Modernisation Canonical Combat Metric Alignment and Player Profile Retirement.md`
              - `Codex Chat Starter - Player Self-Service Command Centre v2 Phase 8 Leadership Stats Player Modernisation Canonical Combat Metric Alignment and Player Profile Retirement.md`
              - `Codex Task Pack - Player Self-Service Command Centre v2 Phase 9 Leadership Stats Kingdom.md`
              - `Codex Chat Starter - Player Self-Service Command Centre v2 Phase 9 Leadership Stats Kingdom.md`
            - Phase 7 is the next implementation candidate. Phase 8 and Phase 9 remain separately
              approval-gated and must not be implemented through the Phase 7 PR.
            """
        ).rstrip(),
        label="taskpack README GovernorOS active packs",
    )
    text = replace_between(
        text,
        "Phase 6 Interactive Period Performance and `/my_stats` Retirement is complete and archived.",
        "Other temporary deprecated command paths remain captured",
        _dedent(
            """
            Phase 6 Interactive Period Performance and `/my_stats` Retirement is complete and archived.

            The active programme pack now records:

            - the closed KVK history placement decision: no `/me history`, `/kvk history` remains
              canonical;
            - Phase 7 `/me` Visual Consistency, Content Audit and Programme Closeout as the next active
              slice, with no command or SQL change;
            - Phase 8 leadership `/stats player` modernisation, global canonical Tanking Score alignment,
              dedicated leadership audit/source foundations, and `/player_profile` retirement;
            - Phase 9 private `/stats kingdom` with dynamic-roster twelve-month trends and the latest four
              completed KVKs;
            - Phase 10 usage-led migration review and Phase 11 future-candidate boundaries.

            Phase 7-9 task packs and starters are active in this folder. One-pass execution is not
            approved. Phase 8 must wait for Phase 7 acceptance, and Phase 9 must wait for Phase 8
            acceptance.
            """
        ),
        label="taskpack README GovernorOS roadmap",
    )
    path.write_text(text, encoding="utf-8")


def update_canonical_reference(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "Last updated: 2026-07-17",
        "Last updated: 2026-07-18",
        label="canonical updated date",
    )
    text = replace_once(
        text,
        "| Player/KVK | `/kvk history` | `commands/kvk_cmds.py` | Grouped | KVK stats channel decorator with admin override | Private picker/error handling where needed; selected/default single-account history posts public; preserves `governor_id` lookup | Standard | Canonical player KVK history command | Player KVK History, Summary, Trends, and CSV export journey. |",
        "| Player/KVK | `/kvk history` | `commands/kvk_cmds.py` | Grouped | KVK stats channel decorator with admin override | Private picker/error handling where needed; selected/default single-account history posts public; preserves `governor_id` lookup | Standard | Canonical player KVK history command; `/me history` explicitly rejected | Player KVK History, Summary, Trends, and CSV export journey. The 2026-07-18 placement decision keeps this as the one KVK-history entry point; no `/me history`, alias, redirect, or Dashboard History action is planned. |",
        label="canonical kvk history row",
    )
    text = replace_once(
        text,
        "| Player/KVK | `/player_profile` | `commands/telemetry_cmds.py` | Flat | Admin or leadership in allowed channels | Ephemeral | Standard | Preserve; out of Phase 13 player self-service redirect scope | Leadership profile lookup, not a player self-service path. Review only in a future leadership/profile workflow task. |",
        "| Player/KVK | `/player_profile` | `commands/telemetry_cmds.py` | Flat | Admin or leadership in allowed channels | Ephemeral command acknowledgement with current channel-posting behaviour | Standard | Current until coordinated Phase 8 removal; no redirect afterward | Phase 8 is approved to replace the fragmented leadership profile/stats routes with modern private `/stats player`, prove shared callers, remove command-specific profile code, remove this top-level registration, resync, and leave no redirect. Until that deployment this row remains the current runtime truth. |",
        label="canonical player_profile row",
    )
    text = replace_once(
        text,
        "| Stats/KVK | `/stats player` | `commands/stats_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral | Standard | Preserve; include in Player Self-Service v2 scoping review | Leadership player stats lookup remains live; alignment with the full stats/profile modernisation belongs in the v2 programme pack. |",
        "| Stats/KVK | `/stats player` | `commands/stats_cmds.py` | Grouped | Current generic admin/leadership decorator; Phase 8 will replace it with stable role-ID/channel-specific checks | Ephemeral | Standard | Canonical leadership player route; Phase 8 modernisation approved | Remains live in its legacy form until Phase 8. The approved target is one selected-governor private review with 30/90/180/360-day kingdom contribution, ranks, Scan Presence, Activity Index v1, completed-KVK performance, linked-governor context, aliases, alliance history, location/shield, dedicated 90-day audit, and no `/me inspect`. |",
        label="canonical stats player row",
    )

    planned = _dedent(
        """
        ## Approved Future Command Roadmap (Not Yet Runtime)

        The current command table and validator baseline above remain authoritative until each phase is
        deployed and commands are resynced.

        ### Phase 7

        - No command change.
        - `/me` remains eight subcommands.
        - `/me history` will not be implemented.
        - `/kvk history` remains canonical.
        - Target remains `37 top-level / 100 grouped / 8 me / 2 inventory`.

        ### Phase 8

        - Modernise existing `/stats player`.
        - Do not create `/me inspect`.
        - Remove top-level `/player_profile` with no redirect.
        - Target after resync: `36 top-level / 100 grouped / 8 me / 1 stats / 2 inventory`.
        - Dedicated stable-role-ID/channel gate:
          - leadership role IDs in Leadership channel/threads;
          - admin in Leadership and Notify channel/threads;
          - no role-name-only, Ark Setup, DM, or other-channel authorization.

        ### Phase 9

        - Add grouped `/stats kingdom`.
        - No new top-level command and no `/me` change.
        - Target after resync: `36 top-level / 101 grouped / 8 me / 2 stats / 2 inventory`.
        - Private two-page Kingdom Overview and completed-KVK Summary.

        """
    )
    text = replace_once(
        text,
        "## Migration And Disposition Notes\n",
        planned + "## Migration And Disposition Notes\n",
        label="canonical future roadmap",
    )

    text = replace_once(
        text,
        "- GovernorOS v2 Phase 6 completed final production Discord smoke and was operator accepted on\n  2026-07-18. The maintained target\n  is 37 top-level, 100 grouped, eight `/me`, and two `/inventory` commands. Private-anywhere\n  `/me stats` owns personal Period Performance; top-level `/my_stats` is removed without a redirect.\n  `/stats player`, `/player_profile`, `/mykvkcrystaltech`, `/kvk history`, Inventory import/audit,\n  selected-governor Inventory report-page exports, and Account Summary Download data remain.\n  SQL PRs #43/#44 deployed the additive `dbo.usp_GetPersonalStatsDaily` contract before the bot;\n  its header exposes latest anchor-date source refresh independently from report generation time.",
        "- GovernorOS v2 Phase 6 completed final production Discord smoke and was operator accepted on\n  2026-07-18. The maintained current target is 37 top-level, 100 grouped, eight `/me`, and two\n  `/inventory` commands. Private-anywhere `/me stats` owns personal Period Performance; top-level\n  `/my_stats` is removed without a redirect. `/stats player`, `/player_profile`, `/mykvkcrystaltech`,\n  `/kvk history`, Inventory import/audit, selected-governor Inventory report-page exports, and Account\n  Summary Download data remain at the current runtime baseline. The approved follow-on roadmap closes\n  `/me history`, makes Phase 7 a no-command `/me` visual/content closeout, assigns `/stats player` and\n  `/player_profile` consolidation to Phase 8, and adds `/stats kingdom` in Phase 9. SQL PRs #43/#44\n  deployed the additive `dbo.usp_GetPersonalStatsDaily` contract before the bot; its header exposes\n  latest anchor-date source refresh independently from report generation time.",
        label="canonical phase6 disposition",
    )
    path.write_text(text, encoding="utf-8")


def update_deferred(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    old_route = _dedent(
        """
        ### Deferred Optimisation
        - Area: `commands/registry_cmds.py`, `commands/telemetry_cmds.py`, `commands/stats_cmds.py`, `commands/inventory_cmds.py`, `commands/subscriptions_cmds.py`, `commands/calendar_cmds.py`, player self-service command docs/tests
        - Type: cleanup
        - Description: Phase 13 introduced selected private redirects. Completed Phases 5F, 5G, and 6 removed their explicitly approved Inventory, export, and `/my_stats` routes. Account/reminder redirects, `/mykvkcrystaltech`, `/player_profile`, `/stats player`, and `/kvk history` remain outside those completed retirement boundaries and still require route-specific evidence rather than programme-wide assumptions.
        - Suggested Fix: For each remaining compatibility/specialist route, collect fresh qualified usage and caller evidence, define the replacement ownership and permission/visibility contract, communicate the proposal, observe the agreed no-feedback window where appropriate, and obtain explicit operator approval before changing registration. Update command governance, canonical docs, resync, smoke, and rollback one approved route at a time. Do not infer permission to retire `/stats player` or public `/kvk history` from the completed personal-route migration.
        - Impact: high
        - Risk: medium
        - Dependencies: Phase 6 completed and operator accepted on 2026-07-18; separate later route-specific task packs, including the Phase 8 Inspect decision and Phase 9 evidence-led migration review.
        """
    )
    new_route = _dedent(
        """
        ### Deferred Optimisation
        - Area: remaining redirect-only account/reminder/KVK compatibility paths, `/mykvkcrystaltech`, command governance, and migration communications
        - Type: cleanup
        - Description: Completed Phases 5F, 5G, and 6 removed their explicitly approved Inventory, export, and `/my_stats` routes. The 2026-07-18 roadmap separately assigns `/stats player` modernisation and `/player_profile` removal to Phase 8, and closes `/me history` while preserving canonical `/kvk history`. Those decisions are no longer part of this generic deferred item. Remaining redirected account/reminder/KVK paths and `/mykvkcrystaltech` still require route-specific usage, feedback, caller, and replacement evidence.
        - Suggested Fix: Use future Phase 10 for fresh qualified usage and no-feedback review. Change one remaining route at a time only after explicit operator approval, communication, command-governance updates, resync, smoke, and rollback. Do not reopen the Phase 8 `/stats player`/`/player_profile` decision or the canonical `/kvk history` placement through this generic item.
        - Impact: medium
        - Risk: medium
        - Dependencies: Phase 7-9 roadmap approved on 2026-07-18; Phase 8 and Phase 9 have dedicated task packs; future Phase 10 evidence review.
        """
    )
    text = replace_once(text, old_route, new_route, label="deferred remaining routes")

    old_stats = _dedent(
        """
        ### Deferred Optimisation
        - Area: `commands/stats_cmds.py`, `embed_my_stats.py`, root `stats_service.py`, `stats_helpers.py`, and future `/me inspect`
        - Type: architecture
        - Description: Phase 6 removes the personal `/my_stats` registration but deliberately retains the proven legacy `embed_my_stats.py`/root `stats_service.py`/`stats_helpers.py` stack because `/stats player` still calls it. The leadership route retains its registration, permissions, visibility, KVK stats-channel dependencies, legacy charts, and behavior. Mixing leadership cleanup into Phase 6 would make command retirement unsafe and would pre-empt the later `/stats player` versus private `/me inspect` decision.
        - Suggested Fix: Run a separately task-packed leadership/Inspect audit after Phase 6 observation. Reconfirm callers and permission/visibility requirements, decide whether `/stats player` remains leadership-owned or becomes `/me inspect`, then migrate or delete only zero-caller legacy helpers with focused permission, registration, chart, and rendering regression coverage.
        - Impact: high
        - Risk: medium
        - Dependencies: Phase 6 completed and operator accepted on 2026-07-18; fresh `/stats player` usage/dependency evidence; explicit Phase 8 leadership/privacy product decision and separate task pack. Inspect lookup must remain separate from the accepted self-view linked-governor picker.
        """
    )
    new_stats = _dedent(
        """
        ### Deferred Optimisation
        - Area: post-Phase-8 residual `embed_my_stats.py`, root `stats_service.py`, `stats_helpers.py`, profile cache/lookup helpers, and zero-caller leadership compatibility code
        - Type: cleanup
        - Description: The product decision is no longer deferred: Phase 8 will modernise the existing `/stats player`, will not create `/me inspect`, and will remove `/player_profile` with no redirect. The exact caller audit may prove that some legacy stats/profile helpers remain shared by other commands. Any such non-zero-caller helper must be retained during Phase 8 rather than deleted speculatively.
        - Suggested Fix: Execute the Phase 8 task pack. Delete command-specific and zero-caller helpers in that phase. After acceptance, retain only a narrowly documented residual cleanup item for helpers that could not be removed because another live caller remains; do not use broad module cleanup to widen the Phase 8 command/data scope.
        - Impact: medium
        - Risk: medium
        - Dependencies: Phase 8 task pack, caller graph, focused permission/rendering/command tests, coordinated command resync and rollback.
        """
    )
    text = replace_once(text, old_stats, new_stats, label="deferred leadership stack")

    old_visual = _dedent(
        """
        ### Deferred Optimisation
        - Area: `player_self_service/page_cards.py`, page-specific `/me` renderers, and shared attachment/view lifecycle helpers
        - Type: architecture
        - Description: Completed Phase 5G removed the final supported Exports caller and directly orphaned generic page-card mappings/helpers. Phase 6 then established a stronger accepted premium interaction pattern across Stats: right-aligned state/header hierarchy, compact supporting numbers, source/generated time separation, same-payload fallback, opaque paged governor selection, latest-transition-wins, preserve-and-disable timeout, and explicit resource cleanup. Accounts, Reminders, Preferences, Dashboard, Inventory reports, and Stats still intentionally retain page-specific payload/renderer contracts; repeated primitives have not yet been measured as one safe shared implementation.
        - Suggested Fix: After the separately approved History and Inspect slices establish whether the Phase 6 patterns genuinely repeat, inventory duplicated visual/lifecycle primitives and consolidate only identical proven contracts. Keep product copy, backdrop, geometry, data ownership, permission model, selector semantics, and renderer-specific behavior page-specific. Do not create a broad renderer/view framework merely to force consistency.
        - Impact: low
        - Risk: medium
        - Dependencies: Phase 6 accepted on 2026-07-18; completed Phase 5G zero-caller cleanup; Phase 7/8 audit evidence; separate approval for any broader consolidation.
        """
    )
    new_visual = _dedent(
        """
        ### Deferred Optimisation
        - Area: broad cross-page renderer/view framework beyond Phase 7's narrow `/me` visual contract
        - Type: architecture
        - Description: Phase 7 is now approved to align retained `/me` typography, colours, state pills, panel borders, alignment, dates, numbers, missing values, navigation, fallbacks, and visual testing using `/me stats` as the reference. It may extract a small proven `player_self_service/visual_contract.py`. It must keep Dashboard, Inventory, summary payloads, selectors, data ownership, dimensions, and page-specific renderers independent. A universal renderer/grid/view framework is still unproven and outside Phase 7.
        - Suggested Fix: During Phase 7, measure duplicated primitives and extract only contracts with at least two identical consumers. After Phase 7 and later leadership cards are observed, reconsider a broader framework only with quantified duplication, a migration matrix, visual parity tests, lifecycle proof, and separate approval.
        - Impact: low
        - Risk: medium
        - Dependencies: Phase 7 task pack and contact-sheet audit; accepted `/me stats` reference; no broad framework without a later explicit task pack.
        """
    )
    text = replace_once(text, old_visual, new_visual, label="deferred visual framework")

    text = replace_once(
        text,
        "- Description: The Phase 5C Codex Security repository scan validated that the shared `is_admin_or_leadership` path treats an exact configured leadership role name as an independent authorization grant when no configured stable role ID matches. Both private SQL-backed usage commands inherit that decision. Guild/channel scoping, ephemeral aggregate output, and unknown production role/channel ACLs constrain the exposure, so final severity is low/P3, but the stable-identity boundary is not enforced by code.",
        "- Description: The Phase 5C Codex Security repository scan validated that the shared `is_admin_or_leadership` path treats an exact configured leadership role name as an independent authorization grant when no configured stable role ID matches. Both private SQL-backed usage commands inherit that decision. Phase 8 will not reuse this broad gate for `/stats player`; it has a dedicated stable-role-ID and Leadership/Notify channel matrix. The generic decorator and other commands remain a separate low/P3 hardening item.",
        label="deferred generic role-name description",
    )
    text = replace_once(
        text,
        "- Dependencies: Operator confirmation of production leadership role IDs, duplicate-role policy, and allowed-channel ACLs; preserve intended admin and leadership access; run focused permission/telemetry tests, command registration, full pytest, and operator smoke.",
        "- Dependencies: Production leadership role IDs are confirmed for Phase 8, but generic decorator consumers still need their own compatibility audit. Preserve intended admin/leadership access outside Phase 8; run focused permission/telemetry tests, command registration, full pytest, and operator smoke before changing the shared decorator.",
        label="deferred generic role-name dependencies",
    )

    path.write_text(text, encoding="utf-8")


def update_briefing(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    roadmap = _dedent(
        """
        Approved follow-on roadmap on 2026-07-18:

        - The proposed `/me history` route is closed with no build. `/kvk history` remains the one
          canonical KVK-history command.
        - Phase 7 is the `/me` Visual Consistency, Content Audit and Programme Closeout. It uses the
          accepted `/me stats` card as the reference for typography, colours, panel borders, alignment,
          state pills, dates, numbers, missing values, navigation, fallback, timeout, and mobile
          readability. It changes no command, SQL, metric, permission, privacy, selector, or data owner.
        - Phase 8 modernises the existing private leadership `/stats player`, adopts one canonical
          higher-is-better Tanking Score across every KVK/Account/leadership surface, adds the bounded
          leadership data/audit foundations, and removes `/player_profile` with no redirect.
        - Phase 9 adds private `/stats kingdom` with current kingdom totals, twelve-month dynamic-roster
          trends, and the latest four completed KVKs. Participants are governors with final-event
          Acclaim greater than zero, and Acclaim per Participant is included.
        - Phase 10 remains a usage-led review of other compatibility routes; Phase 11 remains a future
          candidate feature programme.

        Phase 7 is the next implementation candidate. Phase 8 must wait for Phase 7 acceptance and Phase
        9 must wait for Phase 8 acceptance.

        """
    )
    text = replace_once(
        text,
        "The completed task pack and starter are archived.\n\n",
        "The completed task pack and starter are archived.\n\n" + roadmap,
        label="briefing roadmap insertion",
    )

    text = replace_between(
        text,
        "Locked follow-on consistency:",
        "The following earlier phase notes remain as historical delivery context",
        _dedent(
            """
            Locked follow-on consistency:

            Phase 7 starts from the accepted Phase 6 visual hierarchy and checks every retained `/me`
            card/fallback against it. Core 1702x924 summary cards should align closely; Dashboard retains
            1180x760; Inventory retains 1400x980 and report-specific accents. A small shared visual-token
            module is permitted only for proven identical primitives.

            Phase 8 and Phase 9 are leadership `/stats` products, not `/me` pages. They reuse accepted
            private attachment/fallback/lifecycle patterns but use dedicated stable-role-ID/channel
            authorization, neutral leadership identity, their own typed payloads, and no self-view
            governor picker or All Linked scope.

            Canonical combat metric for every current/future surface:

            ```text
            KP Loss = Healed Troops * 20
            Tanking Score = Kill Points / (KP Loss + Deads) * 100
            ```

            Higher is better. Phase 8 owns the coordinated correction of old KVK formulas, labels, ranking
            direction, trends, exports, and playstyle copy.

            """
        ),
        label="briefing locked follow-on",
    )

    text = replace_once(
        text,
        "Admin/leadership inspect is confirmed as required Phase 8 work and remains a separate\npermission-gated slice using the Phase 2 inspect-safe contract.",
        "Leadership review is confirmed as Phase 8 work under the existing `/stats player` command. It will\nuse a dedicated stable-role-ID/channel gate, remain private, remove `/player_profile`, and will not\ncreate `/me inspect`.",
        label="briefing inspect paragraph",
    )

    text = replace_once(
        text,
        "Resources, Speedups, and Materials retain their own private selected-governor\nreport-page exports. `/stats player`, `/player_profile`, and `/mykvkcrystaltech` remain live.",
        "Resources, Speedups, and Materials retain their own private selected-governor report-page\nexports. `/stats player`, `/player_profile`, and `/mykvkcrystaltech` remain live at the current Phase 7\nruntime baseline. Phase 8 is approved to modernise `/stats player` and remove `/player_profile` with no\nredirect; `/mykvkcrystaltech` remains outside that phase.",
        label="briefing player current/future routes",
    )

    operator_insert = _dedent(
        """
        Approved next phases:

        - Phase 7: no command or SQL change; visually align all retained `/me` cards/fallbacks against
          `/me stats`, preserve Dashboard/Inventory specialist layouts, and complete contact-sheet plus
          desktop/mobile review.
        - Phase 8: dedicated Leadership-channel role-ID gate; admin additionally allowed in Notify;
          private `/stats player` only; 30/90/180/360 periods; Scan Presence, source coverage, ranks,
          Activity Index v1, latest/last-three completed KVK, linked governors, aliases, alliance
          history, location/shield, dedicated 90-day audit; global Tanking correction; remove
          `/player_profile`; deploy SQL before bot; resync to 36 top-level.
        - Phase 9: add private `/stats kingdom`; dynamic-roster monthly final scans, current totals,
          Total Kingdom Acclaim as `SUM(HighestAcclaim)`, last four completed KVKs, KVK Acclaim as
          `SUM(Acclaim)`, participants as distinct governors with Acclaim > 0, Acclaim per Participant,
          and ratio-of-sums Tanking; resync grouped commands to 101.

        """
    )
    text = replace_once(
        text,
        "Phase 6 pre-deployment Stats-channel announcement used for the accepted rollout:\n",
        operator_insert + "Phase 6 pre-deployment Stats-channel announcement used for the accepted rollout:\n",
        label="briefing operator roadmap",
    )

    path.write_text(text, encoding="utf-8")


def copy_new_taskpacks(repo_root: Path) -> None:
    source_dir = BUNDLE_ROOT / "docs" / "task_packs"
    target_dir = repo_root / "docs" / "task_packs"
    target_dir.mkdir(parents=True, exist_ok=True)
    for source in sorted(source_dir.glob("*.md")):
        shutil.copy2(source, target_dir / source.name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "repo_root",
        nargs="?",
        default=".",
        help="Path to K98-bot-mirror checkout (default: current directory)",
    )
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()

    files = {
        "programme": repo / "docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md",
        "taskpack_readme": repo / "docs/task_packs/README.md",
        "canonical": repo / "docs/reference/canonical_command_reference.md",
        "deferred": repo / "docs/reference/deferred_optimisations.md",
        "briefing": repo / "docs/player_self_service_command_centre_briefing.md",
    }
    missing = [str(path) for path in files.values() if not path.is_file()]
    if missing:
        print("Missing expected repository files:", file=sys.stderr)
        for item in missing:
            print(f"  {item}", file=sys.stderr)
        return 2

    update_programme_pack(files["programme"])
    update_taskpack_readme(files["taskpack_readme"])
    update_canonical_reference(files["canonical"])
    update_deferred(files["deferred"])
    update_briefing(files["briefing"])
    copy_new_taskpacks(repo)

    changed = [
        *files.values(),
        *sorted((repo / "docs/task_packs").glob(
            "Codex * - Player Self-Service Command Centre v2 Phase [789]*.md"
        )),
    ]
    print("GovernorOS Phase 7-9 documentation update applied.")
    print("Review with:")
    print("  git status --short")
    print("  git diff -- docs")
    print("Modified/created paths:")
    for item in changed:
        try:
            print(f"  {item.relative_to(repo)}")
        except ValueError:
            print(f"  {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
