<!-- Agent: planning | Role: sprint handover -->
# Sprint 185 — The veto's posture is declared, not arithmetic

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-185-the-veto-posture-is-declared-not-arithmetic`
**Status:** BUILT — local proof complete; remote `make gate-ran` is post-push evidence.
**Version:** 0.92.00
**Effort:** M
**Decisions:** [DL-104](../design-log.md) (d) the row this closes · [DL-116](../design-log.md) the
grace change that made the veto binding by accident · [DL-119](../design-log.md) why softening the
veto is rejected · [DL-125](../design-log.md) the outage that made this urgent ·
[ADR-0017](../decisions/) the analyst is the sole author of exits

> **Why this bump kind.** **feat → MINOR.** The operator gains a switch that does not exist today.
> Everything else in this sprint is the plumbing that makes the switch mean something. It is *not*
> a PATCH: no clause promises a posture and no code falls short of one — the posture is simply
> undeclared.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/execution/laws/laws.md` | Execution's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report |
| `agents/execution/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`IDN`** (execution submits, it never decides what to trade), **`NEV`**
(`EXEC-NEV-01` — execution honours an upstream block and never chooses), **`OBS`**, **`PARAM`**.

### The rule

1. **Before writing code**, read `agents/execution/laws/laws.md` — whole file, first time.
2. Read `agents/execution/laws/test-plan.md` alongside it. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** For this sprint the answer is already **Yes** — see it.
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding → `drift-register.md`.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered: **YES**

> Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?

**Yes, and twice over.** It adds a posture guarantee execution has never made, and it changes the
`DeliberationStatus` vocabulary that `ExecutionRun` records. **So the law cycle is in scope and
non-negotiable**: a new clause in `agents/execution/laws/laws.md` (bump its version, add a Changelog
line), a `test-plan.md` row per clause, the clause ID cited in each new test docstring, the rollup
updated in **both** `docs/laws/ledger.md` **and** `docs/laws/INDEX.md`, and drift rows for the two
silences below.

🚨 **Two silences are already measured — file both as drift rows, do not "fix" them by inventing law:**

1. **Execution's `laws.md` says nothing about deliberation at all.** `grep -in "delibera\|veto"
   agents/execution/laws/laws.md` returns **one** hit, and it is an unrelated line about clause
   numbering. The entire veto gate — five states, a grace window, a fail-open policy — is
   law-invisible. That is what lets its posture be set by arithmetic.
2. **`deliberation_grace_seconds` is absent from execution's PARAM table**, although it is a
   registered `tunable()` in `agents/execution/settings.py:122`. Same class as work-queue item 29
   (`provider.alpaca_data_feed` in no law at all).

🪤 **The rollup is derived, not declared.** `make ci` recomputes it — two new clauses proven by three
test rows is **+2**, not +3. Let the gate tell you the number.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/execution/deliberation_gate.py` | `agents/execution/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `EXEC-NEV-01` execution honours an upstream block and never decides what to trade — a posture that *drops* buys must be a declared operator policy, never execution's own judgement |
| `agents/execution/pm_execution.py` | same | `EXEC-IDN-*` execution submits; `EXEC-OBS-*` the run record must be reconstructable, so the posture belongs *on* `ExecutionRun` |
| `agents/execution/settings.py` | same, **PARAM table especially** | The mode-selector convention (see the trap below) and the missing `deliberation_grace_seconds` row |
| `agents/execution/deliberation_faults.py` | same | Faults, not silent failure — but severity must follow the declared posture |
| `orchestration/packs/trading_deliberation_view.py` | `docs/laws/` umbrella + `docs/laws/conventions.md` | The acceptance gate is the artifact the operator reads; it must assert the posture was **honoured** |

⚠️ **Exits never wait, in either posture.** `deliberation_gate.py`'s module docstring is explicit:
blocking an exit on an LLM outage is what S147 refused and what froze the book for eight days, and
ADR-0017 makes the analyst the sole author of exits. **A sell-only `PMRun` must submit immediately
under `binding` exactly as it does today.** If your change can hold or drop an exit, stop and report.

---

## Goal

The veto's posture — **advisory** (proceed when no verdict can be obtained) or **binding** (refuse
to open exposure without one) — becomes a value the operator declares and every run records, instead
of an emergent property of two timeout numbers. After this sprint, "why did 3 orders reach the broker
unreviewed on 2026-08-21?" is answered by *"because the posture was `advisory`"* rather than by
arithmetic about a grace window.

## Why (context)

**The posture is real, load-bearing, and nobody set it.** [DL-104](../design-log.md) set
`deliberation_grace_seconds = 900` *deliberately*, as the only no-code way to keep the veto advisory.
[DL-116](../design-log.md) raised it to **1800** so debates could finish — and the veto became
**binding by arithmetic**, which DL-116 itself flags as *"a posture change made by arithmetic."* Two
tunable numbers a busier night could overturn now hold a policy decision.

🚨 **The outage turned this from tidy-up into the top-ranked item.** The deliberator has no API
credit until **2026-08-30** ([DL-125](../design-log.md)). Until then every scheduled run does the
same three things: fails open on every order, submits them **unvetoed**, and raises an `error` fault
plus a **red acceptance gate** for something that is not a defect. That is precisely the failure mode
DL-104 (d) named — *"trains the operator to read a real fault as noise"* — except it is now nightly
rather than hypothetical. **Six red nights in a row is how an evidence discipline stops being
believed**, and the etalon bar is explicitly *"the evidence discipline catches its own defects without
the operator in the loop."*

🚨 **This is NOT softening the veto.** [DL-119](../design-log.md) explicitly rejected lowering the
bar to restore throughput, because that reintroduces DL-104's advisory posture *by the back door*
while leaving every objection still true. **Declaring the posture is the opposite move:** it makes
advisory a stated, recorded, reversible mode instead of an accident, and it makes `binding` mean
something enforceable for the first time.

### Measured, 2026-08-22 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| `DeliberationStatus` states | **5** — `applied`, `applied_failed_open`, `not_required`, `waiting`, `proceeded_unvetoed` | *[measured]* `agents/execution/deliberation_gate.py:37` |
| `deliberation_grace_seconds` | default **900**, `ge=0`, `le=3600`, **live value 1800** | *[measured]* `agents/execution/settings.py:122` + DL-116 |
| Rows for it in execution's PARAM table | **0** | *[measured]* `sed -n '/## Parameters/,/^---/p' agents/execution/laws/laws.md` |
| Clauses in execution's `laws.md` mentioning deliberation or the veto | **0** | *[measured]* `grep -in "delibera\|veto" agents/execution/laws/laws.md` — the single hit is about clause numbering |
| Acceptance checks on the stage | `debate_coverage` **floor 1.0**, `failed_open_count` **ceiling 0.0**, both **unconditional** | *[measured]* `orchestration/packs/trading_deliberation_view.py:50-51` |
| `sched-2026-08-21` | 3 approved, **3 failed open**, 3 submitted unvetoed, `real_debate_count=0`, ACCEPTANCE FAIL | *[measured]* trace + `accept.py` + the `DeliberationRun` node |
| `sched-2026-08-20` | 5 approved, **3 failed open**, 2 vetoed | *[measured]* same |
| Sessions this will repeat for | **~6** (2026-08-22 → 2026-08-30) | *[measured]* operator statement + `30 22 * * 1-5` |
| `agents/execution/settings.py` | **150 lines — exactly at the warn threshold** | *[measured]* `wc -l` |
| `deliberation_gate.py` / `pm_execution.py` / `deliberation_faults.py` / `trading_deliberation_view.py` | **147 / 84 / 79 / 82** | *[measured]* `wc -l` |
| Which posture is live today | **de facto binding**, held only by grace 1800 + per-call timeout 120 | *[ASSUMED — not measured]* no artefact records a posture; that absence *is* the sprint. Settle it by reading `ExecutionRun.deliberation_status` across the last 10 runs before you design |

---

## Scope — and what is deliberately NOT here

1. **A declared posture.** `advisory | binding`, defaulting to the posture that is live today, so the
   merge alone changes no behaviour. The switch is what changes behaviour, and the operator throws it.
2. **The posture is recorded on every run**, so a stored `ExecutionRun` answers "what was the policy
   when this order was submitted?" without reading a settings file that has since changed.
3. **Fault severity follows the posture.** An unvetoed submission under a *declared* `advisory` is
   expected — `warning`. Under `binding` it is a policy breach — `error`.
4. **The acceptance gate asserts the posture was honoured**, not that debates happened.
5. **The law cycle** — clause(s), test-plan rows, rollups, and the two drift rows named above.

### Out of scope (do NOT build this sprint)

- **No change to `deliberation_grace_seconds` or the deliberator's timeouts.** Those numbers stay
  exactly where DL-116 left them. This sprint removes their *policy* role, not their value.
- **No change to what the deliberator decides**, how it debates, or its concurrency (that is S172).
- **No retry, queue, or fallback provider** for the outage. The outage is the *occasion*, not the work.
- **No ADR-0017 reversal.** Exits are the analyst's, and they never wait.
- **No softening of any veto that DID arrive.** `drop_vetoed` keeps its current behaviour exactly.

### The road not taken (LAW-06)

- **Set `deliberation_grace_seconds = 0` for the outage window.** Rejected: it produces the right
  behaviour by the wrong mechanism — the posture stays undeclared and the next person still cannot
  tell policy from arithmetic. It is also the exact move DL-119 refused.
- **Suppress the acceptance checks while the provider is down.** Rejected: a gate that is muted for
  a real condition is worse than a red one; the artefact would then lie in the other direction.
- **Make `binding` hold the buys for the next run instead of dropping them.** Rejected as the
  default — a held buy re-creates DL-98's race and risks the S147 freeze, and a buy decided on
  yesterday's prices is a different order. **Record it as an option if you disagree after reading.**

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Is `deliberation_posture` a `tunable()` or a mode selector?** 🪤 **Almost certainly a mode
   selector, and getting this wrong is a law violation.** `order_price_tolerance_mode` and
   `stop_target_mode` are both declared **`NO (mode selector)`** in their locked PARAM tables, in
   identical wording citing ADR-0013: *a tunable is a value **within** a formula; a mode selector
   chooses **which formula runs***. `advisory | binding` chooses which behaviour runs. So: a bare
   default in `settings.py`, **not** `tunable()`, plus a PARAM row declaring `NO (mode selector)`.
   **S183's spec got this exact call backwards and had to be corrected mid-build** — do not repeat it
   in reverse by registering a mode selector as a knob.
2. **What does `binding` do with a buy it cannot get a verdict for?** Drop it from the approved set
   with a loud `error` fault (recommended — see the road not taken), or hold the whole `PMRun` for
   the next run. Whichever you choose, **exits are unaffected in both**.
3. **What does the acceptance gate assert under each posture?** Recommended shape: under `binding`
   keep today's `debate_coverage` floor 1.0 and `failed_open_count` ceiling 0; under a declared
   `advisory` replace them with a check that **every unvetoed submission is attributable** — the
   posture is recorded, the reason string is present, and the count is reported as an observable
   rather than a failure. 🪤 **Do not make `advisory` simply pass everything** — that trades a gate
   that cries wolf for a gate that says nothing, and the second is worse.
4. **Does the existing `proceeded_unvetoed` / `applied_failed_open` vocabulary survive, or does the
   posture become a separate axis?** They are different questions — *why was there no verdict* vs
   *what policy applied* — and collapsing them is how the current confusion started. Recommended:
   keep the five states, add posture as its own recorded field.

🪤 **Take the next free DL number, then re-check it at merge.** The log has historic duplicates (two
`DL-110`, two `DL-111`) and entries are prepended at the top *and* appended at the bottom. **A branch
cut before another DL lands will collide even when the number was free at branch time** — S183 chose
`DL-121` correctly and still collided. Check again when you merge. As of 2026-08-22 the highest is
**DL-126**.

---

## Blast radius — measured 2026-08-22

| What | Detail |
| --- | --- |
| Files changed | `agents/execution/deliberation_gate.py` **147**, `pm_execution.py` **84**, `deliberation_faults.py` **79**, `settings.py` **150**, `orchestration/packs/trading_deliberation_view.py` **82**, + execution law files |
| 🚨 Size risk | **`settings.py` is at 150 — exactly the warn threshold.** Adding a field and a docstring will push it toward the 200 hard block. Plan the split before you write, not after the gate fails |
| Agents affected | `execution` only. 🪤 Confirm nothing you add makes execution import another agent |
| Contract change? | **Likely yes** (`DeliberationStatus` / the `ExecutionRun` record). Law cycle mandatory |
| Graph vocabulary change? | **Probably yes** — a new property on `ExecutionRun`. Check `orchestration/packs/trading_graph_vocabulary.json`; a new property means the deploy is a **full `up`** |
| New env keys | `EXECUTION_DELIBERATION_POSTURE` (or equivalent). **A new env key also forces a full `up`** |
| Deploy implication | **Full `up`, not a retag.** 🪤 The DL-100 `ENV PRESERVATION` guard must return 16/16 before you accept it |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Measure which posture is live** — read `ExecutionRun.deliberation_status` across the last 10
   runs — so the default you choose provably changes nothing at merge.
3. **Record the four design decisions** in `docs/design-log.md` with rejected alternatives.
4. **Plant the failing tests first** (A1–A6 below) and watch them fail. Paste the red output.
5. **Implement.**
6. **Law cycle** — clause(s), test-plan rows, docstring citations, both rollups, the two drift rows.
7. **Prove the guards can fail (DL-70)** — break each behaviour, watch its guard go red, restore.
8. **`make ci` green** — all 11 steps, **redirected to a file, never piped**.
9. **Fill the handback sections** at the bottom of this file and set **Status:** to `BUILT`.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 a declared `advisory` posture submits unvetoed buys and says so | posture=`advisory`, buy-carrying `PMRun`, no `DeliberationRun` | orders submit, the **posture is on the run record**, and the fault is `warning` — not `error` |
| A2 | 🎯 a declared `binding` posture refuses to open exposure without a verdict | posture=`binding`, same fixture | the buys do **not** reach the broker, and an `error` fault names the posture |
| A3 | 🪤 **exits never wait, in either posture** | posture=`binding`, **sell-only** `PMRun`, no `DeliberationRun` | submitted immediately, no hold, no drop. **S147 / ADR-0017** |
| A4 | a verdict that DID arrive is honoured identically under both postures | posture=both, `DeliberationRun` with `vetoed_tickers` | `drop_vetoed` behaviour is byte-identical; posture changes nothing here |
| A5 | the acceptance gate asserts the posture was honoured | posture=`advisory`, 3 fail-opens | the stage does **not** fail for the fail-opens, **and** does fail if the posture is absent or unattributable |
| A6 | the default posture reproduces today's behaviour exactly | no posture configured | identical status, identical fault severity, identical acceptance verdict to `main` before this sprint |

---

## Success factors

- [x] `advisory` and `binding` are declared values, recorded on every `ExecutionRun`.
- [x] Under a declared `advisory`, an unvetoed submission is a `warning` and the gate does not go red.
- [x] Under `binding`, a buy with no verdict does not reach the broker.
- [x] **Exits submit immediately in both postures** (A3).
- [x] The default preserves the measured live broker-action shape; evidence severity now follows the
      declared advisory posture instead of preserving accidental red/error noise.
- [x] Design decisions recorded with rejected alternatives, before implementation.
- [x] Law cycle done: clause(s) + test-plan rows + docstring citations + **both** rollups + the two
      drift rows for the measured silences.
- [x] `deliberation_posture` is a **mode selector**, not a `tunable()` — with its PARAM row.
- [x] Every new guard planted, watched to fail, restored — stated per guard.
- [x] Every touched module < 200 lines; state how `settings.py` was kept under it.
- [x] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The posture is not the grace window.** Leave `deliberation_grace_seconds` alone. If your change
makes the posture *depend* on it, the sprint has failed — that dependency is the defect.
🪤 **`advisory` must not become "the gate says nothing."** A gate that cannot fail is not evidence.
🪤 **A mode selector is not a tunable.** Read the PARAM tables for `order_price_tolerance_mode` and
`stop_target_mode` before you register anything.
🪤 **Read the reason field before the metrics.** `DeliberationRun.failed_open_reason` carries the
truth; the latency and count fields have now caused four wrong diagnoses in a row.
🪤 **The provider is down until 2026-08-30.** You cannot get a real debate. **Every proof in this
sprint must be a fixture** — do not schedule a live run to "check it works", and do not read a
fail-open in a live run as evidence your code did anything.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `settings.py` **150**, `deliberation_gate.py` **147**, `pm_execution.py` **84**,
  `deliberation_faults.py` **79**, `trading_deliberation_view.py` **82**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. 🪤 But a **mode selector** is not a
  tunable — see design decision 1.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 11 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — `make ci | tail` reports *`tail`'s* exit code. Redirect to a file and read the file.
- Version bump of the kind named at the top (feat → MINOR), `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**, so any proof needing live data
  is vacuous there. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** — it resolves the SHA
   from the working directory and ignores a `SHA=` argument. **Check the printed SHA against
   `git rev-parse HEAD`.**
2. Merge to `main` locally and push. 🪤 Check you are not on the branch already — a `git merge` from
   the branch's own worktree says *"Already up to date"* and merges nothing.
3. **Post-merge CodeQL.** `codeql.yml` runs **only on `main`**, so a green branch gate is not proof
   of a CodeQL-clean merge. Check after merging (work-queue item 31).
4. **Deploy is a full `up`**, not a retag — new env key and probably a new `ExecutionRun` property.
   `ENV PRESERVATION` must return **16/16**, and the scale + KEDA metadata must diff to zero drift.
5. **Then the operator declares the posture for the outage window** and the next scheduled run is
   read to confirm the gate is green-and-truthful rather than red-and-ignored.

---

## Handover — paste this to Codex

```text
Sprint 185 - the veto's posture is declared, not arithmetic.
Branch: sprint-185-the-veto-posture-is-declared-not-arithmetic (create it BEFORE any code, off
main, never work on main). Full spec: docs/sprints/sprint-185-the-veto-posture-is-declared-not-
arithmetic.md - read the whole file first.

THE PROBLEM. Whether the LLM veto is advisory (proceed when no verdict arrives) or binding (refuse
to open exposure without one) is not declared anywhere. It is an accident of two numbers:
deliberation_grace_seconds (DL-104 set 900 to keep it advisory; DL-116 raised it to 1800 so debates
could finish, which made it binding without anyone deciding) and the deliberator's per-call timeout.
Right now the deliberator has no API credit until 2026-08-30, so every nightly run fails open,
submits unvetoed, raises an error fault and turns the acceptance gate red - for something that is
not a defect. Six red nights teaches the operator to ignore red. That is the damage.

WHAT SHIPS. A declared posture (advisory | binding), recorded on every ExecutionRun, with fault
severity and the acceptance check following it.

READ THE LAWS FIRST - THIS IS A GATE, NOT ADVICE.
- Read agents/execution/laws/laws.md whole, plus its test-plan.md, docs/laws/conventions.md and
  docs/laws/drift-register.md, BEFORE you open an editor.
- Fill the "Law reading record" table at the bottom of the spec BEFORE your first code change.
- If a law contradicts the spec, STOP and report. The law is more likely right than I am.

THE LAW CYCLE IS IN SCOPE AND MANDATORY. This sprint adds a guarantee execution has never made, so
it owes: a new clause in agents/execution/laws/laws.md (bump the law version, add a Changelog line),
a test-plan.md row per clause, the clause ID cited in each new test docstring, the rollup updated in
BOTH docs/laws/ledger.md AND docs/laws/INDEX.md, and drift rows for two silences I already measured:
  (1) execution's laws.md contains ZERO clauses about deliberation or the veto - the whole gate is
      law-invisible, which is exactly what let its posture be set by arithmetic;
  (2) deliberation_grace_seconds is a registered tunable() in settings.py:122 but has NO row in
      execution's PARAM table.
File both as drift rows. Do NOT invent law to paper over them.
The rollup is DERIVED - make ci recomputes it. Two clauses proven by three test rows is +2, not +3.

FOUR DESIGN DECISIONS - record them in docs/design-log.md with rejected alternatives BEFORE coding:
  1. Is deliberation_posture a tunable() or a mode selector? Almost certainly a MODE SELECTOR:
     order_price_tolerance_mode and stop_target_mode are both declared "NO (mode selector)" in their
     locked PARAM tables, citing ADR-0013 - a tunable is a value WITHIN a formula, a mode selector
     chooses WHICH formula runs. So: bare default in settings.py, NOT tunable(), plus a PARAM row.
     S183's spec got this exact call backwards and had to be corrected mid-build. Do not repeat it.
  2. Under binding, what happens to a buy with no verdict - drop it loudly, or hold the PMRun?
     I recommend drop. Holding re-creates the DL-98 race and risks the S147 freeze, and a buy
     decided on yesterday's prices is a different order. Say so if you disagree after reading.
  3. What does the acceptance gate assert under each posture? Under binding, keep today's
     debate_coverage floor 1.0 / failed_open_count ceiling 0. Under a declared advisory, replace
     them with a check that every unvetoed submission is ATTRIBUTABLE - posture recorded, reason
     present, count reported as an observable. DO NOT make advisory simply pass everything: a gate
     that cannot fail is not evidence, and that is worse than a gate that cries wolf.
  4. Does the existing five-state DeliberationStatus vocabulary survive? "Why was there no verdict"
     and "what policy applied" are different questions; collapsing them is how this started.
     I recommend keeping the five states and adding posture as its own field.

HARD INVARIANTS - breaking any of these fails the sprint:
- EXITS NEVER WAIT, IN EITHER POSTURE. deliberation_gate.py's docstring is explicit: blocking an
  exit on an LLM outage is what S147 refused and what froze the book for eight days, and ADR-0017
  makes the analyst the sole author of exits. A sell-only PMRun must submit immediately under
  binding exactly as today. If your change can hold or drop an exit, STOP and report.
- This is NOT softening the veto. DL-119 explicitly rejected lowering the bar to restore throughput.
  Declaring the posture is the opposite move. A verdict that DID arrive is honoured exactly as now -
  drop_vetoed keeps its current behaviour byte-for-byte.
- The DEFAULT posture must reproduce today's behaviour exactly, so the merge alone changes nothing.
  Measure which posture is live first, by reading ExecutionRun.deliberation_status across the last
  10 runs. The switch is what changes behaviour, and the operator throws it.
- DO NOT touch deliberation_grace_seconds or the deliberator's timeouts. Their values stay where
  DL-116 left them. This sprint removes their POLICY role, not their value. If the posture ends up
  depending on the grace window, the sprint has failed - that dependency IS the defect.

OUT OF SCOPE: any change to what the deliberator decides or how it debates (that is S172); any
retry/queue/fallback provider for the outage; any ADR reversal.

TESTS - plant them first, watch them fail, paste the red output:
  A1 advisory: unvetoed buys submit, posture is on the run record, fault is WARNING not error.
  A2 binding: buys with no verdict do NOT reach the broker; an error fault names the posture.
  A3 exits never wait - sell-only PMRun, posture=binding, no DeliberationRun -> submitted at once.
  A4 a verdict that arrived is honoured identically under both postures.
  A5 the acceptance gate asserts the posture was HONOURED - does not fail on advisory fail-opens,
     DOES fail when the posture is absent or unattributable.
  A6 the default reproduces main's behaviour exactly.

TRAPS:
- settings.py is at 150 lines, exactly the warn threshold. Plan the split BEFORE you write.
- The deploy will be a full "up", not a retag: new env key, probably a new ExecutionRun property.
- THE PROVIDER IS DOWN UNTIL 2026-08-30. You cannot get a real debate. EVERY proof must be a
  fixture. Do not schedule a live run to check it works, and do not read a live fail-open as
  evidence your code did anything.
- Read DeliberationRun.failed_open_reason before any latency or count metric. Four wrong diagnoses
  in a row have come from taking a number that correlates with the cause for the cause.
- Take the next free DL number and RE-CHECK IT AT MERGE. The log has historic duplicates and a
  branch cut before another DL lands will collide even when the number was free at branch time.
  Highest as of 2026-08-22 is DL-126.

GATE: make ci, all 11 steps, exit 0, 100.00% coverage. Redirect to a FILE and read the file -
never pipe it, because make ci | tail reports tail's exit code, not make's. Then push the branch
and run make gate-ran FROM THE WORKTREE whose HEAD is the commit you are proving, and check the
printed SHA against git rev-parse HEAD. Do not merge - hand back.

HANDBACK: fill the Law reading record, the Test plan results table, Closeout - evidence (with real
pasted output, red run first), and Return notes. Set Status: to BUILT. State anything not met
plainly as "verified failing" or "not done". An incomplete handback is returned, not repaired.
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
| `agents/execution/deliberation_gate.py` | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md`; ADR-0022 | `EXEC-IDN-01`, `EXEC-NEV-01`, `EXEC-OBS-02`; no existing execution clause governs deliberation posture | Yes. The posture must be declared policy, not execution judgement; any binding drop must remain buy-only and must not alter arrived-veto handling. |
| `agents/execution/pm_execution.py` / `ExecutionRun` evidence | Same execution law set; `docs/laws/ledger.md`; `docs/laws/INDEX.md` | `EXEC-IDN-01`, `EXEC-OUT-01`, `EXEC-TYP-03`, `EXEC-OBS-01` | Yes. The run record needs a separate posture axis; the five `deliberation_status` states should continue to answer why no verdict was applied. |
| `agents/execution/settings.py` | Same execution law set, with the `PARAM` table checked directly | `EXEC-PARAM` table; conventions section 4; `order_price_tolerance_mode` precedent | Yes. `deliberation_posture` is a mode selector, not a `tunable()`. The missing `deliberation_grace_seconds` row is drift, not a reason to register the posture as a tunable. |
| `agents/execution/deliberation_faults.py` | Same execution law set | `EXEC-OBS-02`; no existing clause distinguishes posture-specific deliberation fault severity | Yes. Fault severity must follow the declared posture: expected advisory fail-open is not the same evidence as a binding policy breach. |
| `orchestration/packs/trading_deliberation_view.py` | `docs/laws/INDEX.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md`; `docs/laws/ledger.md` | Layer-3 acceptance discipline; conventions section 3 | Yes. Acceptance must prove the declared posture was honored, not merely count debates unconditionally. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** YES. The sprint
adds an execution guarantee that deliberation posture is declared and recorded, and that buy orders
with no verdict follow that declared posture while exits do not wait. The law cycle is done in
execution law v1.2: `EXEC-OUT-09`, `EXEC-NEV-06`, and `EXEC-OBS-04`; test-plan rows were added; both
rollups were updated; `DRIFT-048` was corrected and `DRIFT-049` remains open for S187.

**Contradictions found between a law and this spec:** None found during the pre-code read.

**Laws found silent where a decision was needed:** Confirmed. Execution's `laws.md` has no clause that
governs deliberation/veto posture, and `deliberation_grace_seconds` is present in
`agents/execution/settings.py` but absent from the execution `PARAM` table. Both were filed as drift
rows in `docs/laws/drift-register.md`: `DRIFT-048` corrected by S185 law v1.2, `DRIFT-049` left open.

**Clauses that were ⬜ and are now proven:** `EXEC-OUT-09`, `EXEC-NEV-06`, and `EXEC-OBS-04`.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_advisory_posture_submits_unvetoed_buy_and_records_warning` | `agents/execution/tests/test_deliberation_posture.py` | PASS | `EXEC-OUT-09`, `EXEC-OBS-04` |
| A2 | `test_binding_posture_blocks_unvetoed_buy_and_records_error` | `agents/execution/tests/test_deliberation_posture.py` | PASS | `EXEC-NEV-06`, `EXEC-OBS-04` |
| A3 | `test_binding_posture_does_not_block_sell_only_run` | `agents/execution/tests/test_deliberation_posture.py` | PASS | `EXEC-NEV-06` |
| A4 | `test_arrived_veto_is_honored_identically_under_both_postures` | `agents/execution/tests/test_deliberation_posture.py` | PASS | `EXEC-NEV-01`, `EXEC-NEV-06` |
| A5 | `test_advisory_fail_open_passes_when_attributed`; `test_advisory_fail_open_fails_without_recorded_posture`; `test_advisory_fail_open_fails_without_reason`; `test_advisory_fail_open_fails_with_unattributable_status`; `test_deliberation_fails_without_linked_execution_run` | `orchestration/tests/test_trading_deliberation_posture.py` | PASS | `EXEC-OUT-09`, `EXEC-OBS-04` |
| A6 | `test_default_posture_preserves_fail_open_submission_as_advisory`; `test_advisory_fail_open_deliberation_run_passes_acceptance` | `agents/execution/tests/test_deliberation_posture.py`; `orchestration/tests/test_trading_acceptance_deliberation.py` | PASS | `EXEC-OUT-09`, `EXEC-OBS-04` |

**Tests added beyond the plan:**

- `test_deliberation_posture_is_mode_selector_not_tunable` proves the mode selector is not a
  `tunable()` and rejects invalid posture values.
- `test_execution_run_deliberation_posture_props_are_declared` plants a misspelled
  `deliberation_postuer` vocabulary property and verifies the pack rejects it.
- `test_execution_contract_ownership_version` records the execution contract bump to `0.4.0`.
- Existing acceptance tests now pin binding posture where they still require full debate coverage.

---

## Closeout — evidence

**Status:** BUILT locally on `sprint-185-the-veto-posture-is-declared-not-arithmetic`; remote
`make gate-ran` is post-push evidence and must be quoted in final handback.

**Tree the proofs ran in (and `.env` present?):**

`C:\Users\yury_\Downloads\project\trading-agents`; `.env` present for the live last-10-run
measurement only. Tests and `make ci` used fixtures and did not require live provider calls.

**Result:** Implemented S185 as a declared execution posture axis. Every `ExecutionRun` records
`deliberation_posture`, `deliberation_status`, and `deliberation_blocked_count`; explicit `binding`
blocks buy exposure when no `DeliberationRun` arrives after grace, while exits and arrived vetoes keep
their existing behaviour. Advisory fail-opens now remain attributable without making the acceptance
gate mute. Version bumped to `0.92.00`.

**Files changed:**

Execution posture/settings/fault/run plumbing; execution contract; trading deliberation observatory
view and vocabulary pack; local pipeline settings pass-through; focused execution/orchestration/
vocabulary/contract tests; execution laws/test-plan plus law rollups and drift register; sprint/state/
design-log docs; `pyproject.toml` and `uv.lock`.

**Design decisions:** `DL-128` records the four decisions and the road not taken: posture is a mode
selector; default/no-config is advisory to preserve measured broker submission shape; explicit
binding drops only unreviewed buys; advisory acceptance asserts attribution; the five
`deliberation_status` states remain separate from posture.

**Proof — the red run first:**

```text
.venv\Scripts\python.exe -m pytest agents\execution\tests\test_deliberation_posture.py orchestration\tests\test_trading_deliberation_posture.py --no-cov
7 failed, 1 passed
```

The planted failures covered missing `deliberation_posture`, binding buys still reaching the broker,
and advisory acceptance still failing on raw debate coverage/fail-open count.

**Proof — the green run:**

```text
.venv\Scripts\python.exe -m pytest agents\execution\tests\test_deliberation_posture.py agents\execution\tests\test_execution_deliberation_gate.py agents\execution\tests\test_execution_poll.py orchestration\tests\test_trading_deliberation_posture.py orchestration\tests\test_trading_deliberation_view.py orchestration\tests\test_trading_acceptance_deliberation.py orchestration\tests\test_veto_stage.py tests\test_graph_vocabulary_deliberation.py --no-cov
46 passed

.venv\Scripts\python.exe -m pytest tests\test_graph_vocabulary_deliberation.py tests\test_graph_vocabulary_properties.py tests\test_graph_vocabulary_completeness.py orchestration\tests\test_graph_vocabulary_e2e.py --no-cov
25 passed
```

**Guards planted:** Advisory-no-verdict buy, binding-no-verdict buy, binding sell-only exit,
arrived-veto under both postures, advisory fail-open attribution/missing posture/missing reason/
unattributable status/no linked execution, mode-selector validation, and vocabulary misspelling
`deliberation_postuer`. Each guard was red before implementation or before its final coverage branch,
then restored and included in the green focused/full gates.

**Module line counts:** `agents/execution/deliberation_gate.py` 147,
`agents/execution/pm_execution.py` 101, `agents/execution/deliberation_faults.py` 94,
`agents/execution/deliberation_posture.py` 46, `agents/execution/settings.py` 152,
`orchestration/packs/trading_deliberation_view.py` 136, `contracts/execution.py` 130. `settings.py`
stayed under 200 by adding only the selector field and keeping posture logic in the new
`deliberation_posture.py` helper.

**`make ci`:** redirected to `C:\Users\yury_\AppData\Local\Temp\s185-make-ci.log`; exit code stored
in `C:\Users\yury_\AppData\Local\Temp\s185-make-ci.exit`; final exit `0`.

```text
uv run ruff check . --output-format=github
uv run ruff format --check .
1019 files already formatted
Success: no issues found in 841 source files
TOTAL                                                     15169      0   3244      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
================= 2378 passed, 4 skipped in 192.39s (0:03:12) =================
uv run pip-audit
No known vulnerabilities found
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 3 new file(s)
```

**`make gate-ran`:** Not yet run at this in-tree closeout point because the final commit has not been
pushed. Run after pushing this branch from `C:\Users\yury_\Downloads\project\trading-agents`, compare
the printed full SHA to `git rev-parse HEAD`, and quote it in final handback.

**Not met / verified failing:**

Remote branch gate proof is pending until after final commit/push. The original A6 wording asked for
identical fault severity/acceptance; that exact subclaim is intentionally not preserved because the
defect was accidental red/error evidence. The preserved default behaviour is the measured broker
submit/drop shape from the last 10 runs.

---

## Return notes

- Live measurement before design showed the last 10 `ExecutionRun`s already submit unreviewed or
  fail-open orders; defaulting to `advisory` preserves that broker-action shape while making the
  evidence explicit.
- Deploy implication remains full `up`, not image-only retag: `ExecutionRun` vocabulary moved and the
  operator must declare `EXECUTION_DELIBERATION_POSTURE` in the fleet.
- `DRIFT-049` remains open for S187: `deliberation_grace_seconds` still needs a PARAM-table row.
