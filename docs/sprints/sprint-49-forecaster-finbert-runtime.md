<!-- Agent: planning | Role: sprint handover -->
# Sprint 49 — Forecaster agent first runtime: FinBERT sentiment shadow scorer (P12)

**Status:** in progress · **Branch:** `sprint-49-forecaster-finbert-runtime` · **Build phase:** P12 (the FinBERT challenger — the reserved forecaster agent's first runtime) · **Effort: L**

## Goal

Stand up the **forecaster agent's first runtime** — the third leg of the sentiment trinity
(ADR-0002). Given a subject ticker, the forecaster requests that ticker's recent headlines from the
**provider** (its only dependency), scores them with a **FinBERT** model held **behind a Protocol**, and
persists a **`ShadowPrediction`** (`shadow=True`, 0–1 sentiment, aligned to the lexicon/provider
challengers) plus its **`Model`** node. It also answers `scorecard(model_id)` with an honest, **never
self-promoting** report. The heavy `torch`/`transformers` dependency is isolated as an **optional group**
and a **lazy import** so the unit gate never touches it (a deterministic `FakeSentimentModel` backs every
test; the real adapter's inference is `# pragma: no cover` + integration-marked).

This implements the existing reserved contract **unchanged** (`contracts/forecaster.py`:
`forecast(ForecastRequest)->ShadowPrediction`, `scorecard(ScorecardRequest)->Scorecard`,
`owns_graph=("ShadowPrediction","Model")`, `depends_on=("provider",)`, `external_io=()`, the three
`never`-clauses). **No contract change, no boundary-map change** (the forecaster is already the 12th
registered agent; this is the first time it gets a runtime).

## Why (context)

- Read first: `docs/decisions/0002-sentiment-champion-challenger.md` (the trinity; FinBERT is the advisory
  shadow leg, *never gates*); `docs/build-plan.md` §P12 ("Forecaster agent (FinBERT, advisory) — the first
  implementation of the reserved forecaster contract … emitting ShadowPredictions … never gates"); memory
  `sentiment-champion-challenger`; `agents/forecaster/mission.md`.
- **Patterns to mirror (read them):**
  - `agents/operator/llm_anthropic.py` — the **lazy-import isolation** of a heavy external lib via
    `importlib.import_module` behind a kernel Protocol (`AnthropicLLMClient`/`LLMClient`). The FinBERT
    adapter copies this shape exactly (no top-level `torch` import; raises `ConfigurationError` if the
    lib is absent).
  - `kernel/llm.py` — `LLMClient` Protocol + `FakeLLMClient`. The forecaster's `SentimentModel` Protocol
    + `FakeSentimentModel` are the analogue.
  - `agents/analyst/provider_client.py::request_market_data` — the bus request to provider with
    `fields=(...)`; the forecaster requests `fields=("news",)`.
  - `agents/analyst/store.py` — `merge_node` / `add_edge` / guarded cross-label edge (`_link_candidate`);
    `agents/analyst/agent.py` — handler + `fault_boundary(reraise=False)` shape.
  - `agents/analyst/tests/helpers.py::wire_analyst` — the provider+agent in-process wiring with a
    `FakeDataSource(news=...)` fixture; `wire_forecaster` is the twin.

## Architecture (the key decision)

**The model lives behind a Protocol; the agent never imports torch.**

```
SentimentModel (Protocol)            domain/sentiment.py (pure, 100% tested)
  score_headlines(headlines)           ModelReading(value, confidence)
    -> tuple[float, ...]               aggregate(scores) -> ModelReading | None
       (per-headline 0-1)              align_label(label, prob) -> float   # FinBERT's reducer
   │                                   │
   ├─ FakeSentimentModel  (gate)       └─ used by both Fake and FinBERT
   └─ FinBERTModel        (finbert.py: lazy torch/transformers import, inference # pragma: no cover)
```

- `value` is **0–1 aligned** (same scale as the lexicon champion and the provider challenger), so the
  three readings are directly comparable when the scorecard harness lands (next sprint).
- A forecast with **no usable headlines** returns a *neutral, zero-confidence* shadow prediction
  (`value=0.5, confidence=0.0`), not a fault — "no signal" is a valid shadow result.

## Parts

- **A — `agents/forecaster/domain/sentiment.py`** (pure): `ModelReading` (frozen dataclass:
  `value: float`, `confidence: float`); `aggregate(scores: tuple[float, ...]) -> ModelReading | None`
  (None on empty; else `value = mean(scores)`, `confidence = min(len/​max_for_full_confidence, 1.0)` via a
  tunable passed in or a domain constant — keep the dispersion-free count rule, justified);
  `align_label(label: str, probability: float) -> float` (FinBERT's `positive→0.5+0.5p`,
  `negative→0.5-0.5p`, else `0.5`). Known-value unit tests.
- **B — `agents/forecaster/model.py`**: `SentimentModel` Protocol (`score_headlines(headlines) ->
  tuple[float, ...]`, per-headline 0–1, `# pragma: no cover` on the `...`); `FakeSentimentModel`
  deterministic — constructor takes `per_headline: dict[str, float] | None` and `default: float = 0.5`;
  returns `per_headline.get(h, default)` for each headline. (Lets a test pin an exact aggregate.)
- **C — `agents/forecaster/finbert.py`**: `FinBERTModel` — `__init__` lazy-imports `transformers`
  (`importlib`), builds the sentiment pipeline (`model_ref` default `"ProsusAI/finbert"`), raising
  `ConfigurationError` if absent; `score_headlines` runs the pipeline then maps each result through
  `align_label`. The pipeline call + construction are `# pragma: no cover` (integration-only); keep the
  module tiny so nothing untested hides in it.
- **D — `agents/forecaster/provider_client.py`**: `request_news(bus, sink, ticker, window) ->
  dict[str, tuple[str, ...]]` — bus request to provider `get_market_data` with `fields=("news",)`,
  `fault_boundary(reraise=False)`, returns `{}` on fault. Mirror analyst's helper.
- **E — `agents/forecaster/store.py`**: `write_forecast(graph, *, model_id, model_ref, subject_kind,
  subject_ref, reading) -> Provenance` — merge `Model` (key `model_id`; props `ref`, `kind="sentiment"`,
  `created_at`), merge `ShadowPrediction` (key `f"{model_id}:{subject_ref}:{run_id}"`; props `subject_ref`,
  `value`, `confidence`, `shadow=True`, `model_id`), edge `Model -[:PREDICTED]-> ShadowPrediction`, and a
  **guarded** `ShadowPrediction -[:ADVISES]-> subject` (look up `get_node({Recommendation|Position},
  subject_ref)`; link only if present). `read_predictions(graph, model_id) -> tuple[Node, ...]` for the
  scorecard (filter `list_nodes("ShadowPrediction")` by `model_id`).
- **F — `agents/forecaster/settings.py`**: `ForecasterSettings(env_prefix="FORECASTER_", frozen=True)` —
  `model_id` (str, default `"finbert-sentiment"`), `model_ref` (str, default `"ProsusAI/finbert"`),
  `news_lookback_days` (tunable, e.g. 7), `headlines_for_full_confidence` (tunable, e.g. 5). Justified
  tunables, bounded.
- **G — `agents/forecaster/agent.py`**: `ForecasterAgent(AgentBase)` with `__init__(bus, *, graph,
  model: SentimentModel | None=None, settings=None, sink=None)` (defaults `FakeSentimentModel()`),
  `handlers={"forecast": ..., "scorecard": ...}`:
  - `forecast`: validate `ForecastRequest`; request news for `subject_ref` (the ticker) from provider;
    `scores = model.score_headlines(headlines)`; `reading = aggregate(scores)` or the neutral fallback;
    `write_forecast(...)`; return `ShadowPrediction(model_id, subject_ref, value, confidence, shadow=True,
    provenance)`. Wrap the model call in a `fault_boundary(reraise=False)`; on fault return the
    neutral, zero-confidence shadow prediction (still shadow, never a hard error to callers).
  - `scorecard`: validate `ScorecardRequest`; `preds = read_predictions(graph, model_id)`; return
    `Scorecard(model_id, metrics={"mean_value": ..., "mean_confidence": ...}, sample_size=len(preds),
    fresh_as_of=now, promotion_eligible=False)`. **Always `promotion_eligible=False`** — no forward-return
    evidence exists yet, and the agent must never self-promote (the scorecard *harness* is the next sprint).
- **H — `agents/forecaster/__init__.py`**: export `ForecasterAgent` (keep the charter docstring).
- **I — `pyproject.toml`**: add an optional group `forecaster = ["torch>=2", "transformers>=4"]`
  (NOT in `dev`; the gate never installs it). Add `torch`/`transformers` to the mypy
  `ignore_missing_imports` override only if needed (the `importlib` path returns `Any`, like
  `anthropic`, so likely no override is required — verify with `mypy`).

## Part T — Tests (every branch; 100% floor holds)

- `agents/forecaster/tests/helpers.py`: `wire_forecaster(*, news=None, model=None, register_provider=True,
  fail_news=False) -> (bus, graph, sink)` — Provider(FakeDataSource(news=...)) + ForecasterAgent, mirror
  `wire_analyst`. A `forecast_message(subject_ref, ...)` / `scorecard_message(model_id)` builder.
- `test_forecaster_domain.py`: `aggregate` known values (mean; empty→None; confidence saturates at the
  full-confidence count); `align_label` for positive/negative/neutral.
- `test_forecaster_model.py`: `FakeSentimentModel` returns `default` and per-headline overrides
  deterministically.
- `test_forecaster_store.py`: `write_forecast` persists `Model` + `ShadowPrediction` (props incl.
  `shadow=True`), the `PREDICTED` edge; **ADVISES present** when a `Recommendation` subject node exists
  and **absent** when it does not (both branches).
- `test_forecaster_agent.py`: end-to-end via `wire_forecaster(news={"AAPL": (...)}, model=FakeSentiment
  Model(per_headline={...}))` → response is a `ShadowPrediction` with the expected `value`/`confidence`,
  `shadow is True`, persisted node present; **no-news** path → neutral `0.5`/`0.0`; **provider-fault** path
  (`fail_news=True`) → still a shadow prediction (degraded, not an error); **model-fault** path (a stub
  model whose `score_headlines` raises) → neutral fallback, fault recorded on the sink; `scorecard` after
  N forecasts → `sample_size==N`, `promotion_eligible is False`.
- `test_forecaster_boundary.py`: the **never-clause** — every `forecast` response has `shadow is True`;
  `scorecard.promotion_eligible is False` regardless of inputs (the agent cannot self-promote). Assert the
  contract still declares the three `never` items and `external_io == ()`.

## Acceptance criteria

- `ForecasterAgent` answers `forecast` and `scorecard` over the in-process bus; `forecast` persists a
  `ShadowPrediction` (`shadow=True`, 0–1 value aligned to the other scorers) and its `Model`, linked
  `Model -[:PREDICTED]-> ShadowPrediction` (+ guarded `ADVISES` to the subject).
- **Never gates / never self-promotes:** every prediction is `shadow=True`; `promotion_eligible` is always
  `False`. The torch/transformers dependency is optional + lazy — the unit gate imports neither (a single
  `uv run python -c "import agents.forecaster.agent"` must not pull in torch).
- No contract change (forecaster `0.1.0`); boundary meta-test green. `make ci` green at floor **100.00**;
  every module **< 200 lines**.

## Out of scope (the rest of P12 / P13)

- The **relationship & scorecard harness** (align lexicon/provider/FinBERT readings vs **forward returns**;
  regression + incremental IC; promotion through the **P10 predictor registry**) — its own sprint, and it
  needs the live news-accrual runway (ADR-0002; the v1 Postgres has returns but **no news history**).
- **Wiring FinBERT into the analyst's run / the daily loop** — the forecaster stays invoked-on-demand here;
  no `orchestration/bindings.py` or dispatcher change.
- Actually downloading/running FinBERT weights in CI (integration-marked, skipped without `torch`).

## Handback report (paste into PR / reply)

- Confirm: no contract/boundary change; the gate does not import torch (show the import check); how the
  model is isolated (Protocol + lazy adapter); every `forecast` is `shadow=True` and `scorecard` is never
  promotion-eligible. New module line counts; coverage % + floor; total test count.

After merge: the only P12 leg left is the **scorecard harness** (blocked on the news-accrual runway), plus
the still-owed **full Loughran–McDonald master dictionary** (champion upgrade).
