"""The config facts that keep the remote gate and the commit hook equal to `make ci`.

Agent: tooling
Role: declare the invariants that pin one check's arguments in each place it is wired.
External I/O: none (declares expected file content; the runner reads it).

The workflow and the hooks list their commands independently of the Makefile, so a
folder added to one is not added to the others. Measured 2026-10-11 (work-queue 129,
DL-293): a module with no header in `surfaces/` passed the commit hook and the remote
gate, which named four folders where `make ci` named five.
"""

from __future__ import annotations

from scripts.gate_selftest_types import Invariant

_HEADER_WHY = (
    "DL-293: the header check must read the same folders wherever it is wired; "
    "`orchestration/` and `surfaces/` were read by `make ci` alone"
)

PARITY_INVARIANTS: tuple[Invariant, ...] = (
    Invariant(
        name="header-check-reads-five-packages-locally",
        why=_HEADER_WHY,
        path="Makefile",
        must_contain=("scripts/check_module_header.py $(PKGS) scripts",),
    ),
    Invariant(
        name="header-check-reads-five-packages-in-ci",
        why=_HEADER_WHY,
        path=".github/workflows/ci.yml",
        must_contain=(
            "scripts/check_module_header.py "
            "kernel contracts agents orchestration surfaces scripts",
        ),
    ),
    Invariant(
        name="header-hook-reads-five-packages",
        why=_HEADER_WHY,
        path=".pre-commit-config.yaml",
        must_contain=(
            "files: ^(kernel|contracts|agents|orchestration|surfaces|scripts)/",
        ),
    ),
    Invariant(
        name="param-sync-wired-in-ci",
        why=(
            "DL-293: the tests catch a wrong PARAM row remotely, but only as two "
            "assertion failures; the step makes the failure name its cause, and "
            "the remote gate then runs every step `make ci` can run there"
        ),
        path=".github/workflows/ci.yml",
        must_contain=("scripts/check_param_law_sync.py",),
    ),
)
