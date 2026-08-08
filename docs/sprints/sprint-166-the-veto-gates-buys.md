<!-- Agent: execution | Role: sprint spec + closeout for DL-98 -->
# S166 — the veto gates buys, never exits

**Closes:** [DL-98](../design-log.md) · **Decides:** [ADR-0022](../decisions/0022-the-veto-gates-buys-never-exits.md)
· **Type:** fix · **Version:** 0.89.07 · **Branch:** `sprint-166-the-veto-gates-buys`
· **Deploys:** image-only retag (no pack change)

## Why

The deliberation veto has never blocked an order. That looked like policy; it was a race. Measured
on `check-s166-flat-book` (2026-08-08): `PMRun` 05:35:56 → **18 orders at the broker 05:36:22** →
`DeliberationRun` **05:47:32**, saying *revise* about orders already live. `_drop_vetoed` treated an
absent veto as *execute everything*, so in graph-pull "has not finished yet" and "is not deployed"
were the same thing, and the faster poller won.

Hidden for weeks because the PM approved **zero** orders on every run since 07-31 — no orders, no
race. The deadlock was masking it.

## What shipped

1. **`agents/execution/deliberation_gate.py`** — `deliberation_status` classifies a PMRun as
   `applied` / `not_required` / `waiting` / `proceeded_unvetoed`.
2. **The wait is expressed by not consuming the PMRun.** `find_pending` skips it; the next poll
   retries. No new state; a restart resumes because the window comes from the PMRun's `created_at`.
3. **Exits never wait** — a sell-only set returns `not_required` immediately (S147 / ADR-0017).
4. **Bounded and reversible** — `deliberation_grace_seconds`, default 900, range 0–3600; `0`
   restores the previous behaviour exactly.
5. **Fail-open stays, silence does not** — `ExecutionRun.deliberation_status` is a queryable fact
   and `proceeded_unvetoed` raises a `DeliberationGraceExpired` fault.

## Success factors

- [x] A buy-carrying PMRun inside the window is held, not submitted.
- [x] A sell-only PMRun is never delayed.
- [x] The wait is bounded and then proceeds loudly.
- [x] Both defects observed failing on planted violations first (DL-70).
- [x] `make ci` green, measured unpiped to a file.
- [x] Remote `make gate-ran` green.

## Closeout — evidence

**Local gate.** `make ci` **exit 0**, `2195 passed / 6 skipped / 100.00 % coverage`, redirected to a
file and read back.

**Planted defects (DL-70).**

| Planted | Result |
| --- | --- |
| Never wait — the pre-DL-98 race restored | **3 failed** / 192 passed |
| Exits made to wait too — the S147 violation | **2 failed** / 181 passed, one a broker-stops test |

🚨 **The in-process cascade needed an explicit opt-out, and that was the informative part.**
`local_pipeline` runs deliberation only when an LLM is configured, so with none the harness waited
for a veto that never arrives — **18 tests failed** until it was made explicit. Harness-only:
production runs the deliberator as three container apps polling independently and always deployed,
which is why the race was real rather than theoretical.

**Module size.** `poll.py` hit **242** against the 200-line hard block mid-change and was split, not
trimmed — the gate's helpers moved to their natural home. Now `poll.py` **190**, `deliberation_gate.py`
**159**.

**No pack coupling.** `ExecutionRun` is not one of the five property-enforced labels, so
`deliberation_status` cannot cause the S148 fail-closed stall; a deploy is an image-only retag.

**Remote gate.** `make gate-ran` **exit 0** — GATE PROVEN for `1c014af4800567780964ae56a43a09ca9c6efc40`, **CI: success** and **Security Findings: success**. Merged as `afc5088`, tagged `v0.89.07`.

**Not proven.** No run has executed this code. The guard is the suite plus two planted defects. The
first real test is the next run in which the PM approves a buy.
