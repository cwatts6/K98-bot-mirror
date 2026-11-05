# Codex Task Pack - Discord Embed Payload Safety Phase 2H Isolated Pre-KVK Dispatch Diagnostics

## Operator acceptance — 2026-09-08

Phase 2H isolated diagnostic smoke passed on deployed pre-merge commit `7794d2ae`. Phase 2G’s real reservation protocol was exercised successfully through isolated diagnostics. Production-state comparison passed for the observed status/edit operations. Natural production calendar dispatch remains separately pending.

Owner: Chris Watts. Phase 2H is delivered, tested within the bounds below, explicitly accepted,
and archived. Mirror PR #259 and production PR #566 remain OPEN at documentation preparation;
operator merges and final production-main deployment/restart verification remain pending.
This acceptance supersedes earlier implementation/smoke-pending notes retained as history.

### Evidence and limits

| Check | Observed result |
|---|---|
| Deployed candidate | Operator-reported production HEAD `7794d2aee6cc9ea7483a2e0a0f46770e47c925c8`, restarted before smoke |
| Session | `9e986a8ec9034623a60b38b3f4e14b62`, guild `890980578034352138`, owner `559076207627468807`, destination `1380183673147490479` |
| Real protocol | Reserved, sent, isolated CSV slot 1/1, committed attempt `73b6e1dd0b5b4e5eba903b69a095e195`; message `1546875239743496235` |
| Payload | 13 fields, 2,052 characters, largest field 725; one event field, zero compacted/omitted events |
| Before restart | Read-only status at `2026-09-08T13:31:11.347528+00:00`; same-session edit at `13:31:48.427132+00:00` |
| After restart | Status at `2026-09-08T13:33:47.946759+00:00`; same-session edit at `13:34:20.645658+00:00`; same committed attempt retained |
| Guard | Both status/edit receipts reported fresh admission blocked (observation) True. Edits do not independently prove fresh-admission rejection |
| Interaction boundaries | Operator confirmed My Local Time visible only as expected and permission/destination boundaries working; button worked before and after reopening following restart |
| Production-state comparison | Empty Compare-Object result for Path, Exists, SHA256 over the observed status/edit interval; values below |

Message: https://discord.com/channels/890980578034352138/1380183673147490479/1546875239743496235

Diagnostic CSV was under
`logs/prekvk_dispatch_diagnostics/890980578034352138/1380183673147490479/9e986a8ec9034623a60b38b3f4e14b62/alerts.csv`.
Production comparison evidence:

| Production path | Exists before/after | SHA256 before/after |
|---|---|---|
| `logs/stats_alert_log.csv` | True | `D8D715D1CB54B41A7233D23B9869D723B9551E6C0FCB23CA39776ECBE2EB2980` |
| `logs/stats_alert_log.csv.dispatch.json` | False | absent |
| `logs/stats_alert_log.csv.state.json` | True | `44136FA355B3678A1146AD16F7E8649E94FB4FC21FE77E8310C060F61CAAFF8A` |

The comparison does not retrospectively prove unchanged production state during the first fresh
diagnostic send. No production journal was created during the compared operations. Boundary and
visibility checks are operator attestations; individual raw rejection logs were not supplied.
No live duplicate, crash, ambiguous-send retry, state swap or forced calendar change was used.
Natural calendar/scheduler dispatch, cross-process contention and all live failure modes are not
proved by this smoke; no exactly-once claim is made. Phase 2F's next natural public save remains
separately pending with Chris Watts. Keep diagnostic evidence; no cleanup/reset is authorized.

### Final delivery manifest

Runtime: `bot_instance.py`, `commands/prekvk_cmds.py`, `stats_alerts/diagnostic_sessions.py`,
`stats_alerts/diagnostics.py`, `stats_alerts/dispatch_reservations.py`,
`stats_alerts/embeds/prekvk.py`, `stats_alerts/state.py`,
`ui/views/prekvk_dispatch_diagnostic_view.py`.
Tooling: `scripts/validate_command_registration.py`.
Tests: `tests/test_command_registration_smoke.py`,
`tests/test_prekvk_dispatch_diagnostic_lifecycle.py`,
`tests/test_prekvk_dispatch_diagnostic_view.py`, `tests/test_prekvk_dispatch_diagnostics.py`,
`tests/test_prekvk_report_command.py`, `tests/test_validate_command_registration.py`.
Documentation: README-DEV, canonical command reference, deferred register and resolved archive,
events/reminders, diagnostic runbook, task/archive indexes, archived Phase 2G/2H and audit evidence,
and proposed Phase 2I pack/starter. SQL/config/dependency manifest: empty.
Earlier command placement in `commands/admin_cmds.py` was reverted; it has no final runtime delta.

### Final automated evidence

Final runtime: mirror `ba34d7a2360f03d3903de421641ece1e5b19dafa`, production
`7794d2aee6cc9ea7483a2e0a0f46770e47c925c8`; matching Python blobs. Final focused verification
passed 79 tests in each checkout. Full suite: 3,381 passed, 2 skipped; operational log-noise gate
passed. Hooks, architecture/deferred/security-routing validators, imports and registration passed.
Registration: 36 primary / 101 grouped / 25 ops / 3 prekvk. Command `/prekvk dispatch_test` v1.02
uses evaluated Option defaults; real Pycord invocation and serialized option-count/type tests
cover both live smoke failures fixed before this successful delivery.

Final correction Changes-only reviews, Deep off, complete with zero findings:
mirror `e5f0213d-ec9d-45d6-a2e5-2235601eef0c` (`05827d86..ba34d7a2`), production
`bbdbfb57-a2a3-4a51-a8a5-0e54e3ad7754` (`b1d22543..7794d2ae`). These incremental scans supplement
the original implementation and earlier review-fix evidence; they are not whole-PR rescan claims.
SQL manifest empty; no SQL deployment. This closeout changes Markdown only: runtime tests and a
new security scan are skipped for this exact documentation delta, with documentation validators.

### Handoff

Phase 2I Fighting-KVK Diagnostic Parity is selected for an audit/scope-first response, with design
and implementation unapproved. Its active pack and starter are in the parent task_packs directory.
Before next implementation, revalidate both Phase 2H PR merges, final production-main and deployed
head/restart evidence, clean branch/worktree and Phase 1–2H source. Do not infer a running process
revision from Git HEAD alone. Natural production Pre-KVK dispatch remains a separate observation.

## Historical preparation and implementation record


## 1. Status and objective

- Date: 2026-09-08
- Owner: Chris Watts
- Status: approved implementation and deterministic review complete; operator Discord smoke and Phase 2H promotion/deployment remain pending.
- Repositories: K98-bot-mirror first; production patch promotion after validation; SQL separately gated.
- Objective: enable an operator to exercise the real Pre-KVK reservation protocol against Discord outside the calendar window, with isolated durable diagnostic state and mentions disabled. This is a Phase 2 validation extension, not a change to production eligibility or payload policy.

Phase 2G is complete as an accepted implementation and bounded-validation delivery. Its archived
pack owns the delivered protocol and limitations. Mirror #258 and production #565 were OPEN at
preparation; operator merges and final verification remain pending. Revalidate actual states,
production-main head, deployed head, worktree, mirror base and Phase 1–2G source presence before
coding. Do not assume archival status proves deployment or that a restart log proves a Git head.

Reviewed Phase 2G runtime: mirror `bd99ea1421286ddb152f7729e11de664116d7e47`, production
`fea2767f52f345450225bcdf0c1f03f3d5e3dc4c`; Python trees match. Later closeout changes are docs-only.
Validation: 3314 passed / 2 skipped full, 91 pinned-filelock focused, 67 production focused,
log-noise/hooks/validators/import/registration passed. Separate mirror/production Changes-only,
Deep-off reviews completed without findings; exact IDs remain in archived Phase 2G closure.

## 2. Evidence and required reading

Read AGENTS.md, README-DEV.md, docs/reference/README.md and its required core standards. Apply
architecture-scope, discord-command-feature, test-selection and security-review-routing guidance.
Conditional references: command/canonical registration guidance, interaction safety, events and DM
reminders, REVIEW_HELPERS, startup operations; Promotion Guide only for delivery. Read applicable
SECURITY.md context. Consult authoritative C:\K98-bot-SQL-Server before any SQL-facing change.

Historical evidence:

- `archive/Codex Task Pack - Discord Embed Payload Safety Phase 2G Atomic Pre-KVK Reservation.md`
- `archive/Discord Embed Payload Safety Audit Findings.md`
- `archive/Codex Task Pack - Discord Embed Payload Safety Phase 2F Active Reminder Tracker Atomic Persistence.md`

The supplied 2026-09-08 log shows graceful restart, full startup at 09:17:05 and normal fighting-KVK
daily-cap skip at 09:21:50. It contains no reservation/commit receipt. The generic success line after
the skip is not delivery proof. Pre-KVK is outside its current calendar window. Existing
`/ops test_embed` follows current season; `/kvk_admin test_embed post_here:true` forces fighting KVK,
not Pre-KVK. `send_prekvk_embed(..., is_test=True)` bypasses reservation but still reads/writes the
shared message reference, so direct invocation is not isolated protocol validation.

## 3. First-response scope and architecture gate

Map command permission/defer/error/usage/version/registration patterns; scheduled/manual/test
callers; calendar routing; Pre-KVK build/edit/fresh paths; the real reserve/start/receipt/finalize
lifetime; every journal/CSV/message-state/lock producer; offloads, cancellation, shutdown/restart,
content sources, views/buttons and potential mentions. Distinguish singleton metadata from actual
ownership. Classify safe / fix now / defer / not runtime with concrete source evidence.

Propose one subcommand in an existing admin group (provisional name `/prekvk dispatch_test`;
final spelling/options require architecture approval). Preserve the existing admin AND notify-channel
invocation boundary. Require an explicit validated guild text destination; no silent stats-channel
fallback or arbitrary path input. Explain destination eligibility, bot permissions, requester
authority, prevention of concurrent command spam and where acknowledgements are ephemeral.
No new top-level group or broadening of existing command permissions is approved.

The command must be thin: permission/input checks, safe defer, service invocation, truthful bounded
result. A service owns diagnostic orchestration and a repository/context owns persistence paths.
Reuse the real Phase 2G transitions and canonical renderer; do not duplicate the reservation engine
or call the existing bypass and describe it as reservation testing. No temporary global monkeypatch,
production date/SQL edits or runtime state-file swapping on a running bot.

## 4. Isolation contract to prove before implementation

- Isolate journal, CSV, message reference, all corresponding locks and generation counters together.
  `ReservationStore(log_path=...)` alone is insufficient: current message projection uses global
  state paths. Trace every read/write, including stale clear, test send, receipt recovery and views.
- Use trusted fixed-root paths and validated opaque session identity. Define guild/channel/session
  namespace, durable reopening after restart, owner access, retention, cleanup and rollback. No
  command-supplied filesystem paths or silent new schema/SQL selection.
- Keep production adapters/defaults compatible. Do not alter production quota, eligibility,
  timestamps, off-season exclusion, identity, payload, mentions, executor or uncertainty semantics.
- Explicitly suppress all allowed mentions for diagnostic sends and edits. If a visible diagnostic
  label is proposed, fit it within canonical budgets and document the limited payload difference.
  Local-time controls must not escape to shared production state or acquire broader authority.
- Preserve once-only offloads and cancellation drainage. Do not hold filesystem locks over Discord
  awaits. Fail closed on invalid state, contention, uncertain receipt or failed persistence; never
  retry a possibly delivered send merely to make the smoke pass.
- Separate same-day edit from fresh admission: a second renderer invocation may edit and therefore
  does not prove reservation rejection. Provide a bounded read-only admission/receipt observation
  or deterministic companion test that proves guard behavior without forcing a live duplicate.
- Define status output from actual outcome: sent / edited / guarded / uncertain / failed, with
  positive message receipt, destination and durable phase where appropriate. A returned coroutine
  or generic success log is not proof of publication or persistence.

The operator has approved this diagnostic direction, not an exact storage format, retention policy,
new SQL object, production reset/delete capability or general-purpose forced-send command. The first
response must make those decisions reviewable and request approval before runtime or test edits.

## 5. Candidate manifests — exact paths must be finalised in scope response

Runtime candidates: `commands/admin_cmds.py`, a small `stats_alerts/diagnostics.py` service (proposed),
`stats_alerts/dispatch_reservations.py`, `stats_alerts/state.py`, `stats_alerts/guard.py` and
`stats_alerts/embeds/prekvk.py` only where dependency injection is required. Identify whether any
view/registration helper actually needs modification; do not pre-authorise unrelated rewrites.

Test candidates: a new `tests/test_prekvk_dispatch_diagnostics.py`, existing reservation, Pre-KVK
embed, state, guard, fighting lifecycle and command registration/permission suites selected by
actual paths. Docs: this pack/starter, task indexes, canonical command reference, command versions
and operational smoke/recovery guidance where required by grouped-command conventions.

SQL manifest: **empty unless independently justified and approved**. Existing report reads reuse
the current service/DAL. A no-diff skip requires no schema/procedure/view/index/UDT/ProcConfig,
embedded query, DAL result-shape or SQL deployment delta. If any changes emerge, inspect the SQL
source repository, produce a separate exact manifest, validation and Changes review target.

## 6. Validation and smoke acceptance

Run selector with actual changed paths; architecture/deferred/security-routing validators, focused
pytest, smoke imports, registration and pre-commit. Run the full suite/log-noise check for changed
tests and persistence/command integration. Document justified skips. Tests must prove:

- Admin/notify boundary, wrong guild/channel, missing permissions, invalid session and no arbitrary
  destination/path escape; mention suppression for sends, edits, errors and component callbacks.
- Real protocol entry, positive receipt projection, isolated paths/locks and byte-for-byte unchanged
  production state across success, clear, failure, cancellation, restart and concurrent sessions.
- Same-session contention, distinct-session behavior, owner checks, existing edit vs guard semantics,
  UTC rollover, unknown/stale owners, accepted/uncertain recovery and fail-closed corrupt state.
- One worker invocation, loop responsiveness and cancellation drainage; existing production default
  paths/behavior and all Phase 1–2G payload/permission/visibility/mention contracts preserved.

Security gate: bot **Scan type: Changes; Deep off**, exact immutable base/head or docs-only skip as
applicable. New command, network destination and restart-sensitive paths require a scoped diff
review; no routine Codebase/Deep scan. SQL history receives a separate review only if changed.

After approved implementation, review, merges and production-main deployment, operator smoke:

1. Record deployed head; inspect isolated session identity and production state baseline.
2. Invoke in the permitted admin location with the explicit diagnostic destination. Observe one
   mention-neutral Pre-KVK message, valid payload/buttons and matching committed receipt/CSV/reference.
3. Reinvoke same session; verify expected edit/guard outcome without another fresh publication.
4. Gracefully restart; reopen the same durable session and verify identity/receipt retention and
   repeat behavior. Compare production state to baseline accounting for independent natural traffic.
5. Exercise permission rejection without sending. Record UTC times, message link, outcome and logs.

Do not inject live crashes, ambiguous Discord failures, simultaneous bot processes, forced mentions
or delete/reset uncertain records. Deterministic tests own those failure boundaries. Diagnostic
protocol smoke and natural production calendar/scheduler dispatch are separate acceptance rows.
The diagnostic enables broader validation now; it does not promise exactly-once or complete live
failure coverage. Carry any unobserved natural window into a named operator observation with owner.

## 7. Separate work and closure

Keep singleton repair, public child-task lifecycle, generic tracked-view timeout, DM redesign,
broad JSON consolidation, Stats/KVK History executor audits and ProcConfig pending-result/error
propagation repair separate. The 09:20:17 ProcConfig error and misleading pipeline success require
their own SQL-aware scope; the transient Sheets 503 recovered and does not justify a retry redesign.
The Phase 2F next-natural-public-save observation stays separate. Explain a hard dependency if one
is proved; do not silently expand this task.

Phase 2H closes only after its approved command, isolation and deterministic gates pass and operator
Discord protocol/restart smoke is recorded. Preserve any remaining natural production-window gate
honestly. Archive this pack only on explicit acceptance; leave operator merges/deployed-head
verification visibly pending until evidenced.
## Approved implementation record — 2026-09-08

The operator approved the design and retained Phase 2H scope. Mirror #258 is merged at
`4cf1faddf0e5165b0a7f1e4d0f268b87baa71935`; production #565/main is
`c0a3bc6ba5a618d5b6a2d9e26d7d4d332f5558ab`. All 916 Python blobs match clean mirror base
`69895f32fefd18f77b4f1e1d6001e66bd5adebad`. Production changes since reviewed runtime
`fea2767f` are documentation only. SQL is clean at `fc0e94ebd2e0a98286069c8a8b71365dd5178657`.

Operator deployment evidence: "production is deployed", followed by
`c0a3bc6ba5a618d5b6a2d9e26d7d4d332f5558ab 2026-09-08T10:49:43+01:00 Merge pull request #565`.
This is operator attestation plus commit evidence, not independent process inspection; the
timestamp is the commit timestamp, not a measured restart time.

Implementation branch: `codex/discord-embed-payload-safety-phase-2h`, isolated mirror clone.
Runtime manifest: `commands/admin_cmds.py`, `stats_alerts/diagnostics.py`,
`stats_alerts/diagnostic_sessions.py`, `stats_alerts/dispatch_reservations.py`,
`stats_alerts/state.py`, `stats_alerts/embeds/prekvk.py`,
`ui/views/prekvk_dispatch_diagnostic_view.py`, `bot_instance.py` (diagnostic teardown only).

Test manifest: new `tests/test_prekvk_dispatch_diagnostics.py`,
`tests/test_prekvk_dispatch_diagnostic_view.py`, `tests/test_prekvk_dispatch_diagnostic_lifecycle.py`;
extended `tests/test_command_registration_smoke.py` and `tests/test_validate_command_registration.py`. Existing reservation/embed/state/guard,
off-season and fighting lifecycle suites are regression gates without unnecessary edits.
Documentation manifest: this pack, its starter, task index, README-DEV, canonical command reference,
events/reminders, diagnostics runbook and deferred register.

The command and complete persistence/lifecycle contract are recorded in
`docs/reference/runbook_diagnostics.md`. No production routing, payload budget, SQL, shared-state
swap or global runtime monkeypatch changes. Existing production adapters retain defaults.
Command version is v1.02; expected registration is 36 primary / 101 grouped / 25 ops / 3 prekvk.
No shared view, guard, registration helper, dependency or config source edit.

SQL manifest: empty. No schema/procedure/view/index/UDT/ProcConfig, embedded query, DAL result-shape
or deployment delta. Bot security gate: Changes only, Deep off, exact immutable final diff.
SQL receives a separate no-diff skip.

Validation at runtime commit `81ee0a70c9c87ba6db68f3cbd29dafabce8a7bbc`: focused regression
149 passed; full suite 3357 passed / 2 skipped; pytest operational log-noise check passed.
Tests used the repository-pinned filelock 3.20.0. All pre-commit hooks, architecture boundaries,
deferred-item validation, security routing, imports and command registration passed. Selector
recommended the full suite and registration/import gates, all satisfied.

Changes-only security scan `3a280eb6-65e6-4905-8c47-d56cc3698baf` is sealed complete with
zero reportable findings and no deferred discovery. Deep remained off. Immutable target:
`69895f32fefd18f77b4f1e1d6001e66bd5adebad..81ee0a70c9c87ba6db68f3cbd29dafabce8a7bbc`.
Subsequent task-pack/starter evidence edits receive a documentation-only review/skip: no runtime,
permissions, configuration, dependencies, network, SQL or persistence behavior changes.
Code review found no blocking issue; mirror merge readiness does not imply live acceptance.

Existing singleton/public-child lifecycle, generic view timeout, DM/JSON redesign, Stats/KVK
History executor audits, ProcConfig result/false-success repair and Phase 2F natural-save observation
remain separately owned by Chris Watts. Fighting-KVK diagnostic parity is future scope.
Diagnostic Discord smoke and natural calendar routing remain distinct pending acceptance rows.
Do not archive this pack merely on implementation delivery.

### Live registration correction

Operator restart exposed Discord HTTP 50035: `/ops` had 26 options, exceeding the 25 limit.
The previous count gate passed an invalid payload. The diagnostic now registers as
`/prekvk dispatch_test` in `commands/prekvk_cmds.py`, with the same admin AND notify gate,
destination checks, ephemeral responses and isolated service. Existing `/ops` commands stay put.
No session migration is needed. Runtime correction manifest: `commands/admin_cmds.py` (removal)
and `commands/prekvk_cmds.py` (relocation); validation tooling additionally changes
`scripts/validate_command_registration.py`. The command smoke serializes actual group payloads
and recursively checks their option counts; static validation rejects a 26-child group and
accepts 25. Existing scan/test evidence above remains tied to its original revisions; updated
validation and separate mirror/production Changes-only results belong to the PR follow-up.

### Live invocation correction

Operator confirmed restart and deployed pre-merge production head `b1d22543`. Registration
succeeded, but both diagnostic invocations failed in Pycord option conversion before the callback.
Postponed `discord.Option(...)` annotations in the new module were retained as strings; destination
was serialized as string instead of channel, then `_invoke` raised at `issubclass`.
The v1.02 command uses explicit evaluated Option defaults with channel/str annotations, matching
existing working declarations. No shared helper, dependency or persistence change. The command
boundary tests now call real Pycord `_invoke` with resolved channel input, optional defaults,
explicit run/status and session values across allowed and rejected permission cases. They also
assert the serialized channel type and action choices. The regression reproduced the supplied
TypeError before the fix and passed after it. These failures provide no reserve/send/commit receipt;
isolated protocol and natural production routing smoke remain pending.
