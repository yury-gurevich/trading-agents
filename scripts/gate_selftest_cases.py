"""The cases proving each gate can fail.

Agent: tooling
Role: define planted violations and config invariants for the gate self-test.
External I/O: none (declares file content; the runner writes it).

Every entry here exists because a real defect got through. A check that has never
been observed failing is not known to work — three gates read green in one day
while examining nothing (DL-52, DL-54, DL-55).
"""

from __future__ import annotations

from dataclasses import dataclass, field

PROBE_PREFIX = "_gate_selftest_probe"


@dataclass(frozen=True)
class FailureCase:
    """A planted violation that a named gate step must reject."""

    name: str
    why: str
    files: dict[str, str]
    command: list[str]


@dataclass(frozen=True)
class Invariant:
    """A config fact whose regression would silently disable a gate."""

    name: str
    why: str
    path: str
    must_contain: tuple[str, ...] = field(default=())


_OVERSIZE = "\n".join(f"X{n} = {n}" for n in range(230))
_PROBE_HEADER = (
    '"""Probe.\n\nAgent: tooling\nRole: probe.\nExternal I/O: none.\n"""\n\n'
)
# The planted violation for the untracked-secret gate. Deliberately looks like a
# credential — that is the point — and resolves to nothing.
_FAKE_DSN = (
    "postgresql://someuser:"  # pragma: allowlist secret
    "notarealpassword@example.invalid/db"
)

FAILURE_CASES: tuple[FailureCase, ...] = (
    FailureCase(
        name="ruff",
        why="a lint error must fail the lane, not merely warn",
        files={f"kernel/{PROBE_PREFIX}_lint.py": "import os\n"},
        command=["uv", "run", "ruff", "check", f"kernel/{PROBE_PREFIX}_lint.py"],
    ),
    FailureCase(
        name="module-size",
        why="the 200-line hard block must actually block (CLAUDE.md)",
        files={f"kernel/{PROBE_PREFIX}_size.py": f"{_PROBE_HEADER}{_OVERSIZE}\n"},
        command=[
            "uv",
            "run",
            "python",
            "scripts/check_module_size.py",
            "kernel",
        ],
    ),
    FailureCase(
        name="module-header",
        why="the Agent:/Role: header convention must be enforced, not assumed",
        files={f"scripts/{PROBE_PREFIX}_header.py": '"""No header fields here."""\n'},
        command=[
            "uv",
            "run",
            "python",
            "scripts/check_module_header.py",
            "scripts",
        ],
    ),
    FailureCase(
        name="untracked-secrets",
        why=(
            "DL-55: --all-files resolves through git, so a brand-new file was "
            "invisible to the secret sweep until staged"
        ),
        files={f"scripts/{PROBE_PREFIX}_secret.py": f'FAKE = "{_FAKE_DSN}"\n'},
        command=["uv", "run", "python", "scripts/check_untracked_secrets.py"],
    ),
)

INVARIANTS: tuple[Invariant, ...] = (
    Invariant(
        name="security-gate-runs-on-push",
        why=(
            "DL-52/DL-56: while this gate was pull_request-only, S131/S132/S134 "
            "each merged locally and were never gated at all"
        ),
        path=".github/workflows/security-findings.yml",
        must_contain=("push:", 'branches: ["**", "!backup/**"]'),
    ),
    Invariant(
        name="ci-runs-on-push",
        why="quality/test/security must run on every branch, not only on PRs",
        path=".github/workflows/ci.yml",
        must_contain=("push:", 'branches: ["**", "!backup/**"]'),
    ),
    Invariant(
        name="untracked-scan-wired-into-ci",
        why=(
            "the DL-55 fix is only real while `make ci` actually calls it; a "
            "dropped Makefile line would silently restore the blind spot"
        ),
        path="Makefile",
        must_contain=("scripts/check_untracked_secrets.py",),
    ),
)
