from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

GREEN = "🟩"
GRAY = "⬜"


def write_book(
    root: Path,
    *,
    laws: tuple[str, ...] = ("PRB-IDN-01",),
    rows: tuple[tuple[str, str, str], ...] = (
        ("PRB-IDN-01", "`test_probe.py::test_good`", GREEN),
    ),
    tests: dict[str, str] | None = None,
    schema: str = "five",
    marker: str = "bold",
    rollup: tuple[int, int] | None = None,
    agent: str = "probe",
) -> None:
    law_dir = root / "agents" / agent / "laws"
    test_dir = root / "agents" / agent / "tests"
    law_dir.mkdir(parents=True)
    test_dir.mkdir(parents=True)
    law_dir.joinpath("laws.md").write_text(_laws(laws, marker), encoding="utf-8")
    law_dir.joinpath("test-plan.md").write_text(_plan(rows, schema), encoding="utf-8")
    test_sources = _default_tests() if tests is None else tests
    for name, source in test_sources.items():
        target = test_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(dedent(source).lstrip(), encoding="utf-8")
    _write_rollups(root, agent, rollup or _counter(rows))


def _laws(ids: tuple[str, ...], marker: str) -> str:
    lines = ["# Probe laws", ""]
    for clause_id in ids:
        if marker == "backtick":
            lines.append(f"- `{clause_id}` — The probe does the required thing.")
        else:
            lines.append(f"- **{clause_id}** — The probe does the required thing.")
    return "\n".join(lines) + "\n"


def _plan(rows: tuple[tuple[str, str, str], ...], schema: str) -> str:
    headers = {
        "five": "| Law | What the test must prove | Scenario | Test | Status |",
        "deliberator": "| Clause | Proof obligation | Test type | Test(s) | Status |",
        "three": "| Clause | Status | Test |",
        "master": "| Clause | Description | Test | Status |",
    }
    body = [headers[schema], "| --- | --- | --- | --- | --- |"]
    if schema == "three":
        body = [headers[schema], "| --- | --- | --- |"]
    for clause_id, test, status in rows:
        if schema == "three":
            body.append(f"| {clause_id} | {status} | {test} |")
        elif schema == "master":
            body.append(f"| {clause_id} | summary | {test} | {status} |")
        else:
            body.append(f"| {clause_id} | summary | happy | {test} | {status} |")
    return "\n".join(body) + "\n"


def _default_tests() -> dict[str, str]:
    return {
        "test_probe.py": '''
            def test_good():
                """PRB-IDN-01: proves the clause."""
                assert True
        '''
    }


def _counter(rows: tuple[tuple[str, str, str], ...]) -> tuple[int, int]:
    return sum(status == GREEN for _, _, status in rows), len(rows)


def _write_rollups(root: Path, agent: str, counter: tuple[int, int]) -> None:
    laws_dir = root / "docs" / "laws"
    laws_dir.mkdir(parents=True)
    green, total = counter
    laws_dir.joinpath("ledger.md").write_text(
        "\n".join(
            [
                "| Agent | Laws authored? | Clauses green / total | Status |",
                "| --- | --- | --- | --- |",
                f"| {agent} | yes | {green} / {total} | partial |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    laws_dir.joinpath("INDEX.md").write_text(
        "\n".join(
            [
                "| Agent | `laws.md` | Green clauses | Notes |",
                "| --- | --- | --- | --- |",
                f"| {agent} | locked | {green} / {total} | partial |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
