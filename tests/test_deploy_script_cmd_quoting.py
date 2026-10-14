"""No bare `az` call in the infra scripts hands cmd.exe an unquoted metacharacter.

Agent: tooling
Role: read infra/*.ps1 and check each bare `az` call's quoted arguments.
External I/O: reads local source only; never runs a script or the Azure CLI.

On Windows `az` is `az.cmd`. PowerShell quotes an argument only when it holds a space,
so `--query "length(@)"` reached cmd.exe as `length(@)`, its parentheses broke the line
and the sensor step's role read-back always came back empty (2026-10-14, the `s275`
deploy). `Invoke-Az` calls the CLI's Python directly and is exempt.
"""

from __future__ import annotations

import re
from pathlib import Path

INFRA = Path(__file__).resolve().parents[1] / "infra"
CMD_META = frozenset("()&|<>^")
SUBEXPRESSION = re.compile(r"\$\((?:[^()]|\([^()]*\))*\)")
QUOTED = re.compile(r'"([^"]*)"|\'([^\']*)\'')
BARE_AZ = re.compile(r"(?<![\w-])az (?!@)")


def _bare_az_calls(source: str) -> list[tuple[int, str]]:
    lines = source.splitlines()
    found: list[tuple[int, str]] = []
    for number, line in enumerate(lines, start=1):
        start = BARE_AZ.search(line)
        if start is None or line.lstrip().startswith("#"):
            continue
        text, follow = line[start.start() :], number
        while text.rstrip().endswith("`") and follow < len(lines):
            text = f"{text.rstrip()[:-1]} {lines[follow].strip()}"
            follow += 1
        found.append((number, text))
    return found


def _unsafe(text: str) -> list[str]:
    literals = (
        match.group(1) if match.group(1) is not None else match.group(2)
        for match in QUOTED.finditer(SUBEXPRESSION.sub("X", text))
    )
    return [
        literal
        for literal in literals
        if " " not in literal and CMD_META & set(literal)
    ]


def test_no_bare_az_call_passes_a_cmd_metacharacter() -> None:
    """DSP-SEC-03: the sensor step's role read-back reaches the CLI intact."""
    unsafe: dict[str, list[str]] = {}
    total = 0
    for script in sorted(INFRA.glob("*.ps1")):
        calls = _bare_az_calls(script.read_text(encoding="utf-8"))
        total += len(calls)
        for number, text in calls:
            if _unsafe(text):
                unsafe[f"{script.name}:{number}"] = _unsafe(text)
    assert total > 50  # the reader finds the scripts' calls, not none
    assert unsafe == {}


def test_the_guard_reads_the_failure_it_exists_for() -> None:
    """DSP-SEC-03: the 2026-10-14 form is caught; the safe forms are not."""
    broken = '$held = az role assignment list `\n  --query "length(@)" -o tsv\n'
    assert [_unsafe(text) for _, text in _bare_az_calls(broken)] == [["length(@)"]]
    safe = (
        '$n = @(az role assignment list --query "[].id" -o tsv).Count\n'
        'az containerapp job update --set-env-vars "$SENSOR_ENV=$($ws.customerId)"\n'
        '$x = az group show --query "{a:a, b:length(b)}" -o json\n'
        '$y = Invoke-Az @("role", "--query", "length(@)")\n'
    )
    assert [_unsafe(text) for _, text in _bare_az_calls(safe)] == [[], [], []]
