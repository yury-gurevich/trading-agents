<!-- Agent: planning | Role: sprint handover template -->
# Sprint 282 — each exit arm is scored against stops-only on the same days, and arms that are not EXP-022's give no verdict

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-282-each-exit-arm-is-scored-against-stops-only-on-the-same-days`
**Status:** SPEC
**Version:** *no bump*
**Effort:** M
**Decisions:** [DL-305](../design-log.md) (this sprint and the experiment, ten decisions) ·
[EXP-022](../research/experiments/EXP-022-does-an-exit-besides-the-stop-make-the-book-earn-more.md)
(the pre-registration this scorer applies) · [DL-304](../design-log.md) (the replay's exits, S281) ·
work-queue 92

> **Why no bump.** Every changed file is under `scripts/` or `tests/`. No file under `kernel`,
> `contracts`, `agents`, `orchestration` or `surfaces` changes, so the package ships nothing new
> (S271's and S281's precedent). The full cycle still applies: it adds Python, so branch, `make ci`
> and the gate.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **RPT-OUT-07** (every return is computed by the reporter's
`calculate_performance`; the scorer computes none of its own). No law governs `scripts/exit_verdict*`
or `scripts/replay_*`; EXP-022's Appendix P is the rule this scorer applies.

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
8. Every test cites its plan ID (`S282-A<n>`) in its docstring; no clause governs these scripts.

### 🩹 The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**No.** The change is a scorer under `scripts/` that reads replay outputs. No agent gains or loses a
behaviour. No `laws.md`, `test-plan.md`, ledger or INDEX row changes.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `scripts/exit_verdict_stats.py`, `exit_verdict_score.py` (new) | `agents/reporter/laws/laws.md` + `test-plan.md` | RPT-OUT-07: returns come from `calculate_performance` only |
| `scripts/exit_verdict_rule.py`, `exit_verdict_load.py`, `exp022_arms.json` (new) | [EXP-022](../research/experiments/EXP-022-does-an-exit-besides-the-stop-make-the-book-earn-more.md) sections 2, 5 and Appendix P; [DL-305](../design-log.md) | the arms, the interval and the verdict are Appendix P's, in code |
| `scripts/exit_verdict_trips.py`, `exit_verdict_report.py`, `exit_verdict_markdown.py`, `exit_verdict.py` (new) | the same; [EXP-014](../research/experiments/EXP-014-does-the-price-only-pipeline-beat-spy-held-at-the-same-exposure.md) Appendix P | S250's scorer is reused, never edited: EXP-014 is frozen |

⚠️ **No existing file changes.** Every production file is new. S250's modules
(`replay_verdict_*.py`, `exp014_arms.json`) and S281's (`replay_exits.py`, `replay_arms.py`) are
imported as they are. If your change needs to edit one, stop and report.

---

## Goal

One command scores EXP-022: it loads the twelve arm folders the replay writes, refuses any that are not
Appendix P's or do not belong together, pairs each exit arm with stops-only at its own slippage on one
shared set of bootstrap draws, applies the pre-registered rule, and writes a byte-stable verdict with
each arm's exits broken down by the reason that closed them.

## Why (context)

Work-queue 92: the book only ever exits on its stop. S281 taught the replay four exits; DL-240's next
step is the pre-registered experiment, EXP-022, written with this spec. The experiment runs only once
the fidelity verdict reads PASS (9 of 10 judged PM recommendations on 2026-10-16; the count restarted at
`sched-2026-10-16`), so its scorer must exist, proven, before then. EXP-014's scorer cannot do it: its
arms are fixed in code, its statistic is each arm against exposure-matched SPY, and it never checks an
arm's recorded exits.

### Measured, 2026-10-16 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| EXP-014's scorer names its arms in code | `BASE_ARM = "base-25"`, `ABLATION_ARMS` | *[measured 2026-10-16]* read `scripts/replay_verdict_rule.py` on `main` `39f00061` |
| S250's loader does not check `exits` | `_own_reasons` compares arm, experiment, overrides, history rule, slippage, start, sessions, dirty | *[measured 2026-10-16]* read `scripts/replay_verdict_load.py` |
| S250's loader takes the first arm as the reference when `base-25` is absent | `reference = BASE_ARM if BASE_ARM in loaded.arms else next(iter(loaded.arms))` | *[measured 2026-10-16]* `replay_verdict_load.py::_belong_together`; EXP-022's first arm is `stops-25` |
| `replay_arms.py` runs any manifest, exits included | `--manifest`; `arm.json` carries `exits` only when declared | *[measured 2026-10-16]* `scripts/replay_arms.py` (S281) |
| Fill rows carry what a round trip needs | `date, line, side, quantity, price_cents, reason`; a sell's price is on its position's entry basis | *[measured 2026-10-16]* `scripts/replay_ledger.py::_fill_row`, `_position_price_cents` |
| Exits multiply buys | 2024 H1, 10 bps: 91 stops-only, 376 take-profit, 353 time exit, 290 trailing | *[measured 2026-10-16]* `wq92-2026-10-16/f1_proto.txt` (OneDrive) |
| Coverage and mypy do not read `scripts/` | `[tool.coverage.run] source` and the Makefile's `PKGS` name the five packages only | *[measured 2026-10-16]* `pyproject.toml:250`, `Makefile:5` |
| The prototype passes the gate | `make ci` exit 0 (5,178 passed, 100.00 %); the planner's 21 tests (24 cases) pass and are red by import on `main`; 34 of 34 breaks red | *[measured 2026-10-16]* `../ta-s282-proto`, `proto-s282` `1691d5df`; kit `wq92s282-2026-10-16/` (OneDrive) |

---

## Scope — and what is deliberately NOT here

1. **The manifest (`scripts/exp022_arms.json`, new).** EXP-022's twelve arms, byte for byte as the
   Appendix gives it.
2. **The rule (`scripts/exit_verdict_rule.py`, new).** Appendix P's arms (`POLICIES`, `CHALLENGERS`,
   `FAMILIES`) and its verdict (`reading`, `decide`).
3. **The statistic and the scoring (`exit_verdict_stats.py`, `exit_verdict_score.py`, new).** `R`,
   the family interval, every arm's blocks, the control, the paired differences on shared draws.
4. **The round trips (`exit_verdict_trips.py`, new).** Each sell paired with the oldest open buy of its
   line; trips summarised by exit reason.
5. **Loading, the document and the command (`exit_verdict_load.py`, `exit_verdict_report.py`,
   `exit_verdict_markdown.py`, `exit_verdict.py`, new).**

### Out of scope (do NOT build this sprint)

- **Running EXP-022.** The planner runs it, after the fidelity verdict reads PASS.
- **Any change to S250's or S281's scripts**, or to `scripts/exp014_arms.json`.
- **Any live exit.** Nothing under `agents/` changes.
- **No `laws.md` edit, no ADR, no version bump, no `uv.lock` change.**

### The road not taken (LAW-06)

- **Generalising EXP-014's scorer.** Rejected: it backs a frozen pre-registration.
- **Excess over exposure-matched SPY as the bar.** Rejected: it rewards holding cash (DL-305).
- **One cost only.** Rejected: turnover makes the cost decisive; 10 bps is a second, weaker family.
- **A pilot inside the scored window.** Rejected: it would show results before the fidelity gate.

---

## The design decisions — made, and recorded in DL-305

1. **`dR = R(X) − R(stops)` at the same slippage**, `R = ((1 + P/100)^(252/n) − 1) × 100` from
   `calculate_performance`; `dA` beside it.
2. **One set of stationary-bootstrap draws for all twelve arms** (mean block 20, 10,000, seed 0);
   each paired difference is taken draw by draw.
3. **The family interval:** `k = B × 25 // (1000 × 5)`, `v[k]` and `v[B − 1 − k]`.
4. **Readings:** wins (lower bound > 0 and both halves > 0), split (the bound only), behind (upper
   bound < 0), indistinguishable.
5. **Verdict:** EXIT WINS at 25 bps, else EXIT WINS AT LOW COST at 10 bps, else CHAMPION HOLDS; the
   leader is the largest winning `dR`, the first in `CHALLENGERS` on a tie.
6. **Control:** each arm rebuilt in its own order scores its own `R` and `A` within 1e-6.
7. **Refusals:** a manifest that is not Appendix P's is never loaded; a missing `fills.csv`, recorded
   exits that differ, and every S250 refusal (missing files, commit, cache, sessions, SPY closes,
   history rule, dirty) give no verdict.
8. **`appendix_p`** is true only for EXP-022's experiment, start and history rule with the frozen
   bootstrap; otherwise the title says `NOT Appendix P`.
9. **Round trips:** FIFO per line; held sessions = the sell's session index less the buy's.
10. **Byte-stable output:** S250's `stable` (six decimals, sorted keys).

---

## Blast radius — measured 2026-10-16

| What | Detail |
| --- | --- |
| Files changed | new: `scripts/exp022_arms.json`; `scripts/exit_verdict.py` (79), `exit_verdict_load.py` (70), `exit_verdict_markdown.py` (146), `exit_verdict_report.py` (96), `exit_verdict_rule.py` (88), `exit_verdict_score.py` (138), `exit_verdict_stats.py` (81), `exit_verdict_trips.py` (86); new tests under `tests/` |
| Agents affected | none; the scorer imports `agents.reporter.domain.performance` (through S250's stats) unchanged |
| Contract change? | no |
| Graph vocabulary change? | no |
| New env keys / tunables | none |
| Deploy implication | none: scripts do not ship in an image |
| Rollback | revert the merge; nothing outside the repo is written. The fidelity count is untouched (no decision path changes) |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. DL-305 and EXP-022 are already recorded; read them. Do not edit either.
3. **Write the tests first** under the names and files of the Test plan, and run them on the unchanged
   tree: every one is red (each file fails to import `scripts.exit_verdict*`). Paste the output.
4. **Apply the Appendix exactly.** Change nothing else under `scripts/`.
5. **Plant the breaks** B01 to B34 (Traps), one at a time; each must turn at least one of your tests red.
6. **`make ci` green**, redirected to a file.
7. **Fill the handback sections.**

---

## Test plan

Files: `tests/test_exit_verdict_rule.py` (A1–A3), `tests/test_exit_verdict_stats.py` (A4, A5, A21),
`tests/test_exit_verdict_score.py` (A6–A12), `tests/test_exit_verdict_trips.py` (A13, A14),
`tests/test_exit_verdict_cli.py` (A15–A20), and a helper `tests/exit_verdict_fixtures.py`: the twelve
arms on one seeded SPY walk (S250's `tests/replay_verdict_fixtures.py`), each challenger its family's
champion with a planted drift added to every session's step (or one drift per half), and a writer of
arm folders as `replay_arms.py` lays them out, with two round trips in each `fills.csv`. Every test is
red on the unchanged tree.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | the committed manifest is Appendix P's | `load_manifest(exp022_arms.json)` | twelve arms in `expected_arms()` order; no `manifest_refusals`; EXP-022, 2017-01-03, rule on; `target-time10-25`'s exits; `stops-10` declares none |
| A2 | a difference reads wins, split, behind or indistinguishable | six intervals and halves | (0.1, 2) wins; a half at −0.5 or at 0 split; low 0 indistinguishable; (−2, −0.1) behind; high 0 indistinguishable |
| A3 | 🎯 the bar family decides first; the leader is the largest | ten readings, three ways | two 25 bps winners tied → EXIT WINS, leader the first in order; distinct points → the larger; only a 10 bps winner → AT LOW COST; a split → CHAMPION HOLDS, leader `None` |
| A4 | R is the annualised portfolio return | four metric sets | 10 % / 252 → 10; 21 % / 504 → 10; −50 % / 252 → −50; n = 0 → 0 |
| A5 | the interval holds 95 % over the five | 0 … 9,999, shuffled | (50, 9,949); m = 1 equals S250's `percentile_interval`; `COMPARISONS` 5 |
| A6 | 🎯 a planted gain wins; a copy differs by exactly 0 | `target-25` +0.001 a session | lower bound > 10; both halves > 0; point = R(target) − R(stops); `trail-10` point 0, interval [0, 0], champion `stops-10`; bootstrap record |
| A7 | a planted loss is behind | `time10-25` −0.001 | upper bound < −10; dA < −10; CHAMPION HOLDS |
| A8 | a gain in one half only is split | `trail-25` +0.003 then −0.0005 | bound > 0, first half > 0 > second; halves labelled `first half`, `second half` |
| A9 | a win only at 10 bps | `cool5-10` +0.001 | AT LOW COST, leader `cool5`; `cool5-25` indistinguishable |
| A10 | the control passes; a failed one refuses; it reads A too | tolerance −1; a rebuild at half the exposure | passes within 1e-6; refused by `control`, no verdict, no differences; the half-exposure rebuild fails it |
| A11 | a gap or a short arm is refused | one SPY close removed; one point dropped | `2 gap session(s)`, no control; `ValueError` naming the pairs |
| A12 | the same draws give the same result | seeds 3, 3, 4 | equal; another seed moves the interval, not the point |
| A13 | 🎯 a sell closes the oldest open buy of its line | ten fill rows | 5 buys, 4 trips, 1 stray sell, 1 open; stop −10 % held 2; target ×2 +10 % median 9; time exit held 10; buys a year 5 |
| A14 | the profile reads `fills.csv` | the rows as a file; a date outside the sessions | the same profile; `KeyError` |
| A15 | a manifest that is not Appendix P's is refused by arm | other slippage, overrides, exits; one missing; one extra | five refusals in Appendix P's order, extra last, with the reasons |
| A16 | twelve folders score and write one page | 121 sessions, `target-25` +0.001, 40 resamples | exit 0; EXIT WINS; `appendix_p` false; the title line; five sections; the stop trip row; `2017, partial`; profiles; provenance start |
| A17 | scoring twice writes the same bytes | 61 sessions | `verdict.json` and `verdict.md` byte-identical |
| A18 | a folder that misfits gives no verdict | missing `fills.csv`; exits dropped; exits on `stops-25`; an arm missing | exit 2; refused by name with the reason; `NO VERDICT` page lists it |
| A19 | a wrong manifest is not loaded; output stays out of the repo | the last arm removed; an out-root in the worktree | one refusal, no arms; `ValueError` |
| A20 | only Appendix P's manifest and bootstrap are Appendix P's | the frozen bootstrap set to the test's; a pilot manifest | frozen manifest → `appendix_p` true, title without the suffix; pilot → false |
| A21 | dR reads the return only | `stops-25`'s equity at half its exposure as `trail-25` | dR point 0 and interval [0, 0]; dA not 0 |

---

## Success factors

- [ ] On the F1 pilot's twelve real arm folders the built scorer writes `verdict.json` and
      `verdict.md` byte for byte the prototype's (planner, `s282_f1_score.py`).
- [ ] A1–A21 pass, each docstring citing its ID.
- [ ] B01–B34 each turn at least one of the builder's tests red (planner re-runs `s282_breaks.py`).
- [ ] The Appendix applied exactly: every production blob equals the prototype's.
- [ ] No existing file changed; every new module under 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage (the remote gate).

---

## Traps

🪤 **The paired difference is taken draw by draw, on one order for every arm.** Drawing an order per
arm gives two independent intervals; the copy in A6 then differs by more than 0.
🪤 **Each family pairs with its own champion.** `target-10` is compared with `stops-10`, never
`stops-25`.
🪤 **`dR`, not `dA`, decides.** An arm can hold the same equity at another exposure (A21): its `dR` is
exactly 0 while its `dA` is not.
🪤 **A manifest that is not Appendix P's is never loaded**, so its arms are never scored.
🪤 **S250's loader is reused unchanged.** Its first-arm reference makes `stops-25` the reference
because it is first in the manifest; do not reorder the manifest.
🪤 **The family interval's index is integer arithmetic**: `B × 25 // (1000 × m)`, never a float
percentile.
🪤 **Replay outputs refuse a path inside the worktree** (`refuse_worktree_out`): tests write to
`tmp_path`.
🪤 **Scripts sit outside coverage and mypy** (`pyproject.toml`, `Makefile`), so a green `make ci`
does not prove a line is reached: the tests and the breaks do.
🪤 **The breaks.** Plant each in the Appendix's code, one at a time; each must turn at least one of
your tests red. The planner re-runs them as `s282_breaks.py` against your tests alone.

| # | File | Plant |
| --- | --- | --- |
| B01 | `exit_verdict_rule.py` | a lower bound of 0 wins (`>=`) |
| B02 | `exit_verdict_rule.py` | the halves are not read |
| B03 | `exit_verdict_rule.py` | a half at 0 counts as ahead |
| B04 | `exit_verdict_rule.py` | an upper bound of 0 is behind |
| B05 | `exit_verdict_rule.py` | the 10 bps family decides first |
| B06 | `exit_verdict_rule.py` | the leader is the smallest difference |
| B07 | `exit_verdict_rule.py` | a tie goes to the last challenger |
| B08 | `exit_verdict_rule.py` | the families are listed 10 bps first |
| B09 | `exit_verdict_rule.py` | Appendix P's time exit is 5 sessions |
| B10 | `exit_verdict_stats.py` | R is the growth factor, not the return |
| B11 | `exit_verdict_stats.py` | R annualises by n / 252 |
| B12 | `exit_verdict_stats.py` | the interval ignores the family |
| B13 | `exit_verdict_stats.py` | the halves are the years |
| B14 | `exit_verdict_score.py` | each arm draws its own order |
| B15 | `exit_verdict_score.py` | the 10 bps family is paired with `stops-25` |
| B16 | `exit_verdict_score.py` | dR's interval comes from the A draws |
| B17 | `exit_verdict_score.py` | dR's point is A's |
| B18 | `exit_verdict_score.py` | a failed control is not refused |
| B19 | `exit_verdict_score.py` | a gap session is not refused |
| B20 | `exit_verdict_score.py` | unequal pair counts are not refused |
| B21 | `exit_verdict_score.py` | the control reads R only |
| B22 | `exit_verdict_trips.py` | a sell closes the newest buy |
| B23 | `exit_verdict_trips.py` | held counts the buy's session too |
| B24 | `exit_verdict_trips.py` | a year is counted in sessions, not pairs |
| B25 | `exit_verdict_trips.py` | reasons in arrival order |
| B26 | `exit_verdict_load.py` | the manifest's exits are not checked |
| B27 | `exit_verdict_load.py` | a missing `fills.csv` is not refused |
| B28 | `exit_verdict_load.py` | recorded exits are not checked |
| B29 | `exit_verdict_report.py` | any bootstrap is Appendix P's |
| B30 | `exit_verdict_report.py` | any manifest is Appendix P's |
| B31 | `exit_verdict_markdown.py` | the title never says `NOT Appendix P` |
| B32 | `exit_verdict_markdown.py` | a refusal page lists nothing by name |
| B33 | `exit_verdict.py` | a refusal exits 0 |
| B34 | `exp022_arms.json` | `cool5-25`'s cool-down is 3 runs |

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150), test files included. Split, don't grow. No `# noqa` beyond
  the `E402` pattern `scripts/exit_verdict.py` shares with `replay_verdict.py`.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- `make ci` **every step** green, **100.00 % coverage floor**, redirected to a file.
- **No version bump, no `uv.lock` change.**
- The worktree has **no `.env`** and no replay cache; every proof here runs on fixtures.

---

## Sequencing after merge (the planner's)

1. Review: production blobs equal `prototype_blobs.txt`; the planner's tests on the built tree; the
   breaks against the builder's tests alone; CodeQL set-diff against the S281 branch.
2. F1 from the built tree: `s282_f1_score.py` on the pilot's twelve arm folders (OneDrive
   `wq92s282-2026-10-16/pilot/`) must equal `f1_proto/`.
3. `make gate-ran` from `../ta-s282`; fast-forward `main`; no tag (no bump).
4. No deploy. EXP-022 then waits for the fidelity verdict's PASS; its twelve arms run from one clean
   checkout whose decision paths equal the PASS commit's.

---

## Handover — paste this to Codex

```text
You are building Sprint 282 in the worktree ../ta-s282, on the branch
sprint-282-each-exit-arm-is-scored-against-stops-only-on-the-same-days. Never work on main. The
worktree and its venv are ready; never run a bare `uv sync` (it needs the network and you have none).

Read docs/sprints/sprint-282-each-exit-arm-is-scored-against-stops-only-on-the-same-days.md, whole,
before anything else. It is the spec, and its bottom sections are your handback. The Appendix holds the
production code, which you apply exactly. Your work is the tests and the evidence.

In order:
1. Read agents/reporter/laws/laws.md and test-plan.md, docs/laws/conventions.md and
   docs/laws/drift-register.md, DL-305 in docs/design-log.md, and
   docs/research/experiments/EXP-022-does-an-exit-besides-the-stop-make-the-book-earn-more.md. Fill the
   Law reading record in the spec BEFORE any code. The law-cycle answer is No.
2. Write tests/exit_verdict_fixtures.py and the tests A1 to A21 under the files the Test plan names,
   each docstring citing its ID (S282-A<n>). Run them on the unchanged tree and paste the output into
   the Closeout: every one is red, by import.
3. Apply the Appendix exactly (nine new files under scripts/). Change no existing file.
4. Plant the breaks B01 to B34 one at a time (the table in the spec's Traps). Each must turn at least
   one of your tests red; restore each before the next. Record each in the Closeout.
5. No version bump, no uv.lock change. Run make ci redirected to a file and read the file. If the
   dependency audit is the only step that fails for want of network, say so; the planner runs it.
6. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md, docs/design-log.md, docs/work-queue.md or EXP-022.

DO NOT: reach the network; change anything under kernel/, contracts/, agents/, orchestration/ or
surfaces/; change any existing file under scripts/ or tests/ (S250's replay_verdict_* and S281's
replay_* are reused as they are); bump the version; use noqa beyond the Appendix's E402 lines; let any
module, test files included, reach 200 lines; measure make ci through a pipe; write output inside the
worktree.

Traps: one bootstrap order for every arm, differences taken draw by draw; each family pairs with its
own stops arm; dR decides, not dA (A21); scripts are outside coverage, so only the tests and the breaks
prove a line is reached; ruff format grows files, measure after formatting.

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
| Statistic and scoring | *fill at handback* | *fill* | *fill* |
| Rule, manifest and loader | *fill at handback* | *fill* | *fill* |
| Trips, document and command | *fill at handback* | *fill* | *fill* |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *fill*

**Contradictions found between a law and this spec:** *fill*

**Laws found silent where a decision was needed:** *fill*

**Clauses that were ⬜ and are now proven:** *fill*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1–A21 | *fill, one row each* | | | |

---

## Closeout — evidence

*Fill at handback: the tree the proofs ran in and whether a `.env` was present; the unchanged tree's
red run; the Appendix applied (blob ids); each break's result; `make ci`'s file and exit code.*

---

## Return notes

*Fill at handback.*

---

## Appendix — the change, measured on the planner's prototype

Apply with `git apply` from the worktree root. Nine new files; no existing file changes.

```diff
diff --git a/scripts/exit_verdict.py b/scripts/exit_verdict.py
new file mode 100644
index 00000000..00ace369
--- /dev/null
+++ b/scripts/exit_verdict.py
@@ -0,0 +1,79 @@
+"""Score EXP-022's exit arms into a verdict, by Appendix P (S282).
+
+Agent: tooling
+Role: load the twelve arms, refuse what does not belong together, score, profile
+      each arm's exits, and write the verdict.
+External I/O: reads arm folders; writes verdict.json and verdict.md outside the repo.
+
+    uv run python scripts/exit_verdict.py score --out-root <dir>
+
+Exit 0 with a verdict, 2 with a refusal (both write the two files).
+"""
+
+from __future__ import annotations
+
+import argparse
+import sys
+from pathlib import Path
+from typing import Any
+
+_ROOT = Path(__file__).resolve().parents[1]
+if str(_ROOT) not in sys.path:
+    sys.path.insert(0, str(_ROOT))
+
+from scripts.exit_verdict_load import FILLS, load_exit_arms  # noqa: E402
+from scripts.exit_verdict_report import verdict_document, write_verdict  # noqa: E402
+from scripts.exit_verdict_score import score_exit_arms  # noqa: E402
+from scripts.exit_verdict_trips import exit_profile  # noqa: E402
+from scripts.replay_arms import load_manifest  # noqa: E402
+from scripts.replay_outputs import refuse_worktree_out  # noqa: E402
+from scripts.replay_verdict_score import RESAMPLES  # noqa: E402
+
+MANIFEST = Path(__file__).with_name("exp022_arms.json")
+REFUSED = 2
+
+
+def score_out_root(
+    out_root: Path, manifest_path: Path = MANIFEST, *, resamples: int = RESAMPLES
+) -> dict[str, Any]:
+    """Load, check, score, profile and write; return the document written."""
+    out_root = refuse_worktree_out(out_root)
+    manifest = load_manifest(manifest_path)
+    loaded = load_exit_arms(out_root, manifest)
+    scored = None
+    profiles: dict[str, dict[str, Any]] = {}
+    if not loaded.refusals:
+        scored = score_exit_arms(loaded.arms, resamples=resamples)
+        profiles = {
+            name: exit_profile(
+                out_root / name / FILLS, [point[0] for point in arm.points]
+            )
+            for name, arm in loaded.arms.items()
+        }
+    document = verdict_document(manifest, loaded, scored, profiles)
+    write_verdict(out_root, document)
+    return document
+
+
+def main(argv: list[str]) -> int:
+    parser = argparse.ArgumentParser(description="Score EXP-022's exit arms.")
+    parser.add_argument("command", choices=("score",))
+    parser.add_argument("--out-root", type=Path, required=True)
+    parser.add_argument("--manifest", type=Path, default=MANIFEST)
+    parser.add_argument(
+        "--resamples",
+        type=int,
+        default=RESAMPLES,
+        help="Appendix P's 10,000; anything else is marked as not Appendix P",
+    )
+    args = parser.parse_args(argv)
+    document = score_out_root(args.out_root, args.manifest, resamples=args.resamples)
+    page = (args.out_root / "verdict.md").read_text(encoding="utf-8")
+    print(page.splitlines()[0])
+    for item in document["refusals"]:
+        print(f"refused: {item['arm']}: {item['reason']}")
+    return 0 if document["verdict"] else REFUSED
+
+
+if __name__ == "__main__":
+    raise SystemExit(main(sys.argv[1:]))
diff --git a/scripts/exit_verdict_load.py b/scripts/exit_verdict_load.py
new file mode 100644
index 00000000..11c32551
--- /dev/null
+++ b/scripts/exit_verdict_load.py
@@ -0,0 +1,70 @@
+"""Load EXP-022's arm folders and refuse what Appendix P does not name (S282).
+
+Agent: tooling
+Role: check the manifest against Appendix P's twelve arms, load them through S250's
+      loader, and refuse an arm whose fills are missing or whose exits differ.
+External I/O: reads arm folders under the out-root.
+"""
+
+from __future__ import annotations
+
+from typing import TYPE_CHECKING
+
+from scripts.exit_verdict_rule import FAMILIES, POLICIES, arm_name
+from scripts.replay_verdict_load import LoadedArms, load_arms
+
+if TYPE_CHECKING:
+    from pathlib import Path
+
+    from scripts.replay_arms import Manifest
+
+FILLS = "fills.csv"
+
+
+def load_exit_arms(out_root: Path, manifest: Manifest) -> LoadedArms:
+    """Every Appendix P arm from `<out-root>/<arm>/`, refused by name if it misfits."""
+    refusals = manifest_refusals(manifest)
+    if refusals:  # a manifest Appendix P does not name is never loaded
+        return LoadedArms(refusals=refusals)
+    loaded = load_arms(out_root, manifest)
+    for spec in manifest.arms:
+        record = loaded.records.get(spec.name)
+        if record is None:
+            continue
+        if not (out_root / spec.name / FILLS).is_file():
+            loaded.refusals.append(_refuse(spec.name, f"missing {FILLS}"))
+        told = record.get("exits")
+        want = spec.exits.as_dict() if spec.exits.declared else None
+        if told != want:
+            reason = f"exits is {told!r}; the manifest says {want!r}"
+            loaded.refusals.append(_refuse(spec.name, reason))
+    return loaded
+
+
+def manifest_refusals(manifest: Manifest) -> list[dict[str, str]]:
+    """Each Appendix P arm the manifest omits or sets otherwise, and each extra."""
+    specs = {spec.name: spec for spec in manifest.arms}
+    refusals: list[dict[str, str]] = []
+    for bps in FAMILIES:
+        for stem, policy in POLICIES.items():
+            name = arm_name(stem, bps)
+            spec = specs.pop(name, None)
+            if spec is None:
+                reason = "Appendix P names it; the manifest does not"
+                refusals.append(_refuse(name, reason))
+                continue
+            if (spec.slippage_bps, spec.overrides, spec.exits) != (bps, (), policy):
+                reason = (
+                    f"the manifest gives it {spec.slippage_bps} bps, overrides "
+                    f"{list(spec.overrides)}, exits {spec.exits.as_dict()}; "
+                    f"Appendix P {bps} bps, no overrides, exits {policy.as_dict()}"
+                )
+                refusals.append(_refuse(name, reason))
+    refusals.extend(
+        _refuse(name, "the manifest names it; Appendix P does not") for name in specs
+    )
+    return refusals
+
+
+def _refuse(arm: str, reason: str) -> dict[str, str]:
+    return {"arm": arm, "reason": reason}
diff --git a/scripts/exit_verdict_markdown.py b/scripts/exit_verdict_markdown.py
new file mode 100644
index 00000000..4cf1f88f
--- /dev/null
+++ b/scripts/exit_verdict_markdown.py
@@ -0,0 +1,146 @@
+"""Render EXP-022's verdict document as one page of Markdown (S282).
+
+Agent: tooling
+Role: the verdict and each exit arm's paired difference first; then the arms, their
+      exits, the 25 bps years, the control and provenance.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from typing import Any
+
+from scripts.exit_verdict_rule import BAR_BPS, CHALLENGERS, CHAMPION, arm_name
+
+R_KEY = "annualised_return_pts"
+A_KEY = "annualised_excess_pts"
+_DIFF_HEADER = (
+    "| Arm | dR (pts/yr) | Interval | First half | Second half "
+    "| dA (pts/yr) | dA interval | Reading |"
+)
+_ARM_KEYS = ("portfolio_return_pct", "average_exposure_pct", "max_drawdown_pct")
+_ARM_HEADER = (
+    "| Arm | Slippage (bps) | R (pts/yr) | A (pts/yr) | Portfolio % "
+    "| Avg exposure % | Max drawdown % | Buys a year |"
+)
+
+
+def render_markdown(document: dict[str, Any]) -> str:
+    """The page: a refusal replaces everything after the title."""
+    lines = [f"# {document['experiment']} verdict: {_title(document)}", ""]
+    if document["refusals"]:
+        lines += ["The scorer gives no verdict:", ""]
+        lines += [
+            f"- **{item['arm']}**: {item['reason']}" for item in document["refusals"]
+        ]
+        return "\n".join([*lines, ""])
+    boot = document["bootstrap"]
+    lines += [
+        "Each exit arm against stops-only at its own slippage: dR is the difference "
+        f"in annualised return, each interval 95 % over a family's "
+        f"{boot['comparisons']} challengers; {boot['pairs']:,} session pairs, "
+        f"{boot['resamples']:,} resamples, mean block {boot['mean_block']}, "
+        f"seed {boot['seed']}.",
+        "",
+        "## Paired differences from stops-only",
+        "",
+        _DIFF_HEADER,
+        "| --- | ---: | --- | ---: | ---: | ---: | --- | --- |",
+    ]
+    readings = document["verdict"]["readings"]
+    for name, item in document["differences"].items():
+        excess = item["excess"]
+        cells = (
+            name,
+            _pts(item["point"]),
+            _interval(item["interval"]),
+            *(_pts(gap) for gap in item["halves"]),
+            _pts(excess["point"]),
+            _interval(excess["interval"]),
+            readings[name],
+        )
+        lines.append("| " + " | ".join(cells) + " |")
+    lines += ["", "## Arms", "", _ARM_HEADER, "| --- |" + " ---: |" * 7]
+    lines += [_arm_row(name, arm) for name, arm in document["arms"].items()]
+    lines += _exits(document["arms"])
+    lines += _years(document)
+    control = document["control"]
+    lines += [
+        "",
+        "## Control",
+        "",
+        f"Each arm rebuilt in its own order scores its own R and A within "
+        f"{control['tolerance_pts']:g}: largest deviation "
+        f"{control['max_deviation_pts']:.3g}, "
+        f"{'PASS' if control['passed'] else 'FAIL'}.",
+    ]
+    lines += _provenance(document["provenance"])
+    return "\n".join([*lines, ""])
+
+
+def _title(document: dict[str, Any]) -> str:
+    verdict = document["verdict"]
+    if verdict is None:
+        return "NO VERDICT"
+    title = verdict["verdict"]
+    if verdict["leader"]:
+        title += f" (leader: {verdict['leader']}; {', '.join(verdict['winners'])})"
+    return title if document["appendix_p"] else f"{title}, NOT Appendix P"
+
+
+def _arm_row(name: str, arm: dict[str, Any]) -> str:
+    whole = arm["whole"]
+    cells = [name, str(arm["slippage_bps"]), _pts(whole[R_KEY]), _pts(whole[A_KEY])]
+    cells += [f"{whole[key]:.2f}" for key in _ARM_KEYS]
+    cells.append(f"{arm['profile']['buys_per_year']:.1f}")
+    return "| " + " | ".join(cells) + " |"
+
+
+def _exits(arms: dict[str, Any]) -> list[str]:
+    lines = ["", "## Exits (round trips by the reason that closed them)", ""]
+    lines += ["| Arm | Reason | Trips | Gains % | Mean return % | Median sessions |"]
+    lines += ["| --- | --- | ---: | ---: | ---: | ---: |"]
+    for name, arm in arms.items():
+        for reason, item in arm["profile"]["exits"].items():
+            lines.append(
+                f"| {name} | {reason} | {item['count']} | {item['gain_share_pct']:.1f} "
+                f"| {item['mean_return_pct']:+.2f} | {item['median_held_sessions']:g} |"
+            )
+    return lines
+
+
+def _years(document: dict[str, Any]) -> list[str]:
+    names = [arm_name(stem, BAR_BPS) for stem in CHALLENGERS]
+    differences = document["differences"]
+    lines = ["", f"## Years (dR at {BAR_BPS} bps, pts a year)", ""]
+    lines += ["| Year | " + " | ".join(names) + " |"]
+    lines += ["| --- |" + " ---: |" * len(names)]
+    rows = document["arms"][arm_name(CHAMPION, BAR_BPS)]["years"]
+    for index, row in enumerate(rows):
+        label = row["label"] + (", partial" if row["partial"] else "")
+        cells = [_pts(differences[name]["years"][index]) for name in names]
+        lines.append(f"| {label} | " + " | ".join(cells) + " |")
+    return lines
+
+
+def _provenance(provenance: dict[str, Any]) -> list[str]:
+    cache = ", ".join(f"`{key}` {value}" for key, value in provenance["cache"].items())
+    rule = "on" if provenance["require_history"] else "off"
+    return [
+        "",
+        "## Provenance",
+        "",
+        f"- Commit: `{provenance['commit']}`",
+        f"- Sessions: {provenance['sessions']}, {provenance['first_session']} → "
+        f"{provenance['last_session']}; start {provenance['start']}; "
+        f"history rule {rule}",
+        f"- Cache (SHA-256 prefix): {cache}",
+    ]
+
+
+def _pts(value: float) -> str:
+    return f"{value:+.2f}"
+
+
+def _interval(bounds: list[float]) -> str:
+    return f"[{bounds[0]:+.2f}, {bounds[1]:+.2f}]"
diff --git a/scripts/exit_verdict_report.py b/scripts/exit_verdict_report.py
new file mode 100644
index 00000000..f9057e23
--- /dev/null
+++ b/scripts/exit_verdict_report.py
@@ -0,0 +1,96 @@
+"""Write EXP-022's verdict.json and one-page verdict.md, byte-stable (S282).
+
+Agent: tooling
+Role: assemble the scored arms, their exit profiles and provenance into a sorted,
+      rounded document, and mark whether it ran exactly as Appendix P froze it.
+External I/O: writes verdict.json and verdict.md under the out-root.
+"""
+
+from __future__ import annotations
+
+import json
+from typing import TYPE_CHECKING, Any, cast
+
+from scripts.exit_verdict_markdown import render_markdown
+from scripts.exit_verdict_rule import BAR_BPS, CHAMPION, EXPERIMENT, START, arm_name
+from scripts.replay_verdict_report import HISTORY_COUNTER, stable
+from scripts.replay_verdict_score import MEAN_BLOCK, RESAMPLES, SEED
+
+if TYPE_CHECKING:
+    from pathlib import Path
+
+    from scripts.replay_arms import Manifest
+    from scripts.replay_verdict_load import LoadedArms
+
+FROZEN_BOOTSTRAP = (RESAMPLES, MEAN_BLOCK, SEED)
+
+
+def verdict_document(
+    manifest: Manifest,
+    loaded: LoadedArms,
+    scored: dict[str, Any] | None,
+    profiles: dict[str, dict[str, Any]],
+) -> dict[str, Any]:
+    """The verdict or the refusals, every arm's numbers and exits, and provenance."""
+    refusals = [*loaded.refusals, *(scored["refusals"] if scored else [])]
+    bootstrap = scored["bootstrap"] if scored else {}
+    specs = {spec.name: spec for spec in manifest.arms}
+    arms = {
+        name: {
+            "exits": specs[name].exits.as_dict(),
+            "profile": profiles.get(name),
+            "slippage_bps": specs[name].slippage_bps,
+            **numbers,
+        }
+        for name, numbers in (scored["arms"] if scored else {}).items()
+    }
+    told = tuple(bootstrap.get(key) for key in ("resamples", "mean_block", "seed"))
+    frozen = (manifest.experiment, manifest.start, manifest.require_history) == (
+        EXPERIMENT,
+        START,
+        True,
+    )
+    return cast(
+        "dict[str, Any]",
+        stable(
+            {
+                "absent_inputs": loaded.absent_inputs,
+                "appendix_p": frozen and told == FROZEN_BOOTSTRAP,
+                "arms": arms,
+                "bootstrap": bootstrap,
+                "control": scored["control"] if scored else None,
+                "differences": scored["differences"] if scored else {},
+                "experiment": manifest.experiment,
+                "provenance": _provenance(loaded),
+                "refusals": refusals,
+                "verdict": None if refusals or not scored else scored["verdict"],
+            }
+        ),
+    )
+
+
+def write_verdict(out_root: Path, document: dict[str, Any]) -> None:
+    """verdict.json (sorted keys, 6 decimals) and verdict.md beside the arms."""
+    out_root.mkdir(parents=True, exist_ok=True)
+    (out_root / "verdict.json").write_text(
+        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
+    )
+    (out_root / "verdict.md").write_text(render_markdown(document), encoding="utf-8")
+
+
+def _provenance(loaded: LoadedArms) -> dict[str, Any]:
+    champion = arm_name(CHAMPION, BAR_BPS)
+    record = loaded.records.get(champion) or next(iter(loaded.records.values()), {})
+    return {
+        "cache": record.get("cache", {}),
+        "commit": record.get("commit"),
+        "first_session": record.get("first_session"),
+        "last_session": record.get("last_session"),
+        "require_history": record.get("require_history"),
+        "sessions": record.get("sessions"),
+        "start": record.get("start"),
+        "withheld_member_sessions": {
+            name: counters.get(HISTORY_COUNTER)
+            for name, counters in loaded.absent_inputs.items()
+        },
+    }
diff --git a/scripts/exit_verdict_rule.py b/scripts/exit_verdict_rule.py
new file mode 100644
index 00000000..3c4aed36
--- /dev/null
+++ b/scripts/exit_verdict_rule.py
@@ -0,0 +1,88 @@
+"""EXP-022 Appendix P's arms and verdict rule, applied by code (S282).
+
+Agent: tooling
+Role: name the twelve arms and their exits; read each exit arm's paired difference
+      from stops-only; decide EXIT WINS, EXIT WINS AT LOW COST or CHAMPION HOLDS.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from datetime import date
+from typing import TYPE_CHECKING, Any
+
+from scripts.replay_exits import STOPS_ONLY, ExitPolicy
+
+if TYPE_CHECKING:
+    from collections.abc import Mapping
+
+EXPERIMENT = "EXP-022"
+START = date(2017, 1, 3)
+CHAMPION = "stops"
+POLICIES = {
+    CHAMPION: STOPS_ONLY,
+    "target": ExitPolicy(take_profit=True),
+    "time10": ExitPolicy(time_exit_sessions=10),
+    "trail": ExitPolicy(trailing_stop=True),
+    "target-time10": ExitPolicy(take_profit=True, time_exit_sessions=10),
+    "cool5": ExitPolicy(reentry_cooldown_sessions=5),
+}
+CHALLENGERS = ("target", "time10", "trail", "target-time10", "cool5")
+BAR_BPS = 25
+LOW_COST_BPS = 10
+FAMILIES = (BAR_BPS, LOW_COST_BPS)
+EXIT_WINS = "EXIT WINS"
+EXIT_WINS_AT_LOW_COST = "EXIT WINS AT LOW COST"
+CHAMPION_HOLDS = "CHAMPION HOLDS"
+WINS = "wins"
+SPLIT = "split"
+BEHIND = "behind"
+INDISTINGUISHABLE = "indistinguishable"
+
+
+def arm_name(stem: str, bps: int) -> str:
+    """The manifest's name for an arm: `<stem>-<bps>`."""
+    return f"{stem}-{bps}"
+
+
+def expected_arms() -> tuple[str, ...]:
+    """Every arm Appendix P names, the 25 bps family first, the champion first."""
+    return tuple(arm_name(stem, bps) for bps in FAMILIES for stem in POLICIES)
+
+
+def reading(difference: Mapping[str, Any]) -> str:
+    """wins: lower bound > 0 and each half's point > 0; split: the bound alone.
+
+    behind: the upper bound < 0; indistinguishable: anything else.
+    """
+    low, high = difference["interval"]
+    if low > 0:
+        halves_ahead = all(point > 0 for point in difference["halves"])
+        return WINS if halves_ahead else SPLIT
+    return BEHIND if high < 0 else INDISTINGUISHABLE
+
+
+def decide(differences: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
+    """EXIT WINS at 25 bps; else EXIT WINS AT LOW COST at 10 bps; else CHAMPION HOLDS.
+
+    The leader is the winning challenger with the largest point difference, the
+    first in CHALLENGERS' order on a tie.
+    """
+    readings = {name: reading(item) for name, item in differences.items()}
+    for bps, verdict in ((BAR_BPS, EXIT_WINS), (LOW_COST_BPS, EXIT_WINS_AT_LOW_COST)):
+        winners = [s for s in CHALLENGERS if readings[arm_name(s, bps)] == WINS]
+        if winners:
+            points = {s: differences[arm_name(s, bps)]["point"] for s in winners}
+            leader = max(winners, key=points.__getitem__)
+            return {
+                "verdict": verdict,
+                "winners": winners,
+                "leader": leader,
+                "readings": readings,
+            }
+    return {
+        "verdict": CHAMPION_HOLDS,
+        "winners": [],
+        "leader": None,
+        "readings": readings,
+    }
diff --git a/scripts/exit_verdict_score.py b/scripts/exit_verdict_score.py
new file mode 100644
index 00000000..cbf98995
--- /dev/null
+++ b/scripts/exit_verdict_score.py
@@ -0,0 +1,138 @@
+"""Score EXP-022's arms: each exit arm against stops-only on shared draws (S282).
+
+Agent: tooling
+Role: every arm's blocks, the rebuild control, then each challenger's paired
+      difference with its family interval, then the verdict.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from typing import TYPE_CHECKING, Any
+
+from scripts.exit_verdict_rule import CHALLENGERS, CHAMPION, FAMILIES, arm_name, decide
+from scripts.exit_verdict_stats import (
+    A_KEY,
+    COMPARISONS,
+    R_KEY,
+    family_interval,
+    resampled,
+    windows,
+)
+from scripts.replay_verdict_score import MEAN_BLOCK, RESAMPLES, SEED
+from scripts.replay_verdict_stats import arm_pairs, seeded, stationary_draws
+
+if TYPE_CHECKING:
+    from collections.abc import Mapping, Sequence
+
+    from scripts.replay_verdict_score import ArmSeries
+    from scripts.replay_verdict_stats import Pair
+
+CONTROL_TOLERANCE_PTS = 1e-6
+Draws = tuple[list[float], list[float]]  # R, then A, one value per resample
+
+
+def score_exit_arms(
+    arms: Mapping[str, ArmSeries],
+    *,
+    resamples: int = RESAMPLES,
+    mean_block: int = MEAN_BLOCK,
+    seed: int = SEED,
+) -> dict[str, Any]:
+    """Every arm's blocks, the control, each challenger's difference, the verdict."""
+    scored = {name: windows(arm) for name, arm in arms.items()}
+    refusals = [
+        {"arm": name, "reason": f"{gaps:.0f} gap session(s) in the scored window"}
+        for name in arms
+        if (gaps := scored[name]["whole"]["performance_gap_sessions"]) > 0
+    ]
+    result: dict[str, Any] = {
+        "arms": scored,
+        "bootstrap": {},
+        "control": None,
+        "differences": {},
+        "refusals": refusals,
+        "verdict": None,
+    }
+    if refusals:  # a gap has no pair to resample; nothing further is scored
+        return result
+    pairs = {name: arm_pairs(arm.points, arm.closes) for name, arm in arms.items()}
+    count = len(next(iter(pairs.values())))
+    if any(len(items) != count for items in pairs.values()):
+        raise ValueError("arms differ in their number of session pairs")
+    result["control"] = control = _control(scored, pairs, count)
+    if not control["passed"]:
+        refusals.append({"arm": "control", "reason": _control_reason(control)})
+        return result
+    draws: dict[str, Draws] = {name: ([], []) for name in arms}
+    rng = seeded(seed)
+    for _ in range(resamples):
+        order = stationary_draws(count, mean_block, rng)  # one draw for every arm
+        for name in arms:
+            ret, excess = resampled(pairs[name], order)
+            draws[name][0].append(ret)
+            draws[name][1].append(excess)
+    differences = {
+        arm_name(stem, bps): _difference(scored, draws, stem, bps)
+        for bps in FAMILIES
+        for stem in CHALLENGERS
+    }
+    result["bootstrap"] = {
+        "comparisons": COMPARISONS,
+        "mean_block": mean_block,
+        "pairs": count,
+        "resamples": resamples,
+        "seed": seed,
+    }
+    result["differences"] = differences
+    result["verdict"] = decide(differences)
+    return result
+
+
+def _difference(
+    scored: Mapping[str, Any], draws: Mapping[str, Draws], stem: str, bps: int
+) -> dict[str, Any]:
+    name, champion = arm_name(stem, bps), arm_name(CHAMPION, bps)
+    arm, base = scored[name], scored[champion]
+    paired = [
+        [a - b for a, b in zip(mine, theirs, strict=True)]
+        for mine, theirs in zip(draws[name], draws[champion], strict=True)
+    ]
+    return {
+        "champion": champion,
+        "point": arm["whole"][R_KEY] - base["whole"][R_KEY],
+        "interval": list(family_interval(paired[0])),
+        "halves": _gaps(arm["halves"], base["halves"]),
+        "years": _gaps(arm["years"], base["years"]),
+        "excess": {
+            "point": arm["whole"][A_KEY] - base["whole"][A_KEY],
+            "interval": list(family_interval(paired[1])),
+        },
+    }
+
+
+def _gaps(rows: Sequence[dict[str, Any]], base: Sequence[Any]) -> list[float]:
+    return [a[R_KEY] - b[R_KEY] for a, b in zip(rows, base, strict=True)]
+
+
+def _control(
+    scored: Mapping[str, Any], pairs: Mapping[str, Sequence[Pair]], count: int
+) -> dict[str, Any]:
+    """Each arm rebuilt in its own order must score its own whole-window R and A."""
+    deviation = 0.0
+    for name, items in pairs.items():
+        ret, excess = resampled(items, range(count))
+        whole = scored[name]["whole"]
+        deviation = max(deviation, abs(ret - whole[R_KEY]), abs(excess - whole[A_KEY]))
+    return {
+        "max_deviation_pts": deviation,
+        "passed": deviation <= CONTROL_TOLERANCE_PTS,
+        "tolerance_pts": CONTROL_TOLERANCE_PTS,
+    }
+
+
+def _control_reason(control: Mapping[str, Any]) -> str:
+    return (
+        f"an arm rebuilt in its own order scored {control['max_deviation_pts']:.6g} "
+        f"pts from its own R or A; it must be within {control['tolerance_pts']:g}"
+    )
diff --git a/scripts/exit_verdict_stats.py b/scripts/exit_verdict_stats.py
new file mode 100644
index 00000000..22c3c4c6
--- /dev/null
+++ b/scripts/exit_verdict_stats.py
@@ -0,0 +1,81 @@
+"""EXP-022's statistic, its family interval and an arm's scored blocks (S282).
+
+Agent: tooling
+Role: annualised return and excess for a window or a rebuilt series, every arm's
+      whole window, years and halves, and the interval over a family's challengers.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from typing import TYPE_CHECKING, Any
+
+from scripts.exit_verdict_rule import CHALLENGERS
+from scripts.replay_verdict_stats import (
+    SESSIONS_PER_YEAR,
+    annualised_excess,
+    performance,
+    rebuild,
+)
+from scripts.replay_verdict_windows import Window, half_windows, year_windows
+
+if TYPE_CHECKING:
+    from collections.abc import Iterable, Mapping, Sequence
+    from datetime import date
+
+    from scripts.replay_verdict_score import ArmSeries
+    from scripts.replay_verdict_stats import Pair
+
+R_KEY = "annualised_return_pts"
+A_KEY = "annualised_excess_pts"
+COMPARISONS = len(CHALLENGERS)  # Bonferroni over one family's challengers
+_TAIL_PER_MILLE = 25  # 2.5 % a side before the family adjustment
+_PER_MILLE = 1000
+
+
+def annualised_return(metrics: Mapping[str, float]) -> float:
+    """R = ((1 + P/100)^(252/n) - 1) x 100 from the reporter's metrics."""
+    sessions = metrics["performance_sessions"]
+    if sessions <= 0:
+        return 0.0
+    growth = 1.0 + metrics["portfolio_return_pct"] / 100.0
+    return (growth ** (SESSIONS_PER_YEAR / sessions) - 1.0) * 100.0
+
+
+def family_interval(
+    values: Sequence[float], comparisons: int = COMPARISONS
+) -> tuple[float, float]:
+    """v[k] and v[B - 1 - k] with k = B x 25 // (1000 x comparisons)."""
+    ordered = sorted(values)
+    k = len(ordered) * _TAIL_PER_MILLE // (_PER_MILLE * comparisons)
+    return ordered[k], ordered[len(ordered) - 1 - k]
+
+
+def windows(arm: ArmSeries) -> dict[str, Any]:
+    """The arm's whole window, its calendar years and its two halves."""
+    whole = Window("whole", False, tuple(sorted(arm.points)))
+    return {
+        "whole": _row(whole, arm.closes),
+        "years": [_row(window, arm.closes) for window in year_windows(arm.points)],
+        "halves": [_row(window, arm.closes) for window in half_windows(arm.points)],
+    }
+
+
+def resampled(pairs: Sequence[Pair], order: Iterable[int]) -> tuple[float, float]:
+    """R and A of the series rebuilt from `pairs` taken in `order`."""
+    points, closes = rebuild(pairs, order)
+    metrics = performance(points, closes)
+    return annualised_return(metrics), annualised_excess(metrics)
+
+
+def _row(window: Window, closes: Mapping[date, float]) -> dict[str, Any]:
+    metrics = performance(window.points, closes)
+    return {
+        "label": window.label,
+        "first": window.points[0][0].isoformat(),
+        "last": window.points[-1][0].isoformat(),
+        "partial": window.partial,
+        **metrics,
+        R_KEY: annualised_return(metrics),
+        A_KEY: annualised_excess(metrics),
+    }
diff --git a/scripts/exit_verdict_trips.py b/scripts/exit_verdict_trips.py
new file mode 100644
index 00000000..6b759e0b
--- /dev/null
+++ b/scripts/exit_verdict_trips.py
@@ -0,0 +1,86 @@
+"""What an EXP-022 arm's exits did: round trips by the reason that closed them (S282).
+
+Agent: tooling
+Role: pair each sell in an arm's fills.csv with the oldest open buy of its line, and
+      summarise the trips by exit reason. Reported beside the verdict, never in it.
+External I/O: reads one arm's fills.csv.
+"""
+
+from __future__ import annotations
+
+import csv
+from collections import defaultdict, deque
+from dataclasses import dataclass
+from datetime import date
+from statistics import median
+from typing import TYPE_CHECKING, Any
+
+from scripts.replay_verdict_stats import SESSIONS_PER_YEAR
+
+if TYPE_CHECKING:
+    from collections.abc import Sequence
+    from pathlib import Path
+
+_PERCENT = 100.0
+
+
+@dataclass(frozen=True)
+class Trip:
+    """One buy and the sell that closed it."""
+
+    reason: str
+    held_sessions: int
+    return_pct: float
+
+
+def exit_profile(fills_csv: Path, sessions: Sequence[date]) -> dict[str, Any]:
+    """Buys, buys a year, trips by exit reason, lines open at the end, stray sells."""
+    with fills_csv.open(encoding="utf-8", newline="") as handle:
+        rows = list(csv.DictReader(handle))
+    return profile_of(rows, sessions)
+
+
+def profile_of(
+    rows: Sequence[dict[str, str]], sessions: Sequence[date]
+) -> dict[str, Any]:
+    """The profile of fill rows in their file order; each fill's date is a session."""
+    index = {day: position for position, day in enumerate(sessions)}
+    opened: dict[str, deque[tuple[int, int]]] = defaultdict(deque)
+    trips: list[Trip] = []
+    buys = unmatched = 0
+    for row in rows:
+        session = index[date.fromisoformat(row["date"])]
+        price = int(row["price_cents"])
+        if row["side"] == "buy":
+            buys += 1
+            opened[row["line"]].append((session, price))
+            continue
+        queue = opened.get(row["line"])
+        if not queue:
+            unmatched += 1
+            continue
+        start, cost = queue.popleft()
+        gain = (price / cost - 1.0) * _PERCENT
+        trips.append(Trip(row["reason"], session - start, gain))
+    years = max(len(sessions) - 1, 1) / SESSIONS_PER_YEAR
+    by_reason: dict[str, list[Trip]] = defaultdict(list)
+    for trip in trips:
+        by_reason[trip.reason].append(trip)
+    return {
+        "buys": buys,
+        "buys_per_year": buys / years,
+        "exits": {reason: _summary(by_reason[reason]) for reason in sorted(by_reason)},
+        "open_at_end": sum(len(queue) for queue in opened.values()),
+        "trips": len(trips),
+        "unmatched_sells": unmatched,
+    }
+
+
+def _summary(trips: Sequence[Trip]) -> dict[str, Any]:
+    gains = sum(1 for trip in trips if trip.return_pct > 0)
+    return {
+        "count": len(trips),
+        "gain_share_pct": gains / len(trips) * _PERCENT,
+        "mean_return_pct": sum(trip.return_pct for trip in trips) / len(trips),
+        "median_held_sessions": float(median(trip.held_sessions for trip in trips)),
+    }
diff --git a/scripts/exp022_arms.json b/scripts/exp022_arms.json
new file mode 100644
index 00000000..da8a33be
--- /dev/null
+++ b/scripts/exp022_arms.json
@@ -0,0 +1,99 @@
+{
+  "arms": [
+    {
+      "name": "stops-25",
+      "overrides": [],
+      "slippage_bps": 25
+    },
+    {
+      "exits": {
+        "take_profit": true
+      },
+      "name": "target-25",
+      "overrides": [],
+      "slippage_bps": 25
+    },
+    {
+      "exits": {
+        "time_exit_sessions": 10
+      },
+      "name": "time10-25",
+      "overrides": [],
+      "slippage_bps": 25
+    },
+    {
+      "exits": {
+        "trailing_stop": true
+      },
+      "name": "trail-25",
+      "overrides": [],
+      "slippage_bps": 25
+    },
+    {
+      "exits": {
+        "take_profit": true,
+        "time_exit_sessions": 10
+      },
+      "name": "target-time10-25",
+      "overrides": [],
+      "slippage_bps": 25
+    },
+    {
+      "exits": {
+        "reentry_cooldown_sessions": 5
+      },
+      "name": "cool5-25",
+      "overrides": [],
+      "slippage_bps": 25
+    },
+    {
+      "name": "stops-10",
+      "overrides": [],
+      "slippage_bps": 10
+    },
+    {
+      "exits": {
+        "take_profit": true
+      },
+      "name": "target-10",
+      "overrides": [],
+      "slippage_bps": 10
+    },
+    {
+      "exits": {
+        "time_exit_sessions": 10
+      },
+      "name": "time10-10",
+      "overrides": [],
+      "slippage_bps": 10
+    },
+    {
+      "exits": {
+        "trailing_stop": true
+      },
+      "name": "trail-10",
+      "overrides": [],
+      "slippage_bps": 10
+    },
+    {
+      "exits": {
+        "take_profit": true,
+        "time_exit_sessions": 10
+      },
+      "name": "target-time10-10",
+      "overrides": [],
+      "slippage_bps": 10
+    },
+    {
+      "exits": {
+        "reentry_cooldown_sessions": 5
+      },
+      "name": "cool5-10",
+      "overrides": [],
+      "slippage_bps": 10
+    }
+  ],
+  "experiment": "EXP-022",
+  "require_history": true,
+  "start": "2017-01-03"
+}
```
