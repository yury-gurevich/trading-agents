"""Every bound DLIB-IDM-02 names is actually recorded and queryable.

Agent: deliberator
Role: prove the clause's full list -- role, model, max rounds, prompt hashes,
      response hashes, timestamps -- is stamped on a real deliberation, not just
      the half S200 repaired.
External I/O: none; in-memory graph and a deterministic fake LLM.

🪤 This file exists because [DRIFT-056](../../../docs/laws/drift-register.md) said
plainly: *"Do not close it by citing a test that only exercises the user half."*
S200 makes the system prompt hashed, which removes the measured gap -- but the
clause promises six bounds across two node types, so proving one of them is not
proving the clause. Asserting all six is what turns `DLIB-IDM-02` from measured
to proven.
"""

from __future__ import annotations

from decimal import Decimal

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.poll import review_pm_node
from agents.deliberator.settings import DeliberatorSettings
from contracts.common import Explanation, Money, Provenance
from contracts.deliberator import DebateTurnRecord, DebateTurnReply, DebateTurnRequest
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus
from kernel.llm_tokens import SOURCE_ESTIMATED
from kernel.prompt_recipe import RECIPE_UNKNOWN

_UPHOLD = '{"ruling": "uphold", "rationale": "clears review"}'


class _EchoPeer:
    """A peer that answers every turn, so a full transcript is produced."""

    def preflight(self, recipients: tuple[str, ...]) -> None:
        del recipients

    def debate_turn(
        self, recipient: str, request: DebateTurnRequest
    ) -> DebateTurnReply:
        del recipient
        return DebateTurnReply(
            request_id=request.request_id,
            turn=DebateTurnRecord(
                role=request.role,
                round=request.round_number,
                text=f"{request.role} argues in round {request.round_number}",
            ),
        )


def _intent() -> OrderIntent:
    return OrderIntent(
        ticker="USB",
        action="buy",
        quantity=10,
        est_price=Money(amount=Decimal("100.00")),
        rationale=Explanation(summary="sized under the cap"),
    )


def _run() -> tuple[InMemoryGraphStore, DeliberatorSettings]:
    graph = InMemoryGraphStore()
    order_set = OrderIntentSet(
        run_id="pm-bounds",
        approved=(_intent(),),
        rejected=(),
        explanation=Explanation(summary="sized"),
        provenance=Provenance(run_id="pm-bounds", source_agent="portfolio_manager"),
    )
    node = graph.merge_node(
        "PMRun", "pm-bounds", {"order_intent_set": order_set.model_dump(mode="json")}
    )
    settings = DeliberatorSettings(role="manager", max_rounds=2)
    manager = DeliberatorAgent(
        InProcessBus(),
        graph=graph,
        llm=FakeLLMClient({"": _UPHOLD}),
        settings=settings,
    )
    review_pm_node(
        node,
        graph=graph,
        manager=manager,
        peer_client=_EchoPeer(),
        settings=settings,
    )
    return graph, settings


def test_every_bound_the_clause_names_is_stamped() -> None:
    """DLIB-IDM-02: role, model, max rounds, prompt + response hashes, timestamps."""
    graph, settings = _run()

    run = graph.get_node("DeliberationRun", "pm-bounds")
    assert run is not None
    # role and max rounds -- the shape of the debate that produced the output
    assert run.props["max_rounds"] == 2
    assert set(run.props["role_models"]) == {"defender", "challenger", "judge"}

    calls = [
        node
        for node in graph.list_nodes("LLMCall")
        if node.props["calling_agent"] == settings.identity
    ]
    assert calls, "the judge call must reach the ledger"
    for call in calls:
        # model, both prompt halves, the response, and when it happened
        assert call.props["model"] == settings.model_for_role("judge")
        assert len(str(call.props["prompt_hash"])) == 64
        assert len(str(call.props["system_prompt_hash"])) == 64
        assert len(str(call.props["response_hash"])) == 64
        assert str(call.props["created_at"]).startswith("20")


def test_the_bound_names_the_renderer_that_produced_it() -> None:
    """DLIB-OBS-07: the recorded hashes are attributable to a specific renderer.

    Without this the hashes bound the *output* but not the *question* -- two rows
    could disagree because the model wandered or because the prompt builder had
    changed, and nothing distinguished the two. Re-measured 2026-09-13: 62 of 285
    stored turns replay, so that ambiguity covered ~78 % of the corpus.
    """
    graph, settings = _run()

    calls = [
        node
        for node in graph.list_nodes("LLMCall")
        if node.props["calling_agent"] == settings.identity
    ]
    for call in calls:
        recipe = str(call.props["prompt_recipe_hash"])
        assert recipe != RECIPE_UNKNOWN
        assert len(recipe) == 64


def test_a_deterministic_fake_still_records_honest_provenance() -> None:
    """🪤 The fake LLM reports no usage, and that must not blur the recipe.

    Token provenance and prompt provenance are independent: CI's fake provider
    legitimately yields `token_source=estimated`, while the renderer is known
    exactly. A row that conflated them would make every CI-shaped row look like
    it came from an unknown renderer.
    """
    graph, settings = _run()

    call = next(
        node
        for node in graph.list_nodes("LLMCall")
        if node.props["calling_agent"] == settings.identity
    )
    assert call.props["token_source"] == SOURCE_ESTIMATED
    assert call.props["prompt_recipe_hash"] != RECIPE_UNKNOWN
