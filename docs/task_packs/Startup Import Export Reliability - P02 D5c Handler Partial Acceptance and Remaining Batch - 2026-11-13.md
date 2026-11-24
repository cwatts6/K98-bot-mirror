# D5c handler partial acceptance and remaining batch

The additionally approved V2 pass ran once. It passed 27 checks, failed the next
case (`producer_refusal/stale`) and did not run the final 18. The full batch is
not accepted. Partial adjudication verifies the exact passed prefix, all seven
expected boundary refusals, no pending task/extra thread, and all 619 source/evidence
pins unchanged. No SQL, VM, provider, runtime or retained-input operation occurred.

Receipt `.codex_artifacts/p025/d5c-handler-safeguards-v2/result.json`, SHA256
`14261095b9b3a075af6a8a72457bcb59173be1c6f0708b70778da0210e66cb94`, records
0.266 seconds. Intent and result total 16,669 bytes. Exact accepted/failed/not-run
case identities are saved in `d5c-handler-v2-partial-acceptance.json`. The original
failed receipt stays failed; no replay is used to convert it to success.

The test fixture passed a raw `RequestHash` byte value into the original canonical
digest. The real `ProducerRefusalDAL.snapshot` returns `_wire(...)`, which converts
binary fields to hexadecimal text before that digest is used. The failure occurred
in fixture construction, before the handler or its effect boundary. This establishes
a fixture mismatch, not an application defect. No production correction is proposed.

V3 uses that exact original `_wire` helper for the producer fixture. It preserves
the original assertion, token guard and effect boundaries. It schedules only the
19 outstanding qualification cases, plus the seven boundary controls needed for
the new runner: **26 checks in one pass**. The 20 accepted handler checks are not
replayed; the accepted prefix remains linked by its immutable receipt. V3 reuses
the reviewed inherited-only scaffold and fresh create-only evidence paths.

The complete V3 runner/test/packet/preparer and this plan require Changes review,
Deep off. Execution needs approval for one additional offline pass because the V2
one-pass allowance is consumed. No automatic repeat is allowed. The proposed command
is the existing Python 3.11 interpreter with
`-I -S -B scripts/run_p02_d5c_handler_safeguards_v3.py`.

All numeric limits stay unchanged: 300 seconds, 1 MiB combined diagnostics,
stop on the first unexpected result. Native balance remains 1,305 seconds including
1,000 reserved for later phases; Windows-test balance 50 seconds; 11/64 synthetic
rows; 21 consumed inputs and zero new. No native retry allowance is replenished.

This is still representative handler coverage, not every action path. D5c remains
9/12 families closed with C04/C05/C06 open, and all 25 inspector cases accepted.
Full worker, group membership, further action-specific guards and native season/
queue qualification remain separate obligations. No deployment is authorized.
