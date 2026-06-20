# Technology stack

The living registry of every technology in scope — from production decisions to
horizon research. This is the place to record "we looked at this" alongside "we use
this," so the same ground is never re-investigated twice and impact analysis is fast.

**Status legend:**

| Status | Meaning |
| --- | --- |
| **ADOPTED** | In production or directly wired to production code. Governed by an ADR. |
| **TRANSITIONAL** | In use now but explicitly scheduled for replacement. |
| **DEFERRED** | Designed in, not yet built; a sprint or ADR names the unblock condition. |
| **CONSIDERED** | Evaluated; not chosen now; may be revisited when listed conditions change. |
| **REJECTED** | Evaluated and ruled out; an ADR records the reason permanently. |
| **HORIZON** | Not yet evaluated; on the radar for a future bake-off or sprint. |
| **RETIRED** | Was in use; removed; reason recorded. |

---

## Messaging / communication

| Technology | Status | Governs | If swapped, this breaks |
| --- | --- | --- | --- |
| Azure Service Bus | **ADOPTED** | ADR-0005 (distributed bus); ADR-0009 (Azure-native rule) | `kernel/bus_azure.py`, P14 pub/sub bindings, all `bind()` overrides in every agent |
| In-process `MessageBus` | **ADOPTED** | permanent test/dev bus; no ADR (always kept) | all unit + contract + integration tests |
| Celery + Redis | **TRANSITIONAL** | ADR-0004 (superseded by 0005); retires at P14 | `kernel/bus_celery.py`, `pyproject.toml` `runtime` + `dev` groups; `orchestration/bindings.py` |
| RabbitMQ | **REJECTED** | ADR-0004 superseded by ADR-0005 — Azure Service Bus chosen | nothing currently wired |
| Azure Event Hubs | **DEFERRED** | ADR-0003; log + telemetry plane (not command bus) | `EVENTHUBS_CONNECTION_STRING` in `.env` when provisioned |
| MCP (Model Context Protocol) | **ADOPTED** | S22; `surfaces/mcp_server.py`; operator + supervisor tool binding | `surfaces/mcp_server.py`, all `contract.tools` capability bindings |

---

## Container / deployment

| Technology | Status | Governs | If swapped, this breaks |
| --- | --- | --- | --- |
| Azure Container Apps | **ADOPTED** | ADR-0007 (container-per-agent); ADR-0009 (Azure-native rule) | deployment scripts, `AZURE_CA_ENV_NAME` config; **agent code is unaffected** (stateless) |
| Docker + DockerHub | **ADOPTED** | ADR-0007; one image per agent, tailored deps per `[project.optional-dependencies]` | `Dockerfile`, per-agent image build + push pipeline |
| Azure Key Vault | **ADOPTED** | ADR-0007; sole accessor = master agent | master bootstrap handshake; `EHLO/ACTIVATE` protocol; all `secrets` fields in law `CAP` sections |
| Azure Container Registry | **CONSIDERED** | Not chosen; DockerHub used (free tier) | swap: update image pull refs in Container Apps; no code change |

---

## Observability / monitoring

| Technology | Status | Governs | If swapped, this breaks |
| --- | --- | --- | --- |
| Azure Monitor / Log Analytics | **ADOPTED** | ADR-0003; ADR-0009 | `AZURE_MONITOR_CONNECTION_STRING`; `kernel/metrics.py` emit path |
| Azure Managed Prometheus | **ADOPTED** | ADR-0009; `prometheus-client` remote-writes here | `PROMETHEUS_REMOTE_WRITE_URL`; `prometheus-client` lib stays (it's the SDK) |
| Azure Managed Grafana | **ADOPTED** | ADR-0009 | dashboard definitions; currently manual |
| `prometheus-client` (library) | **ADOPTED** | remote-write adapter to Azure; **not** a local scrape target | `kernel/metrics.py` |
| Local Prometheus sidecar | **RETIRED** | Removed ADR-0009 (2026-06-19); configs in `trading-agent-del/` | nothing (was never used in production path) |
| Local Grafana sidecar | **RETIRED** | Removed ADR-0009 (2026-06-19) | nothing |

---

## Data storage

| Technology | Status | Governs | If swapped, this breaks |
| --- | --- | --- | --- |
| Neo4j (local Enterprise Docker) | **ADOPTED** | ADR-0001 (sole primary store); ADR-0008 (local Docker in dev); ADR-0009 (permanent exception to Azure-native rule) | `kernel/graph.py`, all `store.py` files, provenance graph, RAG vector index, fleet registry (ADR-0007), drift + law ledgers read via graph queries |
| Azure Cosmos DB (Gremlin) | **REJECTED** | ADR-0009 — lacks APOC procedures and Graph Data Science library which are load-bearing for planned graph analytics | nothing (never wired) |
| PostgreSQL | **RETIRED** | Was v1 `price_cache`; removed 2026-06-19 — Tiingo + Alpaca cover the OHLCV need (ADR-0006); raw Postgres probe retired | nothing (never wired to v2 agents) |
| Neo4j vector index (native) | **ADOPTED** | ADR-0001; embedded in the graph store — no separate vector DB needed for current RAG scale | `kernel/graph.py` `upsert_vector`, any future RAG query path |
| Pinecone / Weaviate / Qdrant | **HORIZON** | Evaluate if Neo4j native vector index proves insufficient at scale (>10M embeddings or <50ms P99 ANN query) | would introduce a second data boundary; `kernel/graph.py` RAG path refactored |

---

## Market data feeds

| Technology | Status | Governs | If swapped, this breaks |
| --- | --- | --- | --- |
| Tiingo (OHLCV) | **ADOPTED** | ADR-0006 primary full-S&P-500 feed (500 symbols/month, 30+ yrs history); S44 | `agents/provider/tiingo.py`, `market_source_from_settings`, `TIINGO_API_KEY` |
| Alpaca (broker + failover OHLCV) | **ADOPTED** | ADR-0006 broker boundary + secondary feed; S45 | `agents/execution/alpaca.py`, `broker_from_settings`, `ALPACA_API_KEY/SECRET` |
| Finnhub (fundamentals + news + earnings) | **ADOPTED** | ADR-0006; S34/S36/S42 | `agents/provider/fundamentals.py`, `agents/provider/news_source.py`, `FINNHUB_API_KEY` |
| FMP (Financial Modeling Prep) | **ADOPTED** | ADR-0006; validation sub-universe / failover (~87 curated symbols) | `agents/provider/fmp.py`, `FMP_API_KEY` |
| Alpha Vantage | **ADOPTED** | S47; vendor sentiment challenger (PROV opponent to lexicon champion) | `agents/provider/av_sentiment.py`, `ALPHAVANTAGE_API_KEY` |
| FRED (macro data) | **DEFERRED** | DRIFT-003; lawful to request (`PROV-IN-06`), answered DEGRADED until built; no sprint planned | `agents/provider/agent.py` `fields` handling; `FRED_API_KEY` present in `.env` |
| EDGAR / SEC filings | **DEFERRED** | DRIFT-003; same as FRED | same provider agent expansion |
| Stooq | **RETIRED** | Was keyless OHLCV default; anti-bot blocked 2026-06-16 (PoW interstitial); replaced by Tiingo (ADR-0006) | nothing; `StooqDataSource` retained as stub/stub-test fixture only |

---

## ML / AI models

| Technology | Status | Governs | If swapped, this breaks |
| --- | --- | --- | --- |
| LightGBM | **ADOPTED** | S58/S59; price/return shadow signal (`ReturnModel` port); `forecaster` optional dep | `agents/forecaster/lightgbm_adapter.py`; `ReturnModel` port isolates — swapping only changes the adapter |
| FinBERT (HuggingFace) | **ADOPTED** | S49; sentiment shadow scorer (`SentimentModel` port); `forecaster` optional dep (torch + transformers) | `agents/forecaster/finbert_adapter.py` (if exists); `ShadowPrediction` nodes; the `SentimentModel` port isolates |
| DSPy | **ADOPTED** | ADR-0010; prompt optimization behind `PromptOptimizer` port (no code yet — port + first impl is a deferred sprint) | nothing yet; when wired: the `PromptOptimizer` implementation class only; **the golden eval set and metric are tool-agnostic** |
| EvoPrompt | **CONSIDERED** | ADR-0010; proactive evolutionary prompt search; **not yet evaluated hands-on**; deferred to a bake-off vs DSPy on the same golden set | nothing; adoption would add a second `PromptOptimizer` implementation |
| OPRO / GEPA / TextGrad / APE | **CONSIDERED** | ADR-0010 category; same bake-off criterion as EvoPrompt | same as above |
| Loughran–McDonald lexicon | **ADOPTED** | S56; champion sentiment scorer (Python, no external dep) | `agents/analyst/domain/sentiment_rules.py`, vendor .txt files |
| OpenAI function calling / structured output | **HORIZON** | Alternative to DSPy for structured LLM extraction; evaluate when the operator's intent grammar grows beyond what DSPy handles cleanly | nothing; would be behind the `PromptOptimizer` port |
| vLLM / Triton (self-hosted inference) | **HORIZON** | For latency-sensitive or cost-sensitive LLM paths if Anthropic API becomes a bottleneck | `agents/operator/llm.py` + any forecaster LLM path; model port isolates |
| MLflow / Weights & Biases | **HORIZON** | ML experiment tracking for LightGBM + DSPy runs; evaluate when the number of offline training experiments justifies a tracker | `agents/forecaster/` training scripts |
| Feast (feature store) | **HORIZON** | If Alpha158 grows beyond a per-sprint compute and needs a shared, versioned feature registry | `agents/analyst/domain/alpha_features.py` |

---

## LLM providers

| Technology | Status | Governs | If swapped, this breaks |
| --- | --- | --- | --- |
| Anthropic (Claude) | **ADOPTED** | `ANTHROPIC_API_KEY`; operator intent parsing; ADR-0010 governs drift management | `agents/operator/llm.py`; per-(task × model) compiled prompt artifacts when the eval harness is built |
| OpenAI | **HORIZON** | Fallback provider candidate; evaluate in DSPy bake-off | operator LLM path; prompt predictors need recompile per ADR-0010 |
| Google Gemini | **HORIZON** | Same category | same |
| Local / self-hosted | **HORIZON** | Cost or data-sovereignty scenarios | same; vLLM would be the host |

---

## Python runtime / tooling

| Technology | Status | Governs | If changed, this breaks |
| --- | --- | --- | --- |
| Python 3.13 | **ADOPTED** | `requires-python = ">=3.13"` in `pyproject.toml` | nothing lower; pyqlib explicitly 3.13-incompatible (R001 in sprint notes) |
| uv | **ADOPTED** | Package manager + lockfile; `[tool.uv]` in `pyproject.toml` | all `uv run` commands in `Makefile` + CI |
| ruff | **ADOPTED** | Linter + formatter; `[tool.ruff]` in `pyproject.toml` | CI `quality` job; pre-commit hooks |
| mypy (strict) | **ADOPTED** | `[tool.mypy] strict = true`; CI `quality` job | all type annotations; `pydantic.mypy` plugin |
| pytest + pytest-cov | **ADOPTED** | 100 % coverage ratchet; `[tool.pytest.ini_options]` | CI `test` job |
| import-linter | **ADOPTED** | Enforces kernel ← contracts ← agents boundary; `.importlinter` | CI `quality` job; four independence contracts |
| detect-secrets | **ADOPTED** | CI `security` job; `.secrets.baseline` | secret scan step |
| pip-audit | **ADOPTED** | CI `security` job; dependency vulnerability scan | security gate |
| pre-commit | **ADOPTED** | Local gate mirrors CI; hooks in `.pre-commit-config.yaml` | local developer workflow |
| pydantic v2 + pydantic-settings | **ADOPTED** | All contracts and settings; `[tool.pydantic-mypy]` | contracts/, kernel/settings.py, every agent settings.py |
| CodeQL | **ADOPTED** | Conditional in `codeql.yml` (gated on `GHAS_ENABLED`; private repo) | CI `security` job when GHAS is enabled |

---

## Decision dependency map

A quick reference for "if we change X, what also changes?" — use before any ADR
that touches a technology.

```tetx
Neo4j (ADR-0001)
  └── kernel/graph.py (adapter)
  └── all agents/*/store.py (owned labels)
  └── provenance graph (every node/edge in the system)
  └── RAG vector index (native; no separate vector DB)
  └── fleet registry (ADR-0007; master agent)
  └── drift register + ledger (operational state)

Azure Service Bus (ADR-0005)
  └── kernel/bus_azure.py
  └── all agents bind() pub/sub overrides (P14)
  └── data.request/ready.market topics
  └── SERVICEBUS_CONNECTION_STRING secret

DSPy / PromptOptimizer (ADR-0010)
  └── (no code yet — port is the isolation boundary)
  └── golden eval set + metric (tool-agnostic; the guarantee)
  └── per-(task × model) compiled prompt artifacts
  └── champion-challenger registry (ADR-0002 pattern)

LightGBM (ReturnModel port)
  └── agents/forecaster/lightgbm_adapter.py only
  └── ReturnModel protocol isolates callers

FinBERT (SentimentModel port)
  └── agents/forecaster/finbert_adapter.py only
  └── SentimentModel protocol isolates callers

Tiingo / Alpaca / Finnhub / FMP / AV (market data)
  └── agents/provider/<source>.py only
  └── CompositeDataSource + DataSource protocol isolate callers
  └── market_source_from_settings / broker_from_settings routing

Container deployment (ADR-0007)
  └── Dockerfile per agent (tailored deps)
  └── DockerHub image registry
  └── Azure Container Apps env (trading-agents-env, australiaeast)
  └── Azure Key Vault (master-only accessor)
  └── agent code is stateless — deployment change does NOT touch logic
```

---

## Horizon watch list

Technologies the operator actively researches and intends to evaluate. Entries here
graduate to CONSIDERED (with an ADR or decision note) when a bake-off has real data.

| Technology | Why watching | Unblock condition |
| --- | --- | --- |
| EvoPrompt | Proactive pre-model-swap prompt tuning (evolutionary search over candidate prompts) | Build DSPy eval harness first; run EvoPrompt on the same golden set; compare IC on the same metric |
| Pinecone / Weaviate / Qdrant | Vector database at scale if Neo4j native index proves too slow for RAG | Measure Neo4j ANN latency at 1M+ embeddings; open only if P99 > SLA |
| MLflow | Experiment tracking for LightGBM + DSPy offline runs | When ≥3 training runs per sprint justify a tracker |
| Feast | Feature store for Alpha158 + future factors | When Alpha158 is enabled (weight > 0) and factor computation moves offline |
| vLLM / Triton | Self-hosted LLM inference | If Anthropic API cost or latency SLA becomes a constraint |
| Interactive Brokers | Live execution (beyond Alpaca paper) | After sustained paper-trading profitability + regulatory review |
