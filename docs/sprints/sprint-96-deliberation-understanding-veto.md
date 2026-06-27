# Sprint 96 — Deliberation: define-then-justify + scored understanding, then challenger-veto

**Branch:** `sprint-96-deliberation-understanding-veto`
**Status:** Part A SHIPPED (0.40.00) · Part B mechanism SHIPPED (0.41.00, opt-in, off by default) · **Phase:** Deliberation → runtime (DL-31) · **Effort: L (split A/B)**

> **Part B shipped (mechanism):** `orchestration/veto.py` (opt-in challenger-veto stage between PM and
> execution — debates each approved order, records a `DeliberationRun` with per-order verdicts + the
> vetoed/subtracted set; judge may only subtract); execution honours the veto (`_drop_vetoed`, EXEC-NEV-01);
> `cascade_once(deliberation_llm=...)` adds the stage only when an LLM is injected, so the 1156-test
> deterministic cascade is unchanged; **fail-open** on LLM outage. **Proven live:** with a real LLM
> (gpt-5.5) the veto fired and execution submitted 0. **KEY FINDING — the veto must be grounded before it
> is enabled:** with a thin proposition ("a PM-approved order; review before execution") the LLM revised
> *everything* (blanket block). So Part B stays **off by default**; enabling it for real needs (a) a
> grounded/rich proposition (the order's rationale + the parameter facts from Part A's answer key) and
> (b) verdict semantics (treat `revise` as flag vs `reject` as block). That is the remaining work before
> the veto touches live capital.

> **Part A shipped:** define-then-justify prompts + `kernel/deliberation_understanding.py`
> (`ParameterTruth`/`score_understanding`/`understanding_rate`/`misread_parameters`) +
> `orchestration/packs/trading_parameter_truths.py` (answer key from `llm-interpretation-deltas.md`) +
> `scripts/deliberate.py --score`. **Proven live:** gpt-5.5 gave a fluent UPHOLD on "Buy AMD" yet scored
> 0–33% understanding (vague on `max_daily_move_sigma`/`base_min_confidence` — the predicted Class-1
> deltas). The live run also caught + fixed a scorer false-positive (misread now requires the param be
> cited). 1151 tests, 100%. **Part B (runtime challenger-veto) remains.**

## Goal

Earn justified confidence that the expert-LLM deliberation actually *understands* the parameters it
reasons over, then put it in the live loop **as a veto that can only subtract**. Today the 3-analyst
deliberation (`kernel/deliberation.py`) is real but **offline-only** (called from scripts, not the
cascade), and EXP-001/003 proved the model confidently *misreads* our parameters (it calls
`max_daily_move_sigma` a per-stock vol filter; it is a **pooled cross-sectional** gate). The fix is
*confidence by measurement, not eloquence* (DL-31).

## Scope

### Part A — understanding gate (do first; offline, low risk)

**In:**

- **Define-then-justify prompt.** Edit `DEFENDER_SYSTEM` / `CHALLENGER_SYSTEM` / the judge prompt in
  `kernel/deliberation.py` so each role, for every parameter it invokes, first **states the parameter's
  meaning in THIS system**, then justifies its verdict against those definitions. The transcript now
  carries explicit parameter definitions.
- **Score the definitions against ground truth.** Grade the model's parameter-definitions against the
  answer key `docs/research/quant-methods/llm-interpretation-deltas.md`, reusing
  `kernel/deliberation_eval.py` + the frozen golden. Emit a per-parameter correct/incorrect and an
  aggregate "understanding score".
- **Gate it (DL-24).** A regression in the understanding score trips `scripts/deliberation_gate.py`
  (model/prompt are gated parameters) — a model or prompt change that worsens parameter comprehension
  fails the gate.
- **Answer-key coverage test.** A test asserts every parameter the deliberation can cite has an entry in
  `llm-interpretation-deltas.md`, so the key cannot silently fall behind the code.

**Out (Part A):** no change to the trading path; deliberation stays offline. This part only proves +
gates *understanding*.

### Part B — asymmetric challenger-veto in the loop (follow-on; touches the capital path)

**In:**

- A new orchestration stage (a side branch like the forecaster) that runs defend/challenge/judge on each
  **PM-approved** order intent, **after PM-approve and before execution**.
- The judge may **block** an order (verdict `revise`/`reject` → the order is dropped with a recorded
  reason) but may **never originate or resize** one — the deterministic core stays authoritative (the LLM
  analogue of `FORE-NEV-02`: advise/veto, never gate-up).
- Persist the transcript + verdict as graph nodes (provenance/audit); surface a `[deliberation]` line in
  the observatory (advisory unless it blocked).

**Out (Part B):** no LLM origination or sizing; no free-form parameter changes.

## Decisions (open questions from DL-31, resolved here — confirm before building Part B)

- **Placement:** between PM-approve and execution (PM has already sized/risk-checked; this is the final
  sanity gate before capital is committed).
- **Granularity:** one debate per PM-approved order intent (approved trades are few — 2–5 — so cost is
  bounded).
- **Fail-safe on LLM outage:** **fail-open + loud** — if the deliberation errors/times out, do *not*
  block the trade, but record a fault and an observatory WARN. (An LLM outage must not halt trading;
  it must be visible.) *Confirm: fail-open vs fail-closed.*
- **Veto scope:** **hard-block only** (drop the order). No revise-size-down — that edges toward
  origination.

## Deliverables

- Part A: updated deliberation prompts; understanding scorer + aggregate; gate wired; answer-key coverage
  test; all `make ci` green, 100% coverage.
- Part B: the veto stage + graph nodes + observatory line + tests proving (i) a block drops exactly the
  vetoed order and nothing else, (ii) the judge can never add/resize an order, (iii) fail-open on outage.

## Acceptance

- **Part A:** the deliberation transcript names + defines each parameter it uses; the scorer reports an
  understanding score against `llm-interpretation-deltas.md`; a deliberately-wrong definition (or a model
  swap that regresses comprehension) **trips the gate**.
- **Part B:** on a live/seeded run, a challenger block removes only the vetoed order intent; execution
  proceeds on the rest; the deterministic counts are otherwise unchanged; transcript persisted.
- `make ci` green at every step; GitHub CI green.

## Dependencies

- Builds on the existing firewall: `kernel/deliberation.py`, `kernel/deliberation_eval.py`,
  `scripts/deliberation_gate.py`, the frozen golden, and `docs/research/quant-methods/llm-interpretation-deltas.md`.
- Part B depends on Part A (don't wire an un-graded judge into the capital path).
- Relates to DL-24 (model/prompt are gated parameters), DL-31 (this sprint's source), `FORE-NEV-02`
  (advise/veto-never-gate precedent), and Discussion-topic 3 (test LLM understanding).

## Notes

This is sized **L** and naturally splits: **Part A is the high-value, low-risk first increment** — it
directly answers the operator's confidence question (does the LLM understand?) without touching money.
Ship A, prove understanding is measured + gated, then take Part B (the runtime veto) as its own push.
