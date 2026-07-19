# GovernorOS v2 Phase 7–9 documentation bundle

Prepared against:

- Repository: `cwatts6/K98-bot-mirror`
- Pull request: `#228`
- Branch: `codex/player-self-service-phase6-stats`
- Reviewed head: `50c011b654ed51f316aea150df5339c0758cdb14`
- Date: `2026-07-18`

This bundle contains the agreed GovernorOS documentation update for the Phase 7 PR. It does not contain runtime or SQL implementation.

## Included new files

Copy these six Markdown files into `docs/task_packs/`:

1. `Codex Task Pack - Player Self-Service Command Centre v2 Phase 7 Visual Consistency Content Audit and Programme Closeout.md`
2. `Codex Chat Starter - Player Self-Service Command Centre v2 Phase 7 Visual Consistency Content Audit and Programme Closeout.md`
3. `Codex Task Pack - Player Self-Service Command Centre v2 Phase 8 Leadership Stats Player Modernisation Canonical Combat Metric Alignment and Player Profile Retirement.md`
4. `Codex Chat Starter - Player Self-Service Command Centre v2 Phase 8 Leadership Stats Player Modernisation Canonical Combat Metric Alignment and Player Profile Retirement.md`
5. `Codex Task Pack - Player Self-Service Command Centre v2 Phase 9 Leadership Stats Kingdom.md`
6. `Codex Chat Starter - Player Self-Service Command Centre v2 Phase 9 Leadership Stats Kingdom.md`

## Existing files updated by the helper

`apply_documentation_updates.py` updates:

- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- `docs/task_packs/README.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- `docs/player_self_service_command_centre_briefing.md`

The updater also copies the six task packs/starters into `docs/task_packs/`.

## Apply to a local checkout

From the extracted bundle directory:

```powershell
.\.venv\Scripts\python.exe .\apply_documentation_updates.py C:\path\to\K98-bot-mirror
```

Or, from the repository root after copying the bundle contents somewhere accessible:

```powershell
python C:\path\to\governoros_phase7_9_docs_bundle\apply_documentation_updates.py .
```

The helper is fail-closed: it checks the expected Phase 6 headings and text before replacing them. If the branch changed after the reviewed head, it exits at the first unmatched section rather than making an uncertain edit.

## Review the result

```powershell
git status --short
git diff --check
git diff -- docs/task_packs docs/reference docs/player_self_service_command_centre_briefing.md
```

Expected documentation result:

- The former proposed `/me history` Phase 7 is recorded as a closed product-placement decision with no build.
- New Phase 7 is `/me` Visual Consistency, Content Audit and Programme Closeout.
- Phase 8 modernises `/stats player`, globally aligns canonical Tanking Score, and retires `/player_profile` with no redirect.
- Phase 9 adds private `/stats kingdom`.
- Later roadmap becomes Phase 10 Usage-Led Migration Review and Phase 11 Future Sticky Player Features.
- Current runtime baseline remains `37 top-level / 100 grouped / 8 /me / 2 /inventory` through Phase 7.
- Approved future target after Phase 8 is `36 top-level / 100 grouped / 8 /me / 1 /stats / 2 /inventory`.
- Approved future target after Phase 9 is `36 top-level / 101 grouped / 8 /me / 2 /stats / 2 /inventory`.

## Documentation validation

Because this is a documentation-preparation change, run the repository’s documentation/governance gates after applying it:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe -m pre_commit run -a
```

The task packs intentionally require audit and approval stops before implementation. Adding the Phase 8 and Phase 9 packs to the Phase 7 PR does not approve their runtime implementation.
