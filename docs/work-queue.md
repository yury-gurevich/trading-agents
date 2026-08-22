<!-- Agent: planning | Role: the single ranked work queue — what to do next, in order, with provenance -->
# Work queue — the one ranked list

**Re-reviewed 2026-08-22 15:10 AEST** against `main` @ `12d15dc` (`0.91.01`) and the fleet on `s184`,
after `sched-2026-08-21` ([DL-125](design-log.md)). This review **promoted item 6 to first**, closed
item 18, corrected item 3's "unblocked" claim, and re-measured items 20 and 27.

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
| 6 | 🚨 **A real advisory/binding switch** (DL-104 d) — **PROMOTED TO FIRST 2026-08-22, PACKAGED as [S185](sprints/sprint-185-the-veto-posture-is-declared-not-arithmetic.md) the same day** | *[measured 2026-08-22, [DL-125](design-log.md)]* 🚨 **The referee is down until 2026-08-30 on an API billing failure, so for ~6 scheduled sessions the system trades unvetoed while the gate goes red every night for something that is not a defect.** That is no longer the theoretical failure mode this item was filed against — *"trains the operator to read a real fault as noise"* — it is the nightly one, and it is the single thing that most damages the evidence discipline the etalon bar is actually measured on. **A declared `advisory` posture makes those six nights honest**: unvetoed submission becomes a *stated* mode with a truthful green, instead of six reds everyone learns to skip. 🪤 **Scope discipline — this is a declared mode, not a softened veto.** DL-119 explicitly rejected lowering the bar; declaring the posture is the opposite move, and when credit returns the switch flips back to `binding` as a recorded decision rather than an arithmetic accident. *[carried from 2026-08-19]* The veto became binding by arithmetic: DL-116 raised the grace 900 → 1800 while DL-104 had set 900 deliberately to keep it advisory, so the posture rests on **two tunable numbers a busier night could overturn**. S175 made every route to an unreviewed order a distinct queryable state; **no mode switch exists**. ✅ **SPEC'd 2026-08-22** — four design decisions handed over unmade (is posture a tunable or a **mode selector**; does `binding` drop or hold; what the gate asserts per posture; does the five-state vocabulary survive), and two measured law silences to file as drift: **execution's `laws.md` has no deliberation clause at all**, and `deliberation_grace_seconds` has **no PARAM row**. 🪤 Sized **M, not small** — the earlier estimate predated the law cycle and the full-`up` deploy | **M, with Codex** |
| 3 | 🚨 **Deliberator concurrency — [S172](sprints/sprint-172-independent-debates-run-independently.md): BUILT and gate-proven at `5bf72c9`, NOT merged — blocked on the live K=4 proof** | *[measured 2026-08-19]* Re-measured on `s181`: sum-of-latency ÷ span **0.95** (worse than the original 0.90) at **124 s per order**, because `effort` reaching the wire in `0.90.02` roughly **doubled** the per-order cost. **The trigger is now measured, not argued: 15 orders breaches the 1800 s grace** (1,854 s); 25 needs 3,091 s against a `le=3600` cap. The last two runs had 9 and 7. **When the grace expires execution submits unvetoed — that happened on `sched-2026-08-19`**, 9 orders to the broker, 6 vetoes arriving 71 s late. Now includes what was item 24. 🟠 **2026-08-20: code is done** — `debate_concurrency=4`, deterministic reassembly, fail-open isolation, shared correlated inbox, peer `maxReplicas=4`; `make ci` 2336 passed / 100.00 %, `GATE PROVEN`. **The only thing missing is the measurement**: the 15-order K=4 run returned `real_debate_count=0` / `failed_open_count=15` on an OpenAI 429. 🪤 **Its deploy left unmerged code on the fleet; rolled back to `s181`.** Merge only after the ratio, headroom and orphan-count measurements come back clean. 🪤 **RE-BLOCKED 2026-08-22 — the "UNBLOCKED 2026-08-20" claim below is withdrawn.** It read: *"the operator raised the Anthropic cap and the deliberator now runs `claude-opus-5`; nothing stands between this and merge but the measurement."* The cap was raised; the **credit balance then ran out on 2026-08-20** (`HTTP 400`, [DL-125](design-log.md)), and the operator cannot restore it **until 2026-08-30**. The K=4 measurement needs real debates, so this cannot merge before then — **do not attempt the run, it will return `real_debate_count=0` like the last two.** 🪤 Running it needs `s172` images redeployed and peer `maxReplicas=4` restored, which puts unmerged code on the fleet again — reversible by retag to `s182`, as done on 2026-08-20 | **ready to prove, then merge** |
| 27 | ~~**A position filled between runs is unprotected until the run after**~~ **DONE + DEPLOYED** (`S182`, `0.90.16`, `s182`, 2026-08-20) — [DL-118](design-log.md). 🪤 **Live proof still owed — and 2026-08-21 was checked and did NOT supply it.** The run looked like the case: INTC/NEE/XOM filled between runs, raised `missing_graph_position` divergence flags at run start, and execution placed three protective stops on them at 22:40. **But each stop carries `stop_pct_source=position`**, i.e. it came from a `Position` that `position_sync` had already created at 22:31:52 — **eight minutes before execution ran** — so the Fill+OrderIntent fallback never fired. 🚨 **Do not re-check it this way.** Broker reconciliation now adopts holdings at run start, which means it *closes the window* S182 was built for; the proof needs a fill that lands **after** `position_sync` in the same run, or the execution log naming the derivation path | At 22:30 on 2026-08-19 the fleet raised three `error` faults — *"unprotected held position CSCO qty=9: no active graph position"* (also MO, NFLX) — yet by the end of that same run all three **were** active `Position` nodes. So `place_broker_stops` runs **before** reconciliation has adopted the run's newly-filled positions, and the stop can only be placed on the *following* run. **Measured consequence right now: 22 positions, 19 stops, $2,147.76 unprotected.** 🪤 **A second, independent blocker was stacked on it** — Alpaca rejected two stop submissions with `403 potential wash trade detected... opposite side order exists`, because open buy limits from a test run existed on the same symbols. **Test orders can block protective stops.** That half is cleared (orders cancelled 2026-08-20). 🚨 Same class as S146's unprotected-ABT incident. **Cause found on packaging and it is structural, not an ordering slip:** `Position` is created by the **monitor (stage 7)**, stops are placed by **execution (stage 6)**. 🪤 `reconcile_run_start` never creates a `Position` — I assumed it adopted holdings and it does not. 🚨 Ownership is a **law question**: the monitor's `laws.md` declares `Position` in `labels_owned` | 1 sprint + possible law cycle |
| 29 | **One agent honours a law its sibling ignores: `scanner.benchmark_ticker`** — *[swept 2026-08-20, [DL-120](design-log.md) — headline RETRACTED same day]* | 🪤 **This row originally claimed six bare settings were defects and that two agents had made "the same mistake". That was backwards.** `stop_target_mode` and `order_price_tolerance_mode` are declared **`NO (mode selector)`** in their locked laws, in identical deliberate wording citing ADR-0013, and `curator.predictor_strategy` is `NO` (structural). One convention applied consistently, not a repeated error — my audit classified by code shape and never opened `laws.md`, which CLAUDE.md requires. **What actually survives:** 🚨 the **scanner law declares `benchmark_ticker` `YES`** (a tunable) while the scanner code leaves it a bare default — and the *analyst* honours the same law row correctly, so one agent obeys and the other does not; **`provider.alpaca_data_feed` / `ingest_ohlcv_only` appear in no law at all** (the provider `laws.md` is LOCKED v1, so they were added post-lock — a law cycle, not a code edit); and `execution.stage` is missing from the execution PARAM table (**unverified** whether it belongs there). 🟢 `execution.stage` is not dangerous — `run.py:51` rejects every non-paper stage. ✅ **RE-VERIFIED 2026-08-22 against the files, and the shape changed again.** **(a) `scanner.benchmark_ticker` CONFIRMED** — both the scanner *and* analyst laws declare it `YES`; `agents/analyst/settings.py:93` registers `tunable(`, `agents/scanner/settings.py:53` is a bare `= "SPY"`. One law row, one agent obeys it, the other does not. Code fix, no law change. **(b) `provider.alpaca_data_feed` + `ingest_ohlcv_only` CONFIRMED** — both are plain `Field(default=…)` in `agents/provider/settings_feeds.py:64,93` and appear **nowhere** in the provider `laws.md`, which is **LOCKED v1**, so they were added post-lock → a law cycle, not a code edit. 🚨 **(c) `execution.stage` RETRACTED — it is already there**, `agents/execution/laws/laws.md:310`, declared `NO (config)`. The row called it *unverified*; it is now verified and it is not a defect. 🚨 **A fourth instance arrived from S185's spec work:** `execution.deliberation_grace_seconds` is a registered `tunable()` with **no PARAM row** — same class as (b), opposite direction to (a). **So the real item is that PARAM tables and code drift in BOTH directions with nothing checking**, across three agents. **Packaged as [S187](sprints/sprint-187-a-parameter-is-declared-once.md)**, whose durable half is a `make ci` check that reconciles every PARAM row against its settings field | small + 1 law cycle |
| 26 | **News is market-wide, and the sentiment score is an unweighted mean of it** — *[diagnosed 2026-08-20, [DL-117](design-log.md)]* | **Diagnosed: it is the provider, and we apply no filter.** Finnhub `/company-news?symbol=X` returns market-wide content and `_parse_news` takes every headline with no relevance test. Measured over 1,533 slots / 99 tickers: **48 % are filed under ≥2 tickers, 19 % under ≥5**; *"Which dow jones stocks are moving on Tuesday?"* is filed under **20**; MRK is **60 %** generic. It moves the number because `score_sentiment` is an **unweighted mean** — re-scoring without the ≥5-ticker headlines shifts **15 tickers by >10 points** and TSLA by **75** (75.0 → 0.0). 🪤 **RETRACTED — my earlier wording "mis-attributed news is buying stocks" was wrong**: every approved order scores *higher* once contamination is removed (CSCO +14.3), so this is **bidirectional noise**, and the risk is mis-ranking and false rejection as much as false approval. **Fix is cheap and vendor-independent** — cross-ticker duplication is computable from the batch at zero API cost. ✅ **DECIDED 2026-08-22 — down-weight each headline by `1 / n_tickers`** ([DL-127](design-log.md)), chosen on a measured downstream comparison rather than taste. 🚨 **Two carried numbers here were wrong and are corrected:** slots filed under ≥5 tickers are **23.4 %**, not 19 %; and a drop would leave **4** tickers with no sentiment at all (`CMCSA`, `GD`, `PEP`, `TXN`), not 1. Measured on `sched-2026-08-21` through the real pipeline (composite → confidence → the 0.600 floor), with the recomputed baseline reproducing **every** stored confidence to 3 dp: down-weight loses **no** ticker its signal (drop loses 4), discards **no** slots (drop discards 23.4 %), and its worst downstream confidence shift is **0.034 vs drop's 0.065** — gentler on the decision boundary while using more evidence. 🪤 Drop's one floor crossing (`CMCSA` 0.638→0.573) is an **artefact of information loss**, not a correction. 🪤 `1/n` is parameter-free, so unlike `N=5` it cannot drift or be quietly retuned. **Packaged as [S186](sprints/sprint-186-a-headline-about-twenty-companies-is-not-news-about-one.md)** | ADR-lite + small |
| 12 | **Fill hygiene — the pending backlog is growing, not shrinking** | *[re-measured 2026-08-19]* 🚨 **The carried number was wrong and stale: 202 pending Fills, not "~122"**, of 211 total — and **121 carry `broker_status=rejected`** while still reading `status=pending`. ✅ **The flag half of this item is CLOSED** — 53 Flags now have **53 `FlagResolution`s** (S178's machinery caught up), so `pending_human_flags` is 0. What remains is the Fill backlog and the `pg_teardown` delete path, still never run on live data — its first real use must be a disposable synthetic run | light + diagnose |
| 20 | **Stop-identity mismatch re-faults every run** | *[re-measured 2026-08-22]* **Still accruing every run and the rate is not stable**: by day — 08-08 **40**, 08-10..08-17 **10/run**, 08-18 **24**, 08-19 **39**, 08-20 **52**, 08-21 **13**. All `warning`, `BrokerStopIdentityMismatch`, unbroken across **12 days** since 2026-08-08. 🪤 The 08-21 drop to 13 is not improvement — it tracks how many stops the sweep saw, not how many mismatched. *[was: 163 faults across 9 days, ~12/run — the per-run figure was an average that hid a 5× spread]* The broker holds the stop open (`broker_stop=True`) while the graph `Fill` for the same key reads `broker_status=rejected`. The sweep **exempts** rather than cancels, which is the safe behaviour. **Not yet determined:** whether the idempotency key is reused across lots or the graph missed a status refresh — decide that before changing anything. 🟢 Warning-level, does not pin `healthy` | 1 small sprint |
| 21 | **`record_deploy.py` trusts the SHA it is handed** — *packaged as [S180](sprints/sprint-180-a-deploy-record-must-name-the-commit-that-was-built.md)* | *[carried, still true]* Recording `s179` with `--git-sha $(git rev-parse HEAD)` wrote a commit that was never built. `projections_currency.py:61` compares that field to the newest main image build, so the dashboard reads the fleet **"behind" while current**. 🪤 **Hand-avoided twice on 2026-08-19** — both the `s181` deploy and its record required me to pin the build's own head SHA manually. That is a workaround holding, not a fix | small |
| 9 | **Verdict-quality gate** — *packaged as [S173](sprints/sprint-173-a-verdict-must-be-reproducible.md)* | *[carried]* **56 % self-agreement** on a binary verdict is the number to beat. ✅ **Unblocked** — it depended on the DL-104 (a)+(b) fixes, which shipped in S175. Runs on the Batch API, where batching actually earns its place. 🪤 Self-agreement is not accuracy: a veto reproducibly wrong scores 100 % | 1 sprint |
| 7 | **S170 / DL-101 — one LLM adapter in the kernel** | *[carried]* **The only dated item: 2026-09-01.** The port and `LLMCall` ledger are kernel; the vendor adapters and factory are not, and are duplicated, so S168's OpenAI fallback reached only the deliberator. 🪤 **Would not have prevented the 2026-08-19 outage, nor the 2026-08-20 one** — a provider switch only helps if some provider has credit, and **both OpenAI and Anthropic ran dry inside three days** ([DL-125](design-log.md)). Do not re-justify this item on either outage. 🪤 Its 2026-09-01 date is about the Anthropic *usage cap*; the *credit* outage is a separate, earlier constraint clearing 2026-08-30. Also stops `surfaces/dashboard/chat_binding.py` reaching into an agent's adapter | 1 sprint |
| 22 | **A sprint's built/unbuilt state is not machine-checkable** | *[carried]* Closeout placeholders use at least three wordings, so nothing answers "is this spec built?". Cost a wasted handover when I recommended S171 after it had already shipped. **Fix:** one required line (`**Status:** SPEC \| BUILT`) plus a check reconciling it against the INDEX. 🟢 Docs-only; the cost is wasted handovers and wrong ranking | small |
| 10 | **S157 / hardening row O** | *[carried]* 101 law clauses with no test-plan row; assertion E in `check_law_coverage.py` is warn-only and cannot be promoted until the rows exist | 1 sprint |
| 30 | **15 law clauses say "matches the contract file exactly" — which is unfalsifiable** | *[measured 2026-08-20, [DL-121](design-log.md)]* The `laws → test-plan → tests` loop is CI-enforced; **contracts are outside it**. Zero of the 24 files in `contracts/` cite a clause ID, and the only link is 16 clauses asserting *"X matches `contracts/<agent>.py` exactly"* — so the file is both the claim and the oracle, and a contract can change with every test still green. 🚨 **Not theoretical:** `PM-NEV-09` turned out to be unexpressible in `GateOutcome` (`passed: bool`, two states), and the scanner's `FilterVerdict` collapses *"did not run"* and *"passed"* into the same bytes — **that is the S183 bug**, in a second agent, which neither law book prevented. `PM-TYP-03` is rewritten (v1.3); **15 remain**. Each rewrite enumerates the required fields and will demote greens — the conventions §7a trade, accepted knowingly | 1 chore per 3–4 agents |
| 31 | **A green branch gate does not mean CodeQL-clean — and the same rule has now landed twice** | *[measured 2026-08-20, [DL-123](design-log.md)]* `codeql.yml` runs **only on `main`**, so a branch can be `GATE PROVEN` on CI + Security Findings while the analysis that finds a whole defect class has not run. 🚨 **Twice in four days:** `py/mismatched-multiple-assignment` #177 (S181-era, [DL-110](design-log.md)) and **#187** raised by the S184 merge — same rule, same package, same one-line shape (a fixed-arity unpack of a call that can return `()`). Each cost a red gate on the *next* branch and a merge-then-verify. **A trap that fires twice is a missing check.** Options: run CodeQL on branches (obvious, cost unmeasured — scan minutes plus the branch-vs-main alert-state semantics DL-110 already found confusing), or a cheap local guard in `make ci` for this shape with a `gate_selftest` case | 1 chore |
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
| 18 | The PM has no issuer or correlation dimension | **S184, `0.91.00`, deployed `s184`.** 🟩 **PM half proven live 2026-08-21, unattended**: GOOG and GOOGL hit the same batch, GOOG's approved $1025.19 counted against GOOGL as `issuer=alphabet`, and GOOGL's sizing gate read **1.67 % > 1 %, `outcome=failed`** — pre-S184 both would have passed at 1.00 % and 0.67 % and opened two positions in one company ([DL-122](design-log.md) amendment). 🚨 **The reason this item was promoted — ADR-0023's prediction that the 73 % veto rate falls — is NOT proven and cannot be measured until 2026-08-30** ([DL-125](design-log.md)). Tracked there, not here: the *work* is done |
| 28 | A scanner gate that never ran is indistinguishable from one that passed | **S183, `0.91.02`, merged `4187770` 2026-08-22**, `GATE PROVEN` for `948f1bd`. `Candidate` and `FilterVerdict` carry `skipped_filters`; no-earnings-date is attested, a known **past** date is an evaluated pass, thin beta history is attested, and the debate packet renders the stop's basis. 🪤 **The mid-build correction held** — `stop_target_mode` stayed a bare default, as the locked analyst law requires. 🚨 **My spec omitted the law cycle** although the sprint changed `contracts/scanner.py` under a LOCKED law book; closed at merge rather than filed — `SCAN-OUT-06`/`SCAN-OUT-07`, scanner laws **v1.1**, rollup **18 / 41**, and `DRIFT-047` for the `SCAN-TYP-01` clause the change slipped under (item 30's class). The omission is now a required section in [`_TEMPLATE.md`](sprints/_TEMPLATE.md) |
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

**🚨 THE DELIBERATOR IS DOWN UNTIL 2026-08-30 — operator-stated, not estimated (2026-08-22).** The
Anthropic **credit balance** is exhausted (`HTTP 400 "Your credit balance is too low"`), first seen on
`sched-2026-08-20` and again on `sched-2026-08-21`, and it cannot be topped up before **2026-08-30**.
🪤 **This is a different constraint from the 2026-09-01 date** that appears elsewhere in this file —
that one is the Anthropic *usage cap*; this is *credit*, and it clears earlier. **Both providers have
run dry inside three days**: OpenAI `HTTP 429 "no credits remaining"` on 2026-08-19, Anthropic
`HTTP 400` on 2026-08-20. *[Superseded: "the operator restored credits; roughly ten runs of balance"
— measured 2026-08-19, false by the next evening. A 9-order run costs **$0.46**, so a balance
expressed in runs is not a durable claim; state the date instead.]*

**Consequences while it lasts, all of which are expected and none of which are defects.** Every
scheduled run fails acceptance on `debate_coverage: 0.0 < 1.0` and `failed_open_count > 0`; every
run submits its PM-approved orders **unvetoed**; `compute_health` returns `healthy=false` on the
three `deliberator-manager` error incidents each run raises. 🚨 **Do not diagnose these as new
faults, and do not fire test runs to investigate them** — they will reproduce exactly.
🪤 **An exhausted account presents as `no deliberator peer reply received`**, which reads exactly
like a timeout — it cost me a wrong diagnosis and a wasted run (DL-116 amendment). **Read
`DeliberationRun.failed_open_reason` before the latency metrics.**

**🪤 `healthy=false` is NOT the Flag backlog — that premise is stale.** Re-measured 2026-08-22 with
the real predicate (`agents/supervisor/domain/health.py::compute_health`) rather than raw props:
`pending_human_flags` = **0**, because all **60** Flags carry a `FlagResolution` (items 17 and 19
closed this via S178/S179). `Flag.status` stays `pending` **by design** — the resolution is a separate
node — exactly like `Position.status` staying `open`. What actually pins `healthy=false` is
`open_incidents`, today **5**: 3 deliberator billing faults + 2 execution (`cancel_stop` HTTP 422, and
the `DeliberationFailedOpenSubmit` fault). 🚨 **Anything that still ranks a critical-Flag sweep on
"it pins healthy" is citing a dead premise** — audit on the contract predicate, never on raw props.

**Pre-production, so test runs are allowed.** Widen the KEDA window or force `minReplicas 1`, fire a
run, restore. 🪤 **The drop sweep runs *first*, before anything else** — firing a run before the
13:30 UTC open cancels any pending order from a previous run. 🪤 A manual dispatch of
`sched-YYYY-MM-DD` **consumes that night's scheduled run** (DL-110); use a non-scheduled run id if
the schedule must survive.

---

## Two notes on the ordering

**Item 6 is first as of 2026-08-22, and the reason is the outage, not the item's own merit.** With
the deliberator down until 2026-08-30 the next ~6 scheduled sessions each produce a red gate for a
non-defect and a batch of unvetoed orders. Item 6 is the only queued item that changes what those six
nights *mean*, and it needs no LLM to build or to prove. 🪤 **It is also the item most easily
mis-built**: a declared posture, not a softened veto — see the row.

**Item 3 dropped from first because it is blocked, not because it got smaller.** S172's failure mode
is still *orders reaching the broker unreviewed* and its spec is still handed over; its K=4
measurement simply cannot run without a working provider. It returns to the top on 2026-08-30.
🪤 **Do not re-rank it up on urgency** — urgency it has, availability it does not.

**Item 18 is closed.** S184 shipped and its PM behaviour is proven live; what remains is a
*prediction* about the veto rate, which is evidence owed rather than work queued, and lives in
[DL-119](design-log.md)/[DL-125](design-log.md).

**Item 28 is closed, and it left a standing fix behind it.** S183 shipped, but its spec never asked
for the law cycle a `contracts/` change owes — caught only at merge. That is now a mandatory,
answer-before-you-code section in [`_TEMPLATE.md`](sprints/_TEMPLATE.md), which every new sprint is
copied from. 🪤 **Item 22 (a sprint's built/unbuilt state is not machine-checkable) is partly
addressed there too** — the template pins one `**Status:** SPEC | BUILT | MERGED` line — but the
reconciling check the row asks for is still unbuilt, so the row stays open.

**Ranked below the fixes on purpose:** items 9, 7, 22, 10 and 11 are all real, and none of them can
put a wrong order at the broker. Item 7 is the only one with a date (**2026-09-01**), which is why
it sits above the docs and law-coverage work rather than at the bottom. 🪤 **Item 9 (S173) is also
provider-blocked until 2026-08-30** — it needs the Batch API. **Items 28, 29, 26, 12, 20, 21, 22, 30,
31 and 11 are not**, and they are what the next six sessions can actually ship.
