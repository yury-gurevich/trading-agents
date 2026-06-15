# Build Plan

The sequenced engineering plan. Product intent is in `docs/PRD.md`; structure is in
`docs/architecture.md`. This document owns "what we build next and how we know it
works." Phases are the spine; capabilities that thread through several phases are
named under **Cross-cutting workstreams**, and the product roadmap (`docs/PRD.md`
§12, Phases A–D) is mapped to these phases under **Product roadmap alignment**.
Refresh the status column at every closeout.

## Principles for building

- **Boundary first, runtime second.** A capability is designed as a contract before
  it is implemented. The contract is the review artifact.
- **One agent at a time.** Implement and validate an agent in isolation, then wire
  it into a flow. Never broaden a change across agents to make one work.
- **In-process before distributed.** Prove a flow on the in-process bus with tests,
  then run it on the distributed bus. The distributed backend changes deployment,
  not logic.
- **Advisory before binding.** ML and any non-deterministic component ships shadow
  first, behind a scorecard, before it can influence a decision.
- **Reuse where clean, rewrite where it pays.** Porting settled domain math (the
  trading rules) is encouraged; the kernel, contracts, per-agent data ownership,
  bus, graph, and dispatcher are written fresh.

## Phases

### P0 — Boundary map · **complete**

Kernel contract descriptors and message envelope; the justified-tunable config
primitive and the central fault channel; the shared `contracts/` vocabulary; all
12 agent contracts and missions; the self-enforcing boundary meta-test; the CI/test
toolchain (including the module-size and coding-agent-header guards).
**Exit:** boundary meta-test green; CI quality gate green. *(met)*

### P1 — Kernel runtime

Implement the bus (`InProcessBus` + a distributed backend), the `AgentBase`
lifecycle, the **Neo4j `GraphStore` adapter** (nodes/edges + the vector index for
RAG), observability emission, and the tool-interface binding generated from a
contract. There is no relational store or migration tool — the graph is
schema-flexible (`docs/decisions/0001-neo4j-primary-store.md`).
**Tests:** kernel unit tests; an in-process round-trip (request → handler →
response) for a trivial echo agent; `GraphStore` adapter tests against a Neo4j test
service; a node/edge write smoke test.
**Exit:** an echo agent answers a typed request over both bus backends; the
`GraphStore` adapter round-trips nodes/edges; coverage ratchet raised to the new
measured floor. **Effort: M.**

### P2 — First vertical slice (`provider → scanner → analyst`)

Implement these three agents end-to-end over the in-process bus, porting the
settled domain logic. Each gets `agent.py`, `domain/`, `store.py`, and tests. The
provider becomes the sole holder of data-API credentials and applies the
**data-integrity gates** (ingest anomaly checks, source lineage) before any agent
sees a fact; scanner and analyst request data rather than fetching it. The analyst
stamps each recommendation with its confidence, horizon, and the regime at decision
time — the seed of the calibration substrate. Provenance nodes and edges are written
as each artifact is created: the provenance graph starts here.
**Tests:** per-agent unit + contract tests; one integration test driving the slice;
data-integrity gate tests; graph-provenance assertions (candidate → recommendation
lineage).
**Exit:** a request produces explained recommendations with full provenance, with
no agent importing another. *(met — Sprint 06; full-slice provenance test green.)* **Effort: L.**

### P3 — Decision loop (`portfolio_manager → execution → monitor → reporter`)

Complete the daily loop in **paper** stage. Portfolio manager sizes and risk-checks;
execution submits idempotently to a paper broker and records fills; monitor opens
positions from fill events and decides exits; reporter stitches the run snapshot and
per-trade narrative. Closed positions and elapsed horizons emit the append-only
**realized-outcome** records the calibration workstream later scores.
**Tests:** sizing and risk-check unit tests; idempotency tests for execution; exit-
rule unit tests; an integration test for a full paper run; narrative-completeness
test (scan → exit).
**Exit:** a full paper trading day runs end-to-end with a stitched narrative and
single-writer data ownership intact. **Effort: L.**

### P4 — Orchestration

Replace any temporary in-test sequencing with the dispatcher and the distributed
bus. A scheduler issues run triggers; agents idle until messaged. Dead-letter and
retry handling lands in the supervisor.
**Tests:** dispatcher routing tests; idle/active behavior (no message → no work);
end-to-end run on the distributed backend.
**Exit:** the daily loop runs on the distributed bus, event-driven, with the
supervisor recording message lineage. **Effort: M.**

### P5 — Operator command layer + supervisor safety

Implement the operator agent (intent grammar, typed schemas, command audit, model-
call ledger, evidence-grounded explanations, confirmation semantics) and the
supervisor's capability matrix and hard-NO surface. Expose the tool interface from
the operator as the bounded external bridge.
**Tests:** intent-mapping tests (correct intent, safe refusal on ambiguity);
capability-gate tests (forbidden caller blocked, hard-NO never enabled); audit/
ledger append-only tests; policy-parity tests (command path == dashboard path).
**Exit:** the allowed command families execute safely with full audit and zero
unsafe bypasses. **Effort: M.**

### P6 — Surfaces

Dashboard read-models over the graph store (pipeline status,
recommendation evidence, approval queue, position lifecycle, scorecards, control-
plane state, incidents, active-incidents pane) and a CLI. Surfaces read; they never
drive an agent except through the operator's bounded commands.
**Tests:** read-model projection tests; explain-on-demand affordance tests.
**Exit:** an operator can run, inspect, approve, and recover entirely from the
dashboard. **Effort: M–L.**

### P7 — Self-management

The researcher proposes bounded, measurable parameter changes into a human-review
queue; nothing is applied without operator approval through the control plane.
**Tests:** evidence-window enforcement; forbidden-combination rejection; proposal
audit; "proposes but never applies" boundary test.
**Exit:** a measured proposal can be reviewed and approved through the operator,
with full provenance. **Effort: M.**

### P8 — Hardening + expansion readiness

Stage promotion/demotion gates (paper → broker-shadow → live-manual →
live-autopilot) made evidence-based and reversible; the market-pack and exchange-
calendar abstractions; a per-pack readiness checklist.
**Exit:** a new market pack can be added without core control-plane changes (G6).
**Effort: L.**

### P9 — Observability stack

Provision Prometheus scraping and Grafana dashboards over the kernel metrics
adapter: system health, per-agent throughput and latency, fault rate by source
module, and the trust indicators over time. Wire the central fault channel into
the fault-rate panels and incidents.
**Tests:** metric-emission tests; dashboard provisioning smoke.
**Exit:** an operator can watch system health and fault trends in Grafana, beside
the product dashboard. **Effort: M.** See `docs/observability.md`.

### P10 — Curator (out-of-band data engineering)

Implement the curator and the training plumbing: a signal catalogue and
producer↔training contract; dataset assembly by **provenance-graph traversal**
(clean, labelled, versioned, with train/validation/test splits); a training trigger
that selects data and runs a chosen target; and a **predictor registry** that gates
advisory → load-bearing promotion with frozen evidence. Strictly out of band — never
gating a trading decision.
**Tests:** dataset assembly + split tests; "never influences a decision" boundary
test; manifest/versioning tests; predictor-registry promotion-audit test.
**Exit:** a versioned dataset can be built from collected data and described to the
operator with full provenance; a target can be trained on command and a predictor
promoted through the registry. **Effort: M–L.**

### P11 — Decision-logic depth (extension)

An extension of the original plan. The vertical slice (P2) and decision loop (P3) proved
the agent boundaries, provenance chain, and end-to-end flow with **deliberately shallow**
deterministic scoring. This phase deepens that decision logic to production quality without
changing any boundary or contract — each item lands inside an existing agent's `domain/`:

- **Analyst** — the full technical-indicator suite (RSI, MACD, Bollinger, ATR, stochastic,
  Williams %R, choppiness, OBV, golden cross, calendar/mean-reversion signals, kernel
  smoother, geometric patterns), fundamental scoring (P/E, ROE, margins, leverage, growth),
  relative strength, and signal-diversity selection; composite weighting with bounded,
  justified tunables. *(Sentiment scoring moved to its own phase — P12 — once it grew into a
  multi-agent champion–challenger design; see `docs/decisions/0002-sentiment-champion-challenger.md`.)*
- **Portfolio manager** — reward/risk-ratio gate and sector-concentration cap; explicit
  portfolio-value computation.
- **Scanner** — beta computation + beta-cap filter; earnings-window exclusion.
- **Reporter** — profit-factor and expectancy metrics.

Each addition is a deterministic function with unit tests, registered tunables, and modules
kept ≤ 200 lines. The detailed, sequenced sprint breakdown is held by the planning agent.
**Tests:** per-function unit tests with known-value fixtures; rejection-path tests for the
new gates. **Exit:** the analyst emits a multi-pillar score with explainable contributions;
the new PM gates reject correctly; CI quality gate stays green. **Effort: L.**

### P12 — Sentiment scoring (champion–challenger)

The analyst's reserved third (sentiment) pillar, built as a **champion–challenger** bake-off rather
than a single scorer. One `SentimentScorer` interface, three implementations, compared on evidence;
full rationale in `docs/decisions/0002-sentiment-champion-challenger.md`.

- **Provider news feed** — Finnhub `/company-news` populates `MarketData.news` (per-ticker headlines);
  field-gated, no contract change. *(Sprint 36, planned.)*
- **Lexicon pillar (champion)** — a deterministic Loughran–McDonald scorer in the analyst's `domain/`
  becomes the **binding** third pillar (`sentiment_weight` 0.20); each per-ticker reading is written
  to the graph so challengers can be aligned to it.
- **Provider-sentiment challenger** — Finnhub `/news-sentiment` as an advisory number, written aligned;
  shadow only.
- **Forecaster agent (FinBERT, advisory)** — the first implementation of the reserved `forecaster`
  contract. FinBERT behind the agent boundary (heavy `torch`/`transformers` dependency isolated as an
  optional group + integration-marked tests), emitting `ShadowPrediction`s with a `model_version`;
  **never gates** a decision.
- **Relationship & scorecard harness** — align `(provider, lexicon, FinBERT)` readings + forward
  returns; correlations, regression + residual, incremental information coefficient; promotion (if any)
  through the **predictor registry (P10)** gate; optional deterministic distillation. **Data
  precondition (this harness sprint only):** forward returns are in hand — the deprecated v1 Postgres
  (test-only, never a runtime dependency) has 5 yr of S&P-500 daily OHLCV usable as a fixture — but
  **news history is empty**, so the three-scorer comparison needs a **live news-accrual runway** (the
  S36 feed, scored + stored forward) before it can run. See ADR-0002.

The binding decision path stays deterministic throughout (only the lexicon gates); the model is
advisory until a scorecard earns it (the "advisory before binding" principle).
**Tests:** per-scorer known-value tests; aligned-reading + scorecard tests; a "FinBERT never gates"
boundary test (the forecaster's never-clause). **Exit:** the analyst emits a deterministic sentiment
pillar; provider + FinBERT challengers run in shadow with a scorecard comparing all three on forward
returns. **Effort: L.**

### P13 — Cross-asset & macro signal graph

Move beyond per-ticker scoring to **relationships**: sector contagion (a peer/sector signal, not just
the single name) and **macro events** (tariffs, sanctions) whose effect is *relationship-dependent and
signed* — the same event helps a shielded domestic competitor and hurts a foreign exporter and a
supply-exposed name. Modeled as Neo4j nodes/edges (`Sector`, `PEER_OF`, `IN_SECTOR`,
`EXPOSED_TO {role, weight}`, `Event -[:AFFECTS {sign, magnitude}]->`) with **deterministic signed
propagation** over the graph; per-document scores (P12) are the inputs that propagate. Turning a
macro headline into a typed `Event` (target + direction) is LLM **extraction** (operator/forecaster),
written append-only. Sector/peer edges are cheap (Finnhub); supplier/exposure edges are the hard,
premium data — start with sector + peers + country exposure and grow.
**Tests:** propagation-math unit tests (cap-weighted sector aggregate; signed event flow);
event-extraction provenance tests. **Exit:** a sector/peer sentiment signal and at least one signed
macro-event signal are computed deterministically over the graph and surfaced with explainable
contributions; never binding until scorecarded. **Effort: L–XL.** *(Contingent on P12 + the data
runway; the highest-ambition phase.)*

## Cross-cutting workstreams

Some capabilities are not single phases but threads woven through many. Naming them
here keeps each a tracked deliverable rather than an implicit assumption; the phase
column says where each is built.

- **Provenance graph (Neo4j, the single store).** Typed nodes for every artifact and
  message, edges for derivation and routing (candidate → recommendation → order →
  fill → outcome); the same store also holds transactional records and RAG vectors
  (ADR-0001). The substrate for explanation, audit, retrieval, and dataset export.
  *Built: `GraphStore` adapter (P1); mirror-writes begin with the first artifacts
  (P2) and extend every phase after; traversal + export consumed by the curator (P10).*
- **Decision evidence & calibration.** Every recommendation carries confidence, a
  horizon, and the regime at decision time; realized outcomes are captured and scored
  into per-confidence-bucket calibration curves; drift becomes a parameter-change
  signal and a stage-promotion gate. *Built: horizon/regime tagging (P2); outcome
  capture (P3); curves + scorecards (P7, P9); gates live stages (P8).*
- **Model-call ledger & command audit.** Every model call and every accepted operator
  command is an append-only, replayable record (prompt/response + model+version,
  parsed intent, validation, outcome). *Built: operator (P5); surfaced (P6); the
  ledger is a curation corpus (P10).*
- **Fault & failure catalog.** Every exception is a provenance-carrying fault on the
  central channel; durable incidents with reproducer linkage form a regression
  corpus. *Built: channel (P0, done); supervisor handling (P4–P5); fault-rate panels
  (P9).*
- **Data integrity.** Ingest anomaly gates, source lineage, and a survivorship-aware
  universe so downstream evidence is never built on bad data. *Built: provider (P2);
  cross-provider canary + lineage panels (P9).*
- **Training-data curation.** A signal catalogue + producer↔training contract, dataset
  assembly by graph traversal, a training trigger, and a predictor registry gating
  advisory → load-bearing promotion. *Built: curator (P10), on the provenance, ledger,
  and calibration substrates.*
- **Configuration & constants governance.** Every processing/forecast constant is a
  justified, bounded tunable in a central, operator-visible catalogue. *Built:
  primitive (P0, done); each agent registers its tunables as it lands; catalogue
  surfaced (P5–P6).*
- **Transport & telemetry planes.** Four separated planes so operational logs never ride
  the trade-message bus: **command bus** (Celery on **RabbitMQ**, vendor-neutral, ADR-0004)
  / **log plane** (Azure-native, ADR-0003) / **Neo4j** system-of-record / **metrics**
  (Prometheus/Grafana). The log plane sits behind a kernel `LogSink` protocol: Event Hubs
  (Kafka endpoint) → Function → Azure Cache for Redis (**tunable retention window**, dialled
  with earned confidence) → dashboard, with W3C-trace correlation (seeded from `run_id`) for
  parallel multi-producer steps; durable audit stays in Neo4j. *Decisions:
  `docs/decisions/0003-telemetry-log-plane-azure.md`, `docs/decisions/0004-rabbitmq-command-broker.md`.
  Built: `LogSink` abstraction + correlation-id schema first; Event Hubs/Redis provisioned
  when parallel-agent operation lands; no Log Analytics/KQL forensic tier (lock-in bound to
  the ephemeral plane).*

## Product roadmap alignment

The product roadmap in `docs/PRD.md` §12 (Phases A–D) and the engineering phases
here are two lenses on one delivery:

| Product phase (PRD §12)   | Built by       |
| ------------------------- | -------------- |
| A — Trust foundation      | P2, P3, P4, P9 |
| B — Quiet command layer   | P5             |
| C — Phone-first control   | P6             |
| D — Market-pack expansion | P8             |

Phase A is the broadest: it spans the vertical slice and its why-no-action surfaces
(P2), the decision loop with trade narrative and broker idempotency (P3), the
fail-loud scheduler (P4), and the observability stack (P9). The remaining build
phases are foundational or cross-cutting rather than product phases: P0–P1 (boundary
map, kernel runtime) are what every phase stands on, P7 is self-management
(PRD §8.4), and P10 is out-of-band data engineering (PRD §4.8).

## Testing & CI parameters

The toolchain:

- **Python 3.13**, dependency + lock management via `uv`.
- **Lint/format:** `ruff` (same rule set and 88-col format), no auto-fix in hooks.
- **Types:** `mypy --strict` with the pydantic plugin, over `kernel contracts
  agents orchestration surfaces`.
- **Boundaries:** `import-linter` (`lint-imports`) — the four contracts in
  `.importlinter`.
- **Tests + coverage:** `pytest` with a branch-coverage **ratchet floor** (set to
  the real measured floor; raised as coverage grows, never lowered).
- **Security:** `pip-audit` and `detect-secrets` against a committed baseline.
- **Module size:** warn at 150 lines, hard-block at 200. Clean start — no
  grandfathered files; `__init__.py` and migration revisions are exempt.
- **Module headers:** every module declares a coding-agent header (`Agent:` /
  `Role:`), enforced by `scripts/check_module_header.py`.
- **Pre-commit** runs the same uv-locked binaries and flags as CI, so local and CI
  verdicts match.

CI jobs: `quality` (lint, format, types, import-linter,
module size), `test` (pytest + coverage floor, with a Neo4j service), `security`
(pip-audit, detect-secrets). There is no `migration` job — the graph store is
schema-flexible (ADR-0001). The staged `promotion_check` job is introduced with the
stage gates in P8.

## Status

| Phase | State |
| --- | --- |
| P0 Boundary map | **complete** |
| P1 Kernel runtime | **complete** (S01/S07 both bus backends, S03 Neo4j GraphStore, S08 observability, S22 MCP tool-binding shipped; RAG vector index deferred build-when-needed; S02 superseded by ADR-0001) |
| P2 First vertical slice | **complete** (S04 provider, S05 scanner, S06 analyst; exit met) |
| P3 Decision loop | **complete** (S09 PM, S10 hardening, S11 execution, S12 monitor, S13 reporter — exit criterion met) |
| P4 Orchestration | **complete** (S14 dispatcher, S15 supervisor lineage + scheduler — exit criterion met) |
| P5 Operator + supervisor | **complete** (S16 operator + LLM ledger, S17 supervisor gate + hard-NO — exit criterion met) |
| P6 Surfaces | **complete** (S18–S21 shipped; exit criterion met — test_p6_exit.py green) |
| P7 Self-management | **complete** (S23 researcher agent shipped; propose+evidence+cli proposals; exit criterion met — test_p7_boundary green) |
| P8 Hardening + expansion | **complete** (S24 stage gate + S25 market pack; G6 exit criterion met — test_p8_exit.py green) |
| P9 Observability stack | **complete** (infra deployed: Azure Monitor Workspace + Managed Grafana; S25 entrypoint + metrics_server + paper_context wiring, S26 MeteredFaultSink through bus + every agent sink; exit criterion met — test_p9_exit.py green) |
| P10 Curator | **complete** (S27 dataset assembly + S28 advisory training trigger + S29 predictor registry/promotion gate — build_dataset/describe_corpus, versioned splits, train_predictor + frozen evidence, promote_predictor evidence-gate + operator approval + PredictorPromotion audit; exit criterion met — test_p10_exit.py green; never-influences-decision invariant proven throughout) |
| P11 Decision-logic depth | **active** (extension; S30–S33 technical engine complete — 15 indicators; S34 provider fundamentals feed + S35 analyst fundamental pillar shipped; relative strength + signal-diversity, PM/scanner/reporter gaps to follow; sentiment split out to P12) |
| P12 Sentiment (champion–challenger) | **planned** (S36 provider news feed handed off; then lexicon pillar / provider + FinBERT challengers / scorecard harness — implements the reserved forecaster agent; ADR-0002) |
| P13 Cross-asset & macro signal graph | **planned** (sector contagion + signed tariff/sanction event propagation over Neo4j; contingent on P12 + a news+returns data runway; ADR-0002) |
