> **Current P02 checkpoint, 10 November 2026:** D3 source and review are complete; private [PR739](https://github.com/cwatts6/k98-bot/pull/739) is merged at `5ec55e3b`, with all six final checks passing. D2/D3 are not deployed. The [D4 scope and handover](Startup%20Import%20Export%20Reliability%20-%20P02%20D4%20Scope%20and%20Handover%20-%202026-11-10.md) is the current entry point; begin with a scope review and missed/new-item check. D4 owns installed/manual/legacy and exact combined release compatibility; D5 owns final combined qualification. Deployment remains held until D4/D5 are complete and a separate release decision is made. P03 actual blockers plus essential P04 corrections precede the first normal import/export. Earlier dated status remains historical.

## Phase 1 lessons carried forward, 9 November 2026

- Reproduce the actual failure in permanent tests: qualified host case variants,
  native permission-entry order, harmless catalogue row shuffling and genuine
  column-order/privilege drift need different positive and negative controls.
  Never repair an expected fingerprint by adopting an unreviewed live hash.
- Native SQL commitment, installer completion, startup verification and provider
  acceptance are separate outcomes. Resume exact remaining release stages;
  never reapply committed SQL or start a second process after an unknown start.
- Use Windows PowerShell 5.1 for production-script qualification. Preserve full
  child errors, explicit arrays and evidence shapes across process boundaries.
  Compress bounded evidence instead of casually increasing collection limits.
- Test-monitor failures can follow successful business work. Read retained
  completion/output evidence before replay. Track exact connection identities,
  not reused session numbers. Metadata-reader success does not qualify history
  readers across index DDL; retain the SQL 3961 case for P02 maintenance work.
- Latest shared names apply across all reports; historical statistics remain
  historical. Check date windows against the actual report clock and do not
  mistake unspecified tied ranks for changed scores or name regressions.
- Keep scope/recovery dependencies explicit: first standard import/export after
  actual P03 blockers and essential P04 corrections, not automatically after
  every incident closes or only at the end of P05. No replay to make status green.

# Reliability programme: engineering and acceptance principles

Operator reaffirmed 6 November 2026 at P01.6 closeout. Apply alongside AGENTS.md and the seven core engineering references, not as a replacement. Current order is P02, remaining P03, P04, P05, then the separately deferred follow-ups and applicable wider programme work. P01.2b was closed by decision without feature delivery; do not resurrect its rejected monitoring design.

## Whole-solution scope

1. Begin each packet with review/scope. Map the complete affected flow, equivalent callers, shared helpers, direct and alternate entrypoints, scheduled/manual/legacy use, cancellation, recovery, cleanup and diagnostics. Avoid spot fixes, larger timeouts and blanket retries presented as architecture.
2. Design for the whole programme, then deliver coherent PR-sized slices. Give each finding one owner and explicit dependencies. P05 confirms combined delivery; it must not be used to postpone missing functional fixes. Existing accepted work is not reopened without evidence.
3. At scope, design, implementation, PR, promotion and acceptance, reconcile the source/caller census, finding register, tests and scope matrix again. Record additions, omissions, adverse evidence, residual limits and next owners. Fix related defects; capture unrelated work rather than silently expanding or narrowing scope.
4. Reuse established layers/helpers. Commands and views route authorized interactions; services own business rules/coordination; DAL owns SQL and persistence. Critical authority must survive restart. Avoid parallel frameworks, duplicate orchestration and new permanent observers without measured justification.

## Bot and SQL are one investigation

Assess Python scheduling, worker admission, cleanup, data transfer, stored procedures, views, indexes, table configuration, statistics, isolation, transaction/lock lifetime and maintenance as one path. Validate contracts against `C:/K98-bot-SQL-Server` and actual approved deployment evidence. Include all dependent startup fingerprints, grants/signatures, result shapes, migrations and rollback. A fast isolated procedure or passing Bot mock is insufficient.

Compare targeted optimisation with a full procedure or flow rewrite when evidence justifies it. Preserve business semantics, authoritative receipts and authorization. Measure representative distributions, worst allowed bounds, read/write/log/storage costs, concurrency, restart and both arrival orders. An index's read benefit must be weighed against import overhead. Local memory mitigation is not a production configuration recommendation.

Evaluate SQL-originated change/completion signals, notifications or durable queued events as alternatives to repeated polling, alongside cheaper bounded reads and identity-bound reuse. This is a design option, not a selected technology or promise of less contention. Verify installed SQL/driver capability and operational constraints before proposing a mechanism. Compare writer overhead, transaction coupling, permissions, event volume, acknowledgement, duplicates, ordering, missed delivery, reconnect/resubscribe, catch-up, retention, poison events, fallback and shutdown. A signal is a hint or durable event under a defined contract; it must not replace authoritative action-time identity/version/receipt validation. Do not put provider/network effects inside a SQL transaction or make optional notification delivery gate business commit.

## Outcomes, ownership and evidence

- Separate requested/accepted/started/completed/unknown effects from audit, cache, render, delivery and observation. A UI deadline or cancelled awaiter does not stop a native worker. Retain exact ownership until physical cleanup; do not release capacity, retry or start a successor on observation alone.
- Preserve first failure and later settlement, committed captures and provider receipts. No replay of committed imports or provider mutations to repair bookkeeping. No forced/age-based release, clearing unknown outcomes or deleting evidence to make status green.
- Carry D01-D06 through existing bounded evidence: operation/attempt/parent correlation; initiating actor versus executor/session; resource/mode and actual holder versus requester; connection/admission/wait/hold/execution/commit/cleanup timing and original codes; durable effects and remaining work; observed/not-applicable/unavailable with provenance and time. Known-holder tests must identify the holder. Do not invent historical attribution.
- Diagnostics and status remain passive and bounded. Optional logs, clocks, CSV, audit and notifications cannot redefine business success or block required work. Mandatory custody, ownership, commit and integrity receipts stay mandatory. No polling ledger, automatic provider probe or broad history scrape merely to fill a dashboard.
- Separate cold/warm reads, database execution, result consumption, loop scheduling, physical rendering and Discord delivery. Sample counts are not exact CPU shares; correlation is not full causation. Preserve unsuccessful runs when a later run passes.

## Startup, Windows custody and deployment

Verify actual machine, identity/elevation, shell, installed source/updater, runtime admission, SQL contracts and retained work before proposing operations. On MINI_AMD use reviewed elevated Windows PowerShell 5.1 workflows. Development privileges do not establish production ownership.

Before every release, inventory every changed path and existing ancestor on the actual host, including tests, documentation and archive folders. Owner, ACL/inheritance, attributes, reparse/hard-link/stream state, bytes and prior handles are separate requirements. Hash matches and clean Git do not prove custody. Keep protected source/updater/startup policy separate from application-writable state. Use bounded reviewed fresh-object replacement when necessary; retain originals and interruption/resume evidence. No blanket takeown/icacls, recursive cleanup or weakened guards.

Review the complete final delta once before requesting host checks; consolidate collectors where practical. New paths still need coverage. Present redirected child paths with forward slashes in code fences to avoid missing separators before `.codex` and `.codex_artifacts`.

Qualify Bot and SQL independently, then their deployment order together. Mirror PR review precedes file-patch private promotion; never merge private/mirror histories or deploy the mirror. Upgrade the installed updater if the exact reviewed transition requires it; verify all SQL startup contracts before drain and on successor. Deploy private main via the protected updater, one graceful restart when prompted. No live Git pull/reset, manual task start or package changes to bypass a guard. Prepare concrete rollback for the actual source/SQL/contract combination; do not invent a reverse switch.

## Validation and acceptance

Use meaningful negative, permission, real-thread cancellation/drain, restart, uncertainty, concurrency and cost cases. Qualify actual child maintenance procedures and installed legacy paths, not just stubbed parents. Test final formatted/pinned artifacts and user-visible interactions against deployed dependency behavior. Keep production operational logs untouched by tests.

Run architecture, deferred, test-selection and security-routing gates. For security-sensitive changes, use exact Bot/SQL Changes reviews, Deep off, through the routing skill; no inferred repository-wide security audit. Tests do not replace review. Failures are fixed if related; unrelated failures remain documented unless scope expansion is explicitly authorized.

Keep four separate verdicts: source qualification, current host readiness, installed release, exercised functional acceptance. Preserve source hashes, timestamps, denominators and unavailable evidence. A partial report containing only resolved rows cannot explain open incidents. Monitor completion, Discord online, released reservations and zero incident counts do not certify whole-flow import/export.

Exact retained-work disposition and fresh end-to-end acceptance are separate from packet closure. Keep P01.4/P01.5 natural observations, P03a.2 whole-flow acceptance, P02-P05 and P0 credit visible. The final P05 sweep must revisit the complete programme and all newly discovered equivalent cases.
