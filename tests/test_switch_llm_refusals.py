"""Provider-switch replica and configuration-preservation refusals.

Agent: tooling
Role: prove checks fail before unsafe updates or when anything else moves.
External I/O: temporary snapshots only, Azure is fake.
"""

import json
from pathlib import Path

import pytest
from tests.switch_llm_testkit import ROOT, START, FakeAzure, run_switch


def test_d3_evidence_inside_repo_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MST-OUT-04: evidence never enters the repository tree."""
    from scripts import switch_llm_provider

    # A planted path-guard break must still keep test evidence outside the tree.
    monkeypatch.setattr(
        switch_llm_provider, "apply", lambda *args, **kwargs: (0, START)
    )
    azure = FakeAzure()
    code, output = run_switch(
        tmp_path,
        azure,
        args=["--apply", "--evidence-dir", str(ROOT / "forbidden-evidence")],
    )
    assert code == 2
    assert any("outside the repository" in line for line in output)
    assert azure.updates == []


@pytest.mark.parametrize(
    "args", [["--apply"], ["--prove-since", "2026-10-09T00:00:00Z"]]
)
def test_d3_proof_without_dsn_is_refused(tmp_path: Path, args: list[str]) -> None:
    """MST-OUT-04: no proof silently reads an in-memory graph without POSTGRES_DSN."""
    azure = FakeAzure()
    if "--apply" in args:
        args += ["--evidence-dir", str(tmp_path)]
    code, output = run_switch(tmp_path, azure, args=args, environ={})
    assert code == 2
    assert any("POSTGRES_DSN" in line for line in output)
    assert azure.calls == []


def test_d3_replicas_refuse_before_first_update(tmp_path: Path) -> None:
    """MST-OUT-04: actual replicas refuse regardless of runningStatus."""
    azure = FakeAzure()
    azure.replicas = [{"name": "replica-1"}]
    code, output = run_switch(tmp_path, azure)
    assert code == 1
    assert any("has replicas" in line for line in output)
    assert azure.updates == []
    code, output = run_switch(
        tmp_path,
        azure,
        args=["--apply", "--evidence-dir", str(tmp_path), "--even-if-running"],
    )
    assert code == 0
    assert len(azure.updates) == 3


def test_d3_unknown_provider_refuses_before_azure(tmp_path: Path) -> None:
    """MST-NEV-07: a mistyped pack provider cannot apply or read Azure."""
    packs = tmp_path / "root/orchestration/packs"
    packs.mkdir(parents=True)
    (packs / "trading_llm.json").write_text(
        json.dumps({"provider": "opnai", "apps": {"master": "MASTER_LLM_PROVIDER"}})
    )
    (packs / "trading_credential_tests.json").write_text("{}", encoding="utf-8")
    azure = FakeAzure()
    code, output = run_switch(tmp_path / "evidence", azure, root=tmp_path / "root")
    assert code == 2
    assert any("opnai" in line for line in output)
    assert azure.calls == []


@pytest.mark.parametrize(
    "field", ["image", "scale", "env", "secrets", "ingress", "registries", "identity"]
)
def test_d4_nothing_else_may_move(tmp_path: Path, field: str) -> None:
    """MST-OUT-04: every protected snapshot field can falsify the apply."""
    azure = FakeAzure()

    def mutate(snapshot: dict) -> None:
        props = snapshot["properties"]
        if field == "image":
            props["template"]["containers"][0]["image"] = "unexpected"
        elif field == "scale":
            props["template"]["scale"]["minReplicas"] = 1
        elif field == "env":
            props["template"]["containers"][0]["env"].append(
                {"name": "UNRELATED", "value": "moved"}
            )
        elif field == "identity":
            snapshot["identity"]["type"] = "UserAssigned"
        else:
            props["configuration"][field] = [{"name": "unexpected"}]

    azure.mutate = mutate
    code, output = run_switch(tmp_path, azure)
    expected = {"image": "containers", "env": "containers"}.get(field, field)
    assert code == 1
    assert any(
        "master:" in line and expected in line and "moved" in line for line in output
    )
