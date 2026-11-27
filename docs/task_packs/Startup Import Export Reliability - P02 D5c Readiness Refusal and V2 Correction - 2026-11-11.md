# P02 D5c readiness refusal and V2 correction - 2026-11-11

Status: **Original readiness refused before SQL; corrected packet reviewed for one handoff.**

The returned receipt `d5c-readiness-result-02dc6276b98343cfb2c017673d95495a.json`
matches SHA256
`AC5E1A834B9369F701F1290C333A484FD7E5ED0C3517A6888252C5E34A6ACEBA`.
It records zero SQL statements/rows and SQL closure `not opened`. The unchanged
collector source opens SQL only after registration collection succeeds. The
borrowed session and VM isolation were preserved. There was no workload or input
consumption and no permission, installation or ownership change.

The host measured 0.7515414 seconds for the complete invocation. Debit one second:
**1,479 native seconds remain**, with 479 seconds of the proposed D5c allocation
remaining. The 21-input allowance stays consumed. The shorter worker clock does
not replace the full host measurement. Preserve the original script, manifest,
intent and failed receipt; their hashes are sealed in
`.codex_artifacts/p025/d5c-readiness-first-adjudication.json`.

## Cause and bounded correction

The original collector enumerated all ODBC driver registrations in both registry
views. Three 64-bit SQL registrations were followed by unrelated 32-bit Access,
Excel, text, dBase, Paradox and Oracle registrations. Those exhausted the unchanged
16-record cap before SQL was opened. This is an overly broad inventory selection,
not evidence of a missing SQL driver or a database failure.

V2 reads only three exact driver names in each view: `ODBC Driver 18 for SQL
Server`, `ODBC Driver 17 for SQL Server`, and `SQL Server`. The dedicated candidate
factory names Driver 18. Six explicit present/missing records are sufficient to
inventory these candidates. Do not label the result a complete ODBC census or
infer a working Python/driver connection from registry metadata.

Keep the existing 16-record ceiling and path/value limits. Do not enumerate
unrelated ODBC values, expand registry environment strings, invoke Python or load
driver libraries. Every opened registry key is disposed; missing registrations
remain explicit. Python registration collection, SQL statements and preimages,
identity/session/resource gates, cleanup rules and receipt caps remain unchanged.

Files are separate from V1:

- `scripts/collect_p02_d5c_readiness_v2.ps1`.
- `tests/validate_p02_d5c_readiness_v2.ps1`.
- `.codex_artifacts/p025/d5c-readiness-v2-execution-packet.json`.

V2 verifies the original failure receipt before admission, creates a new one-shot
intent and uses separate receipt names. Its budget starts at 1,479 seconds. A
host Stopwatch must again wrap the entire invocation; final adjudication debits
the ceiling of that full elapsed time, including orchestration and cleanup.

## Validation and execution gate

The PS5.1 parser and **42 offline checks pass**. Tests use fake registry keys and
readers, never the host/guest registry or SQL. Cases cover more than 16 unrelated
registrations, both views, missing candidates/keys, invalid types and long paths,
read exceptions, the unchanged cap, disposal and unchanged SQL/preimages.

The first expanded validator failed when its new full-statement comparison used
the row canonicalizer on an empty parameter object. Preserve that failure and
exact test source in `d5c-readiness-v2-offline-first-failure.json`. The corrected
validator compares the two parsed manifest structures directly as JSON; the
collector's canonicalizer is unchanged. This was offline and consumed no native
time. No application runtime correction was made.

Security routing: Changes review of exactly the three V2 files against the prior
review snapshot; Deep off. No SQL repository changes. Do not hand off the packet
before that review completes. The existing broad D5 continuation authorization
covers this narrowed read-only correction; no new permission/resource exception
is needed. One console invocation follows review, then receipt adjudication
before any dependent native work. Stop on refusal or unverified cleanup; never
reset the old intent or repeat an old script.

All prior resource/time/row/output constraints remain in force, including the
60-second readiness packet ceiling and no post-start eight-GiB free-RAM gate.
The result will determine feasible later D5c cases; D5d/e/f remain open.

Completed Changes review `330ed4d0-5c5d-4dae-ab71-2a7bf22494b7` covers all three
files at range `4d128908c0f332b41c9b136fb12cc2bce281e172` to
`8326e07aaf2427dd9a0c3eec0eb0f6eead4c5bf8`, with zero findings and no deferred
coverage. The completed scan records 589,280 total tokens, including cached input;
this is review usage, not native execution time. The separate review snapshot
changed no branch/ref or remote.

Final execution bindings:

- Collector SHA256 `FBEFD5D65BC2EAA4DA21C4A20EA6FC2916E0621DCADAF31B2B6F1328D3B502AE`.
- Manifest SHA256 `a5092ad58b4b314f56786989710ab40c3f86e841f684db89efe33b6ad417436c`.
- Validator SHA256 `67AD2C146073B81B8BEDB2854E4C19CEEE35ACAB82C9A8DE91D949463063C9A1`.

Scoped whitespace and security-routing checks passed. The test selector ran;
its generic full-suite, application-import, registration and release-schema
commands are skipped because this isolated PowerShell correction changes no
application runtime, command registration or schema. The 42 focused checks and
unchanged SQL/preimage comparison cover the correction. The Python architecture
validator is not applicable to the PowerShell/JSON delta. No native V2 execution
is claimed before the operator returns its receipt.
