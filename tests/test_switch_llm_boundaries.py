"""Azure/graph boundary refusal and credential containment tests.

Agent: tooling
Role: prove external errors do not expose credentials or become success.
External I/O: temporary snapshots only; runner and graph are fake.
"""

import subprocess
from pathlib import Path

import pytest
from scripts import switch_llm_azure
from tests.switch_llm_testkit import FakeAzure


@pytest.mark.parametrize(
    ("operation", "stdout", "code"),
    [
        ("show", "[]", 0),
        ("show", "progress", 0),
        ("show", "{}", 1),
        ("replica", "{}", 0),
    ],
)
def test_malformed_azure_result_refuses_without_stderr(
    tmp_path: Path, operation: str, stdout: str, code: int
) -> None:
    """MST-OUT-04 / OPR-SEC-01: invalid Azure output fails without echoing stderr."""
    azure = FakeAzure()
    sentinel = "fixture-private-stderr"

    def runner(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[1] == operation:
            return subprocess.CompletedProcess(args, code, stdout, sentinel)
        return azure(args)

    from scripts.switch_llm_provider import main
    from tests.switch_llm_testkit import ROOT, FakeClock, proof_graph

    clock = FakeClock()
    output: list[str] = []
    result = main(
        ["--apply", "--evidence-dir", str(tmp_path)],
        runner=runner,
        graph=proof_graph(),
        clock=clock,
        sleep=clock.sleep,
        environ={"POSTGRES_DSN": "fixture"},
        root=ROOT,
        emit=output.append,
    )
    assert result == 1
    assert sentinel not in "\n".join(output)
    assert azure.updates == []


def test_unexpected_runner_error_is_sanitized() -> None:
    """OPR-SEC-01 / MST-OUT-04: an arbitrary exception never prints credentials."""

    def fail(args: list[str]) -> object:
        raise RuntimeError("fixture-private-error")

    from scripts.switch_llm_provider import main

    output: list[str] = []
    assert main([], runner=fail, emit=output.append) == 1
    assert "fixture-private-error" not in "\n".join(output)
    assert "switch failed: RuntimeError" in output


def test_uninjected_graph_uses_the_validated_postgres_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MST-OUT-04: proof cannot fall through to the development memory backend."""
    from scripts.switch_llm_provider import main
    from tests.switch_llm_testkit import START, FakeClock, proof_graph

    from kernel import graph_postgres
    from kernel.graph_postgres_config import PostgresGraphSettings

    captured: list[str] = []

    def store(settings: PostgresGraphSettings) -> object:
        captured.append(settings.postgres_dsn)
        return proof_graph()

    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    monkeypatch.setattr(graph_postgres, "PostgresGraphStore", store)
    clock = FakeClock()
    assert (
        main(
            ["--prove-since", START.isoformat()],
            clock=clock,
            sleep=clock.sleep,
            environ={"POSTGRES_DSN": "fixture-validated-dsn"},
        )
        == 0
    )
    assert captured == ["fixture-validated-dsn"]


def test_resolved_azure_executable_uses_argument_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MST-OUT-04: runner resolves az and captures stdout/stderr without a shell."""
    monkeypatch.setattr(switch_llm_azure.shutil, "which", lambda name: "fixture-az")
    captured: list[tuple[list[str], dict]] = []

    def run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, "{}", "progress")

    monkeypatch.setattr(switch_llm_azure.subprocess, "run", run)
    result = switch_llm_azure.run_az(["containerapp", "show"])
    assert result.stdout == "{}"
    assert captured == [
        (
            ["fixture-az", "containerapp", "show"],
            {"capture_output": True, "text": True, "check": False},
        )
    ]
    monkeypatch.setattr(switch_llm_azure.shutil, "which", lambda name: None)
    with pytest.raises(switch_llm_azure.SwitchOperationError, match="unavailable"):
        switch_llm_azure.run_az([])
