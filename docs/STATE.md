# Project State

**Last updated:** 2026-07-30 15:20 AEST · **Version:** 0.83.00 · **🟢 S148 IS DEPLOYED — ADR-0018 is now live.** Fleet retagged `:s147` → **`:s148`** at 2026-07-30 05:08 UTC (14/14 `Succeeded`, 13 apps + `dispatcher-cron` verified on tag, env intact at `minReplicas=0`, `DeployRecord …:s148:e8bcca1` written after verification). Tonight's run is the **first live test of bounded same-session orders and the drop sweep** — expect roughly **3 in 10 decisions to drop** (measured: 50 bps refuses 35 % of buys, 23 % of sells) and treat that as the ADR working, not a defect. The first thing to check is the drop rate; the second is that all nine resting stops survived the sweep. · **🟡 S150 PACKAGED — the stop distance is flat across the whole book, and that is worse than the tolerance was** ([sprint-150](sprints/sprint-150-volatility-scaled-stops.md), feat → 0.84.00, depends on S149 merging first). Measured over ~65 sessions: a flat 5 % stop is touched on **0 % of days for BAC and 39.4 % for MRVL**, because on an 8.5 %-ATR name 5 % sits *inside* one day's normal range — 0.6 ATRs, versus 2.4 ATRs for BAC. A 2 × ATR stop equalises the book at 0–3 %. 🚨 **The trap named in the handover:** the reward-risk gate is `target_pct / stop_pct` and the target is flat too, so widening stops alone would make AMD/MRVL/HPE **silently stop passing the gate** — no error, no fault, just approvals ceasing. An honest check that MRVL's 07-27 forced stop was a noise stop-out **failed**: it kept falling to 16.6 % below the exit, so that stop was correct. [DL-77](design-log.md). · **🟢 S149 MERGED** (`v0.83.00`, [sprint-149](sprints/sprint-149-volatility-scaled-tolerance.md), 0.83.00, tip `1b471c4`, CI `30512736642` + Security Findings `30512736663` green, `make ci` re-verified independently at 1949 passed / 100.00%). Merged into `main` 2026-07-30 after independent verification; **not deployed** — fleet stays `:s148` so S148's live drop rate is measured against one variable, not two. Challenger ships **off**; `atr_multiplier=0.50`, floor 25 bps, ceiling 250 bps. **DRIFT-027 opened — the fourth consecutive sprint** to find execution's LOCKED constitution behind its code (024/025/026/027). **Found in review:** S149 extended the kernel vocabulary guard to enforce declared node *properties* (currently `Fill` only, 45 props). The static completeness suite proves labels, edge types and edge signatures are supersets of what the code can write — **it does not yet do that for properties**, which is S144's trailing-indicator lesson one level down. Not biting today because the guard is off, but it makes **enabling S144 a bigger step than S144 was scoped for**: extend the completeness scan to properties first. · · **🟢 THE EXIT-REPLAY OUTAGE IS FULLY CLOSED.** `sched-2026-07-27` — the run that crash-looped for two hours — now scores **`ACCEPTANCE PASS`**, which was S145's last outstanding success factor. `confirm-s146-20260728` is **PASS**; last night's `sched-2026-07-28` ran **7/7** on `:s146`. **S146 shipped, deployed, proven** (0.80.03, merged `7b06662`, `v0.80.03`, fleet retagged `:s145` → `:s146`, 14/14 verified on tag, `DeployRecord …:s146:7b06662` written after verification). **S145's completed-exit skip fired in production for real** — `CompletedExitReplaySkipped … AMD position_ref=22d71d0d3acc0586` — the exact defect that bricked the fleet, provably contained on a live scheduled run. **ABT's missing stop was never a code bug:** Alpaca refuses it as a wash trade (`code 40310000`, `"opposite side market/stop order exists"`) against `fd1f1c2c` — the **ABT buy orphaned by the 07-27 crash**. S145's orphan and S146's unprotected position were the same event two hops apart. What S146 fixed is the **silence**: the refusal is now retried every run and re-surfaced as an `UnprotectedPosition` Fault, where before it was recorded once and forgotten. · **🔴 ADR-0018 DECIDED (2026-07-29) — the largest measured cost in the system.** Every order is a market order submitted after the close and filled at the next open, at a price nobody evaluated: **≈ −$2,850 across two exits** (MRVL −$1,330.12; AMD −$3,515.60, of which **≈ −$1,515 is pure overnight gap** — decided at `est $494.90`, filled at `$467.35`). [ADR-0018](decisions/0018-decision-validity-same-session-or-dropped.md) closes it: **a decision is valid for one session — fill it or drop it.** Bounded price tolerance, cancel-unfilled at session end, dropped decisions recorded as a visible `Fault`, **resting broker stops exempt** (they are risk instruments, not decisions). S148 is the active build. · **✅ RESOLVED 2026-07-30 — the two unprotected positions now carry stops.** This entry previously read *"TWO POSITIONS STILL CARRY NO STOP — ABT 191 sh and MDT 118 sh"* and recorded that my 07-28 prediction had **not** been met. Kept as a correction rather than deleted, because the diagnosis it forced is what fixed it: the position book was never at fault (9/9 matching the broker); the cause was the **same stale-book ordering defect S147 fixes, one stage further down** — `place_broker_stops` runs at stage 5 off a book the monitor only heals at stage 6, so it saw ABT 96 against a broker holding 191 and the quantity guard skipped it. The `:s147` head sync closed that gap and ABT's stop went on at the first run. MDT cleared separately when its blocking buy filled. **Verified live 2026-07-30: nine held, nine stops, zero unprotected.** · **⬜ DRIFT-024 open / ⬜ DRIFT-026 open** — execution's LOCKED constitution still needs a later law amendment for broker-stop state/fallback parameter and for ADR-0018's bounded-order tolerance/drop semantics. · **📁 Detail for the S128–S146 arc — the outage narrative, S144's scheduled outage caught before it fired, Opus 5 at max effort, the 07-24 loop closing, the hardening run — moved to [state-archive/STATE-06.md](state-archive/STATE-06.md)** on 2026-07-29, when this line had reached 17,904 characters.

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + [`state-archive/`](state-archive/INDEX.md) `STATE-01…06.md` + git). **LAW-02:** an item is "shipped" only when
its success factors are *proven* (tests, `make ci`, the named live check) — never restate intent as outcome.

---

## Current focus

Since P14 the project runs as **etalon-first continuous improvement** (DL-19).
**The platform is self-driving in paper mode**: the DEPLOYED, STANDING fleet (13 Container Apps +
`dispatcher-cron` job, KEDA scale-to-zero windows, idle ≈ $0) places a calendar-gated `RunRequest`
at 22:30 UTC daily, runs graph-pull + served-over-Service-Bus on the Neon Postgres spine (ADR-0014),
reconciles holdings against the broker (DL-44), debates vetoes under compiled prompts (DL-42), and
proves `ACCEPTANCE PASS`. Pausing = disable the job + zero the scale windows (`docs/deployment.md`).
Completed arcs live in their sprint docs + archives: fleet (DL-35), credentials (DL-36), Postgres
migration (DL-43), deliberation quality (DL-41/42). Layer-3 acceptance 🟩 at the full S&P-500;
Layer-2 choreography 🟩 on a distributed run (S102).

## Recent (most recent first — detail in each sprint doc)

- **The write guard was undeployable, and its pack was a trailing indicator (feat, 0.80.00,
  2026-07-27 — DL-68).** S143 shipped the vocabulary guard unset. Enabling it was two defects deep.
  **(1)** `GRAPH_VOCABULARY_PATH` names a file and **no image copies `orchestration/packs/`** —
  setting it would have raised `FileNotFoundError` at boot, not enabled a guard. Added
  `GRAPH_VOCABULARY_B64`, resolved first, path kept for local dev; injected for master, all 13
  agents and the dispatcher by `deploy-agents.ps1`. This is the shape the master already used for
  grants and the secret map (S86/DL-12) — S143 invented a weaker one instead of following the
  precedent in the same repo. **(2)** The pack came from **observed** writes, so it could not cover
  code that had never run. ADR-0015 §3 stops merged Friday having never placed one, and both its
  edges were undeclared — labels and edge types declared, **signatures** missing — so enabling the
  guard would have raised `VocabularyError` on tonight's first real stop and destroyed the pending
  proof. Now checked two ways because neither suffices alone: static recovery
  (`scripts/vocabulary_{coverage,signatures}.py`) reaches `Fill -STOPS_WITH-> BrokerStopOrder`;
  `Position -PROTECTED_BY-> BrokerStopOrder` resolves via a dict lookup and is reachable **only** by
  executing the path, so the e2e test now runs `place_stop` under a guarded store. Static also found
  `Experiment -PROPOSES-> ParamChange` undeclared. Invariant `graph-vocabulary-injected-at-deploy`
  added (self-test 14/14). Its own first run produced a **false positive** from flow-insensitive
  resolution (`Rejection -EMITTED_BY-> PMRun`; the PM rebinds `node`) — fixed by binding to the
  nearest assignment *above* the call. Worth recording because the tempting fix, unioning the
  bindings, would have pushed fiction into the pack to make the check pass. `make ci` **1851 passed
  / 100.00%**, four remote gates green before merge (`d215a76`). **Functionality check PROVEN** on
  the live Neon spine, base64 only: `GuardedGraphStore` over **`PostgresGraphStore`** (asserted),
  undeclared label rejected with **0 rows written**, both stop signatures accepted, live
  `BrokerStopOrder`=0 / Position=21. **Fleet deliberately NOT enabled** — `:s143` predates the code
  and tonight's run outranks the guard; enablement is a dated action and **S144 stays open** until
  it lands.
- **Opus 5 at max effort — the reasoning knob was inert (feat, 0.78.00, 2026-07-27 — DL-63).**
  Every Anthropic call sent `model`/`max_tokens` only, so `output_config` never left the process
  and reasoning depth sat at the API default. Wired through all three adapters — the operator's
  tool-use client, the deliberation debate, the remediation gate — with `max` as the default rung
  and `ANTHROPIC_EFFORT` as the script-side override. `effort` is a `Literal` over the API's own
  ladder, so a bad override fails on load rather than as a 400 mid-run. Two traps surfaced:
  `max_tokens=512` is a **truncation trap** once effort drives thinking (thinking and structured
  output share the ceiling → the parse returns `refused`), raised to 4096 (OPR-PERF-01); and
  **a container reads no `.env`** — it gets `os.environ` from the master's ACTIVATE payload, which
  `trading_secrets.json` fills with credentials only, so the **code default is the fleet's effective
  value** (DL-63, verified live on the operator app). Defaults moved `claude-sonnet-4-6` →
  `claude-opus-5` in code. `claude-opus-5` priced into `llm_pricing.json` ($5/$25 per MTok) — an
  unpriced model would silently distort the LLMCall ledger. `make ci` **1823 passed / 100.00%**,
  all four remote gate jobs green before merge, fleet retagged **14/14 → `:s143`** (`818e7a9`),
  `DeployRecord …:s143:818e7a9` written. **Functionality check PROVEN** (2026-07-27): a real debate
  ran on `claude-opus-5` — no 400 on `output_config`, substantive turns, `REVISE` verdict. Scope it
  honestly: that proves the *script-side* adapter; the operator agent's tool-use client is deployed
  but **not yet exercised live**.
- **Broker-native stops — the durable floor (feat, 0.77.00, 2026-07-25 — ADR-0015 §3 / DL-61).**
  The stop moves from the once-a-night analyst rail to a **resting `gtc` sell stop at the broker**
  for every held position — continuous, not re-decided daily. **Stop-only** (no take-profit leg —
  ADR-0017 retired `target`). The S137 analyst forced-stop **degrades to a gated fallback**: it
  fires only when a position has no live broker stop, so the two never double-sell. Append-only
  safe (`BrokerStopOrder` immutable fact + `cancelled_at` marker; broker is truth for liveness,
  DL-44); a stop fill rides the **existing** reconciliation + 0.75.00 realized-PnL — no new closure
  path. The one unproven §3 assumption — after-hours `gtc` stops rest — was **probed PASSED**
  (2026-07-25). Implemented by codex, verified independently: `make ci` **1809 passed / 100.00%**,
  all four remote gate jobs green, fleet retagged **14/14 → `:s142`** (`ca57fff`), `DeployRecord
  …:s142:ca57fff` written. **Functionality check PENDING** the next 22:30 UTC run — watch for a
  real `BrokerStopOrder` placed at Alpaca for a held name and the analyst deferring to it. *(A
  scripting error of mine emptied the 12 new files mid-verify; recovered via codex re-emit and
  re-verified. Root cause: a wrong "repo is CRLF" memory — the repo is **LF**; now corrected.)*
- **Exit authority: alpha proposes, risk disposes (feat, 0.76.00, 2026-07-24 — ADR-0017).** The
  question the closure work surfaced — *when the monitor's mechanical exit and the analyst's
  thesis disagree, which wins?* — is now settled and built. The analyst is the **sole
  discretionary exit author**; a **breached stop is forced onto the same rail regardless of
  confidence** (`decide(held=True)` short-circuits to a `sell` with `exit_trigger="stop"` before
  the thesis check — alpha cannot veto risk on the downside); the monitor **stops authoring exit
  decisions** and instead raises a `Fault` when a stop is breached-but-unsold (DL-57 visibility);
  `target`/`time` retire into deferred strategy; the dead `order_from_close`/`execute_close` path
  is removed (one rail, DL-60). Stop arithmetic moved to `contracts/stop_rule.py` (agents never
  import agents); `contracts/positions.open_position_stop_thresholds` does quantity-weighted-avg
  entry and **raises rather than guesses** if lots disagree on `stop_pct`. Built by codex
  (xhigh), verified independently: **`make ci` 1786 passed / 100.00%**, EOL churn on 4 files
  restored to CRLF, all four remote gate jobs green before merge, fleet retagged **14/14 → `:s141`**
  (`29a36f4`), `DeployRecord …:s141:29a36f4` written. **Functionality check PROVEN**
  (`sched-2026-07-24`): first-ever forced stop — `MRVL exit_trigger='stop'` at conf 0.637 >
  0.5 floor overrode a hold thesis; monitor silent (`closes=0`) and raised the breach Fault;
  sell reached the broker (`submitted=3`), fill queued for the open. Durable stop stays
  broker-native (ADR-0015 §3, still open).
- **Realized PnL belongs to a fill + the ledger repaired (fix, 0.74.03, 2026-07-24).** The monitor
  computed `pnl_cents` at **decision** time, so profit factor and expectancy rested on trades that
  never happened. The monitor no longer writes it; the reporter skips anything marked
  `pnl_invalidated_at`; and — the DL-57 lesson again — `collect_trade_outcomes` now **omits**
  `profit_factor`/`expectancy_cents` when there is no evidence instead of emitting a confident
  `0.0`. `scripts/repair_close_pnl.py` **appends** markers rather than rewriting history (the store
  is append-only, and the wrong number staying visible-but-marked is the better audit trail).
  **Applied to production:** 7 of 7 entries marked, `manual_review=0`, `pnl_cents` preserved, re-run
  a no-op (`skipped_invalidated=7`), reporter now returns `{closed_trades_with_pnl: 0.0}`.
  `make ci` 1762 passed / 100.00%. Fleet **`:s139`** (`9a8a88c`), `DeployRecord` written.
- **Live proof of evidence-based closure (2026-07-24, run `check-s138-unstrand` on `:s138`).** 7/7.
  Analyst **`scored=10`** — **AMD, CSCO, HPE, MRVL evaluated for the first time since 07-20**; PM
  `approved=1`, all 9 held names skipped `hold_recommendation`; execution `submitted=1 rejected=0`.
  **ABT closed by evidence** (`broker_absent=True`, sell Fill `broker_status=filled`), leaving graph
  holdings an exact match to Alpaca. **Three closes decided — nothing stranded.** Acceptance
  `UNPROVEN` (queued for the open). Windows restored and verified.

- **Evidence-based position closure — the stranding root cause (fix, 0.74.02, 2026-07-23).**
  `_is_open_position` removed a position from the book the moment a `CloseDecision` existed. A
  decision is **intent, not evidence** — and because the monitor's closes reach no broker, four
  positions still held at Alpaca (AMD, CSCO, HPE, MRVL) became invisible to every future run:
  unscoreable, unexitable, unreconcilable, with each run stranding more. The correct mechanism
  already sat beside it: `reconcile_positions_from_latest_snapshot` marks a Position
  `broker_absent` when its ticker leaves the broker holdings (DL-44 — the broker is truth for
  holdings). Decision-based exclusion **deleted**; `monitor/store.is_open_position`,
  `surfaces/queries/positions.py` and `execution/reconciliation_store.py` now share **one**
  closure predicate so they cannot drift. **PROVEN against the live graph:** held tickers read
  `ABT, AMD, BAC, CSCO, HPE, MRVL, PYPL, USB, WFC` — all nine, exactly matching Alpaca; the four
  stranded positions are back. `make ci` 9/9, **1755 passed, 100.00% coverage**, verified
  independently of the agent that wrote it; all four remote gate jobs green before merge.
  **ADR-0015 §2 corrected, not implemented:** "merge re-decisions into one position-keyed node
  carrying the latest `run_id`" is **not representable** — `kernel/graph_support.py` is
  append-only and refuses to overwrite a property. In an append-only store a re-decided exit is
  a new fact, so the `CloseDecision` key stays run-scoped. Also folds in the `status.ps1` fixes
  (replicas counted in PowerShell; a failed probe prints `?` not `0`; wake window with
  awake/asleep; named columns; all **14** deploy targets counted).
- **Exit orders keyed on the position, not the run (fix, 0.74.01, 2026-07-23).** With sells
  finally reaching the broker, `order_from_intent`'s run-scoped key was an **oversell hazard**:
  `run_id` is new every night and becomes Alpaca's `client_order_id`, so an unfilled sell would
  be re-submitted as a *second distinct order* the next night, and a third after that. Sells now
  key on `f"exit:{position_ref}:{ticker}:sell"`, a sha256 of the sorted open `Position` node
  keys — unchanged holding replays instead of duplicating, and a partial fill or re-entry
  changes the node keys and correctly re-attempts the remainder (ADR-0015 §5 falling out of the
  key). Buys keep their run-scoped key, asserted byte-for-byte. `make ci` 1752 passed, 100%.

- **S135 — one run, one evidence set, both directions (0.74.00, 2026-07-23) — THE SELL SIDE FINALLY
  EXECUTED.** Entries and exits were decided by two systems on two bodies of evidence: a buy passed
  provider facts + analyst scoring + PM gates + an LLM veto; a sell was three hardcoded numbers on
  prices alone. The book showed the cost — BAC 171→338→503, USB 160→320→478, WFC 116→233→348,
  re-bought nightly, never trimmed, until `regt_buying_power` hit 0. **Shipped (ADR-0016):** the
  analyst scores scanner survivors ∪ open held positions on the same snapshot/regime (held names
  bypass the scanner, whose filters are entry-selection criteria) and emits buy/hold/sell — the
  `held` branch returns *before* the buy path is reachable, so anti-pyramiding is **structural**;
  the PM sizes both directions into one `OrderIntentSet`; sells ride the **existing buy rail**, so
  **DL-60's missing close-dispatch became moot rather than built**. Held-position reading moved to
  `contracts/positions.py` with `monitor/position_book.py` delegating (no second copy to drift).
  Conservation became `analyst.scored <= scanner.survived + analyst.held`; older runs carry no
  `held_count` so the bound degrades and no history breaks. **PROVEN:** `make ci` 9/9 exit 0,
  **1748 passed, 100.00% coverage**, import-linter 4 kept/0 broken, live `pip-audit` clean —
  verified independently of the agent that wrote it; remote gate green on all four jobs before
  merge; fleet `:s136` from `1b858e7` with `DeployRecord` written after verification. **Live check
  (register 2026-07-23):** `check-s136-sell` 7/7 → **`ABT sell qty=98 type=market accepted
  id=fc7f075f`** — the first sell order in the system's history; `qty=98` matched the real held
  quantity, not the retired `close_quantity=1` fixture (DL-58); acceptance returned **`UNPROVEN`**,
  correctly refusing to call a queued order a pass (DL-59). `check-s136-clean` 7/7 proved the other
  half — all 7 held names `hold`, every one skipped `hold_recommendation`, only the genuine new
  candidate approved. **Teardown:** override removed (analyst env back to its 5 vars, secretRefs
  intact), KEDA windows restored to `22:30-00:30Z` and verified against backup, litter run torn
  down (9 edges/9 nodes); the two runs with real meaning retained — deleting the lineage of a live
  broker order would manufacture the exact DL-44 divergence we spent the day fixing. **NOT DONE:**
  ADR-0015 fill-keyed closure (stranded count now 4 and growing), realized-PnL repair where
  decision-time `pnl_cents` was booked without a fill, and exit strategy proper.
- **Status board fixed (chore, 2026-07-23) — A BROKEN PROBE READ AS A FACT.** `infra/status.ps1`
  showed `replicas=0` for the whole fleet while every app had a live replica: on Windows `az` is a
  `.cmd` shim, PowerShell strips the quotes, and `cmd` chokes on the parentheses in
  `--query 'length([])'` — exit 255 → `$null` → rendered `0`. Third instance of the DL-57 pattern in
  one day. Counting moved into PowerShell; a failed probe now prints **`?`**, never `0`; and the
  board gained the **wake window** with `awake`/`asleep`, so a legitimate scale-to-zero reads grey
  while `0 while awake` — the only genuinely broken case — reads red. Columns are now named and
  grouped: identity (`APP`) │ deployed (`DEPLOY`, `IMAGE`) │ running (`PODS`, `POWER`, `WAKE`).

- **Fleet on `s135` + the sell side proven still unbuilt (2026-07-23) — INTENT WAS NOT OUTCOME,
  AGAIN.** Deployed `s135` from `c7ccdb0` (all 14 targets, config intact, `DeployRecord` written),
  then widened the KEDA windows to fire a real run and **restored them, verified identical to
  backup** (master `25 22`, twelve agents `30 22`, all `end 30 00`). `sched-2026-07-23` ran
  **7/7** on the new images. **PROVEN WORKING:** the DL-58 `GraphFaultSink` — the first `Fault`
  nodes ever written (`provider returned no current price for HPE` / `MRVL`, so those two are
  silently skipped every run); and the DL-59 gate, which returned **`UNPROVEN`** on the live run
  instead of a false PASS. **PROVEN FAILING:** the monitor decided `CloseDecision CSCO close
  trigger=time` and the broker's lifetime sell count stayed at **0**, with **no fault recorded**
  — nothing was attempted. Root cause (DL-60): `dispatch_closes` exists only on the **bus RPC**
  path; the deployed **graph-pull** path writes the decision and stops, and execution's poll
  handles `PMRun` buys only. **There is no graph-pull consumer for close decisions anywhere — the
  sell side is unbuilt, not broken.** DL-58's fix was necessary but insufficient: it corrected the
  payload of a message nothing sends. Design note **DL-60** written (lifecycle: a position is
  closed by a **fill**, not a decision — decision-time `CLOSES` is what stranded AMD forever, and
  decision-time `pnl_cents` books realized PnL at a price nobody traded at). **Blocked on
  operator:** exit timing (a once-daily after-hours stop executes at the next open) and AMD
  recovery. 5 more unfillable buys cancelled; `regt_buying_power` still 0.

- **Acceptance scores outcome, not intent (fix, 0.73.02, 2026-07-23) — THE GATE COULD NOT SEE
  TWO DEAD DAYS.** DL-58's named limit, closed. The gate's boundaries were all *conservation*
  checks, and `execution.submitted` is an **intent count** — it says orders reached the broker,
  never that the broker did anything with them. So 07-21 (all five orders rejected at the open,
  `regt_buying_power=0`) and 07-22 (five more against zero buying power) both scored
  `ACCEPTANCE PASS`. **Fix (DL-59):** `FillOutcomes` classifies a run's Fill nodes by real broker
  outcome (`broker_status` overrides submit-time `status`), and a fourth verdict **`UNPROVEN`**
  names the third state — filled → PASS, all resolved unfilled → **FAIL**, still queued →
  UNPROVEN (exit 0, never rendered as PASS). Counted from Fill nodes, **not**
  `ExecutionRun.submitted`: a broker refusing at submit time leaves `submitted=0`, so scoring
  intent would pass exactly that run. Dashboard: UNPROVEN stays **GREEN + warning row**
  (a nightly false RED trains the operator to ignore the light — DL-47), summary "N orders
  placed, none filled yet"; a real fault is still RED. **Proven:** `make ci` exit 0, 9/9,
  1737 passed, 100.00% coverage; end-to-end test drives a rejecting broker and asserts FAIL with
  `submitted=0, orders=2, unfilled=2` proving intent ≠ outcome; **replayed on the three real
  runs — 07-20 `PASS`, 07-21 `FAIL` ("0 of 5 submitted orders filled … the run traded
  nothing"), 07-22 `UNPROVEN`.** **Named limit:** proves *whether* orders filled, not *how well*
  (slippage/partials unscored); and a run stays UNPROVEN until acceptance is re-run after the
  open, which nothing yet does automatically.

- **Exit path made executable + faults made visible (fix, 0.73.01, 2026-07-23) — THE STACK
  COULD ONLY BUY.** A routine run review found `sched-2026-07-22` green (7/7, `ACCEPTANCE PASS`)
  while the system had been incapable of selling since inception: **zero sell orders in the
  broker's entire 33-order history.** The monitor stopped us out of AMD on 07-20
  (`CloseDecision`, `trigger=stop`, `pnl_cents=-153065`); no order ever reached Alpaca; we still
  held 55 shares. Two defects (DL-58): `CloseDecision` carried no quantity or price, so execution
  substituted `close_quantity=1` / `close_reference_price=$1.00` — tunables whose own `why=`
  admitted they were fixtures; and `dispatch_closes` swallowed failures into an in-process sink,
  so `surfaces/queries/faults.py` — the operator incident view — had been **empty by
  construction** and read as "no incidents". Buy-only execution then ratcheted the account to
  `regt_buying_power=0`; **all five orders on 07-21 were rejected at the open**, and 07-22
  submitted five more against zero buying power, both days scoring PASS. **Fix:** `CloseDecision`
  gains required `quantity` + `reference_price_cents` (contract 0.2.0 → 0.3.0), monitor
  populates both, `order_from_close` reads them, both fixture tunables **deleted**;
  `GraphFaultSink` appends a `Fault` node on all four graph-pull poll paths, keyed by
  origin+timestamp so recurrence appends. **Proven:** `make ci` exit 0, 9/9 steps, 1719 passed,
  100.00% coverage; a new test drives a 55-share stop end-to-end and asserts the broker saw
  55 shares at $94.00 (it saw 1 @ $1.00 before); a second asserts a swallowed dispatch failure
  lands as a queryable `Fault`. **Operator action taken:** the 5 unfillable 07-22 orders were
  cancelled at the broker (verified `canceled`, 0 open). **NOT fixed — named limit:** the
  acceptance gate still scores stage completion, not whether an order can fill, so it passed on
  two dead days; and **AMD (55 sh) is still held** against a 07-20 close decision — the code
  path is fixed, the stranded position is not yet resolved.

- **Gate self-test (chore, 0.73.00, 2026-07-22) — PROVING THE CHECKS CAN FAIL.** Three gates read
  green in one day while examining nothing: the security gate had run on **zero** sprint merges
  (DL-52), a STATE claim had no check able to contradict it (DL-54), and the secret sweep could not
  see new files (DL-55). Shared defect: *"didn't look"* rendered identical to *"looked and found
  nothing."* `scripts/gate_selftest.py` plants a violation per gate and requires a non-zero exit,
  and asserts the config facts whose loss silently disables a gate (the `push` triggers, the
  Makefile line wiring the untracked scan). Runs in CI `quality` on **every push** so it cannot rot.
  **Proven both directions at introduction:** 7/7 on a healthy tree; removing the `push` trigger —
  the exact DL-52 regression — made it exit 1 naming the invariant, and neutering a case to a
  command that always exits 0 made it exit 1 too. **Named limit:** it only tests failure modes
  someone imagined; it stops known blind spots regressing, it does not promise there are no new
  ones (DL-57).
- **Credential-delivery audit (chore, 0.72.00, 2026-07-22) — A CHECK THAT CAN CONTRADICT THE
  STATUS DOC.** Asked to apply the S131 Postgres flip, the audit-before-acting found it **already
  applied** — STATE had carried a false pending item for two days (DL-54). The real gap was that
  *no cheap check could disprove it*: a flip rewrites the secret's **value** while the env var name
  stays identical, so `preflight` and `az containerapp show` read the same before and after a flip
  **and after a rollback**. `scripts/cred_audit.py` reads the delivered value, reports the role it
  names, and connects as it — verdicts `scoped` / `scoped-degraded` / `shared` / `cross-wired` /
  `unreachable` / `missing`, `--strict` exits non-zero unless all 14 are scoped. **`cross-wired`
  (a target holding another agent's role) is a defect neither the flip script nor preflight could
  ever surface.** Live: **14/14 `scoped`**, `master` correctly `bus secretRef: none`; the negative
  run exited **1** — the check can fail, which is what makes the pass mean anything. 13 unit tests,
  `make ci` exit 0 @ 100 %. Runbook in `deployment.md`.
- **S133 — per-agent Service Bus SAS (0.71.07, 2026-07-22) — THE LAST SHARED CREDENTIAL IS
  CLOSED.** Every container held the same namespace-level `RootManage` connection string; now each
  of **13 bus targets** carries its own **entity-level topic SAS** with a Send/Listen split —
  **33 rules, `cap_violations={}`** (planner output reproduced independently at verify, matching
  the handback exactly). Azure's **12-rule cap** per namespace *and* per entity is what forced the
  per-topic model: 13 agents don't fit 12 namespace rules (DL-53). The grant matrix is **derived
  from source** (`scripts/sb_sas_plan.py` reads `serve_transport.py` + publish topics), not a
  hand-kept list that drifts. Delivery mirrors S131: per-target Key Vault secrets → Container Apps
  `secretRef`, `-UseSharedServiceBusDsn` rollback retained. **`master` was given no bus rights
  rather than an invented permission** — its Service Bus env is removed. Live proof: scoped
  Send/Listen served a request, an out-of-scope Send was **refused**, and revoking one rule locked
  out **only** that identity while the fleet stayed `Succeeded`; canary topics torn down to zero.
  **Backlog row I → Done, leaving no open hardening rows.** Verified at merge: `make ci` exit 0 @
  100 %, no key in the tree, and the credential-fallback path checked to **fail closed** (the
  per-target "primary" secret is itself a scoped grant, so a bundle miss cannot reach `RootManage`).
  *Honest limit:* proof used disposable canary topics, not a production container-origin run —
  that capture is an operator follow-up. Merged via PR #63 with the gate green (the PR requirement
  was reversed hours later — DL-56; the gate now runs on push to every branch).
- **Security-gate repair + backlog row L (chores on 0.71.06, 2026-07-22) — THE GATE THAT NEVER
  FIRED.** Investigating one red check on a Dependabot PR unwound five stacked defects: the
  `SECURITY_FINDINGS_TOKEN` was absent from the **Dependabot** secret store (separate from
  Actions, so it resolved empty); the replacement PAT lacked read access to the private toolset
  (403); the gate then flagged 6 error-level `py/undefined-export` alerts — all **false positives**
  from S131's PEP 562 lazy exports (CodeQL cannot follow `__getattr__`), dismissed with reason;
  **the gate is `pull_request`-triggered, so S131/S132/S134 — each merged directly with no PR —
  were never gated at all**; and `GITHUB_TOKEN` auto-merges fire no `push` workflows, so four
  dependency merges landed without rebuilding images (`:latest` stale and unscanned). Fixes: the
  gate was first made to fire by requiring PRs, **since replaced** by triggering it on push to every
  branch (DL-52 → **DL-56**: on a one-developer repo a PR buys no review, so the trigger was the
  only thing being bought); the whole investigation + named residual
  risk is **DL-52**, the 5-PR dependency backlog (frozen ~2.5 weeks) was drained, and setuptools
  was bumped for CVE-2026-59890 (not reachable — sdist/macOS-only — cleared for signal hygiene).
  **Row L Done:** the container entrypoint smoke went from provider-only to **all 12 agent
  images** — DRIFT-016/017/018 were the *same* defect three times ("unit gate hid it"). Verified
  by dispatch run `29904029290`: 14/14 jobs green and all 12 images printed the assertion,
  confirming the step *fired* rather than silently skipping. Merged `d54fd54` (PR #59).

- **S134 (assertion hardening, row K, 0.71.05→0.71.06) — ROW K CLOSED HONESTLY, IN THREE ROUNDS.**
  A planning verify gate ran between each round, and the first two did not pass it. R1 killed the
  alpaca money-parser bucket (39→7 named residuals) plus the PM gate/reward-risk/sector
  boundaries — but relabelled ~250 analyst math survivors "equivalent" using one template note
  repeated on all 274 rows, so it was **bounced**. R2 took the targeted analyst survivors
  **249→127** with a real per-module before/after table and honestly held row K at *Partial*
  rather than closing it. R3 forced **all 127** into an auditable per-mutant disposition —
  **107 killed, 12 individually justified equivalents, 8 named wording exclusions, 0 un-triaged**
  (`round-3-dispositions.csv`; the anti-template gate held — 20 non-killed rows, 20 *distinct*
  reasons). Scoped decision-engine kill-rate **79.87 % → 84.36 %** (5,678/6,731). Test+docs only:
  no production source, no `pragma` removed (81/81), mutmut stays manual. Planning re-ran
  `make ci` on the branch and on the merge result (1692 passed / 6 skipped / 100 %).
  **Merged `d831260`, tag `v0.71.06`** (GitHub CI + CodeQL + image build all green).

- **S132 (mutation testing, row G, 0.71.04→0.71.05) — TESTS THAT ASSERT, NOT JUST EXECUTE.**
  `mutmut` over the deterministic decision engines as a **manual periodic exercise, not a CI
  gate**: +94 mutants killed with cited tests, scoped kill-rate 78.47 % → 79.87 %. Survivors were
  dispositioned in a committed report rather than deleted. That report is what S134 then acted on —
  and the review of it found the "rainy day" parking had under-called ~130 genuinely killable
  survivors. Merged `15c23d6`, tag `v0.71.05`.

- **S131 (blast radius, rows I+J, 0.71.03→0.71.04) — 15 IDENTITIES INSTEAD OF ONE DSN.** Per-agent
  Postgres runtime identities: 15 `ta_<agent>` roles, per-role Key Vault DSNs, secret-backed
  Container Apps delivery, and a revocation canary; plus the dispatcher image slimmed to its
  measured 43/44-file import closure (row J). Live: role provisioning/flip/canary proven, a
  controlled `pg_stat_activity` audit saw all 15 roles. The Service Bus connection string remains
  the **last shared credential** → row I part 2 = S133. Merged `0ca7459`.

- **S130 (base image, row H / R005, 0.71.02→0.71.03) — ALL 14 IMAGES OFF DEBIAN.** Two-stage
  Docker Hardened Images (`dhi.io/python:3.13-dev` → `dhi.io/python:3.13`) with venv-carrying
  runtimes, and Trivy keeping HIGH/CRITICAL enforcement with `ignore-unfixed: true` while
  `.trivyignore` stays empty. Actionable findings dropped **22 → 0**; manual run `29681635979`
  built/pushed all 14 `s130-test` images through every Trivy gate. Merged `8aefe2a`.

- **S129 (fixpack + GitHub hardening, 0.71.01→0.71.02).** Quant-evidence persistence into
  Recommendation/veto context plus dashboard read-cache egress reduction; and the supply-chain
  lane: dependency review on PRs and Trivy container scanning, both SHA-pinned. Merged `3be1ee8`.

- **S128 (feed resilience, DRIFT-021, 0.71.00→0.71.01) — ONE 429 COSTS ONE TICKER, NOT THE FEED.**
  Per-request Finnhub pacing (55/min tunable budget) and per-ticker fault attribution across all
  four enrichment feeds, with durable attributed notes on the graph quality trace; the real rate
  limit was used as the fault injector. Live check PASSED (paced 99/99, zero degraded notes in
  7 min; unpaced runs showed per-ticker `:429` attribution with the majority kept). **This is the
  sprint that unblocked trading**: `sched-2026-07-20` then ran 7/7 ACCEPTANCE PASS with zero
  degraded feeds, flipping the chronic all-reject signature into 5 buys. Merged `09120b3`.

- **S127 (fixpack, 0.70.00→0.71.00) — FLAGS ARE ACTIONABLE; CURRENCY JUDGES THE TEMPLATE.**
  Backlog rows 4/9/10/11/12 in one sprint: per-flag "Acknowledge" through the audited operator
  `approve` command with the S125 confirm machinery (typed intent echoed verbatim; result is an
  appended `FlagResolution`); deterministic `approve <target>` routing normalizer + regression
  table (row 11); deploy currency judges the dispatcher by its *template* image with the last
  execution kept as evidence — a fresh retag now reads `current` immediately (row 12, proven
  live pre-fire: template `:s126`/execution `:s121` → `current`); verdict warnings deep-link to
  their evidence panels; the bus integration test skips without the azure extra. Live check
  acknowledged exactly one stale warn flag (`15bb3e29df185949`, pending 2→1); the one critical
  divergence flag remains for the operator. Evidence + 5 screenshots in
  `docs/reports/sprint-127-fixpack/`. **First sprint under the DL-48 contract — drift rule
  held (main unmoved at `a823763`), closeout + return notes arrived filled, nothing bounced.**
  Codex-built; planning review re-ran `make ci` (exit 0, 1584 passed / 5 skipped / 100%).
  Merged `32c73cc`.

Older sprints — **S102–S126 → [STATE-05.md](state-archive/STATE-05.md)** · S99–S118 + chores →
[STATE-04.md](state-archive/STATE-04.md) · S77–96 → [STATE-03.md](state-archive/STATE-03.md) · S37–76 →
[STATE-02.md](state-archive/STATE-02.md) · S36→P0 → [STATE-01.md](state-archive/STATE-01.md); full index
`docs/sprints/README.md`.

## Now

**🟢 S145 is SHIPPED, DEPLOYED, and PROVEN**
([sprint-145-exit-replay-append-safe](sprints/sprint-145-exit-replay-append-safe.md), 0.80.02,
`2c49f88`, [DL-71](design-log.md) option A): `make ci` **1856 passed / 100.00%**, remote CI +
Security Findings green on the merge tip, `Build and push agent images` green on `main`,
`v0.80.02` tagged, **fleet retagged `:s143` → `:s145`** (14/14 verified on tag, config intact,
`DeployRecord` written after verification), the **resumed run scored `7/7 stages complete`**
where it had crash-looped at 4/7, and a **full fresh cascade then scored `ACCEPTANCE PASS`**
(`confirm-s145-20260728`, 7/7). Execution wrote `submitted=2 rejected=0 skipped=1` on the resume
and `submitted=1 rejected=0` on the fresh run, adopted every existing order instead of duplicating
it, and created exactly **one** new broker order across both — SCHW's missing protective stop.
**The one item still open** is the realized outcome of `sched-2026-07-27` itself: its acceptance is
`UNPROVEN - completed` because AMD sell 55 and ABT buy 95 are queued for the 13:30 UTC open.
Re-run `accept.py --run-id sched-2026-07-27` after the open for the realized verdict.

**⬜ DL-73 — RETRACTED IN FULL the same day; the defect does not exist.** I audited `Position` nodes on `status == "open"`, which is **not** the active-position predicate. The real one is `contracts/positions.py::is_active_position_node`, which also excludes `broker_absent` **and `broker_superseded_by`** — and `reconcile.py` has always called `_mark_superseded` / `_mark_absent`. Re-audited correctly: **23 nodes, 9 active — exactly one per held ticker, every quantity matching the broker** (ABT 96/96, AMD 55/55, BAC 503/503, CSCO 177/177, HPE 229/229, PYPL 175/175, SCHW 196/196, USB 478/478, WFC 348/348). The 14 "phantoms" are a correct supersession chain (`BAC 171→338→503`, `USB 160→320→478`, `WFC 116→233→348`) plus two correctly `broker_absent`. The "unexplained mitigation" was my own measurement error: the PM sized AMD at 55 because the predicate filters superseded nodes, as designed. Two further claims from that audit are also withdrawn — the "3 fabricated rejections" are `rejected_broker_fill`'s documented `rejected:{key}` sentinel for pre-submit refusals (all three `HTTP Error 403: Forbidden`), and `canceled`→`rejected` is a deliberate four-value `BrokerStatus` contract that keeps the raw word in `reason`. **The lesson (kept, not deleted):** an audit that does not use the code's own predicates audits my assumptions, not the system. **What genuinely survived** is in [sprint-146](sprints/sprint-146-unprotected-position.md).

**🟢 S146 SHIPPED, DEPLOYED, PROVEN — and the cause is now known.** Merged `96dfa6f..7b06662` (0.80.03, `v0.80.03` tagged), fleet retagged **`:s145` → `:s146`** (14/14 `Succeeded`, 13 apps + `dispatcher-cron` verified on tag, env vars and `daily-agent-window` intact at `minReplicas=0`, `DeployRecord …:s146:7b06662` written after verification), and run `confirm-s146-20260728` scored **`RESULT 7/7 stages complete`** on the deployed code. **ABT's stop was never a code bug: Alpaca refuses it as a wash trade** — `code 40310000`, `"potential wash trade detected"`, `reject_reason: "opposite side market/stop order exists"`, `existing_order_id: fd1f1c2c…` — which is the **ABT buy 95 orphaned by the 07-27 crash**. S145's orphan and S146's unprotected position are the same event two hops apart. **What S146 actually fixed is the silence:** the refusal is now retried every run and re-surfaced as an `UnprotectedPosition` Fault — two exist, `08:05:23` (pre-deploy check) and **`09:45:02` (this run, on `:s146`)** — where previously the 403 was recorded once, days ago, and nothing ever retried. **No fabricated `BrokerStopOrder`** was written (still exactly 7, none ABT), and the PM's re-approved `AMD sell 55` **adopted the existing broker order rather than duplicating it** (AMD market sells at the broker: exactly 1). The **4 orphan PM-run fills are repaired** and present with real broker ids; the second `--apply` was idempotent. **DRIFT-024 opened** (law gap: execution's LOCKED constitution declares neither `BrokerStopOrder` state nor a fallback stop parameter, despite ADR-0015 §3 depending on both — the second sighting of S138's declaration debt after S144 caught the vocabulary half). **Still open, honestly:** ABT remains `held=96 stop_qty=0` and **stays that way while that buy order is open**. It should clear once the buy fills at the 13:30 UTC open and a subsequent run retries — that is the next thing to verify, not a claim.

**🟠 S147 IS PACKAGED — DL-71 option B, the last open half of the outage's root cause.**
[sprint-147-fresh-book-before-decision](sprints/sprint-147-fresh-book-before-decision.md) (feat →
**0.81.00**), handed to Codex under the [DL-74](design-log.md) law-first MUST RULE. **Every decision
this system makes is made against a book at least one full run old.** Broker truth arrives at stage
5 (`reconcile_run_start` writes a fresh `BrokerPositionSnapshot`), is adopted at stage 6
(`reconcile_positions_from_latest_snapshot` heals the `Position` book), and is consumed by the
analyst at stage 3 — *of the next run*. Across the 07-25/07-26 weekend skips that gap was **three
days**, which is why the analyst authored `MRVL sell` for a position that had already sold and
bricked the fleet. The fix is a **head-of-run position sync**, and its shape is decided by law
rather than preference: `MON-IDN-02` reserves `Position` writes to the monitor and `EXEC-IDN-01`
reserves the broker to execution, so it ships as **two agents in a new order** — execution refreshes
the snapshot, the monitor reconciles, and the analyst is simply not pending until both have
happened. Only the *triggers* move, so DL-71's ownership worry does not materialise. Carries a
**20-test plan** (each test named with the violation it must plant, DL-70) and the
`BROKER_RESUME_STAGES = frozenset(RESUME_STAGES[:5])` **index trap** — inserting a stage at the head
shifts every index, and getting it wrong stops the supervisor warning before a resume that really
does submit orders. **Complementary to ADR-0018, not an alternative:** ADR-0018 stops a stale
decision surviving the night; S147 stops it being made.

**PROVEN (LAW-02) — what the merge actually established.** One attempt = one immutable `Fill` node
with the broker `client_order_id` unchanged (the 0.74.01 oversell guard stands); a `filled` exit is
never re-issued and the skip is a visible `Fault`; a per-intent failure degrades to a per-intent
fault so one ticker cannot cost three stages (DRIFT-014 / S128 restated for order submission). Each
was observed **failing** on a planted violation first (DL-70), and all three were re-proven against
the live Neon spine with teardown to zero. Gate self-test 14/14.
**Those success factors are now all met** (2026-07-28): the fleet retag to `:s145`, the resumed run
at **7/7** with MRVL out of the book and SCHW carrying its stop, and both orphaned orders adopted
rather than fabricated. S144's dated vocabulary enablement remains sequenced after, and is still
open.

**🟢 S146 SHIPPED** — [sprint-146-unprotected-position](sprints/sprint-146-unprotected-position.md)
(0.80.03, merged `7b06662`, fleet `:s146`, `ACCEPTANCE PASS`). Its predecessor packet
(orphan-fill lineage, [DL-72](design-log.md)) was **superseded**: the two orphans it targeted healed
themselves on `:s145` exactly as DL-72 predicted, and the audit that followed found the real gap was
an unprotected position, not a lineage lie. It also ran the [DL-74](design-log.md) **law-first
trial** — the coding agent read the governing constitutions before writing code, recorded which
clauses bound each element, and surfaced **DRIFT-024** (a genuine law gap) *before* implementation.
Verdict recorded in the sprint doc: it changed the approach on 4 of 7 elements and found no
law/spec contradiction.

The hardening backlog has **no open rows** — S133 closed the last one. Other queued work is in
*Next*; the standing operator items below are the only other outstanding threads.

**Fleet:** standing on `:s145` (retagged and verified 2026-07-28 — all 13 apps + dispatcher on the
same tag, built from `fcd81a4`), self-driving in paper mode — the calendar-gated 22:30 UTC
`dispatcher-cron` fires nightly, KEDA scale-to-zero, idle ≈ $0. **It now fires into the fixed
execution agent; that the fix holds is unproven until the run completes.** **Both scoped-credential
flips are applied live** — Service Bus (S133) and Postgres (S131) — so the running fleet holds
per-agent identities on both. Verified end-to-end 2026-07-22: all 14 app-delivered DSNs connect as
their own `ta_*` role with the spine privileges, and all 13 bus targets carry scoped SAS
`secretRef`s. Shared credentials are retained, unused, for rollback only.

**Awaiting the operator (two standing items, none blocking):**

1. **Broker-divergence Flags (07-09 / 07-14 / 07-15)** still need acknowledgement — actionable
   from the dashboard since S127.
2. **Container-origin identity capture (S131 + S133, one errand)** — both sprints proved their
   scoped identities with controlled checks rather than by firing a production run out of hours
   (the honest, conservative call). During one live KEDA window, repeat the `pg_stat_activity`
   query *and* capture Service Bus sessions, to see both under real container origin.

**P12 sentiment scorecard-run** stays queued until roughly two weeks of clean-news nights
accumulate; the runway began 2026-07-20 and cannot be short-circuited.

**Standing principles (DL-19 etalon-first):** remaining gray law clauses go green with cited
tests; **every sprint ends with a real-environment functionality check**
([`laws/functionality-checks.md`](laws/functionality-checks.md)) plus teardown; each sprint or
chore lives in **its own worktree on its own branch**, and is **pushed and seen green on the
remote before it is merged locally** (DL-56 — no PR required; the `gate` now runs on push to every
branch, so pushing *is* the gate). Merge to `main` is the deploy trigger that rebuilds and pushes
agent images.

## Next

- **🔴 ADR-0018 — PACKAGED as [S148](sprints/sprint-148-decision-valid-one-session.md), handed to Codex
  2026-07-29** ([ADR-0018](decisions/0018-decision-validity-same-session-or-dropped.md), accepted 2026-07-29).
  **The largest measured cost in the system, and now a closed decision.** Every order today is a
  market order submitted after the close and filled at the next open, at a price nobody evaluated —
  **≈ −$2,850 across two exits** (MRVL −$1,330.12; AMD −$3,515.60, of which ≈ −$1,515 is the
  overnight gap). Ship: a bounded price tolerance around the decision price (a `tunable`, not a
  literal), cancel-unfilled at session end, dropped decisions recorded as a visible `Fault`
  (DL-57), and **resting broker stops exempt** — they are risk instruments, not decisions. Two
  consequences to build against rather than discover: ADR-0017's forced daily-rail stop becomes
  best-effort within tolerance, which makes S146's audit check `A2` (every held position carries a
  live stop) **load-bearing**; and the reporter must not read a dropped decision as a rejection or
  a loss. Second-order win: stale live orders stop existing, removing the wash-trade stop blocker
  and most of the orphan/adopt complexity S145 and S146 had to build.
- **S146 — SHIPPED** ([sprint-146](sprints/sprint-146-unprotected-position.md), 0.80.03, merged
  `7b06662`, fleet `:s146`, `ACCEPTANCE PASS`). Left open: **DRIFT-024** — execution's LOCKED
  constitution declares neither `BrokerStopOrder` state nor a fallback stop parameter despite
  ADR-0015 §3 depending on both. Second sighting of S138's declaration debt after S144 caught the
  vocabulary half; wants a law amendment, not another register row.
- **DL-71 option B — SHIPPED as [S147](sprints/sprint-147-fresh-book-before-decision.md) (0.81.00,
  merged `2989acb`), NOT YET DEPLOYED — the fleet still runs `:s146`.** *Priority corrected:* the
  2026-07-28 audit that appeared to raise its urgency was **wrong and is retracted** — using
  `is_active_position_node`, the position book is correct (one active node per held ticker, every
  quantity matching the broker). This stays worth doing for its original reason only. The
  broker snapshot is written by execution at stage 5, but the position book is only healed by the
  monitor at stage 6 — one full run later. That is why the analyst scored a nine-hour-stale book on
  07-27 and authored an exit for a position that had already sold. Deferred out of S145 because it
  reorders the cascade and moves position truth across DL-44's ownership line, which is not a change
  to make on top of a live outage. **Deferred, not rejected — and now smaller than it looked:**
  ADR-0018 drops unfilled orders at session end, which removes the *carried phantom intent* half of
  the hazard. What B still owns is the one-run reconciliation lag itself. Sequence it after
  ADR-0018, not before.
- **🟠 S144's dated fleet enablement — now unblocked and overdue.** Deferred through S145, S146
  and S147; a write-time guard that is never enabled protects nothing. Build + retag at `:s147`, then set
  `GRAPH_VOCABULARY_B64` and verify it on an agent's env. Sequenced *after* S145 and its resumed
  run: a new fail-closed write path does not go into a fleet that cannot execute. S144 stays OPEN.
- **`chore-wsl2-dev-env`** (packaged, branch pushed) — move the dev loop to WSL2 for
  native-ext4 `mutmut`/`pytest` and CI/prod parity; the 14 `.ps1` files stay and run under `pwsh`
  (verified on the operator's Ubuntu), so the real work is `.gitattributes` LF normalisation and
  a setup runbook. Must not overlap an in-flight sprint branch — the renormalise commit touches
  nearly every text file.
- **DL-50 — ADR-0007 amendment cycle:** the accepted ADR still names DockerHub while the pipeline
  ships to GHCR. Recorded as drift rather than silently rewritten; needs a proper amendment.
- **DL-46 option A** — a deploy step in CI remains the recorded end state, deferred not rejected
  (option C, the `DeployRecord` + currency judgement, shipped in S126).
- **Deliberation as a reasoning/competence source (DL-39, DIRECTION)** — the transcript's *why*,
  not the verdict, is the asset: grade whether the expert model reasons at senior-analyst level and
  learn which parameters carry the decision. Assembles DL-31 (`--score`) + DL-09 + ADR-0010/CI-2;
  needs a research item and a live runway before packaging. Companion **DL-40 (parked)**:
  literacy-tiered verdict explanations as a `surfaces/` renderer, ruling single-sourced.
- **Prompt-optimiser bake-off** — EvoPrompt / TextGrad behind the ADR-0010 `PromptOptimizer` port
  ([R003](research/textgrad/INDEX.md)), when prioritised. DL-42 shipped the compiled judge +
  challenger as live champions; defender stays hand-written.
- **Remaining DL-36 hardening** — destructive executors (`rotate-credential`,
  `recreate-instance`) stay human-manual until a provider-specific write path and an approval UI
  land.
- **Deferred behind a perfect etalon (DL-19):** CI-1..CI-6 (ADR-0013, S90–S95) · the bundle
  **generator** · the ADR-0010 reusable predictor registry/promotion (first instance landed in
  S107) · P13 cross-asset graph · the `contracts/` substrate/pack split.

## Pointers

Product `docs/PRD.md` · architecture `docs/architecture.md` · phases `docs/build-plan.md` · closed
decisions `docs/decisions/INDEX.md` · open threads `docs/design-log.md` · "does it work"
`docs/laws/{ledger,drift-register,functionality-checks}.md` · per-agent `agents/<name>/mission.md`.
