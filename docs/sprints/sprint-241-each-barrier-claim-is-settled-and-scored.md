<!-- Agent: planning | Role: sprint handover -->
# Sprint 241 — ten sessions after each barrier claim, the forecaster settles it, and a scorecard says whether the claims come true

**Phase:** Etalon-first continuous improvement (DL-19) · work-queue 92 (the book as a distribution), sprint B of the ledger
**Branch:** `sprint-241-each-barrier-claim-is-settled-and-scored`
**Status:** SPEC
**Version:** *next available MINOR at merge*
**Effort:** M
**Decisions:** [DL-240](../design-log.md) (nothing sizes or exits on a probability until a ledger shows it comes true) · [DL-241](../design-log.md) (the claim: D1–D11) · [EXP-018](../research/experiments/EXP-018-garch-history-depth.md) (the outcome rule and the baseline) · the builder's design decisions go to the **next free DL** (`DL-243` at spec time)

> **Why this bump kind.** The forecaster gains two capabilities it did not have: it settles its own claims
> against what the market did, and it scores them. New capability, so MINOR.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build**, except the forecaster amendment this spec names (law-cycle answer: Yes) |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections: **`FORE-IDN-02`**, **`FORE-IN`**, **`FORE-TRG-01/02`**, **`FORE-OUT-03/04/07`**, **`FORE-NEV`**
(01/02: advisory only; 04: market data only from the provider, over the bus or from a node the provider wrote),
**`FORE-STA`**, **`FORE-IDM-04`**, **`FORE-FAIL`**, **`FORE-CAP`**, **`FORE-PARAM`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes, both.** `contracts/forecaster.py` gains a capability, a request model and an owned label. Owed in the same
unit of work:

- **`FORE-IDN-02` amended**: the forecaster also writes `BarrierSettlement`.
- **New `FORE-OUT-08`** (next free `OUT` ID; check it): each claim is settled once, from bars the provider wrote,
  by EXP-018's outcome rule, as an append-only record; `barrier_scorecard` reports the ledger. You own the wording.
- **New `FORE-FAIL-05`** (or the next free ID): a claim that cannot be settled honestly is settled `void` with a
  named reason, **never** as a stop, a target or neither.
- `TRG` (the loop's settlement work), `CAP` (the capability), `PARAM` (every new setting).
- Forecaster book **v1.6 → v1.7** with a Changelog line; a `test-plan.md` row per clause; clause IDs in test
  docstrings; the rollup in **both** `docs/laws/ledger.md` **and** `docs/laws/INDEX.md` (let `make ci` tell you
  the number); a `drift-register.md` row for anything the change slips under.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/forecaster/*` (new settlement and scorecard modules, `poll.py`, `entrypoint.py`, `agent.py`, `settings.py`) | `agents/forecaster/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `FORE-IDN`, `TRG`, `OUT`, `NEV`, `FAIL`, `IDM`, `PARAM` |
| `contracts/forecaster.py` | same | `FORE-CAP`; the capability, its request, `owns_graph` |
| `orchestration/packs/trading_graph_vocabulary.json` | the pack's own notes; DL-85 (the fail-closed write guard) | an undeclared label or edge raises `VocabularyError` on its first write |
| `scripts/barrier_ledger.py` (new, read-only) | `CLAUDE.md` (read-only tooling) | prints the ledger from the live graph; writes nothing |

⚠️ **The forecaster stays advisory.** Nothing it writes may reach the PM, execution or the monitor, and no setting
may make it binding (`FORE-NEV-01/02`). The scorecard **reports**; it decides nothing. Whether the claims have
"come true" enough to size or exit on is a later, pre-registered experiment and the operator's call.

---

## Goal

At merge, every `BarrierForecast` is settled once its ten sessions have passed: the forecaster reads the bars from
a later run's `MarketData` (written by the provider), applies EXP-018's outcome rule, and records a
`BarrierSettlement` (stop first, target first, neither, or `void` with a reason). A `barrier_scorecard` capability,
and a read-only script, report the ledger: how many claims, what they said, what happened, and the Brier skill over
EXP-018's climatology with a date-bootstrap interval.

## Why (context)

DL-240 (operator, 2026-09-28): the book is to be managed as a distribution, but **nothing may size or exit on a
probability until a ledger shows it comes true**. S239 (deployed `s239`, 2026-09-28) makes the claims: from the run of
2026-09-28 on, each buy with a stop and a target gets a `BarrierForecast`. This sprint closes the loop so the ledger
exists. The first claims become settleable ten sessions later, about **2026-10-12**.

### Measured, 2026-09-28 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Where the settlement bars already are | each scheduled run's `MarketData` node (key `market-data:{run_id}`) holds the whole scanned universe: **98 tickers × 203 sessions** | *[measured on the live graph]* `sched-2026-09-23/24/25` |
| Does a later run cover an earlier run's buys? | **90 of 90** buys (with both barriers) over the last 30 scheduled runs have their entry bar and ≥ 10 later sessions in the `MarketData` of the run 11 sessions later | *[measured]* planner script over `sched-2026-08-14 … 09-25` |
| Does the entry close move between two fetches? | **0** drift on all 90 (the entry-day close is identical in both runs' bars) | *[measured]* same script |
| Why no drift: the bars are **raw** | the provider sets no `adjustment`, so Alpaca serves raw prices | *[read from the code]* no `adjustment` anywhere in `agents/provider/` |
| Consequence of raw bars | a split inside the ten sessions shows as a fake one-day fall of 50–90 %, which EXP-018's rule would score as a stop | *[derived]* |
| Reading one `MarketData` by key | ~1.3 s (38.5 s for 30) | *[measured]* |
| The outcome rule | `scripts/barrier_testbed.outcome()`: for sessions 1…10 after the entry, a low at or below `entry × (1 − stop)` is the stop (checked first), a high at or above `entry × (1 + target)` the target; else neither | *[read]* EXP-018 / the test bed |
| The baseline | EXP-018's primary realised shares: stop 0.287, target 0.477, neither 0.236 | *[measured]* EXP-018 Appendix R |
| Claim fields settlement reads | `ticker`, `as_of`, `entry_close`, `stop_pct`, `target_pct`, `p_stop_first`, `p_target_first`, `p_neither`, `horizon_sessions` (10), `model_id`, `history_ref` | *[read]* `agents/forecaster/barrier_store.py` |
| Module sizes | `agent.py` **164**, `poll.py` **151** (past the 150 warning), `entrypoint.py` 63, `scorecards.py` 83 | *[measured]* `wc -l` |
| How the deployed loop is triggered | graph-pull on a **current** `AnalystRun` (created within 24 h, DL-241 D11) | *[read]* `agents/forecaster/poll.py`, `contracts/barrier_history.py` |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first** (C1–C9 below).
2. **Settlement, pure.** A function that, given a claim's fields and one ticker's daily bars (date, high, low,
   close), returns the outcome by **EXP-018's rule exactly** (copy `scripts/barrier_testbed.outcome()`'s logic;
   the test uses it as the oracle), measured from **the later series' own close on `as_of`** (not the claim's
   `entry_close`: the claim's bars and the settling bars may come from different fetches), plus the ratio of the
   two closes, recorded.
3. **Void, never a false outcome.** A claim settles `void` with a named reason when: the settling bars lack the
   `as_of` bar or hold fewer than 10 sessions after it; or any session-over-session raw close ratio inside the
   window is below **0.6** or above **1.67** (a one-day move of 40 % or more: in large caps, a split or another
   corporate action) — reason `suspected_corporate_action`. A claim still unsettled **45 calendar days** after its
   `as_of` settles `void`, reason `no_settling_bars` (its ticker left the universe). All three thresholds are named
   constants citing this spec; none is a tunable.
4. **The trigger.** The forecaster's deployed graph-pull loop gains a settlement pass per **current** `AnalystRun`
   (D11's rule): read that run's `MarketData` through its lineage (`AnalystRun ← ANALYZED_BY ← ScanRun →
   DERIVED_FROM → MarketData`, as `agents/portfolio_manager/poll.py` does), and settle every open claim the bars
   cover. Mark the pass done per run so a run is settled once. The local pipeline does the same.
5. **The record.** `BarrierSettlement`, keyed from the claim's key (for example `settlement:{claim_key}`), with an
   edge from the `BarrierForecast`, holding at least: `claim_key`, `ticker`, `as_of`, `outcome` (`stop` | `target`
   | `neither` | `void`), `void_reason`, `settled_on` (the 10th session's date, or the day it was voided),
   `settling_ref` (the `MarketData` key), `entry_close_settling`, `entry_ratio` (settling ÷ claimed close),
   `brier` (the three-class Brier of the claim, absent for `void`), `created_at`. Append-only: a settled claim is
   never settled again.
6. **The scorecard.** A capability **`barrier_scorecard`** (request: `model_id`; response: the existing
   `Scorecard`, `promotion_eligible` structurally `False`). `metrics`: `settled`, `void`, `open`; realised shares
   and mean declared probabilities per outcome; `brier_model`; `brier_climatology` (EXP-018's shares above, fixed:
   the baseline is pre-registered, not re-estimated from the ledger); `skill` = 1 − model ÷ climatology; and a
   **date-bootstrap** 95 % interval `skill_lo` / `skill_hi` (resample `as_of` dates, 1,000 draws, a fixed seed:
   EXP-018's `run()` in its Appendix, `exp018_score.py`). With fewer than 2 settled dates, the interval is absent,
   not zero.
7. **The script.** `scripts/barrier_ledger.py`: read-only, from the live graph with `.env`; prints the scorecard and
   one line per settlement. Writes nothing.
8. **Declarations.** `contracts/forecaster.py` (the capability, its request, `BarrierSettlement` in `owns_graph`);
   the vocabulary pack (the label, its properties, the edge and its signature).
9. **The law cycle** above, and the builder's decisions in `docs/design-log.md` under the next free DL.

### Out of scope (do NOT build this sprint)

- **Any reader outside the forecaster**, the dashboard included. A tile comes after the ledger has something to show.
- **A verdict.** The rule for "the claims come true" belongs to the pre-registered exit experiment (DL-240), not here.
- **Held positions, exits, sizing.** Later sprints, and the operator's call.
- **Any new provider fetch or provider change.** The bars are already in the graph.
- **Backfilling claims for runs before `s239`** (DL-241 D11's rejected option (a)).

### The road not taken (LAW-06)

- **Have the provider write a settlement history** (D10's pattern). Rejected: every run's `MarketData` already holds
  the whole universe's bars (90 of 90 covered), so a new artifact would duplicate what is there.
- **Settle from the claim's `entry_close`.** Rejected: the claim's bars and the settling bars are separate fetches;
  measuring both ends on one series is exact whatever the adjustment. The ratio is kept, so drift stays visible.
- **Re-estimate climatology from the ledger.** Rejected: a baseline fitted to the outcomes it scores flatters
  nothing and moves under the reader; EXP-018's shares are pre-registered.
- **Treat a split as a stop** (raw bars as they come). Rejected: it scores a corporate action as a forecast failure.
- **Write the outcome onto the `BarrierForecast`.** Rejected: the claim is a record of what was said; what happened
  is a separate, later fact with its own provenance.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **How the settlement pass is marked done per run**, and how it shares the loop with the claim work without
   pushing `poll.py` (151) past 200. Say what you moved.
2. **Which `MarketData` settles a claim** when several runs cover it (the first run whose bars hold ten sessions after
   `as_of` is the natural one; say why, and that the choice is recorded in `settling_ref`).
3. **How the 45-day void fires** when no run covers the ticker (it has to run on some pass, not only when bars exist).
4. **The final wording of the new clauses.**

🪤 **Take the next free DL number, then re-check it at merge.** `DL-243` is free at spec time.

---

## Blast radius — measured 2026-09-28

| What | Detail |
| --- | --- |
| Files changed | new settlement / scorecard modules under `agents/forecaster/`; `poll.py` (**151**), `entrypoint.py`, `agent.py` (164), `settings.py`; `contracts/forecaster.py`; `orchestration/packs/trading_graph_vocabulary.json`; `orchestration/local_pipeline.py` if the local pipeline needs wiring; `scripts/barrier_ledger.py`; tests; `agents/forecaster/laws/{laws,test-plan}.md`, `docs/laws/{ledger,INDEX,drift-register}.md`, `docs/design-log.md` |
| Agents affected | forecaster only. No agent imports another. |
| Contract change? | **Yes** (`contracts/forecaster.py`): the law cycle above is mandatory. `contracts/` is a fidelity decision path; DL-237's first verdict already runs from `8a059386`. |
| Graph vocabulary change? | **Yes**, a new label and edge: the deploy is a **full `up`**. |
| New env keys / tunables | none expected: the outcome rule, the void thresholds and the baseline are constants citing this spec and EXP-018. If you add one, give it a PARAM row. |
| Deploy implication | **Full `up`**, the operator's call. It changes nothing the fleet trades. |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Plant the failing tests first** (C1–C9) and watch them fail. Paste the red output.
4. **Implement.**
5. **Law cycle**: amended `FORE-IDN-02`, the new `OUT` and `FAIL` clauses, `TRG`, `CAP`, `PARAM`, v1.7 + Changelog,
   test-plan rows, docstring citations, both rollups, drift row if owed.
6. **Prove the guards can fail (DL-70)**: plant each, watch it go red, restore: the target checked before the stop
   (C1 red); settlement from the claim's `entry_close` instead of the settling close (C2 red); the corporate-action
   void removed (C3 red); the pass not marked, so a claim settles twice (C6 red); the climatology re-estimated from
   the ledger (C7 red).
7. **`make ci` green**: every step of the `ci:` target, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| C1 | 🎯 The outcome is EXP-018's (`FORE-OUT-08`) | synthetic bars: stop first, target first, neither, and one session touching both | stop, target, neither, stop; equal to `scripts/barrier_testbed.outcome()` on the same bars (the oracle) |
| C2 | Measured from the settling series' own close | settling bars whose `as_of` close differs from the claim's `entry_close` by 3 % | the outcome follows the settling close; `entry_ratio` recorded |
| C3 | 🪤 A split is `void`, never a stop (`FORE-FAIL-05`) | a 2:1 split (close ratio 0.5) inside the window; a 1:3 reverse split (3.0) | `void`, `suspected_corporate_action`; no Brier |
| C4 | Too few bars is not a settlement (`FORE-FAIL-05`) | the `as_of` bar missing; 9 sessions after it | the claim stays open; on the pass 45 days after `as_of`, `void`, `no_settling_bars` |
| C5 | 🎯 A settlement records what sprint B's reader needs (`FORE-OUT-08`, `FORE-IDN-02`) | one claim, one covering `MarketData` | every field in Scope 5; the edge from the claim; `brier` equals the three-class Brier by hand |
| C6 | 🪤 Settled once (`FORE-IDM`) | two passes over the same run, then a later run that also covers the claim | one `BarrierSettlement`; `settling_ref` names the first covering run |
| C7 | 🎯 The scorecard (`FORE-OUT-03/04`, `FORE-OUT-08`) | a fixture ledger with known outcomes and claims | counts, shares, `brier_model`, `brier_climatology` from EXP-018's fixed shares, `skill`, a bootstrap interval equal to EXP-018's `run()` on the same cases with the same seed; `promotion_eligible` is `False`; fewer than 2 dates → no interval |
| C8 | The deployed loop settles; the local pipeline too (`FORE-TRG-01`) | a current `AnalystRun` whose run's `MarketData` covers an older claim; a non-current one | the current run settles the claim; the old run is skipped (D11) |
| C9 | 🪤 Nothing reaches the decision path (`FORE-NEV-01/02`) | a full pass on a fake graph | no node with a PM, execution or monitor label; no message to those agents |

---

## Success factors

- [ ] Every claim settles once, by EXP-018's rule on the settling series, or `void` with a named reason (C1–C6).
- [ ] The scorecard reports counts, shares, Brier, skill over EXP-018's fixed climatology and a date-bootstrap interval
      that matches EXP-018's own scorer on the same cases (C7).
- [ ] Nothing reaches the PM, execution or monitor (C9).
- [ ] Law cycle done; design decisions recorded under a free DL.
- [ ] Every DL-70 plant in step 6 planted, watched to fail, restored — stated per plant.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.
- [ ] **Planner, before merge (live data):**
  - **F1, settle the past**: run the settlement function, read-only, over the live graph's recent runs as if each buy
    had been claimed (the claims' probabilities do not matter for the outcome): every buy of the last 30 runs settles
    or voids with a named reason, and the outcome shares are near EXP-018's (0.29 / 0.48 / 0.24) or the gap is named.
  - **F2, the oracle on the replay cache**: the settlement function reproduces `scripts/barrier_testbed.outcome()` on
    EXP-011's 47,485 decisions, outcome for outcome.
  - **F3, the script**: `scripts/barrier_ledger.py` runs against the live graph and prints an empty ledger (0 settled)
    without error.
- [ ] **Owed after the operator's full `up` (F4)**, from about 2026-10-12: the first claims settle on the run that
      covers their tenth session, and the scorecard reports them.

---

## Traps

🪤 **The bars are raw.** A split looks like a crash. The corporate-action void exists for this; test it with a real
ratio (0.5, 0.1, 3.0), not a made-up one.
🪤 **Two fetches, two series.** Never mix the claim's `entry_close` with the settling bars' highs and lows.
🪤 **Daily bars are stamped 04:00Z or 05:00Z.** Compare bar *dates*, never timestamps.
🪤 **`MarketData` nodes are large (98 × 203 bars).** Read one by key per pass; never list every `MarketData` in the
graph per poll.
🪤 **`poll.py` is at 151.** Put the settlement pass in its own module.
🪤 **The vocabulary guard is fail-closed.** Test the new label and edge against the pack.
🪤 **A settlement is a fact about the market, not about the model.** It must not read the claim's probabilities to
decide the outcome; only the Brier uses them.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass a rule.
  📌 Current sizes: `agent.py` **164**, `poll.py` **151**, `entrypoint.py` 63, `scorecards.py` 83.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: the void thresholds (0.6, 1.67, 45 days), the horizon and the baseline shares are named constants
  citing this spec or EXP-018.
- Faults, not silent failure: `kernel.fault_boundary`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a pipe.**
- Version bump: MINOR in `pyproject.toml`. 🪤 A cloud session cannot re-resolve `uv lock` (`download.pytorch.org` is
  blocked, DL-228): leave `uv.lock` untouched and say so; the planner re-locks.
- Secrets never through the tree. The cloud session has **no `.env`, no `gh` and no Azure**: state which environment
  you ran in, and leave F1–F3 to the planner.

---

## Sequencing after merge

1. The cloud session: `make ci` green in its environment, the branch pushed, then it stops.
2. The planner, locally: re-lock, `make ci` on Windows, **`make gate-ran`** from a worktree whose `HEAD` is the pushed
   commit (check the printed SHA), F1–F3, the branch ref's open CodeQL alerts.
3. Merge to `main` locally and push; post-merge CodeQL on `main`.
4. **Deploy: a full `up`** (the vocabulary moved), the operator's call. F4 from about 2026-10-12.

---

## Handover — paste this to the Claude cloud session

```text
Sprint 241 — ten sessions after each barrier claim, the forecaster settles it, and a scorecard says
whether the claims come true. Spec: docs/sprints/sprint-241-each-barrier-claim-is-settled-and-scored.md
on main (read ALL of it, then CLAUDE.md). Repo: yury-gurevich/trading-agents.

Branch: sprint-241-each-barrier-claim-is-settled-and-scored, cut from main. Never main. If your
session forces another branch name, use it and name it in the handback.
You have NO .env, NO gh, NO Azure and no route to download.pytorch.org. Every proof is a unit test.
You cannot run `make gate-ran`: it is owed to the planner. Leave uv.lock untouched and say so; the
planner re-locks. A run result read through the GitHub connector is an observation, never GATE
PROVEN. Take DL-243 (re-check it is still free on main).

This handover is complete: nobody will send you follow-up messages. If something in the spec is
wrong or blocked, record it in the handback (Return notes, "not done") and stop; do not wait.

What and why: DL-240 says nothing sizes or exits on a probability until a ledger shows it comes true.
S239 (deployed) records, per buy, P(stop first / target first / neither) within 10 sessions as a
BarrierForecast. This sprint settles each claim once its 10 sessions have passed and scores the
ledger. Measured: every scheduled run's MarketData (key market-data:{run_id}) holds 98 tickers x 203
sessions of RAW daily bars; the run 11 sessions later covered 90 of 90 recent buys. No provider change.

MUST RULE before any code: read agents/forecaster/laws/laws.md and test-plan.md whole,
docs/laws/conventions.md, docs/laws/drift-register.md. Fill the Law reading record first.

Law-cycle answer: YES (contracts/forecaster.py changes; new guarantees). Amend FORE-IDN-02 (also
writes BarrierSettlement); new OUT clause (settled once, EXP-018's rule, from provider-written bars,
append-only; barrier_scorecard reports); new FAIL clause (void with a named reason, never a false
outcome); TRG, CAP, PARAM; v1.6 -> v1.7 + Changelog; test-plan rows; clause IDs in docstrings;
rollups in docs/laws/ledger.md AND docs/laws/INDEX.md; drift row if owed.

Build:
1. Settlement, pure: EXP-018's outcome rule exactly (scripts/barrier_testbed.outcome() is the
   oracle: sessions 1..10 after as_of, low <= entry*(1-stop) is the stop and is checked first, high >=
   entry*(1+target) the target, else neither), with entry = the SETTLING series' own close on as_of;
   record entry_ratio = settling close / claim entry_close.
2. Void, never a false outcome: as_of bar missing or < 10 later sessions -> stays open; any
   session-over-session raw close ratio in the window < 0.6 or > 1.67 -> void
   suspected_corporate_action (raw bars: a split looks like a crash); still open 45 calendar days
   after as_of -> void no_settling_bars. Named constants, not tunables.
3. Trigger: the deployed loop (and the local pipeline) gains a settlement pass per CURRENT
   AnalystRun (contracts/barrier_history.is_current_run): read that run's MarketData through its
   lineage (AnalystRun <-ANALYZED_BY- ScanRun -DERIVED_FROM-> MarketData, as
   agents/portfolio_manager/poll.py does), settle every open claim it covers, mark the pass done per
   run. Read ONE MarketData by key per pass; never list them all. Own module: poll.py is at 151.
4. Record: BarrierSettlement keyed from the claim key, edge from the BarrierForecast; fields:
   claim_key, ticker, as_of, outcome (stop|target|neither|void), void_reason, settled_on,
   settling_ref, entry_close_settling, entry_ratio, brier (3-class; absent for void), created_at.
   Settled once, never again.
5. barrier_scorecard capability (request: model_id -> Scorecard, promotion_eligible False): settled,
   void, open; realised shares and mean declared per outcome; brier_model; brier_climatology from
   EXP-018's FIXED shares (stop 0.287, target 0.477, neither 0.236); skill = 1 - model/climatology;
   skill_lo / skill_hi by EXP-018's date bootstrap (1,000 draws, fixed seed; copy its run() from
   the EXP-018 appendix exp018_score.py); fewer than 2 settled dates -> no interval.
6. scripts/barrier_ledger.py: read-only, prints the scorecard and one line per settlement.
7. Declare: contracts/forecaster.py (capability, request, BarrierSettlement in owns_graph); the
   vocabulary pack (label, properties, edge + signature); MINOR version bump.

Order: DL-243 -> red tests C1-C9 (paste) -> implement -> law cycle -> DL-70 plants (target checked
before stop; entry from the claim's entry_close; corporate-action void removed; pass not marked so a
claim settles twice; climatology re-estimated from the ledger: each must go red, paste, restore) ->
make ci redirected to a file, exit 0, 100.00 %.

DO NOT:
- let anything outside the forecaster read BarrierSettlement or the scorecard (FORE-NEV-01/02).
- change the provider, add a fetch, or change orchestration/history_window.py.
- settle from the claim's entry_close, or read the claim's probabilities to decide an outcome.
- score a suspected corporate action as a stop, target or neither.
- re-estimate climatology from the ledger.
- list every MarketData per poll; grow poll.py past 200; # noqa to bypass a rule.
- let any test reach the network.
- claim a live proof or GATE PROVEN: F1-F3 and the gate are the planner's.
- pin a version: MINOR, next available at merge.

Handback — the planner returns it if ANY of these is missing:
[ ] Law reading record filled, including the law-cycle answer and contradictions/silences found.
[ ] Test plan results: C1-C9, each with final test name, file, PASS, clause IDs cited.
[ ] Closeout: the red run pasted before the fix; the green run after.
[ ] Each of the five DL-70 plants: what was planted, its red output, restored.
[ ] Module line counts for every file touched (all < 200).
[ ] make ci: the file, exit code, passed/skipped, coverage 100.00 %, dependency audit, detect-secrets.
[ ] Exactly how uv.lock was touched (untouched and owed, or re-resolved).
[ ] The design decisions under DL-243 with rejected alternatives.
[ ] Return notes: scope held or moved; what you disagreed with after reading the laws; what the
    exit experiment should know about the ledger.
[ ] Status: BUILT on the spec, and this sprint's README.md row leads with BUILT, in the same commit.
[ ] Owed items named: uv lock, make gate-ran, Windows make ci, F1-F3, full up, F4.
Commit on the branch and PUSH it, then stop: no merge. Anything not met: "not done", never a
Result: for work not done.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| *(builder)* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(builder)*

**Contradictions found between a law and this spec:** *(builder)*

**Laws found silent where a decision was needed:** *(builder)*

**Clauses that were ⬜ and are now proven:** *(builder)*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| C1 | *(builder)* | | | |

**Tests added beyond the plan:** *(builder)*

---

## Closeout — evidence

**Status:** *(builder: BUILT)*

**Tree the proofs ran in (and `.env` present?):** *(builder)*

**Result:** *(builder)*

**Files changed:** *(builder)*

**Design decisions:** *(builder: DL number, one line, where the rejected alternatives are)*

**Proof — the red run first:**

```text
(builder)
```

**Proof — the green run:**

```text
(builder)
```

**Guards planted:** *(builder, per plant)*

**Module line counts:** *(builder)*

**`make ci`:** *(builder: file, exit code, passed/skipped, coverage, dependency audit, detect-secrets)*

**`uv.lock`:** *(builder: untouched and owed, or re-resolved)*

**`make gate-ran`:** *(planner: local worktree, full SHA, output)*

**Planner live checks (F1–F3):** *(planner, before merge)*

**Not met / verified failing:** *(builder)*

---

## Return notes

- *(builder: scope held, or where it moved and why)*
- *(builder: what you disagreed with in the spec after reading the laws)*
- *(builder: what the exit experiment should know about the ledger)*
