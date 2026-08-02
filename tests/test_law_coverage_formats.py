from __future__ import annotations

import pytest
from scripts.check_law_coverage import main
from tests.law_coverage_fixtures import GREEN, write_book


@pytest.mark.parametrize("schema", ["five", "deliberator", "three", "master"])
def test_all_table_schemas_parse(tmp_path, capsys, schema):
    write_book(tmp_path, schema=schema)

    assert main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


def test_backtick_clause_markers_parse(tmp_path, capsys):
    write_book(tmp_path, marker="backtick")

    assert main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


def test_file_and_bare_citations_both_resolve(tmp_path, capsys):
    write_book(
        tmp_path,
        laws=("PRB-IDN-01", "PRB-IDN-02"),
        rows=(
            ("PRB-IDN-01", "`test_probe.py::test_file_citation`", GREEN),
            ("PRB-IDN-02", "`test_bare_citation`", GREEN),
        ),
        tests={
            "test_probe.py": '''
                def test_file_citation():
                    """PRB-IDN-01: cited with an explicit file."""
                    assert True

                def test_bare_citation():
                    """PRB-IDN-02: cited by bare name."""
                    assert True
            '''
        },
    )

    assert main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""
