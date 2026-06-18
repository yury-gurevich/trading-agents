---
type: Architecture Decision
status: accepted
closes: "How do we evaluate and promote ML sentiment models without breaking the deterministic gate?"
tags: [sentiment, finbert, analyst, forecaster, p12]
---

# ADR 0002 — Sentiment as champion–challenger; the forecaster hosts advisory ML

**Status:** Accepted · **Date:** 2026-06-15 · **Decider:** Yury Gurevich (product owner)

> **Amendment 2026-06-16 (provider-sentiment source).** Finnhub `/news-sentiment` (Decision §1) is
> **dead for us** — `403 "You don't have access"` on the free tier (verified). The trinity shape is
> unchanged (LOCKED); only the *vendor* of the provider-sentiment challenger moves. Owner chose
> **"alternative free vendor"** → **Alpha Vantage `NEWS_SENTIMENT`** (free key; returns
> `feed[].ticker_sentiment[].ticker_sentiment_score`). Pending a real-key live verification (the
> Finnhub lesson); **Marketaux** (free 100/day entity sentiment) is the documented fallback if AV's
> endpoint proves premium. Read `ticker_sentiment_score` ∈ [-1, 1] → `50 + 50·score` to align 0–100.

## Context

The analyst's composite score reserves a third **sentiment** pillar (weight 0.20) alongside the
shipped technical and fundamental pillars. Building it raised two questions the product owner pushed
on:

1. **Which scorer?** A deterministic lexicon (count finance-tuned positive/negative words), a
   provider-supplied sentiment number (a vendor computes it), or a transformer model (FinBERT) that
   "reads" headlines and captures nuance the other two miss.
2. **Sentiment of *what*?** Per-ticker tone is not enough. If Tesla does well, is the EV *industry*
   doing well? How do **tariffs/sanctions** move stocks — events whose sign is *relationship-
   dependent* (a tariff that shields a domestic competitor hurts the foreign exporter and a
   China-exposed domestic name at the same time)? That cross-asset reasoning lives in **relationships**,
   not in any single document's words.

Two findings shaped the decision:

- **There is nothing to port.** The reference system's sentiment pillar was a dormant stub: its news
  records carried no sentiment field, so the scorer always returned a neutral 50. This is build-new.
- **The boundary map already reserved the home.** The `forecaster` agent
  (`contracts/forecaster.py`, never implemented) is defined as *"advisory shadow-ML signals, never
  binding until scorecards earn it"* — `ShadowPrediction(shadow=True, "never gates a decision")` plus
  a `Scorecard` capability. The build plan's principle is explicit: *"Advisory before binding. ML and
  any non-deterministic component ships shadow first, behind a scorecard, before it can influence a
  decision."* The owner's "keep FinBERT as a separate smart agent, compare, decide later" is that
  agent, activated.

Constraints in force: determinism + the 100 %-pinned coverage gate; justified-tunable governance; a
lightweight dependency footprint; the one rule (no agent imports another); single-writer-per-label;
exclusive external I/O.

## Decision

1. **One interface, three scorers, champion–challenger.** A `SentimentScorer` maps news → a 0–100
   score. Three implementations behind that interface:
   - **Lexicon (Loughran–McDonald finance word lists)** — deterministic, explainable, pinnable. The
     analyst's **binding** sentiment pillar.
   - **Provider sentiment number** — a vendor's per-ticker sentiment, an **advisory** challenger
     (Alpha Vantage `NEWS_SENTIMENT` per the 2026-06-16 amendment; Finnhub `/news-sentiment` is dead).
   - **FinBERT** — a transformer (`p_pos/p_neu/p_neg → 50 + 50·(p_pos − p_neg)`), an **advisory**
     challenger, isolated behind the forecaster.

2. **The forecaster agent hosts the FinBERT scorer** (its first implementation). The heavy
   `torch`/`transformers` dependency lives **entirely behind the forecaster's boundary** — no other
   agent imports it; it participates only via typed messages and writes its own `ShadowPrediction`/
   `Model` nodes. The agent boundary *is* the dependency-isolation mechanism. Non-determinism is made
   auditable by stamping a `model_version` on every reading (every score is reproducible *given* the
   recorded version).

3. **Only the deterministic lexicon gates decisions.** Provider and FinBERT run in **shadow**: their
   readings are recorded *aligned* to the lexicon's, never gating, until a scorecard earns promotion
   through the **predictor registry (P10)**.

4. **A relationship/scorecard harness produces the quantitative answer.** Over aligned triples
   `(A=provider, B=lexicon, F=FinBERT)` + forward returns: pairwise correlations, a regression
   `F = α + β·A + γ·B + ε`, the **residual** `ε`, and each scorer's **incremental information
   coefficient** on forward returns. The part of FinBERT *not* reproducible from A and B *that also
   predicts returns* is its measurable marginal value; if that is ≈ 0, FinBERT is dropped on evidence.
   Optional **distillation** (`F ≈ g(A, B, …)`) folds the value back into the deterministic path.

5. **Cross-asset & macro signal is a graph layer, not a scorer.** Sector contagion (Tesla → EV peers)
   and macro events (tariffs/sanctions) are modeled as Neo4j relationships + **signed** propagation,
   sitting *on top* of whatever per-document scorer is used. Turning a macro headline into a typed
   `Event` (target sector/country/commodity + direction) is **extraction**, an LLM job (operator/
   forecaster), not word-matching. This is a later phase (P13), separable from the scorer work.

## Rationale

- **Determinism stays where it must.** The binding pillar is the deterministic lexicon, so the live
  decision path remains exactly pinnable at the coverage gate; the non-deterministic model is advisory
  only — consistent with "advisory before binding."
- **The agent boundary isolates the heavy dependency.** Because no agent imports another, FinBERT's
  `torch` footprint never enters anyone else's import graph or the default unit gate.
- **It reuses, not invents.** The forecaster contract and the P10 predictor-registry promotion gate
  already exist for exactly this advisory→binding-by-evidence flow. **No boundary-map change, no new
  agent.**
- **It answers the owner's question quantitatively.** A per-call probabilistic model becomes a
  *measured relationship* with point estimates and confidence intervals; the decision to keep/drop/
  distill FinBERT rides on forward-return evidence, not taste.
- **It absorbs the sector/macro vision** without coupling: all three scorers feed the same per-node
  sentiment that the graph layer later propagates across peer/sector/exposure edges.

## Consequences

- **Implements the forecaster** (first time) and opens two phases: **P12** (sentiment champion–
  challenger) and **P13** (cross-asset & macro signal graph). Sentiment is **removed from P11**'s
  analyst scope; P11 keeps technical (done), fundamental (done), relative strength, signal-diversity,
  and the PM/scanner/reporter gaps.
- **Graph labels** keep single-writer-per-label: the analyst owns the deterministic sentiment reading;
  the provider owns its provider-sentiment reading; the forecaster owns `ShadowPrediction`/`Model`.
- **Dependencies:** `torch`/`transformers` enter **only** as an optional dependency group with
  integration-marked tests; the default unit run stays deterministic and infra-free. The forecaster
  contract's `external_io` may need a narrow entry for model-artifact provisioning (decide in the
  forecaster sprint; a vendored/local model keeps the live path call-free).
- **Data precondition (gates the scorecard sprint only).** The relationship harness needs *aligned
  historical news + forward returns*. The feed/lexicon/provider/forecaster sprints do **not** depend
  on it. **Verified 2026-06-15** against the deprecated reference Postgres (a v1 store — **test/
  validation only, never a runtime dependency; the product accrues data live into Neo4j**): it holds
  **5 years of daily OHLCV** (`price_cache`: 629,823 rows, 507 tickers, 2021-04 → 2026-05,
  adjustment-tracked) — a usable fixture for the **forward-return** side — but **no news history**
  (`news_embedding_cache` and `news_impact_shadow_log` both empty; v1 scaffolded the shadow-sentiment
  schema and never fed it). Therefore: the return side is seedable now; the **news side needs a live
  accrual runway** — turn on the S36 feed, score + store headlines going forward, then run the
  scorecard against `price_cache` returns. A paid news backfill would only shortcut the wait.

## Alternatives considered

- **FinBERT inside the analyst.** Pollutes the deterministic, *binding* agent with a heavy
  non-deterministic dependency; breaks the coverage gate's meaning. Rejected.
- **A new dedicated `sentiment`/`nlp` agent.** A boundary-map change for no gain — the forecaster is
  already the designated advisory-ML role. Rejected in favour of the forecaster.
- **Lexicon only.** Cheapest and fully deterministic, and it remains the *champion*; but as the *end
  state* it forecloses the empirical comparison the owner wants and the macro-event understanding.
  Rejected as the terminal design.
- **FinBERT as the binding scorer.** Best raw reading quality, but non-reproducible across versions,
  un-pinnable, un-governable (opaque weights vs justified tunables), ~2 GB footprint. Rejected for the
  decision path; allowed as an advisory challenger and as an *offline* distillation teacher.

## Optionality

Scorers sit behind one `SentimentScorer` interface and the forecaster behind the bus, so a fourth
scorer (or a different model) is an added implementation, not a rewrite — the same two-backend
discipline the bus and `GraphStore` already use. The champion is promotable/demotable purely on
scorecard evidence.
