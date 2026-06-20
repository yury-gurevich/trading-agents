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
| **Law cycle** | S70 | Per-agent law backfill: scanner/analyst/PM/execution laws authored → cited → LOCKED v1 | **complete** |
| **S71 (next)** | S71 | Per-agent law backfill cont.: monitor/reporter/forecaster/operator/supervisor/curator/researcher | **planned** |
| **P12/P13** | tbd | DSPy `PromptOptimizer` port; `system_prompt` tunable on operator + forecaster | **queued** |
| **P15** | tbd | Multi-agent container split: DockerHub images, Azure Container Apps deploy, master bootstrap | **queued** |

---

## Queued / parked sprints

| Sprint | Goal | Blocked by |
| --- | --- | --- |
| S43 (monitor realized PnL) | Monitor real `pnl_cents` → reporter re-point to $ | S55 already re-pointed; revisit when live broker wired |
| P12/P13 DSPy harness | `PromptOptimizer` port + golden eval set + DSPy first impl | Plumbing complete first (build-plan P11/P14 exit) |

---

## Adding a sprint

1. Next number: **S71** (active), then S72, S73 …
2. Create `sprint-NN-<slug>.md` using the standard header block from [README.md](README.md).
3. Add a row to the `README.md` index table immediately.
4. Update the phase map above when the sprint belongs to a defined phase.
5. Set STATUS in [../../docs/STATE.md](../STATE.md) to the active sprint.
