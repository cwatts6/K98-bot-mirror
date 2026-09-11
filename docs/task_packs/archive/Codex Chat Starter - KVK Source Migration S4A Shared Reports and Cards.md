# Codex Chat Starter — KVK Source Migration S4A Shared Reports and Cards

## Archived final closeout — 2026-09-10

**S4A is complete, operator smoke accepted and merged.** Mirror [#268](https://github.com/cwatts6/K98-bot-mirror/pull/268) merged on 2026-09-10 at 16:12:39 UTC as `eba04639eced51e368d6fc7036284f25640ce871`; private bot [#575](https://github.com/cwatts6/k98-bot/pull/575) merged at 16:13:04 UTC as `021fc7adc9952ab07d21517e8e47f3966c285f7a`.
Operator candidate smoke on `055b9590e1114661ff0369c7815fbbea82661454` passed imports, registration **36/100** without drift/duplicates, **134 focused tests in 11.97s**, and **3,810 full-suite tests with 34 skipped in 134.19s**. Both pytest runs left operational logs unchanged. This closes the S4A full-suite gap; earlier stalls and passes remain historical evidence, not a post-merge rerun.
Local mirror `main` is `7baf92c7badc3f40006841046825a788bc823373`; local `production/main` is `021fc7adc9952ab07d21517e8e47f3966c285f7a`; SQL `main` remains `44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Bot and SQL checkouts were clean at closeout entry. Local pulls are complete, per operator and local refs; **nothing has been pulled to the bot machine**.
S4A pack/starter are archived. **Next: S4B Versioned Exports and Delivery in a new chat, with separate S4B G3 approval.** S4B's pack requires all pending closeout documents and both archive rename sides in its eventual separately authorized PR. Prior S3B closeout documents were included in the merged S4A PRs.
Source routing remains disabled. No bot-machine update/restart, SQL deployment, live imports/exports, Discord action or activation is needed for S4B local development. Use mocks/fake destinations unless a disposable SQL target and exact operations are explicitly authorized first; preserve retained S2A/S2B/S3B databases. Historical prerequisite wording below does not reopen completed slices.

Seven review findings were fixed in both PRs and all seven threads resolved. Separate Changes security reviews, Deep off, completed with zero findings: mirror `7e4ae070-0ce3-4444-946c-5dac9238b24d`, private `f292412a-a94d-4293-aade-559d0e2311e1`. Exact coverage and earlier implementation evidence remain below. Live SQL/Discord integration was not performed. All following approval requests, readiness exceptions and entry instructions are historical; do not execute this archived starter/pack again.

Refreshed 2026-09-10 after S3B merged closeout. **Not executed; S4A G3 pending.**
Use this only when approving this slice; G2 alone does not approve implementation.

---

I approve G3 for **KVK Source Migration S4A only**, following
[this task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S4A%20Shared%20Reports%20and%20Cards.md).
Implement and validate its exact boundary, then stop for review.
Read current instructions/core references, approved architecture including EndScanID, Phase 2B plan
and pack. Verify both repos branches/HEADs/remotes/status; preserve all existing work.
Prerequisites: S3B accepted and S4A G3; new source routing remains disabled.
S3B is complete and merged: verify mirror #267, private bot #574 and archived final evidence.
Operator post-merge smoke passed 36 tests in 9.11s, imports and registration 36/100.
Local pulls are complete; no bot-machine update/restart is needed for S4A local development.
Preserve all pending S3B closeout docs and archive moves, including untracked Markdown.
When the S4A PR is separately authorized, include the full thirteen-document carried-forward
manifest in its pack, both sides of both archive renames, repaired links and delivery evidence.
The post-review full suite stalled around 19% and remains incomplete: investigate and record
the outcome during S4A full-suite/log-noise validation; do not claim historical passes as fresh.
Use mocks unless a disposable SQL target and operations are explicitly authorized first;
preserve retained S2A/S2B/S3B databases and never use production.
Confirm evidence before edits; do not execute predecessor or later packs automatically.

Preserve B0 eligibility, exact endpoints, UTC scan start and semantic re-export deduplication.
Either endpoint may change; supplied EndScanID >= StartScanID. Equal endpoints mean zero
supported fight scores for all B0 members, with aggregates not applicable. Distinct scans
increase both ScanID and UTC; ordinary missing values remain explicit.
Interim 11−10 then 12−10; final 13−10; authorized EndScanID update to 14 itself permits replacement
14−10 without a separate correction command. Aggregate reports and daily SCANORDER stay separate.
Use exact file/test/security manifests; report canonical delivery with actual outcomes and gaps.
No pull/reset/merge/push/PR, production SQL, real imports/exports, Discord actions, restarts,
deployment or activation. No private player data or credentials in Git. Required security reviews
use Changes at exact separate repo targets, Deep off; no standard/deep scan or automatic new task.
