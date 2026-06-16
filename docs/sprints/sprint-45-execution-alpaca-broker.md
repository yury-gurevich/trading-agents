<!-- Agent: planning | Role: sprint handover -->
# Sprint 45 — Execution Alpaca paper broker (real fills behind the Broker port)

**Status:** planned · **Branch:** `sprint-45-execution-alpaca-broker` · **Build phase:** execution / DEP-BROKER (ADR-0006) · **Effort: M–L**

## Goal

Give the execution agent a **real broker**: an `AlpacaBroker` that submits orders to Alpaca's
**paper-trading** REST API and returns real fills/positions — behind the **existing `Broker` port**, so
the rest of the pipeline is untouched. Today the only broker is the in-process `PaperBroker` (a
deterministic fake). Alpaca paper mode is a free, broker-grade harness (real account, simulated fills,
real P/L — "fake purchases"); ADR-0006 locks Alpaca as the broker. This sprint builds the adapter +
a `broker_from_settings` builder and wires it as the runtime default **when Alpaca keys are present**
(else `PaperBroker`, keeping the unit gate network-free).

**No contract change.** `contracts/execution.py` already declares `external_io=("alpaca_broker",)` and
`Fill.status` already allows `filled | partial | rejected | pending`. This is a new adapter behind the
`Broker` Protocol plus a settings-driven default swap — the exact shape of Sprint 44 (Tiingo), but on
the broker boundary instead of the data boundary.

## Why (context)

- Read first: `docs/sprints/README.md` (guardrails); **`docs/sprints/sprint-44-provider-tiingo-feed.md`**
  (the adapter+builder+default-swap pattern this mirrors); `docs/decisions/0006-market-data-feed-strategy.md`
  (Alpaca = broker); `docs/laws/dependencies.md` DEP-BROKER (the contract this proves).
- **Shipped code you mirror / extend (read it):**
  - **`agents/provider/tiingo.py` + `composite.py::market_source_from_settings`** — the network-isolated
    adapter (`_download` is `# pragma: no cover`; pure mappers fully tested) and the settings-builder
    pattern. Your `AlpacaBroker` + `broker_from_settings` are the broker-side twins.
  - **`agents/execution/broker.py`** — the `Broker` Protocol (`submit(idempotency_key, ticker, side,
    quantity, limit_price) -> BrokerFill`; `fills() -> tuple[BrokerFill, ...]`), the `BrokerFill`
    dataclass (status `filled|partial|rejected|pending`), `BrokerRejectedError`, and `PaperBroker`
    (the reference implementation — match its `submit`/`fills` semantics, incl. idempotent replay).
  - **`agents/execution/domain/submit.py`** — `submit_order` wraps `broker.submit` in a
    `fault_boundary`; **any exception your broker raises becomes an auditable rejected fill**
    (`rejected_broker_fill`). So network/API failure must *raise* (not fabricate) — the agent degrades
    honestly. `BrokerRejectedError` is the special case that carries a structured rejected fill.
  - **`agents/execution/domain/reconcile.py`** — `reconcile_fills(recorded, broker.fills())` matches by
    `idempotency_key` signature. Your `fills()` feeds this; keep `idempotency_key` stable across submit
    and fills (it's Alpaca's `client_order_id`).
  - **`agents/execution/settings.py`** — already has `alpaca_api_key`/`alpaca_secret_key` (Part A
    extends these). `ExecutionStageValue` + `live_gate.py` already gate non-paper stages — **do not
    touch stage gating**; AlpacaBroker runs at the `paper` stage against Alpaca's *paper* endpoint.
  - **`orchestration/bindings.py`** — `broker=broker or PaperBroker()` (the default re-point, Part D),
    mirroring how S44 re-pointed the data source.

### The Alpaca call (port this shape)

Paper REST base `https://paper-api.alpaca.markets`. Auth headers on every request:
`APCA-API-KEY-ID: <key>` and `APCA-API-SECRET-KEY: <secret>`.

- **Submit** — `POST /v2/orders`, JSON body
  `{"symbol", "qty", "side", "type": "market", "time_in_force": "day", "client_order_id": <idempotency_key>}`.
  Use a **market** order; `limit_price` from the port is the **reference price** for non-filled outcomes
  (Alpaca fills market orders at the market; an est-price limit risks never filling). Response (201) is
  an **order object**: `{id, client_order_id, symbol, qty, filled_qty, side, status, filled_avg_price,
  limit_price, ...}`.
- **Idempotency (DEP-BROKER-02)** — a duplicate `client_order_id` returns **`422`**
  (`client_order_id must be unique`). On that, **GET `/v2/orders:by_client_order_id?client_order_id=<key>`**
  and return that existing order's fill — same key submitted twice ⇒ one order. (PaperBroker's replay
  semantics, achieved via Alpaca's client_order_id.)
- **Fills** — `GET /v2/orders?status=all&limit=500` → array of order objects → one `BrokerFill` each,
  for `reconcile_fills`.

**Status map** (Alpaca order `status` → `BrokerFill.status`), in a pure helper:

| Alpaca status | BrokerFill.status | price |
| --- | --- | --- |
| `filled` | `filled` | `filled_avg_price` |
| `partially_filled` | `partial` | `filled_avg_price` |
| `new`, `accepted`, `pending_new`, `held`, `accepted_for_bidding` | `pending` | the submitted reference `limit_price` |
| `rejected`, `canceled`, `expired`, `done_for_day`, `stopped`, `suspended`, `replaced` | `rejected` | reference `limit_price`; `reason` = the Alpaca status |

> **Expected async behaviour (document, don't fix here).** The daily loop runs after the close, so a
> market order is usually **`pending`** at submit and fills next session. That is honest and
> contract-valid (`status="pending"`). The pending→filled **catch-up across sessions** (a reconcile/
> monitor pass) is **out of scope** — a follow-up. This sprint makes submit/fills faithful; it does not
> rework the loop's fill timing.

## Part A — Settings

`agents/execution/settings.py` — make the Alpaca fields read the real `.env` names (the `.env` uses
unprefixed `ALPACA_*`, but `ExecutionSettings` env_prefix is `EXECUTION_`; bridge with `validation_alias`)
and add base-url + timeout:

```python
from pydantic import AliasChoices, Field
# ...
alpaca_api_key: str | None = Field(
    default=None, repr=False,
    validation_alias=AliasChoices("EXECUTION_ALPACA_API_KEY", "ALPACA_API_KEY"),
)
alpaca_secret_key: str | None = Field(
    default=None, repr=False,
    validation_alias=AliasChoices("EXECUTION_ALPACA_SECRET_KEY", "ALPACA_API_SECRET"),
)
alpaca_base_url: str = Field(
    default="https://paper-api.alpaca.markets",
    validation_alias=AliasChoices("EXECUTION_ALPACA_BASE_URL", "ALPACA_BASE_URL"),
)
alpaca_timeout: int = tunable(
    15, why="Bound the Alpaca REST call so a slow broker cannot hang the run.",
    ge=1, le=60, unit="seconds",
)
```

(Confirm `populate_by_name`/alias behaviour with the existing `AgentSettings` base — if aliases fight
the `EXECUTION_` prefix, prefer `AliasChoices` so both the prefixed and `.env` names resolve. The
`.env` already carries the unprefixed Alpaca credential names plus an endpoint var; note in the handback
if the endpoint value (which includes `/v2`) needs reconciling — this adapter wants the host root.)

## Part B — Alpaca broker

New `agents/execution/alpaca.py` — ≤ 170L:

```python
"""Alpaca paper-trading broker over the execution Broker port.

Agent: execution
Role: submit orders and read fills from Alpaca's paper REST API (the real broker
boundary; ADR-0006). Idempotent via client_order_id.
External I/O: HTTPS calls to Alpaca (paper-api.alpaca.markets).
"""
```

- `AlpacaBroker(*, api_key, secret_key, base_url, timeout)` implementing `Broker`.
- `submit(idempotency_key, ticker, side, quantity, limit_price) -> BrokerFill`:
  builds the order body (client_order_id=idempotency_key), calls `self._submit_or_get(...)`
  (network), returns `_fill_from_order(order_json, idempotency_key, limit_price)` (pure).
- `fills() -> tuple[BrokerFill, ...]`: `_list_orders()` (network) → `_fill_from_order(...)` per order.
- **Network helpers** `_submit_or_get` / `_list_orders` / `_request` — all `# pragma: no cover`
  (real HTTPS; stdlib `urllib.request.Request` with the two `APCA-*` headers + `noqa: S310`).
  `_submit_or_get` encapsulates the POST→422→GET-by-client-order-id idempotency dance so the pure
  mapper never sees the network.
- **Pure, fully tested:** `_fill_from_order(order, idempotency_key, reference_price) -> BrokerFill`
  and the `_status_of(alpaca_status) -> Literal[...]` map. Never raise on a well-formed order dict;
  a `rejected`/`canceled` order maps to a rejected `BrokerFill` **returned** (not raised) so `fills()`
  can include it — but **submit** of a freshly-rejected order should raise `BrokerRejectedError(fill)`
  (so `submit_order` records it as rejected), matching `PaperBroker`.
- Money: `Money(amount=Decimal(str(filled_avg_price)))` when filled/partial; else the reference price.

## Part C — Broker builder

New tiny module `agents/execution/broker_factory.py` (or fold into `broker.py` if it stays < 200L):

```python
def broker_from_settings(settings: ExecutionSettings) -> Broker:
    """Return the live Alpaca paper broker when keyed, else the in-process PaperBroker."""
    if settings.alpaca_api_key and settings.alpaca_secret_key:
        from agents.execution.alpaca import AlpacaBroker
        return AlpacaBroker(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            base_url=settings.alpaca_base_url,
            timeout=settings.alpaca_timeout,
        )
    return PaperBroker()
```

## Part D — Runtime default re-point

`orchestration/bindings.py` — build execution settings once and route the broker through the builder:

```python
from agents.execution.broker_factory import broker_from_settings
from agents.execution.settings import ExecutionSettings
# ...
execution_settings = ExecutionSettings()
ExecutionAgent(
    bus,
    graph=graph,
    broker=broker or broker_from_settings(execution_settings),
    settings=execution_settings,
    sink=sink,
).bind()
```

No Alpaca keys in the unit gate ⇒ `broker_from_settings` returns `PaperBroker` ⇒ every existing test is
unaffected (and tests inject brokers explicitly anyway). With keys present, real paper runs hit Alpaca.

## Part E — Tests

### E1. `agents/execution/tests/test_alpaca_broker.py` — ≤ 150L

Pure mapper tests (the `MethodType` offline-stub of `_submit_or_get`/`_list_orders`, mirroring
`test_tiingo`/`test_fmp`):

- A **filled** order → `status="filled"`, `price == filled_avg_price`, `broker_order_id == id`,
  `idempotency_key == client_order_id`.
- **partially_filled** → `"partial"`; **new/accepted/pending_new** → `"pending"` priced at the
  reference; **rejected/canceled/expired** → `"rejected"` with `reason` = the status.
- **submit** of a rejected order raises `BrokerRejectedError` carrying the rejected fill; **fills()**
  *includes* rejected/pending orders (does not raise).
- Idempotent replay: a stubbed `_submit_or_get` that returns the pre-existing order for a duplicate key
  yields the same `BrokerFill` (same `broker_order_id`).
- `fills()` maps a list payload to one `BrokerFill` per order; empty/`[]` → `()`.

### E2. Builder routing

- `broker_from_settings(ExecutionSettings())` (no keys) → `PaperBroker`.
- `broker_from_settings(ExecutionSettings(alpaca_api_key="k", alpaca_secret_key="s"))` → `AlpacaBroker`.

### E3. Regression

- Full execution suite + `orchestration`/`surfaces` binding tests green; confirm the `bindings.py`
  change re-pins nothing (no keys ⇒ PaperBroker). Run the whole suite.

## Steps

1. Branch `sprint-45-execution-alpaca-broker` off `main`.
2. **A** settings → **B** `alpaca.py` (+ E1) → **C** builder (+ E2) → **D** bindings → **E3**.
3. `make ci`; full-suite regression green at the coverage floor (100.00).
4. `wc -l agents/execution/*.py` — every file < 200 (warn 150).
5. Push; hand back.

## Acceptance criteria

- `AlpacaBroker` implements `Broker`: `submit` POSTs a market order with `client_order_id=idempotency_key`
  and maps the response to a `BrokerFill`; a duplicate key returns the existing order's fill (idempotent);
  `fills()` lists broker orders for reconciliation. Network is isolated (`# pragma: no cover`); the
  status/price mappers are pure and fully tested.
- A freshly **rejected** submit raises `BrokerRejectedError`; a network/API failure raises (→
  `submit_order` records an auditable rejected fill — no fabrication).
- `broker_from_settings` returns `AlpacaBroker` iff both keys are set, else `PaperBroker`; the
  `bindings.py` default routes through it.
- **No contract change** (`contracts/execution.py` untouched); **no new dependency** (stdlib
  `urllib`/`json` only).
- Existing execution/binding tests unchanged (keyless ⇒ PaperBroker); `make ci` green at/above floor
  100.00; import-linter kept; every touched/new module < 200L.

## Out of scope (explicit — flag, don't build)

- **Pending→filled reconciliation across sessions** (the async fill catch-up via a reconcile/monitor
  pass) — the headline follow-up.
- **A real DEP-BROKER probe** (submit a 1-share paper order through `AlpacaBroker`, confirm fill +
  idempotency, then cancel) — recommended next, in `probes/` not the unit gate.
- **Stage promotion to live** (`broker_shadow`/`live_*`) — `live_gate.py` already guards it; untouched.
- **`AlpacaDataSource`** (OHLCV failover feed) and the **`FailoverDataSource`** wrapper — data-side,
  separate sprints.
- **Sourcing the monitor's realized `pnl_cents` from the Alpaca account** (S43 source-of-truth question,
  memory `realized-pnl-sequencing`) — decide when S43 is planned.
- Editing `.env`/`.env.example` or any `infra/*` file (external-agent territory; flag env-name
  reconciliation in the handback instead).

## Handback report (paste into PR / reply)

- Confirm no contract change and no new dependency.
- The status/price mapping table you implemented; how `submit` distinguishes replay (duplicate key) from
  a fresh order, and how rejected vs pending are handled in `submit` vs `fills`.
- The settings alias outcome (did `AliasChoices` resolve the `.env` `ALPACA_*` names under the
  `EXECUTION_` prefix?) and any `ALPACA_ENDPOINT` reconciliation needed.
- Final line counts for every touched/new execution module; new coverage % and floor; total test count.

The planning agent reviews, merges to `main`, marks DEP-BROKER progress in `ledger.md`, and plans the
**real DEP-BROKER probe** + the **pending-fill reconciliation** follow-ups.
