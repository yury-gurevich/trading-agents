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


def test_master_credential_tests_are_set_by_own_narrow_update() -> None:
    """S188: credential-test pack is too large to ride the master create call."""
    text = _script_text()
    lines = text.splitlines()
    offenders = [
        line.strip()
        for line in lines
        if "Get-MasterCredentialTestsEnv" in line
        and any(builder in line for builder in _CREATE_ARG_BUILDERS)
    ]

    assert "function Set-MasterCredentialTests" in text
    assert "MASTER_CREDENTIAL_TESTS_B64" in text
    assert not offenders, f"credential tests spliced into create args: {offenders}"


def test_issuer_map_is_loaded_from_pack_and_sent_only_to_pm() -> None:
    """S184: the issuer map is PM pack data, not a tunable or fleet-wide env."""
    text = _script_text()
    agent_env = text.split("function Get-AgentEnv", 1)[1].split(
        "function Get-LiveEnvNames", 1
    )[0]

    assert "function Get-IssuerMapEnv" in text
    assert "trading_issuer_map.json" in text
    assert "PORTFOLIO_MANAGER_ISSUER_MAP_B64" in text
    assert '$name -eq "portfolio-manager"' in agent_env
    assert agent_env.count("Get-IssuerMapEnv") == 1


def test_preflight_imports_what_its_own_steps_import() -> None:
    """A package can look installed while being unusable, and preflight missed it.

    The `s187` deploy failed at Service Bus route prep on a corrupt `azure-core`
    — dist-info with no RECORD file, so uv still listed it installed while
    `azure/core/` held zero `.py` files. Route prep imports its admin client
    lazily inside `main()`, so the ImportError landed *after* `alembic upgrade
    head` had migrated. Preflight checked every input to that step and never
    that the step could import its own dependency. Pinned on both sides: if
    route prep changes what it imports, this fails and preflight must follow.
    """
    text = _script_text()
    body = text.split("function Preflight", 1)[1]
    preflight = body.split("\nfunction ", 1)[0]
    route_prep = Path("scripts/servicebus_prepare_routes.py").read_text(
        encoding="utf-8"
    )
    symbol = "from azure.servicebus.management import ServiceBusAdministrationClient"

    assert "function Test-ServiceBusImports" in text
    assert "Test-ServiceBusImports" in preflight, "the check must run in preflight"
    assert symbol in route_prep, "route prep no longer imports the pinned symbol"
    assert symbol in text, "preflight must import exactly what route prep imports"


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


def test_status_board_column_width_is_derived_not_hardcoded() -> None:
    """A new agent must not be able to break the status board's alignment.

    S153's `deliberator-proponent` is 21 characters and ran straight into the
    DEPLOY column under the previous hardcoded width of 19. Same shape as the
    build-matrix gap: a literal that silently stops matching the fleet.
    """
    text = Path("infra/status.ps1").read_text(encoding="utf-8")

    assert "$appW" in text, "the APP column width must be computed"
    assert "{0,-19}" not in text, "hardcoded APP column width reintroduced"


def test_deliberator_served_peers_can_scale_past_one_replica() -> None:
    """S172: proponent/opponent scale out, while the manager stays singular."""
    text = _script_text()

    assert "function Get-AppMaxReplicas" in text
    assert "function Get-AppDesiredReplicas" in text
    assert '"deliberator-proponent", "deliberator-opponent"' in text
    assert '"--max-replicas", $maxReplicas' in text
    assert "desiredReplicas=$desiredReplicas" in text
    assert "(Get-AppMaxReplicas $name)" in text
    assert "(Get-AppDesiredReplicas $name)" in text
    assert re.search(r'"deliberator-manager".*return 1', text, re.DOTALL)


def test_gitignored_deploy_json_can_come_from_process_env() -> None:
    """Secrets stay out of sibling worktrees used for branch deploys."""
    text = _script_text()

    assert "GHCR_LOCAL_JSON" in text
    assert "KEY_VAULT_LOCAL_JSON" in text
    assert '[Environment]::GetEnvironmentVariable($envName, "Process")' in text
