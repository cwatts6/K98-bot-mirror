# P02 D5c restricted scope approval and preflight packet

The operator approved the bounded test-account scope on 2026-11-12: one new
`P02_D5c_Reader_20261112` login/user, three object SELECT grants, one positive
actual-reader case, one denied-read case and removal of the exact new principals.
The Rights Acceptance and Restricted Login Plan remains the authority boundary.
No existing login, mapping, role, permission, application record or setting may
be changed. No authentication-mode change, impersonation, restart or retry.

## Sequence refinement within the approved four-packet scope

1. **Read-only preflight (this packet):** obtain authentication mode, creation
   authority, proposed-name absence and inherited public/guest permissions.
2. Setup, only after the complete setup/read/denial/cleanup sequence is prepared,
   offline-tested, frozen and reviewed against the actual preflight findings.
3. One positive actual-reader case, followed by receipt adjudication.
4. One denied-read case and identity-checked cleanup in the same reviewed packet.
   Preserve the refusal/error evidence before removing the exact temporary user
   and login. Cleanup must also work after an earlier-stage failure, subject to
   identity and physical session-closure proof. No arbitrary deletion or kill.

Separating preflight avoids creating an account before the inherited privileges
are understood. Combining the final refusal and cleanup retains the maximum
four packets. The 180-second whole-scope budget remains cumulative, including
this read-only stage, with at least 45 seconds reserved for cleanup before either
reader is admitted. Each later packet remains at most 60 seconds and must fit
its actual remaining scope budget; four individual maxima are not additive
authorization. If time cannot support a reader plus cleanup, admit cleanup only.

The remaining three executable stages are not yet prepared or reviewed. This
first read-only handoff does not authorize setup before their complete review.
Any unresolved feasibility, authentication mode or budget issue stops setup.

## Exact read-only preflight

Derived from the accepted rights V2 collector. Preserve its 24 non-cache
observations and every SQL identity, physical closure, custody, original history,
permission fingerprint, paired poststate and resource check. Replace the three
old user-rights queries with three bounded metadata queries:

| Observation | Scope | Maximum rows |
| --- | --- | --- |
| restrictedPrerequisites | Existing authentication mode; current ALTER ANY LOGIN, ALTER ANY USER and CONTROL capability; exact proposed-name counts; public/guest role-membership counts; three required table object IDs | 1 |
| serverPublicPermissions | Full explicit server public-role permissions, including endpoint identity | 128 |
| databasePublicGuestPermissions | Full explicit copy public/guest permission rows, all classes, object/schema/column identity | 512 |

Public server role is resolved by exact name/type in sys.server_principals, not
by assuming a login lookup resolves a role. No password, password hash, connection
secret or retained-input contents are read. No TOP/pagination/JSON packing,
impersonation, new principal, grant/deny, actor launch or business call. Unknown,
missing or excessive metadata is not an access pass. The receipt must be
adjudicated; merely collecting it does not prove safe restricted authentication.

No runtime or authoritative SQL repository change. Catalog names follow the
already reviewed rights inventory; all three application objects were checked
against the authoritative SQL definitions in the approved scope review.

## Bounds and immutable evidence

Before this packet: **1,413 native seconds; 50 Windows-test seconds; 21 inputs
consumed; zero new inputs**. Scope allocation 180 seconds starts with this packet.
Final 1,000 native seconds remain reserved for later D5 slices. No isolation,
writer or maintenance retry. This stage consumes no Windows-test allocation.

27 metadata statements plus six reserved open/close/cancellation units = 33/48.
Planned maximum returned rows 776/2,048; per result at most 512. Existing
1 MiB receipt, 128 KiB manifest, disk/log/version-store and VM limits unchanged.
This stage narrows the whole-host ceiling to **45 seconds**: stop request at 30,
join reserve 10, receipt reserve 3; guest work admission stops at 20 and cleanup
admission at 32. No retries, forced settings changes or removal of uncertain jobs.

Original failed rights script/manifest/intent/receipt remain intact. The accepted
rights V2 receipt is an additional pinned lineage prerequisite. New create-only
intent refuses repeated attempts. Account creation is absent from this script.

## Validation and handoff gate

280 offline PowerShell checks passed: parser, preserved helpers and 24 observations,
expected state and lineage, exact metadata scopes, all public/guest classes and
column exceptions, changed deadlines, full command/row budget, no native effects,
one-shot intent and injected extra statement refusal. No Python actor or app
source changed; application tests, startup imports and command registration do
not exercise this read-only wrapper and are skipped. Repository validators and
explicit selector run before handoff. Complete a three-file frozen Changes scan,
Deep off, before native preflight. Later account/secret/reader executables need
their own complete review before setup; no current test result substitutes for it.

Script: `scripts/collect_p02_d5c_restricted_preflight.ps1`.
SHA256: `6cff925ba758b98315b7b3204aa34625f5b9b331d02daea5a209e92ce059ae68`.
Manifest: `.codex_artifacts/p025/d5c-restricted-preflight-execution-packet.json`.
SHA256: `0414819bbb38f229ab601ed800a717d36fbbe01f2fc9164283ca77380b22c7ff`.
Manifest bytes: 42,558. No native preflight or account setup has run.

The existing elevated PS5.1 console holding `$global:D5bReportSession` runs this
once after review. Return receipt path and whole host elapsed time. Stop on error
or incomplete output; cancel/report a hang before 45 seconds. Adjudicate the
receipt before any further native step. This is D5 qualification, not deployment.
