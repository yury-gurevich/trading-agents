"""DL-276 Type-cell comparisons against the complete enforced bounds set.

Agent: tooling
Role: prove each book notation, strictness and both sides of a rail are checked.
External I/O: temporary filesystem writes and checker reads.
"""

import pytest
from scripts.check_param_law_sync import main
from tests.param_law_sync_helpers import write_book


@pytest.mark.parametrize(
    ("type_cell", "bounds"),
    [
        ("`float ≥ 0, ≤ 1` (ratio)", ", ge=0, le=1"),
        ("float >= 0, <= 1 seconds", ", ge=0, le=1"),
        ("`float > 0, < 1`", ", gt=0, lt=1"),
        ("`float [0, 1]`", ", ge=0, le=1"),
        ("`float ∈ (0, 1]`", ", gt=0, le=1"),
        ("`float [0, 1)`", ", ge=0, lt=1"),
        ("`float (0, 1)`", ", gt=0, lt=1"),
    ],
)
def test_every_bound_notation_compares_numbers(tmp_path, capsys, type_cell, bounds):
    """DL-276 A4: every rail notation passes, and a changed upper number fails."""
    write_book(
        tmp_path,
        default="0.5",
        value="`0.5`",
        annotation="float",
        bounds=bounds,
        type_cell=type_cell,
    )
    assert main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""
    write_book(
        tmp_path,
        default="0.5",
        value="`0.5`",
        annotation="float",
        bounds=bounds,
        type_cell=type_cell.replace("1", "2"),
    )
    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "probe.limit" in output
    assert "2" in output
    assert "1" in output


def test_exclusive_lower_bound_is_not_inclusive(tmp_path, capsys):
    """DL-276 A4: (0, 1] cannot describe a field that permits zero."""
    write_book(
        tmp_path,
        default="0.5",
        value="`0.5`",
        annotation="float",
        bounds=", ge=0, le=1",
        type_cell="`float ∈ (0, 1]`",
    )
    assert main([str(tmp_path)]) == 1
    assert "probe.limit" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("bounds", "type_cell"),
    [
        (", ge=0, le=10", "`int ≥ 0`"),
        (", ge=0, le=10", "`int`"),
        ("", "`int ≥ 0`"),
    ],
)
def test_missing_or_extra_bounds_fail(tmp_path, capsys, bounds, type_cell):
    """DL-276 A5: a missing side, a missing rail and an invented rail fail."""
    write_book(tmp_path, bounds=bounds, type_cell=type_cell)
    assert main([str(tmp_path)]) == 1
    assert "probe.limit" in capsys.readouterr().out


def test_no_bounds_on_either_side_passes(tmp_path, capsys):
    """DL-276 A5: a genuinely unbounded field has no missing side."""
    write_book(tmp_path)
    assert main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    ("bounds", "type_cell"),
    [
        (", ge=1, le=60", "int days [1, 60]"),
        (", ge=1, le=1000000000.0", "`int ≥ 1, ≤ 1e9` (shares/day)"),
        (", ge=1, le=1000000", "`int >= 1, <= 1,000,000`"),
        (", ge=1, le=1000000", "`int [1, 1_000_000]`"),
    ],
)
def test_units_and_grouped_decimal_bounds(tmp_path, capsys, bounds, type_cell):
    """DL-276 A4: units are ignored and scientific/grouped rails compare exactly."""
    write_book(tmp_path, bounds=bounds, type_cell=type_cell)
    assert main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""
    write_book(tmp_path, bounds=bounds, type_cell=type_cell.replace("1", "2", 1))
    assert main([str(tmp_path)]) == 1
    assert "probe.limit" in capsys.readouterr().out


def test_numeric_literal_members_are_not_an_interval(tmp_path, capsys):
    """DL-276 A4: a Literal's numeric members do not invent a pair of rails."""
    write_book(
        tmp_path,
        default="0",
        value="`0`",
        annotation="Literal[0, 1]",
        type_cell="`Literal[0, 1]`",
    )
    assert main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""
