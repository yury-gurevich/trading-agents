"""A30: the sensor deploy step has one identity, role and workspace.

Agent: tooling
Role: inspect the PowerShell step, env preservation, vocabulary and Up sequencing.
External I/O: reads local source only; never runs the deploy script or Azure CLI.
"""

from __future__ import annotations

import re
from pathlib import Path

from orchestration.container_sensor_guard import WORKSPACE_ENV

SOURCE = Path(__file__).resolve().parents[1] / "infra/deploy-agents.ps1"


def test_a30_sensor_identity_role_and_workspace_are_exact() -> None:
    """DSP-SEC-03: system identity and Log Analytics Reader target only one
    workspace.
    """
    source = SOURCE.read_text(encoding="utf-8")
    sensor = source.split("function Enable-ContainerSensor {", 1)[1].split(
        "\nfunction Up {", 1
    )[0]
    assert '$LOG_WORKSPACE = "trading-agents-logs"' in source
    assert '$SENSOR_ROLE = "Log Analytics Reader"' in source
    assert '$SENSOR_ENV = "LOG_ANALYTICS_WORKSPACE_ID"' in source
    assert WORKSPACE_ENV == "LOG_ANALYTICS_WORKSPACE_ID"
    assert "az containerapp job identity assign --name $DISPATCHER_JOB" in sensor
    assert "--system-assigned --query principalId" in sensor
    role_calls = re.findall(
        r"az role assignment (?:list|create)[\s\S]*?(?=\n  [^ ]|\n    [^ ]|$)", sensor
    )
    assert len(role_calls) == 3
    assert all("--role $SENSOR_ROLE --scope $ws.id" in call for call in role_calls)
    assert (
        "--assignee-object-id $principal --assignee-principal-type ServicePrincipal"
        in sensor
    )
    assert "--workspace-name $LOG_WORKSPACE" in sensor
    assert all(
        word not in sensor.lower()
        for word in ("secret", "password", "client-id", "management.azure.com")
    )
    assert '--set-env-vars "$SENSOR_ENV=$($ws.customerId)"' in sensor
    assert '$vocabOk = ($state -eq "Succeeded") -and (Set-JobVocabulary)' in sensor
    assert "if (-not $ws) { Bot; return $false }" in sensor
    assert "if (-not $principal) { Bot; return $false }" in sensor
    assert 'return ($held -eq "1") -and $vocabOk' in sensor


def test_a30_up_env_preservation_and_sensor_action() -> None:
    """DSP-TRG-04 / DSP-SEC-03: Up enables after job deploy; sensor fails loudly."""
    source = SOURCE.read_text(encoding="utf-8")
    up = source.split("function Up {", 1)[1].split("\nfunction ", 1)[0]
    assert up.index("Deploy-DispatcherJob $ghcr") < up.index(
        "Enable-ContainerSensor | Out-Null"
    )
    assert (
        '$dispatcherPlanned = @("POSTGRES_DSN", "TELEGRAM_BOT_TOKEN", '
        '"TELEGRAM_CHAT_ID", $SENSOR_ENV)' in source
    )
    assert (
        "'sensor' { if (-not (Enable-ContainerSensor)) "
        '{ throw "container sensor not enabled" } }' in source
    )
    actions = re.search(r"\[ValidateSet\(([^\n]+)\)\]", source)
    assert actions is not None
    assert "'sensor'" in actions.group(1)
