<!-- Agent: planning | Role: sprint handover -->
# Sprint 46 — Persisted sentiment-reading node (scorecard alignment substrate)

**Status:** shipped · **Branch:** `sprint-46-analyst-sentiment-reading` · **Build phase:** P12 (checklist item 2) · **Effort: M**

## Goal

Persist the champion (lexicon) sentiment **reading** as a first-class graph node — one per scored
candidate that carries news sentiment, **including non-recommended (rejected) tickers** — so the future
champion–challenger **scorecard** can align each scorer's reading against forward returns. Today the
lexicon score only survives on the `Recommendation` of *recommended* tickers (S37); a rejected-but-scored
ticker's reading is lost. This slice captures every reading, tagged by `scorer` so challengers write
aligned readings later. This is **checklist item 2** of the LOCKED P12 trinity (memory
`sentiment-champion-challenger`); item 1 (full LM dictionary) is deferred (data not sourceable here),
and the provider-sentiment challenger is **blocked** — Finnhub `/news-sentiment` returns 403 on the free
tier (a forced decision for the owner: alternative source, paid, or drop).

## Design (firm)

- **`SentimentReading`** — a frozen analyst-domain dataclass: `ticker, scorer, score (0-1), articles,
  positive, negative`. `scorer="lexicon"` (the champion); challengers reuse the same node with their own
  `scorer` tag and key.
- The reading rides on **`AnalysisDecision`** (built in `decide()` for every candidate, rec or reject)
  so it survives splitting; `_analyze` collects the present readings and passes them to `write_analysis`.
- **Node:** `SentimentReading` keyed `{run_id}:{scorer}:{ticker}`, linked `AnalystRun --PRODUCED-->
  SentimentReading` (so a run's readings are traversable). Analyst `owns_graph += "SentimentReading"`
  (unique writer — passes `test_each_graph_label_has_one_writer`); CONTRACT `0.1.0 -> 0.2.0`.
- **No gating change** — the lexicon still gates via S37's composite; this only *records* the reading.
  Absent news ⇒ no reading (sentiment_score `None`) ⇒ no node ⇒ existing runs unchanged (no re-pin).

## Parts

- **A** `agents/analyst/domain/sentiment_reading.py` (new) — `SentimentReading` + `LEXICON_SCORER` +
  `lexicon_reading(ticker, score) -> SentimentReading | None` (None when `score.sentiment_score is None`;
  reads counts from `score.metrics`).
- **B** `recommend.py` — `AnalysisDecision` gains `sentiment_reading: SentimentReading | None = None`;
  `decide()` builds it once and attaches to every returned decision.
- **C** `store.py` — `write_analysis(..., sentiment_readings=())` writes a `SentimentReading` node per
  reading + the `PRODUCED` edge from the run.
- **D** `agent.py::_analyze` — collect `d.sentiment_reading` for present readings; pass to `write_analysis`.
- **E** `contracts/analyst.py` — `owns_graph += ("SentimentReading",)`; bump version `0.2.0`.
- **F** tests — domain (`lexicon_reading` present/absent); store (readings persisted incl. a
  **rejected** ticker, node props + `PRODUCED` edge); agent (an analyze run with news writes the nodes).

## Acceptance

- A scored candidate with news yields a `SentimentReading` node keyed by run/scorer/ticker, linked to
  the run, **whether or not** it was recommended; absent news writes no node.
- Analyst `owns_graph` includes `SentimentReading` (single writer); no other test re-pinned.
- `make ci` green at floor 100.00; every module < 200L.

## Out of scope

- The provider-sentiment / FinBERT challengers + the scorecard harness itself (later); the full LM
  dictionary; a typed read-projection/CLI for readings; P13.
