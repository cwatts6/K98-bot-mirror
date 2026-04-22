# K98 Bot — Standard Development Initiation Statement

> **Purpose:** Paste this at the start of AI-assisted coding sessions.  
> This is a workflow prompt, not the authoritative architecture document.

---

## Context

This project uses two repositories:

| Repo | Purpose |
|------|---------|
| `cwatts6/K98-bot-mirror` | Python Discord bot |
| `cwatts6/K98-bot-SQL-Server` | SQL Server schema and database objects |

**Deployment model:** local-first.  
Provide complete implementation output suitable for local validation and manual PR creation.

---

## Required Reading Order

Before implementation, review in this order:

1. feature specification or task overview
2. `K98 Bot — Project Engineering Standards.md`
3. `K98 Bot — Coding Execution Guidelines.md`
4. `K98 Bot — Testing Standards.md`
5. `K98 Bot — Skills & Refactor Triggers.md`

If these conflict, follow the priority order in the execution guidelines.

---

## Working Method

### Step 1 — Review scope

**Stop after this step and wait for confirmation unless the user has explicitly asked for a one-pass deliverable.**

Confirm understanding of:

- feature scope
- affected subsystem(s)
- modules likely involved
- SQL schema implications
- command/view implications
- caching implications
- restart/persistence implications
- testing implications
- refactor opportunities in the touched area

Required review question:

> Does the touched area currently contain direct SQL in commands/views, business logic in interaction layers, duplicate helpers, or dead code from prior iterations?

If yes, call it out early.

---

### Step 2 — Validate architecture

**Stop after this step and confirm alignment before coding.**

Check placement:

| Element | Must go in | Must not go in |
|---------|------------|----------------|
| Slash commands | `commands/<domain>_cmds.py` | legacy root modules, `cogs/` |
| Views/modals | `ui/views/` | root-level UI files |
| Business logic | services / subsystem packages | commands, views |
| Repository / DAL | services or repository modules | commands, views |
| Shared low-level utilities | `core/` | new root helpers |
| SQL schema objects | SQL repo `sql_schema/...` | inline schema SQL in Python |
| Tests | `tests/` | omitted delivery |

Also confirm whether the task should include opportunistic extraction from legacy modules.

---

### Step 3 — Confirm implementation plan

**Stop after this step and get approval before writing code.**

Provide a concise plan covering:

- new files to create
- existing files to modify
- SQL objects to create/modify
- command decorator plan
- services/repositories needed
- helpers to reuse
- logging points
- restart safety approach
- test plan
- refactor items to address now vs defer

---

## Implementation Requirements

All code must follow the engineering standards and execution guidelines.

### Non-negotiable rules

- new code goes into target architecture directories
- commands stay thin
- views stay thin
- services own business logic
- no new direct SQL in commands or views
- touched areas must be checked for existing embedded SQL and obvious duplication
- helper reuse must be checked before creating new helpers
- UTC only for persisted times
- module-level logging only
- no `logging.basicConfig()`
- no bare `print()`
- no silent exception swallowing
- critical state must be restart-safe
- destructive actions require explicit confirmation flow

---

## Required Delivery Format

When delivering an implementation, provide:

1. file manifest
2. new files
3. modified files
4. SQL changes separately
5. helpers reused
6. refactor findings in touched areas
7. configuration changes
8. testing steps
9. deployment / migration order
10. deferred debt, if any

For code delivery, provide complete file contents unless a different format is requested.

---

## Prompt Block

Use this starter block at the top of coding sessions:

```text
Read and follow these documents before making changes:
1. Feature specification / task overview
2. K98 Bot — Project Engineering Standards.md
3. K98 Bot — Coding Execution Guidelines.md
4. K98 Bot — Testing Standards.md
5. K98 Bot — Skills & Refactor Triggers.md

Required working approach:
- Audit the current implementation first.
- Map the affected modules, services, SQL objects, views, caches, and restart implications.
- Identify obvious structural debt in the touched area, especially:
  - direct SQL in commands/views
  - business logic in interaction layers
  - duplicate helpers
  - dead code from prior iterations
- Propose a compliant design before coding.
- Stop for approval before implementation unless I explicitly ask for a one-pass deliverable.
- Keep changes production-quality with validation, logging, graceful fallback behaviour, and restart safety.
- Keep architecture consistent with existing subsystem patterns.
- Add or update tests in line with Testing Standards.
- When work is complete, explicitly list:
  - helpers reused
  - refactor improvements made
  - debt deferred in the touched area
- Always produce a PR summary and a draft note for briefing users on the key changes  
```

---

## Goal

Deliver output that is:

- architecture-compliant
- production-quality
- restart-safe
- test-backed
- explicit about refactor decisions
- suitable for local deployment and manual review
