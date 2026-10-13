"""The planted violation and the config fact for the secrets scan's encoding.

Agent: tooling
Role: prove the secrets scan reads a UTF-8 file the platform default cannot decode.
External I/O: none; exports an immutable case table and an invariant table.

detect-secrets opens a file with the platform's default encoding and treats one it
cannot decode as binary: it passes over it. On Windows that default is cp1252, and
184 of 2,408 tracked files hold a character it cannot decode (measured 2026-10-14,
DL-298 and DL-299); a Linux machine in the C locale passes over every file that is
not ASCII. The hook's entry puts its interpreter in UTF-8 mode. The case here runs
the hook in the environment that would skip the file and requires the finding.
"""

from __future__ import annotations

from scripts.gate_selftest_types import PROBE_PREFIX, FailureCase, Invariant

HOOK_ENTRY = "entry: python -X utf8 -m detect_secrets.pre_commit_hook"
# The environment in which an interpreter left to itself cannot decode the plant:
# UTF-8 mode off, and on Linux the C locale with its coercion to UTF-8 off, which
# leaves ASCII. On Windows the first key alone leaves the ANSI code page.
UNDECODING_ENV = {"PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0", "LC_ALL": "C"}
# U+274C is E2 9D 8C in UTF-8, and 9D is a byte cp1252 does not define.
UNDECODABLE = "\u274c"
# Assembled from parts so that no line of this file has the shape the scan reports.
_CREDENTIAL = "".join(
    ("postgresql://someuser", ":", "notarealpassword", "@example.invalid/db")
)
_PROBE = f"scripts/{PROBE_PREFIX}_encoding.md"
_WHY = (
    "DL-298: the commit hook passed a credential-shaped line in a page that held "
    "one character outside cp1252, and the remote scan was the first to read it"
)

ENCODING_FAILURE_CASES: tuple[FailureCase, ...] = (
    FailureCase(
        name="secrets-scan-reads-utf-8",
        why=_WHY,
        files={_PROBE: f'dsn = "{_CREDENTIAL}"\n{UNDECODABLE}\n'},
        command=["uv", "run", "pre-commit", "run", "detect-secrets", "--files", _PROBE],
        must_output=("Basic Auth Credentials", f"{PROBE_PREFIX}_encoding.md:1"),
        env=UNDECODING_ENV,
    ),
)

ENCODING_INVARIANTS: tuple[Invariant, ...] = (
    Invariant(
        name="secrets-hook-runs-in-utf-8-mode",
        why=_WHY,
        path=".pre-commit-config.yaml",
        must_contain=(HOOK_ENTRY,),
    ),
)
