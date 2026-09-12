# Codex Chat Starter - Private Inventory Import and Support Sharing Phase 1 Pycord 2.8 Upgrade and UI Compatibility Foundation

Status: prepared first implementation slice. Pasting the starter below is explicit approval to
implement Phase 1 in one pass, subject only to the task pack's stop/escalation gates. It does not
approve later private-upload, support-sharing, SQL, or cutover phases.

```text
Codex, implement Private Inventory Import and Support Sharing Phase 1:
Pycord 2.8 Upgrade and UI Compatibility Foundation.

Approval state:
- the Private Inventory Import and Support Sharing programme direction is approved
- the final user direction is a Pycord DesignerModal + multi-file FileUpload workflow
- users should experience one later atomic cutover, not several temporary upload journeys
- this starter is explicit one-pass implementation approval for Phase 1 only
- Phase 1 must make no user-visible inventory workflow change
- do not implement the inventory modal, support sharing, SQL, feature flags, or legacy-route retirement
- operator Discord smoke and production promotion remain separate external gates

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/reference/K98 Bot - Project Engineering Standards.md
- docs/reference/K98 Bot - Coding Execution Guidelines.md
- docs/reference/K98 Bot - Testing Standards.md
- docs/reference/K98 Bot - Skills & Refactor Triggers.md
- docs/reference/K98 Bot - Deferred Optimisation Framework.md
- docs/reference/canonical_command_reference.md
- docs/task_packs/Private Inventory Import and Support Sharing - Programme Pack.md
- docs/task_packs/Codex Task Pack - Private Inventory Import and Support Sharing Phase 1 Pycord 2.8 Upgrade and UI Compatibility Foundation.md
- requirements.txt
- requirements-freeze.txt
- current GitHub workflow Python versions
- all current Modal/View/DesignerModal/DesignerView usages and representative tests
- Pycord 2.8.0 changelog, package metadata, FileUpload source, Label source, DesignerModal API, and official example

Use these skills/workflows:
- k98-architecture-scope
- k98-discord-command-feature
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review
- k98-promotion-check before production promotion
- codex-security:security-diff-scan after implementation

SQL:
- k98-sql-validation is not applicable
- no SQL or DAL work is approved
- stop if the upgrade unexpectedly requires SQL

Before editing, report one concise implementation map and then continue unless a stop gate applies:
1. active Python version, CI Python version, and how production Python will be verified;
2. current Pycord pin and installed version;
3. exact stable 2.8.0 Python requirement and required modal APIs;
4. every repository Modal/View family and representative tests;
5. changed/deprecated/removed 2.7/2.8 APIs that the repository actually uses;
6. expected files to modify/create;
7. focused and full validation plan;
8. confirmation that command counts and inventory behaviour remain unchanged.

Locked dependency decision:
- replace the historical Git pin with exact `py-cord==2.8.0`
- do not pin master, another unreleased commit, or a version range
- update requirements-freeze.txt consistently
- do not upgrade unrelated dependencies
- perform at least one clean requirements installation and run pip check
- record the installed discord/Pycord version

Locked compatibility decision:
- keep existing discord.ui.Modal and discord.ui.View code on the legacy APIs
- do not mass-migrate existing modals/views to DesignerModal/DesignerView
- use direct, focused compatibility fixes only when tests or source evidence prove they are required
- do not add a global warning suppression or speculative compatibility framework
- preserve callbacks, ephemeral flags, permission/author gates, timeouts, follow-ups, message edits,
  attachment cleanup, paginators, webhooks, and command registration
- capture broad modernisation opportunities as deferred optimisations

Add a focused capability contract, preferably:
- tests/test_pycord_ui_capabilities.py

It must prove without a live Discord call:
- intended stable package version is installed
- discord.ui.DesignerModal exists
- discord.ui.Label exists
- discord.ui.FileUpload exists
- FileUpload(min_values=1, max_values=4, required=True) serialises with the expected bounds/type
- Label can wrap FileUpload
- DesignerModal can contain the Label
- legacy Modal + InputText construction still works
- invalid FileUpload bounds fail correctly

Audit actual repository usage for:
- discord.ui.Modal / View / InputText
- send_modal / ctx.send_modal
- view and webhook edits
- paginator custom views
- discord.Emoji
- Messageable.pins assumptions
- VoiceClient / VoiceProtocol
- scheduled-event cover
- removed guild creation/ownership methods
- role colour/type helpers
- Pycord-private attributes used by tests

Classify findings as:
- compatible as-is
- focused fix now
- deprecated but defer
- not used

Do not implement:
- private inventory upload setup or modal
- image reading/validation/storage
- Materials multi-image processing
- Share with Support
- support configuration or retention
- inventory SQL/audit changes
- feature flags
- public upload route retirement
- new commands/options
- report preference or reporting changes

Validation:
- run the environment/dependency commands from the task pack
- run the new capability test
- use k98-test-selection to select representative inventory, MGE, Ark, registry, survey/voting,
  Player Self-Service, webhook/view, startup, and command-registration coverage
- confirm selected files exist before running them
- run architecture boundary validation
- run deferred-item validation
- run selected-test tooling
- run command registration validation and governance tests
- run smoke_imports.py
- run pre-commit
- run the full pytest suite
- run pytest log-noise analysis under current standards
- run codex-security:security-diff-scan
- run k98-pr-review
- prepare k98-promotion-check evidence, but do not claim production promotion or operator smoke

Required final response:
1. summary
2. pre-edit compatibility map
3. Python/runtime evidence
4. dependency diff
5. file manifest
6. compatibility fixes
7. API audit findings
8. command-surface statement
9. SQL statement: none
10. test commands and exact results
11. warnings/deprecations
12. security and PR-review findings
13. operator smoke checklist/status
14. deployment and rollback
15. deferred optimisations
16. remaining blockers

Stop only if a section-16 task-pack gate applies, especially:
- local or production Python is unsupported
- 2.8.0 cannot be installed
- the installed release lacks DesignerModal/Label/FileUpload
- one-to-four FileUpload cannot be represented
- broad legacy modal/view rewrites are required
- command registration changes unexpectedly
- unrelated dependency resolution cannot be constrained
- a high-confidence security issue remains
- bot-wide incompatibility cannot be fixed narrowly

Do not silently choose another upload architecture, use an unreleased Pycord commit, widen the task,
or claim the private inventory outcome is complete.
```
