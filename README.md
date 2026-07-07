# trading-agents

An agent-first rebuild of the trading system. **One rule:** trading knowledge
lives *only* in agents. Agents never import each other — they exchange typed
messages over a bus. Everything else is plumbing.

## Layers

```text
kernel/        Plumbing only. NO trading knowledge. Message envelope, bus
               interface (in-process for tests, Celery for runtime), contract
               descriptors, GraphStore adapters, observability, MCP binding.

contracts/     The shared vocabulary — the boundary map. Typed message payloads
               and one AgentContract per agent. Agents import message types from
               here, never from each other. Depends on kernel only.

agents/        The trading system. Each agent owns its logic, its data, its tests.
               <name>/ mission.md  contract.py  agent.py  domain/  store.py  mcp.py  tests/

orchestration/ Thin dispatcher + Celery app. Routes messages; makes no decisions.

surfaces/      Consumers, not agents: dashboard, CLI. Read the system; never drive it.
```

Dependency direction is one-way: `kernel ← contracts ← agents`. Surfaces and
orchestration sit on top. `.importlinter` enforces all of this in CI.

## Data architecture

One store: **PostgreSQL** (see `docs/decisions/0014-postgresql-system-of-record.md`).
The graph spine is exposed through the kernel `GraphStore` port and migrated only
through Alembic. Neo4j remains available until S118 as an ad-hoc analysis workbench
and rollback backend.

- **Transactional truth** (orders, positions, approvals, audits) — nodes with ACID
  guarantees, append-only; each agent owns *its own* node/edge labels, no shared
  god-schema. Money as integer minor units.
- **Provenance & analysis** — every artifact and every A2A message is a node; edges
  encode derivation (`Candidate → Recommendation → OrderIntent → Fill → Outcome`) and
  message lineage. The data-collection-and-analysis layer.
- **Retrieval (RAG)** — deferred pgvector/vector-index work; not part of the S117
  fleet swap.

## The 12 agents

| Agent | One-line mission |
| --- | --- |
| provider | Single boundary to external market data + regime; nobody else calls a data API. |
| scanner | Reduce the universe to a ranked candidate set, explaining every filter. |
| analyst | Turn candidates into scored, evidence-backed recommendations. |
| forecaster | Advisory shadow-ML signals, never binding until scorecards earn it. |
| portfolio_manager | Decide which recommendations become sized, risk-checked orders. |
| execution | The single idempotent broker boundary: submit, fill, reconcile, stage-gate. |
| monitor | Watch open positions, decide exits, explain every hold and close. |
| reporter | Stitch runs and trades into durable narrative + metrics. |
| researcher | Propose bounded, measurable parameter changes — never apply them. |
| curator | Curate collected graph data into versioned datasets for later LLM training (out of band). |
| operator | Translate operator language into typed, policy-bound intents; explain state. |
| supervisor | Route messages, enforce the capability matrix, flag for human, master report. |

Read each agent's `mission.md` for its full charter and `contract.py` for its
machine-readable boundary.

## Status

The kernel runtime (both bus backends, `AgentBase`, the `GraphStore` port, the
metrics adapter) is in place, and the first pipeline runs end-to-end —
`provider → scanner → analyst → portfolio_manager` — each agent an island talking only
through typed messages, with provenance spanning them. Live status: `docs/STATE.md`.
