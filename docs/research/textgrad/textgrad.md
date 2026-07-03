# Research: TextGrad — textual-gradient optimization for the continuous-improvement effort

**Status:** Research complete · **Date:** 2026-07-03 · **Author:** planning agent (operator-reviewed)
**Audience:** Product owner, planning agents, coding agents
**Source:** <https://github.com/zou-group/textgrad> (Stanford Zou group; Nature, March 2025; MIT)

---

## What it is

"Autograd for text." LLM-generated critiques act as **textual gradients** backpropagated through a
computation graph; a PyTorch-like API (`Variable`, `TextLoss`, `TGD` optimizer, `.backward()` /
`.step()`) iteratively rewrites whatever is marked optimizable — prompts, but also **specific
instances**: a solution, a code snippet, a report draft. Supports OpenAI + Anthropic (plus LiteLLM
engines). ~3.6k stars.

## Question asked

Can TextGrad help the continuous-improvement effort (ADR-0010 prompt quality, ADR-0013 CI-1..CI-6,
DL-24 drift firewall)?

## Findings

1. **The repo already holds a position on it.** ADR-0010 names TextGrad (with EvoPrompt / OPRO / GEPA /
   APE) as staying "one implementation away" behind the `PromptOptimizer` port — adoptable **only via a
   data-driven bake-off on the same golden set** vs DSPy, never on reputation.
   `docs/technology-stack.md` lists it as CONSIDERED. Nothing found changes that calculus.
2. **The port now exists (S107)** — `kernel/optimizer.py` + `kernel/dspy_optimizer.py`, with one live
   gated instance (the remediation selector). A TextGrad implementation behind the same port is cheap
   to build *when a bake-off is warranted*.
3. **Its distinctive capability vs DSPy is instance-level (test-time) optimization.** DSPy compiles a
   reusable prompt offline; TextGrad can refine a *specific output* (a report narrative, a proposal
   rationale) against a natural-language loss. That maps to the reporter/researcher free-form outputs —
   but ADR-0010 already flags the blocker: **free-form quality needs a validated rubric / LLM-judge
   metric first**, and that metric does not exist yet. Without it, TextGrad's loss is just another LLM
   opinion steering the text.
4. **The mechanism is already run by hand here.** Textual-gradient = critique→revise, which is the
   deliberation Challenger + the DL-25 findings→code loop — except this system deliberately routes
   critiques through laws, gates, and a human rather than auto-revision. A deliberate control, not a gap.
5. **Not blocked on tooling.** The CI effort's actual blockers are golden sets + metrics (ADR-0010's
   stated long pole) and CI-1..CI-6 deferred behind the etalon (DL-19). Only two golden sets exist today
   (remediation selector: 5 cases; deliberation Class-1: 6 cases) — a DSPy-vs-TextGrad bake-off on sets
   that small measures noise, not optimizers.
6. **Maintenance risk.** Last release v0.1.6 (Dec 2024, ~18 months old at evaluation), ~140 commits —
   research-grade, not an actively maintained production dependency. DSPy is trusted and already landed.

## Recommendation (accepted by operator, 2026-07-03)

**Do not adopt now.** Keep TextGrad exactly where ADR-0010 put it — the named bake-off challenger behind
the `PromptOptimizer` port — with two concrete **revisit triggers**:

- **(a)** ≥3 real golden sets exist and an optimizer bake-off is wanted, or
- **(b)** the free-form report-quality metric (rubric / LLM-as-judge) ships — the one place TextGrad's
  test-time refinement offers something DSPy does not.

## Ruled out (and why)

- *Adopt as a second optimizer now* — violates ADR-0010's bake-off rule; nothing is blocked on it.
- *Use for test-time report refinement now* — no validated quality metric to serve as the loss; an
  ungated LLM self-revision loop conflicts with the audit/gate discipline (DL-31 asymmetry).
