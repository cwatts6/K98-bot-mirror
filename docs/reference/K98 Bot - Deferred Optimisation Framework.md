# K98 Bot - Deferred Optimisation Framework

> Canonical repo copy: `docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 1. Purpose

This framework defines how deferred optimisations, tech debt, and refactor opportunities are
captured, grouped, prioritised, and executed.

It ensures:

- clear separation between delivery scope and improvements
- no loss of valuable observations during refactors
- efficient batching of related work into high-value optimisation packs
- consistent conversion into Codex-ready tasks

## 2. Core Principles

- Capture everything, execute selectively.
- Log observations when they are relevant and actionable.
- Do not expand scope mid-task without user approval.
- Deferred items must not be added to active PRs unless they are critical and approved.
- Optimisations should be delivered in meaningful batches, not scattered fragments.
- Raw observations become grouped, validated, Codex-ready tasks before implementation.

## 3. Required Deferred Item Format

All deferred items must follow this structure:

```markdown
### Deferred Optimisation
- Area: <module/file>
- Type: performance | architecture | cleanup | refactor | consistency
- Description: <what is wrong>
- Suggested Fix: <proposed improvement>
- Impact: low | medium | high
- Risk: low | medium | high
- Dependencies: <optional>
```

Do not replace this with unstructured placeholders or generic backlog text.

## 4. Staging Location

Repo-level captured items are staged in:

`docs/reference/deferred_optimisations.md`

This file is a temporary holding area and bulk review source. It may contain recently captured
items and resolved history until Phase 2 of the reference-doc cleanup separates active backlog
from archive/history.

## 5. Lifecycle

### 1. Capture

During audit, implementation, or review, capture out-of-scope issues that are:

- clear enough to act on later
- relevant to the touched area
- not safe or appropriate to fix in the current task

### 2. Review And Group

Group items when they share:

- the same module
- the same subsystem
- the same architecture concern
- the same service/repository boundary
- the same UI/view layer
- the same cache or persistence pattern

Do not group unrelated high-risk items just because they are nearby.

### 3. Score When Preparing A Batch

Use `K98 Bot Deferred Optimisation Scoring Model.md` when preparing a deferred optimisation
batch or task pack. Scoring is not required for a normal implementation PR unless the task is
specifically about prioritising deferred work.

### 4. Promote To GitHub Issues Or Task Packs

Promote only when an item is:

- clear and actionable, or
- part of a logical group, or
- ready to become a Codex task pack

## 6. Issue Types And Labels

Suggested issue types:

| Issue type | Purpose | Labels |
|------------|---------|--------|
| Micro issue | Small isolated observation | `deferred`, `micro` |
| Consolidation issue | Grouped batch candidate | `optimisation-batch`, `batch-candidate` |
| Execution task | Fully scoped Codex-ready task | `codex-task`, `ready` |

Useful labels:

- `tech-debt`
- `performance`
- `architecture`
- `cleanup`
- `refactor`
- `consistency`
- `needs-design`
- `blocked`

## 7. Review Cadence

At weekly or phase-end review:

1. Pull active deferred items.
2. Remove or archive resolved items.
3. Group related items.
4. Create consolidation issues when useful.
5. Identify high-value batches.
6. Promote ready batches into Codex task packs.

## 8. Execution Pattern

For a deferred optimisation batch:

1. Select a coherent batch.
2. Perform a full audit of the relevant subsystem.
3. Design the target state.
4. Build or update the Codex task pack.
5. Implement only after approval.
6. Close or update linked deferred items.

## 9. Anti-Patterns

Avoid:

- one issue per tiny fix when related items should be grouped
- mixing deferred work into active PRs without approval
- unstructured debt notes
- using deferred capture to avoid fixing an in-scope low-risk issue
- treating scoring as a substitute for engineering judgement

## 10. Success Criteria

Deferred items are successful when:

- important observations are not lost
- active delivery scope remains controlled
- optimisation work is batched meaningfully
- later agents can understand and execute the item without rediscovery
- completed items are removed from active backlog or moved to history
