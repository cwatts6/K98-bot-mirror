# K98 Bot Reference Docs

## Current KVK delivery status - S4B closeout, 2026-09-11

**S4B is complete, operator accepted, successfully synthetic-smoke tested and merged.**
Mirror [#269](https://github.com/cwatts6/K98-bot-mirror/pull/269) merged at 21:06:11 UTC as
`39c93df39485d796fd66881e47562da112886da1`; private bot [#576](https://github.com/cwatts6/k98-bot/pull/576)
merged at 21:06:38 UTC as `63fcb392385fd2ccad78801cbd4f8bd70f426cc3` on 2026-09-11.
Local mirror main/origin main is `64f6b058c224e749ece334d66cdf0efc81bd983d` (synchronized from the private merge);
local production/main matches that private merge. SQL main remains `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
Both repositories were clean at closeout entry; local pulls are complete. The operator confirms **no bot-machine pull**.

The archived S4B pack retains actual real-SDK/disposable-SQL synthetic smoke: private recovery,
public Viewer publication, fresh-client reconciliation/deduplication and retired-slot reuse succeeded.
These are historical bounded smoke results, not a post-merge live rerun. Final review-fix validation:
150 focused tests passed; full suites passed in both checkouts with 3,940 passed / 34 skipped
(production 166.93s, mirror 168.50s), operational logs unchanged. Imports and registration 36/100 passed.
Separate exact Changes reviews, Deep off, completed with zero findings; both review comments were resolved.
Production quality and secret CI passed. Earlier incomplete smoke attempts remain historical evidence.

**Next: S5A Private Intake and Admin Controls in a new chat, after explicit S5A G3 approval.**
S1/S3B/S4A/S4B prerequisites are accepted. Start with fresh repo/contract checks and preserve this pending
closeout documentation. The S5A pack requires its exact documentation carry-forward manifest, both sides
of both S4B archive moves, repaired links and this evidence in its eventual separately authorized PR.
No S5A implementation or new chat was started by this closeout.

S4B-MP01 is complete. S5B-REC01 and S6-OPS01/PERF01/CAP01 remain open under their named gates;
they do not block mocked S5A development and are not closed by S4B smoke. Source routing remains disabled.
No bot-machine update/restart, deployment, production SQL, real import/export or Discord action is authorized.
Use mocks/fake destinations; any disposable SQL target and exact operations require explicit authorization.
Preserve all retained predecessor and S4B disposable databases. Historical prerequisite wording below is
retained as history; accepted slices stay closed and S5A/S5B/S6 retain separate approval gates.



This folder contains active project standards, operating runbooks, and domain references.
Do not read every file for every task. Use the tiers below.

## Required For Every Repo Task

Read these before implementation work:

- `../../README-DEV.md`
- `K98 Bot - Project Engineering Standards.md`
- `K98 Bot - Coding Execution Guidelines.md`
- `K98 Bot - Testing Standards.md`
- `K98 Bot - Skills & Refactor Triggers.md`
- `K98 Bot - Deferred Optimisation Framework.md`

Read the task brief, issue, or task pack before these documents when one exists.

## Conditional References

| Area | Reference |
|------|-----------|
| Deferred optimisation backlog | `deferred_optimisations.md` |
| Deferred optimisation batching/scoring | `K98 Bot Deferred Optimisation Scoring Model.md` |
| Command reference and command-surface governance | `canonical_command_reference.md` |
| Promotion or deployment | `Promotion Guide.md`, `runbook_devops.md` |
| Environment variables or runtime config | `ENV_REFERENCE.md` |
| Local SQL setup or disposable integration testing | `local_sql_development.md` |
| Startup lifecycle | `runbook_startup.md`, `singleton_lock.md` |
| Shutdown/recovery lifecycle | `runbook_shutdown.md`, `singleton_lock.md` |
| Diagnostics, telemetry, offloads, queue recovery | `runbook_diagnostics.md` |
| Repo navigation | `runbook_structure.md` |
| Helper or shared utility changes | `REVIEW_HELPERS.md` |
| MGE work | `mge_reference_model.md` plus SQL repo validation |
| Honor ingestion | `honor_scan.md` |
| Event reminders and calendar reminders | `events_and_dm_reminders.md` |
| Weekly activity import | `weekly_activity_importer.md` |
| Security-sensitive work or Codex Security routing | root/applicable `SECURITY.md`, `AGENTS.md`, and the K98 security routing skill |

## Archive

Historical or consolidated notes live in `archive/`. Do not use archived files as active guidance.
Current standards and runbooks override archive content.

Archived examples include:

- historical quality automation task spec
- superseded helper standards note
- old rehydrate test note
- old operations note
- resolved deferred optimisation history

## Templates Live Elsewhere

Reusable task and initiation templates live in `../templates/`. Do not treat template generator
docs as mandatory reading unless the task is to create or update a task pack.

## SQL Source Of Truth

For SQL-facing work, validate object names, columns, procedures, views, indexes, and `ProcConfig`
usage against:

`C:\K98-bot-SQL-Server`

The SQL repo overrides inferred schema assumptions from Python code.

## KVK Source Migration audit

For migration work, read the [decision/evidence register](kvk_source_migration/decision_and_evidence_register.md)
and [Phase 1 audit](kvk_source_migration/phase_1_audit.md). The audit links the dependency and field
matrices, proposed next slice and validation log. Delivered 2026-09-09 for operator review;
B0/deployed-state/aggregate-period limits remain explicit. No implementation is approved.


## KVK Source Migration — Phase 2A architecture review

The 2026-09-09 bounded design pass is delivered: [contract and architecture](kvk_source_migration/phase_2_contract_and_architecture.md),
[synthetic acceptance scenarios](kvk_source_migration/phase_2_acceptance_scenarios.md), and
[evidence/validation](kvk_source_migration/phase_2_evidence_and_validation_log.md).
Latest B0, per-fight/final-overall and Pass-4 evidence supersedes earlier missing-input wording.
G2 awaits operator review; no implementation or Phase 2B packs approved. Local SQL/config parity
is operator-attested; independent live rows/jobs remain later readiness evidence.


KVK Phase 2A clarification (2026-09-09): authorized EndScanID changes are explicit player-window
corrections through normal configuration processing, without a separate correction command.
The contract and scenarios T68-T70 now cover interim scans, revised finals and pending endpoints.
G2 remains pending; no Phase 2B packs or implementation started.


## Phase 2B delivery and G2 approval — 2026-09-09

Chris Watts explicitly approved: **“G2 approved, please proceed”.** G2 is approved, including
the EndScanID clarification and scenarios T68–T70. This supersedes earlier G2-pending/no-pack
statements as current status; their historical evidence remains intact. Phase 2B planning is
delivered in the [implementation plan](kvk_source_migration/phase_2_implementation_plan.md)
and [planning evidence log](kvk_source_migration/phase_2b_evidence_and_validation_log.md).
Ten bounded task packs and matching starters are prepared. **G3 remains pending per slice; S1 is
the recommended first approval.** No implementation, SQL change, live action, PR or deployment
is authorized by this delivery. S6 prepares readiness evidence and stops at separate G4 approval.


## Current S4B validation follow-up - 2026-09-11

S4B is accepted and merged; the current closeout record and archived pack supersede historical review-pending text. The remaining synthetic multi-period component test is complete. Track the [named follow-up register](kvk_source_migration/phase_2_implementation_plan.md#s4b-follow-ups) for S5B integration and S6 operational interruption, shared-quota throughput and capacity gates. These remain explicit acceptance work, not permission to execute future packs or activate routing.
