# K98 Bot Reference Docs

This folder contains project standards, operating runbooks, and domain references.
Do not read every file for every task. Use the tiers below so repo work starts with the
right contract without turning every change into a documentation crawl.

## Required For Every Repo Task

Read these before implementation work:

- `../../README-DEV.md`
- `K98 Bot — Project Engineering Standards.md`
- `K98 Bot — Coding Execution Guidelines.md`
- `K98 Bot — Testing Standards.md`
- `K98 Bot — Skills & Refactor Triggers.md`
- `k98 Bot — Deferred Optimisation Framework.md`

Read the task brief, issue, or task pack before these documents when one exists.

## Conditional References

Use these when the task touches the relevant area:

| Area | Reference |
|------|-----------|
| Deferred optimisation batching | `deferred_optimisations.md`, `K98 Bot Deferred Optimisation Scoring Model.md` |
| Promotion or deployment | `Promotion Guide.md`, `runbook_devops.md` |
| Environment variables or runtime config | `ENV_REFERENCE.md` |
| Startup, shutdown, diagnostics, lifecycle | `runbook_startup.md`, `runbook_shutdown.md`, `runbook_diagnostics.md`, `singleton_lock.md` |
| Helper or shared utility changes | `REVEIW_HELPERS.md` |
| MGE work | `mge_reference_model.md` plus SQL repo validation |
| Honor ingestion | `honor_scan.md` |
| Event reminders and legacy DM reminders | `events_and_dm_reminders.md` |
| Weekly activity import | `weekly_activity_importer.md` |

## Background Or Historical References

These are useful for context but should not be mandatory for routine coding:

- `OPERATIONS.md`
- `Quality Automation + Review System.md`
- `rehydrate_view_tests.md`
- `helpers_project_standards.md`
- `runbook_structure.md`

Phase 2 of the reference-doc cleanup will update, consolidate, or archive these files.

## Templates Live Elsewhere

Reusable task and initiation templates live in `../templates/`. Do not treat template
generator docs as mandatory reading unless the task is to create or update a task pack.

## SQL Source Of Truth

For SQL-facing work, validate object names, columns, procedures, views, indexes, and
`ProcConfig` usage against:

`C:\K98-bot-SQL-Server`

The SQL repo overrides inferred schema assumptions from Python code.
