"""Factor mining script helper tests.

Agent: tooling
Role: verify offline factor proposal runs and fail-open selector behavior.
External I/O: temporary CSV/JSON fixtures only.
"""

from __future__ import annotations

import json

from scripts import mine_factors

from contracts.researcher import FactorProposal


def test_manual_factor_run_writes_round_tripped_proposal(tmp_path, capsys) -> None:
    input_path = tmp_path / "bars.csv"
    out_path = tmp_path / "proposal.json"
    _write_csv(input_path)
    args = mine_factors.build_parser().parse_args(
        [
            "--input",
            str(input_path),
            "--out",
            str(out_path),
            "--factor",
            "momentum",
            "--params",
            '{"lookback": 5}',
            "--proposal-id",
            "manual-factor",
        ]
    )

    assert mine_factors.run(args) == 0

    proposal = FactorProposal.model_validate(json.loads(out_path.read_text()))
    assert proposal.proposal_id == "manual-factor"
    assert proposal.factor.name == "momentum"
    assert proposal.backtest is not None
    assert proposal.backtest.n_days > 0
    assert "factor=momentum" in capsys.readouterr().out


def test_fake_llm_path_selects_catalogue_factor(tmp_path) -> None:
    input_path = tmp_path / "bars.csv"
    out_path = tmp_path / "proposal.json"
    _write_csv(input_path)
    args = mine_factors.build_parser().parse_args(
        ["--input", str(input_path), "--out", str(out_path)]
    )

    assert mine_factors.run(args) == 0

    proposal = FactorProposal.model_validate(json.loads(out_path.read_text()))
    assert proposal.factor.name == "momentum"
    assert proposal.factor.params == (("lookback", 20.0),)


def test_off_menu_selection_json_fails_open_without_output(tmp_path, capsys) -> None:
    input_path = tmp_path / "bars.csv"
    out_path = tmp_path / "proposal.json"
    _write_csv(input_path)
    args = mine_factors.build_parser().parse_args(
        [
            "--input",
            str(input_path),
            "--out",
            str(out_path),
            "--selection-json",
            '{"name":"invented","params":{},"rationale":"force guardrail"}',
        ]
    )

    assert mine_factors.run(args) == 0

    assert not out_path.exists()
    assert "no proposal generated" in capsys.readouterr().out


def test_selector_text_rejects_malformed_or_extra_fields() -> None:
    assert mine_factors.selection_from_text("not json") is None
    assert (
        mine_factors.selection_from_text(
            '{"name":"momentum","params":{"lookback":5},'
            '"rationale":"ok","extra":"nope"}'
        )
        is None
    )


def _write_csv(path) -> None:
    lines = ["date,ticker,close,volume"]
    for index in range(1, 26):
        lines.append(f"2024-01-{index:02d},A,{100.0 + index},1000")
        lines.append(f"2024-01-{index:02d},B,{100.0 - index / 2.0},1000")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
