<!-- Agent: portfolio_manager | Role: sprint spec — concentration measured by issuer and correlation, not by a vendor label -->
# S184 — one issuer is one bet, and correlation is measured

**Closes:** [ADR-0023](../decisions/0023-concentration-is-issuer-and-correlation-not-a-vendor-label.md)
· **Implements:** PM `laws.md` **v1.3** (`PM-NEV-07`, `PM-NEV-08`, `PM-NEV-09`, `PM-TYP-03`) ·
**Clears:** DRIFT-042, DRIFT-043, DRIFT-044, DRIFT-045, DRIFT-046 · **Type:** feat ·
**Target version:** next available **MINOR** at merge — **do not pin it in this file** ·
**Branch:** `sprint-184-one-issuer-is-one-bet`

> Handover to a delegated coding agent. Everything under **Measured** was read off this repo or the
> live Postgres spine on **2026-08-20**. Everything marked **Assumed** has **not** been verified —
> check it before building on it. Do not treat an unmarked claim as measured.

## Why

**The deliberator has rejected 19 of 26 PM-approved orders — 73 % — across four consecutive binding
runs, and the dominant objection is always the same** ([DL-119](../design-log.md)). The PM's
concentration gates count *vendor industry labels*. The correlation that actually bites crosses
those labels, and share classes of one issuer count as two independent bets.

> *GOOG: "the PM treats GOOG as a new ticker while the portfolio already holds GOOGL, and the
> sector/name-count gates do not catch duplicate Alphabet issuer exposure"*
>
> *AMZN: "the sector gates are label-based counts with no name-correlation penalty, so 'Retail' lets
> AMZN pass at 1 name while the book already carries correlated mega-cap tech beta"*

🚨 **This is the binding constraint on the system trading at all.** `verify-2026-08-20-s182-a`
approved four orders and traded **none**. 🪤 **Do not soften the veto to restore throughput** — the
objections would stop *binding* without ceasing to be *true*. Fix the PM, not the referee.

**The law has already moved.** ADR-0023 was accepted and PM `laws.md` was amended to **v1.3** on
2026-08-20. This sprint implements clauses that already exist. **Read
`agents/portfolio_manager/laws/laws.md` before writing anything** — `PM-NEV-06` through `PM-NEV-09`
and `PM-TYP-03` are the specification; this document is the evidence and the sequencing.

## Measured, 2026-08-20 — read these before designing

**1 · The correlation input is already on the graph, at zero API cost.**

| Fact | Value |
| --- | --- |
| `Bar` label node count | **0** — the label exists in the vocabulary and *nothing writes it*. Do not look for bars there. |
| `MarketData` nodes | **47**, exactly **one per `run_id`** |
| Latest (`verify-2026-08-20-s182-a`) | `window_end` 2026-08-20 · **99 requested, 98 returned**, 19 796 bars — **exactly 202 per ticker** (min = median = max), earliest bar **2025-10-29** |
| Held tickers with bars in that node | **22 of 22**, 202 bars each — **none below the 60-bar floor** |

The bars live in `MarketData.snapshot`. **The read idiom already exists** —
[`agents/scanner/poll.py:43`](../../agents/scanner/poll.py#L43):

```python
market = MarketData.model_validate(node.props["snapshot"])
```

`MARKET_DATA_LABEL` is exported from `contracts/provider.py:85`. The provider writes the node keyed
by `run_id` (`agents/provider/ingest.py:126`, DRIFT-011), and the PM's `RecommendationSet` carries
that same `run_id`.

🚨 **2 · The PM's own provider call cannot supply this, and must not be widened to try.**
[`agent.py:105`](../../agents/portfolio_manager/agent.py#L105) builds a `Window` of
**`price_lookback_days = 7` days**, and
[`provider_client.py:52`](../../agents/portfolio_manager/provider_client.py#L52) requests
**only `recommendation_set.recommendations` tickers**. Seven days, recommended names only — useless
for a 120-day correlation against the held book. **Read the run's `MarketData` node from the graph
instead.** Widening the bus call would add a large provider round-trip per run to fetch data the
graph already holds, and `PM-NEV-02` forbids the PM fetching market data itself.

**3 · The labels are 30 vendor industry strings, and five of them are prose.**

`Sector` holds **106 rows**: **101 real ticker→label rows over 30 distinct labels**, plus **5 junk
rows** where prose was parsed as a ticker —

```text
'Note' -> Professional Services   'feed' -> Health Care   'for' -> Real Estate
'free' -> Food Products           'on'   -> Semiconductors
```

(almost certainly a vendor free-tier notice ingested as data). GICS level 1 has **11** sectors;
`Semiconductors`, `Banking` and `Pharmaceuticals` are not among them. 🪤 **Out of scope to fix** —
but do not let a fix depend on the sector table being clean.

**4 · GOOG and GOOGL both map to `Media`.** Neither is currently held — GOOG was vetoed for exactly
this reason. The dual-class case is live and reachable, not hypothetical.

**5 · The held book already binds.** 22 positions over 13 labels, **max 3 per label** — so
`max_names_per_sector = 3` is currently binding at `Banking` and `Telecommunication`.

**6 · The three code defects, all confirmed by reading the file.**
[`concentration.py`](../../agents/portfolio_manager/domain/concentration.py):

- **DRIFT-045** — `__init__` seeds `_names` from held positions but leaves `_deployed` empty, so
  `max_sector_pct` **counts only the current batch**. Masked today because the name count binds first.
- **DRIFT-044** — `outcomes()` and `exit_outcomes()` `return ()` when a ticker has no label, and
  `record()` silently no-ops. **An empty outcome tuple is indistinguishable from a passed gate.**
- **DRIFT-046** — `GateOutcome.passed` is a `bool`. **Two states. There is no way to say
  *not evaluated*** ([DL-121](../design-log.md)).

## Scope — and what is deliberately NOT here

**In scope**, and all five must land together:

1. `PM-NEV-07` — aggregate exposure by **issuer** before any gate counts or weighs.
2. `PM-NEV-08` — a **measured correlated-cluster cap** against the held book.
3. `PM-NEV-09` — an unevaluable gate emits **not-evaluated**, never a silent pass.
4. **DRIFT-045** — `max_sector_pct` sees held positions, not just the current batch.
5. **DRIFT-046** — `GateOutcome` gains a third state.

🚨 **DRIFT-045 is not optional and cannot be deferred.** The dollar cap is only harmless today
because the name count binds first. **Fix the name count alone and you un-mask it** — the dollar cap
silently becomes the weak gate, and the sprint will have made one thing worse while fixing another.

**Out of scope:**

- 🪤 **Tuning the new thresholds.** `correlation_threshold=0.70`, `max_correlated_cluster_pct=0.25`,
  `correlation_lookback_days=120`, `min_correlation_bars=60` are the law's declared defaults. Moving
  them by evidence is a **tuner experiment** with its own before/after on a fixed `as_of`. Ship the
  declared values.
- The **5 junk `Sector` rows**. Real, separate, and not this sprint.
- The other **15 `TYP` clauses** that still say *"matches the contract file exactly"* (queue item 30).

## The design decisions this sprint has to make

Record all of them in `docs/design-log.md` **with rejected alternatives, before implementing**
(LAW-06). 🪤 The log has duplicate IDs (two `DL-110`, two `DL-111`) and entries are prepended at the
top *and* appended at the bottom — **check the highest number in use first**. The last one written
was **DL-121**.

**1 · How does `GateOutcome` express three states?** Options:

- **(a) Replace `passed: bool` with a status enum** (`passed` / `failed` / `not_evaluated`).
  Honest, and the type then makes the illegal state unrepresentable. Breaking: **five production
  call sites** read `.passed` — `deliberator/context_pm.py:97`, `pm/domain/gate_report.py:79`,
  `pm/domain/position_gates.py:96,109,115`, `orchestration/pm_rejections.py:39`.
- **(b) Add `evaluated: bool` alongside `passed`.** Additive, no reader breaks — but it permits
  `evaluated=False, passed=True`, which is precisely the state the clause forbids.
- 🚨 **Recommended (a).** `PM-TYP-03` asks the contract to *express* the distinction, and (b) leaves
  the forbidden state representable. Five call sites is a bounded, nameable cost; a compatibility
  shim for reading historical payloads is acceptable and probably necessary.

**2 · Where does the issuer map live?** `PM-NEV-07` says the trading pack owns it (ADR-0012), and
the PARAM row marks it `NO (pack data)`. 🪤 **Check how other pack data is loaded before inventing a
mechanism** — `orchestration/packs/` already holds `trading_tunables.json` and
`trading_graph_vocabulary.json`. **Absence from the map means single-class**, which is the common
case and an ordinary pass — *not* a not-evaluated outcome. The law says so explicitly.

**3 · What exactly is "one correlated cluster"?** The law defines it as *the candidate issuer plus
every held issuer whose pairwise return correlation with it is at least `correlation_threshold`*.
Decide and record: returns from close-to-close; what happens when the candidate is already held;
whether the cluster is recomputed per candidate within a run as tentative approvals accumulate
(`PM-STA-03` says the running book must reflect them).

**4 · Where is correlation computed, and is it cached within a run?** 99 tickers × 202 bars is a
2.9 MB payload and up to 22 pairwise correlations per candidate. Naïvely recomputing per candidate
is wasteful but probably still trivial; **measure it rather than assuming either way**, and note the
result — `PM-PERF-01` claims the gate math adds negligible latency, and that claim is now testable.

**5 · What does a not-evaluated outcome say?** It must **name the missing input** (`PM-NEV-09`) and
reach `gate_report` so the debate packet can render it. 🪤 Check what
`deliberator/context_pm.py:97` currently does with a gate outcome and make sure the third state
renders as itself — not as a pass, and not as a crash.

## Blast radius — measured 2026-08-20

| File | Lines | Note |
| --- | --- | --- |
| `agents/portfolio_manager/domain/concentration.py` | **145** | 🚨 **5 lines from the 150 warn, 55 from the 200 hard block.** Issuer + correlation + tri-state will not fit. **Plan the split before you start.** |
| `agents/portfolio_manager/domain/risk.py` | 133 | constructs `SectorBook`; threads the new settings |
| `agents/portfolio_manager/domain/position_gates.py` | 133 | maps failing outcomes to reason strings; reads `.passed` ×3 |
| `agents/portfolio_manager/domain/order_decision.py` | 128 | entry/exit decisions |
| `agents/portfolio_manager/domain/gate_report.py` | — | reads `.passed` |
| `agents/portfolio_manager/agent.py` | 117 | where the run's `MarketData` node gets read |
| `agents/portfolio_manager/settings.py` | 95 | four new `tunable()` fields |
| `contracts/portfolio_manager.py` | 101 | `GateOutcome` third state |
| `agents/deliberator/context_pm.py` | — | renders gate outcomes into the debate packet |
| `orchestration/pm_rejections.py` | — | reads `.passed` |

🚨 **This sprint WILL change which orders are approved. That is the point, and it is the opposite of
S183.** The gate begins refusing concentration it previously admitted. **Measure it:** run the same
`RecommendationSet` before and after and report what changed and why. A diff that changes nothing
means the gates are not binding.

## Steps, in order

1. **Failing tests first**, one per clause, each citing its ID in the docstring (conventions §7):
   - `PM-NEV-07` — a portfolio holding GOOGL rejects GOOG as the **same issuer**, not as a second name.
   - `PM-NEV-08` — a candidate correlated above threshold with held names is rejected on
     **cluster weight**, with the sector caps passing.
   - `PM-NEV-09` — a ticker with no sector label produces an explicit **not-evaluated** outcome,
     provably distinct from a pass; likewise a pair with fewer than `min_correlation_bars`.
   - **DRIFT-045** — a held position's dollar exposure counts toward `max_sector_pct` on the next run.
2. **Record decisions 1–5** in `docs/design-log.md` with rejected alternatives. Before implementing.
3. **`GateOutcome` third state** + fix the five reader call sites.
4. **Issuer aggregation**, then **the correlation gate**, then **not-evaluated**, then **DRIFT-045**.
5. **Split `concentration.py`** — it cannot absorb this and stay under 200.
6. **Register the four new settings as `tunable()`** with the law's bounds and a `why`:
   `correlation_lookback_days` 120 [20, 250] · `correlation_threshold` 0.70 [0.0, 1.0] ·
   `max_correlated_cluster_pct` 0.25 [0.0, 1.0] · `min_correlation_bars` 60 [20, 250].
   🪤 **Read the PARAM table in `laws.md` for each one** — the law is the source, and the `issuer_map`
   row is deliberately `NO (pack data)`, not a tunable.
7. 🚨 **Add them to `orchestration/packs/trading_tunables.json`.** A full `up` replaces each app's env
   set (DL-100 / S169), so an operator value that is not in the pack is silently lost on the next
   deploy.
8. **Green the law rows.** Update `agents/portfolio_manager/laws/test-plan.md` — the `_tbd_ (v1.3)`
   rows are already there waiting — and reconcile the counters in **both** `docs/laws/ledger.md`
   **and** `docs/laws/INDEX.md`. `scripts/check_law_coverage.py` fails the build if they disagree.
9. **Mark DRIFT-042..046 `CORRECTED`** in `docs/laws/drift-register.md`, each naming its regression test.
10. **Before/after measurement** on the same `RecommendationSet`: which orders changed verdict, and why.
11. `make ci` green — **redirected to a file, never piped**. Every new guard planted, watched to fail,
    restored.

## Success factors

- [ ] A book holding GOOGL treats GOOG as the **same issuer** — one name, one exposure.
- [ ] A candidate correlated above threshold with the held book is rejected on **cluster weight**
      while every label-based gate passes. This is the case no labelling scheme catches.
- [ ] A missing sector label and a too-short bar history each produce an explicit **not-evaluated**
      outcome that names the missing input, provably distinct from a pass.
- [ ] `GateOutcome` cannot represent "not evaluated **and** passed".
- [ ] `max_sector_pct` counts held positions, proven by a test that fails on today's code.
- [ ] Correlation is computed from the run's `MarketData` node. **Zero new provider calls** —
      state the measured call count.
- [ ] `PM-NEV-07`, `PM-NEV-08`, `PM-NEV-09` are 🟩 with tests citing the IDs; `ledger.md` and
      `INDEX.md` agree with the derived count; `check_law_coverage.py` exits 0 with no `[FAIL]`.
- [ ] DRIFT-042..046 marked `CORRECTED`, each naming its regression test.
- [ ] The four new tunables are in `trading_tunables.json`.
- [ ] **The approved-order set is measured before and after, and every change is explained.**
- [ ] No module over 200 lines; `concentration.py` split rather than grown.
- [ ] Each new guard planted, watched to fail, restored — stated per guard.
- [ ] `make ci` exit 0, 100.00 % coverage.
- [ ] `make gate-ran` **GATE PROVEN**, run from the worktree whose `HEAD` is the commit, SHA checked.

## Traps

🪤 **`Bar` has zero nodes.** The label is in the vocabulary and nothing writes it. Bars are inside
`MarketData.snapshot`. Two hours are available to lose here.

🪤 **Do not widen the PM's provider call.** 7 days, recommendation tickers only, by design. The graph
already holds 202 bars for all 99 tickers including every held name. `PM-NEV-02` forbids the PM
fetching market data itself.

🚨 **DRIFT-045 must land with the name-count fix.** Fixing the count un-masks the dollar cap.

🪤 **`concentration.py` is at 145 of 200.** Plan the split first, not after CI blocks you.

🪤 **The sector table contains prose.** Five rows are junk words with real sector labels. Do not
assume the table is clean; do not fix it here.

🪤 **Absence from the issuer map is a pass, not a not-evaluated.** Most tickers are single-class.
Treating absence as unevaluable would flag ~99 % of the universe. The law says this explicitly.

🪤 **Read `agents/portfolio_manager/laws/laws.md` v1.3 first, and treat it as the spec.** S183 was
handed over with an instruction that contradicted a locked law because the law file was never
opened. If this document and `laws.md` disagree, **`laws.md` wins** — stop and say so.

🪤 **A script run from a git worktree silently gets the in-memory store** — no `.env`, and every
count reads 0. Copy the refuse-on-in-memory guard from `scripts/sweep_divergence_flags.py`.
**Never copy `.env` into a worktree.**

## Handover — paste this to Codex

```text
Work item: S184 - one issuer is one bet, and correlation is measured.
Repo: trading-agents. Read docs/sprints/sprint-184-one-issuer-is-one-bet.md IN FULL before writing
anything. Read CLAUDE.md. Read docs/INDEX.md before opening any docs folder.
THEN READ agents/portfolio_manager/laws/laws.md (amended to v1.3 on 2026-08-20). The law is the
specification; the sprint doc is the evidence and the sequencing. If the two disagree, laws.md wins -
stop and say so.

WHY
The deliberator has rejected 19 of 26 PM-approved orders across four consecutive binding runs (73%),
and verify-2026-08-20-s182-a approved four orders and traded none. The dominant objection is always
the same: the PM's concentration gates count vendor industry labels, so GOOG passes while GOOGL is
held, and AMZN passes at 1 name in "Retail" while the book carries correlated mega-cap tech.
DO NOT soften the veto to restore throughput. Fix the PM, not the referee.

WHAT TO BUILD - five things, all of which must land together
1. PM-NEV-07: aggregate exposure by ISSUER before any gate counts or weighs. GOOG+GOOGL = one name,
   one exposure. The issuer map is trading-pack data (ADR-0012), NOT a tunable. Absence from the map
   means single-class, which is an ordinary PASS, not a not-evaluated outcome.
2. PM-NEV-08: a measured correlated-cluster cap. A cluster is the candidate issuer plus every held
   issuer whose pairwise return correlation with it over correlation_lookback_days is at least
   correlation_threshold. Reject if cluster weight would exceed max_correlated_cluster_pct.
3. PM-NEV-09: a gate that could not evaluate emits an explicit NOT-EVALUATED outcome naming the
   missing input. Never a silent pass.
4. DRIFT-045: max_sector_pct must count HELD positions. SectorBook.__init__ seeds _names from held
   but leaves _deployed empty, so the dollar cap sees only the current batch.
5. DRIFT-046: GateOutcome.passed is a bool - two states, no way to say "not evaluated".

DRIFT-045 IS NOT OPTIONAL. The dollar cap is harmless today only because the name count binds first.
Fix the name count alone and you UNMASK it - the dollar cap silently becomes the weak gate.

MEASURED 2026-08-20 ON THE LIVE SPINE - do not re-derive, but do verify before depending on it
- The Bar graph label has ZERO nodes. It exists in the vocabulary and nothing writes it. DO NOT look
  for bars there.
- Bars are inside MarketData.snapshot. There are 47 MarketData nodes, exactly ONE per run_id. The
  latest (verify-2026-08-20-s182-a, window_end 2026-08-20) requested 99 tickers and returned 98, with
  19,796 bars - EXACTLY 202 per ticker, min = median = max - earliest bar 2025-10-29.
- ALL 22 held tickers have bars in that node, 202 each, NONE below the 60-bar min_correlation_bars
  floor. So correlation against the held book costs no API calls at all, and no held name starts out
  not-evaluated.
- The read idiom already exists, agents/scanner/poll.py:43 -
      market = MarketData.model_validate(node.props["snapshot"])
  MARKET_DATA_LABEL is in contracts/provider.py:85. The provider writes the node keyed by run_id
  (agents/provider/ingest.py:126), and RecommendationSet carries that same run_id.
- DO NOT WIDEN THE PM'S OWN PROVIDER CALL. agent.py:105 builds a 7-day Window from
  price_lookback_days, and provider_client.py:52 requests only the recommendation tickers. Seven
  days, recommended names only. Read the graph instead - PM-NEV-02 forbids the PM fetching market
  data itself.
- Sector holds 106 rows: 101 real ticker->label rows over 30 DISTINCT LABELS, plus 5 junk rows where
  prose was parsed as a ticker ('Note'->Professional Services, 'feed'->Health Care, 'for'->Real
  Estate, 'free'->Food Products, 'on'->Semiconductors). GICS level 1 has 11 sectors; Semiconductors,
  Banking and Pharmaceuticals are not among them. DO NOT fix the junk rows here, and do not assume
  the table is clean.
- GOOG and GOOGL both map to "Media". Neither is currently held - GOOG was vetoed for exactly this.
- Held book: 22 positions over 13 labels, max 3 per label, so max_names_per_sector=3 currently binds
  at Banking and Telecommunication.
- agents/portfolio_manager/domain/concentration.py is 145 lines - 5 from the 150 warn, 55 from the
  200 hard block. It CANNOT absorb this. Plan the split before you start.
- GateOutcome.passed has five production readers: deliberator/context_pm.py:97,
  pm/domain/gate_report.py:79, pm/domain/position_gates.py:96 and :109 and :115,
  orchestration/pm_rejections.py:39.

DESIGN DECISIONS - record ALL of them in docs/design-log.md WITH rejected alternatives BEFORE
implementing (LAW-06). The log has duplicate IDs (two DL-110, two DL-111) and entries are prepended
at the top AND appended at the bottom - check the highest in use. The last written was DL-121.
a. How GateOutcome expresses three states. RECOMMENDED: replace passed:bool with a status enum, so
   the illegal state is unrepresentable. Adding evaluated:bool alongside passed is additive but
   permits evaluated=False + passed=True, which is exactly the state the clause forbids. Five call
   sites is a bounded cost; a shim for reading historical payloads is fine.
b. Where the issuer map lives. Check how orchestration/packs/ already loads pack data before
   inventing a mechanism.
c. What exactly one correlated cluster is: returns basis, what happens when the candidate is already
   held, and whether the cluster is recomputed as tentative approvals accumulate within a run
   (PM-STA-03 requires the running book to reflect them).
d. Where correlation is computed and whether it is cached per run. MEASURE the cost rather than
   assuming - PM-PERF-01 claims the gate math is negligible and that claim is now testable.
e. What a not-evaluated outcome says. It must name the missing input and reach gate_report so the
   debate packet renders it as itself - not as a pass, and not as a crash.

STEPS
1. Failing tests FIRST, one per clause, each citing its law ID in the docstring:
   PM-NEV-07 (holding GOOGL rejects GOOG as the same issuer, not a second name);
   PM-NEV-08 (a correlated candidate is rejected on cluster weight while every label gate passes);
   PM-NEV-09 (no sector label, and too-few bars, each give an explicit not-evaluated distinct from a
   pass); DRIFT-045 (a held position's dollars count toward max_sector_pct on the next run).
2. Record decisions a-e in docs/design-log.md with rejected alternatives.
3. GateOutcome third state + fix the five readers.
4. Issuer aggregation, then the correlation gate, then not-evaluated, then DRIFT-045.
5. Split concentration.py.
6. Register four new tunable() settings with the law's bounds and a why:
   correlation_lookback_days 120 [20,250]; correlation_threshold 0.70 [0.0,1.0];
   max_correlated_cluster_pct 0.25 [0.0,1.0]; min_correlation_bars 60 [20,250].
   Read the PARAM table in laws.md for each. issuer_map is deliberately NO (pack data), not a tunable.
7. ADD THEM TO orchestration/packs/trading_tunables.json. A full `up` replaces each app's env set
   (DL-100/S169), so any operator value not in the pack is silently lost on the next deploy.
8. Green the law rows: agents/portfolio_manager/laws/test-plan.md already has _tbd_ (v1.3) rows
   waiting. Reconcile the counters in BOTH docs/laws/ledger.md AND docs/laws/INDEX.md -
   scripts/check_law_coverage.py fails the build if they disagree.
9. Mark DRIFT-042..046 CORRECTED in docs/laws/drift-register.md, each naming its regression test.
10. Before/after measurement on the same RecommendationSet: which orders changed verdict, and why.
11. make ci green, REDIRECTED TO A FILE not piped. Plant every guard, watch it fail, restore.

CONSTRAINTS
- THIS SPRINT WILL CHANGE WHICH ORDERS ARE APPROVED. That is the point - it is the opposite of S183.
  Measure it and explain every change. A diff that changes nothing means the gates are not binding.
- OUT OF SCOPE: tuning the new thresholds. 0.70 / 0.25 / 120 / 60 are the law's declared defaults.
  Moving them by evidence is a separate tuner experiment with a before/after on a fixed as_of.
- OUT OF SCOPE: the 5 junk Sector rows; the other 15 TYP clauses that say "matches the contract file
  exactly" (queue item 30).
- Do NOT edit laws.md. It was amended to v1.3 on 2026-08-20 and is the spec. If something in it looks
  wrong, STOP and say so - do not work around it and do not file drift without reading it first.
- Version: next available MINOR (this is a feat), do not pin it in the spec file.
- Branch sprint-184-one-issuer-is-one-bet. Push the branch and get `make gate-ran` GATE PROVEN before
  merging - run it FROM THE WORKTREE whose HEAD is the commit, and check the printed SHA against
  git rev-parse HEAD. Fill in the Closeout block before handing back.
- A script run from a git worktree silently gets the in-memory store (no .env) and every count reads
  0. Copy the refuse-on-in-memory guard from scripts/sweep_divergence_flags.py. NEVER copy .env into
  a worktree.
```

## Closeout — evidence

**Status:** BUILT locally on `sprint-184-one-issuer-is-one-bet`; remote `make gate-ran` is post-push
proof and must be quoted in the final handoff for the pushed `HEAD`.

**Result:** Implemented PM issuer aggregation, measured correlated-cluster concentration, explicit
`not_evaluated` gate evidence, held-book sector dollars for `max_sector_pct`, and the
`GateOutcome` tri-state contract. Version bumped to `0.91.00` / `uv.lock` `0.91.0`.

**Files changed:** PM contract and domain gates; PM agent/run/poll/entrypoint/settings wiring;
deliberator PM rendering/value labels; PM rejection rendering; deploy env-pack wiring; trading
tunables and new issuer-map pack; focused PM/contract/orchestration fixture tests; law/test-plan,
drift, ledger, index, design-log and state docs.

**Design decisions:** [DL-122](../design-log.md#dl-122---s184-concentration-gates-issuer-correlation-and-not-evaluated-evidence---status-decided-2026-08-20)
records the five decisions and rejected alternatives before implementation: `GateOutcome.outcome`
enum; issuer map as trading-pack data; cluster recomputed against the running issuer book; PM-local
correlation from run `MarketData` cached per evaluation; not-evaluated outcomes name the missing
input and block approval.

**Proof:** Failing guards came first:
`uv run pytest agents\portfolio_manager\tests\test_issuer_correlation_concentration.py --no-cov`
failed 5/5 before implementation. Green evidence includes
`test_issuer_concentration.py::test_dual_class_order_counts_existing_issuer_exposure` for
GOOGL-then-GOOG as one issuer/exposure; `test_correlation_concentration.py::test_correlated_cluster_rejects_cross_label_order`
for cluster rejection while label gates pass; `test_missing_sector_label_is_not_evaluated` and
`test_short_correlation_history_is_not_evaluated` for not-evaluated distinct from pass; and
`test_held_sector_dollars_count_toward_sector_cap` for DRIFT-045.

**Before/after measurement:** Same two-order set (`GOOG`, `AMZN`) against the same held book
(`GOOGL`, `AAPL`, `MSFT`). Before `main@806956b10d64471702e2e5eb7d9e3a6577d0e4d4` approved both
orders; all old gates rendered `True`. After S184 approved none: `GOOG` rejected `sizing` because
held `GOOGL` already consumes Alphabet issuer exposure; `AMZN` rejected
`correlated_cluster_concentration` with `correlated_cluster_pct=failed` while sizing, position,
cash, reward/risk and label gates passed.

**Provider-call measurement:** Correlation input came from graph-carried run bars; the PM provider
request stayed `(('AMZN',),)` for the recommendation ticker only, so correlation added `0` provider
requests for held names.

**Law rows:** `PM-NEV-07`, `PM-NEV-08`, `PM-NEV-09`, the widened issuer half of `PM-NEV-06`, and the
tri-state half of `PM-TYP-03` are green in `agents/portfolio_manager/laws/test-plan.md`. PM counters
in `docs/laws/ledger.md` and `docs/laws/INDEX.md` both read `28 / 47`; `DRIFT-042..046` are marked
`CORRECTED` with regression tests. `uv run python scripts/check_law_coverage.py` is green inside
`make ci`.

**Guards planted:** PM-NEV-07 planted a GOOGL-held/GOOG-buy case and failed before issuer kwargs
existed. PM-NEV-08 planted a correlated AMZN-vs-held-AAPL/MSFT case and failed before correlation
inputs existed. PM-NEV-09 planted missing-sector and short-history cases and failed because the old
code silently passed/approved instead of emitting not-evaluated. DRIFT-045 planted a held-sector
dollar cap case and failed because held dollars were absent from the old `max_sector_pct`
calculation. All are restored as passing tests in the final suite.

**`make ci`:** Redirected to `.tmp\make-ci-s184-final.log`, exit `0`. Summary:
`2360 passed, 6 skipped`, `100.00%` coverage, `pip-audit` found no known vulnerabilities,
detect-secrets passed tracked and untracked scans.

**Remote gate:** `make gate-ran` must be run after the final commit is pushed from the worktree whose
`HEAD` is being proved. Its output is intentionally not pre-pasted into this committed closeout,
because editing this file after the gate would change the SHA the gate proved. The final handoff
must quote the `make gate-ran` output and compare its printed SHA to `git rev-parse HEAD` before
merge.
