---
type: Architecture Decision
status: accepted
closes: "How do we keep an LLM-attached agent's output quality from degrading when we change model, provider, fallback tier, or functionality? Do we adopt DSPy, EvoPrompt, or both?"
tags: [llm, prompts, dspy, evoprompt, quality-gate, champion-challenger, operator, forecaster, p10]
---

# ADR-0010 — LLM interaction quality: eval-gated prompts, DSPy behind a port

**Status:** Accepted
**Date:** 2026-06-20
**Deciders:** Operator

---

## Context

An LLM-attached agent is **code + a prompt + a model**. Code quality is already arrested
by linters, types, tests, and CI. The **LLM interaction** — prompt × model — is the
uncontrolled surface, and it degrades for reasons outside our code:

- the model changes (version bump, **provider swap**, **fallback-tier** activation, silent
  provider-side updates, deprecation);
- decoding params change (temperature, top_p, max_tokens, seed, stop);
- the prompt, its few-shot demonstrations, or the output/tool **schema** change;
- the bounded **action set** changes (operator intent families, a report's allowed
  sections, the MCP/skill tool set) — which invalidates any prompt compiled against it;
- the input distribution drifts (new operator phrasings, new message types, adversarial
  input) or the injected context/RAG/graph evidence changes.

The operator is human and fallible; models will change. We want an **independent method
that guarantees no quality degradation across these changes** — and one that can be run
**proactively** (validate a candidate/fallback model *before* the switch), not only after.

Today the **operator** is the only agent that calls an LLM (`agent.py`,
`complete(system=…)` for intent parsing + explanation). The **forecaster** is designated
for LLM macro-event extraction (build-plan; P13, not yet built). Narration is an
operator-LLM concern, not a separate agent. Every other agent is deterministic.

DSPy is trusted in prior work (structured/outbound, multi-step). EvoPrompt is unproven
here but reads as offering proactive, evolutionary prompt search.

## Decision

**The independent guarantee is the eval harness, not the optimizer.**

1. **Golden eval set + metric per LLM task** is the regression gate. Every change to
   model, provider, decoding params, prompt, schema, or action set must pass the frozen
   set before promotion. This is tool-agnostic and is the durable, load-bearing asset.

2. **A prompt is a versioned predictor**, compiled **per (task × model)** and stored in
   the predictor registry, promoted through the existing **champion–challenger** gate
   (ADR-0002 pattern, P10). The `system_prompt` declared on the agent (a `tunable` in its
   settings / law `PARAM`, per ADR-0007) is the **champion slot** the gate writes back to.

3. **Optimization is offline, behind a `PromptOptimizer` port** —
   `(task signature + metric + examples + target model) → versioned prompt artifact`.
   **DSPy is the first and only adopted implementation.** EvoPrompt (and OPRO / GEPA /
   TextGrad / APE) stay one implementation away for a future, data-driven **bake-off on the
   same golden set** — itself a champion–challenger. We adopt **DSPy now, not both**.

4. **Fallback tiers are pre-compiled and pre-validated.** Each (task × model) the runtime
   may fall back to has a known-good prompt compiled and gated *offline ahead of time*, so a
   runtime fallback loads a validated prompt, never an untested one. Decoding params are
   pinned (temperature 0 / seed where supported); structured output is validated at the
   boundary (refuse/repair on miss).

5. **Triggers** re-run the harness: model/provider/decoding change, schema/action-set
   change, scheduled cadence, and input-drift detection.

The proactive requirement is satisfied by DSPy itself: recompile a task against a
candidate or fallback model offline and evaluate on the frozen set before switching. A
separate optimizer is **not** required to get proactive validation.

## Consequences

### Immediate (this decision)

- `system_prompt` is declared as a `tunable` in each LLM-backed agent's definition — the
  **operator** now, the **forecaster** pre-declared (unused until its LLM path ships). It
  is documented in the agent's law `PARAM` section as the champion slot (ADR-0007).
- No optimizer code lands yet — adding unused DSPy/EvoPrompt wiring would be dead config.

### Deferred (own sprint, ADR-backed)

- The **eval harness** (`PromptOptimizer` port + DSPy first impl + per-(task×model) compiled
  artifact + registry entry + promotion gate). Gated on having eval data.
- **The long pole is the metric + example set, not the tool.** Structured tasks (operator
  intent, report schemas) get cheap exact/F1 metrics and can harvest labeled examples from
  the operator's LLM ledger. **Free-form report quality needs a rubric / LLM-as-judge
  metric that must itself be validated** — the genuinely hard, later work. No optimizer
  helps until that metric exists.

### Permanent

- Any new LLM task requires a golden set + metric before its prompt can gate or promote.
- Adopting a second optimizer (EvoPrompt et al.) requires a bake-off against DSPy on the
  same golden set — never adopted on reputation.

## Alternatives considered

- **EvoPrompt only.** Rejected: unproven here, narrower (free-form string search; no
  structured output, multi-step pipelines, or few-shot demo selection), and it does not
  cover the operator's structured intent-parsing or report schemas.
- **DSPy *and* EvoPrompt now.** Rejected: doubles integration + artifact maintenance for an
  unproven, task-dependent gain. The proactive case — the stated reason to want
  EvoPrompt — is already covered by DSPy's per-model recompile. Kept as a future bake-off.
- **No optimizer; hand-tuned static prompts only.** Rejected: provides detection (if the
  harness exists) but no **recovery** mechanism, and does not scale to the many planned
  report prompts.
- **Prompt as a plain static tunable with no gate.** Rejected: a tunable string without a
  golden-set gate gives the *illusion* of control with no guarantee against model-swap
  degradation — the exact risk this ADR exists to close.

## Open question (follow-up, non-blocking)

Whether prompt-predictors live in the **same** registry as model predictors (LightGBM,
FinBERT) or a **sibling** keyed by (task × model). Affects the registry schema; resolved
when the harness sprint is planned.
