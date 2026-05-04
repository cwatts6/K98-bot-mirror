K98 Bot — Standard Development Initiation Statement (v2)

Purpose: Paste this at the start of AI-assisted coding sessions.
This document defines the working contract for execution, not architecture rules.

🧭 Context

This project uses two repositories:

Repo	Purpose
cwatts6/K98-bot-mirror	Python Discord bot
cwatts6/K98-bot-SQL-Server	SQL Server schema and database objects
📚 Required Reading Order

Before implementation, review in this order:

feature specification or task overview
K98 Bot — Project Engineering Standards.md
K98 Bot — Coding Execution Guidelines.md
K98 Bot — Testing Standards.md
K98 Bot — Skills & Refactor Triggers.md
K98 Bot — Deferred Optimisation Framework.md

If documents conflict, follow the priority defined in Coding Execution Guidelines.

⚠️ Critical Execution Rules
Scope Control
Do NOT expand scope beyond the requested task
Do NOT silently ignore improvements
ALL out-of-scope improvements MUST be captured using the Deferred Optimisation Framework
🔍 Mandatory Working Method
Step 1 — Audit First (MANDATORY)

STOP after this step unless explicitly asked to proceed in one pass

You MUST:

Analyse the current implementation
Identify:
direct SQL in commands/views
business logic in interaction layers
duplicate helpers
dead code from prior iterations
weak validation or logging
restart/persistence risks

Also map:

modules involved
services
SQL objects
views
caches
restart implications
Step 2 — Deferred Optimisation Capture (MANDATORY)

For ALL out-of-scope findings:

### Deferred Optimisation
- Area: <module/file>
- Type: performance | architecture | cleanup | refactor | consistency
- Description: <issue>
- Suggested Fix: <proposal>
- Impact: low | medium | high
- Risk: low | medium | high
- Dependencies: <optional>
Rules:
Do NOT leave unstructured notes
Do NOT say “could be improved later”
Group related items where possible
Do NOT implement unless approved
Step 3 — Architecture Validation

STOP and confirm before coding

Validate:

correct layer placement
services own business logic
commands/views remain thin
SQL is not in command/view layers
helper reuse has been checked
Step 4 — Implementation Plan

STOP and confirm before coding

Provide:

files to create
files to modify
SQL changes
services/repositories required
helpers to reuse
logging plan
restart safety approach
testing plan
refactor items to fix now vs defer
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
capture as deferred optimisation if appropriate
📦 Required Delivery Format

You MUST include:

summary
file manifest
new files
modified files
SQL changes
helpers reused
refactor findings
test plan
deployment steps
Deferred Optimisations (MANDATORY structured section)
🚨 Failure Conditions

The task is NOT complete if:

❌ Deferred optimisations are missing
❌ Notes are unstructured
❌ Technical debt is silently ignored
❌ Scope expanded without approval
🎯 Goal

Deliver output that is:

architecture-compliant
production-quality
restart-safe
test-backed
explicit about refactor decisions
structured for future optimisation batching
