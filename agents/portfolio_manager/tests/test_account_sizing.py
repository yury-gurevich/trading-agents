"""Portfolio Manager account-backed sizing tests.

Agent: portfolio_manager
Role: prove PM sizes buys from execution-recorded account equity and holdings.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.graph_portfolio import portfolio_from_graph
from agents.portfolio_manager.tests.account_helpers import position, snapshot
from agents.portfolio_manager.tests.helpers import recommendation
from contracts.common import Money
from kernel import InMemoryGraphStore


def test_pm_sizes_against_snapshot_equity_not_starting_cash() -> None:
    """PM-IDN-01 / PM-NEV-04: snapshot equity, not the starting_cash constant,
    is the sizing base."""
    graph = InMemoryGraphStore()
    snapshot(graph, "r1", equity_cents=500000)

    portfolio = portfolio_from_graph(graph, Decimal("10000.00"), run_id="r1")
    approved, rejected = evaluate_recommendations(
        (recommendation("AAPL"),),
        {"AAPL": Money(amount=Decimal("100.00"))},
        portfolio,
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.00"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
    )

    constant_cash_answer = 10
    assert rejected == ()
    assert approved[0].quantity == 5
    assert approved[0].quantity != constant_cash_answer


def test_2026_08_margin_regression_approves_zero_new_buys() -> None:
    """PM-NEV-04 / PM-OUT-03: 2026-08-06 equity 104,042.69 against
    209,009.46 deployed approves zero new buys."""
    graph = InMemoryGraphStore()
    snapshot(graph, "sched-2026-08-06", equity_cents=10404269)
    position(graph, "held:book", "BOOK", 1, market_value_cents=20900946)
    portfolio = portfolio_from_graph(
        graph, Decimal("100000.00"), run_id="sched-2026-08-06"
    )

    approved, rejected = evaluate_recommendations(
        (recommendation("AAPL"),),
        {"AAPL": Money(amount=Decimal("100.00"))},
        portfolio,
        max_position_pct=Decimal("0.10"),
        max_positions=500,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
    )

    assert approved == ()
    assert [(item.ticker, item.reason) for item in rejected] == [
        ("AAPL", "insufficient_cash")
    ]


def test_leverage_is_impossible_across_repeated_runs() -> None:
    """PM-NEV-04 / PM-STA-01: repeated runs subtract already deployed value;
    the old constant-cash book passes run 1 and fails by run 3."""
    graph = InMemoryGraphStore()
    deployed_cents = 0
    approvals: list[int] = []
    for run_id, ticker in (
        ("run-1", "AAPL"),
        ("run-2", "MSFT"),
        ("run-3", "NVDA"),
    ):
        snapshot(graph, run_id, equity_cents=100000)
        portfolio = portfolio_from_graph(graph, Decimal("1000.00"), run_id=run_id)
        approved, _rejected = evaluate_recommendations(
            (recommendation(ticker),),
            {ticker: Money(amount=Decimal("500.00"))},
            portfolio,
            max_position_pct=Decimal("0.50"),
            max_positions=10,
            cash_buffer_pct=Decimal("0.00"),
            min_order_quantity=1,
            default_stop_pct=0.05,
            default_target_pct=0.10,
            min_reward_risk_ratio=1.5,
        )
        approvals.append(len(approved))
        if approved:
            deployed_cents += 50000
            position(graph, f"held:{ticker}", ticker, 1, market_value_cents=50000)

    assert approvals == [1, 1, 0]
    assert deployed_cents <= 100000


def test_starting_cash_is_only_no_snapshot_bootstrap_seed() -> None:
    """PM-STA-01: starting_cash seeds only a graph with no snapshot; any
    snapshot present prevents the constant from satisfying sizing."""
    graph = InMemoryGraphStore()
    seeded = portfolio_from_graph(graph, Decimal("12345.00"), run_id="no-snapshot")
    assert seeded.value == Decimal("12345.00")

    snapshot(graph, "has-snapshot", equity_cents=500000)
    observed = portfolio_from_graph(graph, Decimal("12345.00"), run_id="has-snapshot")

    assert observed.value == Decimal("5000")
    assert observed.value != Decimal("12345.00")


def test_position_values_fall_back_to_snapshot_holdings_safely() -> None:
    """PM-STA-01 / PM-NEV-04: snapshot holdings fill position value gaps while
    malformed rows are ignored."""
    graph = InMemoryGraphStore()
    graph.merge_node(
        "BrokerPositionSnapshot",
        "snapshot:holdings-run",
        {
            "run_id": "holdings-run",
            "status": "fresh",
            "account_status": "fresh",
            "account_cash_cents": 100000,
            "account_equity_cents": 100000,
            "account_buying_power_cents": 100000,
            "holdings": (
                "not-a-holding",
                {"ticker": "", "market_value_cents": 1},
                {"ticker": "AAPL", "market_value_cents": 25000},
            ),
        },
    )
    graph.merge_node(
        "Position",
        "held:AAPL",
        {
            "ticker": "AAPL",
            "quantity": 2,
            "opened_price_cents": 10000,
            "status": "open",
        },
    )

    portfolio = portfolio_from_graph(graph, Decimal("1000.00"), run_id="holdings-run")

    assert portfolio.position_values["AAPL"].amount == Decimal("250")
