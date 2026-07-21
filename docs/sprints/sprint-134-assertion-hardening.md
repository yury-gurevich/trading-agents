<!-- Agent: planning | Role: sprint handover -->
# Sprint 134 — Assertion hardening: kill the decision-logic + money-parser mutants (backlog row K)

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-134-assertion-hardening`
**Status:** ready for handover (packaged 2026-07-21)
**Effort:** M
**Sequence:** executes **before S133** (operator directive 2026-07-21) — fixes-first, and this
touches real-money decision code; S133 (Service Bus SAS, lower severity) follows it.

---

## Why this sprint

S132 ran mutmut and killed 94 mutants, but parked ~1,355 survivors. Triage of *where they
sit* (S132 CSV, done at review) shows the parking conflated three different things — and a
real, cheap, high-value subset was wrongly deferred as "rainy day." This sprint acts on that
subset: the survivors in **code that decides trades and parses money**, where a weak
assertion is a genuine risk. A report you don't act on is waste; this is the acting.

Grounded triage of the S132 survivors (`docs/reports/sprint-132-mutation-testing/actionable-mutants.csv`):

| Where | ~Count | This sprint |
| --- | ---: | --- |
| Alpaca **pure helpers** — `_order_body`, `_fill_from_order`, `_price_of` (lines 126–185) | ~50 | **KILL** — cheap, deterministic, money-parsing |
| Analyst scoring / PM gates / confidence floor (decision boundaries) | ~84 | **KILL** — gates every trade |
| Alpaca `# pragma: no cover` **HTTPS transport** — `cancel`/`_request`/`_list_orders`/`_submit_or_get` (lines 76–108) | ~91 | **EXCLUDE** — verified by live DEP-BROKER + paper runs, not unit-killable without mocking the mock; justify in writing |
| render-context / audit / log-string mutants | remainder | **EXCLUDE** — killing over-specifies tests (brittle wording assertions); justify in writing |

Target: kill the ~130 worth-killing survivors, prove the count drops on a re-run, and record
the two exclusion classes with their justification so the "not acted on" set is a *decision*,
not an oversight.

## What already exists (read before estimating)

- **S132 tooling is in place**: `mutmut>=3.6.0` in the dev group, `[tool.mutmut]` config
  scoped to the decision engines, the `README.md` + `actionable-mutants.csv` inventory. Re-use
  the exact same scope + command (README "Commands" section) so before/after counts compare.
- **mutmut runs on WSL Ubuntu, not native Windows** (S132 note) — the coder needs that path.
- **Target test files already exist**: `agents/execution/tests/test_alpaca_broker.py`,
  `agents/analyst/tests/test_analyst_domain.py`,
  `agents/portfolio_manager/tests/test_portfolio_manager_audit.py` + siblings. Add assertions
  there; do not create parallel files.
- **The pure helpers are genuinely pure** (`agents/execution/alpaca.py` lines 126–189:
  `_order_body`, `_fill_from_order`, `_status_of`, `_side_of`, `_price_of`) — deterministic
  inputs, no I/O; killing their mutants is a few assertion lines each.
- **The `# pragma: no cover - real HTTPS` methods are a deliberate boundary** — do NOT remove
  the pragma or add HTTP-mock tests just to raise a mutation number (decision 2).

## Decisions taken at packaging (LAW-06)

1. **Kill only the two worth-killing buckets** (money-parsers + decision-logic gates). Each
   new/strengthened assertion targets a specific survivor and cites its mutant id in the test
   docstring (S132 convention). *Ruled out:* chasing 100 % kill-rate (equivalent + over-
   specified mutants make the suite worse).
2. **The two exclusion classes are recorded, not silently skipped.** The `pragma`-HTTPS
   transport (verified-by-live-check) and the string/render/audit mutants (over-specification)
   each get a one-paragraph written justification in the sprint report. *Ruled out:* relabeling
   them to inflate the number, or deleting the pragma to force coverage.
3. **A survivor that turns out to be a real bug is fixed** (not just asserted-around) with a
   regression test + drift-register row — same as S132 decision 3. Mutating a money-parser or
   a gate boundary is exactly where a latent bug would hide.
4. **Re-run proves the delta.** The DoD is the survivor count on the two targeted buckets
   dropping to ~0 on a fresh mutmut run over the same scope — measured, not asserted.

## Kickoff (paste this)

> Execute **Sprint 134 — assertion hardening** exactly as specified in this file
> (`docs/sprints/sprint-134-assertion-hardening.md`). Read first: backlog row K in
> `docs/hardening-backlog.md`; the S132 report + `actionable-mutants.csv` (your work-list);
> `agents/execution/alpaca.py` (pure helpers vs `pragma` transport), the analyst/PM domain
> gates; design-log **DL-48**.
>
> **Contract (DL-48 — enforced):**
>
> - **Start:** `git pull` on `main` — `pyproject.toml` must read **0.71.05** (stop and report
>   if not). Branch `sprint-134-assertion-hardening`. Bump **PATCH → 0.71.06** + `uv lock`
>   (only if uv.lock actually changes — this sprint may add no deps).
> - **Drift rule / Secrets rule / Handback rule:** as prior sprints (fetch+merge+re-gate;
>   no secret in tree/output; closeout + return notes last).
> - Hard gate: `make ci` green (exit code captured), 100 % coverage held, ≤200-line modules,
>   headers. **Do not wire mutmut into `make ci`; do not remove any `# pragma: no cover`.**
>
> **Work items:**
>
> - **A (kill money-parsers):** strengthen `test_alpaca_broker.py` to kill the survivors in
>   `_order_body` / `_fill_from_order` / `_price_of` (assert the exact built body, parsed
>   fill fields, computed price — not just "a value returned"). Each test docstring cites the
>   mutant id.
> - **B (kill decision-logic):** strengthen analyst-scoring / PM-gate / confidence-floor tests
>   to kill the ~84 gate-boundary survivors (assert the boundary: value at, just below, just
>   above the threshold). Cite mutant ids.
> - **C (record exclusions):** in the sprint report, list the `pragma`-HTTPS transport bucket
>   and the string/render/audit bucket as **deliberately not killed**, each with its
>   one-paragraph justification (verified-by-live-check; over-specification).
> - **D (re-run + prove):** re-run the S132 mutmut scope; record before/after survivor counts
>   for the two targeted buckets (target ≈0 remaining in them) and the new overall kill-rate.
>   Commit the refreshed report under `docs/reports/sprint-134-assertion-hardening/`.
> - **E (docs):** backlog row K → Done with the delta; if any real bug was found, a drift row;
>   note the residual (excluded buckets) as a permanent, justified non-target.
> - **Functionality check (LAW-02):** the re-run IS the proof — targeted-bucket survivor count
>   before/after + `make ci` green. Offline; no infra/graph/broker/teardown — state that.
> - **Wrap up:** README/INDEX rows; Closeout + Return notes; push, hand back. **Do not merge.**

## Guardrails

- Scope is the two worth-killing buckets only; do not widen to the whole survivor set.
- Never remove a `# pragma: no cover`, never add a test that asserts a mocked call's own
  arguments back to itself just to raise the number (that tests the mock, not the code).
- Do not over-specify: no assertions on exact log/explanation wording (that's the excluded
  string bucket, excluded for a reason).
- A real bug found → fix + regression test + drift row, never assert-around it.

## Definition of done

1. The money-parser and decision-logic survivor buckets drop to ≈0 on a fresh mutmut re-run
   over the S132 scope (counts recorded before/after).
2. Every new/strengthened test cites the mutant it kills; the two excluded buckets are
   recorded with written justification.
3. Backlog row K → Done; any behavioral bug found is fixed with a drift row.
4. `make ci` green at 100 % (exit code captured); no `pragma` removed; closeout + return
   notes filled.

## Closeout (coding agent fills; planning agent verifies before merge)

```text
CLOSEOUT — Sprint 134
Branch / merge commit:   <branch> / <merge sha or "not merged by instruction">
make ci:                 MAKE_CI_EXIT_CODE=<n>; <passed/skipped>; coverage <pct>
Functionality check:     <money-parser + decision-logic survivor counts before/after;
                          overall kill-rate; excluded buckets recorded>
Version:                 0.71.05 → 0.71.06 (PATCH); uv.lock refreshed (if changed)
Backlog row K:           <Done + report link>; behavioral bugs found: <n + drift rows>
Drift rule:              <origin/main moved? merged? re-gated?>
Deviations from spec:    <none, or the honest list>
```

## Return notes (coding agent appends at handback — mandatory)

<!-- return notes go below this line -->
