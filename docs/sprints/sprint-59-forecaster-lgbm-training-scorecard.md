<!-- Agent: planning | Role: sprint handover -->
# Sprint 59 — Forecaster: LightGBM booster training + price-return IC scorecard

**Status:** active (2026-06-19) · **Branch:** `sprint-58-forecaster-lightgbm-shadow`
**Build phase:** qlib Phase Q1 follow-on · **Effort: M**
**Prerequisite:** S58 shipped (forecaster `forecast_return` runtime in place).

## Goal

Two deliverables that turn S58's **runtime** (a wired-up model port) into a **measured signal**:

1. **Offline training pipeline** — pure-Python label builder + lazy LightGBM trainer;
   a CLI script reads a `price_cache` CSV export, builds feature/label pairs with
   walk-forward split, trains the booster, saves `models/lgbm-return-v1.txt`.
2. **`return_scorecard` capability** — the forecaster aligns its `ShadowPrediction`
   nodes (from `forecast_return` calls) against injected forward returns and reports
   IC, hit rate, and directional breakdown; never promotion-eligible.

Unlike the sentiment scorecard (data-runway-gated), this scorecard is **immediately
usable**: `price_cache` (629,823 rows, 507 tickers, 2021-04 → 2026-05) already holds
the OHLCV + forward-return side.

## Context

- Pattern to follow: [Sprint 57](sprint-57-forecaster-sentiment-scorecard.md) (the
  sentiment scorecard) for the capability structure; all 7 invariants in
  [R001](../research/qlib-integration.md) §"For Coding Agents" still bind verbatim.
- The S58 `build_features` + `FeatureRow` are reused as-is; no changes to them.
- `pyqlib` is still uninstallable on 3.13; lightgbm is accessed via `importlib` as
  in S58 `LightGBMModel`.
- Scorecard keys `forward_returns` by `subject_ref` (ticker string), exactly as
  `sentiment_scorecard` keys by `{analyst_run_id}:{ticker}`.
- `split_rows` (walk-forward split) and `TrainingReport` are pure Python and fully
  tested. The `train_and_save` function itself is `# pragma: no cover` (requires the
  optional `lightgbm` dep and a real dataset — like `LightGBMModel.predict`).

## Parts

### A — `agents/forecaster/domain/return_labels.py` (pure, no heavy deps)

```python
@dataclass(frozen=True)
class LabelRow:
    ticker: str
    as_of_date: str          # ISO "YYYY-MM-DD"; used for walk-forward sort/split
    features: FeatureRow
    forward_return: float

def build_label_rows(
    ticker_bars: dict[str, list[tuple[str, float, float]]],
    # {ticker: [(date_iso, close, volume), ...]}  date-ascending
    *,
    forward_days: int,
    horizons: tuple[int, int, int],
    volatility_window: int,
    momentum_window: int,
) -> list[LabelRow]:
```

For each ticker, for each index `i` where `build_features` returns a row **and**
`i + forward_days < len(bars)`:

- `forward_return = closes[i + forward_days] / closes[i] - 1.0`
- Append `LabelRow(ticker, date_at_i, features, forward_return)`.

No lookahead: features use only `closes[:i+1]`, forward return uses only the
`+forward_days` bar (a future fact, only available offline). Returns `[]` if empty.

### B — `agents/forecaster/domain/return_scorecard.py` (pure IC math + graph read)

```python
@dataclass(frozen=True)
class ReturnObservation:
    subject_ref: str
    predicted: float     # squashed 0-1 from ShadowPrediction.value
    forward_return: float

def build_return_observations(graph, model_id, forward_returns) -> list[ReturnObservation]
def return_scorecard_metrics(observations) -> dict[str, float]
```

`build_return_observations`: reads `ShadowPrediction` nodes for `model_id`, inner-joins
with `forward_returns` by `subject_ref`. Skips refs present only on one side.

`return_scorecard_metrics` emits (all omitted when undefined):

| Key | Definition |
| --- | --- |
| `complete_cases` | number of aligned observations |
| `ic` | Pearson(predicted, forward_return); `None`→omitted when < 2 |
| `hit_rate` | fraction where `sign(predicted − 0.5) × forward_return > 0` |
| `mean_up_pred` | mean predicted value on days with `forward_return > 0`; omitted if none |
| `mean_down_pred` | mean predicted value on days with `forward_return ≤ 0`; omitted if none |

Reuses `pearson` from `agents.forecaster.domain.statistics` (already in-tree).

### C — `agents/forecaster/model_trainer.py` (split + training; lazy lightgbm)

```python
@dataclass(frozen=True)
class TrainingReport:
    train_size: int
    test_size: int
    oos_ic: float | None   # None when test set < 2 rows

def split_rows(rows: list[LabelRow], *, train_fraction: float
               ) -> tuple[list[LabelRow], list[LabelRow]]:
    """Sort by as_of_date, split at train_fraction. Fully tested (pure)."""

def train_and_save(  # pragma: no cover
    label_rows: list[LabelRow],
    output_path: str,
    *,
    train_fraction: float = 0.7,
    forward_days: int = 5,
) -> TrainingReport:
    """Load lightgbm via importlib; train on train split; save booster; return OOS IC."""
```

LightGBM params: `{"objective": "regression", "metric": "mae", "verbosity": -1,
"num_leaves": 31, "num_boost_round": 100}`.  Feature column names from
`FeatureRow.as_vector()` order: `ret_short`, `ret_mid`, `ret_long`, `volatility`,
`momentum`, `volume_ratio`.

### D — `scripts/train_lgbm_return.py` (offline CLI; not in coverage source)

```text
Usage:
  python scripts/train_lgbm_return.py \
    --input price_cache.csv \           # CSV: date,ticker,open,high,low,close,volume
    --output models/lgbm-return-v1.txt \ # booster artifact path (default)
    --forward-days 5 \                  # forward-return horizon (default 5)
    --train-fraction 0.7                # walk-forward train/test split (default 0.7)
```

Reads CSV, constructs `{ticker: [(date, close, vol), ...]}`, calls
`build_label_rows(...)`, then `train_and_save(...)`, prints `TrainingReport`.

Getting the CSV from Postgres:

```sql
COPY (SELECT date::text, ticker, close, volume FROM price_cache ORDER BY ticker, date)
  TO '/tmp/price_cache.csv' WITH CSV HEADER;
```

### E — `contracts/forecaster.py` (CONTRACT 0.3.0 → 0.4.0)

Add:

```python
class ReturnScorecardRequest(_Frozen):
    model_id: str
    forward_returns: dict[str, float]
    """Realized forward returns keyed by subject_ref (ticker); injected offline."""
```

Add capability:

```python
Capability(
    "return_scorecard",
    "Compare the LightGBM return model's shadow predictions against injected "
    "forward returns; advisory, never promotion-eligible.",
    request=ReturnScorecardRequest,
    response=Scorecard,
),
```

`owns_graph`, `depends_on`, `external_io` unchanged.

### F — `agents/forecaster/agent.py` (add handler; import new domain + contract)

```python
def _return_scorecard(self, request: BaseModel) -> Scorecard:
    req = ReturnScorecardRequest.model_validate(request)
    observations = build_return_observations(
        self._graph, req.model_id, req.forward_returns
    )
    return Scorecard(
        model_id=req.model_id,
        metrics=return_scorecard_metrics(observations),
        sample_size=len(observations),
        fresh_as_of=datetime.now(tz=UTC),
        promotion_eligible=False,
    )
```

Register as `"return_scorecard"` in `self.handlers`.

### G — `models/` directory

Create `models/.gitkeep` (empty) and `models/README.md` documenting that this folder
holds trained model artifacts (not committed; produced by `scripts/train_lgbm_return.py`).
Add `models/*.txt` and `models/*.bin` to `.gitignore`.

### Part T — Tests (100% floor holds)

**`test_forecaster_return_labels.py`** (new):

- `build_label_rows` known forward_return (trivial closes sequence)
- Returns `[]` when not enough bars for features + forward window
- No-lookahead: feature at i uses only closes[:i+1]
- Multiple tickers accumulate independently
- `LabelRow` fields are correct

**`test_forecaster_model_trainer.py`** (new):

- `split_rows` sorts by date and splits at correct fraction
- `split_rows` with 0 rows → two empty lists
- `split_rows` with 1 row → all in train (n_train = max(1, ...) = 1)
- `TrainingReport` is a frozen dataclass

**`test_forecaster_return_scorecard_math.py`** (new):

- `return_scorecard_metrics` empty → `{}`
- `return_scorecard_metrics` single case → `complete_cases=1`, `hit_rate`, no IC (n<2)
- `return_scorecard_metrics` two cases correct IC + hit_rate + up/down breakdown
- Correct direction: `predicted > 0.5` and `forward_return > 0` → hit
- `build_return_observations` skips refs absent from either side

**`test_forecaster_return_scorecard.py`** (new — agent end-to-end):

- Fire `forecast_return` for a ticker → persists ShadowPrediction
- Fire `return_scorecard` with injected forward return for same ticker
- Scorecard `sample_size=1`, `promotion_eligible=False`, `complete_cases=1`
- Missing ticker in forward_returns → `sample_size=0`
- `return_scorecard` for unknown model_id → empty Scorecard

**`agents/forecaster/tests/helpers.py`** (extend):

- Add `ReturnScorecardRequest` import
- Add `return_scorecard_message(model_id, forward_returns) -> AgentMessage`

## Acceptance criteria

- `return_scorecard` capability live; every response `promotion_eligible=False`.
- `build_label_rows` + `split_rows` have 100% unit coverage; `train_and_save` is
  `# pragma: no cover`.
- `scripts/train_lgbm_return.py` runs end-to-end on a minimal CSV fixture (manual
  verification; not in CI gate — `scripts/` is outside coverage source).
- CONTRACT `0.3.0 → 0.4.0`; boundary meta-test green.
- `feat` → project version `0.7.0 → 0.8.0` (MINOR, HARD RULE).
- `make ci` green at floor **100.00**; every module **< 200 lines**.

## Out of scope (→ later)

- Wiring `return_scorecard` into a CLI surface command (can use MCP/operator for now).
- Scheduled re-training (researcher agent proposal flow).
- Promoting the LightGBM model from shadow to binding (requires operator approval
  via P10 predictor-registry gate after scorecard evidence accumulates).

## Handback report (paste into PR / reply)

Confirm: CONTRACT `0.3.0 → 0.4.0`; `return_scorecard` never promotes; `train_and_save`
is `# pragma: no cover`; `split_rows` / `build_label_rows` / `return_scorecard_metrics`
are 100% covered; `models/.gitkeep` + `.gitignore` entries added; boundary meta-test
green. New module line counts; coverage %; total test count; project version
`0.7.0 → 0.8.0`.
