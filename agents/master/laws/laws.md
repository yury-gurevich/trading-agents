# `Master` — Laws

**Prefix:** `MST` · **status:** LOCKED v1.7 · **Owner:** Yury Gurevich

> Receive EHLO from freshly-started agent containers, verify declared capabilities,
> distribute minimum-privilege credentials via ACTIVATE, and maintain the
> PostgreSQL-backed operational fleet registry.

Each clause below has a stable ID (`MST-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

## Identity & purpose (`IDN`)

- **MST-IDN-01** — Master's sole job is bootstrap lifecycle: it activates trading-system agent
  containers, distributes minimum-necessary credentials, and records the live fleet in the graph store.
  It has zero trading logic.
- **MST-IDN-02** — Master exclusively owns graph labels: `AgentDefinition`, `AgentInstance`,
  `Session`, `CapabilityGrant`, `FleetPreflight`. No other agent writes these labels.
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

- **MST-TRG-01** — `activate` is triggered by an agent container sending EHLO as `POST /ehlo` over
  HTTP. Master may be asleep, starting or busy, so an agent resends an EHLO that met a transport
  failure (a timeout; a refused, reset or dropped connection; HTTP 502, 503 or 504) with the **same**
  `ephemeral_boot_id`, within the kernel's bounded EHLO budget (an attempt cap, a per-attempt
  timeout, a total time, and exponential backoff with full jitter between attempts). A 4xx answer or
  an ACTIVATE whose signature fails verification is final and is never resent.
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
- **MST-OUT-04** — `run_fleet_preflight` tests every pack-declared probe for every agent type in
  the grant policy and writes one `FleetPreflight` node per check. The check passes only if every
  probe passed or has a fresh costly-pass cache entry. A credential failure or a transport failure
  fails it.

## Never (`NEV`)

- **MST-NEV-01** — Master never activates an agent whose `agent_type` is not in the grant policy
  the pack supplies. Rogue or unknown containers cannot receive credentials.
- **MST-NEV-02** — Master never distributes credentials beyond what the agent's declared capability
  requires. A scanner never receives broker API keys; a reporter never receives LLM credentials.
- **MST-NEV-03** — Master never places orders, calls market APIs, or produces any trading artifact.
- **MST-NEV-04** — Master never shares its Key Vault credential or private signing key with any
  other process. The key lives in Key Vault; master accesses it; no agent receives it.
- **MST-NEV-05** — Master never imports code from any trading agent (`agents/scanner/`, etc.).
  It knows agent types by name/grant table, not by importing their code.
- **MST-NEV-06** — Master never hands over a pack-declared credential until its applicable
  credential test has either passed live or has a fresh costly-pass cache entry. A failed required
  credential test refuses activation and writes no `AgentInstance`.

## State & storage (`STA`)

- **MST-STA-01** — `start()` writes one `Session` node with `started_at`. On next boot, if the
  latest `Session` has no `ended_at`, master infers a crash and enters recovery mode.
- **MST-STA-02** — Master writes one `AgentInstance` node per activated boot id:
  `{ agent_type, boot_id, state="active", started_at }`. A resent EHLO answered by replay
  (`MST-IDM-03`) writes none.
- **MST-STA-03** — `activate()` writes one `CapabilityGrant` node per granted capability,
  keyed `grant:<instance_id>:<capability>`.
- **MST-STA-04** — `drain()` merges `{ drain_reason, drain_at }` into the `AgentInstance` node.
  The `state` is not overwritten (append-only constraint); drain is observable via `drain_reason`.

## Idempotency (`IDM`)

- **MST-IDM-01** — Two EHLO messages from the same `agent_type` with different
  `ephemeral_boot_id`s produce two distinct `instance_id` values (counter suffix). Multiple instances
  of the same type are supported. (A repeated boot id is `MST-IDM-03`.)
- **MST-IDM-02** — If master restarts, it reads the existing `Session` nodes to determine recovery
  context before writing a new `Session`.
- **MST-IDM-03** — A repeated EHLO with the same `ephemeral_boot_id` **and** the same `agent_type`
  within the replay lifetime returns the same ACTIVATE (same `instance_id`, grants and config, validly
  signed), writes nothing and runs no credential test; concurrent duplicates produce one activation.
  The replay lifetime is `handshake_timeout_2_seconds`, capped by `credential_pass_cache_ttl_minutes`
  and `secret_cache_ttl_minutes` when they are non-zero, so a replay never re-delivers a credential
  for longer than its pass or its fetched value is trusted; with the defaults it is at least the
  kernel's EHLO budget. Past it the boot id activates afresh. The same boot id with a **different**
  `agent_type` is refused (422): nothing is returned but the refusal and nothing is written
  (`MST-NEV-02`). A refused or failed activation is never replayed.

## Ordering (`ORD`)

- **MST-ORD-01** — `start()` must be called before `activate()`. `activate()` without a live
  session writes the instance but cannot link it to a session (session_id may be None).
- **MST-ORD-02** — Master may be asleep (scaled to zero), starting, or busy with an activation wave
  when an agent boots; nothing assumes master is up first. That the agent proceeds only after
  master's ACTIVATE is achieved by the agent's resend (`MST-TRG-01`), never by start-up order.
- **MST-ORD-03** — Master serves EHLOs concurrently, so one slow activation does not hold the others
  behind it, and its listen backlog (`ehlo_listen_backlog`) holds at least one whole activation wave
  (every agent type in the grant policy waking at once).

## Failure modes (`FAIL`)

- **MST-FAIL-01** — If the graph is unavailable on `activate()`, the fault is captured by
  `fault_boundary` and re-raised. The EHLO is not acknowledged; the agent remains in PRE_FLIGHT.
- **MST-FAIL-02** — If the graph is unavailable on `drain()`, the fault is re-raised. The agent
  continues running; operator must retry drain.
- **MST-FAIL-03** — Master itself is a single point of failure (RISK-1 in ADR-0007). Mitigation:
  thin implementation (no business logic), state in PostgreSQL via `GraphStore`, Container Apps
  auto-restart.
- **MST-FAIL-04** — Credential-test transport failures are visible faults, not credential failures:
  activation may proceed, no pass is cached, and required failures are decided from credential
  rejection. Optional credential failures do not block activation.
- **MST-FAIL-05** — A probe status listed in the probe's `credential_failure_statuses` is recorded
  as `unrecoverable`. Any other 4xx is recorded as `unexpected`. A 5xx, timeout, or network error
  is recorded as `transient`. All three fail the fleet check.
- **MST-FAIL-06** — An agent whose EHLO budget is spent (the attempt cap or the total time) exits
  non-zero with one line naming the attempts, the elapsed time and the last cause; every failed
  attempt before it writes one line to stderr. Nothing is swallowed.

## Type contracts (`TYP`)

- **MST-TYP-01** — The master handshake payload types carry, at minimum, the fields its own clauses
  require; the clause, not `kernel/handshake.py`, is the authority on what must be present.
  `EHLOMessage` carries `ephemeral_boot_id`, `agent_type`, and `capability_declaration`
  (`MST-IN-01`). `ACTIVATEMessage` carries `instance_id`, `agent_type`, `capability_grants`,
  `config`, and `signature` (`MST-OUT-01`/`MST-SEC-01`/`MST-SEC-02`). `DRAINMessage` carries
  `instance_id` and `reason` (`MST-IN-02`/`MST-OUT-02`). These three messages are Pydantic
  `_Frozen` models. `AgentState` is a `StrEnum`.
- **MST-TYP-02** — `capability_grants` in `ACTIVATEMessage` is `dict[str, object]` — a JSON-safe
  map of interface names to operation lists. Never contains product names.

## Security (`SEC`)

- **MST-SEC-01** — ACTIVATE signature field is stub `""` in S73. RSA signing wired in S74:
  master's private key lives in Azure Key Vault; the corresponding public key is baked into every
  agent image at build time and used to verify ACTIVATE before accepting it.
- **MST-SEC-02** — Each agent receives only the config/credentials for its declared `capability_grants`.
  The full `.env` is never passed to any non-master container.
- **MST-SEC-03** — The pack's grant policy is the only privilege table master consults; the master
  image ships none, and master reads the policy once, when it starts.
- **MST-SEC-04** — Credential-test evidence never contains raw secret values. Activation records,
  escalations, faults, and refusal exceptions name credential/test labels and sanitized causes only.

## Dependencies (`DEP`)

- **MST-DEP-01** — PostgreSQL must be reachable before `start()`. The startup guard retries briefly
  before halting safely instead of crash-looping.
- **MST-DEP-02** — Azure Key Vault must be reachable before master can resolve credentials for
  ACTIVATE. Wired in S74; stub config `{}` used in S73.
- **MST-DEP-03** — No dependency on any trading agent's code. All agent knowledge is in the pack
  data injected at start-up (grant policy, secret map, credential tests) plus `AgentDefinition`
  graph nodes.
- **MST-DEP-04** — A credential-bearing pack must supply a non-empty credential-test declaration at
  startup. Missing declarations, empty declarations, and unknown probe kinds are rejected loudly
  instead of being treated as zero successful tests.
- **MST-DEP-05** — Master imports only the substrate (`kernel` and its own package) and never a
  pack module. It never imports `contracts`, another agent's package, `orchestration`, or
  `surfaces`.

## Observability (`OBS`)

- **MST-OBS-01** — Every `activate()` call writes an `AgentInstance` node — the live fleet is
  queryable through the PostgreSQL graph spine.
- **MST-OBS-02** — Every `drain()` call merges `drain_reason` onto the `AgentInstance` — shutdown
  intent is recorded alongside the live state.
- **MST-OBS-03** — Fault channel receives all graph/Key Vault errors via `fault_boundary`.
- **MST-OBS-04** — Successful activation records applicable credential-test evidence on the
  `AgentInstance`: live-tested names, live-passed names, cached-pass names, optional failures, and
  transport failures.

## Performance (`PERF`)

- **MST-PERF-01** — `activate()` writes 1 `AgentInstance` node + N `CapabilityGrant` nodes where
  N = count of granted capabilities (2–4). Expected p99 < 100 ms against the graph store.

## Capability declaration (`CAP`)

```json
{
  "graph": {
    "operations": ["append_write", "read"],
    "labels_owned": ["AgentDefinition", "AgentInstance", "Session", "CapabilityGrant", "FleetPreflight"],
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
| `handshake_timeout_2_seconds` | `300.0` | `float ≥ 30.0 ≤ 600.0` | YES | Master's replay window (`MST-IDM-03`): seconds a resent EHLO with the same boot id and type gets the first ACTIVATE back; must be ≥ the kernel's EHLO budget (`ehlo_budget_seconds`, 300) so every resend is replayed |
| `ehlo_listen_backlog` | `64` | `int ≥ 16 ≤ 1024` | YES | Listen backlog of master's EHLO server (`MST-ORD-03`); one wave is the 15 agent types waking together, and 64 holds four waves of resends |
| `credential_tests_path` | `""` | `str` | YES | Filesystem path fallback for the master credential-test declaration pack |
| `credential_tests_b64` | `""` | `str` | YES | Base64 environment delivery for the master credential-test declaration pack |
| `credential_pass_cache_ttl_minutes` | `5` | `int ≥ 0 ≤ 60` | YES | Minutes a costly credential-test pass remains fresh during an activation wave |
| `fleet_preflight_interval_minutes` | `60` | `int ≥ 5 ≤ 240` | YES | Minutes between master-owned whole-fleet readiness checks; bounds detection delay and repeated probe cost |
| `grant_policy_path` | `""` | `str` | YES | Filesystem path to the pack's grant-policy JSON; empty = the substrate ships no grants, so every agent type is unknown until a pack supplies one |
| `grant_policy_b64` | `""` | `str` | YES | Base64 grant-policy JSON injected at deploy time; wins over `grant_policy_path` and keeps the master image pack-agnostic |
| `secret_map_path` | `""` | `str` | YES | Filesystem path to the pack's secret-map JSON; empty = no agent type is entitled to any secret until a pack supplies the table |
| `secret_map_b64` | `""` | `str` | YES | Base64 secret-map JSON injected at deploy time; wins over `secret_map_path` and keeps the master image pack-agnostic |
| `secret_cache_ttl_minutes` | `5` | `int ≥ 0 ≤ 60` | YES | Minutes a fetched Key Vault secret stays cached for repeated references; 0 = never expires |
| `remediation_mode` | `"manual"` | `str` | YES | How a credential-test failure is handled (DL-36): `manual` refuses and escalates to a human; `automatic` allows one remediation shot, then forces manual |
| `auto_remediation_scope` | `"safe_only"` | `str` | YES | Which catalogue remediations may run automatically under `remediation_mode=automatic`: `safe_only` (non-destructive only) or `all` |
| `max_auto_remediation_attempts` | `1` | `int ≥ 0 ≤ 3` | YES | Automatic remediation runs allowed per failure signature before human review is forced; one shot by default |

## Divergence register

| ID | Law says | Code / contract says | Decision |
| --- | --- | --- | --- |
| DRIFT-001 | MST-SEC-01: RSA signature required on ACTIVATE | `signature=""` stub in S73 | **RESOLVED S74** — `sign_pss()` in `http_server.handle_ehlo()`; `kernel/crypto.py` |
| DRIFT-002 | MST-DEP-02: Key Vault resolves credentials in ACTIVATE | `config={}` in S73 | **RESOLVED S75** — `resolve_config()` in `agents/master/secret_map.py`; `SecretStore` protocol; KV + env-var impls |

## Changelog

- v1 — authored S73 (P15 foundation) and locked immediately.
- v1.1 — S74: DRIFT-001 resolved (RSA-PSS signing wired); S75: DRIFT-002 resolved (Key Vault wired).
- v1.2 — S188: credential tests become pack-declared activation guards; required credential
  failures refuse activation, transport failures fault without blocking, activation records test
  evidence, and credential-test records are secret-redacted.
- v1.3 — S205 rewrites `MST-TYP-01` from a file-as-oracle contract assertion into explicit
  required fields for `EHLOMessage`, `ACTIVATEMessage`, and `DRAINMessage`, while preserving the
  `_Frozen` and `AgentState`/`StrEnum` type assertions. No contract shape changes.
- v1.4 — S217 adds master-owned `FleetPreflight` evidence (`MST-IDN-02` / `MST-OUT-04`) and
  `MST-FAIL-05` classification for whole-fleet readiness. `MST-FAIL-04` is unchanged: activation
  still permits a transport failure, while fleet readiness fails it by design (DL-179).
- v1.5 — DL-203 / work-queue item 33 (2026-09-23): `PARAM` only. Declares the grant-policy and
  secret-map delivery fields (`*_path` / `*_b64`, the pattern the credential-test rows already use),
  `secret_cache_ttl_minutes` and the three DL-36 remediation controls. No clause moves.
- v1.6 — S232 / DL-228 / ADR-0012 / DL-12 (2026-09-26): `MST-NEV-01`, `MST-SEC-03` and `MST-DEP-03`
  rewritten to name the pack data the master now consults (`DEFAULT_GRANTS` was deleted in S84).
  `MST-SEC-03` drops the *"cannot be changed by runtime config"* claim, which the `PARAM` table's own
  `Tunable YES` rows already contradicted (DRIFT-058's lesson: a clause whose check cannot fail).
  `MST-TYP-01` renames its cited path to `kernel/handshake.py` (the master handshake contract moved
  out of `contracts/`, into the kernel, alongside `Provenance`/`Explanation`/the frozen base). New
  `MST-DEP-05`: master imports only the substrate, never a pack module.
- v1.7 — S244 / DL-248 / DL-249 / DRIFT-091 (2026-09-29): the fleet crashed where the book promised a
  resend budget no code read. `MST-TRG-01` names the real trigger (`POST /ehlo`) and the agent's
  bounded resend with one boot id (4xx and a bad signature final); `MST-ORD-02` drops the assumption
  that master is up first; `MST-STA-02` is one `AgentInstance` per boot id, not per message;
  `MST-IDM-01` is scoped to different boot ids so it does not contradict the new `MST-IDM-03`
  (a repeated boot id replays, another type is refused). New `MST-ORD-03` (concurrent EHLO service,
  a backlog for a wave) and `MST-FAIL-06` (a spent budget exits loud). `PARAM`:
  `handshake_timeout_1_seconds` and `handshake_max_retries` leave the table (the agent's side; the
  kernel's `EhloSettings` owns the envelope now), `handshake_timeout_2_seconds` is master's replay
  window, `ehlo_listen_backlog` is new.
