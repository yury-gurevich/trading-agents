# Project State

**Last updated:** 2026-08-11 16:52 AEST · **Version:** 0.90.02 · **The advisory posture was exercised live on `sched-2026-08-10`: the grace expired, 18 buys went out, and the veto's verdicts arrived four minutes too late to bind — see Now.**

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

- **The veto reached production, was read for the first time, and was demoted to advisory (feat + fix,
  0.89.07–0.90.01, 2026-08-08→10 — ADR-0022, DL-98/99/101/102/103/104).** **S166** closed the race the
  veto had always lost: execution reached the broker at 05:36:22 while the `DeliberationRun` saying
  *revise* landed at 05:47:32, and `_drop_vetoed` read an absent veto as *execute everything* — so *not
  finished yet* and *not deployed* were indistinguishable. A buy-carrying `PMRun` is now held for a
  bounded grace (`deliberation_grace_seconds`, default 900); **exits never wait** (ADR-0017). **S167**
  fixed an audit reporting *"Faults today = 0"* while 18 were being written — `Fault` stamps
  `occurred_at`, the query read `created_at`, which is `NULL` on every Fault node (measured both ways at
  the same moment: **18** vs **0**) — and made `failed_open_reason` record the captured cause instead of
  asserting one. **S168** (`0.90.00`) gave the veto a second vendor after the Anthropic key hit its limit
  to 2026-09-01: an `OpenAILLMClient` behind the same port plus an `llm_provider` **tunable, deliberately
  not an automatic fallback chain**, because a silent switch makes *which model reviewed this order*
  unanswerable after the fact. **chore-openai-cutover** granted the key and found the vault and `.env`
  holding **different** OpenAI keys — both authenticated, so nothing was broken, but the fleet would have
  billed a five-week-old key nobody tracked. **S171** (`0.90.01`) fixed a peer client taking `messages[0]`
  with no correlation; cold peers now measure `real_debate_count=18`, `failed_open_count=0`, reply
  subscription **0 active / 0 dead-letter**. 🚨 **Each fix exposed the next.** Correlation revealed the
  debate's true cost — **943 s** against a 900 s grace (DL-103) — so the grace went 900 → 1800; then
  DL-104 read the verdicts and returned it to **900 deliberately**: **45 `revise` of 58** real debates,
  **56 %** self-agreement on the same model and prompt 3.5 h apart, and roughly **2 of 15** grounds
  surviving a check against the code. The veto is a good auditor and a bad gate.

Older sprints — **`0.89` and below → [STATE-07.md](state-archive/STATE-07.md)**; earlier arcs (S36→S146)
in [STATE-01…06](state-archive/INDEX.md). Full chronological list: `docs/sprints/README.md`.

## Now

**The veto is advisory by an expiring grace, and the first run under that posture is half-proven.**
Version `0.90.02`. Fleet **all 16 apps on `:s171`** (measured 2026-08-11). 🪤 **`main` is now one
PATCH ahead of the fleet:** `0.90.02` wired the `effort` tunable and is **not deployed**, so the
latency sweep [DL-105](design-log.md) calls for cannot run until the fleet is retagged.

**`sched-2026-08-10` — 8/8 stages, `ACCEPTANCE UNPROVEN`.** *Proven:* provider **99/99** tickers with
**zero `*_degraded` notes** (4059 bars, 1857 headlines, regime `neutral`); scanner 99 → **22** survivors;
analyst **18 scored / 4 rejected**, all four within 0.020 of the 0.600 regime floor (NOW 0.580, PFE 0.585,
META 0.593, XOM 0.597); PM **18 approved / 0 rejected**; execution **18 submitted / 0 rejected**; monitor
and reporter both 0 on a flat book. *Not proven, and the reason acceptance reads `UNPROVEN` rather than
`PASS`:* all 18 sit at Alpaca `accepted` with `filled_qty 0`, queued for the 2026-08-11 open — equity
**$102,464.21**, **0 positions**, ≈ **$17.3 k** committed at ≈ 1 % per name. Whether the resized book
actually refills is decided at that open, not by this run.

🚨 **[DL-104](design-log.md)'s posture worked exactly as written, and charged exactly the cost it named.**
The grace expired and the buys proceeded: `submitted 18 order(s) carrying a buy with no DeliberationRun
after 900s`, severity **error**, 22:55:57 UTC. The `DeliberationRun` landed **22:59:56 — four minutes after
the orders were already at the broker** — carrying **3 `uphold`** (AAPL, ABT, DIS), **14 `revise`**,
**1 `overturn`** (BMY) and **15 tickers in `vetoed_tickers`**. **Had it bound, 18 orders would have been 3.**
DL-104 called this fault-used-as-a-feature acceptable for one run and corrosive as a standing posture; that
one run has now happened, so owed item **(d) — a real advisory/binding switch — stops being theoretical.**

**Everything else on the day is a known.** 28 `drop_unfilled_orders` **warnings** clearing the 08-08
cutover-test batch (the S148 sweep working as designed), plus one **error** — `stop:probe-s164:T#1` has no
Fill chain, the same row `audit_broker_graph.py` reports as its single `A3 FAIL`. **Zero `Escalation`s**;
**no new divergence Flag** (the latest is still 2026-08-03); 50 unacknowledged flags outstanding, unchanged.

**The fill check is scheduled, not remembered.** One-shot cloud routine `trig_01YG4Es36pFPwAMhx5qofJ2d`
fires **2026-08-11 21:00 UTC** (07:00 Wed AEST) — after the close, and ≈ 90 min before the next run's drop
sweep clears any leftovers. 🪤 It **emails a reminder and nothing more**: a cloud session gets a bare
checkout with no `.env`, so it cannot reach the spine or the broker. `accept.py` is re-run locally.

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
🪤 The sweep needs the fleet retagged off `:s171` to pick up `0.90.02`, which wants S169 first.

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
9. **Row Q's live confirmation, still owed at the next deploy.** Expect `[OK]` on all 17 targets; any `[XX]`
   should now be a genuine failure carrying its stderr. Item 1 is the deploy that would supply it.

## Pointers

Product `docs/PRD.md` · architecture `docs/architecture.md` · phases `docs/build-plan.md` · closed
decisions `docs/decisions/INDEX.md` · open threads `docs/design-log.md` · "does it work"
`docs/laws/{ledger,drift-register,functionality-checks}.md` · per-agent `agents/<name>/mission.md`.
