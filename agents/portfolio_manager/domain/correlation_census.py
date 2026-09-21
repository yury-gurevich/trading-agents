"""Census of the comparisons behind one correlated-cluster gate outcome.

Agent: portfolio_manager
Role: record and render how many held issuers a correlation gate examined, so a
      cluster of one is distinguishable from a comparison that never happened.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

_TOP_BELOW = 3
_NONE = "none"
_UNMEASURED = "unmeasured"


@dataclass(frozen=True)
class IssuerComparison:
    """One held issuer measured against the candidate ticker."""

    issuer: str
    correlation: float | None
    overlap_bars: int
    contribution: float = 0.0

    def render(self) -> str:
        """Render this comparison as ``ISSUER:correlation``."""
        if self.correlation is None:
            return f"{self.issuer}:{_UNMEASURED}"
        return f"{self.issuer}:{self.correlation:.4f}"


@dataclass(frozen=True)
class SkippedPair:
    """One held issuer pair skipped because overlap was too thin."""

    issuer: str
    overlap_bars: int

    def render(self) -> str:
        """Render this skipped pair as ``ISSUER:overlap``."""
        return f"{self.issuer}:{self.overlap_bars}"


@dataclass(frozen=True)
class CorrelationCensus:
    """Every comparison the correlated-cluster gate performed for one candidate."""

    comparisons: tuple[IssuerComparison, ...]
    threshold: float
    ceiling: float = 0.90
    skipped: tuple[SkippedPair, ...] = ()

    def clustered(self) -> tuple[IssuerComparison, ...]:
        """Return weighted held-issuer comparisons with positive contributions."""
        return self._contributing()

    def all_pairs_unusable(self) -> bool:
        """Return whether every available held pair was below the overlap floor."""
        return not self.comparisons and bool(self.skipped)

    def first_skipped(self) -> SkippedPair | None:
        """Return the first skipped pair by issuer order, if any."""
        return self.skipped[0] if self.skipped else None

    def max_skipped_overlap(self) -> int:
        """Return the widest skipped overlap, or zero when no pair was skipped."""
        return max((item.overlap_bars for item in self.skipped), default=0)

    def detail(self) -> str:
        """Render the census as gate-detail fields."""
        contributing = self._contributing()
        weight_total = sum(item.contribution for item in contributing)
        return "; ".join(
            (
                f"examined_issuers={len(self.comparisons)}",
                f"correlated_issuers={_render_contributing(contributing)}",
                f"below_threshold_top={_render(self._below()[:_TOP_BELOW])}",
                f"correlation_ramp={self.threshold:.4f}..{self.ceiling:.4f}"
                f"{':degenerate' if self.ceiling <= self.threshold else ''}",
                f"cluster_weight_total={weight_total:.4f}",
                f"min_pair_overlap_bars={self._min_overlap()}",
                f"skipped_pairs={len(self.skipped)}",
                f"skipped_pair_issuers={_render_skipped(self.skipped)}",
            )
        )

    def _contributing(self) -> tuple[IssuerComparison, ...]:
        return tuple(
            sorted(
                (item for item in self.comparisons if item.contribution > 0),
                key=lambda item: (-item.contribution, item.issuer),
            )
        )

    def _below(self) -> tuple[IssuerComparison, ...]:
        return self._ranked(item for item in self.comparisons if item.contribution == 0)

    @staticmethod
    def _ranked(items: Iterable[IssuerComparison]) -> tuple[IssuerComparison, ...]:
        return tuple(
            sorted(
                items,
                key=lambda item: (
                    item.correlation is None,
                    -(item.correlation or 0.0),
                    item.issuer,
                ),
            )
        )

    def _min_overlap(self) -> str:
        if not self.comparisons:
            return _NONE
        return str(min(item.overlap_bars for item in self.comparisons))


def _render(items: tuple[IssuerComparison, ...]) -> str:
    return ",".join(item.render() for item in items) if items else _NONE


def _render_contributing(items: tuple[IssuerComparison, ...]) -> str:
    return (
        ",".join(
            f"{item.issuer}:{item.correlation:.4f}:w{item.contribution:.4f}"
            for item in items
        )
        if items
        else _NONE
    )


def _render_skipped(items: tuple[SkippedPair, ...]) -> str:
    return ",".join(item.render() for item in items) if items else _NONE
