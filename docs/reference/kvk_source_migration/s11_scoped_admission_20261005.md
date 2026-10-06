# S11 source-scoped admission

The version-2 application SQL contract uses the pinned conservative dependency
scope in `deploy/s11_activation_scope.json`. It does not require unrelated retained
backup, survey or vote objects to be repaired or enrolled. Version 1 keeps its
existing whole-database behavior.

The scope is generated offline from the exact SQL Git blobs at
`9103f2c2b54821e8145aedf63a17e4aca474c911`, with every source SHA256 checked against
the accepted 540-member source manifest. Roots include all reviewed SQL modules
and table types, all KVK objects, fixed coordination objects and direct application
grant targets. Canonical names mentioned in their source are included recursively,
including unqualified names, comments and dynamic SQL strings. This deliberately
over-inclusive closure contains 429 objects; it is not a complete SQL parser.

Generate the reproducible inventory without any SQL connection:

```powershell
.\.venv\Scripts\python.exe -m scripts.prepare_s11_activation_scope `
  --sql-root C:\K98-bot-SQL-Server `
  --revision 9103f2c2b54821e8145aedf63a17e4aca474c911 `
  --out <new-review-output.json>
```

The contract keeps the complete accepted `sources` list and all existing target,
review ID and metadata/permission hash fields. Set its `version` to 2 and add
`scope_hash` equal to
`cd2708b81ad2affcf0986678e18be604fd695cab66e4266684aa7e2edcf2d234`.
There is no caller-selectable object list. The runtime independently checks the
committed scope hash, source membership and dynamic producer membership.

Metadata and effective object/column permissions are read for this scope plus
the independently reviewed `dynamic_objects`. Global schema permissions, synonyms
and database triggers remain in the contract because they affect resolution,
privileges or writes. Both startup and legacy producer admission apply this same
scope. Fixed execution/coordination, legacy direct permissions, headroom, ownership,
process identity, protected source/configuration and provider evidence checks remain.

Dynamic output shapes must still be independently reviewed. Season 16 target
tables remain relevant to the registered legacy target producer even though new
KVK source services do not directly use `TARGETS_16`. Existing historical shapes
may be accepted only through their recorded source compatibility evidence; no
table conversion, truncation or regeneration is part of this correction.

The grant plan includes only SELECT on `sys.sql_expression_dependencies` in addition
to the already reviewed application rights. Production separately installed and
verified that metadata permission on 5 October. The renderer permits that exact
system-catalog object and permission, with no general `sys` grant exception.

## Rollout and activation boundaries

This change prepares admission; it does not activate any production feature.

1. Review and merge the mirror correction, then promote its file delta onto the
   private Bot `production/main` history through the standard promotion process.
2. With actual operator hold and manual Bot stop, deploy the merged private main.
   Preserve the prior release and environment. No SQL migration, dependency
   installation or launcher change is required by this correction.
3. Build independently reviewed scoped metadata and effective-permission contracts
   from preserved source comparisons and receipts. Observed hashes alone cannot
   become expected hashes. Do not rerun successful inventory groups merely to
   refresh timestamps.
4. Bind protected runtime/authority configuration to actual deployment ownership,
   source hashes and process identities. Existing ordinary-user-owned source and
   private `.env` receipts alone do not prove the immutable runtime boundary.
5. Separately approve candidate-pool enrollment and coordinated validation. Preserve
   the demo index/report, all eleven exclusions, recovery databases and uncertain
   publications. Slots 02–06 remain the accepted existing candidates.
6. Present the resulting G5/activation decision with validation and rollback receipts;
   change flags and restart only under that decision.

Rollback before enrollment/activation is the preserved prior private Bot release
with flags closed. After a provider operation, retain durable receipts and reconcile
uncertain effects before any rollback or retry. Never reset SQL ownership/evidence
or rerun a predecessor/baseline to make a gate pass.
