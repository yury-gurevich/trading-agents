<!-- Agent: planning | Role: sprint handover -->
# Sprint 37 — Analyst sentiment pillar (the deterministic lexicon champion)

**Status:** planned · **Branch:** `sprint-37-analyst-sentiment-pillar` · **Build phase:** P12 · **Effort: M**

## Goal

Give the analyst its **third (sentiment) pillar**, blended into the same confidence gate as the
technical and fundamental pillars. The scorer is a **deterministic finance lexicon** (Loughran–McDonald
net-tone over the headlines the provider began serving in Sprint 36) — this is the **binding champion**
of the champion–challenger design in `docs/decisions/0002-sentiment-champion-challenger.md`. The
vendor-sentiment number and the FinBERT model are advisory **challengers** that land in later P12
sprints; **only this deterministic pillar gates decisions.**

This is the structural twin of **Sprint 35** (the fundamental pillar). The analyst contract already
has `Recommendation.sentiment_score: float | None`, so **no contract change**. The blend is designed so
that **when no headline carries sentiment the pillar is skipped and the composite is unchanged** — every
existing pinned confidence/technical/fundamental value keeps its current number; only new
sentiment-bearing tests are pinned fresh.

## Why (context)

- Read first: `docs/sprints/README.md` (guardrails); `docs/decisions/0002-sentiment-champion-challenger.md`
  (why lexicon is the binding champion, not FinBERT); `docs/sprints/sprint-35-analyst-fundamental-scoring.md`
  and `docs/sprints/sprint-36-provider-news-feed.md` (the pattern you mirror and the feed you consume —
  `MarketData.news: dict[Ticker, tuple[str, ...]]`).
- **Shipped code you extend (read it):**
  - `agents/analyst/domain/scoring.py` (90L) — `score_candidate(candidate, bars, fundamentals, settings)`
    builds `ScoreBreakdown`; `_composite(technical, fundamental, settings)` renormalises the present
    pillars. You add a `news` argument, compute the sentiment pillar, and **generalise `_composite` to
    three pillars**.
  - `agents/analyst/domain/fundamental_rules.py` (127L) — the exact convention to mirror: a named
    module-constant rule table + a pure `score_*` returning `(float | None, dict)` that skips absent
    evidence and never raises.
  - `agents/analyst/domain/recommend.py` (77L) — `decide(...)`; the `if score.fundamental_score is not
    None:` clause is the precise pattern for extending the rationale only when the pillar is present.
  - `agents/analyst/agent.py` (`_score`, ~line 133) — passes `market.fundamentals.get(ticker, {})`; you
    add `market.news.get(ticker, ())`.
  - `agents/analyst/provider_client.py` (`request_market_data`, ~line 49) — `fields=("ohlcv",
    "fundamentals")`; add `"news"`.
  - `agents/analyst/settings.py` (76L) — `technical_weight`/`fundamental_weight` live here; add
    `sentiment_weight` beside them.
  - `contracts/analyst.py` — confirm `Recommendation.sentiment_score` exists (it does, line 24); CONTRACT
    stays `0.1.0`, `owns_graph=("AnalystRun", "Recommendation")` untouched.

### The scoring rule

`score_sentiment(headlines, settings) -> tuple[float | None, dict[str, float]]` — a Loughran–McDonald
**net-tone** scorer:

- For each headline: lowercase, extract alphabetic tokens, count tokens in `_POSITIVE` and `_NEGATIVE`.
- A headline is **scored** only if `pos + neg > 0`; its sub-score is
  `50.0 + 50.0 * (pos - neg) / (pos + neg)` → bounded to `[0, 100]` (all-positive → 100, balanced → 50,
  all-negative → 0).
- **Skip** a headline with no lexicon words (no signal — never dilute toward neutral).
- Return `(mean_of_scored_sub_scores, {"sentiment_articles": n_scored, "sentiment_positive": Σpos,
  "sentiment_negative": Σneg})`, or **`(None, {})`** when the input is empty or **no** headline is
  scored. The value is 0–100 (the caller divides by 100). Never raises.

### The lexicon (named constants, the rule — not tunable policy)

Two module-level frozensets `_POSITIVE` / `_NEGATIVE` of high-signal finance terms, curated from the
**Loughran–McDonald** positive/negative categories (cite the source in the module header, mirroring the
"fixed reference rule" comment in `fundamental_rules.py`). A **compact curated set** (roughly 40–80
positive, 80–140 negative terms — e.g. *beats, surges, record, upgrade, raised, outperform, growth,
profit* / *misses, plunges, lawsuit, downgrade, cut, bankruptcy, fraud, probe, recall, default, loss,
warning*) is the **baseline champion** and keeps the module pure-Python and < 200L. **Do not** hand-pick
to fit the tests — pick a defensible finance set, then pin the tests to whatever it yields.
(Expanding to the full LM master dictionary later is a sanctioned upgrade that does not change the
interface; if it does, move the word lists to a vendored data file loaded once at import so the module
stays < 200L. Out of scope here.)

### Design decision — absent sentiment is *skipped*, not neutral-50 (decided; read)

Identical to the Sprint 35 fundamental decision: when no headline carries a lexicon word the pillar is
**skipped** (`score_sentiment → None` → the composite excludes it), **not** blended as a neutral 50.
Rationale: it matches v2's "skip absent evidence, never dilute" idiom, keeps the composite identical to
today whenever news is missing (so the gate isn't dragged toward neutral on the common no-news path),
and **re-pins no existing test**. (The reference system averaged unscored articles to a neutral 50; we
deliberately do not — flag back before implementing if strict reference parity is wanted, but it would
dilute every score whenever news is thin and re-pin essentially every analyst/pipeline confidence.)

### The blend

Generalise the composite to **renormalise over the present pillars** (all in 0–1):

- `technical` is always present.
- `fundamental` / `sentiment` are each included **only when** their scorer returned a value.
- `composite = Σ(weightᵢ · valueᵢ) / Σ(weightᵢ)` over the present pillars
  (`(w_t·tech + w_f·fund + w_s·sent)/Σ present`).
- `confidence = bounded(confidence_floor + composite · confidence_span)` — unchanged.

This **must** reduce exactly to today's two-pillar and one-pillar results: fundamental present +
sentiment `None` → the current `(w_t·tech + w_f·fund)/(w_t+w_f)`; both `None` → `technical` alone. That
identity is what keeps every existing value pinned.

## Part A — Settings

`agents/analyst/settings.py` — add to `AnalystSettings`, beside the other weights:

- `sentiment_weight: float = tunable(0.20, why="Reference composite weight for the sentiment pillar; renormalised over present pillars.", ge=0.0, le=1.0)`

Keep `settings.py` < 200L (currently 76L).

## Part B — Sentiment rules

New `agents/analyst/domain/sentiment_rules.py` — ≤ 180L:

```python
"""News-headline sentiment scoring rules and their pillar score.

Agent: analyst
Role: score Loughran-McDonald net tone over news headlines into a 0-100 pillar.
External I/O: none.
"""
```

- The `_POSITIVE` / `_NEGATIVE` frozensets (with the LM-provenance header comment).
- A pure tokeniser (`_tokens(headline) -> list[str]` — lowercase alphabetic tokens).
- `score_sentiment(headlines: tuple[str, ...], settings: AnalystSettings) -> tuple[float | None,
  dict[str, float]]` exactly as specified. (`settings` is accepted for signature symmetry even if unused
  this sprint — mark `# noqa: ARG001` like `score_candidate`'s `candidate`, or omit it and pass only
  `headlines`; your call, but keep the call site clean.)

## Part C — Fold into scoring

`agents/analyst/domain/scoring.py`:

- Signature → `score_candidate(candidate, bars, fundamentals, news, settings)` (insert `news:
  tuple[str, ...]` before `settings`).
- Add `sentiment_score: float | None = None` to `ScoreBreakdown`.
- After the fundamental block: `raw_sent, smetrics = score_sentiment(news, settings)`;
  `sentiment = None if raw_sent is None else _bounded(raw_sent / 100.0)`.
- Generalise `_composite` to take `sentiment` and renormalise over present pillars (see The blend).
- Set `sentiment_score` on the result; add it and the `smetrics` entries to `metrics` (e.g. only when
  present, matching how `fundamental_score` is added) so they are auditable.
- The `insufficient_market_history` early return is unchanged (no price history is still a hard reject;
  news does not rescue it).

## Part D — Wire the agent + request

- `agents/analyst/provider_client.py`: `fields=("ohlcv", "fundamentals", "news")`.
- `agents/analyst/agent.py` `_score`: pass `market.news.get(candidate.ticker, ())` into `score_candidate`
  (positionally before `self._settings`).

## Part E — Decision + rationale

`agents/analyst/domain/recommend.py`:

- Set `sentiment_score=score.sentiment_score` on the `Recommendation`.
- When `score.sentiment_score is not None`, append a short clause (e.g. `" and a news-sentiment score of
  {…:.3f}"`) and add evidence ref `"analyst.sentiment_score"` — mirroring the fundamental clause. When it
  is `None`, leave the summary **byte-for-byte unchanged** so the existing exact-string tests stay green.

## Part F — Tests

### F1. `agents/analyst/tests/test_sentiment_rules.py` — ≤ 130L

Hand-built headlines using known in-lexicon words: an all-positive headline → 100; all-negative → 0; a
balanced headline → 50; a headline with **no** lexicon word skipped; **all** headlines neutral → `(None,
{})`; empty input → `(None, {})`; case-insensitivity and punctuation tokenisation; the partial average
over a mix of scored/neutral headlines; the metrics dict counts. Never raises.

### F2. Scoring + decision

- New: a candidate **with** news → hand-computed three-pillar blended `confidence`
  (`floor + ((w_t·tech + w_f·fund + w_s·sent)/(w_t+w_f+w_s)) · span`) and `Recommendation.sentiment_score`
  set; rationale gains the sentiment clause. Also a two-pillar case (news present, fundamentals absent).
- Existing `score_candidate` call sites gain the new `news=()` argument. With `()` the pillar is skipped →
  **every pinned confidence/technical/fundamental value is unchanged** (mechanical arg addition only — do
  not alter expected numbers).

### F3. Agent + pipeline regression

- An analyst-agent test where `market.news` carries headlines for a ticker → the recommendation shows a
  populated `sentiment_score` and the rationale clause.
- Existing analyst-agent and full-pipeline tests use `FakeDataSource` with no news fixture →
  `market.news == {}` → skipped pillar → **no re-pin**. (Requesting `"news"` does not degrade quality on
  empty data — confirm the degraded-rejection tests are unaffected.) Run the whole suite.

## Steps

1. Branch `sprint-37-analyst-sentiment-pillar` off `main`.
2. **A** settings → **B** `sentiment_rules.py` (+ F1) → **C** fold into `scoring.py` (generalise
   `_composite`).
3. **D** request + agent wiring → **E** decision/rationale. `make ci`.
4. **F2/F3**: add sentiment-bearing tests; add `news=()` to existing call sites; full-suite regression.
   `make ci` green at the coverage floor (100.00).
5. `wc -l agents/analyst/domain/*.py agents/analyst/settings*.py` — all < 200.
6. Push; hand back.

## Acceptance criteria

- `score_sentiment` reproduces the net-tone rule (hand-verified), averages only headlines that carry a
  lexicon word, returns `(None, {})` when none do, and never raises.
- Confidence is gated on the renormalised composite over the **present** pillars; when sentiment is
  absent the composite is unchanged and **no existing expected value changes** (two-pillar and one-pillar
  identities preserved).
- `Recommendation.sentiment_score` is populated when present, `None` otherwise; rationale extended only
  in the present branch.
- **No contract change** (analyst CONTRACT 0.1.0, `owns_graph` untouched); analyst now requests the
  `"news"` field. **No new dependency** (pure-Python lexicon).
- `make ci` green at/above floor 100.00; import-linter kept; every touched/new module < 200L.

## Out of scope (later P12 sprints — see ADR-0002)

- **Provider-sentiment challenger** (Finnhub `/news-sentiment`, advisory/shadow) and the
  **forecaster/FinBERT agent** (advisory, heavy dep isolated behind the agent boundary). Neither gates;
  both write readings aligned to this champion's.
- **Relationship/scorecard harness** — compares the three scorers on forward returns and promotes via the
  P10 registry gate. *This is where the live news-accrual runway is consumed:* shipping this sprint is
  what starts the analyst requesting real headlines and stamping `sentiment_score` onto persisted
  `Recommendation` nodes — the beginning of the accrual. (Per-ticker readings for **non-recommended**
  tickers, if the harness needs them, are added with that sprint, not here.)
- Persisting a separate sentiment-reading node; the full Loughran–McDonald master dictionary;
  sector/macro propagation (P13). Any change outside the analyst package + its tests (plus the one-line
  provider-request field change).

## Handback report (paste into PR / reply)

- Confirm no contract change (analyst 0.1.0) and that the absent-sentiment path leaves the composite
  identical (so existing values were re-used, not re-pinned — only the mechanical `news=()` arg added).
- The generalised `_composite` and the three weights; one worked example (tech, fund, sent → confidence).
- The lexicon source/size (how many positive/negative terms; provenance note) and how `score_sentiment`
  handles neutral/empty/mixed headlines and the all-unusable case.
- Final line counts: `sentiment_rules.py`, `scoring.py`, `recommend.py`, `settings.py`.
- New coverage % and floor; total test count; confirmation existing tests needed no value re-pin.

The planning agent reviews, merges to `main`, and plans P12's next sprint — the provider-sentiment
challenger (advisory/shadow), then the forecaster/FinBERT agent — per ADR-0002.
