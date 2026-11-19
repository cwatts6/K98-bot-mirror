# D5c retained-output acceptance and countdown

The corrected grouped offline batch passed all **126 checks**: 119 behavior scenarios and seven runner safety controls. The saved receipt was adjudicated without replay. Three additional final-action routes are accepted within the documented offline model:

| Route | Accepted scenarios |
| --- | ---: |
| Player-report cache-only completion | 38 |
| Configuration-only completion | 38 |
| Historical export retirement | 43 |

**Countdown: 16 of 73 final recovery routes accepted; 57 remain.** This is the final-action route countdown, not a percentage of all D5c. Inspector checks remain 25/25. D5c remains 9/12 families closed; native season/routing/weight consistency, queue/pool/hold exclusion and remaining recovery/native-effect obligations stay open. Deployment has not occurred.

## Corrections and review

The original retained-output packet never ran and remains byte-for-byte preserved. V2 adds the two missing source-file hashes and correctly models/asserts the decision timestamp. No runtime code changed. The original review-record schema error and failed completion remain in the conversation/tool history; the same review was repaired and sealed, without replacing it to conceal failure.

- Original review: `6bd9b389-0a5e-4f27-b136-e1f2de3f1373`, sealed `2026-11-14T18:17:34.006720Z`, operational blockers retained.
- Corrected five-file Changes review: `e539f83a-66f5-4501-a5cf-5f86b5809ea7`, head `8c07227887719983809ef7070d9c05fe8fb58a82`, sealed `2026-11-14T18:20:33.403215Z`. No security candidates; independent source review ready for one pass.
- Reported review usage: 1,944,254 total tokens, including 1,931,392 cached input tokens. This is tool-reported rollout accounting, not an additional execution allowance.

## Verified execution evidence

- Packet: `.codex_artifacts/p025/d5c-retained-disposition-v2/packet.json`, SHA256 `4f3fd4394c17747dd6a89dc370d8070496b1e76df89813479def7595354b9647`.
- Result: `.codex_artifacts/p025/d5c-retained-disposition-v2/result.json`, SHA256 `52bb6b096618af138b38b6205bcdfdf20844f2fc0224c3cc5f8b62f63de9b9de`.
- Acceptance: `.codex_artifacts/p025/d5c-retained-disposition-acceptance.json`.
- Current complete route ledger and handoff: `.codex_artifacts/p025/d5c-retained-disposition-closeout.json`.

All 779 preservation pins and authoritative SQL contract hashes verified. Case ordering exactly matches the packet and intent, all cases passed, all seven deliberate boundary refusals match, no unexpected boundary activity, pending tasks or extra threads remain. Intent plus result occupy 30,105 bytes, below 1 MiB. The batch recorded 0.516 seconds, below its 300-second ceiling. One offline pass was used; no test retry occurred. Normal Git HEAD and index are unchanged.

## Preserved allowances and proof limits

Native allowance remains **1,302 seconds**, including the **1,000-second later-phase reserve**. Windows-test allowance remains **50 seconds**. Synthetic rows remain **11/64**. Retained inputs remain **21 consumed, zero new**. No limits were extended, and no SQL/VM, provider, report production, import, maintenance, permission or deployment work ran.

The actual adapters, snapshot decoder, read DAL, store path/read and final DAL bodies ran against inert SQL and memory-file transports. This proves their modeled guard and disposition behavior, not native filesystem containment, SQL isolation/permissions, physical rollback, real timestamp behavior or crash recovery. Historical retirement preserves unknown SQL outcome as unproven. Existing original failures and accepted evidence retain their independent statuses.

## Next grouped work

Continue the remaining final-action route groups with exact source/branch verification. Separately finish the native fixture graph for season/routing/weights and queue/pool/hold checks using captured structure. The retained canonical owner remains protected; an absence of active streams cannot authorize its clearance. No new PowerShell batch is ready or required from the operator for this completed offline group.
