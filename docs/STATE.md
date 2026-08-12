# Project State

**Last updated:** 2026-08-12 17:35 AEST · **Version:** 0.90.02 · **The veto bound for the first time: on `sched-2026-08-11` a `revise` verdict reached execution 118 s after the PM run and stopped the day's only buy — `deliberation_status='applied'`, 0 submitted.**

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

**The veto bound for the first time, and the fleet is current again.** Version `0.90.02` now runs
on **all 17 deploy targets** (16 apps + `dispatcher-cron`), retagged 2026-08-12 —
`DeployRecord deploy:2026-08-12T07:27:25…:v0.90.02:ffdbaf1b`. *Proven at the fleet, not assumed:*
16/16 images `v0.90.02`, 16/16 `Succeeded`, KEDA intact on **all** sixteen (`min=0`, 1 rule each),
job cron still weekday-only `30 22 * * 1-5`, and the switches S169 exists to protect survived the
image-only path — `SCANNER_CANDIDATE_CAP=25`, `PORTFOLIO_MANAGER_MAX_POSITION_PCT=0.01`,
`PORTFOLIO_MANAGER_MAX_POSITIONS=60`. The vocabulary pack hashed **identical** across
`9a22102`→`ffdbaf1` (`13c0e3a0…`), which is why image-only was the legal path and not an S148 stall.

**`sched-2026-08-11` — 8/8 stages, `ACCEPTANCE PASS`, and 0 orders submitted on purpose.** Provider
**99/99** with **zero `*_degraded` notes** (4059 bars, 1825 headlines, regime `neutral`); scanner
99 → 20; analyst **19 scored / 2 rejected** (NOW 0.584, META 0.583, both under the 0.600 floor); PM
**1 approved** — XOM ×6, est. $159.78. Then the thing that had never happened: `PMRun` 22:38:49Z →
`DeliberationRun` **22:40:47Z**, `verdicts={'XOM': 'revise'}`, `vetoed_tickers=('XOM',)`,
`real_debate_count=1`, `failed_open_count=0`, and `ExecutionRun … deliberation_status='applied'`
with **submitted=0**. **118 seconds against a 900 s grace.** The verdict was *read and bound*, not
defaulted past. DL-104's owed item (d) is still owed — but the machinery under it is now proven to
work whenever the debate finishes in time.

**`sched-2026-08-10`'s open question is closed: the 18 orders filled.** They sat `accepted` with
`filled_qty 0` at that run's close, which is the whole reason acceptance read `UNPROVEN`. Measured
2026-08-12: **18 active positions** (`is_active_position_node`, never raw `status`), adopted from the
broker snapshot at 22:32:46Z on 08-11, matching the broker one-for-one, with `Fill` nodes already
keyed `pm-run-74dc…:TICKER:buy`. The `critical` divergence Flag that run raised is reconciliation
reporting its own adoption — not a fault. **51** flags now unacknowledged, still climbing.

🚨 **`effort` is live at `max` for the first time, and that is untested in production.** Until
`0.90.02` the value was assigned and dropped, so every debate ever run — including the clean 118 s
bind above — used the vendor default. `DELIBERATOR_EFFORT` is **unset** on all three deliberators, so
`settings.py`'s `"max"` applies from the next fire, against `max_tokens=4096` (hard-capped, `le=4096`)
on `DELIBERATOR_LLM_PROVIDER=openai`. Two exposures, **neither measured**: reasoning latency pushes
straight into the 900 s grace [DL-105](design-log.md) already calls the scarce resource, and reasoning
tokens count against the 4096 completion budget — an exhausted budget returns empty content that
`_text()` renders as `""`. Env-overridable without a rebuild, so backing it off is one `az` call.

🪤 **The image tag scheme changed, and the decision is not yet recorded.** This deploy is tagged
`v0.90.02`, not `sNNN`: the change was a **chore** with no sprint number, and `s172` is packaged but
unbuilt. Traceability holds through the `DeployRecord`'s full SHA — but the *name* alone no longer
identifies a commit, because git tag `v0.90.02` points at `de3c071` while the image was built from
`ffdbaf1`, two docs commits later. `sNNN` never collided that way. **Open:** adopt a chore-suffix
convention (`s171a`) and rebuild, or keep version-shaped tags and lean on the SHA.

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
The fleet runs `0.90.02` as of 2026-08-12, so the sweep is **unblocked** — and `effort` is
already live at `max`, which makes the first sweep point a measurement of the status quo.

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
