# K98 Bot - Skills & Refactor Triggers

> Canonical repo copy: `docs/reference/K98 Bot - Skills & Refactor Triggers.md`.

## 1. Core Skills Expected

A strong implementation in this project usually requires several of these skills at once.

### Architecture Judgement

Ability to:

- place code in the correct layer
- keep commands and views thin
- move business logic into services
- move data access into repositories or DAL modules
- avoid expanding legacy monoliths

### Refactor Awareness

Ability to notice when the touched area still contains:

- direct SQL in commands/views
- duplicated helpers
- dead code from earlier feature iterations
- mixed responsibilities
- weak restart safety
- inconsistent logging and validation

### SQL / Persistence Discipline

Ability to:

- treat the SQL repo as the source of truth for schema objects
- separate schema changes from Python changes
- avoid hidden schema assumptions in Python
- recognize when JSON-only state is insufficient

### Testing Judgement

Ability to decide what needs:

- regression tests
- negative-path coverage
- permission testing
- restart/persistence testing
- cache safety testing

### Operational Awareness

Ability to consider:

- startup / shutdown
- rehydration
- duplicate-post prevention
- structured logging
- local validation
- production promotion and migration order

### AI-Assisted Review Judgement

Ability to:

- use `k98-security-review-routing` when a task touches a security-sensitive surface
- distinguish a routine diff review from a standard or deep codebase audit
- use `$codex-security:security-diff-scan` for required PR/commit/branch/working-tree reviews
- document clear skip reasons for documentation-only, comment-only, generated-only, or genuinely mechanical changes
- never treat tests, deferred optimisation, or promotion checks as substitutes for security triage

## 2. Refactor Triggers

These triggers should prompt cleanup in the touched area or a structured deferred item.

### Trigger A - Direct SQL Found In Commands Or Views

Expected response:

- move it into repository/DAL or service-owned data-access code
- if not fixed now, explicitly state why it is deferred and capture it using the Deferred
  Optimisation Framework

### Trigger B - Business Logic Found In Commands Or Views

Expected response:

- extract to a service
- leave commands/views responsible only for interaction flow and rendering

### Trigger C - Duplicate Helper Or Near-Duplicate Found

Expected response:

- reuse the existing helper when viable
- or consolidate and replace duplication
- do not add another helper without justification

### Trigger D - Dead Code From Prior Iterations

Expected response:

- remove it if clearly unused and safe
- or capture it using the Deferred Optimisation Framework if not addressed now

### Trigger E - Critical State Stored Only In Memory Or Fragile JSON

Expected response:

- assess whether SQL-backed persistence is required
- improve restart safety where the feature depends on state continuity
- defer structurally if the fix is larger than the approved task

### Trigger F - Logging Is Insufficient To Explain Failures

Expected response:

- add meaningful logs at decision and outcome points
- avoid generic exception-only logging
- keep sensitive values out of logs

### Trigger G - Tests Exist But No Longer Match The Architecture

Expected response:

- update tests as part of the refactor
- do not leave tests describing old layer boundaries

### Trigger H - Security-Sensitive Surface Touched

Security-sensitive surfaces include permissions, Discord interactions, SQL/data access, file
handling, secrets/config, deployment, network calls, user-controlled input, and restart-sensitive
persistence.

Expected response:

- make and record the decision through `k98-security-review-routing`
- for routine Git-backed changes, use `$codex-security:security-diff-scan` or a precise documented skip
- do not invoke standard or deep codebase scans without an explicit request for that broader audit
- fix validated issues within the approved scope
- keep untriaged or confirmed vulnerabilities in the security findings workflow; capture only separated non-vulnerability hardening through the Deferred Optimisation Framework

## 3. Review Questions Before Coding

1. Which layer should own this behaviour?
2. Is any direct SQL present in the command or view path?
3. Is there a service already suitable for this work?
4. Is there an existing helper to reuse?
5. Is there dead code in the touched area from previous versions?
6. What state must survive restart?
7. What test types are required?
8. Which conditional reference docs apply?
9. Does the task trigger Codex Security review?
10. What technical debt is obvious enough that leaving it untouched would likely repeat the
   problem later?

## 4. Review Questions Before Marking Complete

1. Did this change improve the touched area, or only patch it?
2. Did I leave direct SQL in a place it should not live?
3. Did I preserve duplicate logic that should have been consolidated?
4. Did I update or add tests for the changed behaviour?
5. Did I explicitly list any debt I chose not to fix?
6. Would another engineer understand the flow from logs if it failed in production?
7. Would the feature still behave correctly after a restart?
8. Was Codex Security run or explicitly skipped with reasons?

## 5. Practical Use In Task Packs

When writing or using a task pack, include a short section like:

- Skills needed: architecture judgement, service extraction, SQL review, test updates
- Refactor triggers to check: direct SQL in commands, duplicate helpers, dead flow from old signup versions
- Expected cleanup: extract SQL from command, remove dead legacy branch, update nearby tests

This makes task packs more consistent and raises the chance that obvious improvements are addressed
during the work rather than deferred by default.

## 6. Compact Checklist

Before implementation:

- [ ] correct layer ownership identified
- [ ] helper reuse checked
- [ ] SQL location reviewed
- [ ] persistence implications reviewed
- [ ] test implications reviewed
- [ ] refactor triggers reviewed
- [ ] conditional reference docs selected

Before completion:

- [ ] direct SQL in touched command/view path addressed or explicitly deferred
- [ ] duplicate helpers addressed or explicitly deferred
- [ ] dead code addressed or explicitly deferred
- [ ] tests added, updated, or explicitly ruled out
- [ ] logging adequate
- [ ] restart safety preserved
- [ ] Security decision recorded; required Changes review completed or precise skip justified
- [ ] follow-on debt listed if still present

## 7. Deferred Optimisation Handling

When a refactor trigger cannot be addressed within the current task:

- Capture the item using `K98 Bot - Deferred Optimisation Framework.md`.
- Do not silently defer.
- Ensure the item is suitable for later batching.
- Include it in task output under deferred debt.
