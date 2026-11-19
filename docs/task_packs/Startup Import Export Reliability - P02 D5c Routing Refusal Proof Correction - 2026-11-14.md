# D5c routing refusal proof correction

Parent and independent review of the unexecuted 40-case V1 packet found a test-proof weakness: `resolve_season_read` catches `Exception`, so a missing test dependency or unexpected inert SQL assertion could return the same unavailable reason as the intended integrity refusal. This is a qualification-harness issue, not an established runtime defect.

V2 preserves every V1 file, snapshot and manifest, with no V1 intent or execution. It retains unexpected transport exceptions independently of the resolver and requires none. It captures the original resolver's logged exception type: intended integrity cases must reach `SourceConflict`; deliberately denied/missing metadata must reach `PermissionError`/`RuntimeError`. Successful or early-unavailable cases must log no exception. Production bodies are unchanged.

The same 40 checks (33 behavior, seven runner controls) remain fixed. The runner is mechanically renamed for a new create-only output directory. Run once after completed Changes review and independent review, using Python `-I -S -B`, maximum 300 seconds and 1 MiB combined receipt. Existing approval covers this preparation correction; no qualification pass was consumed by V1. Stop on the first failure, retain its evidence, and never reuse an intent.

All V1 proof limits continue: SQL transport and snapshot context are models; payload callback proves ordering only; no original decorated mutator method runs. Neither packet proves native isolation, FK semantics, physical cleanup or publication generation. No runtime edit, native operation, new input, synthetic row or permission change. Native balance 1,302 including 1,000 reserved; Windows 50; rows 11/64; inputs 21 consumed.

Routing decision: Changes, Deep off, exact five new V2 files (test, runner, preparation helper, manifest and this plan); original V1 files are unchanged supporting evidence. Core architecture/full-suite/PR gates remain deferred under the preceding test-only plan. Final action route counts remain 7/73 and D5c C04/C05/C06 remain open.
