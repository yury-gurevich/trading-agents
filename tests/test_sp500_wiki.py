"""Tests for parsing S231's Wikipedia source pages.

Agent: tooling
Role: verify synthetic Wikipedia-shaped tables become typed replay inputs.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from tests.sp500_fixtures import changes_table_fixture, constituents_table_fixture


def test_changes_table_parses_measured_structure() -> None:
    """S231-A1: changes rows parse by id, skip two headers, and normalize tickers."""
    from scripts.sp500_wiki import parse_changes_page

    page = parse_changes_page(changes_table_fixture())

    assert page.revision_id == "987654321"
    assert len(page.rows) == 2
    assert page.rows[0].date == date(2020, 1, 5)
    assert page.rows[0].added == "ABC"
    assert page.rows[0].removed is None
    assert page.rows[1].date == date(2020, 1, 6)
    assert page.rows[1].added is None
    assert page.rows[1].removed == "DEF"


def test_constituents_table_parses_by_id_and_keeps_dots() -> None:
    """S231-A2: constituents table id is selected and dotted tickers stay intact."""
    from scripts.sp500_wiki import parse_constituents_page

    page = parse_constituents_page(constituents_table_fixture())

    assert page.revision_id == "123456789"
    assert [row.symbol for row in page.rows] == ["BRK.B"]
    assert page.rows[0].security == "Berkshire Example"
    assert page.rows[0].date_added == date(2010, 2, 16)
    assert page.rows[0].cik == "0001067983"
