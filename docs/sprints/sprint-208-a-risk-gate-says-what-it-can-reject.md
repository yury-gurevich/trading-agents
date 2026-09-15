<!-- Agent: planning | Role: sprint handover -->
# Sprint 208 — a risk gate says what it can reject

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-208-a-risk-gate-says-what-it-can-reject`
**Status:** BUILT
**Version:** `0.98.05`
**Effort:** M–L
**Decisions:** [DL-169](../design-log.md) the open thread · `DRIFT-063` the row this opens · work-queue items **60** and **61**

> **Why this bump kind.** PATCH. No agent gains a capability. The PM already promises a measured
> correlation cap (`PM-NEV-08`) and a gate that never records an unevaluable comparison as passed
> (`PM-NEV-09`). Presenting a global constant as a risk verdict, and abandoning a whole gate on the
> first unusable pair, are those promises broken — not new ones made. The new clause codifies the
> existing intent.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`PM-NEV`**, **`PM-OBS`**, **`PM-OUT`**, **`PM-TYP`**.

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

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**`contracts/` — No.** *[measured 2026-09-15]* `GateOutcome` already carries `name`, `value`,
`threshold`, `outcome` and a free-text `detail` (`contracts/portfolio_manager.py`), and `GateStatus`
already has the three states `PASSED` / `FAILED` / `NOT_EVALUATED` that S184 added. Everything this
sprint renders fits in `detail`. Confirm with `git diff --stat contracts/` — **it must be empty.**

**A new guarantee — Yes, one.** The PM will promise something its law book does not currently say:
that a gate which reports a `PASSED`/`FAILED` verdict discloses whether it *could* have produced the
other answer. So this sprint **owes a full law cycle**: `PM-OBS-04`, a `test-plan.md` row, the clause
ID in the test docstrings, `laws.md` **v1.4 → v1.5** with a Changelog line, and the rollup updated in
**both** `docs/laws/ledger.md` **and** `docs/laws/INDEX.md`. 🪤 **The rollup is derived, not
declared** — `make ci` recomputes it. Let the gate tell you the number.

🪤 **`PM-OBS-04` and `PM-NEV-10` are both free** *[verified 2026-09-15: highest declared are
`PM-OBS-03` and `PM-NEV-09`]*. This sprint wants the **OBS** one — the defect is what the gate
*discloses*, not a new prohibition. If you find yourself writing a `NEV` clause, re-read scope.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/portfolio_manager/domain/gate_report.py` | `agents/portfolio_manager/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `PM-OUT-*` (the gate report is PM output); `PM-OBS-03` (the *shape* this sprint follows — an evaluated gate reports what it examined) |
| `agents/portfolio_manager/domain/correlation.py` | same | `PM-NEV-08` (measured correlated-cluster cap), `PM-NEV-09` (never record an unevaluable gate as passed), `PM-OBS-03` |
| `agents/portfolio_manager/domain/correlation_census.py` | same | `PM-OBS-03` is *its* clause — the census is what it renders |
| `agents/portfolio_manager/laws/laws.md` | itself, plus `conventions.md` §2 (append-only IDs) | You are adding `PM-OBS-04`. **LOCKED v1.4** — a deliberate cycle, not a quiet edit |

⚠️ **The invariant this sprint must not break: the PM may reject an order, and this sprint must not
change which orders it rejects — except where the correlation gate previously abandoned itself.**
`reward_risk`'s verdict and threshold do **not** move. If `make ci` shows an approved/rejected count
changing in any fixture other than the pairwise-skip ones, stop and report.

---

## Goal

Every PM gate that renders `PASSED` or `FAILED` discloses whether the other answer was reachable —
and the correlation gate stops abandoning itself for every candidate because of one unusable pair.

---

## Why (context)

### Measured, 2026-09-15 — read these before designing

**All figures below were measured against the live spine on 2026-09-15 by the planning session, at
`main` @ `deca4e9` with the fleet on `:s206`.** They supersede the numbers carried in work-queue
items 60 and 61, which were counted over a different denominator. Where a carried number moved, the
row below says so.

🪤 **The denominator first, because both carried rows got it wrong.** The spine holds **273**
`OrderIntent` nodes, but only **35** carry gate outcomes at all — the other **238** are pre-S183/S184
records from **2026-07-07 → mid-August** whose `gate_report` entries have `outcome: null`. Outcome
recording begins **2026-08-20**. So the honest denominator for *any* gate-outcome claim is **35
approved orders across 15 trading days**, not 181 and not 170. **Re-derive it yourself before you
quote it** — the query is four lines and it is T0.

**1. `reward_risk` is one number.** Across every recorded gate entry the value is
**`{2.0: 256}` — 256 recordings, one distinct value** — against `min_reward_risk_ratio = 1.5`
(`agents/portfolio_manager/settings.py:67`). The gate is at
`agents/portfolio_manager/domain/gate_report.py:57-75`.

🚨 **It is a constant by construction, in both stop modes, in every regime — proven in code, not
inferred from the sample:**

- `_scaled_target = min(flat_target × (scaled_stop / flat_stop), _MAX_PCT)`
  (`agents/analyst/domain/stop_target.py:89`, in `_scaled_target` at `:86`). Divide by `scaled_stop` and the mode cancels:
  **ratio ≡ `flat_target / flat_stop`**, whatever ATR does to the stop. The floor/ceiling clamps on
  the *stop* (`stop_target.py:79-83`) cancel with it. Only the `_MAX_PCT` clamp on the *target* could
  break the identity, and it has never bitten.
- `flat_target` and `flat_stop` are `base_take_profit_pct` and `base_stop_loss_pct`, and
  `agents/provider/agent.py:155-161` returns **both straight from settings** — `0.10` and `0.05`
  (`agents/provider/settings.py:23,29`). 🚨 **The regime `label` is computed and then never touches
  them.** So the ratio is `0.10 / 0.05` = **2.0 in `calm`, in `neutral`, in `stressed`** — there is no
  regime in which this gate can discriminate.

**2. Neither gate has ever rejected an order.** The spine holds **919** `Rejection` nodes and their
complete reason census is: `hold_recommendation` **848**, `sector_name_count` **30**, `sizing` **19**,
`account_unavailable` **18**, `max_positions` **3**, `insufficient_cash` **1**. 🎯 **`reward_risk`
appears zero times. `correlated_cluster_pct` appears zero times.** Other gates *do* fire — this is not
"the PM never rejects", it is these two specifically.

**3. The correlation gate's abort path is real code and has never run.** `_unevaluated_pair`
(`agents/portfolio_manager/domain/correlation.py:98-110`) walks held issuers in sorted order and
`return`s on the **first** one whose best overlap is under `min_correlation_bars = 60`; its caller
(`correlation.py:63-66`) then returns that single `NOT_EVALUATED` outcome **for the whole gate**. One
short-history holding would switch correlation checking off for every candidate that night.

🪰 **But measured: it has never fired.** All **35** recorded evaluations are `passed` — **0 failed, 0
not-evaluated** — and the observed `min_pair_overlap_bars` is **81–82** against a threshold of **60**.
**This is repair before it bites, and the spec says so rather than dressing it as a live incident.**
Work-queue item 61's *"absent from the other ~150 order evaluations"* is explained by the
pre-2026-08-20 era, **not** by the disable path. Correct the row.

**4. S197's census works, and it is what makes the real story visible.** `PM-OBS-03` shipped
2026-09-05 and **7** of the 35 records carry the census fields. They show the gate is honest and
narrow at once:

```text
2026-09-14 WFC  passed  candidate_issuer=WFC; cluster_issuers=USB,WFC; examined_issuers=24;
                        correlated_issuers=USB:0.7054; below_threshold_top=C:0.6650,SCHW:0.3856,BMY:0.2185;
                        correlation_threshold=0.7000; min_pair_overlap_bars=81
2026-09-14 MDLZ passed  cluster_issuers=MDLZ; examined_issuers=25; correlated_issuers=none;
                        below_threshold_top=KO:0.6397,KHC:0.6175,MO:0.5780; correlation_threshold=0.7000
```

🎯 **The cluster is one name in 19 of 35 evaluations and two in the other 16 — it has never had
three.** USB clears 0.70 by **0.0054**; C misses it by **0.0350**. The referee's recurring objection —
*"`cluster_issuers` enumerates clusters that omit co-held names"* — is **correct as an observation and
already disclosed** by `below_threshold_top`. 🪤 **That makes the cutoff a tunable question, not a
defect, and it is explicitly out of scope here.**

---

## Scope — and what is deliberately NOT here

**In scope — two gates, audited as a pair because they share the same law family and the same
symptom.**

| # | Site | Today | After |
| --- | --- | --- | --- |
| 1 | `reward_risk` (`gate_report.py:57-75`) | `value=2.0 threshold=1.5 -> PASSED`, indistinguishable from a risk check that discharged | **Keep the verdict and the threshold.** Add the disclosure: the ratio is **structurally determined** by the two regime constants, and the detail names them and the applied mode |
| 2 | `_unevaluated_pair` (`correlation.py:98-110`) | First unusable held issuer returns `NOT_EVALUATED` **for the whole gate** | **Evaluate pairwise.** Skip only the unusable pair; the gate evaluates on what remains, and the census reports how many pairs were skipped and why |
| 3 | `CorrelationCensus.detail()` (`correlation_census.py:48-56`) | Reports `examined_issuers`, `correlated_issuers`, `below_threshold_top`, `correlation_threshold`, `min_pair_overlap_bars` | **Gains `skipped_pairs=N`** so the honest-state signal `PM-NEV-09` protects survives the change from whole-gate to per-pair |
| 4 | `PM-OBS-04` + `DRIFT-063` | — | The clause, the test-plan row, the register row |

🪤 **Case 2 changes what the gate can reject.** Today a thin-history holding silently disables the cap;
after this, the cap evaluates on the usable pairs and **could reject**. That is the point, and it is
also why the invariant note above asks you to check fixture approve/reject counts deliberately.

🪤 **If every pair is unusable, the gate is still `NOT_EVALUATED` for the whole candidate.** Do not
degrade that into a pass. `PM-NEV-09` is not weakened by this sprint — it is made narrower in scope
and kept absolute.

**Explicitly NOT here — each is a separate decision, and taking one on is scope creep:**

- ❌ **Do not change `min_reward_risk_ratio`, `correlation_threshold` (`0.70`),
  `max_correlated_cluster_pct` (`0.25`), `min_correlation_bars` (`60`) or `MAX_POSITION_PCT`.** These
  are tunables; moving one is a `/tuner` experiment with operator confirmation, not a defect sprint.
- ❌ **Do not make the stop and target derive independently.** That changes how targets are set — a
  capital-risk policy decision, owed an ADR. It is the *other* half of work-queue item 60 and is
  deliberately left open.
- ❌ **Do not build risk-based position sizing** (work-queue item **62**). Policy, ADR-owed,
  operator's call.
- ❌ **Do not make the regime label modulate the base stop/target pair.** Finding 1 above discovered
  that it does not; **file it** (see step 10), do not fix it here. Same reason: policy.
- ❌ **Do not change `contracts/`.**

### The road not taken (LAW-06)

| Option | Why not |
| --- | --- |
| Widen or lower `min_reward_risk_ratio` so the gate "does something" | The value is a **constant**. No threshold discriminates a constant — it only moves the boundary between *always passes* and *always fails*. This is the S202/S203 trap ([DRIFT-058](../laws/drift-register.md)) in its other mask |
| Delete the `reward_risk` gate | It is a real invariant assertion — if the analyst's derivation ever changes, a `FAILED` here is the tripwire. Deleting it removes the tripwire; disclosing it keeps it |
| Compare `scaled_target` to a `scaled` baseline | Identity that can never fail. [S206](sprint-206-a-rendered-verdict-names-the-check-that-produced-it.md) rejected exactly this for exactly this reason |
| Lower `correlation_threshold` to 0.65 so C clusters with WFC | Fits the instrument to one night's answer. It is a tunable move with a capital consequence and belongs in a `/tuner` experiment with a registered hypothesis |

---

## The design decisions this sprint has to make

### 1. What "discloses whether the other answer was reachable" actually renders

🪤 **Do not invent a new `GateStatus`.** `contracts/` is closed this sprint and three states are
enough. The disclosure belongs in `detail`, the way `PM-OBS-03` put the census there.

The precedent to copy is [S203](sprint-203-a-check-that-cannot-fail-says-so.md)'s
`comparison: FORCED | INFORMATIVE | NO DATA` ending on `compare_order_tolerances`. Give
`reward_risk`'s detail a terminal field of the same shape — one token a reader can grep, plus the
*reason*: for this gate the ratio is fixed by `base_take_profit_pct / base_stop_loss_pct`, so name
both constants and the applied mode. A reader must be able to tell `2.0 vs 1.5 -> PASSED (and it
could not have been otherwise)` from a comparison that genuinely discharged.

🚨 **Write the rule for the class, then bring the site into compliance — not the reverse.** A clause
whose oracle is the one site it describes is the S205 anti-pattern, and S206 called it out by name.
`PM-OBS-04` should be true of every gate in `gate_report.py`; the other gates satisfy it because their
values vary. **Prove that** in the test, don't assert it.

### 2. Pairwise, without growing the module past the block

📌 `correlation.py` is **153 lines** — already past the 150-line warning. The pairwise walk plus the
skip bookkeeping will not fit. **Split before you add.** `correlation_census.py` (131) is the natural
home for anything census-shaped; a new small module beside them is fine if it earns its docstring.
🪤 Adding first and splitting after is how a module reaches the 200-line hard block mid-sprint.

### 3. What the skipped pair reports

`min_correlation_bars`'s `why=` says *"below this the gate is not evaluated, never passed"* — written
when the gate was all-or-nothing. After this sprint that sentence is true of a **pair**, not the gate.
🪤 **A tunable's `why=` that no longer describes the code is the DRIFT-057 defect — a law going stale
the day its sprint merges, by our own hand.** Update the `why=` in the same commit, and say you did.

---

## Blast radius — measured 2026-09-15

| File | Lines now | Change |
| --- | --- | --- |
| `agents/portfolio_manager/domain/gate_report.py` | **120** | Grows — the `reward_risk` disclosure |
| `agents/portfolio_manager/domain/correlation.py` | **153** ⚠️ past the 150 warn | Must **shrink or split** — pairwise walk replaces the abort |
| `agents/portfolio_manager/domain/correlation_census.py` | **131** | Grows — `skipped_pairs` in `detail()` at `:48-56` |
| `agents/portfolio_manager/domain/risk.py` | **161** ⚠️ | Likely untouched — check before editing |
| `agents/portfolio_manager/settings.py` | — | One `why=` string only (design decision 3). **No default moves** |
| `agents/portfolio_manager/laws/laws.md` | LOCKED **v1.4**, rollup **29 / 48** | → v1.5, `PM-OBS-04` |
| `contracts/` | — | **UNTOUCHED — verify with `git diff --stat contracts/`** |

**Deploy shape: image-only retag.** *[predicted, verify before deploying]* No `contracts/` change, no
new graph label or property, no new env key, no new tunable — so no injected pack moves. 🪤 **Verify
all three packs anyway** (`trading_graph_vocabulary`, `trading_credential_tests`, `trading_issuer_map`)
— S202 nearly shipped inert by checking only one.

---

## Steps, in order

1. Create the branch and a worktree. **Do not work on `main`.**
2. Do the MUST RULE reading. Fill the **Law reading record** before any edit.
3. **Re-derive the denominator yourself** (T0 below) before trusting any number in this spec. It is
   four lines of SQL against `POSTGRES_DSN`, and it is the number two work-queue rows got wrong.
4. **Write the failing tests first** — T1 and T2. **Paste the red output into the Closeout.**
5. Add `PM-OBS-04` to `laws.md` (v1.5 + Changelog), add the `test-plan.md` row.
6. Split `correlation.py` *before* adding the pairwise walk (design decision 2).
7. Implement the pairwise skip + `skipped_pairs` in the census; update the `min_correlation_bars`
   `why=`.
8. Add the `reward_risk` disclosure.
9. Add `DRIFT-063` recording that two gates carried `PASSED` verdicts they could not have withheld,
   and that item 61's carried denominator was an artefact of pre-2026-08-20 records.
10. **Do not re-file the regime finding, and do not fix it.** That the `label` never modulates the base
    stop/target pair is already recorded as [DL-169](../design-log.md) and work-queue item **64** by the
    planning session that wrote this spec. If your reading contradicts it, say so — do not silently
    correct it.
11. `make ci` to a **file**, read the file. 🪤 Never `make ci | tail` — that reports `tail`'s exit code.
12. Fill the handback sections at the bottom of this file.

---

## Test plan

| # | Test | Asserts | Clause |
| --- | --- | --- | --- |
| T0 | Denominator re-derivation (manual, free) | Count `OrderIntent` nodes, and how many carry any non-null gate `outcome`. **Paste both numbers.** If they are not 273 / 35, this spec is stale — say so and use yours | — |
| T1 | `test_a_structurally_fixed_gate_discloses_that_it_could_not_differ` | The `reward_risk` detail names both regime constants and the applied mode, and marks the comparison as structurally determined. **Must fail on `main`** | `PM-OBS-04` |
| T2 | `test_one_unusable_pair_does_not_disable_the_whole_gate` | With one held issuer below `min_correlation_bars` and others above, the gate **evaluates** (not `NOT_EVALUATED`) and the census reports `skipped_pairs=1`. **Must fail on `main`** | `PM-OBS-04`, `PM-NEV-09` |
| T3 | `test_every_pair_unusable_still_reports_not_evaluated` | All pairs below `min_bars` → the whole gate is `NOT_EVALUATED`, never `PASSED` | `PM-NEV-09` |
| T4 | `test_a_gate_whose_value_varies_is_not_marked_structurally_fixed` | Run the property over **every** gate in a full `gate_report`: only `reward_risk` carries the structural marker. This is what stops the clause describing one site | `PM-OBS-04` |
| T5 | `test_skipped_pair_names_the_issuer_and_its_overlap` | The skip is attributable — issuer and observed bars both rendered, not just a count | `PM-OBS-03`, `PM-OBS-04` |
| T6 | Replay over the recorded census (manual, free) | Re-run the new renderer over the **7** census-bearing records from the spine and confirm no `cluster_issuers` set changes. **The pairwise fix must not silently re-cluster history** | — |

🚨 **No paid measurement in this sprint.** Nothing here touches an LLM path. If you find yourself
wanting a replay, the scope has drifted.

---

## Success factors

1. T1 and T2 **fail on `main`** (red output pasted) and pass after.
2. T0, T3, T4, T5, T6 pass, with T0's two numbers pasted.
3. `git diff --stat contracts/` is **empty**.
4. `make ci` **all 12 steps** green, exit code read **from a file**, 100.00 % coverage.
5. `agents/portfolio_manager/laws/laws.md` at **v1.5** with `PM-OBS-04`, a `test-plan.md` row, the
   clause ID cited in T1–T5 docstrings, and the rollup updated in **both** `ledger.md` and
   `docs/laws/INDEX.md` — **the number the gate computed**, not one you chose.
6. `DRIFT-063` filed. (`DL-169` and work-queue item **64** already exist — do not duplicate them.)
7. Every module touched **< 200 lines**, and `correlation.py` **below 150** after the split.
8. `min_correlation_bars`'s `why=` describes per-pair behaviour.
9. `make gate-ran` exits 0 **from the worktree whose `HEAD` is the commit being proven**, and the
   printed SHA matches `git rev-parse HEAD`.

🚨 **What is deliberately NOT a success factor: that either gate starts rejecting orders.** The claim
is that a gate discloses what it can do and that the correlation cap stops abandoning itself — not
that the book changes. If nothing is rejected for a month, this sprint still succeeded.

---

## Traps

1. 🪤 **The tempting wrong fix on `reward_risk` is to move the threshold.** It is a constant. No
   threshold discriminates a constant. See *The road not taken*.
2. 🪤 **`correlation.py` is at 153 lines.** Split before you add, or you will hit the 200 hard block
   mid-change.
3. 🪤 **The abort path has never fired in production.** Do not write the Closeout as though you fixed
   a live incident — it is repair before it bites, and S206's precedent is to say which.
4. 🪤 **Two work-queue rows carry a wrong denominator** (170 / 181 / "31 of 181"). The real one is
   **35 outcome-bearing intents since 2026-08-20**. Re-derive it (T0) and correct the rows.
5. 🪤 **`min_correlation_bars`'s `why=` goes stale the moment this merges** unless you edit it in the
   same commit. That is DRIFT-057's exact shape.
6. 🪤 **`PM-NEV-09` must come out of this *stronger*, not weaker.** All-pairs-unusable is still
   `NOT_EVALUATED`. A reviewer will check this first.
7. 🪤 **A worktree has no `.env`**, so T0 and T6 cannot run there. State which tree you ran them in.
8. 🪤 **Do not touch the `sizing` gate.** It is work-queue item 62 and it is a policy decision.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `correlation.py` **153**, `risk.py` **161**, `correlation_census.py` **131**,
  `gate_report.py` **120**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. **This sprint should need none.**
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0** from the branch worktree.
2. Merge to `main` locally and push. 🪤 Check you are not on the branch already.
3. **Post-merge CodeQL.** `codeql.yml` runs **only on `main`**. Check after merging.
4. **Deploy: image-only retag** — but verify **all three** injected packs first.
5. Re-measure work-queue items **60** and **61**, and correct their denominators.

---

## Handover — paste this to Codex

```text
Branch: sprint-208-a-risk-gate-says-what-it-can-reject, from main at 03f40b4 or later (that commit
carries this spec).

THE DEFECT, measured 2026-09-15 against the live spine. Two PM risk gates have never rejected an
order, for two different reasons, and neither says so.

(1) reward_risk (agents/portfolio_manager/domain/gate_report.py:57-75) tests target_pct/stop_pct
against min_reward_risk_ratio=1.5. Measured: 256 recorded gate entries, ONE distinct value - 2.0.
It is a constant by construction: _scaled_target = min(flat_target * (scaled_stop/flat_stop),
_MAX_PCT) at agents/analyst/domain/stop_target.py:89, so dividing by scaled_stop cancels the mode
and the ratio reduces to flat_target/flat_stop in BOTH modes. And flat_target/flat_stop are
base_take_profit_pct/base_stop_loss_pct, which agents/provider/agent.py:155-161 returns STRAIGHT
FROM SETTINGS (0.10 and 0.05) - the regime label never touches them. So the ratio is 2.0 in every
regime. There is no threshold that makes a constant discriminate.

(2) correlated_cluster_pct: _unevaluated_pair (agents/portfolio_manager/domain/correlation.py:98-110)
returns on the FIRST held issuer whose overlap is under min_correlation_bars=60, and its caller
(correlation.py:63-66) then returns that single NOT_EVALUATED for the WHOLE gate. One short-history
holding disables correlation checking for every candidate that night.

MEASURED CENSUS: 919 Rejection nodes, complete reason breakdown hold_recommendation 848,
sector_name_count 30, sizing 19, account_unavailable 18, max_positions 3, insufficient_cash 1.
reward_risk: ZERO. correlated_cluster_pct: ZERO. Other gates do fire - these two specifically do not.

THE DENOMINATOR TRAP - RE-DERIVE IT FIRST. The spine has 273 OrderIntent nodes but only 35 carry gate
outcomes; the other 238 are pre-2026-08-20 records with outcome:null. The work-queue rows say "170 of
170" and "31 of 181" and both are wrong denominators. Run T0 before you trust any number in the spec,
including mine, and correct the rows.

ALSO MEASURED: the correlation abort path has NEVER FIRED. All 35 recorded evaluations passed, 0
failed, 0 not-evaluated, and observed min_pair_overlap_bars is 81-82 against a threshold of 60. This
is repair before it bites. Do NOT write the closeout as if you fixed a live incident.

MUST RULE: read agents/portfolio_manager/laws/laws.md AND test-plan.md AND docs/laws/conventions.md
AND docs/laws/drift-register.md before you open an editor. Fill the Law reading record FIRST.

LAW CYCLE: YES, one new clause. contracts/ must NOT change - GateOutcome already carries detail and
GateStatus already has three states. Add PM-OBS-04 (a gate that renders a verdict discloses whether
the other answer was reachable), bump laws.md v1.4 -> v1.5 with a Changelog line, add a test-plan row,
cite the clause in every test docstring, let make ci compute the rollup for ledger.md and
docs/laws/INDEX.md. PM-OBS-04 and PM-NEV-10 are both free; take the OBS one.

ORDER OF WORK: failing tests FIRST (T1, T2), both must fail on main. PASTE THE RED OUTPUT.

THE FIX: (1) keep reward_risk's verdict AND threshold, add a disclosure to its detail naming the two
regime constants and the applied mode and marking the comparison structurally determined - copy the
shape of S203's "comparison: FORCED | INFORMATIVE | NO DATA". (2) make the correlation gate evaluate
PAIRWISE: skip only the unusable pair, evaluate on what remains, and report skipped_pairs=N with the
issuer and its observed overlap in the census. If EVERY pair is unusable the whole gate is still
NOT_EVALUATED - PM-NEV-09 must come out stronger, not weaker.

correlation.py is 153 lines, already past the 150 warning. SPLIT BEFORE YOU ADD.

Write the clause for the CLASS and prove it over every gate in a full gate_report (T4), not just the
one site you fixed. A clause whose oracle is the thing it describes is the S205 anti-pattern.

DO NOT change min_reward_risk_ratio, correlation_threshold (0.70), max_correlated_cluster_pct,
min_correlation_bars or MAX_POSITION_PCT - tunables, /tuner territory, operator confirmation.
DO NOT make stop and target derive independently (capital policy, ADR-owed).
DO NOT build risk-based sizing (work-queue item 62, policy).
DO NOT make the regime label modulate the bases - already filed as DL-169 + work-queue row 64, leave it.
DO NOT change contracts/ - verify with git diff --stat contracts/.

DO update min_correlation_bars' why= string: it says "below this the gate is not evaluated" and after
this sprint that is true of a PAIR, not the gate. A why= that goes stale the day its sprint merges is
DRIFT-057's exact shape.

NO PAID MEASUREMENT. Nothing here touches an LLM path.

make ci all 12 steps, redirected to a FILE (never | tail - that reports tail's exit code), 100.00%
coverage. Then make gate-ran from the worktree whose HEAD is the commit you are proving, and check
the printed SHA against git rev-parse HEAD.

HANDBACK: fill Law reading record, Test plan results, Closeout - evidence (real pasted output,
including the RED runs and T0's two numbers), Return notes, and set Status: BUILT. A placeholder left
intact means the handback is returned, not repaired.
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
| `gate_report.py` | `agents/portfolio_manager/laws/laws.md`; `agents/portfolio_manager/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `PM-OUT-01..03`, `PM-NEV-04`, `PM-TYP-03`, `PM-OBS-01`, new `PM-OBS-04` | Yes. The law file confirms the contract already has `GateOutcome.detail`; the disclosure belongs there, with no `contracts/` edit. |
| `correlation.py` | `agents/portfolio_manager/laws/laws.md`; `agents/portfolio_manager/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `PM-NEV-08`, `PM-NEV-09`, `PM-OBS-03`, new `PM-OBS-04` | Yes. `PM-NEV-09` requires all-pairs-unusable to remain `NOT_EVALUATED`; the fix is pair-level skipping, not a silent pass. |
| `correlation_census.py` | `agents/portfolio_manager/laws/laws.md`; `agents/portfolio_manager/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `PM-NEV-08`, `PM-NEV-09`, `PM-OBS-03`, new `PM-OBS-04` | Yes. The census is the existing `PM-OBS-03` evidence channel, so skipped-pair attribution should render there rather than in a new contract field. |
| `laws.md` / `test-plan.md` | `agents/portfolio_manager/laws/laws.md`; `agents/portfolio_manager/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md`; `docs/laws/INDEX.md` | conventions §2, §3, §4, §7, §7a, §9; `PM-OBS-04` free; `PM-NEV-10` free but out of scope | Yes. This is an observability clause, not a prohibition; `PM-OBS-04` is the correct new ID. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No `contracts/`
change is needed or allowed; `GateOutcome.detail` and tri-state `GateStatus` already carry the
evidence. Yes, the sprint adds one PM guarantee: a rendered `PASSED`/`FAILED` gate must disclose
whether the opposite verdict was reachable. Full law cycle owed as `PM-OBS-04`.

**Contradictions found between a law and this spec:** None found.

**Laws found silent where a decision was needed:** PM laws were silent on verdict-reachability
disclosure for gates that render `PASSED` or `FAILED`; this sprint fills that silence with
`PM-OBS-04`.

**Clauses that were ⬜ and are now proven:** `PM-OBS-04` is now 🟩; PM rollup moved
from **29 / 48** to **30 / 49** in both law rollups.

**Clauses that were 🟩 and are now ⬜:** None identified before implementation.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| T0 | live denominator re-derivation | manual read-only graph query via main `.env` | PASS — `OrderIntent count=273`; `OrderIntent with non-null gate outcome=35` | — |
| T1 | `test_a_structurally_fixed_gate_discloses_that_it_could_not_differ` | `agents/portfolio_manager/tests/test_reward_risk.py` | PASS; verified red on `main` first | `PM-OBS-04` |
| T2 | `test_one_unusable_pair_does_not_disable_the_whole_gate` | `agents/portfolio_manager/tests/test_correlation_concentration.py` | PASS; verified red on `main` first | `PM-OBS-04`, `PM-NEV-09` |
| T3 | `test_every_pair_unusable_still_reports_not_evaluated` | `agents/portfolio_manager/tests/test_correlation_concentration.py` | PASS | `PM-NEV-09`, `PM-OBS-04` |
| T4 | `test_a_gate_whose_value_varies_is_not_marked_structurally_fixed` | `agents/portfolio_manager/tests/test_gate_reachability.py` | PASS | `PM-OBS-04` |
| T5 | `test_skipped_pair_names_the_issuer_and_its_overlap` | `agents/portfolio_manager/tests/test_correlation_census.py` | PASS | `PM-OBS-03`, `PM-OBS-04` |
| T6 | recorded census replay | manual read-only graph replay via main `.env` | PASS — 7 records, 0 cluster mismatches, new skip field renders as zero | — |

**Tests added beyond the plan:**

- `agents/portfolio_manager/tests/test_reward_risk.py::test_a_zero_stop_ratio_is_not_labelled_structurally_fixed`
  cites `PM-OBS-04` and covers the undefined-ratio defensive branch.
- `agents/portfolio_manager/tests/test_correlation_edges.py::test_repeated_pair_uses_cached_correlation`
  cites `PM-NEV-08` and covers the pair-correlation cache-hit branch introduced by the split.

---

## Closeout — evidence

**Status:** BUILT — local CI and branch gate proved for implementation commit
`95e17d776b6f661852473f8736c8d731f39db3e5`.

**Tree the proofs ran in (and `.env` present?):** Local tests and `make ci` ran in
`C:\Users\yury_\Downloads\project\trading-agents-sprint-208-a-risk-gate-says-what-it-can-reject`
with no local `.env`. T0 and T6 were read-only graph measurements run from that worktree after
loading `..\trading-agents\.env` from the main worktree; no secrets were printed.

**T0 — the denominator you measured:** *(OrderIntent count, outcome-bearing count)*

```text
OrderIntent count=273
OrderIntent with non-null gate outcome=35
```

**Result:** `reward_risk` detail now renders `base_take_profit_pct`, `base_stop_loss_pct`,
`applied_mode`, `structural_basis` and `comparison=STRUCTURALLY_DETERMINED` when the recorded
stop/target evidence shows the ratio was fixed by the base pair. Data-varying gates do not carry the
structural marker. `correlated_cluster_pct` now evaluates usable pairs even when one held issuer is
below `min_correlation_bars`, reports `skipped_pairs` plus `skipped_pair_issuers`, and still returns
whole-gate `NOT_EVALUATED` when no usable pair remains.

**Files changed:**

```text
agents/portfolio_manager/domain/correlation.py
agents/portfolio_manager/domain/correlation_census.py
agents/portfolio_manager/domain/gate_report.py
agents/portfolio_manager/domain/reward_risk_detail.py
agents/portfolio_manager/settings.py
agents/portfolio_manager/laws/laws.md
agents/portfolio_manager/laws/test-plan.md
agents/portfolio_manager/tests/test_correlation_census.py
agents/portfolio_manager/tests/test_correlation_concentration.py
agents/portfolio_manager/tests/test_correlation_edges.py
agents/portfolio_manager/tests/test_gate_reachability.py
agents/portfolio_manager/tests/test_reward_risk.py
docs/STATE.md
docs/laws/INDEX.md
docs/laws/drift-register.md
docs/laws/ledger.md
docs/work-queue.md
pyproject.toml
uv.lock
```

**Design decisions:** recorded as `DL-169`; `DRIFT-063` filed and marked corrected by S208.

**Proof — the RED runs first (T1 and T2 failing on `main`):**

```text
2 collected; 2 failed
test_reward_risk.py:78: assertion failed because old detail was
"target_pct=0.1600; stop_pct=0.0800; source=recommendation"
and did not contain "base_stop_loss_pct=0.0500"
test_correlation_concentration.py:105: expected "correlated_cluster_concentration";
observed "correlation_not_evaluated"
```

**Proof — the green run:**

```text
uv run pytest agents\portfolio_manager\tests\test_reward_risk.py::test_a_structurally_fixed_gate_discloses_that_it_could_not_differ agents\portfolio_manager\tests\test_correlation_concentration.py::test_one_unusable_pair_does_not_disable_the_whole_gate agents\portfolio_manager\tests\test_correlation_concentration.py::test_every_pair_unusable_still_reports_not_evaluated agents\portfolio_manager\tests\test_gate_reachability.py::test_a_gate_whose_value_varies_is_not_marked_structurally_fixed agents\portfolio_manager\tests\test_correlation_census.py::test_skipped_pair_names_the_issuer_and_its_overlap --no-cov
5 passed in 1.21s

uv run pytest agents\portfolio_manager --no-cov
116 passed in 1.87s
```

**Proof — T6, the recorded census replayed:**

```text
census-bearing records=7
cluster_issuers mismatches=0
new_renderer_skip_field=skipped_pairs=0
```

**`git diff --stat contracts/`:** empty output.

**Rollups, as computed by the gate:** `check_law_coverage.py` first reported
`portfolio_manager claims 29 / 48; derived 30 / 49`; after updating both rollups it exited 0.
`agents/portfolio_manager/laws/laws.md`, `docs/laws/ledger.md` and `docs/laws/INDEX.md` now all
record **30 / 49** with `PM-OBS-04` green.

**Module line counts:** *(`correlation.py` must be below 150)*

```text
agents\portfolio_manager\domain\correlation.py 115
agents\portfolio_manager\domain\correlation_census.py 141
agents\portfolio_manager\domain\gate_report.py 105
agents\portfolio_manager\domain\reward_risk_detail.py 90
agents\portfolio_manager\tests\test_correlation_census.py 157
agents\portfolio_manager\tests\test_correlation_concentration.py 134
agents\portfolio_manager\tests\test_correlation_edges.py 138
agents\portfolio_manager\tests\test_gate_reachability.py 55
agents\portfolio_manager\tests\test_portfolio_manager_audit.py 145
agents\portfolio_manager\tests\test_reward_risk.py 128
```

**`make ci`:** redirected to
`C:\Users\yury_\AppData\Local\Temp\s208-make-ci-20260915-220939.log`. Exit code: `0`.

```text
TOTAL                                                     16525      0   3518      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
2763 passed, 6 skipped in 84.85s
uv run pip-audit
No known vulnerabilities found
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 2 new file(s)
```

**`make gate-ran`:** run from
`C:\Users\yury_\Downloads\project\trading-agents-sprint-208-a-risk-gate-says-what-it-can-reject`
at `95e17d776b6f661852473f8736c8d731f39db3e5`:

```text
uv run python scripts/assert_gate_ran.py
GATE PROVEN for 95e17d776b6f661852473f8736c8d731f39db3e5:
  CI: success (attempt 1)
  Security Findings: success (attempt 1)
head=95e17d776b6f661852473f8736c8d731f39db3e5
exit=0
```

**Not met / verified failing:** No merge, post-merge CodeQL or deploy was attempted.

---

## Return notes

S208 deliberately leaves work-queue item 60's independent-target-derivation half open as an operator
policy decision. It closes item 61's pairwise correlation-disable defect and corrects the stale
denominators in `docs/work-queue.md`. `docs/local/STATE.md` does not exist in this repository, so the
sprint boundary note was recorded in tracked `docs/STATE.md` instead.
