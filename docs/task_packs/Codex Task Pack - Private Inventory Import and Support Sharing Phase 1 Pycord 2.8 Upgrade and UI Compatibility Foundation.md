# Codex Task Pack - Private Inventory Import and Support Sharing Phase 1 Pycord 2.8 Upgrade and UI Compatibility Foundation

## 1. Task Header

- Task name: `Private Inventory Import and Support Sharing Phase 1 — Pycord 2.8 Upgrade and UI Compatibility Foundation`
- Date: `2026-07-15`
- Owner/context: Approved first implementation slice of the Private Inventory Import and Support Sharing programme
- Task type: `dependency upgrade | Discord UI compatibility | enabling foundation | tests/tooling/docs`
- One-pass approved: `Yes only when the companion Codex chat starter is used; otherwise follow the normal review and approval checkpoints`
- Product direction approved: `Yes`
- Runtime implementation approved by this documentation task: `No`
- Status: `prepared`
- User-visible inventory change: `None`
- SQL impact: `None expected or approved`
- Command-surface impact: `Neither top-level nor grouped command count changes`
- Target dependency: `py-cord==2.8.0`
- Current dependency: `Git pin at e4738227b3d22e92d3b0be4c016a4c287bb0fd1e`
- Primary outcome: `A supported stable Pycord runtime that exposes DesignerModal, Label, and FileUpload while preserving the existing bot`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed standards in this order:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/ENV_REFERENCE.md` if Python/runtime/dependency deployment guidance is changed
- `docs/reference/Promotion Guide.md` before production promotion
- `docs/task_packs/Private Inventory Import and Support Sharing - Programme Pack.md`
- this task pack

Repository files to inspect before editing:

- `requirements.txt`
- `requirements-freeze.txt`
- `.github/workflows/`
- `DL_bot.py`
- `bot_instance.py`
- `Commands.py`
- `commands/command_inventory.py`
- `scripts/smoke_imports.py`
- `scripts/validate_command_registration.py`
- every current `discord.ui.Modal`, `discord.ui.DesignerModal`, `discord.ui.View`, and modal/view test
- representative command and interaction safety helpers

Upstream Pycord evidence to validate against:

- stable Pycord `2.8.0` changelog/release;
- `discord/ui/file_upload.py`;
- `discord/ui/label.py`;
- `discord/ui/modal.py` / DesignerModal implementation;
- `examples/modal_dialogs.py`;
- stable UI-kit documentation.

Known upstream facts at pack creation:

- Pycord 2.7 added `ui.FileUpload`;
- Pycord 2.7 introduced `DesignerModal`/`DesignerView` for Components V2 while restoring legacy
  `Modal`/`View` behaviour for existing code;
- Pycord 2.7 removed Python 3.8 and 3.9 support;
- Pycord 2.8.0 is a stable release dated 2026-05-18;
- the current Pycord project metadata supports Python `>=3.10,<3.15`;
- the K98 command-governance workflow currently uses Python 3.11.

Do not rely only on this summary. Reconfirm the exact package metadata and API in the installed
2.8.0 distribution during implementation.

## 3. Objective

Replace the current historical Pycord Git commit pin with stable `py-cord==2.8.0`, prove that the
repository and target runtime meet its Python requirements, and validate that the wider bot remains
compatible.

Add a narrow, explicit capability contract proving that the installed library exposes and can
construct:

- `discord.ui.DesignerModal`;
- `discord.ui.Label`;
- `discord.ui.FileUpload`;
- a FileUpload configured for one-to-four files;
- the existing legacy `discord.ui.Modal` and `discord.ui.InputText` pattern.

Make only compatibility changes that are directly required by the dependency upgrade. Do not
implement the private inventory modal, support sharing, SQL changes, feature flags, or public-route
retirement in this task.

## 4. Background

The repository currently pins Pycord to:

```text
py-cord @ git+https://github.com/Pycord-Development/pycord@e4738227b3d22e92d3b0be4c016a4c287bb0fd1e
```

That commit predates the Components V2 modal support needed by the approved inventory programme.
The current pinned project metadata supports Python 3.8+, and the installed source's component enum
does not provide the new File Upload modal component.

Stable Pycord 2.8.0 includes the required 2.7 modal architecture:

- existing `discord.ui.Modal` and `discord.ui.View` remain on the compatible legacy behaviour;
- `discord.ui.DesignerModal` and `discord.ui.DesignerView` support newer components;
- `DesignerModal` composes modal inputs through `discord.ui.Label`;
- `discord.ui.FileUpload` accepts `min_values` and `max_values` between the documented bounds and
  returns uploaded `Attachment` objects through `.values`.

The upgrade is bot-wide, not inventory-only. Existing legacy modals are present across inventory,
MGE, Ark, registry, voting/survey, and Player Self-Service areas. Existing views, follow-up
responses, webhook edits, paginators, selects, and message components may also exercise changed or
fixed Pycord paths.

This task isolates that shared dependency risk before any inventory feature code is added.

## 5. Scope

### In Scope

- Audit the actual local, CI, and production Python versions relevant to installation and deployment.
- Confirm they are within Pycord 2.8.0's supported range.
- Replace the Git commit dependency with exact stable `py-cord==2.8.0`.
- Update `requirements-freeze.txt` consistently without upgrading unrelated packages.
- Install in the project environment and run `pip check`.
- Record the installed `discord.__version__` or authoritative package version.
- Audit repository usage affected by Pycord 2.7/2.8 changed, deprecated, removed, and fixed APIs.
- Preserve current legacy Modal/View behaviour.
- Make focused compatibility fixes only where tests or direct evidence prove they are required.
- Add a Pycord UI capability/compatibility test module.
- Ensure every current modal/view module imports successfully.
- Run representative legacy modal/view tests plus full repository quality gates.
- Run command registration validation and prove command counts/paths did not change.
- Run Codex Security diff review because this changes the Discord/network dependency.
- Update minimal developer/programme documentation needed to record the new runtime baseline.
- Produce an operator smoke checklist and rollback note.

### Out of Scope

- The private inventory setup view.
- `DesignerModal` implementation in inventory runtime code.
- File reading, image validation, or transient image storage.
- Multi-image Materials processing.
- Share with Support.
- New support-channel configuration.
- SQL or DAL changes.
- Inventory audit semantic changes.
- Feature flags.
- Retirement of `handle_inventory_upload_message`, `upload_routes/inventory_route.py`, or the
  `DL_bot.py` inventory fast path.
- Public/private inventory report preference changes.
- Broad conversion of legacy modals or views to DesignerModal/DesignerView.
- Unrelated dependency upgrades.
- Cosmetic refactors that are not required to restore compatibility.
- New commands or command options.

## 6. Source Deferred Items

Not applicable. This is an approved programme foundation rather than a batch from the deferred
optimisation backlog.

If the audit discovers unrelated dependency debt or broad modal-modernisation opportunities, capture
them structurally and do not expand this task.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Shared dependency upgrade affects startup, commands, views, modals, interaction responses, tests, and deployment. |
| `k98-discord-command-feature` | use | No command is added, but Discord UI and interaction compatibility are the core risk. |
| `k98-sql-validation` | not applicable | No SQL contract is touched or required. Stop if implementation unexpectedly proposes SQL. |
| `k98-test-selection` | use | Select representative modal/view coverage plus dependency, startup, registration, and full-suite gates. |
| `k98-deferred-optimisation-capture` | use | Capture broad modernisation or unrelated compatibility debt without widening scope. |
| `k98-pr-review` | use | Required before handoff because the dependency is bot-wide. |
| `k98-promotion-check` | use before production promotion | Confirm production Python, clean install, bot startup, and rollback procedure. |
| `codex-security:security-diff-scan` | use | Dependency supply chain, Discord interactions, network behaviour, and user input are security-sensitive. |

## 8. Mandatory Workflow

The companion chat starter explicitly approves one-pass execution for this Phase 1 task. Even in one
pass, preserve the following order:

1. Read the required standards and programme/task packs.
2. Produce a concise pre-edit implementation map.
3. Confirm local and CI Python versions.
4. Determine how production Python will be verified before promotion.
5. Inspect the current Pycord pin and exact 2.8.0 package metadata/changelog.
6. Search the repository for changed/deprecated/removed Pycord APIs and all modal/view classes.
7. Record the expected files and tests before editing.
8. Upgrade only Pycord and its directly required resolution metadata.
9. Add the capability contract.
10. Run focused compatibility tests.
11. Fix only upgrade-caused failures.
12. Run broad quality, registration, startup/import, and full-suite gates.
13. Run Codex Security diff review and K98 PR review.
14. Update task/programme status only after validation.
15. Leave operator Discord smoke and production promotion explicitly pending until performed.

Stop only for a blocker in section 16. Do not pause merely because a normal compatibility fix is
needed and remains inside scope.

## 9. Audit Requirements

### 9.1 Runtime and dependency audit

Record:

- `python --version` and `sys.version_info` in the active development environment;
- Python version used by each relevant GitHub workflow;
- the documented or observed production interpreter path/version;
- current installed Pycord version/commit;
- exact 2.8.0 `Requires-Python`;
- direct Pycord dependency changes between the pin and 2.8.0;
- whether a clean `pip install -r requirements.txt` succeeds;
- `pip check` result;
- whether the bot uses optional voice dependencies or removed guild-creation APIs.

Do not claim production compatibility solely from CI. Promotion must verify the bot machine's actual
interpreter.

### 9.2 Repository API audit

Search for and classify at least:

- every `discord.ui.Modal` subclass;
- every `discord.ui.View` subclass;
- any existing `DesignerModal`/`DesignerView`;
- `discord.ui.InputText`;
- modal `add_item` patterns;
- `interaction.response.send_modal`;
- `ctx.send_modal`;
- view/message edits;
- webhook edits and attachment replacement;
- paginators/custom views;
- `discord.Emoji`;
- `Messageable.pins()` assumptions;
- `discord.VoiceClient` / `discord.VoiceProtocol`;
- removed guild creation/ownership methods;
- scheduled-event `cover` usage;
- role colour assumptions;
- deprecated role-type helpers;
- use of attributes changed by 2.7/2.8;
- tests that stub or monkeypatch Pycord internals.

Classify each finding:

```text
compatible as-is
requires focused change
deprecated but safe to defer
not used
```

Do not replace an API merely because upstream deprecated it unless leaving it creates a concrete
runtime/test problem or the change is trivially local and lower risk.

### 9.3 Interaction behaviour audit

Confirm representative coverage for:

- slash command defer and follow-up;
- ephemeral responses;
- legacy modal open and callback;
- button-to-modal response;
- select values;
- view timeout/disable;
- message edit with a view;
- attachment replacement/removal;
- webhook follow-up/edit;
- application-command registration;
- bot startup/import.

### 9.4 Architecture and cleanup audit

Review for:

- dependency-specific compatibility shims placed in the wrong layer;
- broad monkeypatches or global warning suppression;
- test helpers coupled to old private Pycord attributes;
- duplicate modal helpers that appear only because of the upgrade;
- changes that accidentally implement later inventory phases.

Any broad redesign is deferred unless it is the smallest safe way to restore 2.8 compatibility.

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Dependency pin | `requirements.txt`, mirrored consistently in `requirements-freeze.txt` |
| Capability contract | focused test under `tests/` |
| Compatibility fixes | existing owning module; no new global compatibility layer unless strictly necessary |
| Commands | unchanged except a proven compatibility fix |
| Views/modals | retain legacy classes; no mass DesignerModal migration |
| Startup | existing bot startup path |
| Runtime guidance | current developer/environment docs |
| SQL | no change |
| Programme docs | status/evidence update only after validation |

Preferred capability-test name:

```text
tests/test_pycord_ui_capabilities.py
```

A different name is acceptable if repository naming conventions require it.

## 11. Likely Files

### Review

- `requirements.txt`
- `requirements-freeze.txt`
- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/ENV_REFERENCE.md`
- `.github/workflows/*.yml`
- `DL_bot.py`
- `bot_instance.py`
- `Commands.py`
- `commands/command_inventory.py`
- `core/interaction_safety.py`
- `account_picker.py`
- all files returned by searches for `discord.ui.Modal`, `discord.ui.View`,
  `discord.ui.InputText`, `send_modal`, and relevant deprecated APIs
- modal/view/command-registration/startup tests
- `scripts/smoke_imports.py`
- `scripts/select_tests.py`
- `scripts/validate_command_registration.py`

### Modify

Expected:

- `requirements.txt`
- `requirements-freeze.txt`

Conditional, only if required by evidence:

- focused existing modal/view modules;
- focused tests coupled to changed Pycord behaviour;
- `README-DEV.md` or `docs/reference/ENV_REFERENCE.md` to state Python/Pycord baseline;
- programme/task-pack status after completion.

### Create

Expected:

- `tests/test_pycord_ui_capabilities.py`

Not approved:

- inventory private-upload runtime modules;
- support modules;
- SQL files;
- generic compatibility framework.

## 12. Implementation Requirements

### 12.1 Dependency pin

Use:

```text
py-cord==2.8.0
```

Do not:

- pin Pycord `master`;
- replace one Git commit with another unpublished commit;
- use a range;
- upgrade all requirements;
- regenerate the freeze in a way that silently changes unrelated versions.

Record any direct transitive resolution change required by a clean install.

### 12.2 Python version contract

Pycord 2.8 must run only where its package metadata supports the interpreter.

Required outcome:

- development environment supported;
- CI Python supported;
- production interpreter verification documented as a promotion gate;
- no vague "should work" assumption;
- no in-code version bypass.

If production is below 3.10, stop under section 16 rather than changing the programme to an older
Pycord or inventing a custom FileUpload implementation.

### 12.3 Capability contract

The new focused test must prove, without making a live Discord call:

1. the installed package is the intended stable version;
2. `discord.ui.DesignerModal` exists;
3. `discord.ui.Label` exists;
4. `discord.ui.FileUpload` exists;
5. a FileUpload can be built with `min_values=1`, `max_values=4`, and `required=True`;
6. the generated component reports the expected values and File Upload component type;
7. a Label can wrap the FileUpload;
8. a DesignerModal can contain that Label;
9. a legacy `discord.ui.Modal` with `discord.ui.InputText` can still be constructed using the
   repository's current pattern;
10. invalid FileUpload bounds raise appropriate errors.

Avoid brittle tests of unrelated private upstream internals. Inspecting the component dictionary is
acceptable where it is the public serialization contract needed to prove the feature.

### 12.4 Existing modal/view compatibility

- Keep existing legacy `Modal` subclasses on `Modal`.
- Do not change their layout to `Label` unless the upgrade proves it necessary.
- Keep existing `View` subclasses on `View`.
- Do not introduce `DesignerView` merely because it exists.
- Preserve callback signatures expected by the installed Pycord release.
- Preserve ephemeral flags, timeout behaviour, and author/permission gates.
- Preserve attachment/file-stream cleanup.
- Keep compatibility changes narrow and covered by a focused regression test.

### 12.5 Warnings and deprecations

- Do not globally suppress Pycord warnings.
- Record new warnings from focused/full tests.
- Fix warnings only when they indicate a current break, near-certain future break, or trivial
  low-risk local change.
- Capture broad cleanup as a deferred optimisation with file evidence and impact/risk.

### 12.6 Command surface governance

- [x] This task changes neither top-level command count nor grouped subcommand count.
- [ ] Preserve every command decorator, name, description, option, permission, version, usage identity,
      and registration owner.
- [ ] Do not add a test-only command.
- [ ] Run `scripts/validate_command_registration.py`.
- [ ] Run `tests/test_validate_command_registration.py`.
- [ ] Run `tests/test_command_inventory.py`.
- [ ] Run `tests/test_command_registration_smoke.py`.
- [ ] Update `docs/reference/canonical_command_reference.md` only if an unexpected real command
      contract changes; such a change should normally be a blocker for this task.

### 12.7 Dependency hygiene

- Use a clean or recreated environment for at least one install verification.
- Run `pip check`.
- Capture the final installed Pycord version.
- Do not commit virtual-environment or wheel artifacts.
- Do not commit credentials or machine-specific paths.
- Check the dependency diff for suspicious or unexpected packages.
- Run the required security review.

## 13. Refactor Decisions

| Issue | Decision | Reason |
|---|---|---|
| Replace all legacy modals with DesignerModal | defer | Pycord explicitly retains legacy behaviour; mass migration would widen risk and does not enable Phase 1. |
| Create a global Pycord compatibility shim | not applicable unless proven necessary | Prefer direct owning-module fixes; a global shim could hide real incompatibilities. |
| Modernise unrelated deprecated APIs | defer unless trivial and directly blocking | Keep the dependency slice focused. |
| Add private inventory FileUpload modal | defer to programme Phase 3 | This task proves capability but changes no user workflow. |
| Add support sharing | defer to programme Phase 4 | Requires separate consent, SQL, permissions, and retention work. |
| Retire public inventory uploads | defer to programme Phase 5 | Must occur atomically with the completed private replacement. |
| Adjust unrelated dependency versions | do not do | Prevent an unreviewable dependency bundle. |

New findings must use the structured deferred-optimisation format from the active reference
framework.

## 14. Testing Requirements

### 14.1 Environment and dependency checks

Run from the project environment, using the repository's current Windows conventions:

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "import discord, sys; print(sys.version); print(discord.__version__)"
```

Where the active environment directory is `venv` rather than `.venv`, use the actual repository
environment. Do not create duplicate environments accidentally.

### 14.2 Required focused tests

At minimum:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_pycord_ui_capabilities.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_inventory_upload_flow.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_inventory_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_registry_views_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_survey_post_view.py tests/test_survey_admin_update_view.py
```

Use `k98-test-selection` and repository evidence to add representative tests for:

- MGE legacy modals and views;
- Ark modals/views;
- Player Self-Service modals/views;
- webhook/view edit behaviour;
- paginators if used;
- startup and import smoke.

Do not blindly run a guessed file name. Confirm selected tests exist.

### 14.3 Required repository gates

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Use the current standards for capturing a pytest audit log when needed.

### 14.4 Manual local/runtime smoke

Before PR handoff where practical:

- import the bot command registration path;
- instantiate representative existing legacy modals;
- instantiate representative views;
- confirm no startup-time Pycord exception;
- inspect warning output;
- verify the new capability test is testing the installed package, not a stub.

### 14.5 Operator Discord smoke before production acceptance

The operator should test representative existing journeys after the dependency-only release:

- open and submit an existing legacy inventory correction modal;
- open and submit one MGE modal;
- open and submit one registry/account modal;
- open and submit one survey/voting modal;
- exercise a button and select view;
- exercise an ephemeral follow-up;
- confirm command registration and normal bot startup;
- confirm no inventory import behaviour changed.

Do not mark this external smoke complete until the operator performs it.

### 14.6 AI review gates

- `codex-security:security-diff-scan`: required after implementation.
- `k98-pr-review`: required before handoff.
- `k98-promotion-check`: required before production promotion.
- Document all findings and whether they were fixed, deferred, or false positives.

## 15. Acceptance Criteria

- [ ] Current local Python version is recorded and supported by Pycord 2.8.0.
- [ ] CI Python version is recorded and supported.
- [ ] Production Python verification is completed before promotion, not inferred.
- [ ] `requirements.txt` pins exactly `py-cord==2.8.0`.
- [ ] `requirements-freeze.txt` is consistent.
- [ ] No unrelated dependency was upgraded without an explicit reason.
- [ ] Clean installation succeeds.
- [ ] `pip check` succeeds.
- [ ] Installed Pycord version is confirmed.
- [ ] DesignerModal, Label, and FileUpload capability tests pass.
- [ ] FileUpload one-to-four bounds and invalid bounds are covered.
- [ ] Legacy Modal/InputText construction is covered.
- [ ] Existing modal/view modules import.
- [ ] Representative inventory, MGE, Ark, registry, survey, and Player Self-Service UI regressions
      pass or the selected equivalent coverage is documented.
- [ ] No inventory user workflow changed.
- [ ] No command name, count, option, registration owner, or permission changed.
- [ ] No SQL changed.
- [ ] No private inventory modal or support code was added.
- [ ] Architecture and deferred-item validators pass.
- [ ] Command registration validation passes.
- [ ] Startup/import smoke passes.
- [ ] Pre-commit passes.
- [ ] Full pytest passes, or unrelated pre-existing failures are documented under repository rules.
- [ ] Test log-noise analysis passes where required.
- [ ] Codex Security diff review and K98 PR review are complete.
- [ ] Rollback steps are documented.
- [ ] Operator Discord smoke remains explicitly pending until performed.
- [ ] Out-of-scope findings are captured structurally.

## 16. Stop / Escalation Gates

Stop and report before implementation or promotion if:

1. the local or production interpreter is below Python 3.10 or outside `>=3.10,<3.15`;
2. `py-cord==2.8.0` cannot be installed from the approved package source;
3. the installed 2.8.0 package lacks DesignerModal, Label, or FileUpload;
4. FileUpload cannot express `min_values=1,max_values=4`;
5. a broad rewrite of legacy modals/views is required;
6. command registration changes unexpectedly;
7. the upgrade requires SQL, schema, or inventory workflow work;
8. the dependency resolver changes unrelated packages materially and cannot be constrained safely;
9. a high-confidence security issue in the dependency or integration remains unresolved;
10. full-suite failures indicate a bot-wide incompatibility that cannot be fixed narrowly;
11. production promotion cannot verify the real interpreter and clean install.

Do not fall back to another private-upload design, an unreleased Pycord commit, or custom raw Discord
component implementation inside this task.

## 17. Required Delivery Output

Use this delivery shape:

1. Summary
2. Pre-edit compatibility map
3. Python/runtime evidence
4. Dependency diff
5. File Manifest
6. New Files
7. Modified Files
8. Compatibility fixes
9. API audit findings
10. Command-surface statement
11. SQL Changes (`none`)
12. Helpers reused
13. Refactor/deferred findings
14. Test plan and exact results
15. Warning/deprecation evidence
16. AI review gates
17. Operator smoke checklist/status
18. Deployment steps
19. Rollback steps
20. Remaining blockers

Do not claim inventory privacy has been delivered. This task only establishes the supported runtime
foundation.

## 18. Deployment Steps

Before mirror PR:

1. Complete all automated validation.
2. Complete Codex Security diff review and K98 PR review.
3. Confirm the dependency diff contains only intended changes.
4. Provide the operator smoke checklist.

Before production PR/promotion:

1. Run `k98-promotion-check`.
2. Verify the bot machine's actual Python version.
3. Stop the bot through the approved runbook.
4. Install the updated requirements in the production virtual environment.
5. Run `pip check`.
6. Confirm `discord.__version__`.
7. Start the bot through the approved watchdog/startup path.
8. Check startup logs and command registration.
9. Perform representative operator Discord smoke.
10. Monitor errors before declaring acceptance.

## 19. Rollback

If the dependency release fails:

1. Revert the Pycord requirement to the prior Git commit pin.
2. Reinstall `requirements.txt` in the production virtual environment.
3. Run `pip check`.
4. Restart through the approved runbook.
5. Confirm the prior `discord` version/commit.
6. Repeat startup and representative modal/view smoke.
7. Record the failure evidence and do not start programme Phase 2.

No SQL rollback is involved.

## 20. PR Summary Template

```md
## Summary

- Upgrade Pycord from the historical Git commit pin to stable `py-cord==2.8.0`.
- Add an explicit UI capability contract for DesignerModal, Label, FileUpload, and legacy Modal compatibility.
- Preserve all existing commands and user workflows.

## Changes

- Updated dependency pins.
- Added focused Pycord UI capability coverage.
- Applied only evidence-backed compatibility fixes, if any.
- Updated runtime/developer evidence where required.

## Tests

- `python -m pip check`
- `python -m pytest -q tests/test_pycord_ui_capabilities.py`
- selected representative modal/view tests
- architecture/deferred/registration/smoke/pre-commit gates
- full pytest suite
- test log-noise analysis

## AI Review Gates

- Codex Security: `run`
- K98 PR review: `run`
- Promotion check: `required before production`

## Deferred Optimisations

- None, or structured findings only.

## Risk / Rollback

- Bot-wide Discord dependency upgrade; rollback restores the prior Pycord Git pin, reinstalls requirements, and repeats startup/UI smoke.
- No inventory workflow or SQL change in this PR.
```
