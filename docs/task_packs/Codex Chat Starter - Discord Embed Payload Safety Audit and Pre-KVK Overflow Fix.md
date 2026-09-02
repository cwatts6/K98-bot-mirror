# Codex Chat Starter - Discord Embed Payload Safety Audit and Pre-KVK Overflow Fix

Use this starter to begin the task. One-pass execution is not approved: the first response must be
audit/scope and architecture planning only, then stop for operator approval before changing runtime
code or tests.

## Copy/Paste Starter

```markdown
# Files mentioned by the user:

## Codex Task Pack - Discord Embed Payload Safety Audit and Pre-KVK Overflow Fix.md:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Discord Embed Payload Safety Audit and Pre-KVK Overflow Fix.md

## My request for Codex:

Begin the Discord Embed Payload Safety Audit and Pre-KVK Overflow Fix task.

Use the task pack:

C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Discord Embed Payload Safety Audit and Pre-KVK Overflow Fix.md

The KingdomScanData4/KS4 database work that previously blocked this fix is complete. This is
expected to be a bot-only task. Start with audit/scope and architecture planning only. Do not
change runtime code or tests until I approve your first response.

Read the current repository instructions and all task-specific references required by the pack.
Revalidate current main rather than assuming the preparation commit is still HEAD.

Current confirmed baseline to revalidate:

- On 2026-08-24, Discord rejected the scheduled Pre-KVK alert with:
  `embeds.0.fields.10.value: Must be 1024 or fewer in length`.
- The failed `🗓️ Next 7 days:` field in `stats_alerts/embeds/prekvk.py` joins up to 12 complete
  event strings by count only.
- The normal KVK 16 launch-week fixture rendered to 1,029 characters, five above Discord's
  1,024-character field-value limit.
- The fixture contains:
  - Preparation phase
  - Pre-KVK Starts!
  - KVK Map opens!
  - Marauders
  - Four Kings Enter...
  - Karuak
  - Finding a Foothold
  - Crusader Camp
  - Marauders' Forts
  - Megingjörð (Artifact)
  - Shoring Up
  - Crusader Fortress
- Event names are loaded from column B of `Chronicle_BOT_DATES` and `Major_BOT_DATES`.
  The proper bot fix must not depend on shortened Sheet values.
- `tests/test_prekvk_embed.py` currently replaces the upcoming-event source with an empty list and
  therefore does not build the failed field.
- `prekvk_daily` is currently claimed in both `stats_alerts/embeds/prekvk.py` and
  `stats_alerts/interface.py`.
- The module's `run_blocking_in_thread()` claim call currently passes an unintended empty tuple,
  raises `TypeError`, and falls back to `asyncio.to_thread()`.
- `embed_utils.send_embed_safe()` is the existing shared sender, but it does not enforce the full
  Discord embed contract.
- Its aggregate-overflow branch appears able to append attachment-note fields without replacing
  original fields, creating duplicate fields and unreliable field-count/aggregate bookkeeping.
- Other local approaches exist in `stats_alerts/embeds/kvk.py`,
  `embed_utils.LocalTimeToggleView`, `ui/views/calendar.py`, Ark, MGE and other renderers.
- The mirror head observed when the task was prepared was
  `cca6d9cdb0dd15ba99403b89f03d1fede69f0e68`; treat that only as a reference and report the
  actual current head.

Required first response:

1. Confirm the current branch/head, working-tree state and whether the task is still bot-only.
2. Reproduce or calculate the exact incident payload and identify why existing tests missed it.
3. Map the full Pre-KVK builder/send/edit/state/guard flow, including:
   - event selection and formatting;
   - first-send ping;
   - same-day edit;
   - `prekvk_msg_id`;
   - off-season and daily guards;
   - every current `claim_send` owner.
4. Inventory the existing shared and local embed-limit helpers/constants and compare their
   behavior, tests, import dependencies and suitability for canonical ownership.
5. Run a functional repository-wide inventory of live embed constructors, mutations and outbound
   send/edit/follow-up/DM/webhook paths. Do not stop at searching `discord.Embed(`.
6. Produce an initial findings matrix with:
   - path/function;
   - delivery route and visibility;
   - dynamic data source/cardinality;
   - current limits and tests;
   - realistic failure mode;
   - `safe`, `fix now`, `defer`, or `not runtime` disposition.
7. Recommend one canonical low-level embed-limit model covering:
   - maximum 10 embeds;
   - title 256;
   - description 4,096;
   - 25 fields;
   - field name 256;
   - field value 1,024;
   - footer 2,048;
   - author 256;
   - 6,000 combined characters across all embeds.
8. Explain why the canonical boundary should be a reusable validator/budget primitive rather than
   forcing every output through `send_embed_safe()`.
9. Propose the exact Pre-KVK logical-event chunking/compaction behavior, including field-count and
   aggregate-budget exhaustion and the pathological single-event case.
10. Propose one clear `prekvk_daily` owner and the exact removal/correction of duplicate and
    malformed claim paths.
11. Identify the exact runtime files and tests you recommend changing now. Separate any broader
    pagination/export/product redesign into structured deferred items.
12. Give the selector-driven and risk-based test plan, including the exact 12-event regression,
    one-over boundaries, send failure, edit path, one-and-only-one claim, shared-helper
    compatibility, validators, pre-commit and full pytest.
13. Record Codex Security routing:
    - bot implementation: Changes-only diff review, Deep off;
    - SQL: documented skip if no SQL diff;
    - no standard or deep security codebase scan.
14. State production smoke and rollback expectations.
15. List open questions or approval needed.

Important boundaries:

- The requested wider audit is a functional Discord payload audit. It does not authorise a
  standard or deep Codex Security codebase scan.
- Do not change the KVK Timeline Sheet as the application fix.
- Do not add, rename, move or retire commands.
- Do not change permissions, output visibility, event selection, KVK state logic, source-data
  contracts, SQL objects or cache schemas.
- Do not globally monkeypatch discord.py or mechanically rewrite every embed builder.
- Do not add a third competing helper. Compare `embed_utils.py` with a dependency-light
  `core/discord_embed_limits.py` extraction and recommend one canonical ownership model.
- Do not silently truncate meaningful lists. Choose chunk, paginate, attach, omit-with-marker or
  truncate-with-marker according to the owning output.
- Keep additional `fix now` work limited to confirmed same-root-cause, behavior-preserving,
  PR-sized defects.
- Create the durable audit artifact at:
  `docs/task_packs/Discord Embed Payload Safety Audit Findings.md`.

Stop for approval after the first response. Do not edit code or tests yet.

After approval, implement only the agreed boundary, update the audit record and relevant task
status documentation, run focused and broad validation, complete the bot Changes-only security
review with Deep off, create the mirror PR, and leave production promotion/deployment for the
normal separately approved workflow.
```
