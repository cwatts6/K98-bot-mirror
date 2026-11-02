# S11 SQL file visibility runtime contract

The SQL migration 20261008_001_sql_auth_import_file_visibility replaces
xp_fileexist with sys.dm_os_file_exists in the immutable claim, import and
archive procedures. A real SQL-authenticated application connection demonstrated
that the former reported a present ready file as absent. An administrator's
impersonated connection did not reproduce that result.

This is a behavioral amendment, not an alternate spelling of the historical
permission installation. Keep the historical direct source manifest, grant
plan, signed profiles and permission installation allowlists unchanged.

The protected version-2 legacy_sql_contract can explicitly select
module_amendment: "20261008_001_sql_auth_import_file_visibility". Runtime then
requires the migration's applied ledger row and exact checksum
dde9189ac05cb699b2114775eef5769b7ab7e629b63d4c1681427d53ed3c5aaf,
and requires only the reviewed postimage for each of the three affected modules.
The runtime constants use the existing canonical definition hash: CRLF to LF,
trim outer whitespace, normalize the leading CREATE/ALTER token, then SHA-256 of
UTF-16LE. All remaining module, owner, SET option, execution context, login,
grant, membership and metadata fingerprint checks remain active.

The ledger read is bounded to the historical direct-permission migration and
this one amendment. Installed bodies cannot select an amendment or widen its
accepted hashes. A partial migration, old body, changed body, missing or wrong
receipt, or permission drift fails closed even if an observation fingerprint is
resealed.

Deploy the reviewed SQL migration first while producers are stopped. Then read
the real dedicated application's legacy and whole-application contracts and
independently compare them with the reviewed source amendment. Rebuild the
protected automatic startup seed with those accepted fingerprints and the new
Bot source pins before starting. Do not replay a retained uncertain import
until its file, receipt and coordination state have been reconciled separately.
The startup change neither imports the CSV nor activates KVK intake/recovery.
