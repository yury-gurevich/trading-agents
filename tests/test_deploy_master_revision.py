"""Guard the master's revisions during a full fleet deployment.

Agent: tooling
Role: prove create carries the required probes and the committed packs fit.
External I/O: reads the deploy script and committed packs; in-memory graph only.
"""

from __future__ import annotations

import base64
import re
from pathlib import Path

import pytest

from agents.master.entrypoint import build_app
from agents.master.settings import MasterSettings
from kernel import InMemoryGraphStore
from kernel.llm_factory import KEY_ENV

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "infra" / "deploy-agents.ps1"
PACKS = ROOT / "orchestration" / "packs"


def _script_text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def _create_block(text: str) -> str:
    return text.split('Top "DEPLOY MASTER"', 1)[1].split(
        "$masterState = Invoke-Az $mArgs", 1
    )[0]


def _env_list(block: str) -> str:
    return block.split("$envv = @(", 1)[1].split("$masterGraph", 1)[0]


def _pack_b64(name: str) -> str:
    return base64.b64encode((PACKS / name).read_bytes()).decode("ascii")


def _settings(provider: str, *, with_probes: bool) -> MasterSettings:
    return MasterSettings(
        _env_file=None,
        llm_provider=provider,
        grant_policy_b64=_pack_b64("trading_grants.json"),
        secret_map_b64=_pack_b64("trading_secrets.json"),
        credential_tests_b64=(
            _pack_b64("trading_credential_tests.json") if with_probes else ""
        ),
        credential_tests_path="",
        remediation_mode="manual",
    )


def test_a1_create_carries_probes_secret_map_and_provider() -> None:
    """DL-296: the revision created with vendor grants already has its probes."""
    block = _create_block(_script_text())
    env = _env_list(block)

    assert '"MASTER_SECRET_MAP_B64=$secretB64"' in env
    assert "(Get-MasterCredentialTestsEnv)" in env
    assert '(Get-AppLlmEnv "master")' in env
    assert '$mArgs += @("--env-vars") + $envv' in block


def test_a2_no_later_call_delivers_the_probe_pack() -> None:
    """DL-296: in a full up only master's create names it; the narrow step is apart."""
    text = _script_text()
    up = text.split("function Up {", 1)[1].split("\n}", 1)[0]
    step = text.split("function Enable-LlmCandidates {", 1)[1].split("\n}", 1)[0]

    assert "Set-MasterCredentialTests" not in text
    assert "credentialTestsOk" not in text
    assert text.count("Get-MasterCredentialTestsEnv") == 3
    assert up.count("Get-MasterCredentialTestsEnv") == 1
    assert step.count("Get-MasterCredentialTestsEnv") == 1
    assert text.count("MASTER_CREDENTIAL_TESTS_B64") == 1


def test_a3_vocabulary_keeps_its_separate_update() -> None:
    """DL-296: vocabulary never joins the create line but is delivered after it."""
    text = _script_text()
    block = _create_block(text)
    after_create = text.split("$masterState = Invoke-Az $mArgs", 1)[1]

    assert "Get-VocabularyEnv" not in block
    assert "GRAPH_VOCABULARY_B64" not in block
    assert '$vocabOk = Set-AppVocabulary "master"' in after_create


def test_a4_committed_create_packs_fit_the_command_line() -> None:
    """DL-296: the actual three pack paths fit with the declared 5,000 reserve."""
    text = _script_text()
    getter = text.split("function Get-MasterCredentialTestsEnv {", 1)[1].split(
        "\n}", 1
    )[0]
    names = re.findall(r"trading_\w+\.json", _create_block(text) + getter)

    assert sorted(names) == [
        "trading_credential_tests.json",
        "trading_grants.json",
        "trading_secrets.json",
    ]
    line_length = sum(len(_pack_b64(name)) for name in names) + 5_000
    assert line_length <= 32_767, f"create line budget exceeded: {line_length}"


@pytest.mark.parametrize("provider", sorted(KEY_ENV))
def test_a5_master_starts_with_the_create_packs(provider: str) -> None:
    """MST-NEV-07: committed create packs cover every declared vendor grant."""
    agent, _ = build_app(
        InMemoryGraphStore(), "fixture-pem", _settings(provider, with_probes=True)
    )

    assert agent.session_id is not None


@pytest.mark.parametrize("provider", sorted(KEY_ENV))
def test_a6_missing_probes_refuse_vendor_grants(provider: str) -> None:
    """MST-NEV-07: the same vendor grants without their probes refuse startup."""
    with pytest.raises(ValueError, match=f"granted {provider} key without its probe"):
        build_app(
            InMemoryGraphStore(), "fixture-pem", _settings(provider, with_probes=False)
        )
