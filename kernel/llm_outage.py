"""Detect a silent LLM outage from the call ledger alone.

Agent: kernel
Role: classify a window of LLMCall rows as healthy, partially failing, or a
      total outage, from the rows themselves.
External I/O: none.

Nine nights returned nothing and nobody noticed. Measured 2026-09-13 over
`2026-08-21, -24, -25, -26, -28` and `2026-09-08, -09, -10, -11`: **every**
`LLMCall` carried `response_hash` = the SHA-256 of the empty string, with
`stop_reason='unknown'` and a mean latency of ~300 ms against a working night's
~15,610 ms over 1,042 calls. The first was nineteen days before anyone filed it.

🪰 **`tokens_out == 0` is NOT the signature.** 140 of 1,182 rows carry it,
including partial-failure days when the system was working. A check built on it
cries wolf, and a check that cries wolf is one nobody reads.

🪤 **An empty response is not by itself a failure.** A normal `end_turn`
carrying an empty string is a legitimate model answer at the port level
(DL decision 1 on the shared stopped-completion exception). So the signature is
the empty hash **together with** a stop reason the model never gave: the call
did not complete, as opposed to completing with nothing to say.

Latency is deliberately *not* part of the predicate. The measured separation is
wide (~300 ms against ~15,610 ms), but a threshold is a magic number that would
need its own evidence envelope and would misread a genuinely fast completion.
`stop_reason` already carries the distinction without one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from kernel.llm import STOP_REASON_UNKNOWN
from kernel.llm_ledger import digest_text

if TYPE_CHECKING:
    from collections.abc import Iterable

    from kernel.graph import Node

#: SHA-256 of the empty string — what the ledger records when nothing came back.
EMPTY_RESPONSE_HASH = digest_text("")

VERDICT_OK = "ok"
VERDICT_PARTIAL = "partial"
VERDICT_TOTAL_OUTAGE = "total_outage"
VERDICT_NO_CALLS = "no_calls"


@dataclass(frozen=True)
class LLMOutageReport:
    """What a window of ledger rows says about whether the models answered."""

    calls: int
    silent_calls: int
    verdict: str
    agents: tuple[str, ...]
    silent_agents: tuple[str, ...]

    @property
    def is_total_outage(self) -> bool:
        """True when every call in the window came back silent."""
        return self.verdict == VERDICT_TOTAL_OUTAGE

    def summary(self) -> str:
        """One line an operator can read without opening the graph."""
        if self.verdict == VERDICT_NO_CALLS:
            return "no LLM calls in window — nothing to conclude"
        agents = ", ".join(self.silent_agents) or "-"
        return (
            f"{self.verdict}: {self.silent_calls}/{self.calls} calls silent"
            f" (agents: {agents})"
        )


def is_silent_call(node: Node) -> bool:
    """True when this call returned nothing and never said why.

    Both halves are required. The empty hash alone would flag a legitimate
    empty answer; an unknown stop reason alone says nothing about content.
    """
    props = node.props
    response_hash = str(props.get("response_hash", ""))
    stop_reason = str(props.get("stop_reason", "")).strip() or STOP_REASON_UNKNOWN
    return response_hash == EMPTY_RESPONSE_HASH and stop_reason == STOP_REASON_UNKNOWN


def outage_report(nodes: Iterable[Node]) -> LLMOutageReport:
    """Classify a window of LLMCall rows.

    🪤 An empty window is `no_calls`, never `ok`. A night on which nothing ran
    is not a night on which everything worked, and reporting it green is how a
    dead scheduler passes for a healthy one.
    """
    rows = tuple(nodes)
    agents: list[str] = []
    silent_agents: list[str] = []
    silent = 0
    for node in rows:
        agent = str(node.props.get("calling_agent", ""))
        if agent and agent not in agents:
            agents.append(agent)
        if is_silent_call(node):
            silent += 1
            if agent and agent not in silent_agents:
                silent_agents.append(agent)
    if not rows:
        verdict = VERDICT_NO_CALLS
    elif silent == len(rows):
        verdict = VERDICT_TOTAL_OUTAGE
    elif silent:
        verdict = VERDICT_PARTIAL
    else:
        verdict = VERDICT_OK
    return LLMOutageReport(
        calls=len(rows),
        silent_calls=silent,
        verdict=verdict,
        agents=tuple(sorted(agents)),
        silent_agents=tuple(sorted(silent_agents)),
    )
