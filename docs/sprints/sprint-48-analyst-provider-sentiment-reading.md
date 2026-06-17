<!-- Agent: planning | Role: sprint handover -->
# Sprint 48 — Analyst persists the provider-sentiment shadow reading (P12)

**Status:** planned · **Branch:** `sprint-48-analyst-provider-sentiment-reading` · **Build phase:** P12 (provider-sentiment challenger — completes it) · **Effort: S–M**

## Goal

Close the provider-sentiment challenger loop: the analyst now **requests** the vendor sentiment that
the provider serves (S47, `MarketData.sentiment`) and **persists a second `SentimentReading`** per
scored ticker, tagged `scorer="provider"`, **aligned** to the lexicon champion's reading (same run +
ticker, same 0–1 scale) — **shadow, never gates a decision**. With this, every analyst run records both
the champion (lexicon) and the challenger (provider) readings side by side, which is exactly the input
the future **scorecard harness** compares against forward returns (ADR-0002).

This is the **S37/S46 twin, one scorer over**: S46 already built the `SentimentReading` node, the
`write_analysis` persistence (a *tuple* of readings keyed `{run_id}:{scorer}:{ticker}`), and the
`lexicon_reading` builder. This sprint adds the `provider` scorer alongside it. **No gating change** —
the provider sentiment never enters `score_candidate`/`_composite`/confidence; it is recorded only.

## Why (context)

- Read first: `docs/sprints/sprint-46-analyst-sentiment-reading.md` (the node + persistence this
  extends); `docs/sprints/sprint-47-provider-sentiment-feed.md` (the `MarketData.sentiment` it consumes);
  `docs/decisions/0002-sentiment-champion-challenger.md` (shadow-aligned challengers); memory
  `sentiment-champion-challenger`.
- **Shipped code you extend (read it):**
  - `agents/analyst/domain/sentiment_reading.py` — has `SentimentReading`, `LEXICON_SCORER`, and
    `lexicon_reading(ticker, score)`. You add `PROVIDER_SCORER = "provider"` and
    `provider_reading(ticker, score) -> SentimentReading`. (The dataclass's `articles/positive/negative`
    are lexicon word-counts; for the provider they are **0** — N/A. Tag distinguishes the scorers.)
  - `agents/analyst/agent.py::_analyze` — already collects `lexicon` readings from `decisions` and
    passes `sentiment_readings=...` to `write_analysis`. `market` (a `MarketData`) is in scope here, so
    build the provider readings here and **concatenate**.
  - `agents/analyst/provider_client.py::request_market_data` — `fields=("ohlcv", "fundamentals",
    "news")`; add `"sentiment"`.
  - `agents/analyst/store.py::write_analysis` — already persists a `tuple[SentimentReading, ...]` and
    keys nodes by `scorer`; **no change needed** (the provider readings ride the same path, distinct key).
  - `agents/analyst/tests/helpers.py::wire_analyst` — add a `sentiment: dict[str, float] | None = None`
    param passed to `FakeDataSource(sentiment=...)` (mirror how `news` was added).
  - `contracts/analyst.py` — **no change** (`SentimentReading` already in `owns_graph` from S46;
    CONTRACT stays `0.2.0`).

## Parts

- **A** `sentiment_reading.py` — add `PROVIDER_SCORER = "provider"` and:
  ```python
  def provider_reading(ticker: str, score: float) -> SentimentReading:
      """Build the advisory provider (vendor) reading; counts are N/A for this scorer."""
      return SentimentReading(
          ticker=ticker, scorer=PROVIDER_SCORER, score=score,
          articles=0, positive=0, negative=0,
      )
  ```
- **B** `agent.py::_analyze` — after the existing lexicon-reading collection, build provider readings
  from `market.sentiment` for every candidate that has a vendor score, and concatenate:
  ```python
  provider_readings = tuple(
      provider_reading(candidate.ticker, market.sentiment[candidate.ticker])
      for candidate in candidate_set.candidates
      if candidate.ticker in market.sentiment
  )
  # ... pass sentiment_readings=lexicon_readings + provider_readings to write_analysis
  ```
  (Import `provider_reading`. The vendor score is already 0–1 aligned by S47, so it is directly
  comparable to the lexicon's.)
- **C** `provider_client.py` — `fields=("ohlcv", "fundamentals", "news", "sentiment")`.
- **D** `tests/helpers.py` — `wire_analyst(..., sentiment=None, ...)` → `FakeDataSource(sentiment=sentiment)`.

## Part F — Tests

- `test_sentiment_reading.py`:
  - `provider_reading("AAPL", 0.58)` → `scorer="provider"`, `score==0.58`, counts 0.
  - **Agent end-to-end:** `wire_analyst(source_bars=bars(), sentiment={"AAPL": 0.58})` → after
    `analyze`, `graph.get_node("SentimentReading", f"{run_id}:provider:AAPL")` exists with
    `props["score"]==0.58` and `props["scorer"]=="provider"`; **and** the lexicon node still absent
    (no news) — i.e. the two scorers are independent. (If you also pass `news=`, assert *both*
    `:lexicon:` and `:provider:` nodes exist for the run — the alignment.)
  - **Shadow invariant:** the run with vendor sentiment but no news produces the **same confidence /
    recommendation** as without it (provider sentiment does not gate). Assert the recommendation's
    `confidence` is unchanged vs a no-sentiment run.
- Regression: existing analyst-agent + pipeline tests use `FakeDataSource` with no `sentiment` fixture
  → `market.sentiment == {}` → no provider readings, requesting `"sentiment"` does not degrade quality
  on empty data (confirm, like `news`) → **no re-pin**. Run the whole suite.

## Acceptance criteria

- The analyst requests `"sentiment"`; for each candidate with a vendor score it persists a
  `SentimentReading` keyed `{run_id}:provider:{ticker}` (0–1, aligned to the lexicon), **including
  non-recommended tickers**, linked to the run (S46's `PRODUCED` edge).
- The provider sentiment **never** changes a confidence, recommendation, or rejection (shadow); no
  existing value re-pinned (mechanical: a new field requested + readings appended).
- No contract change (analyst `0.2.0`); no new dependency. `make ci` green at floor 100.00; every
  module < 200L.

## Out of scope (the rest of P12 — ADR-0002)

- The **forecaster/FinBERT** scorer (advisory, `torch` isolated behind the forecaster boundary) and the
  **relationship/scorecard harness** (compare lexicon/provider/FinBERT readings vs forward returns,
  promote via the P10 gate). The full Loughran–McDonald master dictionary (champion upgrade). P13.
- Any settings-alias reconciliation for `PROVIDER_ALPHAVANTAGE_API_KEY` vs the `.env`'s
  `ALPHAVANTAGE_API_KEY` — only needed when a live run reads it through `ProviderSettings`; flag it,
  don't fix it here (the unit gate is fake-backed).

## Handback report (paste into PR / reply)

- Confirm no contract change and no re-pin (only `news=()`-style mechanical additions); how `_analyze`
  concatenates lexicon + provider readings; that the shadow invariant test passes (confidence unchanged).
- Final line counts for touched analyst modules; new coverage % and floor; total test count.

After merge: P12's remaining trinity work is **forecaster/FinBERT** then the **scorecard harness**.
