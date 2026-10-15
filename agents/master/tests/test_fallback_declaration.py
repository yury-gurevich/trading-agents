"""A17: the fallback handover key is a required part of every declared role.

Agent: master
Role: prove real-pack keys and refusal of an incomplete role declaration.
External I/O: committed pack reads only.
"""

import json

import pytest

from agents.master.model_candidates import load_llm_plan, parse_llm_plan
from agents.master.tests.candidate_testkit import PACKS


def test_a17_every_role_names_its_fallbacks_key() -> None:
    """MST-OUT-05 / MST-NEV-08: every choosing role names the required fourth key."""
    plan = load_llm_plan(str(PACKS / "trading_llm.json"))
    assert len(plan.roles) == 3
    for role in plan.roles.values():
        assert role.fallbacks_key == "DELIBERATOR_LLM_FALLBACKS"


@pytest.mark.parametrize(
    "role", ["deliberator-manager", "deliberator-proponent", "deliberator-opponent"]
)
def test_a17_missing_fallback_key_refuses_pack(role: str) -> None:
    """MST-NEV-08: missing fallbacks cannot silently become an empty handover key."""
    raw = json.loads((PACKS / "trading_llm.json").read_text("utf-8"))
    raw["roles"][role].pop("fallbacks", None)
    with pytest.raises(ValueError, match=r"'fallbacks'.*non-empty string"):
        parse_llm_plan(json.dumps(raw))
