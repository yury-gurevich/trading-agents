<!-- Agent: planning | Role: sprint handover -->
# Sprint 288 — Each barrier claim states its return, and its settlement says what the return was

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-288-each-claim-states-its-return`
**Status:** SPEC
**Version:** *next available MINOR at merge*
**Effort:** M
**Decisions:** [DL-312](../design-log.md) (decided, seven decisions with the roads not taken) · work-queue 92 ([DL-240](../design-log.md): each name a distribution, *"the chance … and the return in each case"*; [DL-310](../design-log.md): the held claims this sprint extends)

> **Why this bump kind.** A barrier claim gains a dimension it did not have: what its paths say of its return and its timing, and the settlement and scorecard that check it. A MINOR.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/forecaster/laws/laws.md` | The forecaster's **locked constitution** | **LOCKED. Read-only during a build**, except Appendix section 2, which you apply exactly. A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/forecaster/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`OUT`** (FORE-OUT-07, FORE-OUT-08, FORE-OUT-09, FORE-OUT-10, the new FORE-OUT-11 and FORE-OUT-12), **`IDM`** (FORE-IDM-04: the seed and the rerun merge; FORE-IDM-05: settled once, a repeatable scorecard), **`FAIL`** (FORE-FAIL-05: a void is never scored), **`IDN`** (FORE-IDN-02: the pack's vocabulary), **`NEV`** (FORE-NEV-01/02: shadow only, nothing on the decision path).

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
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes: two new guarantees, no contract change.** A claim states four return figures from its own paths and its settlement three realised ones (`FORE-OUT-11`); the scorecard reports the return scores (`FORE-OUT-12`). The cycle is written for you in Appendix section 2: forecaster v1.11 → v1.12 (two new clauses, `FORE-OUT-07` and `FORE-OUT-08` naming the new fields, a Changelog line), the two `test-plan.md` rows naming your tests, and both rollups: **28 / 55 → 30 / 57**. **`contracts/` is not touched**: its deploy would restart the fidelity count.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/forecaster/domain/barrier_garch.py` | forecaster `laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `FORE-OUT-07` (EXP-018's simulation, its probabilities bit for bit), `FORE-IDM-04` (the seed) |
| `agents/forecaster/domain/barrier_returns.py` (new), `barrier_forecast.py`, `barrier_store.py` | same | `FORE-OUT-11` (the four figures from the same paths), `FORE-IDM-04` (a rerun adds them), `FORE-IDN-02` |
| `agents/forecaster/domain/barrier_settlement.py`, `settlement_store.py` | same | `FORE-OUT-08` (the outcome rule, unchanged), `FORE-OUT-11` (the realised figures), `FORE-FAIL-05` (a void records none) |
| `agents/forecaster/domain/barrier_return_scores.py` (new), `barrier_scorecard.py` | same | `FORE-OUT-12`, `FORE-OUT-10` (`held_` apart), `FORE-IDM-05` (repeatable), `FORE-OUT-08` (S241's names unchanged) |
| `orchestration/packs/trading_graph_vocabulary.json` | forecaster `FORE-IDN-02`; `kernel/graph_vocabulary.py` | seven new properties, or the fleet's guard refuses every claim and settlement |
| `agents/forecaster/tests/test_barrier_claim.py`, `test_barrier_settlement_record.py` (existing) | `FORE-OUT-07`, `FORE-OUT-08` | each pins its node's exact fields; section 2 adds the new names |

⚠️ **The probabilities do not move.** `garch_path_probs` must return exactly what it returns on `main` for every input: the golden values in `test_barrier_garch_oracle.py` and F1's probabilities digest prove it. Nothing on the decision path moves either: no file under `contracts/`, `kernel/`, `agents/scanner/`, `agents/analyst/`, `agents/portfolio_manager/`, `agents/provider/`, `agents/execution/`, `agents/monitor/`, `orchestration/` (but the vocabulary pack) or `surfaces/` changes. If your change needs one, stop and report.

---

## Goal

At merge, every barrier claim, a buy's or a held name's, states beside its three probabilities what the same simulated paths say of its return: the mean return to its first barrier or its tenth close (`expected_return`), the tenth close's return at its 5th percentile with the barriers ignored (`close_return_p05`), and the median session of each barrier's first touch (`sessions_to_target`, `sessions_to_stop`). Its settlement records what happened by the same rule (`realised_return`, `close_return`, `outcome_session`), and `barrier_scorecard` reports the declared against the realised return, their gap with a date-bootstrap interval and the tail's hit rate, once a claim that stated them settles. The probabilities, the outcome rule and every score S241 and S286 report are unchanged.

## Why (context)

Item 92: the operator's direction is to manage the book as a distribution (DL-240): for each name *"the chance it reaches its target first, its stop first, or neither, and the return in each case"*. Since S239 a claim states the chances only; S286 put a claim on every held name. The PM's sizing over distributions (the last step of 92, the operator's policy) needs a return per name, and the take-profit and time exit after EXP-022 need to know how long a target takes. Every step that sells waits for EXP-022, which waits for the fidelity PASS; this sprint is forecaster only, shadow, with no decision path, so it can be deployed while the count runs, and its figures start settling about ten sessions later.

### Measured, 2026-10-21 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| What the simulation already has | 1,000 paths × 10 sessions of prior close, high and low, and the tenth close; `garch_path_probs` returns the three shares and throws the rest away | *[measured by reading, 2026-10-21]* `agents/forecaster/domain/barrier_garch.py` |
| The settled ledger re-simulates | 25 settled claims on the live graph (`as_of` 2026-09-28 to 10-05, 6 dates): each claim's stored seed and GARCH parameters on the bars of the history it names give back its stored probabilities on **25 of 25**; the outcome rule re-read gives the stored outcome on **25 of 25** | *[measured 2026-10-21]* kit `measure/wq92ret_ledger.py`; `s288_f1.py` part 2 on `ledger_2026-10-21.json` |
| What those 25 would have said | declared expected return mean **+0.50 %** (+0.02 % to +1.15 %); realised by the outcome's rule **+0.16 %**; bias **−0.34 %, interval −1.80 % to +1.73 %**; **0 / 25** tenth closes below their declared 5th percentile | *[measured 2026-10-21]* the same; the prototype's scorecard over them |
| The claim's own return's 5th percentile | **minus the stop on 25 / 25** (the return to the first barrier has a point mass there) | *[measured 2026-10-21]* `wq92ret_ledger.txt` |
| The held book on 2026-10-20 | 32 held claims: expected return mean **+0.41 %** (DOW −0.58 % to NVDA +1.18 %), **4 of 32 negative** (DOW, TMO, AAPL, PFE); tenth close's 5th percentile mean −8.4 % | *[measured 2026-10-21]* kit `s288_f1.py` part 1 (S286's frozen book and its frozen history, the real GARCH fit) → `f1_proto.txt` |
| The probabilities do not move | main's code and the prototype's state the same probabilities on all 35 claims and the same 2 designed refusals: probs digest **`43c45020da6e057d`** both | *[measured 2026-10-21]* `f1_main_4f73228c.txt`, `f1_proto.txt` |
| Whether the figures have skill | *[ASSUMED — not measured]* 25 settled claims on 6 dates; the bias's interval spans zero. The scorecard reports; nothing reads the figures | the scorecard about ten sessions after the deploy |

---

## Scope — and what is deliberately NOT here

1. **The paths, returned** (`domain/barrier_garch.py`, Appendix section 1): `garch_paths` is EXP-018's loop returning its four arrays; `garch_path_probs` keeps its signature and counts them.
2. **The four figures** (`domain/barrier_returns.py`, new), stated on every claim (`barrier_forecast.py`, `barrier_store.py`).
3. **The realised figures** (`domain/barrier_settlement.py`: `first_touch` and three new `Settlement` fields; `settlement_store.py`).
4. **The return scores** (`domain/barrier_return_scores.py`, new; `barrier_scorecard.py`).
5. **The vocabulary pack**: four `BarrierForecast` and three `BarrierSettlement` properties.
6. **The law cycle and two existing-test edits** (Appendix section 2), exactly.

### Out of scope (do NOT build this sprint)

- **Anything that reads the figures**: the PM, the brief, the dashboard, the deliberators. The figures are shadow evidence (`FORE-NEV-01/02`).
- **The book's tail.** Each name's paths are drawn on their own; a book tail needs a joint simulation (DL-312, named).
- **Scoring the sessions.** They are recorded (`outcome_session`); scoring them is named in DL-312.
- **A new `model_version`** (DL-312 D5).
- **No `laws.md` edit** beyond Appendix section 2. **No ADR reversal.**

### The road not taken (LAW-06)

- **The claim's own return's 5th percentile as the worst case.** Rejected: it is minus the stop on 25 of 25 settled claims.
- **The return if neither, stored.** Rejected: implied by `expected_return` and the probabilities.
- **The return under today's policy (stop only).** Rejected: EXP-022's question, answered on the replay with real exits.
- **A second simulation for the figures.** Rejected: two loops can drift; the figures must describe the probabilities' own paths.
- **A new model version.** Rejected: it would refuse a rerun on a claim stated before the deploy.
- **A notice when a name passes its target, or a `BarrierHistory` retention rule.** Not chosen by the operator this time.

---

## The design decisions this sprint has to make

**None are left to make: DL-312 records D1 to D7 with the rejected alternatives, on `main`.** Do not add a design-log entry. If a decision there does not survive contact with the code, stop and report.

---

## Blast radius — measured 2026-10-21

| What | Detail |
| --- | --- |
| Files changed | Production (Appendix section 1, 9 files): new `agents/forecaster/domain/barrier_returns.py` **73**, `domain/barrier_return_scores.py` **82**; `domain/barrier_garch.py` 172 → **191**, `domain/barrier_settlement.py` 138 → **151**, `barrier_forecast.py` 176 → **177**, `barrier_store.py` 110 → **122**, `settlement_store.py` 100 → **104**, `barrier_scorecard.py` 85 → **108**; `orchestration/packs/trading_graph_vocabulary.json` (+7 properties). Law and rollups (section 2): `agents/forecaster/laws/laws.md` and `test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`. Two existing test files (section 2): `agents/forecaster/tests/test_barrier_claim.py` (+4 names), `test_barrier_settlement_record.py` (+3 entries). Your tests: five files (Test plan) and a helper of your own |
| Agents affected | forecaster only. It imports nothing new from another agent |
| Contract change? | **No** |
| Graph vocabulary change? | **Yes: seven properties.** `BarrierForecast`: `close_return_p05`, `expected_return`, `sessions_to_stop`, `sessions_to_target`. `BarrierSettlement`: `close_return`, `outcome_session`, `realised_return`. No new label or edge |
| New env keys / tunables | none (`TAIL_PERCENTILE` is the figure's definition, a constant like `HORIZON_SESSIONS`) |
| Deploy implication | **`deploy-agents.ps1 -Action vocabulary` first** (an older image reads the larger vocabulary as before), **then an image-only retag**. No fidelity decision path (`scripts/replay_fidelity_git.py`'s `DECISION_PATHS`): the count holds |
| Rollback | Retag to `s287`. A retag does not undo: the figures already written on claims and settlements (append-only, shadow; nothing reads them but the scorecard), the seven vocabulary properties (harmless to `s287`) |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **No design-log entry**: DL-312 is decided.
3. **Write the tests A1 to A14 under the exact names in the Test plan** and run them on the unchanged tree: every one fails or errors (`garch_paths` and the two new modules do not exist; `Settlement` has no realised figures). Paste the output.
4. **Apply Appendix section 1 exactly.**
5. **Apply Appendix section 2 exactly** (law cycle, rollups, the two existing-test edits).
6. **Plant the breaks B1 to B27** one at a time against your tests alone; each turns at least one red; restore each.
7. **Bump MINOR, `uv lock --offline`, `make ci` redirected to a file.**
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

Each docstring cites the clauses in the last column. The names are fixed: the test-plan rows in Appendix section 2 cite them. Paths: `agents/forecaster/tests/`. Where a row gives numbers, assert them exactly (or with `pytest.approx` where a float is computed).

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 `test_barrier_returns.py::test_the_figures_are_the_return_to_the_first_barrier_or_the_tenth_close` | four hand-made paths of 10 sessions as `garch_paths`' four arrays (prior close 1.0, highs 1.01, lows 0.99 unless named), stop 0.05, target 0.06: the stop on session 3 (low 0.94), the target on session 5 (high 1.07), both on session 2 (high 1.07, low 0.94), neither; tenth closes 0.93, 1.07, 0.97, 1.02 | `expected_return` = (−0.05 + 0.06 − 0.05 + 0.02) / 4; `sessions_to_stop` 2.5; `sessions_to_target` 5.0; `close_return_p05` = −0.07 + 0.15 × 0.04 (numpy's linear percentile of −0.07, −0.03, 0.02, 0.07) (`FORE-OUT-11`) |
| A2 | `…returns.py::test_with_no_touch_a_barriers_sessions_are_absent` | two quiet paths, tenth closes 1.01 and 0.97 | both sessions `None`; `expected_return` −0.01 (`FORE-OUT-11`) |
| A3 | 🎯 `…returns.py::test_the_paths_are_exp018s_own` (the three `GOLDEN` cases of `test_barrier_garch_oracle.py`) | EXP-018's `garch_path_probs` read from the frozen record as that test reads it, its last line `return barrier_probs(prev_all, hh, llw, stop, target)` replaced by `return prev_all, hh, llw, level` | `garch_paths` returns four arrays, each `np.array_equal` to the experiment's; `barrier_probs` on the first three, and `garch_path_probs`, equal the golden probabilities (`FORE-OUT-07`, `FORE-OUT-11`) |
| A4 | 🎯 `test_barrier_claim_returns.py::test_a_claim_states_its_return_from_the_paths_its_probabilities_counted` | 760 AAPL bars (drift 0.0004), a buy request at stop 0.05, target 0.06, the store wrapped in the pack's vocabulary guard | no fault; the claim's three probabilities and four figures equal `barrier_probs` and `barrier_returns` of `garch_paths` re-run in the test from the claim's own `seed`, `garch_*` and `n_paths` on those bars; −0.05 ≤ `expected_return` ≤ 0.06; `close_return_p05` < 0; both sessions in 1 to 10 (`FORE-OUT-11`, `FORE-IDM-04`) |
| A5 | `…claim_returns.py::test_a_held_claim_states_its_return_too` | 760 COP bars, a `position` request (stop 0.8 × close, target 1.03 × close, width 0.05), the guard | no fault; the key starts `barrier-garch-v1:held:COP:`; probabilities and figures equal the re-run on the claim's own `stop_pct` and `target_pct` (`FORE-OUT-11`, `FORE-OUT-09`) |
| A6 | `…claim_returns.py::test_a_claim_stated_before_its_figures_gains_them_on_a_rerun` | a claim stated once; a fresh graph holding the same claim without its four figures and with `created_at` `2026-10-20T22:31:00+00:00`; the same request again | no fault; the node keeps that `created_at` and gains the four figures, equal to the first statement's (`FORE-IDM-04`, `FORE-OUT-11`) |
| A7 | 🎯 `test_barrier_settlement_returns.py::test_a_settlement_records_the_return_its_outcome_gave` (3 cases) | `settlement_paths.path` around `AS_OF`, the claim's `entry_close` 101.0 (the settling series closes at 100 on `as_of`), stop 0.05, target 0.07: a low of 94 on session 3 and a tenth close of 103; a high of 107.5 on session 5 and a tenth close of 98; a tenth close of 102 | `stop`, `realised_return` −0.05, `close_return` 0.03, `outcome_session` 3; `target`, 0.07, −0.02, 5; `neither`, 0.02, 0.02, `None` (`FORE-OUT-11`, `FORE-OUT-08`) |
| A8 | `…settlement_returns.py::test_a_session_touching_both_is_the_stop_and_its_session` | a session 4 with high 108 and low 94 | `stop`, session 4, `realised_return` −0.05 (`FORE-OUT-08`, `FORE-OUT-11`) |
| A9 | `…settlement_returns.py::test_a_void_settlement_records_no_return` | a 2:1 split on session 3; no bars at 45 days; the split's settlement written through the pack's vocabulary guard | both void (`suspected_corporate_action`, `no_settling_bars`) with the three figures `None`; the written node's three are `None` (`FORE-FAIL-05`, `FORE-OUT-11`) |
| A10 | 🎯 `test_barrier_return_scorecard.py::test_the_return_scores_appear_once_a_claim_that_stated_one_settles` | S241's ledger (`ledger_fixture.write_ledger`); apart, three claims that stated figures, settled: AAPL 2026-10-21 declared 0.010, p05 −0.08, target, realised 0.07, close 0.05; MSFT 2026-10-21 0.004, −0.06, stop, −0.05, −0.09; NVDA 2026-10-22 0.006, −0.07, neither, 0.01, 0.01 | S241's ledger reports exactly its 14 names (`settled`, `void`, `open`, `realised_*` and `declared_*` of the three outcomes, `brier_model`, `brier_climatology`, `skill`, `skill_lo`, `skill_hi`); the three report `return_settled` 3, `declared_return` 0.020 / 3, `realised_return` 0.01, `return_bias` 0.01 − 0.020 / 3, `close_below_p05` 1 / 3, `return_bias_lo` 0.003, `return_bias_hi` 0.004, `settled` 3, no `held_` name (`FORE-OUT-12`, `FORE-OUT-08`) |
| A11 | `…return_scorecard.py::test_held_claims_return_scores_are_apart` | A10's three, then the same three as held claims (`…:held:…`, `subject_kind` `position`) | every non-`held_` metric equals the buys-only card; each `held_` return score equals the buys' value; `sample_size` 3 (`FORE-OUT-12`, `FORE-OUT-10`) |
| A12 | `…return_scorecard.py::test_a_claim_or_settlement_without_figures_is_not_return_scored` | a claim with figures whose settlement has no realised figures (`Settlement` of five fields); a claim without figures whose settlement has them | `settled` 2; no return score name (`FORE-OUT-12`) |
| A13 | `test_barrier_return_scores.py::test_the_bias_interval_resamples_whole_dates` | `ReturnCase`s: two dates with gaps +0.01 and −0.01; the same two on one date; none | the two dates: `return_bias` 0, `return_bias_lo` −0.01, `return_bias_hi` 0.01; one date: no interval; none: `{}`; a second call returns the same dict (`FORE-OUT-12`, `FORE-IDM-05`) |
| A14 | `…return_scores.py::test_the_tail_share_counts_closes_strictly_below_their_percentile` | three cases with `close_p05` −0.05: tenth closes −0.05, −0.0501, 0.02 | `close_below_p05` 1 / 3 (`FORE-OUT-12`) |

On the unchanged tree every one fails or errors. After Appendix section 1 all fourteen pass, and the existing suites pass unchanged except the two files section 2 edits.

---

## Success factors

- [ ] On the built tree, F1 (`s288_f1.py <kit> <out>`, run from the main checkout with `PYTHONPATH=<built tree>`) prints exactly the prototype's output (`f1_proto.txt`, full digest **`83e0650cf43b3a55`**): its probabilities digest is main's, `43c45020da6e057d`; 32 held claims with figures; the ledger's 25 claims re-simulate and re-settle 25 / 25.
- [ ] No file under `contracts/`, `kernel/`, a decision path, `orchestration/` (but the pack) or `surfaces/` changes; no existing test changes but section 2's two.
- [ ] Design decisions recorded with rejected alternatives: DL-312, already on `main`.
- [ ] Law cycle done as Appendix section 2: `FORE-OUT-11`, `FORE-OUT-12` 🟩; forecaster 30 / 57 in both rollups.
- [ ] B1 to B27 each planted, watched to fail against your tests alone, restored — stated per break.
- [ ] Every touched module < 200 lines, test files included.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The probabilities must not move by a bit.** `garch_paths` is the loop `garch_path_probs` had, line for line, returning `prev_all, hh, llw, level`; `garch_path_probs` calls it and counts. Reordering the random draws, or simulating twice, changes the claims the fleet already states. A3's oracle and the existing golden values catch it.
🪤 **One simulation, two readers.** The claim's figures read the same four arrays its probabilities were counted on (`barrier_probs(*paths[:3], …)` and `barrier_returns(paths, …)`). A4 re-runs the claim's own seed: a second, differently seeded simulation shows.
🪤 **The worst case is the tenth close's, barriers ignored**, never the claim's own return's (that one is minus the stop on 25 of 25).
🪤 **Sessions are 1 to 10**, the first touch's index plus one, and `None`, not NaN, when no path touches.
🪤 **The settlement's figures read the settling series' own close on `as_of`**, never the claim's `entry_close` (A7 sets them 1 % apart). The outcome rule is unchanged: `first_touch` replaces `outcome_index` (which nothing else called) with the same comparisons in the same order, and returns the session beside the index.
🪤 **A void records no figure**, and a `Settlement` built with its first five fields (every existing test does) has all three `None`.
🪤 **The return scores appear only when a claim that stated its figures has a settlement that recorded a realised return.** S241's ledger keeps exactly its 14 names (A10); `sample_size` stays the buys' settled count.
🪤 **`model_version` stays `1.0.0`** (DL-312 D5): a new one would refuse the rerun A6 proves.
🪤 **The vocabulary pack is part of the deploy**: without its seven properties the fleet's guard refuses every claim and every settlement. A4, A5 and A9 write through the guard.
🪤 **Sizes.** `barrier_garch.py` 191 and `barrier_forecast.py` 177 after section 1: do not grow them; keep each new test file under 200 after `ruff format`. **Do not name a helper `return_helpers.py`**: that file exists (the return model's).
🪤 **Write files with an editor, not a shell heredoc** (Git Bash's heredoc has eaten backslashes before). Write the minus sign in a docstring as a word or a hyphen: ruff's `RUF001` refuses U+2212.

**The breaks** (plant one at a time in production code, run your A1 to A14 alone, expect red, restore). Each is an exact replacement of text in the file after section 1:

| # | File | Replace | With |
| --- | --- | --- | --- |
| B1 | `agents/forecaster/domain/barrier_garch.py` | `    return prev_all, hh, llw, level` | `    return prev_all, hh, llw, prev_all[:, -1]` |
| B2 | same | `    return barrier_probs(prev, high, low, stop, target)` | `    return barrier_probs(prev, low, high, stop, target)` |
| B3 | `agents/forecaster/domain/barrier_returns.py` | `stop_first = (fs < HORIZON_SESSIONS) & (fs <= ft)` | `stop_first = (fs < HORIZON_SESSIONS) & (fs < ft)` |
| B4 | same | `np.where(stop_first, -stop, ` | `np.where(stop_first, stop, ` |
| B5 | same | `    close_return = last - 1` | `    close_return = prev[:, -1] - 1` |
| B6 | same | `np.percentile(close_return, TAIL_PERCENTILE)` | `np.percentile(returns, TAIL_PERCENTILE)` |
| B7 | same | `np.median(first[touched] + 1)` | `np.median(first[touched])` |
| B8 | same | the two lines `    if not touched.any():` / `        return None` | nothing (both removed) |
| B9 | same | `TAIL_PERCENTILE = 5` | `TAIL_PERCENTILE = 10` |
| B10 | `agents/forecaster/barrier_forecast.py` | `        returns=barrier_returns(paths, stop, target),` | `        returns=barrier_returns(garch_paths(np.random.default_rng(seed + 1), params.as_tuple(), r, lh_pct, ll_pct, 0, len(r), n_paths=settings.barrier_paths), stop, target),` |
| B11 | same | `        returns=barrier_returns(paths, stop, target),` | nothing (the line removed) |
| B12 | `agents/forecaster/barrier_store.py` | `"close_return_p05": claim.returns.close_return_p05,` | `"close_return_p05": claim.returns.expected_return,` |
| B13 | same | `    if claim.returns is not None:` | `    if claim.returns is not None and claim.held is None:` |
| B14 | `agents/forecaster/domain/barrier_settlement.py` | `realised = (-stop_pct, target_pct, close_return)[k]` | `realised = (close_return, target_pct, close_return)[k]` |
| B15 | same | `            return 0, k - t` | `            return 0, k - t - 1` |
| B16 | same | `            return 1, k - t` | `            return 1, None` |
| B17 | same | `close_return = window[-1].close / entry - 1` | `close_return = window[-1].close / entry_close - 1` |
| B18 | same | `return Settlement(VOID, CORPORATE_ACTION, pass_date, entry, ratio)` | `return Settlement(VOID, CORPORATE_ACTION, pass_date, entry, ratio, 0.0, 0.0)` |
| B19 | `agents/forecaster/settlement_store.py` | `        "outcome_session": settlement.outcome_session,` | nothing (the line removed) |
| B20 | `agents/forecaster/domain/barrier_return_scores.py` | `"return_bias": float(realised.mean() - declared.mean()),` | `"return_bias": float(declared.mean() - realised.mean()),` |
| B21 | same | `        np.concatenate([by_date[u] for u in rng.choice(udates, len(udates))])` | `        rng.choice(len(gap), len(gap))` |
| B22 | same | `case.close_return < case.close_p05` | `case.close_return <= case.close_p05` |
| B23 | same | `    if len(udates) < 2:` | `    if len(udates) < 1:` |
| B24 | `agents/forecaster/barrier_scorecard.py` | `    if declared is None or realised is None:` | `    if declared is None:` |
| B25 | same | `    metrics.update(return_scores([case for case in returns if case is not None]))` | the two lines `    if not prefix:` / `        metrics.update(return_scores([c for c in returns if c is not None]))` |
| B26 | `orchestration/packs/trading_graph_vocabulary.json` | the line `      "expected_return",` | nothing (the line removed) |
| B27 | same | the line `      "outcome_session",` | nothing (the line removed) |

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes after the Appendix: `barrier_garch.py` **191**, `barrier_forecast.py` **177**, `domain/barrier_settlement.py` **151**, `barrier_store.py` **122**, `barrier_scorecard.py` **108**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. No tunable is added: the tail's percentile defines the figure, as the horizon defines the model.
- Faults, not silent failure — `kernel.fault_boundary` (the claim's and the settlement's existing boundaries cover the new code).
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a pipe.**
- Version bump MINOR, `uv.lock` staged with it.
- Secrets never through the worktree — your worktree has **no `.env`**, and nothing in this sprint needs one. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0** from the branch's worktree; check the printed SHA against `git rev-parse HEAD`.
2. Planner's review: CodeQL set-diff against the baseline branch first; the blobs against `prototype_blobs.txt` (kit); the planner's tests on the built tree; B1 to B27 against Codex's tests alone; F1 (equals `f1_proto.txt` byte for byte).
3. Merge to `main` locally and push; tag `v<version>`; post-merge CodeQL.
4. **Deploy, on the operator's word: `pwsh infra/deploy-agents.ps1 -Action vocabulary` (17 `[OK]`, each app's decoded pack = the repo's), then an image-only retag.** The fidelity count holds (no decision path); record the rollback tag `s287`. F2 on the first weekday night after: 8 / 8; every claim of the run (buys and held) carries the four figures; the first `BarrierSettlement` written after the deploy carries `realised_return`, `close_return` and `outcome_session`; no forecaster `error` fault; no `VocabularyError`. About ten sessions later, the first claims stated with figures settle: then read `barrier_scorecard`'s return scores.

---

## Handover — paste this to Codex

```text
You are building Sprint 288 in the worktree ../ta-s288, on the branch
sprint-288-each-claim-states-its-return. Never work on main. The worktree and its venv are ready;
never run a bare `uv sync` (it needs the network and you have none).

Read docs/sprints/sprint-288-each-claim-states-its-return.md, whole, before anything else. It is
the spec, and its bottom sections are your handback. The Appendix holds the production code, the
law text and two existing-test edits, which you apply exactly. Your work is the tests A1 to A14,
the breaks, the bump and the evidence.

In order:
1. Read agents/forecaster/laws/laws.md and test-plan.md, docs/laws/conventions.md and
   docs/laws/drift-register.md, whole. Fill the Law reading record in the spec BEFORE any code.
2. Write the tests A1 to A14 under the exact file paths and names in the Test plan (five files
   under agents/forecaster/tests/; a helper module of your own is fine, but not named
   return_helpers.py, which exists), each docstring citing the clauses in its row, each asserting
   the exact numbers its row gives. Run them on the unchanged tree and paste the output into the
   Closeout: every one fails or errors.
3. Apply Appendix section 1 exactly (9 files: 8 Python modules, 2 of them new, and the graph
   vocabulary pack). Change nothing else in production code.
4. Apply Appendix section 2 exactly (the forecaster's laws.md and test-plan.md, docs/laws/ledger.md,
   docs/laws/INDEX.md, and the two existing tests test_barrier_claim.py and
   test_barrier_settlement_record.py). Change no other existing test. The test-plan rows name your
   tests; if a name differs, your name is wrong.
5. Plant the breaks B1 to B27 (Traps: each row is an exact replacement) one at a time; each must
   turn at least one of your A1 to A14 red; restore each before the next. Record each in the
   Closeout.
6. Bump the version MINOR to the next number after main's in pyproject.toml, run
   uv lock --offline, stage uv.lock. Run make ci redirected to a file and read the file. If the
   dependency audit is the only step that fails for want of network, say so; the planner runs it.
   Paste the step lines and their verdicts into the Closeout, not the whole log.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md, docs/design-log.md or docs/work-queue.md.

DO NOT: reach the network or any live service; run infra/ scripts, pwsh or any az command; change
contracts/, kernel/, any agent but agents/forecaster, orchestration/ (but the vocabulary pack in
section 1), surfaces/ or any Dockerfile; change what garch_path_probs returns for any input;
simulate a claim's paths twice; bump BARRIER_MODEL_VERSION; add or reword a law clause beyond
section 2; add a design-log entry; use noqa; let any module, test files included, reach 200 lines;
measure make ci through a pipe; write files with a shell heredoc.

Traps (the spec's Traps section has them all): the probabilities must not move by a bit; the
figures read the probabilities' own paths; the worst case is the tenth close's, barriers ignored;
sessions are 1 to 10 and None, not NaN, with no touch; the settlement's figures read the settling
close, not the claim's; a void records none; the return scores appear only once a claim with
figures settles with them, and S241's ledger keeps exactly its names; the pack's seven properties
are part of the change.

Two tiers when something does not fit. A wrong command, count, path or line number whose intent is
plain: correct it, record it in Return notes, and carry on. A law that contradicts the spec, an
existing test failing outside section 2's files, or a measurement in the spec that does not
reproduce: STOP and report. State anything not done as "not done" or "verified failing". Never
write a Result for work you have not done.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output: the step lines and their verdicts, not the whole `make ci` log.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| *(builder fills)* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(builder fills)*

**Contradictions found between a law and this spec:** *(builder fills)*

**Laws found silent where a decision was needed:** *(builder fills)*

**Clauses that were ⬜ and are now proven:** *(builder fills)*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | *(builder fills)* | | | |

**Tests added beyond the plan:** *(builder fills)*

---

## Closeout — evidence

**Status:** *(builder fills: BUILT)*

**Tree the proofs ran in (and `.env` present?):** *(builder fills)*

**Result:** *(builder fills)*

**Files changed:** *(builder fills)*

**Design decisions:** recorded as [`DL-312`](../design-log.md) — seven decisions, the roads not taken listed there.

**Proof — the red run first:**

```text
(builder fills)
```

**Proof — the green run:**

```text
(builder fills)
```

**Guards planted:** *(builder fills: B1 to B27, per break)*

**Module line counts:** *(builder fills)*

**`make ci`:** *(builder fills: the step lines and verdicts, exit code, passed/skipped, coverage, dependency audit, detect-secrets)*

**`make gate-ran`:** *(planner: run from the branch's worktree after the push)*

**Not met / verified failing:** *(builder fills)*

---

## Return notes

- *(builder fills)*

---

## Appendix — the prototype (`proto-s288` `37d41e01`: `make ci` 5,297 passed, 9 skipped, 100.00 %, every step green, the dependency audit included; 27 / 27 breaks red against the planner's tests; F1 digest `83e0650cf43b3a55`)

Apply each section with `git apply` from the worktree's root, or by hand; either way the 15 files must end byte for byte as below. The diffs are against `main` at `4f73228c`.

### Section 1 — production code and the vocabulary pack (9 files)

```diff
diff --git a/agents/forecaster/barrier_forecast.py b/agents/forecaster/barrier_forecast.py
index 1879a274..d4cf926e 100644
--- a/agents/forecaster/barrier_forecast.py
+++ b/agents/forecaster/barrier_forecast.py
@@ -5,8 +5,8 @@ Role: for one ticker and its stop and target (a buy's, or a held name's live sto
       and declared target measured from the claim's close, DL-310), read ~3 years
       of its own daily bars from the BarrierHistory the provider wrote for the run
       (DL-241 D10), fit GARCH(1,1)-t, simulate EXP-018's 10-session paths and
-      record the three probabilities as an append-only, advisory BarrierForecast
-      claim. Any refusal
+      record the three probabilities, and the return figures the same paths give
+      (DL-312), as an append-only, advisory BarrierForecast claim. Any refusal
       (malformed barriers, no or a failed history, a ticker the provider dropped,
       short history, a failed fit, a conflicting rerun) records a fault and returns
       the neutral reading; a claim is never fabricated (FORE-FAIL-04). A designed
@@ -34,10 +34,12 @@ from agents.forecaster.barrier_store import BARRIER_LABEL, BarrierClaim, write_c
 from agents.forecaster.domain.barrier_garch import (
     BARRIER_MODEL_ID,
     accept_fit,
+    barrier_probs,
     barrier_seed,
     daily_moves,
-    garch_path_probs,
+    garch_paths,
 )
+from agents.forecaster.domain.barrier_returns import barrier_returns
 from agents.forecaster.domain.features import confidence_from_history
 from agents.forecaster.domain.sentiment import NEUTRAL
 from agents.forecaster.held_claim import held_barriers, held_prices
@@ -138,7 +140,7 @@ def _state_claim(
         )
     as_of = date.fromisoformat(rows[-1][0])
     seed = barrier_seed(ticker, as_of)
-    probabilities = garch_path_probs(
+    paths = garch_paths(
         np.random.default_rng(seed),
         params.as_tuple(),
         r,
@@ -146,8 +148,6 @@ def _state_claim(
         ll_pct,
         0,
         len(r),
-        stop,
-        target,
         n_paths=settings.barrier_paths,
     )
     return BarrierClaim(
@@ -156,7 +156,8 @@ def _state_claim(
         entry_close=rows[-1][4],
         stop_pct=stop,
         target_pct=target,
-        probabilities=probabilities,
+        probabilities=barrier_probs(*paths[:3], stop, target),
+        returns=barrier_returns(paths, stop, target),
         params=params,
         history_bars=len(rows),
         n_paths=settings.barrier_paths,
diff --git a/agents/forecaster/barrier_scorecard.py b/agents/forecaster/barrier_scorecard.py
index d81fdf05..5aad620e 100644
--- a/agents/forecaster/barrier_scorecard.py
+++ b/agents/forecaster/barrier_scorecard.py
@@ -5,7 +5,8 @@ Role: answer the barrier_scorecard capability from the forecaster's own ledger,
       BarrierForecast claims and their BarrierSettlements: counts settled, void and
       open, then EXP-018's scores over the settled ones (FORE-OUT-08): buys' claims
       under the names S241 gave them, held names' claims apart under ``held_``
-      once the ledger holds one (DL-310), each against the same climatology.
+      once the ledger holds one (DL-310), each against the same climatology; and,
+      once a settled claim stated its return, the return scores (DL-312).
       Read-only and
       repeatable (FORE-IDM-05); never promotion-eligible (FORE-OUT-04); it reports
       and decides nothing (FORE-NEV-01/02).
@@ -17,6 +18,7 @@ from __future__ import annotations
 from datetime import UTC, datetime
 from typing import TYPE_CHECKING

+from agents.forecaster.domain.barrier_return_scores import ReturnCase, return_scores
 from agents.forecaster.domain.barrier_settlement import OUTCOMES, VOID
 from agents.forecaster.domain.barrier_skill import ScoredCase, ledger_scores
 from agents.forecaster.settlement_store import model_ledger
@@ -68,6 +70,8 @@ def _scores(
         "open": float(len(claims) - len(mine)),
     }
     metrics.update(ledger_scores(cases))
+    returns = [_return_case(claims[key], mine[key]) for _as_of, key in settled]
+    metrics.update(return_scores([case for case in returns if case is not None]))
     return {f"{prefix}{name}": value for name, value in metrics.items()}, len(cases)


@@ -83,3 +87,22 @@ def _case(claim: Node, settlement: Node) -> ScoredCase:
         ),
         brier=float(settlement.props["brier"]),
     )
+
+
+def _return_case(claim: Node, settlement: Node) -> ReturnCase | None:
+    """A settled claim's return figures, or None when it stated none.
+
+    A claim stated before its figures existed, or settled before the settlement
+    recorded a realised return, has nothing to score.
+    """
+    declared = claim.props.get("expected_return")
+    realised = settlement.props.get("realised_return")
+    if declared is None or realised is None:
+        return None
+    return ReturnCase(
+        as_of=str(settlement.props["as_of"]),
+        declared=float(declared),
+        realised=float(realised),
+        close_p05=float(claim.props["close_return_p05"]),
+        close_return=float(settlement.props["close_return"]),
+    )
diff --git a/agents/forecaster/barrier_store.py b/agents/forecaster/barrier_store.py
index 69938cc6..e3a7a5ec 100644
--- a/agents/forecaster/barrier_store.py
+++ b/agents/forecaster/barrier_store.py
@@ -4,7 +4,7 @@ Agent: forecaster
 Role: persist a barrier claim with every field its later settlement reads, keyed
       so a rerun on the same last bar merges into the same node (DL-241 D2/D5); a
       held name's claim is keyed apart from a buy's and says which stop and target
-      it stood on (DL-310).
+      it stood on (DL-310); a claim states its return figures (DL-312).
 External I/O: GraphStore writes via the injected backend.
 """

@@ -24,6 +24,7 @@ if TYPE_CHECKING:
     from datetime import date

     from agents.forecaster.domain.barrier_garch import GarchParams
+    from agents.forecaster.domain.barrier_returns import BarrierReturns
     from agents.forecaster.held_claim import HeldBarriers
     from kernel import GraphStore, Node

@@ -51,6 +52,8 @@ class BarrierClaim:
     sessions_requested: int
     held: HeldBarriers | None = None
     """A held name's stop and target, and where they came from; None for a buy."""
+    returns: BarrierReturns | None = None
+    """What the same paths say of the return (DL-312); every stated claim has them."""

     @property
     def key(self) -> str:
@@ -91,6 +94,15 @@ def write_claim(graph: GraphStore, claim: BarrierClaim) -> Node:
         "created_at": datetime.now(tz=UTC).isoformat(),
         "shadow": True,
     }
+    if claim.returns is not None:
+        props.update(
+            {
+                "expected_return": claim.returns.expected_return,
+                "close_return_p05": claim.returns.close_return_p05,
+                "sessions_to_target": claim.returns.sessions_to_target,
+                "sessions_to_stop": claim.returns.sessions_to_stop,
+            }
+        )
     if claim.held is not None:
         props.update(
             {
diff --git a/agents/forecaster/domain/barrier_garch.py b/agents/forecaster/domain/barrier_garch.py
index 74508bde..a7033bb2 100644
--- a/agents/forecaster/domain/barrier_garch.py
+++ b/agents/forecaster/domain/barrier_garch.py
@@ -3,9 +3,10 @@
 Agent: forecaster
 Role: turn a stock's daily history, a stop, a target, fitted GARCH parameters and a
       seed into P(stop first), P(target first), P(neither) within 10 sessions, and
-      apply EXP-018's fit-acceptance rule. Copied from the experiment's
-      `exp018_sim.py` (EXP-018 Appendix S), not rewritten: the one change is that
-      the variance filter is the same first-order recursion written as a loop,
+      apply EXP-018's fit-acceptance rule; the paths are returned too, so a claim's
+      other figures read the paths its probabilities counted (DL-312). Copied from the
+      experiment's `exp018_sim.py` (EXP-018 Appendix S), not rewritten: the one change
+      is that the variance filter is the same first-order recursion written as a loop,
       because the unit gate has no scipy (DL-241 D7: bit-identical to `lfilter`).
 External I/O: none.
 """
@@ -124,6 +125,24 @@ def garch_path_probs(
     n_paths: int,
 ) -> tuple[float, float, float]:
     """EXP-018's `garch_path_probs`, with `N_PATHS` as ``n_paths``."""
+    prev, high, low, _last = garch_paths(
+        rng, params, r, lh_pct, ll_pct, lo, t, n_paths=n_paths
+    )
+    return barrier_probs(prev, high, low, stop, target)
+
+
+def garch_paths(
+    rng: np.random.Generator,
+    params: tuple[float, float, float, float],
+    r: Floats,
+    lh_pct: Floats,
+    ll_pct: Floats,
+    lo: int,
+    t: int,
+    *,
+    n_paths: int,
+) -> tuple[Floats, Floats, Floats, Floats]:
+    """EXP-018's loop: each path's prior closes, highs, lows and tenth close."""
     mu, omega, alpha, beta = params
     seg = r[lo:t]
     s2_0 = seg.var()
@@ -143,7 +162,7 @@ def garch_path_probs(
         llw[:, k] = np.exp(np.minimum(s * ul[j], rr) / 100)
         level = level * np.exp(rr / 100)
         s2_next = omega + alpha * (rr - mu) ** 2 + beta * s2_next
-    return barrier_probs(prev_all, hh, llw, stop, target)
+    return prev_all, hh, llw, level


 def _variance_filter(
diff --git a/agents/forecaster/domain/barrier_return_scores.py b/agents/forecaster/domain/barrier_return_scores.py
new file mode 100644
index 00000000..1be51544
--- /dev/null
+++ b/agents/forecaster/domain/barrier_return_scores.py
@@ -0,0 +1,82 @@
+"""Barrier return scores, pure: whether the returns the claims stated came true.
+
+Agent: forecaster
+Role: score the settled claims that stated their return figures (DL-312): the mean
+      declared expected return against the mean return realised by the outcome's
+      rule, their difference with a 95 % interval from EXP-018's date bootstrap
+      (1,000 resamples of whole dates, its fixed seed, as the skill's), and the share
+      of tenth closes below their declared 5th percentile (near 0.05 when the tail
+      is calibrated). It reports; it decides nothing.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+from typing import TYPE_CHECKING
+
+import numpy as np
+
+from agents.forecaster.domain.barrier_skill import BOOTSTRAP_DRAWS, BOOTSTRAP_SEED
+
+if TYPE_CHECKING:
+    from collections.abc import Sequence
+
+    from numpy.typing import NDArray
+
+
+@dataclass(frozen=True)
+class ReturnCase:
+    """One settled claim's stated and realised return figures."""
+
+    as_of: str
+    declared: float
+    """The claim's ``expected_return``."""
+    realised: float
+    """The settlement's ``realised_return``."""
+    close_p05: float
+    """The claim's ``close_return_p05``."""
+    close_return: float
+    """The settlement's ``close_return``."""
+
+
+def return_scores(cases: Sequence[ReturnCase]) -> dict[str, float]:
+    """Count, means, the bias and its interval, the tail's share; empty with no case.
+
+    ``cases`` in a fixed order (the caller sorts): the bootstrap resamples them.
+    """
+    if not cases:
+        return {}
+    declared = np.array([case.declared for case in cases])
+    realised = np.array([case.realised for case in cases])
+    below = np.array([case.close_return < case.close_p05 for case in cases])
+    scores = {
+        "return_settled": float(len(cases)),
+        "declared_return": float(declared.mean()),
+        "realised_return": float(realised.mean()),
+        "return_bias": float(realised.mean() - declared.mean()),
+        "close_below_p05": float(below.mean()),
+    }
+    interval = _bias_interval(
+        realised - declared, np.array([case.as_of for case in cases])
+    )
+    if interval is not None:
+        scores["return_bias_lo"], scores["return_bias_hi"] = interval
+    return scores
+
+
+def _bias_interval(
+    gap: NDArray[np.float64], dates: NDArray[np.str_]
+) -> tuple[float, float] | None:
+    """The bias's 95 % interval over resampled dates; None under two dates."""
+    udates = np.unique(dates)
+    if len(udates) < 2:
+        return None
+    rng = np.random.default_rng(BOOTSTRAP_SEED)
+    by_date = {u: np.where(dates == u)[0] for u in udates}
+    draws = [
+        np.concatenate([by_date[u] for u in rng.choice(udates, len(udates))])
+        for _ in range(BOOTSTRAP_DRAWS)
+    ]
+    means = [gap[s].mean() for s in draws]
+    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))
diff --git a/agents/forecaster/domain/barrier_returns.py b/agents/forecaster/domain/barrier_returns.py
new file mode 100644
index 00000000..386960ec
--- /dev/null
+++ b/agents/forecaster/domain/barrier_returns.py
@@ -0,0 +1,73 @@
+"""Barrier returns, pure: what a claim's own paths say of its return and its timing.
+
+Agent: forecaster
+Role: from the paths a claim's three probabilities were counted on (DL-312), state the
+      mean return to the first barrier or the tenth close (the stop's return at the
+      stop, the target's at the target, else the tenth close's), the tenth close's 5th
+      percentile with the barriers ignored, and the median session of each barrier's
+      first touch. A first touch is EXP-018's: the low is checked first, so a session
+      touching both is the stop. Never a second simulation: the figures read the
+      probabilities' own paths.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+from typing import TYPE_CHECKING
+
+import numpy as np
+
+from agents.forecaster.domain.barrier_garch import HORIZON_SESSIONS
+
+if TYPE_CHECKING:
+    from numpy.typing import NDArray
+
+    Floats = NDArray[np.float64]
+
+#: The worst case is the tenth close's return one path in twenty falls below.
+TAIL_PERCENTILE = 5
+
+
+@dataclass(frozen=True)
+class BarrierReturns:
+    """A claim's return figures, each a fraction of the claim's close."""
+
+    expected_return: float
+    """The mean return to the first barrier or the tenth close."""
+    close_return_p05: float
+    """The tenth close's return at its 5th percentile, the barriers ignored."""
+    sessions_to_target: float | None
+    """The median session (1 to 10) of the target's first touch; None if none."""
+    sessions_to_stop: float | None
+    """The median session (1 to 10) of the stop's first touch; None if none."""
+
+
+def barrier_returns(
+    paths: tuple[Floats, Floats, Floats, Floats], stop: float, target: float
+) -> BarrierReturns:
+    """The figures of ``paths`` (`garch_paths`' four arrays) for one stop and target."""
+    prev, high, low, last = paths
+    hit_s = prev * low <= 1 - stop
+    hit_t = prev * high >= 1 + target
+    fs = np.where(hit_s.any(1), hit_s.argmax(1), HORIZON_SESSIONS)
+    ft = np.where(hit_t.any(1), hit_t.argmax(1), HORIZON_SESSIONS)
+    stop_first = (fs < HORIZON_SESSIONS) & (fs <= ft)
+    target_first = (ft < HORIZON_SESSIONS) & (ft < fs)
+    close_return = last - 1
+    returns = np.where(stop_first, -stop, np.where(target_first, target, close_return))
+    return BarrierReturns(
+        expected_return=float(returns.mean()),
+        close_return_p05=float(np.percentile(close_return, TAIL_PERCENTILE)),
+        sessions_to_target=_median_session(ft, target_first),
+        sessions_to_stop=_median_session(fs, stop_first),
+    )
+
+
+def _median_session(
+    first: NDArray[np.int64], touched: NDArray[np.bool_]
+) -> float | None:
+    """The median 1-based session of the touched paths' first touch, or None."""
+    if not touched.any():
+        return None
+    return float(np.median(first[touched] + 1))
diff --git a/agents/forecaster/domain/barrier_settlement.py b/agents/forecaster/domain/barrier_settlement.py
index d9d6bf29..32e3faed 100644
--- a/agents/forecaster/domain/barrier_settlement.py
+++ b/agents/forecaster/domain/barrier_settlement.py
@@ -4,10 +4,11 @@ Agent: forecaster
 Role: settle one claim on one ticker's later daily bars by EXP-018's outcome rule
       (`scripts/barrier_testbed.outcome()`, copied: over the 10 sessions after
       ``as_of`` the low is checked first, so a session touching both is the stop),
-      measured from the settling series' own close on ``as_of``; or void it with a
-      named reason, never a false outcome (S241, DL-243). It reads the claim's date,
-      entry close and barriers only: never its probabilities, which only the Brier
-      uses.
+      measured from the settling series' own close on ``as_of``, with the return that
+      rule gives, the tenth close's return and the session of the touch (DL-312); or
+      void it with a named reason, never a false outcome (S241, DL-243). It reads the
+      claim's date, entry close and barriers only: never its probabilities, which
+      only the Brier uses.
 External I/O: none.
 """

@@ -62,27 +63,35 @@ class Settlement:
     """The settling series' own close on ``as_of`` (absent when it has no such bar)."""
     entry_ratio: float | None
     """``entry_close_settling`` / the claim's ``entry_close``: drift between fetches."""
+    realised_return: float | None = None
+    """Minus ``stop_pct``, ``target_pct``, or the tenth close's return, by outcome."""
+    close_return: float | None = None
+    """The tenth close over the settling close, less 1, whatever the outcome."""
+    outcome_session: int | None = None
+    """The session (1 to 10) of the stop's or the target's touch; None for neither."""


-def outcome_index(
+def first_touch(
     hi: Sequence[float],
     lo: Sequence[float],
     cl: Sequence[float],
     t: int,
     stop: float,
     target: float,
-) -> int:
-    """0 stop first, 1 target first, 2 neither; touching both counts as the stop.
+) -> tuple[int, int | None]:
+    """0 stop first, 1 target first, 2 neither, and the touch's session (1 to 10).

+    Touching both counts as the stop; neither has no session (None).
     `scripts/barrier_testbed.outcome()` line for line, with its ``H`` as
-    ``HORIZON_SESSIONS``: the same comparisons in the same order.
+    ``HORIZON_SESSIONS``: the same comparisons in the same order (DL-312: the
+    session is returned beside the index).
     """
     for k in range(t + 1, t + HORIZON_SESSIONS + 1):
         if lo[k] <= cl[t] * (1 - stop):
-            return 0
+            return 0, k - t
         if hi[k] >= cl[t] * (1 + target):
-            return 1
-    return 2
+            return 1, k - t
+    return 2, None


 def settle(
@@ -110,7 +119,7 @@ def settle(
     ratio = entry / entry_close
     if _corporate_action(window):
         return Settlement(VOID, CORPORATE_ACTION, pass_date, entry, ratio)
-    k = outcome_index(
+    k, session = first_touch(
         [bar.high for bar in window],
         [bar.low for bar in window],
         [bar.close for bar in window],
@@ -118,7 +127,11 @@ def settle(
         stop_pct,
         target_pct,
     )
-    return Settlement(OUTCOMES[k], None, window[-1].day, entry, ratio)
+    close_return = window[-1].close / entry - 1
+    realised = (-stop_pct, target_pct, close_return)[k]
+    return Settlement(
+        OUTCOMES[k], None, window[-1].day, entry, ratio, realised, close_return, session
+    )


 def _corporate_action(window: Sequence[SettlingBar]) -> bool:
diff --git a/agents/forecaster/settlement_store.py b/agents/forecaster/settlement_store.py
index 4a51e353..575bbb14 100644
--- a/agents/forecaster/settlement_store.py
+++ b/agents/forecaster/settlement_store.py
@@ -3,9 +3,10 @@
 Agent: forecaster
 Role: persist a claim's settlement as its own append-only node, keyed from the
       claim and linked BarrierForecast -SETTLED_BY-> BarrierSettlement, carrying
-      the claim's three-class Brier (absent for a void); and read the ledger back
-      for one model (S241, DL-243). The claim itself is never written to: it is a
-      record of what was said, and what happened is a later fact of its own.
+      the claim's three-class Brier (absent for a void) and the return its outcome
+      gave (DL-312); and read the ledger back for one model (S241, DL-243). The
+      claim itself is never written to: it is a record of what was said, and what
+      happened is a later fact of its own.
 External I/O: GraphStore reads and writes via the injected backend.
 """

@@ -73,6 +74,9 @@ def write_settlement(
         "entry_close_settling": settlement.entry_close_settling,
         "entry_ratio": settlement.entry_ratio,
         "brier": None if void else brier(probabilities, settlement.outcome),
+        "realised_return": settlement.realised_return,
+        "close_return": settlement.close_return,
+        "outcome_session": settlement.outcome_session,
         "created_at": datetime.now(tz=UTC).isoformat(),
     }
     node = graph.merge_node(SETTLEMENT_LABEL, settlement_key(claim.key), props)
diff --git a/orchestration/packs/trading_graph_vocabulary.json b/orchestration/packs/trading_graph_vocabulary.json
index 920f0217..62e88782 100644
--- a/orchestration/packs/trading_graph_vocabulary.json
+++ b/orchestration/packs/trading_graph_vocabulary.json
@@ -571,9 +571,11 @@
     ],
     "BarrierForecast": [
       "as_of",
+      "close_return_p05",
       "created_at",
       "declared_target_pct",
       "entry_close",
+      "expected_return",
       "fit_status",
       "garch_alpha",
       "garch_beta",
@@ -589,6 +591,8 @@
       "p_stop_first",
       "p_target_first",
       "seed",
+      "sessions_to_stop",
+      "sessions_to_target",
       "shadow",
       "stop_pct",
       "stop_price",
@@ -615,11 +619,14 @@
       "as_of",
       "brier",
       "claim_key",
+      "close_return",
       "created_at",
       "entry_close_settling",
       "entry_ratio",
       "model_id",
       "outcome",
+      "outcome_session",
+      "realised_return",
       "settled_on",
       "settling_ref",
       "ticker",
```

### Section 2 — the law cycle, the rollups and two existing tests (6 files)

```diff
diff --git a/agents/forecaster/laws/laws.md b/agents/forecaster/laws/laws.md
index 865c6067..86baad96 100644
--- a/agents/forecaster/laws/laws.md
+++ b/agents/forecaster/laws/laws.md
@@ -1,6 +1,6 @@
 # `Forecaster` — Laws

-**Prefix:** `FORE` · **status:** LOCKED v1.11 · **Owner:** Yury Gurevich
+**Prefix:** `FORE` · **status:** LOCKED v1.12 · **Owner:** Yury Gurevich

 > Produce clearly-labelled shadow ML forecasts (sentiment + price/return) and measure
 > them via scorecards — every output is advisory and never gates a decision until
@@ -103,8 +103,9 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   last bar's date), `entry_close` (that bar's close), `horizon_sessions`, `stop_pct`, `target_pct`,
   the three probabilities, `model_id`, `model_version`, `history_bars`, `history_ref` (the
   `BarrierHistory` the bars were read from), `n_paths`, `seed`, `fit_status` (`accepted` |
-  `capped`), the fitted `garch_mu` / `garch_omega` / `garch_alpha` / `garch_beta`, `created_at` and
-  `shadow: true`, and returns a `ShadowPrediction` whose `value` is `p_target_first` and whose
+  `capped`), the fitted `garch_mu` / `garch_omega` / `garch_alpha` / `garch_beta`, `created_at`,
+  `shadow: true` and the return figures `FORE-OUT-11` names, and returns a `ShadowPrediction` whose
+  `value` is `p_target_first` and whose
   `confidence` is `history_bars ÷` the history's `sessions_requested` (at most 1). It writes no
   `ShadowPrediction` node. The claim is advisory evidence only (`FORE-NEV-01/02`).
 - **FORE-OUT-08** — Each `BarrierForecast` claim is settled against what the market did, by
@@ -118,8 +119,8 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   `claim_key`, `model_id`, `ticker`, `as_of`, `outcome` (`stop` | `target` | `neither` | `void`),
   `void_reason`, `settled_on` (the tenth session's date, or for a void the date of the pass that
   voided it), `settling_ref` (that run's `MarketData` key), `entry_close_settling`, `entry_ratio`
-  (settling ÷ claimed close), the claim's three-class `brier` (absent for `void`) and `created_at`; the
-  claim itself is never written to. `barrier_scorecard` (`BarrierScorecardRequest { model_id }`)
+  (settling ÷ claimed close), the claim's three-class `brier` (absent for `void`), the realised
+  figures `FORE-OUT-11` names and `created_at`; the claim itself is never written to. `barrier_scorecard` (`BarrierScorecardRequest { model_id }`)
   reports one model's ledger: the `settled`, `void` and `open` counts; the realised share and the mean
   declared probability of each outcome; `brier_model`; `brier_climatology` from EXP-018's fixed shares
   (stop 0.287, target 0.477, neither 0.236), never re-estimated from the ledger; `skill` = 1 −
@@ -145,6 +146,31 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   them, exactly as it would with no held claim in the ledger, and, once the ledger holds a held-name
   claim, the held claims' own counts and scores under the same names prefixed `held_`, against the
   same climatology. `sample_size` counts the buys' settled claims. *(DL-310.)*
+- **FORE-OUT-11** — Each barrier claim also states what the paths its three probabilities were counted
+  on say of its return, from that one simulation (never a second): `expected_return`, the mean over the
+  paths of the return to the first barrier or the tenth close (minus `stop_pct` on a path the stop comes
+  first on, `target_pct` on one the target comes first on, else the tenth close over the claim's close,
+  less 1; first touches by `FORE-OUT-07`'s rule); `close_return_p05`, the tenth close's return at its
+  5th percentile with the barriers ignored; and `sessions_to_target` and `sessions_to_stop`, the median
+  session (1 to 10) of that barrier's first touch over the paths it comes first on, null when it comes
+  first on none. The figures are fractions of the claim's close, and the probabilities are unchanged. A
+  claim stated before the figures existed gains them on a rerun on the same last bar, from the same
+  paths (`FORE-IDM-04`). Its settlement (`FORE-OUT-08`) records what happened by the same rule:
+  `realised_return` (minus `stop_pct`, `target_pct`, or the tenth session's close over the settling
+  close, less 1, by the outcome), `close_return` (that tenth close's return, whatever the outcome) and
+  `outcome_session` (the session, 1 to 10, of the stop's or the target's touch; null for neither); a
+  void records none of the three. They are the model's figures, never a fill's: a stop gapped through
+  still realises minus `stop_pct`. *(DL-312.)*
+- **FORE-OUT-12** — Once the ledger holds a settled claim that stated `expected_return` and whose
+  settlement recorded a `realised_return`, `barrier_scorecard` reports the return scores over those
+  claims beside `FORE-OUT-08`'s: `return_settled` (their count), `declared_return` (their mean
+  `expected_return`), `realised_return` (their mean `realised_return`), `return_bias` (the second less
+  the first) with its 95 % interval `return_bias_lo` / `return_bias_hi` from `FORE-OUT-08`'s date
+  bootstrap (the same draws and seed; absent under two dates), and `close_below_p05` (the share whose
+  `close_return` is below their `close_return_p05`: near 0.05 when the tail is calibrated). A claim
+  without the figures, or a settlement without a realised return, is counted as before and not
+  return-scored; with none, no return score is reported. Held claims' return scores carry `held_`
+  (`FORE-OUT-10`). The scorecard reports; it decides nothing (`FORE-NEV-01/02`). *(DL-312.)*

 ## Prohibitions (`NEV`)

@@ -448,3 +474,10 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   `FORE-IN-07` (the held request's prices), `FORE-TRG-01` (a run waits for its history while the book
   holds a name; one request per held name; `held_count`) and `FORE-FAIL-04` (three designed held
   refusals; malformed held prices). 25 / 52 → 28 / 55.
+- v1.12 — S288 / DL-312 (2026-10-21): each claim states its return. New `FORE-OUT-11` (from the paths
+  its probabilities were counted on: the expected return to the first barrier or the tenth close, the
+  tenth close's 5th percentile, each barrier's median session; the settlement's realised return,
+  tenth-close return and session) and `FORE-OUT-12` (the scorecard's return scores once a claim that
+  stated them settles). `FORE-OUT-07` and `FORE-OUT-08` name the new fields. Why: DL-240 reads each
+  name as a distribution, the chance of each outcome and the return in each case; the claim stated the
+  chances only, and the PM's sizing over distributions needs the return. 28 / 55 → 30 / 57.
diff --git a/agents/forecaster/laws/test-plan.md b/agents/forecaster/laws/test-plan.md
index 4490c3aa..892f8bc8 100644
--- a/agents/forecaster/laws/test-plan.md
+++ b/agents/forecaster/laws/test-plan.md
@@ -23,6 +23,8 @@
 | FORE-OUT-08 | 🟩 | `test_the_outcome_is_exp018s`, `test_the_settlement_equals_the_test_beds_outcome_on_random_paths`, `test_the_entry_is_the_settling_series_own_close`, `test_a_settlement_records_every_field_the_ledger_needs`, `test_a_split_settles_void_with_no_brier`, `test_the_settlement_passes_the_packs_vocabulary_guard`, `test_the_oracle_is_the_records_run`, `test_the_scorecard_reports_the_ledger_as_exp018_scores_it`, `test_fewer_than_two_settled_dates_give_no_interval`, `test_an_empty_ledger_reports_counts_and_no_scores`, `test_another_models_ledger_is_its_own`, `orchestration/tests/test_forecaster_settlement_stage.py::test_the_local_pipeline_settles_an_older_claim`, `test_a_pass_lists_no_claim_and_settles_the_open_ones` |
 | FORE-OUT-09 | 🟩 | `test_a_held_name_carries_its_live_stop_and_declared_target`, `test_a_pm_lineage_position_declares_its_own_target`, `test_a_target_the_lineage_does_not_declare_is_left_out`, `test_the_newest_live_placement_is_the_stop`, `test_every_held_name_gets_a_claim_request_beside_the_buys`, `test_a_held_claim_measures_its_barriers_from_its_close`, `test_past_its_target_a_held_claim_asks_for_the_width_again` |
 | FORE-OUT-10 | 🟩 | `test_held_claims_are_scored_apart_and_the_buys_scores_stand` |
+| FORE-OUT-11 | 🟩 | `test_the_figures_are_the_return_to_the_first_barrier_or_the_tenth_close`, `test_with_no_touch_a_barriers_sessions_are_absent`, `test_the_paths_are_exp018s_own`, `test_a_claim_states_its_return_from_the_paths_its_probabilities_counted`, `test_a_held_claim_states_its_return_too`, `test_a_claim_stated_before_its_figures_gains_them_on_a_rerun`, `test_a_settlement_records_the_return_its_outcome_gave`, `test_a_session_touching_both_is_the_stop_and_its_session`, `test_a_void_settlement_records_no_return` |
+| FORE-OUT-12 | 🟩 | `test_the_return_scores_appear_once_a_claim_that_stated_one_settles`, `test_held_claims_return_scores_are_apart`, `test_a_claim_or_settlement_without_figures_is_not_return_scored`, `test_the_bias_interval_resamples_whole_dates`, `test_the_tail_share_counts_closes_strictly_below_their_percentile` |
 | FORE-NEV-01 | 🟩 | `test_every_forecast_is_a_shadow_signal`, `test_contract_declares_never_clauses_and_no_external_io`, `test_a_full_deployed_pass_never_reaches_the_decision_path`, `test_nothing_outside_the_forecaster_reads_the_ledger` |
 | FORE-NEV-02 | 🟩 | `test_contract_declares_never_clauses_and_no_external_io`, `test_served_forecast_is_request_triggered_shadow_only`, `test_forecast_factor_enabled_writes_shadow_only_prediction`, `test_a_full_deployed_pass_never_reaches_the_decision_path`, `test_nothing_outside_the_forecaster_reads_the_ledger` |
 | FORE-NEV-03 | 🟩 | `test_scorecard_is_never_promotion_eligible`, `test_contract_declares_never_clauses_and_no_external_io`, `test_the_scorecard_reports_the_ledger_as_exp018_scores_it` |
@@ -59,4 +61,4 @@
 | FORE-PERF-04 | 🟩 | `test_a_runs_claims_read_its_history_once`, `test_a_history_the_provider_writes_later_is_read_when_it_lands`, `test_a_pass_lists_no_claim_and_settles_the_open_ones` |
 | FORE-CAP | ⬜ | — |

-## **Green: 28 / 55**
+## **Green: 30 / 57**
diff --git a/agents/forecaster/tests/test_barrier_claim.py b/agents/forecaster/tests/test_barrier_claim.py
index 839e0de3..283e49e9 100644
--- a/agents/forecaster/tests/test_barrier_claim.py
+++ b/agents/forecaster/tests/test_barrier_claim.py
@@ -59,6 +59,10 @@ _CLAIM_FIELDS = {
     "garch_beta",
     "created_at",
     "shadow",
+    "expected_return",
+    "close_return_p05",
+    "sessions_to_target",
+    "sessions_to_stop",
 }


diff --git a/agents/forecaster/tests/test_barrier_settlement_record.py b/agents/forecaster/tests/test_barrier_settlement_record.py
index b17ce31f..1f0f5674 100644
--- a/agents/forecaster/tests/test_barrier_settlement_record.py
+++ b/agents/forecaster/tests/test_barrier_settlement_record.py
@@ -68,6 +68,9 @@ def test_a_settlement_records_every_field_the_ledger_needs() -> None:
         "entry_close_settling": 100.0,
         "entry_ratio": 1.0,
         "brier": pytest.approx(0.38, abs=1e-12),
+        "realised_return": 0.07,
+        "close_return": 0.0,
+        "outcome_session": 2,
     }
     assert created.tzinfo is not None
     assert list(graph.descendants(claim, max_depth=1, edge_types={"SETTLED_BY"})) == [
diff --git a/docs/laws/INDEX.md b/docs/laws/INDEX.md
index 4bea1a93..06adaf35 100644
--- a/docs/laws/INDEX.md
+++ b/docs/laws/INDEX.md
@@ -46,7 +46,7 @@ Each agent's law files live at `agents/<name>/laws/`:
 | execution | ✅ LOCKED **v1.16** (S283, DL-306) | 45 / 70 | S283 (DL-306) adds and proves `EXEC-OBS-08` (no broker read is cut at a page limit; run-start reconciliation reads every order the graph waits on, by id where no listing shows it) and `EXEC-PERF-03` (a run-start broker read is bounded by the book), with PARAM row `broker_recent_order_days`. S280 (DL-303) amends and proves `EXEC-OUT-07` (an order the broker ended after filling part of it is a fill of that part, its rest told once) and adds and proves `EXEC-TYP-04` (`Fill.broker_filled_quantity`, read by every reader of an executed size); `EXEC-OBS-06` matches on the filled quantity. S279 (DL-302) adds and proves `EXEC-PERF-02`: the drop sweep reads each label once, sees written drops and contains one failed-read fault; the stop plan shares one lazy Fill read; no decision changes. S258 (DL-276) reconciles `PARAM` only: the bounds of `slippage_bps`, `min_promotion_runs`, `min_approval_rate` and `alpaca_timeout` follow the code, no clause changes; S252 / DL-261: `EXEC-TRG-07` bounds sync requests; new proven `EXEC-TRG-08` names graph-pull submit and its candidate/grace rule; DRIFT-100 corrected, 40 / 66. S251 adds and proves `EXEC-IDN-04` (the divergence-family Flag exception, `owns_graph` widened; DRIFT-094), names the contract's fields in `EXEC-OUT-01/02/04/05` (DRIFT-061) and narrows `EXEC-TYP-03`'s version sentence (DRIFT-060); S248 adds/proves `EXEC-OBS-07`: a broker-position divergence is flagged per episode, `critical` only when it survived a run, whatever the ticker's history; S230 adds/proves `EXEC-OBS-06`: the broker stop is the PM-decided stop, read through the shared resolver, and a mismatched live stop is replaced in place with `replaced_at`/`replaces` markers; S227 adds/proves `EXEC-NEV-07`: degraded `RunRequest`s hold buys without deliberation wait while exits and protective stops continue; DL-203 reconciles `PARAM` only; S209 amends `EXEC-OBS-05` so the stale-order sweep compares stop identity, not liveness views, without moving the count; S205 rewrites `EXEC-TYP-03` into required fields and records DRIFT-060/DRIFT-061; S190 adds/proves `EXEC-OBS-05`, the missing `EXEC-OBS-03` liveness limb, and `EXEC-STA-05`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
 | monitor | ✅ LOCKED v1.4 (S279, DL-302) | 22 / 47 | S279 (DL-302) adds and proves `MON-PERF-03`: the end-of-run evaluation shares one lazy Fill read across the book and retains each decided width; no decision changes. S252 / DL-261: `MON-TRG-02` bounds both work kinds, sync from requests and their linked snapshot; DRIFT-097 corrected, 21 / 46 unchanged. S251 names the graph-pull triggers in `MON-TRG-02` (DRIFT-086) and files DRIFT-097 for the unbounded sync poll; S205 rewrites and proves `MON-TYP-01`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
 | reporter | ✅ LOCKED v1.5 (S253, DL-262, DL-263) | 26 / 43 | S253 rewrites `RPT-OUT-02` (book counts from the broker's fills in the run's window, outcomes since the inception; DRIFT-099), amends `RPT-IN-01` and `RPT-NEV-03` (DRIFT-101), and adds and proves `RPT-IDM-04`; S251 names the run's own benchmark lineage in `RPT-OUT-07` (DRIFT-087) and the graph-pull trigger in `RPT-TRG-02` (DRIFT-086); v1.3 (DL-224) latest-per-date snapshot; S226 adds benchmark-relative `performance_metrics`, as-of bounded graph reads, contained performance failure, and backward-compatible snapshots; S205 rewrites `RPT-TYP-01`; S156 removed orphan `RPT-OBS-03`; S204 gives every clause a row and makes rowless clauses a hard gate |
-| forecaster | ✅ LOCKED v1.11 (S286, DL-310) | 28 / 55 | S286 / DL-310: a barrier claim on every held name, its live stop and declared target from the claim's close (`FORE-OUT-09`), held claims scored apart (`FORE-OUT-10`), one history read per run and open-claims-only settlement (`FORE-PERF-04`); 25 / 52 → 28 / 55. Before: S252 / DL-261: `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged. S251 names the four legs (`FORE-IDN-01`), one node per prediction (`FORE-OBS-01`; DRIFT-081) and the shadow scorecards' subject (`FORE-IDM-03`; DRIFT-083); S243 amends and re-proves `FORE-FAIL-04` (a designed refusal is a `warning`, a missing input an `error`); S241 adds and proves `FORE-OUT-08`, `FORE-IDM-05`, `FORE-FAIL-05` (the settlement of each barrier claim and `barrier_scorecard`) and amends `FORE-IDN-02`/`TRG-01`/`OUT-03`; the S239 second follow-up (D10) re-words the barrier clauses for the provider-written history; the S239 follow-up amends `FORE-TRG-01`/`FORE-TRG-02` (graph-pull trigger; the deployed loop fires `forecast_barrier` only); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim); DL-203 reconciled `PARAM`; S205 proved `FORE-TYP-01`; counters are clauses proven / clauses declared |
+| forecaster | ✅ LOCKED v1.12 (S288, DL-312) | 30 / 57 | S288 / DL-312: each claim states, from the paths its probabilities were counted on, its expected return, the tenth close's 5th percentile and each barrier's median session, and its settlement the realised return (`FORE-OUT-11`); the scorecard's return scores (`FORE-OUT-12`); 28 / 55 → 30 / 57. Before: S286 / DL-310: a barrier claim on every held name, its live stop and declared target from the claim's close (`FORE-OUT-09`), held claims scored apart (`FORE-OUT-10`), one history read per run and open-claims-only settlement (`FORE-PERF-04`); 25 / 52 → 28 / 55. Before: S252 / DL-261: `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged. S251 names the four legs (`FORE-IDN-01`), one node per prediction (`FORE-OBS-01`; DRIFT-081) and the shadow scorecards' subject (`FORE-IDM-03`; DRIFT-083); S243 amends and re-proves `FORE-FAIL-04` (a designed refusal is a `warning`, a missing input an `error`); S241 adds and proves `FORE-OUT-08`, `FORE-IDM-05`, `FORE-FAIL-05` (the settlement of each barrier claim and `barrier_scorecard`) and amends `FORE-IDN-02`/`TRG-01`/`OUT-03`; the S239 second follow-up (D10) re-words the barrier clauses for the provider-written history; the S239 follow-up amends `FORE-TRG-01`/`FORE-TRG-02` (graph-pull trigger; the deployed loop fires `forecast_barrier` only); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim); DL-203 reconciled `PARAM`; S205 proved `FORE-TYP-01`; counters are clauses proven / clauses declared |
 | operator | ✅ LOCKED v1.10 (S269, DL-292) | 20 / 51 | S269 (DL-292) rewords and re-proves `OPR-FAIL-02`: only text, a number or a boolean is a value; `null`, lists and objects are omitted from required and optional parameters, so missing required values are refused with the existing sentence and audit, while scalar text and blank-text behavior are unchanged; DRIFT-112 corrected; no clause added; before that S268 (DL-290) rewords and re-proves `OPR-FAIL-02`: an intent of no known family, or lacking a parameter its family requires under any accepted name, is refused before its audit, which reads `refused`, and no `Intent` is written; the prompt states each family's parameter names; DRIFT-109 corrected; no clause added; before that S265 (DL-286) rewords and re-proves `OPR-FAIL-01`: failed requests are audited on both capabilities, one operator fault and one plain reason, no grammar or error text in graph; malformed JSON is a fault-free refusal; DRIFT-107/108 corrected; no clause added; before that S264 (DL-285) re-proves `OPR-STA-03` for vendor stop reasons and billed counts on both reply paths and adds/proves `OPR-FAIL-04` for audited, fault-free cut-offs with one sentence and explicit grammar preserved; DRIFT-106 corrected; before that S263 (DL-284) amends and re-proves `OPR-DEP-01` for provider effort resolution and pre-call model-family refusal; PARAM effort and CAP reconciled; before that S262 (DL-282) amends and re-proves `OPR-DEP-01` for the selected vendor, model resolution and no fallback; PARAM reconciled; before that S256 (DL-272) rewrites and proves `OPR-IDM-02`: duplicate commands share the audit and intent, but every model call has its own ledger row; DRIFT-104 corrected; S222 proves `OPR-SEC-01` key containment and `OPR-DEP-01` Anthropic-only dependency; S205 rewrites and proves `OPR-TYP-01`; counters are clauses proven / clauses declared |
 | supervisor | ✅ LOCKED v1.3 (S251, DL-260) | 23 / 48 | S251 declares the divergence-family exception in `SUP-IDN-02` (DRIFT-094) and proves `SUP-OBS-02` (DRIFT-076); v1.2 (DL-225) `last_successful_run`; S205 rewrites and proves `SUP-TYP-01`; S179 proves append-only `FaultResolution` retirement (`SUP-OBS-03`); counters are clauses proven / clauses declared |
 | curator | ✅ LOCKED v1.1 (S205) | 23 / 47 | S205 rewrites and proves `CUR-TYP-01`; counters are clauses proven / clauses declared |
diff --git a/docs/laws/ledger.md b/docs/laws/ledger.md
index 8744db40..8df0441e 100644
--- a/docs/laws/ledger.md
+++ b/docs/laws/ledger.md
@@ -38,7 +38,7 @@ and torn down to zero. Historical Neo4j rows remain valid evidence for the pre-S
 | provider | ✅ v1.11 (LOCKED) | 24 / 67 | 🟨 partial — **24 of 67 clauses proven** after S286 (DL-310) amends `PROV-TRG-04` and `PROV-OUT-08` (the barrier history holds every held name) and S266 (DL-287) amends and re-proves `PROV-OUT-08`: the barrier history ends on the run's as-of by lineage whenever the provider reaches it, missing lineage serves the fetch's UTC date, and a broken stored date raises before any fetch or history write (DRIFT-110); count unchanged; before that S255 (DL-269) amends and re-proves `PROV-OUT-02`: the regime records its four label thresholds; count unchanged; before that S251 (DL-260) amends four clauses to the code: `PROV-TRG-01` names every recorded data need (a bus request, an unconsumed `RunRequest`, an `AnalystRun`'s qualifying buys) and is re-proven with no bus event (DRIFT-082); `PROV-TRG-02` states the poll's key-and-edge bound and turns green (DRIFT-086); `PROV-OUT-07` says served bars are raw (DRIFT-084); `PROV-OUT-04` is narrowed to fetch time and the fallback flag and turns green (DRIFT-040, the vendor gap is work-queue 105); before that S249 (DL-256) adds and proves `PROV-TRG-05`: an ingest a `RunRequest` triggers serves that run's as-of whenever the provider reaches it (window, coverage check, regime, news and earnings anchors), an unusable as-of is refused before any fetch, and an ingest with no run serves today (DRIFT-095); before that S243 (DL-247) adds and proves `PROV-OUT-09`: the extreme-move guard judges each ticker's newest session only, against that session's cross-section, so a real extreme day in a name's history never drops it (DRIFT-088), and states the guard's √(n−1) ceiling (DRIFT-090, CORRECTED: the barrier path leans on the daily request's guard, DL-247 D4); `PROV-OUT-08` amended and re-proven; before that S239 (DL-241 D10) adds and proves `PROV-TRG-04` / `PROV-OUT-08` (the `BarrierHistory` per `AnalystRun`, one batched fetch, dropped tickers named, a failed fetch still written); before that S238 adds and proves `PROV-OUT-07`: a bar's volume is the consolidated tape's (the Alpaca feed defaults to SIP), a SIP request never ends inside the plan's 15-minute recent-data window, and a refusal fails loud with no IEX fallback (DRIFT-080); S213 sharpens and proves `PROV-OUT-03` for FMP `^VIX` freshness without adding clauses; S187 added PARAM rows only; S204 gives every clause a row and promotes missing rows to a hard gate; S169-sweep demoted `PROV-OUT-04` |
 | scanner | ✅ v1.5 (LOCKED) | 18 / 41 | 🟨 partial — **18 of 41 clauses proven**: S259 (DL-276) reconciles `PARAM` only (the upper bound of `min_average_volume` follows the code; no clause moves); S251 (DL-260) names the graph-pull trigger in `SCAN-TRG-02` (a `MarketData` with no `SCANNED_BY` edge, found by key and edge; DRIFT-085) and narrows `SCAN-TYP-01`'s version sentence (DRIFT-060), count unchanged; S205 rewrites `SCAN-TYP-01` into required fields and closes DRIFT-047 without moving the count; S183 added and proved `SCAN-OUT-06`/`SCAN-OUT-07`; S204 gives every clause a row and promotes missing rows to a hard gate |
 | analyst | ✅ v1.12 (LOCKED) | 31 / 54 | 🟨 partial — **31 of 54 clauses proven** after S284 (DL-308) adds and proves `ANLZ-OUT-11`: the lexicon sentiment pillar scores only headlines that name the ticker's company, no pillar below two; before that S279 (DL-302) adds and proves `ANLZ-PERF-02`: the held-stop read shares one lazy Fill read across the book and retains each lineage width, no decision changes; before that S259 (DL-276) reconciles `PARAM` only (the bounds of `scaled_stop_atr_multiplier` follow the code; no clause moves) and S255 (DL-269) adds and proves `ANLZ-OUT-10`: each scored recommendation records its constants and actual mean order; before that S253 (DL-263) adds and proves `ANLZ-IN-05`: a candidate under `required_history_bars` is scored on the indicators its bars allow, each missing core indicator visible as `<metric>_missing_bars`, and only fewer than `min_history_bars` rejects (DRIFT-096); before that S251 (DL-260) adds and proves `ANLZ-OUT-09`: a held position's stop check reads the shared stop-width resolver, a close at or below the decided stop is a forced `stop` sell, a live broker stop owns the exit, an unreadable book is a fault (DRIFT-074); `ANLZ-TRG-02` names the graph-pull trigger (DRIFT-086); before that S211 adds and proves `ANLZ-OBS-06`: decision-time favourable-excursion target evidence is measured from prior settled windows, serialized, and missing evidence rejects instead of falling back to a constant target; S205 rewrites `ANLZ-TYP-01` into required fields without moving the count; S198 adds and proves `ANLZ-OBS-05`; S186 adds and proves `ANLZ-OBS-04`; S204 gives every clause a row and promotes missing rows to a hard gate · S152 declared 3 new clauses (43→46) · S169-sweep demoted `ANLZ-OBS-01` |
-| forecaster | ✅ v1.11 (LOCKED) | 28 / 55 | 🟨 partial — **28 of 55 clauses proven** after S286 (DL-310): a barrier claim on every held name (`FORE-OUT-09`, `FORE-OUT-10`, `FORE-PERF-04` new and green); before that, 25 / 52 after S252 (DL-261): `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged; v1.9 (S251, DL-260) names the four legs in `FORE-IDN-01`, one recorded node per prediction in `FORE-OBS-01` (DRIFT-081) and the three shadow scorecards in `FORE-IDM-03` (DRIFT-083), all still gray, count unchanged; v1.8 (S243, DL-247) amends and re-proves `FORE-FAIL-04`: a designed "no claim" records a `warning`, a missing or broken input an `error` (DRIFT-089), count unchanged; after S241 (DL-243) adds and proves `FORE-OUT-08` (each claim settled once by EXP-018's rule from a provider-written `MarketData`; `barrier_scorecard` over EXP-018's fixed climatology), `FORE-IDM-05` (settled once, one pass per run) and `FORE-FAIL-05` (void with a named reason, never a false outcome), and amends and re-proves `FORE-IDN-02`/`TRG-01`/`OUT-03`; v1.6 (S239, DL-241 D10) re-words `FORE-IN-07`/`TRG-01`/`OUT-07`/`IDM-04`/`FAIL-04`/`NEV-04` for the provider-written history, count unchanged; before that the S239 follow-up amends and re-proves `FORE-TRG-01`/`FORE-TRG-02` (the deployed graph-pull loop fires `forecast_barrier` only; count unchanged); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim), each proven; 27 have a gray row |
+| forecaster | ✅ v1.12 (LOCKED) | 30 / 57 | 🟨 partial — **30 of 57 clauses proven** after S288 (DL-312): each claim states its return and its settlement what happened (`FORE-OUT-11`), the scorecard's return scores (`FORE-OUT-12`), both new and green; before that, 28 / 55 after S286 (DL-310): a barrier claim on every held name (`FORE-OUT-09`, `FORE-OUT-10`, `FORE-PERF-04` new and green); before that, 25 / 52 after S252 (DL-261): `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged; v1.9 (S251, DL-260) names the four legs in `FORE-IDN-01`, one recorded node per prediction in `FORE-OBS-01` (DRIFT-081) and the three shadow scorecards in `FORE-IDM-03` (DRIFT-083), all still gray, count unchanged; v1.8 (S243, DL-247) amends and re-proves `FORE-FAIL-04`: a designed "no claim" records a `warning`, a missing or broken input an `error` (DRIFT-089), count unchanged; after S241 (DL-243) adds and proves `FORE-OUT-08` (each claim settled once by EXP-018's rule from a provider-written `MarketData`; `barrier_scorecard` over EXP-018's fixed climatology), `FORE-IDM-05` (settled once, one pass per run) and `FORE-FAIL-05` (void with a named reason, never a false outcome), and amends and re-proves `FORE-IDN-02`/`TRG-01`/`OUT-03`; v1.6 (S239, DL-241 D10) re-words `FORE-IN-07`/`TRG-01`/`OUT-07`/`IDM-04`/`FAIL-04`/`NEV-04` for the provider-written history, count unchanged; before that the S239 follow-up amends and re-proves `FORE-TRG-01`/`FORE-TRG-02` (the deployed graph-pull loop fires `forecast_barrier` only; count unchanged); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim), each proven; 27 have a gray row |
 | portfolio_manager | ✅ v1 (LOCKED, amended **v1.12**) | 33 / 51 | 🟨 partial — **33 of 51 clauses proven** after S259 (DL-276) reconciles `PARAM` only (the bounds of six rows follow the code; no clause moves) and S251 (DL-260) narrows `PM-OBS-01`/`PM-OUT-06`/`PM-STA-04` to what `PMRun` and `OrderIntentResult` carry (the `portfolio_state_snapshot` promise withdrawn, DRIFT-039; `PM-STA-04` now green), makes `PM-OBS-04` per candidate (DRIFT-065), uses the emitted reason strings in `PM-OUT-03` (DRIFT-037), names the graph-pull trigger in `PM-TRG-02` (DRIFT-086) and narrows `PM-TYP-03`'s version sentence (DRIFT-060); DRIFT-098 filed for `PM-OUT-01`/`PM-TYP-03`; before that S240 adds and proves `PM-IN-05`: a run weighs each held ticker once at its own snapshot mark (adoption mark, then cost, as fallbacks) and a resumed run reads the snapshot of the run it resumes, closing DRIFT-079; `PM-IDN-01` stays gray (current-state conjunct proven, the whole-purpose boundary proof still owed); S220 amends and re-proves `PM-NEV-08` / `PM-OBS-03`: correlated issuers contribute on the ADR-0030 `0.50..0.90` ramp and gate detail renders the applied weights; S211 adds and proves `PM-OBS-05`: reward-risk now compares measured target evidence against stop risk, varies across measured profiles, and rejects measured upside below measured downside at the configured floor; S210 amends `PM-NEV-06`/`PM-NEV-08`/`PM-NEV-09` so concentration ratios use deployed capital and deployment-floor evidence is explicit without moving the count; S208 declares and proves `PM-OBS-04`; S197 declared and proved `PM-OBS-03`; S184 made PM-NEV-07/08/09 green and closed the v1.3 widened PM-NEV-06 and PM-TYP-03 rows |
 | deliberator | ✅ v1.18 (LOCKED) | 35 / 66 | S277 (DL-289 amendment 4) adds and proves DLIB-FAIL-05, refusal-only sticky switching with one model-attributed row per attempt; re-proves DLIB-FAIL-01, DLIB-OUT-02 (always-written llm_switches) and DLIB-DEP-05 (handed-over fallback construction). S276 (DL-289 amendment 1) adds and proves DLIB-DEP-05 and DLIB-NEV-11; amended DLIB-OUT-02 re-proven for the models that answered; effort defaults to empty. 🟨 partial — **35 of 66 clauses proven** after S257 (DL-274) reconciles `PARAM` only (the output cap 16,384, the peer wait up to 300 seconds; no clause moves) and S256 (DL-272) adds and proves `DLIB-IDM-04` (settle-on-take and visible reply faults), `DLIB-OBS-08` (every completion is its own row), and proves spend attribution `DLIB-OBS-02`; S255 (DL-269) adds and proves `DLIB-OUT-08`: recorded arithmetic reproduces before rendering, with first-failure withholding and old-packet parity; DRIFT-102/103 corrected; before that S254 / ADR-0032: `DLIB-NEV-10` proves prompt libraries use only the agent's own client; before that S252 (DL-261): `DLIB-TRG-01` now proven for the key-and-edge candidate bound and order-property filter, 27 / 59; before that S246 (DL-252) adds and proves `DLIB-OUT-06` (each defender and challenger turn records its guided reasoning, readings then gaps before the argument, exactly as written or why it could not be read, and an unreadable one never fails the turn or the order) and `DLIB-OUT-07` (each debated order's record carries its decision and evidence packet), and amends `DLIB-TYP-01` (`DebateTurnRecord.reasoning`, `.reasoning_error`); before that S245 (DL-251) adds and proves `DLIB-NEV-09`: every fact the challenger and judge prompts state about our code is pinned by a test that reads that code, the false calendar-day staleness fact and the stale name-correlation example are gone (DRIFT-092), and the champions rebuild byte for byte from pack-side sources; before that S222 moves its vendor adapters to `kernel/` and proves `DLIB-SEC-02` with a key-containment sentinel; S214 narrows `vetoed_tickers` to `overturn` verdicts only, routes unreadable judge answers through loud fail-open, and proves `DLIB-OUT-04`; S206 adds and proves `DLIB-NEV-08`: rendered debate-context verdicts name their enforcing check and agent, while descriptive stop-target regime evidence has no verdict; S205 rewrites and proves `DLIB-TYP-01`; S200 adds `DLIB-OBS-07` and promotes `DLIB-IDM-02`; S199 adds `DLIB-OBS-05`/`DLIB-OBS-06`; S172 proves concurrent-order record order and pending-reply handling; S194 adds `DLIB-OBS-04`; S189 added stop-reason audit evidence; S167 proves queryable fail-open causes |
 | execution | ✅ v1.16 (LOCKED) | 45 / 70 | 🟨 partial — **45 of 70 clauses proven** after S283 (DL-306) adds and proves `EXEC-OBS-08` (no broker read is cut at a page limit; run-start reconciliation reads every order the graph waits on, by id where no listing shows it) and `EXEC-PERF-03` (a run-start broker read is bounded by the book: open orders, the recent window, the waiting Fills), with PARAM row `broker_recent_order_days`; before that S280 (DL-303) amends and proves `EXEC-OUT-07` (a partly filled ended order is a fill of its part, its rest told once) and adds and proves `EXEC-TYP-04` (`Fill.broker_filled_quantity`, read by every reader of an executed size), `EXEC-OBS-06` matching on the filled quantity; before that S279 (DL-302) adds and proves `EXEC-PERF-02`: the drop sweep reads each label once, sees written drops and contains one failed-read fault, and the stop plan shares one lazy Fill read, no decision changes; before that S258 (DL-276) reconciles `PARAM` only (the bounds of four rows follow the code; no clause moves) and S252 (DL-261): `EXEC-TRG-07` bounds sync requests; new proven `EXEC-TRG-08` names graph-pull submit and its candidate/grace rule; DRIFT-100 corrected, 40 / 66; before that S251 (DL-260) adds and proves `EXEC-IDN-04`: execution writes divergence-family `Flag`/`FlagResolution` nodes and no others, both labels now in `owns_graph` as the one declared shared pair (DRIFT-094); `EXEC-OUT-01`/`-02`/`-04`/`-05` name the contract's fields (DRIFT-061); `EXEC-TYP-03`'s version sentence (DRIFT-060); before that S248 adds/proves `EXEC-OBS-07`: a broker-position divergence is flagged per episode (`warn` at first sight under a subject naming the first-sight snapshot, `critical` only if still present at the next run-start reconciliation, a new episode at `warn` whatever the ticker's history, one unresolved Flag per live divergence); S230 adds/proves `EXEC-OBS-06`: the broker stop's width comes through the shared stop-width resolver (PM lineage first, fallback only without it) and a live stop resting off its decided price is replaced in place, never cancelled and re-placed; S227 adds/proves `EXEC-NEV-07`: degraded `RunRequest`s hold buys without deliberation wait while exits and protective stops continue; S209 amends `EXEC-OBS-05` so the stale-order sweep compares stop identity, not liveness views, without moving the count; S205 rewrites `EXEC-TYP-03` into required fields and records DRIFT-060/DRIFT-061; S190 added/proved `EXEC-OBS-05`, the missing `EXEC-OBS-03` liveness limb, and `EXEC-STA-05`; S204 gives every clause a row and promotes missing rows to a hard gate |
```
