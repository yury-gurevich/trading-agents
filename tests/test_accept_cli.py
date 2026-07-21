"""Acceptance CLI wiring tests.

Agent: tooling
Role: verify scripts.accept parses the run id, loads the injected graph, renders
      the result, and maps the acceptance verdict to its process exit code.
External I/O: none.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest
from scripts import accept as accept_cli


def test_accept_cli_wires_run_id_graph_result_and_exit_code(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Kills scripts.accept.x_main__mutmut_1."""
    calls: dict[str, object] = {}
    graph = object()
    verdict = SimpleNamespace(passed=True)

    def load_dotenv() -> None:
        calls["loaded_dotenv"] = True

    def build_graph_from_env() -> object:
        calls["built_graph"] = True
        return graph

    def accept_run(received_graph: object, run_id: str) -> object:
        calls["accepted"] = (received_graph, run_id)
        return verdict

    def render_acceptance(result: object) -> str:
        calls["rendered"] = result
        return "ACCEPTANCE  PASS"

    monkeypatch.setitem(sys.modules, "dotenv", SimpleNamespace(load_dotenv=load_dotenv))
    monkeypatch.setitem(
        sys.modules,
        "kernel.graph_env",
        SimpleNamespace(build_graph_from_env=build_graph_from_env),
    )
    monkeypatch.setitem(
        sys.modules,
        "orchestration.packs.trading_acceptance",
        SimpleNamespace(accept_run=accept_run, render_acceptance=render_acceptance),
    )
    monkeypatch.setattr(sys, "argv", ["accept.py", "--run-id", "run-42"])

    with pytest.raises(SystemExit) as exc:
        accept_cli.main()

    assert exc.value.code == 0
    assert calls == {
        "loaded_dotenv": True,
        "built_graph": True,
        "accepted": (graph, "run-42"),
        "rendered": verdict,
    }
    assert capsys.readouterr().out == "ACCEPTANCE  PASS\n"
