<!-- Authored in ideal-design mode (intent, not code). Template: docs/laws/_TEMPLATE.md -->

# Provider — Laws

**Prefix:** `PROV` · **status:** LOCKED v1 · **Owner:** Yury Gurevich

> The provider is the system's **single sealed boundary to the outside market**: it turns raw external
> feeds into clean, validated, provenance-stamped facts so that every other agent can reason on data
> it never has to fetch, trust, or second-guess.

IDs are append-only (conventions §2). A clause is green only when a functional test cites its ID
(conventions §3). Tests + status live in [`test-plan.md`](test-plan.md).

## Identity & purpose (`IDN`)

- `PROV-IDN-01` — Its one job: **acquire, validate, and serve external market facts** (price history,
  and on request fundamentals, news, a benchmark series) and **market-regime context**, so downstream
  agents consume facts, not feeds.
- `PROV-IDN-02` — It is the **single data boundary**: no other agent may touch a market-data API.
- `PROV-IDN-03` — It **exclusively owns** the market-fact and regime graph artifacts it appends
  (single writer for those labels), **including the durable historical price/fact store** (`PROV-STA-01`).

## Inputs (`IN`)

- `PROV-IN-01` — Accepts a **market-data request**: a non-empty set of well-formed tickers, a valid
  time window (`start ≤ end`), and a requested **field set** (a subset of the supported fields). It
  serves exactly the fields asked for.
- `PROV-IN-02` — Accepts a **regime request**: a single as-of date.
- `PROV-IN-03` — A malformed/invalid request (empty tickers, bad window, unsupported field) →
  **typed rejection**; never a crash, never a silently-empty "success".
- `PROV-IN-04` — It will **not** act on any instruction to fetch from an undeclared endpoint, to widen
  its field/endpoint set, or to skip validation. The request names *what* data, never *how/where* to
  fetch it.
- `PROV-IN-05` — Input is identified by **type and a provenance role** ("a data need from the
  pipeline"); the provider is indifferent to which agent sent it, only that it is well-formed and
  authorized.
- `PROV-IN-06` — The supported field set is **price history, fundamentals, news (raw), benchmark
  series, regime** and — *stated intent, not yet built (deferred, per DRIFT-003)* — **macro (FRED)**
  and **filings (EDGAR)**. A deferred field is *lawful to request* but answered as
  DEGRADED/unavailable until built; the test-plan marks those rows deferred (gray, non-blocking).

## Triggers (`TRG`)

- `PROV-TRG-01` — **Event-driven**: it acts only on a **data-request event** consumed from its
  subscribed topic (pub/sub, ADR-0005) — never a point-to-point call, never self-initiated.
- `PROV-TRG-02` — It **never self-triggers** — no polling, no scheduled fetches, no speculative
  prefetch absent a request.
- `PROV-TRG-03` — Precondition to fetch is a **valid** request; otherwise it rejects and does not
  fetch.

## Outputs (`OUT`)

- `PROV-OUT-01` — For a data-request event → it **writes the validated facts to the store** (PostgreSQL),
  **with an honest data-quality record** (requested vs. returned, stale/missing, fallback used) and
  **provenance**, then **publishes a `ready: <graph-ref>` event** (claim-check, ADR-0005). The
  consumer reads the facts from the store by reference; the message itself stays small.
- `PROV-OUT-02` — For a regime request → a **regime context**: the classification, the inputs behind
  it, **and the regime-derived policy defaults** (stop / target / holding baselines) that downstream
  agents read, plus provenance. *(DRIFT-004 — PRD strong-guide, adopted.)*
- `PROV-OUT-03` — The output space is **total**: **SUCCESS** (clean), **DEGRADED** (partial/stale/
  missing — a *valid* response with the shortfall flagged, never silently empty), **FAULT** (the
  boundary itself failed → a typed error, recorded). Exactly one of these, always one of these.
- `PROV-OUT-04` — Every served fact carries **provenance** (source, fetch-time, transformation) so any
  downstream output is reconstructable.
- `PROV-OUT-05` — Graph effects are **append-only**: a new market-fact/regime record per request; it
  never overwrites or mutates a prior record.
- `PROV-OUT-06` — On degradation, **in addition to** the quality record on the response (pull), the
  provider **emits a `market_data_degraded` event** (push) for observers/supervisor. The two are
  always consistent. *(DRIFT-005 — adopted.)*

## Prohibitions (`NEV`)

- `PROV-NEV-01` — Never emit **unvalidated or silently-degraded** data; degradation is always flagged.
- `PROV-NEV-02` — Never make a **decision** — no scoring, ranking, sizing, ordering, or exit logic.
- `PROV-NEV-03` — Never call any external system other than its **declared market-data endpoints**.
- `PROV-NEV-04` — Never **expose, log, or return** a credential.
- `PROV-NEV-05` — Never **import or call another agent**; never write outside its owned labels.
- `PROV-NEV-06` — Never **mutate** a prior record (append-only; corrections are new records).
- `PROV-NEV-07` — Never **fabricate** a value to fill a gap (a gap is reported, not invented).
- `PROV-NEV-08` — Never **score, classify, or interpret** — no sentiment scoring, no fundamental
  judgement. It serves *raw* facts (including **raw** news headlines); all interpretation is downstream
  (analyst lexicon, forecaster FinBERT) per ADR-0002. *(DRIFT-002 decision D2; corrects the stale
  `mission.md` "finbert" claim.)*

## State & effects (`STA`)

- `PROV-STA-01` — The provider maintains a **durable, append-only historical price/fact store**
  (graph-resident, ADR-0001). This store is **load-bearing** (DRIFT-001 decision D1): downstream agents
  and backtests read deep history from it. It is a first-class owned responsibility — **not** a
  transparent side-cache.
- `PROV-STA-02` — Side effects are limited to: appending fact/regime records to the store, emitting
  the `market_data_degraded` event on degradation, and emitting metrics/faults. **Nothing else.**
- `PROV-STA-03` — It serves requested history **from the store**, hitting the external feed only to
  **fill or extend** missing ranges. A stored datum must equal what a fresh fetch would yield for the
  same as-of (the store never diverges from source-of-truth).
- `PROV-STA-04` — **Freshness law:** every stored datum carries its as-of / fetch-time; the provider
  **never serves a stale datum as fresh** — a stale or missing range is flagged in the quality record
  (`PROV-OUT-03`), never hidden, never fabricated.
- `PROV-STA-05` — **No carried decision state** between requests (the store holds *facts*, never
  decisions).

## Determinism & idempotency (`IDM`)

- `PROV-IDM-01` — Given the **same request and the same underlying external data**, the validated
  output (facts + quality classification) is **identical**. The feed is a non-deterministic input; the
  provider bounds it by **stamping fetch-time + source provenance** so the result is reproducible
  *given the recorded inputs*.
- `PROV-IDM-02` — **Re-processing is safe**: the same request re-served yields a fresh, independently
  valid record (no corruption, no duplicated meaning), distinguished by its own provenance/timestamp.

## Ordering & concurrency (`ORD`)

- `PROV-ORD-01` — Requests are **independent**; order is irrelevant; no request depends on a prior one.
- `PROV-ORD-02` — **Concurrency-safe**: no shared mutable decision state; concurrent requests each
  produce their own record.
- `PROV-ORD-03` — **Duplicate/late** requests are each served independently with no harm (per
  `PROV-IDM-02`).

## Failure, recovery & rollback (`FAIL`)

- `PROV-FAIL-01` — A failure to reach or parse a source is **contained at the boundary**: it degrades
  to an honest "degraded/unavailable" quality record (or a typed fault) — never a crash, never bad
  data passed as good.
- `PROV-FAIL-02` — **Partial failure** (some tickers/fields available, others not) → a **partial
  response** with the missing parts flagged; honesty is per-item.
- `PROV-FAIL-03` — **Recoverable**: a failed request leaves **no corrupt state** (append-only; a
  degraded record is itself a valid record). Retrying is safe.
- `PROV-FAIL-04` — **No rollback** is required or possible — effects are append-only; a superseding
  fresh fetch is the correction, not a mutation.
- `PROV-FAIL-05` — When the feed dependency is **unhealthy** (`DEP-FEED` red) the provider **fails
  loud** (degraded/fault); it does not fabricate or guess.

## Type alignment (`TYP`)

- `PROV-TYP-01` — It emits exactly the **response types its consumers' contracts expect** — no drift
  between what it produces and what the pipeline consumes.
- `PROV-TYP-02` — **Money/prices are exact** (integer minor units or decimals), never lossy floats
  where money is concerned; all units explicit.
- `PROV-TYP-03` — The contract is **versioned**; an unsupported request shape → typed rejection, never
  a guess.

## Security & privilege (`SEC`)

- `PROV-SEC-01` — **Not root/admin.** It runs at least privilege. Its *only* elevated authority is
  custody of market-data credentials — justified solely because it is the single data boundary. It
  holds **nothing else** (no broker creds, no model creds, no graph authority beyond its own labels).
- `PROV-SEC-02` — **Sole holder** of market-data API keys; injected, never hard-coded; **never**
  logged, returned, or embedded in any response or error.
- `PROV-SEC-03` — **Cannot escalate**: cannot grant itself capabilities, cannot widen its endpoint set
  at runtime, cannot write outside its labels.
- `PROV-SEC-04` — **Blast radius if compromised**: at worst it can poison inbound data or burn the
  data-API quota. It **cannot** place a trade, approve an order, move funds, or alter a decision —
  those authorities live in other sealed agents; downstream validation + the quality record bound the
  reach of any poison.
- `PROV-SEC-05` — **Confused-deputy guard**: it validates every request; no crafted request can make
  it fetch an arbitrary URL or exceed its declared endpoints/fields.
- `PROV-SEC-06` — **Egress restricted** to declared market-data endpoints only.
- `PROV-SEC-07` — **Authorization**: only callers permitted by the capability matrix may invoke it; it
  does not serve arbitrary senders.
- `PROV-SEC-08` — **Containment**: it is independently disableable/quarantinable; with it down the
  system degrades (no fresh data) but never corrupts.

## Dependencies (`DEP`)

- `PROV-DEP-01` — External market-data feed(s) → `DEP-FEED-*` green (else `PROV-FAIL-05`).
- `PROV-DEP-02` — Graph store (append records) → `DEP-POSTGRES-*` green.
- `PROV-DEP-03` — Message bus (receive request / send response) → `DEP-BUS-*` green.
- `PROV-DEP-04` — Clock/time source (fetch-time, staleness) → `DEP-CLOCK-*` green.
- `PROV-DEP-05` — Config/secrets (API keys) → `DEP-CONFIG-*` green.

## Observability & audit (`OBS`)

- `PROV-OBS-01` — Every served fact is **reconstructable from the graph** (provenance + quality
  record).
- `PROV-OBS-02` — It emits throughput/latency metrics and routes faults to the **central fault
  channel** with provenance.
- `PROV-OBS-03` — Degradation is **observable** (the quality record is queryable), never buried in a
  "successful-looking" empty response.

## Performance envelope (`PERF`)

- `PROV-PERF-01` — Every external call is bounded by an **explicit timeout** — no unbounded hangs.
- `PROV-PERF-02` — A request over *N* tickers completes within a stated budget; latency is dominated
  by the external feed and is surfaced in metrics.

## Capability declaration (`CAP`)

*What this agent needs from the runtime to perform its function. Describes interfaces, not products.
This section is the design-time source of truth; the EHLO payload sent to the master agent at
startup is derived from it. See `docs/decisions/0007-container-per-agent-master-bootstrap.md`.*

```json
{
  "messaging": {
    "subscribe": {
      "topics": ["market_data_requests", "regime_requests"],
      "operations": ["consume"],
      "delivery": "at_least_once"
    },
    "publish": {
      "topics": ["market_data_ready", "market_data_degraded"],
      "operations": ["produce"],
      "delivery": "at_least_once"
    },
    "schema_version": "1.0"
  },
  "graph_store": {
    "operations": ["read", "append"],
    "owns_labels": ["MarketSnapshot", "Regime", "Ticker"],
    "access": "exclusive_write_own_labels"
  },
  "external_http": {
    "sources": 4,
    "protocol": "HTTPS_only",
    "operations": ["GET"],
    "auth": "api_key_per_source"
  },
  "secrets": {
    "keys": ["api_key_per_data_source"],
    "access": "read_at_startup",
    "min_privilege": true
  }
}
```

- **messaging** — consumes market-data and regime request events; publishes `market_data_ready`
  (claim-check graph ref, ADR-0005) and `market_data_degraded` (observer push).
- **graph_store** — append-write to its three owned labels; read to check historical coverage and
  staleness before deciding whether to fetch.
- **external_http** — four read-only HTTPS sources (primary OHLCV, validation/failover,
  fundamentals + news + benchmark, vendor sentiment). One API key per source. Provider is the
  **only** agent that may hold or use data-feed credentials (`PROV-SEC-01`, `PROV-SEC-02`).
- **secrets** — one API key injected per source at startup by the master agent; never stored
  beyond the process lifetime, never returned in any response or log.

## Parameters (`PARAM`)

*Every constant used in agent code — both env-overridable tunables and hard-coded values —
documented with schema, rationale, and `tunable`/`non-tunable` classification.
See `docs/decisions/0007-container-per-agent-master-bootstrap.md`.*

All tunable parameters are env-overridable via the `PROVIDER_` prefix and carry a `why=` rationale
in `settings.py`. **Tunable** = safe to adjust for operational experiments without altering
semantic contract. **Non-tunable** = structural; changing the value changes what the agent *means*.

**Regime policy defaults** (published to downstream as `Regime.defaults`):

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `base_min_confidence` | `0.60` | `float [0.0, 1.0]` | YES | Default downstream confidence floor from the reference policy. |
| `base_stop_loss_pct` | `0.05` | `float [0.0, 0.08]` | YES | Reference protective stop; bounded below the PRD maximum risk cap. |
| `base_take_profit_pct` | `0.10` | `float [0.01, 1.0]` | YES | Reference reward target paired with the default stop-loss policy. |
| `base_max_holding_days` | `10` | `int days [1, 60]` | YES | Short tactical holding window used until agent scorecards tune it. |

**Data validation thresholds:**

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `max_daily_move_sigma` | `4.0` | `float sigma [0.1, 20.0]` | YES | Flag daily returns that are extreme relative to the requested window. |
| `max_staleness_days` | `3` | `int days [0, 30]` | YES | Market data older than three sessions flagged as stale. |

**VIX regime thresholds:**

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `vix_risk_on_threshold` | `15.0` | `float [0.0, 100.0]` | YES | Low-volatility VIX level where risk-on regime applies. |
| `vix_risk_off_threshold` | `20.0` | `float [0.0, 100.0]` | YES | Elevated VIX level where new-risk posture should tighten. |
| `vix_high_threshold` | `25.0` | `float [0.0, 100.0]` | YES | High-volatility VIX level from the reference regime gate. |
| `vix_extreme_threshold` | `35.0` | `float [0.0, 150.0]` | YES | Extreme-volatility VIX level from the reference regime gate. |

**Request limits:**

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `finnhub_news_lookback_days` | `7` | `int days [1, 90]` | YES | Trailing window of company news to fetch; recent headlines only, not the full OHLCV lookback. |
| `max_news_per_ticker` | `20` | `int [1, 100]` | YES | Cap headlines per ticker so a noisy feed cannot dominate the downstream sentiment pillar. |
| `finnhub_request_budget_per_minute` | `55` | `int requests/minute [0, 600]` | YES | Pace per-ticker Finnhub calls just under the 60 req/min free-tier cap; `0` disables pacing for controlled proofs. |
| `finnhub_degraded_note_ticker_cap` | `5` | `int [1, 50]` | YES | Bound attributed feed-degradation notes while naming representative tickers. |

**Network timeouts:**

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `finnhub_timeout` | `10` | `int seconds [1, 60]` | YES | Bound the Finnhub fundamentals HTTPS call so a slow feed cannot hang the run. |
| `fmp_timeout` | `15` | `int seconds [1, 60]` | YES | Bound the FMP EOD HTTPS call so a slow feed cannot hang the run. |
| `tiingo_timeout` | `15` | `int seconds [1, 60]` | YES | Bound the Tiingo EOD HTTPS call so a slow feed cannot hang the run. |
| `alphavantage_timeout` | `25` | `int seconds [1, 60]` | YES | Bound the Alpha Vantage sentiment call; AV is slower than other feeds at peak hours. |

**Service base URLs (non-tunable — changing routes to a different service entirely):**

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `finnhub_base_url` | `https://finnhub.io/api/v1` | `str` | NO | Finnhub REST API v1 root; structural — changing connects to a different service. |
| `fmp_base_url` | `https://financialmodelingprep.com` | `str` | NO | FMP REST API root; structural — changing connects to a different service. |
| `tiingo_base_url` | `https://api.tiingo.com` | `str` | NO | Tiingo REST API root; structural — changing connects to a different service. |
| `alphavantage_base_url` | `https://www.alphavantage.co` | `str` | NO | Alpha Vantage REST API root; structural — changing connects to a different service. |

## Divergence register

The master worklist is [`docs/laws/drift-register.md`](../../../docs/laws/drift-register.md). Provider
status:

- **DECIDED & applied** — DRIFT-001 (cache is load-bearing → `PROV-STA-01..04`), DRIFT-002 (sentiment
  is downstream → `PROV-NEV-08`; `mission.md` corrected), DRIFT-003 (FRED/EDGAR in-law deferred →
  `PROV-IN-06`), DRIFT-004 (regime policy inputs → `PROV-OUT-02`), DRIFT-005 (degraded event →
  `PROV-OUT-06`).
- **CORRECTED (S69)** — DRIFT-006 (`PROV-OUT-01`: benchmark added as `DataRequest.benchmark_ticker` +
  `MarketData.benchmark`; `taint=False` for clean candidate quality; analyst uses `market.benchmark`
  directly), DRIFT-007 (`PROV-SEC-07`: `caller_authorized` gate in all three buses; provider
  capability matrix enforced; `test_provider_reconcile.py` covers both).

## Changelog

- v0 — drafted in ideal-design mode (template stress-test).
- v0.1 — reconciled with PRD/mission via forced decisions D1–D3: cache **load-bearing**
  (`STA-01..04`, `IDN-03`); sentiment **downstream** (`NEV-08`); FRED/EDGAR **in-law, deferred**
  (`IN-06`); regime **policy inputs** (`OUT-02`) and **degraded event** (`OUT-06`) adopted. Still
  **DRAFT (in cycle, not locked)** — locks after the full test cycle (conventions §11).
- v0.2 — inter-agent comms model settled (ADR-0005, DRIFT-008): **synchronous RPC** confirmed.
  *(Reversed in v0.3.)*
- v0.3 — comms **re-decided after owner review** (ADR-0005 rewritten): **event-driven pub/sub over
  Azure Service Bus, claim-check**. `PROV-TRG-01` (consume a data-request event) and `PROV-OUT-01`
  (write to store → publish `ready: <ref>`) updated; the durable store (`STA-01..04`) is now also the
  **hand-off** medium (consumer reads it by ref), not only later-pickup. Remaining `OUT`/`IDM` clauses
  still phrased around a "response" — reconciled fully when the provider cycle resumes.
- v0.4 — `CAP` and `PARAM` sections added (ADR-0007, S53): runtime capability declaration (4
  interface categories: messaging, graph_store, external_http, secrets) and full parameter table
  (20 entries — 16 tunable, 4 non-tunable base URLs).
- **v1 — LOCKED (S69)**: full test cycle complete. DRIFT-006 corrected (benchmark as first-class
  `DataRequest` field; `taint=False` isolation). DRIFT-007 corrected (`caller_authorized` gate in all
  three buses + provider capability matrix). Citation pass complete across all provider test files;
  `test-plan.md` bound with 23 green clauses / 43 total. **This law is now the authoritative
  specification; copy template to other agents starting here.**
