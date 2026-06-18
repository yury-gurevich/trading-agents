# Decisions index — what question each ADR closes forever

**How to use:** before discussing any architecture topic, scan the "Closes" column.
If your question is there, the discussion is already done — read the linked ADR
for the rationale instead of re-deriving it.

| # | Title | Status | Closes | Tags |
| --- | --- | --- | --- | --- |
| [0001](0001-neo4j-primary-store.md) | Neo4j as the single primary store | ✅ Accepted | What database do we use for the graph, provenance, and RAG store? | `neo4j` `storage` |
| [0002](0002-sentiment-champion-challenger.md) | Sentiment as champion–challenger | ✅ Accepted | How do we evaluate and promote ML sentiment models without breaking the deterministic gate? | `sentiment` `finbert` `analyst` `forecaster` `p12` |
| [0003](0003-telemetry-log-plane-azure.md) | Telemetry/log plane on Azure | ✅ Accepted | Where do logs and metrics go? Is the log plane the same channel as the command bus? | `azure` `telemetry` `logs` `metrics` `event-hubs` |
| [0004](0004-rabbitmq-command-broker.md) | RabbitMQ as Celery broker | ⛔ Superseded by 0005 | ~~What broker does Celery use?~~ — irrelevant; Celery itself is transitional. | `celery` `rabbitmq` |
| [0005](0005-inter-agent-communication.md) | Inter-agent comms: Azure Service Bus | ✅ Accepted | How do agents communicate asynchronously? Sync RPC or async pub/sub? What replaces Celery? | `azure` `service-bus` `bus` `celery` `p14` |
| [0006](0006-market-data-feed-strategy.md) | Market-data feed strategy | ✅ Accepted | What feeds do we use for OHLCV, fundamentals, news, and sentiment? What happens when one goes down? | `tiingo` `alpaca` `finnhub` `feeds` `provider` |
| [0007](0007-container-per-agent-master-bootstrap.md) | Container-per-agent + master bootstrap | ✅ Accepted | How do we deploy each agent? Who manages secrets? How do agents get their identity? | `docker` `azure` `container-apps` `master` `key-vault` `p14` |
| [0008](0008-neo4j-hosting-local-docker.md) | Neo4j hosting: local Docker | ✅ Accepted | Where does Neo4j run in dev/staging? Aura cloud vs Desktop vs Docker? | `neo4j` `docker` `hosting` `aura` |
| [0009](0009-azure-native-tech-stack.md) | Azure-native infrastructure standard | ✅ Accepted | What is the approved infrastructure list? Can we add Prometheus, Celery, Postgres, Grafana? | `azure` `infrastructure` `stack` `prometheus` `celery` `postgres` |

## Status legend

- ✅ Accepted — decision stands; do not re-open without a new ADR
- ⛔ Superseded — closed by a later ADR (linked in the file)
- 🔄 Amended — core decision stands; details updated in-file

## Adding a new ADR

1. Next number is `0010`.
2. Copy any existing ADR as a template.
3. Add a row to this table immediately — the `closes` question is the most important field.
4. Link from the relevant law file (`docs/laws/`) if the ADR changes a charter or dependency.
