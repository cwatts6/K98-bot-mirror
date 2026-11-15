# P02 D5c restricted setup acceptance and positive handoff

The Setup receipt `d5c-restricted-sequence-result-fff9db4bb129494987a16ea463de7784.json`
matches SHA256 `571ef184296361f49115b058166ab96d2108d53852a356c6f878c67d04297d7f`.
The reviewed script and manifest hashes match; all 28 observations and six
mutation acknowledgements are present. Setup used 40/48 reserved command units,
110/2,048 rows and 24,368 receipt bytes. No reader process was started.

The corrected creation-authority query returned 1, authentication mode remained
supported, and both proposed names were absent before creation. The one new
`P02_D5c_Reader_20261112` login/user has SID
`9e6e525705d72892284a4ea90005affd`, login ID 269 and database user ID 15.
Creation stamps are `2026-11-12T20:16:30.617` and
`2026-11-12T20:16:30.630` respectively. The login is enabled, defaults to the
disposable copy and maps to the SQL user with default schema dbo. No role
memberships, extra direct server permissions, owned databases/schemas/objects
or column overrides were returned. Its exact four grants are CONNECT and SELECT
on ExportPreparation, ExportResource and ExportExecutionStream only.

The non-secret guest custody record is
`Q:/D5b-20261111/d5c-restricted-account-custody.json`, recorded hash
`2e026662ef9ba66bd0a5244a5927bd54676e5e23354719aa788f2dac38c9c08a`.
The password remains in guest memory and was neither requested nor inspected.

All seven paired protected-metadata groups match the accepted preflight.
The 799 original database permission entries retain the same fingerprint, with
only the exact new grantee excluded. The seven fixture rows retain hash
`308abe68ae0efada2bda217282b0e14c03824026b377c93084df7f9d4783042e`.
Both connection disposals and original work-session absence passed; the closure
observer reused SPID 52 with a different birth/connection identity. No competing
copy session was returned. VM/isolation, disk, log and version-store checks passed.

Whole host elapsed **1.1827841 seconds** debits two: **1,410 native seconds,
177 restricted-scope seconds and 50 Windows-test seconds remain**. The input
allowance stays **21 consumed, zero new inputs**. The wrapper's 1,262-second
conservative lower bound is not the exact current balance; it reserves all
three stage ceilings. No budget is refunded and all prior no-retry limits remain.

Saved-file acceptance is `.codex_artifacts/p025/d5c-restricted-setup-acceptance.json`.
The first local adjudicator assertion used PowerShell's displayed `.63` creation
stamp; inspection of the immutable JSON established its exact `.630` spelling.
The local assertion was corrected, with the failed assertion retained in the
tool record. No native operation or original receipt was changed or repeated.

## Next authorized handoff

Run the unchanged reviewed wrapper once with **`-Stage Positive`** in the same
elevated PS5.1 console holding `$global:D5bReportSession`. Setup must not be run
again. Positive's create-only intent is absent at handoff; its guest gate requires
verified Setup and an unused positive allowance. This uses the existing approved
account scope, not a new permission request.

- Script `scripts/run_p02_d5c_restricted_sequence.ps1`: SHA256
  `ad9854413ce6af95ada67bfef04b254e17853c426608773ecdc1bc2561319a0b`.
- Manifest `.codex_artifacts/p025/d5c-restricted-sequence-execution-packet.json`:
  SHA256 `4258810e35e9d573c0440772956a6c44ff379ea6fd86161d4eb609e2192c00c6`.
- Completed full-sequence and correction reviews remain
  `3a45b03c-da7a-41cd-bd89-51aa1b937f8e` and
  `aa05d09f-05cf-4164-89cb-4d0294f525dc`; executable bytes are unchanged.

Positive performs one authenticated actual target reader, verifies its exact
result, preserved rows/permissions and physical cleanup. It creates no rows,
changes no rights/settings and runs no producer, import, maintenance, report,
backup or provider request. Its ceiling remains 45 whole-host seconds, 47
command units and 161 planned rows. Return the receipt and host elapsed time;
stop on errors without retrying or resetting/removing the account.

Keep the console open. Denial and exact account removal follow only after this
receipt is adjudicated. A failed case remains a failure; the already-reviewed
CleanupOnly path is available only after ownership/custody review. Current
evidence does not yet establish restricted authentication, reader success or
denial. D5c and later D5 slices remain open; production deployment is separate.

This continuation changes saved-evidence adjudication and documentation only.
No executable change or fresh discovery scan is needed; the completed frozen
sequence review remains the applicable gate. No application test or startup
import is relevant to saved-file adjudication. Original evidence is untouched.
