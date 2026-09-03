"""Read-only replay of a recorded debate turn, for reproducibility measurement.

Agent: orchestration
Role: rebuild the exact user prompt a stored debate turn was sent, and digest it.
External I/O: reads the injected GraphStore. Writes nothing, by design.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kernel.deliberation import Proposition, Turn, render_debate_prompt
from kernel.llm_ledger import digest_text
from orchestration.veto_context import build_veto_context

if TYPE_CHECKING:
    from contracts.portfolio_manager import OrderIntent, OrderIntentSet
    from kernel import GraphStore, Node

__all__ = ["replayed_prompt_digest", "replayed_user_prompt"]


def replayed_user_prompt(
    graph: GraphStore,
    pm_node: Node,
    order_set: OrderIntentSet,
    intent: OrderIntent,
    *,
    transcript: tuple[Turn, ...] = (),
) -> str:
    """Rebuild the user string one debate turn was sent, from graph state.

    The decision line mirrors the manager (`agents/deliberator/poll.py`), and the
    evidence body is the same `build_veto_context` the live path calls. An empty
    ``transcript`` reproduces the first defender turn, which is a pure function of
    the graph; later turns need the transcript the run recorded.
    """
    proposition = Proposition(
        f"{intent.action} {intent.ticker} (qty {intent.quantity})",
        build_veto_context(graph, pm_node, order_set, intent),
    )
    return render_debate_prompt(proposition, transcript)


def replayed_prompt_digest(
    graph: GraphStore,
    pm_node: Node,
    order_set: OrderIntentSet,
    intent: OrderIntent,
    *,
    transcript: tuple[Turn, ...] = (),
) -> str:
    """Digest the replayed prompt the way the ledger digests the live one.

    Uses the ledger's own ``digest_text`` rather than a second hash implementation, so
    an equal digest means the bytes matched — not that two hash functions agree.

    Scope, measured 2026-09-03: ``LLMCall.prompt_hash`` covers the *user* string only
    (`agents/deliberator/agent.py` passes ``prompt=user``), so equality proves the user
    context was reconstructed, **not** that the system prompt was identical.
    DLIB-IDM-02's "bounded by prompt hashes" is narrower than it reads.
    """
    return digest_text(
        replayed_user_prompt(graph, pm_node, order_set, intent, transcript=transcript)
    )
