---
type: Architecture Decision
status: accepted
closes: "How do we deploy each agent? Who manages secrets? How do agents get their identity at startup?"
tags: [docker, azure, container-apps, master, key-vault, p14]
---

# ADR 0007 — Container-per-agent deployment + Master bootstrap agent

**Status:** Accepted · **Date:** 2026-06-18 · **Decider:** Yury Gurevich (product owner)

## Context

The system was first deployed as a **single monolithic Docker image** containing every agent. This
was an acknowledged shortcut to get the trading spine running. As the agent count grew (13 agents
at time of writing) and the scope of ADR-0005 (event-driven multi-agent) became concrete, several
structural problems became pressing:

1. **Image bloat.** The `forecaster` agent requires PyTorch + Transformers (~2 GB). A monolith forces
   every deployment — scanner, reporter, monitor — to carry that weight.
2. **Over-privileged secrets.** The whole `.env` (all API keys, broker credentials, graph credentials)
   is injected into a single process. The portfolio manager has no need for the broker API key; the
   scanner has no need for the graph write password. Least-privilege is structurally impossible in a
   monolith.
3. **No per-agent scaling.** If report generation is slow, scaling the monolith scales every agent,
   wasting compute. The Azure Container Apps environment (ADR-0003, already live) supports scale-to-zero
   per container — but only if each agent is its own container.
4. **No identity management.** Agents have no runtime identity. Any code in the process could emit any
   message. There is no enforcement that the scanner only produces `CandidateSet` events — it is purely
   by convention.
5. **No crash recovery.** When an agent crashes, its pending messages are lost. There is no registry
   of what was in flight, no way to re-route to a healthy instance of the same type.
6. **No operational visibility.** There is no record of which agents are live, which have crashed,
   which messages are waiting. The state of the runtime fleet exists only in the process tree.

The owner also identified that as parallel multi-agent operation grows (the P14 milestone), a
**bootstrap sequencing and lifecycle problem** emerges: who starts what, in what order, and how do
agents receive their runtime credentials without every container holding the whole secret store?

## Decision

### 1. One Docker image per agent

Each agent has its own `Dockerfile` with its own dependency group. Images are built locally and
pushed to **DockerHub**. The runtime is **Azure Container Apps** (already live: `trading-agents-env`,
australiaeast; ADR-0003), which pulls from DockerHub and provides native scale-to-zero per container.

This eliminates image bloat and enables independent scaling.

### 2. Pre-master bootstrap and the master agent

**Neo4j and Azure Service Bus are permanent Azure-managed infrastructure.** They are not started by
master or by any agent — they are always available on the platform. Master simply connects to them.
There is no startup ordering problem for the underlying infrastructure.

A lightweight **pre-master bootstrap** (a minimal script or init container, not a trading agent)
handles the only unconditional startup step: launching the master container itself. It has no
business logic and no credentials beyond what Azure Container Apps needs to start a container.

A new agent named **master** is the first trading-system container to start. It is the **only**
agent with a lifecycle role; it has no trading logic. Its responsibilities:

- Access **Azure Key Vault** — master is the **sole** Key Vault accessor. No other agent holds vault
  credentials.
- Read Neo4j to determine session context: recovery from crash, clean restart, or upgrade.
- Read Neo4j `AgentDefinition` nodes to learn the domain — what PM is, what Monitor does — before
  starting any of them.
- Start trading-system agents **on demand only** — never preemptively unless a queued message or
  rule requires it.
- Distribute minimum-necessary secrets to each agent based on its declared capability requirements.
- Manage the fleet: start N instances of a slow agent type when needed.

### 3. Agents start braindead — PRE_FLIGHT → ACTIVE lifecycle

A freshly started container has no identity, no capabilities, no secrets. It **cannot** create
workflows, send messages to domain topics, or emit reports until master activates it. This is a hard
security invariant: an agent cannot cause unintentional side effects before it knows what it is.

**State machine:**

```text
[start]
   │
   ▼
PRE_FLIGHT     Listens only on the permanent handshake queue.
   │           Sends EHLO: { ephemeral_boot_id, capability_declaration (JSON schema) }
   │           Waits for ACTIVATE from master (blocking, with tunable backoff).
   │
   ├─ on valid ACTIVATE (signature verified) ──▶  ACTIVE     Normal domain processing.
   │
   ├─ on retries exhausted ─────────────────────▶  INERT     No domain processing.
   │                                                          Health endpoint reports state.
   │                                                          Master or operator restarts.
   │
   └─ on DRAIN from master ──────────────────────▶ DRAINING  Finishes in-flight work,
                                                              rejects new intake, then exits.
```

### 4. Handshake protocol

A **permanent default queue** (the handshake channel) is always available — it is the only queue
that exists before identities have been assigned. It runs **inside master's own process**.

```text
agent  ──EHLO──▶  master      { ephemeral_boot_id, capability_declaration }
master ──ACTIVATE▶ agent      { identity, capability_grants, secrets_subset, signature }
```

The ACTIVATE message is **signed by master's RSA private key**, which lives in Azure Key Vault.
Master's corresponding **public key is baked into every agent image at build time**. The agent
verifies the signature before accepting the payload. A compromised agent container cannot forge an
ACTIVATE — it has only the public key, which is useless for signing.

Blocking wait is not ideal but is preferable to the alternative (each agent holding its own secrets,
requiring per-agent Key Vault management). The wait parameters are **tunable** — documented in
master's law file and candidate for operational experiments:

| Parameter | Suggested default | Purpose |
| --------- | ---------------- | ------- |
| `handshake_timeout_1_seconds` | 10 | Seconds before first retry |
| `handshake_max_retries` | 5 | Maximum number of EHLO resends |
| `handshake_timeout_2_seconds` | 300 | Total time before transitioning to INERT |

### 5. Capability exchange — interface-first, product-agnostic

Agents declare their runtime needs in the EHLO payload as a **JSON schema**. Declarations describe
**what** (functionality) never **which product**:

```json
{
  "messaging": {
    "operations": ["publish", "subscribe", "dead_letter"],
    "delivery": "at_least_once",
    "schema_version": "1.0"
  },
  "graph": {
    "operations": ["merge_node", "merge_edge", "get_node"],
    "access": "read_write"
  }
}
```

Master searches its own capability registry, matches, and returns the required connection config and
secrets in ACTIVATE. The underlying infrastructure product (Azure Service Bus, Neo4j, etc.) is
invisible to the agent — only the interface contract matters. Swapping infrastructure requires no
agent code changes.

**Capability declarations also live in agent law files** (`agents/<name>/laws/laws.md`) under a
`CAPABILITY DECLARATION (CAP)` section — the law file is the design-time source of truth; the EHLO
payload is derived from it at runtime via the agent's settings.

### 6. Two-tier information model

- **Minimum view** — sent to every agent in ACTIVATE: unique instance ID, role name, capability
  grants, and the minimal config/secrets for its declared needs. Nothing about other agents, no
  vault credentials, no full env.
- **Detailed view** — available only via a privileged admin/debug channel with separate credentials.
  All accesses are audit-logged.

If a container is fully compromised, the attacker sees: that agent's own role config + master's
public key. The public key is useless for forgery. Other agents' configs, the vault, and the full
env are not present.

### 7. Neo4j as the operational registry

Neo4j is not just provenance (ADR-0001) — it is **master's operational brain**. The graph model:

| Node | Key fields | Purpose |
| ---- | ---------- | ------- |
| `AgentDefinition` | `type`, `capability_schema` | Static definition: what PM/Monitor/etc. is |
| `AgentInstance` | `unique_id`, `type`, `state`, `started_at` | Live / dead / scaled-down instances |
| `Session` | `started_at`, `ended_at`, `shutdown_reason` | Run sessions; drive recovery logic |
| `MessageRecord` | `dest_instance_id`, `dest_type`, `status` | Queued/inflight messages; survive restarts |
| `CapabilityGrant` | `granted_to`, `capability`, `config` | What was distributed to each instance |

**Session recovery logic (master reads on startup):**

- Latest `Session` has no `ended_at` → crash recovery → resume from last known state.
- `ended_at` + `shutdown_reason = CLEAN` → fresh start.
- `shutdown_reason = UPGRADE` → upgrade flow, restart affected agents.

**Message re-routing on restart:** if a message's destination `AgentInstance` is no longer live,
master looks up its type from `AgentDefinition`, finds or starts a live instance of that type, and
re-routes. Messages are never silently dropped.

Modelling agent definitions in Aura (while live) provides a shared visual understanding: both human
and AI can inspect the process model, the live fleet, and in-flight messages in the graph browser.

### 8. Law file additions (applies to all agents)

Two new sections are required in every agent's `laws.md`:

**`CAPABILITY DECLARATION (CAP)`** — a structured JSON schema block: interface type, required
operations, schema version, minimum access level. This is what goes into the EHLO payload. It must
describe WHAT, never WHICH PRODUCT.

**`PARAMETERS (PARAM)`** — every constant used in the agent's code must be documented here:

| Name | Value | Type | Tunable | Rationale |
| ---- | ----- | ---- | ------- | --------- |
| `NEUTRAL` | `0.5` | `float ∈ [0,1]` | NO | Midpoint of the sentiment scale; the domain definition depends on this value |
| `headlines_for_full_confidence` | `5` | `int ≥ 1` | YES | Shapes the confidence curve; fewer headlines → lower confidence |

**Tunable** means the value can be changed for operational experiments without breaking the agent's
semantic contract. Tunable parameters are candidates for master to expose and vary at runtime.
**Non-tunable** means changing the value changes what the agent *means* — it is a structural
constant, not a dial.

This makes the law file the **complete source of truth** for what an agent does and all its knobs.
Every `tunable()` already carries a `why=` in `settings.py`; non-tunable constants must now be
documented with equal rigour.

## What this solves

| Problem | Solution |
| ------- | -------- |
| Image bloat | Each image carries only its own dep group; forecaster's 2 GB torch stays out of scanner |
| Over-privileged secrets | Master distributes minimum secrets per declared capability; no agent sees the full vault |
| No per-agent scaling | Container Apps scale-to-zero per container; master starts N instances on demand |
| No crash recovery | Neo4j session + message records survive restarts; master re-routes on next boot |
| No identity management | Agents activate only after receiving a signed identity from master |
| No operational visibility | Neo4j fleet registry; live/crashed/pending all observable in Aura |
| Hardcoded agent counts | Master manages cardinality at runtime; no code change to add a second reporter |
| Secrets reachable from any agent | Only master touches Key Vault; all others receive only what their role requires |

## Risks and mitigations

### Risk 1 — Master is a single point of failure

**Severity:** HIGH · **Likelihood:** MEDIUM

If master crashes after starting some agents, those agents are orphaned: they cannot receive new
capability grants or have their pending messages re-routed.

**Mitigations:**

- Master has no business logic — it is deliberately thin, reducing crash surface.
- All master state lives in Neo4j (external to the process). Master restarts cleanly and resumes
  from the last recorded session without needing to re-derive anything.
- Agents in ACTIVE state keep processing whatever is already in their queues during the outage window.
- Master's own health endpoint is monitored by Azure Container Apps; a crash triggers an automatic
  restart.
- The permanent handshake queue is master's first start and last shutdown — the window where it is
  unavailable is minimised.

### Risk 2 — Master's private signing key is compromised

**Severity:** HIGH · **Likelihood:** LOW

A leaked private key allows an attacker to forge ACTIVATE messages and inject agents with arbitrary
capabilities or elevated secrets.

**Mitigations:**

- Private key lives in **Azure Key Vault** (hardware-backed HSM tier). It is never written to disk or
  logged.
- The key is accessed only by master's process; no other container has vault credentials.
- A key rotation procedure should be documented and rehearsed before going live.
- Azure Key Vault provides full audit logs of every key access.

### Risk 3 — Transient Azure service unavailability at master startup

**Severity:** LOW · **Likelihood:** LOW

Neo4j and Azure Service Bus are permanent, always-available Azure-managed services — master does
not start or provision them. However, a transient Azure disruption (brief network partition, cold
region restart) could leave master unable to connect on its first attempt.

**Mitigations:**

- Master retries its initial Neo4j and Service Bus connections with exponential backoff before
  declaring a startup failure.
- Azure Container Apps restarts master automatically on a failed health check.
- Both services have Azure-managed SLAs and are independently monitored; disruptions are observable
  in the Azure portal without any agent instrumentation.
- This is standard cloud-availability risk, not a structural design risk.

### Risk 4 — Handshake queue unavailability stalls all agent activation

**Severity:** MEDIUM · **Likelihood:** LOW

The handshake queue lives inside master's process. If master is mid-restart, agents pile up in
PRE_FLIGHT and cannot be activated.

**Mitigations:**

- The handshake queue is the **first** thing master starts and the **last** thing it shuts down.
- Agents in PRE_FLIGHT retry with tunable exponential backoff — they will not exhaust retries in
  a normal master restart window.
- If retries are exhausted, INERT state is observable via health endpoint; Container Apps restarts
  the agent automatically when master is back.

### Risk 5 — Container image supply chain

**Severity:** HIGH · **Likelihood:** LOW

Images are built locally and pushed to DockerHub. A compromised build machine or DockerHub account
could inject malicious code into agent images.

**Mitigations:**

- Enable Docker Content Trust / `cosign` image signing; master verifies image digest against a known
  good manifest before starting a container.
- MFA required on the DockerHub account.
- Private DockerHub repository (paid tier) limits who can pull images.
- Build machine is not a shared CI server with wide network access.

### Risk 6 — Neo4j unavailability at master startup

**Severity:** MEDIUM · **Likelihood:** LOW

If Neo4j is down when master starts, it cannot read agent definitions or session recovery state.

**Mitigations:**

- Master caches `AgentDefinition` nodes in memory after the first successful read. A subsequent
  Neo4j outage during a session does not prevent ongoing operation.
- A local JSON snapshot of agent definitions is written after each successful read; master can fall
  back to this snapshot for a read-only cold start.

### Risk 7 — Capability declaration drift

**Severity:** MEDIUM · **Likelihood:** MEDIUM over time

The law file CAPABILITY DECLARATION (design-time) could drift from what `settings.py` actually
requests in the EHLO payload (runtime). An agent with a stale declaration might receive wrong grants.

**Mitigations:**

- The law file section and the corresponding `settings.py` `tunable()` declarations are reviewed in
  the same commit when a capability changes (enforced by PR convention, not yet CI).
- Master validates the EHLO JSON schema against a known schema registry — an unrecognised capability
  request is rejected and logged, not silently ignored.
- Future hardening: a CI check that the EHLO schema derivable from `settings.py` matches the law
  file declaration.

### Risk 8 — Operational complexity increase

**Severity:** MEDIUM · Inherent

Moving from `docker compose up` (one container) to orchestrating N containers with startup ordering,
handshakes, and health checks increases operational surface.

**Mitigations:**

- Azure Container Apps handles scheduling, restarts, and health checking. The orchestration problem
  is largely delegated to the platform.
- A local Docker Compose file mirrors the Container Apps deployment for developer iteration.
- Master encapsulates the complexity — the rest of the team interacts with a "start master" operation,
  not with per-agent startup scripts.
- The increased complexity is **intrinsic to the goal** (independent scaling, least-privilege, crash
  recovery). The alternative (monolith) doesn't eliminate the complexity; it hides it unsafely.

### Risk 9 — Upgrade ordering: old and new instance coexist

**Severity:** LOW · **Likelihood:** MEDIUM during upgrades

When upgrading an agent, there is a window where old and new instances coexist. A message intended
for the old instance might be delivered to the new (different) version.

**Mitigations:**

- Master transitions the old instance to DRAINING before starting the new one: the old instance
  finishes in-flight work, rejects new intake, then exits.
- Messages are routed by `dest_instance_id` (unique per instance), not by type alone. A new instance
  has a new ID; pending messages for the old ID are re-routed only after master explicitly promotes
  the new instance as the canonical handler.

## Alternatives considered

| Alternative | Reason rejected |
| ----------- | --------------- |
| Monolith (status quo) | Image bloat, over-privileged secrets, no per-agent scaling. Scales the wrong dimension. |
| Kubernetes | More powerful, but significant operational overhead for a small team. Azure Container Apps provides scale-to-zero + scheduling without cluster management. |
| External identity provider (Azure AD / LDAP) | Adds another external dependency and a complex IAM surface. The master pattern keeps identity management in-house and auditable. |
| Sidecar container for handshake queue | Cleaner process isolation, but adds a container per pod. The handshake queue is simple enough to live inside master's process. |
| Env-vars for secrets (status quo) | Whole `.env` to every agent. No least-privilege. Rotation requires full restart. Rejected for all the reasons in the Context section. |
| Azure Container Registry instead of DockerHub | More tightly integrated with Azure; slightly higher cost. Viable alternative if supply-chain risk proves harder to manage via DockerHub. Consider at P14 sprint. |

## Consequences

- **`agents/master/`** — a new agent package to be created (its own `Dockerfile`, `laws/`, etc.).
- **Every agent** gains two new sections in its `laws/laws.md`: `CAPABILITY DECLARATION (CAP)` and
  `PARAMETERS (PARAM)`.
- **`docs/laws/_TEMPLATE.md`** — updated with stub versions of the two new sections.
- **`orchestration/dispatcher.py`** — unchanged (handles the trading loop, not agent lifecycle).
- **`supervisor`** — unchanged (handles trading-spine gates, not agent lifecycle).
- **`Dockerfile`** — the current monolith becomes the starting point for `agents/master/Dockerfile`
  and is then replaced by per-agent Dockerfiles. Tracked under the P14 milestone.
- **`docker-compose.yml`** — the current single-service compose is superseded. A new multi-service
  compose (one service per agent) is required for local development.
- **`docs/deployment.md`** — stale once the per-agent split ships. Requires a full rewrite under P14.

## Revisit triggers

- If Azure Container Apps proves unsuitable for the startup ordering or identity model (consider
  AKS with init containers as an alternative).
- If the master pattern proves too operationally complex and a stateless alternative (e.g., each
  agent pulling its own creds from Key Vault via managed identity) is preferred — note: this
  re-introduces per-agent Key Vault access and complicates least-privilege enforcement.
- If DockerHub becomes unsuitable for the supply-chain risk profile (migrate to Azure Container
  Registry or GitHub Container Registry with better signing support).
- If Neo4j is replaced as the primary store (ADR-0001 revisit trigger) — the operational registry
  would need an alternative home.
