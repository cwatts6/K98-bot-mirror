# Recovery centre reports and evidence repair

This change follows the initial P0a deployment. It fixes the footer-less Discord
message lookup that can raise `AttributeError`, separates notification health from
incident-check health, and adds an admin-only downloadable incident report.

## Operator workflow

1. In the configured admin notification channel, open **Recovery centre** from
   the bot status or an incident alert. Only the configured admin can use it.
2. Select **Download recovery report**. The ephemeral JSON attachment includes
   open and resolved incidents, saved diagnoses, blocker links, required repairs,
   release restrictions, pending verification and monitor diagnostics. If there
   are multiple parts, use **Download next report part** and retain every part.
   Exporting never rechecks, reconciles or applies repairs. The report identifies
   its observation window and completeness. A store failure produces an explicitly
   incomplete diagnostic attachment, rather than claiming there are no incidents.
3. For **Private recovery evidence — recoverable**, review the verified-copy
   checks. Select the offered restoration button, review its checks and effects,
   then select **Confirm & apply repair**. The authority restores the exact
   hash-verified original bytes and verifies both copies before settlement.
   Existing damaged ciphertext is retained. This does not prove a business write
   succeeded or release its resource reservations.
4. For a receipt-less stats incident with a typed saved admission, select
   **Review interrupted admission**. That workflow independently checks saved
   inputs, execution exclusion, streams, generation, ownership and fencing before
   offering cancellation or continuation. Missing receipts alone never authorize
   release or replay. Historical requests without typed inputs remain unproven;
   the report includes their preparation state and held-resource diagnosis so the
   exact remaining recovery can be investigated without an admin composing SQL.

The only automatically dispatched recovery is the previously approved verified
configuration-read release. Evidence-copy restoration requires admin confirmation,
including when a legacy adapter advertises an automatic repair.

## Validation and release limits

Regression tests exercise real Pycord embeds without footers, notification/check
failure separation, redacted failure call sites, permission boundaries, complete
multi-part reports, all incident states, unavailable-store reports, typed admission
links, confirmation, hash mismatch, lost acknowledgements and restart verification.
Session-local SQL tests use the deployed SQL source pin
`b663308aabe049319e1ce32a50d1bcfd810f9d8f`; they check SQL GUID pagination, scope,
read-only reporting and exclusion of incidents first seen after the report starts.
No SQL migration, dependency, credential, activation-flag or authority-source change
is included. Deploy through the normal updater after the private PR is merged.

This is not full P0b completion. Unknown writes, missing-all-copy evidence,
historical receipts without authoritative execution proof, partial report
completion and other withheld recovery actions remain required scope. The report
must identify those restrictions rather than label them repaired. Production
incident settlement requires current evidence and successful post-repair
verification; local tests do not establish it.

## Deployment and functional acceptance

### Queue navigation and report clarification follow-up

Use **Review queue blockers** from the status message or recovery centre to show
only open account-admission incidents. Pagination keeps that filter. Select the
queue, check its ticket, then use **Review execution and ownership** to reach the
exact domain repair. Do not choose a similarly named report from an unrelated
incident page. Dropdown descriptions now include the last twelve characters of
the incident ID, matching the footer, as well as the first-seen timestamp.

The filter reads recorded incidents; it does not release a queue entry or certify
that all failures have been discovered. Domain repairs still require their checks,
confirmation and independent verification. An empty queue page does not establish
import/export health. Persistent buttons on existing messages remain supported;
new messages include the additional navigation control.

The complete ZIP and detailed JSON reports now distinguish an accepted repair
awaiting verification, a running evidence group, a group completed with exceptions,
an unavailable check and a repair not enabled in the release. A running group does
not require its members to be repaired individually. Review exceptions separately.

Monitor diagnostics include the current cycle's start, latest checkpoint and
progress time, plus completion time when available. These are diagnostics, not
recovery authority. Progress does not refresh the last-success timestamp or turn
a stale/failed check healthy. If monitoring is stale without an exception, retain
the report so the active phase can be investigated rather than assuming an outage
or successful verification.

This follow-up changes no SQL schema, updater package, provider protocol or repair
capability. The unstarted-export qualification is a separate focused change with
its own protected-source deployment requirement. All remaining P0b workflows in
the full-release matrix remain required; this navigation fix is not P0b completion.

Use the installed updater after both recovery PRs are merged. On MINI_AMD, in
Windows PowerShell 5.1 as administrator, first run:

```powershell
& 'C:\ProgramData\K98\S11\updater\Update-K98.ps1' -PrepareOnly
```

Continue only when preparation and preflight pass. During the maintenance window,
run the same command without `-PrepareOnly`, then use `/ops graceful_restart`
only when the updater requests it. The updater coordinates source and startup
policy; no new SQL migration or updater installation is part of this patch.

After the updater confirms the successor is online:

1. Open `/ops dl_bot_status` and **Open recovery centre**. After a successful
   monitor cycle, monitoring should be active. A notification failure must remain
   separately visible; active monitoring does not mean all incidents are resolved.
2. Download the report before repairing incidents and retain every part.
   Confirm the report includes the open evidence and stats incidents, their
   blockers, current repair availability and monitor diagnostics.
3. For the recoverable evidence incident, use **Protect verified evidence** or
   **Restore verified evidence**, review the checks and confirm. Success requires
   both copies to verify. Reopen the incident or recheck it and download a second
   report to verify its resolved state. Do not interpret this as proof that the
   original SQL or provider write succeeded.
4. For receipt-less stats work, follow **Review interrupted admission** when
   available. Review the offered evidence and continuation/cancellation choice
   before confirming. If no typed admission can be proven, keep the incident open
   and supply the report for the required historical recovery work.
5. If a repair remains pending, use **Recheck** to reconcile and verify its saved
   action. Do not replay an uncertain write or clear a reservation manually.
   Failed or unavailable verification must stay visible in the next report.

A deployment/startup success alone does not establish import/export health.
Accept this patch only after the monitor, report download and applicable guided
repair checks above succeed on MINI_AMD. Retain the updater transcript and
before/after reports if any check fails.

Rollback uses the normal coordinated updater with a reviewed revert on private
main; do not overwrite the live checkout. No schema rollback or recovery-record
deletion is needed. Keep repair receipts, evidence copies and retained work.
Reverting this patch removes its new report controls and evidence-action exposure,
but must not be treated as undoing a repair already applied.

All six P0b workstreams and their acceptance criteria remain mandatory in
[the full-release matrix](../task_packs/guided_recovery_release_split.md#p0b--full-release).
That includes partial configuration and reporting, whole-pipeline continuation,
lost evidence/history, unattributed holds and integrated rollover. The unknown-write,
all-KVK and player-report workflows also retain their full qualification requirements.
