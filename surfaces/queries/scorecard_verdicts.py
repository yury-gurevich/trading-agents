"""One verdict word per scheduled session, never decided or recomputed here.

Agent: surfaces
Role: read a session's word: the brief's stored verdict, else the gate's, judged once.
External I/O: injected GraphStore reads; the acceptance gate reads the same graph.

The word is the acceptance gate's, so "complete" has one definition (DL-208). A briefed
run carries it as `brief_verdict` (DSP-IDM-03) and never reaches `accept_run`; any other
run is judged at most once per process, because one judgement costs about 3 s (DL-235).
"""

from __future__ import annotations

from collections.abc import Callable
from threading import Lock
from typing import TYPE_CHECKING

from orchestration.packs.trading_acceptance import accept_run

if TYPE_CHECKING:
    from kernel import GraphStore, Node
    from orchestration.packs.trading_acceptance import TradingAcceptanceResult

Judge = Callable[["GraphStore", str], "TradingAcceptanceResult"]

MISSED = "MISSED"  # no RunRequest was ever placed for the session
# The complete words. Never `.passed`: it is true for UNPROVEN (DL-59).
COMPLETE = frozenset({"PASS", "NO_TRADE"})
BRIEF_VERDICT = "brief_verdict"


class VerdictMemo:
    """The acceptance gate's word per run id, judged at most once."""

    def __init__(self, judge: Judge = accept_run) -> None:
        """Hold ``judge`` (in production `accept_run`) and an empty memo."""
        self.judge = judge
        self._words: dict[str, str] = {}
        self._lock = Lock()  # concurrent refreshes must not judge one run twice

    def word(self, graph: GraphStore, run_id: str) -> str:
        """Return the gate's word for ``run_id``, judging it only the first time."""
        with self._lock:
            if run_id not in self._words:
                self._words[run_id] = self.judge(graph, run_id).verdict
            return self._words[run_id]


# One memo for the process: the tile, the chat and the MCP tool share it (DL-235).
PROCESS_VERDICTS = VerdictMemo()


def session_word(
    graph: GraphStore, run_id: str, request: Node | None, memo: VerdictMemo
) -> str:
    """Return a session's word: as the brief stored it, else judged once, or MISSED."""
    if request is None:
        return MISSED
    stored = request.props.get(BRIEF_VERDICT)
    if isinstance(stored, str) and stored:
        return stored
    return memo.word(graph, run_id)
