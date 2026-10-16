<!-- Agent: planning | Role: sprint handover template -->
# Sprint 281 — a replay arm declares how its positions exit, and a stops-only arm runs as before

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-281-a-replay-arm-declares-how-its-positions-exit`
**Status:** SPEC
**Version:** *no bump*
**Effort:** M
**Decisions:** [DL-304](../design-log.md) (this sprint, ten decisions) · [DL-240](../design-log.md) step 3 (the exit experiment it serves) · work-queue 92

> **Why no bump.** Every changed file is under `scripts/` or `tests/`. No file under `kernel`,
> `contracts`, `agents`, `orchestration` or `surfaces` changes, so the package ships nothing new
> (S271's precedent). The full cycle still applies: it edits Python, so branch, `make ci` and the gate.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **PM-OUT-02** and **PM-TYP-02** (what an approved buy carries: its `stop_pct`
and `target_pct`, stop below target). No law governs `scripts/replay_*`; the replay calls the scanner,
analyst and PM code unchanged.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test cites its plan ID (`S281-A<n>`) in its docstring; no clause governs these scripts.

### 🩹 The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**No.** The change is the replay harness under `scripts/`. No agent gains or loses a behaviour; the
fleet's code paths are unchanged. No `laws.md`, `test-plan.md`, ledger or INDEX row changes.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `scripts/replay_broker.py`, `scripts/replay_ledger.py` | `agents/portfolio_manager/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | PM-OUT-02, PM-TYP-02: the take-profit reads the buy's `target_pct` |
| `scripts/replay_exits.py` (new), `scripts/replay_session.py` | the same; `agents/execution/laws/laws.md` (how the fleet places a sell) | the time exit is placed as the PM's sells are: a DAY limit with the sell tolerance |
| `scripts/replay_arms.py`, `scripts/replay_runner.py`, `scripts/replay_counters.py` | `docs/research/experiments/EXP-014-does-the-price-only-pipeline-beat-spy-held-at-the-same-exposure.md` Appendix P | EXP-014's manifest is frozen; its arms must run and record exactly as before |

⚠️ **A stops-only arm must not change.** With no `exits` declared, the replay's `equity.csv`,
`fills.csv` and `sessions.csv` are byte for byte what `main` writes, `summary.json` differs only by the
new `absent_inputs.sell_without_position: 0`, and an EXP-014 arm calls the runner with exactly the
arguments it did. If your change moves any of that, stop and report.

---

## Goal

A replay arm can declare, in its manifest, how its positions leave the book besides the protective
stop: a take-profit at the PM's own target, a sale after N sessions, a stop that trails the high, and a
cool-down before a stopped name is offered again. Each exit is simulated on daily bars by a stated
rule, fills name the exit that sold them, and an arm that declares nothing replays exactly as today.

## Why (context)

Work-queue 92: the book only ever exits on its stop. Losses are realised automatically and gains never
are. DL-240's sequence is to measure exits on the ten-year replay cache, at no LLM cost, before any is
built live, and the replay cannot yet simulate one. S241's scorecard (F4, 2026-10-16) says why it
matters: on 21 settled buys the stop came first 47.6 % of the time against 29.4 % declared. The
experiment itself (arms, bar, pre-registration) is the planner's next step, after the fidelity verdict;
this sprint builds what it runs on.

### Measured, 2026-10-16 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Exits the replay simulates | DAY limit on its target session; GTC stop from the session after the fill; ended-line sells | *[measured 2026-10-16]* read `scripts/replay_broker.py`, `replay_ledger.py`, `replay_marks.py` on `main` `9d9db45b` |
| An approved buy carries its target | `OrderIntent.target_pct`, set by the PM's gate report | *[measured 2026-10-16]* `contracts/portfolio_manager.py:80`, `agents/portfolio_manager/domain/gate_report.py:61`; PM-OUT-02 |
| Fills in the ten-year smoke | 1,044: 552 buys, 463 stops, 8 PM limit sells, 21 ended-line | *[measured 2026-10-16]* `replays/index-2016-2026-10bps/fills.csv` (OneDrive), counted by side and reason |
| Sells of a line no longer held | 0 in the ten-year smoke, 0 in S250's F1 run | *[measured 2026-10-16]* replayed each `fills.csv` keeping a running holding per line |
| `replay_ledger.equity_cents` callers | none | *[measured 2026-10-16]* `grep -rn "equity_cents(" scripts tests` |
| Stop first, live, 21 settled claims | 47.6 % realised, 29.4 % declared | *[measured 2026-10-16]* `scripts/barrier_ledger.py` (S241 F4) |
| The prototype's stops-only window equals `main`'s | three outputs byte-identical; summary equal but for the new key | *[measured 2026-10-16]* `s281_f1_window.py`, 2024-01-02 to 2024-06-28, 10 bps, history rule on |

---

## Scope — and what is deliberately NOT here

1. **The policy (`scripts/replay_exits.py`, new).** `ExitPolicy` with four fields, all off by default:
   `take_profit`, `time_exit_sessions`, `trailing_stop`, `reentry_cooldown_sessions`. Bad values and
   unknown manifest keys are refused. `ExitState` applies it in the session loop and counts what it did.
2. **The take-profit (`replay_broker.py`, `replay_ledger.py`).** A buy carries its `target_pct` to the
   position only under a take-profit; the barrier rule (DL-304 D2) fills target or stop.
3. **The time exit, the trailing stop and the cool-down** (`replay_exits.py`, wired in
   `replay_session.py`), by DL-304 D3 to D5.
4. **A sell of a line no longer held sells nothing** and is counted (`sell_without_position`).
5. **Arms and outputs.** A manifest arm's `exits` reaches the runner and `arm.json`; fill rows name the
   exit; the summary's `exits` section; all only when declared.

### Out of scope (do NOT build this sprint)

- **The exit experiment's manifest, arms or verdict.** That is the pre-registration, the planner's.
- **Any live exit.** Nothing under `agents/` changes; the fleet still exits only on its stop.
- **`exp014_arms.json`.** Frozen by EXP-014's Appendix P.
- **`replay_series.held_stops`** (it passes stop ÷ entry as a `stop_pct`; unreachable, DL-304).
- **No `laws.md` edit, no ADR, no version bump, no `uv.lock` change.**

### The road not taken (LAW-06)

- **The test bed's rule without the open.** Rejected: an open beyond a barrier decides which filled.
- **A time exit at market on the open.** Rejected: the fleet sells by DAY limit with a tolerance.
- **A trailing stop on the close.** Rejected: the broker's trailing order follows the high.
- **A cool-down that drops the approved buy.** Rejected: it leaves the capital idle.
- **A weekend hold.** Rejected for now: an entry profile, DL-240 step 5.

---

## The design decisions — made, and recorded in DL-304

1. **Declared per arm**; absent is stops only; EXP-014's arms run and record as before.
2. **Take-profit**: entry × (1 + `target_pct`), rounded up; per bar: open ≥ target → target at open;
   low ≤ stop → stop at min(open, stop); high ≥ target → target at the target.
3. **Time exit N**: closed N sessions in the book (fill session = 1) → DAY limit sell next session at
   the close less the sell tolerance, reason `time_exit`; not while a sell waits, not without a bar, not
   on the last session; re-placed while unfilled.
4. **Trailing stop**: after settlement, an active stop rises to the stop price of the session's high;
   never falls; from the next session.
5. **Cool-down k**: a stop in session s leaves the line out of the runs of s to s + k − 1.
6. **A sell of a line no longer held** sells nothing and is counted.
7. **Outputs**: fill reasons; `exits` in the summary and `arm.json` only when declared.
8. **No bump.** 9. **`equity_cents` removed.** 10. **Weekend hold not built.**

---

## Blast radius — measured 2026-10-16

| What | Detail |
| --- | --- |
| Files changed | `scripts/replay_exits.py` (new, 196); `replay_broker.py` 128 → 160; `replay_ledger.py` 186 → 189; `replay_session.py` 180 → 193; `replay_arms.py` 156 → 166; `replay_runner.py` 87 → 94; `replay_counters.py` 62 → 63; new tests under `tests/` |
| Agents affected | none; the replay imports `agents.execution.order_tolerance` and the contracts, unchanged |
| Contract change? | no |
| Graph vocabulary change? | no |
| New env keys / tunables | none |
| Deploy implication | none: scripts do not ship in an image |
| Rollback | revert the merge; nothing outside the repo is written. The fidelity count is untouched (no decision path changes) |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. DL-304 is already recorded; read it. Do not edit `docs/design-log.md`.
3. **Write the tests first** under the names and files of the Test plan, and run them on the unchanged
   tree: every one is red (each file fails to import `scripts.replay_exits` or
   `replay_broker.target_price_cents`). Paste the output.
4. **Apply the Appendix exactly.** Change nothing else under `scripts/`.
5. **Plant the breaks** B01 to B32 (Traps), one at a time; each must turn at least one of your tests red.
6. **`make ci` green**, redirected to a file.
7. **Fill the handback sections.**

---

## Test plan

Files: `tests/test_replay_exit_fills.py` (A2–A7), `tests/test_replay_exit_policy.py` (A1, A8–A13),
`tests/test_replay_exit_runs.py` (A14–A16, A18–A20), `tests/test_replay_exit_arms.py` (A17), and a
helper `tests/replay_exit_fixtures.py` (a four-session, one-line cache written with
`write_universe_cache`, and a day runner that buys once). Every test is red on the unchanged tree.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | the default is stops only; anything unknown is refused | `exit_policy_from(None)`, an unknown key, `"yes"`, 0, `True`, 1.5, −1 | `STOPS_ONLY`, not declared; `ValueError` for each bad input |
| A2 | 🎯 a bar fills the barrier it reaches first | entry 100, stop 95, target 110; four bars | open 112 → target at 112; touches both → stop at 95; high 110 → target at 110; open 93 → stop at 93 |
| A3 | without a target the stop rule is unchanged | target `None`; a bar before activation | no take-profit; nothing before activation; stop at min(open, stop) with slippage |
| A4 | the target rounds up and rebases | entry 100.01 at 10 %; ratio 0.5 | 110.02; target and stop halve, `stop_pct` kept, scale doubles |
| A5 | a limit fill carries its order's reason | `PendingOrder(reason="time_exit")` | fill reason `time_exit`; default `limit` |
| A6 | a buy carries its target only under a take-profit | a buy and a sell, each way | `target_pct` on the buy only with `take_profit`; never on the sell |
| A7 | a buy opens with target and stop percent; a sell of nothing is counted | a pending buy and a sell of an unheld line | position target 110, stop 95, `stop_pct` 0.05; one fill; `sell_without_position` 1, cash only the buy's |
| A8 | a trailing stop rises with the high and never falls | an active and a just-filled position; a lower high next | 104.50 for the active one; the new one unchanged; one raise; stops-only moves nothing |
| A9 | a stopped line sits out k runs; only a stop starts it | k = 2; a stop and a target fill | out of two runs, back on the third; counted 2; off when k = 0 |
| A10 | held sessions count the fill session as the first | filled on S0 | 1, 2, 3, 4 |
| A11 | a time exit sells next session what has held N | four positions: due, a PM sell waiting, no bar, too young; then the last session | one `time_exit` sell for S2 under the close; nothing on the last session, nothing counted there |
| A12 | a take-profit counts a buy with a stop but no target | three intents | `buy_without_target` 1 |
| A13 | the summary names policy and counts only when declared | stops only; a time exit | `None`; the exact dict |
| A14 | 🎯 a stops-only run is the run without a policy | the one-line cache | four outputs byte-identical; no `exits`; `sell_without_position` 0 |
| A15 | a take-profit sells at the target | the same | sold on S2 at 110.00, reason `target` |
| A16 | a one-session time exit sells at the next open | the same | sold on S2 at 104.00, reason `time_exit` |
| A17 | an arm declares its exits; a stops-only arm is unchanged | a two-arm manifest, a fake runner | `exits` reaches the runner and `arm.json` only for the declaring arm |
| A18 | a time exit the target beat is dropped and counted | take-profit and a one-session time exit | the target fills; `sell_without_position` 1 |
| A19 | a trailing stop rises on S2 and sells on S3 | the same cache | sold on S3 at 105.45, reason `stop`; one raise |
| A20 | 🪤 a stopped line is not offered for k runs | bars that stop on S2; k = 2 | tickers offered: AAA, AAA, none, none; counted 2 |

---

## Success factors

- [ ] A stops-only replay is unchanged: F1a (planner) shows `equity.csv`, `fills.csv` and
      `sessions.csv` byte-identical to `main` on the window, `summary.json` differing only by
      `sell_without_position: 0`.
- [ ] Each exit runs on the real cache and equals the prototype: F1b (planner).
- [ ] A1–A20 pass, each docstring citing its ID.
- [ ] B01–B32 each turn at least one of the builder's tests red (planner re-runs `s281_breaks.py`).
- [ ] The Appendix applied exactly: every production blob equals the prototype's.
- [ ] No existing test changed; every touched module under 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **An EXP-014 arm must call the runner with exactly its old arguments.** `test_c16` in
`tests/test_replay_arms.py` pins them; that is why `run_arm` passes `exits` only when declared.
Changing that test is changing an existing test: do not.
🪤 **`replay_session.py` is at 193 lines, `replay_exits.py` at 196.** `ruff format` grows files;
measure after formatting. Tests count too.
🪤 **The barrier order is the rule.** Open beyond the target, then the stop, then the target's high.
A bar touching both is the stop.
🪤 **A time exit's sell can meet a position already gone** (its stop or target filled first that
session). It must sell nothing; A18 is the case.
🪤 **The cool-down counts runs, not calendar days**, and starts on the stop's own session.
🪤 **Replay outputs refuse a path inside the worktree** (`refuse_worktree_out`): tests write to
`tmp_path`.
🪤 **The breaks.** Plant each in the Appendix's code, one at a time; each must turn at least one of
your tests red. The planner re-runs them as `s281_breaks.py` against your tests alone.

| # | File | Plant |
| --- | --- | --- |
| B01 | `replay_broker.py` | delete the open-through-the-target branch |
| B02 | `replay_broker.py` | test the target's high before the stop (both touched → target) |
| B03 | `replay_broker.py` | fill the target at the bar's high |
| B04 | `replay_broker.py` | round the target price down |
| B05 | `replay_broker.py` | a rebase keeps the old target |
| B06 | `replay_broker.py` | a limit fill always says `limit` |
| B07 | `replay_ledger.py` | a buy carries its target without a take-profit |
| B08 | `replay_ledger.py` | a sell carries a target |
| B09 | `replay_ledger.py` | a sell of an unheld line still credits cash |
| B10 | `replay_ledger.py` | a new position gets no `stop_pct` |
| B11 | `replay_exits.py` | a trailing stop moves on any difference (`!=`), so it can fall |
| B12 | `replay_exits.py` | a trailing stop moves before activation |
| B13 | `replay_exits.py` | a trailing stop follows the close |
| B14 | `replay_exits.py` | the cool-down keeps lines while `n > 2` |
| B15 | `replay_exits.py` | a target fill starts the cool-down |
| B16 | `replay_exits.py` | `held_sessions` without the `+ 1` |
| B17 | `replay_exits.py` | a time exit ignores a waiting sell |
| B18 | `replay_exits.py` | a time exit is built (and counted) on the last session |
| B19 | `replay_exits.py` | `TIME_EXIT = "limit"` |
| B20 | `replay_exits.py` | an unknown exit key is accepted |
| B21 | `replay_exits.py` | `time_exit_sessions` 0 is accepted |
| B22 | `replay_exits.py` | `_whole` accepts a `bool` |
| B23 | `replay_exits.py` | a stops-only run writes an `exits` summary |
| B24 | `replay_arms.py` | every arm passes `exits=` to the runner |
| B25 | `replay_arms.py` | every arm records `exits` |
| B26 | `replay_arms.py` | the manifest's `exits` is ignored (`STOPS_ONLY`) |
| B27 | `replay_runner.py` | the runner does not pass `exits` to the loop |
| B28 | `replay_session.py` | members are not passed through `state.cool` |
| B29 | `replay_session.py` | `state.note_stops` is not called |
| B30 | `replay_session.py` | `state.raise_stops` is not called |
| B31 | `replay_exits.py` | `queue_orders` is not given `take_profit` |
| B32 | `replay_session.py` | `sell_without_position` is not summed |

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` beyond the file's existing
  `E402` pattern in `replay_arms.py`.
  📌 Current sizes after the Appendix: `replay_exits.py` **196**, `replay_session.py` **193**,
  `replay_ledger.py` **189**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- `make ci` **every step** green, **100.00 % coverage floor**, redirected to a file.
- **No version bump, no `uv.lock` change.**
- The worktree has **no `.env`** and no replay cache; every proof here runs on fixtures.

---

## Sequencing after merge (the planner's)

1. Review: production blobs equal `prototype_blobs.txt`; the planner's tests on the built tree; the
   breaks against the builder's tests alone; CodeQL set-diff against the S280 branch.
2. F1a and F1b from the built tree (`s281_f1_window.py`, OneDrive `wq92-2026-10-16/`).
3. `make gate-ran` from `../ta-s281`; fast-forward `main`; no tag (no bump).
4. No deploy. Then the exit experiment's pre-registration (DL-240 step 3), run once the fidelity
   verdict reads PASS.

---

## Handover — paste this to Codex

```text
You are building Sprint 281 in the worktree ../ta-s281, on the branch
sprint-281-a-replay-arm-declares-how-its-positions-exit. Never work on main. The worktree and its
venv are ready; never run a bare `uv sync` (it needs the network and you have none).

Read docs/sprints/sprint-281-a-replay-arm-declares-how-its-positions-exit.md, whole, before anything
else. It is the spec, and its bottom sections are your handback. The Appendix holds the production
code, which you apply exactly. Your work is the tests and the evidence.

In order:
1. Read agents/portfolio_manager/laws/laws.md and test-plan.md, agents/execution/laws/laws.md,
   docs/laws/conventions.md and docs/laws/drift-register.md, and DL-304 in docs/design-log.md. Fill
   the Law reading record in the spec BEFORE any code. The law-cycle answer is No.
2. Write tests/replay_exit_fixtures.py and the tests A1 to A20 under the files the Test plan names,
   each docstring citing its ID (S281-A<n>). Run them on the unchanged tree and paste the output into
   the Closeout: every one is red, by import.
3. Apply the Appendix exactly (seven files under scripts/; scripts/replay_exits.py is new). Change
   nothing else under scripts/. Change no existing test.
4. Plant the breaks B01 to B32 one at a time (the table in the spec's Traps). Each must turn at least
   one of your tests red; restore each before the next. Record each in the Closeout.
5. No version bump, no uv.lock change. Run make ci redirected to a file and read the file. If the
   dependency audit is the only step that fails for want of network, say so; the planner runs it.
6. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md, docs/design-log.md or docs/work-queue.md.

DO NOT: reach the network; change anything under kernel/, contracts/, agents/, orchestration/ or
surfaces/; change scripts/exp014_arms.json or any existing test (test_c16 in tests/test_replay_arms.py
pins the arguments an EXP-014 arm passes to the runner); bump the version; use noqa; let any module,
test files included, reach 200 lines; measure make ci through a pipe; write replay output inside the
worktree.

Traps: an arm passes `exits` to the runner only when it declares one; a bar touching stop and target
is the stop; a time exit whose position is gone sells nothing (A18); the cool-down counts runs from the
stop's own session; ruff format grows files, measure after formatting.

Two tiers when something does not fit. A wrong command, count, path or line number whose intent is
plain: correct it, record it in Return notes, and carry on. A law that contradicts the spec, an
existing test failing, or a measurement in the spec that does not reproduce: STOP and report. State
anything not done as "not done" or "verified failing". Never write a Result for work you have not
done.
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
| *to fill* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *to fill*

**Contradictions found between a law and this spec:** *to fill*

**Laws found silent where a decision was needed:** *to fill*

**Clauses that were ⬜ and are now proven:** *to fill*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| *to fill* | | | | |

**Tests added beyond the plan:** *to fill*

---

## Closeout — evidence

**Status:** *to fill*

**Tree the proofs ran in (and `.env` present?):** *to fill*

**Result:** *to fill*

**Files changed:** *to fill*

**Design decisions:** recorded as [`DL-304`](../design-log.md) by the planner.

**Proof — the red run first:** *to fill*

**Proof — the green run:** *to fill*

**Guards planted:** *to fill*

**Module line counts:** *to fill*

**`make ci`:** *to fill*

**`make gate-ran`:** the planner's.

**Not met / verified failing:** *to fill*

### The planner's prototype (measured 2026-10-16, before handover)

In `../ta-s281-proto`, local branch `proto-s281` at `af3d5b27` (from `main` `9d9db45b`); kit in
OneDrive `trading-agents-data/wq92-2026-10-16/`.

- **`make ci`** exit 0: 5,158 passed, 9 skipped, 100.00 % (`s281_proto_make_ci.txt`).
- **Breaks:** 32 of 32 red against the planner's tests (`s281_breaks_on_prototype.txt`). The first
  run left five green (B18, B28, B29, B30, B32); the loop-level tests A18 to A20 and A11's last-session
  count were added for them.
- **Production blobs** (`prototype_blobs.txt`): seven files under `scripts/`.
- **F1a, a stops-only arm is unchanged** (`s281_f1_window.py`, 2024-01-02 to 2024-06-28, 10 bps,
  history rule on, the real replay cache): `main` `9d9db45b` and the prototype write the same
  `equity.csv` (`c47866b8411765cd`), `fills.csv` (`b278dd10d2096b63`) and `sessions.csv`
  (`cfe1ee462d8eb770`); the summaries are equal once `sell_without_position: 0` is removed
  (`f1a_summary_diff.txt`). 143 fills: 91 buys, 51 stops, 1 membership end.
- **F1b, each exit on the same window** (`f1_proto.txt`; a smoke, not the experiment: six months, one
  regime, nothing pre-registered):

| Arm | Fills by exit | Equity 2024-06-28 | Counts |
| --- | --- | --- | --- |
| stops only | 51 stop, 1 membership end | $104,840.51 | none |
| take-profit | 222 target, 130 stop | $103,651.45 | 0 buys without a target |
| time exit, 10 sessions | 230 time exit, 101 stop, 1 membership end | $103,374.25 | 245 orders; 4 sells met a position already gone |
| trailing stop | 268 stop | $102,805.34 | 1,269 raises |
| cool-down, 3 runs | 45 stop, 1 membership end | $104,887.51 | 134 member sessions left out |
| all four | 233 stop, 183 target, 64 time exit | $101,481.50 | 11 sells met a position already gone |

---

## Return notes

- *to fill*

---

## Appendix — the change, measured on the planner's prototype

Apply with `git apply` from the worktree root (it applies cleanly to this branch's base). The
prototype is local branch `proto-s281` in `../ta-s281-proto`.

```diff
diff --git a/scripts/replay_arms.py b/scripts/replay_arms.py
index d27efb5f..b7701c7f 100644
--- a/scripts/replay_arms.py
+++ b/scripts/replay_arms.py
@@ -29,6 +29,7 @@ from scripts.replay_arms_record import (  # noqa: E402
     read_repo_state,
     write_benchmark,
 )
+from scripts.replay_exits import STOPS_ONLY, ExitPolicy, exit_policy_from  # noqa: E402
 from scripts.replay_outputs import refuse_worktree_out  # noqa: E402
 from scripts.replay_runner import DEFAULT_PROGRESS_EVERY, run  # noqa: E402

@@ -41,11 +42,12 @@ ALL = "all"

 @dataclass(frozen=True)
 class ArmSpec:
-    """One arm of the manifest: its name, slippage a side and setting overrides."""
+    """One arm of the manifest: name, slippage a side, overrides, exit policy."""

     name: str
     slippage_bps: int
     overrides: tuple[str, ...]
+    exits: ExitPolicy = STOPS_ONLY


 @dataclass(frozen=True)
@@ -66,7 +68,12 @@ def load_manifest(path: Path = MANIFEST) -> Manifest:
         start=date.fromisoformat(data["start"]),
         require_history=bool(data["require_history"]),
         arms=tuple(
-            ArmSpec(arm["name"], int(arm["slippage_bps"]), tuple(arm["overrides"]))
+            ArmSpec(
+                arm["name"],
+                int(arm["slippage_bps"]),
+                tuple(arm["overrides"]),
+                exit_policy_from(arm.get("exits")),
+            )
             for arm in data["arms"]
         ),
     )
@@ -107,6 +114,7 @@ def run_arm(
         slippage_bps=spec.slippage_bps,
         progress_every=progress_every,
         require_history=manifest.require_history,
+        **({"exits": spec.exits} if spec.exits.declared else {}),
     )
     sessions = equity_dates(out / "equity.csv")
     write_benchmark(cache_dir, sessions, out / "benchmark.csv")
@@ -124,6 +132,8 @@ def run_arm(
         "slippage_bps": spec.slippage_bps,
         "start": manifest.start.isoformat(),
     }
+    if spec.exits.declared:  # a stops-only arm's record is unchanged (S281)
+        record["exits"] = spec.exits.as_dict()
     (out / "arm.json").write_text(
         json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
     )
diff --git a/scripts/replay_broker.py b/scripts/replay_broker.py
index aaeb8e77..6484cdff 100644
--- a/scripts/replay_broker.py
+++ b/scripts/replay_broker.py
@@ -1,15 +1,17 @@
 """Script-local broker simulator for S235 replay orders.

 Agent: tooling
-Role: simulate DAY limit orders, GTC protective stops, and replay ledger rebases.
+Role: simulate DAY limit orders, GTC protective stops and take-profits, and rebases.
 External I/O: none.
 """

 from __future__ import annotations

-from dataclasses import dataclass
+from dataclasses import dataclass, replace
 from typing import TYPE_CHECKING

+from contracts.stop_rule import PCT_SCALE
+
 if TYPE_CHECKING:
     from datetime import date

@@ -35,6 +37,8 @@ class PendingOrder:
     limit_cents: int
     target_session: date
     stop_pct: float = 0.0
+    target_pct: float | None = None
+    reason: str = "limit"


 @dataclass(frozen=True)
@@ -57,6 +61,8 @@ class ReplayPosition:
     stop_active_from: date
     position_ref: str = ""
     price_scale: float = 1.0
+    target_price_cents: int | None = None
+    stop_pct: float = 0.0


 def simulate_limit_fill(
@@ -79,27 +85,47 @@ def simulate_limit_fill(
         order.side,
         order.quantity,
         _apply_slippage(price, order.side, slippage_bps),
-        "limit",
+        order.reason,
     )


 def simulate_stop_fill(
     position: ReplayPosition, bar: ReplayBar, *, slippage_bps: int
 ) -> ReplayFill | None:
-    """Fill an active stop at min(open, stop), after the activation session."""
-    if (
-        bar.date < position.stop_active_from
-        or bar.low_cents > position.stop_price_cents
-    ):
+    """Fill an active stop, or a take-profit when the position carries one.
+
+    From the activation session on: an open at or above the target fills the target at
+    the open; a low at or below the stop fills the stop at min(open, stop), so a bar
+    touching both counts as the stop (EXP-011's and S241's rule); a high at or above
+    the target fills it at the target.
+    """
+    if bar.date < position.stop_active_from:
         return None
-    price = min(bar.open_cents, position.stop_price_cents)
+    target = position.target_price_cents
+    if target is not None and bar.open_cents >= target:
+        return _exit_fill(position, bar, bar.open_cents, "target", slippage_bps)
+    if bar.low_cents <= position.stop_price_cents:
+        price = min(bar.open_cents, position.stop_price_cents)
+        return _exit_fill(position, bar, price, "stop", slippage_bps)
+    if target is not None and bar.high_cents >= target:
+        return _exit_fill(position, bar, target, "target", slippage_bps)
+    return None
+
+
+def _exit_fill(
+    position: ReplayPosition,
+    bar: ReplayBar,
+    price_cents: int,
+    reason: str,
+    slippage_bps: int,
+) -> ReplayFill:
     return ReplayFill(
         bar.date,
         position.line,
         "sell",
         position.quantity,
-        _apply_slippage(price, "sell", slippage_bps),
-        "stop",
+        _apply_slippage(price_cents, "sell", slippage_bps),
+        reason,
     )


@@ -109,18 +135,24 @@ def apply_adjustment_rebase(
     """Rescale a held line's entry and stop for an adjustment-error day."""
     if ratio <= 0:
         return position
-    return ReplayPosition(
-        position.line,
-        position.quantity,
-        round(position.entry_price_cents * ratio),
-        round(position.stop_price_cents * ratio),
-        position.opened,
-        position.stop_active_from,
-        position.position_ref,
-        position.price_scale / ratio,
+    target = position.target_price_cents
+    return replace(
+        position,
+        entry_price_cents=round(position.entry_price_cents * ratio),
+        stop_price_cents=round(position.stop_price_cents * ratio),
+        price_scale=position.price_scale / ratio,
+        target_price_cents=None if target is None else round(target * ratio),
     )


+def target_price_cents(entry_cents: int, target_pct: float | None) -> int | None:
+    """The take-profit price, rounded up to the cent; None without a target."""
+    if target_pct is None:
+        return None
+    scale = PCT_SCALE + round(target_pct * PCT_SCALE)
+    return -(-entry_cents * scale // PCT_SCALE)
+
+
 def _apply_slippage(price_cents: int, side: str, slippage_bps: int) -> int:
     factor = (
         1.0 + slippage_bps / 10_000 if side == "buy" else 1.0 - slippage_bps / 10_000
diff --git a/scripts/replay_counters.py b/scripts/replay_counters.py
index 495086b3..8ddd0213 100644
--- a/scripts/replay_counters.py
+++ b/scripts/replay_counters.py
@@ -28,6 +28,7 @@ def initial_absent_inputs() -> dict[str, Any]:
         "membership_end_exits": 0,
         "expired_no_bar": 0,
         "buy_without_stop": 0,
+        "sell_without_position": 0,
     }


diff --git a/scripts/replay_exits.py b/scripts/replay_exits.py
new file mode 100644
index 00000000..74202b79
--- /dev/null
+++ b/scripts/replay_exits.py
@@ -0,0 +1,196 @@
+"""Exit policies a replay arm can declare beside its protective stops (S281).
+
+Agent: tooling
+Role: hold one arm's exit policy and apply it in the session loop: time exits,
+      trailing stops and the re-entry cool-down (the take-profit rests in the broker).
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from bisect import bisect_left
+from collections import Counter
+from dataclasses import asdict, dataclass, field, replace
+from decimal import Decimal
+from typing import TYPE_CHECKING, Any
+
+from scripts.replay_ledger import queue_orders, replay_bar
+
+from contracts.common import Explanation, Money
+from contracts.portfolio_manager import OrderIntent
+from contracts.stop_rule import stop_price_cents
+
+if TYPE_CHECKING:
+    from collections.abc import Mapping
+    from datetime import date
+
+    from scripts.replay_broker import PendingOrder, ReplayPosition
+    from scripts.sp500_bars import BarRow
+
+    from agents.execution.order_tolerance import OrderToleranceConfig
+
+TIME_EXIT = "time_exit"
+COUNT_KEYS = (
+    "buy_without_target",
+    "cooldown_member_sessions",
+    "time_exit_orders",
+    "trail_raises",
+)
+
+
+def _whole(value: object, floor: int) -> bool:
+    return isinstance(value, int) and not isinstance(value, bool) and value >= floor
+
+
+@dataclass(frozen=True)
+class ExitPolicy:
+    """How an arm's positions leave the book besides their stop; all off by default."""
+
+    take_profit: bool = False
+    time_exit_sessions: int | None = None
+    trailing_stop: bool = False
+    reentry_cooldown_sessions: int = 0
+
+    def __post_init__(self) -> None:
+        for name in ("take_profit", "trailing_stop"):
+            if not isinstance(getattr(self, name), bool):
+                raise ValueError(f"{name} must be true or false")
+        sessions = self.time_exit_sessions
+        if sessions is not None and not _whole(sessions, 1):
+            raise ValueError("time_exit_sessions must be a whole number, at least 1")
+        if not _whole(self.reentry_cooldown_sessions, 0):
+            raise ValueError("reentry_cooldown_sessions must be a whole number, >= 0")
+
+    @property
+    def declared(self) -> bool:
+        """Whether the arm asks for anything beyond stops only."""
+        return self != ExitPolicy()
+
+    def as_dict(self) -> dict[str, Any]:
+        return asdict(self)
+
+
+STOPS_ONLY = ExitPolicy()
+
+
+def exit_policy_from(data: Mapping[str, Any] | None) -> ExitPolicy:
+    """Read a manifest arm's `exits`; absent is stops only, an unknown key refused."""
+    if data is None:
+        return STOPS_ONLY
+    known = tuple(STOPS_ONLY.as_dict())
+    unknown = sorted(set(data) - set(known))
+    if unknown:
+        raise ValueError(f"unknown exit keys {unknown}; known: {', '.join(known)}")
+    return ExitPolicy(**data)
+
+
+@dataclass
+class ExitState:
+    """One run's exit bookkeeping: the lines cooling down and the counts."""
+
+    policy: ExitPolicy
+    cooling: dict[str, int] = field(default_factory=dict)
+    counts: Counter[str] = field(default_factory=Counter)
+
+    def note_stops(self, new_fills: list[dict[str, Any]]) -> None:
+        """Start the cool-down for each line whose stop filled this session."""
+        for row in new_fills:
+            if self.policy.reentry_cooldown_sessions and row["reason"] == "stop":
+                self.cooling[row["line"]] = self.policy.reentry_cooldown_sessions
+
+    def cool(self, members: tuple[str, ...]) -> tuple[str, ...]:
+        """Leave cooling lines out of this session's run, then count one session."""
+        kept = tuple(line for line in members if line not in self.cooling)
+        self.counts["cooldown_member_sessions"] += len(members) - len(kept)
+        self.cooling = {line: n - 1 for line, n in self.cooling.items() if n > 1}
+        return kept
+
+    def raise_stops(
+        self,
+        session: date,
+        positions: dict[str, ReplayPosition],
+        day_bars: Mapping[str, BarRow],
+    ) -> None:
+        """Lift each active stop to the session's high less its stop percent."""
+        if not self.policy.trailing_stop:
+            return
+        for line, position in tuple(positions.items()):
+            row = day_bars.get(line)
+            if row is None or session < position.stop_active_from:
+                continue
+            raised = stop_price_cents(replay_bar(row).high_cents, position.stop_pct)
+            if raised > position.stop_price_cents:
+                positions[line] = replace(position, stop_price_cents=raised)
+                self.counts["trail_raises"] += 1
+
+    def queue_orders(
+        self,
+        index: int,
+        sessions: tuple[date, ...],
+        positions: dict[str, ReplayPosition],
+        pending: list[PendingOrder],
+        day_bars: Mapping[str, BarRow],
+        approved: tuple[Any, ...],
+        config: OrderToleranceConfig,
+    ) -> int:
+        """Queue the PM's intents, then the time exits; return the stopless buys.
+
+        With a take-profit, a buy carries its target and a targetless one is counted;
+        with a time exit, what has held N sessions and has no sell waiting is sold at
+        the next session.
+        """
+        stopless = queue_orders(
+            approved,
+            sessions,
+            index,
+            pending,
+            config,
+            take_profit=self.policy.take_profit,
+        )
+        if self.policy.take_profit:
+            self.counts["buy_without_target"] += sum(
+                1
+                for intent in approved
+                if intent.action == "buy"
+                and intent.stop_pct is not None
+                and intent.target_pct is None
+            )
+        limit = self.policy.time_exit_sessions
+        if limit is None or index + 1 >= len(sessions):
+            return stopless
+        selling = {order.line for order in pending if order.side == "sell"}
+        intents = tuple(
+            _time_exit(line, position, day_bars[line], limit)
+            for line, position in sorted(positions.items())
+            if line not in selling
+            and line in day_bars
+            and held_sessions(sessions, position.opened, index) >= limit
+        )
+        self.counts["time_exit_orders"] += len(intents)
+        queue_orders(intents, sessions, index, pending, config, reason=TIME_EXIT)
+        return stopless
+
+    def summary(self) -> dict[str, Any] | None:
+        """The policy and its counts, or None for a stops-only arm."""
+        if not self.policy.declared:
+            return None
+        counts = {key: self.counts[key] for key in COUNT_KEYS}
+        return {"counts": counts, "policy": self.policy.as_dict()}
+
+
+def held_sessions(sessions: tuple[date, ...], opened: date, index: int) -> int:
+    """Sessions a position has closed in the book by `sessions[index]`, its first 1."""
+    return index - bisect_left(sessions, opened) + 1
+
+
+def _time_exit(
+    line: str, position: ReplayPosition, row: BarRow, limit: int
+) -> OrderIntent:
+    return OrderIntent(
+        ticker=line,
+        action="sell",
+        quantity=position.quantity,
+        est_price=Money(amount=Decimal(str(row.close))),
+        position_ref=position.position_ref,
+        rationale=Explanation(summary=f"time exit after {limit} sessions"),
+    )
diff --git a/scripts/replay_ledger.py b/scripts/replay_ledger.py
index 7bf6f0d7..78aeddf4 100644
--- a/scripts/replay_ledger.py
+++ b/scripts/replay_ledger.py
@@ -17,8 +17,8 @@ from scripts.replay_broker import (
     ReplayPosition,
     simulate_limit_fill,
     simulate_stop_fill,
+    target_price_cents,
 )
-from scripts.replay_marks import mark_positions

 from agents.execution.order_tolerance import (
     OrderToleranceConfig,
@@ -40,6 +40,7 @@ class PendingSettlement(NamedTuple):
     expired: int
     cash_delta_cents: int
     no_bar: int
+    sell_without_position: int = 0


 def queue_orders(
@@ -48,7 +49,14 @@ def queue_orders(
     index: int,
     pending: list[PendingOrder],
     config: OrderToleranceConfig,
+    *,
+    take_profit: bool = False,
+    reason: str = "limit",
 ) -> int:
+    """Queue each intent as a DAY limit for the next session; count stopless buys.
+
+    With `take_profit`, a buy carries its intent's `target_pct` to the position.
+    """
     if index + 1 >= len(sessions):
         return 0
     buy_without_stop = 0
@@ -66,6 +74,8 @@ def queue_orders(
                 money_cents(evidence.applied_limit_price),
                 sessions[index + 1],
                 intent.stop_pct if intent.stop_pct is not None else 0.0,
+                intent.target_pct if take_profit and side == "buy" else None,
+                reason,
             )
         )
     return buy_without_stop
@@ -108,7 +118,7 @@ def settle_pending(
     fills: list[dict[str, Any]],
     slippage_bps: int,
 ) -> PendingSettlement:
-    expired = no_bar = cash = 0
+    expired = no_bar = cash = unheld = 0
     for order in tuple(pending):
         row = bars.get(order.line)
         if order.target_session != session:
@@ -132,18 +142,20 @@ def settle_pending(
                 session,
                 next_session,
                 f"{fill.line}-{session.isoformat()}",
+                target_price_cents=target_price_cents(
+                    fill.price_cents, order.target_pct
+                ),
+                stop_pct=order.stop_pct,
             )
         else:
-            position = positions.get(fill.line)
-            price_cents = (
-                fill.price_cents
-                if position is None
-                else _position_price_cents(position, fill.price_cents)
-            )
+            position = positions.pop(fill.line, None)
+            if position is None:  # its stop or target filled first
+                unheld += 1
+                continue
+            price_cents = _position_price_cents(position, fill.price_cents)
             fills.append(_fill_row(fill, price_cents=price_cents))
             cash += fill.quantity * price_cents
-            positions.pop(fill.line, None)
-    return PendingSettlement(expired, cash, no_bar)
+    return PendingSettlement(expired, cash, no_bar, unheld)


 def replay_bar(row: BarRow) -> ReplayBar:
@@ -158,15 +170,6 @@ def replay_bar(row: BarRow) -> ReplayBar:
     )


-def equity_cents(
-    cash_cents: int,
-    positions: dict[str, ReplayPosition],
-    line_bars: dict[str, tuple[BarRow, ...]],
-    session: date,
-) -> int:
-    return mark_positions(cash_cents, positions, line_bars, session).equity_cents
-
-
 def next_session(sessions: tuple[date, ...], index: int) -> date:
     return sessions[index + 1] if index + 1 < len(sessions) else sessions[index]

diff --git a/scripts/replay_runner.py b/scripts/replay_runner.py
index bd033c19..f0306508 100644
--- a/scripts/replay_runner.py
+++ b/scripts/replay_runner.py
@@ -12,6 +12,7 @@ from typing import TYPE_CHECKING, Any
 from scripts.replay_cache import load_replay_cache
 from scripts.replay_counters import initial_absent_inputs
 from scripts.replay_day import run_replay_day
+from scripts.replay_exits import STOPS_ONLY
 from scripts.replay_outputs import (
     performance_summary,
     refuse_worktree_out,
@@ -31,6 +32,8 @@ if TYPE_CHECKING:
     from datetime import date
     from pathlib import Path

+    from scripts.replay_exits import ExitPolicy
+
 DEFAULT_SLIPPAGE_BPS = 10
 DEFAULT_PROGRESS_EVERY = 20

@@ -46,6 +49,7 @@ def run(
     universe_file: Path | None = None,
     progress_every: int = DEFAULT_PROGRESS_EVERY,
     require_history: bool = False,
+    exits: ExitPolicy = STOPS_ONLY,
 ) -> dict[str, Any]:
     """Run a deterministic replay and write artifacts under the cache directory."""
     context = load_replay_cache(cache_dir)
@@ -71,12 +75,15 @@ def run(
         day_runner=run_replay_day,
         progress_every=progress_every,
         require_history=require_history,
+        exits=exits,
     )
-    summary = {
+    summary: dict[str, Any] = {
         "performance": performance_summary(loop.equity, context.spy_closes),
         "non_default_settings": settings.non_defaults,
         "absent_inputs": loop.absent,
     }
+    if loop.exits is not None:  # only an arm that declares exits (S281)
+        summary["exits"] = loop.exits
     write_replay_outputs(
         refuse_worktree_out(out or cache_dir / "pipeline-replay"),
         loop.equity,
diff --git a/scripts/replay_session.py b/scripts/replay_session.py
index 82c9c4fb..e96390c3 100644
--- a/scripts/replay_session.py
+++ b/scripts/replay_session.py
@@ -14,10 +14,10 @@ from typing import TYPE_CHECKING, Any

 from scripts.replay_counters import replay_day_counts, zero_absent_reasons
 from scripts.replay_day import ReplayDayInputs
+from scripts.replay_exits import STOPS_ONLY, ExitPolicy, ExitState
 from scripts.replay_history import offer_lines, visible_window
 from scripts.replay_ledger import (
     next_session,
-    queue_orders,
     settle_pending,
     settle_stops,
 )
@@ -56,6 +56,7 @@ class ReplayLoopResult:
     equity: tuple[EquityPoint, ...]
     fills: tuple[dict[str, Any], ...]
     session_rows: tuple[dict[str, Any], ...]
+    exits: dict[str, Any] | None = None


 _CENTS = Decimal("100")
@@ -75,8 +76,10 @@ def run_replay_sessions(
     day_runner: Callable[[ReplayDayInputs, ReplaySettings], ReplayDayResult],
     progress_every: int,
     require_history: bool = False,
+    exits: ExitPolicy = STOPS_ONLY,
 ) -> ReplayLoopResult:
     """Run the replay sessions and return byte-stable output rows."""
+    state = ExitState(exits)
     pending: list[PendingOrder] = []
     positions: dict[str, ReplayPosition] = {}
     cash_cents = int(settings.portfolio.starting_cash * _CENTS)
@@ -89,9 +92,11 @@ def run_replay_sessions(
         day_bars = date_bars.get(session, {})
         rebased = apply_adjustment_rebases(session, positions, line_bars, known_moves)
         absent["adjustment_error_rebases"] += rebased.count
+        settled = len(fills)
         cash_cents += settle_stops(
             day_bars, positions, fills, slippage_bps, skip_lines=rebased.lines
         )
+        state.note_stops(fills[settled:])
         pending_result = settle_pending(
             session,
             next_session(sessions, index),
@@ -103,14 +108,16 @@ def run_replay_sessions(
         )
         cash_cents += pending_result.cash_delta_cents
         absent["expired_no_bar"] += pending_result.no_bar
+        absent["sell_without_position"] += pending_result.sell_without_position
         pending = [order for order in pending if order.target_session > session]
-        exits = exit_ended_positions(
+        ended = exit_ended_positions(
             session, positions, line_bars, context.universe.episodes, fills
         )
-        cash_cents += exits.cash_delta_cents
-        absent["data_end_exits"] += exits.data_end_exits
-        absent["membership_end_exits"] += exits.membership_end_exits
-        members = fixed_lines or members_on(context.universe, session)
+        cash_cents += ended.cash_delta_cents
+        absent["data_end_exits"] += ended.data_end_exits
+        absent["membership_end_exits"] += ended.membership_end_exits
+        state.raise_stops(session, positions, day_bars)
+        members = state.cool(fixed_lines or members_on(context.universe, session))
         visible_bars = visible_window(settings, line_bars, members, session)
         if fixed_lines is not None:
             members = tuple(
@@ -150,11 +157,13 @@ def run_replay_sessions(
         )
         for key, value in result.absent_inputs.items():
             absent[key] = int(absent.get(key, 0)) + value
-        absent["buy_without_stop"] += queue_orders(
-            result.approved,
-            sessions,
+        absent["buy_without_stop"] += state.queue_orders(
             index,
+            sessions,
+            positions,
             pending,
+            day_bars,
+            result.approved,
             OrderToleranceConfig.from_settings(settings.execution),
         )
         equity.append(EquityPoint(session, marked.equity_cents, marked.long_cents))
@@ -176,5 +185,9 @@ def run_replay_sessions(
             progress_every,
         )
     return ReplayLoopResult(
-        absent, tuple(equity), tuple(fills), zero_absent_reasons(session_rows)
+        absent,
+        tuple(equity),
+        tuple(fills),
+        zero_absent_reasons(session_rows),
+        state.summary(),
     )
```
