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
