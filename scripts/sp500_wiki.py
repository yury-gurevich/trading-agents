"""Fetch and parse Wikipedia S&P 500 membership source pages.

Agent: tooling
Role: turn the current constituents and historical changes tables into typed rows.
External I/O: Wikipedia HTTP reads when fetch helpers are used.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from html.parser import HTMLParser
from typing import Any

import requests

CONSTITUENTS_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
CHANGES_URL = "https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500"
USER_AGENT = "trading-agents replay-universe builder; contact: local operator"
HTTP_TIMEOUT_SECONDS = 60
EXPECTED_CHANGE_CELLS = {6, 7}


@dataclass(frozen=True)
class Constituent:
    symbol: str
    security: str
    date_added: date | None
    cik: str


@dataclass(frozen=True)
class Change:
    date: date
    added: str | None
    added_security: str | None
    removed: str | None
    removed_security: str | None
    reason: str


@dataclass(frozen=True)
class WikiPage:
    revision_id: str
    rows: tuple[Any, ...]


@dataclass(frozen=True)
class _Row:
    tags: tuple[str, ...]
    cells: tuple[str, ...]


class _TableParser(HTMLParser):
    def __init__(self, table_id: str) -> None:
        super().__init__(convert_charrefs=True)
        self._table_id = table_id
        self._in_table = False
        self._depth = 0
        self._row_tags: list[str] | None = None
        self._row_cells: list[str] | None = None
        self._cell_tag: str | None = None
        self._cell_text: list[str] = []
        self.rows: list[_Row] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "table" and attrs_dict.get("id") == self._table_id:
            self._in_table = True
            self._depth = 1
            return
        if not self._in_table:
            return
        if tag == "table":
            self._depth += 1
        elif tag == "tr":
            self._row_tags, self._row_cells = [], []
        elif tag in {"td", "th"} and self._row_cells is not None:
            self._cell_tag = tag
            self._cell_text = []

    def handle_data(self, data: str) -> None:
        if self._cell_tag is not None:
            self._cell_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self._in_table:
            return
        if tag in {"td", "th"} and tag == self._cell_tag:
            if self._row_tags is None or self._row_cells is None:
                return
            text = re.sub(r"\s+", " ", "".join(self._cell_text)).strip()
            self._row_tags.append(tag)
            self._row_cells.append(text)
            self._cell_tag = None
        elif tag == "tr" and self._row_cells is not None:
            self.rows.append(_Row(tuple(self._row_tags or ()), tuple(self._row_cells)))
            self._row_tags = self._row_cells = None
        elif tag == "table":
            self._depth -= 1
            if self._depth == 0:
                self._in_table = False


def fetch_page(url: str, timeout: int = HTTP_TIMEOUT_SECONDS) -> str:
    """Fetch a Wikipedia page with a descriptive user agent."""
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    response.raise_for_status()
    return response.text


def fetch_source_pages() -> dict[str, str]:
    """Fetch the two Wikipedia pages needed by the universe builder."""
    return {
        "constituents": fetch_page(CONSTITUENTS_URL),
        "changes": fetch_page(CHANGES_URL),
    }


def parse_constituents_page(html: str) -> WikiPage:
    rows = _table_rows(html, "constituents")
    constituents: list[Constituent] = []
    for row in rows:
        if "th" in row.tags or not row.cells:
            continue
        cells = list(row.cells)
        if len(cells) < 7:
            continue
        constituents.append(
            Constituent(
                symbol=_clean_ticker(cells[0]) or "",
                security=cells[1],
                date_added=_parse_optional_date(cells[5]),
                cik=cells[6],
            )
        )
    return WikiPage(_revision_id(html), tuple(constituents))


def parse_changes_page(html: str) -> WikiPage:
    rows = _table_rows(html, "changes")
    changes: list[Change] = []
    for row in rows:
        if "th" in row.tags or len(row.cells) not in EXPECTED_CHANGE_CELLS:
            continue
        cells = list(row.cells)
        changes.append(
            Change(
                date=_parse_date(cells[0]),
                added=_clean_ticker(cells[1]),
                added_security=_clean_optional(cells[2]),
                removed=_clean_ticker(cells[3]),
                removed_security=_clean_optional(cells[4]),
                reason=cells[5],
            )
        )
    return WikiPage(_revision_id(html), tuple(changes))


def _table_rows(html: str, table_id: str) -> tuple[_Row, ...]:
    parser = _TableParser(table_id)
    parser.feed(html)
    if not parser.rows:
        message = f"table id={table_id!r} not found"
        raise ValueError(message)
    return tuple(parser.rows)


def _revision_id(html: str) -> str:
    match = re.search(r"wgRevisionId[^0-9]*(\d+)", html)
    if match is None:
        raise ValueError("wgRevisionId not found")
    return match.group(1)


def _parse_optional_date(value: str) -> date | None:
    value = value.strip()
    return _parse_date(value) if value else None


def _parse_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%B %d, %Y").replace(tzinfo=UTC).date()


def _clean_optional(value: str) -> str | None:
    value = value.strip()
    return value or None


def _clean_ticker(value: str) -> str | None:
    value = value.strip()
    if value.endswith("|"):
        value = value[:-1].strip()
    return value or None
