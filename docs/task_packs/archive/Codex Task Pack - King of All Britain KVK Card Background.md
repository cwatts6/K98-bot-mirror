# Codex Task Pack — King of All Britain KVK Card Background

## Archive Status

Completed and operator smoke accepted on `2026-08-28`. Delivered through mirror PR
[#244](https://github.com/cwatts6/K98-bot-mirror/pull/244) and production PR
[#551](https://github.com/cwatts6/k98-bot/pull/551), pending the operator's manual merges.
This file is retained as the historical execution and completion record; it is no longer an active
task pack.

## 1. Task Header

- Task name: `King of All Britain KVK Card Background`
- Date: `2026-08-26`
- Owner/context: `Chris Watts — add a King of All Britain visual identity to the player KVK Targets and Stats cards`
- Task type: `feature / visual asset integration`
- Final status: `complete / operator smoke accepted / archived`
- One-pass approved: `yes`
- One-pass basis: The operator has supplied and approved the production background asset and has explicitly requested the focused renderer updates and PR-ready deployment task.

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

For the security-routing decision, also read:

- the active root and applicable nested `SECURITY.md` files
- the `k98-security-review-routing` skill
- `docs/templates/Codex Task Pack Template.md`

Then review the implementation area:

- `kvk/theme.py`
- `kvk/rendering/kvk_stats_card_renderer.py`
- `kvk/rendering/kvk_targets_card_renderer.py`
- `tests/test_kvk_stats_card_renderer.py`
- `tests/test_kvk_targets_card_renderer.py`
- `assets/kvk/cards/`

No SQL schema, procedure, view, index, migration, or SQL-repository change is expected. Do not open or modify `C:\K98-bot-SQL-Server` unless the audit discovers an unexpected SQL dependency that genuinely blocks the locked implementation.

## 3. Objective

Add the supplied text-free King of All Britain background to the checked-in KVK card assets and make both the player KVK Stats renderer and player KVK Targets renderer select it whenever the resolved KVK name normalises to `king of all britain`.

Preserve all current card layouts, text, dimensions, filenames, fallback behaviour, target-publication behaviour, command behaviour, data contracts, and Discord visibility.

## 4. Background

Both player-card renderers currently:

- render final PNGs at `1180 × 640`
- load assets from `assets/kvk/cards/`
- normalise the KVK name through `kvk.theme.normalize_kvk_mode`
- maintain a local `MODE_BACKGROUNDS` mapping
- fall back in this order:
  1. matching mode-specific asset
  2. `Default_card.jpg`
  3. `Tides_Stats_Card.png`
  4. no renderable image if no candidate exists

The current explicit mode mappings cover:

- `Tides of War`
- `Heroic Anthem`
- `Storm of Stratagems`
- `Songs of Troy`

`King of All Britain` currently has no explicit mapping, so it falls through to the generic default asset.

The renderers resize any selected source image to `1180 × 640` using Pillow/LANCZOS. An arbitrary source size therefore works technically, but a source asset already authored at the production ratio is preferred because it avoids stretching and composition drift. The supplied asset is already exactly `1180 × 640`.

### Supplied Production Asset

| Property | Locked value |
|---|---|
| Source file supplied to Codex | `King_of_All_Britain_Stats_Card.png` |
| Repository destination | `assets/kvk/cards/King_of_All_Britain_Stats_Card.png` |
| Dimensions | `1180 × 640` |
| Colour mode | `RGB` |
| File size | `856,548 bytes` |
| SHA-256 | `987be4495471936db491d25d00bb3eb9c23e259a86ed02d3e46b361fa3b6d605` |
| Embedded wording | none |
| Embedded game logo | none |
| Intended consumers | KVK Stats, KVK More Stats, and KVK Targets renderers |

The asset was prepared from the operator-supplied King of All Britain/Viking invasion artwork. The embedded title, subtitle, and lower-corner logo were removed, and the lower field was rebuilt as subdued battle mist so the renderer-owned data overlays remain readable.

## 5. Scope

### In Scope

- Add the supplied PNG unchanged at:
  - `assets/kvk/cards/King_of_All_Britain_Stats_Card.png`
- Add the normalised key `king of all britain` to `MODE_BACKGROUNDS` in:
  - `kvk/rendering/kvk_stats_card_renderer.py`
  - `kvk/rendering/kvk_targets_card_renderer.py`
- Point both mappings to the exact same asset filename.
- Preserve the current normalisation and fallback order.
- Extend focused renderer tests to cover King of All Britain selection in both renderer modules.
- Validate the new asset contract:
  - exists
  - can be opened by Pillow
  - is exactly `1180 × 640`
  - resolves from the exact production KVK name
- Render representative local Stats, More Stats, and Targets card smoke artifacts with `kvk_name="King of All Britain"` and visually inspect overlay readability.
- Create a focused branch, commit, push, and PR against `K98-bot-mirror/main`.
- Return a complete PR and deployment handoff.

### Out of Scope

- No SQL changes.
- No change to `dbo.KVK_Details`, KVK context resolution, DAL queries, or KVK-state logic.
- No command, option, permission, autocomplete, registration, or Discord visibility change.
- No change to Stats or Targets payload construction.
- No change to target publication state, progress state, badges, warnings, or provenance.
- No layout, typography, copy, metric, colour-policy, or card-dimension redesign.
- No replacement or modification of existing KVK background assets.
- No history-card, ranking-card, honor-card, or Pre-KVK asset redesign.
- No broad renderer consolidation.
- Do not add an alternative JPG to the repository; the PNG above is the canonical runtime asset.
- Do not merge, promote, or deploy the PR. Hand it back ready for operator review and deployment.

## 6. Locked Implementation Contract

### Asset

Copy the supplied file byte-for-byte to:

```text
assets/kvk/cards/King_of_All_Britain_Stats_Card.png
```

Before committing, verify:

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; from hashlib import sha256; from PIL import Image; p=Path(r'assets/kvk/cards/King_of_All_Britain_Stats_Card.png'); im=Image.open(p); print(p, im.size, im.mode, sha256(p.read_bytes()).hexdigest())"
```

Expected values:

```text
size: (1180, 640)
sha256: 987be4495471936db491d25d00bb3eb9c23e259a86ed02d3e46b361fa3b6d605
```

Do not recompress, resave, recolour, crop, sharpen, or otherwise alter the supplied PNG during implementation.

### Stats Renderer Mapping

In `kvk/rendering/kvk_stats_card_renderer.py`, extend the existing mapping with:

```python
"king of all britain": ASSET_DIR / "King_of_All_Britain_Stats_Card.png",
```

### Targets Renderer Mapping

In `kvk/rendering/kvk_targets_card_renderer.py`, extend the existing mapping with:

```python
"king of all britain": ASSET_DIR / "King_of_All_Britain_Stats_Card.png",
```

### Normalisation

Continue to use the existing `normalize_kvk_mode` helper. Do not add special-case string comparisons elsewhere.

The following must resolve to the King of All Britain asset:

- `King of All Britain`
- `king of all britain`
- `king_of_all_britain`
- `king-of-all-britain`
- variants containing repeated surrounding/internal whitespace that the existing normaliser already supports

### Fallback Behaviour

Do not change `_background_for_mode` fallback ordering or missing-file behaviour.

An unknown KVK name must still resolve to `Default_card.jpg` when it exists. The new mapping must not make King of All Britain the global default.

## 7. Codex Skills To Use

### Skill Decisions

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | `use` | Perform a concise one-pass scope confirmation: one binary asset, two renderer mappings, focused tests, no SQL or command changes. |
| `k98-discord-command-feature` | `not applicable` | Slash commands, views, permissions, response visibility, registration, and interaction behaviour remain unchanged. |
| `k98-sql-validation` | `not applicable` | Existing `KVK_NAME` data is consumed but no SQL contract or query changes. |
| `k98-test-selection` | `use` | Select focused renderer tests plus normal repository gates appropriate to the final diff. |
| `k98-deferred-optimisation-capture` | `use if needed` | Capture only genuine out-of-scope non-security findings; do not expand this visual integration PR. |
| `k98-pr-review` | `use` | Review asset inclusion, mapping parity, fallback preservation, tests, and visual smoke evidence. |
| `k98-promotion-check` | `use` | Produce a clear restart/deployment and post-deployment smoke handoff; do not deploy. |
| `k98-security-review-routing` | `use` | Route the final bot-repository diff to a focused Changes review with Deep Off. |

### Security Review Decision

| Repository | Decision | Target | Expected setup / execution | Evidence |
|---|---|---|---|---|
| `K98-bot-mirror` | `Changes review` | final `origin/main...HEAD` diff, expected to contain the PNG asset, two KVK renderer mapping changes, focused tests, and task documentation if committed | `Changes + Deep Off` using `$codex-security:security-diff-scan` | retain the completed scan result or explicit no-finding evidence in the final handoff |

Reason: the task changes checked-in runtime code and a runtime-selected asset. It does not authorise a standard or deep codebase audit.

## 8. Mandatory Workflow

One-pass implementation is approved for the locked scope:

1. Read the required repository guidance.
2. Confirm the working tree is clean and update from current `main`.
3. Create a focused branch, suggested name:
   - `feat/king-of-all-britain-kvk-card`
4. Audit the two renderer mappings, their fallback functions, current dimensions, and focused tests.
5. Verify that the supplied asset is present in the task inputs and matches the locked hash and dimensions.
6. Copy the PNG byte-for-byte to `assets/kvk/cards/King_of_All_Britain_Stats_Card.png`.
7. Add the exact normalised mapping to both renderer modules.
8. Add focused regression coverage for:
   - Stats resolver
   - Targets resolver
   - normalised name variants
   - asset existence/openability/dimensions
   - unknown-mode fallback preservation
9. Render local King of All Britain smoke artifacts for:
   - main Stats card
   - More Stats card
   - Targets card with populated metrics
   - Targets empty/exempt state if practical
10. Inspect the smoke artifacts at full size for:
    - readable headings and values
    - no visible embedded source wording or logo
    - no distracting collision between characters and dynamic overlays
    - unchanged `1180 × 640` output
11. Run selected validators and tests.
12. Inspect the final Git diff for accidental binary changes or unrelated renderer edits.
13. Run `k98-pr-review`.
14. Run the selected diff-focused Codex Security Changes review with Deep Off.
15. Commit, push, and create/update a PR against `K98-bot-mirror/main`.
16. Return the complete handoff. Do not merge or deploy.

Stop and report before continuing only if:

- the supplied PNG hash or dimensions do not match this pack
- the active renderer architecture differs materially from the audited shape
- `King of All Britain` is resolved from a different payload field than `payload.kvk_name`
- adding the mapping unexpectedly requires SQL, command, payload, or persistence changes
- existing tests reveal a genuine behaviour conflict requiring scope expansion

## 9. Audit Requirements

Confirm and record:

- current branch, base SHA, and clean working tree
- both renderer output dimensions are still `1180 × 640`
- both renderers still select with `payload.kvk_name`
- both renderers still call `normalize_kvk_mode`
- both local `MODE_BACKGROUNDS` mappings are updated
- fallback order remains mode asset → default → Tides
- the Stats secondary/more card uses the same Stats background resolver
- no other KVK renderer silently requires the new mapping
- no command or SQL change is required
- no existing asset is replaced
- the committed PNG hash and dimensions
- local visual smoke artifacts and inspection result
- restart requirement after deployment

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Production visual asset | `assets/kvk/cards/King_of_All_Britain_Stats_Card.png` |
| KVK Stats background selection | `kvk/rendering/kvk_stats_card_renderer.py` |
| KVK Targets background selection | `kvk/rendering/kvk_targets_card_renderer.py` |
| KVK-name normalisation | existing `kvk/theme.py`; review only |
| Stats renderer regression tests | `tests/test_kvk_stats_card_renderer.py` |
| Targets renderer regression tests | `tests/test_kvk_targets_card_renderer.py` |
| SQL | not applicable |
| Command registration | unchanged |
| Persistence/cache | no new state; module mapping becomes active after process restart |

## 11. Likely Files

### Review

- `AGENTS.md`
- `README-DEV.md`
- `SECURITY.md`
- `docs/reference/README.md`
- `docs/templates/Codex Task Pack Template.md`
- `kvk/theme.py`
- `kvk/rendering/kvk_stats_card_renderer.py`
- `kvk/rendering/kvk_targets_card_renderer.py`
- `tests/test_kvk_stats_card_renderer.py`
- `tests/test_kvk_targets_card_renderer.py`
- `assets/kvk/cards/`

### Modify

- `kvk/rendering/kvk_stats_card_renderer.py`
- `kvk/rendering/kvk_targets_card_renderer.py`
- `tests/test_kvk_stats_card_renderer.py`
- `tests/test_kvk_targets_card_renderer.py`

### Create

- `assets/kvk/cards/King_of_All_Britain_Stats_Card.png`

### Optional Documentation

- this task pack and its chat starter, only if the repository’s current task-pack workflow expects them to be committed

## 12. Implementation Requirements

- Add the exact same normalised key and filename to both local renderer maps.
- Keep `_background_for_mode` and `_load_background` behaviour unchanged.
- Do not duplicate a new special-case helper outside the existing maps.
- Do not change `WIDTH`, `HEIGHT`, resize mode, PNG output mode, output filename, or attachment contract.
- Do not alter any Stats or Targets layout coordinates.
- Do not alter target publication badges or warning positioning.
- Preserve all existing supported KVK modes and unknown-mode fallback assertions.
- Keep the PR narrowly focused.

### Mapping Duplication Decision

The Stats and Targets renderers currently own separate but equivalent local mappings. For this task:

- update both mappings explicitly
- add parity-oriented tests
- do not introduce a new shared asset-registry refactor in this PR

A broader mapping consolidation would be a separate refactor with wider regression scope and is not required to deploy the new asset safely.

## 13. Refactor Decisions

| Issue | Decision | Reason |
|---|---|---|
| Duplicate local `MODE_BACKGROUNDS` dictionaries in Stats and Targets renderers | `defer / leave unchanged` | Pre-existing design. Updating both plus focused parity tests is the smallest safe production change. |
| Renderer automatically resizes every source asset | `leave unchanged` | Existing compatibility contract. The supplied asset already matches production dimensions, so no renderer change is needed. |
| Other KVK visual-card families use separate backgrounds | `not applicable` | History/rankings/honor cards are outside the requested player Stats/Targets surface. |
| SQL KVK-name resolution | `not applicable` | Existing payload and DAL path already provides the KVK name; no defect has been identified there. |

Do not create a deferred optimisation solely to restate known renderer duplication if it is already represented in repository history or backlog. Capture a new structured deferred item only if the audit finds a distinct, currently untracked issue.

## 14. Testing Requirements

### Required Focused Coverage

Extend `tests/test_kvk_stats_card_renderer.py` to assert:

- `_background_for_mode("King of All Britain")` returns `King_of_All_Britain_Stats_Card.png`
- a normalised separator variant such as `king_of_all_britain` resolves identically
- unknown and `None` values still resolve to `Default_card.jpg`
- the resolved King of All Britain asset opens successfully and is `1180 × 640`
- a Stats payload using `kvk_name="King of All Britain"` renders a valid `1180 × 640` PNG
- the More Stats renderer also remains renderable with the same payload

Extend `tests/test_kvk_targets_card_renderer.py` to assert:

- the Targets resolver returns `King_of_All_Britain_Stats_Card.png`
- the exact production name and at least one normalised variant resolve identically
- a Targets payload using `kvk_name="King of All Britain"` renders a valid PNG
- populated and empty-state rendering remain valid
- publication-state rendering is unchanged

### Suggested Commands

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_renderer.py tests\test_kvk_targets_card_renderer.py
.\.venv\Scripts\python.exe -m pre_commit run -a
```

Run the broader selected suite, smoke imports, or full tests when `scripts/select_tests.py`, repository guidance, or the final diff requires them.

### Manual / Visual Smoke

Generate representative local files using `King of All Britain` as the payload KVK name and record their paths in the handoff.

Inspect:

- main Stats
- More Stats
- Targets with values
- Targets no-target/exempt state where practical

Confirm:

- correct background is visibly selected
- no embedded title, subtitle, or source logo is visible
- all dynamic text remains legible
- cards remain exactly `1180 × 640`
- output filenames remain unchanged
- fallback behaviour is unchanged

## 15. Acceptance Criteria

- [x] The supplied PNG is committed at `assets/kvk/cards/King_of_All_Britain_Stats_Card.png`.
- [x] The committed file is exactly `1180 × 640`.
- [x] The committed file SHA-256 is `987be4495471936db491d25d00bb3eb9c23e259a86ed02d3e46b361fa3b6d605`.
- [x] The asset contains no embedded title, subtitle, game logo, or replacement wording.
- [x] `kvk_stats_card_renderer.MODE_BACKGROUNDS` contains the exact key `king of all britain`.
- [x] `kvk_targets_card_renderer.MODE_BACKGROUNDS` contains the exact key `king of all britain`.
- [x] Both mappings point to the same exact PNG filename.
- [x] Exact, lowercase, underscore, and hyphen naming variants resolve through the existing normaliser.
- [x] Unknown-mode fallback still selects `Default_card.jpg`.
- [x] Stats, More Stats, and Targets render valid `1180 × 640` PNGs for King of All Britain.
- [x] Existing target-publication rendering and warnings are unchanged.
- [x] No SQL, command, payload, permission, persistence, or registration change is included.
- [x] Focused tests and selected repository gates pass.
- [x] Local visual smoke artifacts are inspected and documented.
- [x] Changes reviews with Deep Off are completed against the mirror and production code/asset diffs.
- [x] Both PRs are created and handed back without merge or deployment.

### Completion Evidence

- Mirror delivery: PR `#244`; review-fix head `3f1760a3` before this documentation-only archive update.
- Production delivery: PR `#551`; review-fix head `4b1b4afa` before this documentation-only archive update.
- Asset contract: `856,548` bytes, `1180 × 640`, `RGB`, SHA-256
  `987be4495471936db491d25d00bb3eb9c23e259a86ed02d3e46b361fa3b6d605`.
- Renderer delivery: both local `MODE_BACKGROUNDS` maps use the exact normalized key and PNG;
  normalisation and mode → default → Tides fallback order are unchanged.
- Focused tests: `32 passed` across the Stats and Targets renderer test modules.
- Broader validation: architecture, deferred-item, security-routing, import-smoke,
  command-registration, Black, Ruff, and whitespace checks passed. One unrelated real-timeout test
  was transient during a full-suite run and passed immediately in isolation.
- Review comments: redundant test parentheses were removed and the exact asset SHA-256 contract was
  added in mirror commit `3f1760a3` and production commit `4b1b4afa`.
- Security: separate Codex Security `Changes` reviews with Deep Off completed with zero findings for
  mirror scan `4a04c229-8330-4505-a3b4-4de135fc3b7b` and production scan
  `09581aab-7a74-4d02-b46f-706f5d279697`.
- Final-head routing: the subsequent commits only update `README-DEV.md`, the archive index, and
  the completed task-pack Markdown through mechanical archive moves. Security review is therefore
  documented as skipped for that documentation-only delta: no executable code, SQL, configuration,
  dependency, deployment, permission, input, network, filesystem-runtime, or persistence behaviour
  changed after the completed code/asset scans.
- Local smoke artifacts retained at `smoke_artifacts/king_of_all_britain/` cover Stats, More Stats,
  active Targets, and exempt Targets; all are `1180 × 640` RGB PNGs.
- Operator smoke acceptance: Stats and Targets displayed the new backdrop correctly and were
  confirmed to look perfect. The local More Stats artifact also passed visual inspection.
- SQL and command surface: unchanged; no SQL deployment or Discord command resync is required.
- Deployment state: not merged or deployed by Codex. After the operator merges, deploy the bot code
  and asset together and restart the bot so the module-level maps reload.
- Deferred optimisations: none created; the known duplicate local mapping remains intentionally
  outside this narrow delivery.

## 16. Required Delivery Output

Return:

1. Summary
2. Branch and PR
3. File Manifest
4. Asset Verification
   - path
   - dimensions
   - mode
   - byte size
   - SHA-256
5. Renderer Mapping Changes
6. Tests Added or Updated
7. Commands Run and Results
8. Visual Smoke Artifact Paths and Inspection Notes
9. Security Review Decision and Evidence
10. SQL Changes
11. Command-Surface Changes
12. Restart / Deployment Steps
13. Post-Deployment Smoke Checklist
14. Risk and Rollback
15. Deferred Optimisations

### Deployment Handoff

No SQL deployment is required.

After the operator merges/promotes the bot PR:

1. Deploy the new bot version including the binary asset.
2. Restart the bot process so the module-level mapping is loaded.
3. Confirm the active KVK row resolves `KVK_NAME` as `King of All Britain`.
4. Run a representative player `/kvk targets` flow.
5. Run a representative player `/kvk stats` flow and inspect both Stats pages.
6. Confirm the King of All Britain background is used and all overlay text is readable.
7. Confirm an unrelated/unknown mode still uses the normal default fallback.

Rollback is a normal code/asset revert. Reverting this PR restores the previous default-background behaviour; no data rollback or SQL rollback is required.

## 17. PR Summary Template

```md
## Summary

- Added the text-free King of All Britain production card background.
- Routed both KVK Stats and KVK Targets cards to the new asset when the normalised KVK name is `king of all britain`.
- Preserved all existing layouts, outputs, fallbacks, commands, target-publication behaviour, and data contracts.

## Changes

- Added `assets/kvk/cards/King_of_All_Britain_Stats_Card.png`.
- Updated the Stats renderer mode mapping.
- Updated the Targets renderer mode mapping.
- Added focused mapping, asset-contract, render, and fallback regression coverage.

## Tests

- `<commands and results>`

## Visual Smoke

- `<artifact paths and inspection result>`

## Security Review

- Decision: `Changes review`
- Repository / target: `K98-bot-mirror origin/main...HEAD`
- Expected setup / execution: `Changes + Deep Off`
- Evidence: `<result or explicit no-finding evidence>`

## SQL / Command Surface

- SQL: none.
- Slash commands and registration: unchanged.

## Risk / Rollback

- Low-risk visual asset and mapping change.
- Roll back by reverting this PR; the prior default-background fallback will resume automatically after restart.

## Deferred Optimisations

- None, unless the implementation audit captures a genuinely new structured item.
```
