🧠 K98 Code Prompt v3 — Execution Contract

This prompt defines the mandatory execution behaviour for all coding tasks.
It enforces architecture, scope control, and deferred optimisation handling.

📚 Required Reading

Read in this order before making changes:

Feature specification / task overview
K98 Bot — Project Engineering Standards.md
K98 Bot — Coding Execution Guidelines.md
K98 Bot — Testing Standards.md
K98 Bot — Skills & Refactor Triggers.md
K98 Bot — Deferred Optimisation Framework.md
⚠️ Critical Rules (NON-NEGOTIABLE)
Scope Control
Do NOT expand scope beyond the requested task
Do NOT silently ignore improvements
ALL out-of-scope improvements MUST be captured using the Deferred Optimisation Framework
Refactor Decision Rule

For every issue identified:

You MUST explicitly choose:

✅ FIX NOW (in scope, low risk)
⏳ DEFER (capture using Deferred Optimisation Framework)

Silent decisions are NOT allowed.

🔍 Mandatory Execution Workflow
Step 1 — Audit (STOP AFTER)

You MUST:

Analyse the current implementation
Identify:
direct SQL in commands/views
business logic in interaction layers
duplicate helpers
dead code from prior iterations
weak validation or logging
restart/persistence risks
Map:
modules
services
SQL objects
views
caches
restart implications
Output Required:
Audit summary
Initial list of issues found
Step 2 — Deferred Optimisation Capture (MANDATORY)

For ALL out-of-scope issues:

### Deferred Optimisation
- Area: <module/file>
- Type: performance | architecture | cleanup | refactor | consistency
- Description: <issue>
- Suggested Fix: <proposal>
- Impact: low | medium | high
- Risk: low | medium | high
- Dependencies: <optional>
Rules:
No unstructured notes
No vague “improve later” statements
Group related items where possible
Items must be suitable for future batching
Step 3 — Architecture Validation (STOP AFTER)

Confirm:

correct layer placement
services own business logic
commands and views remain thin
SQL is not in command/view layers
helper reuse has been checked
Output Required:
Validation summary
Any required architecture corrections
Step 4 — Implementation Plan (STOP AFTER)

Provide:

files to create
files to modify
SQL changes
services/repositories required
helpers to reuse
logging plan
restart safety approach
testing plan
refactor decisions (FIX vs DEFER per issue)
Step 5 — Implementation

Must:

follow engineering standards
keep commands/views thin
move business logic into services
avoid direct SQL in commands/views
reuse helpers
maintain restart safety
add logging
Step 6 — Testing

Must include:

happy path
negative path
regression
restart/persistence where relevant

If not implemented:

explicitly justify
capture as deferred optimisation
📦 Required Output Format (STRICT)

All sections MUST be present.

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. Helpers Reused
7. Refactor Findings

Include:

issues found
FIXED vs DEFERRED decisions
8. Test Plan
9. Deployment Steps
10. Deferred Optimisations

Structured list ONLY (no prose)

🚨 Failure Conditions

The task is NOT complete if:

❌ Deferred optimisations are missing
❌ Issues are identified but not classified (FIX vs DEFER)
❌ Output format is incomplete
❌ Scope expanded without approval
❌ Architecture validation skipped
❌ Unstructured notes included
🎯 Goal

Deliver output that is:

architecture-compliant
production-quality
restart-safe
test-backed
explicitly structured for optimisation batching
🔥 Expected Behaviour Change

Before:

“This could be improved later”

After:

Captured, structured, grouped, and ready for batch execution

✅ Success Criteria
No technical observation is lost
No silent technical debt
No scope creep
All work feeds the optimisation pipeline
Output is consistent across all tasks
