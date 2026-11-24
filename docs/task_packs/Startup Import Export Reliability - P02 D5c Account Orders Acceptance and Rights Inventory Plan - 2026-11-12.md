# P02 D5c account orders acceptance and rights inventory plan

## Accepted result

Reader-first receipt `d5c-account-reader-first-result-09fde79daba54d0bbd36d74b92f5bbef.json`
has verified SHA256 `a20eeccdbd1e04b6a03e2091619fec8782908521029b15cddb8c942c4141d58b`.
Saved evidence confirms the preparation fetch precedes one exact account-holder
acquisition on a distinct SQL connection; remaining reads complete, the holder
stays exclusive after reader closure, and all connections/process cleanup pass.
Original protected records, permissions, definitions and failure history remain
unchanged. Both target-data account orders are accepted; full inspector paths
are not inferred from these tests. Receipt is 25,367 bytes, 48 reserved command
units and 109 rows. Host 1.8539983 seconds debits two: **1,415 native seconds and
50 Windows-test seconds remain, 21 inputs consumed, zero new inputs.**

The immutable acceptance is `d5c-account-reader-first-acceptance.json`. No isolation,
writer, maintenance or completed account-case replay is available. D5c/d/e/f and
D6 release remain distinct from these accepted cases.

## Next scope: read-only C09 feasibility

The existing observer is a lab administrator. Earlier inventory found four SQL
database users with no mapped server login. Their existence does not establish
an authenticated restricted factory or prove permission-failure behavior. Before
proposing any exception, collect only their existing identities, inherited roles
and relevant explicit rights. This is within the existing read-only preparation
approval and changes no principal, permission, ownership or session identity.

Three fixed catalog queries add to all 30 original preservation observations:

| Query | Fixed scope | Row cap |
| --- | --- | --- |
| Principal mapping | SHEETS_USER, rok_user, ImportProcUser, S11_ExportApplication; SID/login mapping, disabled state and observer impersonation capability as metadata only | 4 |
| Role membership | Those four users, transitive database roles and public; recursion ceiling 16 | 128 |
| Relevant permissions | Those users/roles, database/schema grants or denies, and object/column entries for seven configuration/execution tables | 512 |

The exact objects are ExportPreparation, ExportPreparationResource, ExportResource,
ExportExecutionSession, ExportExecutionStream, ExportProviderRequest and
ExportProviderRequestEvent. This inventory reads system catalogs only, no table
payload, credential, password hash or external service. It returns full bounded
rows, without TOP, paging or packed row sets. Overflow or recursion error stops;
no automatic split, retry or cap increase. Public and fixed-role membership is
retained because explicit permission rows alone do not describe effective rights.
Missing mappings, absent entries or insufficient visibility remain unknown/gaps,
not proof of authenticated access or safe denial. No EXECUTE AS is performed.

## Implementation and bounds

Reuse the accepted catalog-poststate collector, all 30 SQL observations and
protected expectations, adding only these three metadata statements. Carry the
later reviewed cumulative cancellation accounting and unresolved configuration/
isolation custody gates. No actor process or Python runs in the guest. Existing
host deadline/runspace and physical SQL closure checks are preserved.

33 queries plus six connection/cancellation units = **39/48**; maximum planned
rows **815/2,048**, per-command maximum 512, receipt 1 MiB, manifest 128 KiB,
three-second query timeout, whole packet 60 host seconds. Extra cancellation
attempts are charged against the same 48 ceiling. Windows-test allowance is not
used. Resource floors, exact host/VM/copy/session bindings, original database
protection and consumed-input allowance remain unchanged. New intent prevents
repeat; the accepted reader-first receipt is pinned in the lineage.

No production source or authoritative SQL repository files change. Built-in
catalog names and ownership/permission conventions follow the existing observed
inventory and accepted collector. No application table structure is guessed.
The next decision after receipt adjudication is whether a restricted test can use
an existing suitable path. Any account creation, grant or impersonation still
requires a concrete separately approved exception. No such action is authorized
by this metadata packet.

## Validation and review

318 offline PowerShell checks passed: parser, original 30 query/parameter/row-cap
bindings, old expected state/history/deadlines, reviewed cancellation helper,
exact principal/object scopes, role/public inclusion, recursion and row caps,
no mutation/impersonation/process launch, receipt lineage, source/manifest hashes,
full command reservation and injected extra-statement refusal.

No runtime Python test applies; no Python actor is introduced. Broad pytest,
application startup imports, command registration and release/permission-repair
suites are skipped for this read-only operational packet. Run architecture,
deferred/security-routing and explicit test selection plus whitespace checks.
An immutable three-file Changes review, Deep off, is mandatory before handoff.
No unrelated refactor or deferred optimisation item is introduced.

Wrapper `scripts/collect_p02_d5c_rights_inventory.ps1` SHA256:
`ab4d1f3ec15a6fce62a9cceea669194c05a2c33fd6d9f32070edf32a6863b580`.
Manifest `.codex_artifacts/p025/d5c-rights-inventory-execution-packet.json` SHA256:
`d77760b52ca70b17f39c4208bcd65e557da43a232c5a19fa28ca2c64a9ee0d1c`.
Manifest is 50,393 bytes. No native attempt has run.
