<!-- Agent: planning | Role: sprint handover -->
# Sprint 123 — Operations dashboard, slice 2: fleet lifecycle + infrastructure + logs + costs (DL-47)

**Phase:** Operations dashboard (DL-47 slice 2 of 4; S122 shipped 0.66.00)
**Branch:** `sprint-123-dashboard-fleet-infra`
**Status:** ready for handover (packaged 2026-07-10)
**Effort:** M–L

---

## Why this sprint

S122 made the trading run legible (Section III). The operator's remaining blind spots are the
machine layers: is the fleet healthy or merely idle, what did each container actually do last
window (per-container logs — DL-47 req. 1), and what is this costing (req. 9). This slice fills
dashboard Sections I and II, extends the `/bundle` with `logs` + `images` (the repair agent's
missing inputs), and widens the status-line vitals. The design spec remains
`docs/design/dashboard-mockup.html`; match it.

## Decisions taken at packaging (LAW-06)

1. **One Azure read-port, REST behind a Protocol.** `surfaces/dashboard/azure_port.py` declares
   a small `AzureReader` Protocol: `list_container_apps()` (name, image, replicas),
   `list_job_executions(job)`, `query_logs(container, start, end, tail)` (Log Analytics
   workspace query), `query_costs(scope, month_to_date)` (Cost Management). The live
   implementation uses **plain REST with an `azure-identity` token** (the `azure` extra already
   ships it) — no new mgmt SDKs. All parsing is pure and unit-tested from committed fixture
   payloads; only the HTTP send is thin. *Ruled out:* `azure-mgmt-*` SDKs (heavy, one-use);
   shelling out to `az` (no typed errors, needs CLI login state).
2. **LLM cost = `LLMCall` ledger × a pricing catalogue file.** Aggregate `LLMCall` nodes per
   `model` (`tokens_in`/`tokens_out`) and price via `orchestration/packs/llm_pricing.json`
   (per-Mtoken in/out rates + a `pricing_as_of` date — config, not code; ADR-0012 pack side).
   **Honesty rule:** models found in the ledger but missing from the catalogue render as
   "untracked", never $0; deliberation/compile spend not in the ledger is labelled untracked.
3. **Section II is graph-first, Azure-second.** Lifecycle stages come from what the graph
   proves (`AgentInstance` activations, `Escalation`s, the run chain) plus job executions +
   replica state from the port. No new node types; this is a projection, not new telemetry.
4. **Images are surfaced, not judged.** The per-app image tag lands in Section I, the vitals,
   and `bundle.images`. The behind-main comparison (the DL-46 tripwire verdict) is **S124** —
   this sprint ships the data, not the judgement.
5. **Config via env, no secrets in the surface.** `DASHBOARD_AZURE_*` env names (subscription,
   resource group, Log Analytics workspace id) + the existing `AZURE_SP_*`/default credential
   chain. The dashboard never reads Key Vault; absent credentials degrade to "Azure data
   unavailable" panels (the graph-backed parts keep working) — never a crash.

## Codex kickoff (paste this)

> Execute **Sprint 123 — dashboard fleet/infra slice** exactly as specified in this file
> (`docs/sprints/sprint-123-dashboard-fleet-infra.md`). Read first:
> `docs/design/dashboard-mockup.html` (rendered — Sections I/II + log drawer + vitals are the
> spec), DL-47 in `docs/design-log.md` (reqs 1, 6, 9, 10), `surfaces/dashboard/` (S122 skeleton
> — extend, don't rework), `agents/master/store.py` (AgentInstance/Escalation shapes),
> `agents/operator/store.py` (`LLMCall`), `infra/deploy-agents.ps1` (app names, job name,
> scale windows).
>
> - **Start:** from `main` (`git pull`), branch `sprint-123-dashboard-fleet-infra`. Hard gate:
>   `make ci` green, 100 % coverage, ≤200-line modules, headers, tunables for any threshold.
>   Bump **MINOR** + `uv lock`.
> - **Part A — Azure read-port** per packaging decision 1 (pure parsers unit-tested on fixture
>   JSON; live sends isolated and injectable).
> - **Part B — projections + endpoints:**
>   `/api/fleet` (Section II: lifecycle stages + per-agent activation state + escalations);
>   `/api/infra` (Section I: env/spine/bus/job cards, container table with image tag + replica
>   count, hardware cost by service, LLM cost by model per decision 2);
>   `/api/containers/{name}/logs?tail=200` (Log Analytics, last window; representative-sample
>   disclaimer gone for real data); `/api/vitals` (pending flags, broker↔graph sync, degraded
>   feeds, spine/bus reachability, image tags summary, mtd cost, next fire);
>   **`/bundle` gains real `logs` (per-container tail for the run window) + `images`.**
> - **Part C — frontend:** render Sections I and II from the mockup (cards, container table
>   with a working log drawer, vitals strip from `/api/vitals`); Section III untouched.
> - **Tests:** fake `AzureReader` for every projection; parser tests on committed fixture
>   payloads (apps list, job executions, log rows, cost rows); pricing table (known tokens →
>   dollars, unknown model → untracked); degraded mode (no Azure creds → panels report
>   unavailable, HTTP 200). 100 % on the Python surface.
> - **Functionality check (LAW-02):** serve locally with real Azure creds + live Neon
>   (read-only): container table shows the 13 apps + `dispatcher-cron` on their real tags;
>   open the log drawer on `execution` for the last window; costs render with real MTD numbers
>   (or an explicit Cost-Management-permission finding); vitals reflect the real pending-flag
>   count. Record in `docs/laws/functionality-checks.md` + screenshots under
>   `docs/reports/sprint-123-dashboard-fleet-infra/`. Read-only — state the teardown as such.
> - **Wrap up:** README index row, closeout block below, push, hand back.

## Guardrails

- Surfaces read, never write — no bus, no agent imports, no graph writes, no Azure writes.
- Log queries are bounded (`tail` capped by a tunable); cost queries cached in-process for a
  tunable TTL (don't hammer Cost Management on every page load).
- Secrets never rendered or logged; DSN/connection strings never appear in any response.
- Stay in scope: no tripwire verdict, no resume, no chat (S124/S125); no gate change.

## Definition of done

1. Sections I and II render real data locally; the log drawer streams real Log Analytics rows.
2. `/api/vitals` powers the status line; `bundle.logs` + `bundle.images` are populated.
3. Costs: hardware by service + LLM by model, with untracked spend named explicitly.
4. Degraded mode proven: without Azure creds the dashboard still serves graph-backed views.
5. `make ci` green at 100 %; live check recorded with screenshots.

## Closeout (coding agent fills; planning agent verifies before merge)

```text
CLOSEOUT — Sprint 123
Branch / merge commit:
make ci:                 (tail: N passed, coverage %)
Functionality check:     (live evidence + screenshot paths + teardown note)
Version:                 (old → new)
Deviations from spec:    (none | list)
```
