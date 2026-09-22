"""Outage CLI wiring: the verdict reaches the operator and the exit code.

Agent: tooling
Role: verify scripts.check_llm_outage loads the graph, reports every calling
      agent, closes the store, and exits non-zero only on a total outage.
External I/O: none.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import TYPE_CHECKING

from scripts import check_llm_outage as cli

from kernel.graph import Node
from kernel.llm_ledger import digest_text

if TYPE_CHECKING:
    import pytest


def _call(agent: str, *, response: str, stop_reason: str) -> Node:
    return Node(
        label="LLMCall",
        key=f"llmcall:{agent}:{stop_reason}:{response}",
        props={
            "calling_agent": agent,
            "response_hash": digest_text(response),
            "stop_reason": stop_reason,
        },
    )


def _wire(
    monkeypatch: pytest.MonkeyPatch, nodes: tuple[Node, ...]
) -> dict[str, object]:
    calls: dict[str, object] = {}

    def load_dotenv(path: object, override: bool = False) -> None:
        calls["loaded"] = (path, override)

    class _Graph:
        def list_nodes(self, label: str) -> tuple[Node, ...]:
            calls["label"] = label
            return nodes

        def close(self) -> None:
            calls["closed"] = True

    monkeypatch.setitem(sys.modules, "dotenv", SimpleNamespace(load_dotenv=load_dotenv))
    monkeypatch.setitem(
        sys.modules,
        "kernel.graph_env",
        SimpleNamespace(build_graph_from_env=lambda: _Graph()),
    )
    return calls


def test_a_healthy_ledger_exits_zero_and_names_the_agents(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The negative control: a working night must not read as an outage."""
    calls = _wire(
        monkeypatch,
        (
            _call("deliberator", response="a turn", stop_reason="end_turn"),
            _call("operator", response="a tool call", stop_reason="end_turn"),
        ),
    )

    exit_code = cli.main([])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "ok:" in out
    assert "deliberator, operator" in out
    assert calls["label"] == "LLMCall"
    assert calls["closed"] is True


def test_a_total_outage_exits_non_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """🎯 The nine blind nights, now detectable without an acceptance run."""
    _wire(
        monkeypatch,
        (
            _call("deliberator", response="", stop_reason="unknown"),
            _call("operator", response="", stop_reason="unknown"),
        ),
    )

    exit_code = cli.main([])
    out = capsys.readouterr().out

    assert exit_code == 1
    assert "total_outage" in out
    assert "2/2 calls silent" in out


def test_a_partial_night_is_reported_but_does_not_fail(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A check that exits non-zero on ordinary noise is one nobody runs."""
    _wire(
        monkeypatch,
        (
            _call("deliberator", response="a turn", stop_reason="end_turn"),
            _call("operator", response="", stop_reason="unknown"),
        ),
    )

    exit_code = cli.main([])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "partial" in out
    assert "operator" in out


def test_an_empty_ledger_reports_nothing_to_conclude(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """🪤 No calls is not a healthy night, and the agents line is omitted."""
    _wire(monkeypatch, ())

    exit_code = cli.main([])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "nothing to conclude" in out
    assert "agents seen" not in out


def test_a_store_without_close_is_tolerated(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The in-memory store has no `close`; the report must still print."""

    class _Graph:
        def list_nodes(self, label: str) -> tuple[Node, ...]:
            return (_call("operator", response="hi", stop_reason="end_turn"),)

    monkeypatch.setitem(
        sys.modules, "dotenv", SimpleNamespace(load_dotenv=lambda *a, **k: None)
    )
    monkeypatch.setitem(
        sys.modules,
        "kernel.graph_env",
        SimpleNamespace(build_graph_from_env=lambda: _Graph()),
    )

    assert cli.main([]) == 0
    assert "ok:" in capsys.readouterr().out
