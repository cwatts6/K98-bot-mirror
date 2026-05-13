
# Codex Task Pack — Stats Commands Full Optimisation & Standardisation

## Goal

Perform a full standards-alignment, optimisation, architecture review, and cleanup pass over `commands/stats_cmds.py` and all directly associated stats command files.

This is intended to be a complete polish batch, not a narrow bug fix.

The end state should leave the stats command subsystem fully aligned to current engineering standards, service/DAL boundaries, restart-safety expectations, testing standards, and command-layer architecture rules.

---

# 🧭 Context

This project uses two repositories:

| Repo                         | Purpose                                |
| ---------------------------- | -------------------------------------- |
| `cwatts6/K98-bot-mirror`     | Python Discord bot                     |
| `cwatts6/K98-bot-SQL-Server` | SQL Server schema and database objects |

---

# 📚 Required Reading Order (MANDATORY)

Before implementation, review in this order:
AGENTS.md
1. feature specification or task overview
2. `K98 Bot — Project Engineering Standards.md`
3. `K98 Bot — Coding Execution Guidelines.md`
4. `K98 Bot — Testing Standards.md`
5. `K98 Bot — Skills & Refactor Triggers.md`
6. `K98 Bot — Deferred Optimisation Framework.md`
7. `docs/deferred_optimisations.md`
8. `commands/stats_cmds.py`

If documents conflict, follow the priority defined in Coding Execution Guidelines.

---

# ⚠️ Critical Execution Rules

## Scope Control

* Do NOT expand scope beyond the requested task
* Do NOT silently ignore improvements
* ALL out-of-scope improvements MUST be captured using the Deferred Optimisation Framework

---

# 🔍 Mandatory Working Method

# Step 1 — Audit First (MANDATORY)

STOP after this step unless explicitly asked to proceed in one pass.

You MUST:

## Analyse the current implementation

Identify:

* direct SQL in commands/views
* business logic in interaction layers
* duplicate helpers
* dead code from prior iterations
* weak validation or logging
* restart/persistence risks
* inconsistent interaction response handling
* inconsistent defer/respond/followup flows
* direct registry dict traversal
* duplicated governor/account resolution logic
* duplicated cache access patterns
* embed/view ownership inconsistencies
* service/DAL boundary violations
* long command handlers that should be decomposed
* commands performing orchestration and business logic together

## Also map:

* modules involved
* services
* SQL objects
* views
* caches
* restart implications
* export pipelines
* registry dependencies
* embed builders
* exporters
* DAL/service ownership

## SQL Validation (MANDATORY)

Before implementation:

1. Search the SQL repo:
   `C:\K98-bot-SQL-Server`

2. Validate:

   * procedure dependencies
   * table schemas
   * expected output columns
   * dynamic SQL targets
   * ProcConfig usage

3. If live SQL access fails:

   * use the SQL repo as the authoritative source
   * do NOT fall back to guessed schema

## Required Step 1 Output

Provide:

1. Files inspected
2. Related GitHub issues found
3. Deferred optimisations found
4. Architecture violations identified
5. Restart/state risks
6. Proposed implementation plan
7. Risk assessment

STOP after Step 1.

Do NOT code until confirmed.

---

# Step 2 — Deferred Optimisation Capture (MANDATORY)

For ALL out-of-scope findings:

```md
### Deferred Optimisation
- Area: <module/file>
- Type: performance | architecture | cleanup | refactor | consistency
- Description: <issue>
- Suggested Fix: <proposal>
- Impact: low | medium | high
- Risk: low | medium | high
- Dependencies: <optional>
```

## Rules

* Do NOT leave unstructured notes
* Do NOT say “could be improved later”
* Group related items where possible
* Do NOT implement unless approved

---

# Step 3 — Architecture Validation

STOP and confirm before coding.

Validate:

* correct layer placement
* services own business logic
* commands/views remain thin
* SQL is not in command/view layers
* helper reuse has been checked
* restart safety implications reviewed
* registry service boundaries respected
* cache access patterns centralised where practical

---

# Step 4 — Implementation Plan

STOP and confirm before coding.

Provide:

* files to create
* files to modify
* SQL changes
* services/repositories required
* helpers to reuse
* logging plan
* restart safety approach
* testing plan
* refactor items to fix now vs defer

---

# Step 5 — Implementation

Must:

* follow engineering standards
* keep commands/views thin
* move business logic into services
* avoid direct SQL in commands/views
* reuse helpers
* maintain restart safety
* add logging
* preserve existing Discord UX unless explicitly improving consistency
* preserve existing command outputs unless fixing bugs or inconsistencies

---

# Step 6 — Testing

Must include:

* happy path
* negative path
* regression
* restart/persistence where relevant

## Required Stats Coverage

Add or update focused tests for:

* stats export service/DAL boundary
* no registered accounts
* empty export data
* export format selection
* registry/account resolution
* command/service handoff
* KVK history account-map fallback
* rankings cache empty path
* interaction defer/respond safety where testable
* embed/view orchestration behaviour where practical

## DB Test Rules

Where live DB is required:

* mark as integration
* gate behind `RUN_DB_TESTS=1`

If not implemented:

* explicitly justify
* capture as deferred optimisation if appropriate

---

# Step 7 — Codex Review Pass (MANDATORY)

After implementation and testing:

Perform a read-only audit.

## MUST validate

* architecture compliance
* refactor triggers
* test coverage correctness
* restart/state safety
* logging quality
* service/DAL boundaries
* command thinness
* helper reuse

## MUST NOT

* expand scope
* add features
* perform large refactors

## Required Output

```md
## Codex Review Summary

### What is correct

### Issues found (fix now)

### Deferred Optimisations

### Test Gaps

### Restart / State Risks

### Overall Assessment
```

---

# 🎯 Required Scope

Review and resolve all stats-related deferred optimisations and GitHub issues, including:

* #27 dict-style registry access
* #28 legacy registry views (where touched by stats flows)
* #29 stats-service registry alignment
* #31 governor registry architecture refactor (stats-related parts only)
* #32 service layer consolidation (stats-related parts only)
* #42 remaining KVK admin SQL/service extraction
* #46 extract `/my_stats_export` SQL into service/DAL

Also review:

* `docs/deferred_optimisations.md`

Resolve or update any stats-related entries.

---

# 🎯 Target Outcomes

## 1. Thin Command Layer

`commands/stats_cmds.py` should only handle:

* slash command registration
* permission/decorator flow
* defer/respond/followup behaviour
* calling services
* presenting final embeds/views/files

Move business logic into services/helpers.

---

## 2. Remove Direct SQL From Commands

Extract `/my_stats_export` direct SQL into a dedicated service/DAL boundary.

Suggested structure:

* `stats/dal/stats_export_dal.py`
* `services/stats_export_service.py`

The command should delegate entirely to service orchestration.

---

## 3. Registry Alignment

Remove direct `load_registry()` and dict traversal from stats command flows where practical.

Prefer canonical service boundaries:

* `registry_service.get_user_accounts()`
* existing governor/account services
* shared account mapping helpers

Likely affected:

* `/mykvkstats`
* `/my_stats`
* `/my_stats_export`
* `/player_stats`
* `/mykvkhistory`

---

## 4. Consolidate Duplicate Account Resolution Logic

Avoid each command rebuilding:

* Governor ID lists
* Governor name maps
* Main/default account selection
* ordered account maps
* fallback account resolution

Introduce reusable helpers/services where sensible.

---

## 5. Interaction Safety Consistency

Audit every command for:

* `safe_defer` vs raw `ctx.defer`
* `ctx.respond` after defer problems
* ephemeral/public consistency
* fallback send/edit behaviour
* timeout/message-reference handling

Do not regress UX.

---

## 6. Preserve Discord UX

Do NOT regress:

* `/mykvkstats`
* `/my_stats`
* `/my_stats_export`
* `/player_stats`
* `/mykvkhistory`
* `/kvk_rankings`
* `/kvk_export_all`
* `/kvk_recompute`
* `/kvk_list_scans`
* `/test_kvk_embed`
* `/kvk_window_preview`
* `/honor_rankings`
* `/honor_purge_last`

Preserve existing output copy unless improving consistency or fixing defects.

---

# 📦 Required Delivery Format

You MUST include:

* summary
* file manifest
* new files
* modified files
* SQL changes
* helpers reused
* refactor findings
* test plan
* deployment steps
* Deferred Optimisations (MANDATORY structured section)

---

# 🚨 Failure Conditions

The task is NOT complete if:

* ❌ Deferred optimisations are missing
* ❌ Notes are unstructured
* ❌ Technical debt is silently ignored
* ❌ Scope expanded without approval
* ❌ Direct SQL remains in command/view layers unnecessarily
* ❌ Registry dict traversal remains where service boundaries exist
* ❌ Restart/state risks are not reviewed

---

# 🎯 Goal

Deliver output that is:

* architecture-compliant
* production-quality
* restart-safe
* test-backed
* explicit about refactor decisions
* structured for future optimisation batching
* fully aligned to current K98 engineering standards
