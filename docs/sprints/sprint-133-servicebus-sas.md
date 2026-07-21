<!-- Agent: planning | Role: sprint handover -->
# Sprint 133 — Blast radius part 2 (backlog row I): per-agent Service Bus SAS

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-133-servicebus-sas`
**Status:** ready for handover (packaged 2026-07-20)
**Effort:** M

---

## Why this sprint

S131 split the Postgres blast radius into 15 per-agent roles. The **last shared credential**
is the Azure Service Bus connection string: every container holds the same namespace-level
`AZURE_SERVICEBUS_CONNECTION_STRING` (a `RootManage`-tier SAS delivered secret-backed), so
one compromised container can send to and listen on the **whole bus**. This sprint scopes
Service Bus access per agent, completing backlog row I.

**Severity note (honest, from the threat-model review):** the bus carries claim-check
`ready:<ref>` pointers and RPC request/reply envelopes — **not the data** (the data is on
the graph, now per-role-locked as of S131). So a compromised bus identity can trigger
spurious work or spoof RPC requests, but cannot read another agent's data off the bus. This
is a lower-severity surface than the Postgres half; the value is the same principle
(attribution + revocability + least authority) and closing the last shared secret.

## What already exists (read before estimating)

- **Topology** (`kernel/serve_transport.py`): 5 **served** agent types
  (`curator, forecaster, operator, researcher, supervisor`) each own a
  `<agent>.requests` topic + worker subscription (`scripts/servicebus_prepare_routes.py`).
  RPC replies go to per-request **reply topics**. The publish/subscribe claim-check path
  (`AzureServiceBusBus.publish` → `_azure_send(topic, event)` in `kernel/bus_azure.py`)
  carries `ready` events on per-stage topics.
- **Delivery today** (`infra/deploy-agents.ps1::Get-ServiceBusConfig`): one
  `AZURE_SERVICEBUS_CONNECTION_STRING` → `secretref:servicebus-connection-string`,
  identical for all 13 apps + the dispatcher job. This is the exact pattern S131 replaced
  for Postgres (`Get-GraphConfig` per-target) — **reuse that shape.**
- **Azure constraint (verify before designing):** Service Bus caps SAS authorization rules
  at **12 per namespace** and **12 per entity (topic/queue)**. We have 13 agents, so
  per-agent *namespace-level* rules do NOT fit — the Azure-correct model is **entity-level
  (per-topic) rules** with `Send` / `Listen` split. Confirm the current caps in the target
  namespace first; the design hinges on this.
- **The send/listen matrix is the design work**: who sends to / listens on each topic. A
  served agent Listens on its own `.requests` subscription and Sends replies; a requester
  Sends to a target's `.requests` topic and Listens on its reply topic; publishers Send to
  stage `ready` topics, subscribers Listen. **Measure this from the code, do not guess.**
- **S131 rollback pattern**: `-UseSharedPostgresDsn` switch + shared secret kept untouched.
  Mirror it: `-UseSharedServiceBusDsn`, shared connection string retained for rollback.

## Decisions taken at packaging (LAW-06)

1. **Entity-level SAS with a Send/Listen split, per the 12-rule cap** (decision confirmed
   only after the coder verifies the live namespace caps — if Azure has raised them, a
   per-agent namespace model may be simpler; record which path was taken and why).
   *Ruled out:* keeping one `RootManage` string (the whole hole); a per-agent namespace
   rule model if the 12-cap still holds (13 > 12).
2. **Derive the SAS grant matrix from `kernel/serve_transport.py` + the publish topics**,
   not a hand-maintained list — a small pure planner (mirror `scripts/pg_role_plan.py`)
   emits, per agent, the (topic, rights) pairs it needs; unit-tested pure-functionally.
   *Ruled out:* a hand-edited YAML matrix that drifts from the code.
3. **Delivery reuses the S131 secret-backed per-target pattern** in `deploy-agents.ps1`
   (`Get-ServiceBusConfig $target`), each app receiving its own scoped connection string
   from Key Vault; provisioning script never prints a key (the S131 catch-all-handler
   discipline). *Ruled out:* env-plaintext delivery.
4. **Scope excludes the message-payload layer** — no change to claim-check/RPC envelope
   format, topics, or `bus_azure` logic; this is a credentials/authorization sprint only.

## Kickoff (paste this)

> Execute **Sprint 133 — Service Bus SAS** exactly as specified in this file
> (`docs/sprints/sprint-133-servicebus-sas.md`). Read first: backlog row I in
> `docs/hardening-backlog.md`; the S131 sprint doc + `scripts/pg_role_plan.py` /
> `scripts/pg_provision_roles.py` (the pattern you mirror); `kernel/serve_transport.py`,
> `kernel/bus_azure.py`, `scripts/servicebus_prepare_routes.py` (the topology);
> `infra/deploy-agents.ps1` (`Get-ServiceBusConfig` + the S131 `Get-GraphConfig` per-target
> shape); design-log **DL-48**.
>
> **Contract (DL-48 — enforced):**
>
> - **Start:** `git pull` on `main` — `pyproject.toml` must read **0.71.06** (stop and
>   report if S134 has not merged; **this sprint sequences AFTER S134** per the 2026-07-21
>   operator directive — assertion hardening runs first). Branch
>   `sprint-133-servicebus-sas`. Bump **PATCH → 0.71.07** + `uv lock`.
> - **Drift rule / Secrets rule / Handback rule:** as S131 (fetch+merge+re-gate; no key in
>   the tree or in output; closeout+return notes last).
> - Hard gate: `make ci` green (exit code captured), 100 % coverage, ≤200-line modules,
>   headers, tunables where thresholds appear.
>
> **Work items:**
>
> - **A (verify + plan):** confirm the live namespace SAS-rule caps; choose the model
>   (entity-level Send/Listen split unless caps allow simpler) and record it. Write a pure
>   planner (`scripts/sb_sas_plan.py`) deriving per-agent (topic, rights) from
>   `serve_transport.py` + publish topics; unit-test pure-functionally (no live Azure).
> - **B (provision):** an idempotent provisioner (`scripts/sb_provision_sas.py`, mirror the
>   S131 role provisioner) that creates/rotates the authorization rules and writes each
>   agent's scoped connection string to Key Vault; never prints a key; catch-all handler
>   emits only the exception type.
> - **C (delivery):** extend `infra/deploy-agents.ps1` `Get-ServiceBusConfig $target` to
>   deliver the per-agent scoped connection string secret-backed, with a
>   `-UseSharedServiceBusDsn` rollback switch and a bounded `az` flip runbook section
>   (outside the 22:25–00:30 UTC window).
> - **D (docs):** backlog row I → Done with part-2 evidence; DEP note in
>   `docs/laws/dependencies.md`; design-log entry recording the chosen SAS model + the cap
>   that forced it.
> - **Functionality check (LAW-02), live, outside the fleet window:** (1) provision scoped
>   rules, flip delivery, `az containerapp show` proves each app carries its own scoped
>   secret; (2) positive path — a served agent Listens on its own topic and a requester
>   Sends to it successfully under the scoped identities (reuse
>   `scripts/servicebus_receiver_live_check.py` / `servicebus_request.py`); (3)
>   **least-authority proof** — an agent's scoped identity is **refused** Send on a topic
>   it should not reach (the canary-equivalent); (4) revoke one scoped rule → that identity
>   refused, fleet stays green. Record under `docs/reports/sprint-133-servicebus-sas/`;
>   tear down any canary rule to zero. As in S131, if proving container-origin identities
>   would require firing a production run outside market hours, prove the mechanism with a
>   controlled check and leave the live-window capture as an operator follow-up.
> - **Wrap up:** README/INDEX rows; Closeout + Return notes; push, hand back.
>   **Do not merge.** The delivery flip is an operator infra step (coordinate; outside the
>   run window).

## Guardrails

- Credentials/authorization only — no change to topics, envelope format, or `bus_azure`
  message logic (decision 4).
- No SAS key ever in the tree or in command output; provisioner silent on secrets.
- Infra flips outside 22:25–00:30 UTC; rollback = `-UseSharedServiceBusDsn` (shared string
  retained untouched).
- If the 12-rule cap forces a coarser model than per-agent, record the honest limit and the
  best achievable scoping — do not fake per-agent isolation that Azure won't enforce.

## Definition of done

1. Every fleet target connects to Service Bus under its own scoped SAS identity (not the
   shared `RootManage` string), proven per-app.
2. A scoped identity is demonstrably refused an out-of-scope Send (least-authority proof)
   and one rule's revocation locks out only that identity while the fleet stays green.
3. Backlog row I → Done (part 2 complete); chosen SAS model + forcing cap recorded in the
   design log.
4. `make ci` green at 100 % (exit code captured); no key in the tree; closeout + return
   notes filled.

## Closeout (coding agent fills; planning agent verifies before merge)

```text
CLOSEOUT — Sprint 133
Branch / merge commit:   <branch> / <merge sha or "not merged by instruction">
make ci:                 MAKE_CI_EXIT_CODE=<n>; <passed/skipped>; coverage <pct>
Functionality check:     <scoped-identity delivery, positive send/listen, least-authority
                          refusal, rule revocation, fleet health>
Version:                 0.71.06 → 0.71.07 (PATCH); uv.lock refreshed
Backlog row I:           <Done + evidence link>; SAS model chosen: <entity/namespace + why>
Drift rule:              <origin/main moved? merged? re-gated?>
Deviations from spec:    <none, or the honest list>
```

## Return notes (coding agent appends at handback — mandatory)

<!-- return notes go below this line -->
