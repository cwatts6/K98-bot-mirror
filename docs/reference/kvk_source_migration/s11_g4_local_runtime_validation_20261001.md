# S11 local protected-runtime validation — 2026-10-01

Chris explicitly approved continuing local development validation, testing and proving without repeated approval questions. This turn completed native synthetic tests, corrected the operational launcher, inspected bounded dependency metadata and executed the reviewed **inactive source-only** RDY-P01 stage. Production, credential transfer, SQL installation, registration, real exports and G5 remain outside this result.

## Completed local result

RDY-P01 completed once at2026-10-01T12:57:59.6435916Z (13:57:59London): exit0, empty stderr, confirmed child termination, complete capture, SOURCE_COPIED_INACTIVE.

- Destination: `C:\K98-S11-Validation` on9SX2VF4.
- 42 directories and 549 Python source files; 7,287,826 source bytes.
- Source inventory and every copied hash matched;591owner/DACL/reparse readbacks passed.
- Creation supplied the protected DACL atomically. Chris SID `S-1-5-21-3167111192-3307161013-4064290451-1001`, SYSTEM and Administrators have FullControl. No workspace permission change.
- config,evidence,credentials directories remain empty. No key read/hash/copy/move and no application/runtime start.
- Observed child elapsed2628ms, peak sampled working set198,180,864bytes, stdout266bytes, stderr0bytes. Working-set monitoring is sampled, not a kernel hard quota.

The root now exists and must be preserved. **Never rerun the one-shot provisioning command or clear/reuse its attempt directory.** Source and evidence are retained for later explicitly bound stages. This is a local source installation only, not an operational S11 deployment, Python dependency installation or any of the seven completed typed G4 proofs.

## Tests and corrected launcher

Native synthetic fixture passed creation-time protected owner/DACL, inherited file rights, duplicate-directory refusal, duplicate-file refusal and preservation of a partial failed tree. The fixture remains under `.codex_artifacts/s11-runtime-validation-20261001/native-fixture-attempt01`; do not delete it.

Independent review identified original launcher problems: output could be lost on timeout, caps were posthoc rather than bounded streaming, and termination success was not recorded. v2 uses bounded streaming captures and saves the captured prefixes/process receipt on incomplete outcomes; it records termination and capture completion. It enforces stdout65536bytes/stderr8192bytes and observes a512MiB child working-set threshold. It kills only its owned process tree on timeout/overflow.

Five synthetic capture tests passed: normal exit, nonzero exit, timeout preserving prior output, stdout overflow, stderr overflow. The actual provisioning script also passed denied-approval refusal before target reads/writes. Native target creation ran only after these checks and corrected-script review.

The corrected independent review found no blocker for a fresh source-only attempt. A residual **retry-only evidence behavior in executed v2** remains: invoking the launcher against an existing incomplete evidence directory without its launcher receipt can append that receipt. This was avoided by verifying a fresh first attempt and running once. Never replay or alter the executed v2 seal. A separate v3 draft gates receipt creation on a returned child result, so helper refusal cannot append to old evidence. Its synthetic replay-refusal test passed without starting a child or changing old evidence. The first fixture's final assertion hit PowerShell scalar Count handling; that failed harness and its evidence remain preserved, and corrected attempt02 passed. v3 has not been executed against the runtime target.

Security routing: Changes only, Deep off. Artifact-only baseline was unsupported by the native scan, so review is a bounded independent assessment with explicit hashes; **no canonical completed Changes scan is claimed**. All prior scans and original draft/seals remain preserved. The parser's earlier copied-baseline review qualification also remains open for final delivery review.

Final bounded v3 review confirmed the replay residual resolved with no new blocker in the two-line correction. Launcher SHA256 is ed7a63a7831ebb326a65c8830cf3ad4f4568720d24d764f647e590791ad82a00; four supporting files individually match reviewed v2 hashes. The v3 review is retained separately. This closes the helper correction, not permission to replay provisioning into the existing target.

## Dependency findings

The current requirements.txt declares94entries. Historical requirements-freeze.txt differs and was not substituted. Under isolated Python `-I -S -B`, bounded reads of selected `.dist-info` metadata found no declared distribution metadata in the base Python site-packages and80declared names in the workspace venv.14declared names were missing from that selected metadata, including pywin32;51observed pinned versions differ from requirements.txt. py-cord metadata says2.7.2, without retained direct-url commit provenance for the declaration's exact Git commit. This is metadata evidence, not a complete search for alternate installations or package import proof.

Do not clone the workspace environment or treat its passing source tests as a pinned-runtime acceptance. It remains unchanged. No package was downloaded, imported by this inspector, installed or upgraded.

Base interpreter files observed and hashed:

|Path|Bytes|SHA256|
|---|---:|---|
|C:\Program Files\Python311\python.exe|103192|5f7b89a612c9b8af1d6456cdfcd1dbe5ca630849e79aebced9bee9a6694952ec|
|C:\Program Files\Python311\python311.dll|5800216|0817a2a657a24c0d5fbb60df56960f42fc66b3039d522ec952dab83e2d869364|

These two hashes are not a complete interpreter/library trust inventory. The next runnable-runtime prerequisite is a resolved, reviewed Windows CPython3.11 dependency artifact set with hashes (including the exact py-cord provenance), isolated installation and validation. The original declarations do not provide wheel hashes or all transitive bindings. No successful installation or import is inferred.

Existing-key custody is a separate remaining prerequisite: bind local consumers/configuration and writers before a reviewed protection/move transition. The current key stays untouched in the workspace. Local tests do not establish production writer drain or cloud key inventory. Continue useful local preparation/testing under the operator's standing approval; ask again only for a materially new boundary such as production, credential transition or real exports requiring its own exact packet.

## Exact evidence

Evidence root: `.codex_artifacts/s11-runtime-validation-20261001/`.

- native-fixture-result.json, capture-test-results.json, denied-gate-test-result.json.
- dependency-observation.json, dependency-version-differences.json.
- original-draft-review.md, v2-review.md.
- v2/sealed command copies, v2/command-seal.json, v2/EXECUTION-SCOPE.md.
- v2/approvals/RDY-P01-attempt01.json.
- v2/observations/RDY-P01-attempt01/{stdout.json,stderr.txt,process-receipt.json,launcher-receipt.json}.
- A separate result seal binds these files and this checkpoint; earlier seals remain untouched.

Approval receipt SHA256:c6884e7f71506969bbeff8056fb8765c20aaedc04dab09750fe436d51cad0ad4.
Provision script SHA256:099e4c21592ad9368e233ad62ee3ffb7f38a59778dc4aa53e3ab06962eb10be5.
Launcher SHA256:72b6c8dbdf5dc43a63e1e8662e1a65df0893d12f532f018a1fdbb648b1245b06.
Capture helper SHA256:188c1baf10fcb9668c21239eba57344842a628ba19512517f6089c4adfb1c479.

Preserve production hotfixbd980c0f497faf2048eaf1fb6b79600662911763, DB22ONLINE/RESTRICTED_USER/read-only/Broker-disabled and119mediafiles, DB23 and synthetic receipts, all inputs/pending files, S6/S8, both uncertain publications, the shared-account amendment and withdrawn memory collector. None was changed or rerun. No provider/G5 acceptance follows from this work.
