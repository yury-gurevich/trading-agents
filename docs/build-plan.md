# Build Plan

The sequenced engineering plan. Product intent is in `docs/PRD.md`; structure is in
`docs/architecture.md`. This document owns "what we build next and how we know it
works." Refresh the status column at every closeout.

## Principles for building

- **Boundary first, runtime second.** A capability is designed as a contract before
  it is implemented. The contract is the review artifact.
- **One agent at a time.** Implement and validate an agent in isolation, then wire
  it into a flow. Never broaden a change across agents to make one work.
- **In-process before distributed.** Prove a flow on the in-process bus with tests,
  then run it on the distributed bus. The distributed backend changes deployment,
  not logic.
- **Advisory before binding.** ML and any non-deterministic component ships shadow
  first, behind a scorecard, before it can influence a decision.
- **Reuse where clean, rewrite where it pays.** Porting settled domain math (the
  trading rules) is encouraged; the kernel, contracts, per-agent data ownership,
  bus, graph, and dispatcher are written fresh.

## Phases

### P0 — Boundary map · **complete**

Kernel contract descriptors and message envelope; the justified-tunable config
primitive and the central fault channel; the shared `contracts/` vocabulary; all
12 agent contracts and missions; the self-enforcing boundary meta-test; the CI/test
toolchain (including the module-size and coding-agent-header guards).
**Exit:** boundary meta-test green; CI quality gate green. *(met)*

### P1 — Kernel runtime

Implement the bus (`InProcessBus` + a distributed backend), the `AgentBase`
lifecycle, the relational persistence adapter and the graph adapter, observability
emission, and the tool-interface binding generated from a contract. Introduce the
schema-migration tool here.
**Tests:** kernel unit tests; an in-process round-trip (request → handler →
response) for a trivial echo agent; persistence adapter tests against a local
database; a graph-write smoke test.
**Exit:** an echo agent answers a typed request over both bus backends; coverage
ratchet raised to the new measured floor. **Effort: M.**

### P2 — First vertical slice (`provider → scanner → analyst`)

Implement these three agents end-to-end over the in-process bus, porting the
settled domain logic. Each gets `agent.py`, `domain/`, `store.py`, and tests. The
provider becomes the sole holder of data-API credentials; scanner and analyst
request data rather than fetching it. Provenance is written for each artifact.
**Tests:** per-agent unit + contract tests; one integration test driving the slice;
graph-provenance assertions (candidate → recommendation lineage).
**Exit:** a request produces explained recommendations with full provenance, with
no agent importing another. **Effort: L.**

### P3 — Decision loop (`portfolio_manager → execution → monitor → reporter`)

Complete the daily loop in **paper** stage. Portfolio manager sizes and risk-checks;
execution submits idempotently to a paper broker and records fills; monitor opens
positions from fill events and decides exits; reporter stitches the run snapshot and
per-trade narrative.
**Tests:** sizing and risk-check unit tests; idempotency tests for execution; exit-
rule unit tests; an integration test for a full paper run; narrative-completeness
test (scan → exit).
**Exit:** a full paper trading day runs end-to-end with a stitched narrative and
single-writer data ownership intact. **Effort: L.**

### P4 — Orchestration

Replace any temporary in-test sequencing with the dispatcher and the distributed
bus. A scheduler issues run triggers; agents idle until messaged. Dead-letter and
retry handling lands in the supervisor.
**Tests:** dispatcher routing tests; idle/active behavior (no message → no work);
end-to-end run on the distributed backend.
**Exit:** the daily loop runs on the distributed bus, event-driven, with the
supervisor recording message lineage. **Effort: M.**

### P5 — Operator command layer + supervisor safety

Implement the operator agent (intent grammar, typed schemas, command audit, model-
call ledger, evidence-grounded explanations, confirmation semantics) and the
supervisor's capability matrix and hard-NO surface. Expose the tool interface from
the operator as the bounded external bridge.
**Tests:** intent-mapping tests (correct intent, safe refusal on ambiguity);
capability-gate tests (forbidden caller blocked, hard-NO never enabled); audit/
ledger append-only tests; policy-parity tests (command path == dashboard path).
**Exit:** the allowed command families execute safely with full audit and zero
unsafe bypasses. **Effort: M.**

### P6 — Surfaces

Dashboard read-models over the relational + graph stores (pipeline status,
recommendation evidence, approval queue, position lifecycle, scorecards, control-
plane state, incidents, active-incidents pane) and a CLI. Surfaces read; they never
drive an agent except through the operator's bounded commands.
**Tests:** read-model projection tests; explain-on-demand affordance tests.
**Exit:** an operator can run, inspect, approve, and recover entirely from the
dashboard. **Effort: M–L.**

### P7 — Self-management

The researcher proposes bounded, measurable parameter changes into a human-review
queue; nothing is applied without operator approval through the control plane.
**Tests:** evidence-window enforcement; forbidden-combination rejection; proposal
audit; "proposes but never applies" boundary test.
**Exit:** a measured proposal can be reviewed and approved through the operator,
with full provenance. **Effort: M.**

### P8 — Hardening + expansion readiness

Stage promotion/demotion gates (paper → broker-shadow → live-manual →
live-autopilot) made evidence-based and reversible; the market-pack and exchange-
calendar abstractions; a per-pack readiness checklist.
**Exit:** a new market pack can be added without core control-plane changes (G6).
**Effort: L.**

### P9 — Observability stack

Provision Prometheus scraping and Grafana dashboards over the kernel metrics
adapter: system health, per-agent throughput and latency, fault rate by source
module, and the trust indicators over time. Wire the central fault channel into
the fault-rate panels and incidents.
**Tests:** metric-emission tests; dashboard provisioning smoke.
**Exit:** an operator can watch system health and fault trends in Grafana, beside
the product dashboard. **Effort: M.** See `docs/observability.md`.

### P10 — Curator (out-of-band data engineering)

Implement the curator: read the provenance graph, assemble clean, labelled,
versioned training datasets with train/validation/test splits, and publish
manifests — strictly out of band, never gating a trading decision.
**Tests:** dataset assembly + split tests; "never influences a decision" boundary
test; manifest/versioning tests.
**Exit:** a versioned dataset can be built from collected data and described to the
operator, with full provenance. **Effort: M.**

## Testing & CI parameters

The toolchain mirrors the conventions of the reference project:

- **Python 3.13**, dependency + lock management via `uv`.
- **Lint/format:** `ruff` (same rule set and 88-col format), no auto-fix in hooks.
- **Types:** `mypy --strict` with the pydantic plugin, over `kernel contracts
  agents orchestration surfaces`.
- **Boundaries:** `import-linter` (`lint-imports`) — the four contracts in
  `.importlinter`.
- **Tests + coverage:** `pytest` with a branch-coverage **ratchet floor** (set to
  the real measured floor; raised as coverage grows, never lowered).
- **Security:** `pip-audit` and `detect-secrets` against a committed baseline.
- **Module size:** warn at 150 lines, hard-block at 200. Clean start — no
  grandfathered files; `__init__.py` and migration revisions are exempt.
- **Module headers:** every module declares a coding-agent header (`Agent:` /
  `Role:`), enforced by `scripts/check_module_header.py`.
- **Pre-commit** runs the same uv-locked binaries and flags as CI, so local and CI
  verdicts match.

CI jobs mirror the reference layout: `quality` (lint, format, types, import-linter,
module size), `test` (pytest + coverage floor), `security` (pip-audit,
detect-secrets). The database-backed `migration` job and the staged
`promotion_check` job are introduced with the persistence layer in P1 and the stage
gates in P8 respectively.

## Status

| Phase | State |
| --- | --- |
| P0 Boundary map | **complete** |
| P1 Kernel runtime | **active** (Sprint 01 shipped: bus + AgentBase) |
| P2 First vertical slice | planned |
| P3 Decision loop | planned |
| P4 Orchestration | planned |
| P5 Operator + supervisor | planned |
| P6 Surfaces | planned |
| P7 Self-management | planned |
| P8 Hardening + expansion | planned |
