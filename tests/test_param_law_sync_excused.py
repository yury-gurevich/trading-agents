"""DL-276 D4 exceptions must retain their exact text and remain necessary.

Agent: tooling
Role: prove excuses cover bounds only and cannot survive edits or reconciliation.
External I/O: temporary filesystem writes and checker reads.
"""

import pytest
from scripts import param_law_sync_numbers
from scripts.check_param_law_sync import main
from tests.param_law_sync_helpers import write_book


@pytest.mark.parametrize(
    ("type_cell", "exit_code", "failure_count"),
    [
        ("`int ≥ 0, ≤ 8`", 0, 0),
        ("`int ≥ 0, ≤ 9`", 1, 2),
        ("`int ≥ 0, ≤ 10`", 1, 1),
        ("int ≥ 0, ≤ 8", 1, 2),
    ],
)
def test_an_excuse_requires_its_exact_still_wrong_text(
    tmp_path,
    capsys,
    monkeypatch,
    type_cell,
    exit_code,
    failure_count,
):
    """DL-276 A6: only the recorded wrong cell passes; edited/stale entries fail."""
    monkeypatch.setattr(
        param_law_sync_numbers, "EXCUSED_BOUNDS", {"probe.limit": "`int ≥ 0, ≤ 8`"}
    )
    write_book(tmp_path, bounds=", ge=0, le=10", type_cell=type_cell)
    assert main([str(tmp_path)]) == exit_code
    lines = capsys.readouterr().out.splitlines()
    assert sum(line.startswith("[FAIL]") for line in lines) == failure_count
    assert all("probe.limit" in line for line in lines)
    if exit_code:
        assert any("excused list entry" in line and "delete" in line for line in lines)
        assert not any(line.startswith("[WARN]") for line in lines)
    else:
        assert lines == ["[WARN] excused PARAM bounds: probe.limit"]


def test_an_excuse_never_excuses_a_wrong_value(tmp_path, capsys, monkeypatch):
    """DL-276 A6: an exact bounds exception cannot turn default drift green."""
    monkeypatch.setattr(
        param_law_sync_numbers, "EXCUSED_BOUNDS", {"probe.limit": "`int ≥ 0, ≤ 8`"}
    )
    write_book(
        tmp_path, value="`4`", bounds=", ge=0, le=10", type_cell="`int ≥ 0, ≤ 8`"
    )
    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "law Value" in output
    assert "code default 5" in output
    assert "[WARN] excused PARAM bounds: probe.limit" in output


def test_an_excuse_fails_when_code_catches_up_without_a_cell_edit(
    tmp_path,
    capsys,
    monkeypatch,
):
    """DL-276 A6: a recorded cell that now agrees with code must lose its entry."""
    monkeypatch.setattr(
        param_law_sync_numbers, "EXCUSED_BOUNDS", {"probe.limit": "`int ≥ 0, ≤ 8`"}
    )
    write_book(tmp_path, bounds=", ge=0, le=8", type_cell="`int ≥ 0, ≤ 8`")
    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "probe.limit excused list entry" in output
    assert "delete" in output
    assert "[WARN]" not in output


def test_an_absent_book_is_not_judged(tmp_path, capsys, monkeypatch):
    """DL-276 A6: a temporary root is not penalized for books it does not hold."""
    monkeypatch.setattr(
        param_law_sync_numbers, "EXCUSED_BOUNDS", {"absent.limit": "`int ≥ 0`"}
    )
    write_book(tmp_path)
    assert main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


def test_an_entry_for_a_missing_field_in_a_present_book_fails(
    tmp_path, capsys, monkeypatch
):
    """DL-276 A6: deleting a row/field cannot silently leave an unused entry."""
    monkeypatch.setattr(
        param_law_sync_numbers, "EXCUSED_BOUNDS", {"probe.gone": "`int ≥ 0`"}
    )
    write_book(tmp_path)
    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "probe.gone excused list entry" in output
    assert "delete" in output
