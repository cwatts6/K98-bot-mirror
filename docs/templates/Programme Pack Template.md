# <Programme Name> — Programme Pack

> Canonical template for K98 bot programme-level work.
> Use this when a piece of work is larger than a single task pack and needs a product vision,
> phased delivery plan, design principles, validation strategy, and future-scope control.
>
> Replace all angle-bracket placeholders before use.
> Programme packs must define per-phase Codex Security routing governance; they must not imply a
> generic programme-wide scan or use unqualified `Codex Security review` wording.

## 1. Programme Header

- Programme name: `<short descriptive programme name>`
- Date: `<YYYY-MM-DD>`
- Owner/context: `<requester, source, epic, incident, product area, or strategic goal>`
- Programme type: `<Product UX | Discord command architecture | SQL/data | operations | visual redesign | tooling | mixed>`
- One-pass approved: `<yes | no>`
- Headline: `<optional user-facing or operator-facing headline>`

## 2. Programme Vision

<Describe the intended end state in 2-5 paragraphs. State the user-visible or operational outcome first.>

The vision should answer:

- What will be meaningfully better when the programme is complete?
- Who benefits?
- What product or engineering standard should this set?
- How does this prepare for named later phases or approved follow-up tasks?

## 3. Why This Programme Exists

<Summarise the current problem, pain points, evidence, prior work, and why a programme is needed instead of a single task.>

Consider including:

- current command or workflow fragmentation
- usability or operational issues
- known deferred optimisation items
- comparison with recently improved areas
- risks of doing nothing
- why now

## 4. Product / Engineering Goal

<Define the practical goal in player, operator, or developer terms.>

This section should include 3-8 questions the programme should answer for its target users, for example:

- `<question 1>`
- `<question 2>`
- `<question 3>`

## 5. Target Model

Use the relevant subsection names for the programme.

### Target command model

```text
/<group> <subcommand>
/<group> <subcommand>
```

### Target workflow model

```text
<entry point> -> <decision/action> -> <result>
```

### Target data/model contract

```text
<source> -> <service/DAL> -> <view/output>
```

### Legacy or current paths to evaluate

```text
/<legacy_command>
<legacy module or workflow>
```

## 6. Navigation / Workflow Model

<Explain how users or operators should move through the redesigned flow.>

For Discord UI programmes, explicitly cover:

- command entry point
- public vs private/ephemeral behaviour
- buttons/select menus/modals
- back/return behaviour
- timeout behaviour
- fallback behaviour
- how complexity is hidden from the first screen

## 7. Target User Journeys

### Journey A — `<journey name>`

Should answer:

- `<question>`
- `<question>`

Target behaviour:

- `<expected behaviour>`
- `<expected behaviour>`

Success means:

- `<definition of success>`

### Journey B — `<journey name>`

Repeat as needed.

## 8. Visual / Output Direction

Use this section when the programme affects player-facing or operator-facing output.

Target direction:

- `<visual or output principle>`
- `<visual or output principle>`
- `<visual or output principle>`

Recommended output shape, if relevant:

```text
Size:
Format:
Privacy:
Fallback:
```

Reusable visual/output primitives to consider:

- `<primitive>`
- `<primitive>`
- `<primitive>`

## 9. Design Principles

1. **<Principle>** — <short explanation>.
2. **<Principle>** — <short explanation>.
3. **<Principle>** — <short explanation>.
4. **<Principle>** — <short explanation>.
5. **<Principle>** — <short explanation>.

Include programme-specific constraints such as:

- no sudden removals
- no misleading metrics
- commands/views stay thin
- SQL source-of-truth validation
- Discord-safe UX
- privacy by default
- website-ready data shapes

## 10. Programme Phases

### Phase 1 — Audit and Design Only

Status: proposed.

Security decision: `<documented skip | findings triage | other explicitly approved outcome>`.

Security target / evidence: `<files inspected and skip reason, captured findings path, or approval>`.

Deliver:

- current-state audit
- target model
- user journey map
- architecture review
- visual/output proposal
- migration/deprecation plan
- implementation phase plan

No runtime code changes unless explicitly approved.

### Phase 2 — `<phase name>`

Status: proposed.

Security decision: `<documented skip | Changes review | standard codebase audit | deep codebase audit | findings triage | finding remediation>`.

Security target / evidence: `<repository and base..head, scope, captured findings path, finding ID, or precise skip reason>`.

Deliver:

- `<deliverable>`
- `<deliverable>`

### Phase 3 — `<phase name>`

Status: proposed.

Security decision: `<documented skip | Changes review | standard codebase audit | deep codebase audit | findings triage | finding remediation>`.

Security target / evidence: `<repository and base..head, scope, captured findings path, finding ID, or precise skip reason>`.

Deliver:

- `<deliverable>`
- `<deliverable>`

Add more phases only where they help control scope. Every implementation phase must have a task
pack that records its own repository/Git target and `k98-security-review-routing` decision. An
audit/design-only phase with no runtime effect normally records a precise documented skip.

## 11. In Scope for the Programme

- `<scope item>`
- `<scope item>`
- `<scope item>`

## 12. Out of Scope for the First Build

- `<explicit exclusion>`
- `<explicit exclusion>`
- `<explicit exclusion>`

## 13. Likely Source Commands and Areas

### Commands to audit

```text
/<command>
/<command>
```

### Modules to audit

```text
commands/<module>.py
ui/views/<view_module>.py
services/<service>.py
```

### SQL repo areas to validate if needed

```text
C:\K98-bot-SQL-Server
```

List likely SQL-backed contracts:

- `<table/view/procedure family>`
- `<table/view/procedure family>`

## 14. Cross-Programme Constraints

- `<constraint>`
- `<constraint>`
- `<constraint>`

Always consider:

- command registration governance
- legacy command migration
- response visibility and permissions
- SQL/data source validation
- no direct SQL in command/view layers
- tests and documentation updates
- phase-specific security review routing and evidence
- deferred optimisation capture, with security findings tracked separately

## 15. Programme-Level Security and Validation Strategy

A programme pack does not authorise a repository-wide or deep scan by itself. For every phase and
affected repository, use `k98-security-review-routing` to choose exactly one outcome and record the
target and evidence.

| Phase | Repository | Security decision | Target | Expected setup / evidence |
|---|---|---|---|---|
| `<phase>` | `<bot | SQL | other>` | `<documented skip | Changes review | standard codebase audit | deep codebase audit | findings triage | finding remediation>` | `<files; base..head; scoped folder; captured findings path; or finding ID>` | `<precise skip evidence | Changes + Deep Off | Codebase + Deep Off | Codebase + Deep On | triage result | remediation and tests>` |

Security routing rules:

- Audit/design-only phases normally use a precise documented skip or findings triage. They do not
  launch a discovery scan merely to prepare a design.
- Routine implementation phases use `$codex-security:security-diff-scan` when security-sensitive
  behaviour changes. Confirm the intended base/head and `Deep: Off`.
- Standard and deep codebase audits are separate, explicitly approved audit phases with a deliberate
  repository or folder target; they are not routine completion, PR, promotion, or deployment gates.
- Existing findings are triaged from captured artifacts without launching another discovery scan.
- Accepted findings are fixed individually, or as one tightly related root-cause family, and the
  resulting change receives the normal diff-focused review.
- Bot and SQL repositories require separate targets and normally separate review evidence.

Each implementation phase should also consider:

- command registration validation
- focused command tests
- permission tests
- response visibility tests
- view/modal/button/select tests
- service/DAL contract tests
- SQL validation where SQL-backed contracts are touched or depended on
- architecture boundary validation
- deferred item validation
- visual artifact review where relevant
- manual Discord smoke testing
- completion of the recorded phase security outcome and retention of its evidence

Baseline commands to consider:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
.\.venv\Scripts\python.exe -m pytest -q tests
```

## 16. Programme Acceptance Criteria

The programme is complete when:

- [ ] `<outcome>`
- [ ] `<outcome>`
- [ ] `<outcome>`
- [ ] documentation and command references are updated
- [ ] command registration validation remains green
- [ ] no new direct SQL exists in command/view layers
- [ ] every phase and affected repository has a precise security decision, target, and evidence
- [ ] routine security reviews use Changes with the intended base/head and `Deep: Off`
- [ ] no standard or deep codebase audit was started without explicit operator approval
- [ ] known findings are triaged from captured artifacts rather than rediscovered by routine scans
- [ ] deferred optimisation findings are captured structurally; security findings are tracked separately

## 17. Deferred / Future Opportunities

Do not include these in early phases unless separately approved:

- `<future idea>`
- `<future idea>`
- `<future idea>`

## 18. Suggested Next Action

```text
<next task pack, approval checkpoint, or manual action>
```

## 19. Programme Change Log

| Date | Change | Notes |
|---|---|---|
| `<YYYY-MM-DD>` | `<change>` | `<notes>` |
