"""Prove the local demonstrator stays within its process.

Agent: tooling
Role: pin DL-329 D1-D3 at the demonstrator CLI and committed pointers.
External I/O: reads committed files; no network, no database, no actual .env.
"""

import os
import re
import socket
import sys
from pathlib import Path

import dotenv
import pytest
from scripts import run_local

import kernel.graph_env
from orchestration.tests.lane_fixtures import (
    preserve_environment as preserve_environment,
)

REMOVED_ARGV = (
    ["--real"],
    ["--veto"],
    ["--universe", "scripts/universe_sp100.txt"],
    ["--chunk-size", "5"],
    ["--chunk-delay", "1"],
    ["--ohlcv-only"],
)
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def doors_shut(preserve_environment: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """DL-329 D2: refuse outward doors and restore all environment mutations."""

    def reached_outside(*args: object, **kwargs: object) -> None:
        raise AssertionError("the demonstrator reached outside its process")

    monkeypatch.setattr(dotenv, "load_dotenv", reached_outside)
    monkeypatch.setattr(dotenv, "dotenv_values", reached_outside)
    monkeypatch.setattr(kernel.graph_env, "build_graph_from_env", reached_outside)
    monkeypatch.setattr(socket, "getaddrinfo", reached_outside)
    monkeypatch.setattr(socket.socket, "connect", reached_outside)
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://planted@fleet.invalid/live")


@pytest.mark.parametrize("argv", REMOVED_ARGV, ids=[a[0] for a in REMOVED_ARGV])
def test_a_flag_that_reached_outside_the_process_is_refused(
    argv: list[str],
    doors_shut: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DL-329 D1: removed flags are refused before any outward door is reached."""
    monkeypatch.setattr(sys, "argv", ["run_local.py", *argv])
    with pytest.raises(SystemExit) as raised:
        run_local.main()
    assert raised.value.code == 2
    assert f"unrecognized arguments: {argv[0]}" in capsys.readouterr().err


@pytest.mark.parametrize(
    "argv",
    [[], ["--trace"], ["--observe"], ["--trace", "--observe", "--run-id", "demo-2"]],
)
def test_the_demo_reaches_nothing_outside_the_process(
    argv: list[str],
    doors_shut: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DL-329 D2: every remaining flag runs locally and leaves the environment."""
    monkeypatch.setattr(sys, "argv", ["run_local.py", *argv])
    before = dict(os.environ)
    run_local.main()
    assert dict(os.environ) == before
    output = capsys.readouterr().out
    run_id = "demo-2" if "--run-id" in argv else "local-1"
    assert "MODE: demo  (in-memory + fake data)" in output
    assert f"placed RunRequest run-request:{run_id} (2 tickers)" in output
    assert "  RunRequest     1" in output


def test_the_help_offers_only_the_in_memory_demo(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """DL-329 D1: help offers only the three demo flags and argparse help."""
    monkeypatch.setattr(sys, "argv", ["run_local.py", "--help"])
    with pytest.raises(SystemExit) as raised:
        run_local.main()
    assert raised.value.code == 0
    output = capsys.readouterr().out
    assert set(re.findall(r"--[a-z][a-z-]*", output)) == {
        "--help",
        "--trace",
        "--observe",
        "--run-id",
    }
    assert "POSTGRES" not in output
    assert "Tiingo" not in output


def test_the_docstring_sends_a_real_run_to_the_lane() -> None:
    """DL-329 D3: the module explains its limits and names the real-data lane."""
    doc = run_local.__doc__
    assert doc is not None
    assert "scripts/run_lane.py" in doc
    assert "No network, no database, no model call" in doc
    for argv in REMOVED_ARGV:
        assert argv[0] not in doc
    assert "POSTGRES_DSN" not in doc
    assert "Tiingo" not in doc


@pytest.mark.parametrize(
    "path",
    [
        "scripts/accept.py",
        "scripts/observatory.py",
        "scripts/trace_run.py",
        "scripts/universe_sp100.txt",
        "scripts/universe_sp500.txt",
        "docs/observability.md",
    ],
)
def test_no_committed_file_points_at_a_removed_flag(path: str) -> None:
    """DL-329 D3: every scoped committed pointer stops recommending old flags."""
    text = (ROOT / path).read_text(encoding="utf-8")
    for argv in REMOVED_ARGV:
        assert f"run_local.py {argv[0]}" not in text


def test_the_observability_guide_sends_a_test_run_to_the_lane() -> None:
    """DL-329 D3: the guide names the lane and the credential-free observatory."""
    text = (ROOT / "docs/observability.md").read_text(encoding="utf-8")
    assert "scripts/run_lane.py --tickers" in text
    assert "scripts/run_local.py --observe" in text
