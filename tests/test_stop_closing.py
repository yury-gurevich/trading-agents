"""Closing-step and closing-line proofs for S272.

Agent: kernel
Role: prove independent cleanup, explicit failure and sanitized closing evidence.
External I/O: captured stderr only.
"""

from __future__ import annotations

import pytest

from kernel.stop import StopSignal, closing_steps, end_loop, finish


@pytest.mark.parametrize(
    ("failure", "unfinished", "tail", "clean"),
    [
        (False, (), "closed faults, graph; exit 0", True),
        (True, (), "closed graph; NOT closed faults (ConnectionError); exit 1", False),
        (False, ("one item",), "left one item; closed faults, graph; exit 1", False),
    ],
)
def test_a12_each_closing_step_runs_and_the_line_is_exact(
    failure, unfinished, tail, clean
) -> None:
    """MST-TRG-03 / MST-OBS-05: failures do not skip cleanup or disclose text."""
    clock = [10.0]
    stop = StopSignal(lambda: clock[0])
    stop.request("SIGTERM")
    clock[0] = 12.3
    calls: list[str] = []
    lines: list[str] = []

    def faults():
        calls.append("faults")
        if failure:
            raise ConnectionError("private-marker")

    result = finish(
        stop,
        agent="scanner",
        steps=(("faults", faults), ("graph", lambda: calls.append("graph"))),
        unfinished=unfinished,
        write=lines.append,
    )
    assert result is clean
    assert calls == ["faults", "graph"]
    assert lines == [f"[scanner] stopped on SIGTERM after 2.3 s: {tail}\n"]
    assert "private-marker" not in lines[0]


def test_a12_no_steps_and_end_loop_exit_codes(capsys) -> None:
    """MST-TRG-03 / MST-OBS-05: no resources is clean; only failure exits 1."""
    stop = StopSignal(lambda: 10.0)
    stop.request("SIGTERM")
    end_loop(stop, agent="agent", steps=())
    assert capsys.readouterr().err == (
        "[agent] stopped on SIGTERM after 0.0 s: nothing to close; exit 0\n"
    )

    def fail():
        raise ConnectionError("private-marker")

    with pytest.raises(SystemExit) as caught:
        end_loop(stop, agent="agent", steps=(("graph", fail),))
    assert caught.value.code == 1
    assert capsys.readouterr().err == (
        "[agent] stopped on SIGTERM after 0.0 s: "
        "NOT closed graph (ConnectionError); exit 1\n"
    )


def test_a12_steps_name_only_held_closable_resources() -> None:
    """MST-TRG-03 / MST-OBS-05: faults, requests, graph close in that order."""
    calls: list[str] = []

    class Held:
        def __init__(self, name):
            self.name = name

        def close(self):
            calls.append(self.name)

    steps = closing_steps(
        faults=lambda: calls.append("faults"),
        requests=Held("requests"),
        graph=Held("graph"),
    )
    assert [name for name, _step in steps] == ["faults", "requests", "graph"]
    for _name, step in steps:
        step()
    assert calls == ["faults", "requests", "graph"]
    assert closing_steps(requests=object(), graph=None) == ()
