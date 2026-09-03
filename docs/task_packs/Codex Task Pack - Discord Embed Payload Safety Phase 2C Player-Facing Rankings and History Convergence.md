# Codex Task Pack - Discord Embed Payload Safety Phase 2C Player-Facing Rankings and History Convergence

## 1. Task Header

- Task name: `Discord Embed Payload Safety Phase 2C Player-Facing Rankings and History Convergence`
- Date: `2026-09-02`
- Owner/context: `Chris Watts / follow-up to delivered Phase 2B`
- Task type: `deferred optimisation batch / payload reliability`
- One-pass approved: `no`
- Status: `approved evidence-led implementation and Changes review complete; PR pending`
- Repository: `K98-bot-mirror` bot repository only

## 2. Delivery Prerequisites

Phase 1 owns the unchanged canonical contract in `core/discord_embed_limits.py`. Phase 2A
event/calendar convergence and Phase 2B Ark hardening are delivered. Phase 2B's PR #253 tree is
present on mirror `main`, and production PR #560 is merged in production commit `6da1c083`. Its
2026-09-02 candidate smoke produced a valid registration payload with
`fields=4`, `chars=346`, `compacted_units=0`, and `omitted_units=0`, reused the existing message
reference with `should_announce=False`, and changed neither state nor message identity. No duplicate
or Discord `50035` occurred.

Before Phase 2C work, fetch both remotes and revalidate branch/head, working-tree state, both PR
merge states, the exact intended base, and presence of the Phase 1-2B prerequisites. If the
operator has not yet merged Phase 2B, audit may continue read-only against its branch, but runtime
or test implementation must use an explicitly approved base that contains it.

Expected scope is bot-only. SQL and source data are review-only. Any required SQL schema,
stored-procedure, DAL query, cache, or persistence change stops the task for separate approval and
`k98-sql-validation` against `C:\K98-bot-SQL-Server`.

## 3. Required Reading And Skills

Read the current `AGENTS.md`, `README-DEV.md`, all core references indexed by
`docs/reference/README.md`, the archived audit findings, archived Phase 1-2B packs, root/applicable
`SECURITY.md`, the canonical helper/tests, and all runtime/test paths selected by current call-graph
searches.

Use `k98-architecture-scope` for the first response, `k98-test-selection` for deterministic gates,
`k98-deferred-optimisation-capture` for new out-of-scope findings,
`k98-security-review-routing` before any security review, `k98-pr-review` after implementation, and
`k98-promotion-check` only after review. Use `k98-discord-command-feature` if the approved diff
touches interaction views. Step 1 remains audit/scope only.

## 4. Objective

Measure and classify every live player-facing KVK rankings/history payload and final Discord
delivery boundary. After separate operator approval, reuse the canonical helper to harden only
proven unsafe output while preserving complete ranking/history meaning through deterministic
pagination, existing CSV/image exports, additional embeds where the current route supports them,
or exact count-bearing omission markers. Do not silently truncate meaningful rows.

Classify each builder/boundary as `safe`, `fix now`, `defer`, or `not runtime`. Legacy modules such
as `build_KVKrankings_embed.py` and `embed_kvk_history.py` enter the implementation manifest only if
the current call graph proves a live route.

## 5. Canonical Contract

Reconfirm authoritative current Discord limits and the repository helper before planning changes:
10 embeds per message; title 256; description 4,096; 25 fields per embed; field name 256; field
value 1,024; footer 2,048; author name 256; and 6,000 combined embed-text characters per message.
Reuse `measure_embed_payload()`, `validate_embed_payload()`,
`require_valid_embed_payload()`, and narrowly appropriate canonical constants. Do not add a
competing helper, globally monkeypatch Discord, or force every route through `send_embed_safe()`.

## 6. Architecture And Delivery Inventory

Audit the current call graph, including at minimum:

| Area | Responsibilities and boundaries |
|---|---|
| `commands/kvk_cmds.py` | `/kvk history` and `/kvk rankings` selection, public versus ephemeral defer/follow-up behavior, card/embed fallback, message/view ownership |
| `commands/kvk_history_card_posting.py` | history payload/card build, public/ephemeral follow-up, text fallback, attached image, view/message reference |
| `kvk/rendering/kvk_rankings_embed.py` | current KVK/Honor/Pre-KVK rows, My Rank, Hall of Fame, title/description/field/footer construction |
| `kvk/rendering/kvk_rankings_card_renderer.py`, `kvk/rendering/kvk_history_renderer.py` | image output and bounded text fallbacks; inspect payload ownership without treating image pixels as embed text |
| `ui/views/kvk_rankings_views.py` | requester ownership, metric/mode/limit navigation, public message edits, card/embed attachment swaps, private My Rank/account selection/CSV export, timeout cleanup |
| `ui/views/kvk_history_card_views.py` | requester ownership, card navigation, public-message edits, ephemeral fallback/error and CSV export, timeout cleanup |
| `ui/views/kvk_history_view.py` | legacy multi-embed chart/table journey, files, public/ephemeral sends and edits, custom picker/export, existing `_offload_callable` behavior |
| `build_KVKrankings_embed.py`, `embed_kvk_history.py` | prove live, legacy-only, test-only, or dead status before disposition |
| `kvk/services/kvk_rankings_service.py`, `services/kvk_history_service.py` | row/cardinality/model construction and source semantics; review-only unless a payload-only change is separately approved |
| `kvk/services/kvk_rankings_export_service.py`, history export utilities | existing CSV size/error policy and private delivery; preserve file contracts |
| `kvk/dal/kvk_rankings_dal.py`, `kvk/dal/kvk_history_dal.py`, models/config/cache | trace sources, finalized-KVK selection, ordering and cardinality; no SQL/DAL change expected |

Inventory any additional live builder or outbound send/edit discovered. Include public output,
ephemeral selectors/errors/My Rank/exports, attachments, fallback, requester permissions,
channel restrictions, `AllowedMentions` or mention-neutral behavior, persistent/in-memory message
references, timeouts, and restart implications. Classify fixtures and render-only objects without a
live outbound path as `not runtime`.

## 7. Evidence And Measurement Requirements

Trace every dynamic value to SQL, cache, config, Discord identity, service model, or export source:
governor/alliance labels, KVK numbers/status, ranking modes/metrics/limits, totals/ranks, comparison
columns, table highlights/legends, history labels, fallback text, filenames, and error summaries.

For every approved output measure:

1. empty/minimum and production-representative normal data;
2. every exact component, field-count, embed-count, and 6,000-character aggregate boundary;
3. one over each applicable boundary;
4. maximum credible ranking/history row and account/KVK cardinality from actual DAL/service caps;
5. one pathological indivisible governor/alliance/metric/KVK label, value, fallback line, filename,
   legend, or highlight;
6. multi-embed history messages as the exact `embeds=[...]` group sent or edited;
7. card success, embed/text fallback, CSV/image attachment, upload failure, and attachment swap;
8. locally clipped rows that remain capable of aggregate or field-count overflow.

Compare all local row-width, preview, page, table-column, Top 10/25/50, overlay, and soft upload
policies with the canonical final-message contract. A count cap is not proof of character safety.

## 8. Required First Response And Stop Gate

The first response must be audit/scope and architecture planning only. It must:

1. confirm branch/head, clean/dirty paths, Phase 1-2B prerequisite state, both PR states, and
   bot-only scope;
2. reconfirm the canonical helper and current Discord hard limits;
3. map every rankings/history builder through public send/edit, ephemeral interaction, fallback,
   file/export, permission, view/message identity, timeout, and restart boundaries;
4. prove which legacy builders are live, test-only, or dead;
5. trace SQL/config/cache/model/Discord contracts and measure normal, exact-boundary, one-over,
   realistic pathological, maximum-cardinality, multi-embed, and pathological-single-unit cases;
6. provide one findings-matrix row per runtime delivery boundary with `safe`, `fix now`, `defer`,
   or `not runtime` disposition and exact evidence;
7. propose exact complete-row/history-unit packing, pagination/additional-embed/attachment behavior,
   visible compaction, and count-bearing omission-marker behavior under component, field,
   aggregate, embed-count, and pathological-single-unit exhaustion;
8. explain how command placement, selection/order/status, finalized-KVK logic, permissions,
   visibility, channel restrictions, requester ownership, mentions, exports, fallback, message/view
   identity, timeouts, data sources, SQL/DAL/cache, restart behavior, and the existing offload
   contract remain unchanged;
9. name the exact runtime, test, and documentation modification manifest;
10. give selector-driven tests, bot Changes-only/Deep-off security routing, SQL no-diff skip,
    production smoke, rollback, and approval questions.

Stop after that response. Do not edit runtime code or tests until the operator explicitly approves
the Phase 2C implementation scope and output choices.

## 9. Hard Boundaries

- Do not reopen Phase 1 Pre-KVK, Phase 2A event/calendar, or Phase 2B Ark behavior.
- Do not change commands, command placement/registration, permissions, public/ephemeral visibility,
  channel restrictions, requester ownership, ranking/history selection/order/status, Top limits,
  finalized-KVK logic, account selection, chart/table meaning, or file schemas.
- Do not change SQL/DAL queries, source data, config, cache/state schemas, message/view identity,
  timeout behavior, startup/rehydration, or existing card/embed/text fallback semantics unless a
  proven payload rejection requires a separately approved presentation-only correction.
- Do not introduce pings or broaden `AllowedMentions`.
- Do not combine operator diagnostics, Ark persistence/orchestration, active-reminder atomicity, or
  atomic Pre-KVK reservation.
- Do not fix `ui/views/kvk_history_view.py::_offload_callable` in Phase 2C. Coordinate measurement
  and tests with its existing deferred audit, but preserve executor selection and once-only
  semantics exactly as they currently behave.
- Do not run a Standard/Codebase or Deep security scan.

## 10. Candidate File Set

Reduce this review inventory to an exact approved modification manifest:

- likely runtime: `kvk/rendering/kvk_rankings_embed.py`,
  `commands/kvk_history_card_posting.py`, `ui/views/kvk_rankings_views.py`,
  `ui/views/kvk_history_card_views.py`, and only proven-live history embed/text builders;
- call-graph dependent: `build_KVKrankings_embed.py`, `embed_kvk_history.py`,
  `ui/views/kvk_history_view.py`, `commands/kvk_cmds.py`;
- review-only unless separately justified: rankings/history services, export services, models, DAL,
  config/cache, renderers that produce only image bytes, and `core/discord_embed_limits.py`;
- focused tests: `tests/test_build_kvkrankings_embed.py`,
  `tests/test_kvkrankingview.py`, `tests/test_kvk_rankings_browser_view.py`,
  `tests/test_kvk_rankings_records_view.py`, `tests/test_kvk_rankings_service.py`,
  `tests/test_kvk_rankings_card_renderer.py`, `tests/test_kvk_history_service.py`,
  `tests/test_kvk_history_renderer.py`, `tests/test_kvk_history_card_posting.py`,
  `tests/test_kvk_history_card_views.py`, and `tests/test_kvk_history_offload_and_utils.py`;
- documentation: this pack, its chat starter, audit findings, `README-DEV.md`, task-pack indexes,
  and deferred records as required by the approved diff.

## 11. Validation, Security, Smoke, And Rollback

Use `scripts/select_tests.py` after the approved diff. Require focused normal/boundary/pathological
tests; complete-row and truthful omission behavior; grouped multi-embed validation; unchanged
public/ephemeral visibility, channel restrictions, requester ownership, message edits, attachment
swaps, fallback, exports, and timeouts; legacy call-graph assertions; and Phase 1-2B regressions.

Before PR handoff, run or justify architecture/deferred/security-routing validators, selected
pytest, import smoke, command registration, pre-commit, full pytest, and log-noise analysis.
Route a bot `Changes` review over the exact approved base..head with Deep off. SQL is a documented
no-diff skip only when both repos and SQL-facing contracts are unchanged.

Production smoke requires separate approval. Use representative public rankings and history,
navigation that edits the same message/view, private My Rank/account selection/CSV export as
applicable, and controlled card fallback only when safely reproducible. Verify metrics, audience,
channel/owner enforcement, attachments, no unexpected mentions, no duplicate, and no `50035`.
Do not mutate source data merely to force pathological output.

Rollback is a bot-PR revert and redeploy of the prior bot revision. No SQL, config, cache, state,
file-schema, command, or data rollback should be required.

## 12. Follow-Up Roadmap Preserved From Phase 2B

- Phase 2D: operator diagnostics payload convergence;
- Phase 2E: confirmation-update retention policy, team-builder audit-service extraction, and Ark
  registration delivery-outcome observability;
- Phase 2F: atomic `active_reminders` persistence;
- Phase 2G: evidence/design-gated atomic Pre-KVK dispatch reservation;
- separate coordinated task: KVK History `_offload_callable` once-only executor audit.

## 13. Approved Audit And Implementation Evidence

On 2026-09-03 the operator approved the evidence-led recommendation to close Phase 2C without a
runtime change. The bot base is mirror `main` commit `e525fb355b5b831bcc84c349df944ee7725776f9`;
the implementation branch is `codex/discord-embed-payload-safety-phase-2c`. The SQL repository was
clean at `fc0e94ebd2e0a98286069c8a8b71365dd5178657` and remains a no-diff boundary.

Authoritative SQL, model, cache, cardinality, render, send/edit, attachment, export, permission,
visibility, owner, timeout, restart, and fallback review found no live `fix now` payload. The largest
reachable textual embed is the Hall of Fame maximum at 4,030 description characters and 4,187
aggregate characters. Current KVK, Honor, and Pre-KVK rankings remain valid at Top 10, 25, and 50;
the complete maximum-contract three-row history fallback remains below Discord's 2,000-character
content limit. Legacy ranking pagination and multi-embed history builders are test-only.

Regression coverage now asserts all current mode/Top combinations at source maxima, the Hall of
Fame maximum, its deliberately out-of-contract 4,097-character single-unit rejection, grouped
multi-embed aggregate rejection, and complete maximum-contract history fallback. Focused validation
passed `79`; the full suite passed `3104 passed, 2 skipped`. Architecture, deferred-item,
security-routing, import-smoke, command-registration, pre-commit, and production-log-noise validators
passed. Runtime, SQL/DAL, config/cache/state, commands, permissions, visibility, mentions,
attachments, exports, message/view identity, timeouts, restart behavior, fallback behavior, and
`_offload_callable` are unchanged.

Bot Changes-only security scan `ba783eb5-12bb-4123-b2cd-1dd2f04b28ec` reviewed the exact
`e525fb355b5b831bcc84c349df944ee7725776f9..6176cda960cd536bf21b9c9ad1c0f2b473d90499`
range with Deep off. It recorded complete coverage of all nine changed files and zero findings.
SQL is a documented no-diff skip. This scan-result record is documentation-only and receives a
precise incremental no-runtime security skip.

No Phase 2B deferred item is unassigned.
