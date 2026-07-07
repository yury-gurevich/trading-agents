<!-- Agent: planning | Role: sprint handover -->
# Sprint 102 — Distributed fleet run-through: 13 containers, one ACCEPTANCE PASS

**Phase:** Fleet Activation (DL-30 / DL-35 — the payoff sprint of the arc)
**Branch:** `sprint-102-fleet-run-through`
**Status:** ready for handover (refreshed 2026-07-07 onto the 0.61.00 Postgres spine; the pre-S104
draft assumed S101/Neo4j and is superseded by this version)
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

<!-- Coding agent: replace this comment. Required: files changed; version/deps; Part A test
evidence; exact `make ci` summary (counts + coverage); Part B evidence — image tag + deploy log
summary, 12-agent activation proof, provenance tally, verbatim ACCEPTANCE PASS line, the five
control-plane round-trip proofs, observatory/ledger update, drift entries for live-only fixes;
teardown proof (pg_teardown 0/0, Service Bus topics clean, fleet scaled to zero); the
functionality-checks.md row. State any deviation from spec explicitly. Do not merge. -->
