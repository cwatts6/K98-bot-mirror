# P02 D5c corrected offline pass findings - 2026-11-11

Status: **the single approved V2 pass stopped during pytest configuration.
Zero cases collected or executed; D5c remains unqualified.**

This updates the [preparation findings](Startup%20Import%20Export%20Reliability%20-%20P02%20D5c%20Offline%20Preparation%20Findings%20and%20Readiness%20Packet%20-%202026-11-11.md)
without replacing the original failure or changing its evidence. The user
approved one corrected offline pass, preserving the five-minute and 1 MiB
ceilings and requiring findings before native work or runtime correction.
That one attempt is now consumed. No second attempt followed.

## Result and cause

The frozen V2 runner and current test matched their reviewed hashes. Pytest
returned internal-error code 3 after approximately **0.734 seconds**. The host
shell reported exit code 1; these are distinct recorded values. Pytest reached
its logging plugin's configuration hook, which constructed a file handler.
The audit boundary refused the attempted write outside the owned artifact
directory. The traceback records the logging hook, file-handler open and
boundary refusal. It does not record the destination path.

The installed plugin uses `get_option_ini(config, "log_file") or os.devnull`
and opens the handler even when no file logging was requested. The repository's
pytest configuration has no `log_file` setting. Therefore the Windows null-device
fallback is the source-supported explanation, not a dynamically captured path.
The previous capture-plugin failure was not encountered on this attempt; this
does not prove that all remaining bootstrap paths are compatible with the guard.

No collection manifest or JUnit results exist. The repository-module record
contains only the runner. All **418 planned cases remain unexecuted**, including
the 73-pair controls and selected existing admission/saturation tests. This is
a test-tool setup failure, not an application assertion failure or a D5c pass.

## Evidence and limits

Private evidence is under
`C:\discord_file_downloader\.codex_artifacts\p025\d5c-offline-preparation-v2`:

| File | SHA-256 |
| --- | --- |
| `run_offline.py` | `bc178bc30ae0de1414130bc9e587a8f52d354c870b284da55a94b0fc44151e0e` |
| `execution-intent.json` | `e4ff630d04483ff6abbe7910fc5064597213e05719dec93c6243d17d54760684` |
| `run.log` | `2017b1084bf66614bf493a8ae735d13be15e2b8618e93bcc074e79879f5faaeb` |
| `result.json` | `45e10bc2a10360d5770d382b4837feca5562bd883655001eae85c08ca0853733` |

`d5c-offline-v2-adjudication.json` records independent post-run verification:
all **148** intent source/evidence bindings and all **nine** prior preparation
artifact bindings still match. V1 evidence, pre-lint test bytes, V2 runner,
current tests and the declarative readiness packet are unchanged. V2's directory
totals **35,991 bytes including the runner**, below 1 MiB. Its intent's historical
"draft; new run requires approval" label is retained byte-for-byte; the user's
subsequent explicit approval authorized this single execution.

No native SQL/VM/pipe/file-lock operation, runtime correction, permission change,
input read or replay occurred. The **21-input allowance remains consumed**;
**1,480 native rehearsal seconds remain**. No failed receipt, completed D5b claim
or original failure history was reset or replaced.

## Next concrete preparation step

Review the remaining default pytest bootstrap plugins together before preparing
another runner. The demonstrated correction candidate is to disable the unused
logging plugin (`-p no:logging`) alongside the already-disabled capture plugin.
The selected four test files contain no `caplog`, `capsys` or `capfd` dependency.
Retain the capped runner output, exact selected assertions, collection manifest,
native/import/write guards, first-failure stop and existing time/size limits.
Do not allow writes to the null device or operational logs merely to get past
setup. Prepare any correction in a separate evidence directory; preserve V1/V2.
This source plan is not a further execution authorization. No V3 was created or
run during this approved pass, and no runtime repair is indicated by this result.

The native readiness packet remains declarative, unchanged and held, SHA-256
`cda42134aafddc6b383f4191bfe8d7c377ca9134ac360dd806157316061a1fe2`.
Offline validation and executable review are still required before a native
handoff. All native coverage gaps in the preparation findings remain open.

## Validation disposition

This turn changes only findings/status documentation and generates execution
evidence. No executable source changed. Document links/whitespace, deferred-item
and security-routing validation apply; architecture/runtime lint and application
tests are not repeated after the authorized first-failure stop. The path selector
is used for the documentation delta; broad smoke imports, registration and full
pytest remain excluded by the offline boundary. Security scan is skipped for
this documentation/generated-evidence-only delta. The earlier executable
Changes review remains pending before native handoff; no review-pass claim is
made and no repository-wide or Deep scan is selected.
