# Decisions index — what question each ADR closes forever

**How to use:** before discussing any architecture topic, scan the "Closes" column.
If your question is there, the discussion is already done — read the linked ADR
for the rationale instead of re-deriving it.

| # | Title | Status | Closes | Tags |
| --- | --- | --- | --- | --- |
| [0001](0001-neo4j-primary-store.md) | Neo4j as the single primary store | ⛔ Superseded by 0014 | ~~What database do we use for the graph, provenance, and RAG store?~~ | `neo4j` `storage` |
| [0002](0002-sentiment-champion-challenger.md) | Sentiment as champion–challenger | ✅ Accepted | How do we evaluate and promote ML sentiment models without breaking the deterministic gate? | `sentiment` `finbert` `analyst` `forecaster` `p12` |
| [0003](0003-telemetry-log-plane-azure.md) | Telemetry/log plane on Azure | ✅ Accepted | Where do logs and metrics go? Is the log plane the same channel as the command bus? | `azure` `telemetry` `logs` `metrics` `event-hubs` |
| [0004](0004-rabbitmq-command-broker.md) | RabbitMQ as Celery broker | ⛔ Superseded by 0005 | ~~What broker does Celery use?~~ — irrelevant; Celery itself is transitional. | `celery` `rabbitmq` |
| [0005](0005-inter-agent-communication.md) | Inter-agent comms: Azure Service Bus | ✅ Accepted | How do agents communicate asynchronously? Sync RPC or async pub/sub? What replaces Celery? | `azure` `service-bus` `bus` `celery` `p14` |
| [0006](0006-market-data-feed-strategy.md) | Market-data feed strategy | ✅ Accepted | What feeds do we use for OHLCV, fundamentals, news, and sentiment? What happens when one goes down? | `tiingo` `alpaca` `finnhub` `feeds` `provider` |
| [0007](0007-container-per-agent-master-bootstrap.md) | Container-per-agent + master bootstrap | ✅ Accepted | How do we deploy each agent? Who manages secrets? How do agents get their identity? | `docker` `azure` `container-apps` `master` `key-vault` `p14` |
| [0008](0008-neo4j-hosting-local-docker.md) | Neo4j hosting: local Docker | 🔄 Amended | Where does Neo4j run when used as an analysis workbench? | `neo4j` `docker` `hosting` `aura` |
| [0009](0009-azure-native-tech-stack.md) | Azure-native infrastructure standard | ✅ Accepted | What is the approved infrastructure list? Can we add Prometheus, Celery, Postgres, Grafana? | `azure` `infrastructure` `stack` `prometheus` `celery` `postgres` |
| [0010](0010-llm-interaction-quality-gate.md) | LLM interaction quality gate (eval-gated prompts, DSPy) | ✅ Accepted | How do we stop LLM output quality degrading across model/provider/fallback/functionality changes? DSPy, EvoPrompt, or both? | `llm` `prompts` `dspy` `evoprompt` `champion-challenger` `p10` |
| [0011](0011-container-registry-ghcr.md) | Container registry: GitHub Container Registry (GHCR) | ✅ Accepted | Where do we store Docker container images? DockerHub, GHCR, or Azure Container Registry? | `docker` `ghcr` `github` `container-registry` `p15` `ci-cd` |
| [0012](0012-platform-domain-separation.md) | Platform/domain separation: substrate vs trading pack | ✅ Accepted | Is this a trading app or a domain-agnostic platform? Where is the substrate↔pack wall, and is it enforced now or just declared? | `platform` `substrate` `decoupling` `boundaries` `text-defined-business` |
| [0013](0013-continuous-improvement-system.md) | Continuous-improvement system: configurable params, measured runs, gated promotion | ✅ Accepted | How do we stop hand-tuning parameters? How does every process get measured, every tunable optimised against a metric, and improvements promoted without regression — and where does that state live? | `continuous-improvement` `tunable` `parameter-set` `metrics` `champion-challenger` `quality-gate` `p16` |
| [0014](0014-postgresql-system-of-record.md) | PostgreSQL system of record | ✅ Accepted | What is the system of record after DL-43? What is Neo4j for now? | `postgres` `neo4j` `storage` `graphstore` `dl-43` |
| [0015](0015-exit-lifecycle-and-stop-ownership.md) | A position is closed by a fill; the broker enforces the stop | 🔄 Amended 2026-07-24 | What closes a position — a decision or a fill? Who enforces the stop: our daily loop or the broker? What happens when a sell is refused or partially fills? | `exits` `monitor` `execution` `alpaca` `bracket` `oco` `stops` |
| [0016](0016-one-run-one-evidence-both-directions.md) | One run, one evidence set, both directions | ✅ Accepted | Are buy and sell decided together on the same evidence, or by separate mechanisms? How does a sell reach execution? | `exits` `analyst` `portfolio-manager` `execution` `monitor` `decisions` |
| [0017](0017-exit-authority-alpha-proposes-risk-disposes.md) | Exit authority: alpha proposes, risk disposes | ✅ Accepted | When the monitor's mechanical exit and the analyst's thesis disagree on a held position, which decider wins? What happens to target and time exits? | `exits` `analyst` `monitor` `execution` `stops` `risk` |
| [0018](0018-decision-validity-same-session-or-dropped.md) | A decision is valid for one session: fill it or drop it | ✅ Accepted | How long is a trading decision valid? What happens to an order that does not fill in the session it was decided for — does it carry to the next open, or is it dropped? | `execution` `exits` `entries` `orders` `slippage` `stops` `alpaca` |
| [0019](0019-risk-cap-binds-position-size-not-stop-distance.md) | The risk cap binds position size, never stop distance | ✅ Accepted | When a volatility-scaled stop wants more room than the per-position risk cap allows, which gives — the cap or the stop? And how does a high-ATR name get a correct stop without breaching the cap? | `portfolio-manager` `analyst` `risk` `sizing` `stops` `volatility` `atr` |
| [0020](0020-llmcall-is-substrate-not-the-operators.md) | `LLMCall` is substrate, not the operator's | ✅ Accepted | Is the operator the only agent allowed to call an LLM, and does it exclusively own the `LLMCall` audit label? When a second agent needs to reason with a model, does it write `LLMCall` too, or its own label? | `operator` `deliberator` `llm` `audit` `cost` `substrate` |
| [0021](0021-clause-summary-mirrors-the-law.md) | A clause summary mirrors the law, never the test | ✅ Accepted | When a test proves only part of a law clause, may the clause summary in `test-plan.md` be narrowed to describe what the test actually covers? Which document wins when `laws.md` and `test-plan.md` disagree? | `laws` `conventions` `test-plan` `coverage` `honesty` |
| [0022](0022-the-veto-gates-buys-never-exits.md) | The veto gates buys, never exits | 🔄 Amended 2026-08-13 | Does the deliberation veto block execution, and what does it block? How do we tell “the veto has not run yet” from “the veto is not deployed”? | `execution` `deliberation` `risk` `adr` |
| [0023](0023-concentration-is-issuer-and-correlation-not-a-vendor-label.md) | Concentration is measured by issuer and correlation, not by a vendor label | ✅ Accepted | How does the PM account for correlated exposure across its book? The law says a per-sector name count is the correlation penalty — but the labels it counts are vendor industry strings, share classes of one issuer count as two names, and the correlation that actually bites crosses labels entirely. **Measured 2026-08-20:** the law says GICS level 1, the feed returns **30 industry labels**, so `max_names_per_sector=3` is ~3× weaker than intended; GOOG and GOOGL both read `Media` and count as two names for one issuer; the mega-cap AI complex spans **five** labels, admitting 15 correlated names before the cap fires once. Correlation is computable from the **203 bars already on the graph** at zero API cost. 🚨 Needs a **law-amendment cycle** — PM `laws.md` is LOCKED v1 and `PM-NEV-06` both names GICS L1 and claims the count cap *is* the correlation penalty |

## Status legend

- ✅ Accepted — decision stands; do not re-open without a new ADR
- ⛔ Superseded — closed by a later ADR (linked in the file)
- 🔄 Amended — core decision stands; details updated in-file

## Adding a new ADR

1. Next number is `0024`.
2. Copy any existing ADR as a template.
3. Add a row to this table immediately — the `closes` question is the most important field.
4. Link from the relevant law file (`docs/laws/`) if the ADR changes a charter or dependency.
