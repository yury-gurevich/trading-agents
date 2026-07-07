<!-- Agent: planning | Role: sprint handover -->
# Sprint 102 — Distributed fleet run-through: 13 containers, one ACCEPTANCE PASS

**Phase:** Fleet Activation (DL-30 / DL-35 — the payoff sprint of the arc)
**Branch:** `sprint-102-fleet-run-through`
**Status:** shipped — merged `3049955` (0.62.00, 2026-07-08); closeout evidence below
**Effort:** M/L (one small CI-tested wire + live infra validation)

---

## What changed since the original draft (why this refresh)

- **The store is PostgreSQL (ADR-0014).** S101 never executed — it was **absorbed by S116–S118**.
  The fleet's shared store is Neon (Sydney) via `POSTGRES_DSN`; `infra/deploy-agents.ps1` already
  probes the DSN, injects it as `secretref:postgres-dsn`, and runs `alembic upgrade head` before the
  fleet starts. Graph-pull agents therefore distribute **for free** — every container polls the same
  Postgres. No Neo4j anywhere (a `NEO4J_URI`-only env raises the ADR-0014 error).
- **The bus receive half exists but is not composed.** S100 shipped
  `kernel/bus_azure_receiver.py` behind the `RequestConsumer` protocol (claim-check both directions,
  complete/abandon/dead-letter), namespace `trading-agents-bus` is provisioned — but all five served
  entrypoints (curator, forecaster, operator, researcher, supervisor) still hard-code
  `LocalRequestConsumer()`. **Nothing in the composition root constructs `AzureServiceBusBus`.**
  That wire is Part A of this sprint.
- **Deploy images are `:latest` from GHCR**, rebuilt on merge-to-main. A branch run-through cannot
  use them — Part B needs branch-tagged images (see kickoff).

## Codex kickoff (paste this)

> Execute **Sprint 102 — distributed fleet run-through** exactly as specified in this file
> (`docs/sprints/sprint-102-fleet-run-through.md`). Read first: `docs/STATE.md` (S100 + S116–S118
> entries), `kernel/serve_loop.py`, `kernel/bus_azure.py` + `bus_azure_receiver.py` +
> `bus_azure_config.py`, `infra/deploy-agents.ps1`, `scripts/accept.py`, and
> `scripts/servicebus_receiver_live_check.py` (the S100 live pattern).
>
> - **Start:** from `main` (`git pull`), `git checkout -b sprint-102-fleet-run-through` (delete any
>   stale local branch first). **Hard gate:** `make ci` green, 100 % coverage, ≤200-line modules,
>   headers. Bump `pyproject.toml` **0.61.00 → 0.62.00** (feat: distributed serve transport) +
>   `uv lock`. Live-only fixes found in Part B land on this same branch under the same version.
> - **Part A — env-selected serve transport (code, CI-tested):**
>   1. A small kernel composition helper (e.g. `consumer_from_env(agent_type)`): returns
>      `AzureServiceBusBus(...).request_consumer(...)` when a Service Bus connection string is in
>      the env (`AZURE_SERVICEBUS_CONNECTION_STRING` / `SERVICEBUS_CONNECTION_STRING`, per
>      `bus_azure_config.py`), else `LocalRequestConsumer()`. Optional-SDK import discipline as in
>      S100 (no `azure` import at module top).
>   2. All five served entrypoints (curator, forecaster, operator, researcher, supervisor) compose
>      through it instead of hard-coding `LocalRequestConsumer()`. Behavior with no bus env is
>      **unchanged** (that is the regression fence).
>   3. The **requesting** side of a cross-container round-trip (whatever the control-plane proofs
>      in Part B use to place a request — trace how `AzureServiceBusBus` publishes) must work from
>      a separate process. If a thin helper/script is needed, keep it in `scripts/`.
>   4. `infra/deploy-agents.ps1`: add a `-Tag` parameter (default `latest`) so Part B can deploy
>      branch-built images; inject the Service Bus connection string as a secretref alongside
>      `postgres-dsn` (mirror that pattern; never print either).
> - **Part B — the run-through (live; the milestone the arc exists for):**
>   1. **Build + push branch images** tagged `s102` (same build path CI uses) and deploy master
>      first, then the 12 agents, via `infra/deploy-agents.ps1 -Tag s102` against Azure Container
>      Apps env `trading-agents-env` (RG `trading-agents`). The script's preflight (DSN probe +
>      `alembic upgrade head`) must pass.
>   2. **Activation proof:** master EHLO → signed ACTIVATE for **all 12** agents (only scanner was
>      proven at S76); `AgentInstance` + `CapabilityGrant` nodes present **in Postgres** for all 12.
>   3. **The distributed run:** place one `RunRequest` (`orchestration/start.py` path) and let the
>      fleet run graph-pull across containers; execution against **Alpaca paper** (DEP-BROKER).
>      Walk the provenance chain (`MarketData → ScanRun → … → Snapshot`) and run
>      `scripts/accept.py` → **`ACCEPTANCE PASS`** on the distributed run.
>   4. **Control-plane proofs, each in its own container over Service Bus:** an operator command
>      round-trips; the supervisor gate/fault path fires; the forecaster writes a `shadow`
>      prediction; curator and researcher each serve a request.
>   5. **Observatory:** capture the run (`orchestration/observatory.py`); ledger Layer 2
>      (choreography) ⬜ → 🟩 with this run as the citation.
>   6. **Live-only defects** (expect some — every prior live run found in-memory-hidden bugs:
>      DRIFT-011/012/013/014): fix on this branch, each with a `drift-register.md` entry + cited
>      regression test.
>   7. **Teardown + cost stop:** run artifacts stamped and torn down via `scripts/pg_teardown.py`
>      to 0/0 (registry/audit nodes from activation may stay — they are production config, like the
>      S108 vault rows; say which stayed); S100-pattern Service Bus topic cleanup; then **scale the
>      fleet to zero / stop the container apps** (13 × min-replicas 1 bills while running — keep
>      the live window short). Record everything in `docs/laws/functionality-checks.md`.
>      **Never print the DSN or any connection string.**
> - **Out of scope — flag, don't build:** cron scheduling (S103 places runs by hand here), any new
>   agent feature or contract change, pgvector/RAG, multi-replica scaling policy (S103+), real
>   capital (Alpaca **paper** only).
> - **Do NOT merge or push to `main`** — commit on the branch only; fill **Closeout evidence** here.

---

## Notes for the coding agent

- Neon quirks (S116/S117): scale-to-zero cold start ~0.5 s — connect timeouts ≥ 10 s;
  `sslmode=require`; direct (non-pooler) host. The DSN comes from `.env` locally and Key Vault
  secret `postgres-dsn` (`trading-agents-kv`) in the fleet — both already wired.
- Service Bus: namespace `trading-agents-bus` (`infra/servicebus.bicep`), connection string in
  `.env`. The S100 live check (`scripts/servicebus_receiver_live_check.py`) is the round-trip
  pattern to imitate, including claim-check and topic teardown.
- Master keypair reaches containers as `MASTER_PUBLIC_KEY_PEM_B64` / private-key equivalents
  (`kernel/bootstrap.py`); `infra/deploy-agents.ps1` handles this today — don't reinvent it.
- Replicas are pinned 1/1 in the deploy script — correct for this run-through; scheduling/scaling
  policy is S103's question, not yours.
- Success is LAW-02-proven: "the fleet works" = the captured `ACCEPTANCE PASS` + the 12-agent
  activation log + the five control-plane round-trips — never a green deploy alone.

---

## Closeout evidence

**Branch / version.** Branch `sprint-102-fleet-run-through`; no merge to `main`. Version bumped
`0.61.00 -> 0.62.00` and `uv.lock` refreshed (`0.62.0`).

**Part A shipped.**

- `kernel/serve_transport.py` adds `consumer_from_env(agent_type, graph)`: no Service Bus connection
  string -> `LocalRequestConsumer`; `AZURE_SERVICEBUS_CONNECTION_STRING` /
  `SERVICEBUS_CONNECTION_STRING` -> lazy `AzureServiceBusBus(...).request_consumer(...)`.
- Curator, forecaster, operator, researcher, and supervisor entrypoints compose through that helper.
- `scripts/servicebus_request.py` provides the separate-process claim-check request side.
- `infra/deploy-agents.ps1 -Tag <tag>` deploys branch images and injects the Service Bus connection
  string as `secretref:servicebus-connection-string`; `scripts/servicebus_prepare_routes.py` creates
  served request topics/subscriptions before containers poll.
- `.github/workflows/build-images.yml` supports manual branch image tags; `:s102` builds were published
  by GitHub Actions, not local Docker.

**CI / tests.** Local gate before live: `make ci` green with 100.00% coverage. Latest pre-closeout
gate after live fixes: `1393 passed, 5 skipped, 100.00% coverage`; ruff, format, mypy (547 files),
import-linter, module-size hard block, headers, pip-audit, and detect-secrets all passed. Focused
regressions: `tests/test_serve_transport.py`, `tests/test_served_agent_images.py`,
`tests/test_agent_image_commands.py`, `agents/execution/tests/test_execution_entrypoint.py`, and
`tests/test_servicebus_request.py`.

**Images / deploy.** Final image build: GitHub Actions `build-images.yml` run `28877717323`, commit
`b50b544`, all 13 matrix jobs green and tagged `s102`. Final deploy:
`infra/deploy-agents.ps1 up -Tag s102` passed preflight (Azure CLI, Container Apps env, GHCR creds,
Postgres connect + `SELECT 1`, Service Bus config, GHCR 13/13), ran `alembic upgrade head`, verified
served request routes, deployed master first, then all 12 agents. Final app list showed all 13
Container Apps Running on `ghcr.io/yury-gurevich/trading-agents-*:s102`.

**Activation proof.** Postgres latest active instances existed for all 12 agent types:
`analyst`, `curator`, `execution`, `forecaster`, `monitor`, `operator`, `portfolio_manager`,
`provider`, `reporter`, `researcher`, `scanner`, `supervisor`; `missing_agent_types=[]`.
Each had `CapabilityGrant` rows; execution included `broker`, provider included `data_feeds`, operator
included `llm`.

**Distributed run.** Placed exactly one manual `RunRequest` via `orchestration.start.place_run_request`:
`s102-dist-20260707T1530Z`, 16 liquid tickers. The distributed containers completed:
`RunRequest -> MarketData -> ScanRun -> AnalystRun -> PMRun -> ExecutionRun -> MonitorRun -> Snapshot`.
Trace: 16/16 OHLCV returned, 640 bars, 320 headlines, 4 scanner survivors, 3 analyst buys, 3 PM
approvals, `ExecutionRun submitted=3 rejected=0`. Alpaca paper proof: the three `Fill` nodes had
non-empty UUID-like `broker_order_id`s and status `pending`; the in-process `PaperBroker` would have
produced `paper:` IDs.

**Observatory / acceptance.**

```text
OBSERVATORY  OK - all invariants hold
ACCEPTANCE  PASS - every stage did its job within its boundaries
```

Ledger Layer 2 moved to 🟩 in `docs/laws/ledger.md` with this run as citation. The functionality
check row was appended to `docs/laws/functionality-checks.md`.

**Service Bus control-plane proofs.** All requests were sent from separate local processes over Azure
Service Bus into the served Container Apps and returned claim-checked replies:

- operator `interpret` -> `outcome=intent`, `family=status`.
- supervisor `report_fault` -> `accepted=true`, durable `Fault`.
- supervisor `dispatch_intent` -> confirmation gate rejection and durable `Flag`.
- forecaster `forecast` -> durable `ShadowPrediction`, `shadow=true`.
- curator `build_dataset` -> durable `Dataset`.
- researcher `propose` -> served response (`insufficient data for evidence window`, no mutation).

**Live-only defects fixed on this branch.**

- `DRIFT-016`: served images lacked `--extra azure`; fixed Dockerfiles + deploy route prep.
- `DRIFT-017`: `portfolio_manager` Dockerfile used `agents.portfoliomanager.entrypoint`; fixed command.
- `DRIFT-018`: execution entrypoint hard-coded `PaperBroker`; fixed to `broker_from_settings()`.
- `DRIFT-019`: Service Bus proof helper could not print frozen Postgres reply payloads; fixed JSON
  normalization.

**Teardown / cost stop.** `scripts/pg_teardown.py` sweeps deleted **33 edges / 58 S102 nodes**; follow-up
query reported `remaining_s102_artifacts={}`. Activation registry rows intentionally stayed as
production boot evidence (`Session=5`, `AgentInstance=115`, `CapabilityGrant=257`). Service Bus cleanup
deleted 11 disposable `s102-*.reply` topics and verified `remaining_s102_topics=[]`; stable served
request topics stayed as production routes (`curator.requests`, `forecaster.requests`,
`operator.requests`, `researcher.requests`, `supervisor.requests`). `infra/deploy-agents.ps1 down`
deleted all 13 Container Apps; final `az containerapp list` returned no app names.

**Deviation notes.** No local Docker was used after the operator explicitly ruled it out; branch images
were built and published by GitHub Actions. Stable Service Bus request topics were not deleted because
they are deploy-prepared production routes, not disposable proof topics. Registry activation rows were
left by design as production/audit config.
