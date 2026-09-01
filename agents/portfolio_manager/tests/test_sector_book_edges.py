"""SectorBook edge tests.

Agent: portfolio_manager
Role: prove issuer exposure remains correct when one share class exits.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

from agents.portfolio_manager.domain.sector_book import SectorBook
from contracts.common import Money


def test_dual_class_exit_keeps_remaining_issuer_exposure() -> None:
    """PM-NEV-07: exiting one share class does not remove the issuer."""
    book = SectorBook(
        {"GOOG": "Media", "GOOGL": "Media"},
        ("GOOG", "GOOGL"),
        held_values={
            "GOOG": Money(amount=Decimal("400.00")),
            "GOOGL": Money(amount=Decimal("600.00")),
        },
        issuer_map={"GOOG": "alphabet", "GOOGL": "alphabet"},
    )

    book.record_exit("GOOG")

    assert book.issuer_value("alphabet") == Decimal("600.00")
    assert book.issuer_tickers() == {"alphabet": ("GOOGL",)}
