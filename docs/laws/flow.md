# Agent flow — the choreography

This is the **only** place inter-agent relationships are recorded. Each box is a sealed agent (its
laws live in `agents/<name>/laws/`); each edge is a **typed message**. Use this diagram to eyeball
whether the system is moving in the right direction and to confirm **type/condition alignment across
every hop** (an edge is valid only if the producer's lawful output is a lawful input of the consumer).

> **The diagram may not lie.** Every edge must correspond to a real message-type contract. When the
> message contracts change, this diagram changes in the same commit. (A CI check that the edges match
> the contracts' `consumes`/`emits` is a later hardening step.)

## Daily trading loop (the spine)

```mermaid
flowchart LR
  SCH([scheduler / trigger]) --> SUP[supervisor]
  SUP --> SCAN[scanner]
  SCAN -->|CandidateSet| ANLY[analyst]
  ANLY -->|RecommendationSet| PM[portfolio_manager]
  PM -->|OrderIntents| EXEC[execution]
  EXEC -->|Fills| MON[monitor]
  MON -->|CloseDecisions| EXEC
  EXEC --> BRK[(broker)]
  MON --> REPT[reporter]
  PM --> REPT

  SCAN -. MarketData .-> PROV[provider]
  ANLY -. MarketData + Regime .-> PROV
  PM   -. prices .-> PROV
  MON  -. prices .-> PROV
  PROV -. external feeds .-> FEEDS[(market-data APIs)]

  FCST[forecaster] -. advisory / shadow .-> ANLY
  GRAPH[(Postgres graph — provenance substrate)]
```

## Control & support (off the trading spine)

```mermaid
flowchart LR
  HUMAN([operator/human]) --> OPER[operator]
  OPER -->|typed intent| SUP[supervisor]
  SUP -->|capability gate / hard-NO| ALL[(all agents)]
  SUP -. faults / lineage .-> GRAPH[(Postgres graph)]
  CURA[curator] -. out-of-band datasets .-> GRAPH
  RSCH[researcher] -. parameter-change proposals .-> SUP
```

## Runtime lifecycle (below the trading spine)

> Managed by the **master agent** (ADR-0007). This layer is not part of the trading choreography;
> it controls which containers exist and what they are allowed to do.

```mermaid
flowchart TD
  MASTER[master] -->|reads AgentDefinition nodes| GRAPH[(Postgres graph registry)]
  MASTER -->|fetches secrets| KV[(Azure Key Vault)]
  MASTER -->|ACTIVATE signed message| AGENT[any agent container]
  AGENT -->|EHLO + capability declaration| MASTER
  MASTER -. starts / drains / scales .-> AGENT
  AGENT -. health: PRE_FLIGHT / ACTIVE / INERT .-> MASTER
  GRAPH -. Session / MessageRecord / AgentInstance .-> MASTER
```

- **master** is the first container to start and the sole Key Vault accessor.
- Agents transition: `PRE_FLIGHT → ACTIVE` (on valid signed ACTIVATE) or `→ INERT` (on timeout).
- Pending messages for crashed instances survive in Postgres-backed `MessageRecord` graph nodes and
  are re-routed on restart by type matching.
- This layer is **orthogonal** to the trading spine above; `orchestration/dispatcher.py` and the
  `supervisor` agent are unaffected.

## Reading notes

- **Solid edges** = the binding trading path (a typed request/response or hand-off).
- **Dashed edges** = supporting flows (data fetch, advisory, audit, out-of-band).
- **`provider` is the single external-data boundary** — every "ask data" edge terminates at it; no
  other agent touches a market-data API.
- **`broker` and the market-data APIs** are external systems; exactly one agent owns each boundary
  (execution → broker, provider → data APIs).
- The **graph** underlies everything: every box appends provenance; no box mutates another's records.

## Legend of the load-bearing message types

| Edge | Message type | Producer role | Consumer role |
| --- | --- | --- | --- |
| scanner → analyst | candidate set | reduced/ranked universe | scores it |
| analyst → PM | recommendation set | scored, gated picks | sizes/risk-checks |
| PM → execution | order intents | sized, approved orders | submits idempotently |
| execution → monitor | fills | executed orders | opens/manages positions |
| monitor → execution | close decisions | exit decisions | submits the close |
| any → provider | market-data / regime request | a data need | clean facts + quality |
