# P0 recovery receipt roundtrip correction

## Scope and cause

The updater correction allowed retained terminal containment through deployment
preflight. It did not exercise the full operator recovery sequence. Two remaining
application checks rejected valid retained history: ODBC uniqueidentifier strings
could differ in case from canonical private receipt IDs, and the configuration
read snapshot included an unrelated target-contained stream as a live conflict.

Normalize only typed containment/closeout receipt identifiers in the closeout DAL.
Do not rewrite signed historical JSON, hashes, provider IDs or existing receipts.
Exclude unrelated terminal target containment from the configuration conflict
query, alongside existing closed/read-contained history. Every owned stream and
every active account claim remains included. No schema or stored procedure change
is required. Existing SQL constraints make target containment terminal with no
active account, and request admission rejects dispatch on that stream.

SQL contracts: ExportExecutionStream, ExportExecutionSession, ExportPreparation,
ExportPreparationResource, ExportResource, ExportTargetContainment,
ExportLegacyCloseout, ExportContainedTarget and the execution/closeout procedures.
Validate against the authoritative SQL repository's merged legacy-closeout release.
Keep all writes inside the existing DAL transaction and compare-and-swap boundaries.

The installed transition registry must include the complete reviewed two-file
successor with exact predecessor/successor hashes. This preserves the P0 source
inventory check and requires a packaged updater upgrade before the routine source
update. Existing SQL contracts and migration receipts remain unchanged.

## Validation and review

The restricted disposable SQL regression must connect actual ODBC snapshots to the
real recovery services and private-journal verification, rather than separately
testing a hand-written service snapshot and the settlement procedure. It creates
eleven synthetic unchanged destinations, seals an original closed request, records
containment through the production procedure, settles the abandoned configuration
read, closes out the obsolete export and verifies the receipt after a new service
instance. A later synthetic job may admit a request to those same targets. No
provider request, imported scan or reporting calculation executes.

Retain regressions for live/frozen foreign streams, damaged receipts, typed UUID
case/representation, unchanged provider IDs, replay rejection and ownership races.
Run existing configuration recovery, containment, legacy closeout and updater tests,
architecture/deferred/security-routing validators, lint and test selection. Run
full private CI and exact-head code reviews. Security: Changes scans for separate
mirror/private Git targets, Deep off; no SQL diff scan because SQL is unchanged.

No command/view business logic or SQL is added. Existing identity and wire helpers
are reused; the new mapper is limited to receipt IDs to avoid altering canonical
historical bodies used elsewhere. No unrelated refactor or optimisation is added.

## Operator sequence and evidence boundaries

After both reviewed PRs are merged, use the packaged normal updater instructions.
Deployment preserves the committed scan, its three reporting receipts, credentials,
activation settings and all eleven URLs. Do not replay the prior SQL migration.

First Recheck the held configuration-read incident. Use its offered guided action
to abandon/isolate that read after checking its evidence; retain prior configuration.
Then Recheck the obsolete export and confirm Allow next export when offered. That
action records abandonment, not delivery, and dispatches no export. If either
refuses, retain its exact diagnosis rather than manually clearing reservations.

Only after both decisions verify may a new genuine scan use normal import/export.
Verify its receipts and publication to the unchanged targets separately from
deployment. Scan 1231 must never be imported or reported again. P0 F01-F05 acceptance
remains separate; preserve the full P1 programme, including tracked-view restoration.
Do not repeat the accepted KVK16 timing measurement.
