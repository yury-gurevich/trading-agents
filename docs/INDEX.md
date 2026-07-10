# Docs index — where to find everything

**How to use:** before digging into any file, scan the "Answers" column. If your
question is listed there, go straight to the linked file. Don't read everything.

---

## Operational state — start here

| File | Answers |
| --- | --- |
| [STATE.md](STATE.md) | Where are we right now? What is the active sprint? What is next? |
| [build-plan.md](build-plan.md) | What are all the phases, and how far through P1–P15 are we? |
| [design-log.md](design-log.md) | What design threads are still OPEN (not yet ADRs)? What options did we weigh and rule out? |
| [STATE-01.md](STATE-01.md) · [STATE-02.md](STATE-02.md) · [STATE-03.md](STATE-03.md) · [STATE-04.md](STATE-04.md) | Archived older sprint history offloaded to keep STATE.md short (S36→P0 in -01; S37–S76 in -02; S77–S96 + etalon-era narrative in -03; S99–S118 + chores in -04) |

---

## Architecture + design

| File | Answers |
| --- | --- |
| [architecture.md](architecture.md) | How do the agents fit together? What is the data flow? |
| [agent-message-chain.md](agent-message-chain.md) | What exact graph nodes, edges, and side-channel messages move one run between agents? |
| [PRD.md](PRD.md) | What is this product trying to do? (vision doc — see laws for ground truth) |
| [technology-stack.md](technology-stack.md) | What technologies are adopted, considered, on the horizon, or rejected? What breaks if we swap X? |
| [design/dashboard-mockup.html](design/dashboard-mockup.html) | What should the operations dashboard look like and do? (interactive design spec for DL-47 / S122–S125 — open rendered) |

---

## Decisions, laws, research, sprints

| Folder | Answers |
| --- | --- |
| [decisions/](decisions/INDEX.md) | What architecture questions are already closed forever? (13 ADRs) |
| [laws/](laws/INDEX.md) | What must each agent do / never do? What is the law book schema? |
| [research/](research/INDEX.md) | What external tools have we evaluated? What is still in progress? |
| [sprints/](sprints/INDEX.md) | Which sprints shipped? Which phase are we in? What is queued? |

---

## Process + guides

| File | Answers |
| --- | --- |
| [sprint-loop.md](sprint-loop.md) | How does a sprint run end-to-end? Planning → coding → review → merge |
| [configuration.md](configuration.md) | What settings exist per agent? Where are they declared? |
| [deployment.md](deployment.md) | How do agents get built and deployed to Azure Container Apps? |
| [ci-cd-setup.md](ci-cd-setup.md) | One-time GHCR + Azure credential setup for the build/deploy pipeline (ADR-0011)? |
| [observability.md](observability.md) | How do metrics, logs, and faults flow to Azure Monitor / Prometheus? |
| [error-handling.md](error-handling.md) | How do agents handle faults without crashing? What is `fault_boundary`? |
| [repo-hygiene.md](repo-hygiene.md) | What are the non-negotiable code quality rules? |
| [hardening-backlog.md](hardening-backlog.md) | What security hardening items are queued? |
| [codeql-local-tooling.md](codeql-local-tooling.md) | How to run CodeQL locally before pushing? |
| [moonshots.md](moonshots.md) | What big ideas are parked for later? |
| [ideas.md](ideas.md) | What small ideas are parked mid-flow (captured via `/idea`) so they don't derail the current sprint? |
