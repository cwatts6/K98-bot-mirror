# P02 D5c offline presentation V2 findings

## Result

The approved runner-only correction was prepared, independently reviewed and run
once. It avoided the original default-event-loop-policy startup failure. It then
stopped at the first guard self-check, before any status-card, Refresh or report
case ran: **0 passed, 1 failed, 34 not executed**.

The failing case is `guards/network`. The observed refusal was
`unlisted_import:encodings.idna`, while the intended refusal was
`socket.getaddrinfo`. V2's strengthened assertion correctly reported
`AssertionError: Wrong refusal boundary`; it did not miscount an unrelated
import refusal as a successful network test. This is another runner/bootstrap
dependency defect, not a demonstrated application defect or a C12 pass.

There was no repeat, application correction or native work. The additional
one-pass allowance is consumed. Both original and V2 evidence remain preserved.

## Evidence and preservation

- Result: `.codex_artifacts/p025/d5c-presentation-offline-v2/result.json`
- Result SHA256: `1c0d24c83f7d2584b7cf9f5d4d824cc721e1336511b6307f8122b038d941f6bd`
- Intent SHA256: `c44cc7bc06ad1aea074abb286a847a83a026d7e476e236249db0598b05c0ddcf`
- Adjudication: `.codex_artifacts/p025/d5c-presentation-offline-v2-adjudication.json`
- Recorded elapsed time: 0.218 seconds; intent/result total: 3,283 bytes.
- No pending async tasks or other test threads. All 436 preservation hashes,
  all three frozen review files, ordinary HEAD and index were independently
  rechecked unchanged after exit.
- The original failed result remains exactly
  `45cb9f6fd94a8fd787879d5669cbd8606e0d4b90a9e7015637a1654f38d851e6`.

Native allocation remains **1,361 seconds**, including the protected 1,000-second
later-phase reserve. Windows-test allocation remains **50 seconds**. The
**21-input allowance remains consumed**, and no new inputs were accessed.
All prior mutation/retry limits remain unchanged.

## Diagnosis without another execution

The saved event identifies the attempted codec import. Installed Python's
`encodings.search_function` imports `encodings.idna` on first lookup; the packet
does not preload it, so the unchanged import guard refuses it. The IDNA module
depends on `stringprep`, `re`, `codecs` and `unicodedata.ucd_3_2_0`. Its ASCII
encoding fast path comes after codec lookup; using the numeric text address
`127.0.0.1` did not avoid that first import.

The failure occurred before the intended socket audit boundary. No connection,
SQL work or application presentation case was admitted. This diagnosis is from
the receipt and installed library source; no network probe or replay was used.
Independent follow-up confirmed the codec dependency missed by the earlier
static readiness review. That review's zero security findings must not be
represented as passing functional qualification.

## Proposed next work — not performed

Prepare another version only after this handback, preserving both failed packets.
Review the complete standard-library bootstrap dependency list for all seven guard
controls and the remaining async/Mock paths, rather than relaxing the guard on
each missing module. The smallest identified correction is an explicit trusted
`encodings.idna` bootstrap import before installing guards, as already done for
UTF-8-with-signature support. Review its fixed dependency closure and pin the
relevant interpreter/library identities in the next packet.

Retain the no-default-policy loop, unchanged 35 tests, exact seven refusal reasons,
all import/network/native/subprocess/write guards, 300-second/1 MiB limits and
original preservation set. Do not allow arbitrary lazy imports or replace the
network-path check with a simulated guard call. Freeze and review the full new
packet before seeking another one-pass allowance. No further execution is covered
by the consumed V2 allowance, and no PowerShell/VM action is needed for this plan.

## Review and validation record

Changes review `759a25b5-0817-4d47-bd99-ab720798ae0d` completed before execution,
with zero reportable security findings and all three changed files plus the
unchanged tests/direct supporting paths reviewed. Exact range:
`45bc50fedbd075ecbe30006fc2783310950016a8` to
`9555f61e0d04e36b36b6c63c48b027c92c20cc33`. Source-delta/AST, syntax, manifest
lineage, case selection and whitespace checks passed. The functional pass failed
as recorded above. Scan-reported usage was 1,997,531 total tokens, including
1,988,608 cached input tokens; these are tool usage figures, not a billing estimate.

Broad pytest/conftest, smoke/registration and test-selector execution remained
excluded to avoid unrelated startup or transports. Architecture/deferred/security
routing checks were focused source review for this test-tooling-only delta; no
SQL contract change, new general deferred item, PR or deployment is included.
This findings-only addition requires no repeat runtime test or security scan.

D5a and D5b remain accepted. D5c's remaining groups, including C12, are still open.
The selected-body test design still does not prove live Discord registration,
authorization or delivery, a full ZIP/download flow, or actual Windows transport.
D5d/D5e/D5f and separate D6 release authorization remain ahead.
