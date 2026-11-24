# P02 D5c account acceptance and reader-first plan

The account-owner-first receipt `d5c-account-owner-first-result-a63eea8a38a749a98c6b3c70b8fecdd6.json`
is accepted after independent saved-evidence checks. SHA256 is
`0eba59bc60a2296346928362d512f41d0d512f2e1da34d74cf2ed98de9d37a76`.
The actual target reader completed while the exact account holder remained
exclusive. Both SQL births, ordered overlap, rollback, physical connection
absence, protected metadata and original history pass. The 25,311-byte receipt
contains 48 reserved command units and 109 rows. Host time 1.3553954 seconds
debits two: **1,417 native seconds and 50 Windows-test seconds remain; 21 inputs
remain consumed.** No isolation, writer or maintenance retry is available.

## Scope and architecture

Prepare one distinct reverse-order C01 case under the existing lock-only approval.
Use the same disposable database, seven-row fixture, current versions 4/23/20,
actual configuration target DAL, actual account mutex and pinned unchanged modules.
Only qualification tooling, inert tests and this plan change. No command, view,
service, production DAL or authoritative SQL source change is needed.

The reader must establish its actual snapshot and fetch the existing preparation
row before the holder opens. A test cursor hook runs only after that physical
fetch returns, once, on the exact preparation query. It opens a second connection,
verifies identity and acquires the account lock with zero wait. Then the original
reader continues its resources and stream reads. Require the complete original
target, exact ordering and the holder still exclusive after reader cleanup.
Finally roll back/close the holder and independently observe both sessions absent.
This is ordered interleaving of actual separate SQL connections; no artificial
SQL delay, repeated read, extra query or production guard substitution.

The existing packet's 23 metadata statements, six outer control/cleanup units and
19 actor units remain within 48. Actor SQL remains eight statements/seven rows;
planned total returned rows 144, whole packet 60 host seconds, original resource
floors and evidence sizes unchanged. New immutable intent prevents repeat.
No new fixture rows, demand, provider dispatch, imports, reports, maintenance,
backup, isolation change or permission change is included.

SQL shape is unchanged from the accepted packet; its authoritative SQL source
hashes and captured fixture catalog remain mandatory. The new hook observes a
fetch boundary only and uses the actual unchanged `_mutex`/snapshot lifecycle.
Do not infer full inspector or closure-verifier qualification from target-data
coverage. Wider C01 and other D5c cases, D5d-f and deployment remain separate.

## Validation and review gates

Inert tests must enforce reader-before-holder ordering, an exact single boundary,
one factory per role, both identities, no holder admission after a failed initial
read, no continuation after holder refusal, preserved native attribution,
uncertain-reader cleanup preventing holder release, and unchanged caps.
PowerShell checks must reject missing/reordered boundaries and remoting shape
changes, preserve process/connection custody and current manifest/source pins.
Run focused tests, Ruff, architecture/deferred/security-routing checks and test
selection. Broad application startup/command-registration/full pytest are skipped
for isolated qualification tooling with no production behavior changes; no
release, live SQL or permission test is authorized by offline preparation.

Security-sensitive SQL/process/evidence handling requires an immutable Changes
review with Deep off, covering all five packet files and directly needed helpers,
before console handoff. No unrelated refactor/deferred item is introduced.
Any uncertainty stops; preserve receipt and intent without automatic repeat.

## Prepared packet

Ten Python tests and 226 PowerShell checks pass, including both normal and
deserialized receipts, missing/repeated/read-after-holder boundary refusal, native
mutex errors, failed preparation read without holder admission, and cleanup
uncertainty. The initial inert test retained an owner-first cleanup expectation
when the reverse-order reader failed before any holder existed. That expectation
was corrected to require retained reader custody; the original failed output is
preserved. No native attempt occurred. Ruff, architecture (48 Python files),
deferred (74 documents) and security-routing checks passed; the selector ran.
The wider recommended suites remain skipped for the reasons above.

Wrapper `scripts/run_p02_d5c_account_reader_first.ps1` SHA256:
`f8b6e187e7d479168e254b777880b5a99f3baa59965ab169d4139da0c0ce5a06`.
Manifest `.codex_artifacts/p025/d5c-account-reader-first-execution-packet.json`
SHA256: `4af8f41a1c15c7e1fbf2bc9700f4a5cf8b7fa10c2b48d4818a16b0d6feac1aeb`.
Manifest size is 129,251 bytes, below the unchanged 128 KiB cap. The expanded
19-module bundle stays 318,932 bytes. Immutable review is required before handoff.
