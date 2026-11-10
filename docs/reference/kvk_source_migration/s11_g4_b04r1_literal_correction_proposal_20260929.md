# B04R1 — one-character volume literal correction

PROPOSED FOR ONE EXACT REPLACEMENT ATTEMPT, NOT EXECUTED. Original B04 and all seals/approval/failed output retained. The assistant-authored loop used volume_mount_point=N'C:' rather than N'C:\'; that is not the volume root returned by the expected C: mount. Unmatched lookup sets @free NULL and triggers52003. This is a script defect, not evidence that free capacity is below100GiB. The initial preflight uses the correct literal. Under the sealed script this loop guard precedes the first chunk increment/materialization/hash; no new completed chunk is claimed. Only supplied error retained, no invented missing results.

Corrected file: C:\discord_file_downloader\.codex_artifacts\s11-g4-capture-preparation-20260926\commands\B04R1.sql

SHA256: 6ab63f7615507deb6b82e789667d279b6b6684cb9ffbea52a062978f657c0221

Exactly one byte inserted: missing backslash in loop C:\literal. All other script bytes unchanged, including historical B04 labels/receipt markers. Record execution as B04R1 via approved filename/hash, not by changing those labels. Local regression validates both volume predicates equal C:\; original fails and correction passes. Byte comparison confirms no other change. No SQL run or live capacity check performed.

Scope/effects/targets/digest encoding/stop conditions remain exactly s11_g4_b04_keyset_continuation_proposal_20260929.md: development9SX2VF4\K98DEV/master, database22/read-only, only KVK.KVK_AllPlayers_Raw after pilot key(13,1,44990547); <=2048source reads x1024rows;4GiB canonical bytes including pilot;4MiB report; empty source read required. No rerun of completed pilot or ProcConfig tables. Initial metadata/key/temp setup may repeat as prerequisites for this corrected attempt.

Fresh query session, SSMS query timeout600seconds, operator610seconds overall;15second cooperative chunk budget/operator20seconds. Existing window ends2026-09-29T09:23:23Z; no extension implied. Previous failed query must have returned control; don't manually clean/kill anything. Preserve full Results/Messages, partial state on error, reset timeout10seconds afterward. No disk cleanup, permission workaround, retry after new failure, automatic continuation, deployment or G5.

The original approval allowed one attempt and no retries. This changed hash plus replacement attempt requires new explicit approval even though the effect scope is unchanged. Preparation-only security-routing skip: byte-local reviewed artifact correction, no deployed source change or live operation; no broad scan/PR/predecessor tests. All broader preservation and G4 limitations remain.
