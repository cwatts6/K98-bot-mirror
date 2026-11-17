# P01.2a: evidence collection, outcome clarity and retained milestones

> **Current programme checkpoint - 4 November 2026 (E68/E69):** P01.2a is deployed and accepted for its declared reporting/evidence scope at private `67c4e12a8ecf0c25280770860480ac65a6826602`.
> Read the [P01.2a closeout](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Closeout%20-%202026-11-04.md) for delivered corrections, evidence limits, learnings and remaining owners; [P01.2b handover](Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Handover%20and%20Scope%20-%202026-11-04.md) is the next review/design task.
> Earlier dated statuses, holds and next-action instructions in this document are retained history and are superseded for current scheduling. P01.3-P01.6/P02-P05 and exact incident recovery remain open; no replay of accepted work.

**Current E64:** mirror [#482](https://github.com/cwatts6/K98-bot-mirror/pull/482) and private [#722](https://github.com/cwatts6/k98-bot/pull/722) are merged. Private target `07bc9d6ebd5964f9bf660822f03a932a2472d966` is prepared for operator deployment, with final review, CI and the packet recorded in the [review/merge receipt](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Review%20and%20Merge%20-%202026-11-03.md). No production deployment, restart or recovery action was performed. Earlier scope, authorization and failed-run receipts below are historical.

Date: 3 November 2026. Status: scope accepted by the user; focused new chat requested
and authorized to begin review/design immediately. The next implementation packet
must resolve the concrete bounds/format/source manifest and qualification below.
This approval does not itself authorize runtime implementation, publication, deployment,
restart, recovery mutation or provider replay. Do not ask the user to reconfirm the
already accepted scope before starting the design work.

Focused review/design is now prepared in the
[P01.2a design and qualification packet](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Design%20and%20Qualification%20-%202026-11-03.md)
(E58). It fixes the proposed bounds, compatibility and qualification decisions;
E59 subsequently approves implementation and local qualification. Publication,
merge and deployment remain separate. The original handoff
below is preserved as the scope and evidence basis.

Continue from the [implementation and qualification receipt](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Implementation%20and%20Qualification%20-%202026-11-03.md)
for the candidate, test/security receipts and remaining gates. Do not repeat the
accepted design work or completed production recoveries.

## Read first and preserve

1. Repository `AGENTS.md`, `README-DEV.md`, reference index and required engineering,
   execution, testing, refactor and deferred-work standards.
2. [P01.1 closeout](Startup%20Import%20Export%20Reliability%20-%20P01.1%20Closeout%20-%202026-11-03.md).
3. [Agreed scope](../Startup%20Import%20Export%20Reliability%20-%20Scope%20-%202026-11-02.md),
   [tracker](../Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md)
   and [P01 design](../Startup%20Import%20Export%20Reliability%20-%20P01%20Design%20-%202026-11-03.md).
4. Root/applicable `SECURITY.md`, diagnostics/helper/lifecycle references selected by
   the index, and the private qualification/live evidence linked by the closeout.

The scope/tracker remain the programme authority. P01.1 is deployed at private
`0247371d90ec88d4c0639e9200164f4256086037`; do not redeploy/restart it or repeat its
business operations. F09/51421 stays P02; exact retained pipeline continuation stays
P03. A diagnostic bundle is evidence, never authority to retry or clear ownership.

## User outcome and accepted scope

Deliver improved evidence collection before P01.2b. Extend the existing authorized
complete-report action so normal-size evidence is obtainable in one download without
manually combining a complete ZIP, ordinary report and runtime observations file.
Keep this independent of protected-launcher changes so it can ship first.

- Include existing incident summary/details plus bounded operation history, startup
  outcomes, diagnostic-worker health and explicit loss/omission counters.
- Add a versioned manifest: available source/process identity with provenance,
  per-component observation/publication/export times, sizes/hashes, schema and
  complete/partial/unavailable coverage. Do not imply a cross-source atomic snapshot.
- Separate a child-worker value from verified parent/feature outcome. A false
  predicate must not read as aggregate failure. Keep parent/child/stage identity;
  explicitly name known startup stages instead of labelling them unavailable.
- Retain first entry, deadline/cancellation, first meaningful failure and terminal
  result separately from bounded rolling detail. Later success must not erase the
  first failure. Count coalescing/trimming, producer drops, context loss and failed
  publication distinctly. Do not solve this by simply increasing buffers.
- Show latest event and available successful-publication evidence so idle history
  differs from failed persistence, without creating a new active health probe.
- Keep collection passive: existing authorized saved-incident reads and diagnostic
  snapshots only. No new provider probes, reconciliation, business execution or retry.
- Bound memory/disk/build cost and concurrent downloads off interaction/event-loop
  critical paths. Keep permission, redaction, archive-name and custody boundaries.
  Do not include secrets, unrestricted raw logs or protected raw launch files.
- Missing/corrupt optional evidence must not suppress useful incident evidence.
  Preserve the complete incident export contract and explicitly expose any exceeded
  bound/continuation. Never label partial content complete or silently drop records.
- Retain old-format readers/history and distinguish legacy ambiguous facts from new
  typed outcomes. Required attempt/phase/terminal receipts remain mandatory.

## Observations that motivate the change

P01.1's production evidence proved the original successful configuration result
survived its deadline. Eight startup references correlated with disk; 23 operations
were settled and all four sink counters were zero. Those outcomes remain accepted.
The investigation nevertheless needed multiple file downloads. Tracked views had
21/21 attached but a child boolean labelled reported_success=false, and 313 worker
transitions were coalesced/trimmed. Known startup stages could render unavailable.
These are concrete collection/interpretation gaps, not proof of lost business work.
The supplied observations cover one process incarnation; do not claim a later live
restart restoration occurred. Use controlled tests and the next necessary restart.

## Architecture and source map

Inspect current implementations, then fix an exact changed-file/caller manifest:

- `core/operation_evidence.py`: explicit result semantics, parent/child/stage context.
- `services/operation_diagnostics.py`: bounded history/milestones, compatible restore,
  passive snapshots, counters, publication evidence and failure isolation.
- `services/recovery_report.py` and `services/recovery_complete_report.py`: align
  ordinary and complete report components without losing incident coverage.
- `services/recovery_service.py`, `ui/views/recovery_backlog_view.py` and relevant
  `ui/views/recovery_view.py` callbacks: retain authorization and existing download flow.
- Startup/result adapters and shared offload callers only where required for accurate
  semantics; use the P01.1 caller inventory rather than invent a parallel framework.

Commands/views render and route; services own collection and projection; DAL remains
the owner of stored incident reads. No SQL schema change is currently proposed.
Validate any SQL-facing assumption against `C:\K98-bot-SQL-Server` before implementation.
Do not infer schema from Python or expand this into SQL contention remediation.

Resolve before coding: exact envelope/schema compatibility, component/archive bounds,
full versus partial behavior, snapshots during concurrent writes, authorization at
collection/delivery, build concurrency/cancellation ownership, source/version provenance,
key-milestone representation and how aggregate outcomes are explicitly supplied.
Choose concrete budgets with rationale and tests, not unspecified promises.

## Required qualification and acceptance

| Area | Required evidence |
|---|---|
| Real report artifact | Open the produced archive; reconstruct a known startup/operation attempt from its manifest, milestones and feature result. Verify component hashes, timestamps and coverage. |
| Outcome semantics | Child false with parent success, parent failure, unknown outcome and multiple child operations. Preserve original returns and required receipt meaning. |
| History/compatibility | Repeated detail around deadlines, first failure then reconciliation, cancellation, restart, mixed old/new records and malformed history. Key milestones survive within bounds. |
| Unavailable evidence | Missing/permission-denied/corrupt/oversized data, failing writer and saturated queues. Available reports still work with truthful limits; no false complete/healthy state. |
| Non-interference | Fail-on-call probes/repair/provider spies; identical business counts/results with collection enabled/disabled; concurrent downloads and actual shared-thread drain/cancellation cases. |
| Access and privacy | Existing actor/guild access checks, unauthorized download, redaction, safe archive members and no privileged raw-file exposure. |
| Cost | Matched collection/diagnostics off/on runs; bounded bytes/memory/concurrency/build latency/event-loop impact and shutdown behavior. State synthetic versus native scope. |
| Production | Review exact deployed target and obtain a normal download using naturally occurring evidence. Do not manufacture faults/restarts/imports just to populate a report. |

Start from existing operation-evidence/diagnostics, startup lifecycle, recovery report,
complete backlog, permission and shared offload tests. Confirm exact filenames and
gaps with the selector plus manual caller review. Run focused tests first; shared
helper/lifecycle changes require the relevant full suite before promotion when practical.
Keep pytest evidence separate from operational logs. Architecture/deferred/security-routing,
registration/smoke as applicable, lint and Changes reviews remain delivery gates.
Use `k98-security-review-routing`, then exact Bot Changes review with Deep off for
implementation; no routine codebase/deep audit. Any SQL delta needs separate review.

## Workspace and evidence handoff

Root `C:\discord_file_downloader` is an older design checkout with intentional
README/index modifications and untracked programme documents, including this handoff.
These files are not yet remotely published. Do not reset, clean, stash away or blanket
commit the existing work; retain the full programme docs when preparing later branches.
Do not use root HEAD as the current production implementation baseline.

Checked locally at handoff:

- Private source checkout: `C:\discord_file_downloader\.codex_artifacts\a1b-updater-correction`,
  clean at deployed `0247371d90ec88d4c0639e9200164f4256086037`.
- Mirror checkout: `C:\discord_file_downloader\.codex_artifacts\p1-mge-mirror-review`,
  clean at `607f6a8136d15c8c60e0fdfed1a059b75e774384` (reviewed follow-up candidate,
  not a claim that it is current mirror main). Refresh branch/remotes before later work.
- SQL source of truth: `C:\K98-bot-SQL-Server`; inspect current state before SQL work.
- Private evidence root: `C:\discord_file_downloader\.codex_artifacts\startup-import-export-review-20261102`.
  Read `p011-merge-qualification.json`, `p011-final-scope-review.md`,
  `p011-report69-review.json`, `p011-live-diagnostics-validation-20261103.json` and
  `p012-scope-amendment-20261103/validation.json`. Preserve original files and hashes.

The source receipts and docs are sufficient to start. Ask only for genuinely missing
installed/live information when a dependent decision needs it. Earlier pre-commit
wrapper attempts hit a read-only global cache and then environment installation;
they were stopped. Documentation validators and introduced-link/whitespace checks
passed. Do not spend the design phase reinstalling unrelated tool environments or
re-running production tests merely to replace that documentation-only limitation.

## First deliverable and later ownership

Begin the focused design now. Produce an implementation-ready P01.2a packet with
exact modules/callers, envelope/bounds/compatibility decisions, negative and concurrency
tests, security routing and rollout/validation evidence plan. Challenge omissions
against shared callers and failure boundaries, then report material decisions and
the implementation approval boundary. No need to repeat the whole programme audit.

P01.2b owns early issuer evidence and offline updater collection. P01.3-P01.6 adopt
the contract for passive health, uploads, calendar and read-worker callers. P02 adds
holder/timing evidence; P03 adds durable effect/recovery links; P04 extends history,
grouping/retention/escalation; P05 verifies combined reconstruction and non-interference.
Nothing in P01.2a closes their separate acceptance obligations.
