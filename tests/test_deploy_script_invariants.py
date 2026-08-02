"""Static invariants for the fleet deploy script.

Agent: kernel
Role: keep deploy-agents.ps1 from re-acquiring the defects that broke the :s155 deploy.
External I/O: reads infra/deploy-agents.ps1 only.
"""

from __future__ import annotations

import re
from pathlib import Path

SCRIPT = Path("infra/deploy-agents.ps1")

# The blocks that build a create/update invocation carrying secrets, the GHCR
# PAT and the master key. The base64 vocabulary pack must never join them.
_CREATE_ARG_BUILDERS = (
    "$agentEnv = ",
    "$envv = @(",
    '$envv = @("POSTGRES_DSN=secretref:postgres-dsn")',
)


def _script_text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_vocabulary_pack_never_rides_on_a_create_command_line() -> None:
    """DL-85: `az` is az.cmd, so every call inherits cmd's line ceiling.

    GRAPH_VOCABULARY_B64 is >12,000 characters on its own. Splicing it into an
    invocation that also carries secrets, the registry PAT and the master key
    produced "The command line is too long." for all 15 agents, while the script
    reported success. It must only ever be set by its own narrow update call.
    """
    lines = _script_text().splitlines()
    offenders = [
        line.strip()
        for line in lines
        if "Get-VocabularyEnv" in line
        and any(builder in line for builder in _CREATE_ARG_BUILDERS)
    ]

    assert not offenders, f"vocabulary spliced into a create arg list: {offenders}"


def test_vocabulary_is_set_by_its_own_narrow_update() -> None:
    """The pack reaches a target through a dedicated single-variable call.

    Pins the fix as well as the defect: if the setters disappear, the pack stops
    reaching the fleet and a target runs new code against a stale vocabulary,
    which raises VocabularyError fail-closed on its first write (S148 stall).
    """
    text = _script_text()

    assert "function Set-AppVocabulary" in text
    assert "function Set-JobVocabulary" in text
    assert text.count("Get-VocabularyEnv") >= 3  # definition + both setters


def test_deploy_reports_its_own_failure() -> None:
    """DL-85: `up` printed "Fleet deployed" and exited 0 after 15 failures.

    A deploy tool that cannot report failure is the DL-57 pattern inside the
    instrument used to verify everything else.
    """
    text = _script_text()

    assert "$script:Failures" in text, "failures must be accumulated, not just printed"
    assert re.search(r"Failures\.Count -gt 0", text), "up must branch on failures"
    assert "exit 1" in text, "a failed deploy must exit non-zero"


def test_agent_deploy_does_not_swallow_stderr() -> None:
    """The real error was hidden by `2>$null` on the agent create call."""
    text = _script_text()

    assert "az @agentArgs 2>$null" not in text
    assert "function Invoke-Az" in text


def test_long_commands_bypass_the_cmd_wrapper() -> None:
    """DL-85: `az` is az.cmd, so cmd's ~8,191-char ceiling applies to every call.

    The vocabulary pack is >12,000 characters, so it cannot travel through that
    wrapper even alone — measured at 12,053 chars, exit 1, "The command line is
    too long.". Invoking the CLI's own Python entry point uses CreateProcess
    (32,767) instead. Pinned because reverting to bare `az` silently reinstates
    a limit that only shows up against the real fleet.
    """
    text = _script_text()

    assert "function Get-AzPython" in text
    assert "-m azure.cli" in text
