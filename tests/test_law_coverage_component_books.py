from __future__ import annotations

from scripts.check_law_coverage import main
from scripts.law_coverage_docs import discover_agent_books
from tests.law_coverage_fixtures import GREEN, write_book, write_component_book


def test_non_agent_book_uncited_green_row_is_caught(tmp_path, capsys):
    write_component_book(
        tmp_path,
        rows=(
            (
                "DSP-IDN-01",
                "`orchestration/tests/test_dispatcher.py::test_good`",
                GREEN,
            ),
        ),
        tests={
            "orchestration/tests/test_dispatcher.py": '''
                def test_good():
                    """This docstring deliberately omits the dispatcher law."""
                    assert True
            '''
        },
    )

    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "DSP-IDN-01" in output
    assert "docstring" in output


def test_non_agent_book_orphan_row_is_caught(tmp_path, capsys):
    write_component_book(
        tmp_path,
        laws=("DSP-IDN-01",),
        rows=(
            (
                "DSP-IDN-99",
                "`orchestration/tests/test_dispatcher.py::test_good`",
                GREEN,
            ),
        ),
    )

    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "DSP-IDN-99" in output
    assert "orphan row" in output


def test_non_agent_book_missing_row_fails(tmp_path, capsys):
    write_component_book(
        tmp_path,
        laws=("DSP-IDN-01", "DSP-IDN-02"),
        rollup=(1, 2),
    )

    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "DSP-IDN-02" in output
    assert "missing row" in output


def test_discovery_uses_declared_component_roots_only(tmp_path):
    write_book(tmp_path, agent="probe")
    write_component_book(tmp_path, component="dispatcher")
    write_component_book(
        tmp_path,
        component="surfaces",
        law_root="surfaces",
        laws=("SRF-IDN-01",),
        rows=(
            (
                "SRF-IDN-01",
                "`surfaces/tests/test_surface.py::test_good`",
                GREEN,
            ),
        ),
        tests={
            "surfaces/tests/test_surface.py": '''
                def test_good():
                    """SRF-IDN-01: proves the surfaces clause."""
                    assert True
            '''
        },
    )
    (tmp_path / "ops" / "laws").mkdir(parents=True)
    (tmp_path / "ops" / "laws" / "laws.md").write_text(
        "- **OPS-IDN-01** - process law\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "laws" / "laws.md").write_text(
        "- **DOC-IDN-01** - umbrella law\n", encoding="utf-8"
    )

    discovered = tuple(book.agent for book in discover_agent_books(tmp_path))

    assert discovered == ("probe", "dispatcher", "surfaces")
