"""Import what the fifteen Dockerfile CMDs actually run (S254 B3).

Agent: tooling
Role: prove the other fourteen entry points remain independent of DSPy.
External I/O: reads tracked Dockerfiles; imports entry points without running them.
"""

from __future__ import annotations

import json
import runpy
import sys
from importlib import import_module
from pathlib import Path

from scripts.check_dependency_audit import tracked_dockerfiles


class Blocker:
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] == "dspy":
            raise ImportError(f"DSPy blocked: {name}")
        return


def main() -> None:
    sys.meta_path.insert(0, Blocker())
    dockerfiles = tracked_dockerfiles(Path.cwd())
    assert len(dockerfiles) == 15
    targets = {}
    for name, text in dockerfiles.items():
        command = next(
            line[4:] for line in text.splitlines() if line.startswith("CMD ")
        )
        targets[name] = json.loads(command)
    deliberator = targets.pop("agents/deliberator/Dockerfile")
    modules = scripts = 0
    for command in targets.values():
        assert command[0] == "python"
        if command[1] == "-m":
            import_module(command[2])
            modules += 1
        else:
            assert command[1] == "scripts/dispatch_scheduled_run.py"
            runpy.run_path(command[1], run_name="s254_import_probe")
            scripts += 1
    assert (modules, scripts) == (13, 1)
    failure = ""
    try:
        import_module(deliberator[2])
    except ImportError as exc:
        failure = str(exc)
    assert "DSPy blocked" in failure, "deliberator unexpectedly imports without DSPy"
    assert "dspy" not in sys.modules
    print("other CMD imports 14 (13 modules, 1 script); deliberator requires DSPy")


if __name__ == "__main__":
    main()
