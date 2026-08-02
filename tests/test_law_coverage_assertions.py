from __future__ import annotations

from textwrap import dedent

from scripts.check_law_coverage import main
from tests.law_coverage_fixtures import GRAY, GREEN, write_book


def test_clean_book_passes(tmp_path, capsys):
    write_book(tmp_path)

    assert main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


def test_dead_citation_is_caught(tmp_path, capsys):
    write_book(tmp_path, rows=(("PRB-IDN-01", "`test_gone`", GREEN),))

    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "PRB-IDN-01" in output
    assert "test_gone" in output
    assert "no live test" in output


def test_uncited_docstring_is_caught(tmp_path, capsys):
    write_book(
        tmp_path,
        tests={
            "test_probe.py": '''
                def test_good():
                    """A docstring that does not name the law."""
                    assert True
            '''
        },
    )

    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "PRB-IDN-01" in output
    assert "test_good" in output
    assert "docstring" in output


def test_comment_is_not_a_citation(tmp_path, capsys):
    write_book(
        tmp_path,
        tests={
            "test_probe.py": '''
                def test_good():
                    """A docstring that still omits the clause."""
                    # PRB-IDN-01 appears only in a comment.
                    assert True
            '''
        },
    )

    assert main([str(tmp_path)]) == 1
    assert "PRB-IDN-01" in capsys.readouterr().out


def test_gray_rows_are_not_checked(tmp_path, capsys):
    write_book(tmp_path, rows=(("PRB-IDN-01", "`test_gone`", GRAY),))

    assert main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


def test_ambiguous_bare_name_fails(tmp_path, capsys):
    write_book(
        tmp_path,
        rows=(("PRB-IDN-01", "`test_shared`", GREEN),),
        tests={
            "test_one.py": '''
                def test_shared():
                    """PRB-IDN-01: first proof."""
                    assert True
            ''',
            "nested/test_two.py": '''
                def test_shared():
                    """PRB-IDN-01: second proof."""
                    assert True
            ''',
        },
    )

    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "ambiguous citation" in output
    assert "test_one.py" in output
    assert "nested/test_two.py" in output


def test_orphan_row_is_caught(tmp_path, capsys):
    write_book(tmp_path, rows=(("PRB-IDN-99", "`test_good`", GREEN),))

    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "PRB-IDN-99" in output
    assert "orphan row" in output


def test_rollup_drift_is_caught(tmp_path, capsys):
    write_book(tmp_path, rollup=(5, 1))

    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "docs/laws/ledger.md" in output
    assert "probe claims 5 / 1; derived 1 / 1" in output


def test_missing_row_warns_without_failing(tmp_path, capsys):
    write_book(tmp_path, laws=("PRB-IDN-01", "PRB-IDN-02"))

    assert main([str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "1 clause(s) have no test-plan row" in output
    assert "PRB-IDN-02" in output


def test_mutants_snapshot_is_ignored(tmp_path, capsys):
    write_book(tmp_path, tests={})
    mutant_test = tmp_path / "mutants" / "agents" / "probe" / "tests" / "test_probe.py"
    mutant_test.parent.mkdir(parents=True)
    mutant_test.write_text(
        dedent(
            '''
            def test_good():
                """PRB-IDN-01: only the snapshot cites this."""
                assert True
            '''
        ).lstrip(),
        encoding="utf-8",
    )

    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "PRB-IDN-01" in output
    assert "no live test" in output
