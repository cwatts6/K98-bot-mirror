# Repeated historical-group confirmation

## Scope and behaviour

An accepted historical-retirement group must be discoverable after a repeated
confirmation, lost commit acknowledgement or restart. The same administrator's
exact selected members, revisions, evidence hashes and reviewed configuration
identify the existing approval. Returning its progress never submits a new repair.
Different selection, actor, configuration or evidence remains a new decision and
must pass the original verification and atomic approval checks.

Services retain authorization and selection validation. The DAL stores a canonical
selection digest in the existing group EvidenceJson and queries it within the
existing recovery scope. The serialized approval transaction also checks for an
existing decision. No SQL schema migration or permission change is required.
Groups saved before selection digests existed are recovered by matching their
original member/configuration evidence and every member action's exact author,
revision and hash. This readback does not backfill or rewrite old decisions.
Readback and approval share the same account-scoped transaction lock, with a
three-second bounded wait for an overlapping approval to commit. If that wait
expires, the admin is told to retry the same confirmation to check progress.
The deployed RecoveryIncident and RecoveryAction contracts were checked against
the reviewed SQL source checkout; tests use disposable local temporary tables.

## Acceptance and validation

- Repeated confirmation returns the original group while pending and after verified
  completion, including from a fresh service instance after restart.
- Lost commit acknowledgement reads back the same approval without duplicate intents.
- Pre-upgrade pending and completed approvals remain discoverable; mixed-author,
  missing or different member receipts cannot be adopted.
- Overlapping approvals and readback wait for the original SQL transaction and
  return one group with one intent per member.
- Selection order does not matter; a changed subset, actor, configuration or token
  cannot adopt another approval.
- Unselected inputs remain untouched; changed selected evidence still refuses a new
  approval. Cross-admin/guild/channel and foreign scope checks remain enforced.
- The existing concise review, per-input selection, saved approvals, independent
  member verification and downloadable report continue to apply.
- No import replay, provider write, held-access release or SQL-success assertion.

Focused tests cover the actual temporary SQL transactions and guided view, restart,
lost-reply, repeat and negative paths. Changes security review is required for the
final mirror and private diffs; no Codebase or Deep scan. The earlier failed-export
release is independent of these ordinary service/DAL changes.

## Remaining mandatory P0b scope

Monitor contention/status and durable diagnostic clarity, configuration membership
mismatch and its linked queue, still-needed captured/historical/failed output,
unknown-write replacement/publication and producer/rollover recovery remain active
delivery work. This focused confirmation fix does not close those workflows.
