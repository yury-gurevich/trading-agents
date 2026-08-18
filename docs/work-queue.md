<!-- Agent: planning | Role: the single ranked work queue — what to do next, in order, with provenance -->
# Work queue — one consolidated list

**Consolidated 2026-08-10 19:09 AEST · last reconciled 2026-08-15 18:40 AEST.** This replaces every
earlier tier, section and Monday note in this file. Nothing below is a duplicate of anything above it,
because there is nothing above it.

**Reconciled 2026-08-15** against `main` @ `b38fcdf` (`0.90.12`) and the fleet on `s177`: items **1, 4,
5, 14, 16** moved to DONE **+ DEPLOYED**; item **15** closed as **not a defect**; item **18** narrowed to
the behaviour half only (S177 fixed the label); items **17** and **18** added; row order restored.

Provenance is marked per item: **[measured today]** means I checked it against the live spine or the
code in this session; **[carried]** means it comes from `docs/hardening-backlog.md` or an earlier
session and I have confirmed the row exists but not re-measured the claim.

> **Durable home — moved into the repo 2026-08-15** (was an untracked root file with no history and
> invisible to a fresh session). It now has version history, survives a clone, and is reviewed like
> any other doc. **This file owns the ranking**; `docs/hardening-backlog.md` owns the dormant
> security/quality rows and their unblock triggers, which appear here only so the ranking is
> complete. 🚨 **`docs/STATE.md` `## Next` still carries a second ranked list** — that is the drift
> CLAUDE.md warns about, and collapsing the two is STATE's own open item (ii). Until that happens,
> **this file is the ranking of record** and STATE's `## Next` is the narrative around it.

---

## Closed since this file was last written

Struck-through entries are gone rather than hidden, so nothing looks lost:

- **The ten flatten exits** — filled **10/10**, book flat, equity **$102,464.21**. The opening
  "live thread" is resolved; Monday's run does have the cash to buy.
- **DL-94, `pg_teardown` half-deletes** — shipped as `chore-teardown-leaves-no-orphans`, `v0.89.04`.
  DL-94's own prescribed fix was measured insufficient. *One residue survives as item 12.*
- **The module-size trio** — shipped as `chore-split-modules-before-the-block`, `v0.89.05`. All three
  now under the 150-line warn line; the split also found the unpinned gate precedence (DL-96).
- **Sprint-doc status drift** — 11 rows corrected across `sprints/INDEX.md` and `README.md`.
- **Ten missing version tags** — 91 tags cut (13 recent + 78 backfilled); gap check returns 0.

---

## The queue

| # | Work | Why it sits here | Size |
| --- | --- | --- | --- |
| 1 | ~~**S169 / DL-100** — a deploy must not discard operator config~~ **DONE + DEPLOYED** (`s176a`, 2026-08-15) — `0.90.10`. Tunables + cron now live in `orchestration/packs/trading_tunables.json`; `up` refuses before its first create if it would drop a live env key, naming it. **Live half CLOSED** — deployed `s176a` 2026-08-15 via full `up` with `-DropEnv`; the guard *refused* first, naming all three keys | ~~Only item where being wrong costs money, and it fires on *every* deploy~~ | ~~1 sprint~~ |
| 2 | ~~**The 42-bar history gap**~~ **DONE** — S174, `0.90.07`, **proven live 2026-08-13**: 98 tickers × **202 bars** (was 41), `sma_distance_pct` + `ema_spread_pct` computed in production for the first time ever | ~~Silently degrades every decision the system makes, right now~~ | ~~1 sprint~~ |
| 3 | **Deliberator concurrency + `max_rounds`** — *packaged as S172* | Hard blocker on widening the funnel. Serialization **proven** (ratio 0.90). 🪤 **Re-measured 2026-08-15:** the 60 s timeout holds at **0 fail-opens** (n=45, median 12.8 s, **max 46.2 s**) — so this is no longer urgent for *correctness*, only for *throughput*; the 46.2 s tail against a 60 s ceiling is the number to watch | 1 sprint + 1 tunable + 1 small chore |
| 4 | ~~**Veto context correctness** (DL-104 a+b)~~ **DONE + DEPLOYED** (`s176a`, 2026-08-15) — S175, `0.90.08`. Invented ATR fragment deleted; explicit portfolio/batch-absence boundary added | ~~Removes ~6 of 15 false vetoes for a very small diff~~ | ~~small~~ |
| 5 | ~~**Hardening row P** — a partial fill can never upgrade~~ **DONE + DEPLOYED** (`s176a`, 2026-08-15) — S176, `0.90.09`. Narrow rule: only `partial` → `filled` may update; terminal statuses immutable; final price now drives realized PnL. 🪤 **No live proof possible** — 0 of 188 production Fills have ever been partial | ~~Real defect, dormant only because no fill has ever been partial~~ | ~~small~~ |
| 6 | **A real advisory/binding switch** (DL-104 d) — 🟠 **PARTIAL, S175 (deployed `s176a`).** Every route to an unreviewed order is now a *distinct, queryable* `deliberation_status` (`applied_failed_open` / `proceeded_unvetoed`) with its own fault, and ADR-0022 was amended to say so. **No mode switch exists** — the veto is still always-permissive | The fault is no longer a proxy for "advisory"; a binding mode remains unbuilt | small |
| 7 | **S170 / DL-101** — one LLM adapter in the kernel | The only dated item: **2026-09-01** | 1 sprint |
| 8 | ~~**The SCAN-OBS-01 shape sweep**~~ **DONE** — 2026-08-14, [DL-111]. Measured **13 rows, not 17** (9 `audit` + 4 `observable`), 4 already gray → **9 read**. **5 demoted**, 2 of them false in code (DRIFT-039, DRIFT-040) | ~~17 audit-type law rows may be 🟩 while their clause is false~~ | ~~read, medium~~ |
| 9 | **Verdict-quality gate** (DL-104 e) — *packaged as S173* | 56 % self-agreement is the number to beat; runs on the **Batch API**, which is where batching actually earns its place | 1 sprint |
| 10 | **S157 / hardening row O** | 101 law clauses with no test-plan row; assertion E is warn-only | 1 sprint |
| 11 | **Hardening row N** — delegated-agent sandbox default | Dormant; every delegated run has overridden it by hand so far | small |
| 12 | **Hygiene sweep** | ~122 pending Fills, teardown delete path unproven live. 🪤 The flag half is now **measured and split out as item 17** (52 Flags, 45 unresolved criticals) — do not double-count it here | light |
| 13 | ~~**Doc drift**~~ **DONE** — 2026-08-13, commit `bf928ca` | ~~Two stale statuses~~ | ~~light~~ |
| 14 | ~~**DL-112 — sentiment counts read as article counts**~~ **DONE + DEPLOYED** (`s176b`, `0.90.11`, 2026-08-15). `sentiment_positive`/`_negative` counted lexicon **words** beside `sentiment_articles` counting **headlines**; the deliberator called it a corrupt feed and vetoed XOM + part of AMZN. Renamed to `*_words` | ~~Cost real orders on sched-2026-08-14~~ | ~~small~~ |
| 15 | ~~**Broker↔graph divergence**~~ **NOT A DEFECT** — diagnosed 2026-08-15, reconciliation worked: graph active == broker **19/19**, AMD/DOW/VZ adopted + stopped at 22:54, AMZN/AVGO `broker_absent`. 🪤 My earlier claim that the graph had the book wrong was **retracted** | ~~Upstream of the veto~~ | ~~diagnose first~~ |
| 16 | ~~**Sweep the debate context for the DL-104 class**~~ **DONE + DEPLOYED** (`s177`, `0.90.12`, 2026-08-15) — S177, [DL-113](docs/design-log.md). Producer-owned values now name unit+scope (`deployed_this_batch_usd`, `quantity_shares`, `requested_tickers`); open-name vendor dicts render under an explicit `source-owned-units-scope-unknown{...}` boundary rather than pretending the renderer knows their units. 🪤 Codex found **3 sites the spec missed**, best being `deployed` meaning *opposite scopes* in adjacent packet lines | ~~Four instances, all cost real orders~~ | ~~1 sprint~~ |
| 17 | ~~**45 unresolved `critical` Flags pin `healthy=false`**~~ **DONE** (`S178`, `0.90.13`, 2026-08-18) — [DL-111](docs/design-log.md). Severity now follows **persistence**: first sight is `warn`, the same divergence still present at the next run start escalates to `critical`, a gone one is retired. `subject_ref` is now `{kind}:{ticker}` (was the per-run snapshot key), so the dedupe guard finally fires. **Sweep run on the spine:** `pending_human_flags` **46 → 0**, Flags 53 → 53 all still `pending` (none mutated), Positions 19 → 19. 🪤 **S178's own recommendation was unimplementable** — adoption happens in the *monitor*, so the outcome is unknowable where execution writes the flag | ~~Since 2026-07-08~~ 🟢 Reporting-only; acceptance reads neither field | ~~1 small sprint + one sweep~~ |
| 18 | **`max_sector_pct` never sees held positions** — the *behaviour* half, still open | 🪤 **The label half is CLOSED by S177** (`deployed_this_batch_usd` now says what it counts). What remains is a real question: `SectorBook.__init__` seeds `_names` from held positions but not `_deployed`, so the dollar sector cap only ever counts the current batch and cross-day exposure can pass 30 % unnoticed. Deliberately split out in [DL-113](docs/design-log.md) because seeding it **changes which orders get approved**. Masked today by `max_names_per_sector=3` binding first | ADR + small |
| 19 | 🚨 **`open_incidents` is the only remaining lock on `healthy`** — *packaged as [S179](docs/sprints/sprint-179-a-fault-must-be-able-to-stop-being-an-incident.md), 2026-08-18* | Measured on the spine: **6119** `Fault` nodes, **every one** `status=pending`, **0** `FaultResolution`, **0** `FaultSuppression`. `health.py:32` counts faults whose status `!= "resolved"` and **nothing in the codebase ever writes that value** — two writers, one hardcodes `"pending"`, the other writes no status at all. So the count only grows and `healthy` can never return to true. 🪤 **Earlier diagnosis corrected:** this is *not* the S178 dedupe bug — `fault_node_key` is keyed by `occurred_at` **deliberately** ("a fault that recurs every run is itself the signal"); do not touch it. 🪤 **94 % (5762) is one closed incident** from 2026-07-30/31, never seen since — the live rate is ~12–14/run. 🚨 **Two independent copies of the predicate** (`health.py` + `surfaces/queries/health.py`) must move together | 1 small sprint |
---

## Detail, in rank order

**~~1 · S169 / DL-100 — a deploy must not silently discard operator config~~ — CLOSED by S169, `0.90.10`, DEPLOYED `s176a` 2026-08-15** *[measured 2026-08-08]*
> ✅ **Live proof supplied 2026-08-15.** The full `up` ran at `s176a` with `-DropEnv
> DELIBERATOR_DEFENDER_MODEL,DELIBERATOR_CHALLENGER_MODEL,DELIBERATOR_JUDGE_MODEL`, and the guard
> **refused the first attempt**, naming all three keys — DL-100 closed by demonstration, not only by
> test. 🪤 `pwsh script.ps1 -DropEnv A,B,C` passes one literal string (`-File` semantics); the call
> operator `& ./infra/deploy-agents.ps1` is what binds the array.
> The spec's pinned `0.90.02` was taken too; shipped as `0.90.10`, and the spec now says
> *"next available PATCH at merge"* rather than a number — item (iii) under STATE's *Next*, applied.
A full `up` **replaces** each app's env set. It wiped `SCANNER_CANDIDATE_CAP=25`,
`MAX_POSITION_PCT=0.01`, `MAX_POSITIONS=60` and reverted the dispatcher cron `30 22 * * 1-5` →
`30 22 * * *` — all with a green `[OK]`. `MAX_POSITION_PCT` reverting 0.01 → 0.10 is a **10× position
size**, silently; the cron revert would have fired a weekend run that night. Caught only because the
env was snapshotted by hand first. Same green-report-while-wrong shape as row Q and DL-88, now paid
for three times. Every item below needs a deploy, so this gates the rest.
🪤 **Its spec targets `0.90.01`, which S171 consumed — renumber to `0.90.02`.**

**~~2 · The 42-bar history gap~~ — CLOSED by S174, proven live 2026-08-13** *[measured today]*
> 🪤 The diagnosis below was **close but not right**: `lookback_days=260` was not "not being
> honoured" — it travelled correctly on the request/response path, which production does not use.
> The graph-pull path called `_today_window()` with no argument, taking a bare
> `_DEFAULT_LOOKBACK_DAYS = 60`. Fixed by deriving the window from the declared indicator periods
> and stamping it on the `RunRequest` (295 calendar days → 202 bars).
`market-data:sched-2026-08-07` holds **4,200 bars for 100 tickers — exactly 42 each**. At 42 bars
these are silently skipped: **SMA-200 distance** (needs 200), **EMA crossover**
(`ema_long_period=50`), **golden cross** (50/200). So **every long-trend input is missing from every
recommendation the system has ever made**, while `recommend.py:99-101` hardcodes a rationale
advertising *"SMA-200 distance, and EMA crossover"*. MACD survives at 35 bars needed, 7 to spare.
`lookback_days=260` exists explicitly *"so SMA200 can compute"* and is not being honoured.
Two parts: **fix the supply**, and **stop the rationale asserting inputs it did not use**.
Found by the LLM veto; our gates cannot see it.

**3 · Deliberator concurrency + `max_rounds`** *[measured today; serialization re-measured and proven 2026-08-11]*
5 calls/order (`max_rounds=2` × 2 peers + judge) ≈ **47 s mean**. Serialized at three independent
levels: `poll.py:64` is a plain synchronous `for` loop over orders; rounds within an order are
inherently sequential; and **all three deliberator apps are `maxReplicas=1`**, so even a concurrent
manager could not fan out. Latency mean ~9–12 s but tail to **50.9 s** on a single call. Tokens are
~5.6 k in / 0.6 k out per order, so **cost is negligible — wall clock is the whole constraint.**

🚨 **Now proven rather than inferred (2026-08-11, off the `LLMCall` ledger for `sched-2026-08-10`):**
90 calls, span first→last **1,136 s**, sum of per-call latency **1,022 s** — **ratio 0.90**. For
ninety per cent of the wall clock exactly one call is in flight; the other ~114 s is bus round-trip
and graph writes. Priced at Claude Opus 5 list rates the whole run is **$0.83**, so the Batch API's
50 % discount is worth **$0.41 a run** — batching this for cost is arguing about $107 a year.

| Orders | Serial time | vs the `le=3600` ceiling |
| --- | --- | --- |
| 18 (measured) | 943 s | fits the 1800 s grace |
| 25 (today's cap) | ~1,185 s | fits, ~34 % headroom |
| 68 | ~3,200 s | at the ceiling |
| 100 (widened funnel) | ~4,740 s | **blows it by 30 %; no grace value fixes it** |

Levers cheapest-first: `max_rounds` 2 → 1 (a tunable, no code, −40 %); **`effort` down from `max`**
(a tunable — but see the adapter findings, it is currently inert); concurrency K across independent
orders (≈ N/K); peer replicas or async-in-one-replica, since the calls are I/O-bound.
100 orders at K=10 with 1 round ≈ **290 s**. **S171 is what makes any of this possible** — while the
manager took `messages[0]`, concurrent debates would have interleaved each other's replies.
Ruled out: a single batched verdict (5 calls total, but it stops being a debate) and deliberating
only marginal orders (the veto's one genuinely useful catch landed on an ordinary order).

**Three adapter findings, found 2026-08-11 while checking the above. None were being looked for.**

- ~~🚨 **`effort` is inert on the deployed fleet.**~~ **DONE** — `0.90.02`, 2026-08-11. 🪤 Setting it live to `high` then cost **3 fail-opens** on 2026-08-13: it lengthens the peer-call *tail* (23.0 s → 39.1 s max) past the 30 s `request_timeout_seconds`, since raised to **60**. Unverified until `sched-2026-08-14`. Original text: `llm_openai.py:43` assigns `self.effort` and
  `complete()` never sends it. The tunable is registered, visible, reads as live, and does nothing on
  `gpt-5.5` — the same shape as DL-63's inert reasoning knob. **So one of the two free latency levers
  above does not currently exist.** One-line fix; keep it out of the concurrency sprint so the blast
  radius stays one concern.
- 🚨 **`effort="max"` with `max_tokens=4096` is a documented misconfiguration on Claude Opus 5.**
  Thinking and answer share that single budget, and Anthropic's own guidance at `max` effort is to
  start at **64 K**. The tunable is hard-capped `le=4096`, so it cannot be raised without a code
  change. *Candidate, not a finding:* a verdict truncated or rushed under that cap is a plausible
  contributor to the 56 % self-agreement in item 9 — which is what would settle it.
- 🟠 **No prompt caching, no structured outputs.** Every one of the 5 calls per order re-sends the
  full prefix at full price, and both adapters `del tool_schema` — the verdict is parsed out of free
  text rather than schema-guaranteed.

**Packaged 2026-08-11** as [`sprint-172-independent-debates-run-independently`] in the repo, opened
from **DL-105**. The three adapter findings are deliberately *not* in it — they are a separate small
chore, because mixing a defect fix into a concurrency sprint muddies the before/after measurement
that is the sprint's whole point.

**~~4 · Veto context correctness — DL-104 (a) and (b)~~ — CLOSED by S175, DEPLOYED `s176a` 2026-08-15** *[measured today]*
> 🪤 S174 made the fragment **worse** before S175 removed it: widening the window 41 → 202 bars
> moved AMD's invented ATR 7.81 % → 4.07 %, flipping the rendered verdict `FAILED` → `PASSED` on an
> unchanged order. A fragment whose outcome is decided by an unrelated sprint was never evidence.
Delete the invented ATR fragment at `context_pm.py:138`, or label it honestly and stop rendering a
`PASSED`: it averages **every bar handed in** (41 periods) and prints the result inside the
`stop_vs_regime_volatility gate:` line, while the real gate only compares `stop_pct`/`target_pct` to
the regime bases. That one string manufactured 6 of 15 vetoes across **both** vendors. Then give the
veto batch context, or stop it reasoning about portfolio state it cannot see — it currently reads
`existing_sector_names=0` on a flat book and concludes the book is broken.

**~~5 · Hardening row P — `broker_status="partial"` can never upgrade to `filled`~~ — CLOSED by S176, DEPLOYED `s176a` 2026-08-15** *[carried]*
> 🚨 It was **worse than filed**: `broker_price_cents` shared the same write-once guard and
> `exit_price_cents` read it back, so a partial froze the price realized PnL is computed from.
> Filed as a labelling defect; it was a money defect.
`_broker_status_props` writes `broker_status` only `if "broker_status" not in node.props` —
write-once, and correct under the append-only spine — so a fill that reaches the broker as
`partial` is stuck there forever. Dormant only because **no fill has ever been partial**; the ten
flatten exits all filled whole. Promoted above the two "small" veto items because a widened funnel
with more limit orders at the open makes the trigger materially more likely, and the failure is
silent graph/broker divergence.

**6 · A real advisory/binding switch — DL-104 (d)** — 🟠 **PARTIAL (S175):** the states are now declared, queryable and faulted; **no mode switch exists** *[decided today]*
Today's advisory posture is an **accident**: a grace that happens to expire, writing a truthful but
uninformative `DeliberationGraceExpired` every run. Acceptable for one night, corrosive as a
standing posture, because it trains you to read a real fault as noise. Make *advisory* a declared
state.

**7 · S170 / DL-101 — one LLM adapter in the kernel** *[carried]*
The port and `LLMCall` ledger are kernel; the vendor adapters and factory are not, and are
duplicated, so S168's OpenAI fallback reached only the deliberator. The operator agent is
Anthropic-only while that key is limited until **2026-09-01** — the only date on this list. Also
stops `surfaces/dashboard/chat_binding.py` reaching into an agent's adapter.

**~~8 · The SCAN-OBS-01 shape sweep~~ — DONE 2026-08-14 (DL-111)** *[measured today]*
> **The 17 was wrong: 13 rows exist, 9 were green and in scope.** Five demoted — `ANLZ-OBS-01`,
> `EXEC-OBS-01`, `EXEC-OBS-02`, `PM-OBS-01` (the snapshot row), `PROV-OUT-04`. Ledger reconciled:
> analyst 24→23, execution 32→30, provider 17→16.
> 🚨 **Two are false in code, not just untested**, and need a forced decision rather than a test:
> **DRIFT-039** — `portfolio_state_snapshot` exists nowhere in the codebase; **DRIFT-040** — nothing
> records which vendor served a fact, so ADR-0006's three-source arrangement is unauditable.
> 🪤 **Next sweep, cheaper and greppable:** four of the five demoted rows cite a test on the
> **pub/sub path production does not use** — the S174 shape, in the ledger instead of the code.
`SCAN-OBS-01` was 🟩 while the clause was false, because its cited test proved provenance rather
than reconstructability. **17 audit-type rows** across the test-plans have the same shape available
to them. The coverage gate cannot detect it — it needs a read. Ranked above the verdict-quality gate
because a ledger that reports proven-when-false undermines every other proof in the project.

**9 · Verdict-quality gate — DL-104 (e)** *[measured today]*
**56 %** self-agreement (same model, same 18 tickers, 3.5 h apart, 9 of 16) is the number to beat.
Cross-vendor agreement is *higher* at 12 of 17. Until something measures reproducibility, "is the
veto right" is a question answered by hand. **Depends on 2 and 4 landing first**, or it measures noise.

**10 · S157 / hardening row O** *[carried]*
**101 law clauses with no test-plan row.** S156 made this checkable as assertion E in
`scripts/check_law_coverage.py` but deliberately left it **warn-only**. Until the rows exist the
assertion cannot be promoted.

**11 · Hardening row N — delegated-agent sandbox default** *[carried]*
`~/.codex/config.toml` carries `approval_policy = "never"` and `sandbox_mode = "danger-full-access"`.
Every delegated run so far has overridden it explicitly, which is why it has never bitten — the
default is the defect, not the practice.

**12 · Hygiene sweep** *[measured today unless noted]*

- **50 pending divergence `Flag`s** — reconciliation working, but at 50 a genuinely new one is invisible. Ack sweep.
- **~122 pending `Fill`s** *[carried]* — if still pending after tomorrow's run, that is a DL-46 image-currency question.
- **`pg_teardown --run-id`'s delete path has never run on live data** — only its collection and verification queries have. First real use must be a disposable synthetic run, not a production lineage.

**~~13 · Doc drift~~ — CLOSED 2026-08-13, `bf928ca`** *[measured today]*

- `DL-102` still reads `OPEN (mitigated 2026-08-08, not fixed)` — S171 fixed it and proved it on cold peers.
- `chore-openai-cutover` reads **SPEC** in `docs/sprints/INDEX.md` but shipped as `8b30624`.

---

## Two notes on the ordering

**The 42-bar gap sits above the scalability work deliberately.** Scalability blocks a veto that is
currently advisory and whose correctness is unproven; the history gap is degrading every decision
right now. Defensible either way — say so and they swap.

**~~Item 1 is first for a boring reason.~~ — CORRECTED 2026-08-13.** It is still the only item where
getting it wrong costs money, but *"everything else has to deploy past it"* is **false**. S169 fixes
a full `deploy-agents.ps1 up`; the **image-only retag** path was exercised five times on 2026-08-12/13
(`v0.90.02`, `s171a`, `s174`, plus a min-replicas bump and two env-var sets) with the scale config and
every operator switch diffed before and after — **nothing lost, ever**. S169 gates nothing currently
queued: S174, S175 and S176 all shipped without a vocabulary-pack move.

---

## Standing constraint — LIFTED 2026-08-11

~~No deploys, merges or tunable edits until `sched-2026-08-10` has run and been read.~~
**The run fired, completed 8/8 and was read on 2026-08-11**: `ACCEPTANCE UNPROVEN` with 18 buy
limits accepted and unfilled at the broker, the DL-104 grace expiring at 900 s exactly as designed,
and the veto returning 3 uphold / 14 revise / 1 overturn four minutes too late to bind. The fleet
state that was being protected has now been measured, so **the tunable levers in item 3 are
unblocked** — `max_rounds` and (once it is wired) `effort` can be swept.

Branch work, specs and `make ci` touch nothing live and can proceed at any time.
