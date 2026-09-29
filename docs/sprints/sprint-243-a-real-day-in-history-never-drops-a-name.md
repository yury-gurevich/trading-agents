<!-- Agent: planning | Role: sprint handover -->
# Sprint 243 — a real day in a name's history never drops it, and a designed "no claim" does not page the operator

**Phase:** Etalon-first continuous improvement (DL-19) · work-queue 94 (live defect)
**Branch:** `sprint-243-a-real-day-in-history-never-drops-a-name`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** [DL-245](../design-log.md) (the defect, measured, and the direction) · DRIFT-014 / DRIFT-012 (why the guard exists) · the builder's decisions go to the **next free DL** (`DL-247` at spec time)

> **Why this bump kind.** No new capability: the guard exists to stop a bad print reaching a decision,
> and it is excluding names for real market days instead. A fix, so PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED except through this sprint's law cycle.** A clause you believe is wrong beyond it is a `drift-register.md` row plus a report |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | `drift-register.md` is the one law-adjacent file you may append to freely |

Binding here: provider **`PROV-OUT-08`** (the barrier fetch runs "the extreme-move guard, unchanged") and
the **PARAM row `max_daily_move_sigma`** (*"Flag daily returns that are extreme relative to the requested
window"*; its default cell reads `4.0` while `agents/provider/settings.py` holds `8.0`, so reconcile it);
forecaster **`FORE-FAIL-04`** (a dropped ticker "records a fault").

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read each `test-plan.md` alongside its `laws.md`.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** before your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring**.

### 🩹 The law-cycle question — answer before step 5

**The planner's answer: YES, for two books.** The provider's guarantee changes (the guard judges the
newest session, not the whole window: amend the PARAM row's meaning and `PROV-OUT-08`'s "unchanged",
and state the guard's scope in an OUT or FAIL clause), and the forecaster's (`FORE-FAIL-04`: a
designed refusal is a `warning`, a missing input stays an `error`). Each: version bump + Changelog,
`test-plan.md` rows, clause IDs in docstrings, rollups in `docs/laws/ledger.md` **and**
`docs/laws/INDEX.md`, drift rows for what slipped.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/provider/domain/integrity.py` (124) | `agents/provider/laws/laws.md` + `test-plan.md`; DRIFT-012, DRIFT-014 | the guard; `max_daily_move_sigma` PARAM row |
| `agents/provider/barrier_history.py` (191) | same | `PROV-OUT-08` |
| `agents/forecaster/barrier_forecast.py` (180) | `agents/forecaster/laws/laws.md` + `test-plan.md` | `FORE-FAIL-04`; `kernel.errors` `Severity` |

⚠️ **The invariant: a genuinely bad newest bar is still excluded, by name.** This sprint narrows *when*
the guard fires, never whether it exists. A plant that removes the guard must turn a test red.

---

## Goal

At merge, the extreme-move guard judges only each ticker's **newest session** against that session's
pooled cross-section; a real extreme day earlier in the window never drops a name from the scan universe
or the barrier history. A forecaster refusal that is a designed outcome (the provider dropped the
ticker, the fit failed EXP-018's acceptance rule, too little history) is recorded at `warning`, so it no
longer counts as an open incident; a missing input (no `BarrierHistory` in the graph, not requested)
stays `error`.

## Why (context)

`sched-2026-09-28`'s first Telegram brief read *Needs you: 2 open incidents*: TXN and COP got no barrier
claim, at `error`, for a real market day. Measuring it found the same guard silently excluding CHTR from
the scan universe on every run since 2026-08-13.

### Measured, 2026-09-29 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| TXN / COP barrier drops | tripped on **2025-04-09** (tariff-pause rally): +16.76 % / +12.82 % open-to-close against a pooled 8σ of **11.34 %** (σ 1.42 % over 14 names × 760 sessions) | *[measured]* SIP raw daily bars from Alpaca, the guard's formula recomputed |
| CHTR scan-universe drops | excluded on **41 of 78** `MarketData` runs, every run since 2026-08-13; its day is **2026-04-24, −22.7 %** open-to-close | *[measured]* `props->'snapshot'->'quality'->'anomalous_tickers'` per `MarketData` on Neon; SIP raw bars |
| How long they would last | TXN/COP until ~2028-04 (760-session window); CHTR until ~2027-02 (203-session window) | *[measured]* window lengths |
| Is anything in the guard's history a bad print? | all three hits are real events | *[ASSUMED — not measured]* beyond these three; F1 settles it over every run's anomaly list |
| The incident count | reads unresolved `error`/`critical` Faults of the latest day (`kernel/fault_incidents.py`) | *[measured]* code |

---

## Scope — and what is deliberately NOT here

1. **The guard judges the newest session only** (per ticker, its last bar, against the pooled
   open-to-close spread of the batch's newest session). The failing test first: a batch whose only
   extreme move is on an older session keeps the ticker; one on the newest session drops it, by name.
2. **Both paths inherit it** through `validate_bars`: the daily ingest and the barrier fetch. No second
   guard.
3. **Forecaster severity**: designed refusals → `warning`; missing inputs → `error`. Name each
   refusal's class in the design log.
4. **Law cycle** for provider and forecaster; reconcile the PARAM row's default (`4.0` vs `8.0`).

### Out of scope (do NOT build this sprint)

- **A per-ticker volatility model** for the guard (own-history σ, market-wide-day exemption). Recorded
  as the rejected alternative; revisit only if a newest-session false positive is measured.
- **Resolving today's two Faults** — the planner acks them after deploy.
- **The settlement void rule** (S241's `suspected_corporate_action`) — a different guard, untouched.

### The road not taken (LAW-06)

- **Exempt the barrier fetch only.** Rejected: CHTR shows the daily ingest has the same defect.
- **Per-ticker σ on the name's own history.** Rejected for now: more code, and a name's own crash day
  inflates its own σ; the newest-session scope removes the failure measured.
- **Raise `max_daily_move_sigma`.** Rejected: DRIFT-012 already raised it 4 → 8; TXN's +16.8 % needs
  ~12σ, and a real crash can be larger still.
- **Ack the Faults.** Rejected: they recur on every run where the name is a buy.

---

## The design decisions this sprint has to make

1. **The newest session's definition** per ticker (its own last bar) vs the batch's last date (a ticker
   whose newest bar is stale); name what happens to a stale newest bar.
2. **The pool**: the batch's newest-session moves only; with fewer than two, the guard abstains (as today).
3. **Which forecaster refusals are designed** (warning) and which are missing inputs (error).

🪤 **Take the next free DL number, then re-check it at merge.**

---

## Blast radius — measured 2026-09-29

| What | Detail |
| --- | --- |
| Files changed | `agents/provider/domain/integrity.py` 124, `agents/forecaster/barrier_forecast.py` 180, provider + forecaster `laws.md` / `test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`, tests; `agents/provider/barrier_history.py` (191) only if its clause text needs it |
| Agents affected | provider, forecaster — neither imports the other |
| Contract change? | No expected |
| Graph vocabulary change? | No |
| New env keys / tunables | None (the PARAM row's text and default cell change, not the tunable) |
| Deploy implication | **Image-only retag** of provider + forecaster (the whole fleet, by convention, so the board reads one tag) |
| Rollback | Retag back to `s242`. **Not undone by a retag:** nothing in the graph; the `MarketData` written while deployed will include names the old guard dropped (CHTR), which is the intended change. The reporter + scanner memory is untouched by a retag |

---

## Steps, in order

1. **Read the laws** and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Plant the failing tests first** (B1, B2, B4) and watch them fail. Paste the red output.
4. **Implement.**
5. **Law cycle** for both books.
6. **DL-70 plants**: (1) the guard judges the whole window again; (2) the guard removed; (3) a designed
   refusal back at `error`; (4) a missing input at `warning`. Each red, pasted, restored.
7. **`make ci` green** — redirected to a file, never piped.
8. **Fill the handback sections.**

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| B1 | 🎯 A real old extreme day keeps the name | 760 sessions; one ticker +17 % on session 100, normal since | the ticker is delivered, not in `anomalous_tickers` |
| B2 | 🎯 A bad newest bar is still dropped | the same, with the extreme move on the newest session | the ticker is excluded, named in `anomalous_tickers` |
| B3 | The daily ingest inherits it | 203-session fixture, CHTR-shaped −22.7 % mid-window | CHTR reaches the scanner's input |
| B4 | 🎯 Designed refusal is a warning | provider dropped a ticker | `forecast_barrier` records a Fault at `warning`; `live_fault_incidents` does not count it |
| B5 | 🪤 Missing input is an error | no `BarrierHistory` node | Fault at `error`, counted as an incident |
| B6 | Stale newest bar | a ticker whose last bar is older than the batch's | the decision-1 behaviour, as recorded |

---

## Success factors

- [ ] B1–B6 pass; B1, B2, B4 red before the fix.
- [ ] Law cycle done for provider and forecaster; the PARAM default cell reconciled.
- [ ] Design decisions recorded with rejected alternatives.
- [ ] Every DL-70 plant red, pasted, restored.
- [ ] Every touched module < 200 lines (`barrier_history.py` is at **191**).
- [ ] `make ci` exit 0, 100.00 % coverage.
- [ ] **Owed to the planner:** `uv lock`, Windows `make ci`, `make gate-ran`, **F1** (every live
      `MarketData`'s newest session re-judged: which names the new guard would drop, expected none or
      named bad prints), the retag, **F2** (next run: CHTR scanned, no barrier drop for a history day,
      the brief's incident count unchanged by a designed refusal), ack today's two Faults.

---

## Traps

🪤 **Pooled σ changes meaning.** Over one session the pool is ~99 moves, not ~20,000; a quiet day has a
small σ, so 8σ may be tighter than today. Measure the newest-session false-positive rate in F1 before
trusting 8.
🪤 **The scanner's `missing_history` count** today includes CHTR; after the fix it should fall by one.
A test asserting the old count will fail for the right reason — update it, and say so.
🪤 **Severity is read by more than the brief.** Grep every reader of `severity` (`fault_incidents`,
`fault_query`, the dashboard) before choosing `warning`.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). No `# noqa`.
  📌 Current sizes: `barrier_history.py` **191**, `barrier_forecast.py` **180**, `integrity.py` 124.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers; no new tunable.
- Faults, not silent failure.
- `make ci` every step green, 100.00 % coverage, redirected to a file.
- No `.env` in a cloud session: every proof is a unit test. State which tree you ran in.

---

## Sequencing after merge

1. Planner: `uv lock`, Windows `make ci`, `make gate-ran` from the worktree at the branch's `HEAD`
   (check the printed SHA), F1 on Neon, merge, post-merge CodeQL.
2. **Deploy: image-only retag** (operator's call). Record the rollback tag with the deploy.
3. F2 on the next scheduled run; ack today's TXN / COP Faults.

---

## Handover — paste this to the Claude cloud session

```text
Sprint 243 — a real day in a name's history never drops it, and a designed "no claim" does not page
the operator. Spec: docs/sprints/sprint-243-a-real-day-in-history-never-drops-a-name.md on main (read
ALL of it, then CLAUDE.md). Repo: yury-gurevich/trading-agents.

Branch: sprint-243-a-real-day-in-history-never-drops-a-name, cut from main. Never main. If your session
forces another branch name, use it and name it in the handback.
You have NO .env, NO gh, NO Azure and no route to download.pytorch.org. Every proof is a unit test.
You cannot run `make gate-ran`: it is owed to the planner. Leave uv.lock untouched and say so. Take the
next free DL (DL-247 at spec time; re-check on main).

This handover is complete: nobody will send you follow-up messages. If something in the spec is wrong
or blocked, record it in the handback (Return notes, "not done") and stop; do not wait.

What and why: agents/provider/domain/integrity.py's extreme-move guard pools open-to-close moves over
EVERY bar in the window and drops a ticker for any day beyond max_daily_move_sigma (8) sigma. Real
days trip it: CHTR (2026-04-24, -22.7 %) is excluded from the scan universe on 41 of 78 runs; TXN and
COP (2025-04-09, +16.8 % / +12.8 %) get no barrier claim, and the forecaster records each refusal at
severity error, so the operator's brief reads "Needs you: 2 open incidents" for a non-defect.

MUST RULE before any code: read, whole, agents/provider/laws/laws.md + test-plan.md,
agents/forecaster/laws/laws.md + test-plan.md, docs/laws/conventions.md, docs/laws/drift-register.md
(DRIFT-012, DRIFT-014). Fill the Law reading record first.

Law-cycle answer: YES for both. Provider: the guard's scope (newest session), PROV-OUT-08's
"unchanged", the max_daily_move_sigma PARAM row (its text says "relative to the requested window"; its
default cell says 4.0 while settings.py holds 8.0: reconcile). Forecaster: FORE-FAIL-04's severity
(designed refusal -> warning; missing input -> error). Version bumps + Changelog, test-plan rows,
clause IDs in docstrings, rollups in docs/laws/ledger.md AND docs/laws/INDEX.md, drift rows.

Build:
1. The guard judges each ticker's NEWEST session only, against the pooled spread of the batch's
   newest-session moves; fewer than two moves -> abstain. Older sessions are never re-judged. Both the
   daily ingest and the barrier fetch inherit it through validate_bars.
2. forecast_barrier: a designed refusal (provider dropped, fit outside EXP-018's rule, too little
   history) -> Fault at warning; a missing input (no BarrierHistory node, ticker not requested) ->
   error. Check every reader of severity (kernel/fault_incidents.py, kernel/fault_query.py, the
   dashboard) before choosing.
3. Law cycle for both books.

Order: next free DL (decisions 1-3, with rejected alternatives) -> red tests B1, B2, B4 (paste) ->
implement -> law cycle -> DL-70 plants (whole-window guard again; guard removed; designed refusal back
at error; missing input at warning: each red, paste, restore) -> make ci redirected to a file, exit 0,
100.00 %.

DO NOT:
- remove the guard, or raise max_daily_move_sigma as the fix.
- touch S241's settlement void rule (suspected_corporate_action).
- add a tunable, label, property, edge or env key.
- grow any module past 200 (barrier_history.py is at 191); # noqa to bypass a rule.
- let any test reach the network.
- claim a live proof or GATE PROVEN: F1, F2 and the gate are the planner's.
- pin a version: PATCH, next available at merge.

Handback — the planner returns it if ANY of these is missing:
[ ] Law reading record filled, including the law-cycle answer and contradictions/silences found.
[ ] Test plan results: B1-B6, each with final test name, file, PASS, clause IDs cited.
[ ] Closeout: the red run pasted before the fix; the green run after.
[ ] Each of the four DL-70 plants: what was planted, its red output, restored.
[ ] Module line counts for every file touched (all < 200).
[ ] make ci: the file, exit code, passed/skipped, coverage 100.00 %, dependency audit, detect-secrets.
[ ] Exactly how uv.lock was touched (untouched and owed, or re-resolved).
[ ] The design decisions under the DL you took, with rejected alternatives.
[ ] Return notes: scope held or moved; what you disagreed with after reading the laws; the
    newest-session false-positive risk as you see it.
[ ] Status: BUILT on the spec, and this sprint's README.md row leads with BUILT, in the same commit.
[ ] Owed items named: uv lock, make gate-ran, Windows make ci, F1, retag, F2, ack the two Faults.
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
| *to fill* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *to fill*

**Contradictions found between a law and this spec:** *to fill*

**Laws found silent where a decision was needed:** *to fill*

**Clauses that were ⬜ and are now proven:** *to fill*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| B1–B6 | *to fill* | | | |

**Tests added beyond the plan:** *to fill*

---

## Closeout — evidence

**Status:** *to fill (BUILT)*

**Tree the proofs ran in (and `.env` present?):** *to fill*

**Result:** *to fill*

**Files changed:** *to fill*

**Design decisions:** *to fill*

**Proof — the red run first:**

```text
to fill
```

**Proof — the green run:**

```text
to fill
```

**Guards planted:** *to fill*

**Module line counts:** *to fill*

**`make ci`:** *to fill*

**`make gate-ran`:** owed to the planner.

**Not met / verified failing:** *to fill*

---

## Return notes

- *to fill*
