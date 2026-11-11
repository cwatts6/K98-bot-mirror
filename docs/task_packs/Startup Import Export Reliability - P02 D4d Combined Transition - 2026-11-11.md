> **Active release reference:** PR740 is merged, not deployed. This fixed combined-transition contract remains needed for D5/D6. Use the [D5 scope](Startup%20Import%20Export%20Reliability%20-%20P02%20D5%20Scope%20and%20Handover%20-%202026-11-11.md) for current authority and qualification; earlier source-preparation status below is historical.

# P02 D4d combined transition

The candidate joins the installed Phase 1 Bot, D2/D3 source and the D4 SQL package
through the existing combined updater. Source qualification and review are
complete in mirror PR532; the [D4 delivery and D5 handoff](Startup%20Import%20Export%20Reliability%20-%20P02%20D4%20Delivery%20and%20D5%20Handoff%20-%202026-11-11.md)
records final validation and remaining owners. This document does not authorize
installation, restart or recovery. D5 and the separate D6 release decision remain required.

## Fixed inputs and behaviour

The descriptor accepts only installed Bot
`97abcce1b2a9e71b3959eff74525c57930a703e6`, SQL main commit
`ba5c6acbefba0eb89cb18842a7f6c6811096759b`, migration
`20261111_001_p02_d4_combined`, and profile `p02_d4_v1`. The exact profile hash is
`57944777e50b7dc9200220cfcc2ce767edb22a2e0972e02bc2cd6f04e23e8171`; the SQL batch is
`8c0c99d92c14cac6da6e22076a5620927bac4c8af3deaa50950d66062381a8dc`.
The containing reviewed private Bot commit supplies the final target. It is not
selected from mirror main at deployment time.

The existing installed updater cannot admit this combined jump. The existing
exact-version package builder binds its replacement to the inventoried installed
manifest; the replacement retains the old package and resumes interrupted staging
or replacement. After separately authorized replacement, normal PrepareOnly and
the combined runner remain the route. There is no alternate launcher or direct
SQL-install shortcut. An active release or deployment request blocks replacement.

The registry has one new indivisible 79-member transition, including unchanged
dependencies, over the real installed predecessor. All 88 historical entries are
preserved exactly as parsed data. The entry allowance rises from 88 to 89;
formatting keeps both LF and Windows CRLF forms below the unchanged 232448-byte
bound. This is a bounded extension, not a registry redesign. Updater-tool copies
remain independently authenticated by the installed package manifest.

The three protected startup contracts move together. Coordination remains byte
identical. Legacy and application contracts require both their retained Phase 1
marker and the explicit D4 marker; unknown or missing lineage refuses. The legacy
closure grows from 44 to 64 modules, application sources from 574 to 591, and
activation scope adds the 17 new objects. The added legacy root is an already
explicitly granted queue-acknowledgement procedure; no new EXECUTE grant or
maintenance-child root is introduced. The three retired entry points have no
old-body compatibility exception. Historical direct and signed profiles remain
supported under their original selectors and fingerprints.

Expected successor fingerprints were derived from the verified installed
predecessor and actual native D4 schema changes. SQL's effective permission row
ordering is preserved. No live observation is adopted as an expected hash and no
grant is added to make verification pass. The legacy reader additionally requires
the exact D4 Applied receipt while retaining all prior required receipts.

## Installation order and recovery boundary

1. D5 qualifies the complete reviewed tuple. D6 obtains separate release approval
   and fresh host identity, source/updater/seed and changed-ancestor custody evidence.
2. The reviewed exact-version updater replacement retains its predecessor. Normal
   preparation verifies the complete source family, fixed SQL inputs, three old
   contracts and dependency closure before requesting drain.
3. Verified drain and physical issuer/worker exit precede SQL. All old and new
   producers/consumers must be stopped; the installed guards cannot revoke a call
   already admitted by the old code.
4. The SQL runner verifies fixed dependencies and resources, applies the single
   transaction and records its durable outcome. Source and all startup contracts
   then move together before the successor is started and verified.
5. Before SQL commit, a failed transaction rolls back. After commit, use the same
   release's verified outcome and continue remaining stages without SQL replay.
   Missing, foreign, partial or contradictory evidence stops. Do not run the old
   Bot against the new ledgers or restore an old policy to bypass startup checks.

SQL PR154's package preserves old captures, unknown claims, historical backup rows
and sequence state. It neither reverses Phase 1 numbers nor adopts old work into
new ledgers. Forward recovery after committed D4 keeps those boundaries.

## Validation

The offline private receipt rehearsal authenticates all 841 installed source pins,
the actual installed 14-member updater inventory, the complete candidate source
delta, all three before/after startup contracts and the seven-file SQL payload.
It proves that the old policy refuses the transition and that the candidate policy
admits it after exact updater replacement. Missing/altered unchanged peers, an
omitted changed member, stale descriptor and foreign installed-tool bytes refuse.
Private-only production paths are preserved by the promotion overlay.

Public tests cover explicit contract selection, permission and dependency closure,
source-only/partial/foreign adoption refusal, descriptor generation, historical
registry custody and packaged verifier resources. Historical assertions first
authenticate the D4 successor before comparing immutable earlier hashes; this
test bridge never authorizes installation.

Windows PowerShell 5.1 checks passed: 30 updater-replacement cases, 11 release
orchestration cases and 39 source-custody cases. They exercise native atomic writes,
handles, Git and interrupted/resumed replacement in isolated fixtures. Task/control
guards and administrative ACL creation are substituted where stated by the tests;
these results are not an elevated MINI_AMD rehearsal or actual host custody proof.
The SQL companion separately passed native full-batch rollback/commit/outcome and
dependency-refusal tests and its 19 PowerShell 5.1 package-reader checks.

Final test totals, exact-head review, security Changes review and CI are recorded
in the delivery PR. Production promotion requires those gates and retains private
workflows; the production PR stops at merge-ready under the current authorization.

## Installed caller and permission closure

The bounded MINI_AMD read-only follow-up found no remaining scheduled/internal
caller of UPDATE_ALL, UPDATE_RALLY_DATA or TEST within the examined source,
database and task scope. The backup-pruning step is filesystem-only. This combines
with the operator's no-manual/external-use statement and conditional retirement
approval. SQL PR153 retains their definitions and data but installs clear refusing
stubs in the future D4 release. UPDATE_ALL2 and the separate Rally importer remain.
Arbitrary future/ad-hoc callers cannot be disproved by an inventory.

The configured operational and import identities were checked through their actual
SQL login contexts for the required server/database diagnostic visibility and
wrapper execution. The S11 application profile retains its narrower reviewed
rights. The wrapper's owner context, fixed enabled job and msdb owner capability
were inspected without dispatch. The release binds their observed dependencies;
the backup route refuses hidden/denied/ambiguous metadata before dispatch and never
falls back after an uncertain request. A requested backup is not a completed one.

Maintenance's operational factory uses the existing SQL_USERNAME configuration;
the separate backup dispatcher selects SQL_MONITOR_USERNAME, then IMPORT_USERNAME,
then SQL_USERNAME. IMPORT_SQL_USERNAME is a different setting used by the import
factory. No selector was silently renamed or broadened. File observations do not
prove the running process's inherited environment: D6 must recheck effective
selection and host custody at release time. Unknown or denied configurations must
be investigated, not repaired by broad grants or profile fallback. Restricted
holder diagnostics remain optional evidence and never erase the original refusal.

D4 adds no business-input allowance, provider execution or backup-schedule change.
The consumed 21-input allowance, RCSI-off decision, SQL 3961 failed evidence and
P03/P04 prerequisites remain in the D5 handoff.
