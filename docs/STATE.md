# Project State

**Last updated:** 2026-08-13 20:33 AEST · **Version:** 0.90.09 · **S174 is proven in production; S175 and S176 are merged and undeployed — the fleet sits two PATCHes behind on purpose, so `sched-2026-08-14` stays a clean single-variable readout for the 60 s peer timeout.**

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + [`state-archive/`](state-archive/INDEX.md) `STATE-01…07.md` + git). **LAW-02:** an item is "shipped" only when
its success factors are *proven* (tests, `make ci`, the named live check) — never restate intent as outcome.
**Size rules**, after this file reached 574 lines with a **112 KB header line**: keep it **under 200
lines**, and keep the header above to **three clauses — stamp, version, one headline**. Replace that
headline each session; never append a fourth. Oldest *Recent* entries split to the archive.

---

## Current focus

Since P14 the project runs as **etalon-first continuous improvement** (DL-19).
**The platform is self-driving in paper mode**: the DEPLOYED, STANDING fleet (16 Container Apps +
`dispatcher-cron` job, KEDA scale-to-zero windows, idle ≈ $0) places a calendar-gated `RunRequest`
at 22:30 UTC daily, runs graph-pull + served-over-Service-Bus on the Neon Postgres spine (ADR-0014),
reconciles holdings against the broker (DL-44), debates vetoes under compiled prompts (DL-42), and
proves `ACCEPTANCE PASS`. Pausing = disable the job + zero the scale windows (`docs/deployment.md`).
Completed arcs live in their sprint docs + archives: fleet (DL-35), credentials (DL-36), Postgres
migration (DL-43), deliberation quality (DL-41/42). Layer-3 acceptance 🟩 at the full S&P-500;
Layer-2 choreography 🟩 on a distributed run (S102).

## Recent (most recent first — detail in each sprint doc)

- **The deliberation constraint was measured, and one of its two free levers did not exist (fix,
  0.90.02, 2026-08-11 — DL-105).** Asked whether two Anthropic APIs fix the deliberator's scaling
  problem, the constraint was established first: 90 calls on `sched-2026-08-10`, span first→last
  **1,136 s**, sum of per-call latency **1,022 s** — **ratio 0.90**, so ninety per cent of the wall
  clock has exactly one call in flight. Serial end to end, proven rather than inferred. Cost is
  **$0.83 per run**, so the Batch API's 50 % is worth $0.41 — **wall clock is the scarce resource,
  not money.** That splits the answer rather than settling it: batching is the right substrate for an
  auditor (it *deletes* the grace window rather than optimising it) and useless for a gate, and the
  multi-agent session API is an ADR that reopens three locked decisions, not a sprint. 🚨 **Three
  adapter findings surfaced while checking, none of them looked for.** `effort` was assigned and
  never sent, so the tunable read as live and did nothing on the deployed `gpt-5.5` fleet —
  **fixed** (`0.90.02`: `reasoning_effort`, planted-failure proven at `KeyError`, `make ci` **2228
  passed / 4 skipped / 100.00 %**, gate proven on the full SHA). `effort="max"` with
  `max_tokens=4096` is a documented misconfiguration on Claude Opus 5 and a *candidate* contributor
  to the 56 % self-agreement — **still open**. Neither adapter uses prompt caching or structured
  outputs. 🪤 **The `effort` defect survived at 100 % coverage because the test asserted the stored
  attribute rather than what reached the wire** — the DL-97 shape again, and the reason the new test
  pins the request, not the object. Packaged
  [S172](sprints/sprint-172-independent-debates-run-independently.md) (concurrency) and
  [S173](sprints/sprint-173-a-verdict-must-be-reproducible.md) (verdict reproducibility on Batches).

Older sprints — **the S166→S171 veto arc (`0.89.07`–`0.90.01`) → [STATE-08.md](state-archive/STATE-08.md)**;
`0.89` and below → [STATE-07.md](state-archive/STATE-07.md); earlier arcs (S36→S146) in
[STATE-01…06](state-archive/INDEX.md). Full chronological list: `docs/sprints/README.md`.

## Now

**Read this first if you are picking the project up.** `main` is `0.90.09` at `71377f2e`, gate proven
and independently re-verified. The **fleet is on `s174` = `0.90.07`, two PATCHes behind, deliberately** —
S175 and S176 are both merged and both undeployed, waiting on one run.

**S174 — shipped, deployed, proven live (2026-08-13).** The deployed dispatcher wrote
`lookback_days=295` / `required_history_bars=200`; `MarketData` carried **98 tickers × 202 bars, 0
under 200** against 41 each the day before; real `Recommendation`s for AMD and XOM carry all five
core indicators with no `*_missing_bars`. `sma_distance_pct` and `ema_spread_pct` had **never once
computed in production** before that run. PM approved **8** buys against 1 on 08-11. 8/8 stages.
Evidence: [functionality-checks.md](laws/functionality-checks.md).

🚨 **That same run failed acceptance, and not on S174.** `debate_coverage 0.625 < 1.0`,
`failed_open_count 3 > 0`. `DELIBERATOR_EFFORT=high` moves the **tail**, not the median, past the
30 s `request_timeout_seconds`:

| run | n | median | p90 | max | > 30 s |
| --- | --- | --- | --- | --- | --- |
| `sched-2026-08-10` (pre-`effort` control) | 90 | 11.4 | 16.4 | **23.0** | **0** |
| `sched-2026-08-12` (`effort=high`) | 5 | 14.8 | 15.9 | 15.9 | 0 |
| `sched-2026-08-13` (`effort=high`) | 32 | 15.1 | 30.1 | **39.1** | **4** |

Ninety pre-`effort` calls never breached 30 s; thirty-two after it breached four times. 08-12 is an
**underpowered sample, not a counter-example**. Three fail-opens → execution submitted 3 of 8, and
**2 of those 3 (AMD, DOW) reached the broker unreviewed**. **Mitigation applied:**
`request_timeout_seconds` **30 → 60**, env-var only. **Prediction, stated so it can fail:** the next
run should show `failed_open_count 0` / `debate_coverage 1.0`. If not, the timeout was not the cause.

**S175 — merged, NOT deployed** ([spec](sprints/sprint-175-the-veto-says-only-what-it-can-prove.md)).
Independently verified: the invented `stop_pct vs ATR%` fragment is gone from the PM packet;
`drop_vetoed` is **unchanged**, so a fail-open still submits — it is now *loud and distinguishable*
(`applied_failed_open` + an `error` fault), never *blocking*, which was the hard constraint. Pack
hash unmoved. 🪤 **It does not change acceptance** — `trading_acceptance` reads
`DeliberationRun` props, not `Fault` nodes, so a run with fail-opens still reads FAIL. The 60 s
timeout is what fixes that, not S175.

**S176 — code-proven, branch-gated, NOT deployed** ([spec](sprints/sprint-176-a-partial-fill-must-be-able-to-finish.md)).
`partial -> filled` is now the only mutable broker-status transition on `Fill`; the completed
broker price and realized-PnL conclusion move with that transition, while terminal statuses remain
immutable. DRIFT-033 is closed by dropping master's stale `"neo4j"` external I/O declaration without
adding `"postgres"`. Local `make ci`: **2243 passed / 6 skipped / 100.00 %**; remote branch gate
proved `57f540f`. Pack hash unmoved. **No live functionality proof is claimed**: the live spine has
never produced a partial fill.

**S176 — merged, NOT deployed** ([spec](sprints/sprint-176-a-partial-fill-must-be-able-to-finish.md)).
Independently verified: `completes_partial_fill` permits **only** `partial` → `filled`, terminal
statuses stay immutable, and `exit_price_cents` switches to the current price only when a partial
completes — a narrowed guard, not a deleted one. `DRIFT-033` **CORRECTED** (`b17ff5fd`): the stale
`neo4j` declaration is gone and `postgres` was correctly *not* added, matching the convention that
analyst/forecaster/monitor declare `external_io=()` despite using the graph. Pack unmoved.
🪤 **No live proof exists or can exist** — zero of 188 production `Fill`s have ever been
`partial`, so the fixed path has never been exercised outside tests. Stated plainly rather than
implied.

## The sequence from here — in order, and the order matters

1. **Read `sched-2026-08-14`.** It runs on `s174`, so nothing S175 changed is under it: the timeout
   is the only variable that moved since the failing run. `trace_run.py` + `accept.py`, then the
   `LLMCall` latency table above for a fourth row. 🪤 **Do not retag before reading it** —
   deploying into the experiment destroys the only clean comparison available.
2. **Merge S176 after the evidence commit is branch-gated.** It is independent of the 08-14 run and
   remains undeployed after merge.
3. **Then one deploy carrying S175 + S176** — both are merged and waiting; one retag, one live
   check, two fixes proven at once. Tag sprint-shaped per [DL-106](design-log.md).
4. 🪤 **A quoted hash that matches no file is still a false claim.** S176's handback cited a
   pack hash (`40bd1b10…`) matching neither the file's sha1 nor its sha256 nor any tracked file;
   the conclusion was right, verified independently. Second instance today after `debt.md`'s
   *"50.9 s"* tail, which also does not reproduce. **Re-derive cited numbers; do not adopt them.**

## Next

**Ahead of the numbered list — one deploy-gated measurement, and three questions raised and not yet
answered.**

**The measurement that reorders everything below it.** `0.90.02` made the `effort` tunable reach the
wire, so the two free latency levers are measurable for the first time. Sweep **`effort` down from
`max` first** — it is the only lever that costs nothing. Then `max_rounds` 2 → 1 **only if that is
not enough**: 🚨 its own `why` says *"debate must show more than one round in live proof"*, so one
round is **cutting the artefact under test to buy wall clock**, a recorded decision rather than a
knob. Build [S172](sprints/sprint-172-independent-debates-run-independently.md) **only if both
together still miss** — full ordering and the arithmetic in [DL-105](design-log.md)'s amendment.
The sweep's first point is **done** — `effort` `max` → `high`, live since 2026-08-12 — and it
cost three fail-opens before `request_timeout_seconds` went 30 → 60. The two levers are
**coupled**: raising effort lengthens the peer-call tail into a fixed timeout. Measure both
together or not at all.

**Undecided, recorded so they are not re-derived** — all raised 2026-08-11, none actioned:
**(i)** amend S172 — its stated reason for excluding `max_rounds` is unsound (the sum-of-latency ÷
span ratio is invariant to call count), and its build-trigger belongs in the spec;
**(ii)** collapse to one ranked queue — the operator's out-of-repo `debt.md` table is the best
"what next" artefact in the project and is a third live tracker; folding its *shape* into this
section would delete a tracker rather than add one; **(iii)** stop pinning version numbers in sprint
specs (*"next available PATCH/MINOR at merge"*) — after three renumberings in one day.

1. 🚨 **DL-104 (a) — delete or honestly relabel the deliberator's invented ATR fragment.** A **fix**, and it
   manufactures the single most-repeated veto objection across **both** vendors: six vetoes cite an ATR
   contradiction that does not exist. `context_pm._atr_pct` averages **every bar handed in** (42 → a
   41-period ATR) while the analyst's `atr_pct` is **14-period**, and `_atr_fragment` renders
   `PASSED`/`FAILED` **inside the `stop_vs_regime_volatility gate:` line** for a comparison **no gate ever
   performs**. Python, so the full CI cycle **and a deploy** before it reaches the fleet.
2. **DL-104 (b) — give the veto batch context, or stop it reasoning about portfolio state it cannot see.**
   The SCHW *"deployed=0 despite holding USB and WFC"* objection is false on a flat book: the deliberator
   sees one order's packet and cannot tell *first in the deterministic order* from *the book is broken*.
3. **DL-104 (c) — the analyst's hardcoded SMA-200 rationale, and the bars gap underneath it.** The summary
   string always names SMA-200 while `indicators.sma_distance` silently returns `None` below its period, so
   the *rationale asserts an input that could not exist* (the scoring itself is unaffected). Underneath sits
   the real gap: `lookback_days=260` exists explicitly *"so SMA200 can compute"*, we receive **42** bars, and
   `min_history_bars=2` waves that through without a murmur. This is the one veto class that **checked out
   correct**.
4. **DL-104 (d) — a real advisory/binding switch**, so *advisory* is a declared posture rather than a grace
   that happens to expire. Every run in the current state writes a truthful but uninformative `error` fault,
   which trains the operator to read a real fault as noise.
5. **S169 — a deploy that keeps the switches it was given**
   ([sprint-169](sprints/sprint-169-one-switch-and-a-deploy-that-keeps-it.md)). A **fix**, and one that has
   already cost a silent wipe of `SCANNER_CANDIDATE_CAP`, `MAX_POSITION_PCT`, `MAX_POSITIONS` and the
   weekday-only dispatcher cron — all under a green `[OK]`. 🪤 Its spec targeted `0.90.01`, which **S171 had
   already taken**; retargeted to `0.90.02` on 2026-08-11.
6. **S170 — one LLM adapter in `kernel/`**
   ([sprint-170](sprints/sprint-170-one-llm-adapter-in-the-plumbing.md)). Ranked **below** the fixes above
   because it is capability rather than repair — but it is what gives the operator the same provider switch
   the deliberator already has, while the Anthropic key is usage-limited to 2026-09-01. Retargeted `0.90.02` → `0.90.03` on
   2026-08-11.
7. **Remaining hardening rows: N, O, P.** **N** — delegated coding agents default to `danger-full-access`
   with no approval prompt; the protection is the operator remembering a CLI flag. **O** — S157's 101
   missing law-clause test-plan rows, then flip assertion E in `scripts/check_law_coverage.py` to hard fail.
   **P** — a `partial` fill can never upgrade to `filled`; still **zero** production fills in that state,
   which is the only reason it is not urgent.
8. **DRIFT-033** — drop `"neo4j"` from master's `external_io` declaration. One token, full CI cycle because
   it is Python; still worth bundling with the next Python chore rather than a branch of its own.
9. **Row Q's live confirmation, still owed.** 🪤 The 2026-08-12 retag went through `az`
   image-only, not `deploy-agents.ps1`, so it did **not** supply it. Expect `[OK]` on all 17 targets; any `[XX]`
   should now be a genuine failure carrying its stderr. Item 1 is the deploy that would supply it.

## Pointers

Product `docs/PRD.md` · architecture `docs/architecture.md` · phases `docs/build-plan.md` · closed
decisions `docs/decisions/INDEX.md` · open threads `docs/design-log.md` · "does it work"
`docs/laws/{ledger,drift-register,functionality-checks}.md` · per-agent `agents/<name>/mission.md`.
