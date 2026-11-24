# H14 receipt reconciliation — 2026-09-27

Operator-supplied MINI_AMD output reports completion from 09:25:30.4995402Z to 09:25:30.5167559Z, stopwatch elapsed 20 ms. Reported timestamps fall within the approved 09:22:49–09:42:49 UTC window; stopwatch and approximately 17.216 ms UTC endpoint duration are below 20 seconds. Preserve these distinct clock fields. One approved file is present, below the 64 MiB cap. No error was supplied; Completed is not independent execution attestation or an OS exit code.

Raw JSON and prompt are retained in `.codex_artifacts/s11-g4-capture-preparation-20260926/received-H14-20260927T092554Z.txt`. Filename time is receipt recording, not execution or file modification time. This additive record updates H14 awaiting-output status without altering historical approvals or seals.

## Observed executable pin

- Path: `C:\Program Files\Microsoft SQL Server Management Studio 22\Release\Common7\IDE\SSMS.exe` (matches H13's path).
- Bytes: 900496.
- SHA256: `935b24379389e8260ac0d02d5e77402b005fce12c72b0ed2894a4138a6864fb7`.
- FileVersion: `22.10.12210.168 built by: stable`.
- ProductVersion: `22.10.12210.168`.
- Attributes: Archive; SizeAndMtimeStable=true; last-write UTC retained in raw receipt.
- Owner: BUILTIN\Administrators.

Retain the UI's 22.10.1 release label and the executable resource's full build versions as distinct fields. No independent vendor hash, signature verification or release-to-build provenance has been established. The result provides a point-in-time observed file pin, not vendor authenticity, loaded-memory equality, full dependency integrity or lifetime process binding.

The supplied SDDL grants SYSTEM and Administrators full access, with 0x1200a9 entries for Users/application-package principals. No Authenticated Users Modify entry appears in this sampled leaf DACL. This does not certify parent-path protection, effective access, absence of all other writable paths or atomic ACL/content binding. It does not resolve the separate broad-write ACL gaps already observed on Bot and SQL scripts. No ACL change is authorized.

## Next boundary

U01R1 remains stopped because maximized PowerShell obscured SSMS; the corrected state binding did not recur as an error. No timeout was observed. The operator was asked to foreground SSMS without changing query/connection settings. Readiness alone is not a silent retry authorization after the approved stop condition; a new bounded UI attempt must be explicit. H14 completion does not authorize SQL, a new connection, timeout/security-setting changes or a failed SQLCMD-route retry.

The SSMS path/hash/version observations are now retained, but timeout/connection configuration and the concrete SQL observation envelope remain unresolved. All seven typed G4 proofs and actual restore remain incomplete. Preserve isolated hotfix, same-account/admin-owned operation, original pending/recovered files, deferred memory cause, withdrawn collector and separate KVK/view-rehydration issues.

Validation: local JSON parse and exact operation/host/path/window/size/output/command-hash comparisons; original evidence and prior seals verified unchanged. Runtime tests, pre-PR validators and new security scan are skipped for this additive evidence-only record; no application/configuration/permission change or PR.
