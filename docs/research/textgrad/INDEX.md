# R003 · TextGrad — textual-gradient optimization, evaluated for continuous improvement

**Status:** 🗄️ Archived (evaluated — not adopted now; kept as the ADR-0010 bake-off candidate) ·
**Date:** 2026-07-03

Can TextGrad (Stanford Zou group — "autograd for text": LLM critiques as backpropagated textual
gradients) help the continuous-improvement effort? **Answer: not yet.** The eval harness — not the
optimizer — is the guarantee (ADR-0010); TextGrad stays one implementation away behind the
`PromptOptimizer` port (which exists since S107), adoptable only via a bake-off on the same golden set
vs DSPy. Its one distinctive capability (instance-level / test-time refinement of free-form outputs)
is blocked on the not-yet-built report-quality metric. Maintenance is research-grade (last release
Dec 2024).

- **[textgrad.md](textgrad.md)** — full evaluation: what it is, findings, revisit triggers, ruled-out
  options.

**Answers:** What is TextGrad and how does it differ from DSPy? Should it join the optimizer stack now?
What would make it worth adopting later?

**Consuming decisions:** ADR-0010 (optimizer bake-off rule — unchanged);
`docs/technology-stack.md` CONSIDERED row.

**Outcome:** Not adopted. **Revisit triggers:** (a) ≥3 real golden sets exist and an optimizer bake-off
is wanted; (b) the free-form report-quality metric (rubric / LLM-as-judge) ships.
