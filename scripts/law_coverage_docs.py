"""Parse law-book Markdown for the coverage checker.

Agent: tooling
Role: recover clause IDs, test-plan rows, and roll-up counters from Markdown.
External I/O: filesystem reads of law and roll-up documents.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from scripts.law_coverage_model import AgentBook, RollupClaim, TestPlanRow

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

CLAUSE_ID_RE = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+-\d{2}\b")
COUNTER_RE = re.compile(r"(?P<green>\d+)\s*/\s*(?P<total>\d+)")


def discover_agent_books(root: Path) -> tuple[AgentBook, ...]:
    """Parse every agent law/test-plan pair under ``root``."""
    books: list[AgentBook] = []
    for laws_path in sorted((root / "agents").glob("*/laws/laws.md")):
        agent = laws_path.parents[1].name
        plan_path = laws_path.with_name("test-plan.md")
        books.append(
            AgentBook(
                agent=agent,
                laws_path=laws_path,
                plan_path=plan_path,
                law_ids=frozenset(parse_law_ids(laws_path)),
                rows=tuple(parse_test_plan(agent, plan_path)),
            )
        )
    return tuple(books)


def parse_law_ids(path: Path) -> set[str]:
    """Return the clause IDs declared in a locked ``laws.md`` file."""
    if not path.is_file():
        return set()
    text = path.read_text(encoding="utf-8")
    return set(CLAUSE_ID_RE.findall(text))


def parse_test_plan(agent: str, path: Path) -> list[TestPlanRow]:
    """Return law rows from any supported test-plan table schema."""
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: list[TestPlanRow] = []
    for _, header, body in _iter_tables(lines):
        indexes = _plan_indexes(header)
        if indexes is None:
            continue
        id_index, test_index, status_index = indexes
        for line_index, cells in body:
            if len(cells) <= max(indexes):
                continue
            match = CLAUSE_ID_RE.search(cells[id_index])
            if match is None:
                continue
            rows.append(
                TestPlanRow(
                    agent=agent,
                    path=path,
                    line_number=line_index,
                    clause_id=match.group(0),
                    test_text=cells[test_index],
                    green="🟩" in cells[status_index],
                )
            )
    return rows


def parse_rollup_claims(path: Path) -> dict[str, RollupClaim]:
    """Return per-agent green/total claims from ``ledger.md`` or ``INDEX.md``."""
    if not path.is_file():
        return {}
    lines = path.read_text(encoding="utf-8").splitlines()
    claims: dict[str, RollupClaim] = {}
    for _, header, body in _iter_tables(lines):
        agent_index = _agent_index(header)
        if agent_index is None:
            continue
        for line_index, cells in body:
            if len(cells) <= agent_index:
                continue
            agent = _plain(cells[agent_index])
            counter = _first_counter(cells)
            if agent and counter is not None:
                green, total = counter
                claims[agent] = RollupClaim(path, line_index, green, total)
    return claims


def _iter_tables(
    lines: list[str],
) -> Iterator[tuple[int, list[str], list[tuple[int, list[str]]]]]:
    index = 0
    while index < len(lines) - 1:
        if not _is_table_line(lines[index]) or not _is_separator(lines[index + 1]):
            index += 1
            continue
        header = _split_row(lines[index])
        body: list[tuple[int, list[str]]] = []
        index += 2
        while index < len(lines) and _is_table_line(lines[index]):
            if not _is_separator(lines[index]):
                body.append((index + 1, _split_row(lines[index])))
            index += 1
        yield index, header, body


def _plan_indexes(header: list[str]) -> tuple[int, int, int] | None:
    normalized = [_normalize(value) for value in header]
    id_index = _first_index(normalized, {"law", "clause"})
    status_index = _first_index(normalized, {"status"})
    test_index = _first_index(normalized, {"test", "tests"})
    if test_index is None:
        test_index = next(
            (
                index
                for index, value in enumerate(normalized)
                if value.startswith("test")
            ),
            None,
        )
    if id_index is None or test_index is None or status_index is None:
        return None
    return id_index, test_index, status_index


def _agent_index(header: list[str]) -> int | None:
    normalized = [_normalize(value) for value in header]
    return _first_index(normalized, {"agent"})


def _first_index(values: list[str], targets: set[str]) -> int | None:
    return next((index for index, value in enumerate(values) if value in targets), None)


def _first_counter(cells: list[str]) -> tuple[int, int] | None:
    for cell in cells:
        match = COUNTER_RE.search(cell)
        if match is not None:
            return int(match.group("green")), int(match.group("total"))
    return None


def _is_table_line(line: str) -> bool:
    return line.lstrip().startswith("|") and line.rstrip().endswith("|")


def _is_separator(line: str) -> bool:
    if not _is_table_line(line):
        return False
    cells = _split_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z]", "", value.lower())


def _plain(value: str) -> str:
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    return value.replace("`", "").replace("*", "").strip()
