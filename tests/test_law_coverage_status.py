from __future__ import annotations

from scripts.check_law_coverage import main
from tests.law_coverage_fixtures import CHARTER, STRUCTURAL, write_book


def test_structural_row_requires_named_gate(tmp_path, capsys):
    write_book(
        tmp_path,
        rows=(("PRB-IDN-01", "_tbd_", STRUCTURAL),),
        rollup=(0, 1),
    )

    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "PRB-IDN-01" in output
    assert "structural row names no gate" in output


def test_structural_row_accepts_named_gate(tmp_path, capsys):
    write_book(
        tmp_path,
        rows=(
            (
                "PRB-IDN-01",
                "dependencies.md DEP-BUS-* + probes/checks.py",
                STRUCTURAL,
            ),
        ),
        rollup=(0, 1),
    )

    assert main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


def test_charter_row_requires_reason(tmp_path, capsys):
    write_book(tmp_path, rows=(("PRB-IDN-01", "_tbd_", CHARTER),), rollup=(0, 1))

    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "PRB-IDN-01" in output
    assert "charter row states no unfalsifiable reason" in output


def test_charter_row_accepts_reason(tmp_path, capsys):
    write_book(
        tmp_path,
        rows=(
            (
                "PRB-IDN-01",
                "Charter: no single observation can prove the mission statement.",
                CHARTER,
            ),
        ),
        rollup=(0, 1),
    )

    assert main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""
