# Telemetry Commands Full Optimisation & Standardisation — Codex Task Pack

## Objective

Perform a full audit, optimisation, standardisation, and architectural cleanup of the telemetry command subsystem centred around:

* `commands/telemetry_cmds.py`

This is **not** a narrow file cleanup.

This task must:

* Resolve all telemetry-related GitHub issues.
* Resolve all telemetry-related deferred optimisations.
* Audit repo-wide consistency with the newer service-alignment and registry-service architecture introduced in recent PRs.
* Ensure telemetry functionality conforms to current K98 architecture standards.
* Remove remaining legacy patterns.
* Standardise telemetry flows against modern command/service/view separation principles.

---

# Required Reading (MANDATORY)

Before starting, read and follow:

* `docs/K98 Bot — Deferred Optimisation Framework.md`
* `docs/deferred_optimisations.md`
* `docs/K98 Bot — Testing Standards.md`
* `README-DEV.md`

Also review:

* Recent registry/service-alignment PRs
* Existing registry architecture:

  * `registry/registry_service.py`
  * `registry/dal/registry_dal.py`
  * `registry/registry_cache.py`

---

# Scope

## Primary Target

* `commands/telemetry_cmds.py`

## Secondary Audit Targets

The following areas must be reviewed for consistency/alignment impacts:

* `commands/registry_cmds.py`
* `mge/mge_signup_service.py`
* `ark/registration_flow.py`
* Registry/cache/service layers
* Related views and helpers
* Related tests

---

# GitHub Issues To Resolve

Minimum required closure targets:

* Issue #26 — telemetry_cmds SQL usage
* Issue #33 — Command Layer SQL Separation Pack (telemetry scope)
* Issue #47 — restart-safe governor session locking

## IMPORTANT

Do **not** assume these are the only relevant issues.

You must:

* Audit the full issue list.
* Identify any additional telemetry-, registry-, command-, interaction-, or service-alignment-related issues.
* Either:

  * resolve them within this task, or
  * explicitly document why they remain deferred.

No hidden telemetry debt should remain after completion.

---

# Deferred Optimisation Review Requirement

You must fully review:

* `docs/deferred_optimisations.md`

Do not limit review to explicitly named telemetry entries.

Identify:

* telemetry-related items,
* command-layer architecture items,
* registry consistency items,
* interaction safety items,
* command/service separation items,
* restart-safety items,
* cache consistency items,
* duplicated workflow/view patterns.

Any applicable items must either:

* be resolved,
* superseded,
* merged into this task,
* or documented with explicit rationale.

---

# Architectural Goals

Telemetry commands must conform to current architecture standards.

## Required Principles

### 1. Thin Command Layer

Commands should:

* validate inputs,
* defer/respond safely,
* invoke services,
* render views/embeds.

Commands should **NOT**:

* contain SQL logic,
* parse registry internals,
* contain DAL access,
* manage locking directly,
* duplicate account resolution logic,
* perform business orchestration.

---

### 2. Service Alignment

Telemetry flows must align with:

* registry service patterns,
* MGE service separation patterns,
* Ark registration patterns,
* modern async helper patterns.

Avoid:

* bespoke telemetry-only lookup implementations,
* dict-shape registry parsing,
* duplicated registry traversal,
* direct `load_registry()` usage in command handlers.

---

### 3. Restart-Safe Session Handling

Current:

* `_ACTIVE_GOV_SESSIONS`
* in-memory locking
* restart unsafe

Must be replaced with:

* reusable lock service,
* UTC-safe expiry handling,
* cleanup support,
* test coverage.

Preferred:

* DAL/service-backed implementation,
* reusable beyond telemetry,
* compatible with future inventory locking architecture.

---

### 4. Standardised Interaction Safety

Review and standardise:

* defer patterns,
* followup patterns,
* edit_original_response usage,
* exception handling,
* ephemeral handling,
* safe response helpers.

Reduce:

* duplicated interaction logic,
* silent exception swallowing,
* inconsistent followup/edit patterns.

---

### 5. Registry Consistency

Telemetry flows must use the same canonical account/governor resolution patterns used elsewhere in the repo.

Audit for:

* direct `.get("accounts")`
* direct registry dict traversal
* duplicated account extraction
* duplicated governor resolution logic

---

# Expected Refactor Direction

Likely target structure (adapt as appropriate):

```text
commands/
  telemetry_cmds.py                # thin registration wrapper only
  kvk_targets_cmds.py
  governor_lookup_cmds.py
  player_profile_cmds.py
  crystaltech_cmds.py

services/
  governor_account_service.py
  governor_session_lock_service.py
  player_profile_post_service.py
  telemetry_interaction_service.py
```

You may adjust structure if a better standardised architecture emerges.

---

# Mandatory Repo-Wide Audit

Before implementation, perform repo-wide grep/search review for:

```text
load_registry(
registry.get(
["accounts"]
.get("accounts")
_ACTIVE_GOV_SESSIONS
_session_claim
_session_refresh
_session_release
resolve_current_kvk_no_from_cursor
asyncio.to_thread(load_registry)
interaction.response.is_done()
except Exception:
except Exception: pass
```

Also compare against:

* registry service usage,
* MGE patterns,
* Ark patterns,
* interaction safety helpers.

Document:

* what was found,
* what was standardised,
* what intentionally remains.

---

# Behaviour Preservation Requirements

The following commands must remain functionally intact:

* `/ping`
* `/mykvktargets`
* `/mygovernorid`
* `/player_profile`
* `/mykvkcrystaltech`

Existing:

* embeds,
* views,
* permissions,
* account-selection flows,
* ephemeral/public behaviour,
* autocomplete,
* CrystalTech setup/progress UX

must remain working unless explicitly improved.

---

# Testing Requirements

Minimum required tests:

## Command Registration

* telemetry commands still register correctly

## Registry/Account Selection

* no-account path
* single-account path
* multi-account path

## Governor Lookup

* exact match
* fuzzy match
* not found

## Player Profile

* permission gating
* allowed-channel gating
* safe interaction handling

## CrystalTech

* account selection
* lock acquisition/release
* restart-safe behaviour

## Lock Service

* expiry
* contention
* cleanup
* UTC handling

## Safety

* interaction defer/followup consistency
* no double-response exceptions

---

# Cleanup Requirements

Remove or review:

* unused imports
* shadow-guard debug code
* duplicated helpers
* nested helper sprawl
* broad silent exception handling
* legacy compatibility exports that are no longer required

---

# Deliverables

## Code

* fully refactored telemetry subsystem
* standardised services/views/helpers
* restart-safe lock service
* repo-wide consistency updates

## Tests

* new/refactored tests
* updated smoke tests

## Documentation

* updated deferred optimisations
* issue closures/comments where appropriate
* architecture notes if required

---

# Acceptance Criteria

Task is complete only if:

* telemetry-related GitHub issues are resolved or explicitly justified,
* telemetry-related deferred optimisations are resolved or explicitly justified,
* no direct SQL remains in telemetry command handlers,
* registry access patterns are standardised,
* session locking is restart-safe,
* command layers are thin,
* behaviour remains stable,
* tests pass,
* repo-wide consistency audit completed,
* telemetry subsystem matches current K98 architecture standards.

---

# STOP RULE

After Phase 0 audit and repo-wide analysis:

STOP and provide:

* findings,
* proposed file move map,
* identified issues/deferred items,
* architecture plan,
* risk areas,
* test impact assessment.

Do not begin implementation until review/approval.
