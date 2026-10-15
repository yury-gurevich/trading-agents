"""A23-A24: every image receives the vocabulary before the candidate packs.

Agent: tooling
Role: inspect deploy bytes and the committed graph/property declarations.
External I/O: committed source reads only; no deploy command is executed.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "orchestration/packs"


def test_a23_role_vocabulary_success_gates_pack_delivery() -> None:
    """MST-OUT-05: master then every declared role must succeed before packs ship."""
    raw = (ROOT / "infra/deploy-agents.ps1").read_bytes()
    script = raw.decode("utf-8")
    body = script.split("function Enable-LlmCandidates {", 1)[1].split("\n}", 1)[0]
    master = '$vocabOk = Set-AppVocabulary "master"'
    loop = "foreach ($role in @((Load-LlmPack).roles.PSObject.Properties.Name)) {"
    assert master in body
    assert loop in body
    role_body = body.split(loop, 1)[1].split("\n  }", 1)[0]
    expected = [
        "$roleOk = Set-AppVocabulary $role",
        'Check $roleOk "graph vocabulary on $role"',
        "$vocabOk = $vocabOk -and $roleOk",
    ]
    assert all(text in role_body for text in expected)
    assert [role_body.index(text) for text in expected] == sorted(
        role_body.index(text) for text in expected
    )
    assert body.index(master) < body.index(loop) < body.index("if ($vocabOk) {")
    gated = body.split("if ($vocabOk) {", 1)[1].split("\n  }", 1)[0]
    assert "(Get-MasterCredentialTestsEnv)" in gated
    assert "(Get-MasterLlmPackEnv)" in gated
    assert "return $vocabOk -and $packOk" in body
    assert "\t" not in body


def test_a24_vocabulary_declares_every_fallback_property_in_sorted_lists() -> None:
    """MST-OBS-04 / DLIB-OUT-02 / DLIB-FAIL-05: images' new props are declared."""
    vocabulary = json.loads(
        (PACKS / "trading_graph_vocabulary.json").read_text("utf-8")
    )
    for label, prop in (
        ("AgentInstance", "llm_fallbacks"),
        ("DeliberationRun", "llm_switches"),
        ("LLMCall", "llm_passed_over"),
    ):
        names = vocabulary["properties"][label]
        assert prop in names
        assert names == sorted(names)
    declaration = json.loads((PACKS / "trading_llm.json").read_text("utf-8"))
    assert set(declaration["roles"]) == {
        "deliberator-manager",
        "deliberator-proponent",
        "deliberator-opponent",
    }
    assert all(
        role["fallbacks"] == "DELIBERATOR_LLM_FALLBACKS"
        for role in declaration["roles"].values()
    )
