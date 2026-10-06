# Windows venv process-image compatibility — 2026-10-06

The reviewed provider-child launcher and the native Windows process image are
different concepts. Windows Python 3.11 venv redirectors can launch the base
interpreter while retaining the venv dependency environment. Requiring the
provider launcher path to equal the authority's native image rejects that setup.

The manual process-pair plan's `python` and `python_sha256` fields pin the native
image reported through retained Windows process handles. Launch the held gates
through the independently reviewed venv executable. The authority manifest's
`python` field remains that protected provider-child launcher, covered by the
typed G4 custody record and immutable path/content checks.

Remove only the incorrect equality between these two paths. Role verification
still checks native image path/hash, ordinary token profile and exact process
incarnation against the protected manual plan. Administrative publication keeps
the actual retained handles. Authority startup validates its own bound process
before creating the SQL connection factory; peer and lifetime checks remain.

No Python replacement, dependency installation, account/grant change, SQL
migration, provider write, enrollment or activation follows from this correction.
Production source deployment and process publication remain separate decisions.
Tests cover distinct launcher/image paths, altered image paths and hashes, and
native-image rejection before any SQL connection factory is created.

Provider containment launches the pinned native authority image directly, with
CPython's `__PYVENV_LAUNCHER__` set to the reviewed venv executable. Inherited
interpreter-path overrides are removed case-insensitively. The image hash and
protected path are checked before each launch, which remains suspended until
assigned to the kill-on-close Job Object. The exact returned PID owns the pipe;
SID/PID authentication, retained process handles and descendant-drain checks remain.

The disposable local native regression uses real Windows process creation,
private named-pipe SID/PID authentication, venv/pywin32 resolution and Job Object
termination. Only synthetic-file ACL inspection is substituted; this is not a
production ACL or future process-identity acceptance record. It also exercised
and corrected pywin32's unnamed-job argument and security API namespace.
Both authority startup and the separately approved manual-pool enrollment path
supply the same protected native-image pin to the provider host.

Security routing: Changes review required for the exact Bot mirror and private
promotion diffs. Deep scan off; no codebase audit. Existing direct-permission and
whole-application SQL contract reviews remain separately qualified.
