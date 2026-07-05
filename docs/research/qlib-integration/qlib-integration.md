# Research: Microsoft Qlib — Integration Vision

**Status:** Research complete · **Date:** 2026-06-18 · **Author:** Claude (claude-sonnet-4-6)
**Audience:** Product owner, planning agents, coding agents
**Source:** [github.com/microsoft/qlib](https://github.com/microsoft/qlib)

> **Update (2026-06-19) — Python-3.13 constraint resolved for Phase Q1.** `pyqlib` is **not
> installable on this workspace**: it ships wheels only for `cp38…cp312`, and the repo pins
> `requires-python = ">=3.13"` (verified via `uv pip install --dry-run pyqlib` → unsatisfiable).
> **Phase Q1 therefore depends on the standalone `lightgbm` package directly** (resolves clean on
> 3.13), behind the forecaster's model port — no `pyqlib` import. Qlib's `LGBModel` is only a thin
> wrapper over `lightgbm`, so Q1 loses nothing; this is also cleaner than the "vendor qlib source"
> fallback in the risk register. Supersedes the `pip install pyqlib` instruction below **for Q1**.
> Handover: [sprint-58](../sprints/sprint-58-forecaster-lightgbm-shadow.md). Phases Q3/Q4 (qlib's own
> backtest + strategy engines) still hit this wall and must be re-scoped when reached.

---

> **Update (2026-07-04) — workflow-level addendum.** Q1 (S58–S59) and Q2 (S68) shipped. A second
> pass re-examined qlib as a source of **workflows** rather than components; see the
> §"Addendum (2026-07-04)" at the end. It adds phases Q1b (signal evaluation battery — packaged as
> [sprint-110](../../sprints/sprint-110-signal-evaluation-battery.md)) and Q1c (rolling retrain),
> **re-scopes Q3 to a self-built walk-forward harness** (pyqlib still ships no cp313 wheel,
> re-verified 2026-07-04), and adds Q5 (governed factor-mining loop, = Moonshot #3).

---

## TL;DR

Qlib is Microsoft's open-source AI-oriented quantitative investment platform. It contains
production-grade implementations of 25+ ML models, 158–360 engineered alpha factors, a
point-in-time backtesting framework, and portfolio optimizers — all battle-tested on real
markets. None of it conflicts with this project's architecture: every component plugs cleanly
inside a single agent boundary and communicates over the existing typed message bus. Four agents
stand to benefit materially. The rest of qlib's surface area is irrelevant or inferior to what
is already in place.

**Recommended entry point:** wire qlib's `LightGBM` forecasting model inside `forecaster` as a
second shadow signal alongside FinBERT, governed by the P10 predictor-registry gate. Low
risk; immediate signal-quality uplift if it earns its scorecard.

---

## What Qlib Is

Qlib is a Python library (not a framework or service) organized as importable modules:

| Module | What it provides |
| --- | --- |
| `qlib.data` | Point-in-time dataset builder; Alpha158/Alpha360 factor pipelines |
| `qlib.model` | 25+ ML model implementations: LightGBM, XGBoost, LSTM, Transformer, HIST, TRA, etc. |
| `qlib.backtest` | Backtesting engine with fill-simulation and no-lookahead guarantees |
| `qlib.strategy` | Portfolio strategy skeletons (mean-reversion, momentum, signal combination) |
| `qlib.contrib.rl` | RL-based order execution: PPO, OPDS, TWAP optimization |
| `qlib.workflow` | Experiment management (MLflow-style) for model training runs |

Install (the library as a whole): `pip install pyqlib` — **Python 3.8–3.12 only**; there is **no
cp313 wheel**, so it does **not** install on this project's pinned 3.13 (confirmed 2026-06-19; see the
update note above). Components that are thin wrappers over standalone packages (e.g. `LGBModel` over
`lightgbm`) are therefore consumed via those packages directly. License: MIT.

---

## Architectural Fit

This project's one law — **agents never import each other; all communication is via typed
messages** — is fully preserved. Qlib is a **library**, not an agent. It is imported inside
a single agent's `domain/` directory, behind that agent's boundary. The bus, contract
system, and boundary meta-test are untouched.

```text
agents/
  forecaster/domain/   ← qlib.model lives here only
  analyst/domain/      ← qlib.data alpha factors live here only
  portfolio_manager/domain/  ← qlib.strategy optimizer lives here only
  researcher/domain/   ← qlib.backtest lives here only
```

No agent imports another. No qlib symbol crosses an agent boundary. The typed contract
messages remain the only inter-agent interface. The boundary meta-test (`test_boundary_map.py`)
continues to enforce this mechanically.

---

## Integration Opportunities — Agent by Agent

### 1. `forecaster` — Primary target

**Current state:** FinBERT sentiment only. Advisory shadow signal, never binding.

**What qlib adds:** A library of time-series forecasting models purpose-built for equity
returns, with proper point-in-time handling (no lookahead). The models are complementary to
FinBERT: they work on price/volume/factor features, not text.

**Specific candidates:**

| Model | Why it fits |
| --- | --- |
| `LightGBM` (`qlib.model.gbdt`) | Fast, interpretable, state-of-the-art on tabular data; low inference cost |
| `HIST` (`qlib.contrib.model.pytorch_hist`) | Explicitly models stock-relationship graphs — pairs naturally with Neo4j edges |
| `TRA` (`qlib.contrib.model.pytorch_tra`) | Temporal Routing Adaptor; handles market regime shifts without retraining |
| `Transformer` (`qlib.contrib.model.pytorch_transformer`) | Captures long-range temporal dependencies missed by FinBERT |

**Integration pattern:**

```python
# agents/forecaster/domain/qlib_signal.py
from qlib.model.gbdt import LGBModel          # isolated here only
from contracts.forecaster import ShadowPrediction

class QlibShadowSignal:
    """Wraps a qlib model as a shadow signal; emits ShadowPrediction only."""

    def predict(self, features: pd.DataFrame) -> ShadowPrediction:
        raw = self._model.predict(features)
        return ShadowPrediction(
            value=float(raw),
            model_version=self._model_version,
            shadow=True,          # never gates a decision
        )
```

Each model is a separate `ShadowPrediction` emitter, governed independently by the P10
predictor-registry scorecard gate. A qlib model earns promotion by the same mechanism
FinBERT does: measured incremental information coefficient on forward returns, not taste.

**ADR impact:** None. ADR-0002 (champion-challenger) explicitly anticipated additional
shadow challengers behind the forecaster boundary. The three-impl pattern (lexicon /
provider-sentiment / FinBERT) generalizes to N.

**Dependency isolation:** Add `pyqlib` and `torch` (already present) to
`agents/forecaster/requirements.txt` only. The default unit gate stays `torch`-free for
all other agents.

---

### 2. `analyst` — Alpha factor library

**Current state:** Manual technical indicators (RSI, MACD, Bollinger, ATR, etc.),
fundamental scoring, and lexicon-based sentiment. Deterministic, binding.

**What qlib adds:** Alpha158 and Alpha360 — libraries of 158 and 360 engineered features
respectively, covering:

- Price/volume momentum and mean-reversion at multiple horizons
- Volatility-adjusted returns, turnover ratios, drawdown features
- Cross-sectional z-scores (a stock relative to its market at a point in time)
- Calendar and microstructure features

These are **deterministic, reproducible formulae** over OHLCV data — not models. They are
implementable without pyqlib itself if the dependency is undesirable; the formulas are
published in the qlib paper (arxiv 2009.11189).

**Specific addition:** Alpha158 as a **fifth scoring pillar** inside the analyst, or as a
feature-enrichment step feeding the existing technical pillar.

```python
# agents/analyst/domain/alpha_features.py
from qlib.data.dataset.handler import Alpha158   # isolated here only

class AlphaFeaturePillar:
    """Computes Alpha158 cross-sectional features from OHLCV data."""

    def score(self, ohlcv: pd.DataFrame) -> float:
        features = Alpha158().fetch(ohlcv)
        # map to 0–100 via percentile rank against universe
        return self._rank_to_score(features)
```

**Governance:** The new pillar ships deterministic (no model, pure math), so it clears the
binding-signal bar without a champion-challenger phase. It does require a tunable weight
(e.g., `ALPHA158_PILLAR_WEIGHT = 0.15`) with the standard `kernel.tunable` justification.

**Prerequisite:** The provider agent must supply daily OHLCV to the analyst with enough
universe breadth for cross-sectional ranking to be meaningful (≥ 50 tickers per day). The
existing `price_cache` (629,823 rows, 507 tickers) satisfies this immediately.

**ADR impact:** None. A new analyst pillar is additive; the boundary map and analyst contract
are unchanged.

---

### 3. `portfolio_manager` — Risk-aware optimization

**Current state:** Heuristic sizing (fixed-fraction, cap-based), risk checks (cash cap,
minimum quantity), no covariance-based portfolio optimization.

**What qlib adds:** `qlib.strategy` includes portfolio optimizers that:

- Construct a covariance matrix from historical returns
- Apply mean-variance or risk-parity optimization
- Compute factor risk exposure (market beta, sector concentration)
- Enforce turnover constraints (limit churn per day)

**Integration pattern:** The portfolio_manager agent currently sizes each recommendation
independently. Qlib's optimizer replaces the final sizing step with a joint optimization over
the full `RecommendationSet`:

```python
# agents/portfolio_manager/domain/qlib_optimizer.py
from qlib.backtest.position import Position
from qlib.strategy.base import BaseStrategy      # isolated here only

class CovarianceAwareSizer:
    """
    Replaces fixed-fraction sizing with mean-variance optimization.
    Returns the same OrderIntentSet shape; the contract is unchanged.
    """

    def size(self, recs: RecommendationSet, portfolio: PortfolioState) -> OrderIntentSet:
        weights = self._optimizer.optimize(
            expected_returns=self._extract_scores(recs),
            covariance=self._cov_matrix,
            constraints=self._build_constraints(portfolio),
        )
        return self._weights_to_order_intents(weights, recs)
```

**Advisory-first discipline:** Ship as a shadow sizer running in parallel with the
deterministic heuristic, comparing sizing decisions for 30+ trading days before any promotion
consideration. Same champion-challenger pattern; the PM's risk checks remain the final gate
regardless.

**Risk:** Covariance matrix requires sufficient history (≥ 60 trading days, preferably 252)
and a stable universe. Estimation error in small universes can produce degenerate allocations.
Shrinkage estimators (Ledoit-Wolf) from `sklearn.covariance` mitigate this and are already
an approved dependency.

---

### 4. `researcher` — Validated proposals

**Current state:** Proposes bounded parameter changes into the human-review queue, backed by
evidence from the provenance graph. Has no ability to run controlled experiments before
proposing.

**What qlib adds:** `qlib.backtest` provides a point-in-time backtester with:

- Fill simulation (slippage, market impact)
- No lookahead bias guarantees (uses historical data as it would have been available)
- IC (information coefficient), Sharpe, max drawdown, and turnover metrics
- Rolling-window evaluation to detect regime sensitivity

**Integration pattern:**

```python
# agents/researcher/domain/qlib_backtest.py
from qlib.backtest import backtest, executor   # isolated here only

class ProposalValidator:
    """
    Runs a qlib backtest for a parameter change proposal.
    Returns structured metrics that become the evidence field
    of a ParameterChangeProposal.
    """

    def validate(self, proposal: ParameterChangeProposal) -> BacktestEvidence:
        result = backtest(
            strategy=self._build_strategy(proposal),
            executor=executor.SimulatorExecutor(...),
            start_time=self._evidence_window_start,
            end_time=self._evidence_window_end,
        )
        return BacktestEvidence(
            sharpe=result.sharpe,
            ic=result.ic_mean,
            max_drawdown=result.max_drawdown,
            turnover=result.turnover,
        )
```

**Value:** The researcher currently proposes changes with provenance-graph evidence (past
outcomes). Qlib's backtester adds a **prospective** evidence dimension: "this parameter
change, applied to historical data, would have produced these metrics." Human reviewers get
both retrospective evidence (what actually happened) and simulated evidence (what would have
happened with the proposed change) before approving.

**Constraint:** Backtests run offline, never in the live decision path. The researcher's
`Never: Apply a parameter change` rule is unchanged — the backtester produces evidence, not
actions.

---

## What NOT to Use from Qlib

| Qlib component | Why it does not apply |
| --- | --- |
| `qlib.data` storage layer | The project uses Neo4j + provider agent. No reason to replace a working, governed data layer with qlib's proprietary format. |
| `qlib.workflow` experiment tracker | Duplicates the P10 predictor-registry pattern already designed for this project. One experiment tracking system per project. |
| RD-Agent (LLM factor mining) | The project's deliberate policy: LLM drives operator narration and intent parsing, never trading decisions. RD-Agent blurs this boundary. |
| RL order execution (PPO/OPDS) | Targets simulation; the project's execution agent connects to live Alpaca. RL policies trained on simulation have no validated transfer guarantee to live markets without a long shadow-testing phase. Flag as a moonshot candidate, not a near-term integration. |
| Qlib CLI / workflow runner | The project has its own orchestration (dispatcher, supervisor). Replacing the runner would break the boundary enforcement and audit trail. |

---

## Phasing

Phases align with the project's existing P-numbering. None of these require a new ADR unless
a promoted model becomes binding — at which point an ADR closes the governance question for
that model.

### Phase Q1 — Forecaster LightGBM shadow signal

**Prerequisite:** P12 (sentiment champion-challenger infra) complete.
**Work:** Add `lightgbm` to the forecaster optional dependency group (pyqlib is uninstallable on
3.13 — see the update note). Implement a `ReturnModel` port + a lazy `LightGBMModel` adapter wrapping
`lightgbm.Booster`. Wire it into the forecaster's shadow-prediction loop alongside FinBERT. Register
it in the P10 predictor-registry. Detailed handover:
[sprint-58](../sprints/sprint-58-forecaster-lightgbm-shadow.md).
**Exit:** `ShadowPrediction` nodes appear in the graph with `model_version = "lgbm-qlib-v1"`;
scorecard harness tracks IC against forward returns.
**Effort:** S (2–3 days). No architecture change.

### Phase Q2 — Analyst Alpha158 pillar

**Prerequisite:** Phase Q1 validated (proves pyqlib works cleanly behind an agent boundary).
**Work:** Add `Alpha158` as an optional fifth pillar inside `agents/analyst/domain/`. Gate
behind a tunable weight `ALPHA158_PILLAR_WEIGHT` (default 0.00 — off). Enable by operator
command after 20-day shadow comparison against existing pillar set.
**Exit:** Analyst composite score optionally incorporates Alpha158; IC comparison shows
whether it adds information beyond the existing technical pillar.
**Effort:** M (3–5 days). Tunable governance entry required.

### Phase Q3 — Researcher backtest evidence

**Prerequisite:** P7 (researcher agent) fully implemented.
**Work:** Superseded by the 2026-07-04 addendum and Sprint 112: qlib's own
backtest engine remains unavailable on Python 3.13, so the project ships a
self-built deterministic walk-forward harness inside `agents/researcher/domain/`.
`ParameterChangeProposal` carries an optional `BacktestEvidence` field; evidence
generation is script-only until a governed evidence hand-off pattern is designed.
**Exit:** Human reviewers see simulated Sharpe/IC alongside provenance-graph evidence on
every proposal.
**Effort:** M (4–6 days). Contract change requires boundary map update.

### Phase Q4 — Portfolio covariance optimizer (shadow)

**Prerequisite:** 60+ days of live portfolio data in Neo4j; Phase Q3 researcher backtest
validates optimizer proposals first.
**Work:** Implement `CovarianceAwareSizer` inside `agents/portfolio_manager/domain/`.
Run in shadow: both heuristic and optimizer size every `RecommendationSet`; record both
in the graph. Scorecard compares realized outcomes.
**Exit:** Shadow sizer accumulates 60 trading days of side-by-side records. Operator reviews
scorecard and decides whether to promote.
**Effort:** L (5–8 days). Requires `sklearn.covariance` (already approved stack).

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| `pyqlib` requires Python ≤ 3.12 | **Confirmed** | High (project targets 3.13+) | **Resolved for Q1:** depend on standalone `lightgbm` directly (no pyqlib import). Q3/Q4 need qlib's own engine — re-scope when reached (vendor MIT source, or a 3.13-capable alternative) |
| LightGBM signal adds no IC | Medium | Low | Governed by the scorecard gate; dropped on evidence, not opinion |
| Alpha158 correlates fully with existing technical pillar | Medium | Low | Measured at Phase Q2 exit; if IC increment ≈ 0, pillar is not enabled |
| Covariance matrix degenerate on small universe | High | Medium | Use Ledoit-Wolf shrinkage; enforce minimum 50-ticker universe in the optimizer's precondition check |
| Backtest overfitting in researcher proposals | Medium | Medium | Enforce walk-forward validation (in-sample ≤ 70%, out-of-sample ≥ 30%); document in researcher's `Never` list |
| qlib brings heavy transitive dependencies | Low | Medium | Pin `pyqlib` to a fixed version; audit `pip show pyqlib` dependency tree before adding |

---

## For Coding Agents

When implementing any phase above, the following invariants must hold. These are
mechanically enforced by the existing CI gate — a violation will fail the boundary
meta-test or coverage ratchet.

1. **Import qlib only inside `agents/<name>/domain/`**. Never in `contracts/`, `kernel/`,
   `surfaces/`, or any other agent's tree.

2. **No qlib symbol in a contract message**. `ShadowPrediction`, `BacktestEvidence`, and
   all other contract types are defined in `contracts/` using only stdlib and project-local
   types. If you need to pass a qlib-computed value across the bus, extract a scalar or
   structured dict before constructing the contract message.

3. **Every new tunable constant needs a justification.** Use `kernel.tunable` — see
   `docs/laws/dependencies.md` and existing examples. Default to `0.00` (off) for new
   pillars until the scorecard earns a non-zero weight.

4. **Shadow flag is non-negotiable.** Any new qlib-backed signal is `shadow=True` in its
   `ShadowPrediction`. It may not gate, veto, or override a deterministic decision until
   the P10 predictor-registry promotion flow has been completed and an operator has
   approved promotion.

5. **Test coverage ratchet.** The 100% coverage floor applies. Mock `pyqlib` at the agent
   boundary in unit tests (do not call qlib in the default unit suite). Add an
   integration-marked test that calls qlib against fixture data for the real validation.

6. **Dependency group isolation.** Add `pyqlib` only to the requiring agent's
   `requirements.txt`. It must not appear in `kernel/requirements.txt` or any shared
   location.

7. **Model artifacts are external I/O.** If a qlib model requires a trained artifact
   (weights file), declare it in the agent's `External I/O` section in `mission.md` and
   handle it under the same provisioning pattern as the FinBERT model in the forecaster.

---

## Relation to Moonshots

Qlib accelerates two moonshots without requiring their full scope:

| Moonshot | Qlib contribution |
| --- | --- |
| **#1 — Probability distributions** | Qlib's ensemble of models (LightGBM + Transformer + HIST) can produce calibrated return distributions via conformal prediction or bootstrap ensembles, feeding the `P(profit > 0)` / `E[drawdown]` vision without needing ABIDES simulation first. |
| **#3 — Self-evolving signal loop** | Qlib's backtest engine is the validation harness the researcher loop needs. Moonshot #3 proposes new indicators; qlib's backtester scores them on historical data before they go to shadow. The loop becomes: researcher proposes → qlib validates → operator approves → shadow → scorecard → promote. |

Moonshot #4 (causal DAG) is independent of qlib (DoWhy/EconML) and is unaffected.

---

## Summary Decision Matrix

| Integration | Agent | Effort | Architecture risk | Priority |
| --- | --- | --- | --- | --- |
| LightGBM shadow signal | forecaster | S | None | **High — do first** |
| Alpha158 pillar | analyst | M | None | Medium |
| Backtest evidence for proposals | researcher | M | Minor (contract field) | Medium |
| Covariance portfolio optimizer | portfolio_manager | L | None (shadow only) | Low — after 60 days live data |
| RL order execution | execution | XL | High (live broker gap) | Moonshot only |
| qlib data layer | provider | — | High (replace working system) | **Do not do** |
| RD-Agent | forecaster/researcher | — | High (policy violation) | **Do not do** |

---

## Addendum (2026-07-04) — workflow-level pass

**Prompt:** the operator's goal restated as three claims the system must earn — *"they did their
homework"*, *"decisions based on all available evidence"*, *"the system is self-learning and
self-improving"*. The original document catalogued qlib's **components**; this pass mines its
**workflows**. Sources re-checked 2026-07-04: `pyqlib` still supports Python 3.8–3.12 only (no
cp313 wheel — the Q1 constraint stands); RD-Agent(Q) (NeurIPS 2025) since validated the governed
factor-mining loop's economics (meaningful factor discovery at trivial compute cost).

### Revised phasing

Sequencing: **Q1b → Q1c → Q3 → Q5**; Q4 unchanged behind its 60-day live-data prerequisite.

**Q1b — Signal evaluation battery (packaged: [sprint-110](../../sprints/sprint-110-signal-evaluation-battery.md)).**
Qlib's report module treats pooled IC as the *start* of signal evaluation, not the conclusion. Extend
the S59 return scorecard with rank IC (Spearman — robust to the 0-1 squash on predictions), per-date
cross-sectional IC series (mean/std/IR), quantile group returns with top-bottom spread + monotonicity,
multi-horizon IC decay, and rank-autocorrelation stability, plus an offline out-of-sample-only
evaluation CLI producing a per-model evidence report. No qlib import — standard math. Serves claim 1;
also builds the measurement Q1c triggers on.

**Q1c — Rolling retrain + IC-decay trigger (shipped: [sprint-111](../../sprints/sprint-111-rolling-retrain.md)).**
A train-once model silently decays; qlib's online-serving workflow retrains on a rolling window and
swaps champion only when the challenger wins walk-forward. Adopted pieces: a pure
`agents/forecaster/domain/retrain_policy.py` decay/verdict policy, `scripts/export_tiingo_bars.py`
for DL-37 Tiingo-sourced raw-history exports, and `scripts/retrain_return_model.py` for the operator
loop. The default is dry-run; `--force` trains a challenger even when decay did not trigger; `--apply`
is the only path that archives the incumbent and installs the challenger. 429s from Tiingo stop the
export for hourly-reset resume; transient 5xx/timeouts get bounded sync backoff. Alpaca remains the
primary runtime/batch OHLCV path; Tiingo is used here only for cheap-fallback / raw-history lineage.
Skip DDG-DA's drift *forecasting* (research-grade). Serves claim 3 mechanically, using the existing
champion–challenger machinery.

**Q3 — re-scoped to a self-built walk-forward harness (shipped: [sprint-112](../../sprints/sprint-112-researcher-backtest-evidence.md)).**
The pyqlib wall stands on 3.13 and vendoring the engine is rejected (heavy, drifts from upstream,
conflicts with the 200-line/100%-coverage regime). The shipped harness is a thin deterministic
simulator inside `agents/researcher/domain/` (fills at next close, fixed slippage in bps as a tunable,
walk-forward split ≥ 30% out-of-sample). The `BacktestEvidence` contract field and reviewer-facing
intent are unchanged from the original Q3. Serves claim 2 — every proposal can carry prospective
evidence alongside retrospective provenance. Also now the **prerequisite for Q5**.

**Q5 (new) — governed factor-mining loop.** RD-Agent's hypothesis → implement → backtest → feedback
loop with this project's governance bolted on: the researcher (LLM) *proposes* candidate factors; the
Q3 harness scores them deterministically; a human approves; shadow period; scorecard; promote or
kill. The LLM only ever proposes — the "LLM never drives trading decisions" policy is preserved, so
the original RD-Agent exclusion stands while its loop shape is adopted. This is Moonshot #3 made
concrete. Blocked by Q3.

### Noted, no sprint yet

**Point-in-time fundamentals discipline.** Fundamentals get restated; a backtest that uses today's
corrected number for last year's date is silent lookahead. When Finnhub fundamentals become decision
inputs, store them as-first-reported (qlib's PIT-database lesson). Owner: provider phase planning.

### Still excluded

Nested decision execution (order-execution optimization — irrelevant at Alpaca-paper scale), full
DDG-DA meta-learning, BPQP, and RD-Agent's autonomous mode — all for the original reasons.
