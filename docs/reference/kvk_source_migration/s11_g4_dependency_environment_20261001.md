# S11 isolated dependency environment — 2026-10-01

The operator approved installing and validating an isolated local dependency environment. That work is complete with the test qualifications below. No credential transition, Bot startup, SQL installation/session, Sheets operation or production change was requested or performed by this workflow. Existing workspace environment and prior source/operation seals remain unchanged.

## Installed and retained

- Runtime environment: `C:\K98-S11-Validation\python-env` (CPython 3.11.9).
- Separate build environment: `C:\K98-S11-Validation\build-env`.
- Retained dependency source: `C:\K98-S11-Validation\pycord-source`.
- Retained wheelhouse: `C:\K98-S11-Validation\wheelhouse`.
- Protected install lock: `C:\K98-S11-Validation\config\runtime-lock.txt`.
- Isolated copied tests: `C:\K98-S11-Validation\validation-tests`.

All are development-only. The source tree remains the previously copied inactive candidate. No environment was activated for the production Bot, and no startup/task configuration changed.

The 94 declarations in current requirements.txt resolved to **106 locked runtime distributions**, including transitive dependencies. Runtime metadata totals 108 distributions including venv-bootstrap pip 24.0 and setuptools 65.5.0, which are recorded separately from the 106-package lock. Historical requirements-freeze.txt and the existing workspace environment were not substituted or modified.

The first pip 24.0 lookup failed certificate verification before resolution. Attempt02 used `--use-feature=truststore` with Windows certificate trust and succeeded. TLS verification stayed enabled; no trusted-host bypass, root-certificate change or SQL certificate-policy change occurred. Both attempt logs remain retained.

Pycord source was cloned separately from the public dependency repository, then detached at the exact declared commit `e4738227b3d22e92d3b0be4c016a4c287bb0fd1e`, identified by Git as `v2.6.1-0-ge4738227`. The setup.py, pyproject.toml and base dependency declaration were inspected before building and rechecked unchanged afterward. The resulting wheel is `py_cord-2.6.1-py3-none-any.whl`, SHA256 `d7123d5cd3d18818c0d2c127b722c1c35975451d93a6d1fb1954b941ebaf3c07`. No application Git history was changed.

The build used separate pinned tools: setuptools69.5.1, setuptools-scm7.1.0, wheel0.45.1 and packaging25.0; resolved typing-extensions4.16.0 and artifact hashes are retained in build-tools-install.json. The build ran offline with `--no-build-isolation --no-deps --no-index`. The retained wheel makes subsequent installation repeatable; a byte-identical rebuild is not claimed.

Runtime installation used `--no-index --find-links C:\K98-S11-Validation\wheelhouse --only-binary=:all: --require-hashes`. All 106 selected name/version/hash entries match the install report and retained wheelhouse. Lock SHA256: `213ce31ea60e0883ae795d63e8bbc749f96785e57cd3b15cc9164c956e2da53b`. Wheelhouse payload totals 124,561,363 bytes. Package artifact retrieval contacted PyPI/pythonhosted and the public Pycord GitHub repository only; this is dependency acquisition, not a provider validation or export.

## Validation outcome

|Check|Result|
|---|---|
|pip check|No broken requirements found|
|All 106 locked versions|Matched installed metadata|
|All 106 retained wheel hashes|Matched resolver/build artifacts|
|Installed wheel payload hashes|18,148 verified|
|Selected dependency/native imports|19 imported successfully|
|Protected application source inventory|549 hashes matched retained candidate|
|Native protected_path checks|26 named critical interpreter/import paths and ancestors passed|
|Targeted copied tests|414 passed, 1 skipped, 2 warnings|

Installed payload verification explicitly excludes nine wheel entries from direct-byte equality: eight installer-relocated entries and one installer-recompiled NumPy bytecode file. They are enumerated in wheel-and-payload-verification.json. Do not claim a complete installed-byte or native-library audit. The 26 native path checks are not a complete typed host_acl proof for every dependency file.

The test runner used isolated Python, disabled automatic pytest plugins, copied exact test bytes without the repository-wide conftest, and used synthetic configuration. It verified all 549 protected source hashes before testing. Python socket connection, Popen and pyodbc connection entrypoints were denied; an audit hook denied `.env` and the known credential filename. These are **cooperative harness guards, not an OS security sandbox or complete no-effects proof**. No direct key read, provider request or process launch exists in the final harness. The environment-verification.json PASS covers lock/source/import checks and is written before pytest; test acceptance comes from the separate test log/XML.

Targeted tests cover source parser/metadata/digest, execution protocol/host and manual enrollment/public-viewer behavior. The skipped test is `test_live_windows_containment_is_a_separate_operation`: it requires a separately bound process/identity/pipe proof and was not enabled by this dependency run. The two warnings concern an imported helper's unregistered asyncio marker, not failed tests.

## Retained broader failures and harness corrections

The broader copied-test attempt remains **not green**: 1305 passed, 20 failed, 1 skipped, 1 error. Counts overlap the targeted suite; never add them together.

- 15 failures invoke the superseded `S11_CREATE_PRIVATE_OUTPUT_POOL` operation; current source accepts only `S11_REGISTER_MANUAL_OUTPUT_POOL`. No automated creation was re-enabled to satisfy those stale tests.
- 5 failures depend on the original repository layout or non-Python deployment metadata absent from the isolated copied-test layout.
- 1 asyncio setup error resulted from the harness denying the Windows event loop's socket connection setup.

These cases are listed individually in broad-test-qualifications.json. No broader-suite, full-suite or G4 acceptance is claimed. Before future whole-repository delivery, reconcile stale test fixtures and run layout-dependent tests in an appropriately bound test checkout. Do not modify the installed source candidate or earlier seals merely to hide failures.

Initial harness attempts are preserved: replacing Popen with a function broke asyncio subclassing; a RuntimeError process denial prevented platform's normal OSError fallback; missing synthetic configuration prevented three collections. The final harness keeps Popen a class and raises PermissionError, preserving denial while allowing normal fallback, and supplies the repository's nonsecret synthetic defaults. Wheel-verifier attempts also retain their bytecode and Windows path-normalization corrections. No dependency or application change was made in response to these harness errors.

## Review and evidence

Evidence root: `.codex_artifacts/s11-dependency-environment-20261001/`.

Key records: original requirements, index resolution attempts and report, index/runtime locks, clone/build logs and build report, runtime install report/log, installed-distributions.json, environment-verification.json, wheel-and-payload-verification.json, native-protected-path-checks.json, test-bundle.json, targeted-selection.json, all attempted test logs/XML and broad-test-qualifications.json. A separate result seal binds these records and this checkpoint; retained wheel hashes bind the external protected artifacts.

Supplemental independent review is retained as `bounded-review.md`, SHA256 `b6f41d8de2a614658fd72854dd75989d280b9cd07ba268f16e0bb0ff618d9449`. Its provenance limitations remain explicit: resolution metadata does not independently attest command-level TLS flags or the exact dependency checkout commit; those observations come from the executing workflow. Blank-hash wheel RECORD entries are also outside payload verification.

Security routing remains bounded Changes review, Deep off. The artifact-only baseline limitation remains: supporting independent evidence review is not a canonical completed Changes scan, dependency vulnerability audit or production-readiness decision. No application implementation, SQL source, requirements declaration or production configuration changed in this task.

## Next boundary

The dependency-installation blocker is resolved for this local candidate, subject to the explicit test/review qualifications. The next operational blocker is the existing key's protected-location transition and exact local consumer/config/writer bindings. Key bytes and location remain untouched. Seven typed G4 proofs, real two-export behavior, production rollout and G5 still need their own evidence and decisions.

Keep the standing approval for local validation; do not ask again for routine safe tests. Preserve DB22 read-only/restricted/Broker-disabled and 119 media files, DB23 evidence, all original inputs/seals/pending files, S6/S8, uncertain publications, the shared-account amendment and withdrawn collector. Production stays isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`.
