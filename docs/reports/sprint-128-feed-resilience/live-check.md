<!-- Agent: planning | Role: S128 live functionality-check evidence -->
# Sprint 128 — Live Functionality Check (2026-07-19)

Provider stage only; live Finnhub + live Neon; no scanner/PM/execution, no broker
calls, no `sched-*` run ids. Precondition met first: DRIFT-023 resolved — the
read-only probe returned `DEP-POSTGRES-01 GREEN postgres: reachable SELECT 1`
before any ingest started.

## 1. Paced full-universe ingest (run id `s128-live-paced-20260719`)

99 tickers (`scripts/universe_sp100.txt`), all four Finnhub feeds, budget 55 req/min:

```text
elapsed_seconds=429.0
requested=99 returned=99 used_fallback=False
stale_tickers=0 anomalous_tickers=()
bars=3960
fundamentals_tickers=99 news_tickers=99 sectors_tickers=99 earnings_tickers=70
notes_count=0 whole_feed_degraded_notes=0 attributed_degraded_notes=0
```

**Zero degraded notes of any kind.** Elapsed 7 min 09 s — comfortably inside the
22:25–00:30 UTC fleet window (`earnings_tickers=70` is the 30-day lookahead window
having no scheduled event for 29 tickers, not degradation). DoD 1 met.

## 2. Unpaced granularity proof (run id `s128-live-unpaced-20260719`)

Same universe, `PROVIDER_FINNHUB_REQUEST_BUDGET_PER_MINUTE=0` — today's pre-S128
nightly behavior, with the **live** Finnhub 60/min limit as the fault injector
(no mocked 429s):

```text
elapsed_seconds=138.1
requested=99 returned=99 used_fallback=False
fundamentals_tickers=60 news_tickers=60 sectors_tickers=60 earnings_tickers=42
notes_count=4 whole_feed_degraded_notes=0 attributed_degraded_notes=4
  fundamentals_degraded:39:MET,META,MMM,MO,MRK:429
  news_degraded:39:MET,META,MMM,MO,MRK:429
  sectors_degraded:39:MET,META,MMM,MO,MRK:429
  earnings_degraded:39:MET,META,MMM,MO,MRK:429
```

One ticker's 429 costs exactly that ticker's enrichment: 60 of 99 kept per feed,
bounded attributed notes (cap 5 named tickers), **zero whole-feed notes**, and
`used_fallback` untouched (DRIFT-012 invariant). DoD 2 met. Before S128 this exact
scenario discarded all four feeds whole.

## 3. Durability on Neon (run id `s128-live-durability-d-20260719`)

A 40-ticker unpaced ingest wired to Neon tripped the live limit mid-run; the
persisted MarketData node was then read back over a **fresh SQL connection**
(psycopg `SELECT` on `nodes`, not the in-process object):

```text
node_key=market-data:s128-live-durability-d-20260719
persisted_used_fallback=False
persisted_notes_count=2
  sectors_degraded:20:CMCSA,COF,COP,COST,CRM:429
  earnings_degraded:20:CMCSA,COF,COP,COST,CRM:429
all_nodes_for_run:
  MarketData / RegimeContext / RunRequest  (×1 each)
```

The attributed notes survive in the graph after the writing process exits — the
scale-to-zero diagnosis story (`/diagnose-feeds`, dashboard vital, verdict warning
all parse this form via `contracts/feed_notes.py`). DoD 3 met. Sector count also
showed the DRIFT-013 cache backfilling 2 of the 20 failed tickers.

## 4. Teardown

`scripts/pg_teardown.py --prefix s128-live --contains`:

```text
deleted_edges=4 deleted_nodes=12
remaining_s128_live_nodes: 0
remaining_s128_live_edges: 0
```

All nodes created by this check (four `run-request:s128-live-*` +
`market-data`/`regime-context` for the three Neon-wired runs) swept to zero.

## Deviations and honest notes (LAW-02)

- **Runs 1–2 did not write to Neon.** The disposable driver lived outside the repo
  tree and `load_dotenv()`'s default upward search missed `.env`, so
  `build_graph_from_env()` silently fell back to `InMemoryGraphStore`. The Finnhub
  side of both runs (pacing, timings, quality trace) is live-process stdout and
  fully valid; graph writes were in-memory only, so those two run ids left nothing
  on Neon (and nothing to tear down). The driver was fixed (explicit `.env` path +
  a loud refuse-to-run-in-memory guard) before the durability leg.
- **Durability came from three small Neon-wired runs** (8, 20/42, 40 tickers), not a
  third full-universe ingest — the sprint's "at most two full-universe live
  ingests" guardrail was respected (exactly two: one paced, one unpaced). The
  42-ticker attempt included comment lines from a bad shell parse of the universe
  file (operator-side error, not code): the garbage symbols failed the whole OHLCV
  batch honestly (`source_unavailable`, `used_fallback=True`) while enrichment
  still attributed real 429s per ticker. The clean 40-ticker run (`-d`) is the
  durability evidence node.
- **Live vendor observation:** Finnhub's free-tier limiter behaves like fixed
  calendar-minute buckets — 80 unpaced calls in 32 s straddling two buckets drew
  zero 429s, while ~160 calls over 62 s reliably tripped. The 55/min sliding-window
  budget stays safely under either interpretation.
