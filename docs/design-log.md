# Design log — in-flight discussions, options, and what we ruled out

The home for design reasoning **before** it hardens into an ADR. Captures the question, the
options weighed (including the ones rejected and *why*), and the current status. This is the
LAW-05 ("every choice has a recorded why") and LAW-01 ("everything is a proposal") record for
threads that are discussed but not yet decided. When an entry resolves, it graduates to an ADR
and is marked CLOSED here.

---

## DL-01 · Primary organizing lens for `ops/`  ·  status: OPEN

**Question.** A filesystem is one tree, so the `ops/` realm can show only one organizing lens
as folders. Which is primary?

| Lens | Organizes by | Residency appears as |
| --- | --- | --- |
| Departmental | who owns / escalation | a GRC concern |
| DataCentre | kind of resource (compute/network/storage) | an attribute (region property) |
| **Lifecycle** | when in the process (build→deploy→operate→recover→retire) | a gate in the flow |

**Key insight (keep regardless of choice).** These are **views, not rival taxonomies.** The
*atoms* (the OIDC app, the Aura instance, a gate) are lens-independent; only the grouping
changes. Pick one lens for the folder tree; express the others as view-indexes now and **Neo4j
queries later** (one graph, project any view). This is a strong argument for modelling `ops/`
in the graph.

**Ruled out.** Committing the tree to one lens *permanently* (violates LAW-01). The current
`departments/` layout is provisional.

**Status.** Operator leaned **Lifecycle** (interrupted before confirming). Not final. Decide
before filling the remaining charters, so they're filed under the right primary lens.

---

## DL-02 · Data-residency: governing gate vs infrastructure attribute  ·  status: OPEN

**Question.** Is residency a **gate** that can block any operation, or an **attribute** of the
infra layer?

- **Option A — governance gate (GRC owns it).** Every deploy/data-move passes a residency check
  first. ✅ provable to a regulator (LAW-05); wrong-region move is structurally impossible.
  ❌ extra ceremony per region-touching action.
- **Option B — infra attribute (region property).** ✅ simpler, fewer gates, matches the
  DataCentre lens. ❌ residency becomes implicit/scattered; nothing *stops* a non-compliant
  move; "prove why here?" is manual and audit-risky.

**Recommendation on record.** **Option A** — financial data with tax-jurisdiction exposure; the
cost of an undefendable region is high. Note the lens choice (DL-01) tugs this: DataCentre→B,
Departmental/Lifecycle-with-GRC→A.

**Status.** Operator leaned **Option A** (interrupted before confirming). Not final.

---

## DL-03 · Multi-tenant residency model — the three-plane decomposition  ·  status: DRAFT (not decided)

The most important architectural idea from the 2026-06-21 platform discussion. Captured so it
is not lost; **not committed** — there are no real clients yet.

**The unlock — classify data by *who it is about*:**

| Tier | Examples | About | Residency? |
| --- | --- | --- | --- |
| Operational | master registry, identity, grants, sessions | the system | none — central |
| Reference/market | OHLCV, news, fundamentals, the universe | instruments | none — global |
| Signal/model | scores, forecasts, regime, model artifacts | instruments | none — global |
| Client-personal | KYC, PII, identity | the client | **strictly zoned** |
| Client-financial | positions, orders, fills, P&L, broker links | the client | **zoned + retention** |

Only the bottom two rows carry a jurisdiction. Everything that makes it a *trading* system is
about stocks, not people.

**Falls onto the 12 agents as three planes:**

- **Signal plane** (scanner · analyst · forecaster · provider) — market signals about
  instruments → **global, shared, one instance, cheap.**
- **Client plane** (portfolio_manager · execution · monitor · reporter) — applies signals to a
  *client's* portfolio → **the only part that gets zoned**, deployed per residency zone.
- **Control plane** (master · operator · supervisor · curator · researcher) — orchestration →
  **central "home" region.**

**Consequences / sub-points:**

- "Spin up an EU zone" = the `ta` deploy framework run with `--region=eu` against an EU graph.
  The multi-region topology *is* the ops framework parameterised by zone.
- **Compute follows data:** processing is itself a transfer (GDPR), so client-plane agents must
  *run* in the zone of the data they touch — not just store there.
- **Aggregation:** zones report anonymized aggregates upward; the centre sees money, never people.
- **Residency is 3 strands** that can point to different countries for one person:
  data-protection (where privacy law applies — extraterritorial, e.g. GDPR follows EU residents),
  tax (CRS/FATCA reporting + retention), regulatory (which financial regulator governs the
  service). The onboarding "interview" must capture them separately; the data domicile is
  derived to satisfy the **strictest intersection**; if none lawful → **decline the client.**

**Ruled out (implicitly).** One global graph for all clients (fails residency); full
stack-per-zone for the *entire* fleet (needless cost — only the client plane needs zoning).

**Status.** DRAFT model, deferred until real clients. **The constraint to protect now:** do not
build a single-tenant data model that can't partition by residency zone later. Graduate to an
ADR ("tenant-partitioned by residency zone; domicile policy-derived at onboarding") when the
data model is next touched.

---

## DL-08 · Agent work loop — "graph as queue" pull model  ·  status: DECIDED (2026-06-21)

**Question.** How do deployed agents get triggered to do their work? (DL-07c concrete design.)

**Decision (operator, 2026-06-21).** **Graph-as-queue / DB-mediated pull model:**

- **Provider** is the sole data-ingestor — one container, runs on its own cadence (market-close
  cron or manual trigger), fetches OHLCV + news + fundamentals, writes everything to the graph,
  then exits or sleeps until the next cycle. Other agents do not need provider alive to work.
- **All other agents** poll the graph: "Is there data with my name on it that I haven't processed
  yet?" If yes → process → write results → loop. If no → sleep(N) → loop.
- **The graph IS the queue.** No Azure Service Bus dependency in the work loop. The P14 pub/sub
  bus becomes an **optional fast-path notification** layer ("doorbell" — hint to wake up early
  instead of waiting for the poll interval). The graph is the source of truth; the bus is additive.

**Work-loop pattern per agent:**

```python
payload = activate_agent(...)          # EHLO → ACTIVATE → config injected to env
graph   = build_graph_from_env()       # reads NEO4J_URI + creds from env (_apply_config set them)
agent   = ScannerAgent(settings, graph=graph)
while True:
    pending = find_unprocessed_scan_windows(graph)   # Cypher: no ScanResult downstream
    for window in pending:
        agent.run(window)
    time.sleep(POLL_INTERVAL)          # default 60s; tunable per SCAN_POLL_INTERVAL env var
```

**Why this model over pure pub/sub:**

| Question | Graph-pull (this decision) | P14 pub/sub only |
| --- | --- | --- |
| Provider down → analyst broken? | No — analyst reads existing DB rows | Yes — event never arrives |
| Test one agent in isolation? | Yes — feed DB, start agent | Hard — upstream must be publishing |
| Azure Service Bus required? | No | Yes |
| Debug state? | `ta graph` at every stage | Log correlation across agents |
| Latency (EOD data) | ~poll interval (60s fine) | Sub-second (overkill) |

**Ruled out.** Pure pub/sub-only work loop (too coupled; agent failure cascades upstream; bus
is a hard runtime dependency for every run; hard to test agents in isolation).

**Consequences:**

- Provider entrypoint gets a `--ingest` mode (or always runs its ingest loop).
- Each agent needs a `find_unprocessed_{agent}_work(graph)` graph-query function.
- Neo4j credentials must reach every agent via ACTIVATE.config (not just master).
  Means adding `neo4j-uri` / `neo4j-user` / `neo4j-password` to `AGENT_SECRETS` for all agents,
  OR deploying them as plain env vars on the Container App (no KV, acceptable — they're connection
  strings, not secrets in the same sense as API keys). **Decision needed (DL-08a, open).**
- `idle_loop()` is replaced by the agent's work loop once this is wired.
- P14 pub/sub bus remains in the codebase as the speed-path; agents can optionally subscribe
  for faster wake-up. The bus subscription is additive, never required for correctness.

**Status.** DECIDED. Graduate to an ADR ("graph-as-queue work loop") when the first agent
(`provider → graph`) implementation lands.

---

## DL-08b · Agents fetch market data over the bus, not the graph — S79 scope correction  ·  status: DECIDED (2026-06-22)

**Constraint discovered (S79 kickoff).** DL-08 assumes every agent reads its inputs from the
graph. The code does not work that way yet:

- **Scanner** (`_run_scan`) and **analyst** (`_analyze`) acquire OHLCV/regime via **live bus RPC
  to the provider** — `request_market_data(self.bus, …)` → `bus.request(recipient="provider")`.
  The graph claim-check only carries the *handoff artifact* (candidates, recommendations) between
  adjacent agents — **not** the underlying market data.
- **S78's ingest writes a summary, not data.** `write_market_snapshot` persists
  `bar_count`/`requested`/`returned` — *not the bars themselves*. There is nothing in the graph
  for a downstream agent to read market data **from**.
- **Per-container `InProcessBus` can't do cross-container RPC.** Each agent container builds its
  own local bus (as the S78 provider entrypoint does). A scanner's `bus.request(recipient=
  "provider")` hits its *own* empty bus — the provider is in a different container. This coupling
  is exactly what DL-08 chose graph-as-queue to eliminate.

**Consequence.** S79 implemented literally (add `poll.py` + `work_loop()`, swap `idle_loop()`)
would pass CI but the agents would still **fail at `request_market_data`** — green, but not
actually standalone. The sprint's headline goal would be unmet.

**Decision (operator + Claude, 2026-06-22).** **Reshape S79 to a vertical slice (provider→scanner)
rather than the full six-agent rewrite.** Smallest surface that proves DL-08 is real:

1. **Provider ingest persists the full market payload** to the graph (bars + earnings + …), not
   just a summary node — so a downstream agent has something to read.
2. **Scanner reads market data from the graph** (a graph-backed market source) instead of bus RPC,
   ending the provider→scanner bus coupling for this handoff.
3. **Ship the reusable `work_loop()` kernel helper** (find_pending → process → sleep).

**Ruled out (this sprint):**

- *Full six-agent rewrite* — multiplies the speculative-Cypher / schema-discovery risk per agent;
  no shippable checkpoint if quota runs out mid-pipeline.
- *Triggers-only (poll claim-check artifacts, keep market-data RPC)* — passes CI but agents still
  die at `request_market_data`; buys the appearance of standalone agents without the substance.

**Pattern established for S80+.** The graph-backed market source built here is the template the
analyst / PM / execution / monitor / reporter reuse when their data paths move graph-first.

**S80 (2026-06-22) — extended the slice to scanner→analyst.** Provider now also persists the full
`RegimeContext` (`ingest._write_regime_context`, keyed by window-end date); scanner persists the
full `CandidateSet` on its `ScanRun` node; analyst reads all three from the graph
(`agents/analyst/poll.py`: `find_pending` over `ScanRun` lacking an `ANALYZED_BY` descendant +
`analyze_scan_node`, which pulls the `CandidateSet` from props, the `MarketData` via the ScanRun's
`DERIVED_FROM` descendant, and the same-day `RegimeContext` by date). The scoring core was extracted
to `agents/analyst/run.py` (`run_analysis`) so the bus path (`_analyze`) and the graph path share one
implementation. **Bug caught by the coverage gap:** the lineage edge is `(scan)-[:DERIVED_FROM]->(market)`,
so market is the ScanRun's *descendant*, not ancestor — the first cut walked `ancestors` and would have
returned empty results forever. **Still deferred to S81:** PM, execution, monitor, reporter.

**Status.** DECIDED. S79 = provider→scanner; S80 = scanner→analyst; PM→reporter → S81.

---

## DL-08a · Neo4j credentials distribution — KV secret vs plain env var  ·  status: OPEN

**Question.** Do non-master agents receive their Neo4j connection string + credentials via
`ACTIVATE.config` (i.e., in `AGENT_SECRETS` / Key Vault), or as plain Container App env vars
set at deploy time?

- **Option A — KV-distributed (ACTIVATE.config path).** Add `neo4j-uri`, `neo4j-user`,
  `neo4j-password` to `AGENT_SECRETS` for all 12 trading agents; master resolves from KV and
  injects. ✅ Single source of truth; changing the URI requires only a KV update. ❌ Every
  agent appears in `AGENT_SECRETS`; bootstrap failure blocks DB access.
- **Option B — Plain env vars (deploy-time).** Set `NEO4J_URI`, `NEO4J_USER`,
  `NEO4J_PASSWORD` as Container App env vars in `deploy-agents.ps1`. ✅ Simple, zero bootstrap
  coupling; `NEO4J_PASSWORD` is a connection credential, not an API key — acceptable as a
  deploy-time secret. ❌ Changing the URI requires redeploying all agents.

**Recommendation.** Option B for now. Neo4j URI + user are non-sensitive config; password can
be a Container Apps secret (stored in the app, not KV, which is the same security model as other
Container App–managed secrets). KV path is for externally-issued API keys (Tiingo, Alpaca, etc.).
Revisit if agent count or rotation frequency makes deploy-time updates burdensome.

**Decision (operator, 2026-06-21).** **Option B — plain Container App env vars.** Neo4j URI +
user are non-sensitive config; password is stored as a Container Apps secret (in-app, not KV).
KV path reserved for externally-issued API keys (Tiingo, Alpaca, Anthropic, etc.).

**Status.** CLOSED.

---

## DL-07 · Key Vault secret-name + missing-secret reconciliation  ·  status: PARTLY OPEN

Surfaced while wiring Key Vault (B). Two issues found and how they're handled:

**1. The config-consumption bridge is MISSING (the real issue, discovered 2026-06-21).** Nothing
reads `ACTIVATE.config` — a grep for consumers is empty. Agents read credentials via
pydantic-settings with an `env_prefix` (e.g. `ProviderSettings` → `env_prefix="PROVIDER_"` →
`PROVIDER_TIINGO_API_KEY`), **not** from the injected config. So the master→KV→`ACTIVATE.config`
path (S75 + B, proven live) is **plumbing that works but is unconsumed**: no code applies the
returned config to the agent's environment/settings. The injected secrets currently go nowhere.

This couples three things into one piece of work:
  (a) a **config→env bridge** — the agent applies `payload["config"]` to `os.environ` *before* its
      settings/work loop reads them;
  (b) a **canonical credential-naming scheme** — `secret_map` output keys must match the settings
      env-var names (incl. the `PROVIDER_`/etc. prefixes), reconciled with `.env` + the KV secret
      names. Current mismatch: `.env` uses provider-prefixed names (finnhub, fred) plus an `FNP_`
      typo for fmp and *unprefixed* tiingo/alpaca, while `secret_map` emits unprefixed UPPER_SNAKE
      keys with no `PROVIDER_` prefix and a different alpaca spelling. One scheme must align all four;
  (c) the **event/work loop** — agents currently `EHLO → idle_loop()`; they don't run their jobs, so
      nothing accrues data (the "live run for news" is inert until this is wired).
All three are the same next piece: **"agents actually do work"** (the bridge from deployed+idle to
operating). It touches the credential scheme system-wide and handles money — scope it as a
deliberate sprint, not a tail-end patch.

**2. Missing-secret behaviour (FIXED).** `AzureKeyVaultSecretStore.get_secret` *threw* on a
not-found secret, but `Null`/`EnvVar` stores return `""` (and `resolve_config` skips empties). So an
agent entitled to an unseeded secret would fail to activate. Fixed: catch `ResourceNotFoundError` →
return `""`. Lets us seed only the secrets that exist (tiingo, anthropic) without breaking the rest.

**3. Alpaca seeding deferred (safety).** `.env` has both live (`ALPACA_API_KEY`) and paper
(`ALPACA_PAPER_API_KEY`). Seeding *live* trading creds into the pipeline is a money-risk; deferred
until the operator makes the paper-vs-live call. KV currently holds only `tiingo-api-key` +
`anthropic-api-key`.

---

## DL-04 · Model `ops/` in Neo4j as a multi-view engine  ·  status: IDEA (later)

Per DL-01: tag each operational atom once (`Subsystem`/`Gate`/`Runbook`, `DEPENDS_ON`/`AFFECTS`),
then query any lens (departmental / datacentre / lifecycle) and run change-impact ("what breaks
if I touch X?"). Seed from the markdown charters first; graduate to the graph when they stabilise.

---

## DL-05 · Cloud graph store hosting  ·  status: DECIDED (refined 2026-06-21)

**Question.** Where does the graph live for the cloud fleet, given we can't afford paid Aura?

**Decision (refined — operator).** **While the Aura trial lasts: use the real Aura** and stay "as
close to reality as possible" (real managed graph, real persistence/backups). **Pause smartly** —
pause the instance whenever the fleet isn't actively being tested (`aura.ps1 pause`,
`deploy-agents.ps1 down`) to stretch the trial credit and keep PAYG low. **When the trial ends:**
fall back to **in-memory** (`MASTER_GRAPH=memory`, shipped v0.14.0 — registry rebuilds on boot, $0)
until trading needs durable provenance, **then** a small **Azure VM (~$15/mo)**.

So the order of preference is: **real Aura (trial, smart-paused) → in-memory (post-trial) → VM (when
durable data matters).** The in-memory toggle is the *fallback*, not the everyday default.

**Ruled out.**

- *Paid Aura* — cost (operator can't afford it).
- *Aura Free* — auto-pauses after 3 days idle; operator said "no Aura".
- *Tunnel to the operator's machine* — worst of both: needs the laptop always-on (= fleet
  availability) and a DB-over-tunnel security surface, with *none* of a VM's reliability, to solve
  a persistence problem we don't have yet. Actively steered away from.

**Trade-off accepted.** In-memory loses persistence across master *restarts* (a restart empties the
registry; running agents then differ from the master's view). Tolerable at the test-rig stage; the
trigger to move to a VM is "real graph data worth keeping."

## DL-06 · Neo4j edition — Community baseline, but backup is a real deferred cost  ·  status: DECIDED (for now)

**Risk.** The local Neo4j **Enterprise** eval expires at 30 days; a Neo4j **Developer license** was
requested and may not be granted.

**Correction (operator caught this).** Enterprise was **not** a cosmetic choice — ADR-0008 chose it
deliberately for **automated online/differential backup + point-in-time restore**, specifically to
avoid hand-rolling backup management and to make **region moves** clean (a `scenarios.md` case). An
earlier note here glibly said "Community loses nothing you use" — wrong.

**What Community actually costs.** It loses **online/hot backup + PITR**. It does **not** force custom
tooling: `neo4j-admin database dump`/`load` and APOC export (`apoc.export.cypher`) are built-in and
cover region-move backups — but **with downtime and no restore-to-timestamp**. So: Enterprise =
zero-downtime + fine-grained recovery; Community = coarse, downtime-y, but built-in. Early stage
(small graph, brief downtime OK) → Community is adequate. The Enterprise advantage earns its keep at
scale / for true DR.

**Decision.** **Community is the assumed baseline** (free, forever); Enterprise (dev license *or*
managed Aura) is a **documented optional ops upgrade, never an app dependency** — exactly ADR-0008's
own rule ("app logic must not depend on an Enterprise-only feature; ops/backup layer may"). Also:
`NEO4J_DATABASE=neo4j` if no license; APOC Core + GDS still work; affects **local dev only** (cloud is
in-memory per DL-05, CI skips the Neo4j test).

**Open, deferred to "trading has durable data + does region moves":** pick the backup strategy —
Enterprise (license/self-host), managed Aura (backups included, ~$260/mo, currently unaffordable), or
Community dump/load + APOC export on a schedule. Not urgent now (nothing persisted). Tied to the same
horizon as the VM decision (DL-05).

**Small follow-up (when WSL2 returns post-trial):** verify no code/test hard-depends on the named db.
