# K98 Bot — Skills & Refactor Triggers

> **Purpose:** Give AI coding agents and reviewers a compact guide to the skills expected during task execution, plus the refactor triggers that should cause broader cleanup in the touched area.

---

## 1. Core Skills Expected

A strong implementation in this project usually requires several of these skills at once:

### 1.1 Architecture judgement

Ability to:

- place code in the correct layer
- keep commands and views thin
- move business logic into services
- move data access into repositories
- avoid expanding legacy monoliths

### 1.2 Refactor awareness

Ability to notice when the touched area still contains:

- direct SQL in commands/views
- duplicated helpers
- dead code from earlier feature iterations
- mixed responsibilities
- weak restart safety
- inconsistent logging and validation

### 1.3 SQL / persistence discipline

Ability to:

- respect SQL as the source of truth
- separate schema changes from Python changes
- avoid hidden schema assumptions in Python
- recognize when JSON-only state is insufficient

### 1.4 Testing judgement

Ability to decide what needs:

- regression tests
- negative-path coverage
- permission testing
- restart/persistence testing
- cache safety testing

### 1.5 Operational awareness

Ability to consider:

- startup / shutdown
- rehydration
- duplicate-post prevention
- structured logging
- local-first deployment and migration order

---

## 2. Refactor Triggers

These are the main triggers that should prompt cleanup in the touched area.

### Trigger A — Direct SQL found in commands or views

Expected response:

- move it into repository/DAL or service-owned data-access code
- if not fixed now, explicitly state why it is deferred and capture it using the Deferred Optimisation Framework

### Trigger B — Business logic found in commands or views

Expected response:

- extract to a service
- leave commands/views responsible only for interaction flow and rendering

### Trigger C — Duplicate helper or near-duplicate found

Expected response:

- reuse the existing helper when viable
- or consolidate and replace duplication
- do not add another helper without justification

### Trigger D — Dead code from prior iterations

Expected response:

- remove it if clearly unused and safe
- or capture it using the Deferred Optimisation Framework if not addressed now

### Trigger E — Critical state stored only in memory or fragile JSON

Expected response:

- assess whether SQL-backed persistence is required
- improve restart safety where the feature depends on state continuity

### Trigger F — Logging is insufficient to explain failures

Expected response:

- add meaningful logs at the decision and outcome points
- not just generic exception logging

### Trigger G — Tests exist but no longer match the architecture

Expected response:

- update the tests as part of the refactor
- do not leave tests describing the old layer boundaries

---

## 3. Review Questions to Ask Before Coding

1. Which layer should own this behaviour?
2. Is any direct SQL present in the command or view path?
3. Is there a service already suitable for this work?
4. Is there an existing helper to reuse?
5. Is there dead code in the touched area from previous versions?
6. What state must survive restart?
7. What test types are required?
8. What technical debt is obvious enough that leaving it untouched would likely repeat the problem later?

---

## 4. Review Questions to Ask Before Marking Complete

1. Did this change improve the touched area, or only patch it?
2. Did I leave direct SQL in a place it should not live?
3. Did I preserve duplicate logic that should have been consolidated?
4. Did I update or add tests for the changed behaviour?
5. Did I explicitly list any debt I chose not to fix?
6. Would another engineer understand the flow from logs if it failed in production?
7. Would the feature still behave correctly after a restart?

---

## 5. Practical Use in Task Packs

When writing or using a task pack, include a short section like:

- **Skills needed:** architecture judgement, service extraction, SQL review, test updates
- **Refactor triggers to check:** direct SQL in commands, duplicate helpers, dead flow from old signup versions
- **Expected cleanup:** extract SQL from command, remove dead legacy branch, update nearby tests

This makes the task pack more consistent and raises the chance that obvious improvements are addressed during the work rather than deferred by default.

---

## 6. Compact Checklist

Before implementation:

- [ ] correct layer ownership identified
- [ ] helper reuse checked
- [ ] SQL location reviewed
- [ ] persistence implications reviewed
- [ ] test implications reviewed
- [ ] refactor triggers reviewed

Before completion:

- [ ] direct SQL in touched command/view path addressed or explicitly deferred
- [ ] duplicate helpers addressed or explicitly deferred
- [ ] dead code addressed or explicitly deferred
- [ ] tests added or updated
- [ ] logging adequate
- [ ] restart safety preserved
- [ ] follow-on debt listed if still present

## 7. Deferred Optimisation Handling (NEW)

When a refactor trigger cannot be addressed within the current task:

Capture the item using the Deferred Optimisation Framework
Do not silently defer
Ensure the item is suitable for later batching
Include it in task output under deferred debt
