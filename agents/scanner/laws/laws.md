# `Scanner` — Laws

**Prefix:** `SCAN` · **status:** LOCKED v1 · **Owner:** Yury Gurevich

> Reduce the full tradable universe to a small, ranked, explained set of candidates
> worth deeper analysis — nothing more.

Each clause has a stable ID (`SCAN-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

---

## Identity & purpose (`IDN`)

- **SCAN-IDN-01** — The scanner's sole job is universe → ranked candidates. It filters by
  price, volume, relative strength, beta, and earnings proximity; it ranks survivors; it
  records why each ticker was dropped. It never scores by fundamental or sentiment analysis,
  never recommends, and never sizes an order.
- **SCAN-IDN-02** — The scanner exclusively owns the `ScanRun` and `Candidate` graph labels.
  No other agent writes to these labels.

---

## Inputs (`IN`)

- **SCAN-IN-01** — The scanner accepts a `ScanRequest` (fields: `universe: str`, optional
  `run_id: str`). `universe` is a named pack (e.g. `"sp500"`); if absent or unrecognised,
  a `StaticUniverse` is used. A missing `run_id` is generated at receipt.
- **SCAN-IN-02** — In pub/sub mode the scanner subscribes to `run.trigger` events and
  derives a `ScanRequest` from the event payload (`universe`, `run_id`). The trigger event
  is treated as authoritative; unknown extra fields are ignored.
- **SCAN-IN-03** — Malformed or empty input (no universe resolvable, no tickers in the
  universe) → empty `CandidateSet` with an explanatory message. No exception propagates to
  the caller.

---

## Triggers (`TRG`)

- **SCAN-TRG-01** — RPC capability `run_scan`: invoked on demand by any caller in
  `allowed_callers` (see CAP). Pull mode; returns a `CandidateSet` synchronously.
- **SCAN-TRG-02** — Pub/sub: `run.trigger` event auto-invokes `run_scan` and emits a
  `scan.candidates.ready` claim-check event to the bus. This is the primary production
  trigger path.
- **SCAN-TRG-03** — The scanner never self-triggers. Idle (no inbound request or event) →
  zero provider calls, zero graph writes.

---

## Outputs (`OUT`)

- **SCAN-OUT-01** — `run_scan` always returns a `CandidateSet` (never `None`, never raises):
  `run_id`, `candidates`, `filter_trace` (counts every drop), `explanation`, `provenance`.
- **SCAN-OUT-02** — The `FilterTrace` accounts for every ticker in the universe: each dropped
  ticker is attributed to one filter. `universe_size == evaluated + sum(dropped_by_filter)`.
  Silence is always explained.
- **SCAN-OUT-03** — If the provider is unavailable or returns degraded data, the scanner
  returns an empty `CandidateSet` with `dropped_by_filter: {"provider_degraded": N}` and a
  clear explanation. It records a fault to the central channel and writes a `ScanRun` node.
- **SCAN-OUT-04** — In pub/sub mode the outbound `scan.candidates.ready` event carries only
  a claim-check reference, not the `CandidateSet` payload. Data lives in the graph store.
- **SCAN-OUT-05** — `explain_filter` returns a human-readable `Explanation` of all active
  filter thresholds for the requested universe. It does not trigger a provider call or write
  any graph node.

---

## Prohibitions (`NEV`)

- **SCAN-NEV-01** — Never calls a market-data API directly. All price, volume, earnings, and
  benchmark data are requested from the provider agent via the bus.
- **SCAN-NEV-02** — Never scores candidates by fundamental or sentiment analysis. Ranking is
  based on filter-survival and the short-window relative-strength proxy only.
- **SCAN-NEV-03** — Never produces an empty result without explaining why. Every `CandidateSet`
  carries an `explanation` that can be shown to a human or fed upstream.
- **SCAN-NEV-04** — Never writes to graph labels it does not own (`ScanRun`, `Candidate`).
  Provenance from the provider (`MarketDataEvent`) is referenced, not re-written.
- **SCAN-NEV-05** — Never mutates the universe definition at runtime. The universe is read
  from the `StaticUniverse` or the named pack at scan time; it is not cached between calls.

---

## State & effects (`STA`)

- **SCAN-STA-01** — Stateless between calls. No ticker lists, filter results, or market data
  are cached in-process between scan invocations.
- **SCAN-STA-02** — Every `run_scan` call writes a `ScanRun` node and one `Candidate` node
  per surviving ticker. All writes are append-only; prior `ScanRun` records are never
  modified or deleted.
- **SCAN-STA-03** — The scan window (`start`, `end`) is calculated fresh on each call from
  `datetime.now(UTC)` and `lookback_days`. No time state is persisted.

---

## Determinism & idempotency (`IDM`)

- **SCAN-IDM-01** — Given identical `ScanRequest`, `lookback_days`, and provider-returned
  `MarketData`, the filter and ranking logic is fully deterministic: same input → same
  `CandidateSet` (same candidates in the same order).
- **SCAN-IDM-02** — A `run_id` is the provenance key for a scan; it is assigned at trigger
  time (from the event or generated). Re-running with the same `run_id` appends a second
  `ScanRun` rather than overwriting (append-only graph); callers are responsible for not
  duplicating triggers.

---

## Ordering & concurrency (`ORD`)

- **SCAN-ORD-01** — Scan requests are independent of one another; no ordering constraint
  between consecutive runs.
- **SCAN-ORD-02** — The scanner holds no shared mutable state and is safe for concurrent
  requests in the same process, subject to the graph store's own concurrency guarantees.

---

## Failure, recovery & rollback (`FAIL`)

- **SCAN-FAIL-01** — Provider unavailable (timeout or bus error) → empty `CandidateSet`
  returned; fault recorded to the central channel; no exception propagates to the caller.
- **SCAN-FAIL-02** — A per-ticker filter error (e.g. malformed bar) causes that ticker to be
  dropped with an attributed reason; the remaining tickers continue normally.
- **SCAN-FAIL-03** — Graph write failure → fault recorded; an empty or partial `CandidateSet`
  is returned (whichever was computed before the write). Safe to retry: the graph is
  append-only so a repeated write produces a new record, not a corrupt one.

---

## Type alignment (`TYP`)

- **SCAN-TYP-01** — `CandidateSet`, `Candidate`, `FilterTrace`, and `Explanation` match
  `contracts/scanner.py` exactly; `contracts.scanner.CONTRACT.version` is the authoritative
  version string.
- **SCAN-TYP-02** — `Candidate.score` is a dimensionless `float`; `Candidate.rank` is a
  positive `int ≥ 1`. Neither carries a currency unit. `FilterTrace` counts are exact
  non-negative integers summing to `universe_size`.

---

## Security & privilege (`SEC`)

- **SCAN-SEC-01** — The scanner holds no credentials and makes no external API calls. Its
  blast radius if compromised is a stale or manipulated candidate list forwarded to the
  analyst — it cannot move money or access the broker.
- **SCAN-SEC-02** — Only callers in the declared `allowed_callers` list (dispatcher,
  supervisor, operator) may invoke `run_scan`. The bus enforces `caller_authorized` at
  receipt. `explain_filter` is read-only; its `allowed_callers` may be broader.
- **SCAN-SEC-03** — The scanner is quarantinable: removing its `run.trigger` subscription
  or taking its container offline stalls the pipeline without corrupting any persisted state.

---

## Dependencies (`DEP`)

- **SCAN-DEP-01** — `DEP-BUS`: requires a messaging substrate capable of request/reply
  (for provider calls) and subscribe/publish (for `run.trigger` / `scan.candidates.ready`).
- **SCAN-DEP-02** — `DEP-NEO4J`: requires graph append-write access to labels `ScanRun` and
  `Candidate`.
- **SCAN-DEP-03** — `DEP-FEED` (via provider): the provider must be healthy and reachable
  before a scan can produce non-empty candidates. Provider health is a prerequisite for
  meaningful output, not for the scanner's own operation (it degrades gracefully).

---

## Observability & audit (`OBS`)

- **SCAN-OBS-01** — Every `ScanRun` node in the graph is fully reconstructable into the
  `CandidateSet` that was returned, including the `FilterTrace` and the provider provenance
  reference.
- **SCAN-OBS-02** — Faults (provider degradation, filter errors) are routed to the central
  fault channel (`FaultSink`). The degraded path is never silent: it produces an attributed
  empty result and a fault record.

---

## Performance envelope (`PERF`)

- **SCAN-PERF-01** — The scanner's latency budget is dominated by the provider round-trip.
  The scanner itself (filter + ranking) is pure in-process computation with no external I/O;
  it adds negligible latency beyond the provider call.

---

## Capability declaration (`CAP`)

```json
{
  "messaging": {
    "operations": ["request_reply", "subscribe", "publish"],
    "topics": {
      "subscribe": ["run.trigger"],
      "publish": ["scan.candidates.ready"]
    },
    "delivery": "at_least_once",
    "schema_version": "1.0"
  },
  "graph": {
    "operations": ["append_write"],
    "labels": ["ScanRun", "Candidate"],
    "access": "write_own_labels_only"
  }
}
```

**Allowed callers for `run_scan`:** `dispatcher`, `supervisor`, `operator`
**Allowed callers for `explain_filter`:** `dispatcher`, `supervisor`, `operator`, `researcher`

---

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `lookback_days` | `5` | `int ≥ 2, ≤ 252` (days) | YES | Short deterministic first-slice window; broader scans tune this |
| `min_relative_strength` | `0.02` | `float ≥ -1.0, ≤ 5.0` | YES | Require a positive lookback return before deeper analyst work |
| `min_price` | `5.0` | `float ≥ 0.01, ≤ 1000.0` (USD) | YES | Avoid illiquid penny-price names in the first scanner slice |
| `min_average_volume` | `500000.0` | `float ≥ 0` (shares/day) | YES | Require enough daily liquidity for later sizing and execution |
| `candidate_cap` | `5` | `int ≥ 1, ≤ 50` | YES | Keep the first vertical slice small and explainable for analyst handoff |
| `benchmark_ticker` | `"SPY"` | `str` | YES | Relative-strength benchmark; matches the scanner's S&P 500 universe |
| `max_beta` | `2.5` | `float ≥ 0.0, ≤ 10.0` | YES | Exclude names with excessive systematic risk |
| `beta_min_observations` | `3` | `int ≥ 2, ≤ 252` (obs) | YES | Minimum aligned returns before the beta cap is trusted to gate |
| `earnings_exclusion_days` | `5` | `int ≥ 0, ≤ 60` (days) | YES | Exclude names with earnings within this window to avoid gap risk |

---

## Divergence register

| ID | Law says | PRD / code says | Decision needed |
| --- | --- | --- | --- |
| — | — | — | No divergences at DRAFT v0 |

---

## Changelog

- v0 — drafted (ideal-design, S70). Not yet locked.
