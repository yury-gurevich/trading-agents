"""Rolling retrain script helper tests.

Agent: tooling
Role: verify retrain date windows, report formatting, and swap mechanics.
External I/O: temporary artifact fixtures only.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts import retrain_return_model_helpers as helpers

from agents.forecaster.domain.features import FeatureRow
from agents.forecaster.domain.retrain_policy import CompareVerdict, RetrainDecision
from agents.forecaster.domain.return_labels import LabelRow
from agents.forecaster.settings import ForecasterSettings


def _label(ticker: str, as_of_date: str) -> LabelRow:
    return LabelRow(ticker, as_of_date, FeatureRow(1, 1, 1, 1, 1, 1), 0.1)


def test_partition_recent_dates_uses_distinct_dates_not_row_counts() -> None:
    rows = [
        _label("A", "2024-01-01"),
        _label("B", "2024-01-01"),
        _label("A", "2024-01-02"),
        _label("A", "2024-01-03"),
    ]

    history, recent = helpers.partition_recent_dates(rows, window_days=2)

    assert [row.as_of_date for row in history] == ["2024-01-01", "2024-01-01"]
    assert [row.as_of_date for row in recent] == ["2024-01-02", "2024-01-03"]


def test_partition_recent_dates_handles_fewer_dates_than_window() -> None:
    history, recent = helpers.partition_recent_dates(
        [_label("A", "2024-01-01")], window_days=5
    )

    assert history == []
    assert len(recent) == 1


def test_partition_recent_dates_rejects_non_positive_window() -> None:
    with pytest.raises(ValueError, match="window_days must be positive"):
        helpers.partition_recent_dates([], window_days=0)


def test_label_rows_for_horizon_uses_forecaster_feature_settings() -> None:
    bars = {
        "A": [(f"2024-01-{index + 1:02d}", 100.0 + index, 100.0) for index in range(25)]
    }

    rows = helpers.label_rows_for_horizon(
        bars,
        horizon=1,
        settings=ForecasterSettings(),
    )

    assert len(rows) == 4
    assert rows[0].as_of_date == "2024-01-21"


def test_render_comparison_table_formats_deltas_and_missing_metrics() -> None:
    table = helpers.render_comparison_table(
        {"complete_cases": 10.0, "rank_ic": 0.01},
        {"complete_cases": 12.0, "rank_ic": 0.03},
    )

    assert "| complete_cases | 10 | 12 | 2.0000 |" in table
    assert "| rank_ic | 0.0100 | 0.0300 | 0.0200 |" in table
    assert "| ic_ir | N/A | N/A | N/A |" in table


def test_decision_and_verdict_payloads_are_json_shapes() -> None:
    decision = RetrainDecision(True, "reference non-positive", 0.1, 0.0)
    verdict = CompareVerdict(False, "challenger did not win both", 0.1, -0.1)

    assert helpers.decision_to_dict(decision)["reason"] == "reference non-positive"
    assert helpers.verdict_to_dict(None) is None
    assert helpers.verdict_to_dict(verdict) == {
        "swap": False,
        "reason": "challenger did not win both",
        "primary_delta": 0.1,
        "secondary_delta": -0.1,
    }


def test_candidate_path_and_swap_plan_archive_without_delete(tmp_path) -> None:
    model_path = tmp_path / "models" / "lgbm-return-v1.txt"
    candidate_path = helpers.candidate_path_for(model_path, stamp="20260704T010203Z")

    steps = helpers.plan_swap(model_path, candidate_path, stamp="20260704T010203Z")

    assert candidate_path == (
        tmp_path / "models" / "candidates" / "lgbm-return-v1-20260704T010203Z.txt"
    )
    assert steps == [
        (
            "archive",
            model_path,
            tmp_path / "models" / "archive" / "lgbm-return-v1-20260704T010203Z.txt",
        ),
        ("install", candidate_path, model_path),
    ]
    assert all(action != "delete" for action, _, _ in steps)


def test_execute_swap_archives_incumbent_and_keeps_challenger(tmp_path) -> None:
    model_path = tmp_path / "models" / "lgbm-return-v1.txt"
    candidate_path = tmp_path / "models" / "candidates" / "challenger.txt"
    model_path.parent.mkdir()
    candidate_path.parent.mkdir()
    model_path.write_text("old", encoding="utf-8")
    candidate_path.write_text("new", encoding="utf-8")
    steps = helpers.plan_swap(model_path, candidate_path, stamp="20260704T010203Z")

    helpers.execute_swap(steps)

    archive_path = Path(steps[0][2])
    assert archive_path.read_text(encoding="utf-8") == "old"
    assert model_path.read_text(encoding="utf-8") == "new"
    assert candidate_path.read_text(encoding="utf-8") == "new"


def test_execute_swap_rejects_unknown_action(tmp_path) -> None:
    with pytest.raises(ValueError, match="unknown swap action"):
        helpers.execute_swap([("surprise", tmp_path / "a", tmp_path / "b")])


def test_report_payload_includes_optional_challenger_metrics(tmp_path) -> None:
    payload = helpers.report_payload(
        model_path=tmp_path / "model.txt",
        generated_at="2026-07-04T00:00:00+00:00",
        config={"force": True},
        decision=RetrainDecision(False, "healthy", 0.2, 0.3),
        verdict=None,
        reference={"ic_ir": 0.3},
        recent_incumbent={"ic_ir": 0.2},
        recent_challenger=None,
    )

    assert payload["verdict"] is None
    assert payload["recent_challenger"] is None


def test_build_parser_defaults_from_settings() -> None:
    settings = ForecasterSettings(
        return_model_path="models/custom.txt",
        retrain_window_days=80,
        retrain_trigger_fraction=0.25,
        retrain_horizon_days=10,
        retrain_min_cases=600,
    )

    args = helpers.build_parser(settings).parse_args(
        ["--input", "bars.csv", "--out", "report.json"]
    )

    assert args.model == "models/custom.txt"
    assert args.window_days == 80
    assert args.trigger_fraction == 0.25
    assert args.horizon == 10
    assert args.min_cases == 600
