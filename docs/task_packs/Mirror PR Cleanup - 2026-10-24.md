# Mirror PR cleanup review — 24 October 2026

## Result

All **42 open mirror PRs** inspected are earlier focused recovery branches whose
observed heads are incorporated into the final P0a aggregate tree. They do not
need another merge. The operator approved closing them as incorporated/superseded
while retaining review history and branches. **All 42 were closed on 24 October
2026** after restored GitHub access, exact current-head checks and a fresh ancestry
check against the merged aggregate. A final open-PR listing returned no open PRs
in the mirror. No branches were deleted and no comments were posted. The completed
`close-superseded-mirror-prs` follow-up is paused. Individual closure timestamps and
head identities are retained privately in `p1-pr-closure-20261024.json`.

Exact closure set: **#336–#375, #377 and #378**. This includes #356 after the
additional ancestry check below. [#376](https://github.com/cwatts6/K98-bot-mirror/pull/376)
and [#438](https://github.com/cwatts6/K98-bot-mirror/pull/438) are already merged and
are not part of this set. Product acceptance still outstanding in P0/P1 does not
require these obsolete review branches to stay open.

## Evidence and limits

- Read both pages of the [live open-PR inventory](https://github.com/cwatts6/K98-bot-mirror/pulls)
  and each of the 42 PR pages, recording their base/head branch and full observed
  commit identity. The connector was unavailable and GitHub CLI authentication
  returned 401; public browser reads succeeded. Authenticated mutation is unavailable
  through those connections in this session.
- The merged aggregate #376 explicitly identifies final reviewed mirror tree
  `2380d642425149062aca86ee38082e2a97d9c5b9`, and its commits page includes that
  correction. Its merged status and merge commit prefix `8aa9158` were visible.
- For every full observed PR head, local `git merge-base --is-ancestor <head>
  2380d642425149062aca86ee38082e2a97d9c5b9` passed: **42/42**, no exceptions.
  Thus this is an exact incorporation check, not a title/age heuristic or an
  assumption that a squash merge retains ancestry in today's snapshot mirror.
- #376's prose excludes the separately opened #356, but its final tree includes it:
  merge `c2d99326f6e77607a57af63131689c99d393b77a` has #356 head
  `498cf47b8567bc733bc66eec8492d81a15e69137` as its second parent and is an ancestor
  of `2380d642`. The current guided-recovery pack explicitly records this integration.
  This resolves that description discrepancy; #356 is also incorporated.
- These are review-lifecycle conclusions, not a new security review, current full
  regression run or certification of every historical acceptance case. Subsequent
  fixes are retained in current source; remerging an old stack is unnecessary.
- Before actual closure, recheck that the PR remains open with the same full head
  and aggregate relationship. If a head changed, review its new delta first. Preserve
  PR conversations, branches, worktrees and retained deployment/recovery artifacts.

## Reviewed inventory

Each row has the same disposition: **close as incorporated in merged #376**.
Commit links identify the exact inspected heads; no outstanding implementation is
being discarded by this classification.

| PR | Observed head | Review branch |
|---|---|---|
| [#336](https://github.com/cwatts6/K98-bot-mirror/pull/336) | [e4eacf39](https://github.com/cwatts6/K98-bot-mirror/commit/e4eacf39b2905ba2d562a6c4ee191392002b7009) | `codex/guided-read-journal` |
| [#337](https://github.com/cwatts6/K98-bot-mirror/pull/337) | [5ac2e7bc](https://github.com/cwatts6/K98-bot-mirror/commit/5ac2e7bc7496975e16c0a34735323866da2c8ad9) | `codex/guided-legacy-capture` |
| [#338](https://github.com/cwatts6/K98-bot-mirror/pull/338) | [be233f36](https://github.com/cwatts6/K98-bot-mirror/commit/be233f36bc099b0aee7f19205fbdf470c3bc1a2a) | `codex/guided-absent-retry` |
| [#339](https://github.com/cwatts6/K98-bot-mirror/pull/339) | [18f85107](https://github.com/cwatts6/K98-bot-mirror/commit/18f851077dac7d60557d8191c38ff639d7a60cca) | `codex/guided-read-close` |
| [#340](https://github.com/cwatts6/K98-bot-mirror/pull/340) | [8993b688](https://github.com/cwatts6/K98-bot-mirror/commit/8993b688c4f4d67c4536fdf5da0865eef943f3f1) | `codex/guided-probe-events` |
| [#341](https://github.com/cwatts6/K98-bot-mirror/pull/341) | [249e9665](https://github.com/cwatts6/K98-bot-mirror/commit/249e966535516e34acdf83dc778aa7e02ff2df16) | `codex/guided-capture-abandon` |
| [#342](https://github.com/cwatts6/K98-bot-mirror/pull/342) | [436047e4](https://github.com/cwatts6/K98-bot-mirror/commit/436047e4b085fd1a998ac9bff2e835087530fb64) | `codex/guided-export-skip` |
| [#343](https://github.com/cwatts6/K98-bot-mirror/pull/343) | [bf9a249d](https://github.com/cwatts6/K98-bot-mirror/commit/bf9a249de8def4490bc6180effbe6066c9d6ca56) | `codex/guided-child-restart` |
| [#344](https://github.com/cwatts6/K98-bot-mirror/pull/344) | [d18716e9](https://github.com/cwatts6/K98-bot-mirror/commit/d18716e9edc1c65f8849c4fda0d543ae9e5883bb) | `codex/guided-read-containment` |
| [#345](https://github.com/cwatts6/K98-bot-mirror/pull/345) | [bef9b5a3](https://github.com/cwatts6/K98-bot-mirror/commit/bef9b5a30bf0d479a89b794d4b4c09d290e72a30) | `codex/guided-unstarted-read` |
| [#346](https://github.com/cwatts6/K98-bot-mirror/pull/346) | [4c7c62f1](https://github.com/cwatts6/K98-bot-mirror/commit/4c7c62f14077d32c9306572b8743a2bcee8042c7) | `codex/guided-write-containment` |
| [#347](https://github.com/cwatts6/K98-bot-mirror/pull/347) | [edf480dc](https://github.com/cwatts6/K98-bot-mirror/commit/edf480dc82d0045daa0c9329d6546285962485dc) | `codex/guided-target-replacement` |
| [#348](https://github.com/cwatts6/K98-bot-mirror/pull/348) | [0cd94e41](https://github.com/cwatts6/K98-bot-mirror/commit/0cd94e41ad822909e486e6cc78d7c067d31bbbd7) | `codex/guided-config-replacement` |
| [#349](https://github.com/cwatts6/K98-bot-mirror/pull/349) | [7fd1b17f](https://github.com/cwatts6/K98-bot-mirror/commit/7fd1b17fa5e7bfcb84c89476a8b1c97f3e935290) | `codex/guided-evidence-recovery` |
| [#350](https://github.com/cwatts6/K98-bot-mirror/pull/350) | [99b4b369](https://github.com/cwatts6/K98-bot-mirror/commit/99b4b369d76a0b59793b6d367d3e5e0340fe1454) | `codex/guided-evidence-loss` |
| [#351](https://github.com/cwatts6/K98-bot-mirror/pull/351) | [03822d47](https://github.com/cwatts6/K98-bot-mirror/commit/03822d4703bd311fd670b9e3c459c6aa7d0e0ce6) | `codex/guided-proposal-loss` |
| [#352](https://github.com/cwatts6/K98-bot-mirror/pull/352) | [fb394d51](https://github.com/cwatts6/K98-bot-mirror/commit/fb394d5154b260de0a8f3d466db5924da1debd9d) | `codex/guided-refused-stage` |
| [#353](https://github.com/cwatts6/K98-bot-mirror/pull/353) | [340490bf](https://github.com/cwatts6/K98-bot-mirror/commit/340490bf4a5cfc537ad9ff11399858fba0e1164b) | `codex/guided-unstarted-stage` |
| [#354](https://github.com/cwatts6/K98-bot-mirror/pull/354) | [ec87ffed](https://github.com/cwatts6/K98-bot-mirror/commit/ec87ffedd70d9cc63696fa4465d7e5c15d1aeb54) | `codex/guided-producer-checkpoints` |
| [#355](https://github.com/cwatts6/K98-bot-mirror/pull/355) | [133d1007](https://github.com/cwatts6/K98-bot-mirror/commit/133d10074e06472057fd29dd0edba6f96a836740) | `codex/guided-rollover-admission` |
| [#356](https://github.com/cwatts6/K98-bot-mirror/pull/356) | [498cf47b](https://github.com/cwatts6/K98-bot-mirror/commit/498cf47b8567bc733bc66eec8492d81a15e69137) | `codex/guided-admission-decisions` |
| [#357](https://github.com/cwatts6/K98-bot-mirror/pull/357) | [90fe456e](https://github.com/cwatts6/K98-bot-mirror/commit/90fe456ef27eae821ff7eab445b7573483c4a6fe) | `codex/guided-rollover-replacement` |
| [#358](https://github.com/cwatts6/K98-bot-mirror/pull/358) | [a2f4ad5a](https://github.com/cwatts6/K98-bot-mirror/commit/a2f4ad5afc839be33deaa37397eb38083ac120d2) | `codex/guided-rollover-evidence-loss` |
| [#359](https://github.com/cwatts6/K98-bot-mirror/pull/359) | [d933b94e](https://github.com/cwatts6/K98-bot-mirror/commit/d933b94e03e750d7e5c256c10d471f062e2fb4de) | `codex/guided-replacement-read-admission` |
| [#360](https://github.com/cwatts6/K98-bot-mirror/pull/360) | [375b639e](https://github.com/cwatts6/K98-bot-mirror/commit/375b639ed1480c2c36a03e786fb8a418f23194a1) | `codex/guided-config-producer-checkpoint` |
| [#361](https://github.com/cwatts6/K98-bot-mirror/pull/361) | [34cdb5c5](https://github.com/cwatts6/K98-bot-mirror/commit/34cdb5c5c83742ece257fc3d7eeb720da0ae7347) | `codex/guided-config-continuation` |
| [#362](https://github.com/cwatts6/K98-bot-mirror/pull/362) | [7bee1fc6](https://github.com/cwatts6/K98-bot-mirror/commit/7bee1fc6fd39ef6c161ba026b0546041d20df277) | `codex/guided-recovery-p0a-release` |
| [#363](https://github.com/cwatts6/K98-bot-mirror/pull/363) | [064149b6](https://github.com/cwatts6/K98-bot-mirror/commit/064149b662f4e0d04e423807327ce6596c614caa) | `codex/guided-p0a-rehearsal` |
| [#364](https://github.com/cwatts6/K98-bot-mirror/pull/364) | [f8bf48c4](https://github.com/cwatts6/K98-bot-mirror/commit/f8bf48c441b11491261c6b4a23d459bb225b1d97) | `codex/guided-p0a-migration-rehearsal` |
| [#365](https://github.com/cwatts6/K98-bot-mirror/pull/365) | [cb5d439c](https://github.com/cwatts6/K98-bot-mirror/commit/cb5d439c93c201ed83cb6965133246a126a1801e) | `codex/guided-p0a-action-boundary` |
| [#366](https://github.com/cwatts6/K98-bot-mirror/pull/366) | [c2d9a961](https://github.com/cwatts6/K98-bot-mirror/commit/c2d9a961e5b483c0d08a54b4bff503a44d57ed7e) | `codex/guided-p0a-package-capacity` |
| [#367](https://github.com/cwatts6/K98-bot-mirror/pull/367) | [1f6e0c47](https://github.com/cwatts6/K98-bot-mirror/commit/1f6e0c47deba5c77501b125934d45a6f6c84c926) | `codex/guided-p0a-contract-package` |
| [#368](https://github.com/cwatts6/K98-bot-mirror/pull/368) | [84b19f54](https://github.com/cwatts6/K98-bot-mirror/commit/84b19f54a327d23098ab8edbe597c1d42264b344) | `codex/guided-p0a-coordinated-package` |
| [#369](https://github.com/cwatts6/K98-bot-mirror/pull/369) | [99ae0243](https://github.com/cwatts6/K98-bot-mirror/commit/99ae02437fe0192b1e6b81c9c503af0db4df7d06) | `codex/guided-p0a-final-qualification` |
| [#370](https://github.com/cwatts6/K98-bot-mirror/pull/370) | [1ef9d6f7](https://github.com/cwatts6/K98-bot-mirror/commit/1ef9d6f730f5fcb0fd45a458dd7eb6d156bbf0f9) | `codex/guided-p0a-capture-qualification` |
| [#371](https://github.com/cwatts6/K98-bot-mirror/pull/371) | [e5d4dd90](https://github.com/cwatts6/K98-bot-mirror/commit/e5d4dd90e2c641cee9ae00eac87b7decc3626b01) | `codex/guided-p0a-evidence-version` |
| [#372](https://github.com/cwatts6/K98-bot-mirror/pull/372) | [490c1dab](https://github.com/cwatts6/K98-bot-mirror/commit/490c1daba514d8f62c95c2cc7b9def7d72aad07f) | `codex/guided-p0a-delivery-rehearsal` |
| [#373](https://github.com/cwatts6/K98-bot-mirror/pull/373) | [56ab521d](https://github.com/cwatts6/K98-bot-mirror/commit/56ab521dcbe4c84edfedd2263bf0845eb5b806bf) | `codex/p0a-promotion-validation` |
| [#374](https://github.com/cwatts6/K98-bot-mirror/pull/374) | [8a4cb2a9](https://github.com/cwatts6/K98-bot-mirror/commit/8a4cb2a9619461d77ccdb5d73ec5022968531888) | `codex/p0a-dependency-order` |
| [#375](https://github.com/cwatts6/K98-bot-mirror/pull/375) | [9f3cadb9](https://github.com/cwatts6/K98-bot-mirror/commit/9f3cadb9da9324ef70bee785285b4631c7b75ebf) | `codex/p0a-sql-image-grants` |
| [#377](https://github.com/cwatts6/K98-bot-mirror/pull/377) | [4e9f52cf](https://github.com/cwatts6/K98-bot-mirror/commit/4e9f52cfdd4ac9e01715375868485de97b53f6bd) | `codex/p0a-ci-portability` |
| [#378](https://github.com/cwatts6/K98-bot-mirror/pull/378) | [2380d642](https://github.com/cwatts6/K98-bot-mirror/commit/2380d642425149062aca86ee38082e2a97d9c5b9) | `codex/p0a-keep-prior-restart` |
