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

**S81 (2026-06-22) — extended the slice to analyst→PM, PM ONLY.** Analyst now persists the full
`RecommendationSet` on its `AnalystRun` (S80 left it `{}`, counts only); PM reads it plus the
`MarketData` (via the AnalystRun's `ANALYZED_BY` ancestor = ScanRun, then its `DERIVED_FROM`
descendant) and the same-day `RegimeContext` (`agents/portfolio_manager/poll.py`). Sizing/risk core
extracted to `agents/portfolio_manager/run.py` (`run_evaluation`), shared by the bus path
(`_evaluate_orders`) and the graph path — the `_provider_rejection`/`_record_fault`/`_empty_result`
helpers moved out of `agent.py`, so the degraded-fault `source_module` is now
`agents.portfolio_manager.run` (one existing test assertion updated). **Scope decision (operator,
2026-06-22):** keep the one-handoff-per-sprint discipline — PM only, execution/monitor/reporter →
**S82**, rather than landing all four at once. **Ruled out:** doing all four in S81 (rejected — same
reason S79/S80 each took one hop: smaller diff, each handoff's lineage gap surfaces in isolation).
**Known limitation:** graph-pull PM builds a fresh `default_portfolio` each poll, not live
position/cash state (that needs execution/monitor running graph-pull first).

**S82 (2026-06-22) — closed the chain: execution + monitor + reporter (all three).** PM now
persists the full `OrderIntentSet` on its `PMRun`. Execution: submit core extracted to
`agents/execution/run.py` (`run_submit`, shared by `_submit` and the new poll path); `poll.py`
finds `PMRun` lacking `EXECUTED_BY`, submits via the injected broker, and writes a new
**`ExecutionRun` anchor** (`PMRun ─[EXECUTED_BY]→ ExecutionRun`) — execution previously wrote only
`Fill` nodes, leaving monitor nothing to poll. Monitor: dropped the live `latest_close_cents`
provider bus RPC (the second cross-container call) and reads current prices from the same-cycle
`MarketData` reached by walking the PM lineage (`EVALUATED_BY→ANALYZED_BY→DERIVED_FROM`); evaluate
core extracted to `agents/monitor/run.py`; `poll.py` finds `ExecutionRun` lacking `MONITORED_BY`.
Reporter: `build_snapshot` was already fully graph-native, so `poll.py` only adds the trigger
(`MonitorRun` lacking `REPORTED_BY`) and links the edge to the existing `Snapshot` node (no new
`ReporterRun` concept). **Scope decision (operator, 2026-06-22):** all three in one sprint (reporter
trivial; Aura deadline favours finishing the pipeline). **Ruled out:** writing S82 against a real
store first — operator chose code-first, store as a separate follow-on, accepting the Aura-lapse
risk. **Known limitations:** monitor prices = the same ingest snapshot the position was sized from
(fine for one daily cycle); PM portfolio state still fresh-`default_portfolio` per poll.

**Status.** DECIDED + COMPLETE. The graph-pull pull model now spans
provider→scanner→analyst→PM→execution→monitor→reporter end-to-end. S79 = provider→scanner;
S80 = scanner→analyst; S81 = analyst→PM; S82 = execution+monitor+reporter. The remaining blocker is
operational, not architectural: a permanent reachable graph store (see DL-05 / the permanent-store
follow-on) before the Aura trial lapses ~2026-06-29.

**S83 (2026-06-22) — the explicit start: dispatcher trigger + provider becomes graph-pull.**
Before S83 nothing "started a run" in the graph-pull world: the provider self-triggered on a
timer (`ingest_loop`, S78) and the only `Dispatcher` was the P14 **pub/sub** one, which can't
drive containers (no shared in-process bus). **Operator model (2026-06-22):** the dispatcher
places ONE "message on the queue" to trigger run #1; everything downstream is woken by
"completing the prerequisite gate". **Decision:** realise the "message on the queue" as a
`RunRequest` **graph node** (DL-08's graph-as-queue), and make the **provider graph-pull on it**
(`agents/provider/poll.py`: `find_pending` over `RunRequest` lacking `INGESTED_BY` +
`ingest_run_node`; entrypoint swaps `ingest_loop`→`work_loop`). So the dispatcher's RunRequest is
the *single* trigger source and **every** agent (provider included) is uniform graph-pull.
`orchestration/start.py` adds pre-flight checks + `place_run_request`; `orchestration/
local_pipeline.py`'s `cascade_once` runs one poll pass per agent (the fleet does this
continuously, one container each); `scripts/run_local.py` is the runnable demonstrator and
`test_graph_pull_e2e.py` is the first end-to-end proof. **Ruled out:** (a) keeping the provider
timer-self-triggering (rejected — no explicit "start", and two trigger sources); (b) reusing the
pub/sub `Dispatcher` for the fleet (can't — needs one in-process bus across containers). The P14
`Dispatcher` is left intact as the in-process dev path. **Deferred:** a **dispatcher cron** to
place the daily RunRequest on a schedule (operator deferred) — today it's placed by hand / the
demonstrator.

**Status.** DECIDED + COMPLETE (orchestration trigger). The pipeline now has an explicit
single-trigger start and a uniform graph-pull model end to end, proven in one process. Real-fleet
run still gated on the permanent graph store.

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

---

## DL-09 · Filter decisions as a labeled training source — measure to improve  ·  status: DRAFT (2026-06-22)

**Question.** The scanner filters drop tickers (`min_price`, `min_average_volume`,
`min_relative_strength`, `max_beta`, `earnings_window`). How do we *prove* a filter is right, and
turn its decisions into labeled data for LLM/predictor training? "I need deterministic methods to
prove the filter is right … We need to be able to measure it in order to improve it." This is to be
**one source among several** feeding a training set.

**The gap.** A dropped ticker vanishes — we never learn what it would have done, so there is no
label and no way to score the filter. `FilterTrace.dropped_by_filter` only *counts* drops
(`{min_relative_strength: 1}`); it carries neither the per-ticker features judged nor the outcome.

**Direction (two mechanisms + a measurement):**

1. **Per-ticker verdict record.** Persist a `FilterVerdict(ticker, decision, filter_fired, features)`
   on each `ScanRun` — every evaluated ticker, survived or dropped, with the exact metrics the filter
   judged (price, avg_volume, relative_strength, beta, days_to_earnings). This is the example's
   *input*; today only aggregate counts survive.
2. **Global `bypass_scanner_filter` flag (default off).** When on, all evaluated tickers become
   survivors (tagged `bypassed=True`) but the verdict still records what the filter *would* have
   decided. Dropped-but-bypassed tickers flow analyst→PM→execution→monitor, so their realized
   outcome becomes the **label**. This is the only way to get the counterfactual — a ticker the
   filter would have dropped, allowed to prove the drop right or wrong.
3. **Confusion matrix per filter** (the evidence, computed deterministically from recorded verdicts +
   realized returns): dropped×down = good drop, dropped×up = missed winner, kept×up = good keep,
   kept×down = wrong keep. Yields per-filter precision and miss-rate → which filters earn their place
   and which throw away winners. Reproducible from stored records, so it is provable, not anecdotal.

**Label decision (operator, 2026-06-22): record BOTH labels side by side.** Each verdict carries
(a) **raw forward return** over a fixed horizon from the bypassed bars — the filter measured *in
isolation*, deterministic, independent of PM behavior; and (b) the **full-pipeline trade outcome**
(close trigger after bypass runs PM→execution→monitor) — the filter *as actually traded*. Two
columns let us separate "the filter dropped a name that rose" from "the filter dropped a name the PM
would have rejected anyway" — i.e. attribute misses to the filter vs to downstream gates.

**Plugs into existing machinery — not a parallel path.** The curator already turns
`ExampleRecord(content, label, source_ref, metadata)` → `DatasetManifest` (train/val/test) →
advisory `Predictor`; its sole source today is `TradeNarrative` lineage labeled by close trigger.
Filter verdicts become a **second assembler** (`assemble_filter_examples`) feeding the same pipeline.

**Platform/pack reading.** The collect→measure→improve *loop* (verdict record, bypass, outcome
labeling, confusion matrix, curator dataset/predictor) is **substrate** — it is the "text-defined
business" self-improvement mechanism. The specific filter *features* are **trading-pack**. So this is
a pack-specific assembler feeding the substrate curator — a clean test case for the platform/pack wall
work queued next.

**Ruled out.** (a) Logging only the aggregate `dropped_by_filter` counts — no per-ticker features and
no outcome, so unmeasurable. (b) Recording verdicts *without* bypass — gives the filter's decision but
never the counterfactual label, so drops can never be scored, only keeps. (c) A bespoke training-data
store outside the curator — duplicates the existing ExampleRecord/Manifest/Predictor loop.

**Status.** COLLECTION SIDE SHIPPED (S88, 2026-06-22, 0.24.00). `contracts/scanner.py::FilterVerdict`
`(ticker, decision, filter_fired, features, bypassed)` rides `FilterTrace.verdicts` (additive, scanner
CONTRACT 0.1.0→0.2.0) and persists on `ScanRun` for free; `ScannerSettings.bypass_scanner_filter` (bool,
default off) emits would-be-dropped tickers as survivors tagged `bypassed` so their downstream outcome
can be observed, while the verdict records the real drop. `filters.apply_filters` reworked to emit a
verdict per ticker (features + first-failing-filter); survivor output unchanged. **Verdict schema +
bypass semantics are now fixed in code** — ready to graduate to an ADR.
**MEASUREMENT ENGINE SHIPPED (S89, 2026-06-23, 0.25.00).** `agents/curator/domain/filter_quality.py`:
`score_filters(verdicts, outcomes) -> FilterScorecard` (pure) computes the per-filter confusion matrix —
`good_drops` (dropped×fell), `missed_winners` (dropped×rose), `precision` per filter — plus overall keep
quality (`good_keeps`/`wrong_keeps`/`keep_precision`); `collect_verdicts(graph)` reads recorded verdicts
off `ScanRun` nodes. Outcomes are **injected** (fixed-horizon forward return per ticker), same discipline
as the forecaster scorecards. Bypassed drops carry a real outcome, so a drop that rose is finally counted
as a missed winner — the counterfactual made measurable.
**REMAINING — wire real outcomes (DL-09 part B.2):** (1) forward-return outcomes from the reference
Postgres (price_cache OHLCV) over a fixed horizon from each scan date; (2) expose a curator capability +
`assemble_filter_examples` → ExampleRecord/Manifest/Predictor; (3) optional surface/CLI to print + persist
the scorecard. The pure measurement core is done and unit-tested.

---

## DL-10 · Staleness gate counts calendar days, not trading sessions  ·  status: CORRECTED (S87, 2026-06-23)

**Resolution (S87).** Chose **option (a)** — count **trading sessions**, with the dependency-free twist of
option (b): `agents/provider/domain/market_calendar.py` (`trading_sessions_between`, a static NYSE holiday
set 2024–2027, weekend-aware) measures session distance; `integrity.py::_stale_tickers` now flags a ticker
only when `trading_sessions_between(latest_bar, window.end) > max_staleness_days`. The setting's `why` was
corrected to read *"three TRADING SESSIONS."* A holiday weekend no longer kills a run. Proven by
`test_market_calendar.py` (4 cases). *Bookkeeping: this status was left OPEN until the DL-19 session
(2026-06-25) verified the fix and closed it.* The EXP-006 `calendar-staleness` Class-1 case (an LLM that
*doesn't* know this fix) remains a useful grounding probe — the firewall's answer key, not a live bug.

---

## DL-10 (original, OPEN 2026-06-22)

**How it surfaced.** First live Aura run (3 tickers, 2026-06-22). The batch trace showed
`analyst: scored=0 rejected=2`, both rejected `provider market data degraded` — i.e. the analyst
bailed at `run.py:39` (`market.quality.used_fallback`) before scoring anything. Tracing upstream:
`MarketData.quality` = `{used_fallback: True, stale_tickers: (AAPL, GOOGL, MSFT), notes:
(stale_or_missing_tickers,)}`. The latest bar for every ticker was **2026-06-18, only 4 calendar
days before the window-end** — fresh data, yet condemned as stale.

**Root cause.** `agents/provider/domain/integrity.py::_stale_tickers` measures
`(window.end - latest_bar).days > max_staleness_days` in **calendar days**, with the default
`max_staleness_days = 3`. But the setting's own `why` says *"older than three **sessions**"* — the
intent is **trading sessions**, the implementation is **calendar days**. They diverge across any
market closure:

- Thu Jun 18 = last real session · Fri Jun 19 = Juneteenth (NYSE closed) · Sat–Sun = weekend ·
  Mon Jun 22 = run date. Jun 18's close is the **freshest data that can exist** — zero sessions stale
  — but **4 calendar days** old → `4 > 3` → whole batch flagged degraded → entire pipeline produces
  nothing. One ordinary holiday weekend silently kills every run.

**Why it matters.** A calendar-day staleness gate conflates *"the data is genuinely old"* with
*"the market was closed."* Every Monday after a holiday Friday (and any Tuesday after a Mon holiday)
trips it. The trade side of the pipeline goes dark precisely when nothing is actually wrong. This is
a correctness flaw in the degraded-data guard, not a tuning nit.

**Options (not yet decided):**

- **(a) Count trading sessions** between `latest_bar` and `window.end` using a market calendar
  (exchange holiday + weekend aware). Correct, but introduces a calendar dependency/source.
- **(b) Skip weekends + a static holiday set** in the day-count. Cheaper, no live dependency, but the
  holiday list must be maintained and is exchange-specific.
- **(c) Widen the default** (e.g. `max_staleness_days = 5`) as a stopgap. Trivial, but a band-aid: a
  4-day holiday stretch (e.g. Thanksgiving, year-end) can still exceed any fixed calendar bound while
  the data is current. Masks rather than fixes.

**Ruled out.** Leaving it calendar-day with the default 3 — demonstrably breaks on a normal holiday
weekend (this run). Also note the `--real` demo path used the default 3 while the in-memory demo
passes `max_staleness_days=7`, so the in-memory tests **never exercised the degraded path** — the
gap was invisible until live data hit it.

**Status.** RESOLVED (S87, 2026-06-22, 0.23.04) — shipped **option (b): trading-session count via a
static NYSE holiday set + weekend exclusion**, dependency-free, over option (a)'s market-calendar
library. `agents/provider/domain/market_calendar.py::trading_sessions_between` counts NYSE sessions in
`(latest_bar, window_end]`; `integrity._stale_tickers` flags `> max_staleness_days` sessions instead of
calendar days. The Jun-18→Jun-22 case is now **1 session** (was 4 days), so fresh data across a holiday
weekend no longer kills the batch; a genuinely old bar still flags. Holiday set covers 2024–2027 (a date
past the window falls back to weekday counting); upgrade path = `exchange_calendars` /
`pandas-market-calendars` when the window needs extending or per-exchange precision. This is a pack-level
(trading) calendar living in the provider agent, not substrate.

---

## DL-11 · Aura backup/restore — API surface vs console-only ops  ·  status: NOTED (2026-06-22)

**From the Neo4j testing track (2026-06-22), verified against the live Aura Professional instance:**

- **Snapshot create + list work over the management API** (`POST`/`GET /v1/instances/{id}/snapshots`).
  `infra/aura.ps1 snapshot|snapshots` drive them. Note the create response carries **only**
  `snapshot_id` (not `status`/`timestamp`) — those appear in the list once the backup completes;
  the script was fixed to stop dereferencing the absent fields.
- **In-place restore is NOT available over the API.** `POST /v1/instances/{id}/restore` returns
  **`403 {"error": "Requested endpoint is forbidden"}`** for this key/tier. Restore is a **console-only**
  action (console.neo4j.io → instance → Snapshots → ↺). `infra/aura.ps1 restore` therefore cannot
  drive it; kept for the day the endpoint is permitted, but treat restore as a manual console step.
- **No byte-size in the API.** Snapshot objects expose `{snapshot_id, status, timestamp, profile,
  exportable}` — no size. On-disk store size is observable only from inside the DB via Browser
  `:sysinfo`; the serialized property payload of one batch run measured ~27.7 KB (MarketData node
  dominates at ~24 KB).
- **Console timestamps are local (AEST/+10); the API reports UTC** — a 05:30:11 UTC snapshot shows as
  15:30:11 in the console. Worth remembering when matching a CLI-triggered snapshot to a console row.

**Restore proven, end to end.** Planted a `RestoreProbe` sentinel node *after* a snapshot, restored
from that snapshot via the console, and confirmed the sentinel's label no longer exists — the DB rolled
back exactly to the snapshot point while all pre-snapshot pipeline data survived. Backup/restore is
trustworthy; the only constraint is that restore is a manual console operation, not scriptable here.

**Status.** NOTED — operational finding, no open decision. Revisit `aura.ps1 restore` if Neo4j later
exposes the restore endpoint to API keys.

---

## DL-12 · Platform/pack separation — master grant policy is the first leak  ·  status: IN PROGRESS (2026-06-22)

**Frame (ADR-0012).** The master is **substrate** (fleet bootstrap mechanism); it must not encode
trading-pack knowledge. `agents/master/grants.py::DEFAULT_GRANTS` violated this — it hardcoded all 12
trading agent types and domain capabilities (`broker`, `data_feeds`, `ohlcv`, …) inside the substrate.
First named leak to close in the platform/pack split.

**Step 1 shipped (2026-06-22): the injection seam.** `MasterAgent.__init__` now takes
`grant_policy: GrantPolicy | None` (`GrantPolicy = Mapping[str, dict[str, object]]`); `activate()`
reads the injected policy, not the module global. Default still falls back to `DEFAULT_GRANTS` so
behavior is unchanged and all callers keep working. Proven by a test that injects a custom policy: a
`widget` type (absent from `DEFAULT_GRANTS`) activates while `scanner` (present in `DEFAULT_GRANTS`,
absent from the injected policy) is rejected — i.e. the master genuinely consults the injected policy.
This is the load-bearing seam; nothing else in the split can proceed without it.

**The hard decision still open — WHERE the trading policy lives + HOW the master receives it.** The
import boundary (`kernel ← contracts ← agents ← orchestration/surfaces`) blocks the obvious move:

- The trading grant policy is pack config → it belongs in a pack module (e.g. `orchestration/packs/`).
- But `agents/master/entrypoint.py` (the master's container bootstrap) is in the **agents** layer and
  **cannot import** `orchestration/packs/` — agents may not import orchestration. So the production
  composition point for the master cannot pull a orchestration-located policy by import.

**Options (not yet decided):**

- **(a) Policy as data the master loads from config** (a JSON/YAML grant-policy file, path via
  `MasterSettings`; the trading pack ships the file). Substrate gains a generic "load a grant policy"
  mechanism; the pack supplies content as *data*, never as a Python import → no boundary violation.
  Matches the container-per-agent "agents start braindead, configured by data" model. Most correct.
- **(b) A top-level `packs/` package importable by `agents`** — inverts the dependency (substrate
  importing pack); contradicts ADR-0012. Rejected.
- **(c) Leave `DEFAULT_GRANTS` in `agents/master` as the default, relocate only the *type knowledge*
  later** — defers the real cut; the substrate still ships trading data. Stopgap only.

**Ruled out.** Importing pack grants into the master entrypoint (option b's boundary inversion).

**Status.** GRANT LEAK CLOSED (S84, 2026-06-22) — **option (a) chosen and shipped.** The 12-agent
grant table now lives in `orchestration/packs/trading_grants.json`, loaded by path via
`MasterSettings.grant_policy_path` (`load_grant_policy` in `agents/master/grants.py`) and injected by
the master entrypoint — never imported, so the `agents↛orchestration` boundary holds. `DEFAULT_GRANTS`
is deleted; with no injected policy the substrate knows no agent types. Deployed behavior unchanged
(loaded policy == old table, asserted). 0.23.01 (PATCH).

**BOTH MASTER LEAKS CLOSED (S85, 2026-06-22, 0.23.02).** The second leak,
`agents/master/secret_map.py::AGENT_SECRETS`, got the identical treatment: the per-agent
`(kv_name, env_name)` entitlement table moved to `orchestration/packs/trading_secrets.json`, loaded
via `MasterSettings.secret_map_path` (`load_secret_map`) and injected into `MasterAgent`;
`resolve_config(agent_type, store, secret_map)` now takes the map as a parameter. `AGENT_SECRETS`
deleted. **The master substrate now names zero trading concepts** — grants and secrets are both
pack-supplied data.

**DEPLOY WIRING DONE (S86, 2026-06-22, 0.23.03) — and the master *image* stays pack-agnostic.** Rather
than bake the pack JSONs into the substrate image (which would re-couple them), the pack policy travels
as **deploy-time config**: `_resolve_pack` in the entrypoint resolves each policy **base64 env content
(cloud) → file path (local) → None**. `deploy-agents.ps1` base64-encodes the two pack JSONs into
`MASTER_GRANT_POLICY_B64` / `MASTER_SECRET_MAP_B64` (like `MASTER_PRIVATE_KEY_PEM_B64`);
`docker-compose.yml` mounts `orchestration/packs/` read-only and sets the `MASTER_*_PATH` vars. The
master `Dockerfile` is **unchanged** — the same image runs any pack. `parse_grant_policy`/
`parse_secret_map` (JSON-string core) added; `load_*` delegate. The b64-content path is unit-tested; the
ps1/compose lines are inspection-verified (not CI-run). **DL-12 is now complete** for the master; the
only remaining ADR-0012 item is the `contracts/` substrate/pack split, deferred to a 2nd pack.

---

## DL-13 · Message-layer schema enforcement — bus IS bilaterally validated  ·  status: NOTED (2026-06-22)

**Trigger.** A flow audit (2026-06-22) of the two message paths (P14 bus RPC vs DL-08 graph-pull)
concluded the bus path was a schema gap: *"the bus does not validate the payload against
`Capability.request`; the handler is expected to call `model_validate` itself."* **Verified against the
code — that conclusion is wrong.** Recording the corrected reality so the audit's table is not trusted as-is.

**What the code actually does.** Every capability handler is registered through
`kernel/agent.py::AgentBase._bus_handler`, which wraps it:

```python
def wrapped(payload):
    request_model  = capability.request.model_validate(payload)    # validates IN
    result         = handler(request_model)                        # handler gets a MODEL, not a dict
    response_model = capability.response.model_validate(result)     # validates OUT
    return response_model.model_dump(mode="json")
```

`AgentBase.bind` (agent.py:37) and even the supervisor's hand-rolled `bind`
(`agents/supervisor/agent.py:69`) both route through `_bus_handler`. So **request and response are
schema-validated against the declared `Capability` types on every bus call**, by the framework, not by
handler discretion. The raw `InProcessBus.request` is schema-agnostic (it routes dicts + enforces
envelope + capability-exists + `caller_authorized`), but no agent registers a raw handler — they all go
through `_bus_handler`. Handlers' own `XRequest.model_validate(request)` calls are redundant
belt-and-suspenders. **The bus path is a typed, bilateral boundary, symmetric with graph-pull.**

**The one genuine residual gap — pub/sub events.** The `subscribe()` path has **no** `_event_handler`
wrapper analogous to `_bus_handler`; a topic carries no declared schema. Event subscribers validate by
convention (e.g. `provider._on_market_data_request` calls `DataRequest.model_validate(event)`), but
nothing in the framework enforces it. Events are fire-and-forget triggers, so the stakes are lower than
request/response, but this is the real "by the handler's discretion" case. **Optional hardening
(backlog, low priority):** an `_event_handler` wrapper + per-topic typing to make the event path
framework-enforced too.

**Accuracy nits in the audit.** (1) `model_dump(mode="json")` does not validate — it serializes an
already-constructed (hence already-validated) model; the producer's guarantee is from model
*construction*. (2) The graph-pull strength is real: producer constructs (validated) → `model_dump` →
consumer `model_validate`, both importing the *same* contract class.

**Status.** NOTED — no action required; request/response is bilaterally enforced on both transports.
Event-path validation is the only open hardening item, deferred.

---

## DL-14 · Operational path map — spine is live, the rest is aspirational or a gap  ·  status: NOTED (2026-06-22)

**Trigger.** Same flow audit (DL-13) drew 13 source→sink edges, raising the concern that the agent
chain has many concurrent live paths. **Verified: it does not.** The diagram conflates *contract
capabilities* with *what is actually running*. Classified by operational status:

- **Class A — the live spine (7 agents on `work_loop`).** RunRequest → provider → scanner → analyst →
  PM → execution → monitor → reporter (audit edges 1-7, 9). This is the only concurrent live flow — a
  linear graph-pull chain, one writer per stage, exactly what `scripts/run_local.py` /
  `test_graph_pull_e2e.py` exercise.
- **Class B — graph re-read, not a separate message** (edge 10). PM/monitor re-read the same
  `MarketData` node by walking lineage; no new path.
- **Class C — NOT wired (the 5 `idle_loop` agents).** forecaster, operator, supervisor, curator,
  researcher are still braindead. So audit edges 11 (forecaster `ShadowPrediction` — advisory, never
  gates even when wired), 12 (operator→supervisor), 13 (→supervisor faults) are aspirational, not running.
- **Class D — contract capability, unwired in graph-pull (a real gap).** Audit edge 8 (monitor
  `CloseDecisionSet` → execution `execute_close`): the monitor *decides* closes (writes `CloseDecision`
  nodes with `pnl_cents`), but `agents/execution/poll.py` has no close-handler and `monitor_pm_node`
  takes no broker — so **positions are opened (execution submits buys via the broker) but closes are
  decided and never executed** against a broker in the current operational path. Acceptable for
  paper/graph-tracked positions; an honest incompleteness vs the diagram. Wire the close-execution loop
  before live broker trading.

**Status.** NOTED. Reassurance: the live system is the linear spine (A), not a many-path tangle. Open
items: activate the 5 control-plane/advisory agents (C) and wire the close-execution loop (D) — both
out of scope until needed; flagged so they are not mistaken for already-working.

---

## DL-15 · DB placement — substrate registry should not use Neo4j  ·  status: OPEN (2026-06-23)

**Trigger.** ADR-0012 platform/pack wall + DL-12 (S84–S86) separated master grant/secret policy
from the trading pack. The next step in the split: the substrate registry (AgentInstance, Session,
CapabilityGrant, CapabilityRoute nodes currently stored via `GraphStore`) is backed by Neo4j —
a choice inherited from the trading pack's provenance graph, not from a substrate need.
**Operator direction:** "substrate (plumbing) should have its own DB. Neo4j belongs to the trading
system because it is the requirement that came from trading demands."

**Two distinct workloads, currently sharing one store:**

1. **Substrate registry** — Session, AgentInstance, CapabilityGrant nodes written by the master.
2. **Trading-pack provenance graph** — RunRequest → provider → scanner → analyst → PM → execution →
   monitor → reporter lineage, graph-traversal-heavy. Cypher queries throughout `kernel/graph_cypher.py`.
   Grows ~55 nodes / ~60 rels per run. Neo4j is genuinely the right fit here.

**Research complete — see [docs/research/db-placement/db-placement.md](research/db-placement/db-placement.md) for full
capability mapping against AuraDB Free, Azure free-tier options, and self-host alternatives.**

**KEY FINDING (2026-06-23): the substrate registry writes are audit-only. Code inspection of
`agents/master/agent.py` and `agents/master/store.py` shows:**

- `activate()` computes grants entirely from `self._grant_policy` (in-memory dict loaded from JSON)
  and returns them in `ACTIVATEMessage`. The `write_agent_instance()` + `write_capability_grant()`
  calls are **write-only audit records** — nothing reads them back to route work or make decisions.
- `drain()` does one `get_node("AgentInstance", ...)` to verify existence before stamping
  drain_reason/drain_at. A consistency guard inside the master itself, not external lookup.
- No agent outside the master, no Cypher pipeline query, no orchestration code reads Session /
  AgentInstance / CapabilityGrant. `grep -rn "Session\|AgentInstance\|CapabilityGrant"` across
  `agents/ orchestration/ kernel/` finds only `agents/master/`.

**The substrate is already effectively in-memory.** Running the master with `InMemoryGraphStore`
(which all tests use — and they pass) is functionally identical to Neo4j for anything that matters.
The Neo4j writes are a pure audit trail. **Option (c) is already the de-facto reality.**

**Direction — RECOMMENDED: drop the graph writes from the substrate master; make InMemoryGraphStore
the only backed store for the substrate.** If an audit trail is wanted later, add it as a
separate lightweight concern (Azure Table Storage append log, or a JSON file). Do not keep a
Neo4j dependency in the substrate just for writes nobody reads.

**Trading pack stays on Neo4j regardless.** All Cypher queries and `kernel/graph_cypher.py` /
`kernel/graph_support.py` / `kernel/graph_neo4j.py` are unchanged. AuraDB Free covers years of
daily single-batch runs (~55 nodes/run → 200K node ceiling hit after ~3,600 runs). Self-hosting
Neo4j Community Edition in the existing Azure Container Apps environment is the zero-cost escape
hatch if Aura Free limits bind or the service becomes unavailable.

**AuraDB Free limits — note inconsistency in official sources:** FAQ states 200K nodes / 400K rels;
product page may show 50K / 175K. **Verify in console before planning against either number.**
No automated backups on Free tier; restore is console-only (DL-11). Auto-pauses on inactivity.

**Ruled out.** (b) Separate Neo4j instances — substrate still depends on trading-pack DB choice.
Cosmos DB Gremlin API for the trading pack — free and Azure-native but requires rewriting every
Cypher query as Gremlin; high migration cost for a working system.

**Status.** OPEN — analysis complete; decision and sprint pending. Recommended sprint: remove
`graph` parameter from `MasterAgent.__init__` and `store.py` writes; master becomes graph-free.
One remaining question: (1) verify AuraDB Free actual node limit in console (planning only).

## DL-16 · Alpaca is the primary OHLCV feed; Tiingo retained but demoted  ·  status: DECIDED (2026-06-24)

**Trigger.** A 100-ticker live populate run (`run_local.py --real --universe scripts/universe_sp100.txt`)
returned `0/100` bars with quality `source_unavailable`. Direct probing showed **Tiingo returns
HTTP 429 (Too Many Requests)** — its free tier (~50 req/hr) cannot serve a 100-symbol batch, because
`TiingoDataSource.fetch_ohlcv` issues **one HTTPS call per ticker** (`/tiingo/daily/{ticker}/prices`).
Even a 2-symbol fetch 429'd once throttled for the hour. ADR-0006 had made Tiingo the primary
full-universe feed; that assumption does not survive a real S&P-100-sized run.

**Decision (operator: "we can use Alpaca finance after all").** Make **Alpaca the primary OHLCV
source.** Alpaca's market-data bars endpoint (`/v2/stocks/bars`) accepts **up to ~100 symbols in a
single request**, so one call covers the whole universe and structurally avoids the per-symbol rate
limit. Free `iex` feed returns complete daily bars for liquid large-caps (probe-verified). Existing
`ALPACA_*` credentials already in `.env`; the `.env` header had long noted "Tiingo (primary) +
Alpaca (failover) cover the OHLCV need" — this realises that failover intent, but promotes Alpaca to
primary rather than fallback.

**Build.** New `agents/provider/alpaca_data.py` (`AlpacaDataSource`) implements the price-source side
of the `DataSource` port: batch `fetch_ohlcv` with internal `next_page_token` pagination (network in
`_download*`, `# pragma: no cover`; parsing in `_parse_bars`/`_bar`, 100% covered). `ProviderSettings`
gains `alpaca_data_base_url`, `alpaca_api_key`, `alpaca_api_secret`, `alpaca_data_feed` (default
`iex`), `alpaca_data_timeout`. `market_source_from_settings` now wires Alpaca as `price_source`.

**Ruled out.** *Tiingo→Alpaca failover wrapper* — more resilient and matches the original `.env` note,
but needs a failover-source abstraction + error taxonomy; deferred (operator chose "Alpaca primary"
for the simplest clean populate). *Configurable price source (setting-selected)* — flexible but adds a
knob with no immediate consumer. *Stooq* — already in-repo and free, but single-symbol CSV fetches
share Tiingo's per-symbol shape. Tiingo code is retained (still tested) and can become the failover.

**Follow-ups (later).** (1) Optional Tiingo→Alpaca failover wrapper if Alpaca `iex` coverage proves
thin for any name. (2) Decide `adjustment` policy (raw vs split/dividend-adjusted) for momentum
inputs — currently raw. (3) Supersede note on ADR-0006's "Tiingo primary" line.

## DL-17 · Chunked ingest — paced sub-batches reassembled into one batch  ·  status: DECIDED (2026-06-24)

**Trigger.** With Alpaca solving OHLCV (DL-16), a 100-ticker run was still `DEGRADED`. Measured
cause: `validate_bars` sets `used_fallback = bool(notes)`, and the **optional fields are all
Finnhub, fetched one HTTPS call per ticker** — 100 tickers × 4 fields (fundamentals, news, sectors,
earnings) = **~400 calls fired in a burst**, far over Finnhub free's ~60/min, so all four pillars
fault and taint the batch. (Sentiment/AV is not requested by ingest, so its 25/day cap is moot.)

**Operator framing.** "Put the batch back together: first 25 are asked for and downloaded, marked
as batch B part one, and so on until the last ticker, then we put the batch together and send it off
down the chain. From the point of view of model training the batch is the best breakdown of
information — it needs regular intervals. Test it at various times of day, measure, re-run with other
parameters until we improve." → **continuous improvement: guess, run, measure, re-run.**

**Decision.** Add a chunked ingest path: split the universe into `ingest_chunk_size` sub-batches,
fetch each through the provider's normal `_get_market_data` (its own fault boundary + a per-chunk
`MarketSnapshot` "part"), `sleep(ingest_chunk_delay_seconds)` between chunks so the aggregate
per-minute call rate stays under the free-tier ceiling, then **reassemble one `MarketData` batch over
the full universe** (concatenated bars, merged field dicts, folded quality) and write it as the single
downstream work item the scanner consumes. `ingest_once` dispatches to the chunked path when
`ingest_chunk_size > 0`; default 0 preserves single-shot behaviour. New module
`agents/provider/ingest_chunked.py`; tunables `ingest_chunk_size`, `ingest_chunk_delay_seconds`;
`run_local.py --chunk-size/--chunk-delay`.

**What it fixes vs not.** Chunking clears the **Finnhub rate-limit** degradation (the 4 optional
pillars). It does **not** fix two independent OHLCV-side taints seen on the 100-run: BK returned only
19 bars on Alpaca `iex` (thin coverage → `stale_or_missing_tickers`) and one name had a >4σ daily
move (`daily_move_sigma_anomaly`). Those are separate follow-ups (drop/relax universe, or revisit
`max_daily_move_sigma`), not rate-limit problems.

**Educated first guess (to be tuned empirically).** `chunk_size=12` (48 Finnhub calls/chunk),
`delay=65s` → ~48 calls/min, ~9 chunks ≈ 9 min for 100 names. The right values depend on the live
per-minute cap and time-of-day latency — exactly the measure-then-tune loop the operator described.

**Ruled out.** *Make the optional pillars non-tainting* (taint=False) — would let trades flow on
price-only data, but silently drops the quality signal the analyst is meant to honour; a real policy
question deferred. *Parallel fetch with backoff* — more throughput but harder to keep under a hard
per-minute cap and to reason about deterministically.

**Measurement log (guess → run → measure → re-run).**

| # | Params | Result | Read-off |
| --- | --- | --- | --- |
| 1 | single-shot (100 at once) | notes: `daily_move_sigma_anomaly`, `stale_or_missing_tickers`, **`fundamentals_/news_/sectors_/earnings_degraded`** | Finnhub 429s on the ~400-call burst → all 4 optional pillars fault |
| 2 | `chunk_size=12`, `delay=60s` (~9 min, ~04:05–04:14 AEST) | notes: `daily_move_sigma_anomaly`, `stale_or_missing_tickers` only — **all 4 Finnhub pillars cleared**; news populated (1810 headlines) | ✅ pacing fixes the rate-limit degradation; the 2 remaining taints are OHLCV-side, not rate-limit |
| 3 | 99 tickers (BK dropped), `chunk_size=12`, `delay=60s`, `max_daily_move_sigma=8.0` (~14 min, 04:22–04:36 AEST) | notes: `daily_move_sigma_anomaly`, **`news_degraded`** | ✅ BK drop killed staleness; ✗ sigma still trips and ✗ news re-faulted — see read-offs below |

**Diagnostics behind run 3.** BK on Alpaca `iex`: 18 bars, latest 2026-05-20 (~5 weeks stale);
`sip` feed is 403 on the free plan → BK genuinely unservable, dropped. The sigma outlier is **INTC
+11.7 % intraday on 2026-05-08** (a real earnings move), global z = 6.6 across the 99-name pool.

**Key architectural read-off (run 3).** `sigma=8.0 > 6.6` yet the anomaly *still* fired — because the
chunked path calls `_get_market_data` **per chunk**, so `validate_bars` computes sigma over each
12-ticker chunk, not the full universe. INTC's z *within its chunk* exceeds 8.0, and `_combine_quality`
unions the per-chunk notes. **Per-chunk validation is the wrong altitude: quality must be assessed on
the reassembled batch, once.** Separately, `news_degraded` reappeared (clean in run 2) — chunk=12/
delay=60 is borderline for Finnhub; one chunk 429'd this run. Time-of-day variance, as predicted.

**Next iterations (open).** (a) **Validate the reassembled batch once** (separate fetch from
validate in the chunked path) so sigma/staleness see the full universe — then `sigma=8.0` clears
INTC. (b) **More conservative pacing** (smaller chunk and/or longer delay) to make Finnhub reliably
clean, not borderline. (c) Whether `max_daily_move_sigma=4.0`→`8.0` should be the committed default
(the check should catch corrupt ~30σ prints, not legit 6.6σ earnings moves). (d) Only after a clean
batch do trades actually flow — chunking was necessary but not sufficient.

## DL-18 · Continuous-improvement system — map, measure, tune, gate  ·  status: PROMOTED → ADR-0013 + S90–S95 (2026-06-24)

> Promoted to **[ADR-0013](decisions/0013-continuous-improvement-system.md)** (storage: all on the
> graph) with sprint specs **S90–S95** (phase P16). This entry is the originating map/design.

**Trigger.** DL-17's pacing work was hand-tuned: guess → run → measure → re-run, with the operator
reading flags off a trace and editing env vars. That loop must become a **system**. Operator
direction: *"PROVIDER_INGEST_CHUNK_SIZE / _DELAY should be **configurable, not settable** parameters.
Create the whole continuous-improvement system — map what processes we have, measure them, tweak
parameters, improve."*

**Configurable vs settable — the distinction that drives this.**

- *Settable* (today): a human edits `PROVIDER_INGEST_CHUNK_SIZE=12` in `.env`; one value, no memory
  of what it scored, no comparison, no promotion gate.
- *Configurable* (target): a parameter lives in a **named, versioned ParameterSet** the run loads;
  the system measures the run, attributes the metrics to that set, sweeps alternatives, and
  **promotes** the winner via the existing ACTIVATE channel. Env stays only as the local-dev override.

**What already exists (do not rebuild).**

- **Parameter catalogue** — `kernel/config.py` `tunable()` + `describe()` already expose ~145
  justified, bounded params across 13 agents (name, env var, default, why, ge/le, unit).
- **Measurement prototypes** — forecaster IC/return scorecard (`forecaster/domain/return_scorecard.py`),
  curator filter confusion matrix (`curator/domain/filter_quality.py`), sentiment
  champion–challenger + eval-gate (ADR-0010). Siloed; each proves one slice of the loop.
- **Delivery channel** — master → agent ACTIVATE config injection (entrypoints `_apply_config`).
- **Measurement substrate** — the provenance graph already records every run's lineage.

**The map — processes → key tunables → candidate metrics.**

| Process | Example tunables | Metric to optimise |
| --- | --- | --- |
| provider / **ingest** | `ingest_chunk_size`, `ingest_chunk_delay_seconds`, `max_daily_move_sigma`, `max_staleness_days` | degradation rate (pillars clean / total), total fetch time, returned/requested |
| scanner | `min_average_volume`, `min_relative_strength`, beta/volume gates | survivors/universe, downstream realised-return of survivors |
| analyst | indicator weights (`settings_indicators.py`, 21 knobs), confidence floor | scored/eligible, hit-rate, calibration |
| portfolio_manager | sizing, sector/RR gates | approved/scored, realised PnL per decision |
| execution | broker/slippage params | fill rate, slippage vs expected |
| monitor | exit thresholds, holding window | premature-exit rate, captured vs left-on-table |
| reporter | — (metrics sink) | profit_factor, expectancy |
| forecaster | booster/IC params (existing scorecard) | information coefficient |
| operator LLM | `system_prompt`, model, reasoning effort | eval-set score (ADR-0010 gate) |

**The loop — four layers.**

1. **Catalogue** — aggregate `describe()` across *every* agent settings class into one registry
   (today it runs per-class; nothing unifies them). This is the menu of what is tunable + its bounds.
2. **Measure** — write a per-run `RunMetrics` record keyed by `(process, parameter_set_id, run_id,
   as_of)`; start with ingest (degradation rate, fetch seconds, returned/requested), reuse the
   forecaster/curator scorecards for their slices.
3. **Experiment** — load a named `ParameterSet` instead of ad-hoc env; run champion vs challenger;
   record both sets' metrics against the same as-of so they are comparable.
4. **Gate** — promote a challenger only when its metric ≥ champion with no regression on the
   guardrails (generalises ADR-0010's eval-gate from prompts to *any* parameter set). Promotion
   updates the active set delivered via ACTIVATE; provenance records who/why.

**First concrete target (closes the DL-17 loop).** Make `chunk_size`/`delay`/`max_daily_move_sigma`
a ParameterSet; metric = (Finnhub degradation rate, fetch time) measured across N runs at different
times of day; sweep a small grid within the tunables' bounds; promote the fastest set that holds 0
degradation. This is the manual DL-17 loop, automated and recorded.

**Phased build (proposed sprints).**

- **CI-1 Catalogue** — `describe_all()` over every agent settings class → one registry + a read
  surface (extend the existing tunables view).
- **CI-2 RunMetrics** — graph node + writer; populate from the ingest trace first.
- **CI-3 ParameterSet** — named/versioned set loaded by a run (replaces ad-hoc env for experiments);
  `run_local --parameter-set <id>`.
- **CI-4 Experiment + compare** — run two sets on one as-of; tabulate metric deltas.
- **CI-5 Gate + promote** — no-regression promotion + ACTIVATE delivery; generalise the eval-gate.
- **CI-6 Optimiser** — sweep within bounds (grid first, smarter later); start on the ingest target.

**Open questions.** (a) Where does ParameterSet live — graph node, JSON in repo, or Cosmos (DL-15)?
(b) Metric storage — RunMetrics on the provenance graph vs the metrics/Prometheus plane already wired.
(c) How much overlaps the curator's existing "filter decisions as training source" (DL-09) — likely
CI-2/CI-4 should subsume it rather than duplicate. (d) Relationship to ADR-0010 — the gate should be
one mechanism, not two.

## DL-19 · Etalon-first, and laws as a creative space (not a solution)  ·  status: DIRECTION (2026-06-24)

**Trigger.** After wiring the `tuner`/`librarian` bindings and writing the etalon
(`ops/agent-genesis.md`), the AI leapt toward a bundle *generator*. Operator correction:
**"Too early. Create the ETALON first — the bundle becomes the first etalon v0.1; we need to show
perfection in a finished trading-agent bundle. I want to cover creativity as well. The overall
solution will be owned by agents; the solution will have to be discovered within the space boundaries
which laws define."**

**Two directional locks.**

1. **Etalon-first sequencing.** The generator is the far endgame, **deferred**. The immediate work is
   to bring the trading-agents bundle to *demonstrated perfection* — and that finished bundle **is**
   etalon v0.1. You cannot reproduce a reference that is not yet a reference; a copier would only
   reproduce gaps. Gate to start the generator = etalon v0.1 proven complete.
2. **Laws define a space, not a solution — creativity is first-class.** Laws/charters/gates/NEVERs
   draw the **boundaries of a solution space**; the **solution is owned and creatively discovered by
   the agents** inside it. Constraints say *where the walls are*, never *what to find in the room*. A
   bundle that is only gates is a **cage**, and a cage discovers nothing — every charter must leave
   **deliberate room for discovery**. Test of a good boundary: it rules out the unsafe/incoherent
   without prescribing the answer; if a law forces a single outcome it has become the solution — suspect
   it. This extends LAW-01 from "tune the dials" to "search the lawful space for a better solution."

**Recorded in** `ops/agent-genesis.md` (Sequence note + "Laws define a space, not a solution" section - deferred-generator endgame) and memory [[etalon-bundle-genesis]].

**Implication for the work.** The near-term backlog is *perfecting the bundle*, not building meta-
machinery: finish the laws (green clauses), the pipeline that actually trades (DL-17 line), the
recorded decisions, and — newly — audit each charter for whether it leaves room for creative discovery
rather than over-constraining. The CI-1…CI-6 experimentation machinery and the generator both wait
behind a perfect etalon.

## DL-20 · Discovery is research-driven, feasibility-gated, and deliberated  ·  status: DIRECTION (2026-06-24)

**Trigger.** DL-19 established that laws define a *space* and agents discover the solution within it,
but left the **discovery mechanism** abstract. Operator fills it in: creativity + a *solution field* +
a mandatory research/feasibility front-end, run autonomously by the AI.

**The principle.**

1. **Solution field, not an answer.** A problem can be designed "this way or that", each with
   different implications. The solution is **created on-the-fly**, not retrieved — there is rarely one
   right answer, there is a field of viable ones to be weighed.
2. **Research precedes any offered solution.** Inputs: **legislative / governance**, **typical
   scenarios**, **best industry practice**, and the **constraining factors** of the specific case —
   time, money, physical placement, CPU/compute, other resources. You cannot reason about a solution
   without first finding the facts.
3. **Feasibility gates** — the questions any sane engineer asks *before committing*, answerable only by
   research:
   - **FEAS-POSSIBLE** — is the solution possible at all?
   - **FEAS-READY** — are we scientifically / technically ready to solve what is being asked? (is it
     tractable with current knowledge and tools?)
   - **FEAS-BUDGET** — is it possible within the money / time / compute / physical-resource envelope?
   A red feasibility gate stops the build before it starts — and is itself a *finding*, recorded.
4. **Creative, deliberated research.** Develop **several candidate solutions** and **argue them** — a
   **group of three agents** deliberating (generate → critique → converge), not a single guess. The
   exact council roles are themselves a solution-field, left open (do not prescribe — DL-19).
5. **Autonomy — on the AI's side of the screen.** The operator cannot help with technical detail and
   should not have to. The AI runs the research and the deliberation and brings back a **reasoned
   recommendation with its trade-offs and feasibility verdict** — the decision, not the derivation
   (LAW-04 legibility: surface the choice, hide the weeds unless asked).

**Relationship to existing parts.** This is the front-end that precedes `tunable()` tuning
(Experimentation tunes *within* a chosen design; this *chooses the design*). It generalises
champion–challenger from parameters to whole solutions. It reuses the platform's `researcher` agent
seed (P7) but is larger: a research/feasibility/solution-design discipline.

**Identified bundle (charter pending — record now, build while perfecting the etalon).**
A **Research & Solution-Design** bundle: a deliberative (≈tri-agent) council that, given a problem,
gathers facts (law/scenarios/practice/constraints), runs the feasibility gates, develops and argues
candidate solutions, and returns a recommendation. Not built now (etalon-first, DL-19); named so the
boundary is on record.

## DL-21 · DSPy steers the deliberation — compile the role prompts, don't hand-write them  ·  status: DIRECTION (2026-06-24)

**Trigger.** Ran the same debate ("Buy AAPL", momentum +0.6 / RSI 55 / earnings in 4 days) twice on
live OpenAI. The **conclusion was stable** (both OVERTURN — the decision is genuinely weak) but the
**conversation wandered**: different arguments, framings, and kill-shots each run. The role prompts
(`DEFENDER_SYSTEM` / `CHALLENGER_SYSTEM` / `JUDGE_SYSTEM`) are hand-written statics, so the model
improvises — quality and steering are uncontrolled. On a *harder* decision that variance would flip
verdicts. Operator: **"DSPy is needed here to steer the conversation."**

**Direction.** The three role prompts are **not hand-tuned strings; they are DSPy-compiled predictors**
(ADR-0010, adopted). DSPy optimizes each role's prompt + few-shot demonstrations **against a
deliberation eval**, so the debate is consistently useful: the **Challenger** reliably surfaces
*material* flaws (not sycophancy), the **Judge** verdict **calibrates to outcomes**. The conversation
is steered by the **metric**, not by prose.

**The eval ("a better debate" = ?).** The one the Deliberation charter already names: **do upheld
decisions out-perform overturned ones?** Plus, does the Challenger find flaws a reviewer agrees are
material? Champion–challenger over compiled role prompts, gated by ADR-0010.

**Sequencing.** This is the **P12/P13 DSPy harness applied to its first concrete target**. Etalon-first
(DL-19) keeps the harness queued behind a perfect bundle, but deliberation is a high-value, well-
bounded place for DSPy to land — and it needs a labelled eval set (decisions with known outcomes),
which the pipeline must first *produce* (the real-trade blocker). So: real trades → outcome-labelled
decisions → DSPy-compiled debate roles. The Deliberation charter OPS-TUNE now names DSPy explicitly.

## DL-22 · The LLM assumes guardrails we don't have — DSPy must teach actual coverage  ·  status: DIRECTION (2026-06-24)

**Trigger.** Asked the deliberation model (gpt-5.4) to interpret 86 decision parameters *cold* (only
`name = default`, our `why` withheld). It read ~90% correctly on general finance — but the errors were
revealing (full critique: `docs/research/quant-methods/llm-interpretation-deltas.md`).

**The three delta classes.** (1) *Implementation misreads* — e.g. it read `max_daily_move_sigma` as a
per-stock vol filter; it is actually a **pooled cross-sectional z-score** data gate (the DL-17 bug).
(2) *Dangerous assumptions* — it read `max_sector_pct=0.30` as "limits concentration from correlated
holdings", which is the textbook intent **but false for us**: we have a sector cap, **not a
name-correlation penalty**, and the pipeline just opened 4 semis. A Defender would falsely claim
concentration is controlled; a Challenger would fail to attack it. (3) *Honest UNSURE* on the genuinely
obscure (Nadaraya-Watson, Alpha158) — low risk.

**The insight (extends DL-21).** The model does **not** need to be taught finance — it needs to be
taught **this system's actual behaviour and its limits**. DSPy's job for the deliberation roles is less
"make it smarter" and more **"stop it assuming we are smarter than we are."** Concretely, the compiled
role context must carry: (a) per-parameter implementation notes where our code ≠ textbook (the
withheld `why` fields), and (b) the **coverage gaps** (quant-methods Part 2) as explicit *"the system
does NOT do X"* facts — otherwise a fluent debate is *falsely reassuring*, which is worse than none.
The eval (do upheld decisions outperform?) still gates; understanding is necessary, not sufficient.

## DL-23 · Manufacture the eval set — don't wait for outcomes  ·  status: DIRECTION (2026-06-24)

**Trigger.** "DSPy needs outcome-labelled decisions we don't have yet" was framed as a wall (the live
trades haven't resolved). Operator: *don't give up — be creative.*

**The reframe.** Eval data need not come from the *future*. Two sources are available **now**:

- **Path A — backtest replay (history has the outcomes).** The pipeline already runs `as_of`-dated; run
  it on *historical* dates → the forward return is **already known** → instant, large, outcome-labelled
  decision set. This is not just DSPy's eval — it is the eval set for the **whole** continuous-improvement
  loop (RunMetrics, forecaster IC, the debate), and backtesting the bundle is part of *perfecting* it.
- **Path B — the known-gap rubric (our own docs are the answer key).** quant-methods Part 2 + EXP-001
  already wrote down the failure modes the debate *should* catch. Score any debate deterministically:
  *did the Challenger raise known flaw X?* Construct **adversarial decisions** where the right verdict is
  known *by construction*. Zero trade outcomes needed.

**Proven (EXP-002).** Same "Buy NVDA" decision, debated blind vs **grounded** with EXP-001's context: the
blind Challenger missed the correlated-semiconductor concentration; the grounded one caught it precisely.
**The caught-vs-missed delta is a binary training signal, generated today.** Path B works.

**Bootstrapping ladder (each stronger; start now, don't wait):** Path B (gap-rubric / adversarial,
*immediate*) → Path A (backtest, *ground-truth profit calibration*) → live outcomes (*gold standard*, as
the 5 positions resolve). DSPy's prerequisite is unblocked at step 1.

**Bonus + follow-up.** Path A unblocks the *entire* loop, not just DSPy — high leverage beyond this goal.
Follow-up bug (EXP-002): the Judge sometimes returns unparseable JSON → defaults to `revise`; harden the
judge output contract (tool-use / stricter parse / retry).

## DL-24 · DSPy's first job is a model-drift firewall — a model change is a *gated* change  ·  status: DIRECTION (2026-06-24)

**Trigger.** gpt-5.5 is the flagship — capable but expensive; we will likely downgrade/side-grade the
model later (cost, or a new provider). Operator foresight: the danger isn't the swap, it's that the swap
makes *"reports come out slightly different, deep in the code"* — **silently**. *"If we can foresee
something at design time we need to cater for it."*

**Reframe of DSPy's value (extends ADR-0010, DL-21/22).** DSPy is **not primarily a quality booster**
for the deliberation — EXP-003 showed a strong model already catches textbook flaws. Its **first job
here is portability / regression protection across model change.** DSPy compiles the role prompts
**per-model** (ADR-0010's "per-(task×model) compiled artifact"), so swapping the model swaps to *its*
compiled prompts, and the **eval (EXP-003 harness) proves the outputs did not regress.**

**Cater for it at design time (the catering, not just the worry):**

1. **The model is a GATED parameter, never silent.** Changing `OPENAI_MODEL` / `operator.model` is an
   *experiment*: run the eval harness on the new model, compare to the champion baseline; a regression
   (pass-rate down, or verdicts flipped on the golden set) **blocks the swap** / escalates to the
   operator gate. No silent drift.
2. **Per-model compiled artifacts.** Each model gets its own compiled role prompts; the `model` field
   selects the artifact, so outputs stay consistent because the prompt is re-fit to the model.
3. **A golden verdict regression set.** A frozen set of decisions whose verdicts must stay stable across
   model swaps — the EXP-003 harness is the substrate; freeze a baseline once the Class-1 cases +
   sharper scorer (DL-22/EXP-003) land.

**Status.** DSPy + the per-model gate are still gated on the harness maturing (Class-1 cases, LLM-judge
scorer) and eval data — but the **design now caters for it**: a model change *cannot* silently drift the
deliberation's outputs, because it must pass the eval. Recorded in the Deliberation charter (model = a
gated parameter; OPS-NEV: no swap without the eval gate). This widens ADR-0010 from "guard prompt drift"
to **"guard model-swap drift."**

---

## DL-25 · Translate the firewall's findings into code — close the name-correlation gap  ·  status: DECIDED (2026-06-25)

**Trigger.** The deliberation firewall (EXP-004..006) was built on DL-23's premise: *our documented gaps
are the answer key.* So the Class-1 cases are a **catalogue of real holes in our trading logic** — not
just test fixtures. The operator's directive: *"bake experiment results into code; translate our findings
into code."* A finding the firewall keeps surfacing — and that gpt-5.4 regressed on, and that the live
book exposed (it opened 4 correlated semis) — is **name-correlation concentration**.

**The gap (made concrete).** The PM had a `max_sector_pct` *dollar* cap (30 %). But five small correlated
names at 5 % each clear a 30 % cap while being **one bet**. The dollar cap bounds weight, not *count* —
there was no name-correlation penalty. (This is the `name-correlation` Class-1 case verbatim.)

**Decision.** Add **PM-NEV-06**: a per-sector **name-count** cap (`max_names_per_sector`, default 3, 0
disables; already-held names count). A new `SectorBook` (`domain/concentration.py`) owns both the dollar
and the count gate. The count cap is the name-correlation penalty in **deterministic, interpretable**
form — consistent with the etalon's "facts + interpretable quant params" style.

**Road not taken.** A **return-correlation matrix** (pairwise correlation from OHLCV, reject a candidate
too correlated with the book) is more powerful but heavier — needs price history at the PM and a
correlation computation, and it is *opaque* (a number, not a reason). Deferred: the count cap is the
honest first cut; a correlation penalty is a future *tunable* the experimentation process can A/B against
it. Also **not** fixed here: the cap is silent when `market.sectors` is empty (a provider data-completeness
gap) — logged as a separate follow-up, not a risk-logic change.

**Why this matters.** It is the first loop closed end-to-end: *firewall surfaces a gap → recorded as a
Class-1 case → translated into a law clause + code + cited test.* The machinery doesn't just measure
quality; it now **feeds fixes back into the bundle.** This is how the bundle moves from *trades cleanly*
to *trades wisely* (DL-19). The remaining Class-1 findings (calendar-day staleness DL-10; fixed-fraction
sizing; Alpha158 weight=0; LightGBM shadow) are the queued backlog of the same loop.

---

## DL-26 · The cage test is role-relative; cages aren't the bundle's problem — implicit discovery is  ·  status: DECIDED (2026-06-25)

**Trigger.** Tackling DL-19 lock #2 ("laws define a space, not a solution") via the **no-cages audit**
(`docs/laws/cage-audit.md`) — surveying all ~67 prohibitions across the 13 agents against the cage test.

**Finding 1 — the test is role-relative (a sharpening of DL-19).** The genesis test ("a law that forces a
single outcome is a cage") is **incomplete as stated**: removing discovery is only a *cage* where discovery
is the agent's *job*. A **faithful executor** (provider fetches faithfully, execution submits the intent
exactly, monitor applies stops) is *meant* to be deterministic — its lack of a discovery surface is correct
scoping, not over-constraint. So the test must first classify the agent: **discoverer** (scanner, analyst,
forecaster, researcher, curator, operator) vs **faithful-executor / integrity-keeper** (provider, execution,
monitor, reporter, supervisor, master; PM mechanics). Apply "is this a cage?" only to discoverers.

**Finding 2 — no prohibition is a cage.** Every NEV is a role boundary or a safety/integrity rule; none
prescribes *what to find*. The bundle's constraint surface is healthy — positive evidence for etalon v0.1.

**Finding 3 — the real DL-19 gap is positive, not corrective.** Discovery surfaces are **implicit**. The
laws declare the walls (NEV), the capabilities (CAP), and the dials (PARAM/`tunable`) — but **no agent
names the space it owns and may creatively search.** The room exists; it is undeclared, so the etalon
can't show, per agent, *"what is this agent free to discover?"* Two sequenced follow-ups: (a) **DONE at the
legibility layer** — the **discovery-surface register** (`docs/laws/discovery-surfaces.md`) names every
discoverer's space (Owns / Walls / Search / admitting gate); promoting a per-charter "Discovery surface"
section into the LOCKED `_TEMPLATE.md` stays deferred to its own law cycle; (b) give **lawful-space search**
a mechanism (DL-19's extension of LAW-01 beyond dial-tuning to re-composition) — gated behind the deferred
CI-6 optimiser + the DL-20 discovery discipline.

**Decision.** The "No cages" success factor is **satisfied** (audited; none found). DL-19's remaining work
is to make the rooms explicit, not to knock down walls. Also reconciled a drift the audit surfaced: PM
`laws.md` footer said "v0, not yet locked" while it is LOCKED v1 (S70) — fixed (DRIFT-010).

---

## DL-27 · Pipeline observatory — a human-legible *checker that prints* for the trade flow  ·  status: DECIDED (2026-06-25)

**Trigger.** Operator wants a **visibility utility**: see what each agent receives (from whom, what
triggered it) and produces, across the whole pipeline; lock **what must be there**; check **floor/ceiling**
on the values. *"A print statement for a human to see something is not right."*

**Insight.** This is the **deliberation firewall pattern (golden baseline + floor/ceiling) applied to the
data pipeline.** It has three separable layers: (1) the **trace/print** (per-stage I/O), (2) the
**structural lock** — what *must* be present (partly the Pydantic contracts already), (3) the **value
floor/ceiling** invariants (the new part). The risk: a print-everything firehose becomes noise a human
stops reading — so build a **checker that prints** (flags only breaches), not a printer that occasionally
checks.

**Decision (v1 — graph post-hoc; chosen over live bus-tap and gate-first).**

- **Substrate** `orchestration/observatory.py`: `Check` (required/floor/ceiling/oneof), `StageView`,
  `breaches`, `render`. Domain-agnostic; evaluates + renders only.
- **Pack** `orchestration/packs/trading_observatory.py`: per-stage extractors (provider→pm) + the trading
  invariants (`returned ≥ 1`, `return_ratio ≥ 0.9`, `universe/evaluated/scored/evaluated ≥ 1`) — the "what
  must be there" + floor/ceiling locks. Reuses `batch_trace.walk_chain`; reads the graph (DL-08 — the data
  is already all there).
- **Passive WARN**, never blocks, in v1. The committed invariant set *is* the baseline.
- **Platform/pack wall (ADR-0012):** the mechanism is substrate; the specific invariants are the trading
  pack. CLI: `scripts/observatory.py --run-id <id>`.

**Road not taken.** *Live bus-tap* (richer "watch it move" feel; needs a kernel bus-observer hook) —
later. *Invariant-as-hard-gate* (a "pipeline firewall" sibling to `deliberation_gate`, WARN→FAIL) — later,
once baselines settle. *Per-field schema re-validation* — already the contracts' job; the observatory
surfaces, doesn't duplicate.

**Next.** Extend to execution/monitor/reporter; freeze a golden run + diff; then promote WARN→FAIL as the
gate. Same arc the deliberation took: print → baseline → gate.

**Shipped + validated (2026-06-25).** Full `provider→reporter` spine (0.34.02); `run_local.py --observe`
runs a test and monitors it in one command (0.34.03). **Validated live against the free Aura (`c3ce91d0`)
with real Tiingo data** — a 3-ticker run pulled 41 bars/name, opened `AAPL qty=34 est=$293.32`, reported
`OBSERVATORY OK`. Usage doc: `docs/observability.md` §2a. Remaining: golden-run diff + the WARN→FAIL gate.

---

## DL-28 · Layer-3 acceptance gate — the observatory promoted to PASS/FAIL with conservation  ·  status: DECIDED (2026-06-25)

**Trigger.** The law ledger's **Layer-3** row — *"one full paper-trading day on real S&P 500 data,
persisted, with each agent's **job + boundaries asserted**"* — is the ledger's own *definition of "the
system works,"* and it is ⬜. The observatory (DL-27) already proves "each agent's **job**" (per-stage
outputs + invariants) on a real run; it is the instrument for Layer 3. The missing half is "**boundaries
asserted**" and a hard PASS/FAIL.

**Decision.** Promote the observatory to an acceptance **verdict** (the DL-27 WARN→FAIL gate), and supply
the missing half as **cross-stage conservation**: each agent's output count is bounded by its input — *no
fabrication, no overreach*. `scanner.survived ≤ provider.returned` · `analyst.scored ≤ scanner.survived` ·
`pm.approved ≤ analyst.scored` · `execution.submitted ≤ pm.approved` (**EXEC-NEV-01** "never decides what
to trade"). Substrate `observatory.accept(stages, cross_checks) → AcceptanceResult{passed, breaches}`
(per-stage + cross-stage); pack `packs/trading_acceptance.py` (the conservation invariants + `accept_run` +
`render_acceptance`); `scripts/accept.py` exits non-zero on FAIL — a real gate.

**Two flavors (same as the firewall).** A deterministic **CI guard** (a full cascade must PASS — proves the
wiring + boundaries every commit) + the **live acceptance run** (real S&P data → Aura, recorded as
evidence). The **Layer-3 ledger row goes 🟩 when both exist**.

**Road not taken.** A *full golden-run diff* (freeze every value, exact-match) — deferred; conservation +
floor/ceiling is the high-signal first cut (catches fabrication/overreach without brittle exact-match that
breaks on every legitimate data change).

**Next.** Run the live acceptance on a real S&P-100/500 universe against Aura; record it; turn the Layer-3
row 🟩 (or 🟨 if partial). Then the golden-run diff for value-level regression.

**Live run (2026-06-25) — gate works; found a real bug.** `accept.py` ran **live against the free Aura** and
returned `ACCEPTANCE PASS` on a real 3-ticker run — the gate is proven end-to-end on real infra. The
**full S&P-100 run surfaced [DRIFT-011](../laws/drift-register.md)**: a same-day re-ingest collides on the
immutable `snapshot` property in Neo4j (the in-memory store hid it) — exactly the integration bug
100%-coverage unit tests miss, and *the reason Layer 3 exists*. Layer-3 row → 🟨 (gate live-verified; 🟩
pending the DRIFT-011 fix + one clean full-universe run).

**Re-run after the DRIFT-011 fix (0.35.01).** The full **S&P-100 → Aura run now completes** (99/99 × 41
real bars, no collision) — DRIFT-011 **CORRECTED, proven live**. The acceptance gate still **FAILed**, now
on *data quality* ([DRIFT-012](../laws/drift-register.md)): clean OHLCV but `used_fallback=True` from a
`daily_move_sigma_anomaly` (too-tight default sigma vs a real big-mover) **and** optional-field faults
(`fundamentals/news/sectors/earnings_degraded` — Finnhub rate-limited at 99 per-ticker calls) → the analyst
rejected all 5 candidates → zero trades. The gate did its job again: it caught **over-taint** — optional
*enrichment* failure blocks trading on otherwise-good OHLCV. The 🟩 is now one over-taint fix (optional
faults record a note but don't set `used_fallback`, à la DRIFT-006's `taint=False`) + sigma review away.

**🟩 Layer-3 GREEN — "the system works" (0.35.02, 2026-06-25).** After the [DRIFT-012](../laws/drift-register.md)
fix (optional faults never taint; sigma 4.0→8.0), the **clean full S&P-100 → Aura run PASSES**:
provider→reporter over all 99 names × 41 real bars, **5 positions opened**, `OBSERVATORY OK` + **`ACCEPTANCE
PASS`**. Three live-only bugs the 100%-coverage in-memory suite hid (DRIFT-011 keying, DRIFT-012 over-taint
×2) fell out of *one* acceptance push — the thesis of Layer 3, vindicated. **Caveat (not blocking,
[DRIFT-013](../laws/drift-register.md)):** the 5 names are correlated and PM-NEV-06 was silently inactive
(empty `sectors` from a Finnhub rate-limit) — the concentration guard is data-dependent. Trades cleanly,
not yet wisely. Remaining stretch: the same path at S&P-500 scale.

## DL-29 · Per-ticker OHLCV quality — a partial degradation excludes a ticker, never taints the batch  ·  status: DECIDED (2026-06-25)

**Trigger.** The live S&P-500 acceptance ([DRIFT-014](../laws/drift-register.md)) `FAIL`ed where S&P-100
passed: Alpaca pulled **503/503** OHLCV (the data layer scales), but the analyst `scored=0`. Root cause —
`daily_move_sigma_anomaly` is a **pooled cross-sectional** check whose taint is **batch-level**: one name's
>8σ intraday move among 503 set `used_fallback=True`, and the analyst's `ANLZ-FAIL-02` gate bails the
*whole* batch. As N→503 the probability of ≥1 outlier → 1, so the batch is ~always "degraded" → zero trades.
The per-batch quality model doesn't scale.

**Decision.** `used_fallback` means *"the whole delivery is untrustworthy"* — a per-ticker problem must not
trip it. So the outlier is **attributed to its own ticker and excluded** (`validate_bars` drops its bars;
new `DataQualityTrace.anomalous_tickers` field records it), exactly parallel to `stale_tickers`. The clean
remainder is delivered and `used_fallback` is set **only** by a genuine whole-batch failure — a tainting
note (validity/staleness) or `returned == 0` (nothing survived). The analyst then scores the survivors.

**What did NOT change (deliberate).** The **detector stays pooled cross-sectional** — a >Nσ move *vs the
whole batch* is the documented data-integrity/event gate (`quant-methods.md`; a Class-1 case the LLMs
misread as a per-stock vol filter). Only the **consequence** changed (batch note → per-ticker exclusion).
Mechanically, a pooled outlier among *k* near-identical clean returns has z = √k, so the gate still fires
for any k ≥ ⌈Nσ²⌉ — detection power preserved, blast radius reduced to the offending name.

**Observability (the DRIFT-013 lesson).** The exclusion is **never silent**: the observatory prints
`anomalous <tickers>  (>sigma excluded, DRIFT-014)` and the batch reads `quality ok`, so a reader sees *what*
was dropped and that the delivery was *not* whole-batch degraded.

**Road not taken.** (1) A **per-ticker time-series** detector (judge each name against its *own* return
history) — rejected: a single unadjusted-split glitch inflates that ticker's *own* σ and **masks itself**;
the pooled comparison is strictly better at catching glitches, which is the point. (2) **Relaxing σ further**
or dropping the check — rejected: that blinds a real integrity gate; the bug was the *taint scope*, not the
threshold. (3) Excluding only the **anomalous bars** but keeping the ticker — rejected: a glitchy name's
remaining bars are suspect too; excluding the whole ticker (like stale) is the conservative, consistent move.

**Proven.** Unit (`test_domain.py::test_integrity_excludes_anomalous_ticker_keeps_clean_remainder`) +
observatory (`test_anomalous_ticker_is_excluded_and_shown_not_degraded`); `make ci` green, 100% coverage,
0.37.01.

**PROVEN LIVE (2026-06-26) — Layer-3 🟩 at the full S&P-500.** A live S&P-500 → Aura acceptance run returned
**`ACCEPTANCE PASS`**: the provider flagged `anomalous SMCI  (>sigma excluded, DRIFT-014)` and the batch
stayed `quality ok  returned=502/503` — the single outlier excluded, the clean remainder delivered and
scored (scanner 503→5, analyst HPE/MRVL, **2 positions opened**). The same path that `FAIL`ed pre-fix now
passes at the literal S&P-500. The run also **validated the OHLCV-only fast mode**: requesting only the
`ohlcv` field skipped the ~2000 Finnhub enrichment calls (`collect_optional_fields` gates each pillar by
`field in fields`), so the whole cascade took **9.4s** vs the ~33 min a fully-enriched single-shot would
spend rate-limited. The only WARN was the expected DRIFT-013 sector-coverage advisory (enrichment skipped).

**Toggle shipped (0.38.00).** The fast mode is now first-class, not a monkeypatch: `provider.ingest_ohlcv_only`
(`PROVIDER_INGEST_OHLCV_ONLY`) + a `--ohlcv-only` flag on `run_local.py`. `_ingest_fields(settings)` returns
`("ohlcv",)` when set (else `MARKET_FIELDS`), threaded through both the single-shot and chunked ingest paths;
`collect_optional_fields` already gates each pillar by `field in fields`, so no enrichment call is made. The
acceptance gate needs nothing more — sectors come from the warmed cache, the rest is advisory.

## DL-30 · Activate the forecaster as an orchestrated advisory side branch (RPC, never gates)  ·  status: DECIDED (2026-06-26)

**Trigger.** The forecaster is a *fully built* agent (FinBERT sentiment + LightGBM return models,
scorecards, graph writes) that **nothing ever called** — it bootstrapped and `idle_loop()`d. The 5
control-plane agents (forecaster/operator/supervisor/curator/researcher) are the last stubs; the forecaster
is the natural first because it slots into the proven trading path as the locked champion–challenger's
FinBERT advisory leg.

**Decision.** Activate it as an **orchestrator-triggered cascade stage**, not a change to the analyst and
not a graph-pull self-trigger. After the analyst writes its `RecommendationSet`, a new `forecaster` stage in
`cascade_once` calls the forecaster over the bus (`forecast` + `forecast_return`) for each recommendation;
the forecaster persists a `ShadowPrediction` per leg and the stage writes a `ForecasterRun` marker linked
`AnalystRun-[:FORECAST_BY]->ForecasterRun` for idempotency. The provider and forecaster are bound to a
**shared bus** (the forecaster's `get_market_data` calls reach the provider — it is in the provider's
allowed-callers). `subject_ref` is the **ticker** (so news/price fetch *and* the by-ticker scorecard line
up; the `ADVISES` edge to the `{run_id}:{ticker}` Recommendation node simply doesn't form — acceptable, the
scorecard matches by ticker). Predictions are `shadow=True` and the stage is a **side branch**: it never
touches the conservation/PM/execution path. Version 0.39.00, `make ci` green (1143 tests, 100%).

**Why this shape.** It respects `FORE-TRG-01/02` (RPC-triggered, never self-triggers — the orchestrator is
the caller), keeps the **LOCKED analyst** untouched, and matches the locked champion–challenger direction:
the forecaster lays down a shadow track record per run that the already-built scorecard/comparison evaluates
offline. The immediate job is to *produce and persist* shadow predictions, not to have the analyst consume
them — so an orchestrated side stage is exactly right.

**Road not taken.** (1) The analyst calls the forecaster synchronously — rejected: more invasive, touches
locked laws, couples the trade decision to an advisory agent. (2) A forecaster graph-pull `work_loop` — it
*looks* like the provider→reporter pattern but **violates FORE-TRG-02** (self-trigger). (3) Linking by the
`{run_id}:{ticker}` Recommendation key — rejected because the forecaster also uses `subject_ref` as the
news/price ticker; ticker wins (the scorecard is by-ticker).

**Finding (cross-cutting, not faked).** There is **no distributed RPC-serve transport** in the kernel —
only `idle_loop` (sleep) and `work_loop` (graph-pull, which self-triggers). So an RPC agent's *standalone
container* cannot truly "serve" yet; the forecaster is activated **in the in-process cascade demonstrator**,
not as a live container service. This gap blocks the full-fleet activation of **all 5 RPC control-plane
agents** and is the real prerequisite for them — a `serve_loop`/bus-consume primitive (Service Bus
queue → dispatch to bound handlers). Logged as the next infra unblock for the control-plane.

**Deferred (small, noted).** An observatory advisory `[forecaster]` line (shadow-prediction count per run);
deferred to avoid entangling the trade-spine conservation view — a clean follow-up.

## Discussion agenda — opened 2026-06-26 (4 topics; status: OPEN / in discussion)

Captured per LAW-06 so they are not lost; each resolves into its own DL entry or ADR.

1. **Control flow — whole process vs. financial decision-making.** Is the trading control flow
   (orchestration *and* the buy/sell/size/reject decision logic) fully pre-determined at code time, or
   does an LLM make a *runtime* decision that mutates the graph / changes the flow? If it is fully
   deterministic, what justifies the agent/graph machinery over a hardcoded function — for the *trading
   pack specifically* (platform dataflow set aside)? **CONCLUDED 2026-06-26 → DL-31.** Verified: the
   trading path is fully deterministic (zero LLM calls in provider→reporter); the 3-analyst deliberation
   exists but is *offline-only* (scripts), not wired into the live decision. The agent/graph machinery is
   justified by isolation / audit / resumability, not flow-dynamism. Direction: put the LLM in the loop as
   an **asymmetric challenger-veto** (DL-31).
2. **Rigor about Laws — review + continuous-improvement cycle.** How do we make the law book
   (~300 gray clauses) rigorous and self-improving, not just a one-time citation pass? Cadence, ownership,
   and the gray→green ledger as a living instrument. Relates to ADR-0013 (continuous improvement) and the
   ledger.
3. **Do LLMs actually understand the parameters we ask them to prioritise/decide on?** When the
   deliberation/operator LLM weighs `max_daily_move_sigma`, `base_min_confidence`, regime floors, etc., does
   it grasp our *implementation* meaning (e.g. sigma is pooled cross-sectional, not per-stock)? How to
   interpret and **test** that understanding. Continues EXP-001 / EXP-003 and
   `docs/research/quant-methods/llm-interpretation-deltas.md`. **Partly folded into DL-31** (define-then-
   justify + score the definitions against the answer key); the broader "test understanding" method stays
   open here.
4. **Insert an LLM into every agent + a pre-defined command set.** Give each agent an LLM and a standard
   command vocabulary (start, show-all-parameters, explain, etc.). Relates to topic 1's "where may an LLM
   make runtime decisions" and to the operator command surface.

## DL-31 · LLM in the loop as an asymmetric challenger-veto, with define-then-justify + scored understanding  ·  status: PROPOSED (2026-06-26)

**Trigger.** Topic-1 discussion. The operator's instinct: the 3-analyst deliberation (defend / challenge /
judge, `kernel/deliberation.py`) is *expert-LLM input that should influence the purchase decision* — and we
should make the LLM **explain what each parameter means and justify its verdict** to earn confidence.

**Finding (rigor).** The trading path is **fully deterministic** — zero LLM calls in
provider→scanner→analyst→PM→execution→monitor→reporter (verified). The deliberation harness is real and
works, but is called **only from scripts** (`deliberate.py` / `deliberation_eval.py` / `deliberation_gate.py`)
— it is **not wired into the cascade or any poll/run path**. So today it is a *design-time / offline* tool;
it does **not** currently let a ticker through or hold one back in a live run. The operator's "in principle"
was exactly right.

**The core principle.** *Asking the LLM to explain ≠ confidence.* EXP-001/EXP-003 +
`docs/research/quant-methods/llm-interpretation-deltas.md` already **proved** the model confidently misreads
our parameters (it calls `max_daily_move_sigma` a per-stock vol filter; it is a **pooled cross-sectional**
gate). A fluent justification can be confidently wrong. **Confidence comes from measurement, not eloquence.**

**Proposal (three parts).**

1. **Wire the deliberation into the loop as an asymmetric challenger-veto.** Run defend/challenge/judge on
   each PM-approved candidate (a new orchestration stage, like the forecaster side branch). The judge may
   **block** a trade (verdict `revise`/`reject`) but may **never originate or resize** one — the
   deterministic core stays authoritative. This is the LLM analogue of `FORE-NEV-02` (advise/veto, never
   gate-up). The transcript + verdict persist as graph nodes (provenance, auditability). A missing/slow
   deliberation must **fail safe** (default = do not block, or block-and-flag — to decide).
2. **Define-then-justify prompt.** Each role must, for every parameter it invokes, first **state its meaning
   in THIS system**, then justify the verdict against those definitions. Edit `DEFENDER_SYSTEM` /
   `CHALLENGER_SYSTEM` / the judge prompt in `kernel/deliberation.py`. Output: a transcript that names and
   defines `base_min_confidence`, the regime floor, `max_daily_move_sigma`, etc., then reasons from them.
3. **Score the definitions against ground truth.** Grade the model's parameter-definitions against the
   answer key (`llm-interpretation-deltas.md`) using the existing scorer (`kernel/deliberation_eval.py` +
   the frozen golden). A regression in *understanding* trips the gate (DL-24: model/prompt are gated
   parameters). This converts "it explained itself, I feel better" into "it defined our N parameters
   correctly, measured, and we block on drift."

**Why this shape.** Transparency (part 2) is for humans/audit; verification (part 3) is for trust; the
asymmetric veto (part 1) is the only safe way to put a non-deterministic judge in a capital path —
reproducibility and testability survive because the LLM can subtract but never add. Parts 2+3 are also the
concrete method for Discussion-topic 3 ("does the LLM understand the parameters, and how do we test it").

**Road not taken.** (a) LLM as **originator/sizer** — rejected: injects hallucination into capital
allocation, breaks reproducibility + the acceptance gate. (b) **Explain-only, no scoring** — rejected: the
project already proved self-explanation is confidently wrong; it is false comfort. (c) Leave deliberation
offline-only — viable as a governance tool, but then it never influences a live decision (the operator's
goal), so it does not satisfy the trigger.

**Open questions to settle before building.** Where in the cascade the veto sits (after PM-approve, before
execution); per-candidate LLM cost/latency (one debate per approved trade) and whether to batch; fail-safe
default on deliberation outage; veto scope (hard block vs. revise-size-down — the latter edges toward
origination, so likely hard-block only); how the `llm-interpretation-deltas.md` answer key is owned and kept
current as parameters evolve.
