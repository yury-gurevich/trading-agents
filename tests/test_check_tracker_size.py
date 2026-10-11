"""Prove the charter's tracker size gate and its fail-closed parsing.

Agent: tests
Role: exercise the thirteen cases of Sprint 261 against isolated roots.
External I/O: reads the repository charter only in T12; otherwise temporary files.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.tracker_size_fixtures import (
    BAD_ROWS,
    CHARTER,
    broken_tables,
    charter,
    load_checker,
    plant,
)


def test_under_limit_reports_exact_size(tmp_path, capsys):
    """T1: a tracker below its charter limit passes with the exact byte report."""
    checker = load_checker()
    plant(tmp_path, files={"docs/a.md": b"x" * 500})
    assert checker.main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == "[OK] docs/a.md: 500 of 2,000 bytes (25 %)\n"


def test_one_byte_over_fails_and_exact_limit_still_reported(tmp_path, capsys):
    """T2: equality passes and an earlier failure does not hide later trackers."""
    checker = load_checker()
    plant(
        tmp_path,
        "| `docs/over.md` | 1 KB |\n| `docs/at.md` | 1 KB |",
        {"docs/over.md": b"x" * 1001, "docs/at.md": b"x" * 1000},
    )
    assert checker.main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "[FAIL] docs/over.md: 1,001 of 1,000 bytes, over by 1." in output
    assert "do not raise the limit" in output
    assert "[WARN] docs/at.md: 1,000 of 1,000 bytes (100 %)\n" in output


def test_crlf_counts_git_stored_bytes(tmp_path, capsys):
    """T3: CRLF contributes the LF byte count that git stores."""
    checker = load_checker()
    plant(tmp_path, "| `docs/a.md` | 1 KB |", {"docs/a.md": b"line\r\n" * 200})
    path = tmp_path / "docs/a.md"
    assert path.stat().st_size == 1200
    assert checker.stored_size(path) == 1000
    assert checker.main([str(tmp_path)]) == 0
    assert "1,000 of 1,000 bytes" in capsys.readouterr().out


def test_utf8_counts_bytes_not_characters(tmp_path, capsys):
    """T4: multibyte characters can exceed a limit despite their character count."""
    checker = load_checker()
    plant(tmp_path, "| `docs/a.md` | 1 KB |", {"docs/a.md": ("é" * 501).encode()})
    assert checker.main([str(tmp_path)]) == 1
    assert "[FAIL] docs/a.md: 1,002 of 1,000 bytes" in capsys.readouterr().out


def test_missing_tracker_fails(tmp_path, capsys):
    """T5: a tracker named by the charter cannot silently disappear."""
    checker = load_checker()
    plant(tmp_path, "| `docs/gone.md` | 1 KB |")
    assert checker.main([str(tmp_path)]) == 1
    assert "[FAIL] docs/gone.md: named in" in capsys.readouterr().out


def test_ninety_percent_warns_without_failing(tmp_path, capsys):
    """T6: the warning starts at ninety percent, while both trackers pass."""
    checker = load_checker()
    plant(
        tmp_path,
        "| `docs/low.md` | 1 KB |\n| `docs/due.md` | 1 KB |",
        {"docs/low.md": b"x" * 899, "docs/due.md": b"x" * 900},
    )
    assert checker.main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == (
        "[OK] docs/low.md: 899 of 1,000 bytes (89 %)\n"
        "[WARN] docs/due.md: 900 of 1,000 bytes (90 %)\n"
    )


def test_unreadable_rows_fail_without_partial_reports(tmp_path, capsys):
    """T7: every malformed row invalidates the whole table before any OK report."""
    checker = load_checker()
    for row in BAD_ROWS:
        plant(tmp_path, f"| `docs/a.md` | 2 KB |\n{row}", {"docs/a.md": b"x"})
        assert checker.main([str(tmp_path)]) == 1, row
        output = capsys.readouterr().out
        assert "cannot read the limit row" in output, row
        assert "[OK]" not in output, row


def test_absent_ambiguous_empty_or_duplicate_table_fails(tmp_path, capsys):
    """T8: absent, ambiguous, empty and duplicate tables all fail closed."""
    checker = load_checker()
    for text, message in broken_tables():
        plant(tmp_path, files={"docs/a.md": b"x"}, text=text)
        assert checker.main([str(tmp_path)]) == 1, message
        assert message in capsys.readouterr().out


def test_missing_unreadable_or_duplicate_sections_fail(tmp_path, capsys):
    """T9: missing or unreadable charter files and two sections are rejected."""
    checker = load_checker()
    assert checker.main([str(tmp_path)]) == 1
    assert capsys.readouterr().out.startswith(f"[FAIL] {CHARTER}: ")
    plant(tmp_path)
    (tmp_path / CHARTER).write_bytes(b"\xff\xfe")
    assert checker.main([str(tmp_path)]) == 1
    assert capsys.readouterr().out.startswith(f"[FAIL] {CHARTER}: ")
    text = charter() + "\n## OPS-TRIM · Second section\n"
    with pytest.raises(checker.CharterError, match="section, found 2"):
        checker.read_limits(text)


def test_padded_cells_and_aligned_rule_rows_read(tmp_path):
    """T10: editor padding and Markdown alignment do not alter the limits."""
    checker = load_checker()
    text = charter("|   `docs/a.md`   |  2 KB  |\n| `docs/b.md` | 1 KB |")
    text = text.replace("| Tracker | Limit |", "|  Tracker  |  Limit  |  Notes  |")
    text = text.replace("| --- | --- |", "| :--- | ---: | :---: |")
    plant(tmp_path, text=text)
    assert checker.read_limits((tmp_path / CHARTER).read_text()) == {
        "docs/a.md": 2000,
        "docs/b.md": 1000,
    }


def test_only_ops_trim_limit_table_is_read(tmp_path):
    """T11: tables before, after and of another shape are outside the limits."""
    checker = load_checker()
    plant(tmp_path)
    assert checker.read_limits((tmp_path / CHARTER).read_text()) == {"docs/a.md": 2000}


def test_repository_charter_tracks_seven_existing_files():
    """T12: the real charter's seven decimal byte limits name existing trackers."""
    checker = load_checker()
    root = Path(__file__).resolve().parents[1]
    limits = checker.read_limits((root / CHARTER).read_text(encoding="utf-8"))
    assert limits == {
        "docs/STATE.md": 40000,
        "docs/work-queue.md": 64000,
        "docs/sprints/README.md": 96000,
        "docs/sprints/INDEX.md": 48000,
        "docs/design-log.md": 512000,
        "docs/laws/functionality-checks.md": 160000,
        "docs/laws/drift-register.md": 160000,
    }
    assert all((root / name).is_file() for name in limits)


def test_no_argument_uses_working_directory(tmp_path, monkeypatch, capsys):
    """T13: an omitted root uses the caller's working directory."""
    checker = load_checker()
    plant(tmp_path, files={"docs/a.md": b"x" * 500})
    monkeypatch.chdir(tmp_path)
    assert checker.main([]) == 0
    assert "[OK] docs/a.md" in capsys.readouterr().out
