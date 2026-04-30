🧠 K98 Bot — Deferred Optimisation Framework
🎯 Purpose

This framework defines how deferred optimisations, tech debt, and refactor opportunities are captured, grouped, prioritised, and executed.

It ensures:

Clean separation between delivery scope and improvements
No loss of valuable observations during refactors
Efficient batching of related work into high-value optimisation packs
Consistent conversion into Codex-ready tasks
🧩 Core Principles
Capture everything, execute selectively
Log all observations
Execute only grouped, validated work
Never expand scope mid-task
Deferred items must NOT be added to active PRs unless critical
Optimisations are delivered in batches, not fragments
Avoid “death by 1000 micro-PRs”
Promote before execution
Raw observations → grouped → validated → Codex task
🔄 Lifecycle
1. Capture (During Refactor)

All deferred items MUST follow this format:

### Deferred Optimisation
- Area: <module/file>
- Type: performance | architecture | cleanup | refactor | consistency
- Description: <what is wrong>
- Suggested Fix: <proposed improvement>
- Impact: low | medium | high
- Risk: low | medium | high
- Dependencies: <optional>
2. Log Storage (Staging Layer)

All captured items go into:

/docs/deferred_optimisations.md

This acts as:

Temporary holding area
Bulk review source
Pre-GitHub staging
3. Promotion to GitHub Issues

Only promote when:

Item is clear and actionable
OR part of a logical group
Issue Types
🔹 Micro Issue (Raw Capture)

Small, isolated observation.

Labels:

deferred
micro
🔹 Consolidation Issue (Batch Candidate)

Grouped set of related improvements.

Labels:

optimisation-batch
batch-candidate


relevant type labels
🔹 Execution Task (Codex Ready)

Fully defined, ready for implementation.

Labels:

codex-task
ready
🏷️ Label System
Core Labels
deferred → captured but not actioned
micro → small standalone item
tech-debt
performance
architecture
cleanup
refactor
consistency
Pipeline Labels
batch-candidate → suitable for grouping
needs-design
ready
in-progress
blocked
🧠 Batching Rules
Group items when:
Same module (e.g. governor_registry.py)
Same pattern (e.g. caching, repeated I/O)
Same architectural concern
Do NOT group when:
Requires major redesign
High uncertainty
Cross-cutting unrelated systems
🗂️ Example (From Current Task)
Raw Deferred Items
Item	Reason
telemetry_cmds._resolve_kvk_no() SQL in command module	Separate domain
Remove legacy registry views	Requires command updates
Remove dict-style registry access	Broad scope
mge_signup_service → registry_service	Targeted improvement
stats_service → get_user_accounts	Pending stats refactor
kvk_ui.py rationalisation	Broader UI scope
Resulting Batches
🧩 Batch 1 — Registry Architecture Cleanup
Remove legacy dict-style access
Standardise registry service usage
Replace legacy views
🧩 Batch 2 — Service Consolidation
mge_signup_service alignment
stats_service alignment
🧩 Batch 3 — Command Layer SQL Separation
Remove SQL from telemetry_cmds
🧩 Batch 4 — UI Rationalisation
kvk_ui.py vs AccountPickerView
📊 GitHub Project Board

Use GitHub Projects with the following columns:

🧠 Captured
Raw micro issues
🔍 Needs Review
Items awaiting grouping
🧩 Grouped
Consolidation issues
🧪 Ready for Codex
Fully defined execution tasks
🚀 In Progress
Active implementation
✅ Done
Completed work
🔁 Review Process
Weekly / Phase-End Review
Pull all deferred issues
Group into themes
Create consolidation issues
Identify high-value batches
Promote to Codex tasks
⚙️ Execution Pattern
Select batch
Perform full audit (not spot fix)
Design target state
Build Codex task pack
Implement
Close all linked issues
🚫 Anti-Patterns
❌ One issue per tiny fix (no grouping)
❌ Mixing deferred work into active PRs
❌ No review cadence
❌ Unstructured capture
✅ Success Criteria
Deferred items are never lost
Optimisations are delivered in meaningful batches
Codebase improves systematically, not randomly
Refactors remain focused and controlled
🚀 Future Enhancements
Auto-generate deferred items during PR reviews
Add /log_deferred admin command in bot
Link deferred items to telemetry for prioritisation
Introduce scoring model (Impact × Frequency × Risk)
