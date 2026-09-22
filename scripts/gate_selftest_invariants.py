"""The config facts whose regression would silently disable a gate.

Agent: tooling
Role: declare the invariants the gate self-test asserts about wiring and config.
External I/O: none (declares expected file content; the runner reads it).

Split out of gate_selftest_cases.py by the chore that taught the size gate to read
`scripts/` (work-queue item 78) - that file was the folder's largest at 486 lines
and had just grown again, and the new ratchet forbids growing a legacy file.
"""

from __future__ import annotations

from scripts.gate_selftest_types import Invariant

INVARIANTS: tuple[Invariant, ...] = (
    Invariant(
        name="merge-procedure-asserts-a-run-exists",
        why=(
            "row M: the assertion is only real while the merge procedure calls "
            "it; a procedure that drifts back to eyeballing `gh run list` "
            "restores the defect without changing a line of code"
        ),
        path="CLAUDE.md",
        must_contain=("make gate-ran",),
    ),
    Invariant(
        name="gate-ran-target-exists",
        why="the procedure names a target that must actually be defined",
        path="Makefile",
        must_contain=("gate-ran:", "scripts/assert_gate_ran.py"),
    ),
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
        name="sprint-status-gate-wired-locally",
        why=(
            "S224: a local check that is absent from make ci can never prove "
            "the repository gate rejects a new unmapped status"
        ),
        path="Makefile",
        must_contain=("scripts/check_sprint_status.py",),
    ),
    Invariant(
        name="sprint-status-gate-wired-in-ci",
        why=(
            "S224: CI enumerates quality commands independently from the "
            "Makefile, so both paths must retain the status classifier"
        ),
        path=".github/workflows/ci.yml",
        must_contain=("scripts/check_sprint_status.py",),
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
        name="dependency-audit-not-ignored-by-ci",
        why=(
            "the local CVE gate must fail make ci instead of being ignored, and "
            "an --ignore-vuln flag would route acceptance around the baseline "
            "that re-measures it (DL-199)"
        ),
        path="Makefile",
        must_contain=("\tuv run python scripts/check_dependency_audit.py",),
        must_not_contain=("\t-uv run", "--ignore-vuln"),
    ),
    Invariant(
        name="dependency-audit-wired-in-ci",
        why=(
            "CI enumerates security commands independently from the Makefile, so "
            "both paths must audit the lock rather than the installed set"
        ),
        path=".github/workflows/ci.yml",
        must_contain=("scripts/check_dependency_audit.py",),
        must_not_contain=("--ignore-vuln",),
    ),
    Invariant(
        name="size-block-reads-scripts-locally",
        why=(
            "work-queue item 78: scripts/ sat outside the size command, so 16 "
            "files crossed the 200-line block unopposed. Dropping the argument "
            "would reopen the hole without failing anything"
        ),
        path="Makefile",
        must_contain=("check_module_size.py $(PKGS) tests scripts",),
    ),
    Invariant(
        name="size-block-reads-scripts-in-ci",
        why=(
            "CI enumerates the quality commands independently of the Makefile, "
            "so both paths must carry the same scope"
        ),
        path=".github/workflows/ci.yml",
        must_contain=(
            "check_module_size.py kernel contracts agents "
            "orchestration surfaces tests scripts",
        ),
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
