# P02 D5b test installation packet — 2026-11-11

Status: source/inert/security review complete; one operator execution pending.
This is within the approved native D5b scope, not production deployment.

## Adjudicated starting state

Read-only receipt `d5b-preimages-result-a94a637cf4424a819df015d8ab069c4d.json`, SHA-256
`de23d98c9d0ad7dbd4bb819ed9262d42fd65f2a5c1a5c1f046f924a55e2baae8`,
has no errors, 47 commands, 57 rows, verified closure and 2.9564024 seconds elapsed.
All 30 D4 structural preimages match the fixed profile. The daily index is absent;
the daily procedure exactly matches the original migration's predecessor after
its own normalization. Sequence current value is 518383. All nine summary
checkpoints equal maximum scan 1245. Configuration last maintenance was
2026-10-29T23:16:01.271Z, with 1650 subsequent rows, so the age condition is eligible
at observation time. Five completed canonical KVK outputs exist (12–16). These
are feasibility observations, not proof of actual report/maintenance execution.

## Executable and bindings

- `scripts/install_p02_d5b_candidate.ps1` SHA-256
  `e300db15c1ab710262b1b176495e676aa538ef2ef621e874d3de3becd34d025f`.
- Private `.codex_artifacts/p025/d5b-install-manifest.json` SHA-256
  `21deb17b3224dea8357f73e078e3d26db72527500582bbda8a9b474a605fbc04`.
- `tests/validate_p02_d5b_install.ps1` SHA-256
  `c187ce76d53f7d2b147351ebb5162e3df8fbb30f6c86d90141b9c3ee4b263e9a`.

Only `K98_P025_D5b_20261111`, ID 8, exact creation time/owner/settings/files,
existing Q volume and pinned VM/session are accepted. Existing visibility is
checked; no permission grants. The packet checks for foreign copy sessions,
takes zero-wait release and five maintenance/publication locks, validates fresh
30-object preimages and the exact daily predecessor, and creates exclusive host
and guest installation-intent records. An existing marker prevents replay.

An owned outer SQL transaction contains the byte-identical daily migration
`20261106_001_personal_stats_daily_read_plan.sql` and the fixed D4 payload. The
daily migration's nested BEGIN/COMMIT must return transaction depth to one.
The D4 payload's only adaptation is the outer database-name guard changed from
`ROK_TRACKER` to this exact disposable target. Reversing that one replacement
must reproduce the authoritative source hash. Production files and guards remain
unchanged. No formal Applied/DeploymentRunHistory rows are fabricated.

Before committing, verify all 30 canonical structural postimages, exact daily
procedure/index, unchanged sequence value, and the expected eight initial ledger
rows. Structural observations use two bounded client batches of the unchanged
parameterized canonical image query, with 30 ordered rows each. No persistent
helper object is created. Commit then requires transaction depth zero, unchanged
original source protection, and owned SQL-session closure. Errors or uncertain
commit/cancellation stop progression and preserve intent, receipts and physical
cleanup ownership; no automatic retry or deletion is permitted.

Limits remain 300 seconds overall, 210 seconds guest work, at most 180 seconds per
work command, 3 seconds metadata, zero lock wait, 48 client commands, 2048 rows,
1 MiB receipt, 8 GiB disk reserves and 512 MiB version store. Successful path is
29 client commands including closure. Actual elapsed time is deducted from the
conservative remaining native budget of 1545 seconds. Original statement,
rehearsal and Bot limits are unchanged. The 21-input allowance remains consumed;
this stage reads no retained inputs and runs no report, import or maintenance
child. Original database, files and failure evidence remain preserved.

## Validation and review

Actual Windows PowerShell 5.1 inert tests passed: identity/settings and visibility
refusals, query/output/deadline limits, structural before/after, missing/wrong/
oversize image refusal, prohibition on adopting postimages as fresh preimages,
and exact daily normalization. Supplemental ignored
`d5b-install-async-validation.ps1` extracts the actual async helper and cleanup
block; fault, pending-cancellation ownership retention and settled disposal pass.
No SQL/VM operation occurred during tests. A preparation shell here-string parse
error and a test-only PS5.1 array-count expression were corrected before review;
neither was a native attempt or changed original evidence.

Both source payload hashes and the single reversible lab guard substitution were
verified against the SQL repository. No GRANT/DENY/REVOKE or formal history writes
exist in the payloads. Independent review found no blocker. Security Changes
scan `e2d91100-73d6-4274-bab0-2d16a2592551` completed with zero reportable findings,
Deep off; nine changed source files accounted for, eight reused only after
unchanged hash verification. Snapshot digest
`a3120572a22b8bbcfadbcf7739b45c44f2225f3aaeddb3384f04ffa03d617f2e`.
Findings SHA-256 `c15feba0e94f5d82c8940b70924c617cf2527de4ccacb52e7cd3a899b5b9de21`;
coverage SHA-256 `d62b8cc65682b5ae0a2165a2bb49cb6ba76fcec05f6fb46fa38b87f3c317d7d6`.
Routing/whitespace checks passed. Python architecture/full suite/smoke/command
registration checks do not exercise this operator-only PowerShell addition;
existing runtime changes retain their earlier validation. No deferred refactor
was introduced. Native installation and D5b completion remain unproven.

Next: adjudicate the installation receipt before any report or child execution.
Use legitimate labelled lab stimuli, an explicit comparison clock and the
independent oracle. No skipped/ineligible/empty-ledger pass, original backup job
dispatch, new input consumption or permission change may substitute for evidence.
