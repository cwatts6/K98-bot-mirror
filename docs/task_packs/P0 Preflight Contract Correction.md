# P0 preflight contract correction

## Scope and incident

The coordinated P0 release stopped during preparation, before drain. The installed
updater was upgraded, but no active update was registered and neither new P0
migration had a history entry in the operator's subsequent read-only diagnostic.
The running bot remains on its predecessor; merged code is not deployed code.

The two live procedure bodies match the authoritative SQL source at
`716c74ebbced800de8243892a7bce6a5ebac380c` and are already accepted by the pinned
P0 migration. The rehearsal metadata used a mis-encoded comment in
`dbo.UPDATE_ALL2` and omitted existing object-level grants:

| Procedure | Existing grantee | Permission |
|---|---|---|
| `dbo.UPDATE_ALL2` | `SHEETS_USER` | EXECUTE |
| `dbo.usp_update_stats` | `SHEETS_USER` | EXECUTE |
| `dbo.usp_update_stats` | `ImportProcUser` | EXECUTE |

The source exports do not independently document these three grants. Their
existence is established by the bounded operator capture. This correction
preserves these specific existing rights; it does not grant new production
rights or generalise acceptance to arbitrary permissions.

## Correction boundary

Only the two before/after image pairs in `scripts/p0a_release_spec.json` change.
The corrected starting definitions are reconstructed from reviewed SQL source,
and the three captured grants are explicitly installed in a fresh local clone.
All eleven images are checked. Expected final images are derived from the already
qualified postimages plus those same retained grants, then checked against the
actual migration result. Observed production hashes are not a runtime fallback.

The SQL payload remains `db18f23730521a41a215b744957cd61002eedf8d`; migration and
application source bytes, startup contract expectations, writer exclusion,
transaction boundaries and recovery semantics are unchanged. No SQL PR is needed
for this correction. Mirror and private release-policy changes require their own
final Changes reviews. Deep scan is off.

The protected updater bundles the release specification. A replacement updater
package must therefore recognise the successfully installed r6 updater as its
predecessor. The operator must not edit the failed packet, substitute hashes,
rerun imports or apply the migration manually.

## Regression and qualification requirements

`tests/test_p0_completion_preimages_sql.py` requires an explicitly prepared
`K98_P0_Completion_<12 hex>` database on local K98DEV. It refuses other targets
before mutation. The regression exercises the actual pinned PowerShell SQL
adapter and checks:

- The original profile reproduces both preflight refusals without applying SQL.
- Corrected preimages pass; an extra grant, removed grant or changed definition
  still refuses before migration.
- Apply and Verify retain all three existing grants and match exact postimages.
- Repeated Apply verifies existing receipts without rewriting them.
- A missing retained grant after application fails postimage verification.

Run release-policy/updater tests and the repository architecture, deferred-item,
security-routing and test-selection gates. Requalify the replacement package and
its upgrade from r6; retain earlier successful application and recovery tests with
their original provenance rather than claiming new full-suite production proof.

## Operator handoff boundary

Implementation, package qualification and deployment remain separate. Nothing in
this document approves bypassing preflight or establishes live deployment success.
After the corrective mirror/private PRs are reviewed and the operator merges them,
use the replacement updater package and the normal protected updater workflow.
The failed preparation is retained historical evidence, not an active release to
resume. Request one graceful restart only when the updater prompts after preflight.

Preserve all F01-F05 production acceptance obligations. Do not repeat the accepted
715-second / 132-request publication check or the verified 415-row cache build.
Keep the full P1 programme next, including unconfirmed tracked-view restoration.
