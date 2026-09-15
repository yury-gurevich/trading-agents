"""Required contract payload field tests.

Agent: contracts (shared)
Role: prove TYP clauses use literal field names instead of contract files as oracles.
External I/O: none.
"""

from pydantic import BaseModel

import contracts.analyst as analyst
import contracts.curator as curator
import contracts.deliberator as deliberator
import contracts.execution as execution
import contracts.forecaster as forecaster
import contracts.monitor as monitor


def _assert_fields(model: type[BaseModel], names: str) -> None:
    required = tuple(names.split())
    missing = [field for field in required if field not in model.model_fields]
    assert missing == []


def test_analyst_payload_fields_required_by_law() -> None:
    """ANLZ-TYP-01: analyst payload types carry the fields its clauses require."""
    _assert_fields(
        analyst.RecommendationSet,
        "run_id recommendations rejections explanation provenance",
    )
    _assert_fields(
        analyst.Recommendation,
        "ticker action exit_trigger confidence technical_score sentiment_score "
        "fundamental_score suggested_stop_pct suggested_target_pct quant_metrics "
        "stop_target_evidence rationale",
    )
    _assert_fields(
        analyst.StopTargetEvidence,
        "mode counterfactual_mode atr_pct volatility_present volatility_fallback "
        "applied_stop_pct applied_target_pct counterfactual_stop_pct "
        "counterfactual_target_pct flat_stop_pct flat_target_pct scaled_stop_pct "
        "scaled_target_pct",
    )
    _assert_fields(analyst.Rejection, "ticker reason")


def test_curator_payload_fields_required_by_law() -> None:
    """CUR-TYP-01: curator payload types carry the fields its clauses require."""
    _assert_fields(
        curator.DatasetManifest,
        "dataset_id version purpose example_count splits schema_ref "
        "explanation provenance",
    )
    _assert_fields(curator.DatasetSplit, "name example_count")
    _assert_fields(
        curator.PredictorManifest,
        "predictor_id dataset_id purpose target strategy metrics sample_size advisory "
        "promotion_eligible explanation provenance",
    )
    _assert_fields(
        curator.PromotionResult,
        "predictor_id status state reason explanation provenance",
    )


def test_deliberator_bus_payload_fields_required_by_law() -> None:
    """DLIB-TYP-01: deliberator payload types carry the fields its clauses require."""
    _assert_fields(deliberator.DebateProposition, "decision context")
    _assert_fields(deliberator.DebateTurnRecord, "role round text")
    _assert_fields(
        deliberator.DebateTurnRequest,
        "request_id proposition role round_number transcript",
    )
    _assert_fields(deliberator.DebateTurnReply, "request_id turn llm_call_key")
    _assert_fields(deliberator.VerdictRequest, "request_id proposition transcript")
    _assert_fields(deliberator.VerdictReply, "request_id ruling rationale llm_call_key")


def test_execution_payload_fields_required_by_law() -> None:
    """EXEC-TYP-03: execution payload types carry the fields its clauses require."""
    assert execution.CONTRACT.version == "0.4.0"
    _assert_fields(
        execution.ExecutionResult,
        "run_id stage fills submitted rejected dropped skipped provenance",
    )
    _assert_fields(execution.Fill, "ticker side quantity price broker_order_id status")
    _assert_fields(execution.ReconcileResult, "matched discrepancies provenance")
    _assert_fields(execution.StageStatus, "stage idempotent reason")
    _assert_fields(
        execution.PromoteStageResult,
        "accepted previous_stage current_stage reason provenance",
    )


def test_forecaster_payload_fields_required_by_law() -> None:
    """FORE-TYP-01: forecaster payload types carry the fields its clauses require."""
    _assert_fields(
        forecaster.ShadowPrediction,
        "model_id subject_ref value confidence shadow provenance",
    )
    _assert_fields(
        forecaster.Scorecard,
        "model_id metrics sample_size fresh_as_of promotion_eligible",
    )


def test_monitor_payload_fields_required_by_law() -> None:
    """MON-TYP-01: monitor payload types carry the fields its clauses require."""
    _assert_fields(
        monitor.CloseDecisionSet,
        "run_id decisions positions_checked explanation provenance",
    )
    _assert_fields(
        monitor.CloseDecision,
        "ticker position_id decision trigger rationale quantity reference_price_cents "
        "pnl_cents",
    )
