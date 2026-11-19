# P02 D5c rights V2 review acceptance and handoff

The original rights inventory remains incomplete. Its receipt and failed packet
are preserved. No rights query ran; both SQL connections closed. Nine final
preservation observations were not reached and are not retrospectively credited.
See the Rights Cache Failure and V2 Plan dated 2026-11-12 and immutable
`d5c-rights-inventory-failure-adjudication.json` for the evidence.

## Reviewed correction

V2 removes six unrelated volatile-cache observations and their nonempty gate.
All 24 non-cache preservation observations and the three bounded rights queries
remain unchanged. It performs no mutation, impersonation, permission change,
workload, cache warmup or maintenance repeat. This is within existing read-only
authorization; authenticated restricted-access testing remains unqualified.

286 offline PowerShell checks passed. Architecture, deferred-item and security
routing validators passed; the test selector ran; frozen-range whitespace checks
passed. No Python actor or application runtime change is introduced; full pytest,
app imports and command-registration suites are not applicable to this collector.

Changes review, Deep off, completed and its sealed result was read back:

- Scan: `c23248b1-7f77-43fc-a4bd-04c60c11e5aa`.
- Base: `2f368a335e05f3aac2d7d091eaa64c29a72b7313`.
- Head: `e8ee2d47b06d583ee1a74a6a0752766223a592e2`.
- Three files covered: V2 collector, offline validator and correction plan.
- Sealed: `2026-11-12T19:17:09.898470Z`; complete coverage, zero findings.
- Parent derivative/source review with dedicated preflight worker; this is not
  represented as an independent implementation review.
- Review draft rejected repository paths as artifact receipt references; the
  draft was corrected before finalization. Completion was called once and passed.
- Tool-reported usage: 1,973,077 input tokens, including 1,866,496 cached input;
  4,307 output, including 380 reasoning; 1,977,384 total across two threads.

The ordinary checkout was not switched to the isolated review commit. All three
working file hashes matched the frozen snapshot immediately before handoff.

## One-shot console handoff

Use the existing elevated Windows PowerShell 5.1 console and its authenticated
`$global:D5bReportSession`. V2 intent was absent at handoff; no V2 native execution
has been performed by this process.

- Script: `scripts/collect_p02_d5c_rights_inventory_v2.ps1`.
- Script SHA256: `906a7e0b04f57d6c3ffcc42416a5e2824fc9c8775abb7a1f4498617dd644f02a`.
- Manifest: `.codex_artifacts/p025/d5c-rights-inventory-v2-execution-packet.json`.
- Manifest SHA256: `5d467371677ce601c93788cd6e981971c338aa06ce8ef44a399a7e9dce9e4ace`.
- 33/48 reserved client commands; 779/2,048 planned maximum returned rows;
  unchanged 512/result, 1 MiB receipt and 128 KiB manifest caps.
- Balance before attempt: 1,414 native seconds; 50 Windows-test seconds;
  21 inputs consumed, zero new inputs. Preserve final 1,000 native seconds for
  later slices. No isolation, writer or maintenance retry is available.

Run once, measure whole host elapsed time, return the summary and receipt path.
Stop on error/incomplete output; cancel and report a hang before 60 seconds.
Do not rerun the original packet, change rights/settings, reset work or delete
evidence. Adjudicate the new receipt before any further native step or concrete
access-exception proposal. D5c and later D5 slices remain open; this is not
production deployment or authorization to deploy.
