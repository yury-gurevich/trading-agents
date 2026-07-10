<!-- Agent: planning | Role: sprint handover -->
# Sprint 122 — Operations dashboard, slice 1: the run view (DL-47)

**Phase:** Operations dashboard (DL-47 — the PRD's product surface #1; first of four slices)
**Branch:** `sprint-122-dashboard-run-view`
**Status:** ready for handover (packaged 2026-07-10; amended same day — `/bundle` endpoint added
per DL-47 req. 11 before any code started)
**Effort:** M

---

## Why this sprint

The fleet is self-driving (S103) but not self-explaining: every "how did last night go" is a
manual `trace_run.py` + `accept.py` + ad-hoc graph query session. The operator directed
(DL-47): a dashboard, three sections, run-scoped, animated, ChatGPT/early-Anthropic look. This
slice ships the highest-value section — **Section III, the trading run as a logical unit** —
plus the run selector and the service skeleton the other slices build on. Slices 2–4 (fleet
lifecycle + logs, resume-from-stage, operator chat) are packaged separately.

**The design spec is committed:** `docs/design/dashboard-mockup.html` — open it in a browser.
Match its tokens (palette, type, spacing), section structure, and copy tone exactly. The
mockup's Section III with the run selector is what this sprint makes real; its other sections
stay mocked until S123/S124/S125.

## Decisions taken at packaging (LAW-06)

1. **`surfaces/dashboard/` — FastAPI read-model service + static frontend, no build toolchain.**
   Vanilla JS/CSS served as static files; the repo stays Python-first and CI gains no node step.
   *Ruled out:* React/Vite (toolchain + CI churn), server-rendered templates (the animated,
   run-switching UI wants a data API anyway — and S125's chat will reuse it).
2. **The service reads the graph only.** Every endpoint is a projection over the injected
   `GraphStore` (same pattern as `surfaces/queries`). No bus access, no agent imports, no writes —
   import-linter's surface contract already enforces this. Actions come later and only via the
   operator agent (S125).
3. **Logical verdicts are computed from the observatory, not re-derived.** The per-stage verdict
   API wraps `orchestration.packs.trading_observatory.observe_run` + `trading_acceptance.accept_run`
   — one source of truth for "did the agent do its job" (the same numbers `accept.py` prints).
   The dashboard renders observed facts + checks; it never invents its own thresholds.
4. **Run discovery = `RunRequest` nodes.** The run selector lists run ids (day-keyed `sched-*`
   first, newest first). Everything in the view is scoped to the selected run id — no ambient
   "latest" state mixed in (operator requirement 5, DL-47).
5. **No-trade day annotation, not gate change.** Where acceptance FAILs solely on
   `analyst.scored`/`pm.evaluated` floors with `analyst` rejections present, the view renders the
   "every agent did its job — the gate disagrees" banner (mockup copy). **Changing the gate
   semantics is NOT in scope** — that is a separate decision the planning agent owns (candidate
   drift item; see STATE Next).

## Codex kickoff (paste this)

> Execute **Sprint 122 — dashboard run view** exactly as specified in this file
> (`docs/sprints/sprint-122-dashboard-run-view.md`). Read first: `docs/design/dashboard-mockup.html`
> (the design spec — open it rendered), DL-47 in `docs/design-log.md`,
> `orchestration/packs/trading_observatory.py` + `trading_acceptance.py` (the verdict source),
> `orchestration/batch_trace.py`, `surfaces/queries/` (the read-model pattern to follow),
> `agents/execution/reconciliation_store.py` (snapshot/Flag shapes).
>
> - **Start:** from `main` (`git pull`), `git checkout -b sprint-122-dashboard-run-view`.
>   **Hard gate:** `make ci` green, 100 % coverage, ≤200-line modules, module headers.
>   Bump `pyproject.toml` **MINOR** (new capability) + `uv lock`; stage `uv.lock`.
> - **Part A — read-model API (`surfaces/dashboard/`):**
>   1. `app.py` — FastAPI app factory `build_app(graph: GraphStore)`; graph injected, never
>      constructed in module scope. A thin `__main__.py` composes `build_graph_from_env()` +
>      uvicorn for `uv run python -m surfaces.dashboard` (composition root; `# pragma: no cover`
>      on the I/O line only if unavoidable).
>   2. Endpoints (all GET, all JSON, all run-scoped where meaningful):
>      `/api/runs` (RunRequest ids, newest first, with created_at);
>      `/api/runs/{run_id}/verdict` (acceptance PASS/FAIL + breaches + the no-trade annotation
>      per packaging decision 5);
>      `/api/runs/{run_id}/stages` (per-stage: agent, observed numbers, checks with
>      pass/warn/fail, degraded notes — from `observe_run`);
>      `/api/runs/{run_id}/flags` (Flags whose subject/created_at ties to the run window +
>      all `pending` Flags, each with severity/reason/status);
>      `/api/runs/{run_id}/positions` (open Positions + the latest `BrokerPositionSnapshot`
>      holdings, joined per ticker as graph-vs-broker rows);
>      `/api/runs/{run_id}/recovery` (Escalation + RemediationPlan nodes for the run window —
>      the DL-36 ladder; empty lists are a valid, renderable answer);
>      `/api/runs/{run_id}/bundle` (**the LLM context bundle, DL-47 req. 11** — one JSON document
>      aggregating everything the other endpoints return, plus run metadata: run_id, as_of,
>      version + image tag if recorded, degraded-feed notes. Its consumer is a repair-agent LLM
>      (S125), so shape it for machine ingestion: stable keys, no HTML, explicit pass/warn/fail
>      enums, reasons as plain text. S123 extends it with log excerpts — leave a documented,
>      empty `logs` key now).
>   3. FastAPI + uvicorn go in a new optional dependency group `dashboard` (mirror how `azure`
>      / `postgres` extras are declared); unit tests must not require the extra beyond FastAPI's
>      TestClient (add to dev group).
> - **Part B — frontend (static, no toolchain):**
>   1. `surfaces/dashboard/static/` — `index.html`, `app.css`, `app.js`. Port the mockup's
>      tokens/type/layout **verbatim** (both themes, reduced-motion, focus states). Implement:
>      top bar with run selector (populated from `/api/runs`), verdict pill, Section III
>      (stage flow with staged reveal + travelling-dot connectors, gate banner, flags/positions/
>      notes panels). Sections I/II render as visibly-labelled "ships in S123/S124" placeholders
>      using the mockup's own copy — do not silently omit them.
>   2. Switching the run re-fetches all `/api/runs/{id}/*` and re-renders — no page reload,
>      no state bleed between runs (operator requirement: "that run and only that run").
> - **Tests (unit, 100 % on the Python surface):** projection tests over `InMemoryGraphStore`
>   fixtures for every endpoint (a PASS run, the real no-trade FAIL shape, a run with a critical
>   Flag + snapshot, empty graph → clean 404/empty responses); the no-trade annotation logic
>   table-tested; static files served test. Frontend JS is static asset, not counted in coverage.
> - **Functionality check (mandatory, LAW-02):** run the service locally against the **live Neon
>   graph** read-only (`uv run python -m surfaces.dashboard`), open it, select
>   `sched-2026-07-09` and `sched-2026-07-08`, and verify the rendered verdicts/stages/flags/
>   positions match `scripts/accept.py` + `trace_run.py` output for both runs. Screenshot both
>   states into `docs/reports/sprint-122-dashboard-run-view/`. Read-only — nothing to tear down;
>   say so in the record. Append the row to `docs/laws/functionality-checks.md`.
> - **Wrap up:** update `docs/sprints/README.md` index row (planning agent pre-added it as
>   queued), fill the Closeout block below, push the branch, hand back.

## Guardrails (repo law — non-negotiable)

- Surfaces read; they never drive an agent. No bus import, no agent import, no graph writes.
- Modules ≤ 200 lines (split `app.py` into routers if it grows); coding-agent headers everywhere.
- No magic numbers — any threshold/limit is a `kernel.tunable(..., why=...)`.
- `make ci` fully green before handback; never lower the coverage floor.
- Stay in scope: no gate-semantics change, no resume primitive, no chat, no Azure API calls —
  those are S123–S125 and a separate gate decision.

## Definition of done

1. `uv run python -m surfaces.dashboard` serves the run view locally against `POSTGRES_DSN`.
2. Run selector scopes **everything** rendered to the selected run.
3. Section III shows per-agent logical verdicts + acceptance banner + flags + graph-vs-broker
   positions + the DL-36 recovery ladder, matching the mockup's design.
4. The two real runs render correctly (verified against `accept.py`/`trace_run.py`).
5. `make ci` green at 100 % coverage; version bumped MINOR.

## Closeout (coding agent fills; planning agent verifies before merge)

```text
CLOSEOUT — Sprint 122
Branch / merge commit:
make ci:                 (paste tail: N passed, coverage %)
Functionality check:     (live URL opened, runs verified against accept.py/trace_run.py,
                          screenshot paths, teardown: read-only/nothing)
Version:                 (old → new)
Deviations from spec:    (none | list)
```
