# P02 D5c retry and skip acceptance

**151/151 checks passed on the first bounded execution**, followed by successful receipt adjudication. The group contains 144 behavioral cases and seven runner controls. It qualifies `export_job/retry_unstarted` and `export_job/skip_unstarted` through their original adapters and consuming DAL code with modeled SQL transport.

## Updated countdown

| Group | Accepted | Remaining |
|---|---:|---:|
| This retry/skip batch | 151 | 0 |
| Final recovery-action routes | 47/73 | 26 |
| Inspectors | 25/25 | 0 |
| D5c families | 9/12 | 3 |

The earlier 147 adapter-boundary checks remain accepted as boundary evidence; they did not advance this route count. These two routes now have additional original consuming-code evidence. No native D5c family closes from this offline group.

The accepted cases cover legacy scan-data/all-KVK retry and skip, new-source retry with original season-source eligibility, stale and duplicate requests, missing/foreign identities, version/state/epoch changes, prior attempts and streams, bounded actor/reason values, reservation ownership/fence, protecting later owners, original failure history and original input/ticket identity. The batch also checks final CAS failure, rollback after earlier modeled resource updates, and reconciliation after injected commit-acknowledgement loss without a second mutation.

## Evidence limits

Original adapter, account/resource lock calls, consuming DAL decisions, row mapping, CAS helpers and source-season guards run unchanged. SQL transport and transaction lifecycle are explicit in-memory models. The retry decorator is disabled and the publication-registration check is an identity-checked seam. Physical SQL locks, transaction durability, connection custody, native constraints, actual registration validation, provider work and subsequent worker effects remain separate. Malformed fixtures are defensive where noted; scenario counts do not represent independent branch coverage.

## Preservation and review

Execution elapsed 0.297 seconds; combined intent/result size was 29,339 bytes. The 300-second and 1 MiB ceilings remain unchanged. Adjudication checked the exact packet hash, complete ordered case list, no unexpected boundary activity, no pending tasks/threads, all 989 preservation pins, all 29 SQL pins, all five frozen files, and unchanged ordinary Git HEAD/index.

Changes review `1ba6c422-9d72-4abd-b790-6f3a6791f0e2` covered exact range `4fa2fc0bd179c2e5fd6cdd4bb72aecb68e19713b..1f5dbedc76bca8d135d477b49a32a1e54ba26b72`, Deep off. Parent and independent review found no blocker or reportable security finding. The scan was sealed at `2026-11-14T23:22:07.893417Z`. Measured review accounting: 1,954,139 total tokens, including 1,946,368 cached input tokens.

- Acceptance: `.codex_artifacts/p025/d5c-export-admission-acceptance.json`.
- Countdown: `.codex_artifacts/p025/d5c-export-admission-closeout.json`.
- Frozen packet and exclusive intent/result: `.codex_artifacts/p025/d5c-export-admission/`.
- Review snapshot and completion summary: `.codex_artifacts/p025/d5c-export-admission-review-snapshot.json` and `d5c-export-admission-review-completion.json`.

Original evidence is unchanged. Inputs remain **21 consumed, zero new**; synthetic database rows remain **11/64**. Native allowance remains **1,260 seconds**, including the **1,000-second later-stage reserve**, and Windows allocation remains **50 seconds**. No native operation, production/source correction, permission change or installation occurred. No limit extension was needed.

## Next grouped checks

1. Original publication verification and damaged/absent repair admission: three export routes, including exact proof consumption, ownership and immutable repair receipts.
2. Replacement/rollover authority transitions and private-evidence restoration/attestation for the remaining routes.
3. Native C04/C05/C06 obligations, then later D5 slices and the separate deployment decision.

Existing approval continues to cover preparation, corrections, review and bounded offline passes. The operator need only act when a reviewed native PowerShell packet is ready. Do not rerun any acknowledged prior attempt. This is qualification evidence, not a PR, deployment or completed D5c claim.
