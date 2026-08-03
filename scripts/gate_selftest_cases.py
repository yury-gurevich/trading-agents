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
    must_output: tuple[str, ...] = ()


@dataclass(frozen=True)
class Invariant:
    """A config fact whose regression would silently disable a gate."""

    name: str
    why: str
    path: str
    must_contain: tuple[str, ...] = field(default=())
    must_not_contain: tuple[str, ...] = field(default=())


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
_LAW_PROBE_ROOT = f"scripts/{PROBE_PREFIX}_law_coverage"
_LAW_PROBE_LAWS = """# Probe laws

- **PRB-IDN-01** — Dead citations do not prove green rows.
- **PRB-IDN-02** — A live test must name the clause ID in its docstring.
"""
_LAW_PROBE_PLAN = (
    "# Probe test plan\n\n"
    "| Law | What the test must prove | Scenario | Test | Status |\n"
    "| --- | --- | --- | --- | --- |\n"
    "| PRB-IDN-01 | A deleted test fails the gate. | dead | "
    "`test_probe.py::test_gone` | 🟩 |\n"
    "| PRB-IDN-02 | A docstring must cite the ID. | uncited | "
    "`test_probe.py::test_uncited` | 🟩 |\n"
)
_LAW_PROBE_TEST = '''def test_uncited():
    """A live test whose docstring omits the clause ID."""
    assert True
'''
_LAW_PROBE_LEDGER = """| Agent | Laws authored? | Clauses green / total | Status |
| --- | --- | --- | --- |
| probe | yes | 2 / 2 | partial |
"""
_LAW_PROBE_INDEX = """| Agent | `laws.md` | Green clauses | Notes |
| --- | --- | --- | --- |
| probe | locked | 2 / 2 | partial |
"""

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
        name="law-coverage",
        why=(
            "S156: a law row is not green unless its cited test exists and "
            "the test docstring names the clause ID"
        ),
        files={
            f"{_LAW_PROBE_ROOT}/agents/probe/laws/laws.md": _LAW_PROBE_LAWS,
            f"{_LAW_PROBE_ROOT}/agents/probe/laws/test-plan.md": _LAW_PROBE_PLAN,
            f"{_LAW_PROBE_ROOT}/agents/probe/tests/test_probe.py": _LAW_PROBE_TEST,
            f"{_LAW_PROBE_ROOT}/docs/laws/ledger.md": _LAW_PROBE_LEDGER,
            f"{_LAW_PROBE_ROOT}/docs/laws/INDEX.md": _LAW_PROBE_INDEX,
        },
        command=[
            "uv",
            "run",
            "python",
            "scripts/check_law_coverage.py",
            _LAW_PROBE_ROOT,
        ],
        must_output=("PRB-IDN-01", "test_gone", "PRB-IDN-02", "test_uncited"),
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
    FailureCase(
        name="pip-audit-cve",
        why="the local dependency CVE gate must fail closed on a vulnerable package",
        files={f"scripts/{PROBE_PREFIX}_cve_requirements.txt": "urllib3==1.25.6\n"},
        command=[
            "uv",
            "run",
            "pip-audit",
            "--no-deps",
            "--disable-pip",
            "--progress-spinner",
            "off",
            "-r",
            f"scripts/{PROBE_PREFIX}_cve_requirements.txt",
        ],
        must_output=("urllib3",),
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
    Invariant(
        name="pip-audit-not-ignored-by-ci",
        why="the local CVE gate must fail make ci instead of being ignored",
        path="Makefile",
        must_contain=("\tuv run pip-audit",),
        must_not_contain=("\t-uv run pip-audit",),
    ),
    Invariant(
        name="dependabot-pins-python-to-3-13",
        why=(
            "the ignore rule blocked only semver-major while its comment claimed "
            "to pin 3.13.x; 3.13 -> 3.14 is MINOR and auto-merged through it "
            "(#73, DL-65) - a runtime migration must not arrive unattended"
        ),
        path=".github/dependabot.yml",
        must_contain=("version-update:semver-minor",),
    ),
    Invariant(
        name="graph-vocabulary-guard-wired",
        why=(
            "the vocabulary constrains nothing unless build_graph_from_env "
            "actually wraps the store; unwired it is a declared guard that "
            "guards nothing (DL-66) - the exact pattern it was built to catch"
        ),
        path="kernel/graph_env.py",
        must_contain=("GRAPH_VOCABULARY_PATH", "GRAPH_VOCABULARY_B64", "_guarded("),
    ),
    Invariant(
        name="graph-vocabulary-injected-at-deploy",
        why=(
            "no agent image copies orchestration/packs, so a path-only guard is "
            "undeployable and silently absent in the fleet (S144, DL-68); the "
            "deploy must inject the vocabulary as base64 the way it does grants"
        ),
        path="infra/deploy-agents.ps1",
        must_contain=("GRAPH_VOCABULARY_B64=", "Get-VocabularyEnv"),
    ),
    Invariant(
        name="codeql-custom-query-referenced",
        why=(
            "a .ql file in the repo is not a running check: the custom pack sat "
            "unreferenced by any workflow from 2026-06-23 to 2026-07-27, reading "
            "as coverage while examining nothing"
        ),
        path=".github/codeql-config.yml",
        must_contain=("codeql/python-security/TaintTracking.ql",),
    ),
    Invariant(
        name="codeql-config-queries-not-overridden",
        why=(
            "`queries:` in the workflow REPLACES the config-file list unless it "
            "is prefixed with '+'; without the plus the custom pack silently "
            "does not run - a green CodeQL run evaluated 172 queries, none ours"
        ),
        path=".github/workflows/codeql.yml",
        must_contain=("queries: +security-and-quality",),
    ),
)
