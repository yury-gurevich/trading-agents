<!-- Agent: planning | Role: sprint handover -->
# Sprint 114 — Complete the deliberation evidence: explicit gate outcomes + PM risk gates (DL-41)

**Phase:** deliberation quality — critical path (DL-41, operator priority 2026-07-05)
**Branch:** `sprint-114-complete-deliberation-evidence`
**Status:** shipped — implemented on `sprint-114-complete-deliberation-evidence`; awaiting operator review/merge
**Effort:** M

---

## Codex kickoff (paste this)

> Execute **Sprint 114 — Complete the deliberation evidence** exactly as specified in this file
> (`docs/sprints/sprint-114-complete-deliberation-evidence.md`). It is a complete, self-contained
> handover. Read `docs/design-log.md` **DL-41** first — it is the rationale.
>
> - **Start:** from `main` (`git pull`), `git checkout -b sprint-114-complete-deliberation-evidence`
>   (delete any stale local branch of that name first). Read every file under *Execution notes → read
>   first* before writing anything.
> - **Why this matters:** the challenger-veto (`orchestration/veto.py` → `execution/poll.py` drops
>   vetoed tickers) is the **last gate before real orders**. Money is spent on its output. A debate over
>   incomplete evidence produces a lower-quality veto — so the evidence handed to the debate must be
>   **complete: every enforced gate present, with its value AND its explicit pass/fail outcome.**
> - **The gap (proven, not hypothetical):** `orchestration/veto_context.py` already renders analyst
>   `confidence` + regime `base_min_confidence` + scanner/market lineage, but (1) gate **outcomes are
>   implicit** — it prints the values, never states "0.62 ≥ 0.30 → PASSED"; and (2) the **PM risk gates
>   are absent entirely** — `max_sector_pct` concentration, the position-sizing basis, and
>   existing-position context are computed in the PM but never rendered. Fix both.
> - **Hard gate every commit:** `make ci` green — 9 steps, **100 % coverage**, modules **≤ 200 lines**
>   (`veto_context.py` is at **195/200** — you MUST split before adding), coding-agent `Agent:`/`Role:`
>   headers. Bump `pyproject.toml` **0.55.01 → 0.56.00** (feat → MINOR zeroes the patch) + `uv lock`.
> - **Contract change is additive-only:** the PM emits its gate outcomes as a new additive field on the
>   PM output type (see *Build* step 1); bump the portfolio_manager contract MINOR. No required-field
>   change on any existing type, no consumer breaks. Update boundary/contract tests that snapshot the PM
>   shape.
> - **Boundaries:** `veto_context*.py` stays `Agent: orchestration`, reads only the injected
>   `GraphStore` (no live I/O). The PM gate-outcome capture lives in the PM domain (pure). **No agent
>   imports another agent**; `import-linter` enforces.
> - **Fail-safe rendering:** a missing lineage node or absent gate report degrades gracefully to a
>   stated "gate report unavailable" line — never a crash, never a silent omission. The veto is
>   **fail-open** (an error upholds); do not change that.
> - **Real-environment check** (sprint-close rule): drive a real PM decision through the veto stage on
>   the live graph and assert the rendered context contains **every enforced gate with an explicit
>   outcome** (confidence-floor, sector-concentration, sizing, stop-vs-regime/ATR). Record the row in
>   `docs/laws/functionality-checks.md`; tear down test nodes; **no data files committed.**
> - **Do NOT merge or push to `main`** — commit on the branch only, then stop for operator review.
> - Read *Session gotchas* before coding. When done, append a **Closeout evidence** block to this file.

---

## What this sprint is

The deliberation challenger-veto debates each PM-approved order and may subtract it before execution.
Its verdict is only as good as the evidence it argues over. Today that evidence is **incomplete in two
specific ways**, and this sprint closes both so the debate reasons over a self-contained, self-evident
record — no inference of un-stated checks, no missing risk gate.

**This is not a prompt/LLM change.** It is deterministic evidence assembly (DL-41). DSPi/prompt
optimisation of the *reasoning* is a separate later layer (DL-42) that depends on this landing first —
compiling a prompt over incomplete evidence just makes the wrong argument consistently.

**Out of scope (flag, don't build):** any change to the debate prompts, the verdict logic, DSPy, or the
factor-mining loop (S113). If a fix tempts you toward `kernel/deliberation.py` role prompts, stop — that
is DL-42.

---

## Execution notes

### Read first (the seams)

- `docs/design-log.md` **DL-41** — the spec and rationale (and DL-42 for what this is *not*).
- `orchestration/veto_context.py` (195 lines) — the evidence renderer. `build_veto_context(...)` walks
  PM→analyst→scanner→market→regime and renders lines. Note the existing `Regime:` line already prints
  `base_min_confidence`, and `_recommendation_line` prints `confidence`. **The values are here; the
  outcomes and the PM risk gates are not.**
- `orchestration/veto.py` — how the context is used: `Proposition(decision=..., context=build_veto_context(...))`.
- `agents/portfolio_manager/domain/concentration.py` — the `max_sector_pct` gate
  (`deployed + cost > max_sector_pct * portfolio_value`) and `max_names_per_sector`. This is the
  computed-but-unrendered gate.
- `agents/portfolio_manager/domain/risk.py` — the risk-gate composition (sizing, sector). Find where the
  per-order gate decisions are made — that is where you capture outcomes.
- `contracts/portfolio_manager.py` — `OrderIntent`, `OrderIntentSet` (the type to extend additively).
- `agents/analyst/domain/recommend.py:45` — the `confidence < base_min_confidence` rejection (the
  confidence-floor gate; its inputs are already in context — make its **outcome** explicit).

### Build

1. **PM emits its gate outcomes (additive contract).** Add a small frozen type — e.g.
   `GateOutcome(_Frozen)`: `name: str`, `value: float`, `threshold: float`, `passed: bool`,
   `detail: str` — and an additive field carrying a tuple of them on the PM output
   (`OrderIntent.gate_report: tuple[GateOutcome, ...] = ()` per order, or an
   `OrderIntentSet`-level map keyed by ticker — pick whichever matches how `risk.py` already structures
   per-order decisions; confirm against the code). Populate it in the PM risk domain where each gate is
   evaluated (sector-concentration vs `max_sector_pct`, `max_names_per_sector`, position sizing / max
   position). **Additive only**, default empty; bump the portfolio_manager contract MINOR.
2. **Render outcomes explicitly in the veto context.** Split `veto_context.py` first (it is at 195/200)
   — e.g. move the PM/gate + regime rendering into `orchestration/veto_context_pm.py` and keep the
   walker in `veto_context.py`. Then:
   - Render the PM `gate_report` for the order: each gate as `name=… value=… threshold=… → PASSED/FAILED (detail)`.
   - Make the **confidence-floor** outcome explicit: `confidence=0.62 vs base_min_confidence=0.30 → PASSED`.
   - Make the **stop/target vs regime + volatility** relationship explicit (the recurring cross-model
     challenger point): e.g. `stop_pct=-3.0% vs ATR%/base_stop_loss_pct → …`. Use the OHLCV/regime data
     already in context; if ATR is not available, state that plainly rather than omit.
3. **Completeness guard (test).** A test that, for a representative PM decision with populated gates,
   asserts every enforced gate name appears in the rendered context **with an outcome token**
   (`PASSED`/`FAILED`). This is the regression fence: evidence cannot silently drop a gate again.

### Contract / boundary

- Additive PM field only; contract MINOR bump; no consumer break.
- `veto_context.py` + `veto_context_pm.py`: `Agent: orchestration`, read-only over the injected
  `GraphStore`; import only `contracts` + `kernel`. No agent→agent import.
- Analyst/PM domains stay pure.

---

## Definition of done (verifiable success factors)

1. `make ci` green — 9 steps, **100 % coverage**, all modules ≤ 200 lines (`veto_context.py` split),
   headers present. Version `0.56.00`, `uv.lock` staged.
2. PM emits a `gate_report` (additive) covering the enforced PM risk gates; contract MINOR bump;
   boundary/contract tests updated and green.
3. `build_veto_context` renders **every enforced gate as value + explicit PASSED/FAILED outcome** —
   confidence-floor, sector-concentration (`max_sector_pct`), `max_names_per_sector`, sizing, and the
   stop-vs-regime/volatility relationship — degrading gracefully when a source is absent.
4. Completeness test present and green (every enforced gate → outcome token in the rendered context).
5. **Real-environment functionality check passed and recorded** in `docs/laws/functionality-checks.md`;
   test nodes torn down; no data files committed.
6. Committed on the branch only. **Not** merged or pushed to `main`.

### Real-environment functionality check (sprint-close rule)

- Drive one real PM decision (or a faithful seeded PMRun with populated gate outcomes) through the veto
  stage on the live graph (Aura). Capture the rendered `Proposition.context` and assert it contains, for
  the order under review, **every enforced gate with an explicit outcome** — including the previously
  missing `max_sector_pct` concentration line. Optionally run one live debate and confirm the challenger
  no longer attacks a phantom missing gate. Tear down every stamped node; record intent · environment ·
  proven result · teardown.

---

## Session gotchas (read before coding)

- **Values ≠ outcomes.** The bug is subtle: the context already prints `confidence` and
  `base_min_confidence`, so it *looks* complete. It is not — the debate must not have to infer the
  comparison. Print the **result**.
- **The PM already computes the gates; it just doesn't publish them.** Do not recompute sector exposure
  in orchestration — that would duplicate PM logic across a boundary. The PM must emit the outcome; the
  renderer only formats it. If the outcome genuinely isn't computed for some gate, that is a real PM
  finding — surface it, don't paper over it.
- **Split before you add.** `veto_context.py` is at 195/200. Adding lines to it first will trip the
  module-size gate. Split, then add.
- **Fail-open is sacred.** The veto upholds on any error (`veto.py` `_review` → `None` → uphold). A
  missing gate report must render "unavailable", never raise — an evidence bug must never block trading.
- **Additive contract only.** No required field on `OrderIntent`/`OrderIntentSet`; default empty so
  every existing producer/consumer and snapshot test keeps working.
- **Stay off the prompts.** `kernel/deliberation.py` role strings are DL-42, not this sprint.

---

## Sequencing note (for the planning agent, on merge)

S114 takes `0.55.01 → 0.56.00`. The **S113 handover doc still says `0.55.01 → 0.56.00`** — after S114
merges, re-point S113 to `0.56.00 → 0.57.00` before handing it to Codex. DL-42 (DSPy-compile the
deliberation roles) sequences after this sprint.

---

## Closeout evidence

- Implemented additive PM gate evidence:
  - `contracts/portfolio_manager.py`: added `GateOutcome` and optional
    `OrderIntent.gate_report`, contract `0.1.0 -> 0.2.0`.
  - `agents/portfolio_manager/domain/gate_report.py` + `concentration.py`/`risk.py`:
    emit explicit sizing, cash/name-count, sector, and reward/risk outcomes without
    changing rejection reasons.
  - `orchestration/veto_context.py` split; `orchestration/veto_context_pm.py` renders
    PM gates, confidence-floor, and stop-vs-regime/ATR as explicit `PASSED`/`FAILED`
    lines, with unavailable evidence stated plainly.
- Documentation updated:
  - `agents/portfolio_manager/laws/laws.md`
  - `agents/portfolio_manager/laws/test-plan.md`
  - `docs/laws/functionality-checks.md`
- Version bumped `0.55.01 -> 0.56.00`; `uv.lock` refreshed.
- `make ci`: green on 2026-07-05 — `1346 passed, 5 skipped`, required coverage
  `100.00%` reached; import-linter kept; module-size hard block kept; pip-audit +
  detect-secrets passed.
- Real-environment check recorded in `docs/laws/functionality-checks.md`:
  Aura `bce05bd6` with `Neo4jGraphStore` asserted; stamped seeded PMRun
  `s114-livecheck-20260705T081256` driven through `orchestration.veto.deliberate_pm_node`
  using a recording fake LLM. Captured context contained explicit outcomes for
  `sizing`, `max_sector_pct`, `max_names_per_sector`, `reward_risk`,
  `confidence_floor`, and `stop_vs_regime_volatility`. Teardown deleted 6 stamped
  nodes and restored Aura to baseline 0 nodes; scratch script deleted.
- Not merged or pushed to `main`.
