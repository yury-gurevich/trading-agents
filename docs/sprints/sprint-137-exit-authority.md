<!-- Agent: planning | Role: sprint handover -->
# Sprint 137 — Exit authority: alpha proposes, risk disposes (ADR-0017)

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-137-exit-authority`
**Status:** SHIPPED 0.76.00 — merged `29a36f4`, fleet `:s141`, functionality check PROVEN
**Effort:** M
**Decisions:** [ADR-0017](../decisions/0017-exit-authority-alpha-proposes-risk-disposes.md)
(closes the open question ADR-0015's amendment surfaced)

---

## Why this sprint

Evidence-based closure (S138/0.74.02) stopped positions stranding, but exposed a conflict: the
monitor decided `close` on HPE/MRVL/CSCO **every run** while the analyst, scoring the same names on
full evidence, returned `hold` — and only the analyst reached the broker, so the monitor re-decided
the same exit forever. ADR-0015's amendment closed on it explicitly: *which decider wins is not
settled — it needs an operator decision.*

The operator decided: **the structure a real trading shop runs.** A desk separates **alpha** (what
to own — thesis) from **risk** (the stop), and does not subordinate risk to alpha on the downside.
The analyst wins discretionary exits; the stop is an unconditional floor it cannot veto.

---

## What shipped (spec)

1. **The analyst is the sole author of discretionary exits.** A held name exits on a degraded
   thesis (`sell if confidence < exit_confidence_floor else hold`); the monitor no longer authors a
   competing decision, so the analyst wins every discretionary disagreement by construction.

2. **A breached stop is forced onto the same rail, regardless of thesis.** When a held name is at or
   through its stop, `recommend.decide(held=True)` short-circuits to a `sell` with
   `exit_trigger="stop"` **before** the confidence check — alpha cannot veto the stop. It rides the
   ADR-0016 unified rail (analyst → PM → execution), not a second close-dispatch path (DL-60). The
   stop arithmetic moved to `contracts/stop_rule.py` (agents never import agents);
   `contracts/positions.open_position_stop_thresholds` does quantity-weighted-avg entry and **raises
   rather than guesses** if lots disagree on `stop_pct`.

3. **The monitor stops deciding; it observes and surfaces.** It keeps broker reconciliation and
   raises a `Fault` when a stop is breached but not yet exited (DL-57 visibility) — no more competing
   CloseDecisions.

4. **`target` and `time` retire** into deferred strategy (ADR-0016's sequenced-later work); the stop
   is the only surviving mechanical rule, because it is risk, not opinion. The dead
   `order_from_close`/`execute_close` path was removed (one rail).

The durable home of the stop stays broker-native (ADR-0015 §3 → **sprint-138**); this sprint's
forced daily-rail stop is the interim, exposed to an overnight gap-down.

---

## Closeout — evidence

- **Files changed:** `contracts/stop_rule.py` (new), `contracts/positions.py`, `contracts/analyst.py`,
  `contracts/monitor.py`, `contracts/execution.py`, `agents/analyst/domain/analyze.py`,
  `agents/analyst/domain/recommend.py`, `agents/analyst/run.py`, `agents/analyst/store.py`,
  `agents/analyst/tests/test_exit_authority.py` (new), `agents/monitor/*` (decide, exit_rules,
  positions, result, run, store, agent; `execution_client.py` deleted), `agents/execution/*` (agent,
  domain/orders), plus PM/reporter/orchestration test updates, `tests/test_stop_rule.py` (new),
  `pyproject.toml`, `uv.lock`, ADR-0017 + INDEX + 0015/0016 cross-links.
- **`make ci`:** 1786 passed / 6 skipped / **100.00% coverage**, verified independently; all four
  remote gate jobs (quality/security/test/gate) green before merge.
- **Deploy:** fleet retagged 14/14 → `:s141` (`29a36f4`), `DeployRecord …:s141:29a36f4` written after
  proving every target on tag.
- **Functionality check PROVEN** (run `sched-2026-07-24`, recorded in
  `docs/laws/functionality-checks.md`): the forced stop fired for the first time —
  `MRVL sell exit_trigger='stop' conf=0.637` **above** the `exit_confidence_floor=0.5` (thesis said
  hold; the stop overrode it), the monitor went silent (`checked=9 closes=0 holds=9`) and raised the
  Fault `"stop breached on MRVL, still held"`, and the sell reached the broker (PM `qty=44`,
  execution `submitted=3 rejected=0`). Fill queued for the open (acceptance `UNPROVEN`), like ABT
  before it.
- **Not done:** broker-native stops (ADR-0015 §3) — deliberately deferred to sprint-138 as the
  durable home of the floor.
