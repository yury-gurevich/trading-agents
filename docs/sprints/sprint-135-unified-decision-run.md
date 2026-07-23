<!-- Agent: planning | Role: sprint record -->
# Sprint 135 — One run, one evidence set, both directions

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-135-unified-decision-run`
**Status:** ✅ shipped 2026-07-23 (0.74.00) — merged `1b858e7`, deployed `:s136`
**Effort:** M
**Decision:** [ADR-0016](../decisions/0016-one-run-one-evidence-both-directions.md) (amends ADR-0015)

---

## Why this sprint

Entries and exits were decided by two different systems on two different bodies of evidence. A
**buy** passed provider facts, analyst scoring against a regime floor, PM risk gates and an LLM
challenger-veto. A **sell** was three hardcoded numbers on the `Position` node — `stop_pct 0.05`,
`target_pct 0.10`, `horizon_days 14` — evaluated on prices alone, with no analyst, no PM, no debate.

The book showed the cost. The same names were re-recommended and re-bought nightly with nothing
ever trimmed:

```text
BAC   171 -> 338 -> 503 shares
USB   160 -> 320 -> 478
WFC   116 -> 233 -> 348
```

until `regt_buying_power` reached **0** and every order after that was rejected. A four-name
accumulator is not a portfolio, and no amount of exit *plumbing* fixes a system that never
reconsiders what it holds.

Found the same day: DL-58 (close orders carried no quantity or price), DL-59 (acceptance scored
intent, not outcome), DL-60 (no graph-pull path carried a close to execution at all).

## What shipped

- The analyst scores **scanner survivors ∪ open held positions** in one cycle against the same
  `MarketData` snapshot and regime. Held names **bypass the scanner** — its filters are
  entry-selection criteria, not reasons to hold or exit.
- The analyst emits **buy / hold / sell**. The `held` branch returns *before* the buy path is
  reachable, so a held name can only hold or sell — anti-pyramiding is **structural**, not a
  convention a future edit can quietly break.
- The exit rule is a deliberately conservative `tunable()` — `exit_confidence_floor 0.50` against a
  0.60 entry floor — with a `why=` marking it an ADR-0016 *foundation-now* placeholder. No
  trailing/MAE/MFE/trim heuristics: strategy is explicitly later work.
- The PM sizes both directions into **one `OrderIntentSet`**; sells ride the existing rail as
  `OrderIntent(action="sell")` → `_broker_side`. **No second dispatch path was built** — DL-60's
  missing consumer became moot rather than implemented.
- Held-position reading moved to `contracts/positions.py`; `monitor/position_book.py` now delegates
  to it instead of keeping a second copy that could drift.
- Conservation: `analyst.scored <= scanner.survived` was false by construction and would have
  FAILed every run. It is now `survived + analyst.held`, with `held` exposed on the analyst stage
  view. Runs predating this carry no `held_count`, so the bound degrades to the old one.

## Closeout — evidence

**Gate (verified independently of the agent that wrote the code).** `make ci` exit 0, 9/9 steps,
**1748 passed, 6 skipped, 100.00% coverage**, import-linter `4 kept, 0 broken`, live `pip-audit`
clean. Remote gate green on the branch before merge: `quality` / `test` / `security` / `gate`.

**Deploy.** All 14 targets on `:s136` from `1b858e7`; `DeployRecord
deploy:2026-07-23T06:32:50Z:s136:1b858e7…` written after verifying the tag, not inferred.

**Functionality check (register row 2026-07-23).** The decisive result:

```text
*** SELL ORDERS EVER: 1 ***
   ABT qty=98 type=market status=accepted id=fc7f075f created=2026-07-23T07:28:35Z
```

The first sell order in the system's history. Chain on real infrastructure, run `check-s136-sell`
(7/7): analyst `ABT sell conf=0.62` → PM `approved=2` with `ABT sell qty=98` **and**
`SCHW buy qty=99` in one `OrderIntentSet` → execution `submitted=1`, order accepted at Alpaca.
`qty=98` matched the real held quantity — the retired `close_quantity=1` fixture would have sold
one share (DL-58). Acceptance returned **`UNPROVEN`**, correctly refusing to call a queued order a
pass (DL-59).

Run `check-s136-clean` (7/7) proved the other half: `USB/PYPL/BAC/WFC/ABT/HPE/MRVL` all returned
`hold` and the PM skipped every one with `hold_recommendation`, approving only the genuine new
candidate. **The nightly accumulator is stopped.**

**Honest caveats.**

- The sell required forcing `ANALYST_EXIT_CONFIDENCE_FLOOR=0.625` (above ABT's 0.62, below WFC's
  0.63) because no held name fell below the conservative 0.50 default. The **rail** is proven; the
  **strategy** that decides when to use it is still the agreed placeholder. Override removed and
  verified after the check.
- **The monitor's own stop/target closes are still undispatched.** `check-s136-clean` decided
  `HPE target` and `MRVL stop`; both stranded, taking the stranded count to four (AMD, CSCO, HPE,
  MRVL). Each such decision permanently removes a position from view because `is_open_position`
  excludes anything with a `CLOSES` edge. This is ADR-0015's fill-keyed closure — designed, not
  built — and it is the top follow-up.
- `regt_buying_power` remains 0 until the ABT sell fills at the next open.

## Next

1. **ADR-0015 implementation** — fill-keyed closure, position-derived idempotency key
   (`close:{position_id}`; the current monitor-run-scoped key would place a fresh sell nightly),
   broker-native `bracket`/`oco` stops, bounded retry then escalate, partial-fill semantics.
2. Recompute or invalidate realized PnL wherever a decision-time `pnl_cents` was booked without a
   fill (AMD carries −$1,530.65 against a position that is +$1,277 unrealized).
3. Exit strategy proper, as a champion–challenger against the mechanical rules — only once real
   exits have accumulated a baseline to challenge.
