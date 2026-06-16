# Provider — Test plan (living)

Each row pins one law-ID to a **functional test** that proves it across the relevant input/output
space. This document is the **master**: discovering a needed test with no law → add the law to
[`laws.md`](laws.md) first (new ID), then add a row here. A functional test's docstring **cites the
law-ID** it proves (conventions §7).

Status: ⬜ gray (no passing test) · 🟩 green (≥1 passing test cites the ID) · ⛔ blocked (gray dep).

**Precondition:** every row is ⛔ until the provider's dependencies are green —
`DEP-FEED, DEP-NEO4J, DEP-BUS, DEP-CLOCK, DEP-CONFIG` (see `docs/laws/dependencies.md`).

## Inputs / triggers

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-IN-01 | A valid market-data request is accepted and serves exactly the requested fields. | happy | _tbd_ | ⬜ |
| PROV-IN-03 | Empty tickers / bad window / unsupported field → typed rejection, no crash, no empty-success. | boundary ×3 | _tbd_ | ⬜ |
| PROV-IN-04 | A request naming an undeclared endpoint / extra field is refused, not honoured. | adversarial | _tbd_ | ⬜ |
| PROV-IN-05 | Identical request from two different sender roles yields identical handling. | invariance | _tbd_ | ⬜ |
| PROV-TRG-01 | No output is produced without an inbound request. | negative | _tbd_ | ⬜ |
| PROV-TRG-02 | Idle (no request) ⇒ zero external calls, zero records. | negative | _tbd_ | ⬜ |

## Outputs (total space)

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-OUT-01 | Response carries validated facts + quality record + provenance for the requested fields. | happy | _tbd_ | ⬜ |
| PROV-OUT-02 | Regime request → regime context + its inputs + provenance. | happy | _tbd_ | ⬜ |
| PROV-OUT-03a | Clean feed → SUCCESS quality. | success | _tbd_ | ⬜ |
| PROV-OUT-03b | Stale/missing feed → DEGRADED, flagged, still a valid (non-empty-silent) response. | degraded | _tbd_ | ⬜ |
| PROV-OUT-03c | Boundary failure → typed FAULT, recorded. | fault | _tbd_ | ⬜ |
| PROV-OUT-04 | A served fact's provenance lets you reconstruct source + fetch-time. | audit | _tbd_ | ⬜ |
| PROV-OUT-05 | A second request appends a new record; the prior record is unchanged. | append-only | _tbd_ | ⬜ |

## Prohibitions

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-NEV-01 | A degraded fetch never yields an unflagged "clean" response. | degraded | _tbd_ | ⬜ |
| PROV-NEV-03 | No call is made to any non-declared endpoint (egress assertion). | adversarial | _tbd_ | ⬜ |
| PROV-NEV-04 | No credential appears in any response, log line, or error. | leak-scan | _tbd_ | ⬜ |
| PROV-NEV-05 | Boundary meta-test: provider imports no agent; writes only its own labels. | static + runtime | _tbd_ | ⬜ |
| PROV-NEV-06 | An attempt implying overwrite of a prior record does not mutate it. | append-only | _tbd_ | ⬜ |
| PROV-NEV-07 | A missing datum is reported as missing, never filled with a fabricated value. | degraded | _tbd_ | ⬜ |

## State / idempotency / ordering

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-STA-01 | Cached vs. fresh fetch of the same data produce the same validated result. | invariance | _tbd_ | ⬜ |
| PROV-IDM-01 | Same request + same stubbed feed ⇒ byte-identical validated output. | determinism | _tbd_ | ⬜ |
| PROV-IDM-02 | Re-running a request yields a fresh valid record, no corruption/dupe-meaning. | idempotency | _tbd_ | ⬜ |
| PROV-ORD-02 | Two concurrent requests each produce their own correct record. | concurrency | _tbd_ | ⬜ |

## Failure / recovery

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-FAIL-01 | Unreachable/garbled source → degraded/fault, never crash, never bad-as-good. | fault | _tbd_ | ⬜ |
| PROV-FAIL-02 | Mixed availability → partial response, missing parts flagged per-item. | partial | _tbd_ | ⬜ |
| PROV-FAIL-03 | After a failed request, a retry succeeds; no corrupt state remained. | recovery | _tbd_ | ⬜ |
| PROV-FAIL-05 | DEP-FEED red ⇒ fail-loud (degraded/fault), no fabrication. | dep-red | _tbd_ | ⬜ |

## Type alignment

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-TYP-01 | Output types equal the consumer contracts' expected types (no drift). | contract | _tbd_ | ⬜ |
| PROV-TYP-02 | Money/prices are exact (no lossy float); units explicit. | precision | _tbd_ | ⬜ |
| PROV-TYP-03 | Unsupported request shape → typed rejection, not a guess. | boundary | _tbd_ | ⬜ |

## Security

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-SEC-01 | It holds no authority beyond data-feed creds + its own labels (privilege inventory). | audit | _tbd_ | ⬜ |
| PROV-SEC-02 | Keys are injected, never present in outputs/logs/errors. | leak-scan | _tbd_ | ⬜ |
| PROV-SEC-04 | A poisoned/over-broad request cannot cause a trade/order/fund effect (blast-radius). | adversarial | _tbd_ | ⬜ |
| PROV-SEC-05 | A crafted request cannot redirect egress to an arbitrary URL (confused-deputy). | adversarial | _tbd_ | ⬜ |
| PROV-SEC-07 | An unauthorized caller is refused by the capability gate. | authz | _tbd_ | ⬜ |

## Observability / performance

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-OBS-02 | A boundary fault appears on the central fault channel with provenance. | fault | _tbd_ | ⬜ |
| PROV-OBS-03 | Degradation is queryable from the graph, not buried. | degraded | _tbd_ | ⬜ |
| PROV-PERF-01 | A hanging source is cut off at the timeout, not waited on indefinitely. | timeout | _tbd_ | ⬜ |

> Rows are intentionally implementation-agnostic. At **reconciliation**, each `_tbd_` becomes a real
> `agents/provider/tests/…::test_name`; if the code can't satisfy a row, that is a drift finding —
> fix the code, or (if the law is genuinely lacking) amend `laws.md` with a version bump.
