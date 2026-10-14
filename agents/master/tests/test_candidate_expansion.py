"""A10-A11 and A14: startup builds runnable candidate probes from injected packs.

Agent: master
Role: prove expansion refusals, role entitlements and deploy-style pack loading.
External I/O: committed pack files only; no probe is sent by build_app.
"""

import base64
from dataclasses import replace

import pytest

from agents.master.credential_probes import load_credential_tests
from agents.master.entrypoint import build_app
from agents.master.model_candidates import load_llm_plan
from agents.master.model_expansion import expand_llm_candidates
from agents.master.secret_map import SecretMap, load_secret_map
from agents.master.settings import MasterSettings
from agents.master.tests.candidate_testkit import PACKS, FixtureSecrets, world
from kernel import InMemoryGraphStore


@pytest.mark.parametrize("breakage", ["probe", "paths", "key", "map"])
def test_a10_expansion_refuses_unrunnable_roles(breakage: str) -> None:
    """MST-NEV-08: every role needs every candidate's probe, paths and granted key."""
    plan = load_llm_plan(str(PACKS / "trading_llm.json"))
    tests = load_credential_tests(str(PACKS / "trading_credential_tests.json"))
    declared = load_secret_map(str(PACKS / "trading_secrets.json"))
    secrets: SecretMap | None = declared
    if breakage == "probe":
        tests = tuple(
            test
            for test in tests
            if not (
                test.agent_types == ("deliberator-manager",)
                and test.llm_provider == "anthropic"
            )
        )
        cause = "has no anthropic probe"
    elif breakage == "paths":
        tests = tuple(replace(test, takes_candidate=False) for test in tests)
        cause = "without candidate_paths"
    elif breakage == "key":
        secrets = {
            name: [(kv, env) for kv, env in pairs if env != "ANTHROPIC_API_KEY"]
            for name, pairs in declared.items()
        }
        cause = "not granted ANTHROPIC_API_KEY"
    else:
        secrets = None
        cause = "not granted OPENAI_API_KEY"
    with pytest.raises(ValueError, match=f"deliberator-manager candidate .*{cause}"):
        expand_llm_candidates(plan, "openai", tests, secrets)


def test_a11_expansion_preserves_roles_keys_and_nonchoosing_probe() -> None:
    """MST-OUT-05 / MST-NEV-07: roles keep both keys; the operator keeps one."""
    fixture = world()
    candidates = [test for test in fixture.tests if test.candidate is not None]
    assert len(candidates) == 6
    for role in (
        "deliberator-manager",
        "deliberator-proponent",
        "deliberator-opponent",
    ):
        probes = [test for test in candidates if test.agent_types == (role,)]
        assert [test.name for test in probes] == [
            "openai:gpt-5.5:high",
            "anthropic:claude-opus-5:max",
        ]
        assert all(test.role is not None and test.takes_candidate for test in probes)
        keys = {env for _, env in fixture.secrets[role]}
        assert {"OPENAI_API_KEY", "ANTHROPIC_API_KEY"} <= keys
    operator = [test for test in fixture.tests if test.agent_types == ("operator",)]
    assert [test.name for test in operator] == ["openai"]
    assert not operator[0].takes_candidate
    assert "ANTHROPIC_API_KEY" not in {env for _, env in fixture.secrets["operator"]}
    assert (
        expand_llm_candidates(None, "openai", fixture.tests, fixture.secrets)
        is fixture.tests
    )


def test_a14_base64_packs_start_master_as_deploy_delivers_them() -> None:
    """MST-NEV-08: all four deploy packs load and expand before any activation."""

    def packed(name: str) -> str:
        return base64.b64encode((PACKS / name).read_bytes()).decode("ascii")

    settings = MasterSettings(
        _env_file=None,
        llm_provider="openai",
        grant_policy_b64=packed("trading_grants.json"),
        secret_map_b64=packed("trading_secrets.json"),
        credential_tests_b64=packed("trading_credential_tests.json"),
        llm_pack_b64=packed("trading_llm.json"),
        llm_pack_path="does-not-exist.json",
    )
    graph = InMemoryGraphStore()
    agent, pem = build_app(graph, "fixture-pem", settings, FixtureSecrets())
    assert pem == "fixture-pem"
    assert len(graph.list_nodes("Session")) == 1
    assert [
        test.name
        for test in agent._credential_tests
        if test.agent_types == ("deliberator-manager",)
    ] == ["openai:gpt-5.5:high", "anthropic:claude-opus-5:max"]
