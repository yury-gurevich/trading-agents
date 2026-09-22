from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest
from scripts import check_sprint_status as checker
from scripts.sprint_status_index import leading_token, readme_cells

_EXCLUDED = {"INDEX.md", "README.md", "_TEMPLATE.md"}


def _write_doc(root: Path, name: str, content: str) -> Path:
    path = root / "docs" / "sprints" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_readme(root: Path, *rows: tuple[str, str]) -> None:
    lines = ["| Sprint | Goal | Status |", "| --- | --- | --- |"]
    lines += [f"| [{name}]({name}) | goal | {cell} |" for name, cell in rows]
    _write_doc(root, "README.md", "\n".join(lines) + "\n")


@pytest.mark.parametrize("token", ["SPEC", "BUILT", "MERGED"])
def test_t1_vocabulary_tokens_round_trip(token):
    assert checker.classify_status_line(f"**Status:** {token}").status == token


def test_t2_evidence_after_leading_token_is_preserved_unchanged():
    evidence = " — `abc123` · DEPLOYED `s211`"

    result = checker.classify_status_line(f"**Status:** MERGED{evidence}")

    assert result.status == "MERGED"
    assert result.evidence == evidence


@pytest.mark.parametrize(
    "token",
    ["shipped", "planned", "queued", "ready", "implemented", "Merged", "BUILT;"],
)
def test_t3_a_retired_synonym_is_now_a_refusal(token):
    """Item 22 Part B migrated every synonym S224 accepted, so none is read again."""
    assert checker.classify_status_line(f"**Status:** {token}").status == "UNMAPPED"


def test_t4_document_without_status_is_missing_not_spec(tmp_path):
    _write_doc(tmp_path, "sprint-no-status.md", "# No declared state\n")

    assert checker.scan_root(tmp_path).entries[0].status == "MISSING"


def test_t5_one_unmapped_document_fails_and_names_itself(tmp_path):
    _write_doc(tmp_path, "sprint-vague.md", "**Status:** mostly done\n")
    _write_readme(tmp_path, ("sprint-vague.md", "MERGED"))

    result = checker.check_root(tmp_path)

    assert not result.ok
    assert "UNMAPPED: docs/sprints/sprint-vague.md" in "\n".join(result.errors)


def test_t6_new_document_without_status_fails_and_names_itself(tmp_path, capsys):
    _write_doc(tmp_path, "sprint-new-missing.md", "# No status\n")

    assert checker.main([str(tmp_path)]) == 1

    assert "MISSING: docs/sprints/sprint-new-missing.md" in capsys.readouterr().out


def test_t7_a_readme_row_that_disagrees_fails_and_quotes_the_cell(tmp_path):
    """S205, S207 and S223 merged while their README rows still read SPEC."""
    _write_doc(tmp_path, "sprint-merged.md", "**Status:** MERGED `abc123`\n")
    _write_readme(tmp_path, ("sprint-merged.md", "**SPEC**"))

    result = checker.check_root(tmp_path)

    assert result.errors == (
        "[FAIL] README DISAGREES: docs/sprints/sprint-merged.md declares MERGED, "
        "its README row reads: **SPEC**",
    )


def test_t8_a_document_with_no_readme_row_fails(tmp_path):
    _write_doc(tmp_path, "sprint-unlisted.md", "**Status:** SPEC\n")

    result = checker.check_root(tmp_path)

    assert result.errors == (
        "[FAIL] NO README ROW: docs/sprints/sprint-unlisted.md declares SPEC",
    )


def test_t9_agreeing_rows_pass_whether_or_not_the_token_is_bold(tmp_path):
    _write_doc(tmp_path, "sprint-a.md", "**Status:** MERGED — shipped\n")
    _write_doc(tmp_path, "sprint-b.md", "**Status:** SPEC\n")
    _write_readme(
        tmp_path, ("sprint-a.md", "**MERGED** (0.1.00)"), ("sprint-b.md", "SPEC")
    )

    assert checker.check_root(tmp_path).ok


def test_t10_an_escaped_pipe_inside_a_cell_is_not_a_cell_boundary(tmp_path):
    """S185's row had an unescaped `advisory | binding`, so its last cell was wrong."""
    readme = tmp_path / "README.md"
    readme.write_text(
        "| [s](s.md) | a `x \\| y` goal | **MERGED** `abc` |\nnot a row\n",
        encoding="utf-8",
    )

    assert readme_cells(readme) == {"s.md": "**MERGED** `abc`"}


def test_t11_a_cell_with_no_word_has_no_token():
    assert leading_token("— 🟢") is None


def test_t12_checker_never_writes_a_sprint_document(tmp_path):
    _write_doc(tmp_path, "sprint-known.md", "**Status:** BUILT evidence\n")
    _write_doc(tmp_path, "sprint-unknown.md", "**Status:** mostly done\n")
    _write_doc(tmp_path, "sprint-missing.md", "# No status\n")
    before = {
        path: sha256(path.read_bytes()).hexdigest()
        for path in (tmp_path / "docs" / "sprints").glob("*.md")
    }

    assert checker.main(["--report", str(tmp_path)]) == 0

    assert {p: sha256(p.read_bytes()).hexdigest() for p in before} == before


def test_t13_real_corpus_has_no_refusal_and_no_disagreement(capsys):
    """Item 22 Part B: every spec declares a status, and its README row agrees."""
    root = Path(__file__).resolve().parents[1]
    expected = [
        path
        for path in (root / "docs" / "sprints").glob("*.md")
        if path.name not in _EXCLUDED
    ]

    assert checker.main([str(root)]) == 0

    output = capsys.readouterr().out
    assert f"docs_seen={len(expected)} " in output
    assert "UNMAPPED=0 MISSING=0" in output
