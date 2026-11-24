# Current player weights and imported windows — 2026-10-12

Approved scope: implement and validate locally; stop before PRs, deployment and production
changes. Receipt browsing, old upload prompts and in-flight confirmation UX remain deferred.

## Behaviour

The imported season's three player DKP coefficients are the current calculation authority.
Equivalent decimal spellings and timestamp-only reimports are no-ops. A new period reuses the
approved B0 roster and mapping while taking current weights; it no longer requires the initial
weight import timestamp. Actual mapping differences still reject onboarding.

Changed coefficients append immutable configuration requests. Recovery rebuilds compatible
complete periods from their retained player revisions and aggregate revision, recomputing player
DKP and ranks. The season lock and one outer transaction cover every selection replacement;
only the final replacement emits a complete export vector. An interrupted refresh rolls back all
replacements. Pending endpoint/map/roster differences require a compatible reviewed match; the
previous complete selection remains readable. Manual exports refresh before resolving the latest
intent, and new export admission rejects any vector member using stale coefficients. Existing
admitted jobs retain their immutable intent and ownership/reconciliation rules.

The original accepted scans, roster, historical configuration/publication records and supplied
kingdom/camp facts remain intact. In particular, player weights never recalculate supplied
aggregate DKP. No source reimport, re-baseline or production timestamp patch is needed.

Configuration from a B0 receipt now uses a paginated imported-window picker. The service binds
the selected name to current scan IDs and shows accepted UTC scan times. Initial coverage defaults
to those times, with an explicit override for differing report coverage. A pending end is allowed;
the start must already be accepted. Confirmation rechecks window, scan-time and configuration
meaning, owner, permissions, receipt version and expiry.

Player window authority comes from the confirmed scan tuple. Aggregate report coverage is
independently confirmed and sealed on the matched update; the original period envelope does not
block corrected endpoints or differing report coverage. Final aggregate admission still requires
administrator authorization, and final replacement retains exact revision/version checks.

## Persistence and validation boundary

No SQL migration is required. Static validation used the authoritative SQL repository
`C:\K98-bot-SQL-Server`: `KVK.KVK_DKPWeights` (legacy float coefficients and UTC default),
`SourceWeightConfig` (decimal(38,12) and original strings), `SourceConfigVersion`,
`SourceWindowConfig`, `SourceConfigRequest`, `SourceUpdate`, `SourceCompleteSelection` and export
intent tables. Existing source/season/period foreign keys and update coverage chronology remain
in force. New configuration writes touch only newly allocated snapshots.

Local regressions cover import-time drift, equivalent decimals, new-period reuse, repeated
weight changes and return to earlier values, recalculation/ranks, aggregate preservation,
pending windows, exact assignment authority, stale exports, transaction rollback, stale
confirmation, picker pagination and owner restrictions. These are offline tests and query/transaction
models; they do not establish live SQL concurrency, Discord or provider acceptance.

Architecture, deferred-item, security-routing, test-selection, smoke-import and command-registration
checks form the local gate. Changes security review targets this uncommitted Bot patch only;
Deep scan is off. No SQL-repository edit or security target is part of this patch.

The deployed KVK16 walkthrough remains paused. After a separately approved deployment, resume
the retained B0 receipt and prepare a fresh Pass 4 configuration review for scans 12–18; the old
expired proposal is not reused. Aggregate acceptance, publication, export and activation remain
separate actions. This note authorizes none of them.
