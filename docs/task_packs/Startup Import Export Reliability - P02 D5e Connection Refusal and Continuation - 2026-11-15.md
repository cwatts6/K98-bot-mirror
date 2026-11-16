# P02 D5e connection refusal and grouped continuation

The continuation receipt `d5e-measured-continuation-result-aa1b9419f98847c9ba9a6643c0563abd.json`
matches SHA256 `f6dbe0c143e607f4ca28f88773132cb0ac8b8a52dd26ed4161fba40fb2acea20`.
The actor was created, resumed and joined with exit code zero; its result records
ODBC 08001, `SSL Provider: The target principal name is incorrect.` The error was
captured as a failed result, so exit code zero is not qualification acceptance.
It records zero SQL statements, connection births, arms, row attempts and raw
bytes. Actor/job and collector closure are confirmed. Elapsed 0.8757019 seconds
charges one native second. The post-run preservation flag was not reached; it is
not being accepted as a new preservation proof. The next packet rechecks custody
and preservation before starting outstanding work.

| Accounting | Completed / expected or remaining |
| --- | --- |
| Fixed accepted checks | 100 / 100 |
| Binding checks | 3 / 8 |
| Cost arms | 0 / 12 |
| Native qualification total | **103 / 120** |
| Setup, separately tracked | 1 / 1 |
| Native time | **985 seconds remain** |
| Windows fault time | **49 seconds remain** |
| Row attempts | **83 / 95 consumed; 12 remain** |
| New databases / copy-only backups | **0 / 0 remain** |

The 21-input allowance remains consumed. Earlier evidence, intents and receipts
are immutable; no accepted work has been replayed. Offline test totals and review
results are separately recorded in the final connection handoff JSON.

## Cause and limited correction

The measured actor used `Encrypt=no` and omitted the certificate-trust option,
unlike the successful native D5d actor. This is connection-profile drift during
packet preparation. The receipt proves a certificate-name refusal; it does not
establish which server encryption setting caused validation. Microsoft documents
that ODBC 18 may validate certificates even with `Encrypt=no` when the server
requires encryption. [ODBC connection attributes](https://learn.microsoft.com/en-us/sql/connect/odbc/dsn-connection-string-attribute?view=sql-server-ver17).

The new actor uses the existing isolated native profile:
`SERVER=lpc:localhost;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;Pooling=no;MARS_Connection=no`.
This requests encryption with the already-used connection-local certificate
validation exception. It is restricted to the pinned zero-NIC VM, local shared
memory, exact integrated login and disposable database 11. Production TLS policy
and the application's connection settings are unchanged. No server/trust-store
configuration, network fallback, retry or broader access is added. All existing
database birth, owner, login, host and isolation checks remain before workloads.

The original actor is retained byte-for-byte. A new actor differs only in that
connection option string. A new exact directory `Q:\D5eMeasuredConnection-20261115`,
new C# type names, host intent and receipt prefix avoid reusing prior loaded code
or files. The immediately previous folder must contain exactly its original
actor, payload and pinned failed result; any additional entry stops continuation.
The earlier unentered folder and exact prior SQL owners are checked as before.

## Grouped work, validation and review scope

The twelve arm IDs and request IDs, warmups, five balanced pairs, diagnostics,
typed output/clock rules, SQL/source pins, budgets and cost thresholds are frozen.
Five outstanding binding groups and twelve unentered cost arms remain grouped.
Reservation: **600 native seconds, 0 Windows seconds, at most 12 row attempts**.
Maximum planned time consumption leaves **385 seconds**, above the retained
185-second D5f minimum. No exact allowance extension is required at preparation.
Unknown actor closure still reserves all twelve row attempts; time custody and
exact-handle cleanup remain intact. Any incomplete attempt requires adjudication.

Offline regressions execute the actual new connection method using a recording
driver, check all eleven identity/isolation refusal fields, and ensure a refused
connection makes no SQL calls or fallback. PowerShell 5.1 controls compile the
actual C# and execute the exact wrapper command guard, preservation helpers,
create-only receipts and conservative custody/row accounting without creating a
child process or connecting to SQL. These controls do not establish guest ODBC
success or native cost acceptance. Existing CREATE/CREATE OR ALTER/whitespace and
quoted `[rowcount]` / `[backup]` regressions and documentation remain preserved.

Security routing is Changes, Deep off, exact new continuation snapshot against
the last reviewed snapshot. The changed connection profile, retained-file guards,
launch/cleanup and truthful accounting are reviewed; SQL source is unchanged.
Architecture, deferred-item and security-routing checks and test selection run.
Full application pytest/import/command-registration checks are skipped because
no application runtime or registration changed. Final pins, completed/expected
offline totals, review outcome and immutable revisions are in the handoff record.
