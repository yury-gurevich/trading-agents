"""Provider-switch configuration validation without external calls.

Agent: tooling
Role: prove invalid pack, timestamp and polling inputs refuse before Azure.
External I/O: temporary fixture pack files only.
"""

import json
from pathlib import Path

import pytest
from tests.switch_llm_testkit import APPS, ROOT, START, FakeAzure, run_switch


@pytest.mark.parametrize(
    "apps",
    [[], {}, {"operator": "OPERATOR_LLM_PROVIDER"}, {"master": "WRONG"}],
)
def test_invalid_target_map_refuses_before_azure(tmp_path: Path, apps: object) -> None:
    """MST-OUT-04: targets must be ordered, master-first provider settings."""
    packs = tmp_path / "root/orchestration/packs"
    packs.mkdir(parents=True)
    (packs / "trading_llm.json").write_text(
        json.dumps({"provider": "openai", "apps": apps}), encoding="utf-8"
    )
    (packs / "trading_credential_tests.json").write_text(
        (ROOT / "orchestration/packs/trading_credential_tests.json").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    azure = FakeAzure()
    code, output = run_switch(tmp_path / "evidence", azure, root=tmp_path / "root")
    assert code == 2
    assert any("configuration refused" in line for line in output)
    assert azure.calls == []


def test_missing_selected_probe_refuses_before_azure(tmp_path: Path) -> None:
    """MST-NEV-07: each non-master target must have a selected vendor probe."""
    packs = tmp_path / "root/orchestration/packs"
    packs.mkdir(parents=True)
    (packs / "trading_llm.json").write_text(
        json.dumps({"provider": "openai", "apps": APPS}), encoding="utf-8"
    )
    (packs / "trading_credential_tests.json").write_text("{}", encoding="utf-8")
    azure = FakeAzure()
    code, output = run_switch(tmp_path / "evidence", azure, root=tmp_path / "root")
    assert code == 2
    assert any("operator has no declared openai probe" in line for line in output)
    assert azure.calls == []


@pytest.mark.parametrize(
    "value", ["invalid", "2026-10-09T00:00:00", "2026-10-09T10:00:00+10:00"]
)
def test_invalid_proof_timestamp_refuses(tmp_path: Path, value: str) -> None:
    """MST-OUT-04: proof resume requires an aware UTC timestamp."""
    azure = FakeAzure()
    code, _output = run_switch(tmp_path, azure, args=["--prove-since", value])
    assert code == 2
    assert azure.calls == []


@pytest.mark.parametrize(
    ("option", "value"), [("--poll-seconds", "0"), ("--wait-seconds", "-1")]
)
def test_invalid_poll_bounds_refuse(tmp_path: Path, option: str, value: str) -> None:
    """MST-OUT-04: invalid poll bounds never start a proof wait."""
    azure = FakeAzure()
    code, _output = run_switch(
        tmp_path, azure, args=["--prove-since", START.isoformat(), option, value]
    )
    assert code == 2
    assert azure.calls == []


def test_apply_requires_an_evidence_directory(tmp_path: Path) -> None:
    """MST-OUT-04: apply without durable external evidence is refused."""
    azure = FakeAzure()
    code, output = run_switch(tmp_path, azure, args=["--apply"])
    assert code == 2
    assert any("--evidence-dir" in line for line in output)
    assert azure.calls == []


def test_missing_pack_refuses_before_azure(tmp_path: Path) -> None:
    """MST-NEV-07: a missing declaration never assumes a provider."""
    azure = FakeAzure()
    code, _output = run_switch(tmp_path / "evidence", azure, root=tmp_path / "root")
    assert code == 2
    assert azure.calls == []


def test_subscription_and_resource_group_reach_every_call(tmp_path: Path) -> None:
    """MST-OUT-04: selected Azure scope is preserved on read-only report calls."""
    azure = FakeAzure(differing=())
    code, _output = run_switch(
        tmp_path,
        azure,
        args=["--resource-group", "fixture-group", "--subscription", "fixture-sub"],
        root=ROOT,
    )
    assert code == 0
    for call in azure.calls:
        assert call[call.index("--resource-group") + 1] == "fixture-group"
        assert call[call.index("--subscription") + 1] == "fixture-sub"
