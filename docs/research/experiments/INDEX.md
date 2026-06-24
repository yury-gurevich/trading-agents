# Experiments log — research probes (purpose · process · delivery · interpretation)

**What this is:** the log of **research/probe experiments** — guess → run → measure → *learn*. Distinct
from **parameter experiments** (champion–challenger tuning of a `tunable()`), which use the
Experimentation charter's report (what-changed / gain / verdict). A probe asks a *question about the
system* (does the LLM understand our parameters? does feed X cover name Y?) and records what we learned.

## The record format (the definition — every probe uses these four headings)

| Heading | What it captures |
| --- | --- |
| **Purpose** | the question / hypothesis, and *why it matters* (what decision or risk it informs) |
| **Process** | exactly what we did — method, inputs, controls, models, what was withheld |
| **Delivery** | what was produced — outputs, artifacts, where they live |
| **Interpretation** | what it *means* — findings, deltas, the decision taken, and what it *feeds next* |

Rules (inherit LAW-02 / LAW-06): an experiment is recorded **while fresh**; *Interpretation* states the
proven finding, not the hoped-for one; if a probe was inconclusive, say so. The record is the LAW-05
defence for any action it triggers.

## Log

| ID | Title | Date | Feeds |
| --- | --- | --- | --- |
| [EXP-001](EXP-001-llm-parameter-interpretation.md) | Do the LLMs understand our decision parameters? (gpt-5.4 vs 5.5) | 2026-06-24 | DSPy role-prompt grounding (DL-21/22); switched `OPENAI_MODEL`→gpt-5.5 |
| [EXP-002](EXP-002-manufactured-eval-signal.md) | Can we manufacture a DSPy eval signal without trade outcomes? | 2026-06-24 | DL-23 (manufacture the eval set); proved grounded debate catches a known flaw the blind one misses |
| [EXP-003](EXP-003-eval-harness.md) | Build the manufactured-eval harness (Path B) | 2026-06-24 | shipped `kernel/deliberation_eval.py`; finding: a strong model catches textbook flaws blind — grounding's ROI is Class-1 (our-impl) facts; needs a sharper scorer |

## Adding an experiment

1. Next id is the increment (EXP-002). Create `EXP-00N-<slug>.md` with the four headings above.
2. Add a row here. 3. Link the artifacts (transcripts, critique docs) from *Delivery*.
4. If it triggers a parameter change, that change runs as a **parameter experiment** (charter report) —
   the probe *informs* the dial; it does not move it.
