"""Required contract field tests.

Agent: contracts (shared)
Role: prove TYP clauses use literal field names instead of contract files as oracles.
External I/O: none.
"""

from enum import StrEnum

from pydantic import BaseModel

import contracts.master as master
import contracts.operator as operator
import contracts.reporter as reporter
import contracts.researcher as researcher
import contracts.scanner as scanner
import contracts.supervisor as supervisor
from contracts.common import _Frozen


def _assert_fields(model: type[BaseModel], names: str) -> None:
    required = tuple(names.split())
    missing = [field for field in required if field not in model.model_fields]
    assert missing == []


def test_master_payload_fields_required_by_law() -> None:
    """MST-TYP-01: master payload types carry the fields its clauses require."""
    _assert_fields(
        master.EHLOMessage,
        "ephemeral_boot_id agent_type capability_declaration",
    )
    _assert_fields(
        master.ACTIVATEMessage,
        "instance_id agent_type capability_grants config signature",
    )
    _assert_fields(master.DRAINMessage, "instance_id reason")
    message_types = (master.EHLOMessage, master.ACTIVATEMessage, master.DRAINMessage)
    for message_type in message_types:
        assert issubclass(message_type, _Frozen)
    assert issubclass(master.AgentState, StrEnum)


def test_operator_payload_fields_required_by_law() -> None:
    """OPR-TYP-01: operator payload types carry the fields its clauses require."""
    _assert_fields(operator.CommandResult, "outcome intent message")
    _assert_fields(
        operator.TypedIntent,
        "family parameters requires_confirmation provenance",
    )
    _assert_fields(operator.HumanCommand, "text actor channel request_id")


def test_reporter_payload_fields_required_by_law() -> None:
    """RPT-TYP-01: reporter payload types carry the fields its clauses require."""
    _assert_fields(
        reporter.RunSnapshot,
        "run_id portfolio_metrics signal_metrics regime_attribution headline "
        "provenance",
    )
    _assert_fields(reporter.TradeNarrative, "position_id story provenance")


def test_researcher_payload_fields_required_by_law() -> None:
    """RES-TYP-01: researcher payload types carry the fields its clauses require."""
    _assert_fields(
        researcher.ParameterChangeProposal,
        "proposal_id changes rationale provenance backtest",
    )
    _assert_fields(
        researcher.ProposedChange,
        "parameter current_value proposed_value evidence_window_days expected_effect",
    )
    _assert_fields(
        researcher.BacktestEvidence,
        "sharpe ic_mean max_drawdown turnover n_days window_start window_end "
        "holdout_sharpe holdout_ic_mean slippage_bps engine",
    )


def test_scanner_payload_fields_required_by_law() -> None:
    """SCAN-TYP-01: scanner payload types carry the fields its clauses require."""
    assert scanner.CONTRACT.version == "0.2.1"
    _assert_fields(
        scanner.CandidateSet,
        "run_id candidates filter_trace explanation provenance",
    )
    _assert_fields(
        scanner.Candidate,
        "ticker rank score survived_filters skipped_filters metrics",
    )
    _assert_fields(
        scanner.FilterTrace,
        "universe_size evaluated dropped_by_filter verdicts",
    )
    _assert_fields(
        scanner.FilterVerdict,
        "ticker decision filter_fired skipped_filters features bypassed",
    )


def test_supervisor_payload_fields_required_by_law() -> None:
    """SUP-TYP-01: supervisor payload types carry the fields its clauses require."""
    _assert_fields(supervisor.DispatchResult, "accepted routed_to rejection provenance")
    _assert_fields(
        supervisor.MasterReport,
        "healthy open_incidents pending_human_flags last_successful_run summary "
        "provenance",
    )
    _assert_fields(
        operator.TypedIntent,
        "family parameters requires_confirmation provenance",
    )
    _assert_fields(supervisor.FlagRequest, "subject_ref severity reason")
