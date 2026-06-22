# Project State — Archive (STATE-02)

**Continuation of [STATE.md](STATE.md).** This file holds the shipped-sprint ledger for
**Sprints 37–76** (P11 deterministic-logic depth, P12/P13 sentiment + forecaster, P14 pub/sub
re-architecture, and the P15 container/master-bootstrap arc), split out on 2026-06-22 to keep
STATE.md short. Older history (**Sprint 36 → P0** + retired components) lives in
[STATE-01.md](STATE-01.md). The live dashboard (Now / Next / Parked / recent ~8 Shipped) stays in
[STATE.md](STATE.md).

---

## P15 — container-per-agent + master bootstrap (S73–S76)

**Track B COMPLETE — P15 fleet hardening, PROVEN on Azure 2026-06-21 (then torn down).**

- **Signature verification (0.15.0):** agents verify the master's RSA-PSS signature on ACTIVATE.
  `kernel/bootstrap.py` `master_public_key_from_env`/`master_private_key_from_env` + `_pem_from_env`
  resolve keys from raw OR base64 env (base64 dodges multi-line-PEM in az CLI). 12 entrypoints
  regenerated to resolve+pass the pubkey. `deploy-agents.ps1` generates a stable keypair (gitignored
  `infra/master-keypair.local.json`), distributes private→master (secret), public→agents (env).
- **Key Vault (0.15.1):** `trading-agents-kv` (RBAC) + user-assigned identity `trading-agents-master-id`
  (Key Vault Secrets User) wired into the master deploy via `MASTER_KEY_VAULT_URL` + `AZURE_CLIENT_ID`.
  Real secrets seeded (tiingo, anthropic; alpaca-paper deferred; finnhub/fmp under different .env names).
  `AzureKeyVaultSecretStore.get_secret` now returns `''` on not-found (fix — matches Null/EnvVar stores).
- **Verify-deploy:** full 13-agent fleet up; master read KV via managed identity (logs show vault calls,
  no auth error); all agents registered (= signatures verified); master/operator/provider/scanner logs
  clean (no InvalidSignature / Forbidden / CredentialUnavailable). Torn down + Aura paused → spend 0.
- **Neo4j → Aura (operator request):** local `.env` repointed `NEO4J_URI`/`NEO4J_TEST_URI` →
  `neo4j+s://8cf6d231…`, db `neo4j`; the live integration test now **passes against Aura** (was failing
  on dead localhost). DL-05 posture: real Aura while trial lasts, smart-paused.
- **Open (DL-07):** secret-name reconciliation — `.env` uses `PROVIDER_FINNHUB_API_KEY`/`FNP_API_KEY`/
  `ALPACA_API_KEY` (paper); `secret_map.py` expects `FINNHUB_API_KEY`/`FMP_API_KEY`/`ALPACA_KEY_ID`.
  (Largely addressed in S77.)

**`MASTER_GRAPH=memory` toggle (0.13.0→0.14.0).** `agents/master/entrypoint.py` `select_graph_store()`
picks the master's graph backend — `memory` (`InMemoryGraphStore`, rebuilt on boot, zero deps) else
Neo4j (default). Implements design-log **DL-05**: the cloud fleet runs **in-memory** until trading needs
durable persistence, then a small VM. **972 tests**, 100% coverage.

**S75 — P15 Azure Key Vault secret distribution (0.12.0→0.13.0).** `agents/master/key_vault.py`:
`SecretStore` Protocol + `NullSecretStore` + `EnvVarSecretStore` + `AzureKeyVaultSecretStore` (prod,
`# pragma: no cover`). `agents/master/secret_map.py`: `AGENT_SECRETS` entitlement table
(provider/execution/operator) + `resolve_config`. `MasterAgent.activate()` populates `ACTIVATE.config`
with per-agent minimum-privilege secrets. DRIFT-002 RESOLVED. **971 tests**, 100% coverage. (Note: the
`AGENT_SECRETS` table was later relocated out of the substrate in S85.)

**S76 — FULL 13-AGENT FLEET PROVEN ON AZURE 2026-06-21 (then torn down to stop spend).**
`build-images.yml` matrix built all 13 agent images → GHCR (~1 min for 12 light + the heavy forecaster);
ADR-0011 registry = GHCR. Deployed master + 12 trading agents to Container Apps; master booted, connected
to Aura (trial `8cf6d231`, GCP Sydney). Each agent EHLO'd → signed ACTIVATE → registry persisted; verified
by Cypher: **Session 1 / AgentInstance 12 / CapabilityGrant 27**. Cross-cloud Azure→GCP graph write
confirmed. Torn down + Aura paused → spend ~0. New ops tooling committed: `infra/aura.ps1`,
`infra/status.ps1`, `infra/fleet-graph.ps1`, `infra/setup-github-ci.ps1`; Azure deploy identity = OIDC.

**S74 — P15 RSA signing + agent entrypoints (0.11.0→0.12.0).** `kernel/crypto.py`: `generate_keypair`,
`sign_pss`, `verify_pss` (RSA-PSS 2048 SHA-256). `kernel/bootstrap.py`: `activate_agent` (injectable
`_send`), `idle_loop` placeholder. `agents/master/http_server.py`: `handle_health`/`handle_ehlo` + `serve`.
12 trading-agent entrypoints send EHLO, verify signed ACTIVATE, then idle. **951 tests**, 100% coverage.

**S73 — P15 foundation: master bootstrap agent + per-agent Dockerfiles.** `agents/master/` package:
`MasterAgent` (`start/activate/drain`), `DEFAULT_GRANTS` (12 agent types), `MasterSettings`, graph write
helpers. `contracts/master.py`: `AgentState`, `EHLOMessage`, `ACTIVATEMessage`, `DRAINMessage`. Master
`laws.md` LOCKED v1. 13 per-agent Dockerfiles + `docker-compose.yml`. No version bump (scaffolding).
**906 tests**, 100% coverage. (`DEFAULT_GRANTS` later relocated out of the substrate in S84.)

---

## Law cycle + agent law backfill (S69–S72)

**S72 — `system_prompt` tunable on operator + forecaster (ADR-0010 immediate close).**
`system_prompt: str = tunable("")` on `OperatorSettings` (DSPy champion slot; empty = dynamic
`build_interpret_system()`) wired into `_interpret_command`; pre-declared on `ForecasterSettings`. No
version bump.

**S71 — per-agent law backfill (remaining 7 of 11).** monitor/reporter/forecaster/operator/supervisor/
curator/researcher LOCKED v1 (18 sections each). Citation pass across 18 test files; 124 new green clauses.
No version bump (docs-only). All 11 non-provider agents now have LOCKED v1 laws.

**S70 — per-agent law backfill (4 of 11).** scanner/analyst/PM/execution LOCKED v1. 95 green clauses
(SCAN 18/39, ANLZ 24/43, PM 23/43, EXEC 30/49). `test_scanner_explain.py` split for the 200-line block.
**895 tests**, 100% coverage. No version bump (docs-only).

**S69 — provider law cycle, template locked (0.10.0→0.11.0).** DRIFT-006 (benchmark promoted to
`DataRequest.benchmark_ticker` + `MarketData.benchmark`, `taint=False`); DRIFT-007 (`caller_authorized`
- `allowed_callers` gate across all three buses). Provider `laws.md` LOCKED v1; `_TEMPLATE.md` lock comment
added. **894 tests**, 100% coverage.

---

## P12/P13 sentiment + forecaster, P14 pub/sub (S56–S68)

**S68 — analyst Alpha158 feature pillar (qlib Q2, 0.9.0→0.10.0).** `AlphaFeatureRow` (22 fields) +
`compute_alpha_features` (None < 62 bars) + `score_alpha158` (z-score → logistic 0–100); pillar off by
default (`alpha158_pillar_weight=0.00`); pyqlib-free (3.13). **890 tests**, 100% coverage.

**P14 complete — inter-agent comms re-architecture (S60–S67, 0.8.0→0.9.0).** Replaced synchronous RPC
hand-offs with event-driven publish/subscribe + claim-check (ADR-0005). All 7 agents migrated to dual-mode;
kernel gains `claim_check_write/read` + `ReadyEvent`; dispatcher → trigger-emitter (publishes `run.trigger`,
subscribes `report.snapshot.ready`); `AzureServiceBusBus` + `AzureServiceBusSettings` optional `azure` dep.
`pm_run_id` threaded execution→monitor→reporter. **863 tests**, 100% coverage. `build-plan.md` P14 →
complete.

**S59 — forecaster LightGBM training pipeline + return IC scorecard (qlib Q1 follow-on, 0.7.0→0.8.0).**
`build_label_rows` + walk-forward `split_rows` + `train_and_save`; new `return_scorecard` capability
(Pearson IC + hit_rate + directional quartile breakdown). CONTRACT 0.3.0→0.4.0.

**S58 — forecaster LightGBM price/return shadow signal (qlib Q1, 0.6.0→0.7.0).** `ReturnModel` Protocol +
lazy `LightGBMReturnAdapter` + pure `_features.py` (5 features) → `ShadowPrediction` (never gates) + `Model`
node. `lightgbm`-direct (pyqlib 3.13-incompatible, R001). CONTRACT 0.2.0→0.3.0.

**S57 — forecaster sentiment scorecard harness (P12, 0.5.0→0.6.0).** `sentiment_scorecard` compares the
three scorers (lexicon + provider `SentimentReading`, FinBERT `ShadowPrediction`) vs injected forward
returns. Pure stats (`domain/statistics.py` pearson/std/ols2; `domain/scorecard.py` `comparison_metrics`
with per-scorer IC + incremental IC); inner-joins by `{analyst_run}:{ticker}`; advisory only. forecaster
CONTRACT 0.1.0→0.2.0. **756 tests**, 100% coverage. P12 code-complete (remaining: live news runway).

**S56 — analyst champion = full Loughran-McDonald master dictionary (P12, 0.4.0→0.5.0).** Binding lexicon
(`sentiment_rules.py`) loads the genuine LM master dictionary (Positive 354, Negative 2355; vendored under
`agents/analyst/domain/data/`) unioned with curated headline verbs; polarity-disjoint (asserted). Interface
- behaviour unchanged. **739 tests**, 100% coverage.

---

## P11 — deterministic-logic depth (S41–S55) + ADR-0007

**S55 — reporter re-point to real $ PnL, P11 COMPLETE (0.3.0→0.4.0).** `collect_trade_outcomes` now reads
the monitor's realized `pnl_cents` (S43) off each `CloseDecision`, bucketing by sign into dollar-based
`profit_factor` + `expectancy_cents` + `closed_trades_with_pnl` across all triggers including time exits.
`expectancy_pct → expectancy_cents` rename (free-form dict → no contract change). **735 tests**, 100%
coverage. **Closes P11** (analyst engine, PM gates, scanner beta+earnings, reporter metrics, monitor
realized PnL all ported). PR automation live (Dependabot auto-merge); CodeQL restored.

**S43 — monitor realized PnL on close (P11, 0.2.0→0.3.0).** Pure `realized_pnl_cents=(exit−entry)×qty`
in `domain/exit_rules.py`; per-position decision logic extracted to `agents/monitor/decide.py::evaluate_one`
(agent.py 198→171L); `CloseDecision.pnl_cents: int | None`. Monitor CONTRACT 0.1.0→0.2.0. **738 tests**.

**S54 — scanner earnings-window exclusion (P11, 0.1.0→0.2.0).** Consumes S42's `MarketData.earnings`; drops
candidates with earnings within `earnings_exclusion_days` (5) of the as-of; `_days_to_earnings` gate after
the beta cap; additive + dormant. No contract change. **733 tests**. (First HARD-RULE MINOR bump.) Scanner
deterministic port (beta S50 + earnings S54) complete.

**S42 — provider earnings-calendar feed (P11).** `DataSource.fetch_earnings` via Finnhub `/calendar/earnings`,
pure `_parse_next_earnings` → earliest upcoming date, field-gated into `MarketData.earnings`. Refactor: 5
optional field-gates extracted to `market_fields.py` (provider agent.py 197→131L). CONTRACT 0.3.0→0.4.0.
**726 tests**.

**S41 — reporter profit-factor + expectancy (P11).** `agents/reporter/domain/trade_outcomes.py` pairs
`Position`↔`CloseDecision`, buckets by trigger (target/stop), returns `profit_factor`/`expectancy_pct`/
`closed_trades_with_pnl`; time exits excluded by design; merged into `RunSnapshot.portfolio_metrics` on both
live + degraded paths. No contract change. **714 tests**.

**S53 — provider laws CAP + PARAM sections (ADR-0007 backfill).** `CAPABILITY DECLARATION (CAP)` JSON schema
(messaging/graph/HTTPS/secrets) + `PARAMETERS (PARAM)` 20-entry table for `agents/provider/laws/laws.md`.
Establishes the template for all 11 remaining agent law backfills. No code/contract change.

**ADR-0007 accepted — container-per-agent + master bootstrap.** One Docker image per agent → registry →
Azure Container Apps; master agent is sole Key Vault accessor; agents start braindead, activate via signed
EHLO/ACTIVATE; Neo4j is the operational registry; law files gain CAP + PARAM sections. Graph store at the
time: local Neo4j Enterprise Docker (`infra/neo4j/local/`, db `traiding-agents`); DEP-NEO4J 01/02/03 GREEN.
Aura `02812797` deleted 2026-06-19 (empty at cutover).
