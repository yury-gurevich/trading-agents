# R004 · A2A (Agent2Agent) — interop standard, adopted at the boundary only

**Status:** 🗄️ Archived (evaluated — no internal adoption ever on current architecture; boundary
adapter deferred behind explicit triggers) · **Date:** 2026-07-04

How closely does this platform follow Google's A2A protocol (now Linux-Foundation-governed,
v1.x, 150+ orgs in production), and should it adopt the standard? **Answer: convergent on every
A2A principle (opaque agents, declared capabilities, task lifecycle) with stronger enforcement
than the spec asks; deliberately divergent on wire protocol, discovery, and schemas — where a
closed fleet is better served by the brokered bus, master-granted capabilities, and compile-time
contracts.** A2A's place here is an **A2A front-door adapter in `surfaces/`** (the MCP-surface
pattern, agent↔agent direction), built only when an external agent actually appears.

- **[a2a-boundary.md](a2a-boundary.md)** — full evaluation: what A2A is, the
  convergence/divergence scorecard, the boundary-adapter design sketch, ruled-out options,
  revisit triggers.

**Answers:** How closely do we follow A2A standards and best practice? Should A2A replace any
internal mechanism? When and how would A2A compatibility be added?

**Consuming decisions:** ADR-0012 (adapter = substrate surface) · ADR-0005 (internal bus
unchanged) · DL-38 (unaffected).

**Outcome:** Not adopted internally (permanent, on current architecture). Boundary adapter
deferred. **Revisit triggers:** (a) a concrete external-agent integration request; (b) the
multi-org scaling intent becomes concrete; (c) official MCP↔A2A convergence.
