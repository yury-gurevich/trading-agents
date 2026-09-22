"""The cases proving each gate can fail.

Agent: tooling
Role: define planted violations and config invariants for the gate self-test.
External I/O: none (declares file content; the runner writes it).

Every entry here exists because a real defect got through. A check that has never
been observed failing is not known to work — three gates read green in one day
while examining nothing (DL-52, DL-54, DL-55).
"""

from __future__ import annotations

from scripts.gate_selftest_types import PROBE_PREFIX, FailureCase

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
# The planted report for the accepted-advisory re-check: the advisory this repo
# accepts, but carrying a fix release, which retires the acceptance.
_FIXED_ADVISORY_REPORT = (
    '{"dependencies": [{"name": "diskcache", "version": "5.6.3", "vulns": '
    '[{"id": "PYSEC-2026-2447", "aliases": [], "fix_versions": ["5.6.4"]}]}]}\n'
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
_PARAM_LAW_PROBE_ROOT = f"scripts/{PROBE_PREFIX}_param_law_sync"
_PARAM_LAW_PROBE_SETTINGS = """from kernel import AgentSettings, tunable


class ProbeSettings(AgentSettings):
    declared: int = tunable(1, why="Declared tunable.")
    undocumented: str = "x"
"""
_PARAM_LAW_PROBE_LAWS = """# Probe laws

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `declared` | `1` | `int` | YES | Declared tunable. |
| `missing_from_settings` | `"x"` | `str` | NO (config) | Planted row. |

## Changelog
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
        name="module-size-reads-scripts",
        why=(
            "scripts/ sat outside the size block until 2026-09-23, so 16 files "
            "crossed it unopposed - including one added the night the gate was "
            "taught to look (work-queue item 78)"
        ),
        files={f"scripts/{PROBE_PREFIX}_size.py": f"{_PROBE_HEADER}{_OVERSIZE}\n"},
        command=[
            "uv",
            "run",
            "python",
            "scripts/check_module_size.py",
            "scripts",
        ],
        must_output=("hard block",),
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
        name="param-law-sync",
        why=(
            "S187: a settings field without a PARAM row, or a PARAM row without "
            "a settings field, must not silently pass the lane"
        ),
        files={
            f"{_PARAM_LAW_PROBE_ROOT}/agents/probe/settings.py": (
                _PARAM_LAW_PROBE_SETTINGS
            ),
            f"{_PARAM_LAW_PROBE_ROOT}/agents/probe/laws/laws.md": (
                _PARAM_LAW_PROBE_LAWS
            ),
        },
        command=[
            "uv",
            "run",
            "python",
            "scripts/check_param_law_sync.py",
            _PARAM_LAW_PROBE_ROOT,
        ],
        must_output=("probe.undocumented", "probe.missing_from_settings"),
    ),
    FailureCase(
        name="sprint-status",
        why=(
            "S224: a new sprint document with no declared status must fail the "
            "ratchet rather than silently becoming an inferred SPEC"
        ),
        files={
            f"scripts/{PROBE_PREFIX}_sprint_status/docs/sprints/sprint-probe.md": (
                "# Probe\n"
            ),
        },
        command=[
            "uv",
            "run",
            "python",
            "scripts/check_sprint_status.py",
            f"scripts/{PROBE_PREFIX}_sprint_status",
        ],
        must_output=("sprint-probe.md", "MISSING count"),
    ),
    FailureCase(
        name="markdown-links",
        why=(
            "S221: Markdownlint checks fragments only inside one document, so a "
            "relative link to a missing tracked file previously passed the gate"
        ),
        files={f"docs/{PROBE_PREFIX}_dead_link.md": "[missing](nope.md)\n"},
        command=[
            "uv",
            "run",
            "python",
            "scripts/check_markdown_links.py",
            f"docs/{PROBE_PREFIX}_dead_link.md",
        ],
        must_output=("dead_link.md:1", "nope.md", "missing target"),
    ),
    FailureCase(
        name="version-scheme",
        why=(
            "S220: version 0.103.0 passed every lane despite the declared "
            "MAJOR.MMM.PP scheme requiring a two-digit patch group"
        ),
        files={
            f"scripts/{PROBE_PREFIX}_pyproject.toml": (
                '[project]\nversion = "0.103.0"\n'
            )
        },
        command=[
            "uv",
            "run",
            "python",
            "scripts/check_version_scheme.py",
            f"scripts/{PROBE_PREFIX}_pyproject.toml",
        ],
        must_output=("0.103.0", "MAJOR.MMM.PP"),
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
    FailureCase(
        name="accepted-advisory-re-check",
        why=(
            "an accepted advisory whose fix has shipped must stop being accepted; "
            "the ignore it replaced had no mechanism that could notice (DL-199)"
        ),
        files={f"scripts/{PROBE_PREFIX}_audit.json": _FIXED_ADVISORY_REPORT},
        command=[
            "uv",
            "run",
            "python",
            "scripts/check_dependency_audit.py",
            "--audit-json",
            f"scripts/{PROBE_PREFIX}_audit.json",
        ],
        must_output=("a fix has shipped",),
    ),
    FailureCase(
        name="gate-ran-rejects-abbreviated-sha",
        why=(
            "row M: the GitHub API's head_sha filter returns total_count: 0 for an "
            "abbreviated SHA with no error, so an abbreviated query cannot tell "
            "'no runs' from 'wrong question' (measured: c145e5e -> 0, full -> 2)"
        ),
        files={},
        command=[
            "uv",
            "run",
            "python",
            "scripts/assert_gate_ran.py",
            "--sha",
            "c145e5e",
        ],
        must_output=("not a full 40-character SHA",),
    ),
    FailureCase(
        name="gate-ran-rejects-zero-runs",
        why=(
            "row M: a pushed branch produced no runs at all on 2026-07-23 and the "
            "merge procedure could not tell that from 'not pushed yet'"
        ),
        files={
            f"scripts/{PROBE_PREFIX}_no_runs.json": (
                '{"total_count": 0, "workflow_runs": []}\n'
            )
        },
        command=[
            "uv",
            "run",
            "python",
            "scripts/assert_gate_ran.py",
            "--sha",
            "0000000000000000000000000000000000000000",
            "--runs-json",
            f"scripts/{PROBE_PREFIX}_no_runs.json",
        ],
        must_output=("no workflow run exists",),
    ),
    FailureCase(
        name="gate-ran-judges-the-newest-attempt-not-the-first",
        why=(
            "2026-09-04: Security Findings failed at 11:35:53 because CodeQL had "
            "not yet marked alert #178 fixed; a re-dispatch concluded success and "
            "the script still reported NOT PROVEN off the dead first attempt. A "
            "regression must show as a *newer* failure, never a stale one"
        ),
        files={
            f"scripts/{PROBE_PREFIX}_rerun.json": (
                '{"total_count": 3, "workflow_runs": ['
                '{"name": "CI", "status": "completed", "conclusion": "success",'
                ' "run_started_at": "2026-09-04T11:30:00Z", "id": 1},'
                '{"name": "Security Findings", "status": "completed",'
                ' "conclusion": "success",'
                ' "run_started_at": "2026-09-04T11:35:00Z", "id": 2},'
                '{"name": "Security Findings", "status": "completed",'
                ' "conclusion": "failure",'
                ' "run_started_at": "2026-09-04T11:45:00Z", "id": 3}'
                "]}" + chr(10)
            )
        },
        command=[
            "uv",
            "run",
            "python",
            "scripts/assert_gate_ran.py",
            "--sha",
            "0000000000000000000000000000000000000000",
            "--runs-json",
            f"scripts/{PROBE_PREFIX}_rerun.json",
        ],
        must_output=("concluded 'failure'",),
    ),
)
