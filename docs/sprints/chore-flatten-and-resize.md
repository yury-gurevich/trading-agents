<!-- Agent: planning | Role: chore handover -->
# Chore — Flatten the paper book, then resize for observation

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** none — **config-only, no code change** (see "Why this needs no code")
**Status:** SPEC — packaged 2026-08-07, awaiting operator go
**Version:** **no bump** — no package behaviour changes
**Effort:** S (two env-var moves, two runs, two restores)
**Decisions:** [DL-93](../design-log.md) sizing / cap / sell-policy — **this executes option A, unblocked** ·
[ADR-0017](../decisions/0017-exit-authority-alpha-proposes-risk-disposes.md) alpha proposes, risk disposes ·
[ADR-0018](../decisions/0018-decision-validity-same-session-or-dropped.md) same-session or dropped ·
[S161](sprint-161-pm-knows-what-it-paid.md) the account-backed cash gate · [S162](sprint-162-rejections-name-every-gate.md) the evidence that proves it binds

---

## Why this chore

**The pipeline is deadlocked and produces no selection decisions at all.** Measured 2026-08-07:

| Run | Approved |
| --- | --- |
| 2026-07-31 | 1 |
| 2026-08-03 | 0 |
| 2026-08-04 | 0 |
| 2026-08-05 | 0 |
| 2026-08-06 | 0 |
| test `sched-2026-07-17` | 0 |

**Last approval: 2026-07-31.** DL-93 states the object under test is the **selection process** — *can
the system predict?* — and that position size is not a variable we care about yet. The system is
currently generating **zero** decisions to score. The thing under test is starved.

### 🚨 DL-93 option A cannot work as written — this is new since the entry

Option A says: cut `max_position_pct`, raise `max_positions` 10 → 50–100. **After S161 that alone
changes nothing.** The slot cap stopped being the binding constraint:

```text
available_for_buys = equity x (1 - cash_buffer_pct) - deployed
                   = 103,149.91 x 0.95 - 203,740.91
                   = -105,748.50
```

`cash_available` fails **independently of how many slots exist**. S162's trace shows both gates
failing on the same order — that is precisely the evidence S162 was built to produce. For any buy to
pass, deployed must fall below **$97,992.41**, i.e. the book must shed **~$105,748 of $203,740 —
more than half**. Raising the cap to 100 leaves every buy rejected on cash.

Nothing sheds it on its own: ADR-0017 removed mechanical exits, so an exit needs an analyst `sell`,
and the analyst has returned `hold` on all ten holdings for days. **The state is stable and
self-sustaining.** Operator decision 2026-08-07: flatten the paper book, then resize.

---

## Why this needs no code (and no ADR reversal)

Two facts make this a **configuration** chore:

1. **The flatten uses the designed exit rail, not a bypass.** ADR-0017 §1 makes the analyst the sole
   author of discretionary exits via `sell if confidence < exit_confidence_floor else hold`
   ([`recommend.py:71`](../../agents/analyst/domain/recommend.py#L71)). Raising that floor above the
   highest held confidence makes every held name exit **through analyst → PM → execution** with full
   lineage. DL-93's road-not-taken explicitly rejected hand-fired orders because `EXEC-IDN-01` makes
   execution the sole broker interface and a hand order writes no lineage. This writes lineage.
2. **Every tunable is env-settable on the deployed app.** `AnalystSettings` declares
   `env_prefix="ANALYST_"` and `PortfolioManagerSettings` declares `env_prefix="PORTFOLIO_MANAGER_"`,
   so the values move with `az containerapp update --set-env-vars` — a config revision, not an image
   move. No branch, no `make ci`, no version bump.

`exit_confidence_floor`'s own `why` already calls it a *"deliberate ADR-0016 foundation-now
placeholder"* — moving it temporarily is using it as designed, not overriding a safety cap.

Held confidences to clear (from `sched-2026-08-06`): USB 0.71, WFC 0.69, BAC/BMY/MDT 0.64,
SCHW/HPE/CSCO 0.63, ABT 0.62, PYPL 0.59. **Max = 0.71.**

---

## 🎯 The resize numbers — and the trap in DL-93's own suggestion

DL-93 proposes `max_position_pct` 0.10 → **~0.005** (~$500 a pick) with 50–100 slots. **Do not use
0.005.** `size_quantity` floors to whole shares:

```text
quantity = floor(portfolio_value x max_position_pct / price)
```

At 0.005 of ~$103k the parcel is **~$515**, so **every share priced above $515 floors to 0** and is
rejected `below_min_quantity`. In the current 100-name universe that silently removes the expensive
names — **a systematic bias in exactly the measurement this chore exists to restore.** A selection
scorecard built on "only stocks under $515" is not measuring selection.

**Recommended instead:**

| Parameter | From | To | Why |
| --- | --- | --- | --- |
| `PORTFOLIO_MANAGER_MAX_POSITION_PCT` | 0.10 | **0.01** | ~$1,031 a parcel — clears all but a couple of names in the universe, so price bias is near-eliminated |
| `PORTFOLIO_MANAGER_MAX_POSITIONS` | 10 | **60** | 60 x $1,031 = **$61.9k** max deployed, comfortably under the **$98.0k** the cash gate allows at full equity |

Check the arithmetic against a flat account before committing: max deployed must stay below
`equity x (1 - cash_buffer_pct)`, or the chore re-creates the deadlock it just cleared. Whatever
numbers are chosen, **state the price-bias check** — how many universe names floor to 0 shares.

---

## 🪤 Traps

1. **Restore the exit floor, or everything exits forever.** Left high, the analyst sells every
   position on every subsequent run and the book can never hold anything. The restore is not
   optional cleanup — it is part of the operation. **Verify it, do not assume it.**
2. **Resting stops must not be orphaned.** S151 recorded **nine resting `gtc` stop orders** at
   Alpaca against these holdings. Selling the position while a stop rests can leave an order that
   opens a **short**. Confirm the stops are cancelled or dropped as the exits fill — `/reconcile-broker`
   before and after, and check `0 non-stop open orders` plus no unexpected `Position` rows.
3. **Fills are next-session, and this is a Friday.** Orders carry `time_in_force: "day"`
   ([`alpaca_orders.py:41`](../../agents/execution/alpaca_orders.py#L41)) and the run fires after the
   close, so sells queue to the **next session open** — Monday **2026-08-10 13:30 UTC**. Cash is not
   free until then, so the resize produces no buys before Monday's 22:30 UTC run. **Do not read
   Saturday's zero-approval run as failure.**
4. **ADR-0018 drops decisions that miss their session.** Watch for the drop sweep taking the queued
   sells; if it does, the flatten needs to run *inside* a session instead.
5. **Partial fills leave a partial deadlock.** The gate is all-or-nothing at the threshold: if only
   some sells fill, deployed may still exceed $97,992 and buys stay blocked. Re-measure
   `available_for_buys` after the fills rather than assuming the flatten completed.
6. **Env-var updates create a new revision.** Confirm the apps stay on `:s162` and keep
   `minReplicas=0` + one KEDA rule afterwards — the same check the S162 deploy made.

---

## Sequence

1. **Baseline** — record `available_for_buys`, deployed value, equity, the 10 holdings, and open
   broker orders (`/reconcile-broker`). This is the before-picture the closeout compares against.
2. **Set the exit floor high** on the analyst app: `ANALYST_EXIT_CONFIDENCE_FLOOR=0.99`.
3. **Fire one run** (widen the scale window per the dev-fleet norm, or let the 22:30 UTC scheduled
   run do it). Expect the analyst to emit **`sell` for all 10** held names, the PM to approve all 10
   as full exits — sells are never blocked by the cash gate or the slot cap — and execution to submit
   10 orders.
4. **Restore the exit floor immediately**: `ANALYST_EXIT_CONFIDENCE_FLOOR=0.50`. Verify.
5. **Wait for the fills** at the next session open, then re-measure: deployed ≈ 0, equity ≈ cash,
   `available_for_buys` strongly positive, `Position` rows reconciled to the broker, no orphan stops.
6. **Apply the resize** — `PORTFOLIO_MANAGER_MAX_POSITION_PCT=0.01`,
   `PORTFOLIO_MANAGER_MAX_POSITIONS=60`.
7. **Watch the first run after the fills** (Monday 22:30 UTC). **This is the success test.**
8. **Record** a `functionality-checks.md` row and update DL-93 from OPEN to the decision taken.

---

## Success factors (the definition of done)

- The analyst emits `sell` for **all 10** held names on the flatten run — not 9, not 2.
- The PM approves all 10 exits; execution submits 10 orders; **no order is a buy**.
- After fills: **0 open positions**, **0 resting stop orders**, no divergence `Flag`, and
  `available_for_buys` back above zero and consistent with equity.
- `exit_confidence_floor` **verified back at 0.50** before the next run.
- The first post-resize run approves **many** buys (target: tens, not one) with **zero**
  `insufficient_cash` and **zero** `max_positions` rejections — the deadlock provably cleared, shown
  by S162's gate reports naming which gates now pass.
- A stated price-bias measurement: how many of the 100 universe names floor to 0 shares at the chosen
  parcel size.

## Explicit non-goals

- **No code change, no version bump, no image move.** Config only.
- **No ADR-0017 reversal.** The flatten uses the analyst's existing discretionary-exit voice; it does
  not reintroduce mechanical exits (DL-93 option B stays not-taken).
- **No change to `cash_buffer_pct`** or any other gate — the point is to clear the deadlock, not to
  widen the gates until it disappears.
- **No graph teardown.** The existing lineage is real history and stays (contrast the S162 check,
  which tore down a synthetic run). The shadow book keeps its 163 recommendations.

## The road not taken (LAW-06)

- **Size against `buying_power`** — unblocks with no selling, but authorises leverage on an already
  2x book. S161 flagged this as an operator decision, and it makes the exposure worse rather than
  resetting it.
- **Reverse ADR-0017 and reintroduce mechanical loss exits** (DL-93 option B) — only two holdings are
  down (BMY -2.85%, MDT -0.69%), together **~$425** against the **~$105,748** that must be shed. It
  does not unblock anything on its own and reverses an accepted ADR to achieve almost nothing.
- **Reset the Alpaca paper account from the broker side** — faster, but writes no lineage and would
  strand the graph's `Position`/`Fill` rows against a broker that no longer agrees, manufacturing the
  DL-44 divergence the whole reconciliation design exists to prevent.
- **Raise `max_positions` only** — the original DL-93 option A. Measured to be a no-op while the cash
  gate binds; this chore exists because S162 made that provable rather than arguable.

---

## Closeout — evidence

**Baseline (before):**

**Flatten run — analyst sells / PM approvals / execution submits:**

**Exit floor restored and verified:**

**Fills, and the re-measured `available_for_buys`:**

**Broker reconciliation — positions, orphan stops, divergence flags:**

**Resize applied, with the price-bias measurement:**

**First post-resize run — approvals, and the gate reports that show the deadlock cleared:**

**Fleet config unchanged (tag, minReplicas, KEDA rules, cron):**

**Not met / verified failing:**
