"""The book's odds: each held name, its stop and target, and what its forecast says.

Agent: orchestration
Role: join the book (the active Positions, by ticker) to the forecaster's held claim
      for one session (`barrier-garch-v1:held:{ticker}:{as_of}`, DL-310) and total
      what the brief and the dashboard say of it (DL-311): the names past their
      declared target, their gain, the part above the target and the drop to their
      stops; how many names the forecast expects to reach target first, stop first
      or neither; the names leaning to their stop; the names with no claim.
External I/O: reads the injected GraphStore (Position listed once, then one claim
      read by key per held name); never writes.

Every figure is a stored one or a sum of them: a claim's close, stop and target are
the forecaster's, a name's quantity and entry its Positions'.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, cast

from contracts.positions import active_position_nodes

if TYPE_CHECKING:
    from datetime import date

    from kernel import GraphStore, Node

#: The forecaster's label and held-claim key prefix (agents/forecaster/barrier_store),
#: named here so the dispatcher job loads no forecaster code; a test pins them equal.
BARRIER_LABEL: Final = "BarrierForecast"
HELD_CLAIM_PREFIX: Final = "barrier-garch-v1:held:"
#: A held claim's `target_basis` once its close is at or past the declared target.
PASSED_BASIS: Final = "rebased"
_FIGURES = (
    "entry_close",
    "stop_price",
    "target_price",
    "p_stop_first",
    "p_target_first",
    "p_neither",
    "horizon_sessions",
)


@dataclass(frozen=True)
class HeldClaim:
    """What the session's held claim says of one name, in cents and probabilities."""

    close_cents: int
    stop_cents: int
    target_cents: int
    passed: bool
    p_stop: float
    p_target: float
    p_neither: float
    horizon_sessions: int


@dataclass(frozen=True)
class HeldName:
    """One held ticker: its lots summed, and its claim when the session has one."""

    ticker: str
    quantity: int
    cost_cents: int
    claim: HeldClaim | None

    def gain_cents(self, claim: HeldClaim) -> int:
        """The unrealised gain at the claim's close."""
        return self.quantity * claim.close_cents - self.cost_cents

    def above_target_cents(self, claim: HeldClaim) -> int:
        """How far the close is above the declared target, for the whole holding."""
        return self.quantity * (claim.close_cents - claim.target_cents)

    def to_stop_cents(self, claim: HeldClaim) -> int:
        """What the holding gives back from the close if it falls to its stop."""
        return self.quantity * (claim.close_cents - claim.stop_cents)


@dataclass(frozen=True)
class BookOdds:
    """The book on one session, as its held claims read it."""

    as_of: date
    names: tuple[HeldName, ...]

    @property
    def forecast(self) -> tuple[tuple[HeldName, HeldClaim], ...]:
        """Each name the session's claims cover, with its claim."""
        return tuple((n, n.claim) for n in self.names if n.claim is not None)

    @property
    def passed(self) -> tuple[tuple[HeldName, HeldClaim], ...]:
        """The covered names whose close is at or past their declared target."""
        return tuple((n, c) for n, c in self.forecast if c.passed)

    @property
    def unforecast(self) -> tuple[str, ...]:
        """The held names the session has no readable claim for."""
        return tuple(n.ticker for n in self.names if n.claim is None)

    @property
    def leaning_to_stop(self) -> tuple[tuple[str, float], ...]:
        """Names likelier to hit their stop first than their target, likeliest first."""
        leaning = [
            (n.ticker, c.p_stop) for n, c in self.forecast if c.p_stop > c.p_target
        ]
        return tuple(sorted(leaning, key=lambda item: (-item[1], item[0])))

    @property
    def horizons(self) -> tuple[int, ...]:
        """The claims' horizons in sessions, each once (the model has one: 10)."""
        return tuple(sorted({c.horizon_sessions for _, c in self.forecast}))

    def expected(self) -> tuple[float, float, float]:
        """How many names the claims expect at target first, stop first, neither."""
        claims = [c for _, c in self.forecast]
        return (
            sum(c.p_target for c in claims),
            sum(c.p_stop for c in claims),
            sum(c.p_neither for c in claims),
        )


def book_odds(graph: GraphStore, as_of: date) -> BookOdds | None:
    """The book on ``as_of`` with each name's held claim; None when nothing is held."""
    lots: dict[str, list[int]] = {}
    for node in active_position_nodes(graph):
        quantity = int(node.props["quantity"])
        held = lots.setdefault(str(node.props["ticker"]), [0, 0])
        held[0] += quantity
        held[1] += quantity * int(node.props["opened_price_cents"])
    if not lots:
        return None
    day = as_of.isoformat()
    names = tuple(
        HeldName(
            ticker,
            quantity,
            cost,
            _claim(graph.get_node(BARRIER_LABEL, f"{HELD_CLAIM_PREFIX}{ticker}:{day}")),
        )
        for ticker, (quantity, cost) in sorted(lots.items())
    )
    return BookOdds(as_of, names)


def _claim(node: Node | None) -> HeldClaim | None:
    """The claim's figures; None when there is no claim or a figure is not a number."""
    if node is None:
        return None
    values = [node.props.get(name) for name in _FIGURES]
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
        return None
    close, stop, target, p_stop, p_target, p_neither, horizon = (
        float(cast("float", v)) for v in values
    )
    return HeldClaim(
        close_cents=round(close * 100),
        stop_cents=round(stop * 100),
        target_cents=round(target * 100),
        passed=node.props.get("target_basis") == PASSED_BASIS,
        p_stop=p_stop,
        p_target=p_target,
        p_neither=p_neither,
        horizon_sessions=int(horizon),
    )
