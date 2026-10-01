<!-- Agent: planning | Role: sprint handover -->
# Sprint 241 — ten sessions after each barrier claim, the forecaster settles it, and a scorecard says whether the claims come true

**Phase:** Etalon-first continuous improvement (DL-19) · work-queue 92 (the book as a distribution), sprint B of the ledger
**Branch:** `sprint-241-each-barrier-claim-is-settled-and-scored` (built on `claude/loving-meitner-qeoxgm`, the name the cloud session forced)
**Status:** MERGED 2026-09-29 — `e6891411`, tag `v0.119.00`, on `main`; deployed with S242's full `up` (corrected 2026-10-01; the line read: BUILT 2026-09-29 by the cloud session on `claude/loving-meitner-qeoxgm` (cut from `main` `60400a5`), not merged: C1–C9 green, `make ci` exit 0 in the container (3,592 passed, 100.00 %); owed to the planner: `uv lock`, `make gate-ran`, Windows `make ci`, F1–F3, then a full `up` and F4)
**Version:** *next available MINOR at merge* (`0.119.00` on the branch)
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

*Filled 2026-09-28 by the builder (Claude cloud session) before the first code change. Read whole, first time:
`agents/forecaster/laws/laws.md` (v1.6, 293 lines, 49 clause IDs), `agents/forecaster/laws/test-plan.md` (22 / 49),
`docs/laws/conventions.md`, `docs/laws/drift-register.md` (last ID `DRIFT-082`). Also read for the design: EXP-018 §3–§8 and
Appendix S (`exp018_score.py`'s `run()`), `scripts/barrier_testbed.py` (`outcome()`), DL-240 and DL-241 (D1–D11), and the
code the clauses govern (`poll.py`, `entrypoint.py`, `agent.py`, `barrier_store.py`, `barrier_forecast.py`,
`contracts/forecaster.py`, `contracts/barrier_history.py`, `agents/portfolio_manager/poll.py`'s lineage walk,
`agents/provider/domain/integrity.py`, `kernel/work_loop*.py`, `kernel/graph_vocabulary.py`, the vocabulary scans in
`scripts/vocabulary_*.py`, `scripts/check_law_coverage.py`).*

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| New settlement modules (the pure rule, the record, the pass) | forecaster `laws.md` + `test-plan.md`; `conventions.md` | `FORE-IDN-02` (🟩), `FORE-OUT-07` (🟩, the claim's fields), `FORE-NEV-01/02/04` (🟩), `FORE-STA-02` (⬜), `FORE-IDM-04` (🟩), `FORE-FAIL-04` (🟩); new `OUT`/`IDM`/`FAIL` clauses | **Yes, three ways.** (1) `FORE-NEV-04` (v1.6) allows market data "read from a node the provider wrote": the run's `MarketData` is such a node, so the pass reads it through the run's lineage and sends nothing over the bus. (2) The graph refuses to overwrite a property (DL-241 D5), so "settled once" cannot be a re-merge: it is an open-claim filter before any write plus a per-run pass marker written last. (3) The spec's C6 cites "`FORE-IDM`", but no existing `IDM` clause governs settlement (`IDM-01`/`02` are the sentiment and return models, `IDM-03` the shadow scorecards over `ShadowPrediction`, `IDM-04` the claim); citing one would narrow it to fit a test (§7a), so idempotency gets a new **`FORE-IDM-05`**, as S239 added `IDM-04`. |
| The settlement trigger: new `work.py`, `entrypoint.py`, `orchestration/local_pipeline.py` | same | `FORE-TRG-01` (🟩), `FORE-TRG-02` (🟩) | **Yes.** `TRG-02` forbids a timer, so the 45-day void cannot be a scheduled sweep: it is evaluated on every pass a run triggers, dated by the run (design decision 3). `TRG-01` names "an `AnalystRun` with no `ForecasterRun`" as the loop's only work; it is amended for the settlement pass, and the deployed pass keeps D11's current-run rule. |
| `barrier_scorecard` (handler, pure scoring), `agent.py` | same | `FORE-OUT-03/04` (🟩), `FORE-NEV-03` (🟩), `FORE-IDM-03` (⬜) | **Yes.** `OUT-03` names exactly three capabilities; C7 cites it, which is honest only if `OUT-03` names `barrier_scorecard` too, so `OUT-03` is widened by that one name (its three existing tests still hold). `IDM-03` says scorecard methods read `ShadowPrediction` nodes; the barrier scorecard reads claims and settlements. Left as worded (not in this amendment) and registered as `DRIFT-083`. |
| `contracts/forecaster.py` | same | `FORE-CAP` (⬜), `FORE-TYP-01` (🟩) | The capability, `BarrierScorecardRequest`, and the owned labels join the contract; version `0.6.0` → `0.7.0`; `ShadowPrediction` / `Scorecard` fields untouched, so `TYP-01` holds. The `CAP` block never listed `ForecasterRun` (written since before S239) or the `AnalystRun` / `BarrierHistory` reads S239 added; its amendment now lists every label written and read. |
| `orchestration/packs/trading_graph_vocabulary.json` | DL-85; `tests/test_graph_vocabulary_*.py`; `scripts/vocabulary_properties.py` | the fail-closed write guard | Both new labels with their property names, both edge types and both signatures are declared; props are written from dict literals so the static property scan can read every write site (a blind site fails `make ci`); a test runs the pass through `GuardedGraphStore` built from the pack. |
| `scripts/barrier_ledger.py` (new, read-only) | `CLAUDE.md` (read-only tooling) | `FORE-NEV-01/02` | It composes with the forecaster's own scorecard and settlement reads, writes nothing, and is proven with a graph that refuses every write. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **Yes, both** (the spec's answer
holds). Owed in this unit of work: `FORE-IDN-02` amended; new **`FORE-OUT-08`** (settlement + scorecard; next free `OUT`,
checked: `OUT-01..07` exist), **`FORE-FAIL-05`** (void with a named reason; next free `FAIL`, checked), and **`FORE-IDM-05`**
(settled once, one pass per run, a deterministic scorecard; beyond the spec's list, reason above); `FORE-TRG-01` amended;
`FORE-OUT-03` widened by one name; `CAP`; **`PARAM`: no new setting** (the void thresholds, the horizon, the baseline and
the bootstrap are named constants citing this spec and EXP-018, and `check_param_law_sync.py` fails a `PARAM` row that
names no settings field); v1.6 → v1.7 + Changelog; test-plan rows; both rollups; drift rows.

**Contradictions found between a law and this spec:** none that forces a stop. Three places where the spec's wording is
narrower than the law needs, resolved without weakening anything: (1) C6's "`FORE-IDM`" names no clause that covers it →
new `FORE-IDM-05`. (2) C7's `FORE-OUT-03` does not name `barrier_scorecard` → `OUT-03` widened by that name (a widening,
changelogged). (3) The spec amends `FORE-IDN-02` for `BarrierSettlement` only; the per-run pass marker (design decision 1)
is a second label the forecaster writes, and `DRIFT-081` prescribes adding `ForecasterRun` "at the next forecaster
amendment", which this is: `IDN-02` lists all six labels, and `DRIFT-081` is corrected for that third only.

**Laws found silent where a decision was needed:**

- **The provider's book does not say which price adjustment its bars carry.** The settlement's corporate-action void
  exists because the bars are raw (measured from the code by the planner: no `adjustment` anywhere). Registered as
  `DRIFT-084` for the provider book; the settlement is correct either way (it measures one series end to end, and
  `entry_ratio` shows any adjustment between the two fetches).
- **`FORE-IDM-03`** reads as if every scorecard method reads `ShadowPrediction` nodes (`DRIFT-083`).
- **No clause said when a claim stops waiting for bars**, or which later fetch settles it (design decisions 2 and 3).
- **Nothing defines a "session" when the series has a gap** (a halt): EXP-018's rule counts the series' rows, and the
  settlement does the same (Return notes).

**Clauses that were ⬜ and are now proven** *(result, at handback)*: **none of the 27 pre-existing ⬜ clauses
moved.** The three new clauses, `FORE-OUT-08`, `FORE-IDM-05` and `FORE-FAIL-05`, are 🟩 on their citing tests, and the
amended `FORE-IDN-02`, `FORE-TRG-01` and `FORE-OUT-03` stay 🟩 with new citing tests; `check_law_coverage.py` derives the
forecaster at **25 / 52** (was 22 / 49), matching both rollups. `FORE-STA-02`, `FORE-IDM-03`, `FORE-OBS-01` and
`FORE-IN-06` stay ⬜: the new tests touch only the barrier ledger's part of each, which §7a says leaves a general clause
gray.

---

## Test plan results — fill at handback

Every row PASS in the final `make ci` run (Closeout). Agent-local files are in `agents/forecaster/tests/`.

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| C1 | `test_the_outcome_is_exp018s` ×4 (stop first, target first, neither, one session touching both → stop), each equal to `scripts/barrier_testbed.outcome()` on the same bars (imported as the oracle); `test_the_settlement_equals_the_test_beds_outcome_on_random_paths` (400 random paths and barriers, outcome for outcome: 178 stop, 192 target, 30 neither) | `test_barrier_settlement.py` | PASS | `FORE-OUT-08` |
| C2 | `test_the_entry_is_the_settling_series_own_close` (settling close 103 against a claimed 100: stop from the settling close, target had the claim's been used; `entry_ratio` 1.03) | `test_barrier_settlement.py` | PASS | `FORE-OUT-08` |
| C3 | `test_a_split_is_void_never_a_stop` ×3 (close ratios 0.5, 0.1, 3.0: the raw rule says stop, stop, target; the settlement says `void`, `suspected_corporate_action`), `test_the_corporate_action_bounds_are_the_specs` ×4 (0.6 and 1.67 settle, 0.599 and 1.671 void); `test_a_split_settles_void_with_no_brier` (the record: `brier` null) | `test_barrier_settlement.py`; `test_barrier_settlement_record.py` | PASS | `FORE-FAIL-05`, `FORE-OUT-08` |
| C4 | `test_too_few_bars_is_not_a_settlement` (no `as_of` bar; 9 sessions after it: open), `test_an_unsettled_claim_is_void_45_days_after_as_of` (open on the pass 44 days after, `void` / `no_settling_bars` on the pass 45 days after, dated that pass) | `test_barrier_settlement.py` | PASS | `FORE-FAIL-05` |
| C5 | `test_a_settlement_records_every_field_the_ledger_needs` (every Scope 5 field plus `model_id`, the key, the `SETTLED_BY` edge, `brier` = 0.3² + 0.5² + 0.2² = 0.38 by hand, the pass marker's counts), `test_the_settlement_passes_the_packs_vocabulary_guard` (the whole pass through `GuardedGraphStore` built from the pack) | `test_barrier_settlement_record.py` | PASS | `FORE-OUT-08`, `FORE-IDN-02`, `FORE-NEV-04` |
| C6 | `test_a_claim_is_settled_once` (two `run_once` passes over the same run, a direct second call, then a later run whose bars would say stop: one settlement, `settling_ref` = the first run's `MarketData`, one pass node per run, no run left pending, no fault) | `test_barrier_settlement_record.py` | PASS | `FORE-IDM-05` |
| C7 | `test_the_scorecard_reports_the_ledger_as_exp018_scores_it` (10 settled on 4 dates, 1 void, 1 open, another model's settled claim; counts and shares by hand; `brier_model`, `brier_climatology`, `skill`, `skill_lo`, `skill_hi` **exactly equal** to EXP-018's `run()` read from the record and run on the same cases, order and seed; `promotion_eligible` False), `test_the_oracle_is_the_records_run`; `test_fewer_than_two_settled_dates_give_no_interval`, `test_an_empty_ledger_reports_counts_and_no_scores`, `test_another_models_ledger_is_its_own`, `test_the_scorecard_is_read_only_and_repeatable` | `test_barrier_scorecard_oracle.py`; `test_barrier_scorecard.py` | PASS | `FORE-OUT-08`, `FORE-OUT-03`, `FORE-OUT-04`, `FORE-NEV-03`, `FORE-IDM-05` |
| C8 | `test_the_deployed_loop_settles_on_a_current_run_only` (the deployed work list: the current run's forecast and settlement pass, which settles the older claim from that run's bars; an old run whose bars also cover it gets no work); `test_main_runs_the_graph_pull_loop_with_the_barrier_leg_only` (updated: the container's loop runs both kinds for the current run, none for the old one); the local pipeline: `orchestration/tests/test_forecaster_settlement_stage.py::test_the_local_pipeline_settles_an_older_claim` | `test_barrier_settlement_loop.py`; `test_forecaster_entrypoint.py`; `orchestration/tests/test_forecaster_settlement_stage.py` | PASS | `FORE-TRG-01` (and `FORE-TRG-02` on the entrypoint test), `FORE-OUT-08` |
| C9 | `test_a_full_deployed_pass_never_reaches_the_decision_path` (forecast + settlement on a fake graph: no PM, execution or monitor label; no message to any agent but the forecaster), `test_nothing_outside_the_forecaster_reads_the_ledger` (no shipped module outside the forecaster and its read-only script names `BarrierSettlement`, `SETTLED_BY` or `barrier_scorecard`) | `test_barrier_settlement_loop.py` | PASS | `FORE-NEV-01`, `FORE-NEV-02` |

**Tests added beyond the plan:** `test_the_pass_reads_only_its_own_runs_market_data` (`FORE-TRG-01` / `FORE-NEV-04`: a
graph that refuses to list `MarketData`; a run without lineage settles nothing and records `settling_ref: null`);
`test_barrier_settlement_faults.py`: `test_a_claim_the_pass_cannot_read_faults_and_stays_open`,
`test_an_unreadable_market_data_faults_and_the_age_rule_still_runs` (`FORE-FAIL-05`), and
`test_a_run_without_a_readable_stamp_is_dated_today` (DL-243 D3, no clause); `tests/test_barrier_ledger.py` ×3 (the
script prints the counts, the scores and one line per settlement from a graph that refuses every write; an empty ledger
prints `settled 0  void 0  open 0` and exits 0; no `POSTGRES_DSN` exits 1). **Updated:**
`test_forecaster_boundary.py::test_contract_declares_never_clauses_and_no_external_io` (contract `0.7.0`, the capability,
the two labels), `orchestration/tests/test_graph_pull_e2e.py::test_trigger_then_cascade_builds_full_chain` and
`orchestration/tests/test_drop_sweep_cascade.py::test_poisoned_drop_sweep_still_reaches_reporter` (the stage list gains
`forecaster_settlement: 1`).

---

## Closeout — evidence

**Status:** BUILT 2026-09-29 by the cloud session; not merged, not deployed.

**Tree the proofs ran in (and `.env` present?):** a claude.ai cloud container, Linux, Python 3.13.12 through uv 0.8.17,
a clone of `yury-gurevich/trading-agents` on branch **`claude/loving-meitner-qeoxgm`** (the session forced this name; the
spec's is `sprint-241-each-barrier-claim-is-settled-and-scored`), cut from `main` `60400a5` (this spec's commit). **No
`.env`**, no `gh`, no Azure, no route to `download.pytorch.org`. Every `uv run` ran with `UV_FROZEN=1` (the bumped
`pyproject.toml` cannot be re-locked here). No test reaches the network: the graph is in memory, the fitter a fake, the
provider a fixture source, the script's live graph replaced in-process.

**Result:** proven by unit tests only. For each open `BarrierForecast`, one settlement pass per `AnalystRun` reads that
run's `MarketData` through its lineage (one node; a graph that refuses to list `MarketData` stays green) and settles the
claim by EXP-018's rule measured from the settling series' own `as_of` close, equal to `scripts/barrier_testbed.outcome()`
on 4 crafted and 400 random paths; a raw close ratio outside 0.6–1.67 in the window is `void` /
`suspected_corporate_action` (0.5, 0.1 and 3.0 tested), a claim with no `as_of` bar or fewer than 10 later sessions stays
open and is `void` / `no_settling_bars` on the pass 45 days after `as_of`. Each settlement is written once, as a
`BarrierSettlement` linked from its claim with every Scope 5 field (plus `model_id`), through the pack's fail-closed
vocabulary guard; each run is passed once (a `BarrierSettlementPass`, written last). The deployed loop runs the pass as
its second work kind, on current runs only; the local pipeline runs it as its own stage. `barrier_scorecard` reports
counts, shares, mean declared probabilities, Brier, skill over EXP-018's fixed climatology and the date-bootstrap
interval, exactly equal to EXP-018's own `run()` on the same cases, order and seed; never promotion-eligible; nothing
reaches the decision path. `scripts/barrier_ledger.py` prints the ledger and writes nothing. **Nothing here is proven on
live data** (F1–F3 are the planner's; F4 needs a deploy and ten sessions).

**Files changed:** new `agents/forecaster/domain/barrier_settlement.py` (the pure rule and void, `outcome_index` copied
from the test bed), `domain/barrier_skill.py` (EXP-018's scoring and date bootstrap), `settlement_store.py` (the record and
the ledger read), `settling_bars.py` (the run's `MarketData` by lineage and its bars), `settlement_pass.py` (the pass and
its marker), `barrier_scorecard.py` (the handler), `work.py` (the deployed work list: forecast + settle);
`agent.py` (binds `barrier_scorecard`), `entrypoint.py` (runs `work.py`'s list); `contracts/forecaster.py`
(`BarrierScorecardRequest`, the capability, `BarrierSettlement` and `BarrierSettlementPass` in `owns_graph`, version
`0.7.0`); `orchestration/packs/trading_graph_vocabulary.json` (2 labels with their properties, 2 edge types, 2
signatures; additions only); `orchestration/local_pipeline.py` (the `forecaster_settlement` stage); new
`scripts/barrier_ledger.py`; `pyproject.toml` (`0.119.00`); tests: new `settlement_paths.py`, `settlement_helpers.py`,
`ledger_fixture.py`, `test_barrier_settlement{,_record,_faults,_loop}.py`, `test_barrier_scorecard{,_oracle}.py`,
`orchestration/tests/test_forecaster_settlement_stage.py`, `tests/test_barrier_ledger.py`; updated
`test_forecaster_boundary.py`, `test_forecaster_entrypoint.py`, `orchestration/tests/test_graph_pull_e2e.py`,
`orchestration/tests/test_drop_sweep_cascade.py`; laws: forecaster `laws.md` (v1.7) and `test-plan.md`,
`docs/laws/{ledger,INDEX,drift-register}.md`; `docs/design-log.md` (DL-243), `docs/STATE.md`,
`docs/sprints/{README,INDEX}.md`, this file. **Not touched:** `agents/forecaster/poll.py` (151), the provider,
`orchestration/history_window.py`, `uv.lock`.

**Design decisions:** [DL-243](../design-log.md): D1 the pass is marked by its own `BarrierSettlementPass` node, written
last, and joins the deployed loop as a second work kind in a new `work.py` (nothing moved out of `poll.py`); D2 the first
later run whose bars cover the claim settles it, named in `settling_ref`; D3 the 45-day void is evaluated on every pass,
dated by the run's `created_at`, never by a timer; D4 the clause wording; plus six builder's choices. The rejected
alternatives are listed under each in DL-243.

**Proof — the red run first** (the new test files and the edited existing tests, before any implementation, `pytest
--no-cov`; the collection errors stop that session, so the four edited existing tests were run on their own too):

```text
E   ModuleNotFoundError: No module named 'agents.forecaster.domain.barrier_settlement'
E   ModuleNotFoundError: No module named 'agents.forecaster.settlement_pass'
E   ModuleNotFoundError: No module named 'agents.forecaster.domain.barrier_settlement'
E   ModuleNotFoundError: No module named 'agents.forecaster.domain.barrier_settlement'
E   ModuleNotFoundError: No module named 'agents.forecaster.domain.barrier_settlement'
E   ModuleNotFoundError: No module named 'scripts.barrier_ledger'
ERROR agents/forecaster/tests/test_barrier_settlement.py
ERROR agents/forecaster/tests/test_barrier_settlement_record.py
ERROR agents/forecaster/tests/test_barrier_scorecard.py
ERROR agents/forecaster/tests/test_barrier_settlement_loop.py
ERROR orchestration/tests/test_forecaster_settlement_stage.py
ERROR tests/test_barrier_ledger.py
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
6 errors in 2.13s

E     Right contains 1 more item:
E     {'forecaster_settlement': 1}
E     Right contains 1 more item:
E     {'forecaster_settlement': 1}
E   AttributeError: 'Node' object has no attribute 'kind'
E   AssertionError: assert '0.6.0' == '0.7.0'
FAILED orchestration/tests/test_graph_pull_e2e.py::test_trigger_then_cascade_builds_full_chain
FAILED orchestration/tests/test_drop_sweep_cascade.py::test_poisoned_drop_sweep_still_reaches_reporter
FAILED agents/forecaster/tests/test_forecaster_entrypoint.py::test_main_runs_the_graph_pull_loop_with_the_barrier_leg_only
FAILED agents/forecaster/tests/test_forecaster_boundary.py::test_contract_declares_never_clauses_and_no_external_io
4 failed, 8 passed in 0.94s
```

**Proof — the green run** (the same files plus the two split out or added later,
`test_barrier_scorecard_oracle.py` and `test_barrier_settlement_faults.py`, on the final tree):

```text
................................................                         [100%]
48 passed in 1.25s
```

**Guards planted** (DL-70; each planted on the final tree with a backup in the session scratchpad, run, and restored
from the backup, `cmp` byte-identical):

1. **Target checked before stop** (`outcome_index`: the `hi >= …` test moved above the `lo <= …` test) → **C1 red**:
   `FAILED test_the_outcome_is_exp018s[both-in-one-session]` — `assert 'target' == 'stop'`, and
   `FAILED test_the_settlement_equals_the_test_beds_outcome_on_random_paths` — `assert 'target' == 'stop'` (a random
   path touching both in one session); 2 failed, 13 passed. Restored.
2. **Entry from the claim's `entry_close`** (the `as_of` close replaced by `entry_close` in the series passed to
   `outcome_index`) → **C2 red**: `FAILED test_the_entry_is_the_settling_series_own_close` — `assert 'target' ==
   'stop'`; 1 failed, 14 passed (every other fixture's two closes agree, so only C2 can see it). Restored.
3. **Corporate-action void removed** (the `_corporate_action` check deleted from `settle`) → **C3 red**: 6 failed —
   `test_a_split_is_void_never_a_stop[2:1]`, `[10:1]` (`outcome: 'stop' != 'void'`), `[1:3]` (`outcome: 'target' !=
   'void'`), `test_the_corporate_action_bounds_are_the_specs[below-0.6]`, `[above-1.67]`, and
   `test_a_split_settles_void_with_no_brier`. Restored.
4. **The pass not marked** (the `BarrierSettlementPass` merge and its edge deleted) → **C6 red**: `FAILED
   test_a_claim_is_settled_once` — `assert [Node(label='AnalystRun', key='run-a', …)] == []`: the run is still pending
   after its pass, so every poll would pass over it again (the work loop reads that as "no progress" and quarantines it
   after five attempts). Restored. 🪤 **What this plant did not show, stated plainly:** with only the marker gone, the
   claim was **not** settled twice, because the pass settles open claims only (the spec's wording assumed one guard).
   So a sixth plant, **4b, the open-claim filter removed** (marker kept) → **C6 red**: `assert [AgentFault(…
   ValueError: property 'outcome' cannot be overwritten)] == []`: the later run's pass tried to settle the claim
   again, and the append-only graph refused it. C6 was strengthened to assert "no fault" for this (before, the graph's
   refusal was invisible to it). Restored.
5. **Climatology re-estimated from the ledger** (`CLIMATOLOGY` replaced by the ledger's own realised shares in
   `ledger_scores`) → **C7 red**: `FAILED test_the_scorecard_reports_the_ledger_as_exp018_scores_it` — `assert
   0.6200000000000001 == np.float64(0.621994)`; 1 failed, 5 passed. Restored.

**Module line counts** (all < 200; `wc -l` on the final tree): `agent.py` **166** (was 164), `poll.py` **151** (not
touched), `entrypoint.py` 65, `work.py` 67, `settlement_pass.py` 139, `settling_bars.py` 59, `settlement_store.py` 93,
`barrier_scorecard.py` 66, `domain/barrier_settlement.py` 138, `domain/barrier_skill.py` 87, `contracts/forecaster.py` 153
(was 133), `orchestration/local_pipeline.py` **198** (was 190; the stage binds the forecaster's sink once so it fits),
`scripts/barrier_ledger.py` 125; tests: `settlement_paths.py` 85, `settlement_helpers.py` 121, `ledger_fixture.py` 82,
`test_barrier_settlement.py` 175, `test_barrier_settlement_record.py` 193, `test_barrier_settlement_faults.py` 93,
`test_barrier_settlement_loop.py` 139, `test_barrier_scorecard.py` 62, `test_barrier_scorecard_oracle.py` 122,
`test_forecaster_boundary.py` 54, `test_forecaster_entrypoint.py` 123,
`orchestration/tests/test_forecaster_settlement_stage.py` 57, `orchestration/tests/test_graph_pull_e2e.py` 158,
`orchestration/tests/test_drop_sweep_cascade.py` 122, `tests/test_barrier_ledger.py` 131. Split while building to stay
under the block: the pass's read side into `settling_bars.py`, the scorecard tests into two files and a fixture, the
test helpers into paths and graph seeding.

**`make ci`:** `UV_FROZEN=1 make ci > <session scratchpad>/ci-2.txt 2>&1; echo $?` → **exit 0**, on the final code tree in
this container (00:01–00:05 UTC 2026-09-29), every step of the `ci:` target: ruff check clean; `ruff format --check` 1,455
files formatted; mypy `no issues found in 1098 source files`; import-linter `5 kept, 0 broken`; module size (warnings
only); module header; law coverage; PARAM/settings sync; sprint status; markdown links; version scheme; pytest **3,592
passed, 7 skipped**, coverage **100.00 %**; dependency audit `No unaccepted vulnerabilities; 1 accepted advisory
re-checked`; detect-secrets `Passed` over all files; untracked scan `scanning 19 new file(s)` `Passed`. 🪤 **The first run
(`ci-1.txt`) exited 2 and is not hidden:** it straddled 00:00 UTC. `agents/provider/tests/test_barrier_history.py::test_only_buys_with_both_barriers_get_a_history_from_one_fetch`
failed (`TODAY` in `barrier_history_helpers.py` is fixed at import, 2026-09-28, the window was built after midnight,
2026-09-29), and coverage read 99.99 % (`agents/scanner/domain/beta.py:35` missed: `test_scanner_beta.py`'s module-level
`_ONE_X` bars carry the 09-28 dates and its in-test flat benchmark the 09-29 ones, so they no longer align and the
zero-variance line is never reached). Neither file is touched here; both are date-at-import fixtures, and the re-run
entirely after midnight is the one above. **Final run, after every doc of this handback was written**
(`ci-3.txt`, 00:08–00:12 UTC): exit **0**, the same counts (3,592 passed, 7 skipped, 100.00 %), sprint status reading this
spec as `BUILT` and the README row agreeing. Only this paragraph changed after it; `check_sprint_status.py`,
`check_markdown_links.py` and `check_law_coverage.py` were re-run on it before the commit, each exit 0.

**`uv.lock`:** **untouched and owed** (`git diff --stat uv.lock` is empty). No dependency changed; only `pyproject.toml`'s
version moved to `0.119.00`, so the lock's `trading-agents` entry still reads `0.118.0`. A re-lock cannot run here
(`download.pytorch.org` is blocked, DL-228); the planner re-locks.

**`make gate-ran`:** *(planner: local worktree, full SHA, output)*

**Planner live checks (F1–F3):** *(planner, before merge)*

**Not met / verified failing:** nothing in the builder's scope is unmet or verified failing. **Owed, not done here (by
design, none can run in this container):** `uv lock` (the version only), Windows `make ci`, `make gate-ran` from a
worktree whose `HEAD` is the pushed commit (check the printed SHA), F1–F3 before merge, the operator's full `up` (the
vocabulary moved), and F4 from about 2026-10-12. A run result read through the GitHub connector would be an observation,
never `GATE PROVEN`; none is claimed.

---

## Return notes

- **Scope held, with these moves inside it, each recorded in DL-243 or the Law reading record:** a second new label,
  `BarrierSettlementPass` (and its edge), because "mark the pass done per run" needs a marker (D1); `FORE-IDM-05` beyond
  the spec's list (C6's "`FORE-IDM`" had no clause); `FORE-OUT-03` widened by one name (C7 cites it); `FORE-IDN-02` now
  also lists `ForecasterRun` (`DRIFT-081` prescribed that for this amendment); `CAP` lists every label written and read;
  `model_id` on the settlement (the scorecard is per model); a per-claim fault boundary so one unreadable claim cannot
  block every later run's settlement. Not built: any reader outside the forecaster, a verdict, anything on held
  positions, any provider change, a backfill. `poll.py` and `orchestration/history_window.py` are untouched.
- **What I disagreed with after reading the laws:** (1) C6 cited "`FORE-IDM`" and C7 cited `FORE-OUT-03` for behaviour
  those clauses did not name; citing them as written would have narrowed a clause to fit a test (§7a), hence `IDM-05` and
  the one-name widening. (2) The DL-70 plant "pass not marked, **so a claim settles twice**" assumes the marker is the
  only guard. It is not: the open-claim filter and the append-only graph each stop a second settlement. The plant still
  turns C6 red (the run stays pending); plant 4b removes the filter and shows the graph refusing. (3) The spec calls the
  thresholds "constants, not tunables" and also lists `PARAM` in the law cycle: there is no new setting, so no `PARAM` row
  (`check_param_law_sync.py` fails a row that names no settings field); the Changelog says so.
- **What the exit experiment should know about the ledger:**
  1. **The live outcomes are on raw bars, EXP-018's on split- and dividend-adjusted ones.** Splits are voided, but
     dividends are not: an ex-dividend date inside the ten sessions is a raw price drop of the dividend's size, which can
     tip a stop at the margin. Expect realised stop-first shares a little above EXP-018's definition for the same prices;
     compare with the 0.287 / 0.477 / 0.236 climatology knowing the outcome is defined on a slightly different series.
  2. **The climatology is fixed and historical** (EXP-018's primary set, 2019–2026). A market regime that moves the
     realised shares moves `skill` without the model changing; read `realised_*` beside `skill`.
  3. **Voids are outside the Brier.** The scorecard reports `void` beside `settled`; a verdict should read the void rate
     (a corporate action, or a ticker that left the universe) as well as the skill of what settled.
  4. **The interval needs dates.** It resamples whole `as_of` dates, as EXP-018 did on 385 of them; with about 5–15
     claims per session the first intervals will be wide, and with fewer than two dates there is none.
  5. **A session is a row of the settling series**, as in EXP-018's rule: a halt with no bars stretches the window.
  6. **F2 on the replay cache:** the bars there are adjusted, so every non-void settlement should equal `outcome()`
     exactly; a `suspected_corporate_action` void there is a genuine one-day move of 40 % or more and should be counted
     apart, not as a mismatch.
  7. **Not built, from S239's F1 residue:** a count of claims whose simulated paths went non-finite (numpy overflow on
     rare paths). The claim records no such flag, so the ledger cannot count them yet.
- **Found while building, not in scope (for the planner):** two tests fix a date at import and build another in the test
  body, so a `make ci` that straddles 00:00 UTC fails
  `agents/provider/tests/test_barrier_history.py::test_only_buys_with_both_barriers_get_a_history_from_one_fetch` and
  loses coverage of `agents/scanner/domain/beta.py:35` (`test_scanner_beta.py`'s module-level `_ONE_X`). Measured here
  (`ci-1`, exit 2); not changed. The deployed forecaster now lists `AnalystRun` twice per poll (one listing per work
  kind, as the provider's loop already does); a single listing would need a per-node predicate in `poll.py` (DL-243 D1).
