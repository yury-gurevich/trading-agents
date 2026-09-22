from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest


def _checker():
    try:
        from scripts import check_sprint_status
    except ImportError as exc:
        pytest.fail(f"sprint status checker is missing: {exc}")
    return check_sprint_status


def _write_doc(root: Path, name: str, content: str) -> Path:
    path = root / "docs" / "sprints" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("SPEC", "SPEC"),
        ("planned", "SPEC"),
        ("queued", "SPEC"),
        ("ready", "SPEC"),
        ("BUILT", "BUILT"),
        ("implemented", "BUILT"),
        ("MERGED", "MERGED"),
        ("shipped", "MERGED"),
    ],
)
def test_t1_known_leading_token_classifies_to_canonical_status(token, expected):
    checker = _checker()

    result = checker.classify_status_line(
        f"**Status:** {token} `abc123` · DEPLOYED `s211`"
    )

    assert result.status == expected


def test_t2_evidence_after_leading_token_is_preserved_unchanged():
    checker = _checker()
    evidence = " `abc123` · DEPLOYED `s211`"

    result = checker.classify_status_line(f"**Status:** MERGED{evidence}")

    assert result.status == "MERGED"
    assert result.evidence == evidence


def test_t3_unknown_leading_token_is_unmapped_not_guessed():
    checker = _checker()

    result = checker.classify_status_line("**Status:** mostly done, see notes")

    assert result.status == "UNMAPPED"


def test_t4_document_without_status_is_missing_not_spec(tmp_path):
    checker = _checker()
    _write_doc(tmp_path, "sprint-no-status.md", "# No declared state\n")

    report = checker.scan_root(tmp_path)

    assert report.entries[0].status == "MISSING"


@pytest.mark.parametrize("token", ["SPEC", "BUILT", "MERGED"])
def test_t5_vocabulary_tokens_round_trip(token):
    checker = _checker()

    assert checker.classify_status_line(f"**Status:** {token}").status == token


@pytest.mark.parametrize("token", ["shipped", "SHIPPED", "Shipped"])
def test_t6_shipped_synonym_is_case_insensitive(token):
    checker = _checker()

    assert checker.classify_status_line(f"**Status:** {token}").status == "MERGED"


def test_t7_checker_never_writes_a_sprint_document(tmp_path):
    checker = _checker()
    _write_doc(tmp_path, "sprint-known.md", "**Status:** BUILT evidence\n")
    _write_doc(tmp_path, "sprint-unknown.md", "**Status:** mostly done\n")
    _write_doc(tmp_path, "sprint-missing.md", "# No status\n")
    before = {
        path: sha256(path.read_bytes()).hexdigest()
        for path in (tmp_path / "docs" / "sprints").glob("*.md")
    }

    assert checker.main(["--report", str(tmp_path)]) == 0

    after = {path: sha256(path.read_bytes()).hexdigest() for path in before}
    assert after == before


def test_t8_unmapped_count_above_baseline_fails_and_names_document(tmp_path):
    checker = _checker()
    _write_doc(tmp_path, "sprint-new-unmapped.md", "**Status:** mostly done\n")

    result = checker.check_root(tmp_path, baseline=checker.Baseline())

    assert not result.ok
    assert "sprint-new-unmapped.md" in "\n".join(result.errors)


def test_t9_unmapped_count_below_baseline_passes(tmp_path):
    checker = _checker()
    _write_doc(tmp_path, "sprint-remaining-unmapped.md", "**Status:** mostly done\n")

    result = checker.check_root(tmp_path, baseline=checker.Baseline(unmapped=2))

    assert result.ok


def test_t10_real_corpus_reports_every_sprint_document(capsys):
    checker = _checker()
    root = Path(__file__).resolve().parents[1]
    expected_documents = len(
        [
            path
            for path in (root / "docs" / "sprints").glob("*.md")
            if path.name
            not in {"INDEX.md", "README.md", "_TEMPLATE.md", "status-unmapped.md"}
        ]
    )

    assert checker.main(["--report", str(root)]) == 0

    output = capsys.readouterr().out
    assert f"docs_seen={expected_documents}" in output
    report = checker.scan_root(root)
    assert all(
        entry.path.name
        not in {"INDEX.md", "README.md", "_TEMPLATE.md", "status-unmapped.md"}
        for entry in report.entries
    )


def test_t11_new_document_without_status_fails_and_names_document(tmp_path, capsys):
    checker = _checker()
    _write_doc(tmp_path, "sprint-new-missing.md", "# No status\n")

    assert checker.main([str(tmp_path)]) == 1

    assert "sprint-new-missing.md" in capsys.readouterr().out
