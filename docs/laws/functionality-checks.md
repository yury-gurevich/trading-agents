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

**Lessons (harness):** a first S98 attempt "passed" but silently ran in-memory — `build_graph_from_env()`
returns `InMemoryGraphStore` unless **`NEO4J_URI` is in `os.environ`**, and a `load_dotenv()` called from a
script *outside* the repo tree (e.g. the scratchpad) never finds `.env`. **A real check must load `.env`
by explicit path and assert `isinstance(graph, Neo4jGraphStore)`** before trusting the result. This false
"durability bug" is the reason functionality checks must verify the environment, not assume it (LAW-02).
