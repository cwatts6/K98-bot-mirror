# Installed verifier bootstrap - 31 October 2026

## Problem and resulting behaviour

The installed updater needs the reviewed portable schema comparators before it
installs new application source. Importing those comparators from the predecessor
checkout cannot supply the new implementation. A deterministic installed
`contract_verifier.zip` now carries the fixed 34 services/kvk/resource members.
Preparation, pair verification and recovery select that authenticated archive
before application imports. Missing, changed, ambiguous or preloaded modules fail
closed. No archive is extracted and no conflicting module is silently replaced.

The archive does not contain `core`, root configuration, credentials or arbitrary
target source. Configuration and the real TLS connector remain rooted in the
authenticated application checkout. This is a verifier bootstrap change, not the
portable contract transition itself or permission to deploy.

## Scope and architecture

Operational ownership remains in `scripts/`. The existing installed
`verify_k98_update_pair.py` supplies the deterministic builder, bounded validator
and import selector. Packaging adds one flat binary member; installation and
upgrade retain administrative custody and exact supported inventories. Historical
complete inventories remain valid upgrade predecessors. The read-only compatibility
checker reports a required upgrade for an absent or different archive.

`Update-K98.ps1` authenticates the installed manifest and all tool members, then
binds the archive digest into its protected observation and passes the observation
digest to isolated Python. The preparer authenticates the observation and installed
verifier before its transitive core/services imports. Generated releases retain
the same archive in their sealed member inventory and immutable bindings.

Pair verification first authenticates the complete predecessor or successor source
with the existing bootstrap, then activates the sealed archive. Recovery first
authenticates target source in the native adapter, then loads the hash-bound sibling
`Verify-NewPair.py` and archive. Derived recovery bindings preserve operational
fields and use the original release directory for executable members.

The native adapter rechecks custody, hashes and a 2 MiB limit before each archive
consumer. Python enforces the same size bound, exact case-sensitive ordered names,
stored compression, bounded expanded size and canonical archive bytes. Archive
imports rely on retained administrative custody; this is not a sandbox against an
administrator who can replace trusted code. The application identity must not be
able to write the trusted archive or its ancestry.

## SQL, configuration and persistence

SQL text, result shapes, principal rights, fingerprints, migration order and the
old exact `mge_finalisation_v1` transition are unchanged. This packages the existing
SQL readers previously checked against the authoritative SQL repository and
exercised in the isolated Q/R native receipts. No SQL repository edit is needed.
The real configured-connection import path passed all 41 queries and three
contracts with the normal 15-second statement limit; login disablement and zero
VM adapters were confirmed. Those receipts qualify the comparator source, not
this new installed bootstrap or a combined updater run.

Credentials are never added to tool/release payloads. Production dotenv-file
loading, exact installed predecessor bindings and the separate portable-format
transition still require release validation. Root configuration import behaviour
is preserved. Startup, drain, durable intents, uncertain-outcome refusal and
single-start semantics are unchanged.

## Review and validation

Security routing: **Changes**, Deep off, exact Bot branch diff against its base.
Review archive authority, privileged imports, manifest/custody boundaries and
recovery consumers. No repository-wide or SQL repository scan is implied.

Focused checks cover deterministic source bytes; missing, modified, duplicate,
case-alias, traversal, compressed and oversized archives; loaded-module conflicts;
actual isolated preparer imports; complete sealed recovery selection; source-before-
archive-before-SQL ordering; Windows PowerShell 5.1 parsing and real inventory/hash
gate execution; historical complete upgrade inventories; and unchanged seed
recovery/resumption behaviour. Native ACLs are mocked in the new gate unit test;
the lab rehearsal must prove actual custody separately.

The three package tests now stage the actual installer payload instead of treating
a source directory as an installed tool. Eleven historical transition fixtures
also bind the real archive when representing the candidate installed inventory;
old-policy and old-registry rejection assertions remain unchanged. No test-only
runtime fallback was added.
Run focused/full pytest with operational-log isolation, architecture/deferred/
security-routing validation, test selection, smoke imports, registration, pre-commit
and exact source review before promotion. Record exact results in the review/PR.

No command/view, provider, cache behaviour or new SQL object changes. The archive
reuses existing comparator code; no new business logic or duplicate SQL reader is
introduced. No unrelated refactor or deferred optimisation is required.

## Remaining release gates

1. Finish exact code review, validation and equivalent private promotion.
2. Retain the completed isolated S selector/protected-configuration qualification:
   all 41 queries and three contracts passed at 15 seconds; actual native custody,
   owned configuration-file removal, disabled login and zero VM adapters confirmed.
   S exercised the selector function with authenticated staged source; complete
   installed CLI and combined updater execution remain separate requirements.
3. Complete the separately declared portable contract transition. Keep production
   predecessor evidence distinct from the rebuilt lab schema.
4. Qualify the combined updater, recovery and rollback paths; bind exact release
   source/tool/SQL/backup identities and acceptance checks.
5. Obtain separate production deployment approval against the finished packet.

Production deployment remains unapproved. No installation, SQL write, process
restart or production operation follows from this source change or its merge.
