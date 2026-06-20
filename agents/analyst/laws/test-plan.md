# Analyst — Test plan (living)

Each row pins one law-ID to a **functional test** that proves it. This document is the
**master**: discovering a needed test with no law → add the law to `laws.md` first,
then add a row here. A test's docstring **must cite the law-ID** it proves (conventions §7).

Status: ⬜ gray (no passing test) · 🟩 green (≥1 passing test cites the ID)

**Precondition:** `DEP-BUS, DEP-NEO4J` must be green first (see `docs/laws/dependencies.md`).

## Inputs / triggers

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| ANLZ-IN-01 | Valid CandidateSet accepted; all candidates scored. | happy | `test_analyst_agent.py::test_analyze_returns_recommendation_with_rationale_and_provenance` | 🟩 |
| ANLZ-IN-02 | scan.candidates.ready claim-check resolved before analyze. | pub/sub | `test_analyst_pubsub.py::test_candidates_ready_triggers_recommendations_ready` | 🟩 |
| ANLZ-IN-03 | Empty CandidateSet → empty RecommendationSet; no provider calls. | boundary | `test_analyst_agent.py::test_empty_candidate_set_returns_explainable_silence` | 🟩 |
| ANLZ-TRG-01 | RPC analyze returns a RecommendationSet to the caller. | happy | `test_analyst_agent.py::test_analyze_returns_recommendation_with_rationale_and_provenance` | 🟩 |
| ANLZ-TRG-02 | scan.candidates.ready → analyze → analysis.recommendations.ready emitted. | pub/sub | `test_analyst_pubsub.py::test_candidates_ready_triggers_recommendations_ready` | 🟩 |
| ANLZ-TRG-03 | Idle → zero provider calls, zero graph writes. | negative | _tbd_ | ⬜ |

## Outputs

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| ANLZ-OUT-01 | RecommendationSet always returned; every candidate accounted for. | happy | `test_analyst_agent.py::test_analyze_returns_recommendation_with_rationale_and_provenance` | 🟩 |
| ANLZ-OUT-02 | Each Recommendation carries confidence ∈ [0,1] + scores + rationale. | schema | `test_analyst_agent.py::test_analyze_returns_recommendation_with_rationale_and_provenance` | 🟩 |
| ANLZ-OUT-03 | Below-gate candidate lands in rejections with reason string. | gate | `test_analyst_agent.py::test_low_confidence_candidate_becomes_rejection` | 🟩 |
| ANLZ-OUT-04 | Provider degraded → empty RecommendationSet + incident_refs + fault. | degraded | `test_analyst_agent.py::test_degraded_market_data_returns_explained_rejection` | 🟩 |
| ANLZ-OUT-05 | Pub/sub event carries claim-check ref only, not RecommendationSet payload. | pub/sub | `test_analyst_pubsub.py::test_candidates_ready_triggers_recommendations_ready` | 🟩 |
| ANLZ-OUT-06 | SentimentReading node persisted for every scored ticker. | append-only | `test_analyst_agent.py::test_recommendation_carries_sentiment_score_when_present` | 🟩 |

## Prohibitions

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| ANLZ-NEV-01 | No quantity, price, or dollar amount in any Recommendation field. | schema | `test_analyst_agent.py::test_empty_candidate_set_returns_explainable_silence` | 🟩 |
| ANLZ-NEV-02 | Analyst never calls a data API directly; all via provider bus call. | boundary | `test_analyst_agent.py::test_analyze_returns_recommendation_with_rationale_and_provenance` | 🟩 |
| ANLZ-NEV-03 | Candidate below regime floor always rejected; never recommended. | gate | `test_analyst_agent.py::test_low_confidence_candidate_becomes_rejection` | 🟩 |
| ANLZ-NEV-05 | SentimentReading.scorer ∈ {"lexicon", "provider"}; never omitted. | schema | `test_analyst_agent.py::test_recommendation_carries_sentiment_score_when_present` | 🟩 |

## State & effects

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| ANLZ-STA-01 | Two consecutive analyze calls produce independent results. | stateless | _tbd_ | ⬜ |
| ANLZ-STA-02 | analyze writes AnalystRun + Recommendation/Rejection nodes; append-only. | append-only | `test_analyst_pubsub.py::test_recommendation_result_node_in_graph` | 🟩 |
| ANLZ-STA-03 | Two runs for same ticker produce two separate SentimentReading nodes. | append-only | _tbd_ | ⬜ |

## Determinism & idempotency

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| ANLZ-IDM-01 | Same CandidateSet + MarketData + settings → same RecommendationSet. | determinism | _tbd_ | ⬜ |
| ANLZ-IDM-02 | run_id threaded from CandidateSet to recommendations.ready event. | provenance | `test_analyst_pubsub.py::test_run_id_propagated_in_ready_event` | 🟩 |

## Failure & recovery

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| ANLZ-FAIL-01 | Provider unavailable → empty RecommendationSet + fault; no exception. | fault | `test_analyst_agent.py::test_degraded_market_data_returns_explained_rejection` | 🟩 |
| ANLZ-FAIL-02 | Provider returns degraded data → fault; degraded data not scored. | degraded | `test_analyst_agent.py::test_degraded_market_data_returns_explained_rejection` | 🟩 |
| ANLZ-FAIL-03 | Per-candidate scoring error → that candidate rejected; others proceed. | partial | `test_analyst_agent.py::test_scoring_failure_returns_explained_rejection` | 🟩 |
| ANLZ-FAIL-04 | Sentiment scoring failure → SentimentReading absent; other scores OK. | degraded | _tbd_ | ⬜ |

## Type alignment

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| ANLZ-TYP-01 | Recommendation.confidence ∈ [0.0, 1.0]; never fabricated above 1.0. | schema | `test_analyst_pubsub.py::test_recommendation_result_is_deserializable` | 🟩 |
| ANLZ-TYP-02 | suggested_stop_pct < suggested_target_pct when both present; never inverted. | schema | _tbd_ | ⬜ |
| ANLZ-TYP-03 | SentimentReading.scorer ∈ {"lexicon", "provider"}; never omitted. | schema | `test_analyst_agent.py::test_recommendation_carries_sentiment_score_when_present` | 🟩 |

## Security

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| ANLZ-SEC-02 | Unauthorized caller is refused by the capability gate. | authz | _tbd_ | ⬜ |

## Observability

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| ANLZ-OBS-01 | AnalystRun node contains full score breakdown and is reconstructable. | audit | `test_analyst_pubsub.py::test_recommendation_result_node_in_graph` | 🟩 |
| ANLZ-OBS-02 | Faults routed to central channel; degraded path not silent. | observable | `test_analyst_agent.py::test_degraded_market_data_returns_explained_rejection` | 🟩 |
