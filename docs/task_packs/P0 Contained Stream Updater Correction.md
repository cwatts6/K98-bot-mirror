# P0 contained-stream updater correction

The routine updater classified every execution stream except `closed` as active.
A historical `target_contained` stream in a closed session therefore blocked the
release that supplies its same-URL recovery. The failed preflight installed no
SQL and requested no drain. This correction does not release export containment.

## Scope and contracts

The change belongs to `scripts/K98-SourceUpdate.ps1`, its Windows regression
tests, and a disposable restricted-account SQL inventory test. No command, view,
cache, credential, configuration, reporting, import or SQL object is changed.
The SQL source of truth is `C:\K98-bot-SQL-Server`: execution stream/session
tables and their transition procedures define terminal containment and session
closure. The updater reads these contracts through its existing bounded reader.

Contained streams are accepted only with a closed session on the bound host,
no active account, correctly shaped containment, complete closure fields and
ordered stream/session closure timestamps. Open/frozen streams still block
preflight. After successor start, only the separately verified successor may
own active streams. Missing or malformed containment remains a blocker.

Containment is terminal execution history, not proof of delivery or permission
to free a claim. Scan 1231 and all reporting receipts, private execution evidence,
quarantined resources, rotated credentials and all existing URLs remain intact.
The separately reviewed recovery action still verifies its own complete evidence
before allowing the next ordinary export.

## Validation and review

- Run `scripts/Test-K98Update.ps1`: real guard before and after successor start,
  retained row immutability, live/frozen conflicts, missing closure fields,
  open/foreign sessions, timestamp ordering and read-containment shape.
- Run updater preparation and combined-release pytest suites.
- Run `tests/test_updater_contained_stream_sql.py` with explicit disposable local
  SQL opt-in. The restricted account reads the actual updater query; it cannot
  change the evidence. Fixture owner setup is confined to a disposable database.
- Run architecture, deferred-item, test-selection and security-routing gates.
- Use Changes security reviews against each exact mirror/private base and head,
  with Deep off. No SQL repository diff exists for this correction.
- Qualify the complete credential-corrected predecessor-to-candidate packet,
  preserving the pending SQL migration and all existing startup bindings.
- Rehearse the exact replacement updater package and interrupted source/tool
  updates on an isolated protected Windows fixture.

The previous package rehearsal did not exercise historical contained streams in
the routine guard. The new guard regressions and restricted inventory check cover
that gap. No unrelated cleanup or deferred optimisation is introduced. Operational
SQL remains in the updater's existing SQL boundary, not Discord modules.

## Operator handoff

Use the replacement package's checksum-checked upgrade instructions after the
reviewed bot correction is merged. Retain the failed preflight evidence. The
normal updater prepares a fresh packet automatically because no deployment was
staged. Request one graceful restart only when prompted by the updater.

Do not manually change stream states, delete receipts, rerun committed imports,
retire output links or execute the migration by hand. Deployment, subsequent
export-block recovery and production functional acceptance remain separate.
