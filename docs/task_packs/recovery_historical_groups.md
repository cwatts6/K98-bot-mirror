# Concise decisions and grouped historical retirement

## Approved scope

Replace the repeated mandatory configuration pages with a short decision summary
for historical captured exports. Show the original creation time, retained input
and procedure where recorded, unknown SQL outcome and original fault, whether
original/current configuration matches, and the precise effect of retirement.
Unavailable original upload names must remain explicitly unavailable.

Full technical configuration and destination links remain optional. Group review
uses a read-only technical viewer, so it cannot accidentally approve just the
representative member. Other recovery actions retain their existing review gates.

## Guided workflow

1. Open **Retire historical group** in the recovery centre.
2. Review the shared decision summary. Different original/current configuration
   pairs are separate groups. Each batch contains at most 25 eligible imports.
3. Select only obsolete exports by original date, procedure and retained input.
   Nothing is selected automatically. Leave unknown or still-needed work open.
4. Review the selected input list and **Confirm selected retirements**.
5. Recheck the group for verified, pending and changed counts. The complete report
   includes selected incident IDs and inputs, configuration fingerprints and
   group results; the individual incidents retain their diagnoses.

Retirement prevents future queueing of obsolete captured output. It preserves
captured bytes and unknown SQL history. It never certifies SQL success, replays
an import, writes to the provider, or releases held access.

## Architecture, persistence and acceptance

Services own grouping, fresh evidence checks and authorization. Views handle
the private summary, selection and confirmation. DAL atomically persists all
selected per-member RecoveryAction intents and one historical_batch incident.
The existing historical retirement reconciler applies and verifies each member.
Accepted actions receive bounded priority after restart. A changed member is
not applied and retains its individual incident; others continue.

SQL source: RecoveryIncident, RecoveryAction and ExportPreparation contracts
validated against the reviewed SQL checkout b663308a. No schema or grants change.
The 25-member bound fits the existing 32 KiB incident evidence contract.

Acceptance covers concise confirmation without technical pages; optional complete
details; explicit selection; admin/guild/channel/storage scope; stale input and
configuration; duplicate clicks; atomic group approval; lost acknowledgement;
restart reconciliation; independent changed-member handling; pagination; complete
report membership and outcome; preservation of the existing evidence group flow.

Security routing: Changes only, Deep off, this Bot diff and its private promotion
reviewed separately. Focused SQL/UI tests and the repository architecture, deferred,
security-routing, test-selection and pinned pre-commit gates are required.

## Remaining mandatory P0b scope

Failed-export recovery with complete private-journal verification, genuine
configuration/reservation mismatches, unknown-write replacement/publication and
remaining producer/rollover workflows remain required. The queue closeout is a
separate preceding change. This PR does not mark P0b complete or defer those cases.
