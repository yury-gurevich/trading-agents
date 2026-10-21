"""Literal book and odds wording, totals, limits and empty cases.

Agent: orchestration
Role: prove A6-A9 without using production arithmetic as the expected result.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from kernel import InMemoryGraphStore
from orchestration.tests.book_fixtures import BOOK_LINES, DAY, claim, lot, seed_book


def test_the_book_line_totals_the_names_past_their_target() -> None:
    """DSP-OUT-10: literal gains now, above target and at stops, U+2212 minus."""
    from orchestration.book_brief import book_lines
    from orchestration.book_odds import book_odds

    graph = InMemoryGraphStore()
    seed_book(graph)

    assert book_lines(book_odds(graph, DAY)) == BOOK_LINES


def test_the_odds_line_sums_the_claims_and_names_the_likelier_to_stop() -> None:
    """DSP-OUT-10: strict leaning, descending chance, ticker ties and name caps."""
    from orchestration.book_brief import book_lines
    from orchestration.book_odds import book_odds

    graph = InMemoryGraphStore()
    for ticker, p_stop in (
        ("TGT", 0.61),
        ("NVDA", 0.57),
        ("AMD", 0.57),
        ("TXN", 0.35),
        ("CAT", 0.28),
    ):
        lot(graph, ticker, 1, 10000)
        claim(graph, ticker, probabilities=(p_stop, 0.1, 0.9 - p_stop))
    lot(graph, "KO", 1, 10000)
    claim(graph, "KO", probabilities=(0.2, 0.2, 0.6))
    for ticker in ("PM", "UNH", "ABT", "BA", "WFC"):
        lot(graph, ticker, 1, 10000)

    lines = book_lines(book_odds(graph, DAY))

    assert lines[1] == (
        "Odds, next 10 sessions, 6 names (not yet scored): "
        "target first 0.7 · stop first 2.6 · neither 2.7 · "
        "likelier to stop: TGT 61 %, AMD 57 %, NVDA 57 % and 2 more · "
        "no forecast: ABT, BA, PM, UNH and 1 more"
    )


def test_a_book_with_no_claim_says_so_in_one_line() -> None:
    """DSP-OUT-10: another session is no forecast; no book gives no lines."""
    from orchestration.book_brief import book_lines
    from orchestration.book_odds import book_odds

    graph = InMemoryGraphStore()
    lot(graph, "KO", 10, 8692)
    lot(graph, "PM", 2, 18000)
    claim(graph, "KO", day=date(2026, 10, 17))

    assert book_lines(book_odds(graph, DAY)) == (
        "Book: 2 held · no forecast for 2026-10-20",
    )
    assert book_lines(None) == ()


def test_no_name_past_its_target_reads_none() -> None:
    """DSP-OUT-10: declared basis means none past target, with zero stop odds."""
    from orchestration.book_brief import book_lines
    from orchestration.book_odds import book_odds

    graph = InMemoryGraphStore()
    lot(graph, "KO", 10, 8692)
    claim(
        graph,
        "KO",
        prices=(93.49, 82.57, 95.612),
        probabilities=(0.0, 0.5, 0.5),
    )

    lines = book_lines(book_odds(graph, DAY))

    assert lines[0] == "Book: 1 held · none past its target"
    assert lines[1].endswith("target first 0.5 · stop first 0.0 · neither 0.5")
