# Project State

**Last updated:** 2026-07-28 16:40 AEST · **Version:** 0.80.02 · **🟢 THE EXIT-REPLAY FIX IS PROVEN IN PRODUCTION — `sched-2026-07-27` resumed from 4/7 `ACCEPTANCE FAIL` to `RESULT 7/7 stages complete`.** Fired deliberately on 2026-07-28 by temporarily widening the KEDA windows for master/execution/monitor/reporter (restored to `25 22`/`30 22` → `30 00` UTC immediately after, verified). **Every S145 claim held against real production data:** execution consumed the poisoned `pm-run-df925eea…` and wrote `ExecutionRun … submitted=2 rejected=0 skipped=1` — the `skipped=1` is the MRVL completed-exit skip; **both orphans were adopted, not fabricated** (`exit:22d71d0d3acc0586:AMD:sell` → `broker_order_id=d040c762…`, `pm-run-df925eea…:ABT:buy` → `fd1f1c2c…`, matching the live Alpaca orders exactly); and the **broker order list is byte-identical before and after** — no duplicate orders, no MRVL re-submission, so the 0.74.01 oversell guard held. Monitor ran (`checked=9 closes=0 holds=9`) and reporter ran; neither had run since the crash. `accept.py` → `ACCEPTANCE UNPROVEN - completed; orders submitted but none filled yet (queued for the open)` — the honest verdict, since AMD sell 55 and ABT buy 95 fill at the 13:30 UTC open. **Then confirmed by a full fresh cascade** — `confirm-s145-20260728` (distinct run id, deliberately *not* `sched-2026-07-28`, so tonight's dispatcher cannot day-key-dedupe onto it): provider 100 tickers / 4000 bars / 1880 headlines, scanner 5 survivors, analyst 9 scored, PM `approved=1 rejected=8`, execution `submitted=1 rejected=0`, monitor `checked=9 closes=0 holds=9`, reporter ran → **`RESULT 7/7 stages complete`** and **`ACCEPTANCE PASS - every stage did its job within its boundaries`**. The PM's one order was `AMD sell qty=55`, which execution **adopted onto the existing broker order rather than duplicating it** — AMD still shows exactly one live sell (`d040c762…`), so the feared oversell did not occur. **The only new broker order in the whole run was SCHW's missing protective stop** (`stop:b56b2d2f124326d3:SCHW`, sell stop **qty=196**, 06:55:22Z) — the ADR-0015 §3 item S145 left as *"verify, do not fix"*, now **healed at the correct size** because reconciliation had finally produced a `broker:SCHW:196:10222` node matching the real holding. **The run also exposed a new defect — see 🟠 DL-73 below.** S145 is merged to `main` (`2c49f88`, 0.80.02): local `make ci` **1856 passed / 100.00%**, remote CI + Security Findings green on the merge tip, `Build and push agent images` green on `main`, `v0.80.02` tagged (plus `v0.78.00`/`v0.79.00`/`v0.80.00`/`v0.80.01` backfilled — tagging had silently stopped after `v0.77.00`). **Fleet retagged `:s143` → `:s145`** (2026-07-28, built from `fcd81a4`, code identical to `2c49f88`): all 14 images built, all 13 apps + `dispatcher-cron` returned `Succeeded`, verified **13/13 on `s145`** plus the job, env vars (5) and the `daily-agent-window` KEDA rule intact with `minReplicas=0`, and `DeployRecord deploy:2026-07-28T06:17:06…:s145:fcd81a4` written after the verification, not before. **Scope the claim honestly:** what is proven is that the fixed code is *deployed*. Execution has not yet run under it — the poisoned `pm-run-df925eea…` is still pending and still returned first by `find_pending`, so the actual unbricking is proven only when tonight's 22:30 UTC run (or a `/resume-run`) completes 7/7. **What broke (`sched-2026-07-27`, DL-71) — and the two firsts the same run booked.** The run reached **4 of 7 stages**, `ACCEPTANCE FAIL` (execution/monitor/reporter NOT REACHED). Execution died on `ValueError: property 'price_cents' cannot be overwritten` in `write_fills`, restarted, and crash-looped from **22:40:31 to 00:33 UTC** until the KEDA window closed. **It does not self-clear:** `find_pending` returns every `PMRun` with no downstream `ExecutionRun`, so the poisoned node is returned first on every poll — tonight's run hits the same crash before reaching its own work. **Cause:** 0.74.01 keyed exit orders on the position so an unfilled sell would *"replay instead of duplicating"*; that one string is both the broker `client_order_id` (the oversell guard — it worked) and the append-only `Fill` node key, and a replay carries a moved reference price (`19451` → `18928`). **The replay path had never actually replayed before.** Upstream: the MRVL exit had **filled nine hours earlier** at Monday's open, but the book is only healed by the monitor at stage 6 — one full run later, and 07-25/07-26 were weekend skips — so the analyst scored a stale book, re-decided `MRVL sell`, and the PM approved a full exit of a position that no longer existed. **Two firsts survived, because `place_broker_stops` runs before `run_submit`:** ADR-0015 §3 is **PROVEN** — six resting `sell stop` orders live at Alpaca (BAC 503 @ 56.65, CSCO 177 @ 106.78, HPE 229 @ 41.37, PYPL 175 @ 53.81, USB 478 @ 59.47, WFC 348 @ 82.07, each with a real broker order id, placed 22:40:25–29 UTC) — and the **first realized forced-stop exit** booked: MRVL `44 @ $195.98`, **−$1,330.12**. **Two orphans to heal:** AMD sell 55 and ABT buy 95 are `accepted` at Alpaca with **no `Fill` node**, so a naive retry would record `rejected` for live orders (DL-57/DL-59 class). SCHW (196 sh) holds no stop — that one is the guard *working* (`_broker_quantity_matches`: graph 98 vs broker 196) and self-heals once the monitor reconciles. **S145 SHIPPED** ([sprint-145](sprints/sprint-145-exit-replay-append-safe.md), 0.80.02, `2c49f88`, DL-71 option A): one attempt = one immutable node, a completed exit is never re-issued, and a per-intent failure degrades to a per-intent `Fault` instead of costing three stages — each proven by a planted violation (DL-70) and by a live-spine functionality check on Neon with teardown to zero. **Success factors still outstanding:** the fleet retag, and a resumed run proving **7/7** with the orphans carrying honest Fill nodes. · **🟠 S146 IS PACKAGED — the orphans are a lineage lie, and the self-heal is single-shot (DL-72).** A read-only probe of production on 2026-07-28 (after the merge) established what S145 could only assume: AMD sell 55 (`exit:22d71d0d3acc0586:AMD:sell`, broker `d040c762…`) and ABT buy 95 (`pm-run-df925eea…:ABT:buy`, broker `fd1f1c2c…`) are **still `accepted` at Alpaca** — after-hours market orders queued for the next open — and the graph holds 43 `Fill` nodes, **neither of them**. Their `PMRun` and all three `OrderIntent` nodes exist, but **no `ExecutionRun` does**, so the crashed run is *still pending* and the next execution pass would very likely adopt both through the S145 `422 duplicate` → `by_client_order_id` path. That is the finding **and** the problem: the same pass writes the `ExecutionRun` that removes the `PMRun` from `find_pending` forever, so if adoption silently fails for one ticker the window shuts anyway. [sprint-146](sprints/sprint-146-orphan-fill-lineage.md) (0.80.03) makes the repair deterministic — a bounded append-only script sharing `write_fills` with the agent, reading broker state at run time, refusing to forge an `ExecutionRun`, and a no-op on second run. **Found alongside and deliberately not fixed there — worse than the orphans:** the position book has diverged badly from the broker (**AMD carries three `open` Positions totalling 111 shares against 55 held**; **MRVL is held nowhere at the broker yet has two `open` Positions of 44**; ABT 98 vs 96; SCHW 98 vs 196), and `exit:e67227ec…:MRVL:sell` still reads `status='pending'` while `broker_status='filled'` with its realized PnL booked. These are monitor-reconciliation defects and they make **DL-71 option B the priority successor**, not an optional one. · **🟠 THE WRITE GUARD WAS A SCHEDULED OUTAGE — caught before it fired (S144, 0.80.00, DL-68).** S143's vocabulary guard shipped unset, and turning it on was two defects deep. It was **undeployable**: `GRAPH_VOCABULARY_PATH` names a file and **none of the 14 images copies `orchestration/packs/`**, so setting it would have raised `FileNotFoundError` at boot rather than enabling anything — fixed with `GRAPH_VOCABULARY_B64`, the delivery shape the master already used for grants and the secret map (S86/DL-12), injected per-agent by `deploy-agents.ps1`. Worse, the pack was derived from **observed** writes, so it could not cover code that had never run: ADR-0015 §3 broker-native stops merged Friday without ever placing a stop, and **both its edges were undeclared** (`Fill -STOPS_WITH-> BrokerStopOrder`, `Position -PROTECTED_BY-> BrokerStopOrder`). Labels and edge types *were* declared — only the signatures were missing, the last thing `check_edge` tests — so **enabling the guard would have thrown `VocabularyError` at the moment execution placed tonight's first real stop**, destroying the proof pending since Friday in the name of a guard built to prevent damage. The pack is now proven a superset two ways, because neither alone suffices: static recovery reaches `Fill -STOPS_WITH-> BrokerStopOrder` (so the defect is inside the check's reach, not just hand-fixed once), while `Position -PROTECTED_BY-> BrokerStopOrder` resolves through a dict lookup and is reachable **only** by executing the path under a guarded store. The static pass also found `Experiment -PROPOSES-> ParamChange` undeclared. `make ci` **1851 passed / 100.00%**, all four remote gates green before merge (`d215a76`), gate self-test **14/14**. **Functionality check PROVEN** on the live Neon spine via base64 alone — `GuardedGraphStore` wrapping **`PostgresGraphStore`** (asserted), an undeclared label rejected with **0 rows written**, both stop signatures accepted. **The guard is NOT enabled on the fleet**, deliberately: `:s143` predates the code, and a new fail-closed write path does not belong in tonight's run. That is a **dated action after tonight's 22:30 UTC run**, and S144 stays open until it is done. · **🟢 OPUS 5 AT MAX EFFORT IS LIVE — fleet `:s143` (0.78.00, 2026-07-27).** `output_config` was never sent on any Anthropic call, so the reasoning-depth knob was inert; it is now wired through all three adapters (operator tool-use client, deliberation debate, remediation gate) at `effort=max`, and **PROVEN live** — a real debate ran on `claude-opus-5` with no 400 and returned a substantive `REVISE` verdict. Two traps the work exposed: the operator's `max_tokens=512` is a **truncation trap** once effort drives thinking (thinking and structured output share the ceiling, so the budget is spent reasoning and the parse returns `refused`) — raised to 4096; and **the fleet reads no `.env`** (DL-63) — a container gets `os.environ` from the master's ACTIVATE payload, which `trading_secrets.json` populates with *credentials only* (the operator's whole grant is one row), so the **code default is the fleet's effective value**. Defaults therefore moved `claude-sonnet-4-6` → `claude-opus-5` in code, not in `.env`. `claude-opus-5` priced into `llm_pricing.json` ($5/$25 per MTok) so the LLMCall ledger stays honest — note Opus 5 is **5× Haiku 4.5 per token**, plus max-effort thinking billed at the output rate. **Still pending:** the operator agent's tool-use client is deployed but not yet exercised live; and **broker-native stops (`:s142`) never got a session day** — the 22:30 UTC fires on Sat 07-25 and Sun 07-26 were clean calendar skips, so `BrokerStopOrder` count is still **0** and nine positions hold **no protective stop at the broker**. MRVL's forced-stop sell (`qty=44`, submitted Fri 22:40 UTC) is *still* `accepted`/unfilled and has bled to **−$1,198** — the gap-down exposure DL-62 describes, now real money. **🟢 THE LOOP CLOSED (2026-07-24).** The first sell **FILLED** — `ABT 98 @ $101.35`, entry $100.78, **≈ +$55.81 realized** — `regt_buying_power` recovered **0 → $32,919.70**, and a buy cleared the broker again (`SCHW ×98`, `submitted=1 rejected=0`). Capital now recycles. The four stranded positions are **back in the book and scored** (`scored=10`), ABT closed **by broker evidence**, and three fresh close decisions stranded **nothing**. Lifetime broker sell count went **0 → 1**: `ABT sell qty=98 accepted` reached Alpaca from run `check-s136-sell` on fleet `:s136`, via analyst `ABT sell 0.62` → PM `ABT sell qty=98` **and** `SCHW buy qty=99` in one `OrderIntentSet` → the existing buy rail (ADR-0016). The nightly re-buy accumulator that walked BAC 171→338→503 into a `regt_buying_power=0` wall is **stopped** — held names now return `hold` and the PM skips them. **Scope the claim honestly:** the sell needed a forced `exit_confidence_floor=0.625`, so the *rail* is proven and the *exit strategy* is still the agreed placeholder; and the monitor's own stop/target closes are **still undispatched** — 4 positions (AMD, CSCO, HPE, MRVL) are stranded and the count grows each run until ADR-0015's fill-keyed closure is built. `sched-2026-07-20` (dispatcher `dispatcher-cron-29743110`, fleet on `:s130`) ran **7/7 → ACCEPTANCE PASS** with **ZERO `*_degraded` notes** — the first fully-fed scheduled run since 07-07, and the proof S128 mattered: all four enrichment feeds populated (1867 headlines; the earnings-window filter actually fired), sentiment restored, the analyst scoring on **full signal**, and the chronic all-reject no-trade signature flipped into **5 buys** (USB/BAC/PYPL/WFC/ABT, conf 0.61–0.68 lifted over the 0.600 floor by sentiment). S130's hardened DHI runtimes booted and ran the whole chain; 0 Escalations. Fleet standing on `:s130` (built `d0b0d3a`); **P12 clean-news runway accumulating since 2026-07-20**. **Now:** S133 **shipped** (0.71.07) — the **last shared credential is closed**: Service Bus access is now per-agent entity-level SAS, delivered and flipped live, and the hardening backlog has **no open rows**. The security gate finally ran on sprint code — via a PR at the time, and **since DL-56 it runs on push to every branch**, so worktree-and-merge-locally is gated without any PR. **Fleet on `:s141`** (`29a36f4`, 0.76.00). **Pending unattended:** the `SCHW ×98` buy fills at the next open; tonight's 22:30 UTC run uses a fresh `sched-2026-07-24` key. **Settled & shipped (ADR-0017, 0.76.00, fleet `:s141`):** *which decider wins* is decided — **alpha proposes, risk disposes**. The analyst is now the **sole discretionary exit author** and wins every discretionary disagreement; a **breached stop is forced onto the same rail regardless of confidence** (risk overrides alpha on the downside); the monitor **stops deciding** and raises a `Fault` when a stop is breached-but-unsold (DL-57 visibility); `target`/`time` retire into deferred strategy; the dead `order_from_close`/`execute_close` path is removed (one rail, DL-60). `make ci` 1786 passed / 100.00%, all four remote gate jobs green, `DeployRecord …:s141:29a36f4` written after proving 14/14 on tag. **Functionality check PROVEN** (run `sched-2026-07-24`, 2026-07-25): the forced stop fired for the **first time ever** — `MRVL sell exit_trigger='stop' conf=0.637`, **above** the `exit_confidence_floor=0.5`, so the thesis said *hold* and the stop overrode it (the only `exit_trigger=stop` in the graph). The monitor went **silent** (`checked=9 closes=0 holds=9`) where it used to re-decide HPE/MRVL/CSCO every run, and raised the visibility Fault `"stop breached on MRVL, still held"` (DL-57). The sell reached the broker on the one rail (PM full exit `qty=44`, execution `submitted=3 rejected=0`, alongside SCHW+ABT buys). **Fill outstanding:** MRVL sell + the two buys are queued for the open (acceptance `UNPROVEN`), exactly as ABT was before it filled — re-check `accept.py` after today's US open for the first real forced-stop realized PnL. Broker-native stops (ADR-0015 §3) remain the durable home of the floor; the forced daily-rail stop is the interim, exposed to a gap-down between the 22:30 run and the next open. Last night's scheduled run was a **silent no-op**: the dispatcher `Succeeded` but day-key-deduped onto a `sched-` id a manual run had already consumed — use distinct run ids for manual runs. **Hardening backlog (2026-07-23 series):** row **L is CLOSED** — *corrected 2026-07-27*: STATE carried "`make ci` cannot fail on a CVE" for three days after the fix actually landed. The dash was removed in `77769ce` (0.75.00, 2026-07-24); the recipe is a bare `uv run pip-audit`, and `gate_selftest_cases.py` now guards it twice (`pip-audit-cve` proves it *can* fail; `pip-audit-not-ignored-by-ci` blocks the dash returning). **Dependency posture changed (2026-07-27, DL-64):** Dependabot moved **weekly → monthly, batched** after a trickle of solo major PRs was closed unread (#69/#70/#72) — majors now fold into the group everywhere except Python *production* deps, which keep a solo PR; ≤3 PRs in a typical month. Separately, **Dependabot alerts + security updates enabled** (were `disabled`) with **zero open alerts** — this was never the CVE net (`pip-audit` fails `make ci`; Trivy gates the images) but nothing watched **GitHub Actions or base-image advisories** until now. Security PRs bypass the monthly schedule, so vulnerabilities still arrive same-day. Still open: **M** (a pushed branch produced **zero** workflow runs; the branch-is-the-gate rule can be defeated by an infrastructure miss, not just a process mistake), and **N** (delegated coding agents default to `danger-full-access` with `approval_policy = never`; every run so far overrode it with an explicit sandbox flag, but the protection lives in remembering that flag). **Pending operator:** the standing broker-divergence Flags were **not** noise — they were correctly reporting an exit that never executed (DL-58); do **not** ack them until the AMD position is resolved. *Correction:* STATE had carried "S131 per-role DSN flip not yet applied" since 07-21 — **it was wrong**; the flip ran during S131 and a full 14/14 live probe on 07-22 proves every app connects under its own `ta_*` role (DL-54).

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + `STATE-01…05.md` + git). **LAW-02:** an item is "shipped" only when
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

**🟠 NEW — DL-73: reconciliation accumulates phantom positions (consequence claim CORRECTED).**
`agents/monitor/reconcile.py:108` keys positions `broker:{ticker}:{qty}:{avg_entry_cents}` and
matches on **both** quantity and basis, so any holding change mints a **new** open `Position` and
never closes the old one. Confirmed: **23 `Position` nodes for 8 actual broker holdings** — BAC
open at 171 *and* 338 *and* 503, USB at 160/320/478, WFC at 116/233/348, AMD at 19/37/55, plus
SCHW/ABT/MRVL doubled. `broker_absent` marking is applied **inconsistently** —
`broker:MRVL:44:22621` holds 44 shares of a stock the broker holds **none** of and is not flagged.
**Corrected:** STATE first claimed these phantoms "get scored, sized, and turned into exit keys —
the exact chain that produced DL-71". That was inferred from node counts, and the
`confirm-s145-20260728` run **tested it and did not reproduce it**: the analyst scored **9 tickers,
one per ticker** (AMD scored once despite three nodes), the PM sized `AMD sell qty=55` — the **true
holding**, not 111 — and MRVL was excluded entirely. So this is an **unbounded junk-accumulation
defect with an unexplained mitigation**, not live firefighting. The open question is *why* the
per-ticker selection picks correctly, since nothing tests it. DL-71 option B still owns it.

**PROVEN (LAW-02) — what the merge actually established.** One attempt = one immutable `Fill` node
with the broker `client_order_id` unchanged (the 0.74.01 oversell guard stands); a `filled` exit is
never re-issued and the skip is a visible `Fault`; a per-intent failure degrades to a per-intent
fault so one ticker cannot cost three stages (DRIFT-014 / S128 restated for order submission). Each
was observed **failing** on a planted violation first (DL-70), and all three were re-proven against
the live Neon spine with teardown to zero. Gate self-test 14/14.
**NOT yet proven — the outstanding success factors:** the fleet retag; a resumed run scoring
**7/7** with MRVL out of the book and SCHW carrying its stop; and the two orphaned live orders
carrying Fill nodes matching **real** broker state. Sequenced *before* S144's dated vocabulary
enablement — a new fail-closed write path does not go into a fleet that cannot execute.

**🟠 S146 is packaged** —
[sprint-146-orphan-fill-lineage](sprints/sprint-146-orphan-fill-lineage.md) (0.80.03,
[DL-72](design-log.md)). A production probe on 2026-07-28 found the orphans **would** probably heal
themselves — no `ExecutionRun` exists for the crashed `PMRun`, so it is still pending — but that
heal is **single-shot**: the same pass writes the `ExecutionRun` that closes the window forever,
whether or not every ticker adopted. The sprint makes the repair deterministic and repeatable
instead of a coincidence with good timing. **It is not urgent the way the retag is**, and it
carries a finding that is worse than the orphans: the position book has diverged badly from the
broker (AMD **111 graph shares against 55 held**, MRVL **open in the graph but held nowhere**),
which promotes DL-71 option B from "natural successor" to the priority successor.

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

- **S146 — orphan Fill lineage repair** ([sprint-146](sprints/sprint-146-orphan-fill-lineage.md),
  0.80.03, [DL-72](design-log.md)). Packaged and ready for a coding agent. Runs *after* the retag,
  since the retag may heal the orphans on its own — in which case S146's job becomes proving that
  and demonstrating the script is a no-op on top, which is still a pass.
- **DL-71 option B — reconcile the book before the analyst decides** (now **non-optional**, and it
  must absorb or follow [DL-73](design-log.md): reconciliation itself mints a new open `Position`
  on every holding change and closes nothing, so fixing *when* the book is read does little while
  the thing writing it manufactures phantoms). The
  broker snapshot is written by execution at stage 5, but the position book is only healed by the
  monitor at stage 6 — one full run later. That is why the analyst scored a nine-hour-stale book on
  07-27 and authored an exit for a position that had already sold. Deferred out of S145 because it
  reorders the cascade and moves position truth across DL-44's ownership line, which is not a change
  to make on top of a live outage. **Deferred, not rejected — and S146's probe raised its
  priority:** the book is not merely stale, it is wrong. AMD carries three `open` Position nodes
  totalling **111 shares against 55 held**; MRVL is **held nowhere at the broker** yet has two
  `open` Positions of 44; ABT 98 vs 96; SCHW 98 vs 196. Every night the analyst scores that.
- **S144's dated fleet enablement** — build + retag at the next `:sNNN`, then set
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
