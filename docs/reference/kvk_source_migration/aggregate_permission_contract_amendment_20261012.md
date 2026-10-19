# Aggregate permission-contract amendment for review

This is the bounded configuration specification for the companion SQL amendment
`deploy/amendments/20261012_aggregate_row_permissions.sql`. No live contract,
credential, production identifier binding or activation flag is changed by this PR.
Actual installation fingerprints must be calculated from the existing protected
contract and its verified observations; placeholders are not valid startup pins.

## Exact source change

The application grant-plan digest changes from
`e705339565527bd7ce631eef12dc815f7450cb69119344a3c999ab2825a9b2fd`
to `414ffbd0196d614c4269009ca2b9003f5b9338bcf80662d937b67185740c726e`.
Only INSERT and SELECT on `KVK.SourceKingdomReportRow` and
`KVK.SourceCampReportRow` are added. The table source SHA256 values are respectively
`118d376b466526b4d23aa47f46a4da045a2113380e331d3af96d27f4c41e03b0` and
`d61535898aebf2733687b0caa58c68abab3bce4cf2d3409bcd7bc22a27e01cfe`.
The pinned direct source manifest, schema source manifest, activation scope,
migration identities/checksums and module definitions remain unchanged.

## Reviewable expected observation delta

Before the outage, retain the protected bot startup configuration and complete
legacy/application observations from the real application identity. Validate both
using the currently installed version's normal verifiers. Their hashes must match
the existing approved pins before deriving any new expectation. Never reseal a
drifted or incomplete observation just to make startup pass.

Derive the expected postimage offline from that verified baseline:

1. `legacy_installation_snapshot.application_grants`: add exactly four rows,
   with DatabaseName `ROK_TRACKER`, SecurableClass `OBJECT`, TargetName one of the
   two row tables, PermissionName `INSERT` or `SELECT`, GrantState `G` and
   ColumnName null. Preserve the snapshot query's ordering. Every other legacy
   observation is identical, including migration receipts, roles and capabilities.
2. `application_snapshot_for_contract.object_permissions`: add only the effective
   INSERT/SELECT rows for those tables, including the SELECT column subentities
   returned by `sys.fn_my_permissions` for the exact source-backed column names.
   SQL Server can also expose derived effective permissions (for example
   VIEW DEFINITION); derive and independently review these using disposable SQL
   with the same baseline grants. Do not assume the effective list equals the
   four direct catalog rows. Unexpected effective changes block the release.
3. `application_snapshot_for_contract.column_permissions`: only SELECT changes
   from 0 to 1 for source-backed columns of those two tables. UPDATE and REFERENCES
   are unchanged. Compare the complete lists, not only changed rows.
4. Whole-application metadata and schema permissions remain byte-equivalent
   under the canonical encoder. Use the existing contract version and
   `application_contract_scope`; do not widen or narrow the reviewed scope.

The startup configuration field amendment is restricted to:

| Field | Reviewed replacement |
| --- | --- |
| `bot.legacy_sql_contract.metadata_hash` | `digest(expected_legacy_snapshot).hex()` |
| `bot.application_sql_contract.permissions_hash` | `digest({schema_permissions, object_permissions, column_permissions}).hex()` from the expected application snapshot |
| `bot.application_sql_contract.review_id` | New canonical UUID identifying this independent review |

Here `bot` means the existing bot section of the protected startup specification,
not an instruction to create a new schema. Retain the original container shape.
`application_sql_contract.metadata_hash`, identity/SID, source manifests,
`legacy_sql_contract.migration_hash`, optional module/outcome amendments,
fixed `sql_contract`, host policy, credentials and activation settings are unchanged.
If additional fields need to change, this specification is insufficient: stop and
review the additional delta explicitly.

Use the repository's canonical `digest`, not a hash of pretty-printed JSON.
Run `verify_legacy_installation_contract(..., profile='application')` and
`verify_application_installation_contract` on the expected postimages and candidate
contracts using the new source. Independently review the complete baseline,
expected postimages and three-field configuration diff before approval. During the
authorized outage, compare actual post-amendment observations to those postimages
and rerun both verifiers. An observation is evidence, never automatic authority to
replace a pin. The fixed coordination SQL contract must also still pass.

## Deployment gate and recovery

This changes a protected source constant and installed permissions. Package it as
a reviewed generic configuration/SQL release via `prepare_k98_release.py` and
`Deploy-K98Release.ps1`, not a source-only normal updater run. Bind the final merged
private-main bot commit, SQL commit and script checksum, actual identity, old/new
contract hashes and installed policy/interpreter pins in the private packet.
Do not bypass normal updater compatibility checks or edit a live seed in place.

Order: drain old pair; execute the identity-bound grant amendment; install the
promoted source; install the approved startup specification/seed; start once;
verify readiness and all SQL contracts. Any failure keeps the application stopped
until recovery is reviewed. Roll back source, grants and protected contracts
together while drained, retaining all business data and receipt/artifact history.
The retained receipt needs a fresh operator-reviewed confirmation after readiness.

This PR is review-ready preparation. Deployment remains gated on review completion,
the private identity-bound release packet and explicit production approval.
