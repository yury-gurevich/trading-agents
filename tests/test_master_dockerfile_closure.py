"""The master image carries its whole closure, and no `contracts/`.

Agent: kernel
Role: prove `agents/master/Dockerfile` copies no `contracts/` path and that
      every module in the master's runtime import closure lies under a path
      the Dockerfile does copy (ADR-0012, DL-12, S232).
External I/O: reads the local Dockerfile; spawns a subprocess.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_PROBE = (
    "import sys\n"
    "import agents.master.entrypoint\n"
    "closure = sorted(\n"
    "    name\n"
    "    for name in sys.modules\n"
    "    if name == 'kernel'\n"
    "    or name.startswith('kernel.')\n"
    "    or name == 'agents'\n"
    "    or name.startswith('agents.master')\n"
    ")\n"
    "print('\\n'.join(closure))\n"
)


def _closure_modules() -> list[str]:
    result = subprocess.run(  # noqa: S603 - fixed interpreter and import probe.
        [sys.executable, "-c", _PROBE],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def test_master_dockerfile_copies_no_contracts_directory() -> None:
    text = Path("agents/master/Dockerfile").read_text(encoding="utf-8")

    assert "COPY contracts/" not in text


def test_every_closure_module_lies_under_a_copied_path() -> None:
    text = Path("agents/master/Dockerfile").read_text(encoding="utf-8")
    copied = [
        line.split()[1]
        for line in text.splitlines()
        if line.startswith("COPY ") and not line.startswith("COPY --from=")
    ]

    for name in _closure_modules():
        if name in ("kernel", "agents"):
            continue
        relative = Path(*name.split("."))
        assert any(
            relative.as_posix().startswith(prefix.rstrip("/")) for prefix in copied
        ), f"{name} is not under any copied path {copied}"
