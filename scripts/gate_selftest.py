"""Prove every gate can fail.

Agent: tooling
Role: plant a known violation per check and assert the check rejects it.
External I/O: writes probe files into the worktree, runs gate commands, deletes them.

A gate that has never been seen failing is not known to work. On 2026-07-22 three
read green while examining nothing: the security gate had run on zero sprint
merges (DL-52), a status claim had no check that could contradict it (DL-54), and
the secret sweep could not see new files (DL-55). Each was found by accident. This
turns "can this check fail?" from a question someone happens to ask into one the
lane answers on every push.

Probe files are named `_gate_selftest_probe*` and are removed in a finally block;
a stale-probe sweep runs first in case a previous run was killed.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.gate_selftest_cases import (  # noqa: E402
    FAILURE_CASES,
    INVARIANTS,
    PROBE_PREFIX,
    FailureCase,
    Invariant,
)

CASE_TIMEOUT_SECONDS = 300


def sweep_stale_probes(root: Path) -> list[str]:
    """Delete probe files a killed run may have left behind."""
    removed = []
    for path in sorted(root.rglob(f"{PROBE_PREFIX}*")):
        if ".git" in path.parts or not path.is_file():
            continue
        path.unlink()
        removed.append(str(path.relative_to(root)))
    return removed


def run_failure_case(case: FailureCase, root: Path) -> tuple[bool, str]:
    """Plant the violation, run the gate, and require a non-zero exit."""
    written = []
    try:
        for name, content in case.files.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written.append(target)
        completed = subprocess.run(  # noqa: S603 - fixed commands from the case table.
            case.command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=CASE_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"could not run: {type(exc).__name__}"
    finally:
        for target in written:
            target.unlink(missing_ok=True)
    if completed.returncode == 0:
        return False, "gate exited 0 on a planted violation — it does not catch this"
    output = f"{completed.stdout}\n{completed.stderr}"
    missing = [needle for needle in case.must_output if needle not in output]
    if missing:
        return False, f"gate failed without proving: {', '.join(missing)}"
    return True, f"rejected (exit {completed.returncode})"


def check_invariant(inv: Invariant, root: Path) -> tuple[bool, str]:
    """Assert a config fact whose loss would silently disable a gate."""
    path = root / inv.path
    if not path.is_file():
        return False, f"missing file: {inv.path}"
    text = path.read_text(encoding="utf-8")
    absent = [needle for needle in inv.must_contain if needle not in text]
    if absent:
        return False, f"{inv.path} no longer contains: {', '.join(absent)}"
    present = [needle for needle in inv.must_not_contain if needle in text]
    if present:
        return False, f"{inv.path} still contains: {', '.join(present)}"
    return True, "present"


def main() -> int:
    """Run every case and return non-zero if any gate failed to fail."""
    root = _ROOT
    stale = sweep_stale_probes(root)
    if stale:
        print(f"swept {len(stale)} stale probe file(s): {', '.join(stale)}")

    results: list[tuple[str, bool, str]] = []
    for case in FAILURE_CASES:
        ok, detail = run_failure_case(case, root)
        results.append((f"can-fail: {case.name}", ok, detail))
        print(f"{'PASS' if ok else 'FAIL'}  can-fail: {case.name} — {detail}")
        if not ok:
            print(f"      why it matters: {case.why}")
    for inv in INVARIANTS:
        ok, detail = check_invariant(inv, root)
        results.append((f"invariant: {inv.name}", ok, detail))
        print(f"{'PASS' if ok else 'FAIL'}  invariant: {inv.name} — {detail}")
        if not ok:
            print(f"      why it matters: {inv.why}")

    failed = [name for name, ok, _ in results if not ok]
    print(f"\ngate self-test: {len(results) - len(failed)}/{len(results)} passed")
    if failed:
        listed = "\n".join(f"  {name}" for name in failed)
        sys.stderr.write(
            "\nA gate did not reject its planted violation, or a gate-enabling "
            "config was lost.\nUntil this is fixed, a green lane is not evidence "
            f"that gate examined anything:\n{listed}\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
