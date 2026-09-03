"""Step 0 — a stored debate turn must be reconstructible from graph state alone.

Agent: orchestration
Role: prove the replay harness rebuilds the exact user prompt the live run recorded.
External I/O: none.
"""

from __future__ import annotations

from tests.veto_context_fixtures import intent, linked_graph, order_set

from kernel import InMemoryGraphStore
from kernel.deliberation import Proposition, render_debate_prompt
from kernel.llm_ledger import record_llm_call
from orchestration.deliberation_replay import replayed_prompt_digest


def _decision(item: object) -> str:
    """Mirror the manager's decision line (agents/deliberator/poll.py:136)."""
    return f"{item.action} {item.ticker} (qty {item.quantity})"  # type: ignore[attr-defined]


def test_replayed_defender_r1_digest_matches_the_recorded_prompt_hash() -> None:
    """DLIB-OBS-01 / DLIB-IDM-02: defender r1 is reconstructible from graph state alone.

    The first defender turn carries an empty transcript, so the whole user string is a
    function of the graph. This is the sharpest form of the claim DLIB-OBS-01 makes and
    has never been tested; DLIB-IDM-02's `prompt hashes` bound is what it measures.
    """
    graph = InMemoryGraphStore()
    item = intent()
    orders = order_set(item)
    pm_node = linked_graph(graph, full=True)

    from orchestration.veto_context import build_veto_context

    proposition = Proposition(
        _decision(item), build_veto_context(graph, pm_node, orders, item)
    )
    live_user = render_debate_prompt(proposition, ())
    with record_llm_call(
        graph,
        calling_agent="deliberator-proponent",
        correlation_id=f"{orders.run_id}:{item.ticker}:defender:r1",
        model="claude-opus-5",
        prompt=live_user,
    ) as call:
        call.set_response('{"ruling": "uphold", "rationale": "x"}')

    stored_hash = str(call.node.props["prompt_hash"])  # type: ignore[union-attr]
    replayed = replayed_prompt_digest(graph, pm_node, orders, item, transcript=())

    assert replayed == stored_hash


def test_replay_writes_nothing_to_the_graph() -> None:
    """DLIB-OBS-01: the derivation is read-only — S160 revision 2 and the invariant.

    The corpus this harness measures cannot be regenerated, so a replay that writes has
    corrupted its own evidence.
    """
    graph = InMemoryGraphStore()
    item = intent()
    orders = order_set(item)
    pm_node = linked_graph(graph, full=True)

    before = {label: len(graph.list_nodes(label)) for label in ("LLMCall", "PMRun")}
    replayed_prompt_digest(graph, pm_node, orders, item, transcript=())
    after = {label: len(graph.list_nodes(label)) for label in ("LLMCall", "PMRun")}

    assert before == after
