# `Master` — Laws

**Prefix:** `MST` · **status:** LOCKED v1 · **Owner:** Yury Gurevich

> Receive EHLO from freshly-started agent containers, verify declared capabilities,
> distribute minimum-privilege credentials via ACTIVATE, and maintain the Neo4j
> operational fleet registry.

Each clause below has a stable ID (`MST-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

## Identity & purpose (`IDN`)

- **MST-IDN-01** — Master's sole job is bootstrap lifecycle: it activates trading-system agent
  containers, distributes minimum-necessary credentials, and records the live fleet in Neo4j.
  It has zero trading logic.
- **MST-IDN-02** — Master exclusively owns Neo4j labels: `AgentDefinition`, `AgentInstance`,
  `Session`, `CapabilityGrant`. No other agent writes these labels.
- **MST-IDN-03** — Master is the only process with Azure Key Vault access (ADR-0007). No agent
  receives vault credentials directly; they receive only the resolved config needed for their
  declared capabilities.

## Inputs (`IN`)

- **MST-IN-01** — `activate` capability accepts an `EHLOMessage`
  `{ ephemeral_boot_id: str, agent_type: str, capability_declaration: dict }`.
  `agent_type` must match a known `AgentDefinition`; unknown types are rejected with `ValueError`.
- **MST-IN-02** — `drain` capability accepts a `DRAINMessage` `{ instance_id: str, reason: str }`.
  `instance_id` must match an existing `AgentInstance` node; unknown IDs raise `KeyError`.
- **MST-IN-03** — Malformed or missing fields in EHLO → rejected; no graph write; fault emitted.

## Triggers (`TRG`)

- **MST-TRG-01** — `activate` is triggered by an agent container sending EHLO on the permanent
  handshake queue (in-process for now; moves to a durable queue in S74).
- **MST-TRG-02** — `drain` is triggered by the operator (via supervisor) or by master's own
  crash-recovery logic on startup.

## Outputs (`OUT`)

- **MST-OUT-01** — `activate` returns `ACTIVATEMessage`
  `{ instance_id, agent_type, capability_grants, config, signature }`. `instance_id` is unique per
  run (format: `<type>:<timestamp>:<counter>`). `signature` is stub `""` until RSA wired (S74).
- **MST-OUT-02** — `drain` returns `DRAINMessage` and writes `drain_reason` + `drain_at` to the
  `AgentInstance` node.
- **MST-OUT-03** — On `start()`, writes a `Session` node with `started_at`. Used for
  crash-recovery detection (no `ended_at` → prior session crashed).

## Never (`NEV`)

- **MST-NEV-01** — Master never activates an agent whose `agent_type` is not in `DEFAULT_GRANTS`.
  Rogue or unknown containers cannot receive credentials.
- **MST-NEV-02** — Master never distributes credentials beyond what the agent's declared capability
  requires. A scanner never receives broker API keys; a reporter never receives LLM credentials.
- **MST-NEV-03** — Master never places orders, calls market APIs, or produces any trading artifact.
- **MST-NEV-04** — Master never shares its Key Vault credential or private signing key with any
  other process. The key lives in Key Vault; master accesses it; no agent receives it.
- **MST-NEV-05** — Master never imports code from any trading agent (`agents/scanner/`, etc.).
  It knows agent types by name/grant table, not by importing their code.

## State & storage (`STA`)

- **MST-STA-01** — `start()` writes one `Session` node with `started_at`. On next boot, if the
  latest `Session` has no `ended_at`, master infers a crash and enters recovery mode.
- **MST-STA-02** — `activate()` writes one `AgentInstance` node per EHLO:
  `{ agent_type, boot_id, state="active", started_at }`.
- **MST-STA-03** — `activate()` writes one `CapabilityGrant` node per granted capability,
  keyed `grant:<instance_id>:<capability>`.
- **MST-STA-04** — `drain()` merges `{ drain_reason, drain_at }` into the `AgentInstance` node.
  The `state` is not overwritten (append-only constraint); drain is observable via `drain_reason`.

## Idempotency (`IDM`)

- **MST-IDM-01** — Two EHLO messages from the same `agent_type` produce two distinct `instance_id`
  values (counter suffix). Multiple instances of the same type are supported.
- **MST-IDM-02** — If master restarts, it reads the existing `Session` nodes to determine recovery
  context before writing a new `Session`.

## Ordering (`ORD`)

- **MST-ORD-01** — `start()` must be called before `activate()`. `activate()` without a live
  session writes the instance but cannot link it to a session (session_id may be None).
- **MST-ORD-02** — Master starts before any trading agent container. The handshake queue must be
  live before agents send EHLO.

## Failure modes (`FAIL`)

- **MST-FAIL-01** — If the graph is unavailable on `activate()`, the fault is captured by
  `fault_boundary` and re-raised. The EHLO is not acknowledged; the agent remains in PRE_FLIGHT.
- **MST-FAIL-02** — If the graph is unavailable on `drain()`, the fault is re-raised. The agent
  continues running; operator must retry drain.
- **MST-FAIL-03** — Master itself is a single point of failure (RISK-1 in ADR-0007). Mitigation:
  thin implementation (no business logic), state in Neo4j, Container Apps auto-restart.

## Type contracts (`TYP`)

- **MST-TYP-01** — `EHLOMessage`, `ACTIVATEMessage`, `DRAINMessage`, `AgentState` are declared in
  `contracts/master.py`. All are Pydantic `_Frozen` models. `AgentState` is a `StrEnum`.
- **MST-TYP-02** — `capability_grants` in `ACTIVATEMessage` is `dict[str, object]` — a JSON-safe
  map of interface names to operation lists. Never contains product names.

## Security (`SEC`)

- **MST-SEC-01** — ACTIVATE signature field is stub `""` in S73. RSA signing wired in S74:
  master's private key lives in Azure Key Vault; the corresponding public key is baked into every
  agent image at build time and used to verify ACTIVATE before accepting it.
- **MST-SEC-02** — Each agent receives only the config/credentials for its declared `capability_grants`.
  The full `.env` is never passed to any non-master container.
- **MST-SEC-03** — `DEFAULT_GRANTS` in `grants.py` is the authoritative privilege table.
  Changes to it require a code review commit, not a runtime config change.

## Dependencies (`DEP`)

- **MST-DEP-01** — Neo4j must be reachable before `start()`. Connection retry with exponential
  backoff before declaring startup failure (wired in S74).
- **MST-DEP-02** — Azure Key Vault must be reachable before master can resolve credentials for
  ACTIVATE. Wired in S74; stub config `{}` used in S73.
- **MST-DEP-03** — No dependency on any trading agent's code. All agent knowledge is in
  `DEFAULT_GRANTS` and `AgentDefinition` Neo4j nodes.

## Observability (`OBS`)

- **MST-OBS-01** — Every `activate()` call writes an `AgentInstance` node — the live fleet is
  fully visible in the Neo4j browser without additional tooling.
- **MST-OBS-02** — Every `drain()` call merges `drain_reason` onto the `AgentInstance` — shutdown
  intent is recorded alongside the live state.
- **MST-OBS-03** — Fault channel receives all graph/Key Vault errors via `fault_boundary`.

## Performance (`PERF`)

- **MST-PERF-01** — `activate()` writes 1 `AgentInstance` node + N `CapabilityGrant` nodes where
  N = count of granted capabilities (2–4). Expected p99 < 100 ms against local Neo4j.

## Capability declaration (`CAP`)

```json
{
  "graph": {
    "operations": ["append_write", "read"],
    "labels_owned": ["AgentDefinition", "AgentInstance", "Session", "CapabilityGrant"],
    "access": "owner"
  },
  "key_vault": {
    "operations": ["get_secret"],
    "scope": "all_agent_credentials"
  },
  "messaging": {
    "operations": ["listen"],
    "channel": "handshake_queue"
  }
}
```

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `handshake_timeout_1_seconds` | `10.0` | `float ≥ 1.0 ≤ 60.0` | YES | Seconds before master retries unacknowledged ACTIVATE |
| `handshake_max_retries` | `5` | `int ≥ 1 ≤ 20` | YES | Max EHLO resends before agent transitions to INERT |
| `handshake_timeout_2_seconds` | `300.0` | `float ≥ 30.0 ≤ 600.0` | YES | Total wait before unactivated agent goes INERT |

## Divergence register

| ID | Law says | Code / contract says | Decision |
| --- | --- | --- | --- |
| DRIFT-001 | MST-SEC-01: RSA signature required on ACTIVATE | `signature=""` stub in S73 | **RESOLVED S74** — `sign_pss()` in `http_server.handle_ehlo()`; `kernel/crypto.py` |
| DRIFT-002 | MST-DEP-02: Key Vault resolves credentials in ACTIVATE | `config={}` in S73 | **RESOLVED S75** — `resolve_config()` in `agents/master/secret_map.py`; `SecretStore` protocol; KV + env-var impls |

## Changelog

- v1 — authored S73 (P15 foundation) and locked immediately.
- v1.1 — S74: DRIFT-001 resolved (RSA-PSS signing wired); S75: DRIFT-002 resolved (Key Vault wired).
