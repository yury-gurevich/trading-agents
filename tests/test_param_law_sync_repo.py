from __future__ import annotations

from scripts import param_law_sync


def test_the_repo_has_no_param_settings_divergence_left():
    """DRIFT-052 / DL-276: names, tunables, defaults, bounds agree; none excused."""

    report = param_law_sync.check_root(param_law_sync._ROOT)

    assert report.errors == []
    assert len(report.warnings) == 2
    assert all("envelope=" in line for line in report.warnings)

    from scripts.param_law_sync_excused import EXCUSED_BOUNDS

    assert EXCUSED_BOUNDS == {}


def test_a_repo_divergence_fails_rather_than_warns(monkeypatch):
    """DRIFT-052: a field that loses its PARAM row fails; nothing downgrades it."""

    real_rows = param_law_sync.param_rows

    def rows_without_atr_period(root, agent):
        rows = real_rows(root, agent)
        if agent == "analyst":
            del rows["atr_period"]
        return rows

    monkeypatch.setattr(param_law_sync, "param_rows", rows_without_atr_period)
    report = param_law_sync.check_root(param_law_sync._ROOT)

    assert not report.ok
    assert len(report.errors) == 1
    assert report.errors[0].startswith("[FAIL] agents/analyst/settings_indicators.py:")
    assert report.errors[0].endswith(
        "analyst.atr_period settings field has no PARAM row"
    )
    assert not any("atr_period" in line for line in report.warnings)
