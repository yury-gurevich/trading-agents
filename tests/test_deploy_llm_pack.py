"""Fleet LLM pack and deployment integration guards.

Agent: tooling
Role: bind the provider pack to real apps and their settings.
External I/O: committed JSON and PowerShell source only.
"""

import importlib
import json
import re
from pathlib import Path

from kernel.llm_factory import KEY_ENV

ROOT = Path(__file__).resolve().parents[1]


def test_c1_llm_pack_names_real_apps_and_settings() -> None:
    """MST-NEV-07 / OPR-DEP-01: one provider configures the five declared apps."""
    pack = json.loads(
        (ROOT / "orchestration/packs/trading_llm.json").read_text("utf-8")
    )
    assert pack["provider"] in KEY_ENV
    script = (ROOT / "infra/deploy-agents.ps1").read_text("utf-8")
    block = script.split("$AGENTS = [ordered]@{", 1)[1].split("}", 1)[0]
    names = set(re.findall(r'["\']?([a-z][a-z-]+)["\']?\s*=\s*"', block)) | {"master"}
    assert list(pack["apps"]) == [
        "master",
        "operator",
        "deliberator-manager",
        "deliberator-proponent",
        "deliberator-opponent",
    ]
    for app, key in pack["apps"].items():
        assert app in names
        package = "deliberator" if app.startswith("deliberator-") else app
        module = importlib.import_module(f"agents.{package}.settings")
        cls = getattr(module, f"{package.capitalize()}Settings")
        assert key == cls.model_config["env_prefix"] + "LLM_PROVIDER"
        assert "llm_provider" in cls.model_fields


def test_c2_deploy_filters_tunables_before_appending_llm_pack() -> None:
    """MST-NEV-07: deploy reads the one pack and never sends duplicate keys."""
    script = (ROOT / "infra/deploy-agents.ps1").read_text("utf-8")
    assert "trading_llm.json" in script
    loader = script.split("function Load-LlmPack", 1)[1].split("\n}", 1)[0]
    assert "Test-Path" in loader
    assert "throw" in loader
    body = script.split("function Get-AgentEnv", 1)[1].split(
        "function Get-LiveEnvNames", 1
    )[0]
    assert "$llmKeys -notcontains ($_ -split '=', 2)[0]" in body
    assert "return $envv + $tunables + $llmEnv" in body
    assert '(Get-AppLlmEnv "master")' in script
    assert '"anthropic"' not in script
    assert '"openai"' not in script
