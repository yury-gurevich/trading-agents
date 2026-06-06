# trading-agents

An agent-first rebuild of the trading system. **One rule:** trading knowledge
lives *only* in agents. Agents never import each other — they exchange typed
messages over a bus. Everything else is plumbing.

## Layers

```text
kernel/        Plumbing only. NO trading knowledge. Message envelope, bus
               interface (in-process for tests, Celery for runtime), contract
               descriptors, persistence + graph adapters, observability, MCP binding.

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

- **Postgres = transactional truth** (orders, positions, approvals, audits —
  ACID, append-only). Each agent owns *its own* tables. No shared god-schema.
- **Neo4j = analysis & provenance overlay.** Every artifact and every A2A
  message is a node; edges encode derivation
  (`Candidate → Recommendation → OrderIntent → Fill → Outcome`) and message
  lineage. This is the data-collection-and-analysis layer.

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

Bootstrapping — **contracts first**. The boundary map (`contracts/` + every
`mission.md`) is being locked before any runtime is wired.
