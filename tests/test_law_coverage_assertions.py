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
    # The rollup must already say 1 / 2: a clause with no row still counts
    # against the denominator, it is simply unproven.
    write_book(tmp_path, laws=("PRB-IDN-01", "PRB-IDN-02"), rollup=(1, 2))

    assert main([str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "1 clause(s) have no test-plan row" in output
    assert "PRB-IDN-02" in output


def test_rollup_denominator_is_clauses_never_rows(tmp_path, capsys):
    """A clause with no row must stay in the denominator, not drop out of it.

    Counting rows instead would let an unwritten row shrink the total and make
    coverage read better the less of the constitution was ever considered.
    """
    write_book(
        tmp_path,
        laws=("PRB-IDN-01", "PRB-IDN-02", "PRB-IDN-03"),
        rollup=(1, 1),
    )

    assert main([str(tmp_path)]) == 1
    assert "probe claims 1 / 1; derived 1 / 3" in capsys.readouterr().out


def test_clause_with_two_rows_counts_once(tmp_path, capsys):
    """One clause, two rows: the numerator counts clauses, not green rows."""
    write_book(
        tmp_path,
        rows=(
            ("PRB-IDN-01", "`test_probe.py::test_good`", GREEN),
            ("PRB-IDN-01", "`test_probe.py::test_good`", GREEN),
        ),
        rollup=(2, 2),
    )

    assert main([str(tmp_path)]) == 1
    assert "probe claims 2 / 2; derived 1 / 1" in capsys.readouterr().out


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
