"""Regression proof for the gate self-test runner and encoding case.

Agent: tests
Role: prove environment precedence, probe cleanup, and encoding guard coverage.
External I/O: child interpreters and temporary files; reads the hook configuration.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from scripts import gate_selftest as runner
from scripts.gate_selftest_types import PROBE_PREFIX, FailureCase

if TYPE_CHECKING:
    from types import ModuleType


def _encoding_module() -> ModuleType:
    try:
        return importlib.import_module("scripts.gate_selftest_encoding_cases")
    except ModuleNotFoundError:
        pytest.fail("missing module: scripts.gate_selftest_encoding_cases")


def _child(code: str) -> list[str]:
    return [sys.executable, "-c", code]


def test_case_env_outranks_caller(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T1: a case can disable UTF-8 mode even when its caller enables it."""
    monkeypatch.setenv("PYTHONUTF8", "1")
    case = FailureCase(
        name="env-override",
        why="case environment must outrank the caller",
        files={},
        command=_child("import sys; print(f'mode={sys.flags.utf8_mode}'); sys.exit(1)"),
        must_output=("mode=0",),
        env={"PYTHONUTF8": "0"},
    )
    assert runner.run_failure_case(case, tmp_path) == (True, "rejected (exit 1)")


def test_case_without_env_preserves_caller(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T2: an empty case environment preserves the caller's variables."""
    monkeypatch.setenv("GATE_SELFTEST_CALLER", "inherited-value")
    case = FailureCase(
        name="env-inherit",
        why="the entire caller environment must survive",
        files={},
        command=_child(
            "import os, sys; print(os.environ['GATE_SELFTEST_CALLER']); sys.exit(1)"
        ),
        must_output=("inherited-value",),
    )
    assert runner.run_failure_case(case, tmp_path) == (True, "rejected (exit 1)")


def test_failure_without_finding_is_not_a_pass(tmp_path: Path) -> None:
    """T3: a nonzero exit alone cannot prove the gate found its plant."""
    case = FailureCase(
        name="missing-finding",
        why="tool crashes must not pass as findings",
        files={},
        command=_child("import sys; sys.exit(1)"),
        must_output=("Basic Auth Credentials",),
    )
    ok, detail = runner.run_failure_case(case, tmp_path)
    assert not ok
    assert "without proving" in detail


def test_case_removes_probe_folder_with_gate_leftovers(tmp_path: Path) -> None:
    """T4: cleanup removes a gate-created compiled file and its probe folder."""
    probe = f"scripts/{PROBE_PREFIX}_left"
    settings = f"{probe}/agents/probe/settings.py"
    case = FailureCase(
        name="cleanup-leftovers",
        why="gate-created files must not keep a probe folder alive",
        files={settings: "VALUE = 1\n"},
        command=_child(
            "from pathlib import Path; import sys; "
            f"cache = Path('{probe}/agents/probe/__pycache__'); "
            "cache.mkdir(); (cache / 'settings.pyc').write_bytes(b'compiled'); "
            "sys.exit(1)"
        ),
    )
    assert runner.run_failure_case(case, tmp_path) == (True, "rejected (exit 1)")
    assert not (tmp_path / probe).exists()
    assert (tmp_path / "scripts").is_dir()


def test_sweep_removes_stale_probes_and_preserves_neighbours(tmp_path: Path) -> None:
    """T5: sweep removes stale probes, preserving neighbours and git internals."""
    stale_dir = tmp_path / "scripts" / f"{PROBE_PREFIX}_stale"
    neighbour = tmp_path / "scripts/neighbour/agents/probe/settings.pyc"
    git_file = tmp_path / ".git" / f"{PROBE_PREFIX}_keep" / "nested/settings.pyc"
    for path in (stale_dir / "agents/probe/settings.pyc", neighbour, git_file):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"compiled")
    stale_file = tmp_path / "scripts" / f"{PROBE_PREFIX}_stale.py"
    stale_file.write_text("probe\n", encoding="utf-8")
    assert runner.sweep_stale_probes(tmp_path) == [
        str(stale_file.relative_to(tmp_path))
    ]
    assert not stale_file.exists()
    assert not stale_dir.exists()
    assert neighbour.read_bytes() == b"compiled"
    assert git_file.read_bytes() == b"compiled"


def test_encoding_plant_is_undecodable_and_requires_its_finding() -> None:
    """T6: the exact scan environment, plant, command and finding guard agree."""
    module = _encoding_module()
    assert len(module.ENCODING_FAILURE_CASES) == 1
    case = module.ENCODING_FAILURE_CASES[0]
    assert len(case.files) == 1
    probe, content = next(iter(case.files.items()))
    for encoding in ("cp1252", "ascii"):
        with pytest.raises(UnicodeDecodeError):
            content.encode("utf-8").decode(encoding)
    credential = "".join(
        ("postgresql://someuser", ":", "notarealpassword", "@example.invalid/db")
    )
    assert content.splitlines()[0] == f'dsn = "{credential}"'
    assert case.env == {"PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0", "LC_ALL": "C"}
    assert case.command == [
        "uv",
        "run",
        "pre-commit",
        "run",
        "detect-secrets",
        "--files",
        probe,
    ]
    assert case.must_output == ("Basic Auth Credentials", f"{Path(probe).name}:1")


@pytest.mark.parametrize("config_kind", ["original", "weakened", "removed"])
def test_invariant_requires_full_hook_entry(tmp_path: Path, config_kind: str) -> None:
    """T7: only the complete UTF-8 entry satisfies the invariant (three cases)."""
    module = _encoding_module()
    source = (runner._ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert source.count(module.HOOK_ENTRY) == 1
    if config_kind == "weakened":
        source = source.replace(" -X utf8", "")
    elif config_kind == "removed":
        source = "\n".join(
            line for line in source.splitlines() if module.HOOK_ENTRY not in line
        )
    (tmp_path / ".pre-commit-config.yaml").write_text(source, encoding="utf-8")
    assert len(module.ENCODING_INVARIANTS) == 1
    ok, _ = runner.check_invariant(module.ENCODING_INVARIANTS[0], tmp_path)
    assert ok is (config_kind == "original")


def test_runner_includes_encoding_case_and_invariant_once() -> None:
    """T8: both new guards run once and neither runner table has duplicates."""
    _encoding_module()
    case_names = [case.name for case in runner.CASES]
    invariant_names = [inv.name for inv in runner.ALL_INVARIANTS]
    assert case_names.count("secrets-scan-reads-utf-8") == 1
    assert invariant_names.count("secrets-hook-runs-in-utf-8-mode") == 1
    assert len(case_names) == len(set(case_names))
    assert len(invariant_names) == len(set(invariant_names))
