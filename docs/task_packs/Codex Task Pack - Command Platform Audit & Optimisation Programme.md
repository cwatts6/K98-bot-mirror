Codex Task Pack - Command Platform Audit & Optimisation Programme
1. Task Header
Task name: Command Platform Audit & Optimisation Programme
Date: 2026-05-28
Owner/context: Command architecture, UX, registration, documentation and operational command audit
Task type: deferred optimisation batch
One-pass approved: no
2. Required Reading

Before implementation, read:

AGENTS.md
README-DEV.md
docs/reference/README.md

Then follow the required reading order defined by:

docs/reference/README.md

Also review:

docs/reference/deferred_optimisations.md
docs/reference/command_surface_audit.md
scripts/validate_command_registration.py
All command modules under commands/
Any command registration helpers
Usage tracking and command analytics modules
Permission decorators
Command cache and sync lifecycle modules

Reference sources include the original command surface audit and the active deferred optimisation backlog.

3. Objective

Perform a complete end-to-end audit of the K98 command platform.

This is not limited to command-count reduction.

The goal is to ensure the command platform is:

Scalable
Maintainable
Discoverable
Consistent
Well documented
Operationally safe
Architecturally aligned
Future-proofed against Discord command registration limits

All command-related issues, optimisations, inconsistencies, architecture concerns, documentation gaps, UX issues and technical debt should be identified, classified and prioritised.

4. Background

Batch 1 command grouping successfully reduced the command count from the Discord limit boundary and introduced grouped /ops and /mge commands.

Phase 1 of this programme, Permission Decorator Standardisation, was completed in PR 131
(`codex/command-platform-phase-1-permission-decorators`), smoke tested successfully, merged, and
pushed to production. Phase 1 standardised active command permission gates onto decorators,
introduced the reusable decorator support needed by the current command estate, added focused
permission-decorator tests, and preserved all command paths and the registration count.

Phase 2 of this programme, Validator And Inventory Tooling Enhancement, was completed in PR 132
(`codex/command-platform-phase-2-validator-inventory`), smoke tested successfully, merged, and
pushed to production. Phase 2 retired unused disabled secondary command declarations, updated
duplicate-risk terminology, detected helper-attached grouped subcommands, and preserved all active
command paths.

Phase 3 of this programme, Low-Risk Ops Consolidation And Startup Audit Log Alignment, was
completed in PR 133 (`codex/command-platform-phase-3-ops-startup-audit`), smoke tested
successfully, merged, and pushed to production. Phase 3 grouped approved low-risk
operational/reporting commands under `/ops`, aligned startup command-audit logging with the
authoritative inventory, and confirmed command-cache validation remained green after restart.

The current validator reports:

75 primary commands
29 grouped subcommands
0 disabled legacy command declarations
warning threshold at 90
hard fail at 100

Additional deferred items already exist covering:

Ark grouping
Public command grouping
Validator improvements
Secondary command surface cleanup

However these items were created as tactical follow-ups.

No full command-platform review has yet been performed. Existing command ownership, UX consistency, documentation quality, discoverability, permissions, duplication, architecture boundaries, and operational tooling have not been comprehensively reviewed together.

5. Scope
In Scope

Anything related to command behaviour, structure, lifecycle or discoverability.

Including but not limited to:

Command Inventory
Full command catalogue
Usage analysis
Public/admin classification
Domain ownership mapping
Registration analysis
Command count management
Command Architecture
Command grouping opportunities
Domain ownership
Service boundaries
Repository boundaries
Interaction ownership
Command lifecycle ownership
Command sync ownership
Command UX
Naming consistency
Discoverability
Autocomplete quality
Parameter consistency
Error messaging
Embed consistency
Response consistency
Command Security
Permission checks
Admin validation
Leadership validation
Channel restrictions
Abuse prevention
Dangerous command review
Command Documentation
Missing docs
Stale docs
Command reference accuracy
User guides
Admin guides
Promotion guide updates
Command Testing
Registration coverage
Permission coverage
Interaction coverage
Validation coverage
Missing tests
Command Operations
Sync process
Cache process
Validator coverage
Monitoring
Logging
Version reporting
Command Optimisation
Dead commands
Legacy commands
Duplicate commands
Redundant workflows
Consolidation opportunities
Future Readiness
Command growth forecast
Future command grouping strategy
Governance standards
Command design standards
Out of Scope

Nothing is automatically out of scope.

Items may only be deferred after:

Audit
Classification
Risk assessment
Approval
6. Existing Deferred Items To Include
Phase Candidate A

Ark Command Surface Migration

Current Ark command set remains a significant opportunity for grouping and command-count reduction.

Phase Candidate B

Public Command Domain Grouping

Review:

KVK
Registry
Inventory
Calendar
Subscription commands

for possible grouping strategy.

Phase Candidate C

Legacy Command Surface Cleanup

Review:

Secondary cogs
Disabled command surfaces
Duplicate command declarations
Validator classification improvements

Phase Candidate D

Command Validator Enhancement

Review:

Registration reporting
Threshold warnings
Duplicate reporting
Risk reporting
CI enforcement
7. Mandatory Audit Deliverables

Codex must produce:

Deliverable 1

Complete command inventory.

For every command:

name
category
owner module
permissions
usage level
registration path
proposed path
Deliverable 2

Command architecture review.

For every command domain:

strengths
weaknesses
risks
improvement opportunities
Deliverable 3

Command UX review.

Including:

naming consistency
discoverability
onboarding quality
admin usability
player usability
Deliverable 4

Technical debt register.

Including:

duplication
dead code
missing tests
documentation gaps
architecture violations
Deliverable 5

Future roadmap.

Recommended phased implementation plan.

8. Phase Planning Rules

After audit completion, Codex must propose phases.

Current phase status:

Phase 1 - Permission Decorator Standardisation: complete, smoke tested, merged, and pushed to
production in PR 131.

Phase 2 - Validator And Inventory Tooling Enhancement: complete, smoke tested, merged, and pushed
to production in PR 132.

Phase 3 - Low-Risk Ops Consolidation And Startup Audit Log Alignment: complete, smoke tested,
merged, and pushed to production in PR 133. This phase fixed the stale `DL_bot.py` startup audit
summary and grouped approved low-risk operational/reporting commands under `/ops`, reducing the
active top-level command count to 75.

Phase 4 - Ark Command Grouping: implementation approved for all 14 Ark commands. The active task
pack is `docs/task_packs/Codex Task Pack - Command Platform Phase 4 Ark Command Grouping.md`.

Remaining roadmap:

Phase 5

Public Domain Grouping Design

Phase 6

Canonical Command Documentation

Phase 7

Future Governance And CI Guardrails

Codex may create additional phases if justified.

9. Codex Skills
Skill	Decision
k98-architecture-scope	use
k98-discord-command-feature	use
k98-sql-validation	use if SQL-backed command dependencies discovered
k98-test-selection	use
k98-deferred-optimisation-capture	use
k98-pr-review	use
k98-promotion-check	use
codex-security:security-scan	use
10. Mandatory Workflow
Full command audit.
Stop for approval.
Produce command inventory.
Stop for approval.
Produce phased roadmap.
Stop for approval.
Implement approved phase only.
Validate.
PR review.
Promotion review.
11. Success Criteria
Complete command inventory produced.
All existing command deferred items reviewed.
New command-related findings captured.
Command platform roadmap created.
Discord command limit risk assessed.
Documentation gaps identified.
Permission model reviewed.
UX consistency reviewed.
Architecture consistency reviewed.
Future command governance recommendations documented.
