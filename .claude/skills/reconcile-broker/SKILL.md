---
name: reconcile-broker
description: Investigate broker↔graph state — Alpaca paper positions/orders vs graph Positions/Fills, divergence Flags, pending orders. Use for divergence Flags, "do we really hold X", stuck pending fills, or before cancelling an order. Broker = truth for holdings; graph = truth for lineage (DL-44).
---

# Reconcile broker against graph

Two truths coexist (DL-44): the **broker executes reality** (positions, fills, cash) and the
**graph explains it** (lineage, decisions). Never "fix" a divergence by editing the graph by
hand — S120's reconciliation adopts broker truth with provenance; your job here is to *explain*
a divergence and, at most, act on the **broker** side with operator approval.

## Procedure

1. **Broker state** (creds from `.env`; endpoint already contains `/v2` — strip before joining
   paths):

   ```python
   # GET {base}/v2/positions and {base}/v2/orders?status=open with
   # APCA-API-KEY-ID / APCA-API-SECRET-KEY headers (ALPACA_API_KEY / ALPACA_API_SECRET)
   ```

2. **Graph state:** open `Position` nodes (skip `broker_superseded_by` / `broker_absent`),
   `Fill` nodes with `status=pending` + their `broker_status` props, latest
   `BrokerPositionSnapshot`, and pending divergence `Flag`s (reason text lists
   `missing_graph_position` / `extra_graph_position` / `qty_mismatch` per ticker). Node shapes:
   `agents/execution/reconciliation_store.py`.

3. **Interpret** — common readings:
   - **Flag after a fill night** = reconciliation *working*: quantify (graph vs broker per
     ticker), confirm monitor adopted broker truth (`run_id=broker-reconciled` or later
     pm-run Positions), then recommend the operator ack the Flag.
   - **Pending Fill with `broker_status=filled`** = evidence stamped, terminal state known —
     healthy. A pending Fill with **no** broker evidence past one run means the refresh didn't
     run (check images, DL-46).
   - **Order pending days** = placed after-hours fills at next open, or it's stuck — check the
     order's `created_at` vs sessions.

4. **Acting (operator approval required, broker side only):** cancel an open order =
   `DELETE {base}/v2/orders/{id}`, then re-GET to verify `canceled`. Never sell/flatten to
   "re-zero" — that destroys the accumulating dataset (ruled out in DL-44).

## Report format

Per-ticker table (graph qty · broker qty · verdict) · open orders with age · which reading from
step 3 applies · evidence · recommendation (ack flag / cancel order X / nothing — working as
designed / drift item).
