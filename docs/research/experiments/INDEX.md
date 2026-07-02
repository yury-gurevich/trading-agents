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
| [EXP-004](EXP-004-class1-cases-llm-judge.md) | Arm the drift firewall — Class-1 cases + LLM-judge scorer | 2026-06-25 | ✅ **firewall armed** — on Class-1, grounding Δ = +50 pp (keyword) / **+83 pp (judge)**; judge sharper (blind judge 0% vs keyword 33%). Next: EXP-005 freeze golden baseline + model-swap A/B |
| [EXP-005](EXP-005-model-swap-gate.md) | Operationalise the firewall — golden baseline + model-swap gate | 2026-06-25 | ✅ **firewall trips on a real side-grade** — gpt-5.4 debater silently dropped `calendar-staleness` (4/6) vs gpt-5.5 golden (5/6). `kernel/deliberation_gate.py` + committed golden. Next: N-run hardening (CI-4/S93) |
| [EXP-006](EXP-006-nrun-hardening.md) | Harden the firewall — N-run aggregation against debate noise | 2026-06-25 | ✅ **noise-aware gate** — N=3 reveals `calendar-staleness` was champion-flaky (1/3) so EXP-005's trip was partly noise; gate now trips gpt-5.4 on the *robust* `name-correlation` (2/3→1/3). Found+fixed 400-tok truncation. Next: larger N + margin (CI-4/S93) |
| [EXP-007](EXP-007-aura-snapshot-local-export.md) | Can Aura Free snapshots be stored locally via API? | 2026-07-01 | Snapshot create/list works on the active Free instance, but local download is blocked by `HTTP 403`; Free snapshots are managed rollback only, not off-platform backup proof |

## Adding an experiment

1. Next id is `EXP-008`. Create `EXP-00N-<slug>.md` with the four headings above.
2. Add a row here.
3. Link the artifacts (transcripts, critique docs) from *Delivery*.
4. If it triggers a parameter change, that change runs as a **parameter experiment** (charter report) —
   the probe *informs* the dial; it does not move it.
