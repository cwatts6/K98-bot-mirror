# Manual copy reported complete — destination verification next

Operator reports all 119 files copied into the existing media directory on 9SX2VF4. Statement retained in `manual-copy-completion-20260928T135010Z.json` under the capture evidence root. Record this as operator attestation, not verified membership or hashes. The full backup was previously separately reported copied.

LG01 completion/output was not supplied before transfer, despite the requested receipt-first sequence. Its outcome and timing remain unproved; do not infer it succeeded or request a source operation rerun to fill that gap. Preserve any later supplied LG01 receipt as supplemental provenance. Independent comparison of all destination bytes against accepted ST01R1 is the next required check and does not depend on assuming how copying occurred.

Next is already-approved ST04, once on 9SX2VF4. `commands/ST04.ps1` is a byte-identical saved-file alias of approved `ST04.ps1.txt`, SHA256 `65899aafd070bf1b3fc001fc51115645d980d5238afa05b7dd0e8003c7bc6e3c`. No behavioral change. Use a single hash-guarded invocation rather than multiline console paste. No file transfer to production is needed.

ST04 reads eight named directory boundaries, checks free-space floor, examines at most 120 immediate media entries and hashes exactly the 119 expected files if guards pass. Content read total on success is 2,815,180,800 bytes. Same 180-second per-file/600-second total cooperative limits and operator cutoff 190 seconds/file or 610 seconds total. It has no progress UI and emits JSON only at the end; typical paced runtime about 4.5 minutes. Do not treat quiet console as permission to extend the cutoff. Blocking I/O cannot be forcibly interrupted by its internal checks.

Stop on error/incomplete output; no retry, move, delete, overwrite, recopy or cleanup. Return the JSON as a text attachment. Assistant must compare every set ID/name/length/SHA256 to ST01R1 before accepting staged bytes. ST04 Completed alone does not establish equality. No SQL media metadata/readability/integrity or actual restore is authorized by this verification.

Original ST03 access denial and manual-route operator confirmation remain retained separately. No marker success or permission change is inferred. All seven G4 proofs and actual restore remain incomplete; rollout/G5 unapproved. Existing maintenance window and deferred/withdrawn scope remain unchanged.

Validation: original staging command seal checked; execution alias byte equality verified; original pending/evidence preservation checked. Local preparation only, no destination-media access by assistant.
