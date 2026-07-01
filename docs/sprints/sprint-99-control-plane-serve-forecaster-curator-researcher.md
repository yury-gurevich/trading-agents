# Sprint 99 — Control-plane served in-process (2/2): forecaster + curator + researcher

**Phase:** Fleet Activation (DL-30 / DL-35)
**Branch:** `sprint-99-control-plane-serve-forecaster-curator-researcher`
**Status:** planned
**Effort:** M

---

## Goal

Retire the last three `idle_loop()` stubs — **forecaster**, **curator**, **researcher** — by serving each
over the S97 `serve_loop`. After this sprint **zero `idle_loop()` remains**: every one of the 12 agents
runs a real loop (7 trade-spine on `work_loop`, 5 control-plane on `serve_loop`), so the whole fleet is
*serviceable in-process*. S100 then swaps the in-process consumer for the Service Bus backend behind the
same Protocol.

## Scope

**In:**

- Serve the forecaster over `serve_loop` bound to its `forecast` / `forecast_return` capabilities.
  **Critical constraint (DL-30, `FORE-TRG-01/02`):** the forecaster is **RPC-triggered, never
  self-triggering** — do **not** give it a graph-pull `work_loop` (that violates `FORE-TRG-02`). It serves
  requests from the orchestrator/cascade, exactly as it is called in `cascade_once` today.
- Serve curator + researcher over `serve_loop` bound to their existing out-of-band capabilities (dataset
  assembly / bounded-proposal). These are triggered (operator command or orchestrator), never
  self-triggering — honour their `TRG`/`NEVER` clauses (`researcher` proposes-never-applies;
  `curator` never-gates-a-decision).
- Law reconciliation + clause-cited serving tests for all three.

**Out:** the Service Bus backend (S100); any change to the forecaster's shadow-prediction logic or the
curator/researcher domain logic — trigger wiring only.

## Deliverables

- Updated `agents/forecaster/entrypoint.py`, `agents/curator/entrypoint.py`,
  `agents/researcher/entrypoint.py` — serve, not idle.
- In-process integration tests: forecaster serves a `forecast` request → `ShadowPrediction` (shadow,
  never gates); curator serves a dataset-assembly request; researcher serves a proposal request — each
  citing the relevant `TRG` clause and the never-clause it must not cross.
- `test-plan.md` updates + ledger green-count deltas for all three.
- A grep-guard test (or CI note) asserting **no `idle_loop` reference remains** in any agent entrypoint.

## Decisions to confirm (before building)

- **Forecaster trigger source in the fleet.** In-process, the *orchestrator* calls it (DL-30). As a
  container, who sends the `forecast` request — the analyst stage via the graph-ref event, or a dedicated
  orchestrator stage? Recommend: the orchestrator publishes a `forecast` request per recommendation
  (keeps `FORE-TRG-02` — the forecaster never reads the analyst node itself). **Capture in `design-log.md`.**
- **Curator/researcher cadence.** Confirm both stay out-of-band (operator/scheduler-triggered), not
  continuous pollers — consistent with "never influences a live decision".

## Acceptance / exit criteria

- [ ] No agent entrypoint calls `idle_loop()` (guard test green).
- [ ] Forecaster serves a request and writes a `shadow=True` prediction without touching the PM/execution
      path (side-branch invariant preserved, `FORE-TRG-02` upheld).
- [ ] Curator + researcher serve their capabilities within their never-clauses.
- [ ] `make ci` green; 100% coverage; modules ≤ 200 lines.

## Dependencies

- **S97** (`serve_loop`), **S98** (serving pattern established for supervisor/operator).
- Respects DL-30 (forecaster is RPC-triggered) and the forecaster/curator/researcher LOCKED v1 laws (S71).

## Version bump

New capability (final three control-plane agents serve; fleet fully serviceable in-process).
**0.44.00 → 0.45.00** (feat → MINOR, HARD RULE).

## Notes

At this sprint's exit the **in-process fleet is functionally complete** — the etalon-first-safe milestone.
Everything after (S100+) adds the distributed backend and live infra.
