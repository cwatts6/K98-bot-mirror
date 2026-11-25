# D5c retained-output group

Status: prepared for independent Changes review, then one bounded offline pass under the existing operator approval. D5c remains open. Current final-action countdown is 13 of 73 accepted, 60 remaining; a fully accepted group adds three routes, reaching 16 of 73 with 57 remaining. The 25 inspector checks remain accepted.

## Fixed scope

- `player_report/complete_cache_only`
- `configuration_producer/complete_configuration_only`
- `stats_import/retire_historical_export`

Run original final adapter, retained snapshot decoder, read DAL, byte-verification store, capture/historical final DAL and reconciliation bodies. Positive paths preserve retained bytes and SQL evidence, write one exact decision marker and increment only the preparation version. Automatic completion respects the saved no-export intent; historical retirement explicitly leaves SQL outcome unproven.

Test missing/corrupt/extra/truncated bytes, exact length/hash, opaque keys, symbolic-link/escaped-path refusals, canonical encoding, snapshot identity/output/configuration, ownership/scope, execution/queue/stream conflicts, stale approvals, lost CAS, final-transaction changes, actor/reason bounds and reconciliation. Historical tests also verify original registration/provenance, held resources, typed-producer refusal and corrupt evidence after a saved decision. A known decision with subsequently corrupt evidence must remain unresolved, never be replayed or called not-applied.

## Proof and effect boundary

SQL connection/transaction transport is an inert, strict in-memory model. Query text and bound parameters are checked. Unexpected model errors remain separately visible. The original passive DAL read runs against the model's read context. Original final write transactions, guards and custody logic execute against this model. A read-only in-memory path/stream replaces filesystem transport; original store `_path` and `read` execute, but private directory provisioning and operating-system path guarantees are not certified. The store constructor is bypassed explicitly for that transport. Original runtime constructor executes with a non-dispatching coordinator; unused retry decorators are inert, and no retry-decorated method is invoked. Actual snapshot serialization/deserialization is retained, including typed decimal cells.

No SQL/VM, provider, import, report production, maintenance, account, permission or setting operations. No retained input file is read. Labelled synthetic bytes are fixture data, not additional input consumption. This group does not establish native isolation, permissions, crash handling or physical rollback. Existing unexplained failures and incomplete native cases retain their status.

## Bounds and evidence

One 300-second, first-failure-stop offline batch; combined intent/result maximum 1 MiB; seven independent runner safety controls. Exclusive create-new receipts, immutable source and prior-evidence pins, no implicit repeat. Existing broad approval permits a reviewed correction/additional pass if needed, with separate evidence and allowance accounting. Native allowance remains 1,302 seconds (1,000 reserved), Windows-test 50 seconds, synthetic rows 11/64 and retained inputs 21 consumed, zero new. No runtime correction is included.

Preserve the original capture-disposition failed pass, unexecuted V2, accepted V3 and 492-check result. Record this group's result before advancing the countdown. Three routes count only after all their fixed scenarios and cleanup checks pass.

## Review routing and validation

Changes review, Deep off, against an immutable review-only commit based on `a8cb33fbbf0e53ac4fe34207c8c67b3194697372`. Five changed files: test, guarded runner, packet preparer, packet and this plan. Security-sensitive surfaces are the runner's effect boundaries, evidence writes, dynamic source loading and modeled recovery effects. Review supporting source as required without a repository-wide scan. SQL contract hashes remain pinned to the authoritative SQL checkout.

Run syntax and AST-definition checks before freezing; independent operational/security review before the bounded behavior pass. Architecture/deferred/security-routing/test-selection broad validators are deferred to overall handoff: this packet changes no runtime layer, command registration or production dependency; its exact validation is the guarded batch and immutable diff check. No PR, merge, deployment or runtime readiness claim follows from this packet.
