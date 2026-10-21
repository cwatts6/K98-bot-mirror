# P0 recovery evidence and publication readback batching

## Scope and history

This is the replacement for closed mirror PR #422 after mirror main was replaced
by the production snapshot. The timing delta is reapplied to that current base;
unrelated mirror history is not merged. Private wording PR #672 is merged and the
operator's logs verify the KVK16 415-row cache completed after its startup deadline.
The stats display was accepted. These observations do not close all P0 families.

The combined implementation covers two bounded parts of F01/F02/F05:

- Fresh publication readers batch at most 16 ranges / 50,000 cells, retaining all
  target, rectangle, content and exact sealed-replay checks. Legacy readers keep
  their original request order. Closed request history uses 256-request pages.
- If both working private-evidence copies fail, the configured admin receives
  specific collection instructions. An operator can stage an original encrypted
  backup under a UUID-derived name inside the existing protected evidence root.
  A fresh inspection must decrypt it and match the account-scoped SQL commitment
  before offering a separate restoration confirmation. Damaged files and the
  backup are preserved; both restored copies are read back independently.
- Unroutable queue ownership and unattributed producer holds receive collection
  steps in Discord and downloaded reports. No missing owner, timeout or absence
  of evidence authorises a release, import replay or successful disposition.

## Architecture and safety

The existing authority lock, boundary check, SQL evidence catalogue, bounded
encrypted storage and durable recovery action journal are reused. No path,
plaintext or backup bytes can be submitted through Discord or the authority RPC.
The new backup filename is derived only from the validated evidence UUID. Existing
root containment checks reject symlinks and path escapes. Backup changes invalidate
the reviewed token. Lost replies reconcile the restored copies rather than issue
a second operation. Restoring evidence never proves the original provider outcome.

The SQL schema and queries are unchanged except the history page bound. The
authoritative ExportProviderRequest and ExportProviderRequestEvent definitions
retain unique sequence ordering and at most three event positions per request.
The backup workflow uses the existing catalogue contract; it adds no SQL object or
column. No migration, source-setting change or live provider call is required for
local validation. Some existing replacement catalogue tables are absent from the
current local SQL schema checkout; no replacement schema is inferred or authored.

Security gate: Changes review of the final replacement-branch diff, Deep off.
The protected updater retains complete exact source bundles. Its registry capacity
increases from 32 to 40 entries, still bounded by 64 KiB and 16 members per bundle;
this does not alter provider budgets or broaden permissible backup paths.

## Operator workflow after release

For genuine all-copy loss, open the private-evidence incident and download its
report. Preserve the binding and damaged files. On the bot machine, locate the
installed authority manifest's `evidence_root`. Copy the original encrypted file
from a trusted backup into that folder using the `backup_<reference hex>` name
shown by the incident. Do not overwrite the primary or replica and do not upload
plaintext or credentials to Discord. Choose Recheck; confirm Restore verified
backup only when offered. Then follow the original operation's recovery.

If no decryptable, hash-matching backup exists, the original remains unknown and
open. Independently verified successor recovery is still required; this release
does not manufacture one. Configuration conflicts and unidentified ownership must
be investigated using the displayed read-only collection steps.

After timing deployment, perform one comparable published-output check on the
same retained publication with unchanged registered files. Retain its receipt and
phase-timing JSON. Compare with the saved 170-request / 816.7-second measurement,
including budget wait and retained/sealed history. Offline request reduction is
not a production latency result. Do not inject production corruption or loss.

## Remaining P0 scope

F01 still needs production timing acceptance and remaining absence, damage,
replacement and repeated-repair-failure qualification. F02 still needs independently
qualified successor handling when no exact backup survives and ownership/conflict
resolution beyond evidence collection. F03 retains historical partial configuration,
UPDATE_ALL2 and remaining durable pipeline/pre-request continuation work. F04 retains
the final rollover matrix and natural eligible production verification. F05 retains
the cross-family permission, stale/concurrent interaction, restart, lost reply,
configuration change, live-writer and repeated-failure acceptance matrix against
the final private release. No unfinished P0 item is moved to P1.

The tracked Discord-view restoration deadline remains the separately recorded P1.
Final private promotion, CI/security qualification, exact updater packaging and
operator deployment remain distinct from these implementation tests.
