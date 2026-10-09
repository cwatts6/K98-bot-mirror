# S11 registered health probe — 2026-10-07

The coordinated `/ops dl_bot_status` check supplied the Kingdom Summary Sheet to
the configuration probe. That probe admits only the protected configuration
destinations. Rejecting the mismatched target inside the owned scope retained an
uncertain preparation before a provider request was recorded and blocked later
account admission. A startup readiness probe can therefore succeed while the
subsequent status command exposes this separate failure.

`LegacyExportRuntime.configuration_health_destination` now selects a representative
from its copied, immutable configuration scope before admission. An admitted
preferred target is preserved; otherwise selection is deterministic within that
same scope. Missing scope fails before creating a preparation. The coordinated
health result explicitly identifies registered configuration access. The legacy
health path still checks the caller's requested Sheet.

The Sheets helper also reports a controlled failure stage and bounded exception
type. It does not log exception prose, credentials, request bodies or caller IDs.
Request and closure failures retain the existing uncertainty behavior, with no
credential fallback, automatic release or request retry. Neither the registration
nor the provider operation allowlist is widened.

## Validation and architecture

Regression tests use the real static Google SDK request builder and provider
adapter with an inert execution boundary. They cover the original mismatched
target, admitted and blank preferences, absent scope before admission, immutable
registration, bounded diagnostics and unchanged legacy selection. No Google
request, SQL connection or Bot start is required by those tests.

Target selection belongs to the existing runtime service; the public helper's
signature and command surface are preserved. No command, view, DAL, schema,
permission, cache or process-binding changes are included. Existing owner/CAS,
closed-stream and failure-retention behavior is reused. Unrelated legacy SQL and
module extraction work is outside this correction.

## Production sequence

1. Review and merge the mirror and separately promoted private Bot PRs after
   validation and a Changes security review. SQL object definitions are unchanged.
2. Verify the retained probe's exact private closure hash, positive child/job
   termination, zero request membership and sealed empty event digest. A closed
   timestamp or zero sequence alone does not authorize release.
3. Hold new imports/exports, stop and drain the current pair, and preserve its
   publication and session receipts. Prepare a separately sealed, guarded
   transaction for the exact aborted preparation and its two resources; preview
   rolls back and Apply rechecks ownership/version/closure evidence. It must not
   alter captured preparations, failed jobs, enrollment or activation.
4. Deploy the reviewed source and updated protected automatic-startup seed through
   the existing scheduled launcher. Source pins prohibit using changed files with
   the old seed. Fresh binding remains automatic; manual PID publication is not
   needed. Verify publication, session and ordinary application identities.
5. Verify the health check and ProcConfig import, then run a fresh export job and
   confirm its recorded provider completion. Do not replay the old failed job.
6. Keep KVK intake/recovery closed until the separate go-live decision and first
   baseline-upload checkpoint.

The code correction does not itself perform recovery, source deployment, runtime
installation, provider calls or activation. Existing SQL observation receipts may
be retained with their original timestamps because this patch changes no SQL
metadata or permission contract; do not describe them as fresh observations.
