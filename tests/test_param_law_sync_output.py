"""DL-276 D5 output preserves failures on Windows consoles.

Agent: tooling
Role: prove printing failures and warnings never changes the exit result.
External I/O: temporary filesystem and in-memory stdout streams.
"""

import io
import sys

from scripts import param_law_sync_numbers
from scripts.check_param_law_sync import main
from tests.param_law_sync_helpers import write_book


def test_a_failing_symbolic_row_prints_on_cp1252(tmp_path, monkeypatch):
    """DL-276 A8: ≥ and ∈ are replaced on cp1252; the row still exits 1."""
    write_book(
        tmp_path,
        bounds=", ge=0, le=10",
        type_cell="`int ≥ 0, ∈ [0, 9]`",
    )
    buffer = io.BytesIO()
    with io.TextIOWrapper(
        buffer, encoding="cp1252", errors="strict", write_through=True
    ) as stream:
        with monkeypatch.context() as patch:
            patch.setattr(sys, "stdout", stream)
            exit_code = main([str(tmp_path)])
        output = buffer.getvalue().decode("cp1252")
    assert exit_code == 1
    assert "[FAIL] agents/probe/laws/laws.md:7: probe.limit" in output
    assert "?" in output
    assert "≥" not in output
    assert "∈" not in output


def test_a_warning_prints_on_cp1252(tmp_path, monkeypatch):
    """DL-276 A8: envelope warnings with unsupported symbols also print."""
    monkeypatch.setattr(param_law_sync_numbers, "EXCUSED_BOUNDS", {})
    write_book(tmp_path, bounds=", envelope=(6, 10), source='Synthetic ≥ rail.'")
    buffer = io.BytesIO()
    with io.TextIOWrapper(
        buffer, encoding="cp1252", errors="strict", write_through=True
    ) as stream:
        with monkeypatch.context() as patch:
            patch.setattr(sys, "stdout", stream)
            exit_code = main([str(tmp_path)])
        output = buffer.getvalue().decode("cp1252")
    assert exit_code == 0
    assert "[WARN] probe.limit" in output
    assert "Synthetic ? rail." in output


def test_a_stream_without_encoding_keeps_the_symbols(tmp_path, monkeypatch):
    """DL-276 A8: an encoding-less Unicode stream preserves the original line."""
    write_book(tmp_path, bounds=", ge=0, le=10", type_cell="`int ≥ 0, ≤ 9`")
    stream = io.StringIO()
    with monkeypatch.context() as patch:
        patch.setattr(sys, "stdout", stream)
        patch.chdir(tmp_path)
        exit_code = main([])
    assert exit_code == 1
    assert "probe.limit" in stream.getvalue()
    assert "≥" in stream.getvalue()
