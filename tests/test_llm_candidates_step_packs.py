"""The narrow LLM-candidates step delivers the credential pack the S276 master needs.

Agent: tooling
Role: pin that `deploy-agents.ps1 -Action llm-candidates` sends the credential pack with
      the candidate pack, and why: the injected pack wins over the image's file, and the
      S276 master refuses to start on an LLM role probe without `candidate_paths`.
External I/O: committed source reads only; no script or vendor is invoked.
"""

import json
from pathlib import Path

import pytest

from agents.master.credential_probes import parse_credential_tests
from agents.master.credential_selection import select_llm_provider
from agents.master.model_candidates import load_llm_plan
from agents.master.model_expansion import expand_llm_candidates
from agents.master.secret_map import load_secret_map

ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "orchestration/packs"


def _step() -> str:
    script = (ROOT / "infra/deploy-agents.ps1").read_bytes().decode("utf-8")
    return script.split("function Enable-LlmCandidates {", 1)[1].split("\n}", 1)[0]


def _expand(credential_pack: str) -> None:
    plan = load_llm_plan(str(PACKS / "trading_llm.json"))
    secret_map = load_secret_map(str(PACKS / "trading_secrets.json"))
    tests, secret_map = select_llm_provider(
        "openai", parse_credential_tests(credential_pack), secret_map, roles=plan.roles
    )
    expand_llm_candidates(plan, "openai", tests, secret_map)


def test_step_sends_the_credential_pack_with_the_candidate_pack() -> None:
    """MST-OUT-05: one master update carries both packs, after the vocabulary."""
    gated = _step().split("if ($vocabOk) {", 1)[1].split("\n  }", 1)[0]
    sent = '"--set-env-vars", (Get-MasterCredentialTestsEnv), (Get-MasterLlmPackEnv),'
    assert sent in gated
    assert gated.count('"containerapp", "update"') == 1


def test_the_master_refuses_a_credential_pack_without_candidate_paths() -> None:
    """MST-NEV-08: the s275 pack shape stops the S276 master, so the step sends it."""
    pack = json.loads((PACKS / "trading_credential_tests.json").read_text("utf-8"))
    _expand(json.dumps(pack))
    for entries in pack.values():
        for entry in entries if isinstance(entries, list) else ():
            entry.pop("candidate_paths", None)
    with pytest.raises(ValueError, match="candidate_paths"):
        _expand(json.dumps(pack))
