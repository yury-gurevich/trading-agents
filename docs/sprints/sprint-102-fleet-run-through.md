# Sprint 102 — Full 13-container fleet run-through + distributed acceptance

**Phase:** Fleet Activation (DL-30 / DL-35)
**Branch:** `sprint-102-fleet-run-through`
**Status:** planned
**Effort:** L (live infra; not CI-tested)

---

## Goal

The milestone the whole arc exists for: run the **real distributed fleet** end-to-end. Deploy master +
12 agents as separate containers on Azure Container Apps, place one `RunRequest`, and prove the pipeline
completes across containers with the **same acceptance gate** ([`scripts/accept.py`](../../scripts/accept.py))
that passes in-process — plus prove the 5 control-plane agents actually *serve* in their own containers.
Until now the fleet has only been proven collapsed into one process (`cascade_once`); this proves it
distributed.

## Scope

**In:**

- Deploy all 13 images (master first, then the rest) via
  [`infra/deploy-agents.ps1`](../../infra/deploy-agents.ps1) against the S101 permanent store; confirm
  master EHLO/ACTIVATE for **every** agent (only scanner was proven at S76) — `AgentInstance` +
  `CapabilityGrant` nodes written for all 12.
- Place one `RunRequest` (the dispatcher / `orchestration/start.py` `place_run_request`) and let the fleet
  run graph-pull + served; walk the provenance chain
  (`MarketData → ScanRun → … → Snapshot`) and run `accept_run` → **`ACCEPTANCE PASS`** on the distributed
  run.
- Prove the control plane live: an operator command round-trips; the supervisor gate/fault path fires; the
  forecaster writes a `shadow` prediction; curator/researcher serve a request — each in its own container.
- Capture the run in the observatory ([`orchestration/observatory.py`](../../orchestration/observatory.py))
  and record Layer-2 choreography edges as **proven on a real run** (ledger Layer 2 ⬜ → 🟩).

**Out:** cron scheduling (S103) — this run is placed by hand. No new features; this is validation +
whatever live-only bugs it surfaces (expect some — every prior live run found in-memory-hidden bugs:
DRIFT-011/012/013/014).

## Deliverables

- A documented fleet-run runbook + the evidence: activation log (12 agents), the provenance tally, the
  `ACCEPTANCE PASS` output, and the control-plane serving proofs.
- Fixes for any live-only defects found, each as a `drift-register.md` entry with a cited test (the
  established pattern).
- Ledger updated: Layer 2 (choreography) and Layer 3 (acceptance) rows reflect the distributed proof.

## Decisions to confirm (before building)

- **Broker stage in the fleet.** Confirm execution runs against **Alpaca paper** (DEP-BROKER, live-proven)
  for the run-through — real fills, no real capital — before any live-money consideration.
- **Scale-to-zero vs. min-replicas.** Control-plane servers (supervisor/operator) likely need
  `min-replicas 1` to serve; graph-pull agents can scale to zero and wake on poll. Confirm per agent.

## Acceptance / exit criteria

- [ ] Master activates all 12 agents (EHLO → signed ACTIVATE); registry nodes present.
- [ ] One `RunRequest` drives provider→reporter **across containers**; full provenance chain present.
- [ ] `accept_run` returns `ACCEPTANCE PASS` on the distributed run.
- [ ] Each control-plane agent proven serving in its own container.
- [ ] Any live-only defect captured in `drift-register.md` with a cited regression test; `make ci` green.

## Dependencies

- **S100** (distributed bus proven at parity), **S101** (permanent store). This is the payoff sprint.

## Version bump

Validation milestone. Version bump only if code changes land from live-bug fixes (then PATCH per fix).
Record in the sprint report.

## Notes

Per LAW-02 this sprint's success is **proven, never assumed**: "the fleet works" means the captured
`ACCEPTANCE PASS` + the activation log + the control-plane serving evidence — not a green deploy alone.
