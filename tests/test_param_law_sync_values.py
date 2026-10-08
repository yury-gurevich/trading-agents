"""DL-276 Value-cell comparisons against declared defaults.

Agent: tooling
Role: prove incorrect defaults fail before any production settings are changed.
External I/O: temporary filesystem writes and checker reads.
"""

import pytest
from scripts.check_param_law_sync import main
from tests.param_law_sync_helpers import write_book


def test_a_wrong_value_names_the_law_and_code_and_fails(tmp_path, capsys):
    """DL-276 A1: the old token cap fails; the declared default restores green."""
    write_book(tmp_path, default="16384", value="`8192`")
    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "[FAIL] agents/probe/laws/laws.md:7: probe.limit" in output
    assert "8192" in output
    assert "16384" in output

    write_book(tmp_path, default="16384", value="`16384`")
    assert main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    ("annotation", "default", "value", "wrong"),
    [
        ("int", "16384", "`16384`", "`8192`"),
        ("int", "1000", "`1,000`", "`1,001`"),
        ("int", "1000", "`1_000`", "`1_001`"),
        ("float", "0.1", "`0.10`", "`0.11`"),
        ("Decimal", 'Decimal("0.10")', "`0.10`", "`0.11`"),
        ("Decimal", 'Decimal("100000.00")', '`Decimal("100000.00")`', "`99999`"),
        ("Decimal", 'Decimal("1e9")', "`1e9`", "`1e8`"),
        ("str", '"paper"', '`"paper"`', '`"live"`'),
        ("str", '"paper"', "paper", "live"),
        ("str", '""', "empty", '`"empty"`'),
        ("str", '""', '`""`', "filled"),
        ("str", '""', "-", "filled"),
        ("str", '""', "—", "filled"),
        ("str", '""', "\N{EN DASH}", "filled"),
        ("str | None", "None", "-", "filled"),
        ("str | None", "None", "—", "filled"),
        ("str | None", "None", "\N{EN DASH}", "filled"),
        ("str | None", "None", "NONE", "filled"),
        ("str | None", "None", "null", "filled"),
        ("str | None", "None", "unset", "filled"),
        ("str | None", "None", "empty", "filled"),
        ("bool", "True", "`TrUe`", "false"),
        ("bool", "False", "false", "true"),
        ("date", "date(2026, 10, 8)", "`2026-10-08`", "`2026-10-07`"),
    ],
)
def test_every_value_form_compares_the_default(
    tmp_path,
    capsys,
    annotation,
    default,
    value,
    wrong,
):
    """DL-276 A2: every D1 spelling passes and its changed value fails."""
    write_book(tmp_path, annotation=annotation, default=default, value=value)
    assert main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""
    write_book(tmp_path, annotation=annotation, default=default, value=wrong)
    assert main([str(tmp_path)]) == 1
    assert "probe.limit" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("annotation", "default", "value"),
    [
        ("int", "5", "words"),
        ("int", "5", "-"),
        ("float", "0.1", "`NaN`"),
        ("float", "0.1", "`Infinity`"),
        ("bool", "False", "0"),
        ("date", "date(2026, 10, 8)", "yesterday"),
        ("date", "date(2026, 10, 8)", "`20261008`"),
        ("tuple[int, int]", "(1, 2)", "`(1, 2)`"),
    ],
)
def test_unreadable_values_fail_instead_of_skipping(
    tmp_path, capsys, annotation, default, value
):
    """DL-276 A3: unreadable cells are attributed failures, including dashes."""
    write_book(tmp_path, annotation=annotation, default=default, value=value)
    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "probe.limit" in output
    assert "could not be compared" in output
