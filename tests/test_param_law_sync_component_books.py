from __future__ import annotations

from textwrap import dedent

from scripts.check_param_law_sync import main


def test_surfaces_book_syncs_against_mapped_dashboard_settings(tmp_path, capsys):
    package = tmp_path / "surfaces" / "dashboard"
    package.mkdir(parents=True)
    (tmp_path / "surfaces" / "__init__.py").write_text("", encoding="utf-8")
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "settings.py").write_text(
        dedent(
            """
            from kernel import AgentSettings, tunable


            class DashboardSettings(AgentSettings):
                refresh_seconds: int = tunable(30, why="Bound refresh cadence.")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    laws = tmp_path / "surfaces" / "laws"
    laws.mkdir(parents=True)
    (laws / "laws.md").write_text(
        dedent(
            """
            # Surfaces laws

            ## Parameters (`PARAM`)

            | Name | Value | Type | Tunable | Rationale |
            | --- | --- | --- | --- | --- |
            | `refresh_seconds` | `30` | `int` | NO | Planted mismatch. |

            ## Changelog
            """
        ).lstrip(),
        encoding="utf-8",
    )

    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "surfaces.refresh_seconds" in output
    assert "law declares NO" in output
