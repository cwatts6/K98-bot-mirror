# Codex Task Pack - Discord Embed Payload Safety Phase 2D Operator Diagnostics Convergence

## 1. Task Header

- Task name: `Discord Embed Payload Safety Phase 2D Operator Diagnostics Convergence`
- Date: `2026-09-03`
- Owner/context: `Chris Watts / follow-up to delivered Phase 2C`
- Task type: `deferred optimisation batch / diagnostic payload reliability`
- One-pass approved: `no`
- Status: `implementation and local validation complete; mirror PR #255 ready for review`
- Repository: `K98-bot-mirror` bot repository only

## 2. Delivery Prerequisites

Phase 1 owns the unchanged canonical embed contract in `core/discord_embed_limits.py`. Phase 2A
event/calendar convergence, Phase 2B Ark hardening, and Phase 2C player-facing rankings/history
convergence are delivered. Phase 2C completed review, candidate deployment, and operator smoke on
2026-09-03 through mirror PR #254 and production PR #561. Both PRs await manual merge and final
production-main verification.

Before Phase 2D work, fetch both remotes and revalidate branch/head, working-tree state, both Phase
2C PR merge states, the exact intended base, and presence of the Phase 1-2C prerequisites. Audit
may continue read-only before the merges, but runtime or test implementation must use an explicitly
approved base containing Phase 2C.

Expected scope is bot-only. SQL, runtime log files, command-cache JSON, queue-state JSON, local CSV
logs, and external service status are evidence sources, not pre-approved mutation targets. Any
required SQL/DAL, schema, config, cache/state format, dependency, command, permission, or
persistence change stops for separate approval.

## 3. Required Reading And Skills

Read the current `AGENTS.md`, `README-DEV.md`, core references indexed by
`docs/reference/README.md`, `docs/reference/runbook_diagnostics.md`, the archived payload audit,
archived Phase 1-2C packs, root/applicable `SECURITY.md`, the canonical helper/tests, and every
runtime/test path selected by current call-graph searches.

Use `k98-architecture-scope` for the first response, `k98-test-selection` for deterministic gates,
`k98-deferred-optimisation-capture` for new out-of-scope findings,
`k98-security-review-routing` before any security review, `k98-discord-command-feature` if an
approved diff touches interactions, `k98-pr-review` after implementation, and
`k98-promotion-check` only after review. Step 1 remains audit/scope only.

## 4. Objective

Inventory, measure, and classify every live operator-facing diagnostic embed, content message,
attachment, view edit, notification-channel post, and administrator DM. After separate operator
approval, reuse the canonical helper and existing attachment/export patterns to harden only proven
unsafe output. Preserve complete diagnostic meaning through bounded summaries plus complete files,
complete-unit pagination, or exact count-bearing omission markers. Do not silently truncate
filenames, paths, errors, log lines, command/version rows, queue jobs, or failure/history units.

Privacy and redaction are part of the output contract. Do not broaden who can see diagnostic data,
attach raw logs to a wider audience, add mentions, or expose credentials, tokens, connection
strings, private paths, protected user data, or unredacted diagnostic archives.

Classify each builder and delivery boundary as `safe`, `fix now`, `defer`, or `not runtime`.
Command handlers, scripts, helpers, and renderers enter the implementation manifest only when the
current call graph proves a live affected route.

## 5. Canonical And Adjacent Discord Contracts

Reconfirm authoritative current Discord limits and repository ownership before planning changes.
The unchanged canonical embed contract is: 10 embeds per message; title 256; description 4,096;
25 fields per embed; field name 256; field value 1,024; footer 2,048; author name 256; and 6,000
combined embed-text characters per message. Reuse `measure_embed_payload()`,
`validate_embed_payload()`, `require_valid_embed_payload()`, and narrowly appropriate canonical
constants.

Also measure the actual final message content, attachment count, attachment filenames, and the
destination guild/channel upload limit. Discord message content is separate from embed text, and
an attachment fallback is not safe merely because its companion embed is valid. Do not add a
competing helper, globally monkeypatch Discord, or reopen the Phase 1 shared-sender contract without
a separately proved same-root defect.

## 6. Architecture And Delivery Inventory

Audit the current call graph, including at minimum:

| Area | Responsibilities and boundaries |
|---|---|
| `commands/admin_cmds.py` summary/history family | `/ops summary`, `/ops weeksummary`, `/ops history`, and `/ops failures`; public/default versus admin-only delivery, CSV input, follow-up message/view identity, and failure content |
| `embed_utils.py` diagnostic renderers | `generate_summary_embed`, `send_summary_embed`, `HistoryView`, and `FailuresView`; local clipping, complete-row pagination, omission markers, final validation, 60-second timeout, and caller-owned sends/edits |
| `commands/admin_cmds.py` log family | `/ops logs`, `/ops show_logs`, `/ops last_errors`, and `/ops crash_log`; admin-and-notify-channel gate, ephemeral defer/edit, 200-line cap, 3,800-character previews, code-fence neutralisation, and full-tail attachments |
| `ui/views/admin_views.py::LogTailView` | filtered newest-first log paging, regex/literal fallback, page-size cap, attachment replacement/clearing, filter display, and 120-second in-memory view timeout |
| `commands/admin_cmds.py` health/status family | `/ops dl_bot_status`, `/ops view_restart_log`, `/ops usage`, `/ops usage_detail`, command-version/cache validation, resync outcomes, maintenance/import/export result summaries, and other proved-live diagnostic embeds or error content |
| `utils.py::update_live_queue_embed` | public notification-channel queue post/edit/recreate, five-job display, dynamic filename/user/channel/status values, persisted message metadata, restart rehydration, and post-delivery state save |
| `bot_helpers.py::connection_watchdog` | fixed connection-loss/recovery embeds to the notification channel and administrator DM; alert cadence, restart flag, and shutdown behavior are review-only |
| `scripts/collect_diagnostics.py` and diagnostics runbook | existing redaction/archive/upload policy and operator fallback; prove whether any Discord route calls it before treating it as runtime |
| calendar/Ark/Pre-KVK/other admin outputs | classify common diagnostic presentation only; do not reopen delivered Phase 2A/2B behavior or absorb unrelated operational workflows |

Inventory every additional live constructor, mutation, send, edit, follow-up, DM, attachment, and
fallback discovered. Include command permissions, guild and notification-channel restrictions,
public/ephemeral/DM visibility, requester ownership for controls, `AllowedMentions`, attachment
replacement, message/view identity, timeout cleanup, queue rehydration, deleted-message fallback,
restart implications, and error handling. Prove test-only, script-only, legacy-only, or dead paths.

## 7. Data, File, SQL, Config, Cache, And Privacy Contracts

Trace each dynamic value to its source:

- `summary_log.csv`, download-history CSV, failed-job CSV, and `restart_log.csv` rows;
- general, error, and crash runtime log paths and filtered line pages;
- command cache/version signatures and resync/validation issues;
- telemetry usage rows and user/command labels;
- SQL and Google Sheets connectivity messages and configured server/database labels;
- maintenance, import, export, and event-pipeline result/error objects;
- in-memory queue jobs and `live_queue_cache.json` message metadata;
- watchdog state, notification channel, and administrator DM destinations;
- attachment names, byte sizes, upload caps, and raw-versus-redacted content.

Validate read-only SQL-facing assumptions against `C:\K98-bot-SQL-Server` before implementation.
No SQL or DAL change is expected. Preserve source ordering, row/page caps, filters, timestamps,
status meaning, command cache semantics, queue job ordering, message IDs, tracker/cache formats,
restart behavior, and maintenance/offload execution.

For every output, establish whether its source can contain credentials, tokens, signed URLs,
connection strings, local paths, Discord IDs, private filenames, stack traces, SQL text, or other
sensitive values. Existing visibility restrictions are a floor, not permission to broaden raw data
delivery. Any suspected security finding routes to Codex Security triage rather than the deferred
optimisation register.

## 8. Evidence And Measurement Requirements

For every approved diagnostic output measure:

1. empty/minimum and production-representative normal data;
2. exact title, description, field-name, field-value, field-count, embed-count, 6,000-character,
   2,000-content-character, attachment-count, and destination upload boundaries;
3. one over every applicable boundary;
4. maximum configured row/page/line/cardinality and maximum credible queue/history/failure sizes;
5. pathological indivisible filenames, paths, authors, channels, statuses, exceptions, cache issues,
   command signatures, filter text, log lines, and service-result values;
6. attachment-needed, attachment-within-limit, attachment-too-large, upload-rejected, edit-rejected,
   and replacement/clearing paths;
7. grouped embeds as the exact message payload sent or edited;
8. notification-channel, ephemeral interaction, public summary/history, and administrator-DM paths;
9. view navigation, stale/unauthorised interaction, timeout, deleted-message recreation, and restart
   rehydration behavior;
10. privacy/redaction behavior for both preview text and attached complete content.

Compare every local 3,800/3,900/4,000-character preview budget, 5/10/20/50/200 row or line cap,
25-field branch, 50,000-line tail window, five-job queue window, and attachment fallback with the
canonical full-message contract. A local clip, page cap, or attached file is not proof that the
final delivery is valid, complete, or private.

## 9. Required First Response And Stop Gate

The first response must be audit/scope and architecture planning only. It must:

1. confirm branch/head, clean/dirty paths, Phase 1-2C prerequisite state, both Phase 2C PR states,
   intended base, and bot-only scope;
2. reconfirm canonical embed limits plus message-content, attachment-count, filename, and actual
   destination upload-limit handling;
3. map every diagnostic builder through its public, ephemeral, notification-channel, DM, file,
   fallback, send/edit/recreate, and timeout boundary;
4. prove which admin, queue, watchdog, maintenance, script, legacy, and test paths are live,
   test-only, script-only, or dead;
5. trace file/SQL/config/cache/model/Discord/privacy contracts and measure normal, exact-boundary,
   one-over, maximum-cardinality, grouped, attachment, and pathological-single-unit cases;
6. provide one findings-matrix row per runtime delivery boundary with `safe`, `fix now`, `defer`,
   or `not runtime` disposition and exact evidence;
7. propose complete-unit packing, pages/additional embeds, bounded previews plus complete attachments,
   visible compaction, and exact count-bearing omission behavior under every exhaustion mode;
8. explain redaction and attachment behavior without claiming secrecy for data already visible to an
   authorised operator;
9. explain how commands, permissions, guild/channel gates, audience, mentions, files, filters,
   ordering, status meaning, SQL/DAL, cache/state, queue identity, timeouts, restart/rehydration,
   fallback, and executor/maintenance behavior remain unchanged;
10. name the exact runtime, test, and documentation modification manifest;
11. give selector-driven/risk-based tests, bot Changes-only/Deep-off security routing, SQL no-diff
    skip, production smoke, rollback, and approval questions.

Stop after that response. Do not edit runtime code or tests until the operator explicitly approves
the Phase 2D implementation scope and output choices.

## 10. Hard Boundaries

- Do not reopen Phase 1, Phase 2A event/calendar, Phase 2B Ark, or Phase 2C rankings/history behavior.
- Do not change command names, placement, registration, options, permissions, admin/leadership roles,
  guild or notification-channel restrictions, public/ephemeral/DM visibility, or requester ownership.
- Do not add mentions or broaden `AllowedMentions`; preserve existing intentional user/channel
  references and prove they cannot ping unexpectedly.
- Do not change SQL/DAL queries, connectivity checks, source files, log schemas, command-cache JSON,
  queue-state JSON, config, dependencies, message/view identity, timeouts, startup, restart,
  rehydration, scheduler, watchdog, maintenance, or offload semantics.
- Do not silently truncate meaningful diagnostic units. Preview compaction must remain visible and
  complete detail must use an approved private attachment/page/export path or an exact count-bearing
  omission marker.
- Do not attach raw or less-redacted logs to a broader audience than today.
- Keep Phase 2E Ark persistence/orchestration/observability, Phase 2F active-reminder atomicity,
  Phase 2G atomic Pre-KVK reservation, and the separate KVK History executor audit out of scope.
- Do not run a Standard/Codebase or Deep security scan.

## 11. Candidate File Set

Reduce this review inventory to an exact approved modification manifest:

- likely runtime: `commands/admin_cmds.py`, `ui/views/admin_views.py`, `embed_utils.py`,
  `utils.py`, and only proved-live diagnostic helpers in `bot_helpers.py`;
- call-graph dependent: command-cache/version helpers, telemetry usage presentation, maintenance or
  import/export result renderers, and `scripts/collect_diagnostics.py` only if a live Discord caller
  or approved privacy fix justifies them;
- review-only unless separately justified: `core/discord_embed_limits.py`, SQL/DAL, config,
  queue persistence, restart lifecycle, scheduler/watchdog control, maintenance/offload code,
  Phase 2A/2B/2C renderers, and production log files;
- focused tests: existing `tests/test_embed_utils.py`, `tests/test_ui_imports.py`,
  `tests/test_admin_views_smoke.py`, `tests/test_admin_command_cache_paths.py`,
  `tests/test_command_usage_dal.py`, `tests/test_utils_live_queue.py`,
  `tests/test_live_queue_persistence.py`, `tests/test_queue_lifecycle.py`, and a narrowly named new
  diagnostic payload test module only if the audit proves a need;
- documentation: this pack, its chat starter, the archived payload audit, `README-DEV.md`, task-pack
  indexes, diagnostics runbook, deferred register, and only records required by the approved diff.

## 12. Validation, Security, Smoke, And Rollback

Use `scripts/select_tests.py` after the approved diff. Require focused normal/boundary/pathological
tests; complete diagnostic-unit and truthful omission behavior; grouped payload validation;
unchanged permissions, notification-channel gates, public/ephemeral/DM audience, mentions, filters,
ordering, message identity, attachment replacement, fallback, timeouts, and restart rehydration;
attachment upload rejection; and preview/attachment redaction consistency.

Before PR handoff, run or justify architecture/deferred/security-routing validators, selected
pytest, import smoke, command registration, pre-commit, full pytest, and log-noise analysis. Route
a bot `Changes` review over the exact approved base..head with Deep off because diagnostic/log/file,
Discord interaction, permission, and deployment surfaces are security sensitive. SQL is a
documented no-diff skip only when both repositories and SQL-facing contracts are unchanged.

Production smoke requires separate approval. Use representative authorised `/ops` summary/history,
log preview/file fallback, health/status, and usage routes plus a natural queue edit/restart
rehydration when safely available. Verify audience and channel enforcement, redaction, attachments,
message identity, no unexpected mentions, no duplicate, and no Discord `50035`. Do not inject
secrets, mutate production logs, fabricate failures, or enqueue work merely to force pathological
output.

Rollback is a bot-PR revert and redeploy of the prior bot revision. No SQL, config, cache/state
schema, log/file schema, command, or data rollback should be required.

## 13. Deferred Batch Selection

The Phase 2D diagnostics item scores as follows under the deferred framework:

| Candidate | Impact | Frequency | Risk reduction | Effort | Score | Recommendation |
|---|---:|---:|---:|---:|---:|---|
| Operator diagnostic payload convergence | 3 | 3 | 4 | 3 | 7 | Good bounded batch candidate |

The batch is coherent because every candidate route consumes operator diagnostic/file/status data
and terminates at a Discord presentation boundary. Excluded work remains excluded because it changes
persistence, orchestration, scheduling, or unrelated player-facing product behavior.

## 14. Follow-Up Roadmap

- Phase 2E: confirmation-update retention policy, team-builder audit-service extraction, and Ark
  registration delivery-outcome observability;
- Phase 2F: atomic `active_reminders` persistence;
- Phase 2G: evidence/design-gated atomic Pre-KVK dispatch reservation;
- separate coordinated tasks: Stats and KVK History once-only executor audits.

No prior deferred item is made ownerless by this preparation.

## 15. Approved Implementation And Validation Evidence

On 2026-09-03 the operator approved the audited `fix now` scope and asked Codex to prepare the
mirror pull request as ready for review. Phase 2C prerequisites were revalidated before editing:
mirror `main` is `25525c5512ee929f1092f3575a140ae2bbf625fe`, mirrored from production
`f03b2c8a78a29ab389b65b22d3cec50a34af8faf`, whose merge message records production PR #561.
The implementation branch is `codex/discord-embed-payload-safety-phase-2d`. The SQL repository is
unchanged at `fc0e94ebd2e0a98286069c8a8b71365dd5178657` and remains a documented no-diff skip.

The approved implementation adds `core/operator_diagnostic_payloads.py` for message-content,
complete-unit, redaction, attachment-name, attachment-count, UTF-8 byte, and destination upload
policy while retaining `core/discord_embed_limits.py` as the sole canonical embed contract. Live
operator routes now use complete rows/lines/jobs, exact count-bearing omission markers, canonical
final embed validation, and complete redacted private attachments when the current destination can
accept them. Attachment edits replace or clear the previous file. No command, option, permission,
guild/channel restriction, public/ephemeral/DM audience, requester ownership, mention behavior,
source ordering, status/filter meaning, SQL/DAL, config, cache/state schema, message/view identity,
timeout, startup, restart/rehydration, scheduler, watchdog, maintenance, or executor behavior
changes.

Focused suites passed `149` before formatting and `90` after the formatter-only changes. The full
suite passed `3118 passed, 2 skipped`. Architecture, deferred-item, security-routing, selector,
import-smoke, command-registration, Ruff, Black, Pyright, secrets, and complete pre-commit gates
passed. Bot Changes-only security scan `848b6f62-9da7-4306-bf4d-45661db7c6be` reviewed the exact
approved working-tree snapshot from base `25525c5512ee929f1092f3575a140ae2bbf625fe`, with Deep off,
complete coverage of all 11 changed runtime files, and zero findings. The scan was sealed with
digest `codex-security-snapshot/v1:sha256:cc42cf88aab852775835865caf5017a1e5f541b91a2177aa709e1a19aaeeac37`.
Subsequent task-record changes are documentation-only and receive a precise incremental security
skip.

Mirror PR #255 carries commit `cf450215c1e8080fb9df0f6c009049875894bebf` and was opened
non-draft against `K98-bot-mirror/main`. Production smoke and promotion remain separate
approval-gated work after review. The planned smoke
uses representative authorised summary/history, log preview/attachment, health/status, usage, and
natural queue edit/rehydration paths without injecting secrets or manufacturing failures. Rollback
remains a bot-PR revert and redeploy of the previous production-main revision; no SQL, config,
cache/state, command, or data rollback is required.

PR review then identified four actionable issues across five inline comments: incomplete redaction
of quoted credential forms, a possible ping from public diagnostic error content, a 26-field
subscriber payload when the omission marker followed 25 entries, and incorrect singular wording
for one omitted audit batch. Commit `03dddb60478eab2f759c205573c494d8dd0723a9` fixes all four at
their narrow runtime boundaries and adds adversarial and exact-boundary regressions. Focused review
tests passed `40`; the full and independent log-hygiene suites each passed `3123 passed, 2 skipped`,
with production operational logs unchanged. Final bot Changes-only scan
`5f4f7072-8a27-4b6f-826b-338b9b08a5c5` reviewed the complete
`25525c5512ee929f1092f3575a140ae2bbf625fe..03dddb60478eab2f759c205573c494d8dd0723a9`
range with Deep off, complete coverage of all 11 runtime files, and zero findings. SQL remains a
documented no-diff skip; these record-only updates receive a precise incremental security skip.

Production-candidate smoke on 2026-09-03 confirmed graceful shutdown, queue-state persistence,
successful startup, command-cache no-diff handling, live-queue message rehydration, and successful
representative summary, history, restart-log, status, usage, show-log, and crash-log routes. The
interactive `/ops logs` route exposed one Pycord edit-contract defect when a complete redacted page
attachment was needed: a new `discord.File` was passed as an existing `attachments` item, causing
Pycord to call the unavailable `File.to_dict()`. The narrow correction clears retained attachments
with `attachments=[]` and uploads the replacement through `files=[file]`; no permission, audience,
filter, ordering, timeout, filename, content, view identity, or restart behavior changes. Focused
diagnostic/view tests pass `16`, the full suite passes `3123 passed, 2 skipped`, and focused pytest
log-noise validation confirms production operational logs remain unchanged. The corrected candidate
was restarted and smoke tested again on 2026-09-03. Graceful shutdown, startup, live-queue message
rehydration, `/ops logs`, its component interactions, and all other representative commands passed;
the supplied evidence contains no `CMD ERROR`, traceback, `File.to_dict`, Discord `50035`, or
error/critical entry. Production-candidate smoke is complete.
