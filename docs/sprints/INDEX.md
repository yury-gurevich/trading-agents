# Sprints index — phases, goals, and what shipped

**How to use:** find the phase you care about in the table below. For the full
chronological sprint list with goal summaries, see [README.md](README.md). For
the overall progress bar, see [../build-plan.md](../build-plan.md).

---

## Phase map

| Phase | Sprints | Theme | Status |
| --- | --- | --- | --- |
| **P1** | S01–S07, S22 | Kernel runtime, first 3 agents (provider/scanner/analyst), Celery bus, MCP tool binding | **complete** |
| **P2** | S08 | Observability adapter (metrics SDK) | **complete** |
| **P3** | S09, S11–S13 | PM, execution, monitor, reporter (full pipeline slice) | **complete** |
| **P4** | S14–S15 | Dispatcher daily loop + supervisor message lineage | **complete** |
| **P5** | S16–S17 | Operator intent parsing + supervisor capability gate | **complete** |
| **P6** | S18–S21 | Surfaces CLI (resolve_flag, lifecycle queries, approve, incidents, explain) | **complete** |
| **P7** | S23 | Researcher agent: bounded parameter proposals | **complete** |
| **P8** | S24–S25 | Stage gate: evidence-based promotion, StageTransition nodes | **complete** |
| **P9** | S26 | MeteredFaultSink wiring + observability proof | **complete** |
| **P10** | S27–S29 | Curator: dataset assembly, training trigger, predictor registry | **complete** |
| **P11** | S30–S35, S38–S42, S44–S45, S50–S55 | Analyst deterministic port: 15 technical + fundamental + relative-strength pillars; scanner beta/earnings; PM risk/sector gates; reporter %-metrics + $ repoint; provider feeds (Tiingo, Alpaca, Finnhub, FMP, sectors, earnings) | **complete** |
| **P12** | S36–S37, S46–S49, S56–S57 | Sentiment champion–challenger trinity: LM lexicon (champion) + provider/AV (challenger) + FinBERT (advisory); sentiment scorecard harness | **complete** |
| **P14** | S60–S67 | Kernel pub/sub + claim-check + Azure Service Bus backend (all 8 agents dual-mode) | **complete** |
| **Law cycle** | S69 | Provider law cycle: DRIFT-006/007 corrected; 23/43 clauses green; laws LOCKED v1; template locked for agent backfill | **complete** |
| **Q1** | S58–S59 | Qlib Phase Q1: LightGBM price/return shadow signal + training + IC scorecard | **complete** |
| **Q2** | S68 | Qlib Phase Q2: Alpha158 22-field pillar (off by default, weight=0.00) | **complete** |
| **Q1b** | S110 | Qlib workflow adoption (R001 addendum 2026-07-04): signal evaluation battery — rank IC, per-date IC mean/std/IR, quantile spread + monotonicity, multi-horizon decay, stability; OOS-only CLI. Live Tiingo check (DL-37); baseline best at h=20 (IC-IR 0.27) | **complete** — shipped 0.53.00 (2026-07-04, merged `0818679`) |
| **Q1c** | S111 | Qlib workflow adoption: rolling retrain + IC-decay trigger — decay measured against the S110 baseline, challenger must beat incumbent on the same window, operator holds `--apply`; + committed resumable Tiingo exporter | **complete** — shipped 0.54.00 (2026-07-04, merged `45f6c34`) |
| **Q3** | S112 | Qlib workflow adoption: researcher backtest evidence — self-built no-lookahead walk-forward harness (pyqlib 3.13-incompatible), `BacktestEvidence` optional contract field (researcher 0.2.0), bounded signal-catalogue CLI; the Q5 prerequisite | **complete** — shipped 0.55.00 (2026-07-05, merged `feb7f87`); Q5 governed factor mining unblocked |
| **Deliberation quality (DL-41)** | S114 | 🔴 **Priority** — complete the challenger-veto evidence: render every enforced gate as value **+ explicit pass/fail outcome**, and thread the **PM risk gates** (`max_sector_pct` concentration, sizing, held positions) that are computed but currently unrendered; PM emits gate outcomes (additive contract), `veto_context.py` split, completeness test. Deterministic evidence fix, not a prompt change (DSPy = DL-42, later). | **complete** — shipped 0.56.00 (2026-07-05, merged `6d9e9d0`); live Aura check proved every gate rendered with explicit outcome |
| **Q5 (part A)** | S113 | Qlib workflow adoption: governed factor proposal — bounded factor catalogue + LLM proposes an in-catalogue factor (enum-guarded, fail-open, LLM only in composition root) → S112 walk-forward scores it → `FactorProposal` with `BacktestEvidence` into the review queue. LLM never drives; researcher `external_io=()` intact. Shadow→promote is S115 (part B). | **complete** — shipped 0.57.00 (2026-07-06, merged `3ec2d9e`); live check: GPT-5.5 selected in-catalogue `momentum lookback=60`, off-menu selection failed open |
| **Law cycle** | S70 | Per-agent law backfill: scanner/analyst/PM/execution laws authored → cited → LOCKED v1 | **complete** |
| **Law cycle** | S71 | Per-agent law backfill cont.: monitor/reporter/forecaster/operator/supervisor/curator/researcher | **complete** |
| **ADR-0010** | S72 | `system_prompt` tunable on operator + forecaster (ADR-0010 immediate close) | **complete** |
| **ADR-0010 (LLM quality)** | S109 | Heterogeneous deliberation: Defender/Challenger on GPT-5.5, the debate Judge on Opus (`claude-opus-4-8`); dedicated `DELIBERATION_JUDGE_*` env (operator model untouched); veto now debates a grounded proposition (fixes S96). Not the EXP-004 scorer judge. | **complete** — shipped 0.52.00 (2026-07-03); **re-run 0.55.01 (2026-07-05)** cleared the deferred proofs: live-Opus check + golden re-freeze + firewall PASS, plus a reasoning-budget harness fix (empty `gpt-5` challenger) |
| **P15** | S73–S83 | Multi-agent container split: master bootstrap + Dockerfiles + RSA signing + Key Vault + GHCR build pipeline + credential naming + provider ingestor + graph-pull work loops (S79 provider→scanner; S80 scanner→analyst; S81 analyst→PM; S82 execution+monitor+reporter closes DL-08; S83 dispatcher RunRequest trigger makes provider graph-pull + end-to-end demonstrator) | **in progress** — paused under etalon-first (DL-34) |
| **Platform/pack + etalon** (post-P14) | S84–S89, S96 | ADR-0012 substrate/pack extraction — grants + secrets out of the master image (S84–S86, DL-12); staleness gate counts trading sessions (S87, DL-10); DL-09 filter verdicts + quality scorecard (S88–S89); deliberation understanding + challenger-veto (S96, DL-31). Continuous etalon-first work — live status in `../STATE.md`, not a numbered phase. | **shipped** |
| **P12/P13** | tbd | DSPy `PromptOptimizer` port + golden eval set + per-(task×model) compiled prompt artifact | **queued** |
| **P16** | S90–S95 | Continuous-improvement system (ADR-0013): CI-1 parameter catalogue · CI-2 RunMetrics on graph · CI-3 ParameterSet (configurable-not-settable) · CI-4 experiment+compare · CI-5 gate+promote (absorbs ADR-0010) · CI-6 optimiser (sweep; ingest target first) | **queued** — specs written (S90–S95), deferred behind a perfect etalon (DL-19) |
| **Fleet Activation / Credential Validation** (DL-30/DL-35/DL-36) | S97–S108 | Close the distributed-platform gap: `serve_loop` primitive (S97) → control-plane agents served in-process (S98–S99, retires every `idle_loop()`) → Azure Service Bus receiver + parity (S100) → permanent Neo4j (S101) → 13-container run-through + distributed acceptance (S102) → dispatcher cron (S103). Then the DL-36 credential arc **(A/B/C/D complete)**: tested activation + escalation on failure (S104) → master secret cache (S105) → LLM bounded-catalogue remediation planner (S106) → **eval-gated auto-remediation execution (S107, Piece D)** — DSPy behind ADR-0010's `PromptOptimizer` port gates the selector (its first harness instance), then safe executors run the `test→execute→production→documentation` loop with one automatic shot, plus the `_instance_counter` concurrency fix + composition-root wiring. Then **`.env`→Key Vault seeder, tested-before-insert (S108)** — only working credentials ever enter the vault (DL-36, one step upstream; fail-closed). In-process before distributed; reverses the etalon-first pause for the fleet workstream (DL-35), then hardens activation handoff (DL-36). | **in progress** — S97–99 + S104–108 shipped (0.51.00; zero `idle_loop` remains, in-process fleet complete); **S100 handover refreshed Codex-ready (2026-07-03); Service Bus namespace `trading-agents-bus` provisioned + live-verified** (`infra/servicebus.bicep`), so S100 is unblocked to build; S101–103 handovers exist (pre-S104 drafts — refresh before executing) |

---

## Queued / parked sprints

| Sprint | Goal | Blocked by |
| --- | --- | --- |
| S43 (monitor realized PnL) | Monitor real `pnl_cents` → reporter re-point to $ | S55 already re-pointed; revisit when live broker wired |
| P12/P13 DSPy harness | `PromptOptimizer` port + golden eval set + DSPy first impl | Plumbing complete first (build-plan P11/P14 exit) |

---

## Adding a sprint

1. Next number: **S115**, then S116 …
2. Create `sprint-NN-<slug>.md` using the standard header block from [README.md](README.md).
3. Add a row to the `README.md` index table immediately.
4. Update the phase map above when the sprint belongs to a defined phase.
5. Set STATUS in [../../docs/STATE.md](../STATE.md) to the active sprint.
