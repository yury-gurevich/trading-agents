# Sprint 100 — Azure Service Bus receiver: the distributed backend (fleet arc, etalon cut line)

**Phase:** Fleet Activation (DL-30 / DL-35)
**Branch:** `sprint-100-servicebus-receiver`
**Status:** ready for handover (re-based 2026-07-07 onto the 0.60.01 codebase — version notes updated; bus seams unchanged since S67/S99)
**Effort:** M–L

---

## Codex kickoff (paste this)

> Execute **Sprint 100 — Azure Service Bus receiver** exactly as specified in this file
> (`docs/sprints/sprint-100-servicebus-receiver.md`). It is a complete, self-contained handover.
>
> - **Start:** from `main` (`git pull`), `git checkout -b sprint-100-servicebus-receiver`. The patterns to
>   copy are **S67** (the Azure *send* backend behind the pub/sub protocol) and **S99** (agents serving
>   over `serve_loop` in-process) — this sprint is their receive-side twin.
> - **Coordination (read this first):** the shared working tree currently holds **S109's uncommitted WIP**
>   (HISTORICAL note — S109 long merged). S100 touches `kernel/bus_*` (no file overlap with
>   S109's `kernel/deliberation*`), but the tree state + version bump will collide. **Run S100 in a clean
>   checkout, or only after S109 is committed/merged.**
> - **Hard gate every commit:** `make ci` green — 9 steps, **100 % coverage on non-`# pragma` lines**,
>   modules **≤ 200 lines**, coding-agent `Agent:`/`Role:` headers. Bump the MINOR from the **actual**
>   `pyproject.toml` on `main` at branch time (**0.60.01 → 0.61.00**, feat → MINOR zeroes patch)
>   + `uv lock`.
> - **The unit gate stays infra-free:** all Azure I/O carries `# pragma: no cover`; the Service Bus SDK
>   stays an **optional** dependency group; the parity test **skips cleanly without creds**.
> - **Live check needs a provisioned namespace** (see *Prerequisite*). If it isn't provisioned yet, ship
>   the CI/parity work and record the live smoke as **pending provisioning** (S105 precedent) — do not fake it.
> - **Do NOT merge or push to `main`** — commit on the branch only, stop for operator confirmation, and
>   append a **Closeout evidence** block (like S99/S108's) when done.

---

## Goal

Give the S97 serve transport its **real distributed backend**. Today
[`AzureServiceBusBus`](../../kernel/bus_azure.py) is **send-only** — `publish` pushes to a topic
(`_azure_send`) but there is **no receiver**: nothing consumes a subscription and dispatches to a handler,
and `request` routes through an in-process shim. This sprint implements the **consume/receive half** so an
agent's `serve_loop` can pull work off Service Bus and the claim-check `ready:<ref>` events flow between
containers. After it, the fleet's *communication* is complete and **proven at parity** (in-process ==
Service Bus); only provisioning + a live 13-container run (S101–S102) remain.

## Prerequisite — provisioning ✅ DONE (2026-07-03)

**The namespace is provisioned and verified** — the live smoke can run. `infra/servicebus.bicep` created
`trading-agents-bus` (Standard tier — topics/subscriptions + dead-letter) in RG `trading-agents`
(australiaeast, sub `5ef50a27…`), with a `ready` topic + `probe` subscription for connectivity checks. A
live **send→receive round-trip passed** at provision time (SENT → RECEIVED → completed), so the connection
string is proven-good. It is set as `SERVICEBUS_CONNECTION_STRING` in `.env` (gitignored — never commit it).

Redeploy / rehydrate:

```bash
az deployment group create --subscription 5ef50a27-50a4-4d90-9695-da61b2309cf3 \
  --resource-group trading-agents --template-file infra/servicebus.bicep
az servicebus namespace authorization-rule keys list --resource-group trading-agents \
  --namespace-name trading-agents-bus --name RootManageSharedAccessKey \
  --query primaryConnectionString -o tsv   # -> SERVICEBUS_CONNECTION_STRING (secret)
```

**Production route (still recommended, DL-36):** seed the connection string into Key Vault as a *tested
credential* — add a `servicebus` entry to the S108 vault manifest with a probe = one live send→receive
round-trip — so the master hands it out verified-before-use like every other secret. `.env` is fine for
the local smoke; Key Vault is the fleet path.

## Decisions (resolved at planning — recommendations to confirm + capture in `design-log.md`)

- **Topics/subscriptions, not queues** (pub/sub per ADR-0005): a **topic per capability**, a
  **subscription per consuming agent**. The broker routes by topic; **no agent names another**.
- **The operator sync-RPC and the master handshake stay HTTP** (both already are) — do **not** move them
  onto Service Bus. Only the event/`ready` fan-out moves to SB.
- **Forecast publisher (S99's deferred decision): the orchestrator/dispatcher publishes** a `forecast`
  request per recommendation — so the forecaster never reads the analyst node itself (`FORE-TRG-02`).
- **Reply semantics = claim-check + `ready` event, not blocking RPC:** a served handler writes its artifact
  to the graph (claim-check, ADR-0005) and `RequestConsumer.reply()` **publishes a `ready:<ref>` event**;
  correlation via the envelope id. (`serve_once`'s `consumer.reply(bus.request(...))` shape is unchanged —
  `reply` just publishes rather than returning synchronously.)
- **Ack:** `complete` on success, `abandon` (redeliver) on a transient fault, **dead-letter after N
  attempts**; the **supervisor** watches the dead-letter subscription (its existing fault-sink role).

## Scope

### In

- `AzureServiceBusBus` gains a **`RequestConsumer`** (the S97 protocol —
  `poll() -> list[AgentMessage]`, `reply(response)`): a Service Bus **subscription receiver** that pulls
  messages, decodes the envelope, resolves claim-check refs via
  [`kernel/claim_check.py`](../../kernel/claim_check.py), and returns them from `poll`; `reply` publishes
  the response to the requester's reply path. `serve_once` / `serve_loop` are **unchanged** — the
  transport swaps behind the protocol (exactly as `LocalRequestConsumer` proved in S99).
- Consumer-side claim-check **read** (the producer-side write already exists) so a `ready:<ref>` resolves
  to the graph artifact on the receiving container.
- **Ack semantics:** `complete`/`abandon`/dead-letter as above.
- A **both-backends parity test**: the same served round-trip over the in-process consumer **and** (skipped
  without creds) over Service Bus — proving in-process == Service Bus, exactly as S67 did for `publish`.
- `AzureServiceBusSettings` extended if a subscription name / receive timeout / max-delivery-count is
  needed ([`kernel/bus_azure_config.py`](../../kernel/bus_azure_config.py)).

### Out

- **No new agent logic**; no fleet deploy (S101–S102 — provisioning + the 13-container run).
- The operator/master **HTTP** paths (unchanged).
- Any change to the graph-pull trade spine (it already talks via the graph, not the bus).

## Deliverables

- Receiver in `kernel/bus_azure.py` **or** a small `kernel/bus_azure_receiver.py` if the 200-line guard
  bites — **split rather than grow**.
- `AzureServiceBusSettings` extension (subscription/timeout/delivery-count) if needed.
- Parity test skipping cleanly without creds (the S67 pattern).
- A probe / live-smoke entry doing one real send→receive round-trip against a namespace (reuse the S108
  probe shape; ideally the `servicebus` vault probe from the *Prerequisite*).
- A `design-log.md` entry capturing the resolved decisions above.
- `make ci` green (100 % on non-`# pragma` lines), SDK optional, modules ≤ 200 lines, version bumped + `uv lock`.

## Functionality check (sprint-close rule)

- **CI-provable (always):** the parity test proves a served round-trip is identical over the in-process
  consumer and the Service Bus consumer (SB half skips without creds).
- **Live smoke (needs the provisioned namespace):** one real **send→receive** round-trip — publish a
  served request / `ready:<ref>` to a topic, the subscription receiver pulls it, `serve_once` dispatches,
  and the artifact/`ready` event comes back and resolves via claim-check. **Tear down** the test
  topic/subscription (or drain the test messages) → namespace left as found. Record the row in
  `docs/laws/functionality-checks.md`. If unprovisioned, record **pending provisioning** (do not fake it).

## Dependencies

- **S97** (serve protocol + `RequestConsumer`), **S99** (agents serve over it in-process — shipped
  0.51.00), **S67** (the Azure *send* backend + the optional-SDK/parity pattern), `kernel/claim_check.py`.
- **ADR-0005** (event-driven pub/sub over Azure Service Bus, claim-check — the deployment bus).

## Version bump

New capability (distributed serve backend). **0.60.01 → 0.61.00** (feat → MINOR, HARD RULE). Bump from the *actual*
`main` HEAD `pyproject.toml` at branch time.

## Execution notes (for the coding agent — cold-start handover)

**Start.** From `main` (`git pull`; HEAD ≥ `0d8f4f8`): `git checkout -b sprint-100-servicebus-receiver`.
Read `kernel/serve_loop.py` (the `RequestConsumer` protocol + `serve_once`), `kernel/bus_azure.py` +
`kernel/bus_azure_config.py` (the send-only backend to extend), `kernel/claim_check.py`,
`kernel/envelope.py`, `agents/supervisor/entrypoint.py` (the S99 serve pattern), the **S67** send backend
+ its parity test (search `tests/` for the Azure publish parity), and **ADR-0005**.

**Gate.** `make ci` green — 9 steps, **100 % coverage on non-`# pragma` lines**, modules ≤ 200 lines,
coding-agent headers.

**Boundaries.** `kernel` stays dependency-optional — the Service Bus SDK is an **optional** group, never a
hard import; all live I/O is `# pragma: no cover`; the unit gate never touches a namespace. Agents never
import other agents; no new graph labels.

**Commit.** Branch-per-sprint; commit only your own files; conventional message ending with
`Co-Authored-By: …`. Do **not** merge/push to `main` without operator confirmation.

**Session gotchas (carried from S97–S109):**

1. **Service Bus is NOT provisioned** (`.env` has only a commented `# SERVICEBUS_CONNECTION_STRING=`). The
   parity/CI work is infra-free; the live smoke needs the namespace (see *Prerequisite*).
2. **`detect-secrets`** flags connection strings — keep the real value in `.env`/Key Vault only; never a
   literal in code or tests (use env + `# pragma: allowlist secret` on fixtures if needed).
3. **The SDK stays optional** — mirror how `bus_azure.py` already guards `azure.servicebus` behind the
   connection-string check + `# pragma: no cover`. A missing SDK must not break `make ci`.
4. **Reply is publish, not return** — over pub/sub the served handler's result is a `ready:<ref>` event +
   a graph write, not a synchronous RPC value; keep `serve_once` unchanged and make `reply()` publish.
5. **mypy `--strict`** covers tests; annotate; `if TYPE_CHECKING:` for annotation-only imports.
6. **Coordination:** do this in a clean checkout or after S109 lands — the shared tree has S109's
   uncommitted WIP + a 0.52.00 bump.
7. `jq` is installed + allowed (`Bash(jq:*)`); `gh --jq` also works.

## Notes

**This is the etalon-first cut line.** S97–S100 are CI/parity-provable with no live spend; S101–S103 commit
to running the fleet on live Azure infra (DL-35 accepted that trade). Ship S100 and the fleet's
*communication* is complete and proven at parity — only provisioning + a live run remain. The
`servicebus`-as-a-tested-credential path (Prerequisite option 1) also closes the loop with DL-36: the bus
connection string, like every other credential, is verified before it is trusted.
