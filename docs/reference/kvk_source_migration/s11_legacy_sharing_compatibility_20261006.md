# S11 legacy sharing compatibility — 2026-10-06

Chris approved retaining intentional public editing on Migrate List and the
existing rokkvkstats/hohbot writers on legacy Sheets. The deployment check previously
required a sole authority editor for every registered file and therefore could
not admit those established integrations.

Runtime registration version 1 now accepts an optional `legacy_file_access` map.
Each key must be a registered legacy destination, never a protected exclusion or
an S11 index/generation file. Each entry has exactly these fields:

```json
{
  "editors": ["anyone", "authority@example.iam.gserviceaccount.com", "other@example.com"],
  "audience": "anyone_writer",
  "coordination_scope": "application_writers_only"
}
```

Editors must be unique and sorted, must include the registered authority, and
must match the separately retained file-access observation exactly. The `anyone`
editor requires `anyone_writer` audience and vice versa. Other permitted audiences
are `private` and `anyone_reader`. Ownership checks remain unchanged. A policy
change changes the pinned registration hash and requires administrator-reviewed
reprovisioning; neither Bot IPC nor a provider observation establishes policy.
Absent policies preserve the previous sole-editor/read-only-audience checks.
S11 output pools always retain those strict checks.

Application coordination covers application writers to these legacy destinations.
It cannot exclude or serialize external service-account or public edits. That
limitation is explicit in the policy and is not proof of exclusive provider custody.
No Google permissions, SQL grants, credentials or activation flags change here.

Operational bindings and owner selections are retained in private rollout evidence.
Chris selected his existing 1st Altar, Pass 4 and Pass 7 report copies; unused copies
are preserved. `GOOGLE_KVK_LIST_ID` matches the already observed configuration file.
The five accepted S11 pool files and occupied demo remain separate and protected.

Deploy only after mirror review and private promotion. Production source is now
administrator-owned; use a reviewed elevated source update that preserves the
installed boundary and reconciles new source pins. Keep the Bot held and S11 flags
closed while preparing static records/templates, actual process binding and
coordinated validation. Enrollment and G5 activation remain separate decisions.

Rollback restores the prior reviewed source and static registration under the
same stopped-deployment safeguards. A previous runtime cannot accept a registration
containing the new field; do not restart it with incompatible templates. Preserve
receipts and uncertain operations; do not remove sharing or rewrite SQL/provider
state as part of source rollback.

Validation covers exact accepted sharing, changed editor/audience/owner refusal,
missing authority, malformed policy, protected-exclusion/pool rejection, hash
tampering, immutable registration copies and the existing deployment/runtime tests.
No SQL schema or query changes are needed. No unrelated refactor was introduced.
