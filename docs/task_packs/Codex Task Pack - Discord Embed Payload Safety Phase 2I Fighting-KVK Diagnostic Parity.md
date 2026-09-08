# Codex Task Pack - Discord Embed Payload Safety Phase 2I Fighting-KVK Diagnostic Parity

## Status and objective

- Date: 2026-09-08. Owner: Chris Watts.
- Selected next scope: fighting-KVK diagnostic parity, following accepted Phase 2H.
- First response: audit/scope and architecture only. Stop for approval before code or tests.
- No implementation, command schema, reservation extension or SQL change is approved by this pack.
- Goal: scope safe off-season testing and later appearance iteration of the real fighting-KVK
  embed through the existing `/kvk_admin test_embed` surface, with explicit destination, disabled
  mentions, truthful outcomes and isolated state wherever the real path reads or writes state.

## Delivered baseline and evidence limits

Phase 2H isolated diagnostic smoke passed on deployed pre-merge commit `7794d2ae`. Phase 2G’s real reservation protocol was exercised successfully through isolated diagnostics. Production-state comparison passed for the observed status/edit operations. Natural production calendar dispatch remains separately pending.

Accepted deployed pre-merge production head: `7794d2aee6cc9ea7483a2e0a0f46770e47c925c8`;
matching mirror runtime: `ba34d7a2360f03d3903de421641ece1e5b19dafa`.
Phase 2H PRs: mirror #259 and production #566, OPEN at preparation. Operator plans to merge and
restart after this documentation delivery. Revalidate actual PR states, resulting main heads,
deployed revision and restart evidence before implementation; do not assume these future steps passed.
Phase 2G #258/#565 merged; production merge `c0a3bc6ba5a618d5b6a2d9e26d7d4d332f5558ab`.
Phase 2H's 3,381 passed / 2 skipped and incremental Changes reviews are historical evidence,
not validation of any new Phase 2I code. Read its archived pack for exact receipts and limitations.

## Required source and reference audit

Read AGENTS.md, README-DEV.md, docs/reference/README.md and its required engineering, execution,
testing, refactor and deferred standards. Apply architecture-scope, discord-command-feature,
test-selection and security-review-routing skills. Conditional references: canonical commands,
interaction safety, diagnostics runbook, events/reminders and REVIEW_HELPERS; startup/shutdown
references if lifecycle is touched. Promotion Guide applies at delivery. Read applicable SECURITY.md.

Read archived Phase 2H pack/starter, Phase 2G pack and Discord Embed Payload Safety Audit Findings.
Revalidate Phase 1–2H source presence in a clean isolated mirror branch/worktree and compare the
production baseline. Inspect authoritative C:\K98-bot-SQL-Server for any SQL-facing proposal.

Source seeds (audit candidates, not permission to edit every file):

| Layer | Source to trace | Required question |
|---|---|---|
| Command | `commands/stats_cmds.py::test_kvk_embed` | Prove `post_here=True` and False, defaults, admin AND notify permissions, deferral and truthful outcome |
| Other caller | `commands/admin_cmds.py::test_embed_command` | Identify overlap without silently changing this command |
| Context/service | `kvk/services/kvk_admin_service.py`, `stats_alerts/interface.py`, `stats_alerts/db.py` | Follow seasonal selector, reads, executor calls, daily guards, returns and side effects |
| Renderer/send | `stats_alerts/embeds/kvk.py::send_kvk_embed` | Trace both embeds as one message, aggregate payload limits, mentions, no-data and send/failure semantics |
| Reuse | `stats_alerts/diagnostics.py`, `diagnostic_sessions.py`, `dispatch_reservations.py`, `state.py` | Identify safe reuse versus Pre-KVK-specific protocol/session coupling |
| Interactions/lifecycle | `ui/views/prekvk_dispatch_diagnostic_view.py`, `bot_instance.py`, actual fighting view paths if any | Inventory real buttons, ownership, restart and cancellation; do not invent interaction parity |

The current `post_here=True` route directly calls `send_kvk_embed(..., is_test=True)`;
False calls the public stats entrypoint with seasonal context and a production stats destination.
Audit this distinction: neither a success wrapper nor test-mode execution establishes a real
reservation receipt. Do not assume fighting-KVK has Phase 2G's Pre-KVK reservation protocol.
If extending reservation to fighting-KVK is necessary, explain it as separately gated design scope.

## Architecture and compatibility requirements

1. Prefer extending the existing domain command or a justified sibling in an existing group.
   Compare migration/compatibility choices explicitly; do not silently remove or reinterpret
   current `post_here` behavior. No new top-level group. `/ops` already has 25 children.
2. Keep command/view layers thin. Put orchestration in the domain service/adapter; use existing
   DAL reads and renderer. Reuse helpers only after proving their concrete type/path contracts.
3. Define ordinary same-guild explicit destination validation, production-channel exclusion,
   requester/bot permissions, owner/session/message checks and rechecks before publication.
   Preserve admin AND notify/accepted-thread gate; private acknowledgements/errors, no DM fallback,
   and mentions disabled in all new output paths.
4. Prove every read/write/send/edit/guard/lock path for each selector. A different CSV path alone
   does not isolate message projections, caches or locks. No global monkeypatch, live state swap,
   production calendar/SQL mutation, forced duplicate or production eligibility bypass.
5. Define server-issued ownership, restart reopening, identity, retention/capacity/offline cleanup,
   readonly status, truthful sent/edited/guarded/uncertain/failed receipts and unavailable-data
   behavior. Preserve existing Phase 2H sessions/schema and diagnostic guarantees.
6. Specify cancellation, once-only offload entry, accepted-but-uncommitted outcomes, rollback and
   failure propagation. Do not retry a possibly entered side effect to manufacture success.
7. Preserve production defaults: Phase 1–2H payloads, permissions, visibility, eligibility,
   mentions, identity, timing, SQL/read and executor semantics. Appearance redesign is a later
   use of the diagnostic, not permission to change the fighting embed in this task.
8. Separate a safe render/send preview from protocol/admission validation. Explain exactly what
   each mode proves. Same-day edits and read-only blocked observations are not fresh-admission
   execution proof. Diagnostics cannot prove exactly-once or all live failures.

## Required first-response deliverables

- Evidence-led safe / fix-now / defer / not-runtime findings with source paths and caller traces.
- Proposed command contract, compatibility choice and layer ownership; justify any extraction.
- Exact proposed runtime, test, tooling and docs manifests; distinguish inspected-only files.
- Separately gated SQL manifest: expected empty. No schema, procedure, index, UDT, ProcConfig,
  embedded query or DAL contract change without authoritative validation and explicit approval.
- Selector/risk test matrix, security routing, concrete smoke plan and rollback plan.
- State remaining uncertainty and stop for approval. Do not implement the command or tests yet.

## Test and security plan to refine during audit

Trace both legacy selector values plus proposed default/run/status/session selectors, and seasonal
active/off-season/missing-data conditions. Prove real Pycord invocation and serialized channel,
choices/defaults with installed dependency versions; recursively check every 25-option boundary.
Protect Phase 2H registration and existing command permissions/versioning/usage behavior.

Cover payload aggregate limits across both embeds, mention suppression, no-data/failure outcomes,
rejected destination/owner/revoked permissions, path isolation, separate concurrent sessions,
restart reopen, retained identity, missing/foreign message and uncertainty without replacement.
Use deterministic invocation counters for offloads and file/Discord failure tests for cancellation;
do not inject live failures. Compare production-state baselines from before the first diagnostic
operation through restart/status/edit, accounting separately for natural production traffic.

Existing candidate regressions: `tests/test_kvk_embed.py`, `tests/test_kvk_admin_service.py`,
`tests/test_daily_kvk_overview_lifecycle.py`, `tests/test_daily_kvk_overview_payloads.py`,
`tests/test_prekvk_reservation.py`, the three `tests/test_prekvk_dispatch_diagnostic*.py` files,
`tests/test_command_registration_smoke.py` and `tests/test_validate_command_registration.py`.
Locate actual additional interface/guard/state tests and propose exact new tests after tracing.
Run selector with the final file manifest; justify focused/full suite and log-noise/import gates.
Run architecture, deferred, command-registration and security-routing validators plus hooks.

For implementation use Changes-only security review, Deep off, explicit immutable bot base/head;
SQL is a separate no-diff skip unless separately changed. Do not initiate a Codebase or Deep audit.
This pack/starter preparation changes Markdown only; no runtime pytest or new security scan needed.

## Concrete operator smoke plan to finalize after design

1. Record reviewed/deployed SHA, UTC via `(Get-Date).ToUniversalTime().ToString("o")`, and normal
   restart evidence. Capture all identified production state baselines before the first operation.
2. Invoke the approved diagnostic from the permitted location to an explicit non-production
   destination; retain session, outcome, message link and any actual durable receipt.
3. Verify real fighting-KVK content or truthful unavailable-data result, complete valid payload,
   disabled mentions and expected visibility. Do not fabricate seasonal SQL/calendar data.
4. Inspect readonly status, repeat the same session and confirm the designed identity/admission
   behavior without forcing a fresh duplicate. Never count an edit as admission proof.
5. Gracefully restart, reopen the same session and verify retained identity/status and any real
   supported interactions. Compare production state and retain evidence without cleanup/reset.
6. Verify unauthorized invocation, invalid destination and revoked-permission rejection safely.
7. Record diagnostic acceptance separately from final main deployment and natural calendar routing.

## Separately pending and excluded

Chris Watts owns natural production Pre-KVK calendar dispatch and Phase 2F's next natural public
save. Do not close either from Phase 2I diagnostic evidence. Keep singleton/public-child lifecycle,
generic view timeout, DM/broad JSON redesign, Stats/KVK History executor audits, generic stats
false-success logging and ProcConfig pending-results/error propagation in separate scopes.
Keep natural production data and existing diagnostic evidence; no purge, reset or live duplicate.
