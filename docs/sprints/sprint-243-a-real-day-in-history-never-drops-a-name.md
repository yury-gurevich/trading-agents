<!-- Agent: planning | Role: sprint handover -->
# Sprint 243 — a real day in a name's history never drops it, and a designed "no claim" does not page the operator

**Phase:** Etalon-first continuous improvement (DL-19) · work-queue 94 (live defect)
**Branch:** `sprint-243-a-real-day-in-history-never-drops-a-name`
**Status:** MERGED 2026-09-29 — `7e157697` on `main`, 0.119.02, tag `v0.119.02`; GATE PROVEN for `9391b12b`; F1 passed on Neon; DEPLOYED `s243` (image-only retag, 2026-09-29 16:34 AEST); F2 passed 2026-10-02 (four runs since the deploy)
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

*Filled 2026-09-29, before the first code change. Read whole: `agents/provider/laws/laws.md` (v1.5) +
`test-plan.md`, `agents/forecaster/laws/laws.md` (v1.7) + `test-plan.md`, `docs/laws/conventions.md`,
`docs/laws/drift-register.md` (DRIFT-012, DRIFT-014 and the rest), DL-245; and every reader of a
`Fault`'s severity (`kernel/fault_incidents.py`, `kernel/fault_query.py`, `kernel/fault_graph.py`,
`kernel/metrics_prometheus.py`, `surfaces/queries/faults.py`, `surfaces/dashboard/chat.py`,
`surfaces/mcp_tools.py`, `surfaces/render_extras.py`, `agents/supervisor/domain/health.py`).*

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `agents/provider/domain/integrity.py` | provider `laws.md` + `test-plan.md`; DRIFT-012, DRIFT-014 | `PROV-OUT-08` ("the extreme-move guard, unchanged"), `PROV-OUT-03` / `PROV-FAIL-02` (an excluded ticker is a per-item partial degradation, flagged), `PROV-NEV-01` (never unvalidated data), `PROV-STA-04` (staleness is its own flag), PARAM `max_daily_move_sigma` | **Yes, twice.** (1) No clause states *which bars* the guard judges: its only statement is the PARAM row ("relative to the requested window"), so the new scope needs a clause of its own (`PROV-OUT-09`), not only a PARAM edit. (2) Working the pooled z-score on one session: a population z over *n* moves can never exceed √(n−1) (Samuelson), and the guard needs *more* than 8, so it can fire only on a session holding **≥ 66** moves. The daily ingest (~99 names) can; the barrier fetch (~14 buys) **cannot, ever**. Test B2 therefore uses a 99-name batch, and the bound goes into the PARAM rationale and a drift row rather than being discovered later. `PROV-OUT-03b`'s cited test used a lone ticker whose own history made it the outlier: under the new scope a one-name session abstains, so that test is rewritten to a two-name session (said in the Return notes). |
| `agents/provider/barrier_history.py` | same | `PROV-OUT-08`, `PROV-TRG-04` | No code change needed: it inherits the guard through `validate_bars`; its drop reason (`extreme_move_guard: an open-to-close move beyond max_daily_move_sigma`) stays true. Only the clause text moves. |
| `agents/forecaster/barrier_forecast.py` | forecaster `laws.md` + `test-plan.md`; `kernel/errors.py` `Severity` | `FORE-FAIL-04` (every refusal "records a fault"), `FORE-IN-07` (the refusals' inputs), `FORE-OUT-06` (neutral reading), `FORE-OBS-02` (degraded paths emit faults, never buried) | **Yes.** `fault_boundary` records every exception at `error` and takes no severity, so a `warning` refusal must be submitted by the handler itself; I keep one exception type (`BarrierClaimRefusedError`, so a Fault's `error_type` and signature do not move) carrying its own severity. `FORE-OBS-02` binds: a `warning` still reaches the sink and the graph, it is only not an *incident*. A failed history is classed **designed** because every failed `BarrierHistory` already has the provider's own `error` Fault behind it (`agents/provider/agent.py` `fault_boundary`, or `barrier_history.py`'s own), so the forecaster's echo at `error` counted one outage twice. `barrier_forecast.py` is at 180: the refusal classification moves to a new `barrier_refusal.py` so the module shrinks rather than grows. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **Yes, for two
books; no `contracts/` change.** Provider v1.5 → v1.6: new `PROV-OUT-09` (the guard's scope: each
ticker's newest session against that session's pooled cross-section; an older session is never
re-judged; fewer than two moves or no spread abstains; both paths), `PROV-OUT-08`'s "unchanged" →
"the shared guard of `PROV-OUT-09`", the `max_daily_move_sigma` PARAM row reconciled (`4.0` → `8.0`,
the rationale re-worded and the √(n−1) bound stated). Forecaster v1.7 → v1.8: `FORE-FAIL-04` amended
(a designed refusal records a `warning`; a missing or broken input an `error`). No contract, label,
property, edge, tunable or env key moves.

**Contradictions found between a law and this spec:** None that stops the build. Three worth
naming. (a) The PARAM row's default cell read `4.0` while `settings.py` holds `8.0` since DRIFT-012
(0.35.02): the law was stale, `8.0` is right, reconciled here. (b) `PROV-OUT-08` promised the guard
"unchanged" and the PARAM text said "relative to the requested window": both are the guarantee this
sprint changes, so both are amended rather than contradicted. (c) **The spec's premise that both
paths inherit a working guard is only half true**: by √(n−1), a newest-session pool of the barrier
fetch's ~14 names can never reach 8σ, so on that path the guard is present but cannot fire. The
invariant "a genuinely bad newest bar is still excluded, by name" holds on the daily ingest (≥ 66
names) and on the barrier path only upstream of it (a name the ingest drops never becomes a buy).
Built as specified; recorded as DRIFT-090 (OPEN) and in the Return notes.

**Laws found silent where a decision was needed:** (1) the provider book never said which bars the
extreme-move guard judges (a PARAM row was its only statement) → `PROV-OUT-09`, DRIFT-088. (2) The
forecaster book never said at what severity a refusal records its fault, while `kernel/fault_incidents.py`
(DL-208) makes severity decide whether it is an incident → `FORE-FAIL-04` amended, DRIFT-089. (3) No book
says what a newest bar that is *not* on the batch's newest session is judged against (a lagging
ticker) → decided in DL-247 D1 and written into `PROV-OUT-09`. (4) No clause bounds a pooled guard's
sensitivity by the pool's size → DRIFT-090 (OPEN). Not filed, noted: `docs/laws/conventions.md` §1's
prefix table says `FCST` for the forecaster while its book uses `FORE`.

**Clauses that were ⬜ and are now proven:** none were ⬜; `PROV-OUT-09` is new and proven (20 / 65 →
21 / 66). `PROV-OUT-08` and `FORE-FAIL-04` are amended and re-proven (forecaster 25 / 52 unchanged).

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| B1 | `test_a_real_old_extreme_day_keeps_the_name` (99 names × 760 sessions, +17 % on session 100) | `agents/provider/tests/test_newest_session_guard.py` | PASS (red before the fix) | `PROV-OUT-09` |
| B2 | `test_a_bad_newest_bar_is_still_dropped_by_name` (the same +17 % on the newest session: excluded, named, `used_fallback` False) | same | PASS (**green before the fix too**: the old whole-window guard also drops a newest-bar outlier, so B2 cannot be red first; it is the preservation test, and plant 2 turns it red) | `PROV-OUT-09`, `PROV-FAIL-02` |
| B3 | `test_the_daily_ingest_keeps_a_name_with_a_real_crash_mid_window` (99 names × 203 sessions through `ingest_once`, CHTR −22.7 % at session 101; the written `MarketData` carries all 203 CHTR bars, `anomalous_tickers` empty) | same | PASS (red before the fix) | `PROV-OUT-09`, `PROV-OUT-01` |
| B4 | `test_a_ticker_the_provider_dropped_is_a_warning_not_an_incident` (fault `warning`, written through `GraphFaultSink`, `live_fault_incidents` = 0) | `agents/forecaster/tests/test_barrier_refusal_severity.py` | PASS (red before the fix) | `FORE-FAIL-04` |
| B5 | `test_no_barrier_history_is_an_error_and_an_incident` (fault `error`, `live_fault_incidents` = 1) | same | PASS (green before the fix: missing input was always `error`; plant 4 turns it red) | `FORE-FAIL-04`, `FORE-IN-07` |
| B6 | `test_a_lagging_ticker_is_judged_on_its_own_newest_session` (LAG two sessions behind with +17 % on its newest bar → dropped by name, not stale; CUR with +17 % on an older bar → kept) | `agents/provider/tests/test_newest_session_guard.py` | PASS (red before the fix) | `PROV-OUT-09` |

**Tests added beyond the plan:**

- `test_a_real_history_day_never_drops_a_buy_from_its_barrier_history` — the measured defect on the barrier path: 14 buys × 760 sessions, TXN +16.76 % / COP +12.82 % on session 100 → both keep 760 bars, `dropped` empty (`PROV-OUT-08`, `PROV-OUT-09`; red before the fix).
- `test_a_session_of_one_move_abstains` (`PROV-OUT-09`).
- `test_a_session_of_65_names_or_fewer_cannot_pass_8_sigma` — the √(n−1) ceiling: +500 % passes among 65 names, dropped among 66 (`PROV-OUT-09`, DRIFT-090; red before the fix).
- `test_every_designed_refusal_is_a_warning` ×3 (failed history, short history, fit outside EXP-018) and `test_every_missing_or_broken_input_is_an_error` ×4 (no ref, ticker not requested, malformed barriers, optimiser raised), each also asserting the incident count (`FORE-FAIL-04`, `FORE-IN-07`).
- **Three existing tests rewritten, for the right reason** (each asserted the whole-window pool): `test_provider_agent.py::test_integrity_anomaly_is_reported_without_crashing` (a lone ticker made anomalous by its *own* history; now two names on one session at 0.5σ, both excluded, `used_fallback` True — same point); `test_barrier_history_failures.py::test_a_dropped_ticker_carries_its_named_reason` (TSLA's +60 % was on history day 400; now on its newest bar with four names on that session and the guard at 1.5σ, since four names cap z at √3); `orchestration/tests/test_trading_observatory.py::test_anomalous_ticker_is_excluded_and_shown_not_degraded` (three identical moves on the newest session instead of three AAPL days). The scanner's `missing_history` count trap did not trigger: no scanner test depended on the guard.

---

## Closeout — evidence

**Status:** MERGED 2026-09-29 — `7e157697` on `main`, 0.119.02, tag `v0.119.02`; GATE PROVEN for `9391b12b`; F1 passed on Neon; DEPLOYED `s243` (image-only retag, 2026-09-29 16:34 AEST); F2 passed 2026-10-02 (four runs since the deploy)

**Tree the proofs ran in (and `.env` present?):** the claude.ai cloud container, `/home/user/trading-agents` on branch `claude/zealous-bell-91iycb` (the session forced this name instead of `sprint-243-a-real-day-in-history-never-drops-a-name`), cut from `main` `0bb2292a`. **No `.env`**; `uv run --frozen` against the existing `uv.lock`; no network in any test.

**Result:** the extreme-move guard judges each ticker's newest bar only, against that session's pooled cross-section, on both the daily ingest and the barrier fetch (one change in `validate_bars`); a real extreme day earlier in the window no longer drops a name (B1, B3, the TXN/COP barrier case). An extreme newest bar is still excluded by name (B2). `forecast_barrier` records a designed refusal at `warning` (not an incident) and a missing or broken input at `error` (B4, B5). Unit-proven only; F1/F2 are the planner's.

**Files changed:** `agents/provider/domain/integrity.py`; `agents/forecaster/barrier_forecast.py`; new `agents/forecaster/barrier_refusal.py`; new tests `agents/provider/tests/test_newest_session_guard.py`, `agents/provider/tests/guard_fixture.py`, `agents/forecaster/tests/test_barrier_refusal_severity.py`; rewritten tests `agents/provider/tests/test_provider_agent.py`, `agents/provider/tests/test_barrier_history_failures.py`, `orchestration/tests/test_trading_observatory.py`; laws `agents/provider/laws/laws.md` + `test-plan.md` (v1.6), `agents/forecaster/laws/laws.md` + `test-plan.md` (v1.8), `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md` (DRIFT-088, -089, -090); `docs/design-log.md` (DL-247); `docs/research/quant-methods/quant-methods.md` (the guard's row); this spec, `docs/sprints/README.md`, `docs/sprints/INDEX.md`. **Not touched:** `agents/provider/barrier_history.py`, `contracts/`, `kernel/`, settings, S241's settlement void rule, `pyproject.toml`, `uv.lock`.

**Design decisions:** [DL-247](../design-log.md). D1 — each ticker's own last valid bar, judged against every ticker's bar on that same session (a lagging ticker is judged on its own session; staleness stays its own flag); rejected: judging only the batch's last date (a lagging ticker's newest bar goes unjudged), and pooling every ticker's last bar whatever its date (mixes sessions). D2 — the same population mean/σ on the narrower pool, <2 moves or zero spread abstains; rejected: a leave-one-out σ (lifts the √(n−1) ceiling but changes DRIFT-014's formula and sharpens the quiet-day trap with nothing measured), and a per-ticker vol model (the spec's out-of-scope alternative). D3 — designed (`warning`): provider dropped, **including a failed history** (the provider records its own `error` Fault for every failed fetch), short history, a fit outside EXP-018's rule; missing/broken (`error`): no named history, ticker not held, malformed barriers, optimiser exception, absent `arch`, conflicting rerun. One exception type carries its severity so `error_type` does not move; rejected: a `severity` argument on `kernel.errors.fault_boundary` (a kernel change for one caller), a second exception class (renames `error_type`), `info` (S213's `RegimeVixShortfall` precedent is `warning`). Severity readers checked: only `kernel/fault_incidents.py` decides by severity, and the brief, supervisor health, `surfaces/queries/faults.py`, the dashboard's incidents answer and MCP all read it; `kernel/fault_graph.py` still writes the `warning` as a `Fault` node and Prometheus still counts it.

**Proof — the red run first:**

```text
# provider, before the integrity.py change (the ceiling test then read 64/65 and was named
# ..._fewer_than_65_names_cannot_reach_8_sigma; corrected to 65/66 after the fix showed a
# strict ">" needs n > 65 — plant 1 below is its red run under the corrected name)
PASSED agents/provider/tests/test_newest_session_guard.py::test_a_bad_newest_bar_is_still_dropped_by_name
PASSED agents/provider/tests/test_newest_session_guard.py::test_a_session_of_one_move_abstains
FAILED agents/provider/tests/test_newest_session_guard.py::test_a_real_old_extreme_day_keeps_the_name
FAILED agents/provider/tests/test_newest_session_guard.py::test_the_daily_ingest_keeps_a_name_with_a_real_crash_mid_window
FAILED agents/provider/tests/test_newest_session_guard.py::test_a_real_history_day_never_drops_a_buy_from_its_barrier_history
FAILED agents/provider/tests/test_newest_session_guard.py::test_a_lagging_ticker_is_judged_on_its_own_newest_session
FAILED agents/provider/tests/test_newest_session_guard.py::test_a_session_of_fewer_than_65_names_cannot_reach_8_sigma
5 failed, 2 passed in 2.90s
#   B1: assert 'TXN' in {'N000', 'N001', ...}
#   B3: assert ('CHTR',) == ()
#   TXN/COP: assert {'TXN': 'extr...y_move_sigma'} == {}   (COP and TXN both dropped)

# forecaster, before the barrier_refusal.py change
FAILED ...::test_a_ticker_the_provider_dropped_is_a_warning_not_an_incident   assert ('error', 1) == ('warning', 0)
FAILED ...::test_every_designed_refusal_is_a_warning[failed-history]
FAILED ...::test_every_designed_refusal_is_a_warning[short-history]
FAILED ...::test_every_designed_refusal_is_a_warning[fit-outside-exp018]
4 failed, 5 passed in 0.77s
```

**Proof — the green run:**

```text
PASSED agents/provider/tests/test_newest_session_guard.py::test_a_real_old_extreme_day_keeps_the_name
PASSED agents/provider/tests/test_newest_session_guard.py::test_a_bad_newest_bar_is_still_dropped_by_name
PASSED agents/provider/tests/test_newest_session_guard.py::test_the_daily_ingest_keeps_a_name_with_a_real_crash_mid_window
PASSED agents/provider/tests/test_newest_session_guard.py::test_a_real_history_day_never_drops_a_buy_from_its_barrier_history
PASSED agents/provider/tests/test_newest_session_guard.py::test_a_lagging_ticker_is_judged_on_its_own_newest_session
PASSED agents/provider/tests/test_newest_session_guard.py::test_a_session_of_one_move_abstains
PASSED agents/provider/tests/test_newest_session_guard.py::test_a_session_of_65_names_or_fewer_cannot_pass_8_sigma
PASSED agents/forecaster/tests/test_barrier_refusal_severity.py::test_a_ticker_the_provider_dropped_is_a_warning_not_an_incident
PASSED agents/forecaster/tests/test_barrier_refusal_severity.py::test_no_barrier_history_is_an_error_and_an_incident
PASSED agents/forecaster/tests/test_barrier_refusal_severity.py::test_every_designed_refusal_is_a_warning[failed-history]
PASSED agents/forecaster/tests/test_barrier_refusal_severity.py::test_every_designed_refusal_is_a_warning[short-history]
PASSED agents/forecaster/tests/test_barrier_refusal_severity.py::test_every_designed_refusal_is_a_warning[fit-outside-exp018]
PASSED agents/forecaster/tests/test_barrier_refusal_severity.py::test_every_missing_or_broken_input_is_an_error[no-ref]
PASSED agents/forecaster/tests/test_barrier_refusal_severity.py::test_every_missing_or_broken_input_is_an_error[ticker-not-requested]
PASSED agents/forecaster/tests/test_barrier_refusal_severity.py::test_every_missing_or_broken_input_is_an_error[malformed-barriers]
PASSED agents/forecaster/tests/test_barrier_refusal_severity.py::test_every_missing_or_broken_input_is_an_error[optimiser-raised]
16 passed in 2.58s
```

**Guards planted:** each planted, run, restored (`cmp` against a pre-plant copy: identical).

1. *Whole-window guard again* (`_anomalous_tickers` pools every session and judges every bar) → **5 failed, 5 passed**: `test_a_real_old_extreme_day_keeps_the_name`, `test_the_daily_ingest_keeps_a_name_with_a_real_crash_mid_window`, `test_a_real_history_day_never_drops_a_buy_from_its_barrier_history`, `test_a_lagging_ticker_is_judged_on_its_own_newest_session`, `test_a_session_of_65_names_or_fewer_cannot_pass_8_sigma`. Restored.
2. *Guard removed* (`anomalous = set()` in `validate_bars`) → **6 failed, 15 passed**: `test_a_bad_newest_bar_is_still_dropped_by_name`, `test_a_lagging_ticker_is_judged_on_its_own_newest_session`, `test_a_session_of_65_names_or_fewer_cannot_pass_8_sigma`, `test_barrier_history_failures.py::test_a_dropped_ticker_carries_its_named_reason`, `test_provider_agent.py::test_integrity_anomaly_is_reported_without_crashing`, `test_domain.py::test_integrity_excludes_anomalous_ticker_keeps_clean_remainder`. Restored.
3. *Designed refusal back at `error`* (`DESIGNED = "error"`) → **4 failed, 5 passed**: B4 and the three `test_every_designed_refusal_is_a_warning` cases, each `assert ('error', 1) == ('warning', 0)`. Restored.
4. *Missing input at `warning`* (no-history refusal raised with `severity=DESIGNED`) → **2 failed, 7 passed**: B5 and `test_every_missing_or_broken_input_is_an_error[no-ref]`, each `assert ('warning', 0) == ('error', 1)`. Restored.

**Module line counts:** `agents/provider/domain/integrity.py` 138 (was 124); `agents/forecaster/barrier_forecast.py` 160 (was 180; the refusal classification moved out); `agents/forecaster/barrier_refusal.py` 83 (new); `agents/provider/barrier_history.py` 191 (untouched); tests: `test_newest_session_guard.py` 157, `guard_fixture.py` 67, `test_barrier_refusal_severity.py` 125, `test_barrier_history_failures.py` 118, `test_provider_agent.py` 180, `orchestration/tests/test_trading_observatory.py` 159. All < 200; the four at 150+ are warnings, as the gate prints for many existing files.

**`make ci`:** `make ci > scratchpad/ci.txt 2>&1` in the container → **exit 0**, all 15 steps. pytest **3,648 passed, 8 skipped**; coverage **100.00 %** (19,557 statements, 4,182 branches, 0 missed); dependency audit "No unaccepted vulnerabilities; 1 accepted advisory re-checked"; detect-secrets **Passed** (tracked) and **Passed** (4 untracked new files). The two earlier runs failed on my own code (a ruff E501, then two mypy errors in the new tests), fixed before the green run. Windows `make ci` not run (owed).

**`uv.lock`:** untouched, and `pyproject.toml`'s version too (the PATCH is pinned at merge). Owed: `uv lock` with the bump.

**`make gate-ran`:** owed to the planner.

**Not met / verified failing:**

- **B2 and B5 were not red before the fix**; they cannot be (the old code already did what they assert). Each is shown red by a plant instead (2 and 4).
- **DRIFT-090 is not fixed:** on the barrier fetch (~14 names) the guard cannot fire at 8σ. Built as specified; decision owed.
- Not done by design (the planner's): `uv lock`, Windows `make ci`, `make gate-ran`, F1, the retag, F2, acking the two Faults.

---

## Return notes

- **Scope held.** No tunable, label, property, edge, env key or contract; the guard not removed and `max_daily_move_sigma` not raised; S241's void rule untouched; `barrier_history.py` untouched (its drop reason stays true). Two small moves beyond the file list, both docs: `docs/research/quant-methods/quant-methods.md`'s guard row (it still said "tripped = the batch is degraded", stale since DRIFT-014) and `docs/sprints/INDEX.md`'s row. The branch is `claude/zealous-bell-91iycb`, forced by the session.
- **What I disagreed with after reading the laws, and the one thing the spec missed.** The PARAM row was the guard's *only* statement, so the scope needed a clause (`PROV-OUT-09`), not a PARAM edit. And the spec's premise that both paths inherit a working guard is half true: a population z over *n* moves can't exceed √(n−1), so at 8σ the guard fires only on a session of **66 or more** names. The ingest (~99) is fine; **the barrier fetch (~14 buys) has a guard that can never fire**. It is still covered upstream (same newest session as the ingest, and a name the ingest drops never becomes a buy), but that is an argument, not a clause. DRIFT-090 carries the forced decision (accept and say so in `PROV-OUT-08`; a leave-one-out σ; or reuse the run's `MarketData` verdict). I also classed a **failed history** as designed (`warning`), which the handover's list didn't name explicitly: the provider always records its own `error` for the failed fetch, so the outage is still one open incident, not zero and not two. If the planner prefers the forecaster's echo to stay loud, it's one `severity=` argument in `barrier_refusal.read_history`. Noted, not filed: conventions §1's prefix table says `FCST`, the forecaster book says `FORE`. DRIFT-084 (bar adjustment, "at the next provider amendment") was not in this amendment's list and stays OPEN.
- **Newest-session false-positive risk, as I see it.** (1) A *real* single-name shock on the newest session is still dropped for that one run: CHTR's −22.7 % among ~98 names moving ±1 % is z ≈ 9.6, so on 2026-04-24's own run it would still have been excluded; the next run it is history and returns. That is the intended trade (a same-day bad print and a same-day real crash look identical), but the operator sees it only in `anomalous_tickers`. (2) As the spec's trap says, one session's σ is smaller than three years' on a quiet day, so a moderate single-name move clears 8σ more easily than before; conversely a market-wide day (2025-04-09) widens σ and protects everyone. With ~99 names the ceiling is ≈ 9.9σ, so 8σ sits close to the most extreme z the pool can produce; F1 (every live `MarketData`'s newest session re-judged) is the measurement that should set whether 8 is right. (3) On the barrier path, false positives are impossible and so are true positives (DRIFT-090).
- **Owed to the planner:** `uv lock` (with the PATCH bump at merge), Windows `make ci`, `make gate-ran` from the worktree at this branch's `HEAD` (check the printed SHA), **F1** on Neon, merge, the image-only **retag** (rollback `s242`), **F2** on the next scheduled run (CHTR scanned; no barrier drop for a history day; the brief's incident count unchanged by a designed refusal), and **ack today's two TXN/COP Faults**.

---

## Planner verification (2026-09-29)

**Tree:** worktree `trading-agents-s243` on `sprint-243-a-real-day-in-history-never-drops-a-name`, cut from
the cloud branch's `5d609810`; F1 ran with the main checkout's `.env`.

- **Review.** Diff read in full. The one flagged call (a failed history is a `warning`) was checked
  against the code: the only path to a failed `BarrierHistory` is `fault_boundary` in
  `agents/provider/agent.py` `_get_market_data` or in `barrier_history.py`, each of which records the
  provider's own `error` Fault, so the forecaster's `error` counted one outage twice. **Accepted.**
- **DRIFT-090 decided before merge** ([DL-247](../design-log.md) D4): accepted. The barrier fetch
  leans on the daily ingest's guard (same session, same feed, ~99 names; a name the ingest drops never
  becomes a buy); `PROV-OUT-08` says so. Commit `9391b12b`.
- **PATCH bump** `e735aad6`: 0.119.01 → 0.119.02; `uv lock` changed the package version line only.
- **Windows `make ci`** exit 0 on `e735aad6` and again on `9391b12b`: **3,648 passed, 8 skipped,
  100.00 %**, audit and detect-secrets passed.
- **`make gate-ran`** from the worktree: `GATE PROVEN for 9391b12b…`
  (CI, CodeQL, Security Findings, attempt 1); the printed SHA equals `HEAD`. The branch's open
  code-scanning alerts equal `main`'s (127 = 127, none branch-only, none at `error`).
- **F1 on Neon (read-only).** All **78** `MarketData` nodes, each newest session re-judged by the new
  `_anomalous_tickers`: every newest session held **98–101** names (above the 66 the guard needs);
  **0** names dropped among the stored survivors; the largest newest-session move was CRM +8.85 %
  (z 5.54, 2026-08-27). The 41 runs that had excluded CHTR (its bars are not stored) were re-judged
  with CHTR's own SIP raw bar for each run's newest session added back (32 sessions, 32 bars found):
  **CHTR dropped on 0 of 41**, its largest z 5.13 (2026-09-09). So on live data 8σ on one session
  drops nothing, and CHTR returns.
- **Merge.** Not a fast-forward (the cloud branch was cut before `61a93e86`, a one-line `STATE.md`
  commit, green on `main`); merge commit `7e157697` differs from the gated tree by that line only.

**Deployed** `s243` 2026-09-29 (image-only retag, operator: *"retag"*; 16 / 16 apps + `dispatcher-cron`, `DeployRecord` recorded; rollback `s242`). **Owed:** **F2** on the next scheduled run
(CHTR scanned; no barrier drop for a history day; the brief's incident count unchanged by a designed
refusal) and ack the two TXN / COP Faults from `sched-2026-09-28`.

**F2 passed, 2026-10-02** ([functionality-checks](../laws/functionality-checks.md)). On all four runs since the deploy (`sched-2026-09-29`, `-09-30`, `-10-01` and the test run `verify-2026-10-01-s248-a`) CHTR is in the provider's tickers and the scanner's filter trace; the three `BarrierHistory` nodes are `ok` with nothing dropped, for 9 forecasts; 0 Faults since the deploy. Not exercised: TXN and COP were not among the buys, and no designed refusal occurred. The two 09-28 Faults needed no ack: incidents are scoped to the latest run day, and `sweep_fault_incidents.py --dry-run` reads 0 live.
