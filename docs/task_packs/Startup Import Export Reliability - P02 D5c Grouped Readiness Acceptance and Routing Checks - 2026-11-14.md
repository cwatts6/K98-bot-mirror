# P02 D5c grouped readiness acceptance and routing checks

The operator's grouped read-only receipt `0bc9a80b1ddc4fc09f75eea367a8815c` is accepted. Its SHA256 is `cfbef5cb3f83e94dd659664eff55207f66fcea133c12976287851564be1a4467`. The local adjudicator verified 41 operations, 876 returned rows, all 35 observations, 67 lineage hashes, 31 authoritative SQL source hashes, protected records and connection cleanup. Host elapsed 2.8508816 seconds costs three native seconds: **1,302 remain**, including the protected 1,000-second later-phase reserve. Windows allocation remains 50 seconds, synthetic rows 11/64, consumed input allowance 21, new inputs zero.

The catalog contains 31 tables, 277 KVK columns, 110 dbo columns, 216 foreign-key column relationships and 134 check constraints. All captured constraints are enabled and trusted. Column counts agree with source; this is not yet full per-column fixture validation.

## Retained owner

The canonical `sql_snapshot:legacy_outputs` resource is already owned by preparation `d59a7bfe-9e14-4670-8502-346b7633369a`, owner `f8314ccd-bec3-40e2-9f7b-4d013cd77f1d`, fence 4552, resource version 469. The associated retained preparation is `writing`, version 1, account/storage `p02-phase1-142c9a6cc57b4b728c3e06056b849d71`. Both observations agree. The zero active-stream count does not prove that preparation can be cleared.

Preserve it unchanged. Do not rename the canonical resource, filter foreign owners, expire state by age, or invoke historical recovery. Positive unowned-hold tests require a separately concrete preservation/restoration strategy or a candid unproven disposition. Independent offline work continues now.

## Next bounded offline group

Run the fixed `d5c-routing-weights` group after review: 33 behavioral checks and seven runner safety controls, 40 total. The fourteen planned G3 themes are covered through explicit valid controls and individual missing/scope/hash/version cases. Coverage includes:

- Original season read and passive source guard: valid read/admission, stale version, wrong source and closed lifecycle.
- Original public routing resolver and sealed-tuple validation: valid complete/explicit legacy, absent choice/selection/update/publication/config, foreign season/period/choice, config/hash mismatch, disabled routing, unsupported capability and metadata failure.
- Original export weight discovery method, imported configuration reader and exact decimal comparison: valid two-member vector, stale first/last member, absent weights/vector/imported configuration and denied metadata.
- Original public-report entry point requires metadata context closure before the inert payload callback; original stale-action read comparison refuses a changed season version.

Use exact selected AST bodies from pinned production sources without application startup. The SQL transport and snapshot context are inert models; original row decoding, hashing, models, resolver, season, imported-weight and service logic run. The payload callback is inert and proves call ordering only, not report generation. Unused mutator retry decorators on the loaded coordination class are inert; no decorated mutation method runs. Real snapshot isolation, FK behavior, permissions, lock timing and database cleanup remain separate native obligations.

One create-only pass, 300 seconds maximum and 1 MiB combined intent/result. Seven safety controls check denied network, SQL/Discord/native imports, subprocess, outside writes and swallowed forbidden-effect attempts. Stop at the first failure; preserve original intent/result. Existing broad operator approval covers a separately recorded correction/pass if necessary; never overwrite or replay an old intent. Native allowance and all consumed input allowances are unchanged by this offline group.

Files: `tests/test_p02_d5c_routing_weights.py`, `scripts/run_p02_d5c_routing_weights.py`, `.codex_artifacts/p025/prepare_d5c_routing_weights.py`, `.codex_artifacts/p025/d5c-routing-weights/packet.json`. The runner reuses the reviewed settlement runner, changing only identity/output/test-module names and remaining native balance. All prior preserved hashes carry forward, plus this readiness receipt and acceptance. Source schema pins include every referenced G3 metadata table.

## Review and closure boundaries

Security routing: **Changes**, Deep off, exact isolated Git snapshot of the new test/runner/preparation/packet/plan only, plus directly supporting code. Review before qualification; no runtime fixes. Architecture/deferred/test-selector and repository-wide tests are deferred because this is an isolated test-only qualification packet, not a PR or promotion handoff. Focused compilation, exact AST/source pin checks, independent review and the guarded pass provide the relevant evidence here. No application startup or full suite may run implicitly.

D5c remains open: C04 season/routing/weights, C05 queue/pool/holds and C06 effectful recovery. The 25 inspector checks and other accepted groups remain accepted. Seven of 73 named final action routes have final-boundary offline evidence; this group does not increment that route ledger. Remaining native G3/G4 fixtures must be reconciled against the captured catalog before preparation. D5d, D5e and D5f remain separate, and deployment is not authorized by these test approvals.
