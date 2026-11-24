# P02 D5c rights cache failure and corrected inventory plan

## Preserved failure and verified boundaries

Receipt `d5c-rights-inventory-result-f511382963ac43a593cd2cc94cd8ad8a.json` matches
SHA256 `25ffad8ad7d647c1b66826f04dfa9e914693272a8c29ba1ea641c8424decc635`.
It remains incomplete. The collector stopped at `cache_configuration`, which
returned zero rows. None of the three rights queries ran. The five later cache
queries and all nine paired poststate observations were not reached. Do not claim
those observations were made or infer why the cache record was absent.

All captured initial protected records match the accepted reader-first result.
22 reserved command units and 52 rows are accounted for. Both SQL connections
disposed, exact work-session birth absence was observed, no other copy session
was present and no cancellation occurred. The borrowed PowerShell connection and
VM isolation checks passed. No Python actor, maintenance or other workload ran.
The source packet contains no account/data/permission/setting mutation.

Host time 0.7231229 seconds debits one: **1,414 native seconds and 50 Windows-test
seconds remain; 21 inputs consumed, zero new inputs**. No isolation, writer or
maintenance retry. Failure adjudication is saved separately in
`d5c-rights-inventory-failure-adjudication.json`. Original script, manifest, intent,
receipt and earlier accepted maintenance evidence remain unchanged.

## Diagnosis across the affected collector

The rights collector inherited six current-cache queries and a nonempty-cache
gate from the older maintenance-evidence collector. That was a scope error: a
fresh cache entry is not a prerequisite for observing existing access mappings.
Microsoft documents that procedure-statistics rows last only while their plans
remain cached; removing a plan removes its statistics row. See the
[procedure-statistics contract](https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-views/sys-dm-exec-procedure-stats-transact-sql?view=sql-server-ver16).
This explains why the gate is not durable; it does not establish the cause of
this particular absence. Eviction, recompilation, restarts or other causes are
not asserted. No cache clear, warmup or business rerun is proposed.

Historical cached-plan evidence remains valid only for its recorded observation
instant. Its accepted receipts, original failure history and durable maintenance
rows remain pinned. V2 does not reconstruct or refresh that historical proof.
Both recently accepted account-order packets already omit these six cache reads;
the correction applies that same boundary to unrelated rights preparation.

## Concrete correction and execution scope

Create a separate V2 packet and intent. Remove all six cache queries and their
nonempty gate from this rights inventory. Retain all **24 non-cache preservation
observations** unchanged, including every paired poststate check, and the same
three rights queries with the same row caps and catalog scope. This fixes the
whole inherited cache dependency rather than bypassing only configuration.

V2 starts with fresh identity/resource/protected-state checks, reads the existing
four principals, inherited roles/public and relevant explicit permissions, then
completes paired preservation and physical SQL cleanup. Later state cannot recreate
the first attempt's missed final observation instant. Missing mapping/visibility
remains inconclusive; no authenticated restricted-path or effective-rights pass
is inferred. No impersonation, grant, account creation, data/option change or
business workload is included. Existing read-only authorization covers this
corrected inventory; no original native packet is rerun.

27 metadata statements plus six connection/cancellation units = **33/48**.
Planned returned rows fall from 815 to **779/2,048**; maximum per result remains
512. All three new rights-query bounds stay 4/128/512. No limit rises. Whole
packet remains 60 host seconds, query timeout three seconds, resource floors and
1 MiB receipt/128 KiB manifest unchanged. Windows-test allowance is unused. The
failed receipt becomes an additional immutable lineage prerequisite.

## Validation and handoff gate

286 offline PowerShell checks passed: preserved non-cache observations/parameters/
caps/expected state, cancellation and custody helpers, exact rights queries and
role scopes, original lineage, lower command/row totals, absent cache dependency,
no mutation/process/impersonation, original incomplete disposition and rejection
of an extra statement. No application runtime or SQL source changes. Full pytest,
app imports and command-registration suites are skipped for this isolated
read-only collector; no Python actor is introduced. Run repository validators,
explicit selector and whitespace checks. Complete an immutable three-file Changes
review, Deep off, before console handoff.

Wrapper `scripts/collect_p02_d5c_rights_inventory_v2.ps1` SHA256:
`906a7e0b04f57d6c3ffcc42416a5e2824fc9c8775abb7a1f4498617dd644f02a`.
Manifest `.codex_artifacts/p025/d5c-rights-inventory-v2-execution-packet.json`
SHA256 `5d467371677ce601c93788cd6e981971c338aa06ce8ef44a399a7e9dce9e4ace`.
Manifest size 43,690 bytes. V2 has not run. Stop on error/incomplete result,
preserve evidence, and do not retry, reset work or change settings. Adjudicate
the V2 receipt before any further native step or access-exception proposal.
