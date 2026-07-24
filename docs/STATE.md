# Project State

**Last updated:** 2026-07-24 11:15 AEST · **Version:** 0.74.03 · **🟢 THE LOOP CLOSED (2026-07-24).** The first sell **FILLED** — `ABT 98 @ $101.35`, entry $100.78, **≈ +$55.81 realized** — `regt_buying_power` recovered **0 → $32,919.70**, and a buy cleared the broker again (`SCHW ×98`, `submitted=1 rejected=0`). Capital now recycles. The four stranded positions are **back in the book and scored** (`scored=10`), ABT closed **by broker evidence**, and three fresh close decisions stranded **nothing**. Lifetime broker sell count went **0 → 1**: `ABT sell qty=98 accepted` reached Alpaca from run `check-s136-sell` on fleet `:s136`, via analyst `ABT sell 0.62` → PM `ABT sell qty=98` **and** `SCHW buy qty=99` in one `OrderIntentSet` → the existing buy rail (ADR-0016). The nightly re-buy accumulator that walked BAC 171→338→503 into a `regt_buying_power=0` wall is **stopped** — held names now return `hold` and the PM skips them. **Scope the claim honestly:** the sell needed a forced `exit_confidence_floor=0.625`, so the *rail* is proven and the *exit strategy* is still the agreed placeholder; and the monitor's own stop/target closes are **still undispatched** — 4 positions (AMD, CSCO, HPE, MRVL) are stranded and the count grows each run until ADR-0015's fill-keyed closure is built. `sched-2026-07-20` (dispatcher `dispatcher-cron-29743110`, fleet on `:s130`) ran **7/7 → ACCEPTANCE PASS** with **ZERO `*_degraded` notes** — the first fully-fed scheduled run since 07-07, and the proof S128 mattered: all four enrichment feeds populated (1867 headlines; the earnings-window filter actually fired), sentiment restored, the analyst scoring on **full signal**, and the chronic all-reject no-trade signature flipped into **5 buys** (USB/BAC/PYPL/WFC/ABT, conf 0.61–0.68 lifted over the 0.600 floor by sentiment). S130's hardened DHI runtimes booted and ran the whole chain; 0 Escalations. Fleet standing on `:s130` (built `d0b0d3a`); **P12 clean-news runway accumulating since 2026-07-20**. **Now:** S133 **shipped** (0.71.07) — the **last shared credential is closed**: Service Bus access is now per-agent entity-level SAS, delivered and flipped live, and the hardening backlog has **no open rows**. The security gate finally ran on sprint code — via a PR at the time, and **since DL-56 it runs on push to every branch**, so worktree-and-merge-locally is gated without any PR. **Fleet on `:s139`** (`9a8a88c`, 0.74.03). **Pending unattended:** the `SCHW ×98` buy fills at the next open; tonight's 22:30 UTC run uses a fresh `sched-2026-07-24` key. **Known open:** the monitor's stop/target closes still reach **no broker** (DL-60) — they no longer strand, but they now re-decide every run forever, and the analyst says `hold` on the very names the monitor says close. **Which decider wins is unsettled by ADR-0016 and is the next real question.** Last night's scheduled run was a **silent no-op**: the dispatcher `Succeeded` but day-key-deduped onto a `sched-` id a manual run had already consumed — use distinct run ids for manual runs. **Hardening backlog reopened (2026-07-23):** rows **L** (`make ci` cannot fail on a CVE — the Makefile's `-uv run pip-audit` ignores its exit status), **M** (a pushed branch produced **zero** workflow runs; the branch-is-the-gate rule can be defeated by an infrastructure miss, not just a process mistake), and **N** (delegated coding agents default to `danger-full-access` with `approval_policy = never`; every run so far overrode it with an explicit sandbox flag, but the protection lives in remembering that flag). **Pending operator:** the standing broker-divergence Flags were **not** noise — they were correctly reporting an exit that never executed (DL-58); do **not** ack them until the AMD position is resolved. *Correction:* STATE had carried "S131 per-role DSN flip not yet applied" since 07-21 — **it was wrong**; the flip ran during S131 and a full 14/14 live probe on 07-22 proves every app connects under its own `ta_*` role (DL-54).

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

**No sprint is in flight.** The hardening backlog has **no open rows** — S133 closed the last one.
Queued work is in *Next*; the standing operator items below are the only outstanding threads.

**Fleet:** standing on `:s130` (built `d0b0d3a`), self-driving in paper mode — the calendar-gated
22:30 UTC `dispatcher-cron` fires nightly, KEDA scale-to-zero, idle ≈ $0. Nothing since S130 has
needed a retag: S131–S134 changed roles, tests and CI, not runtime images. **Both scoped-credential
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

- **`chore-wsl2-dev-env`** (packaged, branch pushed — **next up**, now that S133 has landed and no
  sprint branch is in flight) — move the dev loop to WSL2 for
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
