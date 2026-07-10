---
name: audit-costs
description: Report accumulated costs — Azure hardware spend for the trading-agents resource group and LLM spend priced from the graph's LLMCall ledger. Use for "what is this costing", budget checks, or cost anomalies (a spike is a diagnostic signal, not just a bill).
---

# Audit accumulated costs

Two meters, two sources of truth. Report them separately and then together; a cost spike often
diagnoses a defect (a retry loop shows up in tokens or requests before it shows up anywhere else).

## Hardware (Azure)

```bash
az costmanagement query --type ActualCost \
  --scope "subscriptions/5ef50a27-50a4-4d90-9695-da61b2309cf3/resourceGroups/trading-agents" \
  --timeframe MonthToDate \
  --dataset-aggregation '{"totalCost":{"name":"Cost","function":"Sum"}}' \
  --dataset-grouping name=ServiceName type=Dimension -o table
```

If `costmanagement` is unavailable in the CLI, fall back to the portal number and say so —
do not estimate silently. Expected shape (2026-07): Service Bus is the floor cost (standing
namespace); Container Apps ≈ ~2h/day × 14 replicas; Log Analytics + Key Vault marginal;
Neon Postgres and GHCR are on free tiers (report as $0 with the tier named).

## LLM (the graph ledger)

`LLMCall` nodes (`agents/operator/store.py`) carry `model`, `tokens_in`, `tokens_out`,
`created_at` — every operator call is ledgered. Aggregate per model and price:

```python
from dotenv import load_dotenv; load_dotenv(r"<repo>\.env")
from kernel.graph_env import build_graph_from_env
from collections import defaultdict
g = build_graph_from_env(); agg = defaultdict(lambda: [0, 0, 0])
for n in g.list_nodes("LLMCall"):
    a = agg[n.props["model"]]; a[0] += 1; a[1] += n.props["tokens_in"]; a[2] += n.props["tokens_out"]
for m, (calls, ti, to) in agg.items(): print(m, calls, ti, to)
```

Price with current per-Mtoken rates for the models found (check the `claude-api` skill /
provider pricing pages — do **not** price from memory). **Coverage caveat (report it):** the
ledger covers operator-path calls; deliberation (GPT-5.5 debaters + Opus judge), DSPy compile
runs, and remediation-planner calls are only included where they write `LLMCall` nodes — check
before claiming totals, and label anything unledgered as "untracked" rather than $0. Offline
compile spend (S119/S121-style) lives in vendor consoles, not the graph.

## Report format

Hardware MTD $ by service · LLM MTD $ by model (calls, tokens, rate used) · combined total ·
untracked spend named explicitly · one line on trend vs the prior period if data allows ·
anomalies worth a `/diagnose-run` (e.g. token count out of line with runs).
