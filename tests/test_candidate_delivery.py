"""A25-A28: candidate declaration delivery and switch proof guards.

Agent: tooling
Role: inspect deploy bytes and prove candidate-based graph evidence offline.
External I/O: committed source reads only; no script or vendor is invoked.
"""

import base64
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from scripts.switch_llm_config import declared_provider, load_pack
from scripts.switch_llm_proof import missing_terms

from kernel import InMemoryGraphStore

ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "orchestration/packs"


def deploy() -> str:
    return (ROOT / "infra/deploy-agents.ps1").read_bytes().decode("utf-8")


def test_a25_master_create_ships_candidate_declaration() -> None:
    """MST-OUT-05: create carries the fourth pack and keeps Windows headroom."""
    script = deploy()
    getter = script.split("function Get-MasterLlmPackEnv {", 1)[1].split("\n}", 1)[0]
    assert r'"..\orchestration\packs\trading_llm.json"' in getter
    assert (
        '"MASTER_LLM_PACK_B64=" + [Convert]::ToBase64String('
        "[IO.File]::ReadAllBytes($file))" in getter
    )
    assert script.count('"MASTER_LLM_PACK_B64="') == 1
    assert "\t" not in getter
    create = script.split("function Up {", 1)[1].split("  $masterGraph", 1)[0]
    assert create.count("(Get-MasterLlmPackEnv)") == 1
    assert "(Get-MasterCredentialTestsEnv), (Get-MasterLlmPackEnv)" in create
    headroom = 5000 + sum(
        len(base64.b64encode((PACKS / filename).read_bytes()))
        for filename in (
            "trading_grants.json",
            "trading_secrets.json",
            "trading_credential_tests.json",
            "trading_llm.json",
        )
    )
    assert headroom < 32767


def test_a25_image_and_vocabulary_deliver_the_choice() -> None:
    """MST-OUT-05 / DSP-OUT-09: image and vocabulary carry the new evidence surface."""
    dockerfile = (ROOT / "orchestration/Dockerfile").read_text("utf-8")
    assert "COPY orchestration/llm_brief.py orchestration/llm_brief.py" in dockerfile
    vocabulary = json.loads(
        (PACKS / "trading_graph_vocabulary.json").read_text("utf-8")
    )
    assert {"llm_candidate", "llm_passed_over"} <= set(
        vocabulary["properties"]["AgentInstance"]
    )
    assert "llm_passed_over" in vocabulary["properties"]["FleetPreflight"]


def test_a26_narrow_step_sets_vocabulary_before_pack() -> None:
    """MST-OUT-05: vocabulary success gates the pack, both successes gate the action."""
    script = deploy()
    body = script.split("function Enable-LlmCandidates {", 1)[1].split("\n}", 1)[0]
    assert body.index('Set-AppVocabulary "master"') < body.index("Get-MasterLlmPackEnv")
    gated = body.split("if ($vocabOk) {", 1)[1].split("\n  }", 1)[0]
    assert "(Get-MasterLlmPackEnv)" in gated
    assert '"containerapp", "update", "--name", "master"' in gated
    assert '((Get-AppState "master") -eq "Succeeded")' in body
    assert "return $vocabOk -and $packOk" in body
    validate = script.split("[ValidateSet(", 1)[1].split(")]", 1)[0]
    assert "'llm-candidates'" in validate
    assert "'llm-candidates' { if (-not (Enable-LlmCandidates)) { throw" in script


def test_a27_declared_provider_is_first_candidates_vendor() -> None:
    """MST-OUT-05: deploy and switch declare the first candidate's vendor."""
    raw = json.loads((PACKS / "trading_llm.json").read_text("utf-8"))
    assert raw["candidates"][0] == {
        "vendor": "openai",
        "model": "gpt-5.5",
        "effort": "high",
    }
    assert declared_provider(raw) == load_pack(ROOT).provider == "openai"
    assert "@($pack.candidates)[0].vendor" in deploy()
    assert "$pack.provider" not in deploy()


@pytest.mark.parametrize("candidates", [[], {}, [1]])
def test_a27_switch_refuses_a_missing_or_malformed_first_candidate(
    candidates: object,
) -> None:
    """MST-OUT-05: the switch cannot declare a vendor from a malformed candidate."""
    with pytest.raises(ValueError, match="candidate"):
        declared_provider({"candidates": candidates})


@pytest.mark.parametrize(
    "candidate", ["openai/gpt-5.5/high", "anthropic/claude-opus-5/max"]
)
def test_a28_switch_proves_a_choosing_app_by_its_candidate(candidate: str) -> None:
    """MST-OUT-05: the chosen provider proves the switch without legacy lists."""
    graph = InMemoryGraphStore()
    since = datetime(2026, 10, 15, 22, 0, tzinfo=UTC)
    graph.merge_node(
        "FleetPreflight",
        "ready",
        {"checked_at": since.isoformat(), "passed": True, "llm_passed_over": []},
    )
    graph.merge_node(
        "AgentInstance",
        "manager",
        {
            "agent_type": "deliberator-manager",
            "state": "active",
            "started_at": since.isoformat(),
            "llm_candidate": candidate,
        },
    )
    expected = (
        []
        if candidate.startswith("openai/")
        else [
            "deliberator-manager: vendor probe not passed "
            "or other vendor probe declared"
        ]
    )
    assert (
        missing_terms(graph, load_pack(ROOT), ["deliberator-manager"], since)
        == expected
    )
