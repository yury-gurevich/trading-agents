"""Backtest proposal script helper tests.

Agent: tooling
Role: verify catalogue dispatch, fail-open behavior, and evidence JSON output.
External I/O: temporary CSV/JSON fixtures only.
"""

from __future__ import annotations

import json

from scripts import backtest_proposal

from contracts.researcher import BacktestEvidence


def test_catalogue_builders_use_inventory_parameter_names() -> None:
    bars = _bars()

    rsi = backtest_proposal.build_scores("analyst.rsi_period", 2.0, bars)
    bollinger = backtest_proposal.build_scores("analyst.bollinger_window", 3.0, bars)

    assert rsi is not None
    assert bollinger is not None
    assert "2024-01-03" in rsi
    assert "2024-01-03" in bollinger
    assert backtest_proposal.build_scores("analyst.unknown", 1.0, bars) is None


def test_run_writes_proposed_evidence_and_prints_table(tmp_path, capsys) -> None:
    input_path = tmp_path / "bars.csv"
    out_path = tmp_path / "evidence.json"
    _write_csv(input_path)
    args = backtest_proposal.build_parser().parse_args(
        [
            "--parameter",
            "analyst.rsi_period",
            "--current",
            "2",
            "--proposed",
            "3",
            "--input",
            str(input_path),
            "--out",
            str(out_path),
        ]
    )

    assert backtest_proposal.run(args) == 0

    output = capsys.readouterr().out
    evidence = BacktestEvidence.model_validate(json.loads(out_path.read_text()))
    assert "| metric | incumbent full | proposed full | delta |" in output
    assert "holdout delta" in output
    assert evidence.engine == "walkforward-v1"
    assert evidence.n_days > 0


def test_unknown_parameter_fails_open_without_report(tmp_path, capsys) -> None:
    input_path = tmp_path / "bars.csv"
    out_path = tmp_path / "evidence.json"
    _write_csv(input_path)
    args = backtest_proposal.build_parser().parse_args(
        [
            "--parameter",
            "analyst.nope",
            "--current",
            "1",
            "--proposed",
            "2",
            "--input",
            str(input_path),
            "--out",
            str(out_path),
        ]
    )

    assert backtest_proposal.run(args) == 0

    assert "no signal builder for analyst.nope" in capsys.readouterr().out
    assert not out_path.exists()


def _bars() -> dict[str, list[tuple[str, float, float]]]:
    return {
        "A": [
            ("2024-01-01", 10.0, 100.0),
            ("2024-01-02", 10.5, 100.0),
            ("2024-01-03", 11.0, 100.0),
            ("2024-01-04", 11.5, 100.0),
            ("2024-01-05", 12.0, 100.0),
            ("2024-01-06", 12.5, 100.0),
            ("2024-01-07", 13.0, 100.0),
            ("2024-01-08", 13.5, 100.0),
        ],
        "B": [
            ("2024-01-01", 10.0, 100.0),
            ("2024-01-02", 9.5, 100.0),
            ("2024-01-03", 9.0, 100.0),
            ("2024-01-04", 8.5, 100.0),
            ("2024-01-05", 8.0, 100.0),
            ("2024-01-06", 7.5, 100.0),
            ("2024-01-07", 7.0, 100.0),
            ("2024-01-08", 6.5, 100.0),
        ],
    }


def _write_csv(path) -> None:
    lines = ["date,ticker,close,volume"]
    for ticker, rows in _bars().items():
        for bar_date, close, volume in rows:
            lines.append(f"{bar_date},{ticker},{close},{volume}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
