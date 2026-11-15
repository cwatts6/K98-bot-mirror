# P02 D5c session context correction - 2026-11-12

Status: **V2 readiness refused; V3 tested and reviewed, ready for one manual handoff.**

The V2 receipt `d5c-readiness-v2-result-645fae84fbef447abe45c728ac61f3f4.json`
matches SHA256 `3B24D3CF6603BC8D23BF73F32B8536FEB14E6D9072A57403850EB167A582D2D8`.
It records seven client statements and four returned metadata rows. The exact
copy identity passed. The context refusal was `TranCount=0`, implicit mode off,
`OptionsMask=22328`, `XactState=1`, on the expected database and session 63.
No report, maintenance child, producer or input ran.

The work connection was disposed and its captured session birth was absent.
The observer reused session number 63 with a different login time and connection
ID; number reuse is not evidence that the original connection remained open.
Observer disposal was acknowledged. The borrowed PSSession and VM isolation
were preserved. Full host elapsed time was 0.9491101 seconds: debit one second,
leaving **1,478 native seconds** and 478 seconds of the proposed D5c allocation.
The 21-input allowance remains consumed. Original V1/V2 scripts, manifests,
intents and receipts remain intact. The V2 adjudication seals their bindings.

## Diagnosis and equivalent boundary review

This context was already established by the accepted D5b session investigation.
See the [ownership diagnosis and continuation record](Startup%20Import%20Export%20Reliability%20-%20P02%20D5b%20Ownership%20Diagnosis%20and%20Recovery%20Plan%20-%202026-11-11.md),
the preserved session-observation receipt ending `433a9da3547e46088d9ff2e907e9b977`,
and `Assert-Autocommit` in `scripts/resume_p02_d5b_post_import.ps1`.
The new D5c collector failed to carry forward that established lab handling.
Do not infer a general SQL Server defect or claim all autocommit queries behave
this way. No new native diagnosis is needed merely to reproduce the same state.

Authoritative SQL `dbo.usp_RunMaintenance` and `dbo.usp_update_stats` require zero
transaction depth and implicit mode off. Their production guards are unchanged.
D5b report/continuation adapters additionally reject doomed state. Review found
the equivalent D5c pre- and post-context boundaries; V3 validates both with:

- Exactly one complete record, expected database and captured session ID.
- Numeric transaction count zero and implicit mode false, confirmed by the option bit.
- Numeric `XactState` limited to 0 or 1; reject -1, unknown, null or mistyped values.
- Stable database, transaction depth, options, implicit mode and session identity
  across the two observations. Preserve each raw XactState in evidence; its
  allowed 0/1 variation alone does not mean the session or options changed.

This is a lab collector correction, not a runtime or SQL change. No commit,
rollback, isolation setting, permission grant or extra query is introduced.
All 27 manifest statements, expected preimages, resource/row/receipt limits and
physical closure checks remain unchanged. Fixed-name ODBC inventory from V2 is
retained. V3 uses a separate one-shot intent and result path, verifies both prior
failure receipts, and starts its ledger at 1,478 seconds.

## Tests and concrete handoff gate

**63 offline PowerShell 5.1 checks passed.** In addition to the retained registry,
serialization and reader tests, the new cases accept the actual V2 observation
and states 0/1, reject wrong database/session, explicit or implicit transactions,
doomed/unknown state, missing/null/mistyped fields and invalid cardinality, and
verify raw state preservation plus stable option checks. No SQL, VM or registry
collection ran during tests. The manifest SQL/preimages match the prior packet.

Prepared files:

- `scripts/collect_p02_d5c_readiness_v3.ps1`, SHA256
  `73648404B306E962E407BAF581BD626DB2CB3820244F2D0D32DFEE6B545B4DAE`.
- `.codex_artifacts/p025/d5c-readiness-v3-execution-packet.json`, SHA256
  `25cca031e83bb7c5f27a8f7f769e0985df708eac3123d6e309b2034452f657fe`.
- `tests/validate_p02_d5c_readiness_v3.ps1`, SHA256
  `F880D8B2DC19F6BD1BEDAFC76D08248D40E0CA57610E1E779AB9F63DAAFAD7FA`.

Security routing is Changes review of these three versioned files against V2,
Deep off, before manual handoff. No SQL repository change. Continue under the
existing bounded D5 authorization once reviewed; no new exception is required.
Run once in the same authenticated console, with a host Stopwatch around the
whole invocation and the unchanged 60-second ceiling. Adjudicate the receipt and
full elapsed time before any next native packet. Refusal or unknown cleanup
stops dependent work; never reset an earlier intent or rerun an old packet.

The Python architecture validator is inapplicable to the PowerShell/JSON delta.
The selector and document/security-routing/whitespace checks apply. Broad pytest,
application smoke imports and registration/schema tests do not cover this
isolated collector change and remain skipped in favor of the focused 63 checks.
D5c and D5d/e/f remain open; this correction does not imply native qualification.

Changes review `04c198dc-c47e-4cd9-b7f9-641028e4ac8d` is complete with zero
findings and all three files covered, at range
`8326e07aaf2427dd9a0c3eec0eb0f6eead4c5bf8..a15e23e0839693ee2277221dd22ead44891f1fc4`.
The independent collector/manifest review found no concrete next-execution
blocker after reviewing all gates, empty results and physical cleanup. Parent
review covered the validator. Completed scan usage is 2,155,203 total tokens
including cached input; this does not consume native rehearsal time. Source
review cannot replace the returned native receipt. Original hashes, document
links/whitespace, scoped Git whitespace, deferred and security-routing checks
passed; the selector ran with the skip rationale above. No branch/ref or remote
was changed by the separate review snapshot.
