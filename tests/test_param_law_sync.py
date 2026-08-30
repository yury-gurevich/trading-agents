from __future__ import annotations

from textwrap import dedent

import pytest


def _checker():
    try:
        from scripts.check_param_law_sync import main
    except ModuleNotFoundError as exc:
        pytest.fail(f"parameter law sync checker is missing: {exc}")
    return main


def _write_probe(root, *, fields: str = "", rows: tuple[str, ...] = ()) -> None:
    package = root / "agents" / "probe"
    (package / "laws").mkdir(parents=True)
    (root / "agents").mkdir(exist_ok=True)
    (root / "agents" / "__init__.py").write_text("", encoding="utf-8")
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "settings.py").write_text(
        dedent(
            f"""
            from typing import Literal

            from pydantic import Field

            from kernel import AgentSettings, tunable


            class ProbeSettings(AgentSettings):
                limit_bps: int = tunable(50, why="Bound the synthetic order band.")
                stop_target_mode: Literal["flat", "scaled"] = "flat"
                alpaca_api_key: str = Field(default="", repr=False)
                stage: str = "paper"
            {fields}
            """
        ).lstrip(),
        encoding="utf-8",
    )
    law_rows = "\n".join(
        (
            "| `limit_bps` | `50` | `int` | YES | Bound the synthetic order band. |",
            '| `stop_target_mode` | `"flat"` | `Literal["flat","scaled"]` | '
            "NO (mode selector) | Mode selector, not a tunable. |",
            "| `alpaca_api_key` | - | `str` | NO (secret) | "
            "Secret never leaves config. |",
            '| `stage` | `"paper"` | `str` | NO (config) | Operator-selected stage. |',
            *rows,
        )
    )
    (package / "laws" / "laws.md").write_text(
        dedent(
            f"""
            # Probe laws

            ## Parameters (`PARAM`)

            | Name | Value | Type | Tunable | Rationale |
            | --- | --- | --- | --- | --- |
            {law_rows}

            ## Changelog
            """
        ).lstrip(),
        encoding="utf-8",
    )


def test_param_row_without_settings_field_fails(tmp_path, capsys):
    _write_probe(
        tmp_path,
        rows=('| `missing_from_settings` | `"x"` | `str` | NO (config) | Planted. |',),
    )

    assert _checker()([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "probe.missing_from_settings" in output
    assert "PARAM row has no settings field" in output


def test_settings_field_without_param_row_fails(tmp_path, capsys):
    _write_probe(tmp_path, fields='    undocumented: str = "x"\n')

    assert _checker()([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "probe.undocumented" in output
    assert "settings field has no PARAM row" in output


def test_declared_mode_selectors_are_not_tunables(tmp_path, capsys):
    _write_probe(tmp_path)

    assert _checker()([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


def test_secret_and_config_only_rows_are_allowed(tmp_path, capsys):
    _write_probe(tmp_path)

    assert _checker()([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


def test_escaped_pipe_type_does_not_corrupt_tunable_cell(tmp_path, capsys):
    _write_probe(
        tmp_path,
        fields='    effort: str = tunable("max", why="Bound effort.")\n',
        rows=(
            '| `effort` | `"max"` | `low\\|medium\\|high\\|max` | YES | '
            "Bound effort. |",
        ),
    )

    assert _checker()([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""
