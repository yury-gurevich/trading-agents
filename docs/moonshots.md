# Moonshots — Conceptual Edge of What Is Possible

**Source:** ported from `traiding-system/docs/moonshots.md` (v1), 2026-06-19.
**Status:** exploratory vision, not committed roadmap. Original draft 2026-04-18.

> This document is maintained as a long-horizon guide. Ideas here are not on the sprint
> board, but they influence architectural decisions made today. Before locking a design
> choice consult this file — some "future" ideas constrain what "simple" looks like now.

## v2 alignment notes (added 2026-06-19)

Several moonshots have already partly landed in v2 or shaped its architecture:

| Moonshot | v2 status |
| --- | --- |
| #2 Multi-agent deliberation | The container-per-agent architecture (ADR-0007) and master bootstrap are the substrate for this. P14. |
| #3 Self-evolving signal loop | Forecaster agent + P10 predictor-registry gate + `sentiment_scorecard` harness are the first scaffolding. |
| #5 System narrates itself | Operator LLM narration is the v2 equivalent. The corpus begins accumulating now. |
| #6 MASTER supervisor | Partially resolved: the "master" bootstrap agent (ADR-0007) owns identity + secrets + activation. Full incident-recovery catalogue is a later phase. |

Code path references in the original text point at v1 (`src/trading_v2/`, `src/trading/`). The v2 equivalents live in `agents/`, `kernel/`, `contracts/`.

---

## Original document (unmodified)

Status: exploratory vision, not committed roadmap. Drafted 2026-04-18.

Five directions ranked roughly by *daring × feasibility in this codebase*. The
pattern across all of them: change *what kind of object flows through the
pipeline*, not just make a single function smarter. That is where the real
ceiling is.

---

## 1. Turn the analyst into a probability distribution, not a number

**Idea.** Stop shipping a single `composite_score` per candidate. For every
survivor, run *N* microstructure simulations under varied conditions
(order-flow imbalance, queue position, news-spike timing) and emit:

- `P(profit > 0)`
- `E[drawdown]`
- `tail_loss_p99`
- `time_to_target`

The Portfolio Manager then optimises a portfolio over **distributions** instead
of points — Kelly fractions, CVaR budget, the whole modern-portfolio-theory
apparatus becomes available.

**Why feasible here.** ABIDES is already wired in (`src/trading_v2/simulation/`).
The diagnostics schema can absorb a JSON distribution column. No new external
dependencies.

**Why daring.** Almost nobody at retail does this. It changes the unit of
analysis of the entire system from a number to a distribution; every
downstream component (PM sizing, monitor exits, reporter narrative) becomes
more honest.

**First lever.** Ship this first. Everything else (#2–#5) layers on more
naturally once the system thinks in distributions.

---

## 2. Multi-agent deliberation per candidate

**Idea.** Replace the weighted scalar fusion in `analyze_candidate` with three
small LLM calls in parallel, each with a distinct persona:

- **Technical Bull** — argues the buy case from `algo_scores` + signals
- **Fundamental Skeptic** — argues against from `metrics` + EDGAR fallback
- **Macro Risk Officer** — weighs regime, VIX, breadth, news spikes

A 4th synthesizer reconciles them and produces a structured rationale and a
final recommendation.

**Why this beats scalar fusion.** Catches the failure mode weighted sums
cannot: "MACD says buy *and* the 8-K filed yesterday says the CFO resigned."
Scalar fusion has no language to express that conflict; debate does.

**Cost discipline.** Aggressive prompt caching — system prompt and tool schemas
cache across all candidates in a run, so full token cost is paid ~once per
pipeline. With Anthropic SDK this is one parameter; with local models, see
moonshot caveats.

---

## 3. Self-evolving signal discovery loop

**Idea.** Wire a weekly cron-triggered agent that:

1. Reads the last 30 days of `AnalystDiagnostic` rows.
2. Identifies reject-reason / regime combinations where the system bleeds
   alpha (e.g. "in `high_vol` regime, `sentiment` rejects miss 12% upside").
3. Proposes a new indicator as a Python function.
4. Writes tests for it.
5. Runs it in **shadow mode** alongside existing indicators for 2 weeks.
6. Opens a PR to itself if the new indicator beats the ML-2 baseline on
   shadow metrics.

The human becomes the reviewer of an autonomous quant.

**Why feasible here.** Agent SDK is available. `docs/sprint-loop.md` defines
the gate. Quality gate has 863+ tests. Shadow forecasting harness already
exists (`src/trading/ml/shadow_forecast.py`). The system already self-narrates
diagnostics — the missing piece is the loop that proposes and validates code.

**Why daring.** Constrained, gated, falsifiable autonomous engineering. The
discipline of the existing codebase is what makes this safe to attempt; in a
messier project it would be reckless.

---

## 4. Causal DAG over signals instead of weighted sum

**Idea.** Replace correlation-fitted ML-2 weights with a learned causal graph:

- Nodes: indicators, regime, VIX, sector, future return.
- Edges: causal direction (regime confounds RSI→return; VIX confounds
  sentiment→return; etc.).
- Tooling: DoWhy or EconML.

**What this unlocks.**

- **Counterfactual contribution attribution** — "RSI bought you 8 bps of edge
  here, sentiment cost you 3."
- **Principled signal pruning** — drop indicators whose causal contribution is
  zero, not just whose weights are small.
- **"What if I had ignored sentiment?"** becomes a real query, not a
  hand-wave.

**Why feasible here.** Layers on top of the shipped ML-3 Ensemble (v0.6.0,
2026-04-09). The diagnostic data needed is already persisted.

---

## 5. The system narrates itself, then learns from the narration

> **Partial status:** Phase 1 (on-demand narration of analyst diagnostics)
> shipped as the operator LLM narration MVP in b8fb5c0. The corpus foundation has
> begun. Expanding narration to all decision types, and the phase-2
> fine-tuning bet below, remain open.

**Idea.** Every decision the system makes — accept, reject, regime gate, ATR
override, position sizing — gets persisted alongside a natural-language
explanation generated by an LLM at decision time.

After 6–12 months: a corpus of *your own analyst's reasoning*, joined to
realised outcomes.

**Phase 2.** Fine-tune a small open model on that corpus. You end up with a
local, free model that has internalised your system's policy and can serve as
the always-on inner voice when API calls are slow or unavailable on the free
tier.

**Why feasible here.** HuggingFace pipeline already present
(`src/trading/services/huggingface.py`, `services/finbert.py`). The narration
itself can start with any model — the *value* compounds in the corpus.

---

## 6. MASTER supervisor agent for system-wide recovery

**Idea.** A supervisor agent (built on the Claude Agent SDK) that watches the
incident stream continuously. When a dependency degrades — FinBERT sticky,
Stooq flaky, Edgar 404s — the supervisor:

1. Correlates the incident with past ones (pattern or one-off?)
2. Chooses a recovery action from a catalogue (restart service, swap provider,
   tighten throttle, re-authenticate, widen backoff)
3. Applies the action under the system's existing staged-execution gates
4. If recovery fails within a budget, escalates by triggering the dashboard's
   `[Send to support]` flow with a pre-populated bundle
5. Records the chosen action and its outcome as training data for its own
   future decisions

The operator supervises the supervisor, not the base system.

**Why feasible here.** The incident stream, stable dependency tags, and
`recovery_method` field are all in place after Stage A1. Claude Agent SDK
supports long-running agents with tool access. `ExecutionStageAudit`
already exists, so the supervisor's actions are bounded and auditable
from day one.

**Why daring.** Autonomous self-healing is rare at retail. It gives the
system an *immune system* — the operator wakes up to "3 incidents opened
overnight, all auto-recovered" instead of "the pipeline has been broken
since 2 am." Combined with Moonshot #3 (self-evolving signal discovery),
the system can eventually patch its own bugs inside the same gated loop.

**Cost discipline.** The supervisor is lazy: idle at zero cost, activates
only on incident events. Prompt caching for the catalogue of recovery
patterns means each activation is a small delta.

**Design hook.** The `recovery_method` field added to closed incidents in
Stage A1 is the training signal. Every auto-recovered incident becomes a
row of "here's what worked" for the supervisor to learn from.

**Incident hierarchy (owner insight, 2026-04-21).** The supervisor
produces a three-tier recovery structure:

- **Tier 0 — code-level self-heal.** Retries, backoffs, and the recovery
  paths wired in Stage A1. If a dependency recovers on its own, the
  incident closes with `recovery_method ∈ {automatic_retry, backoff_elapsed,
  provider_recovered}`. Human never sees it.
- **Tier 1 — MASTER recovers.** MASTER picks an action from its catalogue
  (restart, swap provider, re-auth, tighten throttle), applies it under
  the staged-execution gates, and on success closes the incident with
  `recovery_method = "master_agent"`. Audited; human still never sees it.
- **Tier 2 — MASTER cannot recover.** MASTER opens a *meta-incident* —
  "I encountered X and none of my catalogue entries worked." The
  meta-incident auto-triggers the dashboard's `[Send to support]` flow.
  These are the only incidents a human (operator or distributor)
  actually triages. By construction the set is small and consists of
  failures that could not be foreseen at coding time.

The `[Send to support]` button is therefore rarely pressed by the
end-user directly — it is mostly auto-triggered by MASTER escalation.
Manual press remains as a catch-all for things MASTER doesn't yet know
how to watch for.

---

## 7. The platform bootstraps its own proof (meta-moonshot)

> **Status:** a dream — like everything here was at the start of its life (owner, 2026-06-21).
> Qualitatively different from #1–#6: those make *trading* better; this is about the
> **platform underneath trading.** Prerequisite: trading fully shipped + the substrate/pack
> wall clean (ADR-0012). Until a second pack exists, this is not even meaningful to attempt.

**The realization.** What we built is not a trading system — it is a **substrate for
text-defined businesses** (master bootstrap, minimum-privilege capability grants, typed
contracts on a bus, the laws framework, the ops constitution, the provenance graph). Trading
is the *first pack* expressed on it. Nothing financial is load-bearing in the substrate;
swap the pack and the same machine could run a shoe factory or a print shop — agents that
drive machinery instead of a broker, governed by the same laws.

**The experiment.** Have the platform *independently* execute the prompt **"create me a stock
trading company"** — synthesising the agents, laws, contracts, capability grants and gates
from intent — and then **compare its output against the hand-drafted system we built.**

- The **hand-built trading pack is the golden reference.**
- The **autonomously-generated pack is the candidate.**
- The **delta** (missing agents, weaker laws, wrong boundaries, absent gates) is the metric.
- **Continuous improvement (LAW-01)** drives the delta toward zero, run after run.

**Why it is the whole thesis as an experiment.** This is champion–challenger (ADR-0010)
lifted from *prompts* to *entire businesses* — the platform grading itself against the one
business we *know* is correct. The day the delta closes, the substrate has demonstrated it
can synthesise what a human architect synthesised. That is not a feature; it is the proof
that "text-defined business" is real.

**Why daring / why gated.** Same discipline as #3, one level up: the generator is
**bounded, falsifiable, and gated** — it proposes a pack, the eval (delta vs golden) judges
it, the operator promotes. It never auto-deploys a synthesised business. Deterministic core,
LLM as the bounded synthesiser.

**What it depends on.** Trading done (the reference must exist and be trusted); the
substrate↔pack wall held clean from now (ADR-0012) so a pack can be *generated against* a
domain-agnostic substrate; and at least one second pack to prove the abstraction before this
is more than introspection.

---

## Cross-cutting bet: privacy-first local execution

If the target persona is the *suspicious, initially weary consumer*, the
strongest differentiator is **nothing leaves the machine**. That reframes the
moonshots:

- **#1** is fully local — pure simulation, no LLM needed.
- **#5** is local-friendly — narration can run on a quantized local model;
  quality bar is lower because outputs are explanations, not decisions.
- **#2** is the hard one locally — small quantized models tend to collapse to
  bland consensus rather than genuine disagreement, and the failure mode that
  makes debate valuable ("CFO resigned") needs world knowledge thin in 4B–12B
  parameter models.
- **#3** can run locally if the agent loop tolerates slower iteration.
- **#4** is fully local — pure statistics.
- **#6** is local-friendly — supervisor runs on the incident stream, no
  external calls required for basic recovery catalogue.

A pragmatic split: **simulation + causal layer + local narration shipped
fully on-device; LLM debate offered as opt-in cloud feature** for users who
trade privacy for fidelity. The privacy story becomes the headline; the cloud
mode becomes the "pro" tier without compromising the core promise.

---

## Cross-cutting preference: deterministic by default

A deliberate bias across every moonshot above: **prefer deterministic
methods when they can do the job, reach for LLMs only where verbal
reasoning is the actual value.** This is not anti-LLM — it is a division
of labour that matches the PRD's *evidence before automation* rule
(§3.5) and *deterministic self-improvement as the first layer* clause
(§6.4).

Concretely:

- **Measurement, simulation, statistics, rules, contracts — deterministic.**
  This is Moonshots #1 (ABIDES distributions) and #4 (causal DAG), the
  shipped ML-1 through ML-5 workstreams, every scorecard, every audit
  surface. The output is reproducible from inputs; a regulator or
  auditor can replay it. New reports belong here by default.
- **Narration, ambiguous classification, intent parsing — LLM.**
  This is Moonshots #2 (debate), #5 (narration), #6 (supervisor
  catalogue selection), and the Phase B operator LLM command layer. Always
  bounded by typed schemas, evidence-grounded prompts, and audit
  trails.

**Growth rule.** Every new surface — a report, a method, a feature —
asks *"can this be deterministic?"* before reaching for an LLM. If the
deterministic version is good enough, ship that; reserve LLM calls for
where their specific strength (language, interpretation, ambiguity
handling) earns its cost and audit burden. New deterministic report or
method ideas are parked via `/idea` and graduated into scope when a
sprint has room; they do not need to become their own moonshot to count.

---

## What I'd actually do first

Ship **#1**. ABIDES is already in-tree, dashboard surfaces are built, and the
diagnostics schema can absorb a JSON distribution column. It's the move that
changes the unit of analysis of the entire pipeline from a number to a
distribution — and once the system thinks in distributions, every other
moonshot becomes more natural to layer on.
