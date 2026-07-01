# Sprint 103 — Dispatcher cron: hands-off scheduled runs

**Phase:** Fleet Activation (DL-30 / DL-35)
**Branch:** `sprint-103-dispatcher-cron`
**Status:** planned
**Effort:** S–M

---

## Goal

Make the fleet run **unattended**. Today the `RunRequest` that starts a run is placed by hand or by the
demonstrator ([`scripts/run_local.py`](../../scripts/run_local.py)); the dispatcher cron was deferred at
S83. This sprint schedules the daily trigger so the whole fleet runs on its own — the last step to a live,
self-driving platform.

## Scope

**In:**

- A scheduled trigger that calls `orchestration/start.place_run_request` once per trading day: an Azure
  Container Apps **Job** with a cron schedule (or a scheduled trigger container), placing the `RunRequest`
  node against the permanent store.
- Market-calendar awareness — no run on weekends/holidays (reuse the existing exchange-calendar /
  trading-session logic from S87 rather than a bare cron).
- Idempotency — a given trading day gets exactly one `RunRequest` even if the job fires twice (dedupe on a
  day key, mirroring the graph-pull gate pattern).
- Observability — the scheduled placement is visible (a log line / observatory note); a missed or failed
  schedule is loud (fail-loud, per the P4 exit criterion "the fail-loud scheduler").

**Out:** no change to the run itself (S102 proved it); no autopilot / live-capital promotion (that is a
separate stage-gate decision, ADR-only).

## Deliverables

- The scheduled job definition in [`infra/`](../../infra) (bicep + deploy script) + the trigger
  entrypoint (reusing `place_run_request`).
- Calendar + idempotency logic with unit tests (the pure parts are CI-testable even though the schedule
  itself is infra).
- A short runbook in [`docs/deployment.md`](../deployment.md): how the schedule is configured, paused, and
  observed.

## Decisions to confirm (before building)

- **Schedule mechanism.** Container Apps Job (cron) vs. a small always-on scheduler container vs. an
  external scheduler (Logic App / GitHub Actions cron). Recommend a Container Apps Job — native, cheap,
  scale-to-zero between fires. **Confirm.**
- **Run time.** When in the trading day to place the `RunRequest` (pre-open scan vs. post-close). Confirm
  against the data feeds' freshness and the staleness gate (S87 / DL-10).

## Acceptance / exit criteria

- [ ] A scheduled fire places exactly one `RunRequest` on a trading day and none on a non-trading day.
- [ ] The fleet completes an **unattended** run from that trigger (observed end-to-end in logs / observatory).
- [ ] A double-fire is deduped; a failed/missed schedule is surfaced loudly.
- [ ] `make ci` green on the CI-testable calendar/idempotency units; modules ≤ 200 lines.

## Dependencies

- **S102** (the fleet runs distributed on the permanent store). Reuses S83 `place_run_request`, S87
  trading-session calendar.
- Closes the "Dispatcher cron" item deferred since S83 and listed in STATE **Next**.

## Version bump

New capability (scheduled hands-off runs). **0.46.00 → 0.47.00** (feat → MINOR, HARD RULE)
— renumber if S100's bump lands differently; the coding agent stamps the actual bump at merge.

## Notes

At this sprint's exit the platform is **self-driving**: master bootstraps the fleet, a cron places the
daily trigger, agents run graph-pull + served across containers on a durable store, and the acceptance
gate proves each run. That is the full-activation end state DL-35 chose.
