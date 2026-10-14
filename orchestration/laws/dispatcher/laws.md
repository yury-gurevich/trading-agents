# `Dispatcher` — Laws

**Prefix:** `DSP` · **status:** LOCKED v1.3 · **Owner:** Yury Gurevich

> Decide whether the scheduled daily graph-pull run is placed, skipped, held, or placed in degraded posture,
> brief the operator once on each run it placed, and tell the operator when a container of the
> fleet fails to start, crashes or is killed, and why.

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
  book governs `scheduled_dispatch*.py`, readiness gating, hold answers, notices, the daily brief
  (`orchestration/daily_brief*.py`, `DSP-IDN-04`) and the container sensor
  (`orchestration/container_*.py`, `DSP-IDN-05`). *(DRIFT-077.)*
- **DSP-IDN-04** — The scheduled dispatcher sends one daily brief per scheduled run it placed
  (`orchestration/daily_brief*.py`): a plain-text report to the operator of what the run did. It
  reports and never decides: no brief changes a placement, a hold, a notice, or any fact another
  component owns.
- **DSP-IDN-05** — The scheduled dispatcher runs the container sensor (`orchestration/container_*.py`,
  DL-301): on each fire it reads the platform's container events from the log workspace, records the
  ones it keeps and tells the operator of each alarm once. It reports and never decides: no sensor read
  changes a placement, a hold, a notice, the brief's other lines, or any container.

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
- **DSP-IN-05** — The sensor's input is the rows of the workspace's `ContainerAppSystemLogs_CL` that
  reached it inside the read window, read by their ingestion time, and for an alarm's why the stderr
  lines of `ContainerAppConsoleLogs_CL` of the same replica. A row is an alarm (a failed start or a
  failed scale-up, a revision that failed to provision, a scale rule the scaler refused, a memory kill,
  an exit with code 137, any other exit whose code is not 0 or cannot be read, any other row the
  platform marks `error`), a report (a preemption, or a node scale-down that moved a replica), or
  nothing; an exit with code 0 is nothing. The app is the row's app or job name, else its revision's
  name less the revision suffix, else `unknown`.

## Triggers (`TRG`)

- **DSP-TRG-01** — A cron fire may place a run only inside the action window
  `_ACTION_START=22:30 UTC` through `_ACT_BY=23:20 UTC`. A late `run_now` answer remains evidence but
  cannot place a run.
- **DSP-TRG-02** — Calendar skip is evaluated before readiness, Telegram polling, notices, or hold
  writes.
- **DSP-TRG-03** — Every fire whose `as_of` is its own UTC date attempts that day's brief after the
  calendar skip and before the action-window return, so fires after `_ACT_BY` attempt it too; a fire
  for a past session briefs nothing. It sends once the run's `Snapshot` exists. On the day's last fire
  (`LAST_FIRE=23:50 UTC`, the cron's last tick) a placed run with no `Snapshot` gets one RED brief
  instead. A skipped run, or a held run with no `RunRequest`, gets no brief.
- **DSP-TRG-04** — Every fire runs the sensor once, after its dispatch, whatever the dispatch's
  outcome: placed, skipped, held, or failed. With no `LOG_ANALYTICS_WORKSPACE_ID` in the job's
  environment the sensor does nothing and the fire's output is unchanged. A read ends at the fire's
  time and starts `container_sensor_overlap_minutes` before the previous successful read ended; the
  first read starts `container_sensor_first_read_hours` back, and no read starts further back than
  `container_sensor_max_lookback_hours`.

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
- **DSP-OUT-06** — A brief is plain text, with the fire's time in the operator's zone (UTC only
  without zone data). It carries the pack's acceptance verdict (`accept_run`) and a `degraded` mark
  for a degraded run; the equity the run's `Snapshot` stored and its change since the previous
  scheduled run with a `Snapshot` (by `PMRun.created_at`), or that there is no figure; the benchmark
  clause of the `Snapshot`'s `headline_summary`; the orders the run placed; the fills that became
  known (`broker_status_refreshed_at`) since that previous run, a resting stop's fill read as stopped
  out; and the open incidents and critical flags the supervisor's health derives. Every figure is read
  as stored, never recomputed. A RED brief says the run did not finish, names the last stage that
  finished, and carries the run's orders and the same needs-you counts.
- **DSP-OUT-07** — A sensor read writes one `ContainerEvent` for each new row it keeps (app, revision,
  replica, kind, whether it is an alarm, the platform's reason and message, the exit code when there is
  one, the repeat count, when it happened, the why line for an alarm, the read that found it) and one
  `ContainerSensorRead` (its window; the rows it read; what it recorded, its alarms and reports; how
  many it told, and its message id or why the message was not sent; whether the look-back cap or the
  row limit cut it). When alarms are untold it sends one plain-text message for all of them, one line
  per kind of failure (a kind and an exit code) across apps (DL-301 D5): first how many apps and how
  many kinds; then each kind, newest first, with its apps (four named, the rest counted), its repeat
  count when above one (each replica's highest count, summed), its latest time in the operator's zone
  with UTC beside it (UTC alone when the zone cannot be read), and under it the why line of its latest
  alarm that has one, naming that alarm's app; at most `container_sensor_alarm_groups_max` kinds, the
  remaining kinds counted; and a note when the cap cut the read.
- **DSP-OUT-08** — From the sensor's first read on, every brief carries one container line before
  needs-you: that the sensor's latest read failed and why; or that it has not read in 24 hours; or that
  it recorded no alarm in 24 hours; or how many alarms it recorded in 24 hours, repeats counted as in
  `DSP-OUT-07`, naming at most three kinds of failure with their apps and counting the rest. Before the
  first read the brief carries no such line.

## Prohibitions (`NEV`)

- **DSP-NEV-01** — The scheduled dispatcher never writes master-owned `FleetPreflight` evidence.
- **DSP-NEV-02** — The scheduled dispatcher never talks to the broker, never chooses tickers beyond
  the configured universe membership, and never decides what to buy, sell, size, or veto.
- **DSP-NEV-03** — The sensor never acts on a container: it starts, stops, scales, restarts and
  reconfigures nothing, and calls no management API. It reads the log workspace and tells.

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
- **DSP-IDM-03** — At most one brief per run id. A fire sends only while the run's `RunRequest`
  carries no `brief_sent_at`; a successful send writes `brief_sent_at`, `brief_message_id`, and
  `brief_verdict` (the verdict the brief carried, `NOT_FINISHED` for a RED brief) on that
  `RunRequest`. A failed send writes nothing, so a later fire retries.
- **DSP-IDM-04** — A row read twice is recorded once: a `ContainerEvent`'s key is a digest of the row's
  own fields. Each alarm is told by one message: a sent message adds a `TOLD` edge from its
  `ContainerSensorRead` to every alarm it told. An alarm whose message was not sent stays untold and
  is told by a later fire's message, while it was recorded less than
  `container_sensor_max_lookback_hours` before that fire.

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
- **DSP-FAIL-03** — Composing or sending a brief can fail only into a fault: an exception, a send the
  port reports failed, or a brief module the image lacks becomes one `Fault`, and the fire goes on. A
  brief never changes the placement outcome and never crashes the fire.
- **DSP-FAIL-04** — The sensor can fail only into its own records and its own line. Once the graph is
  open, a workspace read that fails, a missing managed identity, a sensor module the image lacks (the
  script imports only `container_sensor_guard`), or a graph write that fails becomes one `Fault` and a
  failed `ContainerSensorRead`; a graph that refuses even those gets an error line on stderr. A
  message the port reports unsent is a `Fault` too. Before the graph is open (no `POSTGRES_DSN`, or
  settings, a reader or a graph that cannot be built) the sensor prints one error line and records
  nothing. The fire's placement and its exit code are never changed by the sensor, and a failed read
  does not move the next read's start.

## Type alignment (`TYP`)

- **DSP-TYP-01** — `ScheduledDispatchResult` is the dispatcher output contract and its action space
  is exactly `placed`, `skipped`, or `held`, with readiness details present only when relevant.

## Security & privilege (`SEC`)

- **DSP-SEC-01** — Telegram credentials are held by the injected Telegram port; scheduled-dispatch
  logic receives only the port interface and never logs or returns raw credentials.
- **DSP-SEC-02** — P&L amounts leave the dispatcher only in the daily brief, only to the configured
  operator chat, and only through the injected Telegram port (DL-230). The job's printed output and
  every fault carry no amount: a brief's fault names its step and an error type, never a value.
- **DSP-SEC-03** — The sensor reads as the job's system-assigned managed identity, which holds the role
  Log Analytics Reader on the one log workspace and nothing else; no credential for it is stored
  anywhere. A console line leaves only with credentials in a URL, named secrets, bearer tokens, runs of
  32 or more token characters and amounts masked, and cut to 160 characters. A printed line, a fault
  and a read record name a failure by its error type and a status word, never a reply body, a query or
  a token. Only a replica name that matches the platform's naming rule is put into a query.

## Dependencies (`DEP`)

- **DSP-DEP-01** — The scheduled dispatcher depends on the graph store (`DEP-POSTGRES`), UTC clock
  (`DEP-CLOCK`), provider-owned market calendar, configured universe source, and Telegram port for
  optional operator notices, answers, and the daily brief. For the brief its graph reads include the
  run's chain to its `Snapshot`, `Fill`, `Fault` and `Flag` facts with their resolutions, and the
  pack's acceptance verdict. The sensor depends on the job's managed-identity endpoint and the log
  workspace's query API.

## Observability & audit (`OBS`)

- **DSP-OBS-01** — Holds, releases, answers, notices, degraded-posture causes, and Telegram faults are
  reconstructable from graph facts and returned dispatcher results.
- **DSP-OBS-02** — Human notice deadlines name the operator's Melbourne time first and include the
  UTC deadline as a fallback.
- **DSP-OBS-03** — Each sensor run prints one line: the rows read, the new events, the alarms and how
  many were told, or the failure. Every alarm and report the sensor kept, and every read, is
  reconstructable from `ContainerEvent` and `ContainerSensorRead` facts and their `TOLD` edges.

## Performance envelope (`PERF`)

- **DSP-PERF-01** — Human override placement is bounded to the 22:30-23:20 UTC action window; outside
  that window the dispatcher does not begin a run.

## Capability declaration (`CAP`)

```json
{
  "graph": {
    "operations": ["read", "append_write"],
    "labels_owned": ["RunHold", "ContainerEvent", "ContainerSensorRead"],
    "labels_written": [
      "RunRequest", "RunHold", "RunHoldAnswer", "Fault", "ContainerEvent", "ContainerSensorRead"
    ],
    "labels_read": [
      "FleetPreflight", "RunRequest", "RunHold", "RunHoldAnswer", "MarketData", "ScanRun",
      "AnalystRun", "PMRun", "DeliberationRun", "OrderIntent", "ExecutionRun", "MonitorRun",
      "Snapshot", "Fill", "Fault", "FaultResolution", "Flag", "FlagResolution",
      "BrokerPositionSnapshot", "ContainerEvent", "ContainerSensorRead"
    ],
    "access": "bounded dispatcher placement; the brief marks only its own RunRequest"
  },
  "log_workspace": {
    "operations": ["query"],
    "access": "managed identity; Log Analytics Reader on one workspace"
  },
  "calendar": {
    "operations": ["read_session_status"],
    "source": "provider-owned NYSE calendar"
  },
  "telegram": {
    "operations": [
      "send_notice", "poll_answer", "ack_answer", "confirm_offset", "send_brief", "send_alarm"
    ],
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
| `container_sensor_first_read_hours` | `24` | `int >= 1 <= 168` | YES | The first read covers one day: the day's deploys are seen, and a month of old events does not arrive as one alarm. |
| `container_sensor_max_lookback_hours` | `168` | `int >= 24 <= 720` | YES | A read after a long gap covers at most a week of the workspace's 30 days. |
| `container_sensor_overlap_minutes` | `10` | `int >= 3 <= 60` | YES | An event reached the workspace up to 2 min 36 s late (measured 2026-10-14); a row read twice is recorded once. |
| `container_sensor_alarm_groups_max` | `8` | `int >= 1 <= 20` | YES | One alarm message stays readable and inside Telegram's limit; the rest are counted. |
| `container_sensor_timeout_seconds` | `20.0` | `float >= 1.0 <= 120.0` | YES | A slow workspace read cannot hold the fire. |

## Divergence register

| ID | Law says | PRD / mission / code says | Decision needed |
| --- | --- | --- | --- |
| — | No S229 dispatcher divergence found. | The served-path `orchestration.dispatcher.Dispatcher` is named out of scope by DL-221, not contradicted by this book. | Not applicable. |

## Changelog

- v1 — S229 authored dispatcher scheduled-placement and human-hold law book; closed DRIFT-068 and
  DRIFT-069 by declaring the readiness/degraded and notice/answer guarantees.
- v1.1 — S234 (E19.1, DL-230, DL-231): the daily brief. New `DSP-IDN-04`, `DSP-TRG-03`,
  `DSP-OUT-06`, `DSP-IDM-03`, `DSP-SEC-02` (the operator's DL-230 decision that amounts may leave,
  and only here), and `DSP-FAIL-03`; `DSP-DEP-01` and `CAP` amended for the brief's reads, its
  `send_brief` port operation, and `labels_read`. The reporter's security clause is unchanged: the
  reporter still sends nothing (DL-230). This book names no other book's clause IDs, because the
  coverage gate reads every clause-shaped ID in it as this book's own. `DSP-IDN-03`'s scope sentence
  and the purpose line predate the brief (DRIFT-077). `DSP-SEC-01` is now proven across every port
  operation.
- v1.2 — S251 (DL-259, DL-260; DRIFT-077): the purpose line and `DSP-IDN-03`'s scope sentence name the
  daily brief, which `DSP-IDN-04` added in v1.1 without touching either. `DSP-IDN-03` stays ⬜. No
  behaviour change; 32 / 36 unchanged.
- v1.3 — S275 (DL-301, work-queue 119): the container sensor. New `DSP-IDN-05`, `DSP-IN-05`,
  `DSP-TRG-04`, `DSP-OUT-07`, `DSP-OUT-08`, `DSP-NEV-03`, `DSP-IDM-04`, `DSP-FAIL-04`, `DSP-SEC-03` and
  `DSP-OBS-03`; the purpose line, `DSP-IDN-03`'s scope sentence, `DSP-DEP-01`, `CAP` and `PARAM`
  amended for it.
