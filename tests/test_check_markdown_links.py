from __future__ import annotations

import pytest


def _checkers():
    try:
        from scripts.check_markdown_links import check_paths, main
    except ModuleNotFoundError as exc:
        pytest.fail(f"markdown link checker is missing: {exc}")
    return check_paths, main


def test_missing_relative_link_fails_with_location_and_href(tmp_path, capsys):
    document = tmp_path / "broken.md"
    document.write_text("[missing](nope.md)\n", encoding="utf-8")

    _, main = _checkers()
    assert main([str(document)]) == 1
    output = capsys.readouterr().out
    assert f"{document}:1" in output
    assert "nope.md" in output
    assert "missing target" in output


def test_existing_relative_link_passes(tmp_path, capsys):
    document = tmp_path / "source.md"
    (tmp_path / "target.md").write_text("# Target\n", encoding="utf-8")
    document.write_text("[target](target.md)\n", encoding="utf-8")

    _, main = _checkers()
    assert main([str(document)]) == 0
    assert capsys.readouterr().out == ""


def test_missing_markdown_fragment_fails(tmp_path, capsys):
    document = tmp_path / "source.md"
    (tmp_path / "target.md").write_text("# Present\n", encoding="utf-8")
    document.write_text("[target](target.md#absent)\n", encoding="utf-8")

    _, main = _checkers()
    assert main([str(document)]) == 1
    assert "missing fragment 'absent'" in capsys.readouterr().out


def test_duplicate_heading_fragment_uses_github_suffix(tmp_path, capsys):
    document = tmp_path / "source.md"
    (tmp_path / "target.md").write_text("# Repeat\n\n# Repeat\n", encoding="utf-8")
    document.write_text("[target](target.md#repeat-1)\n", encoding="utf-8")

    _, main = _checkers()
    assert main([str(document)]) == 0
    assert capsys.readouterr().out == ""


def test_heading_fragment_keeps_underscores(tmp_path, capsys):
    """GitHub keeps underscores in anchors; dropping them reports a valid link."""
    document = tmp_path / "source.md"
    (tmp_path / "target.md").write_text("# reward_risk gate\n", encoding="utf-8")
    document.write_text("[target](target.md#reward_risk-gate)\n", encoding="utf-8")

    _, main = _checkers()
    assert main([str(document)]) == 0
    assert capsys.readouterr().out == ""


def test_heading_fragment_keeps_inline_code_content(tmp_path, capsys):
    document = tmp_path / "source.md"
    (tmp_path / "target.md").write_text("# Deploy `up`\n", encoding="utf-8")
    document.write_text("[target](target.md#deploy-up)\n", encoding="utf-8")

    _, main = _checkers()
    assert main([str(document)]) == 0
    assert capsys.readouterr().out == ""


def test_inline_code_link_shape_is_ignored(tmp_path, capsys):
    document = tmp_path / "source.md"
    document.write_text("`probes[probe](env)`\n", encoding="utf-8")

    _, main = _checkers()
    assert main([str(document)]) == 0
    assert capsys.readouterr().out == ""


def test_fenced_link_shape_is_ignored(tmp_path, capsys):
    document = tmp_path / "source.md"
    document.write_text("```text\n[x](nope.md)\n```\n", encoding="utf-8")

    _, main = _checkers()
    assert main([str(document)]) == 0
    assert capsys.readouterr().out == ""


def test_path_like_link_text_must_match_target(tmp_path, capsys):
    document = tmp_path / "source.md"
    (tmp_path / "target.md").write_text("# Target\n", encoding="utf-8")
    document.write_text("[a/b.md](target.md)\n", encoding="utf-8")

    _, main = _checkers()
    assert main([str(document)]) == 1
    assert (
        "path-like text 'a/b.md' does not match href 'target.md'"
        in capsys.readouterr().out
    )


def test_path_like_text_accepts_repository_relative_target(tmp_path, capsys):
    document = tmp_path / "docs" / "source.md"
    target = tmp_path / "orchestration" / "start.py"
    document.parent.mkdir()
    target.parent.mkdir()
    target.write_text("pass\n", encoding="utf-8")
    document.write_text(
        "[orchestration/start.py](../orchestration/start.py)\n", encoding="utf-8"
    )

    check_paths, _ = _checkers()
    assert check_paths([document], tmp_path) == []
    assert capsys.readouterr().out == ""


def test_external_mail_and_autolinks_are_ignored(tmp_path, capsys):
    document = tmp_path / "source.md"
    document.write_text(
        "[web](https://example.invalid) [mail](mailto:ops@example.invalid) "
        "<https://example.invalid>\n",
        encoding="utf-8",
    )

    _, main = _checkers()
    assert main([str(document)]) == 0
    assert capsys.readouterr().out == ""


def test_missing_image_target_fails(tmp_path, capsys):
    document = tmp_path / "source.md"
    document.write_text("![diagram](missing.svg)\n", encoding="utf-8")

    _, main = _checkers()
    assert main([str(document)]) == 1
    assert "missing target" in capsys.readouterr().out


def test_generated_report_tree_is_ignored(tmp_path):
    report = tmp_path / "codeql" / "python-security" / "reports" / "report.md"
    report.parent.mkdir(parents=True)
    report.write_text("[missing](nope.md)\n", encoding="utf-8")

    check_paths, _ = _checkers()
    assert check_paths([report], tmp_path) == []
