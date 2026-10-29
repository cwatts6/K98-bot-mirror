# P1 event-cache readiness release compatibility

## Scope and authority

The operator approved preparation of the release compatibility work on 25 October
2026 after feature mirror #441 and production #690 merged. Those PRs deliver the
feature; this follow-up supplies its exact installed-updater admission policy.
It does not deploy the bot, restart it, run SQL/provider operations, or change
activation settings. The operator performs installation and deployment after the
reviewed package and its machine prerequisites are confirmed.

The last verified runtime is private commit
`d127cb6e08aaecf0a397b9f5a3d41279280b245c`. The feature merged at private commit
`04b4124c`; the initial compatibility check correctly refused its changes to
`bot_instance.py` and `services/recovery_health.py`. A clean development checkout,
passing feature tests and the test-only historical hash bridge are not updater
installation authority.

## Architecture and exact boundary

Use the existing `event_cache_readiness_v1` registry entry and fixed member set
in `scripts/prepare_k98_update.py`. All ten reviewed feature runtime files are
pinned together, including the newly added service whose predecessor must be
absent. Both predecessor and successor images must match for every member. An
altered, missing, partially installed or foreign dependency fails closed.

The registry inventory cap increases from 40 to 41 for this single additional
entry; the 64 KiB registry and 16-member per-entry limits remain unchanged. The
other 40 entries are preserved. No generic path exemption, editable release
flag, new installer mechanism, or change to custody/ACL checks is introduced.
Registry and policy are selected from the installed updater, never from an
untrusted target tree. A new package must be installed before that policy can
admit the feature. Hashes use the established LF normalization; the actual source
plan continues to authenticate installed bytes separately.

The feature's services, scheduler, commands and persistent cache format are
unchanged by this follow-up. There are no SQL, dependencies, environment, startup
activation or provider changes. Existing packaging and exact-version upgrade
helpers are reused. Broader updater refactoring and diagnostics stay separately
scoped; no new general helper or duplicated deployment implementation is needed.

## Validation and security routing

Tests cover the current ten successor images, complete fixed membership, unknown
transition identity, each member's incorrect predecessor/successor, absence of the
new service at the predecessor, LF/CRLF forms, old installed policy/registry,
target-supplied exemption rejection and the bounded registry inventory. Existing
updater, release packaging, exact upgrade and historical-transition tests remain
required. Run full pytest with operational-log protection, architecture/deferred
validators, test selection, routing validation and pre-commit.

Security decision: Changes review, Deep off, separately bound to the final mirror
and production compatibility diffs. The changed security boundary is privileged
source admission. Review fixed membership, exact old/new hashes, installed-policy
selection, package integrity and preserved custody/drain/resume controls. No
standard or deep codebase audit is requested. Record final scans and CI receipts
in the PRs and retain package verification evidence locally.

## Package and operator sequence

1. Obtain fresh MINI_AMD machine/account/elevation/shell evidence, checkout commit
   and installed `C:\ProgramData\K98\S11\updater\update-tool.json`. Confirm any
   deployment since the retained 24 October runtime. Checkout HEAD alone does not
   prove loaded source; reconcile with the retained release evidence.
2. Validate and review both compatibility PRs, then merge mirror before private
   production. Do not push mirror history into the private repository.
3. Build with the existing `scripts.package_k98_update_tool --previous-manifest`
   mechanism, using the exact installed manifest bytes. Independently verify the
   embedded payload, old/new manifest pins and installer/upgrade hashes. Preserve
   the predecessor manifest and a package receipt. Building is not installation.
4. Confirm the source classifier refuses the old installed tool and admits the
   candidate only for the exact reviewed feature bundle. Recheck against the final
   private-main target; unreviewed later source changes require another assessment.
5. Supply the two generated scripts and independent hashes to the operator. On
   MINI_AMD, use elevated Windows PowerShell 5.1 under the reviewed deployment
   account, close other updater windows, and run the hash-verified generated
   `Upgrade-K98InstalledUpdater.ps1`. Do not run the fresh-install script directly
   over an installation with deployment history. The upgrade preserves the old
   updater and does not alter bot source, task, startup policy or SQL.
6. After upgrade verification, run the fixed installed `Update-K98.ps1`. It selects
   private production main and checks live custody, process/session and release
   prerequisites. Run `/ops graceful_restart` once only when prompted. Retain
   transcript, readiness status and final verified receipt.

If any pin, owner, inventory, active release or startup binding differs, stop and
retain the evidence. Do not edit the installed registry, weaken an ACL, delete a
control file, manually pull live source or repeat an uncertain operation. The
existing upgrade supports resumption of its exact old/new pair. A bot rollback is
a separately reviewed reverse release; retaining the old updater is not itself
permission to downgrade a running bot or its startup policy.

## Acceptance remains separate

After source/startup verification, check `/ops show_command_versions` and the
complete recovery report's `monitor.event_cache`, `monitor.event_startup` and
`monitor.event_dm_startup`. Check current task liveness separately from historical
registration. Observe loaded-empty readiness and deferred restoration only when
those conditions occur naturally; do not clear data to manufacture the case.
Unconfirmed restoration remains retained, with no replay.

The original-message safe callback check, exact Daily KVK Overview disposition,
all remaining WS1–WS6 obligations, and P0 natural eligible
rollover/final F01-F05 reconciliation remain open. Earlier accepted import/export
and visual evidence stays accepted and must not be repeated for deployment proof.
