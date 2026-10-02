<!-- Agent: planning | Role: sprint handover -->
# Sprint 253 — a run's snapshot counts the positions the broker opened and closed

**Phase:** Etalon-first continuous improvement (DL-19) · work-queue 106 (DRIFT-099, DRIFT-096)
**Branch:** `sprint-253-a-runs-snapshot-counts-what-the-broker-filled`
**Status:** MERGED 2026-10-02 — `0.121.02`, fast-forwarded to `4152ebd2`, tag `v0.121.02`, GATE PROVEN `4152ebd2` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (3,945 passed, 8 skipped, 100.00 %); built by a Claude cloud session on `claude/magical-archimedes-c24l8w`, merged from `sprint-253-a-runs-snapshot-counts-what-the-broker-filled` with the planner's resumed-run sentence and test; reporter laws v1.5 (26 / 43), analyst laws v1.8 (28 / 51); DRIFT-099, DRIFT-096 and DRIFT-101 `CORRECTED`; **F1 PASS** (the merged reporter over the live graph, its writes captured in memory: 12 / 3, 1 / 1, 0 / 0 and 1 / 3 opened / closed on the four measured runs, 31 exits at −146,279 cents, 129 of 129 filled fills in exactly one window); **not deployed**: the image-only retag waits for the fidelity verdict (after `sched-2026-10-07`); owed: the retag, F2
**Version:** *next available PATCH at merge*
**Effort:** M
**Decisions:** [DL-262](../design-log.md) (the planner's design: the window, the counts, the outcomes, the three keys removed) · the builder's decisions go to **DL-263**, reserved for this sprint · DRIFT-099 and DRIFT-096 (both closed here) · **DRIFT-101**, reserved for `RPT-NEV-03` against the code

> **Why this bump kind.** No new capability: `RPT-OUT-01` and `RPT-OUT-02` already promise a run's
> book metrics, and the code reports zero on every run because it reads the wrong place. A fix, so PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED.** This sprint amends the clauses named below and no others. Any other clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the one law-adjacent file you may append to |

Binding sections here: the reporter's **OUT**, **NEV**, **IDM** and **ORD**; the analyst's **IN**,
**OUT** and **FAIL** (for the wording amendment only).

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** The planner's answer is Yes, and names what is owed.
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**The planner's answer: Yes.** No `contracts/` file changes (`portfolio_metrics` stays
`dict[str, float]`). The reporter's guarantee about what those numbers mean changes, and the analyst's
book gains a statement it did not make. Owed, in this sprint:

| Book | Clause | Amendment |
| --- | --- | --- |
| reporter (v1.4 → **v1.5**) | `RPT-OUT-02` | Rewritten to what the code will do: which keys, over which fills, in which window (design decisions 1–5). It no longer says "derived from `CloseDecision.pnl_cents`" |
| reporter | **`RPT-IDM-04`, new** | No `Fill` whose `broker_status_refreshed_at` is after `PMRun.created_at` is counted, and the window's start is another `PMRun`'s `created_at`, never the reporter's own earlier output (`RPT-ORD-01`); so re-reporting an old run reproduces its book metrics |
| reporter | `RPT-IN-01` | It lists "PMRun, Fills, CloseDecisions, and Recommendations" as what a report aggregates. Say what is read after this sprint |
| reporter | `RPT-NEV-03` | It says an undefined metric is *"reported as 0 / 0.0"*. `agents/reporter/domain/trade_outcomes.py` omits `profit_factor` and `expectancy_cents` when no exit carries P&L, and its docstring says why. **Read the clause against the code and its test, amend the clause to what is true, and file the difference as DRIFT-101, CORRECTED here.** Do not change which of the two the code does |
| analyst (v1.7 → **v1.8**) | builder's choice of clause, or a new one in the family it belongs to | DRIFT-096, ruled **A** in S251's table (row 096): state what the code does with a candidate whose bars cover fewer sessions than `required_history_bars`. It is scored; each indicator that lacks history is absent and visible as a `*_missing_bars` metric; only fewer than `min_history_bars` rejects (`insufficient_market_history`). Cite an existing analyst test of that path. **No analyst code changes** |

Each amended or new clause gets a Changelog line in its book, a `test-plan.md` row, the clause ID in
the proving test's docstring, and the rollups in **both** `docs/laws/ledger.md` and
`docs/laws/INDEX.md` (let `make ci` tell you the numbers). DRIFT-099 and DRIFT-096 become `CORRECTED`.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/reporter/result.py` (154), `agents/reporter/domain/metrics.py` (104), `agents/reporter/domain/trade_outcomes.py` (54), `agents/reporter/domain/lineage.py` (**179**), `agents/reporter/snapshot_result.py` (49) | `agents/reporter/laws/laws.md` + `test-plan.md` | `RPT-OUT-01`, `RPT-OUT-02`, `RPT-NEV-01..03`, `RPT-IDM-01`, `RPT-IDM-03`, `RPT-ORD-01`, `RPT-FAIL-01`, `RPT-FAIL-04` |
| `agents/reporter/performance_inputs.py` (146) — read; reuse its snapshot selection for decision 3 | same | `RPT-OUT-07`, `RPT-IDM-03` |
| `contracts/broker_lifecycle.py` — **read, do not change** | — | `FILLED_BROKER_STATUSES`, `is_resting_stop_fill` |
| `orchestration/daily_brief_fills.py` — **read, do not import** (an agent imports nothing from `orchestration`) | `orchestration/laws/` dispatcher book | The brief's rule this sprint adopts: a fill's time is `broker_status_refreshed_at` |
| `agents/analyst/laws/laws.md`, `agents/analyst/laws/test-plan.md`, one analyst test's docstring | `agents/analyst/laws/laws.md` + `test-plan.md`; `agents/analyst/domain/technical_rules.py` and `scoring.py` (read) | DRIFT-096 |

⚠️ **The reporter synthesises; it never decides (`RPT-IDN-01`, `RPT-NEV-01`, `RPT-NEV-02`).** It reads
`Fill` and `PMRun` nodes other agents wrote and writes only its own `Snapshot`. If your design needs
to write, mark or correct any other label, stop and report.

---

## Goal

At merge, a run's `Snapshot` says how many positions the broker opened and closed since the previous
run, how many of the closes were stops, how many names the book holds, and the profit factor and
expectancy of every exit since the performance inception. Three keys that describe the run's own
orders, and can only read zero when the snapshot is written, are gone. The analyst's book says what
happens to a candidate with short history.

## Why (context)

`sched-2026-10-01`'s snapshot read *"0 positions opened; 0 closed"* on a day one buy filled and three
stops fired. It is not that run: no snapshot has ever counted one. The reporter reads only its own PM
run's lineage, and writes minutes after that run's orders are submitted for the next open, so nothing
in the lineage has filled; exits are resting broker stops, which belong to no PM run's lineage. The
daily brief (which reads fills by time) and the benchmark figures (which read equity) are right, so
the operator's daily numbers are right. The snapshot's counts, the trace's `[reporter]` line and the
observatory view are not.

### Measured, 2026-10-02 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Snapshots that ever counted a position | **0 of 86** have `positions_opened`, `positions_closed` or `execution_count` above zero | *[measured 2026-10-02]* every `Snapshot`'s `metrics.portfolio` on Neon |
| Snapshots carrying `profit_factor` | 15, the last for a run of 2026-07-24; 0 of 27 since 09-01 | *[measured]* same read |
| `CloseDecision` nodes | 7, dated 2026-07-20 to 07-24. The monitor has written none since | *[measured]* |
| `Fill` nodes | 329 (0.35 MB whole): 129 with `broker_status` `filled`, 153 `rejected`, 47 with none | *[measured]* |
| The 129 filled | 85 buys, 31 resting-stop sells, 13 other sells | *[measured]* `contracts.broker_lifecycle.is_resting_stop_fill` |
| Fill time | all 129 carry a readable `broker_status_refreshed_at` | *[measured]* |
| The window partitions the record | placed by that time into (previous `PMRun.created_at`, this `PMRun.created_at`], each of the 129 falls in exactly one run's window, none after the last run | *[measured]* over the 82 `PMRun`s that carry `created_at` (4 old ones do not) |
| The last four runs under that window | `sched-2026-09-29`: opened 12, closed 3 (3 stops). `sched-2026-09-30`: 1 and 1 (1). `verify-2026-10-01-s248-a`: 0 and 0. `sched-2026-10-01`: 1 and 3 (3): TGT bought; JNJ, C, DE stopped | *[measured]* |
| Exits since the inception (`performance_inception`, 2026-08-10) | **31**, all stops, all losses: realised **−146,279 cents**, profit factor **0.0**, expectancy **−4,718.68 cents** | *[measured]* integer `realized_pnl_cents` on filled sell `Fill`s (43 of 44 carry one; 1 has none) |
| Who reads the keys | `positions_opened` and `positions_closed`: the headline, `orchestration/batch_trace.py`, `orchestration/packs/trading_observatory_views.py`. `profit_factor` and `expectancy_cents`: `batch_trace.py`. `approval_rate`: `agents/execution/domain/stage_gate.py`. `positions_held`, `execution_count`, `approval_execution_gap`, `dropped_decision_count`: **nothing** outside the reporter and its tests | *[measured]* `git grep` over every tracked non-markdown file |
| What one report would list | `Fill` 0.35 MB and `PMRun` 0.86 MB, once per run, only when a `MonitorRun` is pending | *[measured]* label sizes; the reporter's poll is already key-and-edge (S242) |

---

## Scope — and what is deliberately NOT here

1. **The book counts come from the broker's fills in the run's window** (decisions 1 and 2), not
   from the PM run's lineage. **The failing test first**, on the fixture below.
2. **`positions_held`** is the number of holdings in the run's own as-of position snapshot (decision 3).
3. **The trade outcomes are cumulative since the inception** (decision 4).
4. **Three keys are removed** (decision 5): `execution_count`, `approval_execution_gap`,
   `dropped_decision_count`.
5. **The reporter's law cycle**: `RPT-OUT-02`, `RPT-IN-01`, `RPT-NEV-03`, new `RPT-IDM-04`, v1.5.
6. **The analyst's wording** (DRIFT-096): one clause, one test-plan row, one docstring citation, v1.8.

**The fixture (build it synthetic, from these numbers; it is `sched-2026-10-01`):** a previous
`PMRun` created `2026-10-01T03:57:58Z` and the reported one created `2026-10-01T22:40:17Z`. Four
`Fill`s with `broker_status` `filled` and `broker_status_refreshed_at` between
`2026-10-01T22:30:51Z` and `22:30:53Z`: a buy of 6 TGT at 15,727 cents; resting-stop sells of 3 JNJ
(`realized_pnl_cents` −2,892), 7 C (−4,627) and 1 DE (−3,186). Four buy `Fill`s of the reported run
itself (JNJ, C, EMR, DE) with no `broker_status`, submitted `22:51Z`. One older stop fill refreshed
`2026-09-30T22:30:50Z` (−3,824) inside the previous window, and one sell refreshed before
`2026-08-10` with a `realized_pnl_cents`, which no outcome may count. Expected: opened **1**, closed
**3**, `close_trigger_stop` **3**; outcomes over the four stops since the inception:
`closed_trades_with_pnl` **4**, `profit_factor` **0.0**, `expectancy_cents` **−3,632.25**; headline
*"1 positions opened; 3 closed; …"*.

### Out of scope (do NOT build this sprint)

- **The headline's wording**, beyond its numbers becoming true. No new sentence, no grammar fix.
- **`close_trigger_target` and `close_trigger_time`.** They still come from the lineage's
  `CloseDecision`s and stay 0 until an exit other than the stop exists (work-queue 92).
- **`approved_count`, `rejected_count`, `approval_rate`.** They describe the PM run and are right.
- **`performance_metrics`** and everything `RPT-OUT-07` governs.
- **The daily brief**, `batch_trace.py` and the observatory view: they read the keys that stay.
- **Any analyst code.** DRIFT-096 is wording: `laws.md`, `test-plan.md`, one docstring.
- **`agents/forecaster/`, `agents/deliberator/`, `agents/execution/`, `agents/monitor/`,
  `tests/test_poll_payloads.py`, `tests/poll_payload_fixtures.py`.** A parallel sprint (S252, Codex)
  is building there.
- **`contracts/`, `kernel/`.** No new label, edge, property, env key or tunable.

### The road not taken (LAW-06)

- **Re-report a run after its orders resolve**, so the lineage has fills. Rejected: `RPT-STA-02` makes
  a `Snapshot` append-only, the stops still belong to no lineage, and the count would arrive a day late.
- **Start the window at the reporter's previous `Snapshot`.** Rejected: `RPT-ORD-01` forbids depending
  on the reporter's own earlier output, and a `Snapshot` carries no time.
- **Import the brief's `fills_between`.** Rejected: an agent imports nothing from `orchestration`.
  The rule is two lines over helpers `contracts/` already holds.
- **Re-point `execution_count` and `approval_execution_gap` at the previous run**, whose orders have
  resolved by now. A fair metric, and a new one: not this fix. Named for a later sprint.
- **Keep the three keys and document that they read zero.** Rejected: a number that cannot be anything
  else misleads the first reader who does not open the law book (work-queue 56's lesson).

---

## The design decisions this sprint has to make

The planner decided these from the measurements above; they are recorded as
[DL-262](../design-log.md). **Record what you decide while building, with rejected alternatives, as
DL-263 BEFORE implementing.**

1. **The window.** A filled `Fill` (`broker_status` in `FILLED_BROKER_STATUSES`) belongs to the run
   whose window holds its `broker_status_refreshed_at`: after the previous `PMRun`'s `created_at`, up
   to and including the reported `PMRun`'s `created_at`. "Previous" is the `PMRun` with the latest
   `created_at` strictly before the reported one's. The first run's window has no start. A `PMRun`
   with no `created_at` is never a boundary; if the **reported** run has none, the book counts are
   undefined: follow `RPT-NEV-03` as you amend it, and say what you did.
2. **The counts.** `positions_opened`: buy fills in the window. `positions_closed`: sell fills in the
   window. `close_trigger_stop`: of those, the ones `is_resting_stop_fill` accepts.
3. **`positions_held`.** The number of holdings in the latest fresh `BrokerPositionSnapshot` created
   at or before `PMRun.created_at`, the same point `RPT-OUT-07` reads for the as-of date. Reuse that
   selection; do not write a second one. No such snapshot: the key is absent.
4. **The outcomes.** `closed_trades_with_pnl`, `profit_factor` and `expectancy_cents` over every
   filled sell `Fill` carrying an integer `realized_pnl_cents`, refreshed from 00:00 UTC of
   `performance_inception` up to and including `PMRun.created_at`. The existing exclusions of
   `trade_outcomes._pnl_cents` stand (a dropped, unfilled or invalidated fill carries no outcome).
   No exit in that span: the keys behave as they do today.
5. **Three keys removed**: `execution_count`, `approval_execution_gap`, `dropped_decision_count`.
   They describe the run's own orders, which cannot have filled when the snapshot is written, and
   nothing reads them. Remove the keys, their reducers and their tests' assertions; name every test
   you edit.
6. **Left to you:** how the window and the two listings are shaped so `result.py` (154) and
   `domain/lineage.py` (**179**) stay under 200 (a new module is expected); and which analyst clause
   takes DRIFT-096's sentence.

🪤 **DL-263 is yours; DL-261 belongs to the parallel sprint and DL-262 is the planner's.** Re-check
the top of `docs/design-log.md` before writing; entries are prepended.

---

## Blast radius — measured 2026-10-02

| What | Detail |
| --- | --- |
| Files changed | `agents/reporter/result.py` 154, `domain/metrics.py` 104, `domain/trade_outcomes.py` 54, `domain/lineage.py` **179**, a new reporter module for the window; reporter tests (five files name the keys); `orchestration/tests/daily_brief_fixtures.py` and `orchestration/tests/test_p4_celery_parity.py` name `positions_opened` / `positions_closed` (read them; change only what the new meaning breaks); reporter and analyst `laws.md` + `test-plan.md`; one analyst test docstring; `docs/laws/ledger.md`, `INDEX.md`, `drift-register.md`; `docs/design-log.md` |
| Agents affected | reporter (behaviour), analyst (wording only). Neither imports another |
| Contract change? | No. `contracts/` is not touched |
| Graph vocabulary change? | No label, property or edge. `Snapshot.metrics` is a blob: three keys leave it, the meaning of five changes. Check `orchestration/packs/trading_graph_vocabulary.json` does not enumerate them, and say what you found |
| New env keys / tunables | None (`performance_inception` exists) |
| Deploy implication | **Image-only retag**, the planner's, and **not before the fidelity verdict** (after `sched-2026-10-07`, [DL-237](../design-log.md) amendment of 2026-10-02): the analyst's law files sit under a path the fidelity check counts as decision code |
| Rollback | Retag to the tag running before the deploy. **Not undone by a retag:** the `Snapshot`s written meanwhile keep the new meaning (append-only, `RPT-STA-02`); nothing else in the graph, at the broker or in infra changes |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record your design decisions** in `docs/design-log.md` as DL-263.
3. **Plant the failing tests first** (A1, A5) and watch them fail. Paste the red output.
4. **Implement.**
5. **Law cycle**: reporter v1.5 (`RPT-OUT-02`, `RPT-IN-01`, `RPT-NEV-03`, new `RPT-IDM-04`), analyst
   v1.8 (DRIFT-096), test-plan rows, docstring citations, both rollups, DRIFT-099 and DRIFT-096
   `CORRECTED`, DRIFT-101 filed and `CORRECTED`.
6. **Prove the guards can fail (DL-70)**: the four plants below, each red, pasted, restored.
7. **`make ci` green**, every step of the `ci:` target, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file, and set this spec and its README row to `BUILT`.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 The fixture above | as described | opened 1, closed 3, stops 3; the headline's numbers; the run's own four unfilled buys count for nothing |
| A2 | 🪤 A fill belongs to one window | the fixture plus the run before it | the older stop is counted by the previous run's report and not by this one; a fill refreshed exactly at a `PMRun.created_at` belongs to that run |
| A3 | 🪤 Re-reporting an old run | the fixture, then a later run and later fills added | the old run's book metrics are unchanged (`RPT-IDM-04`, `RPT-IDM-01`) |
| A4 | The first run, and a run with no `created_at` | no earlier `PMRun`; then a reported `PMRun` without `created_at` | the first run's window is open at the start; the second follows the amended `RPT-NEV-03`, and never raises |
| A5 | 🎯 Outcomes since the inception | the fixture | 4 exits, profit factor 0.0, expectancy −3,632.25; the pre-inception sell is not counted; add one winning exit and the profit factor is wins / losses |
| A6 | 🪤 No exit since the inception | fills, none of them an exit with P&L | the keys behave exactly as today (state which: `RPT-NEV-03` as amended) |
| A7 | `positions_held` | a fresh snapshot of 32 holdings before the run, a later one after it, a stale one | 32; the later and the stale one are not read; no snapshot, no key |
| A8 | 🪤 The removed keys | any snapshot | `execution_count`, `approval_execution_gap` and `dropped_decision_count` are absent from the returned metrics and the written blob |
| A9 | The readers still read | `orchestration/batch_trace.py` and the observatory view over a new snapshot | both print the new numbers; nothing raises on a missing key |
| A10 | DRIFT-096 | the existing analyst test of a short-history candidate | its docstring cites the amended clause; no analyst code changed (`git diff --stat` shows `laws/` and one test file only under `agents/analyst/`) |

**DL-70 plants (each must go red, paste, restore):** (1) the counts read the lineage again, A1 red;
(2) the window's upper bound dropped, A3 red; (3) the inception bound dropped, A5 red; (4) the window's
lower bound made inclusive, A2 red.

---

## Success factors

- [ ] On the fixture the snapshot reads opened 1, closed 3, stops 3 and the outcomes above (A1, A5).
- [ ] Every filled fill belongs to exactly one run's window, and an old run re-reports identically (A2, A3).
- [ ] `positions_held` is the as-of snapshot's holdings (A7); the three keys are gone (A8); the readers work (A9).
- [ ] No file under `contracts/`, `kernel/`, or the forecaster, deliberator, execution or monitor agents changed; no analyst code changed.
- [ ] Law cycle done as named; DRIFT-099, DRIFT-096 and DRIFT-101 `CORRECTED`.
- [ ] DL-263 written with the decisions and their rejected alternatives.
- [ ] Each of the four plants red, pasted, restored.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.
- [ ] **Owed to the planner, not the builder:** the PATCH bump and `uv lock`, Windows `make ci`,
      `make gate-ran`, the CodeQL diff, **F1** (before merge, read-only on Neon: the merged reporter
      over a copy of the live graph gives 12 / 3, 1 / 1, 0 / 0 and 1 / 3 for the four runs measured
      above, 31 exits at −146,279 cents for `sched-2026-10-01`, and places each of the 129 filled
      fills in one window), the retag after the fidelity verdict, and **F2** (the first scheduled
      run after it: the snapshot's headline agrees with that run's daily brief *Filled* line).

---

## Traps

🪤 **`submitted_at` is not a fill time.** It dates a resting stop's placement and is absent on stop
fills. The time is `broker_status_refreshed_at` (the brief's rule, S234 row 12).
🪤 **`status` is not the broker's status.** A `Fill` keeps `status: pending` by design after it
fills; the truth is `broker_status`. Every filled fill on the live graph reads `pending`.
🪤 **The run's own orders are in the lineage and unfilled.** A test that seeds them as `filled` proves
the old code right. The fixture's four own buys carry no `broker_status`.
🪤 **A test run splits a day's window.** `verify-2026-10-01-s248-a` sits between two scheduled runs
and its window is empty. That is correct: a fill is counted once, by the run that first saw it.
🪤 **Profit factor 0.0 is a real value here** (no wins, some losses), not a missing one. Do not let
the "undefined" path of `RPT-NEV-03` swallow it.
🪤 **`RPT-IDM-03` is about performance.** Do not stretch it; the book metrics get their own clause.

---

## Guardrails (every sprint)

- No agent imports another agent; an agent imports nothing from `orchestration` (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `agents/reporter/domain/lineage.py` **179**, `agents/reporter/result.py` **154**,
  `agents/reporter/performance_inputs.py` **146**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: the inception is `ReporterSettings.performance_inception`.
- Faults, not silent failure — `kernel.fault_boundary`; a failure in the new reading is contained
  like `RPT-FAIL-04`'s, never a crash.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- PATCH bump and `uv.lock` are the planner's: leave `pyproject.toml`'s version and `uv.lock` untouched.
- No `.env` in a cloud session: every proof here is a unit test. **State which tree you ran in.**

---

## Sequencing after merge

1. Planner: PATCH bump and `uv lock`, Windows `make ci`, push, **`make gate-ran` exits 0** from the
   worktree at the branch's `HEAD` (the printed SHA checked against `git rev-parse HEAD`), the
   branch's open CodeQL alerts diffed against `sprint-251-every-open-drift-row-is-decided` (131).
2. **F1** on Neon, read-only, before the merge. Whichever of S252 and S253 returns second is rebased:
   they share only docs (design log, drift register, ledger, README, INDEX).
3. Merge to `main`, tag, post-merge CodeQL.
4. **Deploy: image-only retag, after the fidelity verdict** (not before `sched-2026-10-07` has run).
   Rollback: the tag running before it.
5. **F2** on the first scheduled run after the retag.

---

## Handover — paste this to the Claude cloud session

```text
Sprint 253 — a run's snapshot counts the positions the broker opened and closed. Spec:
docs/sprints/sprint-253-a-runs-snapshot-counts-what-the-broker-filled.md on main (read ALL of it,
then CLAUDE.md). Repo: yury-gurevich/trading-agents.

Branch: sprint-253-a-runs-snapshot-counts-what-the-broker-filled, cut from main. Never main. If your
session forces another branch name, use it and name it in the handback.
You have NO .env, NO gh, NO Azure and no route to download.pytorch.org. Every proof is a unit test.
You cannot run `make gate-ran`: it is owed to the planner. Leave pyproject.toml's version and uv.lock
untouched and say so; the planner bumps and re-locks.

This handover is complete: nobody will send you follow-up messages. If something in the spec is wrong
or blocked, record it in the handback (Return notes, "not done") and stop; do not wait.

What and why: sched-2026-10-01's snapshot read "0 positions opened; 0 closed" on a day one buy filled
and three stops fired, and 0 of 86 snapshots have ever counted a position. The reporter reads only its
own PM run's lineage, minutes after that run's orders are submitted for the next open; exits are
resting broker stops in no run's lineage. The daily brief and the benchmark figures are right. This is
DRIFT-099. DRIFT-096 (analyst wording, already ruled) rides along.

MUST RULE before any code: read, whole, laws.md and test-plan.md of reporter and analyst;
docs/laws/conventions.md; docs/laws/drift-register.md; contracts/broker_lifecycle.py;
orchestration/daily_brief_fills.py (read, never import). Fill the Law reading record first. Law-cycle
answer: YES, and exactly this is owed: reporter v1.5 (RPT-OUT-02 rewritten, RPT-IN-01, RPT-NEV-03
amended to what the code does about an undefined metric with DRIFT-101 filed, new RPT-IDM-04);
analyst v1.8 (DRIFT-096: a candidate under required_history_bars is scored, each indicator lacking
history is absent and visible as a *_missing_bars metric, only fewer than min_history_bars rejects;
cite an existing test; NO analyst code change); a Changelog line, test-plan row and docstring citation
per clause; both rollups; DRIFT-099 and DRIFT-096 CORRECTED. Edit no other clause.

Build (the spec's decisions 1-6, recorded as DL-262):
1. Window: a Fill with broker_status in FILLED_BROKER_STATUSES belongs to the run whose window holds
   its broker_status_refreshed_at: after the previous PMRun's created_at (the latest strictly before
   the reported one's), up to and including the reported PMRun's created_at.
2. positions_opened = buy fills in the window; positions_closed = sell fills in the window;
   close_trigger_stop = those is_resting_stop_fill accepts.
3. positions_held = holdings in the latest fresh BrokerPositionSnapshot at or before
   PMRun.created_at; reuse the selection RPT-OUT-07 already makes; absent when there is none.
4. closed_trades_with_pnl, profit_factor, expectancy_cents over every filled sell Fill with an
   integer realized_pnl_cents refreshed from 00:00 UTC of performance_inception up to
   PMRun.created_at; _pnl_cents's exclusions stand.
5. Remove execution_count, approval_execution_gap, dropped_decision_count (nothing reads them).
6. Keep every module under 200: domain/lineage.py is at 179, result.py at 154. A new module is expected.

Order: DL-263 (your decisions, with rejected alternatives) -> red tests A1, A5 on the spec's fixture
(paste) -> implement -> law cycle -> the four DL-70 plants (counts read the lineage again; the
window's upper bound dropped; the inception bound dropped; the lower bound made inclusive: each must
go red, paste, restore) -> make ci redirected to a file, exit 0, 100.00 %.

DO NOT:
- touch contracts/, kernel/, agents/forecaster, deliberator, execution, monitor, or
  tests/test_poll_payloads.py and tests/poll_payload_fixtures.py (S252 is building there).
- change any analyst code, or any analyst clause but the one DRIFT-096 needs.
- import orchestration from an agent.
- change the headline's wording, performance_metrics, approved_count, rejected_count, approval_rate,
  close_trigger_target or close_trigger_time.
- read submitted_at as a fill time, or status as the broker's status.
- write, mark or correct any label but Snapshot.
- add a label, edge, property, env key or tunable.
- grow any module past 200; # noqa to bypass a rule.
- let any test reach the network.
- claim a live proof or GATE PROVEN: F1, F2 and the gate are the planner's.
- touch pyproject.toml's version or uv.lock.

Handback — the planner returns it if ANY of these is missing:
[ ] Law reading record filled, with the law-cycle answer and any contradiction or silence found.
[ ] Test plan results: A1-A10, each with final test name, file, PASS, clause IDs cited.
[ ] Every existing test you edited, listed, with the reason.
[ ] Closeout: the red run pasted before the change; the green run after.
[ ] Each of the four DL-70 plants: what was planted, its red output, restored.
[ ] Module line counts for every file touched (all < 200).
[ ] make ci: the file it was redirected to, exit code, passed/skipped, coverage 100.00 %, dependency
    audit, detect-secrets.
[ ] The clauses as amended (RPT-OUT-02, RPT-IN-01, RPT-NEV-03, RPT-IDM-04, the analyst clause), two
    Changelog lines, test-plan rows, both rollups, DRIFT-099 / 096 / 101 CORRECTED.
[ ] What RPT-NEV-03 said, what the code does, and which way you amended it.
[ ] Whether the vocabulary pack enumerates Snapshot's metric keys.
[ ] DL-263 written.
[ ] Statement that pyproject.toml's version and uv.lock are untouched, and that no analyst code changed.
[ ] Return notes: scope held or moved; what you disagreed with after reading the laws.
[ ] Status: BUILT on the spec, and this sprint's README.md row leads with BUILT, in the same commit.
[ ] Owed items named: bump and uv lock, make gate-ran, Windows make ci, F1, the retag, F2.
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
| `agents/reporter/result.py`, `domain/metrics.py`, `domain/trade_outcomes.py`, `snapshot_result.py`, new `domain/book_window.py` + `book_inputs.py` | `agents/reporter/laws/laws.md` (v1.4, whole) + `test-plan.md` (whole); `docs/laws/conventions.md`; `docs/laws/drift-register.md` (header, reporter, analyst, system rows) | `RPT-IDN-01`, `RPT-IN-01`, `RPT-OUT-01`, `RPT-OUT-02`, `RPT-OUT-06`, `RPT-NEV-01..03`, `RPT-STA-02`, `RPT-IDM-01`, `RPT-IDM-03`, `RPT-ORD-01`, `RPT-FAIL-01`, `RPT-FAIL-04`, `RPT-TYP-02`, `RPT-CAP` (`Fill`, `PMRun`, `BrokerPositionSnapshot` are already in `labels_read`) | Yes, twice. (1) `RPT-NEV-03` says undefined metrics read "0 / 0.0", the code omits the two ratios, and the degraded snapshot reports its counts as 0.0: the clause is amended to all three, and a reported run with no `created_at` follows the omission rule, so its headline prints `?` where a count stands rather than a 0 that cannot be true. (2) `RPT-IDN-01` and `RPT-TYP-02` are 🟩 on `test_dropped_decision_is_visible_but_not_rejected`, which asserts `dropped_decision_count`: removing the key means that test is edited and renamed, and both rows re-pointed |
| `agents/reporter/performance_inputs.py` (reused for `positions_held`) | same | `RPT-OUT-07`, `RPT-IDM-03`, `RPT-FAIL-04` | Yes: the selection is shared by returning the chosen snapshot nodes; a performance fault therefore also leaves `positions_held` absent, which is the containment `RPT-FAIL-04` already allows |
| `contracts/broker_lifecycle.py` (read, unchanged) | — | — | `FILLED_BROKER_STATUSES` is `{"filled"}` only (a `partial` is not counted); `is_resting_stop_fill` keys on `stop_order_key` |
| `orchestration/daily_brief_fills.py` (read, not imported) | — | — | Adopted its two rules: time is `broker_status_refreshed_at`; a fill whose time cannot be read is in no window. Its status read is lower-cased `broker_status` only, never `status` |
| `agents/analyst/laws/laws.md`, `test-plan.md`, `tests/test_analyst_domain.py` | `agents/analyst/laws/laws.md` (v1.7, whole) + `test-plan.md` (whole); `domain/scoring.py`, `domain/technical_rules.py`, `history_requirements.py` (read) | `ANLZ-IN-01..04`, `ANLZ-OUT-01`, `ANLZ-OUT-03`, `ANLZ-FAIL-03`, PARAM `min_history_bars`, `lookback_days` | Yes: `*_missing_bars` is recorded for the **five core indicators** `required_history_bars` is the maximum of (RSI, MACD, Bollinger, SMA-200 distance, EMA crossover), not for every indicator; a short golden cross, OBV or pattern is simply absent and only `indicators_available` shows it. The clause says exactly that (new `ANLZ-IN-05`) |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **Yes**, as the
planner answered. No `contracts/` file changes (`portfolio_metrics` stays `dict[str, float]`). The
reporter's guarantee about what the book numbers mean changes (`RPT-OUT-02`, `RPT-IN-01`,
`RPT-NEV-03`) and it gains one (`RPT-IDM-04`): reporter v1.4 → v1.5. The analyst's book gains a
statement it did not make (`ANLZ-IN-05`, new): v1.7 → v1.8.

**Contradictions found between a law and this spec:** none that stops the sprint. Two between the
spec's wording and the code, settled for the code (which this sprint may not change): (a) the spec
reads `RPT-NEV-03` as "the code omits", and the degraded snapshot (`RPT-OUT-06`) still writes its
counts as 0.0 with a headline that says why; the amended clause states both. (b) The spec's DRIFT-096
sentence ("each indicator that lacks history is … visible as a `*_missing_bars` metric") is true only
of the five core indicators; the clause names them.

**Laws found silent where a decision was needed:** (1) `RPT-NEV-03` was silent on a book count that
cannot be computed (no `created_at` on the reported run): decided as omission, DL-263 D3, closed by the
amended clause (DRIFT-101). (2) No clause says whether the `RPT-OUT-07` selection's inception bound
applies to `positions_held`: it does, because the selection is reused, not copied (DL-263 D4). (3) A
resumed `PMRun` (`linked_from_key`) has its own `created_at`; the window uses the **reported**
`PMRun`'s, as `RPT-IDM-03` does (DL-263 D2). No drift row filed for (2) or (3): the amended
`RPT-OUT-02` states both.

**Clauses that were ⬜ and are now proven:** none was ⬜ and is now 🟩. New and proven: `RPT-IDM-04`
and `ANLZ-IN-05`. `RPT-IDM-01` stays ⬜: A3 proves the book-metrics half only (§7a).

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_the_runs_snapshot_counts_the_fills_in_its_window` | `agents/reporter/tests/test_book_window.py` | PASS | `RPT-OUT-02`, `RPT-IN-01` |
| A2 | `test_a_fill_belongs_to_one_window` | `agents/reporter/tests/test_book_window.py` | PASS | `RPT-IDM-04`, `RPT-OUT-02` |
| A3 | `test_re_reporting_an_old_run_reproduces_its_book_metrics` | `agents/reporter/tests/test_book_window.py` | PASS | `RPT-IDM-04`, `RPT-IDM-01` (cited; the row stays ⬜, see Law reading record) |
| A4 | `test_the_first_run_has_no_window_start`; `test_a_run_without_created_at_has_no_book_counts` | `agents/reporter/tests/test_book_window.py` | PASS | `RPT-OUT-02`; `RPT-NEV-03`, `RPT-OUT-02` |
| A5 | `test_outcomes_are_cumulative_since_the_inception` | `agents/reporter/tests/test_book_window.py` | PASS | `RPT-OUT-02`, `RPT-NEV-03` |
| A6 | `test_no_exit_since_the_inception_omits_the_ratios` | `agents/reporter/tests/test_book_window_edges.py` | PASS | `RPT-NEV-03` (as amended: the ratios absent, `closed_trades_with_pnl` 0.0, exactly as before S253) |
| A7 | `test_positions_held_is_the_as_of_snapshots_holdings` | `agents/reporter/tests/test_book_window_edges.py` | PASS | `RPT-OUT-02` |
| A8 | `test_the_three_removed_keys_are_gone` | `agents/reporter/tests/test_book_window_edges.py` | PASS | `RPT-OUT-02` |
| A9 | `test_the_trace_and_the_observatory_read_the_new_snapshot`; `test_the_readers_do_not_raise_on_absent_counts` | `orchestration/tests/test_reporter_snapshot_readers.py` | PASS | `RPT-OUT-02`; `RPT-NEV-03` |
| A10 | `test_sufficient_history_scores_from_technical_composite`; `test_score_candidate_reports_insufficient_history` | `agents/analyst/tests/test_analyst_domain.py` | PASS | `ANLZ-IN-05` (both). `git diff --stat` under `agents/analyst/`: `laws/laws.md`, `laws/test-plan.md`, `tests/test_analyst_domain.py` only |

**Tests added beyond the plan:** `test_book_window_edges.py::test_a_book_read_fault_is_contained`
(`RPT-NEV-03`): a failing `Fill` listing leaves the book keys absent, records one fault with capability
`report.book`, keeps the rest of the snapshot, and the headline prints `?` (the spec's guardrail
"contained like `RPT-FAIL-04`'s"). A4 also covers the naive (UTC) and unparseable refresh times and an
unparseable `PMRun.created_at`, which is never a boundary.

**Existing tests edited, and why:**

- `agents/reporter/tests/test_metrics_narrative.py::test_metrics_collect_counts_averages_and_regime_context`
  — `collect_portfolio_metrics` now takes `(pm_run, close_decisions)`; the book counts and the stop
  trigger no longer come from it, so it asserts their absence and the target/time triggers instead.
- `::test_metrics_handle_empty_and_bad_numeric_values` — the new signature only.
- `::test_dropped_decision_is_visible_but_not_rejected`, **renamed**
  `test_the_pm_decision_counts_are_reported_as_decided` — it asserted the three removed keys. It keeps
  `RPT-IDN-01` / `RPT-NEV-01` / `RPT-TYP-02` (PM counts projected, all floats) and asserts the keys are
  gone; the `RPT-IDN-01` and `RPT-TYP-02` test-plan rows were re-pointed to the new name (rows only).
- `agents/reporter/tests/test_reporter_agent.py::test_report_and_narrative_return_payloads_and_write_graph_nodes`
  — the fixture's `PMRun` gets a `created_at` and its buy a broker fill ten minutes before it;
  `positions_closed` reads 0.0, not 1.0, because the lineage's `CloseDecision` is no broker fill.
- `::test_snapshot_reports_profit_factor_and_expectancy` (its `_seed_two_closed_trades`) — the two P&L
  fills become filled sells refreshed before the run's `created_at`; same profit factor 2.0 and
  expectancy 250.
- `::test_reporter_handles_missing_nodes_without_crashing` — docstring only: it now also cites
  `RPT-NEV-03` (the degraded snapshot's 0.0 counts and its reason), which the amended clause names.
- `agents/reporter/tests/test_p3_reporter_slice.py::test_full_p3_stop_breach_reports_held_position_and_fault`,
  `orchestration/tests/test_p4_celery_parity.py::test_p4_celery_eager_parity`,
  `orchestration/tests/test_p4_daily_loop.py::test_p4_daily_loop_on_in_process_bus` — they asserted
  `positions_opened >= 1` and `positions_held >= 1`, the lineage meaning. The paper broker writes
  `status: filled` and never `broker_status`, and these flows write no `BrokerPositionSnapshot`, so
  under the new meaning they read 0.0 / 0.0 and no `positions_held`; asserted with a comment saying why.
- `agents/analyst/tests/test_analyst_domain.py` — two docstrings cite `ANLZ-IN-05`; the 40-bar test
  gains `sma_distance_pct_missing_bars == 160.0`, and its four-line arithmetic comment moved into the
  docstring (the file was at 199 and the block is at 200).
- `orchestration/tests/daily_brief_fixtures.py` and `surfaces/tests/performance_fixtures.py` were read
  and **not** edited: they seed `positions_opened` / `positions_closed` as data, which the new meaning
  does not break.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** the claude.ai cloud container,
`/home/user/trading-agents`, branch `claude/magical-archimedes-c24l8w` cut from `main` at `ae54cf3`;
Linux, Python 3.13.14, dependencies from `uv sync --frozen`. **No `.env`.** Every proof is a unit test
on `InMemoryGraphStore`; nothing reached Neon, Azure or the broker.

**Result:** on the spec's fixture the snapshot reads opened 1, closed 3, `close_trigger_stop` 3, headline
"1 positions opened; 3 closed; …", `closed_trades_with_pnl` 4, profit factor 0.0, expectancy
−3,632.25 (A1, A5, PASS). Each fill is counted by one window and an old run re-reports identically
(A2, A3, PASS). `positions_held` is the as-of snapshot's 32 (A7), the three keys are gone (A8), both
readers print the new numbers and tolerate absence (A9). Four plants red and restored. `make ci` exit 0.
The live re-measure (F1) has **not** been run: no route to Neon from here.

**Files changed:** new `agents/reporter/domain/book_window.py`, `agents/reporter/book_inputs.py`,
`agents/reporter/tests/book_fixtures.py`, `test_book_window.py`, `test_book_window_edges.py`,
`orchestration/tests/test_reporter_snapshot_readers.py`; changed `agents/reporter/result.py`,
`domain/metrics.py`, `domain/trade_outcomes.py` (docstring), `performance_inputs.py`,
`snapshot_result.py`, the reporter and analyst tests listed above, reporter and analyst `laws.md` +
`test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md`,
`docs/design-log.md` (DL-263), this spec, `docs/sprints/README.md`. Not touched: `contracts/`,
`kernel/`, the forecaster, deliberator, execution and monitor agents, `tests/test_poll_payloads.py`,
`tests/poll_payload_fixtures.py`, any analyst code, `pyproject.toml`'s version, `uv.lock`.

**Design decisions:** [DL-263](../design-log.md) (D1–D7, with the road not taken), under the planner's
DL-262.

**Proof — the red run first** (A1 and A5 written before any reporter code changed):

```text
FF                                                                       [100%]
=================================== FAILURES ===================================
____________ test_the_runs_snapshot_counts_the_fills_in_its_window _____________
agents/reporter/tests/test_book_window.py:31: in test_the_runs_snapshot_counts_the_fills_in_its_window
    assert portfolio["positions_opened"] == 1.0
E   assert 4.0 == 1.0
_______________ test_outcomes_are_cumulative_since_the_inception _______________
agents/reporter/tests/test_book_window.py:48: in test_outcomes_are_cumulative_since_the_inception
    assert portfolio["closed_trades_with_pnl"] == 4.0
E   assert 0.0 == 4.0
=========================== short test summary info ============================
FAILED agents/reporter/tests/test_book_window.py::test_the_runs_snapshot_counts_the_fills_in_its_window
FAILED agents/reporter/tests/test_book_window.py::test_outcomes_are_cumulative_since_the_inception
2 failed in 1.26s
```

(The old code counted the run's own four unfilled lineage buys as opened, and no outcome.)

**Proof — the green run:**

```text
agents/reporter/tests/test_book_window.py::test_the_runs_snapshot_counts_the_fills_in_its_window PASSED
agents/reporter/tests/test_book_window.py::test_outcomes_are_cumulative_since_the_inception PASSED
agents/reporter/tests/test_book_window.py::test_a_fill_belongs_to_one_window PASSED
agents/reporter/tests/test_book_window.py::test_re_reporting_an_old_run_reproduces_its_book_metrics PASSED
agents/reporter/tests/test_book_window.py::test_the_first_run_has_no_window_start PASSED
agents/reporter/tests/test_book_window.py::test_a_run_without_created_at_has_no_book_counts PASSED
agents/reporter/tests/test_book_window_edges.py::test_no_exit_since_the_inception_omits_the_ratios PASSED
agents/reporter/tests/test_book_window_edges.py::test_positions_held_is_the_as_of_snapshots_holdings PASSED
agents/reporter/tests/test_book_window_edges.py::test_the_three_removed_keys_are_gone PASSED
agents/reporter/tests/test_book_window_edges.py::test_a_book_read_fault_is_contained PASSED
orchestration/tests/test_reporter_snapshot_readers.py::test_the_trace_and_the_observatory_read_the_new_snapshot PASSED
orchestration/tests/test_reporter_snapshot_readers.py::test_the_readers_do_not_raise_on_absent_counts PASSED
agents/analyst/tests/test_analyst_domain.py::test_score_candidate_reports_insufficient_history PASSED
agents/analyst/tests/test_analyst_domain.py::test_sufficient_history_scores_from_technical_composite PASSED
============================== 14 passed in 0.42s ==============================
```

**Guards planted (DL-70)** — each planted, run, red, and the file restored byte-for-byte (`cmp` against
a copy taken before planting):

1. *The counts read the lineage again* — `result.py` set `positions_opened` / `positions_closed` from
   `len(lineage.positions)` / `len(lineage.close_decisions)`. A1:
   `E   assert 4.0 == 1.0` · `FAILED …::test_the_runs_snapshot_counts_the_fills_in_its_window`.
2. *The window's upper bound dropped* — `fills_between` lost `moment <= until`. A3:
   `Differing items: {'close_trigger_stop': 4.0} != {… 3.0}`, `{'positions_opened': 2.0} != {… 1.0}`,
   `{'positions_closed': 4.0} != {… 3.0}` · `FAILED …::test_re_reporting_an_old_run_reproduces_its_book_metrics`.
   (A first version of A3 re-reported into the same graph; the plant then went red through the
   append-only `Snapshot` merge, `ValueError: property 'metrics' cannot be overwritten`, not through the
   test's assertion. A3 now builds the old report on its own graph, so the assertion carries the diff.)
3. *The inception bound dropped* — `exits_since` lost `since <=`. A5: `E   assert 5.0 == 4.0`
   (the pre-inception sell counted) · `FAILED …::test_outcomes_are_cumulative_since_the_inception`.
4. *The lower bound made inclusive* — `moment > after` became `moment >= after`. A2:
   `E   assert (2.0, 3.0, 3.0) == (1.0, 3.0, 3.0)` (the fill refreshed exactly at the previous run's
   `created_at` counted twice) · `FAILED …::test_a_fill_belongs_to_one_window`.

**Module line counts** (all < 200): `book_inputs.py` 63 (new), `domain/book_window.py` 96 (new),
`domain/metrics.py` 104 → 81, `domain/trade_outcomes.py` 54 → 55, `performance_inputs.py` 146 → 147,
`result.py` 154 → 162 (over the 150 warning), `snapshot_result.py` 49 → 55, `domain/lineage.py` 179
(unchanged); tests: `book_fixtures.py` 131, `test_book_window.py` 164, `test_book_window_edges.py` 131,
`test_metrics_narrative.py` 125 → 126, `test_p3_reporter_slice.py` 80, `test_reporter_agent.py`
171 → 191, `agents/analyst/tests/test_analyst_domain.py` 199 → 199,
`orchestration/tests/test_reporter_snapshot_readers.py` 74, `test_p4_celery_parity.py` 49,
`test_p4_daily_loop.py` 51.

**`make ci`:** `make ci > …/scratchpad/ci.txt 2>&1; echo $?` → **exit 0**, in the cloud tree above. All
15 steps ran: ruff, format, mypy (1,149 files, no issues), import-linter (5 kept, 0 broken), module size
(warnings only), module header, law coverage, PARAM sync (two pre-existing warnings), sprint status,
markdown links, version scheme, pytest **3,944 passed, 8 skipped, coverage 100.00 %** ("Required test
coverage of 100.0% reached"), dependency audit ("No unaccepted vulnerabilities; 1 accepted advisory
re-checked", PYSEC-2026-2447), detect-secrets **Passed**, untracked secrets **Passed**. Run before the
spec and README were set to BUILT; `check_sprint_status.py` and `check_markdown_links.py` were re-run
on the final docs (below).

**`make gate-ran`:** owed to the planner.

**Not met / verified failing:** nothing in the builder's scope is failing. **Not done here, by design:**
F1 and F2 (no Neon), `make gate-ran` (no `gh`), Windows `make ci`, the CodeQL diff, the PATCH bump and
`uv lock` (no route to `download.pytorch.org`; `pyproject.toml` and `uv.lock` are byte-identical to
`main`).

---

## Return notes

- **Scope held.** The six decisions were built as specced. Two placements moved within the spec's
  latitude: `positions_held` rides `PerformanceProjection` (the selection is shared, so a performance
  fault also leaves it absent) and `domain/lineage.py` is untouched (the window went to two new modules).
- **Disagreed after reading the laws, and settled for the code:** (1) `RPT-NEV-03`. **It said** an
  undefined metric is "reported as 0 / 0.0". **The code** omits `profit_factor` and `expectancy_cents`
  when no exit carries P&L (`trade_outcomes.py`, held by `test_degraded_snapshot_omits_uncomputed_outcome_keys`),
  while the degraded snapshot writes its counts as 0.0 with a headline that says why. **Amended toward
  the code**: an undefined metric is absent; the degraded snapshot's zeros are named. A reported run
  with no `created_at` follows the omission rule, so its headline prints `?` in the count slots; that
  is the only visible headline change, and only for a run without `created_at` (the spec measured 82
  of 86 `PMRun`s carrying one; 4 old ones do not). Filed as DRIFT-101, CORRECTED. (2) The spec's
  DRIFT-096 sentence says *each* indicator lacking history shows a `*_missing_bars` metric; the code
  records it for the five core indicators only. `ANLZ-IN-05` says so.
- **The vocabulary pack does not enumerate `Snapshot`'s metric keys.** `orchestration/packs/trading_graph_vocabulary.json`
  lists `Snapshot` as a label and in the edge signatures `Snapshot -SUMMARISES-> PMRun` and
  `Snapshot -LINKED_FROM-> Snapshot`; its `properties` map has no `Snapshot` entry, and no pack file
  names `positions_opened` or any removed key.
- **`RPT-IDM-01` stays ⬜.** A3 cites it, but proves only the book-metrics half of "the same
  `RunSnapshot`"; flipping it would narrow the clause (§7a).
- **Worth knowing at F1:** `write_snapshot` merges into `snapshot:<run id>`, and the in-memory store
  refuses to overwrite a different `metrics` blob (seen in plant 2). A re-report on the live graph is
  safe only because `RPT-IDM-04` makes the numbers identical; F1 should report over a copy, as the spec
  says, not write into the live graph.
- **`result.py` is at 162**, past the 150 warning; the next reporter change there should split it.
- **No analyst code changed**; `pyproject.toml`'s version and `uv.lock` are untouched.
- **Owed to the planner:** the PATCH bump and `uv lock`; Windows `make ci`; push and `make gate-ran`
  from the worktree at the branch's `HEAD` (check the printed SHA); the CodeQL diff against
  `sprint-251-every-open-drift-row-is-decided`; **F1** on Neon before the merge (12 / 3, 1 / 1, 0 / 0,
  1 / 3 for the four runs; 31 exits at −146,279 cents for `sched-2026-10-01`; each of the 129 filled
  fills in one window); the image-only retag after the fidelity verdict (not before `sched-2026-10-07`);
  **F2** on the first scheduled run after it. Whichever of S252 and S253 returns second is rebased
  (shared docs only).

---

## Planner's closeout — 2026-10-02

**Result: MERGED.** `main` was fast-forwarded to `4152ebd2`, so the merged SHA is the gated SHA; tag
`v0.121.02`. Not deployed: the retag waits for the fidelity verdict.

- **Handback:** complete against the fifteen-item checklist; no `builder fills` left. Scope held:
  nothing under `contracts/`, `kernel/`, or the forecaster, deliberator, execution and monitor agents;
  under `agents/analyst/` only the two law files and one test file.
- **Bump and lock:** `0.121.01` → `0.121.02`; `uv lock` changed one line, the project's version.
- **Windows `make ci`:** redirected to a file, exit 0: 3,945 passed, 8 skipped, coverage 100.00 %,
  dependency audit clean (one accepted advisory), detect-secrets passed.
- **`make gate-ran`:** run from the worktree at the branch's `HEAD`; `GATE PROVEN` for `4152ebd2`
  (CI, CodeQL, Security Findings, attempt 1 each), the printed SHA equal to `git rev-parse HEAD`.
- **CodeQL:** the branch's open alerts are the same 131 as on
  `sprint-251-every-open-drift-row-is-decided` (117 notes, 14 warnings), compared as sets.
- **F1 PASS**, before the merge ([functionality-checks](../laws/functionality-checks.md)). The
  branch's `build_snapshot` over the live graph, every write captured in memory:

  | Run | Opened / closed (stops) | Live snapshot said | `positions_held` | Exits since the inception |
  | --- | --- | --- | --- | --- |
  | `sched-2026-09-29` | 12 / 3 (3) | 0 / 0 | 34 | 27 |
  | `sched-2026-09-30` | 1 / 1 (1) | 0 / 0 | 34 | 28 |
  | `verify-2026-10-01-s248-a` | 0 / 0 (0) | 0 / 0 | 34 | 28 |
  | `sched-2026-10-01` | 1 / 3 (3) | 0 / 0 | 32 | 31 at −146,279 cents, profit factor 0.0, expectancy −4,718.68 |

  129 of 129 filled fills fall in exactly one run's window, none in two, none after the last run. The
  signal, regime and performance groups equal the live snapshots' on all four runs; 0 faults; 0 live
  writes. A raw recount without the branch's code gives the same 31 exits and the same 32 holdings.
- **What the planner changed at merge (`4152ebd2`).** *[measured]* A resumed run's `PMRun` is a clone
  carrying its source's `created_at` (`orchestration/resume.py` copies the props; one such pair is on
  the graph, from 2026-07-13). The handback's law reading took it to have its own. The behaviour is
  right (the clone reports its source's window and is never the start of it), and unstated:
  `RPT-IDM-04` gained the sentence, `test_book_window_edges.py::test_a_resumed_run_reports_its_sources_window`
  holds it (planted with the start made inclusive: red, restored), and DL-263 carries the note. That
  file is now 150 lines.
- **Where this spec was wrong.** (1) The DRIFT-096 sentence said every indicator short of history
  shows a `*_missing_bars` metric; that was not measured, and only the five core indicators do. The
  builder wrote the true clause (`ANLZ-IN-05`). (2) F1 names the runs by their scheduling ids; a
  `PMRun` is keyed `pm-run-…` and carries no run id, so the four were found by `created_at`.
- **Owed:** the image-only retag, not before `sched-2026-10-07` has run and the fidelity verdict is
  read; then **F2** on the first scheduled run after it (the snapshot's headline agrees with that
  run's daily brief *Filled* line).
