<!-- Agent: planning | Role: sprint handover -->
# Sprint 58 — Forecaster: LightGBM price/return shadow signal (qlib Phase Q1)

**Status:** active (2026-06-19) · **Branch:** `sprint-58-forecaster-lightgbm-shadow` · **Build phase:** qlib Phase Q1 (research [R001](../research/qlib-integration/qlib-integration.md)) · **Effort: M**

## The two decisions that shape this sprint (read first)

1. **`lightgbm` directly, NOT `pyqlib`.** R001's headline entry path was `pip install pyqlib`.
   That is **impossible on this workspace** — `pyqlib` ships wheels only for `cp38…cp312`; this repo
   pins `requires-python = ">=3.13"`. Verified with the project toolchain:

   ```text
   $ uv pip install --dry-run pyqlib
   × No solution found … pyqlib has no wheels with a matching Python ABI tag (cp313);
     we only found wheels for cp38, cp39, cp310, cp311, cp312.

   $ uv pip install --dry-run lightgbm
   Resolved 3 packages … + lightgbm==4.6.0 + numpy + scipy
   ```

   Qlib's `LGBModel` is a thin wrapper over the standalone `lightgbm` package. We depend on
   **`lightgbm` directly** behind our own port — cleaner than R001's own fallback (vendoring qlib
   source), and it drops the qlib/Cython-on-3.13 build problem entirely. No `qlib`/`pyqlib` import
   appears anywhere.

2. **Runtime now (S58); trained artifact + live IC scorecard next (S59).** This sprint stands up the
   *runtime* — the model port, the lazy `lightgbm` adapter, the pure feature builder, the provider
   OHLCV request, persistence, and the never-gates wiring — exactly as **S49 stood up the FinBERT
   runtime** before **S57** built the scorecard. Producing the trained booster (offline training on
   `price_cache` with forward-return labels + walk-forward/no-lookahead validation) and the
   price-return IC scorecard is its **own sprint (S59)**, because doing it with the rigor the project
   (and R001's risk register) demand is not a 2–3 day side-task. The unit gate runs against a
   deterministic `FakeReturnModel`; the real adapter is integration-marked + `# pragma: no cover`.

## Goal

Add a **second shadow signal** to the forecaster: a gradient-boosted **price/return** predictor that
works on OHLCV features (complementary to FinBERT, which works on text). Given a subject ticker, the
forecaster requests that ticker's recent **OHLCV** from the **provider** (its only dependency), builds
a small deterministic feature row, scores it with a **`lightgbm` booster held behind a Protocol**, and
persists a **`ShadowPrediction`** (`shadow=True`, value on the shared 0–1 scale) plus its **`Model`**
node (`kind="return"`). It is governed by the same P10 predictor-registry gate as FinBERT and **never
gates a decision**.

## Why (context)

- Read first: [R001 qlib integration](../research/qlib-integration/qlib-integration.md) §"forecaster — Primary target"
  - §"For Coding Agents" (the 7 invariants — all still bind verbatim; only the import source changed
  from `qlib.model.gbdt.LGBModel` to `lightgbm`); `docs/decisions/0002-sentiment-champion-challenger.md`
  (ADR-0002 explicitly anticipated **N** shadow challengers behind the forecaster boundary — this is
  challenger #4); `agents/forecaster/mission.md`.
- **Pattern to mirror one-to-one: [Sprint 49](sprint-49-forecaster-finbert-runtime.md).** This sprint
  is the price/return twin of the FinBERT runtime. Read S49, then map: `transformers`→`lightgbm`,
  headlines→OHLCV features, `align_label`→`squash`, `SentimentModel`→`ReturnModel`,
  `FinBERTModel`→`LightGBMModel`, `request_news`→`request_prices`.
- Patterns also worth re-reading: `agents/forecaster/finbert.py` (lazy `importlib` isolation of a heavy
  lib behind a port + `ConfigurationError`); `agents/analyst/domain/` pure-Python indicators
  (S30–33 — features stay **pure Python, no numpy**); `agents/forecaster/store.py::write_forecast`
  (already generic — reused, one additive param).

## Architecture (the key decision)

**The booster lives behind a Protocol; the agent (and the unit gate) never imports lightgbm/numpy.**

```text
ReturnModel (Protocol)                 domain/features.py   (pure Python, 100% tested)
  predict(features) -> float             FeatureRow(frozen): trailing returns / vol / momentum
   │   (raw expected-return score)        build_features(ohlcv, as_of) -> FeatureRow | None
   │                                      squash(raw, scale) -> float    # → shared 0–1 scale
   ├─ FakeReturnModel   (gate)
   └─ LightGBMModel     (lightgbm_model.py: lazy lightgbm import, loads booster artifact,
                          predict() integration-only + # pragma: no cover)
```

- `value` is squashed to **0–1** (same scale as the three sentiment scorers) so every shadow reading
  stays directly comparable when the S59 IC scorecard lands.
- **No usable history** (too few bars to build a feature row) → a *neutral, zero-confidence* shadow
  prediction (`value=0.5, confidence=0.0`), not a fault — "no signal" is a valid shadow result
  (mirrors S49's no-headlines path).

## Parts

- **A — `agents/forecaster/domain/features.py`** (pure, no heavy deps): `FeatureRow` (frozen dataclass);
  `build_features(closes: tuple[float, ...], volumes: tuple[float, ...] | None, *, horizons) ->
  FeatureRow | None` — a *small* justified set (trailing returns at e.g. 1/5/20d, realized vol = std of
  returns, momentum = last/SMA-N, volume ratio); **no lookahead** (uses only bars up to as-of); `None`
  on insufficient history. `squash(raw: float, scale: float) -> float` (logistic → 0–1). Known-value
  unit tests. **NOT Alpha158** — that breadth is Phase Q2, a later sprint.
- **B — `agents/forecaster/return_model.py`**: `ReturnModel` Protocol (`predict(features: FeatureRow)
  -> float`, `# pragma: no cover` on the `...`); `FakeReturnModel` deterministic — constructor takes a
  canned `per_key: dict | None` / fixed `default`, returns a deterministic score (lets a test pin an
  exact squashed value).
- **C — `agents/forecaster/lightgbm_model.py`**: `LightGBMModel` — `__init__` lazy-imports `lightgbm`
  (`importlib`), loads a trained booster from `model_path` (`lightgbm.Booster(model_file=...)`), raising
  `ConfigurationError` if the lib is absent or the artifact is missing; `predict` builds the feature
  vector in the booster's order and returns `float(booster.predict([...])[0])`. Construction + inference
  are `# pragma: no cover` (integration-only). Keep the module tiny — nothing untested hides in it.
- **D — `agents/forecaster/provider_client.py`** (extend): `request_prices(bus, sink, ticker, window)
  -> dict[str, OHLCV]` — bus request to provider `get_market_data` with `fields=("ohlcv",)`,
  `fault_boundary(reraise=False)`, returns `{}` on fault. Twin of the existing `request_news`.
- **E — `agents/forecaster/store.py`** (one additive param): `write_forecast(...)` gains
  `model_kind: str = "sentiment"` and writes it as the `Model` node's `kind` prop (currently hard-coded
  `"sentiment"`). Default preserves every existing caller → **no re-pin**. The return model passes
  `model_kind="return"`.
- **F — `agents/forecaster/settings.py`** (extend): `return_model_id` (default `"lgbm-return-v1"`),
  `return_model_path` (artifact path, the External-I/O input), `price_lookback_days` (tunable, enough
  for the longest feature horizon, e.g. 60), feature `horizons` + `squash_scale` (justified tunables,
  bounded).
- **G — `agents/forecaster/agent.py`** (add a capability): new handler `"forecast_return"` —
  validate the request; `request_prices(subject_ref)`; `build_features(...)`; `model.predict(...)`
  wrapped in `fault_boundary(reraise=False)`; `squash` → `ShadowPrediction(model_id=return_model_id,
  value, confidence, shadow=True, provenance)` via `write_forecast(..., model_kind="return")`. On fault
  **or** insufficient history → neutral `0.5`/`0.0` shadow (never a hard error to callers). The generic
  `scorecard(model_id)` handler already serves this model's predictions unchanged.
- **H — `contracts/forecaster.py`** (capability add → version bump): add `forecast_return` to the
  declared capabilities (reuse `ForecastRequest`/`ShadowPrediction` — `subject_kind`/`subject_ref` carry
  the ticker; **no new message type if the existing shapes fit** — verify first). **CONTRACT
  `0.2.0 → 0.3.0`**; `owns_graph` unchanged (still `ShadowPrediction`, `Model`); `depends_on` unchanged
  (already `provider`); `external_io` unchanged (the artifact loads behind the injected port, as FinBERT
  did). Confirm the boundary meta-test stays green.
- **I — `pyproject.toml`**: extend the existing optional group →
  `forecaster = ["torch>=2.12.1", "transformers>=4", "lightgbm>=4"]` (NOT in `dev`; the gate never
  installs it). mypy is already global `ignore_missing_imports = true` → no per-package override.

## Part T — Tests (every branch; 100% floor holds)

- `agents/forecaster/tests/helpers.py`: extend `wire_forecaster(...)` to seed provider OHLCV +
  inject a `FakeReturnModel`; a `forecast_return_message(subject_ref)` builder.
- `test_forecaster_features.py`: `build_features` known values (returns/vol/momentum); `None` on short
  history; `squash` monotone + endpoints (0.5 at raw 0).
- `test_forecaster_return_model.py`: `FakeReturnModel` deterministic default + per-key overrides.
- `test_forecaster_store.py` (extend): `write_forecast(model_kind="return")` writes `Model.kind ==
  "return"`; the `"sentiment"` default branch unchanged.
- `test_forecaster_agent.py` (extend): end-to-end via `wire_forecaster(ohlcv={...},
  model=FakeReturnModel(...))` → `ShadowPrediction` with the expected squashed `value`, `shadow is
  True`, node persisted; **short-history** → neutral `0.5`/`0.0`; **provider-fault** → still a shadow
  (degraded); **model-fault** (stub raising in `predict`) → neutral fallback + fault on the sink.
- `test_forecaster_boundary.py` (extend): the never-clause holds for `forecast_return` too — every
  response `shadow is True`; `scorecard.promotion_eligible is False`; assert `external_io == ()`.
- One integration-marked test constructs `LightGBMModel` against a tiny fixture booster (skipped when
  `lightgbm` is absent); the unit gate must import neither lightgbm nor numpy
  (`uv run python -c "import agents.forecaster.agent"` pulls in neither — assert as in S49).

## Acceptance criteria

- `ForecasterAgent` answers `forecast_return` over the in-process bus and persists a `ShadowPrediction`
  (`shadow=True`, 0–1 value) + its `Model` (`kind="return"`), linked `Model -[:PREDICTED]->
  ShadowPrediction` (+ guarded `ADVISES`).
- **Never gates / never self-promotes:** every prediction `shadow=True`; `scorecard.promotion_eligible`
  always `False`. `lightgbm`/`numpy` are optional + lazy — the unit gate imports neither.
- CONTRACT `0.2.0 → 0.3.0`; boundary meta-test green. `feat` → **project version `0.6.0 → 0.7.0`**
  (MINOR, HARD RULE). `make ci` green at floor **100.00**; every module **< 200 lines**.

## Out of scope (→ Sprint 59)

- **Training the booster** on `price_cache`: feature/forward-return label construction, walk-forward /
  no-lookahead split (R001 risk register: in-sample ≤ 70%, out-of-sample ≥ 30%), writing the
  `return_model_path` artifact. This produces the *real* predictions.
- **The price-return IC scorecard** (track the LightGBM `ShadowPrediction`s' information coefficient
  against `price_cache` forward returns; surface via the P10 predictor registry). Unlike P12's sentiment
  scorecard, this is **not blocked on a news runway** — `price_cache` (629,823 rows, 507 tickers) already
  has the OHLCV/returns needed, so S59 can produce a real verdict immediately.
- **Wiring `forecast_return` into the daily loop / dispatcher** — the forecaster stays invoked-on-demand
  here (no `orchestration/bindings.py` change), as in S49.

## Handback report (paste into PR / reply)

- Confirm: CONTRACT `0.2.0 → 0.3.0`, `owns_graph`/`external_io` unchanged, boundary meta-test green; the
  gate imports neither lightgbm nor numpy (show the import check); model isolated behind `ReturnModel`
  Protocol + lazy adapter; every response `shadow=True`, scorecard never promotion-eligible. New module
  line counts; coverage % + floor; total test count; project version `0.6.0 → 0.7.0`.

After merge: **S59** (booster training on `price_cache` + price-return IC scorecard) turns this runtime
into a real, measured signal. Then resume **P14** (inter-agent comms re-architecture, ADR-0005).
