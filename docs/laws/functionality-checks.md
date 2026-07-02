# Functionality-check register — every sprint's real-environment proof

Every sprint ends with a **functionality check**: the delivered capability exercised in a *realistic*
environment (not just unit tests — **LAW-02**, success is proven, never assumed). `make ci` green is
necessary but not sufficient. Each entry names what was run, against which **real** systems, the result
(with evidence), and confirms **teardown** — every test artifact removed, the environment left as found.

**Procedure (per sprint):** run the check → tear down (DETACH DELETE test nodes on Aura, cancel paper
orders, delete scratch files) → append a row here. If a sprint's feature has no realistic target yet
(a primitive awaiting later sprints), say so and check the nearest real thing it enables.

Dev graph store for checks: **Aura `bce05bd6`** (`neo4j+s://bce05bd6.databases.neo4j.io`). Return it to
its prior node count after each check.

| Date | Sprint | What was exercised | Real environment | Result | Teardown |
| --- | --- | --- | --- | --- | --- |
| 2026-07-01 | S97 serve_loop | Primitive — **no realistic target yet** (needs an agent served over it, S98, across containers, S100). Checked the nearest real thing it enables: the delivered pipeline + the graph store. | Aura `bce05bd6`; Tiingo/FMP/Finnhub/Alpha Vantage; Alpaca paper (probe) | `probes`: **12 green / 0 red** (incl. Neo4j reachable + write/read + uniqueness on the recreated instance). Live cascade `run_local.py --real --observe` (run-id `live-20260701-1`): full provider→reporter chain, **OBSERVATORY OK**, 1 position (in-memory `PaperBroker`, not live Alpaca). | ✅ Broker probe order canceled (account flat). Cascade's 31 Aura nodes DETACH DELETEd → **Aura at 0**. |
| 2026-07-01 | S98 serve supervisor/operator | `serve_loop` serves a **real agent capability** against real Aura: supervisor `flag_for_human` dispatched via `serve_once` → handler wrote a `Flag`; durability confirmed from a **separate** connection. | Aura `bce05bd6` (`Neo4jGraphStore`, asserted) | ✅ `store = Neo4jGraphStore`; `SERVED accepted=True`; **DURABLE = 1** (a separate raw connection saw `flag:S98-REAL:warn`). Proves serve_loop runs something real and the write commits durably (no store bug). | ✅ `Flag` DETACH DELETEd → **Aura at 0**; scratch scripts removed. |
| 2026-07-01 | fix: master auth-frenzy | The login-frenzy fix: deploy creds corrected + `kernel.startup.ensure_reachable_or_halt` — a startup guard that **halts instead of crash-looping** on a bad Neo4j connection (a crash-loop was hammering Aura auth → account lockout → instance recreate). Checked *without* hammering Aura: bad connection uses a **fake** graph (0 real auth attempts). | Aura `bce05bd6` (real probe) + fake failing graph | ✅ [1] guard passes on real Aura (`reachable=True`, no halt); [2] bad connection **halts, never raises** (`raised=None`, FATAL logged) — no restart storm; [3] deploy user/db now `bce05bd6/bce05bd6` == `.env` (MATCH). | ✅ Reads only — no Aura writes; scratch script removed. |
| 2026-07-01 | S104 credential-tested activation | DL-36 A+B: master tests each credential before handover; a required failure refuses activation + writes an `Escalation`. Bad case uses a deterministic-fail test (0 auth hammering). | Aura `bce05bd6` (`Neo4jGraphStore`, asserted) | ✅ `[GOOD]` a **real** Neo4j connectivity test passed → `ACTIVATE issued` (config handed over); `[BAD]` failing test → `ActivationRefused` + **`Escalation` durably written** (`agent=scanner, failed=['neo4j'], status=open`). | ✅ `AgentInstance`+`CapabilityGrant`+`Escalation` DETACH DELETEd → **Aura at 0**; scratch removed. |
| 2026-07-01 | S105 master secret cache | KV secret cache: the master caches fetched secrets for repeated references (`CachingSecretStore`, TTL minutes, 0=never). | Real `EnvVarSecretStore` (reads `os.environ`) | ✅ Fetched a secret, **deleted the underlying env var**, fetched again → the cache still returned it (`CACHE SERVED THE REPEATED REFERENCE: YES`) — served from memory, no re-fetch. Live-KV verification awaits a provisioned Key Vault (mechanism is store-agnostic). | ✅ Reads only — no Aura writes; process-local env var + scratch removed. |
| 2026-07-02 | S106 remediation planner | DL-36 C: credential failure → `Escalation` → real GPT-5.5 bounded-catalogue selection → linked `RemediationPlan` with `auto_eligible`. Also checked `auto_remediation_scope=all` makes destructive catalogue choices auto-eligible. | Aura `bce05bd6` (`Neo4jGraphStore`, asserted); OpenAI `gpt-5.5` | ✅ Aura started at 0 nodes. GPT-5.5 selected `refetch-from-key-vault` for the safe-only failure (`auto_eligible=True`, rationale captured) and `rotate-credential` for the compromised/destructive failure under `scope=all` (`auto_eligible=True`). Both plans were durably written and linked via `PLANNED_BY`; choices were validated as catalogue members. | ✅ Test `Escalation` + `RemediationPlan` nodes DETACH DELETEd by test keys/agent types → **Aura at 0**. |

**Lessons (harness):** a first S98 attempt "passed" but silently ran in-memory — `build_graph_from_env()`
returns `InMemoryGraphStore` unless **`NEO4J_URI` is in `os.environ`**, and a `load_dotenv()` called from a
script *outside* the repo tree (e.g. the scratchpad) never finds `.env`. **A real check must load `.env`
by explicit path and assert `isinstance(graph, Neo4jGraphStore)`** before trusting the result. This false
"durability bug" is the reason functionality checks must verify the environment, not assume it (LAW-02).
