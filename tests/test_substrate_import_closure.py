"""The master's runtime import closure holds no pack module.

Agent: kernel
Role: prove the substrate (kernel + agents.master) never loads pack code at
      runtime — a fresh interpreter importing the master entrypoint must not
      pull in contracts, another agent, orchestration or surfaces.
External I/O: spawns a subprocess (the interpreter running this repo).
"""

from __future__ import annotations

import subprocess
import sys

_PROBE = (
    "import sys\n"
    "import agents.master.entrypoint\n"
    "forbidden = sorted(\n"
    "    name\n"
    "    for name in sys.modules\n"
    "    if name == 'contracts'\n"
    "    or name.startswith('contracts.')\n"
    "    or (name.startswith('agents.') and not name.startswith('agents.master'))\n"
    "    or name == 'orchestration'\n"
    "    or name.startswith('orchestration.')\n"
    "    or name == 'surfaces'\n"
    "    or name.startswith('surfaces.')\n"
    ")\n"
    "print('\\n'.join(forbidden))\n"
)


def _forbidden_modules_loaded() -> list[str]:
    result = subprocess.run(  # noqa: S603 - fixed interpreter and import probe.
        [sys.executable, "-c", _PROBE],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def test_master_import_closure_holds_no_pack_module() -> None:
    """MST-DEP-05: master imports only the substrate, never a pack module."""
    assert _forbidden_modules_loaded() == []
