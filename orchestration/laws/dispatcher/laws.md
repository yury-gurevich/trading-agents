# `Dispatcher` — Laws

**Prefix:** `DSP` · **status:** LOCKED v1 · **Owner:** Yury Gurevich

> Decide whether the scheduled daily graph-pull run is placed, skipped, held, or placed in degraded posture.

Each clause below has a stable ID (`DSP-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

## Identity & purpose (`IDN`)

- **DSP-IDN-01** — The scheduled dispatcher decides one outcome for a scheduled NYSE session:
  place the day-keyed `RunRequest`, skip with an explicit reason, hold because fleet readiness is not
  acceptable, or place a degraded run under the pack-declared exception. It does not sequence the
  downstream trading stages.
- **DSP-IDN-02** — The scheduled dispatcher owns `RunHold` placement decisions and scheduled
  `RunRequest` placement for its own run ids. It reads master-owned `FleetPreflight` facts and never
  owns or rewrites them.
- **DSP-IDN-03** — `orchestration.dispatcher.Dispatcher` is outside this book: it is the older
  event-driven wrapper that publishes `run.trigger` once invoked and records the final snapshot. This
  book governs `scheduled_dispatch*.py`, readiness gating, hold answers, and notices.

## Inputs (`IN`)

- **DSP-IN-01** — Scheduling input is an `as_of` date within the known NYSE calendar. A date beyond
  the calendar raises an explicit `CalendarWindowExceededError`; a non-session date skips before
  readiness or human-answer handling.
- **DSP-IN-02** — Placement requires a non-empty configured universe. An empty universe is an error
  for both normal placement and human `run_now` override placement.
- **DSP-IN-03** — Fleet readiness input is the latest parseable `FleetPreflight` within
  `preflight_max_age_minutes`. Missing, stale, malformed, or non-degradable failed evidence holds the
  run. A failed check degrades only when every failure belongs to a pack-declared degradable agent.
- **DSP-IN-04** — Human answers are only `run_now` or `skip_today`, scoped to the matching scheduled
  `run_id`. Free text, stale run ids, and malformed answer payloads cannot decide today's placement.

## Triggers (`TRG`)

- **DSP-TRG-01** — A cron fire may place a run only inside the action window
  `_ACTION_START=22:30 UTC` through `_ACT_BY=23:20 UTC`. A late `run_now` answer remains evidence but
  cannot place a run.
- **DSP-TRG-02** — Calendar skip is evaluated before readiness, Telegram polling, notices, or hold
  writes.

## Outputs (`OUT`)

- **DSP-OUT-01** — Successful normal placement writes exactly one day-keyed `RunRequest`
  (`run-request:sched-YYYY-MM-DD`) with the selected tickers and no degraded-posture properties.
- **DSP-OUT-02** — A skipped run returns a stated reason and writes no `RunRequest` or `RunHold`.
- **DSP-OUT-03** — A readiness hold writes one active `RunHold` with run id, as-of date,
  readiness state, preflight key, and failures; repeated failing fires reuse the active hold.
- **DSP-OUT-04** — A degraded placement writes `run_posture="degraded"` and `degraded_by` on the
  `RunRequest`, releases any active hold, and leaves normal placements byte-compatible.
- **DSP-OUT-05** — A newly held run sends one operator notice with exactly the two legal answer
  buttons. A degraded placement sends one informational notice and no answer buttons.

## Prohibitions (`NEV`)

- **DSP-NEV-01** — The scheduled dispatcher never writes master-owned `FleetPreflight` evidence.
- **DSP-NEV-02** — The scheduled dispatcher never talks to the broker, never chooses tickers beyond
  the configured universe membership, and never decides what to buy, sell, size, or veto.

## State & effects (`STA`)

- **DSP-STA-01** — `RunHold` facts are append-only: recovery adds `released_at`, and a later re-hold
  creates a new key rather than mutating a released hold into active evidence.
- **DSP-STA-02** — Telegram send, poll, ack, and confirm failures are contained as graph faults and
  do not crash scheduled dispatch.

## Determinism & idempotency (`IDM`)

- **DSP-IDM-01** — The scheduled run id is deterministic from the session date:
  `sched-YYYY-MM-DD`.
- **DSP-IDM-02** — Re-firing the same scheduled placement is idempotent: ready runs merge to one
  `RunRequest`, and failing runs merge to one active `RunHold`.

## Ordering & concurrency (`ORD`)

- **DSP-ORD-01** — The latest valid `FleetPreflight` wins. Older failures, malformed timestamps, and
  non-string timestamps cannot displace a fresher valid check.
- **DSP-ORD-02** — The first effective answer for a run decides placement. Later answer facts remain
  visible but cannot reverse the first decision; replayed Telegram updates do not duplicate evidence.

## Failure, recovery & rollback (`FAIL`)

- **DSP-FAIL-01** — Telegram-port exceptions or reported protocol errors become durable faults and
  caller-selected fallbacks.
- **DSP-FAIL-02** — An empty configured universe fails loudly rather than placing an empty
  `RunRequest`.

## Type alignment (`TYP`)

- **DSP-TYP-01** — `ScheduledDispatchResult` is the dispatcher output contract and its action space
  is exactly `placed`, `skipped`, or `held`, with readiness details present only when relevant.

## Security & privilege (`SEC`)

- **DSP-SEC-01** — Telegram credentials are held by the injected Telegram port; scheduled-dispatch
  logic receives only the port interface and never logs or returns raw credentials.

## Dependencies (`DEP`)

- **DSP-DEP-01** — The scheduled dispatcher depends on the graph store (`DEP-POSTGRES`), UTC clock
  (`DEP-CLOCK`), provider-owned market calendar, configured universe source, and Telegram port for
  optional operator notices and answers.

## Observability & audit (`OBS`)

- **DSP-OBS-01** — Holds, releases, answers, notices, degraded-posture causes, and Telegram faults are
  reconstructable from graph facts and returned dispatcher results.
- **DSP-OBS-02** — Human notice deadlines name the operator's Melbourne time first and include the
  UTC deadline as a fallback.

## Performance envelope (`PERF`)

- **DSP-PERF-01** — Human override placement is bounded to the 22:30-23:20 UTC action window; outside
  that window the dispatcher does not begin a run.

## Capability declaration (`CAP`)

```json
{
  "graph": {
    "operations": ["read", "append_write"],
    "labels_owned": ["RunHold"],
    "labels_written": ["RunRequest", "RunHold", "RunHoldAnswer", "Fault"],
    "access": "bounded dispatcher placement"
  },
  "calendar": {
    "operations": ["read_session_status"],
    "source": "provider-owned NYSE calendar"
  },
  "telegram": {
    "operations": ["send_notice", "poll_answer", "ack_answer", "confirm_offset"],
    "access": "injected port"
  }
}
```

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `operator_timezone` | `"Australia/Melbourne"` | `str` | YES | The operator reads their own local 24-hour time, never UTC. |
| `universe` | `"sp500"` | `str` | YES | Paper-stage default scan universe when a trigger does not specify one. |
| `provider_max_staleness_days` | `7` | `int >= 0 <= 30` | YES | Daily dispatcher accepts a one-week fixture window across weekends. |
| `pm_starting_cash` | `Decimal("100000.00")` | `Decimal >= 0 <= 1000000000` | YES | Seed paper PM sizing with a deterministic portfolio value. |
| `preflight_max_age_minutes` | `70` | `int >= 10 <= 240` | YES | Require the latest hourly fleet preflight with ten minutes of scheduling slack before placing a trading run. |

## Divergence register

| ID | Law says | PRD / mission / code says | Decision needed |
| --- | --- | --- | --- |
| — | No S229 dispatcher divergence found. | The served-path `orchestration.dispatcher.Dispatcher` is named out of scope by DL-221, not contradicted by this book. | Not applicable. |

## Changelog

- v1 — S229 authored dispatcher scheduled-placement and human-hold law book; closed DRIFT-068 and
  DRIFT-069 by declaring the readiness/degraded and notice/answer guarantees.
