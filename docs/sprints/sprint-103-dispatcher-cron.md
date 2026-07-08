<!-- Agent: planning | Role: sprint handover -->
# Sprint 103 — Dispatcher cron: the fleet goes hands-off (fleet arc, final item)

**Phase:** Fleet Activation (DL-30 / DL-35 — the arc's end state: a self-driving platform)
**Branch:** `sprint-103-dispatcher-cron`
**Status:** shipped — merged `6caa2f6` (0.63.00, 2026-07-08); closeout evidence below
**Effort:** M

---

## Design decisions taken at packaging (LAW-06 — roads not taken recorded)

1. **Standing posture: the fleet stays deployed, scaled to zero outside a daily window.** S102
   deleted all 13 apps after its proof; a scheduled run needs the fleet to exist. Chosen: keep the
   13 Container Apps deployed with a **KEDA cron scale rule** (replicas 0 → 1 for a bounded daily
   processing window, master's window opening ~5 min before the agents'), so idle cost is ≈ $0 and
   the window costs ~1–2 h × 13 small containers. *Ruled out:* standing fleet at min-replicas 1
   (24/7 billing for a once-daily batch); deploy-then-delete around each run (fragile, slow, makes
   every run an infra operation). Rollback is trivial: `deploy-agents.ps1 down` still deletes
   everything.
2. **Trigger mechanism: Azure Container Apps Job (cron trigger)** running the dispatcher
   entrypoint. Native, scale-to-zero between fires, visible execution history. *Ruled out:*
   always-on scheduler container (pays 24/7 to sleep); GitHub Actions cron (couples production
   scheduling to the repo host); Logic Apps (new service for one cron line).
3. **Idempotency via the keyed merge, not new state.** `place_run_request` merges on
   `run-request:{run_id}` — a deterministic day-keyed `run_id` (e.g. `sched-2026-07-08`) makes a
   double-fire merge into the same node. No dedupe table.
4. **Fire time: post-close.** Daily cron at **22:30 UTC** (after the 20:00/21:00 UTC NYSE close in
   DST/standard time) so EOD bars are final; the calendar gate inside the entrypoint decides
   whether the day was a trading session. *Ruled out:* pre-open (yesterday's bars — staleness gate
   friction, S87/DL-10).

## Codex kickoff (paste this)

> Execute **Sprint 103 — dispatcher cron** exactly as specified in this file
> (`docs/sprints/sprint-103-dispatcher-cron.md`), including the four packaging decisions above.
> Read first: `orchestration/start.py` (`place_run_request` — the keyed merge is the idempotency
> mechanism), `agents/provider/domain/market_calendar.py` (S87 session calendar; orchestration may
> import it — layering allows orchestration → agents), `infra/deploy-agents.ps1` + the S102
> closeout (deploy tooling + teardown discipline), and `docs/laws/functionality-checks.md` (S102
> row — the distributed-run evidence pattern).
>
> - **Start:** from `main` (`git pull`), `git checkout -b sprint-103-dispatcher-cron` (delete any
>   stale local branch first). **Hard gate:** `make ci` green, 100 % coverage, ≤200-line modules,
>   headers. Bump `pyproject.toml` **0.62.00 → 0.63.00** (feat: scheduled hands-off runs) +
>   `uv lock`.
> - **Part A — the dispatcher trigger (code, CI-tested):**
>   1. A pure, unit-tested decision core (orchestration layer): given today's date + the calendar →
>      trading day? → day-keyed `run_id` (`sched-YYYY-MM-DD`) → place or skip. Non-trading day =
>      clean no-op with a stated reason. Reuse the provider calendar; do **not** duplicate the
>      holiday table.
>   2. A thin scheduled entrypoint (`scripts/` or `orchestration/`, trace the house pattern) that
>      loads env, runs the decision core against the Postgres graph, and **fails loud**: nonzero
>      exit on any error (unreachable graph, calendar exhaustion past 2027 = explicit error, not
>      silent weekday fallback). Log line states placed/skipped + the run_id. Never print the DSN.
>   3. **Universe:** reuse the same ticker-universe source the existing run paths use (trace
>      `scripts/run_local.py` / scanner universe; state in the closeout which source and why). No
>      new universe logic.
>   4. Unit tests: trading-day placement, weekend/holiday skip, double-fire merges to one node
>      (assert same node key), calendar-window-exceeded error path.
> - **Part B — the schedule + standing fleet (live):**
>   1. **Infra:** a Container Apps **Job** (cron `30 22 * * *`, UTC) running the dispatcher image;
>      KEDA **cron scale rules** on the 13 apps (master opens ~22:25, agents 22:30, window closes
>      after ~2 h — make the window bounds parameters of `deploy-agents.ps1`/bicep, not literals).
>      Secrets via the existing secretref pattern (`postgres-dsn`, Service Bus) — mirror, don't
>      reinvent.
>   2. **Live check (sprint-close rule):** deploy the fleet with the scale windows + the job; fire
>      the job **manually once** (same entrypoint, same image) on a trading day and prove the
>      unattended chain: job log shows `placed sched-<date>`, the fleet wakes/completes
>      provider→…→Snapshot distributed, `scripts/accept.py` → **`ACCEPTANCE PASS`**; fire it a
>      second time and prove the double-fire merged (one `RunRequest`, no second run); simulate a
>      non-trading day (entrypoint with an injected date) → clean skip. Alpaca **paper** only.
>   3. **Cost proof:** after the window closes, show all 13 apps at 0 replicas (`az containerapp
>      show` replica counts or equivalent) and the job idle. **The fleet stays deployed** — that is
>      this sprint's end state (decision 1). Tear down only the run's graph artifacts
>      (`pg_teardown.py` on the check's stamped run) — production registry rows and topics stay.
>   4. **Runbook:** `docs/deployment.md` — how the schedule is configured, paused (job disable +
>      scale window to 0), and observed (where to see fired/skipped/failed executions).
>      Record the check in `docs/laws/functionality-checks.md`.
> - **Out of scope — flag, don't build:** live-capital promotion (ADR-only stage gate), intraday
>   or multi-run scheduling, retries/alerting infrastructure beyond fail-loud exit codes, any agent
>   contract change, universe changes.
> - **Do NOT merge or push to `main`** — commit on the branch only; fill **Closeout evidence** here.

---

## Notes for the coding agent

- Layering: orchestration → agents imports are legal (import-linter allows the layers above
  `agents` to depend on it); agent → agent stays forbidden.
- The calendar's holiday table ends at 2027 — that is why the entrypoint must fail loud past the
  window rather than silently degrade to weekday-counting for scheduling (staleness counting may
  degrade; *run placement* may not).
- Neon quirks: cold start ~0.5 s after autosuspend — connect timeout ≥ 10 s in the job entrypoint.
- S102's `servicebus_prepare_routes.py` ran at deploy time; a nightly-waking fleet must not depend
  on manual route prep — routes already exist as production topics, just verify, don't recreate.
- At this sprint's exit the platform is **self-driving in paper mode**: cron places the trigger,
  the fleet wakes, runs distributed on Postgres, proves acceptance, and scales back to zero. That
  is the DL-35 full-activation end state.

---

## Closeout evidence

**Branch / version.** Completed on `sprint-103-dispatcher-cron`; do not merge to `main`.
`pyproject.toml` moved `0.62.00` -> `0.63.00` (`feat: scheduled hands-off runs`) and
`uv lock` was refreshed. Local Docker was not used; GHCR images were built by GitHub Actions.

**Files changed.**

- Dispatcher: `orchestration/scheduled_dispatch.py`, `scripts/dispatch_scheduled_run.py`,
  `orchestration/Dockerfile`.
- Calendar/universe reuse: `agents/provider/domain/market_calendar.py`,
  `agents/scanner/universe.py`, `scripts/run_local.py`.
- Infra: `.github/workflows/build-images.yml`, `infra/deploy-agents.ps1`.
- Tests/docs/teardown: `orchestration/tests/test_scheduled_dispatch.py`,
  `tests/test_dispatch_scheduled_run.py`, `agents/scanner/tests/test_universe.py`,
  `scripts/pg_teardown.py`, `docs/deployment.md`, `docs/laws/functionality-checks.md`.

**Dispatcher behavior.** The pure orchestration decision core uses the provider-owned NYSE
calendar; non-trading days skip with a reason; dates past the provider calendar window raise
`CalendarWindowExceededError` instead of falling back to weekday logic. The job entrypoint loads env,
requires `POSTGRES_DSN`, never prints the DSN, and exits nonzero on errors.

**Universe source.** The scheduled dispatcher uses `FileUniverse()` backed by the committed
`scripts/universe_sp100.txt`, now via the same `load_universe_file()` helper used by
`scripts/run_local.py`. That is the existing realistic run universe; `StaticUniverse` remains the
small four-ticker unit fixture. This was an intentional live-proof pivot after the fixture universe
produced an incomplete acceptance path.

**Local tests / gate.**

- Focused tests:
  `uv run pytest agents/scanner/tests/test_universe.py orchestration/tests/test_scheduled_dispatch.py tests/test_dispatch_scheduled_run.py --no-cov`
  -> `11 passed`.
- Decision-core coverage includes trading-day placement, weekend/holiday skip, double-fire merge to
  one keyed `RunRequest`, and calendar-window-exceeded error.
- Final `make ci`: ruff, format, mypy (`550` source files), import-linter (`4` contracts kept),
  module-size hard block, headers, pytest, pip-audit, and detect-secrets all passed;
  pytest `1404 passed, 5 skipped`, coverage `100.00%`.

**Remote image / deploy.**

- GitHub Actions build-images run `28885499730` built and pushed `:s103` images including
  `ghcr.io/yury-gurevich/trading-agents-dispatcher:s103`.
- `pwsh infra/deploy-agents.ps1 up -Tag s103` passed preflight: Azure CLI/containerapp extension,
  Container Apps env, GHCR credentials, Postgres probe, Service Bus config, GHCR images `14/14`,
  Alembic `upgrade head`, stable Service Bus routes, master + 12 agents, and `dispatcher-cron`
  schedule `30 22 * * *` UTC.
- The deployed posture is standing fleet + KEDA cron scale windows: master `25 22 * * *` UTC,
  agents `30 22 * * *` UTC, all end `30 00 * * *` UTC, desired replicas `1`.

**Live proof.**

- Manual trading-day job execution `dispatcher-cron-k5n6da4` succeeded
  (`2026-07-07T17:29:09Z` -> `17:29:32Z`) and logged:
  `placed sched-2026-07-08 reason=NYSE trading session`.
- Trace for `sched-2026-07-08`: provider returned `99/99` tickers and `3960` bars; scanner
  evaluated `99` and kept `5`; analyst scored `1`; PM approved `1` CSCO paper buy; execution
  submitted `1`; monitor reached; reporter wrote `Snapshot`.
- Acceptance:
  `ACCEPTANCE  PASS - every stage did its job within its boundaries`.
- Second fire `dispatcher-cron-v0fbr3u` succeeded (`2026-07-07T17:37:01Z` -> `17:37:26Z`) and
  logged the same placed line. Lineage proof after the second fire:
  `run_request_count=1`, and exactly one `RunRequest -> MarketData -> ScanRun -> AnalystRun ->
  PMRun -> ExecutionRun -> MonitorRun -> Snapshot` chain for `sched-2026-07-08`.
- Non-trading injection used the same job template with `DISPATCHER_AS_OF=2026-07-04`;
  execution `dispatcher-cron-47cppif` succeeded (`2026-07-07T17:42:23Z` -> `17:42:48Z`) and logged:
  `skipped sched-2026-07-04 reason=2026-07-04 is not a NYSE trading session`.
  Graph proof: `run_request_count=0` for `sched-2026-07-04`.
- Alpaca paper only: the proof order
  `pm-run-6f34914d941d415aada73523ab14d2ea:CSCO:buy` was terminal `filled`; no open order remained
  to cancel.

**Cost / standing end state.** After restoring the normal production cron scale rules, all 13 apps
reported zero replicas: `master`, `scanner`, `analyst`, `portfolio-manager`, `execution`, `monitor`,
`reporter`, `forecaster`, `operator`, `supervisor`, `curator`, `researcher`, `provider` all
`replicas=0`. `az containerapp job execution list` showed terminal executions only; the
`dispatcher-cron` job remains deployed for the next scheduled fire.

**Teardown.** Only stamped run graph artifacts were removed; production registry rows, Service Bus
topics, secrets, the Container Apps fleet, and the dispatcher job stayed.

- `uv run python scripts/pg_teardown.py --run-id sched-2026-07-08 --env-file .env`
  -> `deleted_edges=18 deleted_nodes=17`.
- `uv run python scripts/pg_teardown.py --run-id sched-2026-07-07 --env-file .env`
  -> `deleted_edges=11 deleted_nodes=10`.
- Follow-up proof: `sched-2026-07-07`, `sched-2026-07-08`, and `sched-2026-07-04` all had
  `lineage_nodes=0 run_requests=0`; raw SQL reported
  `remaining_sched_nodes=0 remaining_sched_edges=0`.

**Runbook / register.** Runbook updates are in `docs/deployment.md` under "Container Apps Fleet
Deploy". The functionality-check row is recorded in `docs/laws/functionality-checks.md`.

**Deviations / out-of-scope.** No local Docker. No live-capital promotion, intraday/multi-run
scheduling, retry/alerting infrastructure, agent contract change, or ticker-list change was built.
Two setup attempts failed before final proof and were fixed: dispatcher image import path, and an
Azure `job start --env-vars` date-injection attempt that replaced secret-backed env values. The
runbook now documents the safe template-level override.
