"""The deploy's tunables pack names real apps and real tunables (DL-100).

Agent: tooling
Role: bind orchestration/packs/trading_tunables.json to the fleet it configures —
      every app is a deployed app, every key is a tunable that agent actually
      reads, and no credential is committed as a plain env value.
External I/O: reads orchestration/packs/trading_tunables.json and
      infra/deploy-agents.ps1.

A full `up` replaces each app's env set, so a tunable held only as live cluster
state is reverted with a green [OK] — measured 2026-08-08, when it wiped a 1%
position cap back to 10%. The pack fixes the supply; this test fixes the pack.
`make ci` cannot read PowerShell, so a typo in an app name or an env key would
otherwise deploy cleanly and configure nothing at all — the same silent-success
shape the sprint exists to close.
"""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path
from typing import Any

import pytest

from kernel import AgentSettings

_ROOT = Path(__file__).resolve().parents[1]
_PACK = json.loads(
    (_ROOT / "orchestration" / "packs" / "trading_tunables.json").read_text("utf-8")
)
_DEPLOY = (_ROOT / "infra" / "deploy-agents.ps1").read_text("utf-8")
_APPS: dict[str, dict[str, str]] = _PACK["apps"]
_ITEMS = [(app, key, value) for app, env in _APPS.items() for key, value in env.items()]
_SECRETISH = re.compile(r"KEY|SECRET|TOKEN|PASSWORD|DSN|CONNECTION")


def _deployed_app_names() -> set[str]:
    """Return the app names the deploy script's $AGENTS map declares."""
    block = _DEPLOY.split("$AGENTS = [ordered]@{", 1)[1].split("}", 1)[0]
    return set(re.findall(r'["\']?([a-z][a-z-]+)["\']?\s*=\s*"', block))


def _settings_class(app: str) -> type[AgentSettings]:
    """Return the settings class of the agent behind one container app."""
    package = "deliberator" if app.startswith("deliberator-") else app.replace("-", "_")
    module = importlib.import_module(f"agents.{package}.settings")
    classes = [
        value
        for value in vars(module).values()
        if isinstance(value, type)
        and issubclass(value, AgentSettings)
        and value.model_config.get("env_prefix")
    ]
    (found,) = classes
    return found


def test_every_configured_app_is_a_deployed_app() -> None:
    """A tunable set on a name the fleet does not have configures nothing."""
    assert set(_APPS) <= _deployed_app_names()


@pytest.mark.parametrize(("app", "key", "value"), _ITEMS, ids=lambda p: str(p))
def test_every_key_is_a_tunable_that_agent_reads(
    app: str, key: str, value: str
) -> None:
    """The env key must resolve to a real field on that agent's settings."""
    settings_class = _settings_class(app)
    prefix = str(settings_class.model_config["env_prefix"])

    assert key.startswith(prefix), f"{key} is not read by {app}"
    assert key[len(prefix) :].lower() in settings_class.model_fields


@pytest.mark.parametrize(("app", "key", "value"), _ITEMS, ids=lambda p: str(p))
def test_every_value_is_a_string(app: str, key: str, value: str) -> None:
    """Container env values are strings; a JSON number would deploy as one."""
    assert isinstance(value, str), f"{app}/{key} is {type(value).__name__}"


@pytest.mark.parametrize(("app", "key", "value"), _ITEMS, ids=lambda p: str(p))
def test_no_credential_is_carried_as_a_plain_value(
    app: str, key: str, value: str
) -> None:
    """Secrets reach the fleet as secretrefs, never as a committed env value."""
    assert not _SECRETISH.search(key), f"{app}/{key} looks like a credential"


def test_the_settings_a_pack_app_resolves_accept_the_values_it_carries() -> None:
    """The values must validate — a bad bound is a crash-loop, not a warning."""
    for app, env in _APPS.items():
        settings_class = _settings_class(app)
        prefix = str(settings_class.model_config["env_prefix"])
        fields: dict[str, Any] = {
            key[len(prefix) :].lower(): value for key, value in env.items()
        }
        settings_class(**fields)


def test_the_dispatcher_cron_is_a_five_field_expression() -> None:
    """The cron is carried too: its script default reverted a weekday-only job."""
    assert len(str(_PACK["dispatcher"]["cron"]).split()) == 5


def test_deliberator_manager_carries_debate_concurrency() -> None:
    """DRIFT-041 / DL-100: full up must preserve the manager fan-out value."""
    assert _APPS["deliberator-manager"]["DELIBERATOR_DEBATE_CONCURRENCY"] == "4"
