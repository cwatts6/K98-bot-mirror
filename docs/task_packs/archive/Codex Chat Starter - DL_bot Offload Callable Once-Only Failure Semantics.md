# Codex Chat Starter - DL_bot Offload Callable Once-Only Failure Semantics

> **Completed record — 2026-09-01:** This starter launched the delivered once-only fix. Automated
> validation, PR review, a Changes security review with Deep off, and operator Discord smoke all
> completed successfully. The duplicate MGE import failed as expected and a standard scan import
> succeeded. This archived file is retained as execution history, not active work.

```markdown
# Files mentioned by the user:

## Codex Task Pack - DL_bot Offload Callable Once-Only Failure Semantics.md: C:\discord_file_downloader\docs\task_packs\Codex Task Pack - DL_bot Offload Callable Once-Only Failure Semantics.md

## My request for Codex:
Work in the current local `C:\discord_file_downloader` repository/worktree.

Read and execute:

`C:\discord_file_downloader\docs\task_packs\Codex Task Pack - DL_bot Offload Callable Once-Only Failure Semantics.md`

Begin with audit, deterministic reproduction, call-shape inventory, and architecture review only.
One-pass implementation is not approved. Stop for my approval at every checkpoint required by the
task pack.

The required outcome is that one `_offload_callable` request can enter its submitted callable at
most once. If callable execution begins and then raises, is cancelled, times out, or has an
indeterminate dispatched outcome, propagate that outcome without invoking the callable through a
second backend. Fallback is allowed only when a backend is absent or can prove it rejected the work
before callable entry.

Verified baseline facts to re-check rather than assume:

- The production MGE route passes four positional importer arguments: file bytes, filename,
  uploader ID, and `MgeResultsImportAuditContext`.
- `file_utils.run_blocking_in_thread` is the first compatible executor reached for that shape.
- The current broad catch then falls through to `asyncio.to_thread` when the importer raises,
  causing repeated parsing/audit/database work.
- `file_utils.run_maintenance_with_isolation` has a different argument/result contract.
- `file_utils.start_callable_offload` is a synchronous module/function process launcher, not the
  awaitable arbitrary-callable executor assumed by the current chain.

Locked constraints:

- Preserve successful callable results and the existing MGE route success/failure embed and audit
  behavior.
- Preserve every current direct and injected `DL_bot` call shape.
- Keep non-idempotent once-only semantics as the default; do not introduce an automatic or
  opt-in callable retry in this task.
- Do not use SQL deduplication or importer idempotence as a substitute for the caller guarantee.
- Do not fix similarly shaped helpers in `stats_module.py` or `ui/views/kvk_history_view.py`
  without separate approval; audit and capture proved debt instead.
- Keep the upload-admission/backpressure deferred item separate.
- Make no SQL, config, dependency, command, permission, asset, cache, scheduler, backup cadence, or
  live schedule change.
- Do not run live Discord uploads, production SQL, backup triggers, shutdown-marker writes,
  restarts, resyncs, process cancellation, deployment, or load tests during local implementation.
- A routine final security review must use the bot Git diff with Scan type `Changes` and
  `Deep: Off`; do not run a standard or deep codebase scan.

Your first response must contain:

1. Scope summary and locked exclusions.
2. Deterministic pre-fix reproduction showing the four-argument invocation count and propagated
   outcome.
3. Candidate backend contract audit: signatures, awaitability, result shapes, pre-entry rejection,
   cancellation/timeout, and post-dispatch ambiguity.
4. All direct and injected `DL_bot` call shapes and their side-effect risk.
5. Proposed architecture ownership and minimum safe once-only state machine.
6. Test-selection output plus focused/full-suite/log-noise/smoke/registration validation plan.
7. Security decision: bot Changes review against the final verified base/head, Deep Off; SQL repo
   not affected.
8. Any statement that cannot be verified without guessing.
9. The exact decisions requiring my approval.

Do not edit runtime code in the first response. Stop for approval.
```
