<!-- Authored in ideal-design mode (intent, not code). Template: docs/laws/_TEMPLATE.md -->

# Provider — Laws

**Prefix:** `PROV` · **status:** DRAFT v0 (template stress-test) · **Owner:** Yury Gurevich

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
  (single writer for those labels).

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

## Triggers (`TRG`)

- `PROV-TRG-01` — **Purely reactive**: it acts only on an inbound request (request/response). 
- `PROV-TRG-02` — It **never self-triggers** — no polling, no scheduled fetches, no speculative
  prefetch absent a request.
- `PROV-TRG-03` — Precondition to fetch is a **valid** request; otherwise it rejects and does not
  fetch.

## Outputs (`OUT`)

- `PROV-OUT-01` — For a market-data request → a **market-data response** carrying the validated facts
  for the requested fields, **plus an honest data-quality record** (requested vs. returned, stale or
  missing items, whether a fallback was used) **plus provenance**.
- `PROV-OUT-02` — For a regime request → a **regime context** (the classification and the inputs
  behind it) plus provenance.
- `PROV-OUT-03` — The output space is **total**: **SUCCESS** (clean), **DEGRADED** (partial/stale/
  missing — a *valid* response with the shortfall flagged, never silently empty), **FAULT** (the
  boundary itself failed → a typed error, recorded). Exactly one of these, always one of these.
- `PROV-OUT-04` — Every served fact carries **provenance** (source, fetch-time, transformation) so any
  downstream output is reconstructable.
- `PROV-OUT-05` — Graph effects are **append-only**: a new market-fact/regime record per request; it
  never overwrites or mutates a prior record.

## Prohibitions (`NEV`)

- `PROV-NEV-01` — Never emit **unvalidated or silently-degraded** data; degradation is always flagged.
- `PROV-NEV-02` — Never make a **decision** — no scoring, ranking, sizing, ordering, or exit logic.
- `PROV-NEV-03` — Never call any external system other than its **declared market-data endpoints**.
- `PROV-NEV-04` — Never **expose, log, or return** a credential.
- `PROV-NEV-05` — Never **import or call another agent**; never write outside its owned labels.
- `PROV-NEV-06` — Never **mutate** a prior record (append-only; corrections are new records).
- `PROV-NEV-07` — Never **fabricate** a value to fill a gap (a gap is reported, not invented).

## State & effects (`STA`)

- `PROV-STA-01` — **No carried decision state** between requests. Any cache is a transparent
  performance optimisation that **must not change** the validated result versus a fresh fetch, and
  every cache entry carries its own freshness + provenance.
- `PROV-STA-02` — Side effects are limited to: appending a market-fact/regime record to the graph, and
  emitting metrics/faults. Nothing else.

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
- `PROV-DEP-02` — Graph store (append records) → `DEP-NEO4J-*` green.
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

## Divergence register

| ID | Law says | PRD / mission / code may say | Decision needed |
| --- | --- | --- | --- |
| PROV-STA-01 | Cache is optional perf; must not change the result; not core. | PRD §4.3 frames caching/RAG as a first-class store feature. | Confirm cache is non-load-bearing for the provider's *correctness* law. |
| PROV-OUT-01 | Benchmark series is **just another requested field** of a market-data request. | Code (S38) fetched the benchmark via a *separate* request to dodge a degraded-quality trip. | Confirm the **law** (benchmark is a field); the separate-request is an implementation tactic to reconcile to it later. |
| PROV-IN-01 | Provider serves **only the fields requested**. | Reconcile whether all callers pass an explicit field set. | Confirm; flag any caller relying on implicit defaults. |
| PROV-SEC-07 | Only capability-matrix-authorized callers may invoke it. | Verify the matrix actually gates data requests (vs. open to any pipeline agent). | Confirm enforcement point at reconciliation. |

## Changelog

- v0 — drafted in ideal-design mode as the template stress-test. **Not yet locked.**
