# K98 Bot Reference Docs

## Current KVK delivery status - 2026-09-10

**S1 is accepted and merged** through mirror PR #263 and production PR #570. Its archived
200-test smoke and restart/startup evidence remain historical S1 results.

**S2A is complete, operator accepted and merged.** SQL [PR #78](https://github.com/cwatts6/K98-bot-SQL-Server/pull/78)
merged as `845a25fe66b1d2365fb38720390b4dadf50baa67`; mirror
[PR #264](https://github.com/cwatts6/K98-bot-mirror/pull/264) merged as
`9fc0255dbaa0cbcb80c63c563657dad90bd5bcec` on 2026-09-10. Review fixes passed 401 static
assertions and 96 disposable SQL rejection cases, with twelve-table rollback verified.

**S2B is complete, accepted and merged:** SQL #79, mirror #265 and private bot #572
merged on 2026-09-10. Final validation passed 265 static assertions and 144 disposable SQL
rejections with 25-table rollback; the seven-file review-fix Changes scan found zero issues.
**S3A is complete, smoke accepted and merged.** Mirror #266 merged at 11:28:48 UTC
(`3154997fa2dfc124da75ee35dca79463c3196a43`); private bot #573 merged at 11:29:18 UTC
(`140fc89765b1d6ec8418ac6f6d039e575419c29e`) on 2026-09-10. At the S3A checkpoint, local mirror main was
`9d08b3bf9e7cac6c95db1c4a120c8bf0aad7475f` after synchronization; SQL main remains
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Operator smoke passed 77 tests with operational
logs unchanged and registration 36/100 without drift. The S3A pack/starter are archived.
**S4A is complete, operator smoke accepted and merged.** Mirror [#268](https://github.com/cwatts6/K98-bot-mirror/pull/268) merged on 2026-09-10 at 16:12:39 UTC as `eba04639eced51e368d6fc7036284f25640ce871`; private bot [#575](https://github.com/cwatts6/k98-bot/pull/575) merged at 16:13:04 UTC as `021fc7adc9952ab07d21517e8e47f3966c285f7a`.
Operator candidate smoke on `055b9590e1114661ff0369c7815fbbea82661454` passed imports, registration **36/100** without drift/duplicates, **134 focused tests in 11.97s**, and **3,810 full-suite tests with 34 skipped in 134.19s**. Both pytest runs left operational logs unchanged. This closes the S4A full-suite gap; earlier stalls and passes remain historical evidence, not a post-merge rerun.
Local mirror `main` is `7baf92c7badc3f40006841046825a788bc823373`; local `production/main` is `021fc7adc9952ab07d21517e8e47f3966c285f7a`; SQL `main` remains `44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Bot and SQL checkouts were clean at closeout entry. Local pulls are complete, per operator and local refs; **nothing has been pulled to the bot machine**.
S4A pack/starter are archived. **Next: S4B Versioned Exports and Delivery in a new chat, with separate S4B G3 approval.** S4B's pack requires all pending closeout documents and both archive rename sides in its eventual separately authorized PR. Prior S3B closeout documents were included in the merged S4A PRs.
Source routing remains disabled. No bot-machine update/restart, SQL deployment, live imports/exports, Discord action or activation is needed for S4B local development. Use mocks/fake destinations unless a disposable SQL target and exact operations are explicitly authorized first; preserve retained S2A/S2B/S3B databases. Historical prerequisite wording below does not reopen completed slices.


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

S4B implementation is local for review; its latest pack evidence supersedes historical G3-pending entry text. The remaining synthetic multi-period component test is complete. Track the [named follow-up register](kvk_source_migration/phase_2_implementation_plan.md#s4b-follow-ups) for S5B integration and S6 operational interruption, shared-quota throughput and capacity gates. These remain explicit acceptance work, not permission to execute future packs or activate routing.
