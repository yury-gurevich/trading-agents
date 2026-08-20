<!-- Agent: planning | Role: the single ranked work queue — what to do next, in order, with provenance -->
# Work queue — the one ranked list

**Reviewed 2026-08-19 20:40 AEST** against `main` @ `b84d221` (`0.90.15`) and the fleet on `s181`.
This review **deleted 11 closed rows**, folded **2 items into their parents**, re-measured every
carried number, and re-ranked.

> **This file is the only ranked queue.** The out-of-repo `..\debt.md` was **deleted 2026-08-19** —
> it was not a second opinion, it was a 2026-08-14 ancestor of this file, and everything in it was
> closed or superseded. That closes STATE's open item (ii) the way it was meant to close: by
> **removing a tracker, not reconciling one**. `docs/STATE.md` `## Next` is narrative around this
> ranking, never a second one. `docs/hardening-backlog.md` owns the dormant security rows and their
> unblock triggers; they appear here only so the ranking is complete.

**Reading it.** The table is **in rank order, best first**. The `#` is a **stable ID, not a rank** —
it never changes, because STATE and the design log cite these numbers. A gap in the sequence means
that item closed.

**Provenance per item:** **[measured 2026-08-19]** means checked against the live spine, the broker
or the code during this review. **[carried]** means the row exists but the claim has not been
re-measured — treat the number as suspect.

---

## The queue

| # | Work | Why it sits here | Size |
| --- | --- | --- | --- |
| 3 | 🚨 **Deliberator concurrency — [S172](sprints/sprint-172-independent-debates-run-independently.md): BUILT and gate-proven at `5bf72c9`, NOT merged — blocked on the live K=4 proof** | *[measured 2026-08-19]* Re-measured on `s181`: sum-of-latency ÷ span **0.95** (worse than the original 0.90) at **124 s per order**, because `effort` reaching the wire in `0.90.02` roughly **doubled** the per-order cost. **The trigger is now measured, not argued: 15 orders breaches the 1800 s grace** (1,854 s); 25 needs 3,091 s against a `le=3600` cap. The last two runs had 9 and 7. **When the grace expires execution submits unvetoed — that happened on `sched-2026-08-19`**, 9 orders to the broker, 6 vetoes arriving 71 s late. Now includes what was item 24. 🟠 **2026-08-20: code is done** — `debate_concurrency=4`, deterministic reassembly, fail-open isolation, shared correlated inbox, peer `maxReplicas=4`; `make ci` 2336 passed / 100.00 %, `GATE PROVEN`. **The only thing missing is the measurement**: the 15-order K=4 run returned `real_debate_count=0` / `failed_open_count=15` on an OpenAI 429. 🪤 **Its deploy left unmerged code on the fleet; rolled back to `s181`.** Merge only after the ratio, headroom and orphan-count measurements come back clean | **awaiting credits, then merge** |
| 18 | 🚨 **The PM has no issuer or correlation dimension** — the risk gates cannot see the whole book | *[measured 2026-08-19]* Two halves. **(a)** `SectorBook.__init__` seeds `_names` from held positions but **never `_deployed`**, so the dollar sector cap counts only the current batch and cross-day exposure can pass 30 % unnoticed — masked today only because `max_names_per_sector=3` binds first. **(b) Wider, and the deliberator has now named it on three consecutive nights:** there is **no issuer or correlation dimension at all**. GOOG vetoed because *"the PM treats GOOG as a new ticker while the portfolio already holds GOOGL"*; INTC for adding to AMD/NVDA with no name-correlation penalty; AMZN because the Retail cap tests declared sector only. **4 of the 6 vetoes on the clean run were this.** 🚨🚨 **PROMOTED 2026-08-20 — this is now the binding constraint on the system trading at all ([DL-119](design-log.md)).** Across the four real binding runs the veto rejected **19 of 26** PM-approved orders (**73 %**), and `verify-2026-08-20-s182-a` approved four and traded **none**. The dominant objection is this item, cited on **four consecutive nights**. 🪤 **Do not soften the veto to restore throughput** — that reintroduces DL-104's advisory posture by the back door and leaves every objection still true. Fix the PM, not the referee | ADR + 1 sprint |
| 27 | ~~**A position filled between runs is unprotected until the run after**~~ **DONE + DEPLOYED** (`S182`, `0.90.16`, `s182`, 2026-08-20) — [DL-118](design-log.md). 🪤 **Live proof still owed**: the defect needs a between-runs fill, so a synthetic fixture cannot exhibit it | At 22:30 on 2026-08-19 the fleet raised three `error` faults — *"unprotected held position CSCO qty=9: no active graph position"* (also MO, NFLX) — yet by the end of that same run all three **were** active `Position` nodes. So `place_broker_stops` runs **before** reconciliation has adopted the run's newly-filled positions, and the stop can only be placed on the *following* run. **Measured consequence right now: 22 positions, 19 stops, $2,147.76 unprotected.** 🪤 **A second, independent blocker was stacked on it** — Alpaca rejected two stop submissions with `403 potential wash trade detected... opposite side order exists`, because open buy limits from a test run existed on the same symbols. **Test orders can block protective stops.** That half is cleared (orders cancelled 2026-08-20). 🚨 Same class as S146's unprotected-ABT incident. **Cause found on packaging and it is structural, not an ordering slip:** `Position` is created by the **monitor (stage 7)**, stops are placed by **execution (stage 6)**. 🪤 `reconcile_run_start` never creates a `Position` — I assumed it adopted holdings and it does not. 🚨 Ownership is a **law question**: the monitor's `laws.md` declares `Position` in `labels_owned` | 1 sprint + possible law cycle |
| 28 | 🚨 **A scanner gate that never ran is indistinguishable from one that passed** — *packaged as [S183](sprints/sprint-183-a-gate-that-did-not-run-says-so.md), 2026-08-20* | [`filters.py:131-135`](agents/scanner/domain/filters.py) — `if "days_to_earnings" in features:` — skips the earnings gate **silently** when the date is absent, and `_days_to_earnings` returns `None` for *unknown* **and** *already past* alike. `max_beta` has the same shape. **Measured: 10 of 98 tickers had an earnings date — 10 % coverage — so ~88 tickers per run pass the gate unevaluated**, and `quality.notes` was empty, so the provider reports it as healthy. 🚨 **The system can buy two days before earnings** whenever the vendor has no date, which is the normal case. Carries a second complaint: `stop_target_mode` is a **bare default, not a `tunable()`** ([settings.py:140](agents/analyst/settings.py)), so S150's fully-built volatility-scaled stop is invisible to the operator. 🪤 **Turning scaled stops on is explicitly out of scope** — that is a champion/challenger experiment, not this fix | 1 sprint |
| 6 | **A real advisory/binding switch** (DL-104 d) — 🟠 **PARTIAL** | *[measured 2026-08-19]* 🚨 **Newly urgent: the veto became binding today by arithmetic, not by design.** DL-116 raised the grace 900 → 1800 so the debate could finish, and `deliberation_status` came back `applied`. But DL-104 had set 900 *deliberately*, as the only no-code way to keep the veto advisory — so the posture is now held in place by **two tunable numbers a busier night could overturn**, with no declared mode anywhere. S175 made every route to an unreviewed order a distinct queryable state; **no mode switch exists** | small |
| 26 | **News is market-wide, and the sentiment score is an unweighted mean of it** — *[diagnosed 2026-08-20, [DL-117](design-log.md)]* | **Diagnosed: it is the provider, and we apply no filter.** Finnhub `/company-news?symbol=X` returns market-wide content and `_parse_news` takes every headline with no relevance test. Measured over 1,533 slots / 99 tickers: **48 % are filed under ≥2 tickers, 19 % under ≥5**; *"Which dow jones stocks are moving on Tuesday?"* is filed under **20**; MRK is **60 %** generic. It moves the number because `score_sentiment` is an **unweighted mean** — re-scoring without the ≥5-ticker headlines shifts **15 tickers by >10 points** and TSLA by **75** (75.0 → 0.0). 🪤 **RETRACTED — my earlier wording "mis-attributed news is buying stocks" was wrong**: every approved order scores *higher* once contamination is removed (CSCO +14.3), so this is **bidirectional noise**, and the risk is mis-ranking and false rejection as much as false approval. **Fix is cheap and vendor-independent** — cross-ticker duplication is computable from the batch at zero API cost. **Needs a decision before speccing:** drop at N=5 (removes 19 % and leaves 1 ticker with no signal) or down-weight (keeps signal, stops the score being a plain mean) | ADR-lite + small |
| 12 | **Fill hygiene — the pending backlog is growing, not shrinking** | *[re-measured 2026-08-19]* 🚨 **The carried number was wrong and stale: 202 pending Fills, not "~122"**, of 211 total — and **121 carry `broker_status=rejected`** while still reading `status=pending`. ✅ **The flag half of this item is CLOSED** — 53 Flags now have **53 `FlagResolution`s** (S178's machinery caught up), so `pending_human_flags` is 0. What remains is the Fill backlog and the `pg_teardown` delete path, still never run on live data — its first real use must be a disposable synthetic run | light + diagnose |
| 20 | **Stop-identity mismatch re-faults every run** | *[re-measured 2026-08-19]* **163 faults, up from 112** — all `warning`, `BrokerStopIdentityMismatch`, now across **9 days** since 2026-08-08, accruing ~12/run. The broker holds the stop open (`broker_stop=True`) while the graph `Fill` for the same key reads `broker_status=rejected`. The sweep **exempts** rather than cancels, which is the safe behaviour. **Not yet determined:** whether the idempotency key is reused across lots or the graph missed a status refresh — decide that before changing anything. 🟢 Warning-level, does not pin `healthy` | 1 small sprint |
| 21 | **`record_deploy.py` trusts the SHA it is handed** — *packaged as [S180](sprints/sprint-180-a-deploy-record-must-name-the-commit-that-was-built.md)* | *[carried, still true]* Recording `s179` with `--git-sha $(git rev-parse HEAD)` wrote a commit that was never built. `projections_currency.py:61` compares that field to the newest main image build, so the dashboard reads the fleet **"behind" while current**. 🪤 **Hand-avoided twice on 2026-08-19** — both the `s181` deploy and its record required me to pin the build's own head SHA manually. That is a workaround holding, not a fix | small |
| 9 | **Verdict-quality gate** — *packaged as [S173](sprints/sprint-173-a-verdict-must-be-reproducible.md)* | *[carried]* **56 % self-agreement** on a binary verdict is the number to beat. ✅ **Unblocked** — it depended on the DL-104 (a)+(b) fixes, which shipped in S175. Runs on the Batch API, where batching actually earns its place. 🪤 Self-agreement is not accuracy: a veto reproducibly wrong scores 100 % | 1 sprint |
| 7 | **S170 / DL-101 — one LLM adapter in the kernel** | *[carried]* **The only dated item: 2026-09-01.** The port and `LLMCall` ledger are kernel; the vendor adapters and factory are not, and are duplicated, so S168's OpenAI fallback reached only the deliberator. 🪤 **Would not have prevented the 2026-08-19 outage** — both providers were down, so no adapter unification helps; do not re-justify this item on that evidence. Also stops `surfaces/dashboard/chat_binding.py` reaching into an agent's adapter | 1 sprint |
| 22 | **A sprint's built/unbuilt state is not machine-checkable** | *[carried]* Closeout placeholders use at least three wordings, so nothing answers "is this spec built?". Cost a wasted handover when I recommended S171 after it had already shipped. **Fix:** one required line (`**Status:** SPEC \| BUILT`) plus a check reconciling it against the INDEX. 🟢 Docs-only; the cost is wasted handovers and wrong ranking | small |
| 10 | **S157 / hardening row O** | *[carried]* 101 law clauses with no test-plan row; assertion E in `check_law_coverage.py` is warn-only and cannot be promoted until the rows exist | 1 sprint |
| 11 | **Hardening row N — delegated-agent sandbox default** | *[carried]* `~/.codex/config.toml` carries `approval_policy = "never"` and `sandbox_mode = "danger-full-access"`. Dormant: every delegated run has overridden it by hand, which is why it has never bitten. **The default is the defect, not the practice** | small |

---

## Closed in this review

Removed from the table rather than left struck through. Detail lives in each sprint doc and the
design log; nothing here needs tracking any more.

| # | What | Closed by |
| --- | --- | --- |
| 1 | A deploy must not discard operator config | S169, `0.90.10`, deployed `s176a` — the guard *refused* and named all three keys |
| 2 | The 42-bar history gap | S174, `0.90.07` — 202 bars live, SMA-200 computed in production for the first time |
| 4 | Veto context correctness (DL-104 a+b) | S175, `0.90.08`, deployed `s176a` |
| 5 | A partial fill can never upgrade | S176, `0.90.09`, deployed `s176a`. 🪤 No live proof possible — 0 of 188 Fills have ever been partial |
| 8 | The SCAN-OBS-01 shape sweep | 2026-08-14, DL-111 — 13 rows not 17; 5 demoted, 2 false in code (DRIFT-039/040) |
| 13 | Doc drift | `bf928ca` |
| 14 | Sentiment counts read as article counts | DL-112, `0.90.11`, deployed `s176b` |
| 15 | Broker↔graph divergence | **Not a defect** — graph active == broker 19/19; my claim was retracted |
| 16 | Debate context unit/scope sweep | S177, `0.90.12`, deployed `s177`, DL-113 |
| 17 | 45 unresolved critical Flags pin `healthy=false` | S178, `0.90.13` — severity follows persistence; **53 Flags now have 53 resolutions** |
| 19 | `open_incidents` is the only lock on `healthy` | S179, `0.90.14`, deployed `s179` |
| 23 | One canceled test order red-lights the fleet nightly | **S181, `0.90.15`, deployed `s181`, proven live** — sweep #1 wrote the ack and one fault, sweep #2 wrote neither |
| 24 | Nine orders reached the broker unvetoed | **Folded into item 3** — it is the cost of the serialization, not a separate defect. Mitigated 2026-08-19 by grace 900 → 1800; the fix is still S172 |
| 25 | The deliberator has no working LLM provider | **Folded into the standing note below** — it was an outage, not a work item. Operator restored credits 2026-08-19 |

---

## Standing operational notes

Not work items — conditions to know about.

**🚨 There is no fallback LLM provider until 2026-09-01.** Measured 2026-08-19: OpenAI ran to
`HTTP 429 "no credits remaining"` mid-morning and Anthropic returns `HTTP 400 "You have reached your
specified API usage limits… regain access on 2026-09-01"`. With both down **every debate fails open
and no run can pass acceptance**, because `failed_open_count > 0` fails on its own. The operator
restored credits; a 9-order run costs **$0.46**, so the current balance is roughly ten runs.
🪤 **An exhausted account presents as `no deliberator peer reply received`**, which reads exactly
like a timeout — it cost me a wrong diagnosis and a wasted run (DL-116 amendment). **Read
`DeliberationRun.failed_open_reason` before the latency metrics.**

**Pre-production, so test runs are allowed.** Widen the KEDA window or force `minReplicas 1`, fire a
run, restore. 🪤 **The drop sweep runs *first*, before anything else** — firing a run before the
13:30 UTC open cancels any pending order from a previous run. 🪤 A manual dispatch of
`sched-YYYY-MM-DD` **consumes that night's scheduled run** (DL-110); use a non-scheduled run id if
the schedule must survive.

---

## Two notes on the ordering

**Item 3 is first, and item 18 is a close second on different grounds.** S172 is ranked top because
its failure mode is *orders reaching the broker unreviewed*, it is measured one busy night away, and
the spec is written and handed over. Item 18 is the only item where being wrong **costs money** —
but it needs an ADR before any code, so starting it does not block starting S172. Defensible either
way; say so if they swap.

**Ranked below the fixes on purpose:** items 9, 7, 22, 10 and 11 are all real, and none of them can
put a wrong order at the broker. Item 7 is the only one with a date (**2026-09-01**), which is why
it sits above the docs and law-coverage work rather than at the bottom.
