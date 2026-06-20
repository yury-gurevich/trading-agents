# Sprint 73 — P15 foundation: master bootstrap agent

**Phase:** P15 (multi-agent container split)
**Branch:** `sprint-73-p15-master-agent`
**Status:** shipped

---

## Goal

Lay the P15 foundation: the `master` bootstrap agent that receives `EHLO` from freshly-started
agent containers, distributes minimum-privilege grants via `ACTIVATE`, and maintains the Neo4j
operational fleet registry. Also: per-agent `Dockerfile`s (13 images, one per agent) and the
updated multi-service `docker-compose.yml`.

---

## What shipped

### New files

| File | Description |
| --- | --- |
| `contracts/master.py` | `AgentState` (StrEnum), `EHLOMessage`, `ACTIVATEMessage`, `DRAINMessage`, `CONTRACT` |
| `agents/master/__init__.py` | Public re-export |
| `agents/master/agent.py` | `MasterAgent`: `start()`, `activate()`, `drain()` |
| `agents/master/grants.py` | `DEFAULT_GRANTS` — per-agent minimum-privilege capability table (12 agent types) |
| `agents/master/settings.py` | `MasterSettings`: 3 handshake tunables |
| `agents/master/store.py` | Graph write helpers: `write_session`, `write_agent_definition`, `write_agent_instance`, `write_capability_grant` |
| `agents/master/laws/laws.md` | LOCKED v1 — 18 sections, prefix `MST`, 10 clauses 🟩 |
| `agents/master/laws/test-plan.md` | 18 clauses tracked (10 green, 8 deferred to S74) |
| `agents/master/tests/test_master_agent.py` | 11 tests — start, activate, drain, write_agent_definition |
| `agents/master/Dockerfile` | Master image (azure extra for Key Vault, wired S74) |
| `agents/{name}/Dockerfile` | 12 per-agent images (scanner/analyst/pm/execution/monitor/reporter/forecaster/operator/supervisor/curator/researcher/provider) |
| `docker-compose.yml` | Multi-service local dev runner — all 13 services, master first |
| `scripts/neo4j_crud.py` | CRUD demo script (Create/Read/Update/Delete via `Neo4jGraphStore`) |

### Key design decisions

- **EHLO/ACTIVATE handshake** is in-process for S73; moves to a durable queue in S74.
- **RSA signature** on `ACTIVATEMessage` is stub `""` in S73; Key Vault + signing wired in S74.
  Documented as `DRIFT-001`/`DRIFT-002` in `agents/master/laws/laws.md`.
- **`DEFAULT_GRANTS` is functional** (interface-name → operation list), never product-name based.
- **`write_agent_definition`** is a public store helper for S74 pre-registration of known agent types.
- **`forecaster/Dockerfile`** gets the `forecaster` extra dep group (PyTorch + FinBERT weight).

### Tests

11 tests, all passing. Clause citations: `MST-IDN-01`, `MST-IDN-02`, `MST-STA-01..04`,
`MST-OUT-01..02`, `MST-IDM-01`, `MST-NEV-01..02`.

### Coverage

100% (906 tests total, 4 skipped network/creds).

### Version bump

No version bump — no new user-facing capability shipped. This is infrastructure scaffolding.

---

## Deferred (S74)

- RSA signing: master generates keypair; public key baked into agent images; `signature=` verified.
- Key Vault integration: master resolves agent secrets from Azure Key Vault and populates `config={}`.
- Neo4j retry / exponential backoff on startup failure.
- Durable handshake queue (replace in-process queue with Azure Service Bus).
- Push agent images to DockerHub; wire Azure Container Apps deploy manifest.
