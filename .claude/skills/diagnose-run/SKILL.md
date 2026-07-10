---
name: diagnose-run
description: Investigate why a scheduled/manual pipeline run did not complete (or behaved unexpectedly) and produce an evidence-cited explanation with a bounded remediation recommendation. Use for "how did the run go", "why did the run stop/fail", "why no trades", "why is acceptance red".
---

# Diagnose a pipeline run

You are investigating one run of the trading pipeline. Your deliverable is an **explanation with
cited evidence** (LAW-02: never assert a cause you did not observe) plus a **bounded remediation
recommendation** — you do not apply fixes in this skill.

**Input:** a run id (`sched-YYYY-MM-DD` for scheduled runs, day-keyed on the UTC as-of date).
If none given, default to the most recent expected fire: `sched-<UTC yesterday if before 22:30
UTC today, else UTC today>`. All commands run from the repo root with `.env` present.

## Procedure — stop at the first step that explains the symptom, then report

### 1 · Does the run exist, and how far did it get?

```bash
PYTHONPATH=. uv run python scripts/trace_run.py --run-id <run_id>   # 7 stages, per-stage numbers
PYTHONPATH=. uv run python scripts/accept.py    --run-id <run_id>   # gate PASS/FAIL + breaches
```

- **Run id not found at all** → go to step 2 (scheduler).
- **Stops at stage N** (< 7/7) → note which agent owns stage N+1; go to step 3.
- **7/7 but ACCEPTANCE FAIL** → check the breach list against the known signatures (step 6).
- **7/7 PASS but "something smells"** → steps 4–5 (data quality, deploy currency) still apply.

### 2 · Scheduler: did the cron fire, and was it supposed to?

```bash
az containerapp job execution list -g trading-agents -n dispatcher-cron -o table
```

- No execution at 22:30 UTC → job disabled/deleted, or Azure incident. Check job config.
- Execution `Succeeded` but no RunRequest → almost always the **calendar gate**: the as-of was
  not a NYSE session (weekend/holiday) — a clean skip, not a fault. Past the committed holiday
  table it raises `CalendarWindowExceededError` instead (see `orchestration/scheduled_dispatch.py`).
- Execution `Failed` → job logs:
  `az containerapp job execution show -g trading-agents -n dispatcher-cron --job-execution-name <name>`

### 3 · The stalled stage: did its container run, activate, and speak?

The cascade is graph-pull: each agent polls for its predecessor's artifact. A missing stage-N+1
artifact means the stage-N+1 agent never processed — in order of likelihood:

1. **Never scaled up** — KEDA window is 22:30–00:30 UTC (master 22:25):
   `az containerapp revision list -g trading-agents -n <agent> -o table` (replicas in window?)
2. **Never activated** — DL-36 tested activation refuses on a failed credential:
   query the graph for `Escalation` nodes (see snippet below) and check master logs.
3. **Crashed mid-work** — per-container logs:
   `az containerapp logs show -g trading-agents -n <agent> --type console --tail 200`
   and Log Analytics for prior windows (container logs don't survive scale-to-zero).
4. **Transport** — the five control-plane agents serve over Service Bus; a missing
   `AZURE_SERVICEBUS_CONNECTION_STRING` or deleted topic stalls request/response paths.

Graph queries (read-only; `load_dotenv` must point at the repo `.env` — **beware:** a script
run from outside the repo silently gets the in-memory store and every count reads 0):

```python
from dotenv import load_dotenv; load_dotenv(r"<repo>\.env")
from kernel.graph_env import build_graph_from_env
g = build_graph_from_env()
for label in ("Escalation", "Flag", "RemediationPlan"):
    for n in g.list_nodes(label): print(label, n.key, n.props.get("status"), str(n.props.get("reason",""))[:120])
```

### 4 · Data quality: did the provider serve degraded facts?

The trace's provider block prints `notes` — `fundamentals_degraded news_degraded
sectors_degraded earnings_degraded` means the analyst scored on technicals alone (depresses
confidence; can turn a normal day into a no-trade day). Cross-check the agent's secret
entitlements (`orchestration/packs/trading_secrets.json`) vs what ACTIVATE delivered, and
Finnhub/AlphaVantage rate limits at 22:30 UTC.

### 5 · Deploy currency: is the fleet running the code you think it is? (DL-46)

```bash
az containerapp list -g trading-agents --query "[].properties.template.containers[0].image" -o tsv
gh run list --workflow build-images.yml --limit 3
```

Merges rebuild images but the tag-pinned fleet does **not** move. If the running tag predates a
relevant merge, the explanation may be "the fix isn't deployed" — a green run can still be wrong.

### 6 · Known signatures (check before inventing a novel cause)

| Symptom | Likely explanation | Verify by |
| --- | --- | --- |
| `FAIL analyst.scored: 0 < floor` **with** rejection rows present | Legitimate no-trade day; gate lacks a no-trade verdict (policy gap, 07-09) | rejections listed in trace with confidences below the regime floor |
| Cron `Succeeded`, `run_request_count=0` | Non-session day (calendar gate working) | as-of vs NYSE calendar |
| No `BrokerPositionSnapshot` on a run | Pre-S120 images (deploy gap) — see step 5 | fleet tag vs merge history |
| Divergence Flag `qty_mismatch` after a fill | Reconciliation **working**, not failing | broker positions vs graph Positions |
| Stage artifacts stop after provider; no faults | Consumer agent never scaled/activated | step 3, in order |
| Every graph count reads 0 from a helper script | Wrong `.env` resolution → in-memory store | step 3 snippet warning |

## Report format (the deliverable)

1. **One-line answer** — where the run stopped / what the verdict means.
2. **Cause category** — scheduler · activation/credentials · transport · data-quality ·
   code-defect · deploy-gap · gate-policy · not-a-defect.
3. **Evidence** — the specific command outputs/nodes that prove it (quote them).
4. **Bounded recommendation** — one of: re-fire/resume the run · re-seed a secret (S108 seeder) ·
   retag the fleet (DL-46 machinery) · ack the flag · file a drift item / packaging request for
   the planning agent. Anything needing a code change: propose branch + PR, never push main.
