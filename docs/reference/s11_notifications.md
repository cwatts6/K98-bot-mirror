# S11: separate stats and Sheets outcomes

New coordinated processing runs have two independent outcomes:

- **Bot stats available:** SQL succeeded and the player-stats cache returned a
  fresh, successfully written SQL generation. The existing stats adapters retain
  their channels, seasonal routing, daily caps, reservations and mention rules.
  This happens before the Google-dependent ProcConfig import and export.
- **Sheets available for analysis:** the exact export job is confirmed, its
  publication receipt matches, and all output parts are verified. Public analysis
  links go to `GSHEETS_EXPORT_CHANNEL_ID`, with all mentions disabled. Private
  spreadsheet IDs are not published. Up to 20 public links fit in the Discord
  outcome; larger exports include an explicit count of additional outputs in the
  job record. Failure or uncertainty does not revoke bot
  stats availability.

Configure `GSHEETS_EXPORT_CHANNEL_ID` to the agreed player-readable analysis
channel before rollout. There is no fallback to the stats channel. A missing
channel or permission produces an actionable notification failure; it does not
fail the import or repeat the export. Auxiliary name/target cache warmers keep
their existing behavior; the readiness claim certifies the player-stats generation,
not a new target-publication guarantee.

## Durable correlation and recovery

`data/processing_outcomes.json` records only newly registered runs, with source
message/channel IDs, runtime account/storage owner, required stage outcomes,
preparation/job IDs, cache generation and individual Discord receipts. Preserve
this file across updates and restarts. Its atomic replacement and OS file lock
protect updates; an invalid journal is retained and fails closed for notifications.
Do not delete or replace it with an empty file to clear a problem.

The existing supervised outcome observer checks up to 16 runs per 30-second cycle
in rotation. It never imports data, enqueues an export or calls Google. A lost
enqueue acknowledgment is reconciled by reading the registered preparation's exact
JobID. Terminal events log the run, job, outcome, next action and full elapsed time.
The pending admin summary is edited on completion, and the live queue matches the
run UUID rather than a possibly repeated filename.

Each component is durably marked before Discord dispatch and acknowledged with
its actual message/channel ID. Known failures before dispatch get at most three
attempts. Stats retries also require the exact current cache generation and a
five-minute window. Already acknowledged or ambiguous components cannot resend.
An ambiguous Pre-KVK edit cannot fall through to a fresh mention. A proven deleted
summary can be replaced without mentions. If an uncertain export is later
authoritatively confirmed through the existing separately controlled recovery,
the observer can publish that new outcome once.

Successful completed notification records are retained for diagnosis (up to 128
recent closed runs). Open records are never silently discarded. At 256 total
records, new registration stops and logs the intervention needed; business work
does not replay or acquire different ownership because of this limit.

## Administrator commands

Import/resource problems use `/ops import_resolution` as documented in
[processing outcomes](s11_processing_outcomes.md). Notification problems use the
local operator command below. It has no SQL/provider mutation path; it is not an
export recovery command. Run it from the deployed Bot checkout as the authorized
local operator. Copy the run UUID from the Discord footer or `processing_outcome`
log event.

```powershell
python scripts/processing_notifications.py --run-id <uuid> --action status
python scripts/processing_notifications.py --run-id <uuid> --action preview
```

The preview prints an exact confirmation token. Mutations require that token and
an audit reason; changed evidence requires a fresh preview.

| Evidence | Required administrator action |
| --- | --- |
| Component `failed` | No Discord operation was dispatched. Correct the channel or permissions, then preview and retry that exact status component. |
| Component `sending` or `held` | Delivery may have happened. Inspect the recorded channel, message ID when available, stats timestamp, run footer and correlated logs. Do not retry blindly. After checking or manually posting the missing message, preview and dismiss the component. |
| Stats `unavailable` | Fresh cache readiness was not proved. Inspect cache refresh/write diagnostics and correct the cause before a new scan. Old cached data is never called a new success. |
| Stats `superseded` | A newer cache generation exists. Use the newer run; do not announce the old run. |
| Sheets `uncertain` | Use the exact export job evidence and existing export recovery procedure. Notification commands cannot release resources or repeat provider requests. |
| Journal invalid/unwritable/full | Preserve it. Fix disk/permissions, restore only a verified evidence copy, or explicitly close runs after inspecting and resolving their remaining notifications. Never clear the journal wholesale. |

For an unsent Sheets outcome, the CLI can also correct its destination:

```powershell
python scripts/processing_notifications.py --run-id <uuid> --action retry --component sheets_confirmed --channel-id <channel-id> --confirmation <token> --reason "Corrected analysis channel permissions"
```

To acknowledge a manually resolved ambiguous notification, use `--action dismiss`
with its exact component, token and reason. To acknowledge all remaining
notification issues for a run, use `--action close` with token and
reason. Closing ends notification observation for that run, including later export
resolution updates; it does not stop an active export or change SQL or Google. A run interrupted before job correlation can be explicitly closed after inspection without inventing a successful or failed application outcome. Neither action sends a
message. Stats components cannot be forced to replay through this command.

## Rollout

This change depends on the reviewed import-outcome foundation. It adds read-only
queries against existing export tables; no new SQL migration or grant is required.
Use mirror-first review and private-main patch promotion. Set the separate channel,
preserve the journal, and perform a fresh operator-approved rehearsal after the
matching deployment readiness decision. No historical catch-up, live export,
recovery, import or restart is performed by implementing this change.
